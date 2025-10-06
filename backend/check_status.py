"""
Script de verificación del estado del proyecto OrientaTech (solo lectura)
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

class OrientaTechChecker:
    """Verificador de estado del proyecto (solo lectura)"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.project_root = self.base_dir.parent
        self.env_file = self.project_root / '.env'  # .env está en el directorio padre OrientaTech/
        
    def print_header(self):
        print("=" * 50)
        print("🔍 OrientaTech - Estado del Proyecto")
        print("=" * 50)
        print()
    
    def check_env_status(self):
        """Verifica estado del archivo .env"""
        print("📄 Estado del archivo .env:")
        print(f"   🔍 Buscando en: {self.env_file}")
        
        if not self.env_file.exists():
            print("   ❌ .env no encontrado")
            return False
        
        load_dotenv(dotenv_path=self.env_file)
        print("   ✅ Archivo .env encontrado y cargado")
        
        required_vars = {
            'DATABASE_URL': 'Conexión a base de datos',
            'JWT_SECRET_KEY': 'Clave secreta JWT', 
            'DB_PROJECT': 'Nombre de la base de datos'
        }
        
        all_good = True
        for var, desc in required_vars.items():
            value = os.getenv(var)
            if value:
                print(f"   ✅ {var}: {'*' * min(len(value), 20)}")
            else:
                print(f"   ❌ {var}: No configurado")
                all_good = False
        
        return all_good
    
    def check_directories_status(self):
        """Verifica estado de los directorios"""
        print("\n📁 Estado de directorios:")
        
        required_dirs = [
            ('backend/docs', 'Directorio principal de documentos'),
            ('backend/docs/users', 'Carpetas de usuarios'),
            ('backend/docs/temp', 'Archivos temporales'),
            ('backend/docs/quarantine', 'Archivos en cuarentena')
        ]
        
        all_good = True
        for dir_path, desc in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                print(f"   ✅ {dir_path}: Existe")
            else:
                print(f"   ❌ {dir_path}: No existe")
                all_good = False
        
        return all_good
    
    async def check_database_status(self):
        """Verifica estado de la base de datos"""
        print("\n🗃️ Estado de la base de datos:")
        
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                print("   ❌ DATABASE_URL no configurado")
                return False
            
            # Verificar conexión al servidor PostgreSQL
            from urllib.parse import urlparse
            parsed_url = urlparse(database_url)
            
            try:
                default_db_url = f"{parsed_url.scheme}://{parsed_url.netloc}/postgres"
                if parsed_url.query:
                    default_db_url += f"?{parsed_url.query}"
                
                conn = await asyncpg.connect(default_db_url)
                print("   ✅ Servidor PostgreSQL: Accesible")
                
                # Verificar si la BD del proyecto existe
                db_name = os.getenv("DB_PROJECT")
                if db_name:
                    result = await conn.fetchval(
                        "SELECT 1 FROM pg_database WHERE datname = $1", db_name
                    )
                    if result:
                        print(f"   ✅ Base de datos '{db_name}': Existe")
                    else:
                        print(f"   ❌ Base de datos '{db_name}': No existe")
                        await conn.close()
                        return False
                
                await conn.close()
                
                # Verificar conexión a la BD del proyecto y tabla users
                try:
                    from database.db_connection import connect_async
                    project_conn = await connect_async()
                    
                    if project_conn:
                        print(f"   ✅ Conexión a '{db_name}': Exitosa")
                        
                        # Verificar tabla users
                        table_exists = await project_conn.fetchval(
                            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                        )
                        
                        if table_exists:
                            # Contar usuarios
                            user_count = await project_conn.fetchval("SELECT COUNT(*) FROM users")
                            print(f"   ✅ Tabla 'users': Existe ({user_count} usuarios)")
                        else:
                            print("   ❌ Tabla 'users': No existe")
                            await project_conn.close()
                            return False
                        
                        await project_conn.close()
                        return True
                    else:
                        print(f"   ❌ Conexión a '{db_name}': Falló")
                        return False
                        
                except Exception as e:
                    print(f"   ❌ Error conectando a '{db_name}': {e}")
                    return False
                
            except Exception as e:
                print(f"   ❌ Servidor PostgreSQL: No accesible ({e})")
                return False
                
        except Exception as e:
            print(f"   ❌ Error general de base de datos: {e}")
            return False
    
    async def run_check(self):
        """Ejecuta todas las verificaciones"""
        self.print_header()
        
        # Verificaciones
        env_ok = self.check_env_status()
        dirs_ok = self.check_directories_status()
        db_ok = await self.check_database_status()
        
        # Resumen final
        print("\n" + "=" * 50)
        print("📊 Resumen del estado:")
        print("=" * 50)
        
        status_items = [
            ("Configuración (.env)", env_ok),
            ("Directorios", dirs_ok), 
            ("Base de datos", db_ok)
        ]
        
        all_ok = True
        for item, status in status_items:
            icon = "✅" if status else "❌"
            print(f"{icon} {item}")
            if not status:
                all_ok = False
        
        print()
        if all_ok:
            print("🎉 ¡Todo está configurado correctamente!")
            print("   El proyecto está listo para ejecutarse.")
        else:
            print("⚠️ Hay problemas de configuración.")
            print("   Ejecuta 'python setup.py' para solucionarlos.")
        
        print()
        return all_ok

async def main():
    """Función principal"""
    checker = OrientaTechChecker()
    
    try:
        await checker.run_check()
    except KeyboardInterrupt:
        print("\n⚠️ Verificación cancelada")
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")

if __name__ == "__main__":
    asyncio.run(main())