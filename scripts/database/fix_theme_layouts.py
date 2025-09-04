#!/usr/bin/env python
"""
Script to fix theme layouts with invalid enum values
"""
from app import create_app, db
from app.models import Theme

def fix_theme_layouts():
    app = create_app()
    
    with app.app_context():
        # Mapping of invalid values to valid ones
        layout_mapping = {
            'geometric': 'modern',
            'elegant': 'minimal'
        }
        
        # Get all themes with invalid layouts
        themes = Theme.query.all()
        fixed_count = 0
        
        for theme in themes:
            try:
                # Try to access the layout to see if it causes an error
                current_layout = theme.layout
                print(f"Theme '{theme.name}' has layout: {current_layout}")
            except:
                # If we get an error, the theme has an invalid layout
                # Let's update it directly in the database
                print(f"Theme '{theme.name}' has invalid layout, fixing...")
                
                # Update using raw SQL to bypass enum validation
                with db.engine.connect() as conn:
                    # Get the current layout value directly
                    result = conn.execute(db.text("SELECT layout FROM theme WHERE id = :id"), {"id": theme.id})
                    current_layout_raw = result.fetchone()[0]
                    
                    if current_layout_raw in layout_mapping:
                        new_layout = layout_mapping[current_layout_raw]
                        conn.execute(db.text("UPDATE theme SET layout = :new_layout WHERE id = :id"), 
                                   {"new_layout": new_layout, "id": theme.id})
                        conn.commit()
                        print(f"  Fixed: {current_layout_raw} -> {new_layout}")
                        fixed_count += 1
                    else:
                        print(f"  Unknown layout value: {current_layout_raw}")
        
        print(f"Fixed {fixed_count} themes with invalid layouts")

if __name__ == "__main__":
    fix_theme_layouts()