from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Email, Optional, URL, NumberRange, Length, ValidationError
import re
from ..models import Theme
from ..constants import FONT_FAMILY_CHOICES, LAYOUT_CHOICES, AVATAR_SHAPE_CHOICES

def flexible_url_validator(form, field):
    """Custom URL validator that is more flexible than the default URL validator"""
    if not field.data:
        return  # Allow empty values
    
    url = field.data.strip()
    if not url:
        return  # Allow empty/whitespace-only values
    
    # If it doesn't start with http/https, add https://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Basic URL pattern check
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValidationError('Por favor ingresa una URL válida (ej: miempresa.com o https://miempresa.com)')

class CardForm(FlaskForm):
    title = StringField('Título de la Tarjeta', validators=[Optional()],
                       render_kw={'class': 'form-control', 'placeholder': 'ej: Juan Pérez - Desarrollador'})
    name = StringField('Nombre Completo', validators=[DataRequired()],
                      render_kw={'class': 'form-control', 'placeholder': 'Tu nombre completo'})
    job_title = StringField('Puesto/Cargo', validators=[Optional()],
                           render_kw={'class': 'form-control', 'placeholder': 'ej: CEO, Desarrollador, Diseñador'})
    company = StringField('Empresa', validators=[Optional()],
                         render_kw={'class': 'form-control', 'placeholder': 'Nombre de tu empresa'})
    phone = StringField('Teléfono', validators=[Optional()],
                       render_kw={'class': 'form-control', 'placeholder': '+34 123 456 789'})
    email_public = StringField('Email Público', validators=[Optional(), Email()],
                              render_kw={'class': 'form-control', 'placeholder': 'contacto@empresa.com'})
    website = StringField('Sitio Web', validators=[Optional(), flexible_url_validator],
                         render_kw={'class': 'form-control', 'placeholder': 'miempresa.com'})
    location = StringField('Ubicación', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': 'Madrid, España'})
    bio = TextAreaField('Biografía', validators=[Optional(), Length(max=500)],
                       render_kw={'class': 'form-control', 'rows': 4, 
                                 'placeholder': 'Breve descripción sobre ti o tu negocio...'})
    
    # Social media
    # Social media fields
    instagram = StringField('Instagram', validators=[Optional()],
                           render_kw={'class': 'form-control', 'placeholder': '@tuusuario'})
    
    whatsapp_country = SelectField('País WhatsApp', validators=[Optional()], 
                                  choices=[
                                      ('', 'Seleccionar país'),
                                      ('+1', '🇺🇸 Estados Unidos (+1)'),
                                      ('+1', '🇨🇦 Canadá (+1)'),
                                      ('+34', '🇪🇸 España (+34)'),
                                      ('+52', '🇲🇽 México (+52)'),
                                      ('+54', '🇦🇷 Argentina (+54)'),
                                      ('+55', '🇧🇷 Brasil (+55)'),
                                      ('+56', '🇨🇱 Chile (+56)'),
                                      ('+57', '🇨🇴 Colombia (+57)'),
                                      ('+58', '🇻🇪 Venezuela (+58)'),
                                      ('+51', '🇵🇪 Perú (+51)'),
                                      ('+593', '🇪🇨 Ecuador (+593)'),
                                      ('+33', '🇫🇷 Francia (+33)'),
                                      ('+49', '🇩🇪 Alemania (+49)'),
                                      ('+39', '🇮🇹 Italia (+39)'),
                                      ('+44', '🇬🇧 Reino Unido (+44)'),
                                      ('+351', '🇵🇹 Portugal (+351)'),
                                      ('+41', '🇨🇭 Suiza (+41)'),
                                      ('+31', '🇳🇱 Países Bajos (+31)'),
                                      ('+32', '🇧🇪 Bélgica (+32)')
                                  ],
                                  render_kw={'class': 'form-select'})
    whatsapp = StringField('Número WhatsApp', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': '123 456 789 (sin código de país)'})
    facebook = StringField('Facebook', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': 'https://facebook.com/tuperfil'})
    linkedin = StringField('LinkedIn', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/tuperfil'})
    twitter = StringField('Twitter/X', validators=[Optional()],
                         render_kw={'class': 'form-control', 'placeholder': '@tuusuario'})
    youtube = StringField('YouTube', validators=[Optional()],
                         render_kw={'class': 'form-control', 'placeholder': 'https://youtube.com/@tucanal'})
    tiktok = StringField('TikTok', validators=[Optional()],
                        render_kw={'class': 'form-control', 'placeholder': '@tuusuario'})
    telegram = StringField('Telegram', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': '@tuusuario'})
    snapchat = StringField('Snapchat', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': '@tuusuario'})
    pinterest = StringField('Pinterest', validators=[Optional()],
                           render_kw={'class': 'form-control', 'placeholder': 'https://pinterest.com/tuperfil'})
    github = StringField('GitHub', validators=[Optional()],
                        render_kw={'class': 'form-control', 'placeholder': '@tuusuario'})
    behance = StringField('Behance', validators=[Optional()],
                         render_kw={'class': 'form-control', 'placeholder': 'https://behance.net/tuperfil'})
    dribbble = StringField('Dribbble', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': 'https://dribbble.com/tuperfil'})
    
    theme_id = SelectField('Tema', coerce=int, validators=[DataRequired()],
                          render_kw={'class': 'form-select'})
    is_public = BooleanField('Tarjeta Pública', default=True,
                            render_kw={'class': 'form-check-input'})
    
    submit = SubmitField('Guardar Tarjeta', render_kw={'class': 'btn btn-primary'})
    
    def __init__(self, *args, **kwargs):
        super(CardForm, self).__init__(*args, **kwargs)
        self.theme_id.choices = [(t.id, t.name) for t in Theme.query.all()]

class ServiceForm(FlaskForm):
    title = StringField('Título del Servicio', validators=[DataRequired()],
                       render_kw={'class': 'form-control', 'placeholder': 'ej: Corte de Cabello'})
    description = TextAreaField('Descripción', validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 3,
                                         'placeholder': 'Describe tu servicio...'})
    category = SelectField('Categoría', validators=[Optional()],
                          choices=[
                              ('', 'Sin categoría'),
                              ('belleza', 'Belleza y Estética'),
                              ('salud', 'Salud y Bienestar'),
                              ('tecnologia', 'Tecnología'),
                              ('educacion', 'Educación'),
                              ('consultoria', 'Consultoría'),
                              ('diseño', 'Diseño'),
                              ('fotografia', 'Fotografía'),
                              ('eventos', 'Eventos'),
                              ('hogar', 'Hogar y Mantenimiento'),
                              ('otros', 'Otros')
                          ],
                          render_kw={'class': 'form-select'})
    price_from = DecimalField('Precio Desde', validators=[Optional(), NumberRange(min=0)],
                             render_kw={'class': 'form-control', 'placeholder': '25000', 'step': '1'})
    duration_minutes = StringField('Duración', validators=[Optional()],
                                  render_kw={'class': 'form-control', 'placeholder': 'ej: 30min, 1h, 2h 30min'})
    availability = StringField('Disponibilidad', validators=[Optional()],
                              render_kw={'class': 'form-control', 'placeholder': 'ej: Lun-Vie 9am-6pm'})
    icon = StringField('Icono', validators=[Optional()],
                      render_kw={'class': 'form-control', 'placeholder': 'fa-cut (Font Awesome)'})
    image = FileField('Imagen del Servicio', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Solo se permiten imágenes (JPG, PNG, WEBP)')
    ], render_kw={'class': 'form-control', 'accept': 'image/*'})
    is_featured = BooleanField('Servicio Destacado', default=False,
                              render_kw={'class': 'form-check-input'})
    is_visible = BooleanField('Visible', default=True,
                             render_kw={'class': 'form-check-input'})
    
    submit = SubmitField('Guardar Servicio', render_kw={'class': 'btn btn-primary'})

class GalleryUploadForm(FlaskForm):
    image = FileField('Imagen', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Solo se permiten imágenes (JPG, PNG, WEBP)')
    ], render_kw={'class': 'form-control', 'accept': 'image/*'})
    caption = StringField('Descripción', validators=[Optional()],
                         render_kw={'class': 'form-control', 'placeholder': 'Descripción de la imagen (opcional)'})
    
    submit = SubmitField('Subir Imagen', render_kw={'class': 'btn btn-success'})

class AvatarUploadForm(FlaskForm):
    avatar = FileField('Avatar', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Solo se permiten imágenes (JPG, PNG, WEBP)')
    ], render_kw={'class': 'form-control', 'accept': 'image/*'})
    
    submit = SubmitField('Cambiar Avatar', render_kw={'class': 'btn btn-primary'})

class ThemeCustomizationForm(FlaskForm):
    primary_color = StringField('Color Primario', validators=[DataRequired()],
                               render_kw={'type': 'color', 'class': 'form-control form-control-color'})
    secondary_color = StringField('Color Secundario', validators=[DataRequired()],
                                 render_kw={'type': 'color', 'class': 'form-control form-control-color'})
    accent_color = StringField('Color de Acento', validators=[DataRequired()],
                              render_kw={'type': 'color', 'class': 'form-control form-control-color'})
    font_family = SelectField('Tipografía', validators=[DataRequired()],
                             choices=FONT_FAMILY_CHOICES,
                             render_kw={'class': 'form-select'})
    layout = SelectField('Diseño', validators=[DataRequired()],
                        choices=LAYOUT_CHOICES,
                        render_kw={'class': 'form-select'})
    avatar_shape = SelectField('Forma del Avatar', validators=[DataRequired()],
                              choices=AVATAR_SHAPE_CHOICES,
                              render_kw={'class': 'form-select'})
    
    submit = SubmitField('Actualizar Tema', render_kw={'class': 'btn btn-success'})

class ProductForm(FlaskForm):
    name = StringField('Nombre del Producto', validators=[DataRequired()],
                      render_kw={'class': 'form-control', 'placeholder': 'ej: Zapatos Deportivos Nike'})
    description = TextAreaField('Descripción', validators=[Optional()],
                               render_kw={'class': 'form-control', 'rows': 3,
                                         'placeholder': 'Describe tu producto...'})
    category = SelectField('Categoría', validators=[Optional()],
                          choices=[
                              ('', 'Sin categoría'),
                              ('ropa', 'Ropa y Accesorios'),
                              ('tecnologia', 'Tecnología'),
                              ('hogar', 'Hogar y Decoración'),
                              ('deportes', 'Deportes y Fitness'),
                              ('belleza', 'Belleza y Cuidado Personal'),
                              ('libros', 'Libros y Papelería'),
                              ('juguetes', 'Juguetes y Juegos'),
                              ('alimentacion', 'Alimentación'),
                              ('arte', 'Arte y Manualidades'),
                              ('electronica', 'Electrónica'),
                              ('otros', 'Otros')
                          ],
                          render_kw={'class': 'form-select'})
    brand = StringField('Marca', validators=[Optional()],
                       render_kw={'class': 'form-control', 'placeholder': 'ej: Nike, Apple, Samsung'})
    price = DecimalField('Precio', validators=[Optional(), NumberRange(min=0)],
                        render_kw={'class': 'form-control', 'placeholder': '50000', 'step': '1'})
    original_price = DecimalField('Precio Original (opcional)', validators=[Optional(), NumberRange(min=0)],
                                 render_kw={'class': 'form-control', 'placeholder': '70000', 'step': '1'})
    sku = StringField('Código/SKU', validators=[Optional()],
                     render_kw={'class': 'form-control', 'placeholder': 'ej: PROD-001'})
    stock_quantity = DecimalField('Cantidad en Stock', validators=[Optional(), NumberRange(min=-1)],
                                 render_kw={'class': 'form-control', 'placeholder': '10 (-1 para ilimitado)'})
    external_link = StringField('Enlace Externo', validators=[Optional(), URL()],
                               render_kw={'class': 'form-control', 'placeholder': 'https://tienda.com/producto'})
    image = FileField('Imagen del Producto', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Solo se permiten imágenes JPG, PNG y WEBP.')
    ])
    is_visible = BooleanField('Visible en tarjeta pública', 
                             render_kw={'class': 'form-check-input'})
    is_featured = BooleanField('Producto destacado',
                              render_kw={'class': 'form-check-input'})
    is_available = BooleanField('Disponible para venta',
                               render_kw={'class': 'form-check-input'})
    
    submit = SubmitField('Guardar Producto', render_kw={'class': 'btn btn-success'})