# Scripts de Mantenimiento

Esta carpeta contiene scripts útiles para el mantenimiento y configuración del proyecto ATScard.

## Estructura de Carpetas

### `/database`
Scripts para actualizar y mantener la base de datos:
- Migraciones manuales
- Correcciones de datos
- Actualizaciones de esquema

### `/themes`
Scripts para crear y gestionar temas:
- Creación de temas por defecto
- Temas globales
- Temas específicos por template

### `/testing`
Scripts de prueba y testing:
- Tests de funcionalidad
- Validación de datos
- Scripts de debug

## Uso General

Todos los scripts están diseñados para ser ejecutados desde la raíz del proyecto:

```bash
python scripts/database/script_name.py
python scripts/themes/script_name.py
python scripts/testing/script_name.py
```

**Importante:** Siempre hacer backup de la base de datos antes de ejecutar scripts de database.