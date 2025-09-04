#!/usr/bin/env python
"""
Script to add mobile themes to the database
"""
from app import create_app, db
from app.models import Theme

def add_mobile_themes():
    app = create_app()
    
    with app.app_context():
        # Check if mobile theme already exists
        mobile_theme = Theme.query.filter_by(template_name='mobile').first()
        if mobile_theme:
            print("Mobile theme already exists, skipping...")
            return
        
        # Mobile Modern Theme (your design)
        mobile_modern = Theme(
            name="Móvil Moderno",
            template_name="mobile",
            primary_color="#1173d4",
            secondary_color="#d4e7f9", 
            accent_color="#88bde8",
            font_family="Inter",
            layout="modern",
            avatar_shape="circle",
            is_active=True
        )
        
        # Mobile Dark Theme
        mobile_dark = Theme(
            name="Móvil Oscuro",
            template_name="mobile",
            primary_color="#1f2937",
            secondary_color="#374151",
            accent_color="#10b981",
            font_family="Inter",
            layout="minimal",
            avatar_shape="rounded",
            is_active=True
        )
        
        # Mobile Colorful Theme
        mobile_colorful = Theme(
            name="Móvil Colorido",
            template_name="mobile",
            primary_color="#7c3aed",
            secondary_color="#a78bfa",
            accent_color="#f59e0b",
            font_family="Poppins",
            layout="modern",
            avatar_shape="square",
            is_active=True
        )
        
        themes = [mobile_modern, mobile_dark, mobile_colorful]
        
        for theme in themes:
            db.session.add(theme)
            print(f"Created mobile theme: {theme.name}")
        
        db.session.commit()
        print(f"Successfully created {len(themes)} mobile themes!")

if __name__ == "__main__":
    add_mobile_themes()