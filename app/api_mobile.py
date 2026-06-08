"""
REST API para la app móvil de ATScard.
Usa autenticación por token (Bearer Token).
Base URL: /api/mobile/v1
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from datetime import datetime, date
import secrets
import os

from . import db
from .models import User, Card, Service, Product, GalleryItem, Appointment, TicketSystem, Ticket, TicketType

bp = Blueprint('api_mobile', __name__, url_prefix='/api/mobile/v1')

# ─────────────────────────────── helpers ──────────────────────────────────

def generate_token():
    return secrets.token_urlsafe(32)


def token_required(f):
    """Decorator: valida el Bearer token de la petición."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token requerido'}), 401
        token = auth_header[7:]

        # Buscar usuario por mobile_token
        user = User.query.filter_by(mobile_token=token).first()
        if not user:
            return jsonify({'error': 'Token inválido o expirado'}), 401
        if user.is_suspended:
            return jsonify({'error': 'Cuenta suspendida'}), 403
        return f(user, *args, **kwargs)
    return decorated


def _card_to_dict(card, include_details=False):
    base = {
        'id': card.id,
        'slug': card.slug,
        'title': card.title or card.name,
        'name': card.name,
        'job_title': card.job_title,
        'company': card.company,
        'phone': card.phone,
        'email_public': card.email_public,
        'website': card.website,
        'location': card.location,
        'bio': card.bio,
        'is_public': card.is_public,
        'avatar_url': None,
        'public_url': card.get_public_url(),
        'created_at': card.created_at.isoformat() if card.created_at else None,
        'updated_at': card.updated_at.isoformat() if card.updated_at else None,
    }

    # Avatar URL
    if card.avatar_square_path:
        base['avatar_url'] = f"/static/{card.avatar_square_path}"
    elif card.avatar_path:
        base['avatar_url'] = f"/static/{card.avatar_path}"

    if include_details:
        base.update({
            'instagram': card.instagram,
            'facebook': card.facebook,
            'linkedin': card.linkedin,
            'twitter': card.twitter,
            'youtube': card.youtube,
            'tiktok': card.tiktok,
            'telegram': card.telegram,
            'whatsapp': card.whatsapp,
            'whatsapp_country': card.whatsapp_country,
            'github': card.github,
            'theme': {
                'name': card.theme.name if card.theme else None,
                'primary_color': card.theme.primary_color if card.theme else '#6366f1',
                'secondary_color': card.theme.secondary_color if card.theme else '#8b5cf6',
                'accent_color': card.theme.accent_color if card.theme else '#ec4899',
                'font_family': card.theme.font_family if card.theme else 'Inter',
                'layout': card.theme.layout if card.theme else 'modern',
                'avatar_shape': card.theme.avatar_shape if card.theme else 'circle',
            } if card.theme_id else None,
            'services_count': card.services.count(),
            'gallery_count': card.gallery_items.count(),
        })

    return base


def _service_to_dict(service):
    return {
        'id': service.id,
        'title': service.title,
        'description': service.description,
        'price_from': service.price_from,
        'icon': service.icon,
        'category': service.category,
        'duration': service.duration,
        'is_featured': service.is_featured,
        'is_visible': service.is_visible,
        'accepts_appointments': service.accepts_appointments,
        'order_index': service.order_index,
        'image_path': f"/static/{service.image_path}" if service.image_path else None,
    }


def _appointment_to_dict(apt):
    return {
        'id': apt.id,
        'customer_name': apt.customer_name,
        'customer_phone': apt.customer_phone,
        'customer_phone_country': apt.customer_phone_country,
        'customer_address': apt.customer_address,
        'appointment_date': apt.appointment_date.isoformat() if apt.appointment_date else None,
        'appointment_time': apt.appointment_time,
        'status': apt.status,
        'notes': apt.notes,
        'cancellation_reason': apt.cancellation_reason,
        'service_id': apt.service_id,
        'service_name': apt.service.title if apt.service else None,
        'card_id': apt.card_id,
        'created_at': apt.created_at.isoformat() if apt.created_at else None,
        'confirmed_at': apt.confirmed_at.isoformat() if apt.confirmed_at else None,
    }


def _ticket_to_dict(ticket):
    return {
        'id': ticket.id,
        'ticket_number': ticket.ticket_number,
        'patient_name': ticket.patient_name,
        'patient_phone': ticket.patient_phone,
        'status': ticket.status,
        'ticket_type_id': ticket.ticket_type_id,
        'ticket_type_name': ticket.ticket_type.name if ticket.ticket_type else None,
        'ticket_type_color': ticket.ticket_type.color if ticket.ticket_type else None,
        'is_priority': ticket.is_priority,
        'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
        'called_at': ticket.called_at.isoformat() if ticket.called_at else None,
        'completed_at': ticket.completed_at.isoformat() if ticket.completed_at else None,
        'notes': ticket.notes,
    }


# ─────────────────────────────── AUTH ─────────────────────────────────────

@bp.route('/auth/login', methods=['POST'])
def login():
    """Login con email/password. Retorna token."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email y contraseña requeridos'}), 400

    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciales incorrectas'}), 401

    if not user.is_active:
        return jsonify({'error': 'Cuenta inactiva'}), 403

    if user.is_suspended:
        return jsonify({'error': f'Cuenta suspendida: {user.suspension_reason}'}), 403

    if not user.is_approved:
        return jsonify({'error': 'Cuenta pendiente de aprobación'}), 403

    # Generar/regenerar token
    token = generate_token()
    user.mobile_token = token
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'max_cards': user.max_cards,
        }
    })


@bp.route('/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Invalida el token actual."""
    current_user.mobile_token = None
    db.session.commit()
    return jsonify({'message': 'Sesión cerrada'})


@bp.route('/auth/me', methods=['GET'])
@token_required
def me(current_user):
    """Perfil del usuario autenticado."""
    cards_count = current_user.cards.count()
    total_views = sum(c.services.count() for c in current_user.cards)
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'role': current_user.role,
        'max_cards': current_user.max_cards,
        'cards_count': cards_count,
        'can_create_card': current_user.can_create_card(),
        'has_ticket_system': current_user.ticket_system is not None and current_user.ticket_system.is_enabled,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
    })


# ─────────────────────────────── CARDS ────────────────────────────────────

@bp.route('/cards', methods=['GET'])
@token_required
def list_cards(current_user):
    """Lista todas las tarjetas del usuario."""
    cards = current_user.cards.all()
    return jsonify([_card_to_dict(c) for c in cards])


@bp.route('/cards/<int:card_id>', methods=['GET'])
@token_required
def get_card(current_user, card_id):
    """Detalle de una tarjeta."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    return jsonify(_card_to_dict(card, include_details=True))


@bp.route('/cards/<int:card_id>/toggle-publish', methods=['POST'])
@token_required
def toggle_publish(current_user, card_id):
    """Publicar/despublicar tarjeta."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    if card.is_public:
        card.unpublish()
    else:
        card.publish()
    db.session.commit()
    return jsonify({'is_public': card.is_public})


# ─────────────────────────────── SERVICES ─────────────────────────────────

@bp.route('/cards/<int:card_id>/services', methods=['GET'])
@token_required
def list_services(current_user, card_id):
    """Lista servicios de una tarjeta."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    services = card.services.order_by(Service.order_index).all()
    return jsonify([_service_to_dict(s) for s in services])


@bp.route('/cards/<int:card_id>/services', methods=['POST'])
@token_required
def create_service(current_user, card_id):
    """Crear nuevo servicio."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Título requerido'}), 400

    service = Service(
        card_id=card.id,
        title=data['title'],
        description=data.get('description'),
        price_from=data.get('price_from'),
        icon=data.get('icon', 'star'),
        category=data.get('category'),
        duration=data.get('duration'),
        is_featured=data.get('is_featured', False),
        is_visible=data.get('is_visible', True),
        accepts_appointments=data.get('accepts_appointments', False),
    )
    db.session.add(service)
    db.session.commit()
    return jsonify(_service_to_dict(service)), 201


@bp.route('/services/<int:service_id>', methods=['PUT'])
@token_required
def update_service(current_user, service_id):
    """Actualizar servicio."""
    service = Service.query.get_or_404(service_id)
    if service.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403

    data = request.get_json() or {}
    for field in ['title', 'description', 'price_from', 'icon', 'category',
                  'duration', 'is_featured', 'is_visible', 'accepts_appointments']:
        if field in data:
            setattr(service, field, data[field])

    db.session.commit()
    return jsonify(_service_to_dict(service))


@bp.route('/services/<int:service_id>', methods=['DELETE'])
@token_required
def delete_service(current_user, service_id):
    """Eliminar servicio."""
    service = Service.query.get_or_404(service_id)
    if service.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Servicio eliminado'})


@bp.route('/services/<int:service_id>/image', methods=['POST'])
@token_required
def upload_service_image(current_user, service_id):
    """Subir imagen de servicio (multipart/form-data, campo 'image')."""
    service = Service.query.get_or_404(service_id)
    if service.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403

    if 'image' not in request.files:
        return jsonify({'error': 'No se encontró el archivo'}), 400

    file = request.files['image']
    if not file or not file.filename:
        return jsonify({'error': 'Archivo inválido'}), 400

    from .utils import save_image
    filename, _ = save_image(file, 'static/uploads')
    if not filename:
        return jsonify({'error': 'Error al procesar la imagen'}), 400

    service.image_path = f"uploads/{filename}"
    db.session.commit()
    return jsonify({
        'image_path': f"/static/uploads/{filename}",
        'message': 'Imagen subida'
    })


@bp.route('/services/<int:service_id>/image', methods=['DELETE'])
@token_required
def delete_service_image(current_user, service_id):
    """Eliminar imagen de servicio."""
    service = Service.query.get_or_404(service_id)
    if service.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    service.image_path = None
    db.session.commit()
    return jsonify({'message': 'Imagen eliminada'})


# ─────────────────────────────── APPOINTMENTS ─────────────────────────────

@bp.route('/appointments', methods=['GET'])
@token_required
def list_appointments(current_user):
    """Lista citas de todas las tarjetas del usuario."""
    status_filter = request.args.get('status')
    card_ids = [c.id for c in current_user.cards.all()]

    query = Appointment.query.filter(Appointment.card_id.in_(card_ids))
    if status_filter:
        query = query.filter_by(status=status_filter)

    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).limit(100).all()

    return jsonify([_appointment_to_dict(a) for a in appointments])


@bp.route('/appointments/stats', methods=['GET'])
@token_required
def appointment_stats(current_user):
    """Estadísticas de citas."""
    card_ids = [c.id for c in current_user.cards.all()]
    today = date.today()

    total = Appointment.query.filter(Appointment.card_id.in_(card_ids)).count()
    pending = Appointment.query.filter(
        Appointment.card_id.in_(card_ids),
        Appointment.status == 'pending'
    ).count()
    confirmed = Appointment.query.filter(
        Appointment.card_id.in_(card_ids),
        Appointment.status == 'confirmed'
    ).count()
    today_count = Appointment.query.filter(
        Appointment.card_id.in_(card_ids),
        Appointment.appointment_date == today
    ).count()

    return jsonify({
        'total': total,
        'pending': pending,
        'confirmed': confirmed,
        'today': today_count,
    })


@bp.route('/appointments/<int:apt_id>/confirm', methods=['POST'])
@token_required
def confirm_appointment(current_user, apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    if apt.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    apt.confirm()
    db.session.commit()
    return jsonify(_appointment_to_dict(apt))


@bp.route('/appointments/<int:apt_id>/complete', methods=['POST'])
@token_required
def complete_appointment(current_user, apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    if apt.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    apt.complete()
    db.session.commit()
    return jsonify(_appointment_to_dict(apt))


@bp.route('/appointments/<int:apt_id>/cancel', methods=['POST'])
@token_required
def cancel_appointment(current_user, apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    if apt.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    data = request.get_json() or {}
    apt.cancel(reason=data.get('reason', ''))
    db.session.commit()
    return jsonify(_appointment_to_dict(apt))


@bp.route('/appointments/<int:apt_id>/no-show', methods=['POST'])
@token_required
def no_show_appointment(current_user, apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    if apt.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    apt.mark_no_show()
    db.session.commit()
    return jsonify(_appointment_to_dict(apt))


# ─────────────────────────────── TICKETS ──────────────────────────────────

@bp.route('/tickets', methods=['GET'])
@token_required
def list_tickets(current_user):
    """Lista turnos del sistema activo del usuario."""
    ts = current_user.ticket_system
    if not ts or not ts.is_enabled:
        return jsonify({'enabled': False, 'tickets': []})

    status_filter = request.args.get('status', 'waiting')
    from .timezone_utils import today_start_utc
    day_start = today_start_utc()
    day_end = day_start.replace(hour=23, minute=59, second=59)

    query = Ticket.query.filter(
        Ticket.ticket_system_id == ts.id,
        Ticket.created_at >= day_start,
        Ticket.created_at <= day_end,
    )
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    tickets = query.order_by(Ticket.created_at.asc()).all()

    return jsonify({
        'enabled': True,
        'is_accepting': ts.is_accepting_tickets,
        'business_name': ts.business_name,
        'tickets': [_ticket_to_dict(t) for t in tickets],
        'stats': ts.get_daily_stats(),
        'current_ticket': _ticket_to_dict(ts.get_current_ticket()) if ts.get_current_ticket() else None,
    })


@bp.route('/tickets/call-next', methods=['POST'])
@token_required
def call_next_ticket(current_user):
    """Llama al siguiente turno en espera."""
    ts = current_user.ticket_system
    if not ts or not ts.is_enabled:
        return jsonify({'error': 'Sistema de turnos no disponible'}), 400

    from .timezone_utils import today_start_utc
    day_start = today_start_utc()

    # Terminar el turno actual si existe
    current = ts.get_current_ticket()
    if current:
        current.complete()

    # Obtener siguiente en espera
    next_ticket = Ticket.query.filter(
        Ticket.ticket_system_id == ts.id,
        Ticket.status == 'waiting',
        Ticket.created_at >= day_start,
    ).order_by(Ticket.is_priority.desc(), Ticket.created_at.asc()).first()

    if not next_ticket:
        return jsonify({'message': 'No hay turnos en espera', 'ticket': None})

    next_ticket.call()
    db.session.commit()
    return jsonify({'ticket': _ticket_to_dict(next_ticket)})


@bp.route('/tickets/<int:ticket_id>/complete', methods=['POST'])
@token_required
def complete_ticket(current_user, ticket_id):
    ts = current_user.ticket_system
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.ticket_system_id != ts.id:
        return jsonify({'error': 'Sin permiso'}), 403
    ticket.complete()
    db.session.commit()
    return jsonify(_ticket_to_dict(ticket))


@bp.route('/tickets/<int:ticket_id>/cancel', methods=['POST'])
@token_required
def cancel_ticket(current_user, ticket_id):
    ts = current_user.ticket_system
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.ticket_system_id != ts.id:
        return jsonify({'error': 'Sin permiso'}), 403
    data = request.get_json() or {}
    ticket.cancel(reason=data.get('reason', ''))
    db.session.commit()
    return jsonify(_ticket_to_dict(ticket))


@bp.route('/tickets/<int:ticket_id>/no-show', methods=['POST'])
@token_required
def no_show_ticket(current_user, ticket_id):
    ts = current_user.ticket_system
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.ticket_system_id != ts.id:
        return jsonify({'error': 'Sin permiso'}), 403
    ticket.mark_no_show()
    db.session.commit()
    return jsonify(_ticket_to_dict(ticket))


@bp.route('/tickets/toggle-accepting', methods=['POST'])
@token_required
def toggle_accepting(current_user):
    """Pausa/reanuda la aceptación de turnos."""
    ts = current_user.ticket_system
    if not ts or not ts.is_enabled:
        return jsonify({'error': 'Sin sistema de turnos'}), 400
    ts.is_accepting_tickets = not ts.is_accepting_tickets
    db.session.commit()
    return jsonify({'is_accepting': ts.is_accepting_tickets})


# ─────────────────────────────── ANALYTICS ────────────────────────────────

@bp.route('/analytics', methods=['GET'])
@token_required
def analytics_summary(current_user):
    """Resumen de analíticas para todas las tarjetas."""
    from .models import CardView
    from .timezone_utils import today_start_utc, get_month_range_utc

    card_ids = [c.id for c in current_user.cards.all()]
    day_start = today_start_utc()
    month_start, month_end = get_month_range_utc()

    total = CardView.query.filter(CardView.card_id.in_(card_ids)).count()
    today_views = CardView.query.filter(
        CardView.card_id.in_(card_ids),
        CardView.viewed_at >= day_start
    ).count()
    month_views = CardView.query.filter(
        CardView.card_id.in_(card_ids),
        CardView.viewed_at >= month_start,
        CardView.viewed_at <= month_end
    ).count()

    # Per-card stats
    per_card = []
    for card in current_user.cards.all():
        card_total = CardView.query.filter_by(card_id=card.id).count()
        card_today = CardView.query.filter(
            CardView.card_id == card.id,
            CardView.viewed_at >= day_start
        ).count()
        per_card.append({
            'card_id': card.id,
            'card_name': card.name,
            'card_slug': card.slug,
            'total': card_total,
            'today': card_today,
        })

    return jsonify({
        'total': total,
        'today': today_views,
        'this_month': month_views,
        'per_card': per_card,
    })


# ─────────────────────────────── GALLERY ──────────────────────────────────

@bp.route('/cards/<int:card_id>/gallery', methods=['GET'])
@token_required
def list_gallery(current_user, card_id):
    """Lista ítems de galería."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    items = card.gallery_items.order_by(GalleryItem.order_index).all()
    return jsonify([{
        'id': item.id,
        'image_url': f"/static/uploads/{item.image_path}" if item.image_path else None,
        'thumb_url': f"/static/thumbs/{item.thumbnail_path}" if item.thumbnail_path else None,
        'caption': item.caption,
        'is_featured': item.is_featured,
        'order_index': item.order_index,
    } for item in items])


# ─────────────────────────────── DASHBOARD ────────────────────────────────

@bp.route('/dashboard', methods=['GET'])
@token_required
def dashboard(current_user):
    """Resumen del dashboard."""
    from .models import CardView, Appointment
    from .timezone_utils import today_start_utc

    cards = current_user.cards.all()
    card_ids = [c.id for c in cards]
    day_start = today_start_utc()

    # Views today
    views_today = CardView.query.filter(
        CardView.card_id.in_(card_ids),
        CardView.viewed_at >= day_start
    ).count() if card_ids else 0

    # Pending appointments
    pending_apts = Appointment.query.filter(
        Appointment.card_id.in_(card_ids),
        Appointment.status == 'pending'
    ).count() if card_ids else 0

    # Ticket stats
    ticket_stats = None
    if current_user.ticket_system and current_user.ticket_system.is_enabled:
        ticket_stats = current_user.ticket_system.get_daily_stats()

    # Recent appointments
    recent_apts = []
    if card_ids:
        recent_apts = Appointment.query.filter(
            Appointment.card_id.in_(card_ids),
            Appointment.status.in_(['pending', 'confirmed'])
        ).order_by(Appointment.appointment_date.asc()).limit(5).all()

    return jsonify({
        'cards_count': len(cards),
        'max_cards': current_user.max_cards,
        'views_today': views_today,
        'pending_appointments': pending_apts,
        'ticket_stats': ticket_stats,
        'recent_appointments': [_appointment_to_dict(a) for a in recent_apts],
        'cards': [_card_to_dict(c) for c in cards],
    })


# ─────────────────────────── CARD CREATE / UPDATE ─────────────────────────

@bp.route('/cards', methods=['POST'])
@token_required
def create_card(current_user):
    """Crear nueva tarjeta."""
    if not current_user.can_create_card():
        return jsonify({'error': 'Límite de tarjetas alcanzado'}), 403

    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'El nombre es requerido'}), 400

    # Get default theme
    from .models import Theme
    default_theme = Theme.query.filter_by(is_global=True).first()

    card = Card(
        owner_id=current_user.id,
        name=data['name'],
        job_title=data.get('job_title'),
        company=data.get('company'),
        bio=data.get('bio'),
        phone=data.get('phone'),
        email_public=data.get('email_public'),
        website=data.get('website'),
        location=data.get('location'),
        is_public=data.get('is_public', False),
        theme_id=default_theme.id if default_theme else None,
    )
    db.session.add(card)
    db.session.commit()
    return jsonify(_card_to_dict(card, include_details=True)), 201


@bp.route('/cards/<int:card_id>', methods=['PUT'])
@token_required
def update_card(current_user, card_id):
    """Actualizar tarjeta (info, contacto, redes)."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    data = request.get_json() or {}

    updatable = [
        'name', 'job_title', 'company', 'bio', 'phone', 'email_public',
        'website', 'location', 'instagram', 'facebook', 'linkedin',
        'twitter', 'youtube', 'tiktok', 'telegram', 'whatsapp',
        'whatsapp_country', 'github', 'is_public',
    ]
    for field in updatable:
        if field in data:
            setattr(card, field, data[field])

    card.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_card_to_dict(card, include_details=True))


@bp.route('/cards/<int:card_id>', methods=['DELETE'])
@token_required
def delete_card(current_user, card_id):
    """Eliminar tarjeta."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    db.session.delete(card)
    db.session.commit()
    return jsonify({'message': 'Tarjeta eliminada'})


# ─────────────────────────── AVATAR ───────────────────────────────────────

@bp.route('/cards/<int:card_id>/avatar', methods=['POST'])
@token_required
def upload_avatar(current_user, card_id):
    """Subir avatar de tarjeta (multipart/form-data, campo 'avatar')."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()

    if 'avatar' not in request.files:
        return jsonify({'error': 'No se encontró el archivo'}), 400

    file = request.files['avatar']
    if not file or not file.filename:
        return jsonify({'error': 'Archivo inválido'}), 400

    from .utils import save_avatar
    try:
        square_filename, rect_filename = save_avatar(file)
        if not square_filename:
            return jsonify({'error': 'Error al procesar la imagen'}), 400
        card.avatar_square_path = square_filename
        card.avatar_path = square_filename  # Legacy field
        card.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'avatar_url': f"/static/uploads/{square_filename}",
            'message': 'Avatar actualizado'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/cards/<int:card_id>/avatar', methods=['DELETE'])
@token_required
def delete_avatar(current_user, card_id):
    """Eliminar avatar de tarjeta."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    card.avatar_path = None
    card.avatar_square_path = None
    card.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Avatar eliminado'})


# ─────────────────────────── GALLERY ──────────────────────────────────────

@bp.route('/cards/<int:card_id>/gallery', methods=['POST'])
@token_required
def upload_gallery_image(current_user, card_id):
    """Subir imagen a la galería (multipart/form-data, campo 'image')."""
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()

    if card.gallery_items.count() >= 20:
        return jsonify({'error': 'Límite de 20 imágenes alcanzado'}), 400

    if 'image' not in request.files:
        return jsonify({'error': 'No se encontró el archivo'}), 400

    file = request.files['image']
    if not file or not file.filename:
        return jsonify({'error': 'Archivo inválido'}), 400

    from .utils import save_image
    try:
        filename, thumb_filename = save_image(file, 'static/uploads')
        if not filename:
            return jsonify({'error': 'Error al procesar la imagen'}), 400
        caption = request.form.get('caption', '')
        item = GalleryItem(
            card_id=card.id,
            image_path=filename,
            thumbnail_path=thumb_filename,
            caption=caption,
            order_index=card.gallery_items.count(),
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({
            'id': item.id,
            'image_url': f"/static/uploads/{item.image_path}",
            'thumb_url': f"/static/thumbs/{item.thumbnail_path}" if item.thumbnail_path else None,
            'caption': item.caption,
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/gallery/<int:item_id>', methods=['DELETE'])
@token_required
def delete_gallery_item(current_user, item_id):
    """Eliminar imagen de galería."""
    item = GalleryItem.query.get_or_404(item_id)
    if item.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Imagen eliminada'})


@bp.route('/gallery/<int:item_id>/set-featured', methods=['POST'])
@token_required
def set_gallery_featured(current_user, item_id):
    """Marcar imagen como destacada."""
    item = GalleryItem.query.get_or_404(item_id)
    if item.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    # Unset all featured for this card
    for gi in item.card.gallery_items:
        gi.is_featured = False
    item.is_featured = True
    db.session.commit()
    return jsonify({'message': 'Imagen destacada actualizada'})


# ─────────────────────────── PRODUCTS ─────────────────────────────────────

def _product_to_dict(product):
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price) if product.price else None,
        'original_price': float(product.original_price) if product.original_price else None,
        'category': product.category,
        'brand': product.brand,
        'sku': product.sku,
        'stock_quantity': product.stock_quantity,
        'external_link': product.external_link,
        'is_featured': product.is_featured,
        'is_visible': product.is_visible,
        'is_available': product.is_available,
        'image_url': f"/static/{product.image_path}" if product.image_path else None,
        'order_index': product.order_index,
    }


@bp.route('/cards/<int:card_id>/products', methods=['GET'])
@token_required
def list_products(current_user, card_id):
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    products = card.products.order_by(Product.order_index).all()
    return jsonify([_product_to_dict(p) for p in products])


@bp.route('/cards/<int:card_id>/products', methods=['POST'])
@token_required
def create_product(current_user, card_id):
    card = Card.query.filter_by(id=card_id, owner_id=current_user.id).first_or_404()
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'El nombre es requerido'}), 400

    product = Product(
        card_id=card.id,
        name=data['name'],
        description=data.get('description'),
        price=data.get('price'),
        original_price=data.get('original_price'),
        category=data.get('category'),
        brand=data.get('brand'),
        sku=data.get('sku'),
        stock_quantity=data.get('stock_quantity', -1),
        external_link=data.get('external_link'),
        is_featured=data.get('is_featured', False),
        is_visible=data.get('is_visible', True),
        is_available=data.get('is_available', True),
        order_index=card.products.count(),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(_product_to_dict(product)), 201


@bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    if product.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    data = request.get_json() or {}
    for field in ['name', 'description', 'price', 'original_price', 'category',
                  'brand', 'sku', 'stock_quantity', 'external_link',
                  'is_featured', 'is_visible', 'is_available']:
        if field in data:
            setattr(product, field, data[field])
    db.session.commit()
    return jsonify(_product_to_dict(product))


@bp.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    if product.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Producto eliminado'})


@bp.route('/products/<int:product_id>/image', methods=['POST'])
@token_required
def upload_product_image(current_user, product_id):
    """Subir imagen de producto (multipart/form-data, campo 'image')."""
    product = Product.query.get_or_404(product_id)
    if product.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403

    if 'image' not in request.files:
        return jsonify({'error': 'No se encontró el archivo'}), 400

    file = request.files['image']
    if not file or not file.filename:
        return jsonify({'error': 'Archivo inválido'}), 400

    from .utils import save_image
    filename, _ = save_image(file, 'static/uploads')
    if not filename:
        return jsonify({'error': 'Error al procesar la imagen'}), 400

    product.image_path = filename
    db.session.commit()
    return jsonify({
        'image_url': f"/static/uploads/{filename}",
        'message': 'Imagen subida'
    })


@bp.route('/products/<int:product_id>/image', methods=['DELETE'])
@token_required
def delete_product_image(current_user, product_id):
    """Eliminar imagen de producto."""
    product = Product.query.get_or_404(product_id)
    if product.card.owner_id != current_user.id:
        return jsonify({'error': 'Sin permiso'}), 403
    product.image_path = None
    db.session.commit()
    return jsonify({'message': 'Imagen eliminada'})


# ─────────────────────────── PROFILE ──────────────────────────────────────

@bp.route('/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Cambiar contraseña."""
    data = request.get_json() or {}
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')

    if not current_pw or not new_pw:
        return jsonify({'error': 'Contraseñas requeridas'}), 400
    if len(new_pw) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    if not current_user.check_password(current_pw):
        return jsonify({'error': 'Contraseña actual incorrecta'}), 401

    current_user.set_password(new_pw)
    db.session.commit()
    return jsonify({'message': 'Contraseña actualizada'})


# ─────────────────────────── TICKET SETTINGS ──────────────────────────────

def _ticket_type_to_dict(tt):
    return {
        'id': tt.id,
        'name': tt.name,
        'prefix': tt.prefix,
        'color': tt.color,
        'estimated_duration': tt.estimated_duration,
        'is_active': tt.is_active,
        'order_index': tt.order_index,
    }


@bp.route('/tickets/settings', methods=['GET'])
@token_required
def get_ticket_settings(current_user):
    ts = current_user.ticket_system
    if not ts:
        return jsonify({'error': 'Sin sistema de turnos'}), 404
    return jsonify({
        'business_name': ts.business_name,
        'business_hours': ts.business_hours,
        'welcome_message': ts.welcome_message,
        'display_mode': ts.display_mode,
        'pause_message': ts.pause_message,
        'is_accepting': ts.is_accepting_tickets,
        'ticket_types': [_ticket_type_to_dict(t) for t in ts.ticket_types.order_by(TicketType.order_index).all()],
    })


@bp.route('/tickets/settings', methods=['PUT'])
@token_required
def update_ticket_settings(current_user):
    ts = current_user.ticket_system
    if not ts:
        return jsonify({'error': 'Sin sistema de turnos'}), 404
    data = request.get_json() or {}
    for field in ['business_name', 'business_hours', 'welcome_message', 'display_mode', 'pause_message']:
        if field in data:
            setattr(ts, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Configuración actualizada'})


@bp.route('/tickets/types', methods=['POST'])
@token_required
def create_ticket_type(current_user):
    ts = current_user.ticket_system
    if not ts:
        return jsonify({'error': 'Sin sistema de turnos'}), 404
    data = request.get_json() or {}
    if not data.get('name') or not data.get('prefix'):
        return jsonify({'error': 'Nombre y prefijo requeridos'}), 400

    tt = TicketType(
        ticket_system_id=ts.id,
        name=data['name'],
        prefix=data['prefix'].upper(),
        color=data.get('color', '#6366f1'),
        estimated_duration=data.get('estimated_duration', 15),
        is_active=data.get('is_active', True),
        order_index=ts.ticket_types.count(),
    )
    db.session.add(tt)
    db.session.commit()
    return jsonify(_ticket_type_to_dict(tt)), 201


@bp.route('/tickets/types/<int:type_id>', methods=['PUT'])
@token_required
def update_ticket_type(current_user, type_id):
    ts = current_user.ticket_system
    tt = TicketType.query.get_or_404(type_id)
    if tt.ticket_system_id != ts.id:
        return jsonify({'error': 'Sin permiso'}), 403
    data = request.get_json() or {}
    for field in ['name', 'prefix', 'color', 'estimated_duration', 'is_active']:
        if field in data:
            setattr(tt, field, data[field])
    if 'prefix' in data:
        tt.prefix = data['prefix'].upper()
    db.session.commit()
    return jsonify(_ticket_type_to_dict(tt))


@bp.route('/tickets/types/<int:type_id>', methods=['DELETE'])
@token_required
def delete_ticket_type(current_user, type_id):
    ts = current_user.ticket_system
    tt = TicketType.query.get_or_404(type_id)
    if tt.ticket_system_id != ts.id:
        return jsonify({'error': 'Sin permiso'}), 403
    db.session.delete(tt)
    db.session.commit()
    return jsonify({'message': 'Tipo eliminado'})


@bp.route('/tickets/<int:ticket_id>/mark-urgent', methods=['POST'])
@token_required
def mark_urgent_ticket(current_user, ticket_id):
    ts = current_user.ticket_system
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.ticket_system_id != ts.id:
        return jsonify({'error': 'Sin permiso'}), 403
    ticket.is_priority = True
    db.session.commit()
    return jsonify(_ticket_to_dict(ticket))


@bp.route('/tickets/metrics', methods=['GET'])
@token_required
def ticket_metrics(current_user):
    """Métricas de turnos."""
    ts = current_user.ticket_system
    if not ts or not ts.is_enabled:
        return jsonify({'error': 'Sin sistema de turnos'}), 404

    days = request.args.get('days', 7, type=int)
    from datetime import timedelta
    from .timezone_utils import today_start_utc
    day_start = today_start_utc()
    period_start = day_start - timedelta(days=days - 1)

    all_tickets = Ticket.query.filter(
        Ticket.ticket_system_id == ts.id,
        Ticket.created_at >= period_start,
    ).all()

    completed = [t for t in all_tickets if t.status == 'completed']
    cancelled = [t for t in all_tickets if t.status == 'cancelled']
    no_show = [t for t in all_tickets if t.status == 'no_show']

    total_served = len(completed)
    no_show_rate = round(len(no_show) / max(len(all_tickets), 1) * 100, 1)

    # Average service time (minutes)
    service_times = []
    for t in completed:
        if t.called_at and t.completed_at:
            diff = (t.completed_at - t.called_at).total_seconds() / 60
            service_times.append(diff)
    avg_service_time = round(sum(service_times) / max(len(service_times), 1), 1)

    # Daily trend
    from collections import defaultdict
    daily = defaultdict(int)
    for t in all_tickets:
        key = t.created_at.strftime('%d/%m')
        daily[key] += 1
    daily_trend = [{'date': k, 'count': v} for k, v in sorted(daily.items())]

    # By type
    type_stats = {}
    for t in completed:
        if t.ticket_type_id:
            key = t.ticket_type_id
            if key not in type_stats:
                type_stats[key] = {
                    'name': t.ticket_type.name if t.ticket_type else 'N/A',
                    'color': t.ticket_type.color if t.ticket_type else '#6366f1',
                    'count': 0,
                    'service_times': [],
                }
            type_stats[key]['count'] += 1
            if t.called_at and t.completed_at:
                type_stats[key]['service_times'].append(
                    (t.completed_at - t.called_at).total_seconds() / 60
                )

    type_statistics = []
    for v in type_stats.values():
        times = v['service_times']
        avg = round(sum(times) / max(len(times), 1), 1)
        type_statistics.append({
            'name': v['name'],
            'color': v['color'],
            'count': v['count'],
            'avg_service_time': avg,
        })

    # Efficiency score (0-100)
    target = getattr(ts, 'target_service_time', 15) or 15
    efficiency = max(0, min(100, round((1 - max(avg_service_time - target, 0) / max(target, 1)) * 100)))

    return jsonify({
        'total_served': total_served,
        'avg_service_time': avg_service_time,
        'avg_wait_time': 0,  # Could compute if we stored queue join time
        'no_show_rate': no_show_rate,
        'efficiency_score': efficiency,
        'daily_trend': daily_trend,
        'type_statistics': type_statistics,
    })
