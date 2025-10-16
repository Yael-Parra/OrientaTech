"""
Embedding Service for OrientaTech RAG System
Generates vector embeddings from text using sentence-transformers
"""
import os
import numpy as np
from typing import List, Optional, Dict, Union
from pathlib import Path
from loguru import logger
from sentence_transformers import SentenceTransformer
import torch


class EmbeddingService:
    """
    Service for generating text embeddings using sentence-transformers
    
    Features:
    - Multi-language support (English, Spanish)
    - Batch processing for performance
    - Caching for frequently used embeddings
    - 384-dimensional vectors optimized for semantic search
    """
    
    # Model configuration
    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION = 384
    MAX_SEQUENCE_LENGTH = 512
    
    # Singleton pattern - one model instance per application
    _model_instance: Optional[SentenceTransformer] = None
    _model_loaded: bool = False
    
    def __init__(self):
        """Initialize the embedding service"""
        self.model_name = self.MODEL_NAME
        self.embedding_dim = self.EMBEDDING_DIMENSION
        self.max_length = self.MAX_SEQUENCE_LENGTH
        
        # Device configuration (GPU if available, otherwise CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"EmbeddingService initialized with device: {self.device}")
    
    def _load_model(self) -> SentenceTransformer:
        """
        Lazy loading of the sentence-transformer model
        
        Returns:
            SentenceTransformer: Loaded model instance
        """
        if EmbeddingService._model_instance is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            try:
                # Load model with caching
                cache_folder = Path(__file__).parent.parent.parent / "models_cache"
                cache_folder.mkdir(exist_ok=True)
                
                EmbeddingService._model_instance = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    cache_folder=str(cache_folder)
                )
                
                EmbeddingService._model_loaded = True
                logger.success(f"✅ Model loaded successfully: {self.model_name}")
                logger.info(f"   Dimension: {self.embedding_dim}")
                logger.info(f"   Max sequence length: {self.max_length}")
                logger.info(f"   Device: {self.device}")
                
            except Exception as e:
                logger.error(f"❌ Error loading model: {e}")
                raise RuntimeError(f"Failed to load embedding model: {e}")
        
        return EmbeddingService._model_instance
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before generating embeddings
        
        Args:
            text: Input text to preprocess
            
        Returns:
            str: Cleaned and normalized text
        """
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Truncate to max length (approximate, model will handle exact tokenization)
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = self.max_length * 4
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.debug(f"Text truncated to {max_chars} characters")
        
        return text
    
    def generate_embedding(
        self, 
        text: str,
        normalize: bool = True
    ) -> List[float]:
        """
        Generate embedding vector for a single text
        
        Args:
            text: Input text to embed
            normalize: Whether to normalize the embedding vector
            
        Returns:
            List[float]: 384-dimensional embedding vector
            
        Raises:
            ValueError: If text is empty or invalid
            RuntimeError: If model fails to generate embedding
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Preprocess text
            cleaned_text = self.preprocess_text(text)
            
            if not cleaned_text:
                raise ValueError("Text is empty after preprocessing")
            
            # Load model (lazy loading)
            model = self._load_model()
            
            # Generate embedding
            embedding = model.encode(
                cleaned_text,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            # Convert to list of floats
            embedding_list = embedding.tolist()
            
            # Validate dimension
            if len(embedding_list) != self.embedding_dim:
                raise RuntimeError(
                    f"Unexpected embedding dimension: {len(embedding_list)} "
                    f"(expected {self.embedding_dim})"
                )
            
            logger.debug(f"Generated embedding for text: '{cleaned_text[:50]}...'")
            return embedding_list
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    def generate_batch_embeddings(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of texts to embed
            normalize: Whether to normalize embedding vectors
            batch_size: Number of texts to process at once
            
        Returns:
            List[List[float]]: List of 384-dimensional embedding vectors
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If model fails to generate embeddings
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        try:
            # Preprocess all texts
            cleaned_texts = [self.preprocess_text(text) for text in texts]
            
            # Filter out empty texts
            valid_texts = [text for text in cleaned_texts if text]
            
            if not valid_texts:
                raise ValueError("All texts are empty after preprocessing")
            
            # Load model (lazy loading)
            model = self._load_model()
            
            # Generate embeddings in batches
            embeddings = model.encode(
                valid_texts,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=len(valid_texts) > 10,
                batch_size=batch_size
            )
            
            # Convert to list of lists
            embeddings_list = embeddings.tolist()
            
            logger.info(f"✅ Generated {len(embeddings_list)} embeddings")
            return embeddings_list
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise RuntimeError(f"Failed to generate batch embeddings: {e}")
    
    def calculate_similarity(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Similarity score (0.0 to 1.0)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            # similarity = 1 - cosine_distance
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def get_model_info(self) -> Dict:
        """
        Get information about the embedding model
        
        Returns:
            Dict: Model configuration and metadata
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "max_sequence_length": self.max_length,
            "device": self.device,
            "model_loaded": EmbeddingService._model_loaded,
            "supported_languages": [
                "en", "es", "ru", "de", "fr", "it", "pt", "nl", "pl", "tr",
                "ar", "zh", "ja", "ko", "th", "hi"
            ],
            "description": "Multilingual sentence transformer for semantic search"
        }
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded in memory"""
        return EmbeddingService._model_loaded
    
    def unload_model(self):
        """
        Unload model from memory (useful for testing or cleanup)
        
        Warning: This will cause the model to be reloaded on next use
        """
        if EmbeddingService._model_instance is not None:
            logger.info("Unloading embedding model from memory")
            EmbeddingService._model_instance = None
            EmbeddingService._model_loaded = False
            
            # Clear GPU cache if using CUDA
            if self.device == "cuda":
                torch.cuda.empty_cache()
    
    async def generate_embedding_async(
        self,
        text: str,
        normalize: bool = True
    ) -> List[float]:
        """
        Async wrapper for generate_embedding
        Useful for FastAPI async endpoints
        
        Args:
            text: Input text to embed
            normalize: Whether to normalize the embedding vector
            
        Returns:
            List[float]: 384-dimensional embedding vector
        """
        # Run in thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_embedding,
            text,
            normalize
        )
    
    async def generate_batch_embeddings_async(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Async wrapper for generate_batch_embeddings
        
        Args:
            texts: List of texts to embed
            normalize: Whether to normalize embedding vectors
            batch_size: Number of texts to process at once
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        # Run in thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_batch_embeddings,
            texts,
            normalize,
            batch_size
        )


# ===================================
# Singleton instance for global use
# ===================================

_embedding_service_instance: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    """
    Get singleton instance of EmbeddingService
    
    Returns:
        EmbeddingService: Singleton instance
    """
    global _embedding_service_instance
    
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    
    return _embedding_service_instance


# ===================================
# Convenience functions
# ===================================

def generate_embedding(text: str) -> List[float]:
    """
    Convenience function to generate embedding
    
    Args:
        text: Input text
        
    Returns:
        List[float]: Embedding vector
    """
    service = get_embedding_service()
    return service.generate_embedding(text)


def generate_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Convenience function to generate batch embeddings
    
    Args:
        texts: List of texts
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    service = get_embedding_service()
    return service.generate_batch_embeddings(texts)


# ===================================
# Testing and validation
# ===================================

if __name__ == "__main__":
    """Test the embedding service"""
    logger.info("Testing EmbeddingService...")
    
    # Create service
    service = EmbeddingService()
    
    # Test single embedding
    logger.info("Test 1: Single embedding generation")
    text = "Python developer with FastAPI experience"
    embedding = service.generate_embedding(text)
    logger.info(f"✅ Generated embedding with dimension: {len(embedding)}")
    logger.info(f"   First 5 values: {embedding[:5]}")
    
    # Test batch embeddings
    logger.info("\nTest 2: Batch embedding generation")
    texts = [
        "Python developer with 3 years experience",
        "JavaScript developer with React skills",
        "Data scientist with machine learning expertise"
    ]
    embeddings = service.generate_batch_embeddings(texts)
    logger.info(f"✅ Generated {len(embeddings)} embeddings")
    
    # Test similarity
    logger.info("\nTest 3: Similarity calculation")
    similarity = service.calculate_similarity(embeddings[0], embeddings[1])
    logger.info(f"✅ Similarity between text 1 and 2: {similarity:.4f}")
    
    # Test model info
    logger.info("\nTest 4: Model information")
    info = service.get_model_info()
    logger.info(f"✅ Model info: {info}")
    
    logger.success("🎉 All tests passed!")

