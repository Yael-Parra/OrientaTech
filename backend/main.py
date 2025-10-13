from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from loguru import logger
from contextlib import asynccontextmanager

from routes.auth_simple import auth_router
from routes.github_routes import github_router
from routes.documents_routes import documents_router
from routes.user_profile_routes import profile_router
from routes.system_routes import system_router
from routes.reviews_routes import reviews_router
from routes.employment_platforms_routes import platforms_router
from routes.rag_routes import rag_router
from services.setup_service import setup_service
from pathlib import Path

# Cargar variables de entorno desde backend/.env
load_dotenv(dotenv_path=Path(__file__).parent / '.env')


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
            "name": "🏥 Sistema",
            "description": "Endpoints de sistema, salud, información y monitoreo de la API.",
        },
        {
            "name": "🔐 Autenticación",
            "description": "Operaciones de autenticación y gestión de usuarios. Incluye registro, login, gestión de tokens y perfiles de usuario.",
        },
        {
            "name": "👤 Perfil de Usuario",
            "description": "Gestión completa del perfil personal del usuario. CRUD de información personal, educación, experiencia y habilidades con autenticación JWT.",
        },
        {
            "name": "📄 Documentos",
            "description": "Gestión de documentos de usuario. Subida, descarga, listado y eliminación de CVs, cartas de presentación y certificados con almacenamiento seguro.",
        },
        {
            "name": "🐙 GitHub Integration",
            "description": "Integración con GitHub API para obtener información del equipo y contribuidores del proyecto en tiempo real.",
        },
        {
            "name": "⭐ Reviews (Reseñas)",
            "description": "Sistema completo de reseñas de plataformas de empleo. CRUD con autenticación JWT, estadísticas y relaciones con plataformas laborales.",
        },
        {
            "name": "💼 Employment Platforms",
            "description": "Gestión de plataformas de empleo. Consulta, creación y estadísticas de plataformas laborales con filtros avanzados.",
        },
        {
            "name": "🔍 RAG Search",
            "description": "Sistema de búsqueda semántica con IA. Búsqueda inteligente de documentos usando embeddings vectoriales y similitud semántica.",
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
app.include_router(system_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(documents_router)
app.include_router(platforms_router)
app.include_router(reviews_router)
app.include_router(github_router)
app.include_router(rag_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)