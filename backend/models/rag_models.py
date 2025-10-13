"""
Pydantic models for RAG API endpoints
Request and response models for semantic search functionality
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class DocumentTypeEnum(str, Enum):
    """Document type options"""
    cv = "cv"
    cover_letter = "cover_letter"
    certificate = "certificate"
    other = "other"


# ===================================
# REQUEST MODELS
# ===================================

class SearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Search query text",
        example="Python developer with FastAPI experience"
    )
    document_type: Optional[DocumentTypeEnum] = Field(
        None,
        description="Filter by document type"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results"
    )
    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0.0 to 1.0)"
    )
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class UserSearchRequest(BaseModel):
    """Request model for user-specific search"""
    query: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Search query text"
    )
    document_type: Optional[DocumentTypeEnum] = Field(
        None,
        description="Filter by document type (optional - leave empty to search all types)",
        json_schema_extra={"example": None}
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results"
    )
    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Python developer with FastAPI experience",
                "limit": 10,
                "similarity_threshold": 0.3
            }
        }


class RankingWeightsRequest(BaseModel):
    """Custom ranking weights"""
    similarity: float = Field(default=0.6, ge=0.0, le=1.0)
    recency: float = Field(default=0.2, ge=0.0, le=1.0)
    completeness: float = Field(default=0.1, ge=0.0, le=1.0)
    file_quality: float = Field(default=0.1, ge=0.0, le=1.0)


# ===================================
# RESPONSE MODELS
# ===================================

class SearchResultItem(BaseModel):
    """Single search result item"""
    document_id: str = Field(description="Unique document ID")
    filename: str = Field(description="Stored filename")
    original_filename: str = Field(description="Original filename")
    document_type: str = Field(description="Document type")
    
    # Relevance scores
    similarity_score: float = Field(description="Vector similarity score (0.0-1.0)")
    similarity_percentage: float = Field(description="Similarity as percentage (0-100)")
    final_score: Optional[float] = Field(None, description="Final ranking score if ranking applied")
    
    # Content
    content_preview: str = Field(description="Preview of document content")
    
    # File metadata
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_size_mb: Optional[float] = Field(None, description="File size in MB")
    
    # User info
    user_id: int = Field(description="Document owner ID")
    
    # URLs
    download_url: str = Field(description="URL to download document")
    view_url: str = Field(description="URL to view document")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Document creation timestamp")
    
    # Optional
    description: Optional[str] = Field(None, description="Document description")
    ranking_scores: Optional[Dict[str, float]] = Field(None, description="Individual ranking scores")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "abc123-def456",
                "filename": "resume_johndoe.pdf",
                "original_filename": "John_Doe_Resume.pdf",
                "document_type": "cv",
                "similarity_score": 0.89,
                "similarity_percentage": 89.0,
                "content_preview": "Python developer with 3 years of experience in FastAPI...",
                "file_size": 245678,
                "file_size_mb": 0.23,
                "user_id": 123,
                "download_url": "/api/documents/abc123-def456/download",
                "view_url": "/api/documents/abc123-def456/view",
                "created_at": "2024-10-01T10:00:00",
                "description": "My latest CV"
            }
        }


class SearchResponse(BaseModel):
    """Response model for search results"""
    success: bool = Field(description="Whether search was successful")
    query: str = Field(description="Original search query")
    total_results: int = Field(description="Number of results found")
    results: List[SearchResultItem] = Field(description="List of search results")
    search_params: Dict = Field(description="Search parameters used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "Python developer with FastAPI",
                "total_results": 5,
                "results": [],
                "search_params": {
                    "document_type": "cv",
                    "limit": 10,
                    "similarity_threshold": 0.7
                }
            }
        }


class DocumentStatisticsResponse(BaseModel):
    """Response model for document statistics"""
    total_documents: int = Field(description="Total number of documents")
    cv_count: int = Field(description="Number of CV documents")
    cover_letter_count: int = Field(description="Number of cover letters")
    certificate_count: int = Field(description="Number of certificates")
    other_count: int = Field(description="Number of other documents")
    total_size_bytes: int = Field(description="Total size in bytes")
    total_size_mb: float = Field(description="Total size in MB")
    processed_count: int = Field(description="Number of processed documents")
    pending_count: int = Field(description="Number of pending documents")
    failed_count: int = Field(description="Number of failed documents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 150,
                "cv_count": 80,
                "cover_letter_count": 40,
                "certificate_count": 25,
                "other_count": 5,
                "total_size_bytes": 257425000,
                "total_size_mb": 245.5,
                "processed_count": 148,
                "pending_count": 2,
                "failed_count": 0
            }
        }


class RAGServiceInfoResponse(BaseModel):
    """Response model for RAG service information"""
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    embedding_model: str = Field(description="Embedding model name")
    embedding_dimension: int = Field(description="Embedding vector dimension")
    supported_document_types: List[str] = Field(description="Supported document types")
    default_similarity_threshold: float = Field(description="Default similarity threshold")
    default_max_results: int = Field(description="Default maximum results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service": "OrientaTech RAG System",
                "version": "1.0.0",
                "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
                "embedding_dimension": 384,
                "supported_document_types": ["cv", "cover_letter", "certificate", "other"],
                "default_similarity_threshold": 0.7,
                "default_max_results": 10
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(default=False)
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Search failed",
                "detail": "Database connection error"
            }
        }

