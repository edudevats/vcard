#!/usr/bin/env python
"""
Test script to update a card to use business template
"""
from app import create_app, db
from app.models import Card, Theme

def test_business_template():
    app = create_app()
    
    with app.app_context():
        # Get first card
        card = Card.query.first()
        if not card:
            print("No cards found!")
            return
        
        # Get a business theme
        business_theme = Theme.query.filter_by(template_name='business').first()
        if not business_theme:
            print("No business theme found!")
            return
        
        # Update card to use business template
        card.theme_id = business_theme.id
        db.session.commit()
        
        print(f"Updated {card.name} to use business template: {business_theme.name}")
        print(f"Card URL: /c/{card.slug}")

if __name__ == "__main__":
    test_business_template()