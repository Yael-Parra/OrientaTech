"""
Servicio principal para gestión de documentos de usuario
"""
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from fastapi import UploadFile, HTTPException, status
from loguru import logger

from backend.models.documents import (
    DocumentInfo, DocumentType, UserDocumentsResponse,
    DocumentUploadResponse, DocumentDeleteResponse,
    DocumentValidator, DocumentErrorResponses
)
from backend.services.document_utils import DocumentUtils
from backend.services.cv_anonymizer import anonymize_cv
from backend.services.RAG import get_rag_integration_service

class DocumentService:
    """Servicio principal para gestión de documentos de usuario"""
    
    def __init__(self):
        self.document_utils = DocumentUtils()
        self.rag_integration = get_rag_integration_service()
    
    async def upload_document(
        self, 
        user_id: int, 
        file: UploadFile,
        document_type: DocumentType = DocumentType.CV,
        description: Optional[str] = None
    ) -> DocumentUploadResponse:
        """
        Sube un documento para el usuario
        
        Args:
            user_id: ID del usuario
            file: Archivo subido
            document_type: Tipo de documento
            description: Descripción opcional
            
        Returns:
            DocumentUploadResponse: Resultado de la subida
            
        Raises:
            HTTPException: Si hay errores de validación o subida
        """
        try:
            # Validaciones previas
            await self._validate_upload(user_id, file)
            
            # Leer contenido del archivo
            file_content = await file.read()
            file_size = len(file_content)
            
            # Validar tamaño
            max_size = DocumentUtils.get_max_file_size()
            if not DocumentValidator.validate_file_size(file_size, max_size // (1024 * 1024)):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=DocumentErrorResponses.FILE_TOO_LARGE.dict()
                )
            
            # Generar nombre único y crear carpeta
            unique_filename = DocumentUtils.generate_unique_filename(user_id, file.filename)
            folder_path = DocumentUtils.ensure_user_folder_exists(user_id)
            file_path = folder_path / unique_filename
            
            # Guardar archivo
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Aplicar anonimización si es un archivo PDF
            if file_path.suffix.lower() == '.pdf':
                try:
                    logger.info(f"Aplicando anonimización a {file_path} para usuario {user_id}")
                    result = anonymize_cv(
                        str(file_path), 
                        verbose=False, 
                        output_name=str(file_path),
                        user_id=user_id
                    )
                    if result.success and result.output_file:
                        # Si el archivo de salida es diferente al original, reemplazar
                        if result.output_file != str(file_path):
                            shutil.move(result.output_file, str(file_path))
                        logger.info(f"Anonimización completada para {file_path}")
                        logger.info(f"Datos anonimizados: {result.personal_data_count + result.metadata_count}")
                    else:
                        logger.warning(f"La anonimización no produjo cambios en {file_path}")
                except Exception as e:
                    logger.error(f"Error en anonimización de {file_path}: {str(e)}")
                    # No lanzamos excepción, el archivo se guarda sin anonimizar

            # Crear información del documento
            doc_id = str(uuid.uuid4())
            doc_info = {
                "id": doc_id,
                "filename": unique_filename,
                "original_name": file.filename,
                "type": document_type.value,
                "size": file_size,
                "mime_type": DocumentUtils.get_file_mime_type(file.filename),
                "uploaded_at": datetime.utcnow().isoformat() + "Z",
                "is_active": True,
                "description": description
            }
            
            # Añadir al metadata
            DocumentUtils.add_document_to_metadata(user_id, doc_info)
            
            logger.info(f"Document uploaded successfully for user {user_id}: {unique_filename}")
            
            # 🔥 INTEGRACIÓN CON RAG: Procesar documento para búsqueda semántica
            try:
                logger.info(f"🤖 Iniciando procesamiento RAG del documento {unique_filename}")
                rag_result = await self.rag_integration.process_uploaded_document(
                    user_id=user_id,
                    document_id=doc_id,
                    file_path=file_path,
                    filename=unique_filename,
                    original_filename=file.filename,
                    document_type=document_type.value,
                    description=description,
                    file_size=file_size,
                    mime_type=doc_info["mime_type"]
                )
                
                if rag_result["success"]:
                    logger.info(f"✅ Procesamiento RAG completado: {rag_result.get('message')}")
                else:
                    logger.warning(f"⚠️ Procesamiento RAG falló: {rag_result.get('error')}")
                    # No interrumpimos la carga si el procesamiento RAG falla
                    
            except Exception as e:
                logger.error(f"❌ Error en procesamiento RAG (no crítico): {str(e)}")
                # Continuamos incluso si el procesamiento RAG falla
            
            return DocumentUploadResponse(
                success=True,
                message=f"Documento '{file.filename}' subido exitosamente",
                document_id=doc_id,
                filename=unique_filename,
                size=file_size
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading document for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=DocumentErrorResponses.UPLOAD_FAILED.dict()
            )
    
    async def get_user_documents(self, user_id: int) -> UserDocumentsResponse:
        """
        Obtiene todos los documentos de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            UserDocumentsResponse: Lista de documentos del usuario
        """
        try:
            metadata = DocumentUtils.load_user_metadata(user_id)
            documents = []
            total_size = 0
            
            for doc_data in metadata.get("documents", []):
                if doc_data.get("is_active", True):
                    # Verificar que el archivo existe físicamente
                    folder_path = DocumentUtils.get_user_folder_path(user_id)
                    file_path = folder_path / doc_data["filename"]
                    
                    if file_path.exists():
                        doc_info = DocumentInfo(
                            id=doc_data["id"],
                            filename=doc_data["filename"],
                            original_name=doc_data["original_name"],
                            type=DocumentType(doc_data["type"]),
                            size=doc_data["size"],
                            mime_type=doc_data["mime_type"],
                            uploaded_at=datetime.fromisoformat(
                                doc_data["uploaded_at"].replace("Z", "+00:00")
                            ),
                            is_active=doc_data["is_active"]
                        )
                        documents.append(doc_info)
                        total_size += doc_data["size"]
                    else:
                        # Archivo físico no existe, marcar como inactivo
                        logger.warning(f"File not found: {file_path}")
                        await self._cleanup_missing_file(user_id, doc_data["id"])
            
            return UserDocumentsResponse(
                user_id=user_id,
                total_documents=len(documents),
                total_size_mb=round(total_size / (1024 * 1024), 2),
                max_files_allowed=DocumentUtils.get_max_files_per_user(),
                max_size_mb_per_file=int(os.getenv("MAX_FILE_SIZE_MB", "5")),
                documents=documents
            )
            
        except Exception as e:
            logger.error(f"Error getting documents for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener la lista de documentos"
            )
    
    async def download_document(self, user_id: int, document_id: str) -> Tuple[Path, str, str]:
        """
        Prepara un documento para descarga
        
        Args:
            user_id: ID del usuario
            document_id: ID del documento
            
        Returns:
            Tuple[Path, str, str]: (ruta_archivo, nombre_original, tipo_mime)
            
        Raises:
            HTTPException: Si el documento no existe o no pertenece al usuario
        """
        try:
            metadata = DocumentUtils.load_user_metadata(user_id)
            
            # Buscar el documento
            doc_data = None
            for doc in metadata.get("documents", []):
                if doc["id"] == document_id and doc.get("is_active", True):
                    doc_data = doc
                    break
            
            if not doc_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=DocumentErrorResponses.FILE_NOT_FOUND.dict()
                )
            
            # Verificar que el archivo existe
            folder_path = DocumentUtils.get_user_folder_path(user_id)
            file_path = folder_path / doc_data["filename"]
            
            if not file_path.exists():
                # Limpiar metadata y lanzar error
                await self._cleanup_missing_file(user_id, document_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=DocumentErrorResponses.FILE_NOT_FOUND.dict()
                )
            
            return file_path, doc_data["original_name"], doc_data["mime_type"]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error downloading document {document_id} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al descargar el documento"
            )
    
    async def delete_document(self, user_id: int, document_id: str) -> DocumentDeleteResponse:
        """
        Elimina un documento del usuario
        
        Args:
            user_id: ID del usuario
            document_id: ID del documento a eliminar
            
        Returns:
            DocumentDeleteResponse: Resultado de la eliminación
        """
        try:
            metadata = DocumentUtils.load_user_metadata(user_id)
            
            # Buscar el documento
            doc_data = None
            for doc in metadata.get("documents", []):
                if doc["id"] == document_id:
                    doc_data = doc
                    break
            
            if not doc_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=DocumentErrorResponses.FILE_NOT_FOUND.dict()
                )
            
            # Eliminar archivo físico si existe
            folder_path = DocumentUtils.get_user_folder_path(user_id)
            file_path = folder_path / doc_data["filename"]
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Physical file deleted: {file_path}")
            
            # 🔥 INTEGRACIÓN CON RAG: Eliminar embedding de la base de datos
            try:
                logger.info(f"🤖 Eliminando embedding RAG del documento {document_id}")
                rag_delete_result = await self.rag_integration.delete_document_embedding(
                    user_id=user_id,
                    document_id=document_id
                )
                
                if rag_delete_result["success"]:
                    logger.info(f"✅ Embedding RAG eliminado")
                else:
                    logger.warning(f"⚠️ No se pudo eliminar el embedding RAG: {rag_delete_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"❌ Error al eliminar embedding RAG (no crítico): {str(e)}")
            
            # Eliminar del metadata
            if DocumentUtils.remove_document_from_metadata(user_id, document_id):
                logger.info(f"Document {document_id} deleted for user {user_id}")
                return DocumentDeleteResponse(
                    success=True,
                    message=f"Documento '{doc_data['original_name']}' eliminado exitosamente",
                    document_id=document_id
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=DocumentErrorResponses.DELETE_FAILED.dict()
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting document {document_id} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=DocumentErrorResponses.DELETE_FAILED.dict()
            )
    
    async def get_folder_info(self, user_id: int) -> Dict:
        """
        Obtiene información de la carpeta del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict: Información de la carpeta
        """
        try:
            folder_path = DocumentUtils.get_user_folder_path(user_id)
            folder_hash = DocumentUtils.generate_user_folder_hash(user_id)
            
            metadata = DocumentUtils.load_user_metadata(user_id)
            
            return {
                "user_id": user_id,
                "folder_hash": folder_hash,
                "folder_path": str(folder_path.relative_to(DocumentUtils.BASE_DOCS_DIR)),
                "exists": folder_path.exists(),
                "created_at": metadata.get("created_at"),
                "document_count": len([d for d in metadata.get("documents", []) if d.get("is_active", True)])
            }
            
        except Exception as e:
            logger.error(f"Error getting folder info for user {user_id}: {str(e)}")
            return {"error": str(e)}
    
    async def _validate_upload(self, user_id: int, file: UploadFile) -> None:
        """
        Valida la subida de un archivo
        
        Args:
            user_id: ID del usuario
            file: Archivo a validar
            
        Raises:
            HTTPException: Si hay errores de validación
        """
        # Validar tipo de archivo
        if not DocumentUtils.is_allowed_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DocumentErrorResponses.INVALID_FILE_TYPE.dict()
            )
        
        # Validar cantidad de documentos
        metadata = DocumentUtils.load_user_metadata(user_id)
        active_docs = [d for d in metadata.get("documents", []) if d.get("is_active", True)]
        max_files = DocumentUtils.get_max_files_per_user()
        
        if not DocumentValidator.validate_document_count(len(active_docs), max_files):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DocumentErrorResponses.MAX_FILES_REACHED.dict()
            )
    
    async def _cleanup_missing_file(self, user_id: int, document_id: str) -> None:
        """
        Limpia el metadata de un archivo que no existe físicamente
        
        Args:
            user_id: ID del usuario
            document_id: ID del documento a limpiar
        """
        try:
            DocumentUtils.remove_document_from_metadata(user_id, document_id)
            logger.info(f"Cleaned up missing file reference: {document_id}")
        except Exception as e:
            logger.error(f"Error cleaning up missing file {document_id}: {str(e)}")
    
    async def cleanup_temp_files(self) -> Dict:
        """
        Limpia archivos temporales antiguos
        
        Returns:
            Dict: Resultado de la limpieza
        """
        try:
            temp_dir = DocumentUtils.TEMP_DIR
            if not temp_dir.exists():
                return {"message": "Temp directory does not exist"}
            
            cleaned_files = 0
            current_time = datetime.now()
            
            for temp_file in temp_dir.iterdir():
                if temp_file.is_file():
                    # Eliminar archivos más antiguos de 24 horas
                    file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    if (current_time - file_time).total_seconds() > 24 * 3600:
                        temp_file.unlink()
                        cleaned_files += 1
            
            logger.info(f"Cleaned {cleaned_files} temporary files")
            return {
                "cleaned_files": cleaned_files,
                "message": f"Limpiados {cleaned_files} archivos temporales"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning temp files: {str(e)}")
            return {"error": str(e)}