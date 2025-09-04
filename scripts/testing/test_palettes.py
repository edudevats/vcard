#!/usr/bin/env python
"""
Test script for color palettes system
"""
from app import create_app
from app.color_palettes import get_all_palettes, get_palette

def test_palettes():
    app = create_app()
    
    with app.app_context():
        # Test palette loading
        palettes = get_all_palettes()
        print(f"[OK] Loaded {len(palettes)} color palettes")
        
        # Test specific palette
        business_palette = get_palette('business')
        print(f"[OK] Business palette: {business_palette['name']}")
        print(f"   Primary: {business_palette['primary_color']}")
        print(f"   Secondary: {business_palette['secondary_color']}")
        print(f"   Accent: {business_palette['accent_color']}")
        
        # Test non-existent palette
        invalid_palette = get_palette('nonexistent')
        print(f"[OK] Invalid palette returns: {invalid_palette}")
        
        print("\nAll palettes:")
        for key, palette in palettes.items():
            print(f"   {key}: {palette['name']} - {palette['description']}")

if __name__ == "__main__":
    test_palettes()