"""
RAG Integration Service - RAG Integration with Document Upload

This service automatically:
1. Extracts text from uploaded documents
2. Generates vector representations (embeddings)
3. Saves them to PostgreSQL database
4. Updates document metadata
"""
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from loguru import logger
import psycopg2
from psycopg2.extras import execute_values

from database.db_connection import connect, disconnect
from services.RAG.embedding_service import get_embedding_service
from services.RAG.document_processor import get_document_processor


class RAGIntegrationService:
    """Service for integrating RAG with document upload system"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.document_processor = get_document_processor()
        self.conn = None
        self.cursor = None
        logger.info("✅ RAGIntegrationService initialized")
    
    async def process_uploaded_document(
        self,
        user_id: int,
        document_id: str,
        file_path: Path,
        filename: str,
        original_filename: str,
        document_type: str,
        description: Optional[str] = None,
        file_size: Optional[int] = None,
        mime_type: Optional[str] = None
    ) -> Dict:
        """
        Processes uploaded document for RAG system
        
        Processing stages:
        1. Text extraction from document
        2. Vector representation generation
        3. Saving to database
        4. Synchronization with resume_embedding (if primary CV)
        
        Args:
            user_id: User ID
            document_id: Unique document ID
            file_path: File path
            filename: System filename
            original_filename: Original filename
            document_type: Document type (cv, cover_letter, certificate, other)
            description: Document description
            file_size: File size in bytes
            mime_type: MIME type of file
            
        Returns:
            Dict: Processing result with details
        """
        try:
            logger.info(f"🔄 Starting RAG document processing: {original_filename} for user_id={user_id}")
            
            # 1. Text extraction
            logger.info(f"📄 Extracting text from {file_path}")
            content_text = self.document_processor.extract_text(file_path)
            
            if not content_text or len(content_text.strip()) < 50:
                logger.warning(f"⚠️ Document contains too little text: {len(content_text)} characters")
                return {
                    "success": False,
                    "error": "Document contains insufficient text for analysis",
                    "text_length": len(content_text)
                }
            
            logger.info(f"✅ Extracted {len(content_text)} characters of text")
            
            # 2. Embedding generation
            logger.info("🧮 Generating vector representation...")
            embedding = self.embedding_service.generate_embedding(content_text)
            
            if not embedding:
                logger.error("❌ Failed to generate embedding")
                return {
                    "success": False,
                    "error": "Error generating vector representation"
                }
            
            logger.info(f"✅ Generated vector of dimension {len(embedding)}")
            
            # 3. Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # 4. Determine if this is primary CV
            is_primary_cv = (document_type.lower() == 'cv')
            
            # 5. Save to database
            logger.info("💾 Saving to database...")
            db_result = await self._save_to_database(
                user_id=user_id,
                document_id=document_id,
                filename=filename,
                original_filename=original_filename,
                document_type=document_type,
                content_text=content_text,
                content_embedding=embedding,
                file_size=file_size,
                mime_type=mime_type,
                file_hash=file_hash,
                is_primary_cv=is_primary_cv,
                description=description
            )
            
            if not db_result["success"]:
                return db_result
            
            logger.info(f"✅ Document successfully processed and saved to RAG system")
            
            return {
                "success": True,
                "document_id": document_id,
                "text_length": len(content_text),
                "embedding_dimension": len(embedding),
                "is_primary_cv": is_primary_cv,
                "file_hash": file_hash,
                "message": "Document successfully processed for RAG system"
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing document {original_filename}: {str(e)}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}"
            }
    
    async def _save_to_database(
        self,
        user_id: int,
        document_id: str,
        filename: str,
        original_filename: str,
        document_type: str,
        content_text: str,
        content_embedding: List[float],
        file_size: Optional[int],
        mime_type: Optional[str],
        file_hash: str,
        is_primary_cv: bool,
        description: Optional[str]
    ) -> Dict:
        """
        Saves document and its embedding to database
        
        Returns:
            Dict: Save result
        """
        try:
            # Database connection
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            # SQL query for insert/update
            insert_query = """
            INSERT INTO document_embeddings (
                user_id, document_id, filename, original_filename, document_type,
                is_primary_cv, content_text, content_embedding, file_size, mime_type,
                file_hash, is_active, processing_status, description
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s::vector, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (user_id, document_id) 
            DO UPDATE SET
                filename = EXCLUDED.filename,
                original_filename = EXCLUDED.original_filename,
                document_type = EXCLUDED.document_type,
                is_primary_cv = EXCLUDED.is_primary_cv,
                content_text = EXCLUDED.content_text,
                content_embedding = EXCLUDED.content_embedding,
                file_size = EXCLUDED.file_size,
                mime_type = EXCLUDED.mime_type,
                file_hash = EXCLUDED.file_hash,
                is_active = EXCLUDED.is_active,
                processing_status = EXCLUDED.processing_status,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id;
            """
            
            # Format embedding for PostgreSQL
            embedding_str = '[' + ','.join(map(str, content_embedding)) + ']'
            
            # Execute query
            self.cursor.execute(insert_query, (
                user_id, document_id, filename, original_filename, document_type,
                is_primary_cv, content_text, embedding_str, file_size, mime_type,
                file_hash, True, 'processed', description
            ))
            
            row_id = self.cursor.fetchone()[0]
            self.conn.commit()
            
            logger.info(f"✅ Document saved to DB with ID={row_id}")
            
            # If this is primary CV, trigger will automatically synchronize
            # with user_personal_info.resume_embedding
            if is_primary_cv:
                logger.info(f"📋 Primary CV - sync_primary_cv_trigger will update resume_embedding")
            
            return {
                "success": True,
                "database_id": row_id,
                "message": "Document saved to database"
            }
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"❌ Error saving to DB: {str(e)}")
            return {
                "success": False,
                "error": f"Database save error: {str(e)}"
            }
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)
    
    async def delete_document_embedding(self, user_id: int, document_id: str) -> Dict:
        """
        Deletes document embedding from database
        
        Args:
            user_id: User ID
            document_id: Document ID
            
        Returns:
            Dict: Deletion result
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            # Soft delete (is_active = false)
            delete_query = """
            UPDATE document_embeddings
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND document_id = %s
            RETURNING id;
            """
            
            self.cursor.execute(delete_query, (user_id, document_id))
            result = self.cursor.fetchone()
            self.conn.commit()
            
            if result:
                logger.info(f"✅ Document embedding {document_id} marked as inactive")
                return {
                    "success": True,
                    "message": "Document embedding successfully deleted"
                }
            else:
                logger.warning(f"⚠️ Document embedding {document_id} not found")
                return {
                    "success": False,
                    "error": "Document embedding not found"
                }
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"❌ Error deleting embedding: {str(e)}")
            return {
                "success": False,
                "error": f"Deletion error: {str(e)}"
            }
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)
    
    async def reprocess_document(self, user_id: int, document_id: str, file_path: Path) -> Dict:
        """
        Reprocesses existing document
        
        Useful when:
        - Document was updated
        - Error occurred during initial processing
        - Embedding model changed
        
        Args:
            user_id: User ID
            document_id: Document ID
            file_path: File path
            
        Returns:
            Dict: Reprocessing result
        """
        try:
            logger.info(f"🔄 Reprocessing document {document_id} for user_id={user_id}")
            
            # Get document metadata from DB
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            select_query = """
            SELECT filename, original_filename, document_type, file_size, mime_type, description
            FROM document_embeddings
            WHERE user_id = %s AND document_id = %s;
            """
            
            self.cursor.execute(select_query, (user_id, document_id))
            result = self.cursor.fetchone()
            
            if not result:
                return {
                    "success": False,
                    "error": "Document not found in database"
                }
            
            filename, original_filename, document_type, file_size, mime_type, description = result
            
            # Close connection before reprocessing
            self.cursor.close()
            disconnect(self.conn)
            
            # Reprocess document
            return await self.process_uploaded_document(
                user_id=user_id,
                document_id=document_id,
                file_path=file_path,
                filename=filename,
                original_filename=original_filename,
                document_type=document_type,
                description=description,
                file_size=file_size,
                mime_type=mime_type
            )
            
        except Exception as e:
            logger.error(f"❌ Error reprocessing document: {str(e)}")
            return {
                "success": False,
                "error": f"Reprocessing error: {str(e)}"
            }
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculates SHA-256 hash of file
        
        Args:
            file_path: File path
            
        Returns:
            str: File hash (hex)
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"❌ Error calculating file hash: {str(e)}")
            return ""
    
    async def get_document_embedding_status(self, user_id: int, document_id: str) -> Dict:
        """
        Gets document processing status
        
        Args:
            user_id: User ID
            document_id: Document ID
            
        Returns:
            Dict: Document status
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            query = """
            SELECT 
                id, document_type, processing_status, is_primary_cv, 
                is_active, created_at, updated_at,
                LENGTH(content_text) as text_length
            FROM document_embeddings
            WHERE user_id = %s AND document_id = %s;
            """
            
            self.cursor.execute(query, (user_id, document_id))
            result = self.cursor.fetchone()
            
            if not result:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            return {
                "success": True,
                "database_id": result[0],
                "document_type": result[1],
                "processing_status": result[2],
                "is_primary_cv": result[3],
                "is_active": result[4],
                "created_at": result[5].isoformat() if result[5] else None,
                "updated_at": result[6].isoformat() if result[6] else None,
                "text_length": result[7]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting status: {str(e)}")
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)


# Singleton instance
_rag_integration_service_instance: Optional[RAGIntegrationService] = None


def get_rag_integration_service() -> RAGIntegrationService:
    """
    Gets singleton instance of RAGIntegrationService
    
    Returns:
        RAGIntegrationService: Service instance
    """
    global _rag_integration_service_instance
    if _rag_integration_service_instance is None:
        _rag_integration_service_instance = RAGIntegrationService()
        logger.info("🎯 RAGIntegrationService singleton created")
    return _rag_integration_service_instance


# Convenience function
async def process_document_for_rag(
    user_id: int,
    document_id: str,
    file_path: Path,
    filename: str,
    original_filename: str,
    document_type: str,
    **kwargs
) -> Dict:
    """
    Convenience function for document processing
    
    Args:
        user_id: User ID
        document_id: Document ID
        file_path: File path
        filename: Filename
        original_filename: Original filename
        document_type: Document type
        **kwargs: Additional parameters
        
    Returns:
        Dict: Processing result
    """
    service = get_rag_integration_service()
    return await service.process_uploaded_document(
        user_id=user_id,
        document_id=document_id,
        file_path=file_path,
        filename=filename,
        original_filename=original_filename,
        document_type=document_type,
        **kwargs
    )

