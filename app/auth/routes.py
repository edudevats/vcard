from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from ..models import User
from .. import db
from . import bp
from .forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm
from ..email_utils import send_password_reset_email

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    login_form = LoginForm()
    register_form = RegistrationForm()
    
    if request.method == 'POST':
        # Check which form was submitted using the hidden field
        form_type = request.form.get('form_type')
        
        # Handle login form
        if form_type == 'login' and login_form.validate_on_submit():
            user = User.query.filter_by(email=login_form.email.data).first()
            if user is None or not user.check_password(login_form.password.data):
                flash('Email o contraseña inválidos', 'error')
                return redirect(url_for('auth.login'))
            
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('auth.login'))
            
            if user.is_suspended:
                reason = user.suspension_reason if user.suspension_reason else "Sin motivo especificado"
                flash(f'Tu cuenta ha sido suspendida. Motivo: {reason}', 'error')
                return redirect(url_for('auth.login'))
            
            if not user.is_approved:
                flash('Tu cuenta aún no ha sido aprobada por el administrador. Recibirás una notificación cuando tu cuenta sea activada.', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=login_form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        
        # Handle registration form
        elif form_type == 'register' and register_form.validate_on_submit():
            user = User(email=register_form.email.data)
            user.set_password(register_form.password.data)
            user.is_approved = False  # Requiere aprobación del administrador
            db.session.add(user)
            db.session.commit()
            flash('¡Registro exitoso! Tu cuenta ha sido creada y está pendiente de aprobación por parte del administrador. Te notificaremos por email cuando tu cuenta sea activada.', 'info')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html', login_form=login_form, register_form=register_form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if not current_app.config['ALLOW_SIGNUP']:
        flash('El registro está deshabilitado. Contacta al administrador.', 'error')
        return redirect(url_for('auth.login'))
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        user.is_approved = False  # Requiere aprobación del administrador
        db.session.add(user)
        db.session.commit()
        flash('¡Registro exitoso! Tu cuenta ha sido creada y está pendiente de aprobación por parte del administrador. Te notificaremos por email cuando tu cuenta sea activada.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            db.session.commit()
        
        # Always show success message for security (don't reveal if email exists)
        flash('Se ha enviado un enlace de restablecimiento a tu email si la cuenta existe.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # Find user by token
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash('El enlace de restablecimiento es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash('Tu contraseña ha sido restablecida exitosamente.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

