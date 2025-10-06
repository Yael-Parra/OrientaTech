import os
import psycopg2
from dotenv import load_dotenv
from loguru import logger
from urllib.parse import urlparse

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def connect_to_postgres():
    """Connect to PostgreSQL server (without specifying a database)"""
    try:
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            raise ValueError("DATABASE_URL is not defined in environment variables")
        
        # Parse the URL and connect to the default postgres database
        parsed_url = urlparse(database_url)
        
        # Connect to 'postgres' database instead of the target database
        default_database_url = f"{parsed_url.scheme}://{parsed_url.netloc}/postgres"
        if parsed_url.query:
            default_database_url += f"?{parsed_url.query}"
        
        conn = psycopg2.connect(default_database_url)
        logger.info("Connected to PostgreSQL server")
        return conn
    except Exception as e:
        logger.error(f"Error while connecting to PostgreSQL server: {e}")
        return None

def create_database():
    """Create the target database"""
    db_name = os.getenv("DB_PROJECT")
    if not db_name:
        logger.error("DB_PROJECT is not defined in environment variables")
        return
    
    conn = connect_to_postgres()
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
            cursor.execute(f'CREATE DATABASE "{db_name}";')
            logger.info(f"Database '{db_name}' created successfully")
            
    except Exception as e:
        logger.error(f"Error while creating database {db_name}: {e}")
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

if __name__ == "__main__":
    create_database()
