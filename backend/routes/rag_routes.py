"""
RAG Routes for OrientaTech API
Semantic search and document retrieval endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Annotated, Optional
from loguru import logger

from models.rag_models import (
    SearchRequest,
    UserSearchRequest,
    SearchResponse,
    SearchResultItem,
    DocumentStatisticsResponse,
    RAGServiceInfoResponse,
    ErrorResponse,
    EnhancedSearchResponse,  # ← NUEVO
    LLMContextAnalysis,      # ← NUEVO
    LLMCareerAdvice         # ← NUEVO
)
from services.RAG import (
    get_search_service,
    get_ranking_service
)
from services.rag_llm_integration_service import get_rag_llm_integration_service  # ← NUEVO
from routes.auth_simple import get_current_user


# Router for RAG endpoints
rag_router = APIRouter(
    prefix="/api/rag",
    tags=["🔍 RAG Search"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"description": "Unauthorized - Token required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)

# Service instances
search_service = get_search_service()
ranking_service = get_ranking_service()
integration_service = get_rag_llm_integration_service()  # ← NUEVO


@rag_router.post(
    "/search/user/{user_id}",
    response_model=EnhancedSearchResponse,  # ← CAMBIADO: Ahora devuelve respuesta enriquecida
    summary="👤 Search User Documents (Enhanced with LLM)",
    description="""
    **Search within a specific user's documents with optional LLM analysis.**
    
    This endpoint allows searching only within documents uploaded by a specific user.
    Requires authentication and users can only search their own documents.
    
    ### NEW: Optional LLM Analysis
    - 🧠 Set `include_llm_analysis=true` to get contextual insights
    - 🚀 LLM analyzes ALL found documents and provides career advice
    - ⚡ Adds 2-5 seconds processing time but provides valuable insights
    
    ### Security:
    - 🔐 JWT authentication required
    - ✅ Users can only search their own documents
    - ❌ Admins can search any user's documents (future feature)
    
    ### Use cases:
    - User searching their own uploaded documents
    - Finding specific information in personal documents
    - Getting career insights based on document collection
    - Checking what documents match a job description
    
    ### Document types:
    - Leave `document_type` empty to search ALL document types
    - Specify `document_type` to filter by specific type (cv, cover_letter, etc.)
    """,
    response_description="List of matching user documents with optional LLM analysis"
)
async def search_user_documents(
    user_id: int,
    request: UserSearchRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    include_llm_analysis: Annotated[bool, Query(description="Include LLM contextual analysis")] = False  # ← NUEVO
):
    """
    Search documents of specific user with optional LLM analysis
    """
    try:
        # Security: Users can only search their own documents
        if current_user['id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only search your own documents"
            )
        
        # Perform search
        results = await search_service.search_user_documents(
            user_id=user_id,
            query=request.query,
            document_type=request.document_type.value if request.document_type else None,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Apply ranking
        ranked_results = ranking_service.rank_results(results)
        
        # Prepare base response
        base_response = {
            'success': True,
            'query': request.query,
            'total_results': len(ranked_results),
            'results': [SearchResultItem(**result) for result in ranked_results],
            'search_params': {
                'user_id': user_id,
                'document_type': request.document_type.value if request.document_type else None,
                'limit': request.limit,
                'similarity_threshold': request.similarity_threshold
            },
            'llm_status': 'not_requested'
        }
        
        # ← NUEVA FUNCIONALIDAD: Análisis LLM opcional
        if include_llm_analysis and ranked_results:
            try:
                logger.info(f"Starting LLM analysis for {len(ranked_results)} documents")
                
                # Get user profile (opcional)
                user_profile = None  # TODO: Implementar obtener perfil de usuario si existe
                
                # Perform LLM analysis
                context_analysis, career_advice, processing_time = await integration_service.analyze_search_context(
                    search_results=ranked_results,
                    user_query=request.query,
                    user_profile=user_profile
                )
                
                # Add LLM results to response
                if context_analysis and career_advice:
                    base_response.update({
                        'llm_analysis': context_analysis,
                        'llm_advice': career_advice,
                        'llm_processing_time': processing_time,
                        'llm_status': 'completed'
                    })
                    logger.success(f"✅ LLM analysis completed successfully in {processing_time:.2f}s")
                else:
                    base_response.update({
                        'llm_processing_time': processing_time,
                        'llm_status': 'failed'
                    })
                    logger.warning("⚠️ LLM analysis completed but returned no results")
                    
            except Exception as llm_error:
                logger.error(f"❌ LLM analysis failed: {llm_error}")
                base_response.update({
                    'llm_status': 'failed',
                    'llm_error': str(llm_error)
                })
                # Continue with base response even if LLM fails
        
        # Convert to response model
        return EnhancedSearchResponse(**base_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@rag_router.get(
    "/similar/{document_id}",
    response_model=SearchResponse,
    summary="📄 Find Similar Documents",
    description="""
    **Find documents similar to a specific document.**
    
    🔐 **Authentication required** - Only searches within YOUR documents.
    
    Given a document ID, this endpoint finds other documents with similar content
    using vector similarity search.
    
    ### Security:
    - ✅ JWT authentication required
    - ✅ Only searches YOUR documents
    - ✅ Document must belong to YOU
    
    ### Use cases:
    - Find your CVs similar to a reference CV
    - Discover related certificates in your documents
    - Group similar documents
    
    ### How it works:
    1. Verifies document belongs to you
    2. Retrieves the embedding of the reference document
    3. Searches for similar documents in YOUR collection only
    4. Excludes the reference document itself
    5. Returns top N most similar documents
    """,
    response_description="List of similar documents from YOUR collection"
)
async def find_similar_documents(
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=20, description="Maximum results")] = 5,
    similarity_threshold: Annotated[float, Query(ge=0.0, le=1.0, description="Minimum similarity")] = 0.7
):
    """
    Find documents similar to a specific document (only within user's own documents)
    """
    try:
        # 🔐 Security: Search only within current user's documents
        results = await search_service.get_similar_documents(
            document_id=document_id,
            user_id=current_user['id'],  # ← Filter by current user!
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        # Apply ranking
        ranked_results = ranking_service.rank_results(results)
        
        # Convert to response model
        return SearchResponse(
            success=True,
            query=f"Similar to document: {document_id}",
            total_results=len(ranked_results),
            results=[SearchResultItem(**result) for result in ranked_results],
            search_params={
                'reference_document_id': document_id,
                'user_id': current_user['id'],
                'limit': limit,
                'similarity_threshold': similarity_threshold
            }
        )
        
    except ValueError as e:
        # Document not found or doesn't belong to user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Similar documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===================================
# STATISTICS ENDPOINTS
# ===================================

@rag_router.get(
    "/stats",
    response_model=DocumentStatisticsResponse,
    summary="📊 Document Statistics",
    description="""
    **Get global statistics about indexed documents.**
    
    Returns comprehensive statistics about all documents in the RAG system:
    - Total document count
    - Count by document type (CV, cover letter, certificate, other)
    - Total storage size
    - Processing status (processed, pending, failed)
    
    ### Use cases:
    - System monitoring
    - Dashboard statistics
    - Capacity planning
    """,
    response_description="Global document statistics"
)
async def get_statistics():
    """Get global document statistics"""
    try:
        stats = await search_service.get_search_statistics()
        return DocumentStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@rag_router.get(
    "/stats/user/{user_id}",
    response_model=DocumentStatisticsResponse,
    summary="👤 User Document Statistics",
    description="""
    **Get statistics about a specific user's documents.**
    
    Returns statistics for documents uploaded by a specific user.
    Requires authentication - users can only view their own statistics.
    """,
    response_description="User document statistics"
)
async def get_user_statistics(
    user_id: int,
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Get user-specific document statistics"""
    try:
        # Security: Users can only view their own statistics
        if current_user['id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own statistics"
            )
        
        stats = await search_service.get_search_statistics(user_id=user_id)
        return DocumentStatisticsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===================================
# INFO ENDPOINTS
# ===================================

@rag_router.get(
    "/info",
    response_model=RAGServiceInfoResponse,
    summary="ℹ️ RAG Service Information",
    description="""
    **Get information about the RAG service configuration.**
    
    Returns details about:
    - Service version
    - Embedding model used
    - Vector dimensions
    - Supported document types
    - Default parameters
    
    ### Use for:
    - Service discovery
    - Configuration validation
    - Client setup
    """,
    response_description="RAG service configuration and status"
)
async def get_rag_info():
    """Get RAG service information"""
    try:
        search_info = search_service.get_service_info()
        ranking_info = ranking_service.get_service_info()
        
        return RAGServiceInfoResponse(
            service="OrientaTech RAG System",
            version=search_info['version'],
            embedding_model=search_info['embedding_model'],
            embedding_dimension=search_info['embedding_dimension'],
            supported_document_types=search_info['supported_document_types'],
            default_similarity_threshold=search_info['default_similarity_threshold'],
            default_max_results=search_info['default_max_results']
        )
        
    except Exception as e:
        logger.error(f"Info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===================================
# HEALTH CHECK
# ===================================

@rag_router.get(
    "/health",
    summary="🏥 RAG Health Check",
    description="Check if RAG service is operational"
)
async def rag_health_check():
    """Check RAG service health"""
    try:
        # Check if services are initialized
        search_info = search_service.get_service_info()
        
        # Check database connection with statistics
        stats = await search_service.get_search_statistics()
        
        return {
            "status": "healthy",
            "service": "RAG Search",
            "embedding_service": "operational",
            "search_service": "operational",
            "database": "connected",
            "indexed_documents": stats.get('total_documents', 0)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "service": "RAG Search",
            "error": str(e)
        }

