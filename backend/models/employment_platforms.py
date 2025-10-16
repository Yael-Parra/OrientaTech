"""
Modelos Pydantic para plataformas de empleo
Basado en la tabla 'employment_platforms'
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class PlatformTypeEnum(str, Enum):
    """Tipos de plataformas de empleo"""
    job_board = "job_board"
    freelance = "freelance"
    networking = "networking"
    company_portal = "company_portal"
    recruitment_agency = "recruitment_agency"
    gig_economy = "gig_economy"
    remote_work = "remote_work"
    startup = "startup"


class PlatformCategoryEnum(str, Enum):
    """Categorías de plataformas"""
    technology = "technology"
    design = "design"
    marketing = "marketing"
    finance = "finance"
    healthcare = "healthcare"
    education = "education"
    construction = "construction"
    hospitality = "hospitality"
    retail = "retail"
    manufacturing = "manufacturing"
    general = "general"
    other = "other"


class EmploymentPlatformBase(BaseModel):
    """Modelo base para plataformas de empleo"""
    name: str = Field(
        ...,
        max_length=200,
        description="Nombre de la plataforma",
        example="LinkedIn"
    )
    type: Optional[PlatformTypeEnum] = Field(
        None,
        description="Tipo de plataforma de empleo"
    )
    url: Optional[HttpUrl] = Field(
        None,
        description="URL de la plataforma",
        example="https://www.linkedin.com"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción de la plataforma",
        example="Red profesional para conectar con empleadores y buscar oportunidades laborales"
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="País principal de operación",
        example="Estados Unidos"
    )
    category: Optional[PlatformCategoryEnum] = Field(
        None,
        description="Categoría principal de la plataforma"
    )

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('El nombre de la plataforma debe tener al menos 2 caracteres')
        return v.strip()

    @validator('country')
    def validate_country(cls, v):
        if v:
            return v.strip()
        return v

    @validator('description')
    def validate_description(cls, v):
        if v and len(v.strip()) > 1000:
            raise ValueError('La descripción no puede exceder 1000 caracteres')
        return v.strip() if v else v


class EmploymentPlatformCreate(EmploymentPlatformBase):
    """Modelo para crear una nueva plataforma de empleo"""
    validated: bool = Field(
        default=False,
        description="Estado de validación de la plataforma"
    )


class EmploymentPlatformUpdate(BaseModel):
    """Modelo para actualizar una plataforma de empleo"""
    name: Optional[str] = Field(
        None,
        max_length=200,
        description="Nombre de la plataforma"
    )
    type: Optional[PlatformTypeEnum] = Field(
        None,
        description="Tipo de plataforma de empleo"
    )
    url: Optional[HttpUrl] = Field(
        None,
        description="URL de la plataforma"
    )
    description: Optional[str] = Field(
        None,
        description="Descripción de la plataforma"
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="País principal de operación"
    )
    category: Optional[PlatformCategoryEnum] = Field(
        None,
        description="Categoría principal de la plataforma"
    )
    validated: Optional[bool] = Field(
        None,
        description="Estado de validación de la plataforma"
    )

    @validator('name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('El nombre de la plataforma debe tener al menos 2 caracteres')
        return v.strip() if v else v


class EmploymentPlatformResponse(EmploymentPlatformBase):
    """Modelo para respuestas API de plataformas de empleo"""
    id: int = Field(description="ID único de la plataforma")
    validated: bool = Field(description="Estado de validación de la plataforma")
    registered_at: datetime = Field(description="Fecha de registro de la plataforma")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmploymentPlatformWithStats(EmploymentPlatformResponse):
    """Modelo extendido que incluye estadísticas de la plataforma"""
    total_reviews: Optional[int] = Field(None, description="Total de reseñas")
    average_rating: Optional[float] = Field(None, description="Calificación promedio")
    recent_reviews_count: Optional[int] = Field(None, description="Reseñas recientes (último mes)")