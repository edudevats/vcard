#!/usr/bin/env python
"""
Script to create default themes for the ATScard application
Run this after applying migrations to populate the database with default themes
"""
from app import create_app, db
from app.models import Theme

def create_default_themes():
    app = create_app()
    
    with app.app_context():
        # Check if themes already exist
        if Theme.query.count() > 0:
            print("Themes already exist, skipping...")
            return
        
        # Theme 1: Classic Professional
        classic = Theme(
            name="Clásico Profesional",
            template_name="classic",
            primary_color="#6366f1",
            secondary_color="#8b5cf6",
            accent_color="#ec4899",
            font_family="Inter",
            layout="modern",
            avatar_shape="circle",
            is_active=True
        )
        
        # Theme 2: Mobile First
        mobile = Theme(
            name="Móvil Moderno",
            template_name="mobile",
            primary_color="#1173d4",
            secondary_color="#d4e7f9",
            accent_color="#88bde8",
            font_family="Inter",
            layout="minimal",
            avatar_shape="circle",
            is_active=True
        )
        
        # Theme 3: Elegant Dark (using classic template but with dark colors)
        elegant = Theme(
            name="Elegante Oscuro",
            template_name="classic",
            primary_color="#1f2937",
            secondary_color="#374151",
            accent_color="#10b981",
            font_family="Playfair Display",
            layout="classic",
            avatar_shape="rounded",
            is_active=True
        )
        
        # Theme 4: Colorful Modern (using mobile template)
        colorful = Theme(
            name="Colorido Moderno",
            template_name="mobile",
            primary_color="#7c3aed",
            secondary_color="#a78bfa",
            accent_color="#f59e0b",
            font_family="Poppins",
            layout="modern",
            avatar_shape="square",
            is_active=True
        )
        
        # Theme 5: Minimalist (using classic template)
        minimalist = Theme(
            name="Minimalista",
            template_name="classic",
            primary_color="#000000",
            secondary_color="#f3f4f6",
            accent_color="#ef4444",
            font_family="Roboto",
            layout="minimal",
            avatar_shape="square",
            is_active=True
        )
        
        themes = [classic, mobile, elegant, colorful, minimalist]
        
        for theme in themes:
            db.session.add(theme)
            print(f"Created theme: {theme.name}")
        
        db.session.commit()
        print(f"Successfully created {len(themes)} default themes!")

if __name__ == "__main__":
    create_default_themes()