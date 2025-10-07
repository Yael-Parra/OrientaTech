"""
Validaciones avanzadas de seguridad para documentos
"""
import magic
import os
from pathlib import Path
from typing import List, Tuple, Dict
from fastapi import UploadFile, HTTPException, status
import hashlib

class SecurityValidator:
    """Validaciones avanzadas de seguridad para documentos"""
    
    # Extensiones permitidas y sus tipos MIME correspondientes
    ALLOWED_EXTENSIONS = {
        'pdf': ['application/pdf'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }
    
    # Firmas de archivos (magic numbers) para validación adicional
    FILE_SIGNATURES = {
        'pdf': [b'%PDF'],
        'doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],  # OLE Document
        'docx': [b'PK\x03\x04']  # ZIP (base de DOCX)
    }
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """
        Valida que la extensión del archivo esté permitida
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            bool: True si la extensión está permitida
        """
        if not filename or '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in SecurityValidator.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_mime_type(file_content: bytes, filename: str) -> bool:
        """
        Valida el tipo MIME del archivo comparando con la extensión
        
        Args:
            file_content: Contenido del archivo
            filename: Nombre del archivo
            
        Returns:
            bool: True si el MIME type coincide con la extensión
        """
        if not filename or '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        allowed_mimes = SecurityValidator.ALLOWED_EXTENSIONS.get(ext, [])
        
        if not allowed_mimes:
            return False
        
        try:
            # Intentar detectar MIME type usando python-magic si está disponible
            try:
                import magic
                detected_mime = magic.from_buffer(file_content, mime=True)
                return detected_mime in allowed_mimes
            except ImportError:
                # Si python-magic no está disponible, usar validación de firma
                return SecurityValidator._validate_file_signature(file_content, ext)
        except Exception:
            return False
    
    @staticmethod
    def _validate_file_signature(file_content: bytes, extension: str) -> bool:
        """
        Valida la firma del archivo (magic numbers)
        
        Args:
            file_content: Contenido del archivo
            extension: Extensión del archivo
            
        Returns:
            bool: True si la firma coincide con la extensión
        """
        signatures = SecurityValidator.FILE_SIGNATURES.get(extension, [])
        
        if not signatures:
            return True  # Si no hay firmas definidas, permitir
        
        for signature in signatures:
            if file_content.startswith(signature):
                return True
        
        return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitiza el nombre del archivo para prevenir ataques
        
        Args:
            filename: Nombre original del archivo
            
        Returns:
            str: Nombre sanitizado
        """
        import re
        
        if not filename:
            return "document.bin"
        
        # Separar nombre y extensión
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
        else:
            name, ext = filename, ''
        
        # Limpiar el nombre
        # Remover caracteres peligrosos
        name = re.sub(r'[^\w\s-]', '', name)
        # Reemplazar espacios y guiones múltiples con underscore
        name = re.sub(r'[-\s]+', '_', name)
        # Remover underscores al inicio y final
        name = name.strip('_')
        # Limitar longitud
        name = name[:50]
        
        # Si el nombre queda vacío, usar timestamp
        if not name:
            from datetime import datetime
            name = f"document_{int(datetime.now().timestamp())}"
        
        # Reconstruir filename
        if ext:
            return f"{name}.{ext.lower()}"
        return name
    
    @staticmethod
    def validate_file_size(size: int, max_size_mb: int = 5) -> bool:
        """
        Valida que el archivo no exceda el tamaño máximo
        
        Args:
            size: Tamaño del archivo en bytes
            max_size_mb: Tamaño máximo en MB
            
        Returns:
            bool: True si el tamaño es válido
        """
        max_bytes = max_size_mb * 1024 * 1024
        return 0 < size <= max_bytes
    
    @staticmethod
    def check_for_malicious_content(file_content: bytes) -> Dict[str, any]:
        """
        Realiza verificaciones básicas de contenido malicioso
        
        Args:
            file_content: Contenido del archivo
            
        Returns:
            Dict: Resultado de las verificaciones
        """
        checks = {
            "size_valid": len(file_content) > 0,
            "suspicious_patterns": [],
            "warnings": []
        }
        
        # Patrones sospechosos básicos
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'<%',  # ASP/JSP
            b'<?php',  # PHP
        ]
        
        for pattern in suspicious_patterns:
            if pattern in file_content.lower():
                checks["suspicious_patterns"].append(pattern.decode('utf-8', errors='ignore'))
        
        # Verificaciones adicionales
        if len(file_content) < 100:
            checks["warnings"].append("Archivo muy pequeño")
        
        if b'\x00' * 100 in file_content:
            checks["warnings"].append("Contiene muchos bytes nulos")
        
        return checks
    
    @staticmethod
    def generate_file_hash(file_content: bytes) -> str:
        """
        Genera un hash SHA256 del contenido del archivo
        
        Args:
            file_content: Contenido del archivo
            
        Returns:
            str: Hash SHA256 del archivo
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    async def validate_upload_file(file: UploadFile, max_size_mb: int = 5) -> Tuple[bool, str, bytes]:
        """
        Validación completa de un archivo subido
        
        Args:
            file: Archivo subido
            max_size_mb: Tamaño máximo permitido en MB
            
        Returns:
            Tuple[bool, str, bytes]: (válido, mensaje_error, contenido)
            
        Raises:
            HTTPException: Si el archivo no pasa las validaciones
        """
        try:
            # Leer contenido
            file_content = await file.read()
            
            # Validar tamaño
            if not SecurityValidator.validate_file_size(len(file_content), max_size_mb):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Archivo demasiado grande. Máximo permitido: {max_size_mb}MB"
                )
            
            # Validar extensión
            if not SecurityValidator.validate_file_extension(file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tipo de archivo no permitido. Solo se permiten: PDF, DOC, DOCX"
                )
            
            # Validar MIME type
            if not SecurityValidator.validate_mime_type(file_content, file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El contenido del archivo no coincide con su extensión"
                )
            
            # Verificar contenido malicioso
            security_check = SecurityValidator.check_for_malicious_content(file_content)
            
            if security_check["suspicious_patterns"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo contiene patrones sospechosos"
                )
            
            return True, "Validación exitosa", file_content
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validando archivo: {str(e)}"
            )
    
    @staticmethod
    def create_security_log(user_id: int, filename: str, action: str, result: str) -> Dict:
        """
        Crea un log de seguridad para auditoría
        
        Args:
            user_id: ID del usuario
            filename: Nombre del archivo
            action: Acción realizada
            result: Resultado de la acción
            
        Returns:
            Dict: Log de seguridad
        """
        from datetime import datetime
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "filename": filename,
            "action": action,
            "result": result,
            "ip_address": None,  # Se podría obtener del request
            "user_agent": None   # Se podría obtener del request
        }

class FileQuarantineManager:
    """Gestor de cuarentena para archivos sospechosos"""
    
    QUARANTINE_DIR = Path(__file__).parent.parent / "docs" / "quarantine"
    
    @staticmethod
    def quarantine_file(file_content: bytes, filename: str, reason: str) -> str:
        """
        Pone un archivo en cuarentena
        
        Args:
            file_content: Contenido del archivo
            filename: Nombre del archivo
            reason: Razón de la cuarentena
            
        Returns:
            str: ID de cuarentena
        """
        import uuid
        from datetime import datetime
        
        # Crear directorio de cuarentena si no existe
        FileQuarantineManager.QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generar ID único
        quarantine_id = str(uuid.uuid4())
        
        # Sanitizar nombre
        safe_filename = SecurityValidator.sanitize_filename(filename)
        
        # Guardar archivo
        quarantine_file_path = FileQuarantineManager.QUARANTINE_DIR / f"{quarantine_id}_{safe_filename}"
        
        with open(quarantine_file_path, 'wb') as f:
            f.write(file_content)
        
        # Guardar metadata de cuarentena
        metadata = {
            "quarantine_id": quarantine_id,
            "original_filename": filename,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "file_hash": SecurityValidator.generate_file_hash(file_content),
            "file_size": len(file_content)
        }
        
        metadata_path = FileQuarantineManager.QUARANTINE_DIR / f"{quarantine_id}_metadata.json"
        
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return quarantine_id
    
    @staticmethod
    def list_quarantined_files() -> List[Dict]:
        """
        Lista archivos en cuarentena
        
        Returns:
            List[Dict]: Lista de archivos en cuarentena
        """
        quarantined = []
        
        if not FileQuarantineManager.QUARANTINE_DIR.exists():
            return quarantined
        
        import json
        
        for metadata_file in FileQuarantineManager.QUARANTINE_DIR.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                quarantined.append(metadata)
            except Exception:
                continue
        
        return quarantined