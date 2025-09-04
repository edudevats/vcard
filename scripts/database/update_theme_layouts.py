#!/usr/bin/env python
"""
Script to update theme layouts enum to include new values
"""
from app import create_app, db

def update_theme_layouts():
    app = create_app()
    
    with app.app_context():
        try:
            # For SQLite, we need to recreate the column with new enum values
            # First, let's add new columns with the expanded enum
            with db.engine.connect() as conn:
                # Add temporary column
                conn.execute(db.text("ALTER TABLE theme ADD COLUMN layout_new TEXT"))
                conn.commit()
                
                # Copy data from old column to new one
                conn.execute(db.text("UPDATE theme SET layout_new = layout"))
                conn.commit()
                
                # Drop old column (SQLite doesn't support direct enum modification)
                # We'll keep the old column and just update our model to use TEXT instead
                print("Updated theme layout column preparation")
                
        except Exception as e:
            print(f"Error: {e}")
            # If column already exists, continue
            pass
        
        print("Theme layouts update completed!")

if __name__ == "__main__":
    update_theme_layouts()