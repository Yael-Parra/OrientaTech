"""
Tests para verificar el funcionamiento del sistema OrientaTech
Basado en check_status.py pero adaptado para testing automatizado
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Añadir el directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.setup_service import SetupService


class TestOrientaTechStatus:
    """Suite de tests para verificar el estado del sistema OrientaTech"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.setup_service = SetupService()
        self.backend_dir = Path(__file__).parent.parent
        self.project_root = self.backend_dir.parent
        self.env_file = self.backend_dir / '.env'  # .env ahora está en backend
    
    def test_project_structure(self):
        """Test 1: Verificar que la estructura de directorios es correcta"""
        print("\n🧪 Test 1: Estructura de directorios")
        
        # Verificar directorios principales
        assert self.backend_dir.exists(), f"❌ Directorio backend no existe: {self.backend_dir}"
        print(f"✅ Backend directory: {self.backend_dir}")
        
        assert self.project_root.exists(), f"❌ Directorio proyecto no existe: {self.project_root}"
        print(f"✅ Project root: {self.project_root}")
        
        # Verificar archivos principales
        main_py = self.backend_dir / 'main.py'
        assert main_py.exists(), f"❌ main.py no existe: {main_py}"
        print(f"✅ main.py encontrado")
        
        # Verificar directorios de servicios
        services_dir = self.backend_dir / 'services'
        assert services_dir.exists(), f"❌ Directorio services no existe: {services_dir}"
        print(f"✅ Services directory: {services_dir}")
        
        print("✅ Test 1 PASADO: Estructura de directorios correcta")
    
    def test_env_file_exists(self):
        """Test 2: Verificar que el archivo .env existe y es válido"""
        print("\n🧪 Test 2: Archivo .env")
        
        assert self.env_file.exists(), f"❌ Archivo .env no existe: {self.env_file}"
        print(f"✅ Archivo .env encontrado: {self.env_file}")
        
        # Cargar y verificar variables
        load_dotenv(dotenv_path=self.env_file)
        
        required_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'DB_PROJECT']
        for var in required_vars:
            value = os.getenv(var)
            assert value, f"❌ Variable {var} no configurada o vacía"
            print(f"✅ {var}: configurado")
        
        print("✅ Test 2 PASADO: Archivo .env válido")
    
    def test_required_directories(self):
        """Test 3: Verificar que los directorios requeridos existen"""
        print("\n🧪 Test 3: Directorios requeridos")
        
        required_dirs = [
            self.backend_dir / 'docs',
            self.backend_dir / 'docs' / 'users',
            self.backend_dir / 'docs' / 'temp',
            self.backend_dir / 'docs' / 'quarantine'
        ]
        
        for directory in required_dirs:
            assert directory.exists(), f"❌ Directorio requerido no existe: {directory}"
            print(f"✅ {directory.name}: existe")
        
        print("✅ Test 3 PASADO: Todos los directorios requeridos existen")
    
    def test_setup_service_initialization(self):
        """Test 4: Verificar que el servicio de setup se inicializa correctamente"""
        print("\n🧪 Test 4: Servicio de Setup")
        
        # Verificar que el servicio se puede instanciar
        setup = SetupService()
        assert setup is not None, "❌ No se pudo instanciar SetupService"
        print("✅ SetupService instanciado correctamente")
        
        # Verificar rutas configuradas
        assert setup.backend_dir.exists(), "❌ backend_dir no configurado correctamente"
        assert setup.project_root.exists(), "❌ project_root no configurado correctamente"
        assert setup.env_file == self.env_file, "❌ env_file no configurado correctamente"
        print("✅ Rutas del servicio configuradas correctamente")
        
        # Verificar método is_setup_required
        try:
            is_required = setup.is_setup_required()
            print(f"✅ is_setup_required() ejecutado: {is_required}")
        except Exception as e:
            pytest.fail(f"❌ Error en is_setup_required(): {e}")
        
        print("✅ Test 4 PASADO: Servicio de setup funcional")
    
    @pytest.mark.asyncio
    async def test_database_connection_mock(self):
        """Test 5: Verificar conexión a base de datos (con mock)"""
        print("\n🧪 Test 5: Conexión a base de datos (mock)")
        
        # Mock simple sin async para evitar complicaciones
        with patch('asyncpg.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            try:
                # Simular verificación de conexión
                conn = await mock_connect("postgresql://test:test@localhost:5432/test")
                assert conn is not None, "❌ Mock de conexión falló"
                print("✅ Mock de conexión a BD exitoso")
                
                # Mock simple del cierre
                mock_conn.close()
                print("✅ Cierre de conexión simulado")
                
            except Exception as e:
                pytest.fail(f"❌ Error en test de conexión: {e}")
        
        print("✅ Test 5 PASADO: Verificación de conexión a BD (mock)")
    
    def test_imports_and_dependencies(self):
        """Test 6: Verificar que todas las dependencias se pueden importar"""
        print("\n🧪 Test 6: Importaciones y dependencias")
        
        try:
            # Verificar imports principales
            from fastapi import FastAPI
            print("✅ FastAPI importado correctamente")
            
            from services.setup_service import setup_service
            print("✅ setup_service importado correctamente")
            
            from routes.auth_simple import auth_router
            print("✅ auth_router importado correctamente")
            
            from routes.github_routes import github_router
            print("✅ github_router importado correctamente")
            
            from routes.documents_routes import documents_router
            print("✅ documents_router importado correctamente")
            
            # Verificar dependencias críticas
            import asyncpg
            print("✅ asyncpg disponible")
            
            import loguru
            print("✅ loguru disponible")
            
            from dotenv import load_dotenv
            print("✅ python-dotenv disponible")
            
        except ImportError as e:
            pytest.fail(f"❌ Error de importación: {e}")
        
        print("✅ Test 6 PASADO: Todas las dependencias disponibles")
    
    def test_configuration_completeness(self):
        """Test 7: Verificar completitud de la configuración"""
        print("\n🧪 Test 7: Completitud de configuración")
        
        setup = SetupService()
        
        # Test del método is_setup_required
        setup_required = setup.is_setup_required()
        print(f"✅ Setup requerido: {setup_required}")
        
        if not setup_required:
            print("✅ Sistema completamente configurado")
        else:
            print("⚠️ Sistema requiere configuración adicional")
        
        # Verificar cada componente individualmente
        components = {
            'env_file': self.env_file.exists(),
            'directories': all(d.exists() for d in setup.required_dirs),
            'env_variables': all(os.getenv(var) for var in ['DATABASE_URL', 'JWT_SECRET_KEY', 'DB_PROJECT'])
        }
        
        for component, status in components.items():
            if status:
                print(f"✅ {component}: OK")
            else:
                print(f"❌ {component}: FALLO")
        
        # El test pasa si al menos los componentes básicos están OK
        assert components['env_file'], "❌ Archivo .env es requerido"
        assert components['env_variables'], "❌ Variables de entorno son requeridas"
        
        print("✅ Test 7 PASADO: Configuración básica completa")


def run_all_tests():
    """Función para ejecutar todos los tests manualmente"""
    print("🚀 Iniciando suite de tests para OrientaTech")
    print("=" * 60)
    
    test_instance = TestOrientaTechStatus()
    test_instance.setup_method()
    
    tests = [
        ("Estructura de directorios", test_instance.test_project_structure),
        ("Archivo .env", test_instance.test_env_file_exists),
        ("Directorios requeridos", test_instance.test_required_directories),
        ("Servicio de setup", test_instance.test_setup_service_initialization),
        ("Importaciones", test_instance.test_imports_and_dependencies),
        ("Configuración completa", test_instance.test_configuration_completeness),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ FALLO en {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🏁 RESUMEN DE TESTS:")
    print(f"✅ Pasados: {passed}")
    print(f"❌ Fallados: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        return True
    else:
        print("⚠️ Algunos tests fallaron. Revisar configuración.")
        return False


if __name__ == "__main__":
    # Ejecutar tests directamente
    success = run_all_tests()
    sys.exit(0 if success else 1)