"""
Router para Employment Platforms (Plataformas de Empleo)
Endpoints para consultar plataformas disponibles y crear nuevas plataformas
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional, List
import asyncpg
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

# Import de base de datos
from database.db_connection import connect_async, disconnect_async

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

# ===========================
# FUNCIONES AUXILIARES DB
# ===========================

async def get_platform_by_id(platform_id: int) -> Optional[dict]:
    """Obtener plataforma por ID"""
    conn = await connect_async()
    if not conn:
        return None
    
    try:
        query = """
            SELECT id, name, type, url, description, country, category, validated, registered_at
            FROM employment_platforms 
            WHERE id = $1
        """
        row = await conn.fetchrow(query, platform_id)
        return dict(row) if row else None
    except Exception as e:
        print(f"Error getting platform by ID: {e}")
        return None
    finally:
        await disconnect_async(conn)


async def platform_exists_by_name(name: str, exclude_id: Optional[int] = None) -> bool:
    """Verificar si una plataforma existe por nombre"""
    conn = await connect_async()
    if not conn:
        return False
    
    try:
        if exclude_id:
            query = "SELECT id FROM employment_platforms WHERE LOWER(name) = LOWER($1) AND id != $2"
            row = await conn.fetchrow(query, name, exclude_id)
        else:
            query = "SELECT id FROM employment_platforms WHERE LOWER(name) = LOWER($1)"
            row = await conn.fetchrow(query, name)
        return row is not None
    except Exception as e:
        print(f"Error checking platform existence: {e}")
        return False
    finally:
        await disconnect_async(conn)


async def get_platform_with_stats(platform_id: int) -> Optional[dict]:
    """Obtener plataforma con estadísticas de reseñas"""
    conn = await connect_async()
    if not conn:
        return None
    
    try:
        query = """
            SELECT 
                ep.id, ep.name, ep.type, ep.url, ep.description, 
                ep.country, ep.category, ep.validated, ep.registered_at,
                COUNT(r.id) as total_reviews,
                AVG(r.rating::float) as average_rating,
                COUNT(CASE WHEN r.created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as recent_reviews_count
            FROM employment_platforms ep
            LEFT JOIN reviews r ON ep.id = r.platform_id
            WHERE ep.id = $1
            GROUP BY ep.id, ep.name, ep.type, ep.url, ep.description, 
                     ep.country, ep.category, ep.validated, ep.registered_at
        """
        row = await conn.fetchrow(query, platform_id)
        return dict(row) if row else None
    except Exception as e:
        print(f"Error getting platform with stats: {e}")
        return None
    finally:
        await disconnect_async(conn)

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
    validated_only: bool = Query(False, description="Solo plataformas validadas"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción")
):
    """
    Listar plataformas de empleo disponibles (público)
    
    - **No requiere autenticación** - endpoint público
    - **skip**: Paginación - elementos a omitir
    - **limit**: Paginación - máximo de elementos (max 100)
    - **platform_type**: Filtro opcional por tipo (job_board, freelance, etc.)
    - **category**: Filtro opcional por categoría (technology, design, etc.)
    - **country**: Filtro opcional por país
    - **validated_only**: Solo mostrar plataformas validadas
    - **search**: Buscar en nombre o descripción
    
    Útil para que los usuarios vean qué plataformas están disponibles para reseñar.
    """
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        # Construir query con filtros opcionales
        where_conditions = []
        params = []
        param_count = 0
        
        if platform_type:
            param_count += 1
            where_conditions.append(f"type = ${param_count}")
            params.append(platform_type)
        
        if category:
            param_count += 1
            where_conditions.append(f"category = ${param_count}")
            params.append(category)
        
        if country:
            param_count += 1
            where_conditions.append(f"LOWER(country) = LOWER(${param_count})")
            params.append(country)
        
        if validated_only:
            where_conditions.append("validated = true")
        
        if search:
            param_count += 1
            where_conditions.append(f"(LOWER(name) LIKE LOWER(${param_count}) OR LOWER(description) LIKE LOWER(${param_count}))")
            params.append(f"%{search}%")
        
        # Query base
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT id, name, type, url, description, country, category, validated, registered_at
            FROM employment_platforms
            {where_clause}
            ORDER BY validated DESC, name ASC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, skip])
        
        rows = await conn.fetch(query, *params)
        
        return [EmploymentPlatformResponse(**dict(row)) for row in rows]
        
    except Exception as e:
        print(f"Error listing platforms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener las plataformas"
        )
    finally:
        await disconnect_async(conn)


@platforms_router.get("/{platform_id}", response_model=EmploymentPlatformResponse)
async def get_platform(platform_id: int):
    """
    Obtener una plataforma específica por ID (público)
    
    - **No requiere autenticación** - endpoint público
    - **platform_id**: ID de la plataforma
    
    Retorna la información completa de la plataforma.
    """
    platform = await get_platform_by_id(platform_id)
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plataforma no encontrada"
        )
    
    return EmploymentPlatformResponse(**platform)


@platforms_router.get("/{platform_id}/with-stats", response_model=EmploymentPlatformWithStats)
async def get_platform_with_review_stats(platform_id: int):
    """
    Obtener una plataforma con estadísticas de reseñas (público)
    
    - **No requiere autenticación** - endpoint público
    - **platform_id**: ID de la plataforma
    
    Retorna la plataforma con estadísticas como total de reseñas, calificación promedio, etc.
    """
    platform = await get_platform_with_stats(platform_id)
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plataforma no encontrada"
        )
    
    # Formatear estadísticas
    platform_data = {
        "id": platform["id"],
        "name": platform["name"],
        "type": platform["type"],
        "url": platform["url"],
        "description": platform["description"],
        "country": platform["country"],
        "category": platform["category"],
        "validated": platform["validated"],
        "registered_at": platform["registered_at"],
        "total_reviews": platform["total_reviews"] or 0,
        "average_rating": round(platform["average_rating"], 2) if platform["average_rating"] else None,
        "recent_reviews_count": platform["recent_reviews_count"] or 0
    }
    
    return EmploymentPlatformWithStats(**platform_data)

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
    # Verificar que no exista una plataforma con el mismo nombre
    if await platform_exists_by_name(platform_data.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una plataforma con el nombre '{platform_data.name}'"
        )
    
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        query = """
            INSERT INTO employment_platforms (name, type, url, description, country, category, validated)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, name, type, url, description, country, category, validated, registered_at
        """
        row = await conn.fetchrow(
            query, 
            platform_data.name,
            platform_data.type,
            str(platform_data.url) if platform_data.url else None,
            platform_data.description,
            platform_data.country,
            platform_data.category,
            platform_data.validated
        )
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear la plataforma"
            )
        
        return EmploymentPlatformResponse(**dict(row))
        
    except Exception as e:
        print(f"Error creating platform: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la plataforma"
        )
    finally:
        await disconnect_async(conn)

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
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        query = """
            SELECT 
                COUNT(*) as total_platforms,
                COUNT(CASE WHEN validated = true THEN 1 END) as validated_platforms,
                COUNT(CASE WHEN type = 'job_board' THEN 1 END) as job_board_count,
                COUNT(CASE WHEN type = 'freelance' THEN 1 END) as freelance_count,
                COUNT(CASE WHEN type = 'networking' THEN 1 END) as networking_count,
                COUNT(CASE WHEN type = 'company_portal' THEN 1 END) as company_portal_count,
                COUNT(CASE WHEN category = 'technology' THEN 1 END) as technology_count,
                COUNT(CASE WHEN category = 'design' THEN 1 END) as design_count,
                COUNT(CASE WHEN category = 'marketing' THEN 1 END) as marketing_count,
                COUNT(CASE WHEN category = 'general' THEN 1 END) as general_count
            FROM employment_platforms
        """
        
        row = await conn.fetchrow(query)
        
        return {
            "total_platforms": row["total_platforms"],
            "validated_platforms": row["validated_platforms"],
            "unvalidated_platforms": row["total_platforms"] - row["validated_platforms"],
            "by_type": {
                "job_board": row["job_board_count"],
                "freelance": row["freelance_count"],
                "networking": row["networking_count"],
                "company_portal": row["company_portal_count"],
                "other": row["total_platforms"] - (row["job_board_count"] + row["freelance_count"] + row["networking_count"] + row["company_portal_count"])
            },
            "by_category": {
                "technology": row["technology_count"],
                "design": row["design_count"],
                "marketing": row["marketing_count"],
                "general": row["general_count"],
                "other": row["total_platforms"] - (row["technology_count"] + row["design_count"] + row["marketing_count"] + row["general_count"])
            }
        }
        
    except Exception as e:
        print(f"Error getting platforms summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener estadísticas"
        )
    finally:
        await disconnect_async(conn)