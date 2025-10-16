"""
Modelos Pydantic para sistema de reseñas
Basado en la tabla 'reviews'
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class ReviewTypeEnum(str, Enum):
    """Tipos de reseña"""
    platform_experience = "platform_experience"
    job_opportunity = "job_opportunity"
    hiring_process = "hiring_process"
    company_culture = "company_culture"
    salary_benefits = "salary_benefits"
    work_environment = "work_environment"
    general = "general"


class ReviewBase(BaseModel):
    """Modelo base para reseñas"""
    is_platform_review: bool = Field(
        default=True,
        description="Indica si es una reseña de la plataforma o de una experiencia específica"
    )
    review_type: Optional[ReviewTypeEnum] = Field(
        None,
        description="Tipo de reseña"
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Calificación de 1 a 5 estrellas",
        example=4
    )
    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="Comentario detallado de la reseña",
        example="Excelente plataforma para encontrar oportunidades remotas. El proceso de postulación es muy intuitivo."
    )
    visible: bool = Field(
        default=True,
        description="Indica si la reseña es visible públicamente"
    )

    @validator('comment')
    def validate_comment(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('El comentario debe tener al menos 10 caracteres')
        return v.strip() if v else v

    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('La calificación debe estar entre 1 y 5')
        return v


class ReviewCreate(ReviewBase):
    """Modelo para crear una nueva reseña"""
    platform_id: int = Field(
        ...,
        description="ID de la plataforma siendo reseñada",
        example=1
    )


class ReviewUpdate(BaseModel):
    """Modelo para actualizar una reseña"""
    is_platform_review: Optional[bool] = Field(
        None,
        description="Indica si es una reseña de la plataforma o de una experiencia específica"
    )
    review_type: Optional[ReviewTypeEnum] = Field(
        None,
        description="Tipo de reseña"
    )
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Calificación de 1 a 5 estrellas"
    )
    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="Comentario detallado de la reseña"
    )
    visible: Optional[bool] = Field(
        None,
        description="Indica si la reseña es visible públicamente"
    )

    @validator('comment')
    def validate_comment(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError('El comentario debe tener al menos 10 caracteres')
        return v.strip() if v else v

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('La calificación debe estar entre 1 y 5')
        return v


class ReviewResponse(ReviewBase):
    """Modelo para respuestas API de reseñas"""
    id: int = Field(description="ID único de la reseña")
    user_id: int = Field(description="ID del usuario que escribió la reseña")
    platform_id: int = Field(description="ID de la plataforma reseñada")
    created_at: datetime = Field(description="Fecha de creación de la reseña")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReviewWithRelations(ReviewResponse):
    """Modelo extendido que incluye información relacionada"""
    # Información del usuario (sin datos sensibles)
    user_email: Optional[str] = Field(None, description="Email del usuario (parcialmente oculto)")
    
    # Información de la plataforma
    platform_name: Optional[str] = Field(None, description="Nombre de la plataforma")
    platform_url: Optional[str] = Field(None, description="URL de la plataforma")


class ReviewStats(BaseModel):
    """Modelo para estadísticas de reseñas"""
    total_reviews: int = Field(description="Total de reseñas")
    average_rating: float = Field(description="Calificación promedio")
    rating_distribution: dict = Field(description="Distribución de calificaciones (1-5 estrellas)")
    recent_reviews_count: int = Field(description="Reseñas del último mes")
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }