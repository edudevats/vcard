from . import cache
from .models import Card


def clear_card_cache(card_id):
    """Clear all cache entries related to a specific card"""
    card = Card.query.get(card_id)
    if not card:
        return
    
    # Clear main card cache using slug
    try:
        cache.delete(f'card_data_{card.slug}')
        cache.delete(f'card_view_{card.slug}')
        
        # Clear related data cache
        cache.delete(f'card_services_{card_id}')
        cache.delete(f'card_products_{card_id}')
        cache.delete(f'card_gallery_{card_id}')
        cache.delete(f'card_featured_{card_id}')
        
        # Also try to clear with ID-based keys in case they exist
        cache.delete(f'card_data_{card_id}')
        cache.delete(f'card_view_{card_id}')
        
        # Cache cleared successfully
        pass
    except Exception as e:
        # Silent fail - don't break functionality if cache fails
        pass
    
    # Clear analytics cache (Flask-Caching doesn't have delete_many with patterns)
    # We'll need to manually track or use cache keys instead
    pass  # TODO: Implement pattern-based cache clearing if needed


def clear_user_cache(user_id):
    """Clear all cache entries for a user"""
    # Clear user's cards cache
    user_cards = Card.query.filter_by(owner_id=user_id).all()
    for card in user_cards:
        clear_card_cache(card.id)
    
    # Clear user analytics cache (Flask-Caching doesn't have delete_many with patterns)
    pass  # TODO: Implement pattern-based cache clearing if needed


def warm_card_cache(card_id):
    """Pre-warm cache for a card's data"""
    card = Card.query.get(card_id)
    if not card:
        return
    
    # Cache card data
    cache.set(f'card_data_{card.slug}', card, timeout=300)
    
    # Cache related data
    services = card.services.filter_by(is_visible=True).order_by('order_index').all()
    cache.set(f'card_services_{card_id}', services, timeout=600)
    
    products = card.products.filter_by(is_visible=True).order_by('order_index').all()
    cache.set(f'card_products_{card_id}', products, timeout=600)
    
    gallery_items = card.gallery_items.filter_by(is_visible=True).order_by('order_index').all()
    cache.set(f'card_gallery_{card_id}', gallery_items, timeout=600)
    
    featured_image = card.gallery_items.filter_by(is_featured=True, is_visible=True).first()
    cache.set(f'card_featured_{card_id}', featured_image, timeout=600)


class CacheManager:
    """Centralized cache management"""
    
    @staticmethod
    def invalidate_card(card_id):
        """Invalidate all caches related to a card"""
        clear_card_cache(card_id)
    
    @staticmethod
    def invalidate_user(user_id):
        """Invalidate all caches related to a user"""
        clear_user_cache(user_id)
    
    @staticmethod
    def warm_popular_cards(limit=10):
        """Pre-warm cache for most viewed cards"""
        try:
            from sqlalchemy import func
            from .models import CardView
            from . import db
            
            popular_cards = db.session.query(
                Card.id
            ).join(CardView).group_by(Card.id)\
             .order_by(func.count(CardView.id).desc())\
             .limit(limit).all()
            
            for card in popular_cards:
                warm_card_cache(card.id)
        except Exception as e:
            # Silent fail for cache warming
            pass
    
    @staticmethod
    def clear_expired():
        """Clear expired cache entries (implement based on cache backend)"""
        # This would depend on your cache backend
        # For simple cache, Flask-Caching handles this automatically
        pass
    
    @staticmethod
    def debug_cache_status(card_id):
        """Debug function to check cache status for a card"""
        card = Card.query.get(card_id)
        if not card:
            return f"Card {card_id} not found"
        
        cache_keys = [
            f'card_data_{card.slug}',
            f'card_view_{card.slug}',
            f'card_services_{card_id}',
            f'card_products_{card_id}',
            f'card_gallery_{card_id}',
            f'card_featured_{card_id}'
        ]
        
        status = {}
        for key in cache_keys:
            try:
                cached_value = cache.get(key)
                status[key] = 'HIT' if cached_value is not None else 'MISS'
            except Exception as e:
                status[key] = f'ERROR: {e}'
        
        return status