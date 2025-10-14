"""
Router para Employment Platforms (Plataformas de Empleo)
Endpoints para consultar plataformas disponibles y crear nuevas plataformas
Usa el servicio unificado EmploymentPlatformsService
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional, List
from datetime import datetime

# Imports de modelos
from models.employment_platforms import (
    EmploymentPlatformCreate, 
    EmploymentPlatformUpdate, 
    EmploymentPlatformResponse,
    EmploymentPlatformWithStats,
    PlatformTypeEnum,
    PlatformCategoryEnum
)

# Imports de autenticación
from routes.auth_simple import get_current_user

# Import del servicio unificado
from services.employment_platforms_service import get_employment_platforms_service, populate_sample_platforms

# Router para plataformas de empleo
platforms_router = APIRouter(
    prefix="/platforms",
    tags=["💼 Employment Platforms"],
    responses={
        401: {"description": "No autorizado - Token requerido"},
        404: {"description": "Plataforma no encontrada"},
        409: {"description": "Conflicto - Plataforma ya existe"},
        500: {"description": "Error interno del servidor"}
    }
)

# Instancia del servicio unificado
platforms_service = get_employment_platforms_service()

# ===========================
# ENDPOINTS PÚBLICOS
# ===========================

@platforms_router.get("/", response_model=List[EmploymentPlatformResponse])
async def list_platforms(
    skip: int = Query(0, ge=0, description="Número de plataformas a omitir"),
    limit: int = Query(20, ge=1, le=100, description="Límite de plataformas a retornar"),
    platform_type: Optional[PlatformTypeEnum] = Query(None, description="Filtrar por tipo de plataforma"),
    category: Optional[PlatformCategoryEnum] = Query(None, description="Filtrar por categoría"),
    country: Optional[str] = Query(None, description="Filtrar por país"),
    validated_only: bool = Query(True, description="Solo plataformas validadas"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción")
):
    """
    Listar plataformas de empleo disponibles (público)
    
    - **No requiere autenticación** - endpoint público
    - **skip**: Paginación - elementos a omitir (no usado en servicio actual)
    - **limit**: Paginación - máximo de elementos (max 100)
    - **platform_type**: Filtro opcional por tipo (job_board, freelance, etc.)
    - **category**: Filtro opcional por categoría (technology, design, etc.)
    - **country**: Filtro opcional por país
    - **validated_only**: Solo mostrar plataformas validadas
    - **search**: Buscar en nombre o descripción
    
    Útil para que los usuarios vean qué plataformas están disponibles para reseñar.
    """
    try:
        if search or platform_type or category or country:
            # Usar búsqueda con filtros
            platforms = await platforms_service.get_relevant_platforms(
                query=search or "",
                category=category.value if category else None,
                platform_type=platform_type.value if platform_type else None,
                country=country,
                limit=limit
            )
        else:
            # Obtener todas las plataformas
            platforms = await platforms_service.get_all_platforms(
                validated_only=validated_only,
                limit=limit
            )
        
        return [EmploymentPlatformResponse(**platform) for platform in platforms]
        
    except Exception as e:
        print(f"Error listing platforms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener las plataformas"
        )


@platforms_router.get("/{platform_id}", response_model=EmploymentPlatformResponse)
async def get_platform(platform_id: int):
    """
    Obtener una plataforma específica por ID (público)
    
    - **No requiere autenticación** - endpoint público
    - **platform_id**: ID de la plataforma
    
    Retorna la información completa de la plataforma.
    """
    try:
        platform = await platforms_service.get_platform_by_id(platform_id)
        
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plataforma no encontrada"
            )
        
        return EmploymentPlatformResponse(**platform)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting platform: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la plataforma"
        )


@platforms_router.get("/{platform_id}/with-stats", response_model=EmploymentPlatformResponse)
async def get_platform_with_review_stats(platform_id: int):
    """
    Obtener una plataforma con estadísticas de reseñas (público)
    
    - **No requiere autenticación** - endpoint público
    - **platform_id**: ID de la plataforma
    
    Retorna la plataforma básica (sin estadísticas por ahora, TODO: implementar stats)
    """
    try:
        platform = await platforms_service.get_platform_by_id(platform_id)
        
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plataforma no encontrada"
            )
        
        # TODO: Agregar estadísticas de reseñas
        return EmploymentPlatformResponse(**platform)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting platform with stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la plataforma"
        )

# ===========================
# ENDPOINTS CON AUTENTICACIÓN
# ===========================

@platforms_router.post("/", response_model=EmploymentPlatformResponse, status_code=status.HTTP_201_CREATED)
async def create_platform(
    platform_data: EmploymentPlatformCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Crear una nueva plataforma de empleo
    
    - **Requiere autenticación JWT**
    - **name**: Nombre de la plataforma (único)
    - **type**: Tipo de plataforma (opcional)
    - **url**: URL de la plataforma (opcional)
    - **description**: Descripción (opcional)
    - **country**: País (opcional)
    - **category**: Categoría (opcional)
    
    Las plataformas creadas por usuarios empiezan como no validadas.
    """
    try:
        created_platform = await platforms_service.create_platform(platform_data)
        
        if not created_platform:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una plataforma con el nombre '{platform_data.name}' o error al crear"
            )
        
        return EmploymentPlatformResponse(**created_platform)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating platform: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la plataforma"
        )

# ===========================
# ENDPOINTS DE ESTADÍSTICAS
# ===========================

@platforms_router.get("/stats/summary")
async def get_platforms_summary():
    """
    Obtener resumen estadístico de todas las plataformas (público)
    
    - **No requiere autenticación** - endpoint público
    
    Retorna estadísticas generales como total de plataformas, distribución por tipo, etc.
    """
    try:
        stats = await platforms_service.get_platforms_summary()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting platforms summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener estadísticas"
        )


@platforms_router.post("/admin/populate-sample")
async def populate_sample_platforms_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    Poblar la base de datos con plataformas de empleo de ejemplo (Admin)
    
    - **Requiere autenticación JWT** - Solo administradores
    
    Crea las plataformas de empleo más comunes como LinkedIn, Indeed, InfoJobs, etc.
    Útil para inicializar el sistema con datos de ejemplo.
    """
    try:
        success = await populate_sample_platforms()
        
        if success:
            return {
                "success": True,
                "message": "Plataformas de empleo de ejemplo creadas exitosamente",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear las plataformas de empleo de ejemplo"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error populating sample platforms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al poblar plataformas de ejemplo"
        )


@platforms_router.get("/search/relevant", response_model=List[EmploymentPlatformResponse])
async def search_relevant_platforms(
    query: str = Query(..., description="Consulta de búsqueda"),
    category: Optional[PlatformCategoryEnum] = Query(None, description="Filtrar por categoría"),
    platform_type: Optional[PlatformTypeEnum] = Query(None, description="Filtrar por tipo"),
    country: Optional[str] = Query(None, description="Filtrar por país"),
    limit: int = Query(10, ge=1, le=50, description="Máximo de resultados")
):
    """
    Buscar plataformas de empleo relevantes (público)
    
    - **No requiere autenticación** - endpoint público
    - **query**: Palabras clave para buscar en nombres/descripciones
    - **category**: Filtro opcional por categoría
    - **platform_type**: Filtro opcional por tipo
    - **country**: Filtro opcional por país
    - **limit**: Máximo de resultados (1-50)
    
    Útil para el sistema RAG para encontrar plataformas relevantes según el contexto.
    """
    try:
        platforms = await platforms_service.get_relevant_platforms(
            query=query,
            category=category.value if category else None,
            platform_type=platform_type.value if platform_type else None,
            country=country,
            limit=limit
        )
        
        return [EmploymentPlatformResponse(**platform) for platform in platforms]
        
    except Exception as e:
        print(f"Error searching platforms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al buscar plataformas"
        )