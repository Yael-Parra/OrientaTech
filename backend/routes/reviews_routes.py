"""
CRUD Router para Reviews (Reseñas)
Sistema completo de manejo de reseñas de plataformas de empleo con autenticación JWT
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional, List
import asyncpg
from datetime import datetime

# Imports de modelos
from models.reviews import (
    ReviewCreate, 
    ReviewUpdate, 
    ReviewResponse,
    ReviewWithRelations,
    ReviewStats,
    ReviewTypeEnum
)

# Imports de autenticación
from routes.auth_simple import get_current_user

# Import de base de datos
from database.db_connection import connect_async, disconnect_async

# Router para reseñas
reviews_router = APIRouter(
    prefix="/reviews",
    tags=["⭐ Reviews (Reseñas)"],
    responses={
        401: {"description": "No autorizado - Token requerido"},
        404: {"description": "Reseña no encontrada"},
        403: {"description": "Acceso prohibido - No es el propietario"},
        409: {"description": "Conflicto - Reseña ya existe"},
        500: {"description": "Error interno del servidor"}
    }
)

# ===========================
# FUNCIONES AUXILIARES DB
# ===========================

async def get_review_by_id(review_id: int) -> Optional[dict]:
    """Obtener reseña por ID con información de relaciones"""
    conn = await connect_async()
    if not conn:
        return None
    
    try:
        query = """
            SELECT r.id, r.user_id, r.platform_id, r.review_type, r.rating, 
                   r.title, r.content, r.created_at, r.updated_at,
                   u.email as user_email, u.nome as user_name,
                   ep.name as platform_name, ep.url as platform_url,
                   ep.type as platform_type, ep.category as platform_category
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN employment_platforms ep ON r.platform_id = ep.id
            WHERE r.id = $1
        """
        row = await conn.fetchrow(query, review_id)
        return dict(row) if row else None
    except Exception as e:
        print(f"Error getting review by ID: {e}")
        return None
    finally:
        await disconnect_async(conn)


async def check_review_ownership(review_id: int, user_id: int) -> bool:
    """Verificar si una reseña pertenece al usuario"""
    conn = await connect_async()
    if not conn:
        return False
    
    try:
        query = "SELECT user_id FROM reviews WHERE id = $1"
        row = await conn.fetchrow(query, review_id)
        return row and row['user_id'] == user_id
    except Exception as e:
        print(f"Error checking review ownership: {e}")
        return False
    finally:
        await disconnect_async(conn)


async def platform_exists(platform_id: int) -> bool:
    """Verificar si una plataforma existe"""
    conn = await connect_async()
    if not conn:
        return False
    
    try:
        query = "SELECT id FROM employment_platforms WHERE id = $1"
        row = await conn.fetchrow(query, platform_id)
        return row is not None
    except Exception as e:
        print(f"Error checking platform existence: {e}")
        return False
    finally:
        await disconnect_async(conn)


async def user_already_reviewed_platform(user_id: int, platform_id: int, exclude_review_id: Optional[int] = None) -> bool:
    """Verificar si el usuario ya tiene una reseña para esta plataforma"""
    conn = await connect_async()
    if not conn:
        return False
    
    try:
        if exclude_review_id:
            query = "SELECT id FROM reviews WHERE user_id = $1 AND platform_id = $2 AND id != $3"
            row = await conn.fetchrow(query, user_id, platform_id, exclude_review_id)
        else:
            query = "SELECT id FROM reviews WHERE user_id = $1 AND platform_id = $2"
            row = await conn.fetchrow(query, user_id, platform_id)
        return row is not None
    except Exception as e:
        print(f"Error checking existing review: {e}")
        return False
    finally:
        await disconnect_async(conn)

# ===========================
# ENDPOINTS CRUD
# ===========================

@reviews_router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Crear una nueva reseña
    
    - **Requiere autenticación JWT**
    - **platform_id**: ID de la plataforma a reseñar
    - **review_type**: Tipo de reseña (job_search, interview_process, etc.)
    - **rating**: Calificación de 1 a 5
    - **title**: Título de la reseña
    - **content**: Contenido opcional de la reseña
    
    Un usuario solo puede tener una reseña por plataforma.
    """
    user_id = current_user["id"]
    
    # Verificar que la plataforma existe
    if not await platform_exists(review_data.platform_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La plataforma especificada no existe"
        )
    
    # Verificar que el usuario no tenga ya una reseña para esta plataforma
    if await user_already_reviewed_platform(user_id, review_data.platform_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tienes una reseña para esta plataforma. Puedes editarla en lugar de crear una nueva."
        )
    
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        query = """
            INSERT INTO reviews (user_id, platform_id, review_type, rating, title, content)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, user_id, platform_id, review_type, rating, title, content, created_at, updated_at
        """
        row = await conn.fetchrow(
            query, 
            user_id, 
            review_data.platform_id, 
            review_data.review_type, 
            review_data.rating, 
            review_data.title, 
            review_data.content
        )
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear la reseña"
            )
        
        return ReviewResponse(**dict(row))
        
    except Exception as e:
        print(f"Error creating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la reseña"
        )
    finally:
        await disconnect_async(conn)


@reviews_router.get("/my-reviews", response_model=List[ReviewWithRelations])
async def get_my_reviews(
    skip: int = Query(0, ge=0, description="Número de reseñas a omitir"),
    limit: int = Query(10, ge=1, le=50, description="Límite de reseñas a retornar"),
    review_type: Optional[ReviewTypeEnum] = Query(None, description="Filtrar por tipo de reseña"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener mis reseñas
    
    - **Requiere autenticación JWT**
    - **skip**: Paginación - elementos a omitir
    - **limit**: Paginación - máximo de elementos (max 50)
    - **review_type**: Filtro opcional por tipo de reseña
    
    Retorna solo las reseñas del usuario autenticado con información de la plataforma.
    """
    user_id = current_user["id"]
    
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        # Query base
        where_conditions = ["r.user_id = $1"]
        params = [user_id]
        param_count = 1
        
        # Filtro opcional por tipo de reseña
        if review_type:
            param_count += 1
            where_conditions.append(f"r.review_type = ${param_count}")
            params.append(review_type)
        
        query = f"""
            SELECT r.id, r.user_id, r.platform_id, r.review_type, r.rating, 
                   r.title, r.content, r.created_at, r.updated_at,
                   u.email as user_email, u.nome as user_name,
                   ep.name as platform_name, ep.url as platform_url,
                   ep.type as platform_type, ep.category as platform_category
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN employment_platforms ep ON r.platform_id = ep.id
            WHERE {' AND '.join(where_conditions)}
            ORDER BY r.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, skip])
        
        rows = await conn.fetch(query, *params)
        
        return [ReviewWithRelations(**dict(row)) for row in rows]
        
    except Exception as e:
        print(f"Error getting user reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener las reseñas"
        )
    finally:
        await disconnect_async(conn)


@reviews_router.get("/platform/{platform_id}", response_model=List[ReviewWithRelations])
async def get_platform_reviews(
    platform_id: int,
    skip: int = Query(0, ge=0, description="Número de reseñas a omitir"),
    limit: int = Query(10, ge=1, le=50, description="Límite de reseñas a retornar"),
    review_type: Optional[ReviewTypeEnum] = Query(None, description="Filtrar por tipo de reseña"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Calificación mínima")
):
    """
    Obtener reseñas de una plataforma específica (público)
    
    - **No requiere autenticación** - endpoint público
    - **platform_id**: ID de la plataforma
    - **skip**: Paginación - elementos a omitir
    - **limit**: Paginación - máximo de elementos (max 50)
    - **review_type**: Filtro opcional por tipo de reseña
    - **min_rating**: Filtro opcional por calificación mínima
    
    Útil para que los usuarios vean qué opinan otros sobre una plataforma.
    """
    # Verificar que la plataforma existe
    if not await platform_exists(platform_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La plataforma especificada no existe"
        )
    
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        # Query con filtros opcionales
        where_conditions = ["r.platform_id = $1"]
        params = [platform_id]
        param_count = 1
        
        if review_type:
            param_count += 1
            where_conditions.append(f"r.review_type = ${param_count}")
            params.append(review_type)
        
        if min_rating:
            param_count += 1
            where_conditions.append(f"r.rating >= ${param_count}")
            params.append(min_rating)
        
        query = f"""
            SELECT r.id, r.user_id, r.platform_id, r.review_type, r.rating, 
                   r.title, r.content, r.created_at, r.updated_at,
                   u.email as user_email, u.nome as user_name,
                   ep.name as platform_name, ep.url as platform_url,
                   ep.type as platform_type, ep.category as platform_category
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN employment_platforms ep ON r.platform_id = ep.id
            WHERE {' AND '.join(where_conditions)}
            ORDER BY r.created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, skip])
        
        rows = await conn.fetch(query, *params)
        
        return [ReviewWithRelations(**dict(row)) for row in rows]
        
    except Exception as e:
        print(f"Error getting platform reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener las reseñas"
        )
    finally:
        await disconnect_async(conn)


@reviews_router.get("/{review_id}", response_model=ReviewWithRelations)
async def get_review(review_id: int):
    """
    Obtener una reseña específica por ID (público)
    
    - **No requiere autenticación** - endpoint público
    - **review_id**: ID de la reseña
    
    Retorna la reseña con información completa de usuario y plataforma.
    """
    review = await get_review_by_id(review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseña no encontrada"
        )
    
    return ReviewWithRelations(**review)


@reviews_router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualizar una reseña existente
    
    - **Requiere autenticación JWT**
    - **review_id**: ID de la reseña a actualizar
    - **Solo el propietario** puede actualizar su reseña
    
    Todos los campos son opcionales. Solo se actualizarán los campos proporcionados.
    """
    user_id = current_user["id"]
    
    # Verificar ownership
    if not await check_review_ownership(review_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseña no encontrada o no tienes permisos para editarla"
        )
    
    # Verificar que hay algo que actualizar
    update_data = review_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay datos para actualizar"
        )
    
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        # Construir query dinámicamente
        set_clauses = []
        params = []
        param_count = 0
        
        for field, value in update_data.items():
            param_count += 1
            set_clauses.append(f"{field} = ${param_count}")
            params.append(value)
        
        # Agregar updated_at
        param_count += 1
        set_clauses.append(f"updated_at = ${param_count}")
        params.append(datetime.now())
        
        # Agregar review_id al final
        param_count += 1
        params.append(review_id)
        
        query = f"""
            UPDATE reviews 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            RETURNING id, user_id, platform_id, review_type, rating, title, content, created_at, updated_at
        """
        
        row = await conn.fetchrow(query, *params)
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reseña no encontrada"
            )
        
        return ReviewResponse(**dict(row))
        
    except Exception as e:
        print(f"Error updating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar la reseña"
        )
    finally:
        await disconnect_async(conn)


@reviews_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar una reseña
    
    - **Requiere autenticación JWT**
    - **review_id**: ID de la reseña a eliminar
    - **Solo el propietario** puede eliminar su reseña
    
    La eliminación es permanente y no se puede deshacer.
    """
    user_id = current_user["id"]
    
    # Verificar ownership
    if not await check_review_ownership(review_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseña no encontrada o no tienes permisos para eliminarla"
        )
    
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        query = "DELETE FROM reviews WHERE id = $1 AND user_id = $2"
        result = await conn.execute(query, review_id, user_id)
        
        # Verificar que se eliminó algo
        if result == "DELETE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reseña no encontrada"
            )
        
        # Status 204 No Content - sin return
        
    except Exception as e:
        print(f"Error deleting review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al eliminar la reseña"
        )
    finally:
        await disconnect_async(conn)


# ===========================
# ENDPOINTS ESTADÍSTICAS
# ===========================

@reviews_router.get("/platform/{platform_id}/stats", response_model=ReviewStats)
async def get_platform_review_stats(platform_id: int):
    """
    Obtener estadísticas de reseñas de una plataforma
    
    - **No requiere autenticación** - endpoint público
    - **platform_id**: ID de la plataforma
    
    Retorna estadísticas como total de reseñas, promedio de calificación, etc.
    """
    # Verificar que la plataforma existe
    if not await platform_exists(platform_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La plataforma especificada no existe"
        )
    
    conn = await connect_async()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de conexión a la base de datos"
        )
    
    try:
        query = """
            SELECT 
                COUNT(*) as total_reviews,
                AVG(rating::float) as average_rating,
                COUNT(CASE WHEN rating = 5 THEN 1 END) as five_star_count,
                COUNT(CASE WHEN rating = 4 THEN 1 END) as four_star_count,
                COUNT(CASE WHEN rating = 3 THEN 1 END) as three_star_count,
                COUNT(CASE WHEN rating = 2 THEN 1 END) as two_star_count,
                COUNT(CASE WHEN rating = 1 THEN 1 END) as one_star_count,
                MAX(created_at) as latest_review_date
            FROM reviews 
            WHERE platform_id = $1
        """
        
        row = await conn.fetchrow(query, platform_id)
        
        if not row or row['total_reviews'] == 0:
            # Retornar estadísticas vacías si no hay reseñas
            return ReviewStats(
                platform_id=platform_id,
                total_reviews=0,
                average_rating=0.0,
                five_star_count=0,
                four_star_count=0,
                three_star_count=0,
                two_star_count=0,
                one_star_count=0,
                latest_review_date=None
            )
        
        return ReviewStats(
            platform_id=platform_id,
            total_reviews=row['total_reviews'],
            average_rating=round(row['average_rating'], 2) if row['average_rating'] else 0.0,
            five_star_count=row['five_star_count'],
            four_star_count=row['four_star_count'],
            three_star_count=row['three_star_count'],
            two_star_count=row['two_star_count'],
            one_star_count=row['one_star_count'],
            latest_review_date=row['latest_review_date']
        )
        
    except Exception as e:
        print(f"Error getting platform stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener estadísticas"
        )
    finally:
        await disconnect_async(conn)