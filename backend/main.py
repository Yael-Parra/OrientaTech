"""
OrientaTech - Backend API
Sistema de orientación profesional hacia el sector tecnológico
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from loguru import logger

# Import routes
from routes.system_routes import router as system_router
from routes.auth_simple import router as auth_router
from routes.user_profile_routes import router as user_profile_router
from routes.documents_routes import router as documents_router
from routes.employment_platforms_routes import router as employment_platforms_router
from routes.reviews_routes import router as reviews_router
from routes.github_routes import router as github_router
from routes.cv_analysis_routes import router as cv_analysis_router  # New CV analysis routes

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="OrientaTech API",
    description="API para sistema de orientación profesional hacia el sector tecnológico con análisis de CV y IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", '["*"]')
try:
    import json
    origins = json.loads(cors_origins)
except:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system_router)
app.include_router(auth_router)
app.include_router(user_profile_router)
app.include_router(documents_router)
app.include_router(employment_platforms_router)
app.include_router(reviews_router)
app.include_router(github_router)
app.include_router(cv_analysis_router)  # Include CV analysis routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OrientaTech API - Sistema de orientación profesional hacia el sector tecnológico",
        "version": "1.0.0",
        "features": [
            "Autenticación de usuarios",
            "Gestión de perfiles profesionales", 
            "Análisis de CV con IA",
            "Recomendaciones personalizadas de carrera",
            "Plataformas de empleo tecnológico",
            "Sistema de reseñas",
            "Integración con GitHub"
        ],
        "docs": "/docs"
    }

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint no encontrado", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Error interno del servidor"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )