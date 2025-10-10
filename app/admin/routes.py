from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from ..models import User, Card, Theme, CardView
from .. import db
from . import bp
from .forms import UserForm, NewUserForm, ThemeForm
from ..utils import admin_required
from datetime import datetime

@bp.route('/')
@login_required
@admin_required
def index():
    total_users = User.query.count()
    approved_users = User.query.filter_by(is_approved=True).count()
    pending_users = User.query.filter_by(is_approved=False, is_suspended=False).count()
    suspended_users = User.query.filter_by(is_suspended=True).count()
    total_cards = Card.query.count()
    public_cards = Card.query.filter_by(is_public=True).count()
    private_cards = total_cards - public_cards
    total_views = CardView.query.count()
    
    stats = {
        'total_users': total_users,
        'approved_users': approved_users,
        'pending_users': pending_users,
        'suspended_users': suspended_users,
        'total_cards': total_cards,
        'public_cards': public_cards,
        'private_cards': private_cards,
        'total_views': total_views
    }
    
    return render_template('admin/index.html', stats=stats)

@bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query
    if search:
        query = query.filter(User.email.contains(search))
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            is_active=form.is_active.data,
            max_cards=form.max_cards.data
        )
        user.set_email(form.email.data)  # Normalize email
        password = form.password.data
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'¡Usuario {user.email} creado exitosamente! Contraseña: {password}', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, title='Nuevo Usuario')

@bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
    form = UserForm(original_email=user.email, obj=user)
    if form.validate_on_submit():
        user.set_email(form.email.data)  # Normalize email
        user.role = form.role.data
        user.is_active = form.is_active.data
        user.max_cards = form.max_cards.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash(f'¡Usuario {user.email} actualizado exitosamente!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, user=user, title='Editar Usuario')

@bp.route('/users/<int:id>/cards')
@login_required
@admin_required
def user_cards(id):
    user = User.query.get_or_404(id)
    cards = user.cards.order_by(Card.created_at.desc()).all()
    
    return render_template('admin/user_cards.html', user=user, cards=cards)

@bp.route('/themes')
@login_required
@admin_required
def themes():
    themes = Theme.query.order_by(Theme.created_at.desc()).all()
    return render_template('admin/themes.html', themes=themes)

@bp.route('/themes/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_theme():
    form = ThemeForm()
    if form.validate_on_submit():
        theme = Theme(
            name=form.name.data,
            template_name=form.template_name.data,
            primary_color=form.primary_color.data,
            secondary_color=form.secondary_color.data,
            accent_color=form.accent_color.data,
            avatar_border_color=form.avatar_border_color.data,
            font_family=form.font_family.data,
            layout=form.layout.data,
            avatar_shape=form.avatar_shape.data,
            is_global=True,  # Admin themes are global
            created_by_id=None  # Admin themes don't have owner
        )
        
        db.session.add(theme)
        db.session.commit()
        
        flash(f'¡Tema "{theme.name}" creado exitosamente!', 'success')
        return redirect(url_for('admin.themes'))
    
    return render_template('admin/theme_form.html', form=form, title='Nuevo Tema')

@bp.route('/themes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_theme(id):
    theme = Theme.query.get_or_404(id)
    
    form = ThemeForm(obj=theme)
    if form.validate_on_submit():
        theme.name = form.name.data
        theme.template_name = form.template_name.data
        theme.primary_color = form.primary_color.data
        theme.secondary_color = form.secondary_color.data
        theme.accent_color = form.accent_color.data
        theme.avatar_border_color = form.avatar_border_color.data
        theme.font_family = form.font_family.data
        theme.layout = form.layout.data
        theme.avatar_shape = form.avatar_shape.data
        
        db.session.commit()
        flash(f'¡Tema "{theme.name}" actualizado exitosamente!', 'success')
        return redirect(url_for('admin.themes'))
    
    return render_template('admin/theme_form.html', form=form, theme=theme, title='Editar Tema')

@bp.route('/themes/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_theme(id):
    theme = Theme.query.get_or_404(id)
    
    if theme.cards.count() > 0:
        flash('No se puede eliminar un tema que está siendo usado por tarjetas.', 'error')
        return redirect(url_for('admin.themes'))
    
    db.session.delete(theme)
    db.session.commit()
    
    flash(f'Tema "{theme.name}" eliminado exitosamente.', 'success')
    return redirect(url_for('admin.themes'))

@bp.route('/cards')
@login_required
@admin_required
def cards():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = Card.query
    
    if search:
        query = query.filter(
            db.or_(
                Card.name.contains(search),
                Card.email_public.contains(search),
                Card.slug.contains(search)
            )
        )
    
    if status == 'public':
        query = query.filter_by(is_public=True)
    elif status == 'private':
        query = query.filter_by(is_public=False)
    
    cards = query.order_by(Card.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/cards.html', cards=cards, search=search, status=status)

@bp.route('/cards/<int:id>/views')
@login_required
@admin_required
def card_views(id):
    card = Card.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    views = card.views.order_by(CardView.viewed_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    stats = {
        'total_views': card.get_total_views(),
        'unique_views': card.get_unique_views(),
        'views_today': card.get_views_today(),
        'views_this_month': card.get_views_this_month()
    }
    
    return render_template('admin/card_views.html', card=card, views=views, stats=stats)

# User management routes
@bp.route('/users/<int:id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend_user(id):
    """Suspend a user and all their cards"""
    user = User.query.get_or_404(id)
    
    if user.is_admin():
        flash('No se puede suspender a un administrador', 'error')
        return redirect(url_for('admin.users'))
    
    reason = request.form.get('reason', 'Suspendido por el administrador')
    user.suspend(reason, current_user)
    
    db.session.commit()
    flash(f'Usuario {user.email} suspendido correctamente', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/unsuspend', methods=['POST'])
@login_required
@admin_required
def unsuspend_user(id):
    """Remove user suspension"""
    user = User.query.get_or_404(id)
    
    user.unsuspend()
    db.session.commit()
    flash(f'Suspensión removida para {user.email}', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/update-limits', methods=['POST'])
@login_required
@admin_required
def update_user_limits(id):
    """Update user limits"""
    user = User.query.get_or_404(id)
    
    try:
        max_cards = int(request.form.get('max_cards', 1))
        user.max_cards = max_cards
        db.session.commit()
        flash(f'Límites actualizados para {user.email}', 'success')
    except ValueError:
        flash('Límite de tarjetas debe ser un número válido', 'error')
    
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(id):
    """Reset user password"""
    user = User.query.get_or_404(id)
    
    new_password = request.form.get('new_password')
    if new_password and len(new_password) >= 6:
        user.set_password(new_password)
        db.session.commit()
        flash(f'Contraseña restablecida para {user.email}', 'success')
    else:
        flash('La contraseña debe tener al menos 6 caracteres', 'error')
    
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
    """Toggle user active status"""
    user = User.query.get_or_404(id)
    
    if user.is_admin():
        flash('No se puede desactivar a un administrador', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    if not user.is_active:
        # Deactivate all cards when user is deactivated
        for card in user.cards:
            card.is_public = False
    
    db.session.commit()
    status = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {user.email} {status}', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/pending-approvals')
@login_required
@admin_required
def pending_approvals():
    """Show pending user approval requests"""
    pending_users = User.query.filter_by(is_approved=False, is_suspended=False).order_by(User.created_at.desc()).all()
    
    # Calculate days waiting for each user
    from ..timezone_utils import now_local
    today = now_local().date()
    for user in pending_users:
        if user.created_at:
            user.days_waiting = (today - user.created_at.date()).days
        else:
            user.days_waiting = 0
    
    return render_template('admin/pending_approvals.html', pending_users=pending_users)

@bp.route('/approve-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Approve a user registration"""
    from flask_login import current_user
    
    user = User.query.get_or_404(user_id)
    if user.is_approved:
        flash(f'El usuario {user.email} ya está aprobado', 'warning')
        return redirect(url_for('admin.pending_approvals'))
    
    user.approve(current_user)
    db.session.commit()
    
    flash(f'Usuario {user.email} aprobado exitosamente. El usuario ya puede iniciar sesión.', 'success')
    return redirect(url_for('admin.pending_approvals'))

@bp.route('/reject-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    """Reject and delete a user registration"""
    user = User.query.get_or_404(user_id)
    if user.is_approved:
        flash(f'No se puede rechazar al usuario {user.email} porque ya está aprobado', 'error')
        return redirect(url_for('admin.pending_approvals'))

    user_email = user.email
    db.session.delete(user)
    db.session.commit()

    flash(f'Solicitud de registro de {user_email} rechazada y eliminada', 'success')
    return redirect(url_for('admin.pending_approvals'))

# ============================================================================
# SISTEMA DE TICKETS - Administración
# ============================================================================

@bp.route('/users/<int:id>/toggle-tickets', methods=['POST'])
@login_required
@admin_required
def toggle_tickets(id):
    """Activar/desactivar sistema de turnos para un usuario"""
    from ..models import TicketSystem

    user = User.query.get_or_404(id)

    # Verificar si el usuario ya tiene un sistema de turnos
    if not user.ticket_system:
        # Crear nuevo sistema de turnos
        ticket_system = TicketSystem(
            user_id=user.id,
            is_enabled=True,
            business_name=f"Consultorio de {user.email}",
            max_ticket_types=10,
            display_mode='simple'
        )
        db.session.add(ticket_system)
        db.session.commit()
        flash(f'Sistema de turnos activado para {user.email}', 'success')
    else:
        # Toggle del estado
        user.ticket_system.is_enabled = not user.ticket_system.is_enabled
        db.session.commit()
        status = 'activado' if user.ticket_system.is_enabled else 'desactivado'
        flash(f'Sistema de turnos {status} para {user.email}', 'success')

    return redirect(url_for('admin.edit_user', id=user.id))