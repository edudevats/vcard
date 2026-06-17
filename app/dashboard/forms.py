from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, DecimalField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, URL, NumberRange, Length, ValidationError, EqualTo
import re
from ..models import Theme, Category
from ..constants import FONT_FAMILY_CHOICES, LAYOUT_CHOICES, AVATAR_SHAPE_CHOICES
from flask_login import current_user

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
                       render_kw={'class': 'form-control', 'placeholder': '+52 12 3456 7890'})
    email_public = StringField('Email Público', validators=[Optional(), Email()],
                              render_kw={'class': 'form-control', 'placeholder': 'contacto@empresa.com'})
    website = StringField('Sitio Web', validators=[Optional(), flexible_url_validator],
                         render_kw={'class': 'form-control', 'placeholder': 'miempresa.com'})
    location = StringField('Ubicación', validators=[Optional()],
                          render_kw={'class': 'form-control', 'placeholder': 'CDMX, México'})
    bio = TextAreaField('Biografía', validators=[Optional(), Length(max=500)],
                       render_kw={'class': 'form-control', 'rows': 4, 
                                 'placeholder': 'Una breve descripción sobre ti o tu negocio...'})
    
    # Social media
    # Social media fields
    instagram = StringField('Instagram', validators=[Optional()],
                           render_kw={'class': 'form-control', 'placeholder': '@usuario'})
    
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
                          render_kw={'class': 'form-control', 'placeholder': '12 3456 7890 (sin código de país)'})
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
                          render_kw={'class': 'form-select'})
    new_category = StringField('Nueva Categoría', validators=[Optional()],
                              render_kw={'class': 'form-control', 'placeholder': 'Escribe una nueva categoría...'})
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
    accepts_appointments = BooleanField('Aceptar reservas de citas', default=False,
                                       render_kw={'class': 'form-check-input'})

    submit = SubmitField('Guardar Servicio', render_kw={'class': 'btn btn-primary'})
    
    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        # Load user's service categories
        choices = [('', 'Sin categoría')]
        
        try:
            if current_user and current_user.is_authenticated:
                user_categories = Category.query.filter_by(
                    user_id=current_user.id, 
                    type='service',
                    is_active=True
                ).order_by(Category.name).all()
                
                for cat in user_categories:
                    choices.append((cat.name, cat.name))
        except Exception:
            # In case there's an issue with current_user context, just continue
            pass
        
        # Add default categories as fallback
        default_categories = [
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
        ]
        
        # Add defaults that aren't already in user categories
        existing_values = [choice[0] for choice in choices]
        for value, label in default_categories:
            if value not in existing_values:
                choices.append((value, label))
        
        self.category.choices = choices

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
    avatar_border_color = StringField('Color del Borde del Avatar', validators=[DataRequired()],
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
                          render_kw={'class': 'form-select'})
    new_category = StringField('Nueva Categoría', validators=[Optional()],
                              render_kw={'class': 'form-control', 'placeholder': 'Escribe una nueva categoría...'})
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
    is_visible = BooleanField('Visible en tarjeta pública', default=True,
                             render_kw={'class': 'form-check-input'})
    is_featured = BooleanField('Producto destacado',
                              render_kw={'class': 'form-check-input'})
    is_available = BooleanField('Disponible para venta', default=True,
                               render_kw={'class': 'form-check-input'})
    
    submit = SubmitField('Guardar Producto', render_kw={'class': 'btn btn-success'})
    
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Load user's product categories
        choices = [('', 'Sin categoría')]
        
        try:
            if current_user and current_user.is_authenticated:
                user_categories = Category.query.filter_by(
                    user_id=current_user.id, 
                    type='product',
                    is_active=True
                ).order_by(Category.name).all()
                
                for cat in user_categories:
                    choices.append((cat.name, cat.name))
        except Exception:
            # In case there's an issue with current_user context, just continue
            pass
        
        # Add default categories as fallback
        default_categories = [
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
        ]
        
        # Add defaults that aren't already in user categories
        existing_values = [choice[0] for choice in choices]
        for value, label in default_categories:
            if value not in existing_values:
                choices.append((value, label))
        
        self.category.choices = choices

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña Actual', validators=[DataRequired()],
                                   render_kw={'class': 'form-control'})
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)],
                               render_kw={'class': 'form-control'})
    confirm_password = PasswordField('Confirmar Nueva Contraseña',
                                   validators=[DataRequired(), EqualTo('new_password', 'Las contraseñas no coinciden')],
                                   render_kw={'class': 'form-control'})
    submit = SubmitField('Cambiar Contraseña', render_kw={'class': 'btn btn-primary'})

# Formularios para Sistema de Turnos
class TicketSystemForm(FlaskForm):
    """Formulario de configuración del sistema de turnos"""
    business_name = StringField('Nombre del Consultorio/Negocio', validators=[DataRequired()],
                               render_kw={'class': 'form-control', 'placeholder': 'ej: Consultorio Médico Dr. García'})
    welcome_message = TextAreaField('Mensaje de Bienvenida', validators=[Optional(), Length(max=500)],
                                   render_kw={'class': 'form-control', 'rows': 3,
                                             'placeholder': 'Mensaje que verán los pacientes al tomar turno...'})
    business_hours = StringField('Horario de Atención', validators=[Optional()],
                                render_kw={'class': 'form-control', 'placeholder': 'ej: Lun-Vie 9:00 - 18:00'})
    display_mode = SelectField('Modo de Visualización', validators=[DataRequired()],
                              choices=[
                                  ('simple', 'Simple - Solo números de turno'),
                                  ('detailed', 'Detallado - Con nombres y tiempos')
                              ],
                              render_kw={'class': 'form-select'})

    # Configuración de pausa
    pause_message = TextAreaField('Mensaje de Pausa', validators=[Optional(), Length(max=500)],
                                 render_kw={'class': 'form-control', 'rows': 2,
                                           'placeholder': 'Mensaje cuando no se aceptan turnos (ej: Regresamos a las 14:00)'})
    resume_time = StringField('Hora de Reanudación', validators=[Optional()],
                             render_kw={'class': 'form-control', 'placeholder': 'ej: 14:00 o Mañana a las 9:00'})

    # Configuración de teléfono
    phone_country_prefix = StringField('Prefijo Telefónico por Defecto', validators=[DataRequired()],
                                      render_kw={'class': 'form-control', 'placeholder': '+52'})

    # Configuración de campos del formulario
    require_patient_email = BooleanField('Email Obligatorio',
                                        render_kw={'class': 'form-check-input'})
    collect_patient_birthdate = BooleanField('Recolectar Fecha de Nacimiento',
                                            render_kw={'class': 'form-check-input'})

    submit = SubmitField('Guardar Configuración', render_kw={'class': 'btn btn-primary'})

class TicketTypeForm(FlaskForm):
    """Formulario para crear/editar tipos de citas"""
    name = StringField('Nombre del Tipo de Cita', validators=[DataRequired(), Length(max=100)],
                      render_kw={'class': 'form-control', 'placeholder': 'ej: Consulta General, Inyecciones, etc.'})
    description = StringField('Descripción', validators=[Optional(), Length(max=500)],
                             render_kw={'class': 'form-control', 'placeholder': 'Descripción breve del servicio'})
    color = StringField('Color de Identificación', validators=[DataRequired()],
                       render_kw={'type': 'color', 'class': 'form-control form-control-color'})
    estimated_duration = SelectField('Duración Estimada', validators=[DataRequired()], coerce=int,
                                    choices=[
                                        (15, '15 minutos'),
                                        (30, '30 minutos'),
                                        (45, '45 minutos'),
                                        (60, '1 hora'),
                                        (90, '1 hora 30 min'),
                                        (120, '2 horas')
                                    ],
                                    render_kw={'class': 'form-select'})
    prefix = StringField('Prefijo para Tickets', validators=[DataRequired(), Length(min=1, max=5)],
                        render_kw={'class': 'form-control', 'placeholder': 'ej: A, B, C, CON, INY',
                                  'maxlength': '5', 'style': 'text-transform: uppercase;'})
    is_active = BooleanField('Activo', default=True,
                            render_kw={'class': 'form-check-input'})
    submit = SubmitField('Guardar Tipo de Cita', render_kw={'class': 'btn btn-primary'})

class TakeTicketForm(FlaskForm):
    """Formulario público para que pacientes tomen turnos"""
    ticket_type_id = SelectField('Tipo de Cita', validators=[DataRequired()], coerce=int,
                                     render_kw={'class': 'form-select'})
    patient_name = StringField('Nombre Completo', validators=[DataRequired(), Length(max=200)],
                              render_kw={'class': 'form-control', 'placeholder': 'Tu nombre completo'})
    patient_phone_country = StringField('Prefijo', validators=[DataRequired()],
                                       render_kw={'class': 'form-control', 'placeholder': '+52', 'style': 'width: 80px;'})
    patient_phone = StringField('Teléfono', validators=[DataRequired(), Length(max=20)],
                               render_kw={'class': 'form-control', 'placeholder': '1234567890'})
    patient_email = StringField('Email', validators=[Optional(), Email()],
                               render_kw={'class': 'form-control', 'placeholder': 'tu@email.com'})
    patient_birthdate = StringField('Fecha de Nacimiento', validators=[Optional()],
                                   render_kw={'type': 'date', 'class': 'form-control'})
    submit = SubmitField('Tomar Turno', render_kw={'class': 'btn btn-success btn-lg w-100'})

    def __init__(self, ticket_types=None, phone_prefix='+52', require_email=False, collect_birthdate=False, *args, **kwargs):
        super(TakeTicketForm, self).__init__(*args, **kwargs)
        if ticket_types:
            self.ticket_type_id.choices = [(t.id, t.name) for t in ticket_types]

        # Configurar validadores dinámicamente
        if require_email:
            self.patient_email.validators = [DataRequired(), Email()]
            self.patient_email.label.text = 'Email'
        else:
            self.patient_email.validators = [Optional(), Email()]
            self.patient_email.label.text = 'Email (opcional)'

        # Ocultar fecha de nacimiento si no se solicita
        if not collect_birthdate:
            self.patient_birthdate.validators = []

        # Establecer prefijo por defecto
        if not self.patient_phone_country.data:
            self.patient_phone_country.data = phone_prefix

class AppointmentBookingForm(FlaskForm):
    """Formulario público para que clientes reserven citas para servicios"""
    customer_name = StringField('Nombre Completo', validators=[DataRequired(), Length(max=200)],
                               render_kw={'class': 'form-control', 'placeholder': 'Tu nombre completo'})
    customer_phone_country = SelectField('País', validators=[DataRequired()],
                                        choices=[
                                            ('', 'Seleccionar'),
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
                                        ],
                                        render_kw={'class': 'form-select'})
    customer_phone = StringField('Número de Teléfono', validators=[DataRequired(), Length(max=20)],
                                render_kw={'class': 'form-control', 'placeholder': '1234567890'})
    customer_address = TextAreaField('Dirección', validators=[Optional()],
                                    render_kw={'class': 'form-control', 'rows': 2,
                                              'placeholder': 'Tu dirección completa'})
    appointment_date = StringField('Fecha de la Cita', validators=[DataRequired()],
                                  render_kw={'type': 'date', 'class': 'form-control'})
    appointment_time = SelectField('Hora de la Cita', validators=[DataRequired()],
                                  choices=[
                                      ('', 'Seleccionar hora'),
                                      ('08:00', '8:00 AM'), ('08:30', '8:30 AM'),
                                      ('09:00', '9:00 AM'), ('09:30', '9:30 AM'),
                                      ('10:00', '10:00 AM'), ('10:30', '10:30 AM'),
                                      ('11:00', '11:00 AM'), ('11:30', '11:30 AM'),
                                      ('12:00', '12:00 PM'), ('12:30', '12:30 PM'),
                                      ('13:00', '1:00 PM'), ('13:30', '1:30 PM'),
                                      ('14:00', '2:00 PM'), ('14:30', '2:30 PM'),
                                      ('15:00', '3:00 PM'), ('15:30', '3:30 PM'),
                                      ('16:00', '4:00 PM'), ('16:30', '4:30 PM'),
                                      ('17:00', '5:00 PM'), ('17:30', '5:30 PM'),
                                      ('18:00', '6:00 PM'), ('18:30', '6:30 PM'),
                                      ('19:00', '7:00 PM'), ('19:30', '7:30 PM'),
                                      ('20:00', '8:00 PM'), ('20:30', '8:30 PM'),
                                  ],
                                  render_kw={'class': 'form-select'})
    notes = TextAreaField('Notas adicionales (opcional)', validators=[Optional()],
                         render_kw={'class': 'form-control', 'rows': 3,
                                   'placeholder': 'Información adicional sobre tu cita...'})
    submit = SubmitField('Reservar Cita', render_kw={'class': 'btn btn-success btn-lg w-100'})

    def __init__(self, phone_prefix='+52', require_address=False, *args, **kwargs):
        super(AppointmentBookingForm, self).__init__(*args, **kwargs)

        # Configurar validadores dinámicamente
        if require_address:
            self.customer_address.validators = [DataRequired()]
            self.customer_address.label.text = 'Dirección'
        else:
            self.customer_address.validators = [Optional()]
            self.customer_address.label.text = 'Dirección (opcional)'

        # Establecer prefijo por defecto
        if not self.customer_phone_country.data:
            self.customer_phone_country.data = phone_prefix