"""
Utilidades para gestión de documentos de usuario
"""
import hashlib
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class DocumentUtils:
    """Utilidades para gestión de documentos de usuarios"""
    
    BASE_DOCS_DIR = Path(__file__).parent.parent / "docs"
    USERS_DIR = BASE_DOCS_DIR / "users" 
    TEMP_DIR = BASE_DOCS_DIR / "temp"
    
    @staticmethod
    def generate_user_folder_hash(user_id: int) -> str:
        """
        Genera un hash único para la carpeta del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            str: Hash único de 16 caracteres para la carpeta
        """
        salt = os.getenv("USER_FOLDER_SALT", "OrientaTech_Default_Salt")
        raw_string = f"{user_id}_{salt}"
        hash_object = hashlib.sha256(raw_string.encode())
        return hash_object.hexdigest()[:16]  # Solo primeros 16 caracteres
    
    @staticmethod
    def get_user_folder_path(user_id: int) -> Path:
        """
        Obtiene la ruta de la carpeta del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Path: Ruta completa a la carpeta del usuario
        """
        folder_hash = DocumentUtils.generate_user_folder_hash(user_id)
        return DocumentUtils.USERS_DIR / folder_hash
    
    @staticmethod
    def ensure_user_folder_exists(user_id: int) -> Path:
        """
        Asegura que la carpeta del usuario existe, la crea si no
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Path: Ruta a la carpeta del usuario
        """
        folder_path = DocumentUtils.get_user_folder_path(user_id)
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path
    
    @staticmethod
    def get_metadata_file_path(user_id: int) -> Path:
        """
        Obtiene la ruta del archivo metadata.json del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Path: Ruta al archivo metadata.json
        """
        folder_path = DocumentUtils.get_user_folder_path(user_id)
        return folder_path / "metadata.json"
    
    @staticmethod
    def load_user_metadata(user_id: int) -> Dict:
        """
        Carga el metadata del usuario desde el archivo JSON
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict: Metadata del usuario, dict vacío si no existe
        """
        metadata_path = DocumentUtils.get_metadata_file_path(user_id)
        
        if not metadata_path.exists():
            # Crear metadata inicial si no existe
            initial_metadata = {
                "user_id": user_id,
                "folder_hash": DocumentUtils.generate_user_folder_hash(user_id),
                "created_at": datetime.utcnow().isoformat() + "Z",
                "documents": []
            }
            DocumentUtils.save_user_metadata(user_id, initial_metadata)
            return initial_metadata
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Si el archivo está corrupto, regenerar
            return DocumentUtils._regenerate_metadata_from_files(user_id)
    
    @staticmethod
    def save_user_metadata(user_id: int, metadata: Dict) -> None:
        """
        Guarda el metadata del usuario en el archivo JSON
        
        Args:
            user_id: ID del usuario
            metadata: Diccionario con el metadata a guardar
        """
        # Asegurar que la carpeta existe
        folder_path = DocumentUtils.ensure_user_folder_exists(user_id)
        metadata_path = folder_path / "metadata.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def add_document_to_metadata(user_id: int, doc_info: Dict) -> None:
        """
        Añade información de un documento al metadata del usuario
        
        Args:
            user_id: ID del usuario
            doc_info: Información del documento
        """
        metadata = DocumentUtils.load_user_metadata(user_id)
        metadata["documents"].append(doc_info)
        DocumentUtils.save_user_metadata(user_id, metadata)
    
    @staticmethod
    def remove_document_from_metadata(user_id: int, doc_id: str) -> bool:
        """
        Elimina un documento del metadata del usuario
        
        Args:
            user_id: ID del usuario
            doc_id: ID del documento a eliminar
            
        Returns:
            bool: True si se eliminó, False si no se encontró
        """
        metadata = DocumentUtils.load_user_metadata(user_id)
        original_count = len(metadata["documents"])
        
        metadata["documents"] = [
            doc for doc in metadata["documents"] 
            if doc.get("id") != doc_id
        ]
        
        if len(metadata["documents"]) < original_count:
            DocumentUtils.save_user_metadata(user_id, metadata)
            return True
        return False
    
    @staticmethod
    def _regenerate_metadata_from_files(user_id: int) -> Dict:
        """
        Regenera el metadata leyendo los archivos físicos de la carpeta
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict: Metadata regenerado
        """
        folder_path = DocumentUtils.get_user_folder_path(user_id)
        
        metadata = {
            "user_id": user_id,
            "folder_hash": DocumentUtils.generate_user_folder_hash(user_id),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "documents": []
        }
        
        if folder_path.exists():
            # Buscar archivos que no sean metadata.json
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.name != "metadata.json":
                    # Generar info básica del archivo
                    doc_info = {
                        "id": str(uuid.uuid4()),
                        "filename": file_path.name,
                        "original_name": file_path.name,
                        "type": "unknown",
                        "size": file_path.stat().st_size,
                        "mime_type": "application/octet-stream",
                        "uploaded_at": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat() + "Z",
                        "is_active": True
                    }
                    metadata["documents"].append(doc_info)
        
        DocumentUtils.save_user_metadata(user_id, metadata)
        return metadata
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitiza un nombre de archivo para hacerlo seguro
        
        Args:
            filename: Nombre original del archivo
            
        Returns:
            str: Nombre sanitizado
        """
        # Remover caracteres peligrosos
        import re
        
        # Obtener extensión
        name, ext = os.path.splitext(filename)
        
        # Limpiar nombre
        clean_name = re.sub(r'[^\w\s-]', '', name)
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        clean_name = clean_name.strip('_')[:50]  # Máximo 50 caracteres
        
        # Si queda vacío, usar timestamp
        if not clean_name:
            clean_name = f"document_{int(datetime.now().timestamp())}"
        
        return f"{clean_name}{ext.lower()}"
    
    @staticmethod
    def generate_unique_filename(user_id: int, original_filename: str) -> str:
        """
        Genera un nombre único para el archivo en la carpeta del usuario
        
        Args:
            user_id: ID del usuario
            original_filename: Nombre original del archivo
            
        Returns:
            str: Nombre único para el archivo
        """
        sanitized = DocumentUtils.sanitize_filename(original_filename)
        folder_path = DocumentUtils.get_user_folder_path(user_id)
        
        # Si no existe conflicto, usar el nombre sanitizado
        if not (folder_path / sanitized).exists():
            return sanitized
        
        # Si existe, añadir timestamp
        name, ext = os.path.splitext(sanitized)
        timestamp = int(datetime.now().timestamp())
        return f"{name}_{timestamp}{ext}"
    
    @staticmethod
    def get_file_mime_type(filename: str) -> str:
        """
        Obtiene el tipo MIME basado en la extensión del archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            str: Tipo MIME
        """
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    @staticmethod
    def is_allowed_file_type(filename: str) -> bool:
        """
        Verifica si el tipo de archivo está permitido
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            bool: True si está permitido
        """
        allowed_types = os.getenv("ALLOWED_FILE_TYPES", "pdf,doc,docx").split(",")
        ext = os.path.splitext(filename)[1][1:].lower()  # Sin el punto
        return ext in allowed_types
    
    @staticmethod
    def get_max_file_size() -> int:
        """
        Obtiene el tamaño máximo permitido para archivos en bytes
        
        Returns:
            int: Tamaño máximo en bytes
        """
        max_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
        return max_size_mb * 1024 * 1024  # Convertir a bytes
    
    @staticmethod
    def get_max_files_per_user() -> int:
        """
        Obtiene el número máximo de archivos por usuario
        
        Returns:
            int: Número máximo de archivos
        """
        return int(os.getenv("MAX_FILES_PER_USER", "10"))