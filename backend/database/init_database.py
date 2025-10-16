"""
Script for complete initialization of OrientaTech database
Performs the following steps:
1. Database creation
2. pgvector extension initialization
3. Migration system initialization
4. Apply all migrations
"""

import os
import sys
from loguru import logger

# Add current directory to path for module imports
sys.path.append(os.path.dirname(__file__))

from .create_database import create_database
from .init_extensions import init_pgvector_extension
from .migration_manager import MigrationManager

def init_complete_database():
    """Complete database initialization"""
    logger.info("Starting OrientaTech database initialization...")
    
    try:
        # Step 1: Database creation
        logger.info("Step 1: Creating database...")
        create_database()
        
        # Step 2: pgvector extension initialization
        logger.info("Step 2: Initializing pgvector extension...")
        init_pgvector_extension()
        
        # Step 3: Initialize migration system
        logger.info("Step 3: Initializing migration system...")
        migration_manager = MigrationManager()
        
        # Step 4: Apply all migrations
        logger.info("Step 4: Applying all migrations...")
        if migration_manager.run_migrations():
            logger.success("OrientaTech database successfully initialized!")
            logger.info("Applied migrations:")
            logger.info("- 001_initial_schema.sql (base tables)")
            logger.info("- 002_add_rag_tables.sql (document embeddings)")
            logger.info("- 003_add_rag_functions.sql (search functions)")
            logger.info("- 004_add_rag_indexes.sql (optimization indexes)")
        else:
            logger.error("Failed to apply migrations")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_complete_database()
