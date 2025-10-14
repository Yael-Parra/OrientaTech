"""
Employment Platforms Service for RAG Integration
Provides employment platform data to enrich LLM prompts
"""

from typing import List, Dict, Optional
from loguru import logger
import asyncpg
from database.db_connection import connect, disconnect
from models.employment_platforms import (
    EmploymentPlatformCreate,
    EmploymentPlatformUpdate,
    EmploymentPlatformResponse,
    PlatformTypeEnum,
    PlatformCategoryEnum
)


class EmploymentPlatformsService:
    """
    Service to retrieve and format employment platforms data for RAG integration
    """
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    async def get_relevant_platforms(
        self,
        query: str,
        category: Optional[str] = None,
        country: Optional[str] = None,
        platform_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get relevant employment platforms based on search criteria
        
        Args:
            query: Search query to match against platform descriptions
            category: Platform category filter
            country: Country filter
            platform_type: Platform type filter
            limit: Maximum number of platforms to return
            
        Returns:
            List of platform dictionaries
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            # Build dynamic query based on filters
            where_conditions = ["validated = TRUE"]  # Only validated platforms
            params = []
            param_count = 1
            
            # Add text search if query provided
            if query and query.strip():
                where_conditions.append(f"""
                    (LOWER(name) LIKE ${{param_count}} OR 
                     LOWER(description) LIKE ${{param_count}} OR 
                     LOWER(category) LIKE ${{param_count}})
                """.format(param_count=param_count))
                params.append(f"%{query.lower()}%")
                param_count += 1
            
            # Add category filter
            if category:
                where_conditions.append(f"LOWER(category) = ${param_count}")
                params.append(category.lower())
                param_count += 1
            
            # Add country filter
            if country:
                where_conditions.append(f"LOWER(country) = ${param_count}")
                params.append(country.lower())
                param_count += 1
                
            # Add platform type filter
            if platform_type:
                where_conditions.append(f"LOWER(type) = ${param_count}")
                params.append(platform_type.lower())
                param_count += 1
            
            # Construct final query
            sql_query = f"""
                SELECT 
                    id, name, type, url, description, country, category,
                    validated, registered_at
                FROM employment_platforms
                WHERE {' AND '.join(where_conditions)}
                ORDER BY 
                    CASE WHEN name ILIKE %s THEN 1 ELSE 2 END,
                    registered_at DESC
                LIMIT ${param_count}
            """
            
            # Add query parameter for ordering and limit
            if query and query.strip():
                params.append(f"%{query}%")
            else:
                # If no query, add dummy parameter for ORDER BY
                params.append("%")
            params.append(limit)
            
            logger.debug(f"Executing platforms query with params: {params}")
            
            self.cursor.execute(sql_query, params)
            rows = self.cursor.fetchall()
            
            # Convert to dictionaries
            platforms = []
            for row in rows:
                platform = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'url': row[3],
                    'description': row[4],
                    'country': row[5],
                    'category': row[6],
                    'validated': row[7],
                    'registered_at': row[8]
                }
                platforms.append(platform)
            
            logger.info(f"Retrieved {len(platforms)} relevant employment platforms")
            return platforms
            
        except Exception as e:
            logger.error(f"Error retrieving employment platforms: {e}")
            return []
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)
    
    async def get_platforms_by_categories(
        self, 
        categories: List[str],
        limit_per_category: int = 3
    ) -> Dict[str, List[Dict]]:
        """
        Get platforms grouped by categories
        
        Args:
            categories: List of categories to retrieve
            limit_per_category: Maximum platforms per category
            
        Returns:
            Dictionary with category as key and list of platforms as value
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            result = {}
            
            for category in categories:
                self.cursor.execute("""
                    SELECT 
                        id, name, type, url, description, country, category,
                        validated, registered_at
                    FROM employment_platforms
                    WHERE LOWER(category) = %s AND validated = TRUE
                    ORDER BY registered_at DESC
                    LIMIT %s
                """, (category.lower(), limit_per_category))
                
                rows = self.cursor.fetchall()
                platforms = []
                
                for row in rows:
                    platform = {
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'url': row[3],
                        'description': row[4],
                        'country': row[5],
                        'category': row[6],
                        'validated': row[7],
                        'registered_at': row[8]
                    }
                    platforms.append(platform)
                
                result[category] = platforms
            
            logger.info(f"Retrieved platforms for {len(categories)} categories")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving platforms by categories: {e}")
            return {}
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)
    
    def format_platforms_for_prompt(
        self, 
        platforms: List[Dict],
        include_descriptions: bool = True
    ) -> str:
        """
        Format platforms data for inclusion in LLM prompts
        
        Args:
            platforms: List of platform dictionaries
            include_descriptions: Whether to include platform descriptions
            
        Returns:
            Formatted string for prompt inclusion
        """
        if not platforms:
            return "No hay plataformas de empleo relevantes disponibles."
        
        formatted_sections = []
        
        # Group by category for better organization
        by_category = {}
        for platform in platforms:
            category = platform.get('category', 'other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(platform)
        
        for category, category_platforms in by_category.items():
            category_title = category.replace('_', ' ').title()
            formatted_sections.append(f"\n**{category_title}:**")
            
            for platform in category_platforms:
                name = platform.get('name', 'N/A')
                platform_type = platform.get('type', 'N/A')
                country = platform.get('country', 'N/A')
                url = platform.get('url', '')
                
                platform_info = f"- **{name}** ({platform_type}) - {country}"
                
                if url:
                    platform_info += f" | {url}"
                
                if include_descriptions and platform.get('description'):
                    description = platform['description'][:200]  # Limit description length
                    if len(platform['description']) > 200:
                        description += "..."
                    platform_info += f"\n  {description}"
                
                formatted_sections.append(platform_info)
        
        return "\n".join(formatted_sections)
    
    async def get_platforms_summary(self) -> Dict:
        """
        Get summary statistics about employment platforms
        
        Returns:
            Dictionary with platform statistics
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            # Get total count
            self.cursor.execute("SELECT COUNT(*) FROM employment_platforms WHERE validated = TRUE")
            total_count = self.cursor.fetchone()[0]
            
            # Get count by category
            self.cursor.execute("""
                SELECT category, COUNT(*) 
                FROM employment_platforms 
                WHERE validated = TRUE 
                GROUP BY category 
                ORDER BY COUNT(*) DESC
            """)
            by_category = dict(self.cursor.fetchall())
            
            # Get count by type
            self.cursor.execute("""
                SELECT type, COUNT(*) 
                FROM employment_platforms 
                WHERE validated = TRUE 
                GROUP BY type 
                ORDER BY COUNT(*) DESC
            """)
            by_type = dict(self.cursor.fetchall())
            
            # Get count by country
            self.cursor.execute("""
                SELECT country, COUNT(*) 
                FROM employment_platforms 
                WHERE validated = TRUE 
                GROUP BY country 
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            by_country = dict(self.cursor.fetchall())
            
            return {
                'total_platforms': total_count,
                'by_category': by_category,
                'by_type': by_type,
                'by_country': by_country
            }
            
        except Exception as e:
            logger.error(f"Error getting platforms summary: {e}")
            return {}
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)

    # ===================================
    # CRUD Operations
    # ===================================

    async def create_platform(self, platform_data: EmploymentPlatformCreate) -> Optional[Dict]:
        """
        Create a new employment platform
        
        Args:
            platform_data: Platform creation data
            
        Returns:
            Created platform data or None if failed
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            self.cursor.execute("""
                INSERT INTO employment_platforms 
                (name, type, url, description, country, category, validated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, type, url, description, country, category, validated, registered_at
            """, (
                platform_data.name,
                platform_data.type.value,
                str(platform_data.url) if platform_data.url else None,
                platform_data.description,
                platform_data.country,
                platform_data.category.value,
                platform_data.validated
            ))
            
            row = self.cursor.fetchone()
            self.conn.commit()
            
            if row:
                platform = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'url': row[3],
                    'description': row[4],
                    'country': row[5],
                    'category': row[6],
                    'validated': row[7],
                    'registered_at': row[8]
                }
                logger.info(f"✅ Created employment platform: {platform['name']}")
                return platform
            
            return None
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Error creating employment platform: {e}")
            return None
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)

    async def get_platform_by_id(self, platform_id: int) -> Optional[Dict]:
        """
        Get platform by ID
        
        Args:
            platform_id: Platform ID
            
        Returns:
            Platform data or None if not found
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            self.cursor.execute("""
                SELECT id, name, type, url, description, country, category, validated, registered_at
                FROM employment_platforms
                WHERE id = %s
            """, (platform_id,))
            
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'url': row[3],
                    'description': row[4],
                    'country': row[5],
                    'category': row[6],
                    'validated': row[7],
                    'registered_at': row[8]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting platform by ID: {e}")
            return None
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)

    async def update_platform(self, platform_id: int, platform_data: EmploymentPlatformUpdate) -> Optional[Dict]:
        """
        Update an employment platform
        
        Args:
            platform_id: Platform ID to update
            platform_data: Updated platform data
            
        Returns:
            Updated platform data or None if failed
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            # Build dynamic update query
            update_fields = []
            values = []
            
            if platform_data.name is not None:
                update_fields.append("name = %s")
                values.append(platform_data.name)
            
            if platform_data.type is not None:
                update_fields.append("type = %s")
                values.append(platform_data.type.value)
            
            if platform_data.url is not None:
                update_fields.append("url = %s")
                values.append(str(platform_data.url) if platform_data.url else None)
            
            if platform_data.description is not None:
                update_fields.append("description = %s")
                values.append(platform_data.description)
            
            if platform_data.country is not None:
                update_fields.append("country = %s")
                values.append(platform_data.country)
            
            if platform_data.category is not None:
                update_fields.append("category = %s")
                values.append(platform_data.category.value)
            
            if platform_data.validated is not None:
                update_fields.append("validated = %s")
                values.append(platform_data.validated)
            
            if not update_fields:
                logger.warning("No fields to update")
                return await self.get_platform_by_id(platform_id)
            
            values.append(platform_id)
            
            query = f"""
                UPDATE employment_platforms 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, type, url, description, country, category, validated, registered_at
            """
            
            self.cursor.execute(query, values)
            row = self.cursor.fetchone()
            self.conn.commit()
            
            if row:
                platform = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'url': row[3],
                    'description': row[4],
                    'country': row[5],
                    'category': row[6],
                    'validated': row[7],
                    'registered_at': row[8]
                }
                logger.info(f"✅ Updated employment platform: {platform['name']}")
                return platform
            
            return None
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Error updating employment platform: {e}")
            return None
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)

    async def delete_platform(self, platform_id: int) -> bool:
        """
        Delete an employment platform
        
        Args:
            platform_id: Platform ID to delete
            
        Returns:
            True if deleted, False if failed
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            self.cursor.execute("""
                DELETE FROM employment_platforms 
                WHERE id = %s
            """, (platform_id,))
            
            deleted_count = self.cursor.rowcount
            self.conn.commit()
            
            if deleted_count > 0:
                logger.info(f"✅ Deleted employment platform with ID: {platform_id}")
                return True
            else:
                logger.warning(f"⚠️ No platform found with ID: {platform_id}")
                return False
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Error deleting employment platform: {e}")
            return False
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)

    async def get_all_platforms(
        self, 
        validated_only: bool = True, 
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all employment platforms
        
        Args:
            validated_only: Only return validated platforms
            limit: Optional limit of results
            
        Returns:
            List of platform dictionaries
        """
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            query = """
                SELECT id, name, type, url, description, country, category, validated, registered_at
                FROM employment_platforms
            """
            
            params = []
            if validated_only:
                query += " WHERE validated = TRUE"
            
            query += " ORDER BY registered_at DESC"
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            platforms = []
            for row in rows:
                platform = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'url': row[3],
                    'description': row[4],
                    'country': row[5],
                    'category': row[6],
                    'validated': row[7],
                    'registered_at': row[8]
                }
                platforms.append(platform)
            
            logger.info(f"Retrieved {len(platforms)} employment platforms")
            return platforms
            
        except Exception as e:
            logger.error(f"Error getting all platforms: {e}")
            return []
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)

    async def bulk_create_platforms(self, platforms_data: List[EmploymentPlatformCreate]) -> List[Dict]:
        """
        Create multiple employment platforms in a single transaction
        
        Args:
            platforms_data: List of platform creation data
            
        Returns:
            List of created platform data
        """
        created_platforms = []
        
        try:
            self.conn = connect()
            self.cursor = self.conn.cursor()
            
            for platform_data in platforms_data:
                try:
                    self.cursor.execute("""
                        INSERT INTO employment_platforms 
                        (name, type, url, description, country, category, validated)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, name, type, url, description, country, category, validated, registered_at
                    """, (
                        platform_data.name,
                        platform_data.type.value,
                        str(platform_data.url) if platform_data.url else None,
                        platform_data.description,
                        platform_data.country,
                        platform_data.category.value,
                        platform_data.validated
                    ))
                    
                    row = self.cursor.fetchone()
                    if row:
                        platform = {
                            'id': row[0],
                            'name': row[1],
                            'type': row[2],
                            'url': row[3],
                            'description': row[4],
                            'country': row[5],
                            'category': row[6],
                            'validated': row[7],
                            'registered_at': row[8]
                        }
                        created_platforms.append(platform)
                        
                except Exception as e:
                    logger.warning(f"Failed to create platform {platform_data.name}: {e}")
                    continue
            
            self.conn.commit()
            logger.info(f"✅ Created {len(created_platforms)} employment platforms")
            
            return created_platforms
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Error in bulk platform creation: {e}")
            return created_platforms
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                disconnect(self.conn)


# Singleton instance
_employment_platforms_service_instance: Optional[EmploymentPlatformsService] = None


def get_employment_platforms_service() -> EmploymentPlatformsService:
    """
    Get singleton instance of EmploymentPlatformsService
    
    Returns:
        EmploymentPlatformsService: Service instance
    """
    global _employment_platforms_service_instance
    
    if _employment_platforms_service_instance is None:
        _employment_platforms_service_instance = EmploymentPlatformsService()
        logger.info("🏢 EmploymentPlatformsService initialized")
    
    return _employment_platforms_service_instance


def get_sample_platforms_data() -> List[EmploymentPlatformCreate]:
    """
    Get sample employment platforms data for initial population
    
    Returns:
        List of sample platform creation data
    """
    sample_platforms = [
        # Technology Platforms
        EmploymentPlatformCreate(
            name="LinkedIn",
            type=PlatformTypeEnum.networking,
            url="https://www.linkedin.com",
            description="Red profesional global para conectar con empleadores y encontrar oportunidades laborales",
            country="Global",
            category=PlatformCategoryEnum.technology,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="InfoJobs",
            type=PlatformTypeEnum.job_board,
            url="https://www.infojobs.net",
            description="Portal de empleo líder en España con ofertas de trabajo de todas las categorías",
            country="España",
            category=PlatformCategoryEnum.general,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="Indeed",
            type=PlatformTypeEnum.job_board,
            url="https://www.indeed.com",
            description="Motor de búsqueda de empleos internacional con millones de ofertas de trabajo",
            country="Global",
            category=PlatformCategoryEnum.general,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="Stack Overflow Jobs",
            type=PlatformTypeEnum.job_board,
            url="https://stackoverflow.com/jobs",
            description="Plataforma de empleo especializada en tecnología y desarrollo de software",
            country="Global",
            category=PlatformCategoryEnum.technology,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="Freelancer",
            type=PlatformTypeEnum.freelance,
            url="https://www.freelancer.com",
            description="Marketplace global para proyectos freelance en tecnología, diseño y marketing",
            country="Global",
            category=PlatformCategoryEnum.freelance,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="Upwork",
            type=PlatformTypeEnum.freelance,
            url="https://www.upwork.com",
            description="Plataforma líder para trabajo freelance y remoto en diversas categorías",
            country="Global",
            category=PlatformCategoryEnum.freelance,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="GitHub Jobs",
            type=PlatformTypeEnum.job_board,
            url="https://jobs.github.com",
            description="Portal de empleos para desarrolladores y profesionales de tecnología",
            country="Global",
            category=PlatformCategoryEnum.technology,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="Dribbble Jobs",
            type=PlatformTypeEnum.job_board,
            url="https://dribbble.com/jobs",
            description="Portal de empleos especializado en diseño gráfico y creativo",
            country="Global",
            category=PlatformCategoryEnum.design,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="AngelList",
            type=PlatformTypeEnum.startup,
            url="https://angel.co",
            description="Plataforma para encontrar empleos en startups y empresas tecnológicas",
            country="Global",
            category=PlatformCategoryEnum.technology,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="Remote.co",
            type=PlatformTypeEnum.remote_work,
            url="https://remote.co",
            description="Portal especializado en trabajos remotos de diversas categorías",
            country="Global",
            category=PlatformCategoryEnum.remote,
            validated=True
        ),
        # Spanish specific platforms
        EmploymentPlatformCreate(
            name="Computrabajo",
            type=PlatformTypeEnum.job_board,
            url="https://www.computrabajo.es",
            description="Portal de empleo con presencia en España y América Latina",
            country="España",
            category=PlatformCategoryEnum.general,
            validated=True
        ),
        EmploymentPlatformCreate(
            name="Job Today",
            type=PlatformTypeEnum.job_board,
            url="https://es.jobtoday.world",
            description="Aplicación móvil para encontrar trabajo rápido en España",
            country="España",
            category=PlatformCategoryEnum.general,
            validated=True
        )
    ]
    
    return sample_platforms


async def populate_sample_platforms() -> bool:
    """
    Populate database with sample employment platforms
    
    Returns:
        True if successful, False otherwise
    """
    try:
        service = get_employment_platforms_service()
        sample_data = get_sample_platforms_data()
        
        created_platforms = await service.bulk_create_platforms(sample_data)
        
        logger.info(f"✅ Successfully populated {len(created_platforms)} sample employment platforms")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error populating sample platforms: {e}")
        return False