from flask import current_app, render_template
from flask_mail import Message
from . import mail
from threading import Thread


def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    """Send email with template"""
    msg = Message(
        subject=f"[{current_app.config['APP_NAME']}] {subject}",
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to]
    )
    
    msg.body = render_template(f'emails/{template}.txt', **kwargs)
    msg.html = render_template(f'emails/{template}.html', **kwargs)
    
    # Send asynchronously
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_password_reset_email(user):
    """Send password reset email"""
    token = user.generate_reset_token()
    send_email(
        user.email,
        'Restablecer Contraseña',
        'reset_password',
        user=user,
        token=token
    )


def send_welcome_email(user):
    """Send welcome email after registration"""
    send_email(
        user.email,
        'Bienvenido a ATScard',
        'welcome',
        user=user
    )


def send_email_verification(user, token):
    """Send email verification"""
    send_email(
        user.email,
        'Verificar Email',
        'verify_email',
        user=user,
        token=token
    )