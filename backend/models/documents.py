"""
Modelos Pydantic para gestión de documentos de usuario
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    """Tipos de documentos permitidos"""
    CV = "cv"
    COVER_LETTER = "cover_letter"
    CERTIFICATE = "certificate"
    OTHER = "other"

class DocumentUploadResponse(BaseModel):
    """Respuesta después de subir un documento"""
    success: bool = Field(
        ...,
        description="Indica si la subida fue exitosa"
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo del resultado"
    )
    document_id: Optional[str] = Field(
        None,
        description="ID único del documento subido"
    )
    filename: Optional[str] = Field(
        None,
        description="Nombre final del archivo"
    )
    size: Optional[int] = Field(
        None,
        description="Tamaño del archivo en bytes"
    )

class DocumentInfo(BaseModel):
    """Información detallada de un documento"""
    id: str = Field(
        ...,
        description="ID único del documento",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    filename: str = Field(
        ...,
        description="Nombre del archivo almacenado",
        example="cv_actualizado_2024.pdf"
    )
    original_name: str = Field(
        ...,
        description="Nombre original del archivo subido",
        example="Mi CV Actualizado 2024.pdf"
    )
    type: DocumentType = Field(
        ...,
        description="Tipo de documento",
        example=DocumentType.CV
    )
    size: int = Field(
        ...,
        description="Tamaño del archivo en bytes",
        example=1048576
    )
    mime_type: str = Field(
        ...,
        description="Tipo MIME del archivo",
        example="application/pdf"
    )
    uploaded_at: datetime = Field(
        ...,
        description="Fecha y hora de subida",
        example="2024-10-06T10:00:00Z"
    )
    is_active: bool = Field(
        default=True,
        description="Indica si el documento está activo"
    )
    
    @property
    def size_mb(self) -> float:
        """Tamaño del archivo en MB"""
        return round(self.size / (1024 * 1024), 2)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

class UserDocumentsResponse(BaseModel):
    """Respuesta con todos los documentos de un usuario"""
    user_id: int = Field(
        ...,
        description="ID del usuario"
    )
    total_documents: int = Field(
        ...,
        description="Número total de documentos"
    )
    total_size_mb: float = Field(
        ...,
        description="Tamaño total en MB"
    )
    max_files_allowed: int = Field(
        ...,
        description="Número máximo de archivos permitidos"
    )
    max_size_mb_per_file: int = Field(
        ...,
        description="Tamaño máximo por archivo en MB"
    )
    documents: List[DocumentInfo] = Field(
        default=[],
        description="Lista de documentos del usuario"
    )
    
    @property
    def remaining_slots(self) -> int:
        """Espacios disponibles para más documentos"""
        return max(0, self.max_files_allowed - self.total_documents)
    
    @property
    def is_full(self) -> bool:
        """Indica si el usuario ha alcanzado el límite de documentos"""
        return self.total_documents >= self.max_files_allowed

class DocumentDeleteResponse(BaseModel):
    """Respuesta después de eliminar un documento"""
    success: bool = Field(
        ...,
        description="Indica si la eliminación fue exitosa"
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo del resultado"
    )
    document_id: Optional[str] = Field(
        None,
        description="ID del documento eliminado"
    )

class DocumentValidationError(BaseModel):
    """Error de validación de documento"""
    error: str = Field(
        ...,
        description="Tipo de error"
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo del error"
    )
    details: Optional[dict] = Field(
        None,
        description="Detalles adicionales del error"
    )

class DocumentUploadRequest(BaseModel):
    """Modelo para validar la subida de documentos"""
    document_type: DocumentType = Field(
        default=DocumentType.CV,
        description="Tipo de documento que se está subiendo"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción opcional del documento"
    )
    
    class Config:
        example = {
            "document_type": "cv",
            "description": "Mi CV actualizado con experiencia más reciente"
        }

class UserFolderInfo(BaseModel):
    """Información de la carpeta del usuario"""
    user_id: int = Field(
        ...,
        description="ID del usuario"
    )
    folder_hash: str = Field(
        ...,
        description="Hash único de la carpeta",
        example="a1b2c3d4e5f6g7h8"
    )
    folder_path: str = Field(
        ...,
        description="Ruta relativa de la carpeta"
    )
    created_at: datetime = Field(
        ...,
        description="Fecha de creación de la carpeta"
    )
    last_accessed: Optional[datetime] = Field(
        None,
        description="Última vez que se accedió a la carpeta"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

# Validadores personalizados
class DocumentValidator:
    """Validadores para documentos"""
    
    @staticmethod
    def validate_file_size(size: int, max_size_mb: int = 5) -> bool:
        """Valida que el archivo no exceda el tamaño máximo"""
        max_bytes = max_size_mb * 1024 * 1024
        return size <= max_bytes
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str] = None) -> bool:
        """Valida que el tipo de archivo esté permitido"""
        if allowed_types is None:
            allowed_types = ["pdf", "doc", "docx"]
        
        import os
        ext = os.path.splitext(filename)[1][1:].lower()
        return ext in allowed_types
    
    @staticmethod
    def validate_document_count(current_count: int, max_count: int = 10) -> bool:
        """Valida que no se exceda el número máximo de documentos"""
        return current_count < max_count

# Respuestas de error estándar
class DocumentErrorResponses:
    """Respuestas de error estándar para documentos"""
    
    FILE_TOO_LARGE = DocumentValidationError(
        error="file_too_large",
        message="El archivo excede el tamaño máximo permitido",
        details={"max_size_mb": 5}
    )
    
    INVALID_FILE_TYPE = DocumentValidationError(
        error="invalid_file_type",
        message="Tipo de archivo no permitido",
        details={"allowed_types": ["pdf", "doc", "docx"]}
    )
    
    MAX_FILES_REACHED = DocumentValidationError(
        error="max_files_reached",
        message="Has alcanzado el número máximo de documentos permitidos",
        details={"max_files": 10}
    )
    
    FILE_NOT_FOUND = DocumentValidationError(
        error="file_not_found",
        message="El documento solicitado no existe"
    )
    
    ACCESS_DENIED = DocumentValidationError(
        error="access_denied",
        message="No tienes permisos para acceder a este documento"
    )
    
    UPLOAD_FAILED = DocumentValidationError(
        error="upload_failed",
        message="Error al subir el archivo"
    )
    
    DELETE_FAILED = DocumentValidationError(
        error="delete_failed",
        message="Error al eliminar el documento"
    )