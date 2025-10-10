from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, make_response, abort
from flask_wtf.csrf import validate_csrf
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func
from ..models import Card, Service, Product, GalleryItem, Theme, CardView, Category, TicketSystem, TicketType, Ticket
from .. import db, cache
from . import bp
from .forms import CardForm, ServiceForm, ProductForm, GalleryUploadForm, AvatarUploadForm, ThemeCustomizationForm, ChangePasswordForm
from ..utils import save_image, save_avatar, delete_file, generate_styled_qr_code, generate_qr_code, generate_qr_code_with_logo, generate_qr_code_with_logo_themed, qr_to_base64, save_qr_code, admin_required, get_user_card_or_404, cleanup_files

def handle_category_creation(form, category_type):
    """
    Handle creation of new category if needed.
    Returns the category name to use.
    """
    # If user entered a new category, use that
    if form.new_category.data and form.new_category.data.strip():
        category_name = form.new_category.data.strip()
        
        # Create or get the category for this user
        Category.get_or_create(
            user_id=current_user.id,
            name=category_name,
            category_type=category_type
        )
        
        return category_name
    
    # Otherwise use the selected category
    return form.category.data if form.category.data else None
from ..analytics import AnalyticsService, get_analytics_summary
from ..cache_utils import CacheManager
from ..timezone_utils import now_utc_for_db, get_date_range_utc, format_local_datetime, now_local, today_start_utc
from datetime import datetime, timedelta
import os
import io
import re


def parse_duration_to_minutes(duration_str):
    """Convert duration string like '30min', '1h', '2h 30min' to minutes"""
    if not duration_str:
        return None
    
    duration_str = duration_str.lower().strip()
    total_minutes = 0
    
    # Match hours
    hours_match = re.search(r'(\d+)h', duration_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60
    
    # Match minutes
    minutes_match = re.search(r'(\d+)min', duration_str)
    if minutes_match:
        total_minutes += int(minutes_match.group(1))
    
    # If only numbers, assume minutes
    if not hours_match and not minutes_match:
        numbers = re.search(r'(\d+)', duration_str)
        if numbers:
            total_minutes = int(numbers.group(1))
    
    return total_minutes if total_minutes > 0 else None

@bp.route('/')
@login_required
def index():
    cards = current_user.cards.all()

    # Calculate total views for user's cards
    total_views = sum(card.get_total_views() for card in cards)
    total_unique_views = sum(card.get_unique_views() for card in cards)
    total_views_today = sum(card.get_views_today() for card in cards)
    total_views_this_month = sum(card.get_views_this_month() for card in cards)

    stats = {
        'total_views': total_views,
        'unique_views': total_unique_views,
        'views_today': total_views_today,
        'views_this_month': total_views_this_month,
        'total_cards': len(cards),
        'public_cards': len([c for c in cards if c.is_public])
    }

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/index_pwa.html', cards=cards, stats=stats)
    else:
        return render_template('dashboard/index.html', cards=cards, stats=stats)

@bp.route('/cards/new', methods=['GET', 'POST'])
@login_required
def new_card():
    if not current_user.can_create_card():
        flash(f'Has alcanzado el límite de {current_user.max_cards} tarjetas. Contacta al administrador para incrementar tu límite.', 'error')
        return redirect(url_for('dashboard.index'))

    # Get or create default classic theme
    default_theme = Theme.query.filter_by(template_name='classic', is_global=True).first()
    if not default_theme:
        # Create a default classic theme if none exists
        default_theme = Theme(
            name='Classic Default',
            template_name='classic',
            primary_color='#667eea',
            secondary_color='#764ba2',
            accent_color='#667eea',
            avatar_border_color='#667eea',
            font_family='Inter',
            layout='classic',
            avatar_shape='circle',
            is_global=True,
            is_active=True
        )
        db.session.add(default_theme)
        db.session.commit()

    form = CardForm()
    # Set default theme
    if not form.theme_id.data:
        form.theme_id.data = default_theme.id

    if form.validate_on_submit():
        card = Card(
            owner_id=current_user.id,
            title=form.title.data,
            name=form.name.data,
            job_title=form.job_title.data,
            company=form.company.data,
            phone=form.phone.data,
            email_public=form.email_public.data,
            website=form.website.data,
            location=form.location.data,
            bio=form.bio.data,
            theme_id=form.theme_id.data or default_theme.id,
            instagram=form.instagram.data,
            whatsapp_country=form.whatsapp_country.data,
            whatsapp=form.whatsapp.data,
            facebook=form.facebook.data,
            linkedin=form.linkedin.data,
            twitter=form.twitter.data,
            youtube=form.youtube.data,
            tiktok=form.tiktok.data,
            telegram=form.telegram.data,
            snapchat=form.snapchat.data,
            pinterest=form.pinterest.data,
            github=form.github.data,
            behance=form.behance.data,
            dribbble=form.dribbble.data,
            is_public=form.is_public.data
        )
        card.generate_slug()

        if card.is_public:
            card.publish()

        db.session.add(card)
        db.session.commit()

        # Clear cache for user
        CacheManager.invalidate_user(current_user.id)

        flash('¡Tarjeta creada exitosamente! Ahora puedes personalizar el diseño y agregar más funciones.', 'success')
        # Redirect to theme customization instead of edit
        return redirect(url_for('dashboard.card_theme', id=card.id))

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/new_card_pwa.html',
                              form=form,
                              default_theme=default_theme)
    else:
        return render_template('dashboard/new_card_with_preview.html',
                              form=form,
                              title='Nueva Tarjeta',
                              default_theme=default_theme)

@bp.route('/cards/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_card(id):
    card = get_user_card_or_404(id)

    form = CardForm(obj=card)
    if form.validate_on_submit():
        # Update card fields
        card.title = form.title.data
        card.name = form.name.data
        card.job_title = form.job_title.data
        card.company = form.company.data
        card.phone = form.phone.data
        card.email_public = form.email_public.data
        card.website = form.website.data
        card.location = form.location.data
        card.bio = form.bio.data
        card.theme_id = form.theme_id.data
        card.instagram = form.instagram.data
        card.whatsapp_country = form.whatsapp_country.data
        card.whatsapp = form.whatsapp.data
        card.facebook = form.facebook.data
        card.linkedin = form.linkedin.data
        card.twitter = form.twitter.data
        card.youtube = form.youtube.data
        card.tiktok = form.tiktok.data
        card.telegram = form.telegram.data
        card.snapchat = form.snapchat.data
        card.pinterest = form.pinterest.data
        card.github = form.github.data
        card.behance = form.behance.data
        card.dribbble = form.dribbble.data

        # Handle publishing
        if form.is_public.data and not card.is_public:
            card.publish()
        elif not form.is_public.data and card.is_public:
            card.unpublish()

        try:
            db.session.commit()

            # Clear cache for this card after successful commit
            CacheManager.invalidate_card(card.id)

            # Additional cache clearing to be thorough
            cache.delete(f'card_data_{card.slug}')
            cache.delete(f'card_view_{card.slug}')

            flash('¡Tarjeta actualizada exitosamente!', 'success')
            return redirect(url_for('dashboard.edit_card', id=card.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la tarjeta: {str(e)}', 'error')
            return redirect(url_for('dashboard.edit_card', id=card.id))

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/card_edit_pwa.html', form=form, card=card)
    else:
        return render_template('dashboard/card_form.html', form=form, card=card, title='Editar Tarjeta')

@bp.route('/cards/<int:id>/delete', methods=['POST'])
@login_required
def delete_card(id):
    card = get_user_card_or_404(id)
    
    # Delete associated files
    cleanup_files([card.avatar_path])
    
    # Delete gallery images
    for item in card.gallery_items:
        if item.image_path:
            cleanup_files([item.image_path, item.thumbnail_path])
    
    db.session.delete(card)
    db.session.commit()
    
    flash('Tarjeta eliminada exitosamente.', 'success')
    return redirect(url_for('dashboard.index'))

@bp.route('/cards/<int:id>/services', methods=['GET', 'POST'])
@login_required
def card_services(id):
    card = get_user_card_or_404(id)

    form = ServiceForm()
    if form.validate_on_submit():
        # Get the next order index
        last_service = Service.query.filter_by(card_id=card.id).order_by(Service.order_index.desc()).first()
        next_order = (last_service.order_index + 1) if last_service else 0

        # Handle service image upload
        image_path = None
        if form.image.data:
            filename, _ = save_image(form.image.data, 'static/uploads')
            if filename:
                image_path = filename

        # Handle category creation
        category_name = handle_category_creation(form, 'service')

        service = Service(
            card_id=card.id,
            title=form.title.data,
            description=form.description.data,
            category=category_name,
            price_from=form.price_from.data,
            duration_minutes=parse_duration_to_minutes(form.duration_minutes.data),
            availability=form.availability.data,
            icon=form.icon.data,
            image_path=image_path,
            is_featured=form.is_featured.data,
            is_visible=form.is_visible.data,
            accepts_appointments=form.accepts_appointments.data,
            order_index=next_order
        )
        db.session.add(service)
        db.session.commit()

        # Clear cache for the parent card
        CacheManager.invalidate_card(card.id)

        flash('¡Servicio agregado exitosamente!', 'success')
        return redirect(url_for('dashboard.card_services', id=card.id))

    services = card.services.order_by(Service.order_index).all()

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/services_pwa.html', card=card, services=services, form=form)
    else:
        return render_template('dashboard/services.html', card=card, services=services, form=form)

@bp.route('/cards/<int:card_id>/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_service(card_id, service_id):
    card = get_user_card_or_404(card_id)
    service = Service.query.filter_by(id=service_id, card_id=card.id).first_or_404()
    
    form = ServiceForm(obj=service)
    
    # Convert duration back to text for display
    if service.duration_minutes:
        form.duration_minutes.data = service.get_duration_display()
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            # Delete old image if exists
            cleanup_files([service.image_path])
            
            filename, _ = save_image(form.image.data, 'static/uploads')
            if filename:
                service.image_path = filename
        
        # Handle category creation
        category_name = handle_category_creation(form, 'service')
        
        service.title = form.title.data
        service.description = form.description.data
        service.category = category_name
        service.price_from = form.price_from.data
        service.duration_minutes = parse_duration_to_minutes(form.duration_minutes.data)
        service.availability = form.availability.data
        service.icon = form.icon.data
        service.is_featured = form.is_featured.data
        service.is_visible = form.is_visible.data
        service.accepts_appointments = form.accepts_appointments.data

        db.session.commit()
        
        # Clear cache for the parent card
        CacheManager.invalidate_card(card.id)
        
        flash('¡Servicio actualizado exitosamente!', 'success')
        return redirect(url_for('dashboard.card_services', id=card.id))
    
    return render_template('dashboard/service_form.html', card=card, service=service, form=form)

@bp.route('/cards/<int:card_id>/services/<int:service_id>/delete', methods=['POST'])
@login_required
def delete_service(card_id, service_id):
    card = get_user_card_or_404(card_id)
    service = Service.query.filter_by(id=service_id, card_id=card.id).first_or_404()
    
    # Delete service image if exists
    cleanup_files([service.image_path])
    
    db.session.delete(service)
    db.session.commit()
    
    # Clear cache for the parent card
    CacheManager.invalidate_card(card.id)
    
    flash('Servicio eliminado exitosamente.', 'success')
    return redirect(url_for('dashboard.card_services', id=card.id))

@bp.route('/cards/<int:id>/gallery', methods=['GET', 'POST'])
@login_required
def card_gallery(id):
    card = get_user_card_or_404(id)

    form = GalleryUploadForm()
    if form.validate_on_submit():
        # Check image limit (20 images maximum)
        current_count = GalleryItem.query.filter_by(card_id=card.id).count()
        if current_count >= 20:
            flash('Límite de imágenes alcanzado. Máximo 20 imágenes por galería. Elimina una imagen para subir otra.', 'error')
            return redirect(url_for('dashboard.card_gallery', id=card.id))

        filename, thumbnail = save_image(form.image.data, 'static/uploads')
        if filename:
            # Get next order index
            last_item = GalleryItem.query.filter_by(card_id=card.id).order_by(GalleryItem.order_index.desc()).first()
            next_order = (last_item.order_index + 1) if last_item else 0

            gallery_item = GalleryItem(
                card_id=card.id,
                image_path=filename,
                thumbnail_path=thumbnail,
                caption=form.caption.data,
                order_index=next_order
            )
            db.session.add(gallery_item)
            db.session.commit()

            # Clear cache for the parent card
            CacheManager.invalidate_card(card.id)

            flash('¡Imagen subida exitosamente!', 'success')
        else:
            flash('Error al subir la imagen. Intenta de nuevo.', 'error')

        return redirect(url_for('dashboard.card_gallery', id=card.id))

    gallery_items = card.gallery_items.order_by(GalleryItem.order_index).all()

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/gallery_pwa.html', card=card, gallery_items=gallery_items, form=form)
    else:
        return render_template('dashboard/gallery.html', card=card, gallery_items=gallery_items, form=form)

@bp.route('/cards/<int:card_id>/gallery/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_gallery_item(card_id, item_id):
    card = get_user_card_or_404(card_id)
    item = GalleryItem.query.filter_by(id=item_id, card_id=card.id).first_or_404()
    
    # Delete files
    if item.image_path:
        cleanup_files([item.image_path, item.thumbnail_path])
    
    db.session.delete(item)
    db.session.commit()
    
    # Clear cache for the parent card
    CacheManager.invalidate_card(card.id)
    
    flash('Imagen eliminada exitosamente.', 'success')
    return redirect(url_for('dashboard.card_gallery', id=card.id))

@bp.route('/cards/<int:id>/avatar', methods=['GET', 'POST', 'DELETE'])
@login_required
def card_avatar(id):
    card = get_user_card_or_404(id)

    if request.method == 'DELETE':
        # Handle avatar deletion
        if card.avatar_path:
            # Delete avatar files
            old_files = [card.avatar_path, card.avatar_square_path, card.avatar_rect_path]
            for old_file in old_files:
                cleanup_files([old_file])

            # Clear avatar paths
            card.avatar_path = None
            card.avatar_square_path = None
            card.avatar_rect_path = None

            # Update the updated_at timestamp for cache busting
            card.updated_at = now_utc_for_db()

            db.session.commit()

            # Clear cache for this card
            CacheManager.invalidate_card(card.id)

            return jsonify({'success': True, 'message': 'Avatar eliminado exitosamente'})
        else:
            return jsonify({'success': False, 'message': 'No hay avatar para eliminar'}), 400

    form = AvatarUploadForm()
    if form.validate_on_submit():
        # Save both versions (square and rectangular)
        square_filename, rect_filename = save_avatar(form.avatar.data)

        if square_filename and rect_filename:
            # Delete old avatars
            old_files = [card.avatar_path, card.avatar_square_path, card.avatar_rect_path]
            for old_file in old_files:
                cleanup_files([old_file])

            # Update card with both versions
            card.avatar_square_path = square_filename
            card.avatar_rect_path = rect_filename
            card.avatar_path = square_filename  # Keep legacy field for backward compatibility

            # Update the updated_at timestamp for cache busting
            from datetime import datetime
            card.updated_at = now_utc_for_db()

            db.session.commit()

            # Clear cache for this card
            CacheManager.invalidate_card(card.id)

            flash('¡Avatar actualizado exitosamente! Se crearon versiones optimizadas para todas las formas.', 'success')
        else:
            flash('Error al subir el avatar. Intenta de nuevo.', 'error')

        return redirect(url_for('dashboard.card_avatar', id=card.id))

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/avatar_pwa.html', card=card, form=form)
    else:
        return render_template('dashboard/avatar.html', card=card, form=form)

@bp.route('/cards/<int:id>/theme', methods=['GET', 'POST'])
@login_required  
def card_theme(id):
    card = get_user_card_or_404(id)
    
    # Create a custom theme for this card if it doesn't have one
    if not card.theme or card.theme.cards.count() > 1:
        # Create a copy of the current theme for this card
        current_theme = card.theme
        new_theme = Theme(
            name=f"Mi tema personalizado",
            template_name=current_theme.template_name if current_theme else 'classic',
            primary_color=current_theme.primary_color if current_theme else '#6366f1',
            secondary_color=current_theme.secondary_color if current_theme else '#8b5cf6',
            accent_color=current_theme.accent_color if current_theme else '#ec4899',
            avatar_border_color=current_theme.avatar_border_color if current_theme else '#ffffff',
            font_family=current_theme.font_family if current_theme else 'Inter',
            layout=current_theme.layout if current_theme else 'modern',
            avatar_shape=current_theme.avatar_shape if current_theme else 'circle',
            is_global=False,  # Personal theme
            created_by_id=current_user.id  # Owned by current user
        )
        db.session.add(new_theme)
        db.session.commit()
        
        card.theme_id = new_theme.id
        db.session.commit()
        
        # Clear cache for this card
        CacheManager.invalidate_card(card.id)
    
    form = ThemeCustomizationForm(obj=card.theme)
    if form.validate_on_submit():
        theme = card.theme
        theme.primary_color = form.primary_color.data
        theme.secondary_color = form.secondary_color.data
        theme.accent_color = form.accent_color.data
        theme.avatar_border_color = form.avatar_border_color.data
        theme.font_family = form.font_family.data
        theme.layout = form.layout.data
        theme.avatar_shape = form.avatar_shape.data
        
        db.session.commit()
        
        # Clear cache for this card
        CacheManager.invalidate_card(card.id)
        
        flash('¡Tema personalizado exitosamente!', 'success')
        return redirect(url_for('dashboard.card_theme', id=card.id))
    
    # Get themes available for current user
    available_themes = Theme.get_available_themes_for_user(current_user)
    
    # Import presets
    from ..theme_presets import get_all_templates
    
    # Get template data
    available_templates = get_all_templates()
    current_template = card.theme.template_name if card.theme else 'classic'
    
    return render_template('dashboard/theme.html', 
                         card=card, 
                         form=form, 
                         available_themes=available_themes,
                         available_templates=available_templates,
                         current_template=current_template)

@bp.route('/cards/<int:id>/change-theme', methods=['POST'])
@login_required
def change_card_theme(id):
    """Change card theme via AJAX"""
    card = get_user_card_or_404(id)
    
    data = request.get_json()
    if not data or 'theme_id' not in data:
        return jsonify({'success': False, 'message': 'ID de tema requerido'})
    
    theme_id = data['theme_id']
    theme = Theme.query.filter_by(id=theme_id, is_active=True).first()
    
    if not theme:
        return jsonify({'success': False, 'message': 'Tema no encontrado'})
    
    # Check if user can access this theme
    if not theme.can_user_access(current_user):
        return jsonify({'success': False, 'message': 'No tienes acceso a este tema'})
    
    # Update card theme
    card.theme_id = theme.id
    db.session.commit()
    
    # Clear cache for the card
    CacheManager.invalidate_card(card.id)
    
    return jsonify({'success': True, 'message': 'Tema cambiado exitosamente'})

@bp.route('/cards/<int:id>/change-template', methods=['POST'])
@login_required
def change_card_template(id):
    """Change card template via AJAX"""
    card = get_user_card_or_404(id)
    
    data = request.get_json()
    if not data or 'template_name' not in data:
        return jsonify({'success': False, 'message': 'Nombre de plantilla requerido'})
    
    template_name = data['template_name']
    
    # Import presets
    from ..theme_presets import get_all_templates
    
    # Validate template exists
    if template_name not in get_all_templates():
        return jsonify({'success': False, 'message': 'Plantilla no válida'})
    
    # Update current theme's template
    if card.theme:
        card.theme.template_name = template_name
        db.session.commit()
    
    # Clear cache for the card
    CacheManager.invalidate_card(card.id)
    
    return jsonify({'success': True, 'message': 'Plantilla cambiada exitosamente'})

@bp.route('/cards/<int:id>/apply-preset', methods=['POST'])
@login_required
def apply_theme_preset(id):
    """Apply a preset configuration to card theme"""
    card = get_user_card_or_404(id)
    
    data = request.get_json()
    if not data or 'preset_key' not in data:
        return jsonify({'success': False, 'message': 'Preset requerido'})
    
    preset_key = data['preset_key']
    
    # Import presets
    from ..theme_presets import get_preset_config
    
    # Get current template
    current_template = card.theme.template_name if card.theme else 'classic'
    
    # Get preset configuration
    preset_config = get_preset_config(current_template, preset_key)
    if not preset_config:
        return jsonify({'success': False, 'message': 'Preset no encontrado'})
    
    # Apply preset to current theme
    if card.theme:
        card.theme.primary_color = preset_config['primary_color']
        card.theme.secondary_color = preset_config['secondary_color']
        card.theme.accent_color = preset_config['accent_color']
        card.theme.font_family = preset_config['font_family']
        card.theme.layout = preset_config['layout']
        card.theme.avatar_shape = preset_config['avatar_shape']
        
        db.session.commit()
    
    # Clear cache for the card
    CacheManager.invalidate_card(card.id)
    
    return jsonify({'success': True, 'message': f'Preset "{preset_config["name"]}" aplicado exitosamente'})


@bp.route('/cards/<int:id>/qr')
@login_required
def card_qr(id):
    card = get_user_card_or_404(id)

    # Generate the public URL for the QR code
    card_url = url_for('public.card_view', slug=card.slug, _external=True)

    # Generate QR code with card theme colors
    qr_img = generate_styled_qr_code(card_url, card.theme, size=(400, 400))

    # Convert to base64 for display
    qr_base64 = qr_to_base64(qr_img)

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/qr_code_pwa.html', card=card, qr_base64=qr_base64, card_url=card_url)
    else:
        return render_template('dashboard/qr_code.html', card=card, qr_base64=qr_base64, card_url=card_url)

@bp.route('/cards/<int:id>/qr/download')
@login_required
def download_qr(id):
    card = get_user_card_or_404(id)
    
    # Get parameters for QR style and size
    style = request.args.get('style', 'themed')  # 'themed', 'classic', 'logo'
    size = int(request.args.get('size', 800))
    
    # Generate the public URL for the QR code
    card_url = url_for('public.card_view', slug=card.slug, _external=True)
    
    # Generate QR code based on style
    try:
        if style == 'themed':
            qr_img = generate_styled_qr_code(card_url, card.theme, size=(size, size))
        elif style == 'logo' and card.get_avatar_path():
            avatar_path = os.path.join(current_app.root_path, 'static', 'uploads', card.get_avatar_path())
            qr_img = generate_qr_code_with_logo(card_url, avatar_path, size=(size, size))
        elif style == 'logo-themed' and card.get_avatar_path():
            avatar_path = os.path.join(current_app.root_path, 'static', 'uploads', card.get_avatar_path())
            qr_img = generate_qr_code_with_logo_themed(card_url, avatar_path, card.theme, size=(size, size))
        else:
            # Classic style or fallback
            qr_img = generate_qr_code(card_url, size=(size, size))
        
        # Save to memory buffer
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Create response with descriptive filename
        style_suffix = f"_{style}" if style != 'themed' else ""
        filename = f"qr_{card.slug}{style_suffix}_{size}px.png"
        
        response = make_response(img_buffer.getvalue())
        response.headers['Content-Type'] = 'image/png'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"Error generating QR for download: {e}")
        # Fallback to basic QR
        qr_img = generate_qr_code(card_url, size=(size, size))
        
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        response = make_response(img_buffer.getvalue())
        response.headers['Content-Type'] = 'image/png'
        response.headers['Content-Disposition'] = f'attachment; filename="qr_{card.slug}.png"'
        
        return response

@bp.route('/cards/<int:id>/qr/generate', methods=['POST'])
@login_required
def generate_qr(id):
    card = get_user_card_or_404(id)
    
    # Get parameters from request
    size = int(request.json.get('size', 400))
    style = request.json.get('style', 'themed')  # 'themed', 'classic', 'logo'
    
    # Generate the public URL for the QR code
    card_url = url_for('public.card_view', slug=card.slug, _external=True)
    
    try:
        if style == 'themed':
            qr_img = generate_styled_qr_code(card_url, card.theme, size=(size, size))
        elif style == 'logo' and card.avatar_path:
            avatar_path = os.path.join(current_app.root_path, 'static', 'uploads', card.avatar_path)
            qr_img = generate_qr_code_with_logo(card_url, avatar_path, size=(size, size))
        elif style == 'logo-themed' and card.avatar_path:
            avatar_path = os.path.join(current_app.root_path, 'static', 'uploads', card.avatar_path)
            qr_img = generate_qr_code_with_logo_themed(card_url, avatar_path, card.theme, size=(size, size))
        else:
            qr_img = generate_qr_code(card_url, size=(size, size))
        
        # Convert to base64
        qr_base64 = qr_to_base64(qr_img)
        
        return jsonify({
            'success': True,
            'qr_code': qr_base64
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/cards/<int:id>/qr/save', methods=['POST'])
@login_required
def save_card_qr(id):
    card = get_user_card_or_404(id)
    
    # Generate the public URL for the QR code
    card_url = url_for('public.card_view', slug=card.slug, _external=True)
    
    # Generate QR code
    qr_img = generate_styled_qr_code(card_url, card.theme, size=(600, 600))
    
    # Save to disk
    filename = f"qr_{card.slug}_{card.id}"
    file_path = save_qr_code(qr_img, filename)
    
    if file_path:
        return jsonify({
            'success': True,
            'file_path': file_path,
            'message': 'Código QR guardado exitosamente'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Error al guardar el código QR'
        }), 500

# Product routes
@bp.route('/cards/<int:id>/products', methods=['GET', 'POST'])
@login_required
def card_products(id):
    card = get_user_card_or_404(id)
    products = card.products.order_by(Product.order_index.asc(), Product.created_at.desc()).all()
    form = ProductForm()

    if form.validate_on_submit():
        # Handle category creation
        category_name = handle_category_creation(form, 'product')

        product = Product(
            name=form.name.data,
            description=form.description.data,
            category=category_name,
            brand=form.brand.data,
            price=form.price.data,
            original_price=form.original_price.data,
            sku=form.sku.data,
            stock_quantity=int(form.stock_quantity.data) if form.stock_quantity.data is not None else None,
            external_link=form.external_link.data,
            is_visible=form.is_visible.data,
            is_featured=form.is_featured.data,
            is_available=form.is_available.data,
            card_id=card.id
        )

        # Handle image upload
        if form.image.data:
            filename, thumbnail_filename = save_image(form.image.data, 'static/uploads')
            if filename:
                product.image_path = filename

        db.session.add(product)
        db.session.commit()

        # Clear cache for the parent card
        CacheManager.invalidate_card(card.id)

        flash('Producto agregado correctamente', 'success')
        return redirect(url_for('dashboard.card_products', id=card.id))

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/products_pwa.html', card=card, products=products, form=form)
    else:
        return render_template('dashboard/products.html', card=card, products=products, form=form)

@bp.route('/cards/<int:card_id>/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(card_id, product_id):
    card = get_user_card_or_404(card_id)
    product = Product.query.filter_by(id=product_id, card_id=card_id).first_or_404()
    
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        # Handle category creation
        category_name = handle_category_creation(form, 'product')
        
        product.name = form.name.data
        product.description = form.description.data
        product.category = category_name
        product.brand = form.brand.data
        product.price = form.price.data
        product.original_price = form.original_price.data
        product.sku = form.sku.data
        product.stock_quantity = int(form.stock_quantity.data) if form.stock_quantity.data is not None else None
        product.external_link = form.external_link.data
        product.is_visible = form.is_visible.data
        product.is_featured = form.is_featured.data
        product.is_available = form.is_available.data
        
        # Handle image upload
        if form.image.data:
            cleanup_files([product.image_path])
            
            filename, thumbnail_filename = save_image(form.image.data, 'static/uploads')
            if filename:
                product.image_path = filename
        
        db.session.commit()
        
        # Clear cache for the parent card
        CacheManager.invalidate_card(card.id)
        
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('dashboard.card_products', id=card.id))
    
    return render_template('dashboard/product_form.html', card=card, product=product, form=form)


@bp.route('/analytics')
@login_required
def analytics():
    """Enhanced analytics dashboard"""
    days = request.args.get('days', 30, type=int)

    # Get user's analytics data
    analytics_data = AnalyticsService.get_user_analytics(current_user.id, days)

    # Get device analytics for all user's cards
    card_ids = [card['card_id'] for card in analytics_data.get('cards_analytics', [])]
    device_analytics = {}
    if card_ids:
        device_analytics = AnalyticsService.get_device_analytics(None, days)  # Global for user
        # Filter by user's cards
        user_device_query = db.session.query(
            CardView.device_type,
            func.count(CardView.id).label('count')
        ).filter(
            CardView.card_id.in_(card_ids),
            CardView.viewed_at >= get_date_range_utc(days)[0]
        ).group_by(CardView.device_type).all()

        total_user_views = sum(stat.count for stat in user_device_query)
        user_device_breakdown = []

        for stat in user_device_query:
            device_type = stat.device_type or 'Unknown'
            percentage = (stat.count / total_user_views * 100) if total_user_views > 0 else 0
            user_device_breakdown.append({
                'device_type': device_type,
                'count': stat.count,
                'percentage': round(percentage, 1)
            })

        # Calculate mobile vs desktop for user
        mobile_count = sum(d['count'] for d in user_device_breakdown if d['device_type'] in ['mobile', 'tablet'])
        desktop_count = sum(d['count'] for d in user_device_breakdown if d['device_type'] == 'desktop')

        device_analytics = {
            'device_breakdown': user_device_breakdown,
            'total_views': total_user_views,
            'mobile_vs_desktop': {
                'mobile': {
                    'count': mobile_count,
                    'percentage': round((mobile_count / total_user_views * 100) if total_user_views > 0 else 0, 1)
                },
                'desktop': {
                    'count': desktop_count,
                    'percentage': round((desktop_count / total_user_views * 100) if total_user_views > 0 else 0, 1)
                }
            }
        }

    # Calculate growth rate
    prev_period_views = 0
    if analytics_data['cards_analytics']:
        prev_start, _ = get_date_range_utc(days*2)
        _, prev_period_end = get_date_range_utc(days)
        prev_period_start = prev_start

        card_ids = [card['card_id'] for card in analytics_data['cards_analytics']]
        if card_ids:
            prev_period_views = CardView.query.filter(
                CardView.card_id.in_(card_ids),
                CardView.viewed_at >= prev_period_start,
                CardView.viewed_at < prev_period_end
            ).count()

    growth_rate = 0
    if prev_period_views > 0:
        growth_rate = ((analytics_data['period_views'] - prev_period_views) / prev_period_views) * 100

    # Global views today
    global_views_today = 0
    if analytics_data['cards_analytics']:
        card_ids = [card['card_id'] for card in analytics_data['cards_analytics']]
        if card_ids:
            today_start, today_end = get_date_range_utc(1)
            global_views_today = CardView.query.filter(
                CardView.card_id.in_(card_ids),
                CardView.viewed_at >= today_start,
                CardView.viewed_at <= today_end
            ).count()

    # Aggregate data across all cards for charts
    all_daily_views = {}
    all_device_stats = {}
    all_browser_stats = {}
    all_location_stats = {}
    all_hourly_stats = {}

    for card_analytics in analytics_data['cards_analytics']:
        card_data = card_analytics['analytics']

        # Aggregate daily views
        for day in card_data['daily_views']:
            date = day['date']
            if date in all_daily_views:
                all_daily_views[date] += day['views']
            else:
                all_daily_views[date] = day['views']

        # Aggregate device stats
        for device in card_data['device_stats']:
            device_name = device['device']
            if device_name in all_device_stats:
                all_device_stats[device_name] += device['count']
            else:
                all_device_stats[device_name] = device['count']

        # Aggregate browser stats
        for browser in card_data['browser_stats']:
            browser_name = browser['browser']
            if browser_name in all_browser_stats:
                all_browser_stats[browser_name] += browser['count']
            else:
                all_browser_stats[browser_name] = browser['count']

        # Aggregate location stats
        for location in card_data['location_stats']:
            country = location['country']
            if country in all_location_stats:
                all_location_stats[country] += location['count']
            else:
                all_location_stats[country] = location['count']

        # Aggregate hourly stats
        for hour in card_data['hourly_stats']:
            hour_num = hour['hour']
            if hour_num in all_hourly_stats:
                all_hourly_stats[hour_num] += hour['count']
            else:
                all_hourly_stats[hour_num] = hour['count']

    # Format aggregated data for charts
    aggregated_analytics = {
        'total_views': analytics_data['total_views'],
        'period_views': analytics_data['period_views'],
        'views_today': global_views_today,
        'growth_rate': growth_rate,
        'daily_views': [{'date': date, 'views': views} for date, views in sorted(all_daily_views.items())],
        'device_stats': [{'device': device, 'count': count} for device, count in all_device_stats.items()],
        'browser_stats': [{'browser': browser, 'count': count} for browser, count in all_browser_stats.items()],
        'location_stats': [{'country': country, 'count': count} for country, count in sorted(all_location_stats.items(), key=lambda x: x[1], reverse=True)[:10]],
        'hourly_stats': [{'hour': hour, 'count': all_hourly_stats.get(hour, 0)} for hour in range(24)]
    }

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/analytics_pwa.html',
                              global_stats=aggregated_analytics,
                              cards_analytics=analytics_data['cards_analytics'],
                              device_analytics=device_analytics)
    else:
        return render_template('dashboard/analytics.html',
                              global_stats=aggregated_analytics,
                              cards_analytics=analytics_data['cards_analytics'],
                              device_analytics=device_analytics)


@bp.route('/analytics-data')
@login_required  
def analytics_data():
    """API endpoint for AJAX analytics updates"""
    days = request.args.get('days', 30, type=int)
    
    # Get fresh analytics data
    analytics_data = AnalyticsService.get_user_analytics(current_user.id, days)
    
    # Get device analytics for AJAX updates
    card_ids = [card['card_id'] for card in analytics_data.get('cards_analytics', [])]
    device_analytics = {}
    if card_ids:
        user_device_query = db.session.query(
            CardView.device_type,
            func.count(CardView.id).label('count')
        ).filter(
            CardView.card_id.in_(card_ids),
            CardView.viewed_at >= get_date_range_utc(days)[0]
        ).group_by(CardView.device_type).all()
        
        total_user_views = sum(stat.count for stat in user_device_query)
        user_device_breakdown = []
        
        for stat in user_device_query:
            device_type = stat.device_type or 'Unknown'
            percentage = (stat.count / total_user_views * 100) if total_user_views > 0 else 0
            user_device_breakdown.append({
                'device_type': device_type,
                'count': stat.count,
                'percentage': round(percentage, 1)
            })
        
        mobile_count = sum(d['count'] for d in user_device_breakdown if d['device_type'] in ['mobile', 'tablet'])
        desktop_count = sum(d['count'] for d in user_device_breakdown if d['device_type'] == 'desktop')
        
        device_analytics = {
            'device_breakdown': user_device_breakdown,
            'mobile_vs_desktop': {
                'mobile': {'count': mobile_count},
                'desktop': {'count': desktop_count}
            }
        }
    
    # Aggregate data similar to analytics route
    all_daily_views = {}
    all_device_stats = {}
    all_browser_stats = {}
    all_hourly_stats = {}
    
    for card_analytics in analytics_data['cards_analytics']:
        card_data = card_analytics['analytics']
        
        for day in card_data['daily_views']:
            date = day['date']
            all_daily_views[date] = all_daily_views.get(date, 0) + day['views']
        
        for device in card_data['device_stats']:
            device_name = device['device']
            all_device_stats[device_name] = all_device_stats.get(device_name, 0) + device['count']
        
        for browser in card_data['browser_stats']:
            browser_name = browser['browser']
            all_browser_stats[browser_name] = all_browser_stats.get(browser_name, 0) + browser['count']
        
        for hour in card_data['hourly_stats']:
            hour_num = hour['hour']
            all_hourly_stats[hour_num] = all_hourly_stats.get(hour_num, 0) + hour['count']
    
    return jsonify({
        'total_views': analytics_data['total_views'],
        'period_views': analytics_data['period_views'],
        'growth_rate': growth_rate,
        'daily_views': [{'date': date, 'views': views} for date, views in sorted(all_daily_views.items())],
        'device_stats': [{'device': device, 'count': count} for device, count in all_device_stats.items()],
        'browser_stats': [{'browser': browser, 'count': count} for browser, count in all_browser_stats.items()],
        'hourly_stats': [{'hour': hour, 'count': all_hourly_stats.get(hour, 0)} for hour in range(24)]
    })


@bp.route('/cards/<int:id>/visual-editor')
@login_required
def visual_editor(id):
    """Visual drag-and-drop editor for card layout"""
    from flask import current_app
    
    # Check if visual editor is enabled
    if not current_app.config.get('ENABLE_VISUAL_EDITOR', False):
        abort(404)  # Return 404 if feature is disabled
        
    card = get_user_card_or_404(id)
    return render_template('dashboard/visual_editor.html', card=card)


@bp.route('/cards/<int:id>/save-design', methods=['POST'])
@login_required
def save_design(id):
    """Save visual design layout"""
    from flask import current_app
    
    # Check if visual editor is enabled
    if not current_app.config.get('ENABLE_VISUAL_EDITOR', False):
        abort(404)  # Return 404 if feature is disabled
        
    card = get_user_card_or_404(id)
    
    try:
        data = request.get_json()
        layout = data.get('layout', '')
        
        # Save layout to card's custom_layout field
        card.custom_layout = layout
        db.session.commit()
        
        # Clear cache since layout changed
        CacheManager.invalidate_card(card.id)
        
        return jsonify({'success': True, 'message': 'Diseño guardado exitosamente'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/advanced-features')
@login_required
def advanced_features():
    """Advanced features page showing all new capabilities"""
    cards = current_user.cards.all()
    return render_template('dashboard/advanced_features.html', cards=cards)


@bp.route('/export/vcard/<int:card_id>')
@login_required
def export_vcard(card_id):
    """Export card as vCard (.vcf) format"""
    card = get_user_card_or_404(card_id)
    
    # Create vCard content
    vcard_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{card.name}
ORG:{card.company or ''}
TITLE:{card.job_title or ''}
TEL:{card.get_whatsapp_full_number() or card.phone or ''}
EMAIL:{card.email_public or ''}
URL:{card.website or ''}
NOTE:{card.bio or ''}
END:VCARD"""
    
    response = make_response(vcard_content)
    response.headers['Content-Type'] = 'text/vcard'
    response.headers['Content-Disposition'] = f'attachment; filename="{card.name}.vcf"'
    
    return response


@bp.route('/export/analytics')
@login_required
@admin_required
def export_analytics():
    """Export analytics data as CSV"""
    import csv
    import io
    
    # Get user's analytics data
    analytics_data = AnalyticsService.get_user_analytics(current_user.id, 30)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Tarjeta', 'Vistas Totales', 'Vistas Período', 'Dispositivo Principal', 'País Principal'])
    
    # Write data
    for card_data in analytics_data['cards_analytics']:
        top_device = card_data['analytics']['device_stats'][0] if card_data['analytics']['device_stats'] else {'device': 'N/A'}
        top_country = card_data['analytics']['location_stats'][0] if card_data['analytics']['location_stats'] else {'country': 'N/A'}
        
        writer.writerow([
            card_data['card_name'],
            card_data['analytics']['total_views'],
            card_data['analytics']['period_views'],
            top_device['device'],
            top_country['country']
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename="analytics_{now_local().strftime("%Y%m%d")}.csv"'
    
    return response

@bp.route('/cards/<int:card_id>/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(card_id, product_id):
    card = get_user_card_or_404(card_id)
    product = Product.query.filter_by(id=product_id, card_id=card_id).first_or_404()
    
    cleanup_files([product.image_path])
    
    db.session.delete(product)
    db.session.commit()
    
    # Clear cache for the parent card
    CacheManager.invalidate_card(card_id)
    
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('dashboard.card_products', id=card_id))


# Admin-only routes
@bp.route('/admin/performance')
@login_required
@admin_required
def admin_performance():
    """Admin-only performance dashboard"""
    from ..analytics import AnalyticsService
    
    # Get global analytics
    global_analytics = AnalyticsService.get_global_analytics(30)
    
    # Get cache stats (if available)
    cache_stats = {
        'status': 'active',
        'backend': 'simple',
        'hit_rate': 'N/A'  # Would need to implement cache metrics
    }
    
    # Get system performance metrics
    import psutil
    system_stats = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0
    }
    
    return render_template('dashboard/admin_performance.html',
                         analytics=global_analytics,
                         cache_stats=cache_stats,
                         system_stats=system_stats)

@bp.route('/admin/cache/clear', methods=['POST'])
@login_required
@admin_required
def admin_clear_cache():
    """Admin-only cache clearing"""
    cache_type = request.form.get('cache_type', 'all')
    
    if cache_type == 'all':
        cache.clear()
        flash('Toda la cache ha sido limpiada', 'success')
    elif cache_type == 'analytics':
        # Clear analytics cache
        cache.delete_many('analytics_*')
        flash('Cache de analytics limpiada', 'success')
    elif cache_type == 'cards':
        # Clear cards cache
        cache.delete_many('card_*')
        flash('Cache de tarjetas limpiada', 'success')
    
    return redirect(url_for('dashboard.admin_performance'))

@bp.route('/admin/cache/warm', methods=['POST'])
@login_required
@admin_required
def admin_warm_cache():
    """Admin-only cache warming"""
    CacheManager.warm_popular_cards(10)
    flash('Cache precalentada para las tarjetas más populares', 'success')
    return redirect(url_for('dashboard.admin_performance'))

@bp.route('/admin/backup')
@login_required
@admin_required
def admin_backup():
    """Admin-only backup and export dashboard"""
    import os
    from datetime import datetime
    
    # Get database stats
    db_stats = {
        'total_users': User.query.count(),
        'total_cards': Card.query.count(),
        'total_views': CardView.query.count(),
        'db_size': 'N/A'  # Would need to implement database size calculation
    }
    
    # Get backup history (would need to implement)
    backup_history = []
    
    return render_template('dashboard/admin_backup.html',
                         db_stats=db_stats,
                         backup_history=backup_history)

@bp.route('/admin/export/full-backup')
@login_required
@admin_required
def admin_export_full_backup():
    """Admin-only full system backup"""
    import json
    import io
    
    # Export all data
    backup_data = {
        'users': [],
        'cards': [],
        'views': [],
        'export_date': now_utc_for_db().isoformat()
    }
    
    # Export users (without passwords)
    for user in User.query.all():
        backup_data['users'].append({
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    
    # Export cards
    for card in Card.query.all():
        backup_data['cards'].append({
            'id': card.id,
            'name': card.name,
            'slug': card.slug,
            'owner_id': card.owner_id,
            'is_public': card.is_public,
            'created_at': card.created_at.isoformat() if card.created_at else None
        })
    
    # Create JSON response
    output = json.dumps(backup_data, indent=2)
    response = make_response(output)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename="full_backup_{now_local().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile and password change"""
    form = ChangePasswordForm()

    if request.method == 'POST':
        # First check if current password is correct
        if not current_user.check_password(form.current_password.data):
            form.current_password.errors.append('La contraseña actual es incorrecta.')
        elif form.validate_on_submit():
            # Update password
            current_user.set_password(form.new_password.data)
            db.session.commit()

            flash('¡Contraseña cambiada exitosamente!', 'success')
            return redirect(url_for('dashboard.profile'))
        # If validation fails for other reasons, errors will be in form.errors

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/profile_pwa.html', form=form)
    else:
        return render_template('dashboard/profile.html', form=form)

@bp.route('/cards/<int:id>/social-networks', methods=['GET', 'POST'])
@login_required
def card_social_networks(id):
    """Configure social network display preferences for a card"""
    card = get_user_card_or_404(id)

    if request.method == 'POST':
        # Validate CSRF token
        validate_csrf(request.form.get('csrf_token'))

        # Get selected primary networks from form
        primary_networks = request.form.getlist('primary_networks')

        # Save preferences
        card.set_primary_social_networks(primary_networks)
        db.session.commit()

        # Clear cache for the parent card
        CacheManager.invalidate_card(card.id)

        flash('Configuración de redes sociales actualizada correctamente', 'success')
        return redirect(url_for('dashboard.card_social_networks', id=card.id))

    # Get available networks and current preferences
    available_networks = card.get_available_social_networks()
    primary_fields = card.get_primary_social_network_fields()

    return render_template('dashboard/social_networks.html',
                          card=card,
                          available_networks=available_networks,
                          primary_fields=primary_fields)

@bp.route('/cards')
@login_required
def cards_list():
    """Unified cards list view for mobile navigation"""
    cards = current_user.cards.order_by(Card.created_at.desc()).all()

    # Get filter parameters
    status_filter = request.args.get('status', 'all')  # all, public, draft
    search_query = request.args.get('search', '').strip()

    # Apply filters
    if status_filter == 'public':
        cards = [card for card in cards if card.is_public]
    elif status_filter == 'draft':
        cards = [card for card in cards if not card.is_public]

    if search_query:
        cards = [card for card in cards if search_query.lower() in card.name.lower() or search_query.lower() in card.title.lower()]

    return render_template('dashboard/cards_list.html',
                          cards=cards,
                          status_filter=status_filter,
                          search_query=search_query)

@bp.route('/qr-menu')
@login_required
def qr_menu():
    """QR codes menu showing all user's cards with their QR codes"""
    cards = current_user.cards.order_by(Card.created_at.desc()).all()

    # Generate QR codes for each card
    cards_with_qr = []
    for card in cards:
        # Generate the public URL for the QR code
        card_url = url_for('public.card_view', slug=card.slug, _external=True)

        # Generate QR code with card theme colors
        qr_img = generate_styled_qr_code(card_url, card.theme, size=(300, 300))

        # Convert to base64 for display
        qr_base64 = qr_to_base64(qr_img)

        cards_with_qr.append({
            'card': card,
            'qr_base64': qr_base64,
            'card_url': card_url
        })

    # Use qr_code_pwa.html template with show_list flag
    return render_template('dashboard/qr_code_pwa.html', cards_with_qr=cards_with_qr, show_list=True)

# ============================================================================
# SISTEMA DE TICKETS - Rutas del Dashboard
# ============================================================================

@bp.route('/tickets')
@login_required
def tickets():
    """Panel principal de gestión de turnos para el médico"""
    # Verificar si el usuario tiene el sistema de turnos habilitado
    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        flash('El sistema de turnos no está habilitado para tu cuenta. Contacta al administrador.', 'warning')
        return redirect(url_for('dashboard.index'))

    system = current_user.ticket_system

    # Obtener turno actual (en progreso)
    current_ticket = system.get_current_ticket()

    # Obtener todos los turnos en espera, ordenados por tiempo de creación (FIFO)
    waiting_tickets = system.tickets.filter_by(status='waiting').order_by(Ticket.created_at).all()

    # Estadísticas del día
    today_start = today_start_utc()
    today_stats = {
        'completed': system.tickets.filter(
            Ticket.status == 'completed',
            Ticket.created_at >= today_start
        ).count(),
        'cancelled': system.tickets.filter(
            Ticket.status == 'cancelled',
            Ticket.created_at >= today_start
        ).count(),
        'no_show': system.tickets.filter(
            Ticket.status == 'no_show',
            Ticket.created_at >= today_start
        ).count(),
        'waiting': len(waiting_tickets)
    }

    # Obtener tipos de tickets activos
    ticket_types = system.get_active_types()

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/tickets_pwa.html',
                              system=system,
                              current_ticket=current_ticket,
                              waiting_tickets=waiting_tickets,
                              today_stats=today_stats,
                              ticket_types=ticket_types)
    else:
        return render_template('dashboard/tickets/index.html',
                              system=system,
                              current_ticket=current_ticket,
                              waiting_tickets=waiting_tickets,
                              today_stats=today_stats,
                              ticket_types=ticket_types)

@bp.route('/tickets/settings', methods=['GET', 'POST'])
@login_required
def tickets_settings():
    """Configuración del sistema de turnos y gestión de tipos de citas"""
    from .forms import TicketSystemForm, TicketTypeForm

    # Verificar si el usuario tiene el sistema de turnos habilitado
    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        flash('El sistema de turnos no está habilitado para tu cuenta. Contacta al administrador.', 'warning')
        return redirect(url_for('dashboard.index'))

    system = current_user.ticket_system

    # Formulario de configuración del sistema
    system_form = TicketSystemForm(obj=system)
    if system_form.validate_on_submit() and request.form.get('form_type') == 'system':
        system.business_name = system_form.business_name.data
        system.welcome_message = system_form.welcome_message.data
        system.business_hours = system_form.business_hours.data
        system.display_mode = system_form.display_mode.data
        system.pause_message = system_form.pause_message.data
        system.resume_time = system_form.resume_time.data
        system.phone_country_prefix = system_form.phone_country_prefix.data
        system.require_patient_email = system_form.require_patient_email.data
        system.collect_patient_birthdate = system_form.collect_patient_birthdate.data
        db.session.commit()
        flash('Configuración actualizada exitosamente', 'success')
        return redirect(url_for('dashboard.tickets_settings'))

    # Obtener todos los tipos de citas
    ticket_types = system.ticket_types.order_by(TicketType.order_index).all()

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/tickets_settings_pwa.html',
                              system=system,
                              system_form=system_form,
                              ticket_types=ticket_types)
    else:
        return render_template('dashboard/tickets/settings.html',
                              system=system,
                              system_form=system_form,
                              ticket_types=ticket_types)

@bp.route('/tickets/types/new', methods=['GET', 'POST'])
@login_required
def new_ticket_type():
    """Crear nuevo tipo de cita"""
    from .forms import TicketTypeForm
    from ..models import TicketSystem, TicketType

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        flash('El sistema de turnos no está habilitado para tu cuenta.', 'warning')
        return redirect(url_for('dashboard.index'))

    system = current_user.ticket_system

    # Verificar límite de tipos de citas
    if not system.can_add_type():
        flash(f'Has alcanzado el límite de {system.max_ticket_types} tipos de citas.', 'error')
        return redirect(url_for('dashboard.tickets_settings'))

    form = TicketTypeForm()
    if form.validate_on_submit():
        # Obtener el siguiente order_index
        last_type = system.ticket_types.order_by(TicketType.order_index.desc()).first()
        next_order = (last_type.order_index + 1) if last_type else 0

        ticket_type = TicketType(
            ticket_system_id=system.id,
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            estimated_duration=form.estimated_duration.data,
            prefix=form.prefix.data.upper(),
            is_active=form.is_active.data,
            order_index=next_order
        )
        db.session.add(ticket_type)
        db.session.commit()
        flash(f'Tipo de cita "{ticket_type.name}" creado exitosamente', 'success')
        return redirect(url_for('dashboard.tickets_settings'))

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/tickets_type_form_pwa.html',
                              form=form,
                              title='Nuevo Tipo de Cita')
    else:
        return render_template('dashboard/tickets/type_form.html',
                              form=form,
                              title='Nuevo Tipo de Cita')

@bp.route('/tickets/types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket_type(id):
    """Editar tipo de cita existente"""
    from .forms import TicketTypeForm
    from ..models import TicketType

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        flash('El sistema de turnos no está habilitado para tu cuenta.', 'warning')
        return redirect(url_for('dashboard.index'))

    ticket_type = TicketType.query.filter_by(
        id=id,
        ticket_system_id=current_user.ticket_system.id
    ).first_or_404()

    form = TicketTypeForm(obj=ticket_type)
    if form.validate_on_submit():
        ticket_type.name = form.name.data
        ticket_type.description = form.description.data
        ticket_type.color = form.color.data
        ticket_type.estimated_duration = form.estimated_duration.data
        ticket_type.prefix = form.prefix.data.upper()
        ticket_type.is_active = form.is_active.data
        db.session.commit()
        flash(f'Tipo de cita "{ticket_type.name}" actualizado exitosamente', 'success')
        return redirect(url_for('dashboard.tickets_settings'))

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/tickets_type_form_pwa.html',
                              form=form,
                              ticket_type=ticket_type,
                              title='Editar Tipo de Cita')
    else:
        return render_template('dashboard/tickets/type_form.html',
                              form=form,
                              ticket_type=ticket_type,
                              title='Editar Tipo de Cita')

@bp.route('/tickets/types/<int:id>/delete', methods=['POST'])
@login_required
def delete_ticket_type(id):
    """Eliminar tipo de cita"""
    from ..models import TicketType

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        flash('El sistema de turnos no está habilitado para tu cuenta.', 'warning')
        return redirect(url_for('dashboard.index'))

    ticket_type = TicketType.query.filter_by(
        id=id,
        ticket_system_id=current_user.ticket_system.id
    ).first_or_404()

    # Verificar si hay turnos activos de este tipo
    active_tickets = ticket_type.tickets.filter(
        Ticket.status.in_(['waiting', 'in_progress'])
    ).count()

    if active_tickets > 0:
        flash(f'No se puede eliminar el tipo de cita porque tiene {active_tickets} turnos activos.', 'error')
        return redirect(url_for('dashboard.tickets_settings'))

    type_name = ticket_type.name
    db.session.delete(ticket_type)
    db.session.commit()
    flash(f'Tipo de cita "{type_name}" eliminado exitosamente', 'success')
    return redirect(url_for('dashboard.tickets_settings'))

@bp.route('/tickets/call-next', methods=['POST'])
@login_required
def call_next_ticket():
    """Llamar al siguiente paciente en la cola (AJAX)"""
    from ..models import Ticket

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema de turnos no habilitado'}), 403

    system = current_user.ticket_system

    # Verificar si ya hay un turno en progreso
    current_ticket = system.get_current_ticket()
    if current_ticket:
        return jsonify({
            'success': False,
            'message': f'Ya tienes un turno en progreso: {current_ticket.ticket_number}'
        }), 400

    # Obtener el siguiente turno en espera (FIFO)
    next_ticket = system.tickets.filter_by(status='waiting').order_by(Ticket.created_at).first()

    if not next_ticket:
        return jsonify({'success': False, 'message': 'No hay turnos en espera'}), 404

    # Llamar al paciente
    next_ticket.call()
    db.session.commit()

    return jsonify({
        'success': True,
        'ticket': {
            'id': next_ticket.id,
            'ticket_number': next_ticket.ticket_number,
            'patient_name': next_ticket.patient_name,
            'patient_phone': next_ticket.patient_phone,
            'type_name': next_ticket.type.name,
            'type_color': next_ticket.type.color
        }
    })

@bp.route('/tickets/<int:id>/complete', methods=['POST'])
@login_required
def complete_ticket(id):
    """Completar turno actual"""
    from ..models import Ticket

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema de turnos no habilitado'}), 403

    ticket = Ticket.query.filter_by(
        id=id,
        ticket_system_id=current_user.ticket_system.id
    ).first_or_404()

    # Si el turno está en espera, llamarlo primero
    if ticket.status == 'waiting':
        ticket.call()
        db.session.commit()

    # Verificar estado actual
    if ticket.status == 'completed':
        return jsonify({'success': False, 'message': f'Este turno ya fue completado'}), 400
    elif ticket.status == 'cancelled':
        return jsonify({'success': False, 'message': f'Este turno fue cancelado'}), 400
    elif ticket.status == 'no_show':
        return jsonify({'success': False, 'message': f'Este turno fue marcado como ausente'}), 400
    elif ticket.status != 'in_progress':
        return jsonify({'success': False, 'message': f'Estado inválido: {ticket.status}'}), 400

    # Obtener notas médicas (pueden venir en JSON o form data)
    medical_notes = request.json.get('medical_notes', '') if request.is_json else request.form.get('medical_notes', '')
    ticket.complete(medical_notes)
    db.session.commit()

    # Llamar automáticamente al siguiente en la cola si existe
    system = current_user.ticket_system
    next_ticket = system.tickets.filter_by(status='waiting').order_by(Ticket.created_at).first()
    if next_ticket:
        next_ticket.call()
        db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': f'Turno {ticket.ticket_number} completado'})
    else:
        flash(f'Turno {ticket.ticket_number} completado exitosamente', 'success')
        return redirect(url_for('dashboard.tickets'))

@bp.route('/tickets/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_ticket(id):
    """Cancelar turno"""
    from ..models import Ticket

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema de turnos no habilitado'}), 403

    ticket = Ticket.query.filter_by(
        id=id,
        ticket_system_id=current_user.ticket_system.id
    ).first_or_404()

    if ticket.status not in ['waiting', 'in_progress']:
        return jsonify({'success': False, 'message': f'Este turno no se puede cancelar (estado: {ticket.status})'}), 400

    reason = request.json.get('reason', '') if request.is_json else request.form.get('reason', '')
    was_in_progress = ticket.status == 'in_progress'
    ticket.cancel(reason)
    db.session.commit()

    # Si era el turno actual, llamar automáticamente al siguiente si existe
    if was_in_progress:
        system = current_user.ticket_system
        next_ticket = system.tickets.filter_by(status='waiting').order_by(Ticket.created_at).first()
        if next_ticket:
            next_ticket.call()
            db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': f'Turno {ticket.ticket_number} cancelado'})
    else:
        flash(f'Turno {ticket.ticket_number} cancelado', 'info')
        return redirect(url_for('dashboard.tickets'))

@bp.route('/tickets/<int:id>/no-show', methods=['POST'])
@login_required
def mark_no_show(id):
    """Marcar paciente como ausente"""
    from ..models import Ticket

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema de turnos no habilitado'}), 403

    ticket = Ticket.query.filter_by(
        id=id,
        ticket_system_id=current_user.ticket_system.id
    ).first_or_404()

    # Si el turno está en espera, llamarlo primero
    if ticket.status == 'waiting':
        ticket.call()
        db.session.commit()

    # Ahora marcar como ausente
    if ticket.status not in ['in_progress', 'waiting']:
        return jsonify({'success': False, 'message': f'Este turno ya fue procesado (estado: {ticket.status})'}), 400

    ticket.mark_no_show()
    db.session.commit()

    # Llamar automáticamente al siguiente en la cola si existe
    system = current_user.ticket_system
    next_ticket = system.tickets.filter_by(status='waiting').order_by(Ticket.created_at).first()
    if next_ticket:
        next_ticket.call()
        db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': f'Turno {ticket.ticket_number} marcado como ausente'})
    else:
        flash(f'Turno {ticket.ticket_number} marcado como ausente', 'info')
        return redirect(url_for('dashboard.tickets'))

@bp.route('/tickets/reset-daily-queue', methods=['POST'])
@login_required
def reset_daily_queue():
    """Reiniciar la cola diaria - cancelar turnos en espera del día anterior"""
    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema de turnos no habilitado'}), 403

    system = current_user.ticket_system

    # Ejecutar el reset diario
    cancelled_count = system.reset_daily_queue()

    if request.is_json:
        return jsonify({
            'success': True,
            'message': f'Cola diaria reiniciada. {cancelled_count} turnos antiguos cancelados.',
            'cancelled_count': cancelled_count
        })
    else:
        flash(f'Cola diaria reiniciada exitosamente. {cancelled_count} turnos antiguos fueron cancelados.', 'success')
        return redirect(url_for('dashboard.tickets'))

@bp.route('/tickets/toggle-pause', methods=['POST'])
@login_required
def toggle_pause_tickets():
    """Pausar o reanudar la toma de turnos"""
    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema de turnos no habilitado'}), 403

    system = current_user.ticket_system

    # Alternar el estado
    system.is_accepting_tickets = not system.is_accepting_tickets
    db.session.commit()

    status = 'reanudado' if system.is_accepting_tickets else 'pausado'
    message = f'Sistema {status}. {"Ahora se pueden tomar turnos." if system.is_accepting_tickets else "No se aceptarán nuevos turnos."}'

    if request.is_json:
        return jsonify({
            'success': True,
            'message': message,
            'is_accepting': system.is_accepting_tickets
        })
    else:
        flash(message, 'success')
        return redirect(url_for('dashboard.tickets'))

@bp.route('/tickets/<int:id>/mark-urgent', methods=['POST'])
@login_required
def mark_ticket_urgent(id):
    """Marcar turno como urgente (prioridad alta)"""
    from ..models import Ticket

    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema de turnos no habilitado'}), 403

    ticket = Ticket.query.filter_by(
        id=id,
        ticket_system_id=current_user.ticket_system.id
    ).first_or_404()

    if ticket.status != 'waiting':
        return jsonify({'success': False, 'message': 'Solo se pueden marcar como urgentes los turnos en espera'}), 400

    if ticket.priority == 1:
        return jsonify({'success': False, 'message': 'Este turno ya está marcado como urgente'}), 400

    # Marcar como urgente
    ticket.mark_urgent()
    db.session.commit()

    if request.is_json:
        return jsonify({
            'success': True,
            'message': f'Turno {ticket.ticket_number} marcado como urgente',
            'new_position': ticket.get_position_in_queue()
        })
    else:
        flash(f'Turno {ticket.ticket_number} marcado como urgente', 'success')
        return redirect(url_for('dashboard.tickets'))

@bp.route('/tickets/metrics')
@login_required
def tickets_metrics():
    """Panel de métricas avanzadas del sistema de turnos"""
    if not current_user.ticket_system or not current_user.ticket_system.is_enabled:
        flash('El sistema de turnos no está habilitado para tu cuenta.', 'warning')
        return redirect(url_for('dashboard.index'))

    system = current_user.ticket_system

    # Obtener días de análisis (por defecto 7 días)
    days = request.args.get('days', 7, type=int)

    # Obtener métricas avanzadas
    metrics = system.get_advanced_metrics(days=days)

    # Obtener horas pico
    peak_hours = system.get_peak_hours(days=days)

    # Obtener estadísticas por tipo de cita
    from sqlalchemy import func
    from datetime import timedelta

    start_date = now_utc_for_db() - timedelta(days=days)

    # Tickets por tipo en el período
    type_stats = db.session.query(
        TicketType.name,
        TicketType.color,
        func.count(Ticket.id).label('count'),
        func.avg(
            func.julianday(Ticket.completed_at) - func.julianday(Ticket.called_at)
        ).label('avg_service_minutes')
    ).join(Ticket).filter(
        Ticket.ticket_system_id == system.id,
        Ticket.created_at >= start_date,
        Ticket.status == 'completed'
    ).group_by(TicketType.id).all()

    type_statistics = []
    for stat in type_stats:
        avg_minutes = (stat.avg_service_minutes * 24 * 60) if stat.avg_service_minutes else 0
        type_statistics.append({
            'name': stat.name,
            'color': stat.color,
            'count': stat.count,
            'avg_service_time': round(avg_minutes, 1)
        })

    # Tendencias diarias (tickets por día)
    daily_tickets = db.session.query(
        func.date(Ticket.created_at).label('date'),
        func.count(Ticket.id).label('count')
    ).filter(
        Ticket.ticket_system_id == system.id,
        Ticket.created_at >= start_date
    ).group_by(func.date(Ticket.created_at)).order_by(func.date(Ticket.created_at)).all()

    daily_trend = [
        {
            'date': str(day.date),
            'count': day.count
        }
        for day in daily_tickets
    ]

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/tickets_metrics_pwa.html',
                              system=system,
                              metrics=metrics,
                              peak_hours=peak_hours,
                              type_statistics=type_statistics,
                              daily_trend=daily_trend,
                              days=days)
    else:
        return render_template('dashboard/tickets/metrics.html',
                              system=system,
                              metrics=metrics,
                              peak_hours=peak_hours,
                              type_statistics=type_statistics,
                              daily_trend=daily_trend,
                              days=days)

# ============================================================================
# SISTEMA DE CITAS - Rutas Dashboard para Gestión
# ============================================================================

@bp.route('/appointments')
@login_required
def appointments():
    """Panel principal de gestión de citas"""
    from ..models import Appointment
    from sqlalchemy import or_
    from datetime import date, timedelta

    # Obtener parámetro de vista (activas o historial)
    view = request.args.get('view', 'active')  # 'active' o 'history'
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status_filter = request.args.get('status', '')

    # Base query - todas las citas de las cards del usuario
    base_query = Appointment.query.join(Card).filter(Card.owner_id == current_user.id)

    # Separar entre vista activa e historial
    if view == 'history':
        # Vista de historial: citas completadas, canceladas o no show
        query = base_query.filter(Appointment.status.in_(['completed', 'cancelled', 'no_show']))

        # Filtros de historial
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        if date_from:
            query = query.filter(Appointment.appointment_date >= date_from)
        if date_to:
            query = query.filter(Appointment.appointment_date <= date_to)

        # Ordenar por fecha descendente (más recientes primero)
        appointments_list = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

    else:
        # Vista activa: solo citas pendientes y confirmadas
        query = base_query.filter(Appointment.status.in_(['pending', 'confirmed']))

        # Filtros de vista activa
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        if date_from:
            query = query.filter(Appointment.appointment_date >= date_from)
        if date_to:
            query = query.filter(Appointment.appointment_date <= date_to)

        # Ordenar por fecha ascendente (próximas primero)
        appointments_list = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    # Estadísticas globales
    today = date.today()
    all_appointments = Appointment.query.join(Card).filter(Card.owner_id == current_user.id)

    stats = {
        'total': all_appointments.count(),
        'pending': all_appointments.filter(Appointment.status == 'pending').count(),
        'confirmed': all_appointments.filter(Appointment.status == 'confirmed').count(),
        'today': all_appointments.filter(Appointment.appointment_date == today).count(),
        'active_count': all_appointments.filter(Appointment.status.in_(['pending', 'confirmed'])).count(),
        'history_count': all_appointments.filter(Appointment.status.in_(['completed', 'cancelled', 'no_show'])).count(),
    }

    # Detect device type from User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(keyword in user_agent for keyword in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])

    # Use PWA template for mobile devices, traditional template for desktop
    if is_mobile:
        return render_template('dashboard/appointments_pwa.html',
                              appointments=appointments_list,
                              stats=stats,
                              view=view,
                              status_filter=status_filter,
                              date_from=date_from,
                              date_to=date_to)
    else:
        return render_template('dashboard/appointments/index.html',
                              appointments=appointments_list,
                              stats=stats,
                              view=view,
                              status_filter=status_filter,
                              date_from=date_from,
                              date_to=date_to)

@bp.route('/appointments/<int:id>/confirm', methods=['POST'])
@login_required
def confirm_appointment(id):
    """Confirmar cita (AJAX)"""
    from ..models import Appointment

    appointment = Appointment.query.join(Card).filter(
        Appointment.id == id,
        Card.owner_id == current_user.id
    ).first_or_404()

    if appointment.status != 'pending':
        return jsonify({'success': False, 'message': f'Esta cita no se puede confirmar (estado: {appointment.status})'}), 400

    appointment.confirm()
    db.session.commit()

    # Enviar notificación push
    try:
        from ..push_notifications import send_appointment_notification
        send_appointment_notification(current_user.id, appointment, notification_type='confirmed')
    except Exception as e:
        # No fallar la confirmación si la notificación falla
        print(f"Failed to send confirmation notification: {e}")

    if request.is_json:
        return jsonify({'success': True, 'message': f'Cita #{appointment.id} confirmada'})
    else:
        flash(f'Cita confirmada exitosamente', 'success')
        return redirect(url_for('dashboard.appointments'))

@bp.route('/appointments/<int:id>/complete', methods=['POST'])
@login_required
def complete_appointment(id):
    """Completar cita (AJAX)"""
    try:
        from ..models import Appointment

        appointment = Appointment.query.join(Card).filter(
            Appointment.id == id,
            Card.owner_id == current_user.id
        ).first_or_404()

        if appointment.status not in ['pending', 'confirmed']:
            return jsonify({'success': False, 'message': f'Esta cita no se puede completar (estado: {appointment.status})'}), 400

        notes = request.json.get('notes', '') if request.is_json else request.form.get('notes', '')
        appointment.complete(notes)
        db.session.commit()

        if request.is_json:
            return jsonify({'success': True, 'message': f'Cita #{appointment.id} completada'})
        else:
            flash(f'Cita completada exitosamente', 'success')
            return redirect(url_for('dashboard.appointments'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error completing appointment {id}: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': f'Error al completar la cita: {str(e)}'}), 500
        else:
            flash(f'Error al completar la cita: {str(e)}', 'error')
            return redirect(url_for('dashboard.appointments'))

@bp.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    """Cancelar cita (AJAX)"""
    try:
        from ..models import Appointment

        appointment = Appointment.query.join(Card).filter(
            Appointment.id == id,
            Card.owner_id == current_user.id
        ).first_or_404()

        if appointment.status not in ['pending', 'confirmed']:
            return jsonify({'success': False, 'message': f'Esta cita no se puede cancelar (estado: {appointment.status})'}), 400

        reason = request.json.get('reason', '') if request.is_json else request.form.get('reason', '')
        appointment.cancel(reason)
        db.session.commit()

        if request.is_json:
            return jsonify({'success': True, 'message': f'Cita #{appointment.id} cancelada'})
        else:
            flash(f'Cita cancelada', 'info')
            return redirect(url_for('dashboard.appointments'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error canceling appointment {id}: {str(e)}')
        if request.is_json:
            return jsonify({'success': False, 'message': f'Error al cancelar la cita: {str(e)}'}), 500
        else:
            flash(f'Error al cancelar la cita: {str(e)}', 'error')
            return redirect(url_for('dashboard.appointments'))

@bp.route('/appointments/<int:id>/no-show', methods=['POST'])
@login_required
def appointment_no_show(id):
    """Marcar cliente como ausente (AJAX)"""
    from ..models import Appointment

    appointment = Appointment.query.join(Card).filter(
        Appointment.id == id,
        Card.owner_id == current_user.id
    ).first_or_404()

    if appointment.status not in ['pending', 'confirmed']:
        return jsonify({'success': False, 'message': f'Esta cita no se puede marcar como ausente (estado: {appointment.status})'}), 400

    appointment.mark_no_show()
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': f'Cita #{appointment.id} marcada como ausente'})
    else:
        flash(f'Cita marcada como ausente', 'info')
        return redirect(url_for('dashboard.appointments'))