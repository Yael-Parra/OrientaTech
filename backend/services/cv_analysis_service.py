"""
Service for CV analysis and career advice integration
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from backend.agent.langchain import CVAnalyzer, analyze_user_cv, get_career_advice_for_profile
from backend.services.document_utils import DocumentUtils


class CVAnalysisService:
    """
    Service to handle CV analysis workflow integration
    """
    
    def __init__(self):
        """Initialize the CV Analysis Service"""
        self.analyzer = CVAnalyzer()
        self.document_utils = DocumentUtils()
    
    def analyze_user_resume(self, user_id: int, uploaded_file_path: str) -> Dict[str, Any]:
        """
        Analyze user's uploaded resume and provide career advice
        
        Args:
            user_id: User ID
            uploaded_file_path: Path to uploaded resume file
            
        Returns:
            Dict containing analysis results and career advice
        """
        try:
            logger.info(f"Starting resume analysis for user {user_id}")
            
            # Validate file exists
            if not os.path.exists(uploaded_file_path):
                raise FileNotFoundError(f"Resume file not found: {uploaded_file_path}")
            
            # Process CV and generate advice
            result = analyze_user_cv(user_id, uploaded_file_path)
            
            if result.get("success"):
                logger.info(f"Resume analysis completed successfully for user {user_id}")
                return {
                    "success": True,
                    "message": "CV analizado exitosamente. Se ha generado tu perfil profesional y recomendaciones personalizadas.",
                    "data": {
                        "profile_updated": result.get("database_saved", False),
                        "career_advice": result.get("career_advice"),
                        "analysis_summary": {
                            "name": result.get("analysis", {}).get("full_name", "Usuario"),
                            "current_sector": result.get("analysis", {}).get("current_sector", "No detectado"),
                            "tech_readiness": result.get("analysis", {}).get("tech_readiness", 5),
                            "digital_level": result.get("analysis", {}).get("digital_level", "basic")
                        }
                    }
                }
            else:
                logger.error(f"Resume analysis failed for user {user_id}: {result.get('error')}")
                return {
                    "success": False,
                    "message": "Error al analizar el CV. Por favor, intenta nuevamente.",
                    "error": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error in resume analysis service: {e}")
            return {
                "success": False,
                "message": "Error interno al procesar el CV. Por favor, contacta al soporte técnico.",
                "error": str(e)
            }
    
    def get_updated_career_advice(self, user_id: int) -> Dict[str, Any]:
        """
        Get updated career advice for existing user profile
        
        Args:
            user_id: User ID
            
        Returns:
            Dict containing career advice
        """
        try:
            advice = get_career_advice_for_profile(user_id)
            
            if advice:
                return {
                    "success": True,
                    "message": "Consejos de carrera actualizados exitosamente.",
                    "career_advice": advice
                }
            else:
                return {
                    "success": False,
                    "message": "No se encontró perfil de usuario. Por favor, sube tu CV primero."
                }
                
        except Exception as e:
            logger.error(f"Error getting updated career advice: {e}")
            return {
                "success": False,
                "message": "Error al generar consejos actualizados.",
                "error": str(e)
            }
    
    def validate_resume_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate if the uploaded file is a valid resume format
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict with validation results
        """
        try:
            file_extension = Path(file_path).suffix.lower()
            allowed_extensions = ['.pdf', '.doc', '.docx']
            
            if file_extension not in allowed_extensions:
                return {
                    "valid": False,
                    "message": f"Formato de archivo no soportado. Formatos permitidos: {', '.join(allowed_extensions)}"
                }
            
            # Check file size (max 5MB as per env config)
            max_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                return {
                    "valid": False,
                    "message": f"El archivo es demasiado grande. Tamaño máximo permitido: {max_size_mb}MB"
                }
            
            return {
                "valid": True,
                "message": "Archivo válido para análisis"
            }
            
        except Exception as e:
            logger.error(f"Error validating resume file: {e}")
            return {
                "valid": False,
                "message": "Error al validar el archivo"
            }


# Singleton instance for use across the application
cv_analysis_service = CVAnalysisService()