from flask import render_template, abort, request, redirect, url_for, flash, jsonify
from ..models import Card, Product, CardView
from .. import db, cache
from . import bp
from ..analytics import AnalyticsService

def record_view(card):
    """Record a view for the given card with enhanced analytics"""
    view = AnalyticsService.track_card_view(card, request)
    db.session.add(view)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

@bp.route('/c/<slug>')
@cache.cached(timeout=300, key_prefix='card_view_%s')
def card_view(slug):
    # Use cached query for better performance
    cache_key = f'card_data_{slug}'
    card = cache.get(cache_key)
    
    if not card:
        card = Card.query.filter_by(slug=slug).first()
        if card and card.is_public and not card.owner.is_suspended:
            cache.set(cache_key, card, timeout=300)  # Cache for 5 minutes
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    # Record the view (don't cache this part)
    record_view(card)
    
    # Cache queries for related data
    services_key = f'card_services_{card.id}'
    services = cache.get(services_key)
    if not services:
        services = card.services.filter_by(is_visible=True).order_by('order_index').all()
        cache.set(services_key, services, timeout=600)
    
    products_key = f'card_products_{card.id}'
    products = cache.get(products_key)
    if not products:
        products = card.products.filter_by(is_visible=True).order_by('order_index').all()
        cache.set(products_key, products, timeout=600)
    
    gallery_key = f'card_gallery_{card.id}'
    gallery_items = cache.get(gallery_key)
    if not gallery_items:
        gallery_items = card.gallery_items.filter_by(is_visible=True).order_by('order_index').all()
        cache.set(gallery_key, gallery_items, timeout=600)
    
    featured_key = f'card_featured_{card.id}'
    featured_image = cache.get(featured_key)
    if featured_image is None:  # Use None check because False is valid
        featured_image = card.gallery_items.filter_by(is_featured=True, is_visible=True).first()
        cache.set(featured_key, featured_image, timeout=600)
    
    # Get social networks for the card
    social_links = card.get_primary_social_networks()
    
    # Get the theme template path
    template_path = card.theme.get_template_path() if card.theme else 'public/themes/classic.html'
    
    # Fallback to classic if template doesn't exist
    try:
        return render_template(template_path, 
                             card=card, 
                             services=services,
                             products=products, 
                             gallery_items=gallery_items,
                             featured_image=featured_image,
                             social_links=social_links)
    except:
        return render_template('public/themes/classic.html', 
                             card=card, 
                             services=services,
                             products=products, 
                             gallery_items=gallery_items,
                             featured_image=featured_image,
                             social_links=social_links)

@bp.route('/c/<slug>/services')
def card_services(slug):
    card = Card.query.filter_by(slug=slug).first()
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    services = card.services.filter_by(is_visible=True).order_by('order_index').all()
    
    return render_template('public/services.html', 
                         card=card, 
                         services=services)

@bp.route('/c/<slug>/gallery')
def card_gallery(slug):
    card = Card.query.filter_by(slug=slug).first()
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    gallery_items = card.gallery_items.filter_by(is_visible=True).order_by('order_index').all()
    
    return render_template('public/gallery.html',
                         card=card,
                         gallery_items=gallery_items)

@bp.route('/c/<slug>/productos')
def card_products(slug):
    card = Card.query.filter_by(slug=slug).first()
    
    if not card:
        abort(404)
    
    # Check if user is suspended
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)
    
    if not card.is_public:
        abort(404)
    
    products = card.products.filter_by(is_visible=True).order_by(Product.order_index.asc(), Product.created_at.desc()).all()
    
    return render_template('public/products.html',
                         card=card,
                         products=products)


@bp.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html')

@bp.route('/share-target', methods=['GET', 'POST'])
def share_target():
    """PWA Share Target API handler"""
    from flask import redirect, url_for, session
    from flask_login import current_user
    
    if not current_user.is_authenticated:
        # Store shared content in session and redirect to login
        if request.method == 'POST':
            session['shared_content'] = {
                'title': request.form.get('title', ''),
                'text': request.form.get('text', ''),
                'url': request.form.get('url', ''),
                'files': request.files.getlist('files') if 'files' in request.files else []
            }
        return redirect(url_for('auth.login') + '?next=' + url_for('dashboard.new_card') + '&shared=true')
    
    if request.method == 'POST':
        # Handle shared content
        shared_title = request.form.get('title', '')
        shared_text = request.form.get('text', '')
        shared_url = request.form.get('url', '')
        shared_files = request.files.getlist('files') if 'files' in request.files else []
        
        # Store in session for use in new card creation
        session['shared_content'] = {
            'title': shared_title,
            'text': shared_text,
            'url': shared_url,
            'files': shared_files
        }
        
        return redirect(url_for('dashboard.new_card', shared='true'))
    
    # GET request - redirect to dashboard
    return redirect(url_for('dashboard.index', shared='true'))


@bp.route('/pwa-test')
def pwa_test():
    """PWA functionality test page"""
    return render_template('pwa_test.html')

# ============================================================================
# SISTEMA DE TURNOS - Rutas Públicas para Pacientes
# ============================================================================

@bp.route('/turnos/<username>', methods=['GET', 'POST'])
def appointments_public(username):
    """Página pública para que pacientes tomen turnos"""
    from flask import jsonify, make_response
    from ..models import User, AppointmentSystem
    from datetime import datetime, timedelta
    import json

    # Buscar usuario por email (username puede ser el email o slug)
    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user:
        abort(404)

    # Verificar que tenga sistema de turnos habilitado
    if not user.appointment_system or not user.appointment_system.is_enabled:
        return render_template('public/appointments/not_available.html'), 404

    system = user.appointment_system

    # Obtener tipos de citas activos
    appointment_types = system.get_active_types()

    if not appointment_types:
        return render_template('public/appointments/no_types.html', system=system)

    # Leer cookies del paciente
    patient_cookie_name = f'patient_info_{system.id}'
    patient_info = request.cookies.get(patient_cookie_name)

    # Preparar formulario para tomar turno
    from ..dashboard.forms import TakeAppointmentForm
    form = TakeAppointmentForm(appointment_types=appointment_types)

    # Pre-llenar formulario con datos de cookies si existen
    if patient_info and request.method == 'GET':
        try:
            patient_data = json.loads(patient_info)
            form.patient_name.data = patient_data.get('name', '')
            form.patient_phone.data = patient_data.get('phone', '')
            form.patient_email.data = patient_data.get('email', '')
        except:
            pass  # Si hay error al parsear cookies, ignorar

    if form.validate_on_submit():
        from ..models import Appointment, AppointmentType

        appointment_type = AppointmentType.query.get(form.appointment_type_id.data)

        if not appointment_type or appointment_type.appointment_system_id != system.id:
            flash('Tipo de cita inválido', 'error')
            return redirect(url_for('public.appointments_public', username=username))

        # Generar número de ticket
        ticket_number = appointment_type.get_next_ticket_number()

        # Crear nuevo turno
        appointment = Appointment(
            appointment_system_id=system.id,
            appointment_type_id=appointment_type.id,
            patient_name=form.patient_name.data,
            patient_phone=form.patient_phone.data,
            patient_email=form.patient_email.data,
            ticket_number=ticket_number,
            status='waiting',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(appointment)
        db.session.commit()

        # Guardar información del paciente en cookies (30 días)
        patient_data = {
            'name': form.patient_name.data,
            'phone': form.patient_phone.data or '',
            'email': form.patient_email.data or '',
            'last_ticket': ticket_number
        }

        # Crear respuesta con redirección
        response = make_response(redirect(url_for('public.appointment_ticket', username=username, ticket_number=ticket_number)))

        # Establecer cookie con 30 días de expiración
        expires = datetime.now() + timedelta(days=30)
        response.set_cookie(
            patient_cookie_name,
            json.dumps(patient_data),
            expires=expires,
            httponly=True,
            samesite='Lax'
        )

        flash(f'¡Turno tomado exitosamente! Tu número es: {ticket_number}', 'success')
        return response

    # Pasar información de cookies a la plantilla para mensajes de bienvenida
    returning_patient = False
    patient_name_from_cookie = None
    if patient_info:
        try:
            patient_data = json.loads(patient_info)
            patient_name_from_cookie = patient_data.get('name')
            if patient_name_from_cookie:
                returning_patient = True
        except:
            pass

    return render_template('public/appointments/take_ticket.html',
                         system=system,
                         form=form,
                         appointment_types=appointment_types,
                         username=username,
                         returning_patient=returning_patient,
                         patient_name=patient_name_from_cookie)

@bp.route('/turnos/<username>/mis-turnos')
def my_appointments(username):
    """Ver los turnos de un paciente basándose en cookies"""
    from ..models import User, AppointmentSystem, Appointment

    # Buscar usuario
    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.appointment_system or not user.appointment_system.is_enabled:
        abort(404)

    system = user.appointment_system

    # Leer cookies del paciente
    patient_cookie_name = f'patient_info_{system.id}'
    patient_info = request.cookies.get(patient_cookie_name)

    if not patient_info:
        flash('No se encontró información de paciente. Por favor, toma un turno primero.', 'warning')
        return redirect(url_for('public.appointments_public', username=username))

    try:
        import json
        patient_data = json.loads(patient_info)
        patient_name = patient_data.get('name')
        patient_phone = patient_data.get('phone')
        patient_email = patient_data.get('email')
    except:
        flash('Error al leer información del paciente.', 'error')
        return redirect(url_for('public.appointments_public', username=username))

    # Buscar todos los turnos del paciente (por nombre y/o teléfono)
    query = system.appointments

    if patient_phone:
        query = query.filter(
            db.or_(
                Appointment.patient_name == patient_name,
                Appointment.patient_phone == patient_phone
            )
        )
    else:
        query = query.filter(Appointment.patient_name == patient_name)

    # Obtener turnos activos (esperando o en progreso)
    active_appointments = query.filter(
        Appointment.status.in_(['waiting', 'in_progress'])
    ).order_by(Appointment.created_at.desc()).all()

    # Obtener turnos completados recientes (últimos 7 días)
    from ..timezone_utils import today_start_utc
    from datetime import timedelta
    seven_days_ago = today_start_utc() - timedelta(days=7)

    recent_appointments = query.filter(
        Appointment.status.in_(['completed', 'cancelled', 'no_show']),
        Appointment.created_at >= seven_days_ago
    ).order_by(Appointment.created_at.desc()).limit(10).all()

    return render_template('public/appointments/my_tickets.html',
                         system=system,
                         username=username,
                         patient_name=patient_name,
                         active_appointments=active_appointments,
                         recent_appointments=recent_appointments)

@bp.route('/turnos/<username>/cola')
def appointments_queue(username):
    """Display público de la cola de turnos con auto-actualización"""
    from ..models import User

    # Buscar usuario
    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.appointment_system or not user.appointment_system.is_enabled:
        abort(404)

    system = user.appointment_system

    # Obtener turno actual (en progreso)
    current_appointment = system.get_current_appointment()

    # Obtener próximos turnos en espera (limitar a 10)
    from ..models import Appointment
    waiting_appointments = system.appointments.filter_by(status='waiting')\
        .order_by(Appointment.created_at).limit(10).all()

    return render_template('public/appointments/queue_display.html',
                         system=system,
                         current_appointment=current_appointment,
                         waiting_appointments=waiting_appointments,
                         username=username)

@bp.route('/turnos/<username>/cola/json')
def appointments_queue_json(username):
    """API JSON para actualización en tiempo real de la cola"""
    from ..models import User, Appointment

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.appointment_system or not user.appointment_system.is_enabled:
        return jsonify({'error': 'No encontrado'}), 404

    system = user.appointment_system

    # Turno actual
    current_appointment = system.get_current_appointment()
    current_data = None
    if current_appointment:
        current_data = {
            'ticket_number': current_appointment.ticket_number,
            'patient_name': current_appointment.patient_name if system.display_mode == 'detailed' else None,
            'type_name': current_appointment.type.name,
            'type_color': current_appointment.type.color
        }

    # Próximos turnos
    waiting_appointments = system.appointments.filter_by(status='waiting')\
        .order_by(Appointment.created_at).limit(10).all()

    waiting_data = []
    for apt in waiting_appointments:
        waiting_data.append({
            'ticket_number': apt.ticket_number,
            'patient_name': apt.patient_name if system.display_mode == 'detailed' else None,
            'type_name': apt.type.name,
            'type_color': apt.type.color,
            'waiting_time': apt.get_waiting_time()
        })

    return jsonify({
        'current': current_data,
        'waiting': waiting_data,
        'waiting_count': system.get_waiting_count()
    })

@bp.route('/turnos/<username>/ticket/<ticket_number>')
def appointment_ticket(username, ticket_number):
    """Ver estado de un turno específico"""
    from ..models import User, Appointment

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.appointment_system or not user.appointment_system.is_enabled:
        abort(404)

    system = user.appointment_system

    # Buscar turno por ticket_number
    appointment = system.appointments.filter_by(ticket_number=ticket_number.upper()).first()

    if not appointment:
        flash('Turno no encontrado', 'error')
        return redirect(url_for('public.appointments_public', username=username))

    # Calcular posición en cola
    position = appointment.get_position_in_queue()

    return render_template('public/appointments/ticket_status.html',
                         system=system,
                         appointment=appointment,
                         position=position,
                         username=username)

@bp.route('/turnos/<username>/ticket/<ticket_number>/status/json')
def appointment_ticket_status_json(username, ticket_number):
    """API JSON para estado del turno (para auto-actualización)"""
    from ..models import User, Appointment

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.appointment_system or not user.appointment_system.is_enabled:
        return jsonify({'error': 'No encontrado'}), 404

    system = user.appointment_system
    appointment = system.appointments.filter_by(ticket_number=ticket_number.upper()).first()

    if not appointment:
        return jsonify({'error': 'Turno no encontrado'}), 404

    return jsonify({
        'ticket_number': appointment.ticket_number,
        'status': appointment.status,
        'position': appointment.get_position_in_queue(),
        'waiting_time': appointment.get_waiting_time(),
        'type_name': appointment.type.name,
        'type_color': appointment.type.color,
        'current_ticket': system.get_current_appointment().ticket_number if system.get_current_appointment() else None
    })