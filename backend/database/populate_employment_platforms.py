"""
Script to populate employment platforms table with sample data
Adds example employment platforms for testing the integration
"""

import asyncio
import sys
import os
from datetime import datetime
from loguru import logger

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_connection import connect, disconnect


SAMPLE_PLATFORMS = [
    {
        'name': 'LinkedIn',
        'type': 'professional_network',
        'url': 'https://www.linkedin.com/jobs',
        'description': 'Red profesional global con ofertas de trabajo en todos los sectores. Ideal para networking y búsqueda de empleo profesional.',
        'country': 'Global',
        'category': 'professional_networking',
        'validated': True
    },
    {
        'name': 'InfoJobs',
        'type': 'job_board',
        'url': 'https://www.infojobs.net',
        'description': 'Portal de empleo líder en España con miles de ofertas de trabajo. Especializado en el mercado laboral español.',
        'country': 'España',
        'category': 'general_employment',
        'validated': True
    },
    {
        'name': 'Stack Overflow Jobs',
        'type': 'specialized_board',
        'url': 'https://stackoverflow.com/jobs',
        'description': 'Portal especializado en empleos de tecnología y programación. Comunidad de desarrolladores.',
        'country': 'Global',
        'category': 'technology',
        'validated': True
    },
    {
        'name': 'GitHub Jobs',
        'type': 'specialized_board',
        'url': 'https://jobs.github.com',
        'description': 'Ofertas de trabajo en tecnología y desarrollo de software. Integrado con la plataforma GitHub.',
        'country': 'Global',
        'category': 'technology',
        'validated': True
    },
    {
        'name': 'AngelList',
        'type': 'startup_platform',
        'url': 'https://angel.co/jobs',
        'description': 'Plataforma especializada en empleos en startups y empresas tecnológicas emergentes.',
        'country': 'Global',
        'category': 'startup',
        'validated': True
    },
    {
        'name': 'Remote.co',
        'type': 'remote_platform',
        'url': 'https://remote.co',
        'description': 'Portal especializado exclusivamente en trabajos remotos en todas las industrias.',
        'country': 'Global',
        'category': 'remote_work',
        'validated': True
    },
    {
        'name': 'FlexJobs',
        'type': 'flexible_work',
        'url': 'https://www.flexjobs.com',
        'description': 'Plataforma para trabajos flexibles, remotos y de medio tiempo. Empleos verificados.',
        'country': 'Global',
        'category': 'flexible_work',
        'validated': True
    },
    {
        'name': 'Upwork',
        'type': 'freelance_platform',
        'url': 'https://www.upwork.com',
        'description': 'Plataforma líder para trabajos freelance y proyectos independientes en múltiples categorías.',
        'country': 'Global',
        'category': 'freelance',
        'validated': True
    },
    {
        'name': 'Freelancer',
        'type': 'freelance_platform',
        'url': 'https://www.freelancer.com',
        'description': 'Marketplace global para proyectos freelance en tecnología, diseño, escritura y más.',
        'country': 'Global',
        'category': 'freelance',
        'validated': True
    },
    {
        'name': 'Indeed',
        'type': 'job_board',
        'url': 'https://www.indeed.com',
        'description': 'Motor de búsqueda de empleo más grande del mundo. Agrega ofertas de múltiples fuentes.',
        'country': 'Global',
        'category': 'general_employment',
        'validated': True
    },
    {
        'name': 'Glassdoor',
        'type': 'company_review',
        'url': 'https://www.glassdoor.com',
        'description': 'Portal de empleo con reseñas de empresas, salarios y entrevistas. Transparencia laboral.',
        'country': 'Global',
        'category': 'company_research',
        'validated': True
    },
    {
        'name': 'Jobandtalent',
        'type': 'job_board',
        'url': 'https://www.jobandtalent.com',
        'description': 'Plataforma española de empleo con enfoque en matching automático entre candidatos y empleadores.',
        'country': 'España',
        'category': 'general_employment',
        'validated': True
    },
    {
        'name': 'Tecnoempleo',
        'type': 'specialized_board',
        'url': 'https://www.tecnoempleo.com',
        'description': 'Portal especializado en empleos de tecnología e ingeniería en España.',
        'country': 'España',
        'category': 'technology',
        'validated': True
    },
    {
        'name': 'Domestika Jobs',
        'type': 'creative_platform',
        'url': 'https://www.domestika.org/jobs',
        'description': 'Plataforma especializada en empleos creativos: diseño, ilustración, fotografía, marketing creativo.',
        'country': 'Global',
        'category': 'creative_industries',
        'validated': True
    },
    {
        'name': 'NoFlufJobs',
        'type': 'specialized_board',
        'url': 'https://nofluffjobs.com',
        'description': 'Portal para desarrolladores sin información irrelevante. Solo empleos tech con salarios transparentes.',
        'country': 'Europa',
        'category': 'technology',
        'validated': True
    },
    {
        'name': 'WeWork Remotely',
        'type': 'remote_platform',
        'url': 'https://weworkremotely.com',
        'description': 'Una de las comunidades más grandes de trabajos remotos en tecnología, marketing y más.',
        'country': 'Global',
        'category': 'remote_work',
        'validated': True
    },
    {
        'name': 'Dribbble Jobs',
        'type': 'creative_platform',
        'url': 'https://dribbble.com/jobs',
        'description': 'Ofertas de trabajo en diseño gráfico, UX/UI, y creatividad visual.',
        'country': 'Global',
        'category': 'creative_industries',
        'validated': True
    },
    {
        'name': 'AngelList (Wellfound)',
        'type': 'startup_platform',
        'url': 'https://wellfound.com',
        'description': 'Anteriormente AngelList Talent. Empleos en startups con información sobre equity y cultura.',
        'country': 'Global',
        'category': 'startup',
        'validated': True
    },
    {
        'name': 'JustRemote',
        'type': 'remote_platform',
        'url': 'https://justremote.co',
        'description': 'Ofertas de trabajo exclusivamente remotas en tecnología, marketing, ventas y más.',
        'country': 'Global',
        'category': 'remote_work',
        'validated': True
    },
    {
        'name': 'Toptal',
        'type': 'elite_freelance',
        'url': 'https://www.toptal.com',
        'description': 'Red de freelancers top 3% en desarrollo, diseño y finanzas. Proceso de selección riguroso.',
        'country': 'Global',
        'category': 'elite_freelance',
        'validated': True
    }
]


async def create_employment_platforms_table():
    """Create employment platforms table if it doesn't exist"""
    conn = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'employment_platforms'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.info("Creating employment_platforms table...")
            
            # Create table
            cursor.execute("""
                CREATE TABLE employment_platforms (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    type VARCHAR(100) NOT NULL,
                    url VARCHAR(500),
                    description TEXT,
                    country VARCHAR(100),
                    category VARCHAR(100),
                    validated BOOLEAN DEFAULT FALSE,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX idx_employment_platforms_category ON employment_platforms(category);
                CREATE INDEX idx_employment_platforms_country ON employment_platforms(country);
                CREATE INDEX idx_employment_platforms_type ON employment_platforms(type);
                CREATE INDEX idx_employment_platforms_validated ON employment_platforms(validated);
            """)
            
            conn.commit()
            logger.success("✅ Employment platforms table created successfully")
        else:
            logger.info("Employment platforms table already exists")
            
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            disconnect(conn)


async def populate_employment_platforms():
    """Populate employment platforms table with sample data"""
    conn = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM employment_platforms")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"Employment platforms table already has {existing_count} entries")
            response = input("Do you want to add new platforms without clearing existing? (y/N): ")
            if response.lower() != 'y':
                logger.info("Skipping population")
                return
            
            logger.info("Adding new platforms to existing data...")
        else:
            logger.info("Table is empty, adding initial data...")
        
        # Insert sample platforms (skip if already exists)
        logger.info(f"Preparing to insert {len(SAMPLE_PLATFORMS)} sample employment platforms...")
        
        insert_query = """
            INSERT INTO employment_platforms 
            (name, type, url, description, country, category, validated, registered_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """
        
        current_time = datetime.now()
        
        for platform in SAMPLE_PLATFORMS:
            cursor.execute(insert_query, (
                platform['name'],
                platform['type'],
                platform['url'],
                platform['description'],
                platform['country'],
                platform['category'],
                platform['validated'],
                current_time
            ))
        
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM employment_platforms")
        final_count = cursor.fetchone()[0]
        
        logger.success(f"✅ Successfully inserted {final_count} employment platforms")
        
        # Show summary by category
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM employment_platforms 
            GROUP BY category 
            ORDER BY COUNT(*) DESC
        """)
        
        categories = cursor.fetchall()
        logger.info("Platforms by category:")
        for category, count in categories:
            logger.info(f"  - {category}: {count} platforms")
        
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error populating platforms: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            disconnect(conn)


async def verify_integration():
    """Verify that the integration service can access the platforms"""
    try:
        logger.info("🔍 Verifying integration with platforms service...")
        
        # Import and test the service
        from services.employment_platforms_service import get_employment_platforms_service
        
        service = get_employment_platforms_service()
        
        # Test summary
        summary = await service.get_platforms_summary()
        logger.info(f"Platform summary: {summary}")
        
        # Test search
        platforms = await service.get_relevant_platforms("technology", limit=3)
        logger.info(f"Found {len(platforms)} technology platforms")
        
        for platform in platforms:
            logger.info(f"  - {platform['name']} ({platform['category']})")
        
        logger.success("✅ Integration verification completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Integration verification failed: {e}")


async def main():
    """Main function to set up employment platforms"""
    logger.info("🚀 Starting Employment Platforms Setup")
    
    # Step 1: Create table
    await create_employment_platforms_table()
    
    # Step 2: Populate with sample data
    await populate_employment_platforms()
    
    # Step 3: Verify integration
    await verify_integration()
    
    logger.success("🎉 Employment Platforms setup completed!")


if __name__ == "__main__":
    asyncio.run(main())