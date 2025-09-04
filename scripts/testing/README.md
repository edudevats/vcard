# Scripts de Testing

Scripts para probar y validar funcionalidades del proyecto VCard.

## Scripts Disponibles

### `test_business_template.py`
- **Propósito**: Prueba el template business asignándolo a una tarjeta existente
- **Uso**: `python scripts/testing/test_business_template.py`
- **Funcionalidad**:
  - Busca la primera tarjeta en la base de datos
  - Busca un tema con template 'business'
  - Asigna el tema business a la tarjeta
  - Muestra la URL para ver el resultado

### `test_palettes.py`
- **Propósito**: Prueba el sistema de paletas de colores
- **Uso**: `python scripts/testing/test_palettes.py`
- **Funcionalidad**:
  - Carga todas las paletas disponibles
  - Prueba una paleta específica ('business')
  - Valida manejo de paletas inexistentes
  - Lista todas las paletas con descripción

## Uso Recomendado

### Antes de Usar
Asegurarse de que:
1. La base de datos tenga datos de prueba
2. Existan temas en la base de datos
3. El sistema de paletas esté configurado

### Para Testing de Templates
1. Ejecutar `test_business_template.py`
2. Visitar la URL mostrada para verificar el template
3. Probar diferentes templates modificando el script

### Para Testing de Paletas
1. Ejecutar `test_palettes.py`
2. Verificar que todas las paletas se cargan correctamente
3. Usar la información para debugging del sistema de colores

## Modificaciones Sugeridas

### Para test_business_template.py
```python
# Cambiar template a probar
business_theme = Theme.query.filter_by(template_name='classic').first()

# Probar con tarjeta específica
card = Card.query.filter_by(name='Nombre Específico').first()
```

### Para test_palettes.py
```python
# Probar paleta específica
test_palette = get_palette('creative')  # cambiar 'creative' por otra paleta
```

## Debugging
Los scripts incluyen print statements para tracking:
- Estado de operaciones
- Datos encontrados
- URLs resultantes
- Errores o advertencias