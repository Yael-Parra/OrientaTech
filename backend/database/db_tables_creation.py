import os
import sys
from loguru import logger

# Import connection functions from the same directory
from db_connection import connect, disconnect

def create_essential_tables():
    conn = connect()
    if conn is None:
        return

    cursor = conn.cursor()

    try:
        # Users table for authentication (compatible with auth system)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            );
        """)

        # Create function to update updated_at timestamp
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)

        # Create trigger for users table
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_users_updated_at ON users;
            CREATE TRIGGER update_users_updated_at
                BEFORE UPDATE ON users
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)

        # Create indexes for users table
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
        """)
        
        conn.commit()
        logger.info("Essential tables created successfully")
    except Exception as e:
        logger.error(f"Error while creating tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        disconnect(conn)

if __name__ == "__main__":
    create_essential_tables()
