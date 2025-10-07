import os
from loguru import logger

# Import connection functions from the same directory
from db_connection import connect, disconnect

def create_all_tables():
    conn = connect()
    if conn is None:
        return

    cursor = conn.cursor()

    try:
        # Users table for authentication (compatible with existing structure)
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
        
        # User Personal Info table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_personal_info (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                full_name VARCHAR(200),
                date_of_birth DATE,
                gender VARCHAR(20),
                location VARCHAR(200),
                education_level VARCHAR(100),
                previous_experience TEXT,
                area_of_interest VARCHAR(200),
                main_skills TEXT,
                digital_level VARCHAR(50),
                resume_path VARCHAR(500),
                resume_embedding VECTOR(1536),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Employment Platforms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employment_platforms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                type VARCHAR(100),
                url VARCHAR(500),
                description TEXT,
                country VARCHAR(100),
                category VARCHAR(100),
                validated BOOLEAN DEFAULT FALSE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                platform_id INTEGER NOT NULL REFERENCES employment_platforms(id) ON DELETE CASCADE,
                is_platform_review BOOLEAN DEFAULT TRUE,
                review_type VARCHAR(50),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visible BOOLEAN DEFAULT TRUE
            );
        """)

        # Create triggers for updated_at columns
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_user_personal_info_updated_at ON user_personal_info;
            CREATE TRIGGER update_user_personal_info_updated_at
                BEFORE UPDATE ON user_personal_info
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)

        # Create additional indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_personal_info_user_id ON user_personal_info(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_employment_platforms_name ON employment_platforms(name);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_employment_platforms_country ON employment_platforms(country);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_employment_platforms_category ON employment_platforms(category);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_platform_id ON reviews(platform_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at);
        """)

        conn.commit()
        logger.info("All tables created successfully")
    except Exception as e:
        logger.error(f"Error while creating tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        disconnect(conn)

if __name__ == "__main__":
    create_all_tables()
