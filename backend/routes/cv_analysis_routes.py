"""
Rutas para análisis de CV y consejos de carrera
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import Annotated, Optional
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import tempfile
from pathlib import Path

from loguru import logger
from backend.services.cv_analysis_service import cv_analysis_service
from backend.services.document_utils import DocumentUtils
from backend.routes.auth_simple import get_current_user
from backend.database.db_connection import connect, disconnect

router = APIRouter(prefix="/api/cv-analysis", tags=["CV Analysis"])


@router.post("/analyze-resume")
async def analyze_resume(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze uploaded resume and provide career transition advice
    
    Args:
        file: Uploaded resume file (PDF, DOC, DOCX)
        current_user: Current authenticated user
        
    Returns:
        Analysis results and career advice
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")
        
        # Validate file type
        allowed_types = ["application/pdf", "application/msword", 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Formato de archivo no soportado. Use PDF, DOC o DOCX."
            )
        
        # Create temporary file to process
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Validate file
            validation_result = cv_analysis_service.validate_resume_file(temp_file_path)
            if not validation_result.get("valid"):
                raise HTTPException(status_code=400, detail=validation_result.get("message"))
            
            # Analyze resume
            analysis_result = cv_analysis_service.analyze_user_resume(user_id, temp_file_path)
            
            if analysis_result.get("success"):
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": analysis_result.get("message"),
                        "data": analysis_result.get("data")
                    }
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=analysis_result.get("message", "Error al procesar el CV")
                )
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_resume endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/career-advice")
async def get_career_advice(current_user: Dict = Depends(get_current_user)):
    """
    Get updated career advice for current user profile
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Updated career advice
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")
        
        advice_result = cv_analysis_service.get_updated_career_advice(user_id)
        
        if advice_result.get("success"):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": advice_result.get("message"),
                    "career_advice": advice_result.get("career_advice")
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": advice_result.get("message")
                }
            )
            
    except Exception as e:
        logger.error(f"Error in get_career_advice endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/profile-status")
async def get_profile_status(current_user: Dict = Depends(get_current_user)):
    """
    Check if user has analyzed profile and get basic info
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Profile status information
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")
        
        # Check if user has profile in database
        from backend.database.db_connection import connect, disconnect
        
        conn = connect()
        if conn is None:
            raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT full_name, education_level, digital_level, 
                       area_of_interest, updated_at
                FROM user_personal_info 
                WHERE user_id = %s
            """, (user_id,))
            
            profile = cursor.fetchone()
            
            if profile:
                return JSONResponse(
                    status_code=200,
                    content={
                        "has_profile": True,
                        "profile_data": {
                            "full_name": profile[0],
                            "education_level": profile[1],
                            "digital_level": profile[2],
                            "area_of_interest": profile[3],
                            "last_updated": profile[4].isoformat() if profile[4] else None
                        }
                    }
                )
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "has_profile": False,
                        "message": "No se ha encontrado un perfil analizado. Sube tu CV para comenzar."
                    }
                )
                
        finally:
            cursor.close()
            disconnect(conn)
            
    except Exception as e:
        logger.error(f"Error in get_profile_status endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")