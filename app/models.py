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
    appointment_system = db.relationship('AppointmentSystem', backref='owner', uselist=False, cascade='all, delete-orphan')
    
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

class AppointmentSystem(db.Model):
    """Sistema de turnos/citas para consultorios - Un sistema por usuario"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)  # Controlado por admin
    business_name = db.Column(db.String(200))  # Nombre del consultorio
    welcome_message = db.Column(db.Text)  # Mensaje de bienvenida para pacientes
    business_hours = db.Column(db.String(500))  # Horario de atención
    max_appointment_types = db.Column(db.Integer, default=10)  # Límite de tipos de citas
    display_mode = db.Column(Enum('simple', 'detailed', name='display_modes'), default='simple')

    # Sistema de pausa
    is_accepting_appointments = db.Column(db.Boolean, default=True, nullable=False)  # Si está aceptando turnos
    pause_message = db.Column(db.Text)  # Mensaje cuando está pausado
    resume_time = db.Column(db.String(100))  # Hora de reanudación (ej: "14:00" o "Mañana a las 9:00")

    # Configuración de teléfono
    phone_country_prefix = db.Column(db.String(10), default='+52')  # Prefijo telefónico por defecto

    # Configuración de campos del formulario
    require_patient_phone = db.Column(db.Boolean, default=True, nullable=False)  # Siempre obligatorio
    require_patient_email = db.Column(db.Boolean, default=False, nullable=False)  # Email obligatorio
    collect_patient_birthdate = db.Column(db.Boolean, default=False, nullable=False)  # Recolectar fecha de nacimiento

    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    updated_at = db.Column(db.DateTime, default=now_utc_for_db, onupdate=now_utc_for_db)

    # Relationships
    appointment_types = db.relationship('AppointmentType', backref='system', lazy='dynamic', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='system', lazy='dynamic', cascade='all, delete-orphan')

    def can_add_type(self):
        """Verificar si puede agregar más tipos de citas"""
        return self.appointment_types.filter_by(is_active=True).count() < self.max_appointment_types

    def get_active_types(self):
        """Obtener tipos de citas activos ordenados"""
        return self.appointment_types.filter_by(is_active=True).order_by(AppointmentType.order_index).all()

    def get_waiting_count(self):
        """Obtener cantidad de turnos en espera"""
        return self.appointments.filter_by(status='waiting').count()

    def get_current_appointment(self):
        """Obtener turno actualmente en atención"""
        return self.appointments.filter_by(status='in_progress').first()

    def cleanup_old_appointments(self, days_old=7):
        """Limpiar turnos completados, cancelados y ausentes de hace X días"""
        from datetime import timedelta
        cutoff_date = now_utc_for_db() - timedelta(days=days_old)

        old_appointments = self.appointments.filter(
            Appointment.status.in_(['completed', 'cancelled', 'no_show']),
            Appointment.created_at < cutoff_date
        ).all()

        count = len(old_appointments)
        for appointment in old_appointments:
            db.session.delete(appointment)

        return count

    def reset_daily_queue(self):
        """Resetear cola diaria - cancelar todos los turnos en espera del día anterior"""
        today_start = today_start_utc()

        old_waiting = self.appointments.filter(
            Appointment.status == 'waiting',
            Appointment.created_at < today_start
        ).all()

        count = 0
        for appointment in old_waiting:
            appointment.cancel('Turno expirado - nuevo día')
            count += 1

        return count

    def get_daily_stats(self):
        """Obtener estadísticas del día actual"""
        today_start = today_start_utc()

        return {
            'total': self.appointments.filter(Appointment.created_at >= today_start).count(),
            'completed': self.appointments.filter(
                Appointment.status == 'completed',
                Appointment.created_at >= today_start
            ).count(),
            'waiting': self.appointments.filter_by(status='waiting').count(),
            'in_progress': self.appointments.filter_by(status='in_progress').count(),
            'cancelled': self.appointments.filter(
                Appointment.status == 'cancelled',
                Appointment.created_at >= today_start
            ).count(),
            'no_show': self.appointments.filter(
                Appointment.status == 'no_show',
                Appointment.created_at >= today_start
            ).count(),
        }

    def __repr__(self):
        return f'<AppointmentSystem user_id={self.user_id}>'

class AppointmentType(db.Model):
    """Tipos de citas configurables (1-10 por sistema)"""
    id = db.Column(db.Integer, primary_key=True)
    appointment_system_id = db.Column(db.Integer, db.ForeignKey('appointment_system.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # "Consulta General", "Inyecciones", etc.
    description = db.Column(db.String(500))
    color = db.Column(db.String(7), default='#6366f1')  # Color hex para identificación visual
    estimated_duration = db.Column(db.Integer, default=30)  # Duración estimada en minutos
    prefix = db.Column(db.String(5), default='A')  # Prefijo para números de ticket (A, B, C, etc.)
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=now_utc_for_db)

    # Relationships
    appointments = db.relationship('Appointment', backref='type', lazy='dynamic', cascade='all, delete-orphan')

    def get_next_ticket_number(self):
        """Generar siguiente número de ticket para este tipo"""
        # Obtener el último ticket del día
        today_start = today_start_utc()
        last_appointment = self.appointments.filter(
            Appointment.created_at >= today_start
        ).order_by(Appointment.created_at.desc()).first()

        if last_appointment and last_appointment.ticket_number:
            # Extraer número del ticket (ej: "A005" -> 5)
            try:
                last_num = int(last_appointment.ticket_number[len(self.prefix):])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        # Formatear con ceros (ej: "A001", "B023")
        return f"{self.prefix}{next_num:03d}"

    def get_waiting_count(self):
        """Cantidad de turnos en espera para este tipo"""
        return self.appointments.filter_by(status='waiting').count()

    def __repr__(self):
        return f'<AppointmentType {self.name}>'

class Appointment(db.Model):
    """Turno/Cita individual"""
    id = db.Column(db.Integer, primary_key=True)
    appointment_system_id = db.Column(db.Integer, db.ForeignKey('appointment_system.id'), nullable=False)
    appointment_type_id = db.Column(db.Integer, db.ForeignKey('appointment_type.id'), nullable=False)

    # Información del paciente
    patient_name = db.Column(db.String(200), nullable=False)
    patient_phone_country = db.Column(db.String(10))  # Prefijo del país (ej: +52)
    patient_phone = db.Column(db.String(20))  # Número sin prefijo
    patient_email = db.Column(db.String(120))
    patient_birthdate = db.Column(db.Date)  # Fecha de nacimiento

    # Control de turno
    ticket_number = db.Column(db.String(20), nullable=False, index=True)  # Ej: "A001", "B042"
    status = db.Column(
        Enum('waiting', 'in_progress', 'completed', 'cancelled', 'no_show', name='appointment_statuses'),
        default='waiting',
        nullable=False,
        index=True
    )

    # Timestamps
    created_at = db.Column(db.DateTime, default=now_utc_for_db, index=True)
    called_at = db.Column(db.DateTime)  # Cuando se llamó al paciente
    completed_at = db.Column(db.DateTime)  # Cuando se completó la atención
    cancelled_at = db.Column(db.DateTime)

    # Notas adicionales
    notes = db.Column(db.Text)
    cancellation_reason = db.Column(db.String(500))

    # Metadata
    ip_address = db.Column(db.String(45))  # IP del paciente al tomar turno
    user_agent = db.Column(db.String(500))

    def call(self):
        """Llamar al paciente (pasar a 'in_progress')"""
        self.status = 'in_progress'
        self.called_at = now_utc_for_db()

    def complete(self, notes=None):
        """Completar la atención"""
        self.status = 'completed'
        self.completed_at = now_utc_for_db()
        if notes:
            self.notes = notes

    def cancel(self, reason=None):
        """Cancelar el turno"""
        self.status = 'cancelled'
        self.cancelled_at = now_utc_for_db()
        if reason:
            self.cancellation_reason = reason

    def mark_no_show(self):
        """Marcar como ausente"""
        self.status = 'no_show'
        self.completed_at = now_utc_for_db()

    def get_waiting_time(self):
        """Obtener tiempo de espera en minutos"""
        if self.status == 'waiting':
            delta = now_utc_for_db() - self.created_at
            return int(delta.total_seconds() / 60)
        return 0

    def get_position_in_queue(self):
        """Obtener posición en la cola (considerando intercalado)"""
        if self.status != 'waiting':
            return 0

        # Contar turnos en espera creados antes de este
        waiting_before = Appointment.query.filter(
            Appointment.appointment_system_id == self.appointment_system_id,
            Appointment.status == 'waiting',
            Appointment.created_at < self.created_at
        ).count()

        return waiting_before + 1

    def get_local_created_at(self):
        """Obtener fecha de creación en hora local formateada"""
        from .timezone_utils import format_local_datetime
        return format_local_datetime(self.created_at, '%d/%m/%Y %H:%M')

    def get_full_phone(self):
        """Obtener número de teléfono completo con prefijo"""
        if not self.patient_phone:
            return None
        if self.patient_phone_country:
            return f"{self.patient_phone_country}{self.patient_phone}"
        return self.patient_phone

    def get_whatsapp_url(self, message=None):
        """Generar URL de WhatsApp para contactar al paciente"""
        phone = self.get_full_phone()
        if not phone:
            return None

        # Limpiar el número (remover espacios, guiones, etc.)
        clean_phone = ''.join(filter(str.isdigit, phone.replace('+', '')))

        # Mensaje predeterminado
        if not message:
            message = f"Hola {self.patient_name}, es tu turno. Por favor pasa a consulta."

        # URL encode del mensaje
        import urllib.parse
        encoded_message = urllib.parse.quote(message)

        return f"https://wa.me/{clean_phone}?text={encoded_message}"

    def __repr__(self):
        return f'<Appointment {self.ticket_number} - {self.status}>'

class PushSubscription(db.Model):
    """Push notification subscriptions for PWA users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.String(500), nullable=False)
    p256dh = db.Column(db.String(200), nullable=False)
    auth = db.Column(db.String(200), nullable=False)
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=now_utc_for_db)
    updated_at = db.Column(db.DateTime, default=now_utc_for_db, onupdate=now_utc_for_db)

    # Relationship
    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy='dynamic', cascade='all, delete-orphan'))

    # Unique constraint to prevent duplicate subscriptions
    __table_args__ = (db.UniqueConstraint('user_id', 'endpoint', name='unique_user_endpoint'),)

    def to_dict(self):
        """Convert subscription to dictionary for push sending"""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth
            }
        }

    def __repr__(self):
        return f'<PushSubscription user_id={self.user_id} endpoint={self.endpoint[:50]}...>'