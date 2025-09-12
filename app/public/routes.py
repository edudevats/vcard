from flask import render_template, abort, request
from ..models import Card, Product, CardView
from .. import db, cache
from . import bp
from ..analytics import AnalyticsService

def record_view(card):
    """Record a view for the given card with enhanced analytics"""
    view = AnalyticsService.track_card_view(card, request)
    db.session.add(view)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

@bp.route('/c/<slug>')
@cache.cached(timeout=300, key_prefix='card_view_%s')
def card_view(slug):
    # Use cached query for better performance
    cache_key = f'card_data_{slug}'
    card = cache.get(cache_key)
    
    if not card:
        card = Card.query.filter_by(slug=slug).first()
        if card and card.is_public and not card.owner.is_suspended:
            cache.set(cache_key, card, timeout=300)  # Cache for 5 minutes
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    # Record the view (don't cache this part)
    record_view(card)
    
    # Cache queries for related data
    services_key = f'card_services_{card.id}'
    services = cache.get(services_key)
    if not services:
        services = card.services.filter_by(is_visible=True).order_by('order_index').all()
        cache.set(services_key, services, timeout=600)
    
    products_key = f'card_products_{card.id}'
    products = cache.get(products_key)
    if not products:
        products = card.products.filter_by(is_visible=True).order_by('order_index').all()
        cache.set(products_key, products, timeout=600)
    
    gallery_key = f'card_gallery_{card.id}'
    gallery_items = cache.get(gallery_key)
    if not gallery_items:
        gallery_items = card.gallery_items.filter_by(is_visible=True).order_by('order_index').all()
        cache.set(gallery_key, gallery_items, timeout=600)
    
    featured_key = f'card_featured_{card.id}'
    featured_image = cache.get(featured_key)
    if featured_image is None:  # Use None check because False is valid
        featured_image = card.gallery_items.filter_by(is_featured=True, is_visible=True).first()
        cache.set(featured_key, featured_image, timeout=600)
    
    # Get social networks for the card
    social_links = card.get_primary_social_networks()
    
    # Get the theme template path
    template_path = card.theme.get_template_path() if card.theme else 'public/themes/classic.html'
    
    # Fallback to classic if template doesn't exist
    try:
        return render_template(template_path, 
                             card=card, 
                             services=services,
                             products=products, 
                             gallery_items=gallery_items,
                             featured_image=featured_image,
                             social_links=social_links)
    except:
        return render_template('public/themes/classic.html', 
                             card=card, 
                             services=services,
                             products=products, 
                             gallery_items=gallery_items,
                             featured_image=featured_image,
                             social_links=social_links)

@bp.route('/c/<slug>/services')
def card_services(slug):
    card = Card.query.filter_by(slug=slug).first()
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    services = card.services.filter_by(is_visible=True).order_by('order_index').all()
    
    return render_template('public/services.html', 
                         card=card, 
                         services=services)

@bp.route('/c/<slug>/gallery')
def card_gallery(slug):
    card = Card.query.filter_by(slug=slug).first()
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    gallery_items = card.gallery_items.filter_by(is_visible=True).order_by('order_index').all()
    
    return render_template('public/gallery.html',
                         card=card,
                         gallery_items=gallery_items)

@bp.route('/c/<slug>/productos')
def card_products(slug):
    card = Card.query.filter_by(slug=slug).first()
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    products = card.products.filter_by(is_visible=True).order_by(Product.order_index.asc(), Product.created_at.desc()).all()
    
    return render_template('public/products.html',
                         card=card,
                         products=products)


@bp.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html')

@bp.route('/share-target', methods=['GET', 'POST'])
def share_target():
    """PWA Share Target API handler"""
    from flask import redirect, url_for, session
    from flask_login import current_user
    
    if not current_user.is_authenticated:
        # Store shared content in session and redirect to login
        if request.method == 'POST':
            session['shared_content'] = {
                'title': request.form.get('title', ''),
                'text': request.form.get('text', ''),
                'url': request.form.get('url', ''),
                'files': request.files.getlist('files') if 'files' in request.files else []
            }
        return redirect(url_for('auth.login') + '?next=' + url_for('dashboard.new_card') + '&shared=true')
    
    if request.method == 'POST':
        # Handle shared content
        shared_title = request.form.get('title', '')
        shared_text = request.form.get('text', '')
        shared_url = request.form.get('url', '')
        shared_files = request.files.getlist('files') if 'files' in request.files else []
        
        # Store in session for use in new card creation
        session['shared_content'] = {
            'title': shared_title,
            'text': shared_text,
            'url': shared_url,
            'files': shared_files
        }
        
        return redirect(url_for('dashboard.new_card', shared='true'))
    
    # GET request - redirect to dashboard
    return redirect(url_for('dashboard.index', shared='true'))


@bp.route('/pwa-test')
def pwa_test():
    """PWA functionality test page"""
    return render_template('pwa_test.html')