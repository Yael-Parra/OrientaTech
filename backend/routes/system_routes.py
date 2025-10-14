from fastapi import APIRouter
import os
from datetime import datetime
from backend.database.db_connection import connect_async, disconnect_async

# Router para endpoints del sistema
system_router = APIRouter(
    prefix="",
    tags=["🏥 Sistema"],
    responses={
        500: {"description": "Error interno del servidor"},
        503: {"description": "Servicio no disponible"}
    }
)
router = system_router

@system_router.get(
    "/",
    summary="Página de inicio de la API",
    description="Endpoint principal que confirma que la API está funcionando correctamente y proporciona información básica del servicio.",
    response_description="Mensaje de bienvenida y versión del servicio"
)
async def root():
    """
    Endpoint raíz de la API
    """
    return {
        "message": "🚀 Bienvenido a OrientaTech API",
        "service": "OrientaTech API",
        "version": "1.0.0",
        "description": "API completa de autenticación y gestión de usuarios",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "authentication": "/auth",
            "user_profile": "/profile", 
            "documents": "/documents",
            "github": "/github"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@system_router.get(
    "/health",
    summary="Verificación de salud del servicio", 
    description="Endpoint de verificación de salud del sistema con conexión real a la base de datos.",
    response_description="Estado de salud detallado del servicio y sus componentes"
)
async def health_check():
    """
    Verificar el estado de salud del servicio con conexión real a la base de datos
    """
    # Verificación de base de datos
    db_status = "disconnected"
    db_details = {}
    
    try:
        conn = await connect_async()
        if conn:
            # Hacer una consulta simple para verificar conectividad
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                # Obtener información adicional de la base de datos
                db_version = await conn.fetchval("SELECT version()")
                db_name = await conn.fetchval("SELECT current_database()")
                user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
                
                db_status = "connected"
                db_details = {
                    "name": db_name,
                    "version": db_version.split()[0:3] if db_version else "unknown",
                    "users_registered": user_count,
                    "connection_type": "async"
                }
            await disconnect_async(conn)
    except Exception as e:
        db_status = "error"
        db_details = {"error": str(e)}
    
    # Determinar estado general del sistema
    overall_status = "healthy" if db_status == "connected" else "degraded"
    
    return {
        "status": overall_status,
        "service": "OrientaTech API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": {
            "status": db_status,
            "details": db_details
        },
        "components": {
            "api": "operational",
            "authentication": "operational",
            "database": db_status,
            "file_storage": "operational"
        },
        "uptime": "running"
    }
