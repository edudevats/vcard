from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from .security import hash_password, verify_password
from .timezone_utils import now_utc_for_db, today_start_utc, get_date_range_utc, get_month_range_utc
from sqlalchemy import Enum
import string
import secrets
from itsdangerous import URLSafeTimedSerializer

from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(Enum('admin', 'user', name='user_roles'), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer)
    is_suspended = db.Column(db.Boolean, default=False)
    suspension_reason = db.Column(db.String(500))
    suspended_at = db.Column(db.DateTime)
    suspended_by_id = db.Column(db.Integer)
    max_cards = db.Column(db.Integer, default=1, nullable=False)
    last_login = db.Column(db.DateTime)
    total_views = db.Column(db.Integer, default=0)
    email_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    reset_token = db.Column(db.String(255))
    reset_token_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    updated_at = db.Column(db.DateTime, default=now_utc_for_db, onupdate=now_utc_for_db)
    
    # Relationships
    cards = db.relationship('Card', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def normalize_email(self, email):
        """Normalize email to lowercase for case-insensitive comparison"""
        if email:
            return email.lower().strip()
        return email
    
    @staticmethod
    def find_by_email(email):
        """Find user by email (case-insensitive)"""
        if email:
            return User.query.filter_by(email=email.lower().strip()).first()
        return None
    
    def set_email(self, email):
        """Set email with automatic normalization"""
        self.email = self.normalize_email(email)
    
    def set_password(self, password):
        self.password_hash = hash_password(password)
    
    def check_password(self, password):
        return verify_password(password, self.password_hash)
    
    def can_create_card(self):
        return self.cards.count() < self.max_cards
    
    def is_admin(self):
        return self.role == 'admin'
    
    def approve(self, approved_by_user):
        """Approve user registration"""
        self.is_approved = True
        self.approved_at = now_utc_for_db()
        self.approved_by_id = approved_by_user.id if approved_by_user else None
        
    def is_pending_approval(self):
        """Check if user is pending approval"""
        return not self.is_approved and not self.is_suspended
    
    def suspend(self, reason, suspended_by_user):
        """Suspend user with reason"""
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspended_at = now_utc_for_db()
        self.suspended_by_id = suspended_by_user.id
        
        # Also mark all cards as not public
        for card in self.cards:
            card.is_public = False
    
    def unsuspend(self):
        """Remove user suspension"""
        self.is_suspended = False
        self.suspension_reason = None
        self.suspended_at = None
        self.suspended_by_id = None
    
    def generate_reset_token(self):
        """Generate password reset token"""
        from flask import current_app
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = now_utc_for_db() + timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify password reset token"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        if self.reset_token != token:
            return False
        if now_utc_for_db() > self.reset_token_expires:
            return False
        return True
    
    def clear_reset_token(self):
        """Clear password reset token"""
        self.reset_token = None
        self.reset_token_expires = None
    
    def verify_email(self):
        """Mark email as verified"""
        self.email_verified = True
        self.email_verified_at = now_utc_for_db()
    
    def get_total_card_views(self):
        """Get total views across all user's cards"""
        from .models import CardView
        return CardView.query.join(Card).filter(Card.owner_id == self.id).count()
    
    def get_active_cards_count(self):
        """Get count of public cards"""
        return self.cards.filter_by(is_public=True).count()
    
    def __repr__(self):
        return f'<User {self.email}>'

class Theme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template_name = db.Column(db.String(50), default='classic')  # template file name (classic, mobile, elegant, etc.)
    primary_color = db.Column(db.String(7), default='#6366f1')  # hex color
    secondary_color = db.Column(db.String(7), default='#8b5cf6')
    accent_color = db.Column(db.String(7), default='#ec4899')
    avatar_border_color = db.Column(db.String(7), default='#ffffff')  # avatar border color
    font_family = db.Column(db.String(100), default='Inter')
    layout = db.Column(Enum('classic', 'modern', 'minimal', name='theme_layouts'), default='modern')
    avatar_shape = db.Column(Enum('circle', 'rounded', 'square', 'rectangle', name='avatar_shapes'), default='circle')
    bg_image_path = db.Column(db.String(255))  # optional background image
    preview_image = db.Column(db.String(255))  # preview screenshot for theme selection
    is_active = db.Column(db.Boolean, default=True)  # admin can disable themes
    is_global = db.Column(db.Boolean, default=False)  # True for admin themes visible to all, False for personal themes
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # NULL for admin themes, user_id for personal themes
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    
    # Relationships
    cards = db.relationship('Card', backref='theme', lazy='dynamic')
    
    def get_template_path(self):
        """Get the template file path for this theme"""
        return f'public/themes/{self.template_name}.html'
    
    @staticmethod
    def get_available_themes_for_user(user):
        """Get themes available for a specific user"""
        if user.is_admin():
            # Admin can see all themes
            return Theme.query.filter_by(is_active=True).all()
        else:
            # Regular user can see global themes + their own themes
            return Theme.query.filter(
                db.and_(
                    Theme.is_active == True,
                    db.or_(
                        Theme.is_global == True,
                        Theme.created_by_id == user.id
                    )
                )
            ).all()
    
    def can_user_access(self, user):
        """Check if user can access this theme"""
        if user.is_admin():
            return True
        return self.is_global or self.created_by_id == user.id
    
    def is_personal(self):
        """Check if this is a personal theme"""
        return not self.is_global and self.created_by_id is not None
    
    def __repr__(self):
        return f'<Theme {self.name}>'

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200))  # e.g., "Lourdes Arellano - Salón & Spa"
    name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(200))
    company = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email_public = db.Column(db.String(120))
    website = db.Column(db.String(255))
    location = db.Column(db.String(255))
    bio = db.Column(db.Text)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    published_at = db.Column(db.DateTime)
    avatar_path = db.Column(db.String(255))  # Legacy - kept for backward compatibility
    avatar_square_path = db.Column(db.String(255))  # Square version for circle/rounded/square
    avatar_rect_path = db.Column(db.String(255))   # Rectangular version for rectangle shape
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    updated_at = db.Column(db.DateTime, default=now_utc_for_db, onupdate=now_utc_for_db)
    
    # Social media fields
    instagram = db.Column(db.String(255))
    whatsapp_country = db.Column(db.String(10))  # Country code for WhatsApp (e.g., '+34')
    whatsapp = db.Column(db.String(20))  # Phone number without country code
    custom_layout = db.Column(db.Text)  # Store custom layout JSON from visual editor
    facebook = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    youtube = db.Column(db.String(255))
    tiktok = db.Column(db.String(255))
    telegram = db.Column(db.String(255))
    snapchat = db.Column(db.String(255))
    pinterest = db.Column(db.String(255))
    github = db.Column(db.String(255))
    behance = db.Column(db.String(255))
    dribbble = db.Column(db.String(255))
    
    # Social network display preferences (JSON list of network field names to show as primary)
    primary_social_networks = db.Column(db.Text)
    
    # Relationships
    services = db.relationship('Service', backref='card', lazy='dynamic', cascade='all, delete-orphan')
    products = db.relationship('Product', backref='card', lazy='dynamic', cascade='all, delete-orphan')
    gallery_items = db.relationship('GalleryItem', backref='card', lazy='dynamic', cascade='all, delete-orphan')
    
    def generate_slug(self):
        """Generate a unique slug for the card"""
        base_slug = ''.join(c for c in self.name.lower().replace(' ', '-') if c.isalnum() or c == '-')
        # Add random suffix to ensure uniqueness
        suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        self.slug = f"{base_slug}-{suffix}"
        
        # Ensure uniqueness
        counter = 1
        original_slug = self.slug
        while Card.query.filter_by(slug=self.slug).first():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
    
    def publish(self):
        """Publish the card"""
        self.is_public = True
        self.published_at = now_utc_for_db()
        
        # Clear cache when publishing
        try:
            from .cache_utils import CacheManager
            CacheManager.invalidate_card(self.id)
        except:
            pass  # Don't fail if cache clearing fails
    
    def unpublish(self):
        """Unpublish the card"""
        self.is_public = False
        
        # Clear cache when unpublishing
        try:
            from .cache_utils import CacheManager
            CacheManager.invalidate_card(self.id)
        except:
            pass  # Don't fail if cache clearing fails
    
    def get_public_url(self):
        """Get the public URL for this card"""
        return f"/c/{self.slug}"
    
    def _clean_social_value(self, value, network_type):
        """Clean and normalize social network values"""
        if not value or not value.strip():
            return None
            
        value = value.strip()
        
        # Handle Instagram: remove @ if present
        if network_type == 'instagram':
            if value.startswith('@'):
                value = value[1:]
            # If it's a full URL, extract username
            if value.startswith(('http://', 'https://')):
                if 'instagram.com/' in value:
                    value = value.split('instagram.com/')[-1].rstrip('/')
            return value
            
        # Handle Facebook: extract username from URL if needed
        if network_type == 'facebook':
            if value.startswith(('http://', 'https://')):
                if 'facebook.com/' in value:
                    value = value.split('facebook.com/')[-1].rstrip('/')
            return value
            
        # Handle LinkedIn: extract username from URL if needed  
        if network_type == 'linkedin':
            if value.startswith(('http://', 'https://')):
                if 'linkedin.com/in/' in value:
                    value = value.split('linkedin.com/in/')[-1].rstrip('/')
                elif 'linkedin.com/' in value:
                    value = value.split('linkedin.com/')[-1].rstrip('/')
            return value
            
        # Handle X (Twitter): remove @ if present
        if network_type == 'twitter':
            if value.startswith('@'):
                value = value[1:]
            if value.startswith(('http://', 'https://')):
                if 'twitter.com/' in value:
                    value = value.split('twitter.com/')[-1].rstrip('/')
                elif 'x.com/' in value:
                    value = value.split('x.com/')[-1].rstrip('/')
            return value
            
        # For other networks, just clean URLs
        if value.startswith(('http://', 'https://')):
            return value  # Keep full URLs for other networks
            
        return value

    def get_social_networks(self, priority=None):
        """Get configured social networks with their info
        
        Args:
            priority (int, optional): Filter by priority (1 for primary, 2 for secondary)
        """
        from .constants import SOCIAL_NETWORKS, SOCIAL_NETWORKS_PRIMARY, SOCIAL_NETWORKS_SECONDARY
        
        # Choose source based on priority filter
        if priority == 1:
            networks_source = SOCIAL_NETWORKS_PRIMARY
        elif priority == 2:
            networks_source = SOCIAL_NETWORKS_SECONDARY
        else:
            networks_source = SOCIAL_NETWORKS
        
        social_networks = []
        for network in networks_source:
            field_name = network['field']
            
            # Handle special cases
            if field_name == 'whatsapp_business':
                value = self.get_whatsapp_full_number()
            elif field_name == 'website':
                value = self.website
            elif field_name == 'email_public':
                value = self.email_public
            elif hasattr(self, field_name):
                # Clean social values for known networks
                if field_name in ['instagram', 'facebook', 'linkedin', 'twitter']:
                    value = self._clean_social_value(getattr(self, field_name), field_name)
                else:
                    value = getattr(self, field_name)
            else:
                continue
                
            if value:  # Only add networks with values
                social_networks.append({
                    'name': network['name'],
                    'value': value,
                    'icon': network['icon'],
                    'color': network['color'],
                    'base_url': network['base_url'],
                    'priority': network.get('priority', 1)
                })
        
        return social_networks
    
    def get_social_networks_by_preference(self, is_primary=True):
        """Get social networks based on user preferences
        
        Args:
            is_primary (bool): True for primary networks, False for secondary
        """
        import json
        from .constants import SOCIAL_NETWORKS
        
        # Get user's preferred primary networks from stored preferences
        primary_fields = []
        if self.primary_social_networks:
            try:
                primary_fields = json.loads(self.primary_social_networks)
            except (json.JSONDecodeError, TypeError):
                primary_fields = []
        
        # If no preferences set, use default primary networks
        if not primary_fields:
            primary_fields = ['instagram', 'facebook', 'whatsapp_business', 'email_public', 'linkedin', 'twitter', 'youtube']
        
        social_networks = []
        for network in SOCIAL_NETWORKS:
            field_name = network['field']
            
            # Determine if this network should be shown based on preference
            is_network_primary = field_name in primary_fields
            if is_primary != is_network_primary:
                continue  # Skip if doesn't match requested type
            
            # Handle special cases for value retrieval
            if field_name == 'whatsapp_business':
                value = self.get_whatsapp_full_number()
            elif field_name == 'website':
                value = self.website
            elif field_name == 'email_public':
                value = self.email_public
            elif hasattr(self, field_name):
                # Clean social values for known networks
                if field_name in ['instagram', 'facebook', 'linkedin', 'twitter']:
                    value = self._clean_social_value(getattr(self, field_name), field_name)
                else:
                    value = getattr(self, field_name)
            else:
                continue
                
            if value:  # Only add networks with values
                social_networks.append({
                    'name': network['name'],
                    'value': value,
                    'icon': network['icon'],
                    'color': network['color'],
                    'base_url': network['base_url'],
                    'field': field_name,
                    'priority': 1 if is_primary else 2
                })
        
        return social_networks
    
    def set_primary_social_networks(self, network_fields):
        """Set which social networks should be displayed as primary
        
        Args:
            network_fields (list): List of field names to show as primary
        """
        import json
        if isinstance(network_fields, list):
            self.primary_social_networks = json.dumps(network_fields)
        else:
            self.primary_social_networks = None
    
    def get_primary_social_network_fields(self):
        """Get list of field names configured as primary"""
        import json
        if self.primary_social_networks:
            try:
                return json.loads(self.primary_social_networks)
            except (json.JSONDecodeError, TypeError):
                return []
        # Default primary networks
        return ['instagram', 'facebook', 'whatsapp_business', 'email_public', 'linkedin', 'twitter', 'youtube']
    
    def get_available_social_networks(self):
        """Get all available social networks with their current values"""
        from .constants import SOCIAL_NETWORKS
        
        networks = []
        for network in SOCIAL_NETWORKS:
            field_name = network['field']
            
            # Get current value
            if field_name == 'whatsapp_business':
                value = self.get_whatsapp_full_number()
            elif field_name == 'website':
                value = self.website
            elif field_name == 'email_public':
                value = self.email_public
            elif hasattr(self, field_name):
                if field_name in ['instagram', 'facebook', 'linkedin', 'twitter']:
                    value = self._clean_social_value(getattr(self, field_name), field_name)
                else:
                    value = getattr(self, field_name)
            else:
                value = None
                
            networks.append({
                'field': field_name,
                'name': network['name'],
                'icon': network['icon'],
                'color': network['color'],
                'has_value': bool(value),
                'value': value
            })
        
        return networks
    
    def get_primary_social_networks(self):
        """Get user-customized primary social networks"""
        return self.get_social_networks_by_preference(is_primary=True)
    
    def get_secondary_social_networks(self):
        """Get user-customized secondary social networks"""
        return self.get_social_networks_by_preference(is_primary=False)
    
    def get_total_views(self):
        """Get total number of views for this card"""
        return self.views.count()
    
    def get_unique_views(self):
        """Get number of unique IP addresses that viewed this card"""
        from sqlalchemy import func
        return db.session.query(func.count(func.distinct(CardView.ip_address))).filter_by(card_id=self.id).scalar() or 0
    
    def get_views_today(self):
        """Get views for today"""
        start_utc, end_utc = get_date_range_utc(days=1)
        return self.views.filter(
            CardView.viewed_at >= start_utc,
            CardView.viewed_at <= end_utc
        ).count()
    
    def get_views_this_month(self):
        """Get views for current month"""
        start_utc, end_utc = get_month_range_utc()
        return self.views.filter(
            CardView.viewed_at >= start_utc,
            CardView.viewed_at <= end_utc
        ).count()
    
    def get_avatar_path(self):
        """Get the appropriate avatar path based on theme shape"""
        if not self.theme:
            # Fallback to legacy avatar_path or square version
            return self.avatar_path or self.avatar_square_path
        
        if self.theme.avatar_shape == 'rectangle':
            # Use rectangular version for rectangle shape
            return self.avatar_rect_path or self.avatar_square_path or self.avatar_path
        else:
            # Use square version for circle, rounded, square shapes
            return self.avatar_square_path or self.avatar_path or self.avatar_rect_path
    
    def get_avatar_url_with_cache_busting(self):
        """Get avatar URL with cache busting parameter"""
        from flask import url_for
        import time
        
        avatar_path = self.get_avatar_path()
        if not avatar_path:
            return None
        
        # Use updated_at timestamp as cache busting parameter
        timestamp = int(self.updated_at.timestamp()) if self.updated_at else int(time.time())
        return url_for('static', filename=f'uploads/{avatar_path}', v=timestamp)
    
    def has_avatar(self):
        """Check if card has any avatar version"""
        return bool(self.avatar_square_path or self.avatar_rect_path or self.avatar_path)
    
    def get_whatsapp_full_number(self):
        """Get complete WhatsApp number with country code"""
        if not self.whatsapp or not self.whatsapp_country:
            return None
        
        # Clean the phone number (remove spaces, dashes, etc.)
        clean_number = ''.join(filter(str.isdigit, self.whatsapp))
        if not clean_number:
            return None
            
        # Combine country code with clean number
        return self.whatsapp_country + clean_number
    
    def __repr__(self):
        return f'<Card {self.name} ({self.slug})>'

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price_from = db.Column(db.Numeric(10, 2))  # optional starting price
    icon = db.Column(db.String(50))  # icon class or name
    image_path = db.Column(db.String(255))  # service image
    category = db.Column(db.String(100))  # service category
    duration_minutes = db.Column(db.Integer)  # duration in minutes
    is_featured = db.Column(db.Boolean, default=False)  # featured/popular service
    availability = db.Column(db.String(200))  # availability description
    order_index = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    
    def get_duration_display(self):
        """Convert minutes to human readable format"""
        if not self.duration_minutes:
            return None
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours and minutes:
            return f"{hours}h {minutes}min"
        elif hours:
            return f"{hours}h"
        else:
            return f"{minutes}min"
    
    def __repr__(self):
        return f'<Service {self.title}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum('service', 'product', name='category_types'), nullable=False)
    description = db.Column(db.String(255))
    color = db.Column(db.String(7), default='#6c757d')  # hex color
    icon = db.Column(db.String(50))  # font awesome icon
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    
    # Unique constraint to prevent duplicate categories per user and type
    __table_args__ = (db.UniqueConstraint('user_id', 'name', 'type', name='unique_user_category'),)
    
    @staticmethod
    def get_or_create(user_id, name, category_type):
        """Get existing category or create new one"""
        category = Category.query.filter_by(
            user_id=user_id, 
            name=name, 
            type=category_type
        ).first()
        
        if not category:
            category = Category(
                user_id=user_id,
                name=name,
                type=category_type
            )
            db.session.add(category)
            db.session.flush()  # Get the ID without committing
        
        return category
    
    def __repr__(self):
        return f'<Category {self.name} ({self.type})>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))  # product price
    original_price = db.Column(db.Numeric(10, 2))  # optional original price for discounts
    image_path = db.Column(db.String(255))  # product image
    category = db.Column(db.String(100))  # product category
    brand = db.Column(db.String(100))  # product brand
    sku = db.Column(db.String(100))  # product SKU/code
    stock_quantity = db.Column(db.Integer)  # stock quantity (-1 for unlimited)
    is_featured = db.Column(db.Boolean, default=False)  # featured product
    is_available = db.Column(db.Boolean, default=True)  # product availability
    external_link = db.Column(db.String(500))  # link to buy/more info
    order_index = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    
    def has_discount(self):
        """Check if product has a discount"""
        return self.original_price and self.price and self.original_price > self.price
    
    def get_discount_percentage(self):
        """Calculate discount percentage"""
        if self.has_discount():
            return round(((self.original_price - self.price) / self.original_price) * 100)
        return 0
    
    def is_in_stock(self):
        """Check if product is in stock"""
        if self.stock_quantity is None or self.stock_quantity == -1:
            return True  # Unlimited stock
        return self.stock_quantity > 0
    
    def get_stock_status(self):
        """Get stock status text"""
        if not self.is_available:
            return "No disponible"
        if self.stock_quantity is None or self.stock_quantity == -1:
            return "Disponible"
        if self.stock_quantity == 0:
            return "Agotado"
        elif self.stock_quantity < 5:
            return f"Pocas unidades ({self.stock_quantity})"
        else:
            return f"En stock ({self.stock_quantity})"
    
    def __repr__(self):
        return f'<Product {self.name}>'

class GalleryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    caption = db.Column(db.String(500))
    order_index = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # featured image for card preview
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    
    def __repr__(self):
        return f'<GalleryItem {self.image_path}>'

class CardView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    referrer = db.Column(db.String(500))
    device_type = db.Column(db.String(20))  # mobile, tablet, desktop
    browser = db.Column(db.String(50))  # Chrome, Firefox, Safari, etc.
    platform = db.Column(db.String(50))  # windows, macos, linux, android, ios
    country = db.Column(db.String(100))  # User's country
    city = db.Column(db.String(100))  # User's city
    session_id = db.Column(db.String(100))  # Session tracking
    viewed_at = db.Column(db.DateTime, default=now_utc_for_db, index=True)
    
    # Relationship
    card = db.relationship('Card', backref=db.backref('views', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<CardView {self.card_id} at {self.viewed_at}>'