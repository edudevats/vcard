from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, NumberRange, Optional, EqualTo, ValidationError
from ..models import User
from ..constants import FONT_FAMILY_CHOICES, LAYOUT_CHOICES, AVATAR_SHAPE_CHOICES
from ..utils import validate_email_unique

class UserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],
                       render_kw={'class': 'form-control'})
    password = PasswordField('Contraseña', validators=[Optional()],
                           render_kw={'class': 'form-control', 'placeholder': 'Dejar vacío para no cambiar'})
    password2 = PasswordField('Confirmar Contraseña', 
                             validators=[Optional(), EqualTo('password')],
                             render_kw={'class': 'form-control'})
    role = SelectField('Rol', validators=[DataRequired()],
                      choices=[('user', 'Usuario'), ('admin', 'Administrador')],
                      render_kw={'class': 'form-select'})
    is_active = BooleanField('Activo', render_kw={'class': 'form-check-input'})
    max_cards = IntegerField('Máximo de Tarjetas', validators=[DataRequired(), NumberRange(min=1, max=50)],
                            render_kw={'class': 'form-control'})
    
    submit = SubmitField('Guardar Usuario', render_kw={'class': 'btn btn-primary'})
    
    def __init__(self, original_email=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            if not validate_email_unique(email.data):
                raise ValidationError('Ya existe un usuario con este email.')

class NewUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],
                       render_kw={'class': 'form-control'})
    password = PasswordField('Contraseña', validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    password2 = PasswordField('Confirmar Contraseña', 
                             validators=[DataRequired(), EqualTo('password')],
                             render_kw={'class': 'form-control'})
    role = SelectField('Rol', validators=[DataRequired()],
                      choices=[('user', 'Usuario'), ('admin', 'Administrador')],
                      render_kw={'class': 'form-select'})
    is_active = BooleanField('Activo', default=True, render_kw={'class': 'form-check-input'})
    max_cards = IntegerField('Máximo de Tarjetas', validators=[DataRequired(), NumberRange(min=1, max=50)], default=1,
                            render_kw={'class': 'form-control'})
    
    submit = SubmitField('Crear Usuario', render_kw={'class': 'btn btn-success'})

    def validate_email(self, email):
        if not validate_email_unique(email.data):
            raise ValidationError('Ya existe un usuario con este email.')

class ThemeForm(FlaskForm):
    name = StringField('Nombre del Tema', validators=[DataRequired()],
                      render_kw={'class': 'form-control'})
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
    
    submit = SubmitField('Guardar Tema', render_kw={'class': 'btn btn-primary'})