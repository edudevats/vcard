from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, make_response, abort
from flask_wtf.csrf import validate_csrf
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func
from ..models import Card, Service, Product, GalleryItem, Theme, CardView
from .. import db, cache
from . import bp
from .forms import CardForm, ServiceForm, ProductForm, GalleryUploadForm, AvatarUploadForm, ThemeCustomizationForm, ChangePasswordForm
from ..utils import save_image, save_avatar, delete_file, generate_styled_qr_code, generate_qr_code, generate_qr_code_with_logo, generate_qr_code_with_logo_themed, qr_to_base64, save_qr_code, admin_required, get_user_card_or_404, cleanup_files
from ..analytics import AnalyticsService, get_analytics_summary
from ..cache_utils import CacheManager
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
    
    return render_template('dashboard/index.html', cards=cards, stats=stats)

@bp.route('/cards/new', methods=['GET', 'POST'])
@login_required
def new_card():
    if not current_user.can_create_card():
        flash(f'Has alcanzado el límite de {current_user.max_cards} tarjetas. Contacta al administrador para incrementar tu límite.', 'error')
        return redirect(url_for('dashboard.index'))
    
    form = CardForm()
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
            theme_id=form.theme_id.data,
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
        
        flash('¡Tarjeta creada exitosamente!', 'success')
        return redirect(url_for('dashboard.edit_card', id=card.id))
    
    return render_template('dashboard/card_form.html', form=form, title='Nueva Tarjeta')

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
        
        service = Service(
            card_id=card.id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data if form.category.data else None,
            price_from=form.price_from.data,
            duration_minutes=parse_duration_to_minutes(form.duration_minutes.data),
            availability=form.availability.data,
            icon=form.icon.data,
            image_path=image_path,
            is_featured=form.is_featured.data,
            is_visible=form.is_visible.data,
            order_index=next_order
        )
        db.session.add(service)
        db.session.commit()
        
        # Clear cache for the parent card
        CacheManager.invalidate_card(card.id)
        
        flash('¡Servicio agregado exitosamente!', 'success')
        return redirect(url_for('dashboard.card_services', id=card.id))
    
    services = card.services.order_by(Service.order_index).all()
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
        
        service.title = form.title.data
        service.description = form.description.data
        service.category = form.category.data if form.category.data else None
        service.price_from = form.price_from.data
        service.duration_minutes = parse_duration_to_minutes(form.duration_minutes.data)
        service.availability = form.availability.data
        service.icon = form.icon.data
        service.is_featured = form.is_featured.data
        service.is_visible = form.is_visible.data
        
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

@bp.route('/cards/<int:id>/avatar', methods=['GET', 'POST'])
@login_required
def card_avatar(id):
    card = get_user_card_or_404(id)
    
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
            card.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Clear cache for this card
            CacheManager.invalidate_card(card.id)
            
            flash('¡Avatar actualizado exitosamente! Se crearon versiones optimizadas para todas las formas.', 'success')
        else:
            flash('Error al subir el avatar. Intenta de nuevo.', 'error')
        
        return redirect(url_for('dashboard.card_avatar', id=card.id))
    
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
        product = Product(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
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
            filename = save_image(form.image.data, 'products')
            if filename:
                product.image_path = filename
        
        db.session.add(product)
        db.session.commit()
        
        # Clear cache for the parent card
        CacheManager.invalidate_card(card.id)
        
        flash('Producto agregado correctamente', 'success')
        return redirect(url_for('dashboard.card_products', id=card.id))
    
    return render_template('dashboard/products.html', card=card, products=products, form=form)

@bp.route('/cards/<int:card_id>/products/<int:product_id>/edit')
@login_required
def edit_product(card_id, product_id):
    card = get_user_card_or_404(card_id)
    product = Product.query.filter_by(id=product_id, card_id=card_id).first_or_404()
    
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.category = form.category.data
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
            
            filename = save_image(form.image.data, 'products')
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
            CardView.viewed_at >= datetime.utcnow() - timedelta(days=days)
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
        prev_period_start = datetime.utcnow() - timedelta(days=days*2)
        prev_period_end = datetime.utcnow() - timedelta(days=days)
        
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
        'daily_views': [{'date': date, 'views': views} for date, views in sorted(all_daily_views.items())],
        'device_stats': [{'device': device, 'count': count} for device, count in all_device_stats.items()],
        'browser_stats': [{'browser': browser, 'count': count} for browser, count in all_browser_stats.items()],
        'location_stats': [{'country': country, 'count': count} for country, count in sorted(all_location_stats.items(), key=lambda x: x[1], reverse=True)[:10]],
        'hourly_stats': [{'hour': hour, 'count': all_hourly_stats.get(hour, 0)} for hour in range(24)]
    }
    
    return render_template('dashboard/analytics.html', 
                         analytics=aggregated_analytics, 
                         growth_rate=growth_rate,
                         cards_data=analytics_data['cards_analytics'],
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
            CardView.viewed_at >= datetime.utcnow() - timedelta(days=days)
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
    
    # Calculate growth rate
    prev_period_start = datetime.utcnow() - timedelta(days=days*2)
    prev_period_end = datetime.utcnow() - timedelta(days=days)
    
    card_ids = [card['card_id'] for card in analytics_data['cards_analytics']]
    prev_period_views = 0
    if card_ids:
        prev_period_views = CardView.query.filter(
            CardView.card_id.in_(card_ids),
            CardView.viewed_at >= prev_period_start,
            CardView.viewed_at < prev_period_end
        ).count()
    
    growth_rate = 0
    if prev_period_views > 0:
        growth_rate = ((analytics_data['period_views'] - prev_period_views) / prev_period_views) * 100
    
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
    response.headers['Content-Disposition'] = f'attachment; filename="analytics_{datetime.now().strftime("%Y%m%d")}.csv"'
    
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
        'export_date': datetime.utcnow().isoformat()
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
    response.headers['Content-Disposition'] = f'attachment; filename="full_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile and password change"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('La contraseña actual es incorrecta.', 'error')
            return redirect(url_for('dashboard.profile'))
        
        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('¡Contraseña cambiada exitosamente!', 'success')
        return redirect(url_for('dashboard.profile'))
    
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