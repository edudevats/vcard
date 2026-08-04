"""
REST API Partner para integración B2B de ATScard con aplicaciones externas.
Base URL: /api/v1/partner
Autenticación: Cabecera X-API-Key o Authorization: Bearer <vcard_sk_...>
"""

from flask import Blueprint, request, jsonify, url_for, current_app
from datetime import datetime
import secrets
import re

from . import db
from .models import User, Card, SSOToken, PartnerApiKey, Theme
from .partner_auth import partner_api_key_required
from .timezone_utils import now_utc_for_db

bp = Blueprint('api_partner', __name__, url_prefix='/api/v1/partner')


def _find_user_by_identifier(identifier):
    """Busca un usuario por ID numérico, email o partner_client_id"""
    if not identifier:
        return None
    identifier_str = str(identifier).strip()

    # 1. Si es entero, buscar por ID
    if identifier_str.isdigit():
        user = User.query.get(int(identifier_str))
        if user:
            return user

    # 2. Buscar por email
    user = User.find_by_email(identifier_str)
    if user:
        return user

    # 3. Buscar por partner_client_id
    user = User.query.filter_by(partner_client_id=identifier_str).first()
    return user


def _card_to_partner_dict(card):
    """Serializa una tarjeta a diccionario JSON para la API Partner"""
    return {
        'id': card.id,
        'slug': card.slug,
        'name': card.name,
        'title': card.title,
        'job_title': card.job_title,
        'company': card.company,
        'phone': card.phone,
        'email_public': card.email_public,
        'website': card.website,
        'location': card.location,
        'bio': card.bio,
        'is_public': card.is_public,
        'public_url': card.get_public_url(),
        'qr_code_url': f"/c/{card.slug}/qr" if card.slug else None,
        'created_at': card.created_at.isoformat() if card.created_at else None,
        'updated_at': card.updated_at.isoformat() if card.updated_at else None,
        'owner': {
            'user_id': card.owner_id,
            'email': card.owner.email if card.owner else None,
            'partner_client_id': card.owner.partner_client_id if card.owner else None
        }
    }


# ────────────────────────────── CLIENTS ────────────────────────────────────

@bp.route('/clients', methods=['POST'])
@partner_api_key_required
def create_or_get_client(partner_key):
    """
    Crea o recupera un cliente usuario en ATScard desde la app externa.
    JSON Payload:
    - email: str (requerido)
    - partner_client_id: str (opcional, ID del cliente en la app externa)
    - password: str (opcional, si se omite se genera una segura)
    - max_cards: int (opcional, default 1)
    - auto_approve: bool (opcional, default True)
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'error': 'El campo email es requerido'}), 400

    partner_client_id = data.get('partner_client_id', '').strip() or None
    max_cards = data.get('max_cards', 1)

    try:
        max_cards = int(max_cards)
    except (ValueError, TypeError):
        max_cards = 1

    existing_user = User.find_by_email(email)
    if not existing_user and partner_client_id:
        existing_user = User.query.filter_by(partner_client_id=partner_client_id).first()

    if existing_user:
        # Actualizar datos si es necesario
        if partner_client_id and not existing_user.partner_client_id:
            existing_user.partner_client_id = partner_client_id

        if max_cards > existing_user.max_cards:
            existing_user.max_cards = max_cards

        db.session.commit()

        return jsonify({
            'success': True,
            'created': False,
            'user': {
                'id': existing_user.id,
                'email': existing_user.email,
                'partner_client_id': existing_user.partner_client_id,
                'is_active': existing_user.is_active,
                'is_approved': existing_user.is_approved,
                'max_cards': existing_user.max_cards,
                'cards_count': existing_user.cards.count()
            }
        }), 200

    # Crear nuevo usuario
    password = data.get('password') or secrets.token_urlsafe(16)
    auto_approve = data.get('auto_approve', True)

    new_user = User(
        email=email,
        partner_client_id=partner_client_id,
        max_cards=max_cards,
        is_active=True,
        is_approved=auto_approve,
        email_verified=True
    )
    new_user.set_password(password)

    if auto_approve:
        new_user.approved_at = now_utc_for_db()

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'success': True,
        'created': True,
        'user': {
            'id': new_user.id,
            'email': new_user.email,
            'partner_client_id': new_user.partner_client_id,
            'is_active': new_user.is_active,
            'is_approved': new_user.is_approved,
            'max_cards': new_user.max_cards,
            'cards_count': 0
        }
    }), 201


@bp.route('/clients/<client_identifier>', methods=['GET'])
@partner_api_key_required
def get_client(partner_key, client_identifier):
    """Obtiene los detalles de un cliente y todas sus vCards"""
    user = _find_user_by_identifier(client_identifier)
    if not user:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    cards = user.cards.all()
    return jsonify({
        'user': {
            'id': user.id,
            'email': user.email,
            'partner_client_id': user.partner_client_id,
            'is_active': user.is_active,
            'is_approved': user.is_approved,
            'is_suspended': user.is_suspended,
            'max_cards': user.max_cards,
            'cards_count': len(cards),
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'cards': [_card_to_partner_dict(c) for c in cards]
    }), 200


# ────────────────────────────── CARDS ──────────────────────────────────────

@bp.route('/cards', methods=['POST'])
@partner_api_key_required
def create_card(partner_key):
    """
    Crea una nueva vCard para un cliente determinado.
    JSON Payload:
    - client_identifier: str/int (email, user_id o partner_client_id, requerido)
    - name: str (requerido)
    - title: str (opcional)
    - job_title: str (opcional)
    - company: str (opcional)
    - phone: str (opcional)
    - email_public: str (opcional)
    - website: str (opcional)
    - bio: str (opcional)
    - slug: str (opcional)
    - is_public: bool (opcional, default True)
    """
    data = request.get_json() or {}
    client_identifier = data.get('client_identifier')
    name = data.get('name', '').strip()

    if not client_identifier:
        return jsonify({'error': 'client_identifier es requerido'}), 400
    if not name:
        return jsonify({'error': 'El nombre de la tarjeta es requerido'}), 400

    user = _find_user_by_identifier(client_identifier)
    if not user:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    if not user.can_create_card():
        return jsonify({
            'error': f'El cliente ha alcanzado el límite máximo de vCards ({user.max_cards})'
        }), 400

    # Determinar slug
    slug = data.get('slug', '').strip().lower()
    if slug:
        slug = re.sub(r'[^a-z0-9_-]', '', slug)
        if Card.query.filter_by(slug=slug).first():
            return jsonify({'error': f'El slug "{slug}" ya está en uso'}), 400
    else:
        # Auto-generar slug
        base_slug = re.sub(r'[^a-z0-9]', '', name.lower()) or 'vcard'
        slug = base_slug
        counter = 1
        while Card.query.filter_by(slug=slug).first():
            slug = f"{base_slug}{counter}"
            counter += 1

    # Determinar tema
    theme_id = data.get('theme_id')
    if not theme_id:
        default_theme = Theme.query.filter_by(is_active=True).first()
        if not default_theme:
            default_theme = Theme(
                name='Clásico Azul',
                template_name='classic',
                primary_color='#1e40af',
                secondary_color='#3b82f6',
                accent_color='#60a5fa',
                font_family='Roboto',
                layout='classic',
                avatar_shape='circle',
                is_global=True
            )
            db.session.add(default_theme)
            db.session.flush()
        theme_id = default_theme.id

    card = Card(
        owner_id=user.id,
        theme_id=theme_id,
        name=name,
        slug=slug,
        title=data.get('title', name),

        job_title=data.get('job_title'),
        company=data.get('company'),
        phone=data.get('phone'),
        email_public=data.get('email_public', user.email),
        website=data.get('website'),
        bio=data.get('bio'),
        is_public=data.get('is_public', True)
    )

    db.session.add(card)
    db.session.commit()

    return jsonify({
        'success': True,
        'card': _card_to_partner_dict(card)
    }), 201


@bp.route('/cards/<int:card_id>', methods=['PUT', 'PATCH'])
@partner_api_key_required
def update_card(partner_key, card_id):
    """Actualiza la información de una vCard existente"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({'error': 'Tarjeta no encontrada'}), 404

    data = request.get_json() or {}

    updatable_fields = ['name', 'title', 'job_title', 'company', 'phone', 
                        'email_public', 'website', 'location', 'bio',
                        'instagram', 'facebook', 'linkedin', 'twitter',
                        'youtube', 'tiktok', 'telegram', 'whatsapp', 'github']

    for field in updatable_fields:
        if field in data:
            setattr(card, field, data[field])

    if 'is_public' in data:
        card.is_public = bool(data['is_public'])

    db.session.commit()

    return jsonify({
        'success': True,
        'card': _card_to_partner_dict(card)
    }), 200


@bp.route('/cards/<int:card_id>/status', methods=['POST'])
@partner_api_key_required
def change_card_status(partner_key, card_id):
    """
    Activa, desactiva o publica/despublica una vCard.
    JSON Payload:
    - is_public: bool (requerido)
    """
    card = Card.query.get(card_id)
    if not card:
        return jsonify({'error': 'Tarjeta no encontrada'}), 404

    data = request.get_json() or {}
    if 'is_public' not in data:
        return jsonify({'error': 'Campo is_public es requerido'}), 400

    card.is_public = bool(data['is_public'])
    db.session.commit()

    return jsonify({
        'success': True,
        'card_id': card.id,
        'is_public': card.is_public
    }), 200


# ────────────────────────────── SINGLE SIGN-ON (SSO) ───────────────────────

@bp.route('/sso-session', methods=['POST'])
@partner_api_key_required
def create_sso_session(partner_key):
    """
    Genera un token de Single Sign-On para permitir que el cliente
    inicie sesión automáticamente en ATScard sin ingresar contraseña.
    JSON Payload:
    - client_identifier: str/int (email, user_id o partner_client_id, requerido)
    - expires_in_minutes: int (opcional, default 15)
    """
    data = request.get_json() or {}
    client_identifier = data.get('client_identifier')

    if not client_identifier:
        return jsonify({'error': 'client_identifier es requerido'}), 400

    user = _find_user_by_identifier(client_identifier)
    if not user:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    if not user.is_active or user.is_suspended:
        return jsonify({'error': 'Cuenta de usuario inactiva o suspendida'}), 403

    expires_in = data.get('expires_in_minutes', 15)
    try:
        expires_in = int(expires_in)
    except (ValueError, TypeError):
        expires_in = 15

    sso_token = SSOToken.create_for_user(user, expires_in_minutes=expires_in)
    db.session.add(sso_token)
    db.session.commit()

    # Construir URL de auto-login
    sso_url = url_for('auth.sso_login', token=sso_token.token, _external=True)

    return jsonify({
        'success': True,
        'sso_token': sso_token.token,
        'sso_url': sso_url,
        'expires_at': sso_token.expires_at.isoformat()
    }), 201
