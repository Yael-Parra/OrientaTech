"""
Script de verificación rápida del sistema OrientaTech
Ejecuta tests básicos y muestra el estado del sistema
"""
import sys
from pathlib import Path

# Añadir el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_system_status import run_all_tests


def quick_check():
    """Verificación rápida del estado del sistema"""
    print("🔍 OrientaTech - Verificación Rápida del Sistema")
    print("=" * 50)
    
    try:
        success = run_all_tests()
        
        if success:
            print("\n🎯 RESULTADO: Sistema listo para producción")
            print("💡 Puedes ejecutar: python main.py")
        else:
            print("\n⚠️ RESULTADO: Sistema requiere atención")
            print("💡 Ejecuta: python setup.py")
            
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("💡 Verifica la instalación y configuración")
        return False


if __name__ == "__main__":
    success = quick_check()
    sys.exit(0 if success else 1)