"""
REST API para la app móvil de ATScard.
Usa autenticación por token (Bearer Token).
Base URL: /api/mobile/v1
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from datetime import datetime, date
import secrets

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
        'image_url': f"/static/{item.image_path}" if item.image_path else None,
        'thumb_url': f"/static/{item.thumb_path}" if item.thumb_path else None,
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
