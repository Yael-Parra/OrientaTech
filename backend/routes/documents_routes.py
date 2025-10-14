"""
Rutas para gestión de documentos de usuario
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import FileResponse
from typing import Annotated, Optional
import os

from backend.models.documents import (
    DocumentType, DocumentUploadResponse, UserDocumentsResponse,
    DocumentDeleteResponse, DocumentUploadRequest
)
from backend.services.document_service import DocumentService
from backend.routes.auth_simple import get_current_user

# Router para documentos con documentación mejorada
documents_router = APIRouter(
    prefix="/documents",
    tags=["📄 Documentos"],
    responses={
        401: {"description": "No autorizado - Token inválido o expirado"},
        403: {"description": "Acceso prohibido"},
        404: {"description": "Documento no encontrado"},
        413: {"description": "Archivo demasiado grande"},
        500: {"description": "Error interno del servidor"}
    }
)
router = documents_router

# Instancia del servicio
document_service = DocumentService()

@documents_router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="📤 Subir documento",
    description="""
    **Sube un nuevo documento para el usuario autenticado.**
    
    Este endpoint permite a los usuarios subir documentos como CVs, cartas de presentación, 
    certificados, etc. Cada usuario tiene una carpeta única y segura.
    
    ### 📋 Características:
    - **Carpeta única por usuario**: Hash SHA256 imposible de adivinar
    - **Tipos soportados**: PDF, DOC, DOCX
    - **Tamaño máximo**: 5MB por archivo
    - **Límite**: 10 documentos por usuario
    - **Seguridad**: Solo el propietario puede acceder
    
    ### 📁 Tipos de documentos:
    - **cv**: Curriculum Vitae
    - **cover_letter**: Carta de presentación  
    - **certificate**: Certificados
    - **other**: Otros documentos
    
    ### 🔐 Autenticación requerida:
    Debes estar autenticado para subir documentos.
    """,
    response_description="Información del documento subido exitosamente"
)
async def upload_document(
    file: Annotated[
        UploadFile, 
        File(
            description="Archivo a subir (PDF, DOC, DOCX - máx 5MB)",
            example="mi_cv_2024.pdf"
        )
    ],
    document_type: Annotated[
        DocumentType,
        Form(
            description="Tipo de documento que estás subiendo"
        )
    ] = DocumentType.CV,
    description: Annotated[
        Optional[str],
        Form(
            description="Descripción opcional del documento",
            max_length=500
        )
    ] = None,
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ] = None
):
    """
    Subir un nuevo documento
    """
    return await document_service.upload_document(
        user_id=current_user["id"],
        file=file,
        document_type=document_type,
        description=description
    )

@documents_router.get(
    "/my-documents",
    response_model=UserDocumentsResponse,
    summary="📋 Listar mis documentos",
    description="""
    **Obtiene la lista completa de documentos del usuario autenticado.**
    
    Este endpoint retorna todos los documentos que has subido, junto con:
    
    ### 📊 Información incluida:
    - **Lista de documentos**: Con detalles completos de cada uno
    - **Estadísticas**: Total de archivos y espacio usado
    - **Límites**: Espacios disponibles y restricciones
    - **Metadatos**: Fechas, tamaños, tipos MIME
    
    ### 📁 Datos por documento:
    - ID único del documento
    - Nombre original y nombre almacenado
    - Tipo de documento (CV, carta, certificado)
    - Tamaño en bytes y MB
    - Fecha de subida
    - Estado (activo/inactivo)
    
    ### 🔐 Seguridad:
    Solo puedes ver tus propios documentos.
    """,
    response_description="Lista completa de documentos del usuario"
)
async def get_my_documents(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ]
):
    """
    Obtener lista de documentos del usuario actual
    """
    return await document_service.get_user_documents(current_user["id"])

@documents_router.get(
    "/download/{document_id}",
    summary="📥 Descargar documento",
    description="""
    **Descarga un documento específico del usuario autenticado.**
    
    Este endpoint permite descargar documentos que has subido previamente.
    
    ### 🔐 Seguridad:
    - Solo puedes descargar **tus propios documentos**
    - El sistema verifica que el documento te pertenece
    - URLs de descarga no son adivinables
    
    ### 📁 Funcionamiento:
    1. Verifica que el documento existe
    2. Confirma que te pertenece
    3. Sirve el archivo con el nombre original
    4. Incluye headers apropiados para descarga
    
    ### 📋 Headers de respuesta:
    - `Content-Type`: Tipo MIME del archivo
    - `Content-Disposition`: Nombre original del archivo
    - `Content-Length`: Tamaño del archivo
    """,
    response_description="Archivo descargado",
    responses={
        200: {
            "description": "Archivo descargado exitosamente",
            "content": {
                "application/pdf": {},
                "application/msword": {},
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}
            }
        }
    }
)
async def download_document(
    document_id: Annotated[
        str,
        "ID único del documento a descargar"
    ],
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ]
):
    """
    Descargar un documento específico
    """
    file_path, original_name, mime_type = await document_service.download_document(
        user_id=current_user["id"],
        document_id=document_id
    )
    
    return FileResponse(
        path=file_path,
        filename=original_name,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{original_name}\""
        }
    )

@documents_router.delete(
    "/delete/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="🗑️ Eliminar documento",
    description="""
    **Elimina permanentemente un documento del usuario autenticado.**
    
    ⚠️ **ATENCIÓN: Esta acción es irreversible**
    
    ### 🗑️ Proceso de eliminación:
    1. Verifica que el documento existe
    2. Confirma que te pertenece
    3. Elimina el archivo físico del servidor
    4. Remueve la entrada del metadata
    5. Libera espacio en tu cuota
    
    ### 🔐 Seguridad:
    - Solo puedes eliminar **tus propios documentos**
    - Validación de propietario antes de eliminar
    - Logs de auditoría para seguimiento
    
    ### 📊 Efectos:
    - **Espacio liberado**: Se suma a tu cuota disponible
    - **Contador reducido**: Espacio para más documentos
    - **Irreversible**: No hay papelera de reciclaje
    """,
    response_description="Confirmación de eliminación"
)
async def delete_document(
    document_id: Annotated[
        str,
        "ID único del documento a eliminar"
    ],
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ]
):
    """
    Eliminar un documento específico
    """
    return await document_service.delete_document(
        user_id=current_user["id"],
        document_id=document_id
    )

@documents_router.get(
    "/folder-info",
    summary="📁 Información de carpeta",
    description="""
    **Obtiene información detallada de la carpeta de documentos del usuario.**
    
    Este endpoint es útil para debugging y proporciona información técnica
    sobre la carpeta de almacenamiento del usuario.
    
    ### 📊 Información incluida:
    - **Hash único**: Identificador de la carpeta
    - **Ruta relativa**: Ubicación en el servidor
    - **Estado**: Si la carpeta existe
    - **Fechas**: Creación y último acceso
    - **Estadísticas**: Número de documentos
    
    ### 🔧 Uso técnico:
    - Debugging de problemas de almacenamiento
    - Verificación de integridad
    - Auditoría de uso de espacio
    """,
    response_description="Información técnica de la carpeta"
)
async def get_folder_info(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ]
):
    """
    Obtener información de la carpeta del usuario
    """
    return await document_service.get_folder_info(current_user["id"])

@documents_router.post(
    "/cleanup-temp",
    summary="🧹 Limpiar archivos temporales",
    description="""
    **Endpoint administrativo para limpiar archivos temporales.**
    
    ⚠️ **Solo para administradores o tareas de mantenimiento**
    
    ### 🧹 Proceso de limpieza:
    - Elimina archivos temporales más antiguos de 24 horas
    - Libera espacio en el directorio temporal
    - Retorna estadísticas de limpieza
    
    ### 📊 Información retornada:
    - Número de archivos eliminados
    - Espacio liberado
    - Timestamp de la operación
    """,
    response_description="Resultado de la limpieza"
)
async def cleanup_temp_files(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ]
):
    """
    Limpiar archivos temporales (solo para administradores)
    """
    # En el futuro se podría añadir verificación de rol admin
    return await document_service.cleanup_temp_files()

@documents_router.get(
    "/stats",
    summary="📊 Estadísticas de documentos",
    description="""
    **Obtiene estadísticas personalizadas de uso de documentos.**
    
    Este endpoint proporciona métricas útiles sobre el uso de documentos:
    
    ### 📈 Métricas incluidas:
    - **Uso de espacio**: Total y por tipo de documento
    - **Distribución**: Tipos de documentos más comunes
    - **Actividad**: Documentos subidos por mes
    - **Límites**: Cuotas usadas vs disponibles
    
    ### 📊 Datos útiles para:
    - Panel de control personal
    - Optimización de espacio
    - Planificación de subidas
    """,
    response_description="Estadísticas detalladas de uso"
)
async def get_document_stats(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ]
):
    """
    Obtener estadísticas de documentos del usuario
    """
    # Obtener documentos del usuario
    documents_response = await document_service.get_user_documents(current_user["id"])
    
    # Calcular estadísticas
    stats = {
        "user_id": current_user["id"],
        "total_documents": documents_response.total_documents,
        "total_size_mb": documents_response.total_size_mb,
        "remaining_slots": documents_response.remaining_slots,
        "usage_percentage": round(
            (documents_response.total_documents / documents_response.max_files_allowed) * 100, 2
        ),
        "documents_by_type": {},
        "average_file_size_mb": 0,
        "largest_file_mb": 0,
        "oldest_document": None,
        "newest_document": None
    }
    
    if documents_response.documents:
        # Estadísticas por tipo
        for doc in documents_response.documents:
            doc_type = doc.type.value
            if doc_type not in stats["documents_by_type"]:
                stats["documents_by_type"][doc_type] = {"count": 0, "size_mb": 0}
            stats["documents_by_type"][doc_type]["count"] += 1
            stats["documents_by_type"][doc_type]["size_mb"] += doc.size_mb
        
        # Tamaño promedio y máximo
        total_size = sum(doc.size for doc in documents_response.documents)
        stats["average_file_size_mb"] = round(
            total_size / len(documents_response.documents) / (1024 * 1024), 2
        )
        stats["largest_file_mb"] = max(doc.size_mb for doc in documents_response.documents)
        
        # Documentos más antiguo y más nuevo
        sorted_docs = sorted(documents_response.documents, key=lambda x: x.uploaded_at)
        stats["oldest_document"] = {
            "filename": sorted_docs[0].original_name,
            "uploaded_at": sorted_docs[0].uploaded_at.isoformat() + "Z",
            "type": sorted_docs[0].type.value
        }
        stats["newest_document"] = {
            "filename": sorted_docs[-1].original_name,
            "uploaded_at": sorted_docs[-1].uploaded_at.isoformat() + "Z",
            "type": sorted_docs[-1].type.value
        }
    
    return stats