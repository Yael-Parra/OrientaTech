"""
RAG + LLM Integration Service for OrientaTech
Provides contextual analysis of search results using LLM
"""
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from loguru import logger

from agent.langchain import CVAnalyzer
from agent.prompting import get_search_context_analysis_prompt, get_contextual_career_advice_prompt
from models.rag_models import LLMContextAnalysis, LLMCareerAdvice


class RAGLLMIntegrationService:
    """
    Service for integrating RAG search results with LLM analysis
    
    Features:
    - Contextual analysis of multiple documents found by RAG
    - Career advice based on search context and user profile
    - Token management and optimization
    - Error handling and fallbacks
    """
    
    def __init__(self):
        """Initialize the integration service"""
        self.cv_analyzer = CVAnalyzer()
        self.max_tokens = 20000  # Adjusted for Llama 3.1 8B Instant
        self.max_documents = 10  # Maximum documents to analyze
        
        # Create prompts directory in docs/temp for better organization
        self.prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'temp')
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        logger.debug("RAGLLMIntegrationService initialized")
    
    async def analyze_search_context(
        self,
        search_results: List[Dict],
        user_query: str,
        user_profile: Optional[Dict] = None
    ) -> Tuple[Optional[LLMContextAnalysis], Optional[LLMCareerAdvice], float]:
        """
        Analyze search results context using LLM and generate contextual advice
        
        Args:
            search_results: Results from RAG search containing document content
            user_query: Original search query from user
            user_profile: Optional user profile information
            
        Returns:
            Tuple of (context_analysis, career_advice, processing_time)
        """
        start_time = time.time()
        
        try:
            # Step 1: Prepare documents context for LLM
            documents_context = self._prepare_documents_context(search_results)
            
            if not documents_context.strip():
                logger.warning("No valid document content to analyze")
                return None, None, 0.0
            
            # Step 2: Generate context analysis
            context_analysis = await self._generate_context_analysis(
                user_query, documents_context
            )
            
            # Step 3: Generate contextual career advice
            career_advice = await self._generate_contextual_advice(
                user_query, context_analysis, user_profile
            )
            
            processing_time = time.time() - start_time
            logger.success(f"✅ LLM analysis completed in {processing_time:.2f}s")
            
            return context_analysis, career_advice, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error in LLM analysis: {e}")
            return None, None, processing_time
    
    def _prepare_documents_context(self, search_results: List[Dict]) -> str:
        """
        Prepare documents context for LLM analysis with token management
        
        Args:
            search_results: RAG search results
            
        Returns:
            str: Formatted context for LLM
        """
        if not search_results:
            return ""
        
        context_parts = []
        estimated_tokens = 0
        documents_included = 0
        
        for result in search_results[:self.max_documents]:
            # Extract document content
            content = result.get('content_text', '') or result.get('content_preview', '')
            if not content:
                continue
            
            # Estimate tokens (rough approximation: 1.3 tokens per word)
            content_tokens = len(content.split()) * 1.3
            
            # Check if adding this document would exceed token limit
            if estimated_tokens + content_tokens > self.max_tokens:
                logger.warning(f"Token limit reached, stopping at {documents_included} documents")
                break
            
            # Format document for LLM
            doc_context = f"""
--- DOCUMENTO {result.get('document_id', 'unknown')} (Relevancia: {result.get('similarity_percentage', 0):.1f}%) ---
Tipo: {result.get('document_type', 'unknown')}
Archivo: {result.get('original_filename', 'unknown')}
Contenido:
{content}
"""
            
            context_parts.append(doc_context)
            estimated_tokens += content_tokens
            documents_included += 1
        
        if documents_included == 0:
            logger.warning("No documents with content available for LLM analysis")
            return ""
        
        final_context = "\n".join(context_parts)
        logger.info(f"Prepared context: {documents_included} docs, ~{estimated_tokens:.0f} tokens")
        
        return final_context
    
    def _save_prompt_to_file(self, prompt: str, prompt_type: str, user_query: str) -> str:
        """
        Save prompt to text file for debugging and transparency
        
        Args:
            prompt: Complete prompt sent to LLM
            prompt_type: Type of prompt ('context_analysis' or 'career_advice')
            user_query: Original user query for filename
            
        Returns:
            str: Path to saved file
        """
        try:
            # Create safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c for c in user_query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_query = safe_query.replace(' ', '_')[:50]  # Limit length
            
            filename = f"{timestamp}_{prompt_type}_{safe_query}.txt"
            filepath = os.path.join(self.prompts_dir, filename)
            
            # Create content with metadata
            content = f"""# PROMPT ENVIADO AL LLM - OrientaTech
# Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Tipo: {prompt_type}
# Query Usuario: {user_query}
# Modelo LLM: llama-3.1-8b-instant
# ======================================================

{prompt}

# ======================================================
# FIN DEL PROMPT
# ======================================================
"""
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"📄 Prompt guardado en: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error guardando prompt: {e}")
            return ""
    
    def _save_llm_response_to_file(self, response: str, prompt_type: str, user_query: str) -> str:
        """
        Save LLM response to text file for debugging
        
        Args:
            response: LLM response content
            prompt_type: Type of prompt ('context_analysis' or 'career_advice')
            user_query: Original user query for filename
            
        Returns:
            str: Path to saved file
        """
        try:
            # Create safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c for c in user_query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_query = safe_query.replace(' ', '_')[:50]
            
            filename = f"{timestamp}_RESPONSE_{prompt_type}_{safe_query}.txt"
            filepath = os.path.join(self.prompts_dir, filename)
            
            # Create content with metadata
            content = f"""# RESPUESTA DEL LLM - OrientaTech
# Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Tipo: {prompt_type}
# Query Usuario: {user_query}
# Modelo LLM: llama-3.1-8b-instant
# ======================================================

{response}

# ======================================================
# FIN DE LA RESPUESTA
# ======================================================
"""
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"📥 Respuesta LLM guardada en: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error guardando respuesta LLM: {e}")
            return ""
    
    async def _generate_context_analysis(
        self,
        user_query: str,
        documents_context: str
    ) -> Optional[LLMContextAnalysis]:
        """
        Generate contextual analysis of documents using LLM
        
        Args:
            user_query: Original search query
            documents_context: Formatted document content
            
        Returns:
            LLMContextAnalysis or None if failed
        """
        try:
            # Get prompt template
            prompt_template = get_search_context_analysis_prompt()
            prompt = prompt_template.format(
                user_query=user_query,
                documents_context=documents_context
            )
            
            # 📄 GUARDAR PROMPT EN ARCHIVO
            prompt_file = self._save_prompt_to_file(
                prompt=prompt,
                prompt_type="context_analysis", 
                user_query=user_query
            )
            logger.info(f"🔍 Prompt de análisis contextual guardado en archivo")
            
            # Call LLM
            logger.info("Generating context analysis with LLM...")
            response = self.cv_analyzer.llm.invoke(prompt)
            
            # 📥 GUARDAR RESPUESTA EN ARCHIVO
            self._save_llm_response_to_file(
                response=response.content,
                prompt_type="context_analysis",
                user_query=user_query
            )
            
            # Parse JSON response
            analysis_json = self._extract_json_from_response(response.content)
            if not analysis_json:
                logger.error("Failed to extract JSON from LLM response")
                return None
            
            # Create Pydantic model
            context_analysis = LLMContextAnalysis(**analysis_json)
            logger.success("✅ Context analysis generated successfully")
            
            return context_analysis
            
        except Exception as e:
            logger.error(f"Error generating context analysis: {e}")
            return None
    
    async def _generate_contextual_advice(
        self,
        user_query: str,
        context_analysis: Optional[LLMContextAnalysis],
        user_profile: Optional[Dict]
    ) -> Optional[LLMCareerAdvice]:
        """
        Generate contextual career advice using LLM
        
        Args:
            user_query: Original search query
            context_analysis: Context analysis from previous step
            user_profile: Optional user profile
            
        Returns:
            LLMCareerAdvice or None if failed
        """
        try:
            if not context_analysis:
                logger.warning("No context analysis available, skipping advice generation")
                return None
            
            # Get prompt template
            prompt_template = get_contextual_career_advice_prompt()
            prompt = prompt_template.format(
                user_query=user_query,
                context_analysis=context_analysis.dict() if context_analysis else {},
                user_profile=user_profile or "No hay información de perfil disponible"
            )
            
            # 📄 GUARDAR PROMPT EN ARCHIVO
            prompt_file = self._save_prompt_to_file(
                prompt=prompt,
                prompt_type="career_advice",
                user_query=user_query
            )
            logger.info(f"💡 Prompt de consejos de carrera guardado en archivo")
            
            # Call LLM
            logger.info("Generating contextual career advice with LLM...")
            response = self.cv_analyzer.llm.invoke(prompt)
            
            # 📥 GUARDAR RESPUESTA EN ARCHIVO
            self._save_llm_response_to_file(
                response=response.content,
                prompt_type="career_advice",
                user_query=user_query
            )
            
            # Parse structured response
            advice_dict = self._parse_advice_response(response.content)
            if not advice_dict:
                logger.error("Failed to parse career advice from LLM response")
                return None
            
            # Create Pydantic model
            career_advice = LLMCareerAdvice(**advice_dict)
            logger.success("✅ Contextual career advice generated successfully")
            
            return career_advice
            
        except Exception as e:
            logger.error(f"Error generating contextual advice: {e}")
            return None
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """
        Extract JSON from LLM response
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Dict with parsed JSON or None if failed
        """
        try:
            # Try to find JSON in response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                logger.error("No JSON found in LLM response")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            return None
    
    def _parse_advice_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse career advice response from LLM
        
        Args:
            response_text: Raw LLM response with advice sections
            
        Returns:
            Dict with parsed advice sections or None if failed
        """
        try:
            # Split response into sections
            sections = {}
            import re
            
            # Define section patterns - support both numbered and non-numbered formats
            section_patterns = {
                'search_analysis': [
                    r'(?:1\)\s*)?\*\*Análisis de tu búsqueda\*\*:?\s*\n\n?(.*?)(?=\*\*[A-Za-z]|$)',
                    r'(?:1\)\s*)?\*\*Análisis de tu búsqueda\*\*:?\s*(.*?)(?=\*\*[A-Za-z]|$)'
                ],
                'profile_comparison': [
                    r'(?:2\)\s*)?\*\*Comparación con tu perfil\*\*:?\s*\n\n?(.*?)(?=\*\*[A-Za-z]|$)',
                    r'(?:2\)\s*)?\*\*Comparación con tu perfil\*\*:?\s*(.*?)(?=\*\*[A-Za-z]|$)'
                ],
                'identified_opportunities': [
                    r'(?:3\)\s*)?\*\*Oportunidades identificadas\*\*:?\s*\n\n?(.*?)(?=\*\*[A-Za-z]|$)',
                    r'(?:3\)\s*)?\*\*Oportunidades identificadas\*\*:?\s*(.*?)(?=\*\*[A-Za-z]|$)'
                ],
                'skill_gaps': [
                    r'(?:4\)\s*)?\*\*Brechas de habilidades\*\*:?\s*\n\n?(.*?)(?=\*\*[A-Za-z]|$)',
                    r'(?:4\)\s*)?\*\*Brechas de habilidades\*\*:?\s*(.*?)(?=\*\*[A-Za-z]|$)'
                ],
                'concrete_steps': [
                    r'(?:5\)\s*)?\*\*Pasos concretos\*\*:?\s*\n\n?(.*?)(?=\*\*[A-Za-z]|$)',
                    r'(?:5\)\s*)?\*\*Pasos concretos\*\*:?\s*(.*?)(?=\*\*[A-Za-z]|$)'
                ],
                'recommended_resources': [
                    r'(?:6\)\s*)?\*\*Recursos recomendados\*\*:?\s*\n\n?(.*?)(?=\*\*[A-Za-z]|$)',
                    r'(?:6\)\s*)?\*\*Recursos recomendados\*\*:?\s*(.*?)(?=\*\*[A-Za-z]|$)'
                ],
                'application_strategy': [
                    r'(?:7\)\s*)?\*\*Estrategia de aplicación\*\*:?\s*\n\n?(.*?)(?=\*\*[A-Za-z]|$)',
                    r'(?:7\)\s*)?\*\*Estrategia de aplicación\*\*:?\s*(.*?)(?=\*\*[A-Za-z]|$)'
                ],
                'next_steps': [
                    r'(?:8\)\s*)?\*\*Próximos pasos personalizados\*\*:?\s*\n\n?(.*?)(?:#|$)',
                    r'(?:8\)\s*)?\*\*Próximos pasos personalizados\*\*:?\s*(.*?)(?:#|$)'
                ]
            }
            
            # Try to extract each section using multiple patterns
            for key, patterns in section_patterns.items():
                found = False
                for pattern in patterns:
                    match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()
                        if content and len(content) > 10:  # Valid content found
                            sections[key] = content
                            found = True
                            break
                
                # If no pattern matched, set placeholder
                if not found:
                    sections[key] = "Información no disponible en esta sección"
            
            # Check if we successfully parsed any meaningful content
            meaningful_sections = sum(1 for v in sections.values() if v != "Información no disponible en esta sección")
            
            # If few sections were parsed successfully, try fallback approach
            if meaningful_sections < 3:
                logger.warning(f"Only {meaningful_sections} sections parsed successfully, trying fallback")
                sections = self._parse_advice_fallback(response_text)
            
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing advice response: {e}")
            return None
    
    def _parse_advice_fallback(self, response_text: str) -> Dict:
        """
        Fallback method to parse advice when structured parsing fails
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Dict with extracted content using simpler approach
        """
        import re
        
        # Split by markdown headers (** ... **)
        sections = re.split(r'\*\*([^*]+)\*\*', response_text)
        content_dict = {}
        
        # Map common Spanish headers to our field names
        header_mapping = {
            'análisis de tu búsqueda': 'search_analysis',
            'comparación con tu perfil': 'profile_comparison', 
            'oportunidades identificadas': 'identified_opportunities',
            'brechas de habilidades': 'skill_gaps',
            'pasos concretos': 'concrete_steps',
            'recursos recomendados': 'recommended_resources',
            'estrategia de aplicación': 'application_strategy',
            'próximos pasos personalizados': 'next_steps'
        }
        
        # Process sections in pairs (header, content)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                header = sections[i].lower().strip()
                content = sections[i + 1].strip()
                
                # Find matching field name
                for spanish_header, field_name in header_mapping.items():
                    if spanish_header in header:
                        if content and len(content) > 10:
                            content_dict[field_name] = content
                        break
        
        # Fill missing fields with fallback content
        all_fields = ['search_analysis', 'profile_comparison', 'identified_opportunities', 
                     'skill_gaps', 'concrete_steps', 'recommended_resources', 
                     'application_strategy', 'next_steps']
        
        for field in all_fields:
            if field not in content_dict:
                if len(response_text) > 100:
                    content_dict[field] = f"Contenido disponible en respuesta completa del LLM (ver logs para detalles)"
                else:
                    content_dict[field] = "Información no disponible en esta sección"
        
        return content_dict

    def get_service_info(self) -> Dict:
        """
        Get information about the integration service
        
        Returns:
            Dict: Service configuration and status
        """
        return {
            'service': 'RAGLLMIntegrationService',
            'version': '1.1.0',  # Updated version
            'llm_model': 'llama-3.1-8b-instant',  # Modelo actualizado
            'max_tokens': self.max_tokens,
            'max_documents': self.max_documents,
            'prompt_logging': True,  # Nueva funcionalidad
            'prompts_directory': self.prompts_dir,  # Directorio de prompts
            'features': [
                'contextual_document_analysis',
                'career_advice_generation',
                'token_management',
                'error_handling',
                'prompt_logging',  # Nueva característica
                'response_logging'  # Nueva característica
            ]
        }


# ===================================
# Singleton instance
# ===================================

_integration_service_instance: Optional[RAGLLMIntegrationService] = None

def get_rag_llm_integration_service() -> RAGLLMIntegrationService:
    """
    Get singleton instance of RAGLLMIntegrationService
    
    Returns:
        RAGLLMIntegrationService: Singleton instance
    """
    global _integration_service_instance
    
    if _integration_service_instance is None:
        _integration_service_instance = RAGLLMIntegrationService()
    
    return _integration_service_instance


# ===================================
# Testing
# ===================================

if __name__ == "__main__":
    """Test the integration service"""
    import asyncio
    
    async def test_integration_service():
        logger.info("Testing RAGLLMIntegrationService...")
        
        # Create service
        service = RAGLLMIntegrationService()
        
        # Test service info
        info = service.get_service_info()
        logger.info(f"✅ Service info: {info['service']}")
        logger.info(f"   LLM model: {info['llm_model']}")
        logger.info(f"   Max tokens: {info['max_tokens']}")
        
        logger.success("🎉 Integration service test completed!")
    
    # Run test
    asyncio.run(test_integration_service())