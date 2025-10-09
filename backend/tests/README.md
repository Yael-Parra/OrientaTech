# 🧪 Tests para OrientaTech

Sistema de testing para verificar el estado y funcionamiento de OrientaTech.

## 📁 Estructura

```
tests/
├── __init__.py                 # Paquete Python
├── test_system_status.py       # Suite principal de tests
├── quick_check.py              # Verificación rápida
├── requirements-test.txt       # Dependencias de testing
└── README.md                   # Este archivo
```

## 🚀 Ejecución Rápida

### Verificación básica (sin dependencias adicionales)
```bash
cd backend/tests
python quick_check.py
```

### Con pytest (recomendado)
```bash
cd backend
pip install -r requirements.txt
pytest tests/
```

### Solo dependencias de testing
```bash
cd backend
pip install pytest pytest-asyncio pytest-cov pytest-mock
pytest tests/
```

### Ejecutar tests específicos
```bash
pytest tests/test_system_status.py::TestOrientaTechStatus::test_env_file_exists -v
```

## 📊 Tests Incluidos

### ✅ Test 1: Estructura de directorios
- Verifica que existan los directorios principales
- Comprueba archivos críticos como `main.py`
- Valida estructura de servicios

### ✅ Test 2: Archivo .env
- Verifica existencia del archivo `.env`
- Valida variables de entorno requeridas
- Comprueba configuración de base de datos

### ✅ Test 3: Directorios requeridos
- Verifica carpetas de documentos
- Comprueba estructura de almacenamiento
- Valida permisos de escritura

### ✅ Test 4: Servicio de Setup
- Prueba inicialización del `SetupService`
- Verifica métodos principales
- Comprueba configuración de rutas

### ✅ Test 5: Conexión a base de datos
- Test con mock para evitar dependencias
- Simula conexiones async
- Verifica manejo de errores

### ✅ Test 6: Importaciones
- Verifica que todas las dependencias estén disponibles
- Comprueba imports de módulos propios
- Valida versiones de paquetes críticos

### ✅ Test 7: Configuración completa
- Evaluación integral del sistema
- Verifica completitud de setup
- Reporta estado general

## 🔧 Interpretación de Resultados

### 🎉 Todos los tests pasan
```
🎉 ¡TODOS LOS TESTS PASARON!
🎯 RESULTADO: Sistema listo para producción
💡 Puedes ejecutar: python main.py
```

### ⚠️ Algunos tests fallan
```
⚠️ Algunos tests fallaron. Revisar configuración.
⚠️ RESULTADO: Sistema requiere atención
💡 Ejecuta: python setup.py
```

## 🛠️ Comandos Útiles

### Ejecutar con cobertura
```bash
pytest tests/ --cov=services --cov=routes --cov-report=html
```

### Solo tests rápidos
```bash
pytest tests/ -m "not slow"
```

### Verbose output
```bash
pytest tests/ -v -s
```

### Generar reporte JUnit
```bash
pytest tests/ --junitxml=test-results.xml
```

## 🔍 Debugging

Si algún test falla:

1. **Error en .env**: Verifica que el archivo existe en `OrientaTech/.env`
2. **Error en BD**: Comprueba que PostgreSQL esté corriendo
3. **Error de imports**: Instala dependencias con `pip install -r requirements.txt`
4. **Error de directorios**: Ejecuta `python setup.py` para crear estructura

## 📝 Notas

- Los tests están diseñados para ejecutarse tanto con pytest como directamente
- Se usan mocks para evitar dependencias externas cuando es posible
- Los tests validan la configuración pero no modifican el sistema
- Compatibles con CI/CD para integración continua