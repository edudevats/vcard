#!/usr/bin/env python
"""
Script to update existing themes with new template_name field
"""
from app import create_app, db
from app.models import Theme

def update_existing_themes():
    app = create_app()
    
    with app.app_context():
        themes = Theme.query.all()
        
        for theme in themes:
            # Set template_name to 'classic' if it's None or empty
            if not theme.template_name:
                theme.template_name = 'classic'
                print(f"Updated theme '{theme.name}' with template_name='classic'")
            
            # Set is_active to True if it's None
            if theme.is_active is None:
                theme.is_active = True
                print(f"Updated theme '{theme.name}' with is_active=True")
        
        db.session.commit()
        print(f"Successfully updated {len(themes)} themes!")

if __name__ == "__main__":
    update_existing_themes()