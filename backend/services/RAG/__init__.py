"""
RAG (Retrieval-Augmented Generation) Services for OrientaTech

This module provides vector search and semantic matching capabilities
for document retrieval and recommendation.

Services:
- EmbeddingService: Generate vector embeddings from text
- DocumentProcessor: Extract text from documents (PDF, DOCX)
- SearchService: Semantic search functionality
- RankingService: Result ranking and scoring
- RAGIntegrationService: Integration with document upload system
"""

from .embedding_service import (
    EmbeddingService,
    get_embedding_service,
    generate_embedding,
    generate_batch_embeddings
)

from .document_processor import (
    DocumentProcessor,
    get_document_processor,
    extract_text,
    extract_metadata
)

from .search_service import (
    SearchService,
    get_search_service
)

from .ranking_service import (
    RankingService,
    get_ranking_service
)

from .rag_integration_service import (
    RAGIntegrationService,
    get_rag_integration_service,
    process_document_for_rag
)

__all__ = [
    # Embedding service
    'EmbeddingService',
    'get_embedding_service',
    'generate_embedding',
    'generate_batch_embeddings',
    
    # Document processor
    'DocumentProcessor',
    'get_document_processor',
    'extract_text',
    'extract_metadata',
    
    # Search service
    'SearchService',
    'get_search_service',
    
    # Ranking service
    'RankingService',
    'get_ranking_service',
    
    # RAG Integration service
    'RAGIntegrationService',
    'get_rag_integration_service',
    'process_document_for_rag',
]
