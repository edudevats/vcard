#!/usr/bin/env python
"""
Script ejecutor principal para scripts de mantenimiento
Facilita la ejecución de scripts organizados por categoría
"""
import os
import sys
import importlib.util
from pathlib import Path

def get_available_scripts():
    """Obtiene todos los scripts disponibles organizados por categoría"""
    base_path = Path(__file__).parent
    scripts = {}
    
    # Recorrer subcarpetas
    for category_dir in ['database', 'themes', 'testing']:
        category_path = base_path / category_dir
        if category_path.exists():
            scripts[category_dir] = []
            for script_file in category_path.glob('*.py'):
                if script_file.name != '__init__.py':
                    scripts[category_dir].append(script_file.stem)
    
    return scripts

def load_and_run_script(category, script_name):
    """Carga y ejecuta un script específico"""
    base_path = Path(__file__).parent
    script_path = base_path / category / f"{script_name}.py"
    
    if not script_path.exists():
        print(f"❌ Script no encontrado: {script_path}")
        return False
    
    try:
        # Cargar el módulo dinámicamente
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        
        # Agregar el directorio del script al path para imports relativos
        sys.path.insert(0, str(script_path.parent.parent.parent))
        
        print(f"🚀 Ejecutando: {category}/{script_name}.py")
        print("-" * 50)
        
        # Ejecutar el script
        spec.loader.exec_module(module)
        
        # Ejecutar la función main si existe
        if hasattr(module, script_name.replace('_', '')):
            getattr(module, script_name.replace('_', ''))()
        elif hasattr(module, 'main'):
            module.main()
        
        print("-" * 50)
        print(f"✅ Script completado: {script_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando script: {e}")
        return False
    finally:
        # Limpiar path
        if str(script_path.parent.parent.parent) in sys.path:
            sys.path.remove(str(script_path.parent.parent.parent))

def show_menu():
    """Muestra el menú interactivo"""
    scripts = get_available_scripts()
    
    print("\n" + "="*60)
    print("🛠️  SCRIPTS DE MANTENIMIENTO VCARD")
    print("="*60)
    
    all_options = []
    option_num = 1
    
    for category, script_list in scripts.items():
        print(f"\n📁 {category.upper()}")
        print("-" * 20)
        
        for script in script_list:
            print(f"  {option_num}. {script}")
            all_options.append((category, script))
            option_num += 1
    
    print(f"\n  {option_num}. ❌ Salir")
    print("\n" + "="*60)
    
    return all_options

def main():
    """Función principal del menú interactivo"""
    while True:
        options = show_menu()
        
        try:
            choice = input("\n🔢 Selecciona una opción: ").strip()
            
            if not choice.isdigit():
                print("❌ Por favor ingresa un número válido")
                continue
            
            choice_num = int(choice)
            
            # Opción salir
            if choice_num == len(options) + 1:
                print("👋 ¡Hasta luego!")
                break
            
            # Validar opción
            if choice_num < 1 or choice_num > len(options):
                print("❌ Opción inválida")
                continue
            
            # Ejecutar script
            category, script_name = options[choice_num - 1]
            
            # Confirmar ejecución
            print(f"\n⚠️  ¿Confirmas ejecutar {category}/{script_name}.py?")
            if category == 'database':
                print("   📄 Recuerda hacer backup de la base de datos primero")
            
            confirm = input("   (s/N): ").strip().lower()
            if confirm in ['s', 'si', 'sí', 'y', 'yes']:
                success = load_and_run_script(category, script_name)
                if success:
                    input("\n⏸️  Presiona Enter para continuar...")
            else:
                print("❌ Operación cancelada")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()