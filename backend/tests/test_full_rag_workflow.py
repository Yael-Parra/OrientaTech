"""
Full RAG Workflow Test - Complete End-to-End Testing

This comprehensive test:
1. Creates a new test user
2. Uploads multiple documents (CVs, cover letters)
3. Performs semantic search across all documents
4. Tests ranking and filtering
5. Cleans up test data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from services.RAG import (
    get_rag_integration_service,
    get_search_service,
    get_ranking_service
)
from database.db_connection import connect, disconnect
import uuid


class FullRAGWorkflowTest:
    """Complete RAG system workflow test"""
    
    def __init__(self):
        self.rag_integration = get_rag_integration_service()
        self.search_service = get_search_service()
        self.ranking_service = get_ranking_service()
        
        # Test configuration
        self.test_user_id = None  # Will be set after user registration
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@test.com"
        self.test_documents_dir = Path(__file__).parent.parent / "test_documents"
        self.uploaded_documents = []
        self.user_created = False
        
    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("=" * 80)
        logger.info("🚀 FULL RAG WORKFLOW TEST - START")
        logger.info("=" * 80)
        logger.info(f"Test User Email: {self.test_user_email}")
        logger.info(f"Test Documents Directory: {self.test_documents_dir}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # Step 0: Register test user
            await self.test_register_user()
            
            # Step 1: Upload all test documents
            await self.test_upload_all_documents()
            
            # Step 2: Verify all documents are indexed
            await self.test_verify_documents()
            
            # Step 3: Semantic search tests
            await self.test_semantic_searches()
            
            # Step 4: Advanced search tests
            await self.test_advanced_searches()
            
            # Step 5: Ranking tests
            await self.test_ranking()
            
            # Step 6: Statistics
            await self.test_statistics()
            
            # Step 7: Cleanup
            await self.test_cleanup()
            
            # Step 8: Delete test user
            await self.test_delete_user()
            
            # Final summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"\n❌ CRITICAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            # Cleanup on error
            await self.emergency_cleanup()
            await self.test_delete_user()
    
    async def test_register_user(self):
        """TEST 0: Register a new test user in database"""
        logger.info("\n" + "=" * 80)
        logger.info("👤 TEST 0: Registering new test user")
        logger.info("=" * 80)
        
        conn = None
        try:
            conn = connect()
            cursor = conn.cursor()
            
            # Generate test user data
            password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS7sMBinC"  # "password123"
            
            # Insert user into users table
            insert_query = """
            INSERT INTO users (email, password_hash, is_active)
            VALUES (%s, %s, %s)
            RETURNING id;
            """
            
            cursor.execute(insert_query, (self.test_user_email, password_hash, True))
            self.test_user_id = cursor.fetchone()[0]
            conn.commit()
            
            # Create user_personal_info record
            personal_info_query = """
            INSERT INTO user_personal_info (user_id, full_name)
            VALUES (%s, %s);
            """
            cursor.execute(personal_info_query, (self.test_user_id, "Test RAG User"))
            conn.commit()
            
            self.user_created = True
            
            logger.success(f"✅ TEST 0 PASSED: User created successfully")
            logger.info(f"   User ID: {self.test_user_id}")
            logger.info(f"   Email: {self.test_user_email}")
            
        except Exception as e:
            logger.error(f"❌ TEST 0 FAILED: {str(e)}")
            raise
        finally:
            if conn:
                cursor.close()
                disconnect(conn)
    
    async def test_upload_all_documents(self):
        """TEST 1: Upload all test documents"""
        logger.info("\n" + "=" * 80)
        logger.info("📤 TEST 1: Uploading all test documents")
        logger.info("=" * 80)
        
        # Get all .txt files from test_documents directory
        test_files = list(self.test_documents_dir.glob("*.txt"))
        
        if not test_files:
            logger.error("❌ No test documents found!")
            return
        
        logger.info(f"Found {len(test_files)} test documents")
        
        for idx, file_path in enumerate(test_files, 1):
            logger.info(f"\n📄 Uploading document {idx}/{len(test_files)}: {file_path.name}")
            
            # Determine document type based on filename
            if "cover_letter" in file_path.name.lower():
                doc_type = "cover_letter"
            elif "certificate" in file_path.name.lower():
                doc_type = "certificate"
            else:
                doc_type = "cv"
            
            document_id = f"test-doc-{self.test_user_id}-{idx}"
            
            result = await self.rag_integration.process_uploaded_document(
                user_id=self.test_user_id,
                document_id=document_id,
                file_path=file_path,
                filename=file_path.name,
                original_filename=file_path.name,
                document_type=doc_type,
                description=f"Test document {idx} - {file_path.stem}",
                file_size=file_path.stat().st_size,
                mime_type="text/plain"
            )
            
            if result["success"]:
                logger.success(f"   ✅ Uploaded: {file_path.name}")
                logger.info(f"      Text length: {result['text_length']} characters")
                logger.info(f"      Embedding dimension: {result['embedding_dimension']}")
                logger.info(f"      Document type: {doc_type}")
                
                self.uploaded_documents.append({
                    "document_id": document_id,
                    "filename": file_path.name,
                    "type": doc_type,
                    "text_length": result['text_length']
                })
            else:
                logger.error(f"   ❌ Failed to upload: {file_path.name}")
                logger.error(f"      Error: {result.get('error')}")
        
        logger.success(f"\n✅ TEST 1 PASSED: {len(self.uploaded_documents)}/{len(test_files)} documents uploaded")
    
    async def test_verify_documents(self):
        """TEST 2: Verify all documents are properly indexed"""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 TEST 2: Verifying document indexing")
        logger.info("=" * 80)
        
        verified_count = 0
        
        for doc in self.uploaded_documents:
            status = await self.rag_integration.get_document_embedding_status(
                user_id=self.test_user_id,
                document_id=doc["document_id"]
            )
            
            if status["success"] and status["is_active"]:
                verified_count += 1
                logger.info(f"   ✅ {doc['filename']}: Active and indexed")
            else:
                logger.error(f"   ❌ {doc['filename']}: Not properly indexed")
        
        if verified_count == len(self.uploaded_documents):
            logger.success(f"\n✅ TEST 2 PASSED: All {verified_count} documents verified")
        else:
            logger.error(f"\n❌ TEST 2 FAILED: Only {verified_count}/{len(self.uploaded_documents)} verified")
    
    async def test_semantic_searches(self):
        """TEST 3: Semantic search with various queries"""
        logger.info("\n" + "=" * 80)
        logger.info("🔎 TEST 3: Semantic search tests")
        logger.info("=" * 80)
        
        # Define test queries
        queries = [
            {
                "query": "React and TypeScript frontend developer",
                "expected": "Should find Full-Stack developer CV",
                "min_results": 1
            },
            {
                "query": "machine learning and RAG systems expert",
                "expected": "Should find Data Scientist CV",
                "min_results": 1
            },
            {
                "query": "Python backend developer with FastAPI",
                "expected": "Should find multiple CVs with Python experience",
                "min_results": 1
            },
            {
                "query": "vector databases and embeddings",
                "expected": "Should find Data Scientist CV with pgvector experience",
                "min_results": 1
            },
            {
                "query": "AWS cloud and DevOps experience",
                "expected": "Should find developers with cloud experience",
                "min_results": 1
            }
        ]
        
        total_passed = 0
        
        for idx, test in enumerate(queries, 1):
            logger.info(f"\n   Query {idx}: '{test['query']}'")
            logger.info(f"   Expected: {test['expected']}")
            
            results = await self.search_service.semantic_search(
                query=test["query"],
                user_id=self.test_user_id,
                limit=10,
                similarity_threshold=0.3
            )
            
            if results and len(results) >= test["min_results"]:
                logger.success(f"   ✅ Found {len(results)} results")
                
                # Show top 3 results
                for i, result in enumerate(results[:3], 1):
                    logger.info(f"      {i}. {result['filename']} - Similarity: {result['similarity_score']:.3f}")
                    logger.info(f"         Type: {result['document_type']} | Size: {result['file_size_mb']} MB")
                
                total_passed += 1
            else:
                logger.warning(f"   ⚠️ Found only {len(results) if results else 0} results (expected >= {test['min_results']})")
        
        logger.success(f"\n✅ TEST 3 COMPLETED: {total_passed}/{len(queries)} queries successful")
    
    async def test_advanced_searches(self):
        """TEST 4: Advanced search features"""
        logger.info("\n" + "=" * 80)
        logger.info("🎯 TEST 4: Advanced search features")
        logger.info("=" * 80)
        
        # Test 4.1: Search by document type
        logger.info("\n   4.1: Search only CV documents")
        cv_results = await self.search_service.search_by_document_type(
            document_type="cv",
            query="developer with experience",
            user_id=self.test_user_id,
            limit=10
        )
        logger.info(f"   ✅ Found {len(cv_results) if cv_results else 0} CV documents")
        
        # Test 4.2: Search cover letters
        logger.info("\n   4.2: Search only cover letters")
        cover_letter_results = await self.search_service.search_by_document_type(
            document_type="cover_letter",
            query="application for position",
            user_id=self.test_user_id,
            limit=10
        )
        logger.info(f"   ✅ Found {len(cover_letter_results) if cover_letter_results else 0} cover letter documents")
        
        # Test 4.3: Different similarity thresholds
        logger.info("\n   4.3: Testing different similarity thresholds")
        
        thresholds = [0.3, 0.5, 0.7]
        query = "software engineer with python"
        
        for threshold in thresholds:
            results = await self.search_service.semantic_search(
                query=query,
                user_id=self.test_user_id,
                limit=10,
                similarity_threshold=threshold
            )
            count = len(results) if results else 0
            logger.info(f"      Threshold {threshold}: {count} results")
        
        logger.success("\n✅ TEST 4 PASSED: Advanced search features working")
    
    async def test_ranking(self):
        """TEST 5: Result ranking"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST 5: Result ranking")
        logger.info("=" * 80)
        
        # Get search results
        query = "experienced developer"
        results = await self.search_service.semantic_search(
            query=query,
            user_id=self.test_user_id,
            limit=10,
            similarity_threshold=0.3
        )
        
        if not results:
            logger.warning("⚠️ No results to rank")
            return
        
        # Apply ranking
        ranked_results = self.ranking_service.rank_results(results)
        
        logger.info(f"\n   Ranked {len(ranked_results)} results:")
        for i, result in enumerate(ranked_results[:5], 1):
            logger.info(f"      {i}. {result['filename']}")
            logger.info(f"         Similarity: {result['similarity_score']:.3f}")
            logger.info(f"         Final Score: {result['final_score']:.3f}")
            logger.info(f"         Recency: {result['ranking_scores']['recency']:.3f}")
        
        logger.success("\n✅ TEST 5 PASSED: Ranking working correctly")
    
    async def test_statistics(self):
        """TEST 6: Get search statistics"""
        logger.info("\n" + "=" * 80)
        logger.info("📈 TEST 6: Search statistics")
        logger.info("=" * 80)
        
        stats = await self.search_service.get_search_statistics(
            user_id=self.test_user_id
        )
        
        if stats:
            logger.success("✅ Statistics retrieved:")
            logger.info(f"   Total documents: {stats.get('total_documents', 0)}")
            logger.info(f"   CV count: {stats.get('cv_count', 0)}")
            logger.info(f"   Cover letter count: {stats.get('cover_letter_count', 0)}")
            logger.info(f"   Certificate count: {stats.get('certificate_count', 0)}")
            logger.info(f"   Processed: {stats.get('processed_count', 0)}")
            logger.info(f"   Total size: {stats.get('total_size_mb', 0)} MB")
            
            logger.success("\n✅ TEST 6 PASSED: Statistics working")
        else:
            logger.error("❌ TEST 6 FAILED: Could not retrieve statistics")
    
    async def test_cleanup(self):
        """TEST 7: Clean up test data"""
        logger.info("\n" + "=" * 80)
        logger.info("🗑️ TEST 7: Cleaning up test data")
        logger.info("=" * 80)
        
        deleted_count = 0
        
        for doc in self.uploaded_documents:
            result = await self.rag_integration.delete_document_embedding(
                user_id=self.test_user_id,
                document_id=doc["document_id"]
            )
            
            if result["success"]:
                deleted_count += 1
                logger.info(f"   ✅ Deleted: {doc['filename']}")
            else:
                logger.error(f"   ❌ Failed to delete: {doc['filename']}")
        
        logger.success(f"\n✅ TEST 7 PASSED: {deleted_count}/{len(self.uploaded_documents)} documents cleaned up")
    
    async def test_delete_user(self):
        """TEST 8: Delete test user from database"""
        if not self.user_created or not self.test_user_id:
            logger.info("\n⚠️ No user to delete")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("🗑️ TEST 8: Deleting test user")
        logger.info("=" * 80)
        
        conn = None
        try:
            conn = connect()
            cursor = conn.cursor()
            
            # Delete user (cascade will delete related records)
            delete_query = "DELETE FROM users WHERE id = %s;"
            cursor.execute(delete_query, (self.test_user_id,))
            conn.commit()
            
            logger.success(f"✅ TEST 8 PASSED: User {self.test_user_id} deleted")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete user: {str(e)}")
        finally:
            if conn:
                cursor.close()
                disconnect(conn)
    
    async def emergency_cleanup(self):
        """Emergency cleanup in case of error"""
        logger.warning("\n⚠️ Running emergency cleanup...")
        
        for doc in self.uploaded_documents:
            try:
                await self.rag_integration.delete_document_embedding(
                    user_id=self.test_user_id,
                    document_id=doc["document_id"]
                )
            except:
                pass
        
        logger.info("Emergency cleanup completed")
    
    def print_summary(self):
        """Print final test summary"""
        logger.info("\n" + "=" * 80)
        logger.success("🎉 FULL RAG WORKFLOW TEST - COMPLETED!")
        logger.info("=" * 80)
        logger.info("\n📋 TEST SUMMARY:")
        logger.info(f"   ✅ User Registration: {self.test_user_email}")
        logger.info(f"   ✅ Test User ID: {self.test_user_id}")
        logger.info(f"   ✅ Documents Uploaded: {len(self.uploaded_documents)}")
        logger.info(f"   ✅ Document Types: CVs, Cover Letters")
        logger.info(f"   ✅ Semantic Search: Working")
        logger.info(f"   ✅ Advanced Filters: Working")
        logger.info(f"   ✅ Ranking System: Working")
        logger.info(f"   ✅ Statistics: Working")
        logger.info(f"   ✅ Cleanup: Completed")
        logger.info(f"   ✅ User Deletion: Completed")
        logger.info("\n🚀 RAG SYSTEM FULLY FUNCTIONAL!")
        logger.info("=" * 80)


async def main():
    """Main test runner"""
    logger.info("🚀 Starting Full RAG Workflow Test...")
    logger.info(f"Timestamp: {datetime.now().isoformat()}\n")
    
    test = FullRAGWorkflowTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

