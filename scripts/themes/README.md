# Scripts de Temas

Scripts para crear y gestionar temas del proyecto ATScard.

## Scripts Disponibles

### `create_default_themes.py`
- **Propósito**: Crea los temas básicos del sistema
- **Uso**: `python scripts/themes/create_default_themes.py`
- **Temas creados**:
  1. **Clásico Profesional** (classic template) - Colores modernos con Inter
  2. **Móvil Moderno** (mobile template) - Azules optimizados para móvil
  3. **Elegante Oscuro** (classic template) - Tema oscuro con Playfair Display
  4. **Colorido Moderno** (mobile template) - Púrpuras vibrantes con Poppins
  5. **Minimalista** (classic template) - Negro/blanco con Roboto

### `create_global_themes.py`
- **Propósito**: Crea temas globales profesionales con diferentes templates
- **Uso**: `python scripts/themes/create_global_themes.py`
- **Temas creados**:
  
  **Classic Templates:**
  - **Ejecutivo Clásico** - Azules corporativos
  - **Creativo Clásico** - Púrpuras creativos
  
  **Business Templates:**
  - **Corporativo** - Grises formales con avatar rectangular
  - **Startup** - Púrpuras dinámicos para startups
  - **Consultor Profesional** - Azules consultores
  - **Lujo Premium** - Rojos elegantes con Playfair Display

### `add_mobile_themes.py`
- **Propósito**: Agrega temas específicos para el template móvil
- **Uso**: `python scripts/themes/add_mobile_themes.py`
- **Temas creados**:
  1. **Móvil Moderno** - Azul corporativo con Inter
  2. **Móvil Oscuro** - Tema oscuro minimalista
  3. **Móvil Colorido** - Púrpuras vibrantes con Poppins

## Características de los Temas

### Campos Configurados
Todos los temas incluyen:
- `name`: Nombre descriptivo
- `template_name`: Template a usar (classic, business, mobile)
- `primary_color`, `secondary_color`, `accent_color`: Colores principales
- `font_family`: Tipografía (Inter, Poppins, Playfair Display, Roboto)
- `layout`: Estilo de diseño (classic, modern, minimal)
- `avatar_shape`: Forma del avatar (circle, rounded, square, rectangle)
- `is_active`: Activo por defecto
- `is_global`: True para temas del sistema
- `created_by_id`: None para temas globales

### Templates Disponibles
- **classic**: Diseño vertical tradicional
- **business**: Diseño horizontal estilo tarjeta de negocio
- **mobile**: Diseño optimizado para móviles

## Uso Recomendado

### Para Proyecto Nuevo
1. Ejecutar `create_default_themes.py` primero
2. Luego `create_global_themes.py` para más opciones
3. Opcional: `add_mobile_themes.py` para temas móviles específicos

### Para Actualización
Solo ejecutar los scripts que agreguen temas que no existen.

## Verificación
```sql
SELECT name, template_name, is_global FROM theme ORDER BY template_name, name;
```