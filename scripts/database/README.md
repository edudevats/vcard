# Scripts de Base de Datos

Scripts para actualizar y mantener la base de datos del proyecto ATScard.

## ⚠️ IMPORTANTE
**SIEMPRE hacer backup de la base de datos antes de ejecutar cualquier script.**

## Scripts Disponibles

### Actualizaciones de Campos

#### `add_avatar_border_color.py`
- **Propósito**: Agrega el campo `avatar_border_color` a la tabla `theme`
- **Uso**: `python scripts/database/add_avatar_border_color.py`
- **Efecto**: 
  - Añade columna `avatar_border_color VARCHAR(7) DEFAULT '#ffffff'`
  - Actualiza temas existentes con borde blanco por defecto

#### `add_theme_privacy.py`
- **Propósito**: Agrega campos de privacidad a la tabla `theme`
- **Uso**: `python scripts/database/add_theme_privacy.py`
- **Efecto**:
  - Añade columna `is_global BOOLEAN DEFAULT 0`
  - Añade columna `created_by_id INTEGER`
  - Marca temas existentes como globales

#### `update_existing_themes.py`
- **Propósito**: Actualiza temas existentes con nuevos campos
- **Uso**: `python scripts/database/update_existing_themes.py`
- **Efecto**:
  - Establece `template_name='classic'` para temas sin template
  - Establece `is_active=True` para temas sin estado

### Correcciones de Datos

#### `fix_theme_layouts.py`
- **Propósito**: Corrige layouts de temas con valores enum inválidos
- **Uso**: `python scripts/database/fix_theme_layouts.py`
- **Efecto**:
  - Convierte 'geometric' → 'modern'
  - Convierte 'elegant' → 'minimal'

#### `fix_themes_direct.py`
- **Propósito**: Corrección directa por SQL de layouts inválidos
- **Uso**: `python scripts/database/fix_themes_direct.py`
- **Efecto**: Misma corrección que el anterior pero con SQL directo

#### `update_theme_layouts.py`
- **Propósito**: Actualiza esquema para soportar nuevos layouts
- **Uso**: `python scripts/database/update_theme_layouts.py`
- **Efecto**: Prepara columna para nuevos valores de layout

## Orden de Ejecución Recomendado

Para un proyecto nuevo:
1. `add_theme_privacy.py`
2. `add_avatar_border_color.py`
3. `update_existing_themes.py`
4. `fix_theme_layouts.py`

## Verificación Post-Ejecución

Después de ejecutar scripts, verificar:
```sql
-- Verificar estructura de tabla
PRAGMA table_info(theme);

-- Verificar datos
SELECT name, template_name, is_global, avatar_border_color, layout FROM theme LIMIT 5;
```