from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from typing import Optional
import asyncpg
import os
from dotenv import load_dotenv

from models import UserRegister, UserLogin, UserResponse, Token
from services import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Import the unified database connection
from database.db_connection import connect_async, disconnect_async

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuración de seguridad
security = HTTPBearer()

# Router para autenticación
auth_router = APIRouter(prefix="/auth", tags=["Autenticación"])

async def get_db_connection():
    """Obtener conexión a la base de datos usando la función unificada"""
    return await connect_async()

async def get_user_by_email(email: str) -> Optional[dict]:
    """Obtener usuario por email"""
    conn = await get_db_connection()
    try:
        query = "SELECT id, email, password_hash, created_at, is_active FROM users WHERE email = $1"
        user = await conn.fetchrow(query, email)
        return dict(user) if user else None
    finally:
        await conn.close()

async def create_user(email: str, password_hash: str) -> dict:
    """Crear nuevo usuario"""
    conn = await get_db_connection()
    try:
        query = """
            INSERT INTO users (email, password_hash, created_at, is_active) 
            VALUES ($1, $2, NOW(), true) 
            RETURNING id, email, created_at, is_active
        """
        user = await conn.fetchrow(query, email, password_hash)
        return dict(user)
    finally:
        await conn.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Middleware para obtener usuario actual desde JWT"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    user = await get_user_by_email(token_data["email"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Registrar un nuevo usuario
    
    - **email**: Email del usuario (debe ser único)
    - **password**: Contraseña del usuario
    """
    # Verificar si el usuario ya existe
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Encriptar contraseña
    hashed_password = get_password_hash(user_data.password)
    
    # Crear usuario
    try:
        new_user = await create_user(user_data.email, hashed_password)
        return UserResponse(**new_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )

@auth_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """
    Iniciar sesión y obtener token JWT
    
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    """
    # Verificar que el usuario existe
    user = await get_user_by_email(user_credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # en segundos
    )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Obtener información del usuario actual autenticado
    
    Requiere token JWT válido en el header Authorization: Bearer <token>
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        created_at=current_user["created_at"],
        is_active=current_user["is_active"]
    )

@auth_router.post("/logout")
async def logout():
    """
    Cerrar sesión
    
    Nota: Con JWT, el logout es manejado del lado del cliente eliminando el token.
    Este endpoint existe para consistencia con APIs REST estándar.
    """
    return {"message": "Sesión cerrada exitosamente"}

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """
    Renovar token JWT
    
    Requiere token JWT válido en el header Authorization: Bearer <token>
    """
    # Crear nuevo token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["email"], "user_id": current_user["id"]},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )