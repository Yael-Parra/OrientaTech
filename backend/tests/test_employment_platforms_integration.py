"""
Test script for Employment Platforms Integration
Tests the new functionality for including employment platforms in RAG analysis
"""

import asyncio
import sys
import os
from loguru import logger

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.employment_platforms_service import get_employment_platforms_service
from services.rag_llm_integration_service import get_rag_llm_integration_service


async def test_employment_platforms_service():
    """Test the employment platforms service functionality"""
    logger.info("🧪 Testing Employment Platforms Service...")
    
    service = get_employment_platforms_service()
    
    # Test 1: Get platforms summary
    logger.info("1️⃣ Testing platforms summary...")
    summary = await service.get_platforms_summary()
    print(f"Summary: {summary}")
    
    # Test 2: Search for relevant platforms
    logger.info("2️⃣ Testing platform search...")
    test_queries = [
        "desarrollador python",
        "data scientist",
        "frontend developer",
        "marketing digital"
    ]
    
    for query in test_queries:
        platforms = await service.get_relevant_platforms(
            query=query,
            limit=5
        )
        print(f"\nQuery: '{query}' -> Found {len(platforms)} platforms")
        
        # Format for prompt
        formatted = service.format_platforms_for_prompt(platforms, include_descriptions=True)
        print(f"Formatted output (first 200 chars): {formatted[:200]}...")
    
    # Test 3: Get platforms by categories
    logger.info("3️⃣ Testing platforms by categories...")
    categories = ["technology", "remote", "startup"]
    platforms_by_category = await service.get_platforms_by_categories(
        categories=categories,
        limit_per_category=2
    )
    
    for category, platforms in platforms_by_category.items():
        print(f"Category '{category}': {len(platforms)} platforms")


async def test_enhanced_rag_integration():
    """Test the enhanced RAG integration with platforms"""
    logger.info("🧪 Testing Enhanced RAG Integration...")
    
    # Mock search results (simulate RAG search output)
    mock_search_results = [
        {
            'document_id': 'doc1',
            'content': 'Desarrollador Python con 3 años de experiencia en Django y Flask. Conocimiento en bases de datos PostgreSQL y MongoDB. Experiencia con Docker y AWS.',
            'document_type': 'cv',
            'original_filename': 'cv_python_developer.pdf',
            'similarity_percentage': 92.5,
            'chunk_index': 0
        },
        {
            'document_id': 'doc2',
            'content': 'Experiencia en desarrollo web frontend con React y Vue.js. Conocimientos de JavaScript ES6+, TypeScript, HTML5 y CSS3. Familiaridad con metodologías ágiles.',
            'document_type': 'cv',
            'original_filename': 'cv_frontend_developer.pdf',
            'similarity_percentage': 87.3,
            'chunk_index': 0
        }
    ]
    
    test_queries = [
        "Oportunidades para desarrollador Python",
        "Trabajos remotos en tecnología",
        "Posiciones frontend React"
    ]
    
    integration_service = get_rag_llm_integration_service()
    
    for query in test_queries:
        logger.info(f"🔍 Testing query: '{query}'")
        
        try:
            # Test enhanced analysis with platforms
            context_analysis, career_advice, processing_time = await integration_service.analyze_search_context_with_platforms(
                search_results=mock_search_results,
                user_query=query,
                user_profile=None
            )
            
            print(f"\n✅ Query: '{query}'")
            print(f"Processing time: {processing_time:.2f}s")
            print(f"Context analysis: {'✓' if context_analysis else '✗'}")
            print(f"Career advice: {'✓' if career_advice else '✗'}")
            
            if context_analysis:
                print(f"Context summary: {context_analysis.context_summary[:100]}...")
                print(f"Skill patterns: {context_analysis.skill_patterns[:3]}")
            
            if career_advice:
                print(f"Advice preview: {career_advice.search_analysis[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Error testing query '{query}': {e}")


async def test_platform_keywords_extraction():
    """Test keyword extraction for platform search"""
    logger.info("🧪 Testing Platform Keywords Extraction...")
    
    from models.rag_models import LLMContextAnalysis
    
    # Mock context analysis
    mock_context = LLMContextAnalysis(
        context_summary="Desarrollador con experiencia en Python y React",
        skill_patterns=["Python", "Django", "React", "JavaScript", "PostgreSQL"],
        experience_level="Intermedio con 3 años de experiencia",
        tech_readiness_avg=7.5,
        dominant_sectors=["Desarrollo web", "Tecnología"],
        transition_opportunities=["Full-stack developer", "Backend engineer"],
        matching_quality=8.5,
        key_strengths=["Programación", "Bases de datos"],
        improvement_areas=["DevOps", "Cloud computing"]
    )
    
    integration_service = get_rag_llm_integration_service()
    
    test_queries = [
        "Trabajo para desarrollador Python junior",
        "Oportunidades remotas en frontend",
        "Posiciones senior backend engineer"
    ]
    
    for query in test_queries:
        keywords = integration_service._extract_platform_keywords(query, mock_context)
        print(f"Query: '{query}'")
        print(f"Extracted keywords: {keywords}")
        print()


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Employment Platforms Integration Tests")
    
    print("=" * 60)
    await test_employment_platforms_service()
    
    print("\n" + "=" * 60)
    await test_platform_keywords_extraction()
    
    print("\n" + "=" * 60)
    await test_enhanced_rag_integration()
    
    logger.success("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())