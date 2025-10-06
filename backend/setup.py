"""
Script de configuración inicial para OrientaTech
Verifica y configura automáticamente el proyecto antes del primer uso
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
import asyncpg

# Añadir el directorio actual al path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

class OrientaTechSetup:
    """Configurador automático del proyecto OrientaTech"""
    
    def __init__(self):
        # Configuración de rutas
        self.backend_dir = Path(__file__).parent.absolute()
        self.project_root = self.backend_dir.parent
        self.env_file = self.project_root / '.env'  # .env está en el directorio padre OrientaTech/
        self.required_dirs = [
            self.backend_dir / 'docs',
            self.backend_dir / 'docs' / 'users',
            self.backend_dir / 'docs' / 'temp', 
            self.backend_dir / 'docs' / 'quarantine'
        ]
        
    def print_header(self):
        """Muestra el header del setup"""
        print("=" * 60)
        print("🚀 OrientaTech - Configuración Inicial del Proyecto")
        print("=" * 60)
        print()
    
    def print_step(self, step: str, status: str = "info"):
        """Imprime un paso del proceso"""
        icons = {
            "info": "🔍",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌",
            "working": "🔧"
        }
        icon = icons.get(status, "ℹ️")
        print(f"{icon} {step}")
    
    def check_env_file(self) -> bool:
        """Verifica que el archivo .env existe"""
        self.print_step(f"Verificando archivo .env en: {self.env_file}")
        
        if not self.env_file.exists():
            self.print_step("Archivo .env no encontrado", "error")
            print()
            print("📋 Para configurar el proyecto:")
            print(f"   1. Asegúrate de que .env esté en: {self.env_file}")
            print("   2. O copia .env.example a .env en el directorio backend/")
            print("   3. Configura las variables de base de datos")
            print("   4. Ejecuta este script nuevamente")
            print()
            return False
        
        # Cargar variables de entorno desde el archivo .env en backend/
        load_dotenv(dotenv_path=self.env_file)
        
        # Verificar variables críticas
        required_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'DB_PROJECT']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.print_step("Variables de entorno faltantes", "error")
            print(f"   Faltan: {', '.join(missing_vars)}")
            return False
            
        self.print_step("Archivo .env válido", "success")
        return True
    
    def create_directories(self) -> bool:
        """Crea los directorios necesarios"""
        self.print_step("Verificando directorios del proyecto...")
        
        created_dirs = []
        
        for directory in self.required_dirs:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(directory.name)
                except Exception as e:
                    self.print_step(f"Error creando directorio {directory}: {e}", "error")
                    return False
        
        if created_dirs:
            self.print_step(f"Directorios creados: {', '.join(created_dirs)}", "success")
        else:
            self.print_step("Todos los directorios ya existen", "success")
            
        return True
    
    async def check_database_connection(self) -> bool:
        """Verifica la conexión al servidor PostgreSQL"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                self.print_step("DATABASE_URL no configurado", "error")
                return False
            
            # Intentar conexión al servidor (base postgres por defecto)
            from urllib.parse import urlparse
            parsed_url = urlparse(database_url)
            default_db_url = f"{parsed_url.scheme}://{parsed_url.netloc}/postgres"
            if parsed_url.query:
                default_db_url += f"?{parsed_url.query}"
            
            conn = await asyncpg.connect(default_db_url)
            await conn.close()
            
            self.print_step("Conexión al servidor PostgreSQL exitosa", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error conectando a PostgreSQL: {e}", "error")
            print("   Verifica que PostgreSQL esté ejecutándose")
            print("   Verifica la configuración de DATABASE_URL en .env")
            return False
    
    def create_database(self) -> bool:
        """Crea la base de datos usando el script existente"""
        self.print_step("Verificando base de datos del proyecto...", "working")
        
        try:
            # Importar y ejecutar el script de creación de BD
            from database.create_database import create_database
            
            # Capturar logs para verificar si se creó o ya existía
            old_level = logger.level("INFO")
            
            create_database()
            
            self.print_step("Base de datos verificada/creada", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error configurando base de datos: {e}", "error")
            return False
    
    def create_tables(self) -> bool:
        """Crea las tablas usando el script existente"""
        self.print_step("Verificando tablas de la base de datos...", "working")
        
        try:
            # Importar y ejecutar el script de creación de tablas
            from database.db_tables_creation import create_essential_tables
            
            create_essential_tables()
            
            self.print_step("Tablas verificadas/creadas", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error creando tablas: {e}", "error")
            return False
    
    async def verify_final_setup(self) -> bool:
        """Verificación final de que todo funciona"""
        self.print_step("Realizando verificación final...")
        
        try:
            # Verificar conexión a la BD del proyecto
            from database.db_connection import connect_async
            
            conn = await connect_async()
            if not conn:
                self.print_step("No se puede conectar a la base de datos del proyecto", "error")
                return False
            
            # Verificar que la tabla users existe
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
            
            await conn.close()
            
            if not result:
                self.print_step("Tabla 'users' no encontrada", "error")
                return False
            
            self.print_step("Verificación final exitosa", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Error en verificación final: {e}", "error")
            return False
    
    async def run_setup(self) -> bool:
        """Ejecuta el proceso completo de configuración"""
        self.print_header()
        
        # 1. Verificar .env
        if not self.check_env_file():
            return False
        
        print()
        
        # 2. Crear directorios
        if not self.create_directories():
            return False
        
        print()
        
        # 3. Verificar conexión a PostgreSQL
        self.print_step("Verificando conexión a PostgreSQL...")
        if not await self.check_database_connection():
            return False
        
        print()
        
        # 4. Crear/verificar base de datos
        if not self.create_database():
            return False
        
        print()
        
        # 5. Crear/verificar tablas
        if not self.create_tables():
            return False
        
        print()
        
        # 6. Verificación final
        if not await self.verify_final_setup():
            return False
        
        print()
        print("=" * 60)
        print("🎉 ¡Configuración completada exitosamente!")
        print("=" * 60)
        print()
        print("🚀 El proyecto OrientaTech está listo para usar.")
        print("   Puedes ejecutar: python main.py")
        print()
        
        return True

async def main():
    """Función principal del script"""
    setup = OrientaTechSetup()
    
    try:
        success = await setup.run_setup()
        
        if not success:
            print()
            print("=" * 60)
            print("🛑 Configuración incompleta")
            print("=" * 60)
            print()
            print("❌ Hay problemas que requieren atención manual.")
            print("   Revisa los errores mostrados arriba.")
            print()
            sys.exit(1)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print()
        print("⚠️ Configuración cancelada por el usuario")
        sys.exit(1)
        
    except Exception as e:
        print()
        print(f"❌ Error inesperado durante la configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())