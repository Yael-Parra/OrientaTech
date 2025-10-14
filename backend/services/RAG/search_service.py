"""
Search Service for OrientaTech RAG System
Provides semantic search functionality for documents using vector embeddings
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from backend.database.db_connection import connect_async, disconnect_async

# Import embedding service
try:
    from .embedding_service import get_embedding_service
except ImportError:
    # Fallback for direct execution
    from embedding_service import get_embedding_service


class SearchService:
    """
    Main service for semantic document search
    
    Features:
    - Semantic search across all documents
    - User-specific document search
    - Document type filtering
    - Similar document recommendations
    - Result enrichment with metadata
    """
    
    def __init__(self):
        """Initialize the search service"""
        self.embedding_service = get_embedding_service()
        logger.debug("SearchService initialized")
    
    # ===================================
    # MAIN SEARCH METHODS
    # ===================================
    
    async def semantic_search(
        self,
        query: str,
        user_id: Optional[int] = None,
        document_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Perform semantic search across documents
        
        Args:
            query: Search query text
            user_id: Filter by specific user (None = all users)
            document_type: Filter by document type (None = all types)
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List[Dict]: List of matching documents with metadata
            
        Example:
            results = await search_service.semantic_search(
                query="Python developer with FastAPI experience",
                document_type="cv",
                limit=10
            )
        """
        try:
            # Step 1: Generate embedding for query
            logger.info(f"Searching for: '{query}'")
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Step 2: Search in database using PostgreSQL function
            results = await self._search_in_database(
                query_embedding=query_embedding,
                similarity_threshold=similarity_threshold,
                max_results=limit,
                target_user_id=user_id,
                document_type_filter=document_type
            )
            
            # Step 3: Enrich results with additional metadata
            enriched_results = await self._enrich_results(results)
            
            logger.success(f"✅ Found {len(enriched_results)} documents")
            return enriched_results
            
        except Exception as e:
            logger.error(f"❌ Error in semantic search: {e}")
            raise RuntimeError(f"Search failed: {e}")
    
    async def search_user_documents(
        self,
        user_id: int,
        query: str,
        document_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search documents of specific user
        
        Args:
            user_id: ID of the user
            query: Search query text
            document_type: Filter by document type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List[Dict]: List of matching user documents
        """
        logger.info(f"Searching user {user_id} documents for: '{query}'")
        
        # Use main semantic_search with user_id filter
        return await self.semantic_search(
            query=query,
            user_id=user_id,
            document_type=document_type,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
    
    async def search_by_document_type(
        self,
        document_type: str,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search documents by specific type
        
        Args:
            document_type: Type of document ('cv', 'cover_letter', 'certificate', 'other')
            query: Search query text
            user_id: Filter by user (None = all users)
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List[Dict]: List of matching documents of specified type
        """
        logger.info(f"Searching {document_type} documents for: '{query}'")
        
        # Validate document type
        valid_types = ['cv', 'cover_letter', 'certificate', 'other']
        if document_type not in valid_types:
            raise ValueError(f"Invalid document type. Must be one of: {valid_types}")
        
        # Use main semantic_search with document_type filter
        return await self.semantic_search(
            query=query,
            user_id=user_id,
            document_type=document_type,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
    
    async def get_similar_documents(
        self,
        document_id: str,
        user_id: Optional[int] = None,
        limit: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Find documents similar to a specific document
        
        Args:
            document_id: ID of the reference document
            user_id: Filter by user (if provided, verifies document ownership)
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List[Dict]: List of similar documents
            
        Raises:
            ValueError: If document not found or doesn't belong to user
        """
        try:
            # Get the reference document's embedding from database
            conn = await connect_async()
            if not conn:
                raise RuntimeError("Database connection failed")
            
            try:
                # Get document embedding and verify ownership
                query = """
                    SELECT content_embedding, content_text, user_id
                    FROM document_embeddings
                    WHERE document_id = $1 AND is_active = TRUE
                """
                result = await conn.fetchrow(query, document_id)
                
                if not result or not result['content_embedding']:
                    raise ValueError(f"Document {document_id} not found or has no embedding")
                
                # 🔐 Security: Verify document ownership if user_id provided
                if user_id is not None and result['user_id'] != user_id:
                    raise ValueError(f"Document {document_id} not found or access denied")
                
                # Use the document owner's user_id for filtering similar documents
                search_user_id = user_id if user_id is not None else result['user_id']
                logger.info(f"Searching similar documents for user_id={search_user_id}")
                
                # Convert pgvector to list
                # pgvector returns as string "[0.123,0.456,...]" or as list
                embedding_data = result['content_embedding']
                if isinstance(embedding_data, str):
                    # Parse string format: "[0.123,0.456,...]"
                    reference_embedding = [float(x) for x in embedding_data.strip('[]').split(',')]
                else:
                    # Already a list
                    reference_embedding = list(embedding_data)
                
                # Search using the document's embedding (within same user's documents)
                search_results = await self._search_in_database(
                    query_embedding=reference_embedding,
                    similarity_threshold=similarity_threshold,
                    max_results=limit + 1,  # +1 to exclude self
                    target_user_id=search_user_id,  # ← Filter by user!
                    document_type_filter=None
                )
                
                # Filter out the reference document itself
                filtered_results = [
                    r for r in search_results 
                    if r['document_id'] != document_id
                ][:limit]
                
                # Enrich results
                enriched_results = await self._enrich_results(filtered_results)
                
                logger.success(f"✅ Found {len(enriched_results)} similar documents")
                return enriched_results
                
            finally:
                await disconnect_async(conn)
                
        except Exception as e:
            logger.error(f"❌ Error finding similar documents: {e}")
            raise RuntimeError(f"Similar documents search failed: {e}")
    
    # ===================================
    # DATABASE INTERACTION
    # ===================================
    
    async def _search_in_database(
        self,
        query_embedding: List[float],
        similarity_threshold: float,
        max_results: int,
        target_user_id: Optional[int] = None,
        document_type_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Execute search query in PostgreSQL using pgvector
        
        Args:
            query_embedding: 384-dimensional embedding vector
            similarity_threshold: Minimum similarity score
            max_results: Maximum number of results
            target_user_id: Filter by user ID
            document_type_filter: Filter by document type
            
        Returns:
            List[Dict]: Raw search results from database
        """
        conn = await connect_async()
        if not conn:
            raise RuntimeError("Database connection failed")
        
        try:
            # Convert embedding list to PostgreSQL vector string format
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Call PostgreSQL function search_similar_documents
            query = """
                SELECT * FROM search_similar_documents(
                    $1::vector,  -- query_embedding
                    $2,          -- similarity_threshold
                    $3,          -- max_results
                    $4,          -- target_user_id
                    $5           -- document_type_filter
                )
            """
            
            rows = await conn.fetch(
                query,
                embedding_str,
                similarity_threshold,
                max_results,
                target_user_id,
                document_type_filter
            )
            
            # Convert to list of dictionaries
            results = [dict(row) for row in rows]
            
            logger.debug(f"Database returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
            raise RuntimeError(f"Database search failed: {e}")
        finally:
            await disconnect_async(conn)
    
    # ===================================
    # RESULT ENRICHMENT
    # ===================================
    
    async def _enrich_results(self, results: List[Dict]) -> List[Dict]:
        """
        Enrich search results with additional metadata
        
        Args:
            results: Raw results from database
            
        Returns:
            List[Dict]: Enriched results with URLs, user info, etc.
        """
        enriched = []
        
        for result in results:
            enriched_result = {
                # Basic document info
                'document_id': result['document_id'],
                'filename': result['filename'],
                'original_filename': result['original_filename'],
                'document_type': result['document_type'],
                
                # Search relevance
                'similarity_score': float(result['similarity_score']),
                'similarity_percentage': round(float(result['similarity_score']) * 100, 2),
                
                # Content
                'content_preview': self._create_preview(result.get('content_text', '')),
                
                # File metadata
                'file_size': result['file_size'],
                'file_size_mb': round(result['file_size'] / (1024 * 1024), 2) if result['file_size'] else 0,
                
                # User info
                'user_id': result['user_id'],
                
                # URLs
                'download_url': f"/api/documents/{result['document_id']}/download",
                'view_url': f"/api/documents/{result['document_id']}/view",
                
                # Timestamps
                'created_at': result['created_at'].isoformat() if result.get('created_at') else None,
                
                # Description
                'description': result.get('description', '')
            }
            
            enriched.append(enriched_result)
        
        return enriched
    
    def _create_preview(self, text: str, max_length: int = 200) -> str:
        """
        Create text preview for search results
        
        Args:
            text: Full text
            max_length: Maximum preview length
            
        Returns:
            str: Preview text
        """
        if not text:
            return ""
        
        # Truncate to max length
        if len(text) > max_length:
            return text[:max_length].strip() + "..."
        
        return text.strip()
    
    # ===================================
    # STATISTICS
    # ===================================
    
    async def get_search_statistics(
        self,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Get document search statistics
        
        Args:
            user_id: Filter by user (None = all users)
            
        Returns:
            Dict: Statistics about indexed documents
        """
        try:
            conn = await connect_async()
            if not conn:
                raise RuntimeError("Database connection failed")
            
            try:
                # Call PostgreSQL function get_document_statistics
                query = "SELECT * FROM get_document_statistics($1)"
                result = await conn.fetchrow(query, user_id)
                
                if result:
                    return {
                        'total_documents': result['total_documents'],
                        'cv_count': result['cv_count'],
                        'cover_letter_count': result['cover_letter_count'],
                        'certificate_count': result['certificate_count'],
                        'other_count': result['other_count'],
                        'total_size_bytes': result['total_size_bytes'],
                        'total_size_mb': round(result['total_size_bytes'] / (1024 * 1024), 2),
                        'processed_count': result['processed_count'],
                        'pending_count': result['pending_count'],
                        'failed_count': result['failed_count']
                    }
                else:
                    return {
                        'total_documents': 0,
                        'message': 'No documents found'
                    }
                    
            finally:
                await disconnect_async(conn)
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise RuntimeError(f"Statistics retrieval failed: {e}")
    
    # ===================================
    # UTILITY METHODS
    # ===================================
    
    def get_service_info(self) -> Dict:
        """
        Get information about the search service
        
        Returns:
            Dict: Service configuration and status
        """
        return {
            'service': 'SearchService',
            'version': '1.0.0',
            'embedding_model': self.embedding_service.get_model_info()['model_name'],
            'embedding_dimension': self.embedding_service.get_model_info()['embedding_dimension'],
            'supported_document_types': ['cv', 'cover_letter', 'certificate', 'other'],
            'default_similarity_threshold': 0.7,
            'default_max_results': 10
        }


# ===================================
# Singleton instance
# ===================================

_search_service_instance: Optional[SearchService] = None

def get_search_service() -> SearchService:
    """
    Get singleton instance of SearchService
    
    Returns:
        SearchService: Singleton instance
    """
    global _search_service_instance
    
    if _search_service_instance is None:
        _search_service_instance = SearchService()
    
    return _search_service_instance


# ===================================
# Testing and validation
# ===================================

if __name__ == "__main__":
    """Test the search service"""
    import asyncio
    
    async def test_search_service():
        logger.info("Testing SearchService...")
        
        # Create service
        service = SearchService()
        
        # Test service info
        logger.info("Test 1: Service information")
        info = service.get_service_info()
        logger.info(f"✅ Service info: {info['service']}")
        logger.info(f"   Embedding model: {info['embedding_model']}")
        logger.info(f"   Dimension: {info['embedding_dimension']}")
        
        # Test statistics (requires database connection)
        logger.info("\nTest 2: Search statistics")
        try:
            stats = await service.get_search_statistics()
            logger.success(f"✅ Statistics: {stats.get('total_documents', 0)} total documents")
        except Exception as e:
            logger.warning(f"⚠️ Statistics test skipped (requires database): {e}")
        
        logger.success("🎉 Basic tests passed!")
        logger.info("\n⚠️ Note: Full search tests require database with indexed documents")
    
    # Run async tests
    asyncio.run(test_search_service())

