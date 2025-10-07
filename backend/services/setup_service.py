"""
Servicio de configuración automática para OrientaTech
Configuración automática al iniciar la aplicación
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
import asyncpg


class SetupService:
    """Servicio de configuración automática del proyecto OrientaTech"""
    
    def __init__(self):
        # Configuración de rutas
        self.backend_dir = Path(__file__).parent.parent.absolute()
        self.project_root = self.backend_dir.parent
        self.env_file = self.project_root / '.env'
        self.required_dirs = [
            self.backend_dir / 'docs',
            self.backend_dir / 'docs' / 'users',
            self.backend_dir / 'docs' / 'temp', 
            self.backend_dir / 'docs' / 'quarantine'
        ]
        
    def check_env_file(self) -> bool:
        """Verifica que el archivo .env existe"""
        logger.info(f"Verificando archivo .env en: {self.env_file}")
        
        if not self.env_file.exists():
            logger.error("Archivo .env no encontrado")
            return False
            
        try:
            load_dotenv(dotenv_path=self.env_file)
            
            required_vars = {
                'DATABASE_URL': 'Conexión a base de datos',
                'JWT_SECRET_KEY': 'Clave secreta JWT', 
                'DB_PROJECT': 'Nombre de la base de datos'
            }
            
            for var, desc in required_vars.items():
                if not os.getenv(var):
                    logger.error(f"Variable {var} no configurada")
                    return False
                    
            logger.success("Archivo .env válido")
            return True
            
        except Exception as e:
            logger.error(f"Error validando .env: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Crea los directorios necesarios del proyecto"""
        logger.info("Verificando directorios del proyecto...")
        
        try:
            created_any = False
            for directory in self.required_dirs:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Directorio creado: {directory}")
                    created_any = True
                    
            if not created_any:
                logger.info("Todos los directorios ya existen")
            else:
                logger.success("Directorios creados exitosamente")
                
            return True
            
        except Exception as e:
            logger.error(f"Error creando directorios: {e}")
            return False
    
    def test_postgres_connection(self) -> bool:
        """Verifica la conexión a la base de datos configurada (Neon/PostgreSQL)"""
        logger.info("Verificando conexión a la base de datos...")
        
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.error("DATABASE_URL no configurado")
                return False
                
            # Usar directamente la DATABASE_URL configurada (incluye Neon)
            logger.info(f"Conectando a base de datos: {database_url.split('@')[1] if '@' in database_url else 'configurada'}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def test_connection():
                conn = await asyncpg.connect(database_url)
                await conn.close()
                
            loop.run_until_complete(test_connection())
            loop.close()
            
            logger.success("Conexión a la base de datos exitosa")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Configura la base de datos y crea tablas"""
        logger.info("Verificando base de datos del proyecto...")
        
        try:
            database_url = os.getenv("DATABASE_URL")
            
            # Detectar si es una conexión de Neon (base de datos en la nube)
            if "neon.tech" in database_url:
                logger.info("Detectada base de datos Neon - omitiendo creación de DB")
                # Para Neon, la base de datos ya existe, solo creamos tablas
            else:
                # Para PostgreSQL local, crear base de datos si no existe
                logger.info("Detectada base de datos local - verificando creación")
                from database.create_database import create_database
                create_database()
                logger.success("Base de datos verificada/creada")
            
            # Crear tablas esenciales en cualquier caso
            from database.db_tables_creation import create_all_tables
            create_all_tables()
            logger.success("Tablas verificadas/creadas")
            
            return True
            
        except Exception as e:
            logger.error(f"Error configurando base de datos: {e}")
            return False
    
    async def verify_final_setup(self) -> bool:
        """Realiza una verificación final del sistema"""
        logger.info("Realizando verificación final...")
        
        try:
            from database.db_connection import connect_async, disconnect_async
            
            # Verificar conexión async a la base de datos
            conn = await connect_async()
            if conn:
                await disconnect_async(conn)
                logger.success("Verificación final exitosa")
                return True
            else:
                logger.error("Fallo en verificación final")
                return False
                
        except Exception as e:
            logger.error(f"Error en verificación final: {e}")
            return False
    
    def run_full_setup(self) -> dict:
        """Ejecuta el setup completo y retorna el estado de cada paso"""
        results = {
            'env_check': False,
            'directories': False,
            'postgres_connection': False,
            'database_setup': False,
            'final_verification': False
        }
        
        logger.info("🚀 Iniciando configuración automática de OrientaTech...")
        
        # 1. Verificar archivo .env
        results['env_check'] = self.check_env_file()
        if not results['env_check']:
            return results
            
        # 2. Crear directorios
        results['directories'] = self.create_directories()
        if not results['directories']:
            return results
            
        # 3. Verificar PostgreSQL
        results['postgres_connection'] = self.test_postgres_connection()
        if not results['postgres_connection']:
            return results
            
        # 4. Configurar base de datos
        results['database_setup'] = self.setup_database()
        if not results['database_setup']:
            return results
            
        # 5. Verificación final
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results['final_verification'] = loop.run_until_complete(self.verify_final_setup())
        finally:
            loop.close()
            
        return results
    
    def is_setup_required(self) -> bool:
        """Verifica si es necesario ejecutar el setup"""
        # Verificación rápida de componentes críticos
        if not self.env_file.exists():
            return True
            
        if not all(directory.exists() for directory in self.required_dirs):
            return True
            
        # Verificar variables de entorno básicas
        load_dotenv(dotenv_path=self.env_file)
        required_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'DB_PROJECT']
        if not all(os.getenv(var) for var in required_vars):
            return True
            
        return False


# Instancia global del servicio
setup_service = SetupService()