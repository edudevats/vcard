#!/usr/bin/env python
"""
Script to add privacy fields to themes table
"""
from app import create_app, db

def add_privacy_fields():
    app = create_app()
    
    with app.app_context():
        # Add new columns manually
        try:
            # Add is_global column
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE theme ADD COLUMN is_global BOOLEAN DEFAULT 0"))
                conn.commit()
            print("Added is_global column")
        except Exception as e:
            print(f"is_global column might already exist: {e}")
        
        try:
            # Add created_by_id column
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE theme ADD COLUMN created_by_id INTEGER"))
                conn.commit()
            print("Added created_by_id column")
        except Exception as e:
            print(f"created_by_id column might already exist: {e}")
        
        # Set existing themes as global themes
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("UPDATE theme SET is_global = 1 WHERE is_global IS NULL OR is_global = 0"))
                conn.commit()
            print("Updated existing themes as global")
        except Exception as e:
            print(f"Error updating themes: {e}")
        print("Updated existing themes as global")
        
        print("Theme privacy fields added successfully!")

if __name__ == "__main__":
    add_privacy_fields()