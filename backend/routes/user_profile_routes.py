"""
CRUD Router para User Profile
Manejo completo de perfiles de usuario con autenticación JWT
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import asyncpg
from datetime import datetime

# Imports de modelos
from models.user_profile import (
    UserPersonalInfoCreate, 
    UserPersonalInfoUpdate, 
    UserPersonalInfoResponse
)

# Imports de autenticación
from routes.auth_simple import get_current_user

# Import de base de datos
from database.db_connection import connect_async, disconnect_async

# Router para perfil de usuario
profile_router = APIRouter(
    prefix="/profile",
    tags=["👤 Perfil de Usuario"],
    responses={
        401: {"description": "No autorizado - Token requerido"},
        404: {"description": "Perfil no encontrado"},
        409: {"description": "Conflicto - Perfil ya existe"},
        500: {"description": "Error interno del servidor"}
    }
)

# Funciones auxiliares para base de datos
async def get_profile_by_user_id(user_id: int) -> Optional[dict]:
    """Obtener perfil por ID de usuario"""
    conn = await connect_async()
    if not conn:
        return None
    
    try:
        query = """
            SELECT id, user_id, full_name, date_of_birth, gender, location,
                   education_level, previous_experience, area_of_interest,
                   main_skills, digital_level, resume_path, updated_at
            FROM user_personal_info 
            WHERE user_id = $1
        """
        row = await conn.fetchrow(query, user_id)
        return dict(row) if row else None
    
    except Exception as e:
        print(f"Error obteniendo perfil: {e}")
        return None
    finally:
        await disconnect_async(conn)

async def create_profile_db(user_id: int, profile_data: dict) -> Optional[dict]:
    """Crear nuevo perfil en base de datos"""
    conn = await connect_async()
    if not conn:
        return None
    
    try:
        query = """
            INSERT INTO user_personal_info (
                user_id, full_name, date_of_birth, gender, location,
                education_level, previous_experience, area_of_interest,
                main_skills, digital_level, resume_path
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, user_id, full_name, date_of_birth, gender, location,
                      education_level, previous_experience, area_of_interest,
                      main_skills, digital_level, resume_path, updated_at
        """
        
        row = await conn.fetchrow(
            query,
            user_id,
            profile_data.get("full_name"),
            profile_data.get("date_of_birth"),
            profile_data.get("gender"),
            profile_data.get("location"),
            profile_data.get("education_level"),
            profile_data.get("previous_experience"),
            profile_data.get("area_of_interest"),
            profile_data.get("main_skills"),
            profile_data.get("digital_level"),
            profile_data.get("resume_path")
        )
        
        return dict(row) if row else None
    
    except asyncpg.UniqueViolationError:
        return {"error": "profile_exists"}
    except Exception as e:
        print(f"Error creando perfil: {e}")
        return None
    finally:
        await disconnect_async(conn)

async def update_profile_db(user_id: int, profile_data: dict) -> Optional[dict]:
    """Actualizar perfil existente en base de datos"""
    conn = await connect_async()
    if not conn:
        return None
    
    try:
        # Construir query dinámicamente solo con campos no None
        fields = []
        values = []
        param_count = 1
        
        for field, value in profile_data.items():
            if value is not None:
                fields.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if not fields:
            return await get_profile_by_user_id(user_id)
        
        query = f"""
            UPDATE user_personal_info 
            SET {', '.join(fields)}
            WHERE user_id = ${param_count}
            RETURNING id, user_id, full_name, date_of_birth, gender, location,
                      education_level, previous_experience, area_of_interest,
                      main_skills, digital_level, resume_path, updated_at
        """
        
        values.append(user_id)
        row = await conn.fetchrow(query, *values)
        return dict(row) if row else None
    
    except Exception as e:
        print(f"Error actualizando perfil: {e}")
        return None
    finally:
        await disconnect_async(conn)

async def delete_profile_db(user_id: int) -> bool:
    """Eliminar perfil de base de datos"""
    conn = await connect_async()
    if not conn:
        return False
    
    try:
        query = "DELETE FROM user_personal_info WHERE user_id = $1"
        result = await conn.execute(query, user_id)
        return "DELETE 1" in result
    
    except Exception as e:
        print(f"Error eliminando perfil: {e}")
        return False
    finally:
        await disconnect_async(conn)

# ENDPOINTS CRUD

@profile_router.post(
    "/",
    response_model=UserPersonalInfoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear perfil de usuario",
    description="Crear un nuevo perfil personal para el usuario autenticado"
)
async def create_profile(
    profile: UserPersonalInfoCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear nuevo perfil de usuario"""
    
    # Verificar si ya existe un perfil
    existing_profile = await get_profile_by_user_id(current_user["id"])
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya tiene un perfil creado. Use PUT para actualizar."
        )
    
    # Crear perfil
    profile_data = profile.dict(exclude_unset=True)
    result = await create_profile_db(current_user["id"], profile_data)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno creando el perfil"
        )
    
    if isinstance(result, dict) and result.get("error") == "profile_exists":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El perfil ya existe para este usuario"
        )
    
    return result

@profile_router.get(
    "/",
    response_model=UserPersonalInfoResponse,
    summary="Obtener mi perfil",
    description="Obtener el perfil personal del usuario autenticado"
)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Obtener perfil del usuario logueado"""
    
    profile = await get_profile_by_user_id(current_user["id"])
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado. Use POST para crear uno nuevo."
        )
    
    return profile

@profile_router.put(
    "/",
    response_model=UserPersonalInfoResponse,
    summary="Actualizar perfil completo",
    description="Actualizar completamente el perfil del usuario autenticado"
)
async def update_profile_complete(
    profile: UserPersonalInfoUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar perfil completo (reemplaza todos los campos)"""
    
    # Verificar que existe el perfil
    existing_profile = await get_profile_by_user_id(current_user["id"])
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado. Use POST para crear uno nuevo."
        )
    
    # Actualizar con todos los campos
    profile_data = profile.dict()
    result = await update_profile_db(current_user["id"], profile_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno actualizando el perfil"
        )
    
    return result

@profile_router.patch(
    "/",
    response_model=UserPersonalInfoResponse,
    summary="Actualizar perfil parcial",
    description="Actualizar parcialmente el perfil del usuario autenticado"
)
async def update_profile_partial(
    profile: UserPersonalInfoUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar perfil parcialmente (solo campos enviados)"""
    
    # Verificar que existe el perfil
    existing_profile = await get_profile_by_user_id(current_user["id"])
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado. Use POST para crear uno nuevo."
        )
    
    # Actualizar solo campos enviados
    profile_data = profile.dict(exclude_unset=True)
    if not profile_data:
        return existing_profile
    
    result = await update_profile_db(current_user["id"], profile_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno actualizando el perfil"
        )
    
    return result

@profile_router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar perfil",
    description="Eliminar completamente el perfil del usuario autenticado"
)
async def delete_profile(current_user: dict = Depends(get_current_user)):
    """Eliminar perfil del usuario logueado"""
    
    # Verificar que existe el perfil
    existing_profile = await get_profile_by_user_id(current_user["id"])
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )
    
    # Eliminar perfil
    success = await delete_profile_db(current_user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno eliminando el perfil"
        )
    
    return {"message": "Perfil eliminado exitosamente"}

@profile_router.get(
    "/exists",
    summary="Verificar si existe perfil",
    description="Verificar si el usuario autenticado tiene un perfil creado"
)
async def check_profile_exists(current_user: dict = Depends(get_current_user)):
    """Verificar si el usuario tiene un perfil"""
    
    profile = await get_profile_by_user_id(current_user["id"])
    
    return {
        "exists": profile is not None,
        "user_id": current_user["id"],
        "has_profile": profile is not None
    }