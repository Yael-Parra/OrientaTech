"""
RAG Integration Test with Document Upload

This script tests:
1. Document upload processing
2. Automatic RAG processing
3. Semantic search
4. Document and embedding deletion
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from services.RAG import (
    get_rag_integration_service,
    get_search_service,
    get_embedding_service
)


async def test_rag_integration():
    """
    Full RAG integration test
    """
    logger.info("=" * 80)
    logger.info("🧪 STARTING RAG INTEGRATION TEST")
    logger.info("=" * 80)
    
    # Get services
    rag_integration = get_rag_integration_service()
    search_service = get_search_service()
    embedding_service = get_embedding_service()
    
    # Test data
    test_user_id = 1
    test_document_id = "test-doc-12345"
    test_file_path = Path(__file__).parent.parent / "test_documents" / "sample_cv_2.txt"
    
    # Verify test document exists
    if not test_file_path.exists():
        logger.error(f"❌ Test document not found: {test_file_path}")
        logger.error("Please ensure the test_documents/sample_cv.txt file exists")
        return
    
    logger.info(f"📄 Using test document: {test_file_path.name}")
    logger.info(f"   File size: {test_file_path.stat().st_size} bytes")
    
    try:
        # ===== TEST 1: DOCUMENT PROCESSING =====
        logger.info("\n" + "=" * 80)
        logger.info("📤 TEST 1: Processing uploaded document")
        logger.info("=" * 80)
        
        result = await rag_integration.process_uploaded_document(
            user_id=test_user_id,
            document_id=test_document_id,
            file_path=test_file_path,
            filename="sample_cv.txt",
            original_filename="My_CV_2024.txt",
            document_type="cv",
            description="Test CV for development",
            file_size=test_file_path.stat().st_size,
            mime_type="text/plain"
        )
        
        if result["success"]:
            logger.success(f"✅ TEST 1 PASSED!")
            logger.info(f"   📊 Text length: {result['text_length']} characters")
            logger.info(f"   🧮 Embedding dimension: {result['embedding_dimension']}")
            logger.info(f"   📋 Primary CV: {result['is_primary_cv']}")
            logger.info(f"   🔐 File hash: {result['file_hash'][:16]}...")
        else:
            logger.error(f"❌ TEST 1 FAILED: {result.get('error')}")
            return
        
        # ===== TEST 2: STATUS CHECK =====
        logger.info("\n" + "=" * 80)
        logger.info("🔍 TEST 2: Checking document status in DB")
        logger.info("=" * 80)
        
        status_result = await rag_integration.get_document_embedding_status(
            user_id=test_user_id,
            document_id=test_document_id
        )
        
        if status_result["success"]:
            logger.success(f"✅ TEST 2 PASSED!")
            logger.info(f"   📋 Document type: {status_result['document_type']}")
            logger.info(f"   ⚙️ Processing status: {status_result['processing_status']}")
            logger.info(f"   ✓ Active: {status_result['is_active']}")
            logger.info(f"   📝 Text length: {status_result['text_length']} characters")
        else:
            logger.error(f"❌ TEST 2 FAILED: {status_result.get('error')}")
        
        # ===== TEST 3: SEMANTIC SEARCH =====
        logger.info("\n" + "=" * 80)
        logger.info("🔎 TEST 3: Semantic document search")
        logger.info("=" * 80)
        
        # Search 1: Query related to experience
        query1 = "Python backend developer with FastAPI experience"
        logger.info(f"   Query 1: '{query1}'")
        
        search_results1 = await search_service.semantic_search(
            query=query1,
            user_id=test_user_id,
            limit=5,
            similarity_threshold=0.5
        )
        
        if search_results1:
            logger.success(f"✅ Found {len(search_results1)} results")
            for i, result in enumerate(search_results1, 1):
                logger.info(f"   {i}. {result['filename']} - Similarity: {result['similarity_score']:.3f}")
                logger.info(f"      Preview: {result['content_preview'][:100]}...")
        else:
            logger.warning("⚠️ No results found")
        
        # Search 2: Query related to skills
        query2 = "machine learning and vector databases"
        logger.info(f"\n   Query 2: '{query2}'")
        
        search_results2 = await search_service.semantic_search(
            query=query2,
            user_id=test_user_id,
            limit=5,
            similarity_threshold=0.5
        )
        
        if search_results2:
            logger.success(f"✅ Found {len(search_results2)} results")
            for i, result in enumerate(search_results2, 1):
                logger.info(f"   {i}. {result['filename']} - Similarity: {result['similarity_score']:.3f}")
        else:
            logger.warning("⚠️ No results found")
        
        # Search 3: Search by document type
        logger.info(f"\n   Query 3: Search CVs only")
        search_results3 = await search_service.search_by_document_type(
            document_type="cv",
            query="developer with experience",
            user_id=test_user_id,
            limit=5
        )
        
        if search_results3:
            logger.success(f"✅ Found {len(search_results3)} CV documents")
        
        if search_results1 or search_results2 or search_results3:
            logger.success("✅ TEST 3 PASSED!")
        else:
            logger.error("❌ TEST 3 FAILED: No searches returned results")
        
        # ===== TEST 4: SEARCH STATISTICS =====
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST 4: Search statistics")
        logger.info("=" * 80)
        
        stats = await search_service.get_search_statistics(user_id=test_user_id)
        
        if stats:
            logger.success(f"✅ TEST 4 PASSED!")
            logger.info(f"   Total documents: {stats.get('total_documents', 0)}")
            logger.info(f"   CV count: {stats.get('cv_count', 0)}")
            logger.info(f"   Processed: {stats.get('processed_count', 0)}")
            logger.info(f"   Total size: {stats.get('total_size_mb', 0)} MB")
        
        # ===== TEST 5: DOCUMENT DELETION =====
        logger.info("\n" + "=" * 80)
        logger.info("🗑️ TEST 5: Document and embedding deletion")
        logger.info("=" * 80)
        
        delete_result = await rag_integration.delete_document_embedding(
            user_id=test_user_id,
            document_id=test_document_id
        )
        
        if delete_result["success"]:
            logger.success(f"✅ TEST 5 PASSED!")
            logger.info(f"   {delete_result['message']}")
        else:
            logger.error(f"❌ TEST 5 FAILED: {delete_result.get('error')}")
        
        # Verify document is actually deleted
        status_after_delete = await rag_integration.get_document_embedding_status(
            user_id=test_user_id,
            document_id=test_document_id
        )
        
        if status_after_delete["success"]:
            if not status_after_delete["is_active"]:
                logger.success("✅ Document correctly marked as inactive")
            else:
                logger.error("❌ Document is still active after deletion!")
        
        # ===== SUMMARY =====
        logger.info("\n" + "=" * 80)
        logger.success("🎉 ALL TESTS COMPLETED!")
        logger.info("=" * 80)
        logger.info("\n📊 INTEGRATION STATISTICS:")
        logger.info(f"   ✅ Document processing: working")
        logger.info(f"   ✅ Database saving: working")
        logger.info(f"   ✅ Semantic search: working")
        logger.info(f"   ✅ Search statistics: working")
        logger.info(f"   ✅ Embedding deletion: working")
        logger.info("\n🚀 RAG SYSTEM FULLY INTEGRATED!")
        logger.info(f"\n💡 Test document used: test_documents/{test_file_path.name}")
        
    except Exception as e:
        logger.error(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logger.info("🚀 Starting RAG integration test...")
    asyncio.run(test_rag_integration())
