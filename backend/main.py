from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routes.auth_simple import auth_router

# Cargar variables de entorno
load_dotenv()

# Configuración CORS
CORS_ORIGINS = eval(os.getenv("CORS_ORIGINS", '["*"]'))

# Crear aplicación FastAPI
app = FastAPI(
    title="OrientaTech API",
    description="API de autenticación para OrientaTech",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Endpoint de salud
@app.get("/")
async def root():
    return {"message": "OrientaTech API está funcionando", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OrientaTech API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)