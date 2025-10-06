"""
Script for complete initialization of OrientaTech database
Performs the following steps:
1. Database creation
2. pgvector extension initialization
3. Creation of all tables according to schema
"""

import os
import sys
from loguru import logger

# Add current directory to path for module imports
sys.path.append(os.path.dirname(__file__))

from create_database import create_database
from init_extensions import init_pgvector_extension
from db_tables_creation import create_all_tables

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
        
        # Step 3: Creating all tables
        logger.info("Step 3: Creating all tables...")
        create_all_tables()
        
        logger.success("OrientaTech database successfully initialized!")
        logger.info("Created tables:")
        logger.info("- users (users)")
        logger.info("- user_personal_info (personal information)")
        logger.info("- employment_platforms (employment platforms)")
        logger.info("- reviews (reviews)")
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_complete_database()
