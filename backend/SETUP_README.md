# 🛠️ Setup de OrientaTech

Script de configuración automática para el proyecto OrientaTech.

## 📋 ¿Qué hace este script?

El script `setup.py` verifica y configura automáticamente todo lo necesario para ejecutar OrientaTech:

### ✅ Verificaciones automáticas:
1. **Archivo .env** - Existe y tiene variables requeridas
2. **Directorios** - Crea carpetas docs/, users/, temp/, quarantine/
3. **Conexión PostgreSQL** - Verifica que el servidor esté accesible
4. **Base de datos** - Crea la BD del proyecto si no existe
5. **Tablas** - Crea tabla 'users' e índices si no existen
6. **Verificación final** - Confirma que todo funciona

## 🚀 Uso del script

### Primera configuración:
```bash
# 1. Configura tu archivo .env
cp .env.example .env
# Edita .env con tus datos de PostgreSQL

# 2. Ejecuta el setup
python setup.py
```

### Si ya tienes el proyecto configurado:
```bash
# El script solo verificará que todo esté bien
python setup.py
```

## 📊 Salida del script

### ✅ Configuración exitosa:
```
============================================================
🚀 OrientaTech - Configuración Inicial del Proyecto
============================================================

🔍 Verificando archivo .env...
✅ Archivo .env válido

🔍 Verificando directorios del proyecto...
✅ Directorios creados: users, temp, quarantine

🔍 Verificando conexión a PostgreSQL...
✅ Conexión al servidor PostgreSQL exitosa

🔧 Verificando base de datos del proyecto...
✅ Base de datos verificada/creada

🔧 Verificando tablas de la base de datos...
✅ Tablas verificadas/creadas

🔍 Realizando verificación final...
✅ Verificación final exitosa

============================================================
🎉 ¡Configuración completada exitosamente!
============================================================

🚀 El proyecto OrientaTech está listo para usar.
   Puedes ejecutar: python main.py
```

### ❌ Si hay problemas:
```
============================================================
🚀 OrientaTech - Configuración Inicial del Proyecto
============================================================

🔍 Verificando archivo .env...
❌ Archivo .env no encontrado

📋 Para configurar el proyecto:
   1. Copia .env.example a .env
   2. Configura las variables de base de datos
   3. Ejecuta este script nuevamente

============================================================
🛑 Configuración incompleta
============================================================

❌ Hay problemas que requieren atención manual.
   Revisa los errores mostrados arriba.
```

## 🔧 Variables requeridas en .env

El script verifica estas variables críticas:

```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@host:puerto/database
DB_PROJECT=OrientaTech_db

# JWT
JWT_SECRET_KEY=tu_clave_secreta_jwt

# Opcional pero recomendado
USER_FOLDER_SALT=salt_para_carpetas_usuarios
MAX_FILE_SIZE_MB=5
ALLOWED_FILE_TYPES=pdf,doc,docx
```

## 🗃️ Recursos que utiliza

El script usa los módulos existentes del proyecto:

- `database/create_database.py` - Para crear la base de datos
- `database/db_tables_creation.py` - Para crear tablas
- `database/db_connection.py` - Para conexiones
- `.env` - Para configuración

## 🚨 Solución de problemas

### Error de conexión a PostgreSQL:
1. Verifica que PostgreSQL esté ejecutándose
2. Verifica DATABASE_URL en .env
3. Verifica credenciales de acceso

### Error de permisos:
1. Asegúrate de tener permisos de escritura en el directorio
2. En sistemas Unix: `chmod +x setup.py`

### Variables de entorno faltantes:
1. Copia .env.example a .env
2. Configura todas las variables requeridas

## 📁 Directorios que crea

```
backend/
└── docs/
    ├── users/          # Carpetas hasheadas por usuario
    ├── temp/           # Archivos temporales de subida
    ├── quarantine/     # Archivos en cuarentena
    └── README.md       # Documentación automática
```

---
*Este script es parte del proyecto OrientaTech - API de gestión de usuarios y documentos*