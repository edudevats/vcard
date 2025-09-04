#!/usr/bin/env python
"""
Script to add avatar_border_color field to themes table
"""
from app import create_app, db

def add_avatar_border_color():
    app = create_app()
    
    with app.app_context():
        try:
            # Add avatar_border_color column
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE theme ADD COLUMN avatar_border_color VARCHAR(7) DEFAULT '#ffffff'"))
                conn.commit()
            print("Added avatar_border_color column")
        except Exception as e:
            print(f"avatar_border_color column might already exist: {e}")
        
        # Set default white border for existing themes
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("UPDATE theme SET avatar_border_color = '#ffffff' WHERE avatar_border_color IS NULL"))
                conn.commit()
            print("Updated existing themes with default white border")
        except Exception as e:
            print(f"Error updating themes: {e}")
        
        print("Avatar border color field added successfully!")

if __name__ == "__main__":
    add_avatar_border_color()