import os
import psycopg2
from loguru import logger
from urllib.parse import urlparse
from .db_connection import connect_to_postgres_server

def init_pgvector_extension():
    """Initialize pgvector extension in the target database"""
    db_name = os.getenv("DB_PROJECT")
    if not db_name:
        logger.error("DB_PROJECT is not defined in environment variables")
        return
    
    conn = connect_to_postgres_server()
    if conn is None:
        return

    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # Connect to the target database and create extension
        database_url = os.getenv("DATABASE_URL")
        parsed_url = urlparse(database_url)
        target_database_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{db_name}"
        if parsed_url.query:
            target_database_url += f"?{parsed_url.query}"
        
        # Close current connection and connect to target database
        cursor.close()
        conn.close()
        
        target_conn = psycopg2.connect(target_database_url)
        target_conn.autocommit = True
        target_cursor = target_conn.cursor()
        
        # Create pgvector extension
        target_cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("pgvector extension created successfully")
        
        target_cursor.close()
        target_conn.close()
        
    except Exception as e:
        logger.error(f"Error while creating pgvector extension: {e}")
    finally:
        logger.info("Connection closed")

if __name__ == "__main__":
    init_pgvector_extension()
