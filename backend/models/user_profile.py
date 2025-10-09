"""
Modelos Pydantic para información personal extendida de usuarios
Basado en la tabla 'user_personal_info'
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class GenderEnum(str, Enum):
    """Opciones de género"""
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class EducationLevelEnum(str, Enum):
    """Niveles de educación"""
    no_formal = "no_formal"
    primary = "primary"
    secondary = "secondary"
    high_school = "high_school"
    vocational = "vocational"
    bachelors = "bachelors"
    masters = "masters"
    phd = "phd"


class DigitalLevelEnum(str, Enum):
    """Niveles de competencia digital"""
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class UserPersonalInfoBase(BaseModel):
    """Modelo base para información personal del usuario"""
    full_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Nombre completo del usuario",
        example="María García López"
    )
    date_of_birth: Optional[date] = Field(
        None,
        description="Fecha de nacimiento",
        example="1990-05-15"
    )
    gender: Optional[GenderEnum] = Field(
        None,
        description="Género del usuario"
    )
    location: Optional[str] = Field(
        None,
        max_length=200,
        description="Ubicación del usuario",
        example="Madrid, España"
    )
    education_level: Optional[EducationLevelEnum] = Field(
        None,
        description="Nivel educativo más alto alcanzado"
    )
    previous_experience: Optional[str] = Field(
        None,
        description="Experiencia laboral previa",
        example="3 años como desarrolladora web en startup tecnológica"
    )
    area_of_interest: Optional[str] = Field(
        None,
        max_length=200,
        description="Área de interés profesional",
        example="Desarrollo de aplicaciones móviles, UX/UI"
    )
    main_skills: Optional[str] = Field(
        None,
        description="Habilidades principales",
        example="Python, JavaScript, React, diseño web responsivo"
    )
    digital_level: Optional[DigitalLevelEnum] = Field(
        None,
        description="Nivel de competencia digital"
    )
    resume_path: Optional[str] = Field(
        None,
        max_length=500,
        description="Ruta del archivo CV"
    )

    @validator('full_name')
    def validate_full_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('El nombre completo debe tener al menos 2 caracteres')
        return v.strip() if v else v

    @validator('location')
    def validate_location(cls, v):
        if v:
            return v.strip()
        return v


class UserPersonalInfoCreate(UserPersonalInfoBase):
    """Modelo para crear información personal del usuario"""
    pass


class UserPersonalInfoUpdate(UserPersonalInfoBase):
    """Modelo para actualizar información personal del usuario"""
    pass


class UserPersonalInfoResponse(UserPersonalInfoBase):
    """Modelo para respuestas API de información personal"""
    id: int = Field(description="ID único de la información personal")
    user_id: int = Field(description="ID del usuario asociado")
    updated_at: datetime = Field(description="Fecha de última actualización")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class UserPersonalInfoWithUser(UserPersonalInfoResponse):
    """Modelo extendido que incluye información básica del usuario"""
    user_email: Optional[str] = Field(None, description="Email del usuario")
    user_is_active: Optional[bool] = Field(None, description="Estado activo del usuario")