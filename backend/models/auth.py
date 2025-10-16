from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

# Modelos para autenticación
class UserRegister(BaseModel):
    """
    Modelo para el registro de nuevos usuarios
    
    Campos requeridos:
    - nombre: Nombre completo del usuario (solo para el formulario, no se guarda en DB)
    - email: Dirección de correo electrónico válida y única
    - password: Contraseña del usuario (mínimo 8 caracteres)
    """
    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre completo del usuario (solo para formulario)",
        example="Juan Pérez García"
    )
    email: EmailStr = Field(
        ...,
        description="Dirección de correo electrónico del usuario",
        example="usuario@ejemplo.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Contraseña del usuario (mínimo 8 caracteres)",
        example="miPasswordSegura123"
    )
    
    @validator('password')
    def validate_password(cls, v):
        """Validar que la contraseña cumpla con requisitos mínimos"""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v
    
class UserLogin(BaseModel):
    """
    Modelo para el login de usuarios existentes
    
    Campos requeridos:
    - email: Dirección de correo electrónico registrada
    - password: Contraseña del usuario
    """
    email: EmailStr = Field(
        ...,
        description="Dirección de correo electrónico del usuario registrado",
        example="usuario@ejemplo.com"
    )
    password: str = Field(
        ...,
        description="Contraseña del usuario",
        example="miPasswordSegura123"
    )

class UserResponse(BaseModel):
    """
    Modelo para la respuesta de información del usuario
    
    No incluye información sensible como contraseñas
    """
    id: int = Field(
        ...,
        description="ID único del usuario",
        example=1
    )
    email: str = Field(
        ...,
        description="Dirección de correo electrónico del usuario",
        example="usuario@ejemplo.com"
    )
    created_at: datetime = Field(
        ...,
        description="Fecha y hora de creación de la cuenta",
        example="2024-10-06T10:00:00Z"
    )
    is_active: bool = Field(
        default=True,
        description="Estado de la cuenta del usuario",
        example=True
    )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

class Token(BaseModel):
    """
    Modelo para la respuesta de tokens JWT
    
    Incluye el token de acceso y información relacionada
    """
    access_token: str = Field(
        ...,
        description="Token JWT para autenticación",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo de token (siempre 'bearer' para JWT)",
        example="bearer"
    )
    expires_in: int = Field(
        ...,
        description="Tiempo de expiración del token en segundos",
        example=1800
    )

class TokenData(BaseModel):
    """
    Modelo para los datos decodificados del token JWT
    
    Utilizado internamente para validación de tokens
    """
    email: Optional[str] = Field(
        None,
        description="Email del usuario del token"
    )
    user_id: Optional[int] = Field(
        None,
        description="ID del usuario del token"
    )

class UserUpdate(BaseModel):
    """
    Modelo para actualización de información del usuario
    
    Todos los campos son opcionales para permitir actualizaciones parciales
    """
    email: Optional[EmailStr] = Field(
        None,
        description="Nueva dirección de correo electrónico",
        example="nuevo@ejemplo.com"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Nuevo estado de la cuenta"
    )

class PasswordChange(BaseModel):
    """
    Modelo para el cambio de contraseña
    """
    current_password: str = Field(
        ...,
        description="Contraseña actual del usuario",
        example="passwordActual123"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="Nueva contraseña (mínimo 8 caracteres)",
        example="nuevaPassword456"
    )
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validar que la nueva contraseña cumpla con requisitos mínimos"""
        if len(v) < 8:
            raise ValueError('La nueva contraseña debe tener al menos 8 caracteres')
        return v