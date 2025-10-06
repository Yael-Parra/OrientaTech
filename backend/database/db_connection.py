import os
import psycopg2
import asyncpg
from dotenv import load_dotenv
from loguru import logger
from urllib.parse import urlparse

# Load environment variables from the .env file in backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_database_url():
    """Get the constructed database URL for the target database"""
    database_url = os.getenv("DATABASE_URL")
    db_project = os.getenv("DB_PROJECT")
    
    if not database_url:
        raise ValueError("DATABASE_URL is not defined in environment variables")
    
    if not db_project:
        raise ValueError("DB_PROJECT is not defined in environment variables")
    
    # Parse the original URL and replace the database name with DB_PROJECT
    parsed_url = urlparse(database_url)
    
    # Construct new URL with DB_PROJECT database name
    new_database_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{db_project}"
    if parsed_url.query:
        new_database_url += f"?{parsed_url.query}"
    
    return new_database_url

def connect():
    """Synchronous connection using psycopg2"""
    try:
        new_database_url = get_database_url()
        conn = psycopg2.connect(new_database_url)
        db_project = os.getenv("DB_PROJECT")
        logger.info(f"Connection to database '{db_project}' established")
        return conn
    except Exception as e:
        logger.error(f"Error while connecting to database: {e}")
        return None

async def connect_async():
    """Asynchronous connection using asyncpg"""
    try:
        new_database_url = get_database_url()
        conn = await asyncpg.connect(new_database_url)
        db_project = os.getenv("DB_PROJECT")
        logger.info(f"Async connection to database '{db_project}' established")
        return conn
    except Exception as e:
        logger.error(f"Error while connecting to database: {e}")
        return None

def disconnect(conn):
    if conn:
        conn.close()
        logger.info("Connection to database closed")

async def disconnect_async(conn):
    if conn:
        await conn.close()
        logger.info("Async connection to database closed")

if __name__ == "__main__":
    conn = connect()
    disconnect(conn)