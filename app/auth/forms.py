from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from ..models import User
from ..utils import validate_email_unique

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],
                       render_kw={'class': 'form-control', 'placeholder': 'tu@email.com'})
    password = PasswordField('Contraseña', validators=[DataRequired()],
                            render_kw={'class': 'form-control', 'placeholder': 'Tu contraseña'})
    remember_me = BooleanField('Recordarme', render_kw={'class': 'form-check-input'})
    submit = SubmitField('Iniciar Sesión', render_kw={'class': 'btn btn-primary btn-lg w-100', 'name': 'login_submit'})

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],
                       render_kw={'class': 'form-control', 'placeholder': 'tu@email.com'})
    password = PasswordField('Contraseña', validators=[DataRequired()],
                            render_kw={'class': 'form-control', 'placeholder': 'Mínimo 6 caracteres'})
    password2 = PasswordField('Confirmar Contraseña', 
                             validators=[DataRequired(), EqualTo('password')],
                             render_kw={'class': 'form-control', 'placeholder': 'Repite tu contraseña'})
    submit = SubmitField('Registrarse', render_kw={'class': 'btn btn-success btn-lg w-100', 'name': 'register_submit'})

    def validate_email(self, email):
        if not validate_email_unique(email.data):
            raise ValidationError('Ya existe una cuenta con este email. Usa otro email.')


class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],
                       render_kw={'class': 'form-control', 'placeholder': 'tu@email.com'})
    submit = SubmitField('Enviar Enlace de Restablecimiento', 
                        render_kw={'class': 'btn btn-primary btn-lg w-100'})


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired()],
                            render_kw={'class': 'form-control', 'placeholder': 'Mínimo 6 caracteres'})
    password2 = PasswordField('Confirmar Nueva Contraseña', 
                             validators=[DataRequired(), EqualTo('password')],
                             render_kw={'class': 'form-control', 'placeholder': 'Repite tu nueva contraseña'})
    submit = SubmitField('Restablecer Contraseña', render_kw={'class': 'btn btn-success btn-lg w-100'})