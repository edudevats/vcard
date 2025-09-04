#!/usr/bin/env python
"""
Direct SQL fix for theme layouts
"""
from app import create_app, db

def fix_themes_direct():
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Update geometric to modern
                result1 = conn.execute(db.text("UPDATE theme SET layout = 'modern' WHERE layout = 'geometric'"))
                print(f"Updated {result1.rowcount} themes from 'geometric' to 'modern'")
                
                # Update elegant to minimal  
                result2 = conn.execute(db.text("UPDATE theme SET layout = 'minimal' WHERE layout = 'elegant'"))
                print(f"Updated {result2.rowcount} themes from 'elegant' to 'minimal'")
                
                conn.commit()
                
                # Show current layouts
                result3 = conn.execute(db.text("SELECT name, layout FROM theme"))
                themes = result3.fetchall()
                print("\nCurrent theme layouts:")
                for theme in themes:
                    print(f"  {theme[0]}: {theme[1]}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_themes_direct()