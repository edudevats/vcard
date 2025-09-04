#!/usr/bin/env python
"""
Script to create global themes with different templates and presets
"""
from app import create_app, db
from app.models import Theme

def create_global_themes():
    app = create_app()
    
    with app.app_context():
        # Classic template themes
        classic_business = Theme(
            name="Ejecutivo Clásico",
            template_name="classic",
            primary_color="#1e40af",
            secondary_color="#3b82f6", 
            accent_color="#60a5fa",
            font_family="Inter",
            layout="classic",
            avatar_shape="circle",
            is_global=True,
            created_by_id=None
        )
        
        classic_creative = Theme(
            name="Creativo Clásico",
            template_name="classic",
            primary_color="#7c3aed",
            secondary_color="#a855f7",
            accent_color="#c084fc",
            font_family="Poppins",
            layout="modern",
            avatar_shape="rounded",
            is_global=True,
            created_by_id=None
        )
        
        # Business template themes
        business_corporate = Theme(
            name="Corporativo",
            template_name="business",
            primary_color="#1f2937",
            secondary_color="#374151",
            accent_color="#6b7280",
            font_family="Inter",
            layout="classic",
            avatar_shape="rectangle",
            is_global=True,
            created_by_id=None
        )
        
        business_startup = Theme(
            name="Startup",
            template_name="business",
            primary_color="#7c3aed",
            secondary_color="#8b5cf6",
            accent_color="#a78bfa",
            font_family="Inter",
            layout="geometric",
            avatar_shape="circle",
            is_global=True,
            created_by_id=None
        )
        
        business_consultant = Theme(
            name="Consultor Profesional",
            template_name="business",
            primary_color="#0369a1",
            secondary_color="#0284c7",
            accent_color="#0ea5e9",
            font_family="Inter",
            layout="elegant",
            avatar_shape="circle",
            is_global=True,
            created_by_id=None
        )
        
        business_luxury = Theme(
            name="Lujo Premium",
            template_name="business",
            primary_color="#7c2d12",
            secondary_color="#991b1b",
            accent_color="#dc2626",
            font_family="Playfair Display",
            layout="elegant",
            avatar_shape="circle",
            is_global=True,
            created_by_id=None
        )
        
        # Add all themes
        themes_to_add = [
            classic_business,
            classic_creative,
            business_corporate,
            business_startup,
            business_consultant,
            business_luxury
        ]
        
        for theme in themes_to_add:
            # Check if theme already exists
            existing = Theme.query.filter_by(name=theme.name).first()
            if not existing:
                db.session.add(theme)
                print(f"Created theme: {theme.name}")
            else:
                print(f"Theme already exists: {theme.name}")
        
        db.session.commit()
        print("Global themes created successfully!")

if __name__ == "__main__":
    create_global_themes()