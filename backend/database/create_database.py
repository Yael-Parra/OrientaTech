import os
import re
from loguru import logger
from .db_connection import connect_to_postgres_server

def validate_database_name(name: str) -> bool:
    """
    Validate database name to prevent SQL injection.
    
    Args:
        name (str): Database name to validate
        
    Returns:
        bool: True if name is valid, False otherwise
    """
    if not name:
        return False
    
    
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, name))

def create_database():
    """Create the target database"""
    db_name = os.getenv("DB_PROJECT")
    if not db_name:
        logger.error("DB_PROJECT is not defined in environment variables")
        return
    
    # Валидация имени базы данных для предотвращения SQL injection
    if not validate_database_name(db_name):
        logger.error(f"Invalid database name: '{db_name}'. Only letters, numbers and underscores are allowed.")
        return
    
    conn = connect_to_postgres_server()
    if conn is None:
        return

    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # Check if database already exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if exists:
            logger.info(f"Database '{db_name}' already exists")
        else:
            # Используем параметризованный запрос для безопасности
            cursor.execute("CREATE DATABASE %s", (db_name,))
            logger.info(f"Database '{db_name}' created successfully")
            
    except Exception as e:
        logger.error(f"Error while creating database {db_name}: {e}")
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

if __name__ == "__main__":
    create_database()
