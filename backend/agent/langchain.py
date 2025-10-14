# Importaciones de librerias
import os
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# LangChain imports - Solo los necesarios
from langchain_groq import ChatGroq
from langchain.chains import LLMChain

# Local imports
from dotenv import load_dotenv
from loguru import logger

# Database imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import connect, disconnect
from models.user_profile import EducationLevelEnum, DigitalLevelEnum

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


class CVAnalyzer:
    """
    CV Analyzer using LangChain and Groq for career transition recommendations
    Refactorizado para mantener solo métodos utilizados
    """
    
    def __init__(self):
        """Initialize the CV Analyzer with LLM connection only"""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Initialize Groq LLM - Updated to use current model
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name="llama-3.1-8b-instant",  # Modelo actualizado y compatible
            temperature=0.3,
            max_tokens=2000
        )
        
        logger.info("CV Analyzer initialized successfully")

    def analyze_cv_content(self, cv_text: str) -> Dict[str, Any]:
        """
        Analyze CV content using Groq LLM to extract structured information
        
        Args:
            cv_text: Raw text from CV
            
        Returns:
            Dict containing analyzed CV information
        """
        from agent.prompting import get_cv_analysis_prompt
        analysis_prompt = get_cv_analysis_prompt()
        try:
            chain = LLMChain(llm=self.llm, prompt=analysis_prompt)
            response = chain.run(cv_text=cv_text)

            # Clean and parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis_result = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")

            logger.info("CV analysis completed successfully")
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing CV content: {e}")
            # Return default structure if analysis fails
            return {
                "full_name": "Unknown",
                "education_level": "secondary",
                "previous_experience": "Experience not detected",
                "main_skills": "Skills not detected",
                "area_of_interest": "Technology",
                "digital_level": "basic",
                "current_sector": "Unknown",
                "years_experience": 0,
                "tech_readiness": 5
            }

    def generate_career_advice(self, analysis_result: Dict[str, Any]) -> str:
        """
        Generate personalized career transition advice using Groq
        
        Args:
            analysis_result: Analyzed CV information
            
        Returns:
            str: Personalized career advice in Spanish
        """
        from agent.prompting import get_career_advice_prompt
        advice_prompt = get_career_advice_prompt()
        try:
            chain = LLMChain(llm=self.llm, prompt=advice_prompt)
            advice = chain.run(analysis=analysis_result)

            logger.info("Career advice generated successfully")
            return advice

        except Exception as e:
            logger.error(f"Error generating career advice: {e}")
            return "Lo siento, no pude generar consejos personalizados en este momento. Te recomiendo explorar cursos de programación básica y plataformas como LinkedIn Learning para comenzar tu transición al sector tecnológico."

    def save_user_profile_to_db(self, user_id: int, analysis_result: Dict[str, Any], 
                               resume_path: str) -> bool:
        """
        Save analyzed user profile information to database
        
        Args:
            user_id: User ID
            analysis_result: Analyzed CV information
            resume_path: Path to the resume file
            
        Returns:
            bool: Success status
        """
        conn = connect()
        if conn is None:
            logger.error("Failed to connect to database")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Map analysis results to database fields
            education_mapping = {
                'no_formal': EducationLevelEnum.no_formal,
                'primary': EducationLevelEnum.primary,
                'secondary': EducationLevelEnum.secondary,
                'high_school': EducationLevelEnum.high_school,
                'vocational': EducationLevelEnum.vocational,
                'bachelors': EducationLevelEnum.bachelors,
                'masters': EducationLevelEnum.masters,
                'phd': EducationLevelEnum.phd
            }
            
            digital_mapping = {
                'basic': DigitalLevelEnum.basic,
                'intermediate': DigitalLevelEnum.intermediate,
                'advanced': DigitalLevelEnum.advanced,
                'expert': DigitalLevelEnum.expert
            }
            
            education_level = education_mapping.get(
                analysis_result.get('education_level', 'secondary'), 
                EducationLevelEnum.secondary
            )
            
            digital_level = digital_mapping.get(
                analysis_result.get('digital_level', 'basic'),
                DigitalLevelEnum.basic
            )
            
            # Check if user profile already exists
            cursor.execute(
                "SELECT id FROM user_personal_info WHERE user_id = %s",
                (user_id,)
            )
            existing_profile = cursor.fetchone()
            
            if existing_profile:
                # Update existing profile
                cursor.execute("""
                    UPDATE user_personal_info 
                    SET full_name = %s, education_level = %s, previous_experience = %s,
                        main_skills = %s, area_of_interest = %s, digital_level = %s,
                        resume_path = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (
                    analysis_result.get('full_name'),
                    education_level.value,
                    analysis_result.get('previous_experience'),
                    analysis_result.get('main_skills'),
                    analysis_result.get('area_of_interest'),
                    digital_level.value,
                    resume_path,
                    user_id
                ))
                logger.info(f"Updated user profile for user_id: {user_id}")
            else:
                # Insert new profile
                cursor.execute("""
                    INSERT INTO user_personal_info 
                    (user_id, full_name, education_level, previous_experience, 
                     main_skills, area_of_interest, digital_level, resume_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    analysis_result.get('full_name'),
                    education_level.value,
                    analysis_result.get('previous_experience'),
                    analysis_result.get('main_skills'),
                    analysis_result.get('area_of_interest'),
                    digital_level.value,
                    resume_path
                ))
                logger.info(f"Created new user profile for user_id: {user_id}")
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving user profile to database: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            disconnect(conn)

    def process_cv_and_generate_advice(self, user_id: int, cv_text: str) -> Dict[str, Any]:
        """
        Complete pipeline: process CV text and generate career advice
        Simplificado para trabajar con texto ya extraído
        
        Args:
            user_id: User ID
            cv_text: Text content of the CV (already extracted)
            
        Returns:
            Dict containing analysis results and advice
        """
        try:
            logger.info(f"Starting CV processing for user_id: {user_id}")
            
            # Step 1: Analyze CV content
            analysis_result = self.analyze_cv_content(cv_text)
            
            # Step 2: Save to database (without embedding)
            db_success = self.save_user_profile_to_db(
                user_id, analysis_result, "processed_cv.txt"
            )
            
            # Step 3: Generate career advice
            career_advice = self.generate_career_advice(analysis_result)
            
            result = {
                "success": True,
                "user_id": user_id,
                "analysis": analysis_result,
                "career_advice": career_advice,
                "database_saved": db_success,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"CV processing completed successfully for user_id: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in CV processing pipeline: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "processed_at": datetime.now().isoformat()
            }


# Convenience functions for external use - Simplificadas
def analyze_user_cv(user_id: int, cv_text: str) -> Dict[str, Any]:
    """
    Analyze a user's CV text and provide career transition advice
    Simplificado para trabajar con texto en lugar de archivo
    
    Args:
        user_id: User ID
        cv_text: CV text content
        
    Returns:
        Dict containing analysis and advice
    """
    analyzer = CVAnalyzer()
    return analyzer.process_cv_and_generate_advice(user_id, cv_text)


def get_career_advice_for_profile(user_id: int) -> Optional[str]:
    """
    Generate career advice for an existing user profile
    
    Args:
        user_id: User ID
        
    Returns:
        Career advice string or None if profile not found
    """
    conn = connect()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT full_name, education_level, previous_experience, 
                   main_skills, area_of_interest, digital_level
            FROM user_personal_info 
            WHERE user_id = %s
        """, (user_id,))
        
        profile = cursor.fetchone()
        if not profile:
            return None
        
        # Convert to analysis format
        analysis_result = {
            "full_name": profile[0] or "Usuario",
            "education_level": profile[1] or "secondary",
            "previous_experience": profile[2] or "Sin experiencia detectada",
            "main_skills": profile[3] or "Habilidades por definir",
            "area_of_interest": profile[4] or "Tecnología",
            "digital_level": profile[5] or "basic",
            "current_sector": "Sector actual",
            "years_experience": 0,
            "tech_readiness": 5
        }
        
        analyzer = CVAnalyzer()
        return analyzer.generate_career_advice(analysis_result)
        
    except Exception as e:
        logger.error(f"Error getting career advice for profile: {e}")
        return None
    finally:
        cursor.close()
        disconnect(conn)


if __name__ == "__main__":
    # Test simple del analyzer refactorizado
    try:
        analyzer = CVAnalyzer()
        logger.info("✅ CV Analyzer refactorizado inicializado correctamente")
        logger.info(f"🤖 Modelo LLM: llama-3.1-8b-instant")
        logger.info("🧹 Código refactorizado - Solo métodos utilizados")
    except Exception as e:
        logger.error(f"❌ Error en CV Analyzer refactorizado: {e}")