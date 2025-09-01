#!/usr/bin/env python
import os
import click
from flask import current_app
from flask.cli import with_appcontext
from app import create_app, db
from app.models import User, Theme, Card, Service, GalleryItem

app = create_app()

@app.cli.command()
@click.option('--email', prompt=True, help='Admin email')
@click.option('--password', prompt=True, hide_input=True, help='Admin password')
def create_admin(email, password):
    """Create an admin user."""
    user = User.query.filter_by(email=email).first()
    if user:
        click.echo(f'User {email} already exists.')
        return
    
    admin = User(email=email, role='admin', max_cards=10)
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'Admin user {email} created successfully.')

@app.cli.command()
@click.option('--email', prompt=True, help='User email')
@click.option('--n', prompt=True, type=int, help='Maximum number of cards')
def set_max_cards(email, n):
    """Set max cards for a user."""
    user = User.query.filter_by(email=email).first()
    if not user:
        click.echo(f'User {email} not found.')
        return
    
    user.max_cards = n
    db.session.commit()
    
    click.echo(f'User {email} max cards set to {n}.')

@app.cli.command()
def seed_themes():
    """Create default themes."""
    themes = [
        {
            'name': 'Clásico Azul',
            'primary_color': '#1e40af',
            'secondary_color': '#3b82f6',
            'accent_color': '#60a5fa',
            'font_family': 'Roboto',
            'layout': 'classic',
            'avatar_shape': 'circle'
        },
        {
            'name': 'Moderno Rosa',
            'primary_color': '#ec4899',
            'secondary_color': '#f472b6',
            'accent_color': '#fbcfe8',
            'font_family': 'Inter',
            'layout': 'modern',
            'avatar_shape': 'rounded'
        },
        {
            'name': 'Minimalista Verde',
            'primary_color': '#059669',
            'secondary_color': '#10b981',
            'accent_color': '#6ee7b7',
            'font_family': 'Poppins',
            'layout': 'minimal',
            'avatar_shape': 'square'
        },
        {
            'name': 'Elegante Púrpura',
            'primary_color': '#7c3aed',
            'secondary_color': '#8b5cf6',
            'accent_color': '#c4b5fd',
            'font_family': 'Montserrat',
            'layout': 'modern',
            'avatar_shape': 'circle'
        }
    ]
    
    for theme_data in themes:
        if not Theme.query.filter_by(name=theme_data['name']).first():
            theme = Theme(**theme_data)
            db.session.add(theme)
    
    db.session.commit()
    click.echo('Default themes created successfully.')

@app.cli.command()
def seed_data():
    """Create sample data."""
    # Create themes first
    seed_themes()
    
    # Create sample admin if doesn't exist
    admin_email = 'admin@vcard.test'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, role='admin', max_cards=50)
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create sample users
    users_data = [
        {'email': 'juan@example.com', 'name': 'Juan Pérez', 'job': 'Desarrollador Web', 'company': 'Tech Solutions'},
        {'email': 'maria@example.com', 'name': 'María García', 'job': 'Diseñadora UX/UI', 'company': 'Creative Studio'},
        {'email': 'carlos@example.com', 'name': 'Carlos López', 'job': 'Marketing Digital', 'company': 'Digital Agency'}
    ]
    
    for user_data in users_data:
        if not User.query.filter_by(email=user_data['email']).first():
            user = User(email=user_data['email'], max_cards=3)
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()  
            
            # Create a sample card for each user
            theme = Theme.query.first()
            card = Card(
                owner_id=user.id,
                name=user_data['name'],
                job_title=user_data['job'],
                company=user_data['company'],
                phone='+34 123 456 789',
                email_public=user_data['email'],
                location='Madrid, España',
                bio=f'Profesional especializado en {user_data["job"]} con amplia experiencia en el sector.',
                theme_id=theme.id,
                is_public=True
            )
            card.generate_slug()
            card.publish()
            db.session.add(card)
            db.session.flush()
            
            # Add sample services
            services_data = [
                {'title': 'Consultoría', 'description': 'Asesoramiento profesional personalizado', 'price': 50.00},
                {'title': 'Desarrollo de Proyecto', 'description': 'Desarrollo completo de tu proyecto', 'price': 200.00},
                {'title': 'Soporte Técnico', 'description': 'Soporte técnico continuo', 'price': 25.00}
            ]
            
            for i, service_data in enumerate(services_data):
                service = Service(
                    card_id=card.id,
                    title=service_data['title'],
                    description=service_data['description'],
                    price_from=service_data['price'],
                    order_index=i
                )
                db.session.add(service)
    
    db.session.commit()
    click.echo('Sample data created successfully.')

if __name__ == '__main__':
    app.run(debug=True)