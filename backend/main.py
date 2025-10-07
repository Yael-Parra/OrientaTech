from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from loguru import logger
from contextlib import asynccontextmanager

from routes.auth_simple import auth_router
from routes.github_routes import github_router
from routes.documents_routes import documents_router
from services.setup_service import setup_service

# Cargar variables de entorno
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configuración automática al iniciar la aplicación"""
    # Startup - Configuración automática
    logger.info("🚀 Iniciando OrientaTech API...")
    
    # Verificar si se necesita configuración
    if setup_service.is_setup_required():
        logger.info("⚙️ Ejecutando configuración automática...")
        try:
            results = setup_service.run_full_setup()
            if all(results.values()):
                logger.success("✅ Configuración completada")
            else:
                logger.warning("⚠️ Configuración parcial - algunos servicios pueden fallar")
        except Exception as e:
            logger.error(f"❌ Error en configuración: {e}")
            logger.warning("⚠️ Continuando sin configuración completa")
    else:
        logger.info("✅ Sistema ya configurado")
    
    yield
    
    # Shutdown
    logger.info("🔄 Cerrando aplicación")

# Configuración CORS
try:
    CORS_ORIGINS = eval(os.getenv("CORS_ORIGINS", '["*"]'))
except:
    CORS_ORIGINS = ["*"]


# Crear aplicación FastAPI con configuración automática
app = FastAPI(
    title="🚀 OrientaTech API",
    description="""
    **API completa de autenticación y gestión de usuarios para OrientaTech**
    
    🔧 **Auto-configuración**: Se configura automáticamente al iniciar.
     """,
    version="1.0.0",
    lifespan=lifespan,
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "🔐 Autenticación",
            "description": "Operaciones de autenticación y gestión de usuarios. Incluye registro, login, gestión de tokens y perfiles de usuario.",
        },
        {
            "name": "📄 Documentos",
            "description": "Gestión de documentos de usuario. Subida, descarga, listado y eliminación de CVs, cartas de presentación y certificados con almacenamiento seguro.",
        },
        {
            "name": "👥 GitHub",
            "description": "Integración con GitHub API para obtener información del equipo y contribuidores del proyecto en tiempo real.",
        },
        {
            "name": "🏥 Sistema",
            "description": "Endpoints de monitoreo y estado del sistema.",
        }
    ]
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router)
app.include_router(github_router)
app.include_router(documents_router)

# Endpoint de salud
@app.get(
    "/",
    tags=["🏥 Sistema"],
    summary="Página de inicio de la API",
    description="Endpoint principal que confirma que la API está funcionando correctamente y proporciona información básica del servicio.",
    response_description="Mensaje de bienvenida y versión del servicio"
)


@app.get(
    "/health",
    tags=["🏥 Sistema"],
    summary="Verificación de salud del servicio",
    description="""

   ***Endpoint de verificación de salud del sistema.***
    
    """,
    response_description="Estado de salud del servicio"
)
async def health_check():
    """
    Verificar el estado de salud del servicio
    """
    from datetime import datetime
    
    return {
        "status": "healthy",
        "service": "OrientaTech API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "connected",  # Aquí podrías agregar un check real de la DB
        "uptime": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)