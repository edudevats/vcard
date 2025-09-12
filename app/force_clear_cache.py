#!/usr/bin/env python3
"""
Script para forzar la limpieza de caché de una tarjeta específica
"""

def create_clear_cache_route():
    """Crea una ruta para limpiar caché forzadamente"""
    
    route_code = '''
@bp.route('/force-clear-cache/<slug>')
def force_clear_cache(slug):
    """Force clear all cache for a specific card"""
    card = Card.query.filter_by(slug=slug).first()
    if not card:
        return f"Card with slug '{slug}' not found"
    
    # Force clear cache multiple times
    from ..cache_utils import CacheManager
    
    # Clear card cache
    CacheManager.invalidate_card(card.id)
    
    # Clear specific cache keys
    from .. import cache
    cache_keys_to_clear = [
        f'card_data_{card.slug}',
        f'card_view_{card.slug}',
        f'card_{card.id}',
        f'theme_{card.theme_id}' if card.theme else None
    ]
    
    cleared_keys = []
    for key in cache_keys_to_clear:
        if key:
            try:
                cache.delete(key)
                cleared_keys.append(key)
            except:
                pass
    
    return f"""
    <h2>Cache Cleared for Card: {card.name}</h2>
    <p>Card ID: {card.id}</p>
    <p>Slug: {card.slug}</p>
    <p>Theme: {card.theme.template_name if card.theme else 'None'}</p>
    <p>Cleared keys: {cleared_keys}</p>
    <hr>
    <p><a href="/card/{slug}?v={card.id}">View Card (cache-busted)</a></p>
    <p><a href="/debug-template/{slug}">Debug Info</a></p>
    """
'''
    
    print("Add this route to public/routes.py:")
    print(route_code)

if __name__ == "__main__":
    create_clear_cache_route()