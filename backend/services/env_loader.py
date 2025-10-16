"""
Utilidad para cargar variables de entorno de manera consistente
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_env_vars():
    """
    Carga las variables de entorno del archivo .env ubicado en el directorio backend
    
    Esta función busca el archivo .env en el directorio backend del proyecto,
    independientemente de desde dónde se ejecute el script.
    """
    # Obtener el directorio backend (donde debe estar el .env)
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent  # desde services/ vamos a backend/
    env_file = backend_dir / '.env'
    
    # Cargar variables de entorno
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        return True
    else:
        # Fallback: intentar cargar desde el directorio actual
        load_dotenv()
        return os.getenv("DATABASE_URL") is not None

# Función de conveniencia para importar directamente
def get_env_var(key: str, default: str = None) -> str:
    """
    Obtiene una variable de entorno, cargando el .env si es necesario
    
    Args:
        key: Nombre de la variable de entorno
        default: Valor por defecto si no se encuentra la variable
        
    Returns:
        Valor de la variable de entorno o el valor por defecto
    """
    # Asegurar que las variables estén cargadas
    load_env_vars()
    return os.getenv(key, default)