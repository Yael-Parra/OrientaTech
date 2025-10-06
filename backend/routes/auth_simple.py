from fastapi import APIRouter, HTTPException, status, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional, Annotated
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

# Configuración de seguridad para documentación interactiva
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",  # Este será nuestro endpoint para el login desde docs
    scheme_name="OAuth2 Password Flow"
)

# Configuración de seguridad alternativa para headers manuales
security = HTTPBearer(
    scheme_name="Bearer Token",
    description="JWT Bearer token para autenticación manual"
)

# Router para autenticación con documentación mejorada
auth_router = APIRouter(
    prefix="/auth", 
    tags=["🔐 Autenticación"],
    responses={
        401: {"description": "No autorizado - Token inválido o expirado"},
        403: {"description": "Acceso prohibido"},
        500: {"description": "Error interno del servidor"}
    }
)

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

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    Middleware para obtener usuario actual desde JWT (OAuth2)
    
    Valida el token JWT y retorna la información del usuario autenticado.
    Lanza HTTPException si el token es inválido o el usuario no existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(token)
        if token_data is None:
            raise credentials_exception
            
        user = await get_user_by_email(token_data["email"])
        if user is None:
            raise credentials_exception
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except Exception as e:
        raise credentials_exception

async def get_current_user_manual(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
        "Credenciales Bearer token del header Authorization"
    ]
) -> dict:
    """
    Middleware alternativo para obtener usuario actual desde JWT (Bearer manual)
    
    Para uso cuando se prefiera usar headers manuales en lugar de OAuth2
    """
    try:
        token = credentials.credentials
        token_data = verify_token(token)
        
        user = await get_user_by_email(token_data["email"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

@auth_router.get(
    "/status",
    summary="Estado del servicio de autenticación",
    description="""
    **Verificar el estado y configuración del servicio de autenticación.**
    
    Este endpoint público proporciona información sobre el estado del servicio de autenticación y su configuración básica.
    
    ### Información retornada:
    - Estado del servicio (online/offline)
    - Configuración de expiración de tokens
    - Versión del servicio
    - Timestamp del servidor
    
    ### Casos de uso:
    - Verificar conectividad con el servicio de auth
    - Obtener configuración para clientes
    - Monitoreo del estado del servicio
    """,
    response_description="Estado y configuración del servicio de autenticación",
    responses={
        200: {
            "description": "Estado del servicio obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "online",
                        "service": "OrientaTech Auth Service",
                        "version": "1.0.0",
                        "token_expire_minutes": 30,
                        "timestamp": "2024-10-06T10:00:00Z"
                    }
                }
            }
        }
    }
)
async def auth_status():
    """
    Obtener estado del servicio de autenticación
    """
    from datetime import datetime
    
    return {
        "status": "online",
        "service": "OrientaTech Auth Service", 
        "version": "1.0.0",
        "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "endpoints": {
            "register": "/auth/register",
            "login": "/auth/login",
            "token": "/auth/token (para Swagger UI)",
            "logout": "/auth/logout",
            "me": "/auth/me",
            "refresh": "/auth/refresh",
            "status": "/auth/status"
        }
    }

@auth_router.post(
    "/token",
    response_model=Token,
    summary="🔑 Login para Swagger UI",
    description="""
    **Endpoint especial para autenticación desde la documentación interactiva.**
    
    Este endpoint utiliza el formulario estándar OAuth2 que aparece en Swagger UI.
    Permite hacer login directamente desde la documentación con email y contraseña.
    
    ### Uso en Swagger UI:
    1. Haz clic en el botón "Authorize" en la esquina superior derecha
    2. Ingresa tu email en el campo "username" 
    3. Ingresa tu contraseña en el campo "password"
    4. Haz clic en "Authorize"
    5. Ahora podrás probar todos los endpoints protegidos
    
    ### Campos del formulario:
    - **username**: Tu dirección de email (aunque diga "username")
    - **password**: Tu contraseña
    
    **Nota**: Este endpoint funciona igual que `/auth/login` pero está optimizado para Swagger UI.
    """,
    tags=["🔐 Autenticación"],
    responses={
        200: {
            "description": "Login exitoso desde Swagger UI",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {
            "description": "Credenciales incorrectas",
            "content": {
                "application/json": {
                    "example": {"detail": "Email o contraseña incorrectos"}
                }
            }
        }
    }
)
async def login_for_swagger(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Autenticación OAuth2 para Swagger UI
    
    Este endpoint permite hacer login desde la interfaz de documentación de Swagger.
    El campo 'username' del formulario debe contener el email del usuario.
    """
    # En OAuth2PasswordRequestForm, el email va en el campo 'username'
    user = await get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(form_data.password, user["password_hash"]):
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
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="""
    **Registra un nuevo usuario en el sistema.**
    
    Este endpoint permite crear una nueva cuenta de usuario con las siguientes características:
    - Validación de email único en el sistema
    - Encriptación segura de la contraseña
    - Activación automática de la cuenta
    
    ### Campos requeridos:
    - **nombre**: Nombre completo del usuario (solo para el formulario, no se guarda en la base de datos)
    - **email**: Dirección de correo electrónico válida (debe ser única)
    - **password**: Contraseña del usuario (mínimo 8 caracteres recomendado)
    
    ### Respuesta exitosa:
    Retorna la información del usuario creado sin la contraseña.
    """,
    response_description="Usuario creado exitosamente",
    responses={
        201: {
            "description": "Usuario registrado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "usuario@ejemplo.com",
                        "created_at": "2024-10-06T10:00:00Z",
                        "is_active": True
                    }
                }
            }
        },
        400: {
            "description": "Email ya registrado",
            "content": {
                "application/json": {
                    "example": {"detail": "El email ya está registrado"}
                }
            }
        },
        422: {
            "description": "Error de validación",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def register(
    user_data: Annotated[
        UserRegister,
        Body(
            example={
                "nombre": "Juan Pérez García",
                "email": "usuario@ejemplo.com",
                "password": "miPasswordSegura123"
            },
            description="Datos del usuario a registrar"
        )
    ]
):
    """
    Registrar un nuevo usuario en el sistema
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
    
    # Crear usuario (solo email y password van a la DB)
    try:
        new_user = await create_user(user_data.email, hashed_password)
        
        # Crear respuesta personalizada que incluya un mensaje con el nombre
        user_response = UserResponse(**new_user)
        
        # Retornar respuesta con mensaje personalizado usando el nombre
        return {
            **user_response.dict(),
            "message": f"Usuario '{user_data.nombre}' registrado exitosamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )

@auth_router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
    description="""
    **Autenticar usuario y obtener token de acceso.**
    
    Este endpoint permite a los usuarios autenticarse en el sistema y obtener un token JWT para acceder a recursos protegidos.
    
    ### Campos requeridos:
    - **email**: Dirección de correo electrónico del usuario registrado
    - **password**: Contraseña del usuario
    
    ### Funcionamiento:
    1. Valida las credenciales del usuario
    2. Verifica que la cuenta esté activa
    3. Genera un token JWT con tiempo de expiración
    4. Retorna el token de acceso
    
    ### Uso del token:
    Incluye el token en las peticiones protegidas:
    ```
    Authorization: Bearer <access_token>
    ```
    """,
    response_description="Token de acceso generado exitosamente",
    responses={
        200: {
            "description": "Login exitoso",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {
            "description": "Credenciales inválidas",
            "content": {
                "application/json": {
                    "example": {"detail": "Email o contraseña incorrectos"}
                }
            }
        },
        422: {
            "description": "Error de validación",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def login(
    user_credentials: Annotated[
        UserLogin,
        Body(
            example={
                "email": "usuario@ejemplo.com",
                "password": "miPasswordSegura123"
            },
            description="Credenciales de usuario para autenticación"
        )
    ]
):
    """
    Iniciar sesión y obtener token JWT
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

@auth_router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario actual",
    description="""
    **Obtiene la información del usuario autenticado.**
    
    Este endpoint protegido retorna los datos del usuario que está actualmente autenticado.
    
    ### Autenticación requerida:
    - Token JWT válido en el header `Authorization: Bearer <token>`
    
    ### Información retornada:
    - ID del usuario
    - Email del usuario
    - Fecha de creación de la cuenta
    - Estado de la cuenta (activa/inactiva)
    
    ### Casos de uso:
    - Verificar la información del usuario logueado
    - Validar que el token sigue siendo válido
    - Mostrar datos del perfil en la interfaz
    """,
    response_description="Información del usuario actual",
    responses={
        200: {
            "description": "Información del usuario obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "usuario@ejemplo.com",
                        "created_at": "2024-10-06T10:00:00Z",
                        "is_active": True
                    }
                }
            }
        },
        401: {
            "description": "Token inválido o expirado",
            "content": {
                "application/json": {
                    "example": {"detail": "Token inválido o expirado"}
                }
            }
        }
    }
)
async def get_current_user_info(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
        "Usuario actual obtenido del token JWT"
    ]
):
    """
    Obtener información del usuario actual autenticado
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        created_at=current_user["created_at"],
        is_active=current_user["is_active"]
    )

@auth_router.post(
    "/logout",
    summary="Cerrar sesión",
    description="""
    **Cerrar la sesión del usuario.**
    
    ### Importante sobre JWT:
    Con tokens JWT, el logout es principalmente manejado del lado del cliente eliminando el token del almacenamiento local.
    
    ### Funcionalidad:
    - Este endpoint existe para consistencia con APIs REST estándar
    - El token seguirá siendo válido hasta su expiración natural
    - Para invalidación inmediata, se necesitaría implementar una lista negra de tokens
    
    ### Recomendación:
    En el cliente, elimina el token del almacenamiento local/session storage después de llamar este endpoint.
    """,
    response_description="Confirmación de cierre de sesión",
    responses={
        200: {
            "description": "Sesión cerrada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Sesión cerrada exitosamente",
                        "timestamp": "2024-10-06T10:00:00Z"
                    }
                }
            }
        }
    }
)
async def logout():
    """
    Cerrar sesión del usuario
    """
    from datetime import datetime
    return {
        "message": "Sesión cerrada exitosamente",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
