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
def tickets_public(username):
    """Página pública para que pacientes tomen turnos"""
    from flask import jsonify, make_response
    from ..models import User, TicketSystem
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
    if not user.ticket_system or not user.ticket_system.is_enabled:
        card = user.cards.first()
        return render_template('public/tickets/not_available.html', card=card), 404

    ticket_system = user.ticket_system

    # Verificar si el sistema está aceptando turnos
    if not ticket_system.is_accepting_tickets:
        card = user.cards.first()
        return render_template('public/tickets/paused.html', system=ticket_system, username=username, card=card)

    # Obtener tipos de citas activos
    ticket_types = ticket_system.get_active_types()

    if not ticket_types:
        card = user.cards.first()
        return render_template('public/tickets/no_types.html', system=ticket_system, card=card)

    # Leer cookies del paciente
    patient_cookie_name = f'patient_info_{ticket_system.id}'
    patient_info = request.cookies.get(patient_cookie_name)

    # Verificar si el paciente ya tiene el máximo de turnos activos (máximo 2)
    if patient_info:
        try:
            patient_data = json.loads(patient_info)
            patient_phone = patient_data.get('phone')
            patient_name = patient_data.get('name')

            from ..models import Ticket

            # Contar turnos activos del paciente
            active_tickets_count = 0
            active_tickets = []
            if patient_phone:
                active_tickets = ticket_system.tickets.filter(
                    Ticket.status.in_(['waiting', 'in_progress']),
                    db.or_(
                        Ticket.patient_phone == patient_phone,
                        Ticket.patient_name == patient_name
                    )
                ).all()
            elif patient_name:
                active_tickets = ticket_system.tickets.filter(
                    Ticket.status.in_(['waiting', 'in_progress']),
                    Ticket.patient_name == patient_name
                ).all()

            active_tickets_count = len(active_tickets)

            # Si ya tiene 2 turnos activos, mostrar mensaje de límite alcanzado
            if active_tickets_count >= 2:
                ticket_numbers = [t.ticket_number for t in active_tickets]
                flash(f'Ya tienes el máximo de turnos activos permitidos (2): {", ".join(ticket_numbers)}. Completa o cancela un turno antes de solicitar otro.', 'warning')
                return redirect(url_for('public.my_tickets', username=username))
        except:
            pass  # Si hay error al parsear cookies, continuar normalmente

    # Preparar formulario para tomar turno con configuración del sistema
    from ..dashboard.forms import TakeTicketForm
    form = TakeTicketForm(
        ticket_types=ticket_types,
        phone_prefix=ticket_system.phone_country_prefix or '+52',
        require_email=ticket_system.require_patient_email,
        collect_birthdate=ticket_system.collect_patient_birthdate
    )

    # Pre-llenar formulario con datos de cookies si existen
    if patient_info and request.method == 'GET':
        try:
            patient_data = json.loads(patient_info)
            form.patient_name.data = patient_data.get('name', '')
            form.patient_phone_country.data = patient_data.get('phone_country', ticket_system.phone_country_prefix or '+52')
            form.patient_phone.data = patient_data.get('phone', '')
            form.patient_email.data = patient_data.get('email', '')
        except:
            pass  # Si hay error al parsear cookies, ignorar

    if form.validate_on_submit():
        from ..models import Ticket, TicketType

        ticket_type = TicketType.query.get(form.ticket_type_id.data)

        if not ticket_type or ticket_type.ticket_system_id != ticket_system.id:
            flash('Tipo de cita inválido', 'error')
            return redirect(url_for('public.tickets_public', username=username))

        # Generar número de ticket
        ticket_number = ticket_type.get_next_ticket_number()

        # Procesar fecha de nacimiento si existe
        patient_birthdate = None
        if ticket_system.collect_patient_birthdate and form.patient_birthdate.data:
            from datetime import datetime
            try:
                patient_birthdate = datetime.strptime(form.patient_birthdate.data, '%Y-%m-%d').date()
            except:
                pass  # Si hay error al parsear, dejar como None

        # Crear nuevo turno
        ticket = Ticket(
            ticket_system_id=ticket_system.id,
            ticket_type_id=ticket_type.id,
            patient_name=form.patient_name.data,
            patient_phone_country=form.patient_phone_country.data,
            patient_phone=form.patient_phone.data,
            patient_email=form.patient_email.data,
            patient_birthdate=patient_birthdate,
            ticket_number=ticket_number,
            status='waiting',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(ticket)
        db.session.commit()

        # Send push notification to the user (clinic owner)
        try:
            from ..push_notifications import send_ticket_notification
            send_ticket_notification(user.id, ticket)
        except Exception as e:
            # Don't fail the ticket creation if notification fails
            print(f"Failed to send ticket notification: {e}")

        # Guardar información del paciente en cookies (30 días)
        patient_data = {
            'name': form.patient_name.data,
            'phone_country': form.patient_phone_country.data or '+52',
            'phone': form.patient_phone.data or '',
            'email': form.patient_email.data or '',
            'last_ticket': ticket_number
        }

        # Crear respuesta con redirección (agregar parámetro para indicar que es un turno nuevo)
        response = make_response(redirect(url_for('public.ticket_status', username=username, ticket_number=ticket_number, new=1)))

        # Establecer cookie con 30 días de expiración
        expires = datetime.now() + timedelta(days=30)
        response.set_cookie(
            patient_cookie_name,
            json.dumps(patient_data),
            expires=expires,
            httponly=True,
            samesite='Lax'
        )

        flash(f'¡Has tomado un turno exitosamente! Tu número es: {ticket_number}', 'success')
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

    card = user.cards.first()
    return render_template('public/tickets/take_ticket.html',
                         system=ticket_system,
                         form=form,
                         ticket_types=ticket_types,
                         username=username,
                         returning_patient=returning_patient,
                         patient_name=patient_name_from_cookie,
                         card=card)

@bp.route('/turnos/<username>/mis-turnos')
def my_tickets(username):
    """Ver los turnos de un paciente basándose en cookies"""
    from ..models import User, TicketSystem, Ticket

    # Buscar usuario
    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.ticket_system or not user.ticket_system.is_enabled:
        abort(404)

    ticket_system = user.ticket_system

    # Leer cookies del paciente
    patient_cookie_name = f'patient_info_{ticket_system.id}'
    patient_info = request.cookies.get(patient_cookie_name)

    if not patient_info:
        flash('No se encontró información de paciente. Por favor, toma un turno primero.', 'warning')
        return redirect(url_for('public.tickets_public', username=username))

    try:
        import json
        patient_data = json.loads(patient_info)
        patient_name = patient_data.get('name')
        patient_phone = patient_data.get('phone')
        patient_email = patient_data.get('email')
    except:
        flash('Error al leer información del paciente.', 'error')
        return redirect(url_for('public.tickets_public', username=username))

    # Buscar todos los turnos del paciente (por nombre y/o teléfono)
    query = ticket_system.tickets

    if patient_phone:
        query = query.filter(
            db.or_(
                Ticket.patient_name == patient_name,
                Ticket.patient_phone == patient_phone
            )
        )
    else:
        query = query.filter(Ticket.patient_name == patient_name)

    # Obtener turnos activos (esperando o en progreso)
    active_tickets = query.filter(
        Ticket.status.in_(['waiting', 'in_progress'])
    ).order_by(Ticket.created_at.desc()).all()

    # Obtener turnos completados recientes (últimos 7 días)
    from ..timezone_utils import today_start_utc
    from datetime import timedelta
    seven_days_ago = today_start_utc() - timedelta(days=7)

    recent_tickets = query.filter(
        Ticket.status.in_(['completed', 'cancelled', 'no_show']),
        Ticket.created_at >= seven_days_ago
    ).order_by(Ticket.created_at.desc()).limit(10).all()

    card = user.cards.first()
    return render_template('public/tickets/my_tickets.html',
                         system=ticket_system,
                         username=username,
                         patient_name=patient_name,
                         active_tickets=active_tickets,
                         recent_tickets=recent_tickets,
                         card=card)

@bp.route('/turnos/<username>/cola')
def tickets_queue(username):
    """Display público de la cola de turnos con auto-actualización"""
    from ..models import User

    # Buscar usuario
    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.ticket_system or not user.ticket_system.is_enabled:
        abort(404)

    ticket_system = user.ticket_system

    # Obtener turno actual (en progreso)
    current_ticket = ticket_system.get_current_ticket()

    # Obtener próximos turnos en espera (limitar a 10)
    from ..models import Ticket
    waiting_tickets = ticket_system.tickets.filter_by(status='waiting')\
        .order_by(Ticket.created_at).limit(10).all()

    card = user.cards.first()
    return render_template('public/tickets/queue_display.html',
                         system=ticket_system,
                         current_ticket=current_ticket,
                         waiting_tickets=waiting_tickets,
                         username=username,
                         card=card)

@bp.route('/turnos/<username>/cola/json')
def tickets_queue_json(username):
    """API JSON para actualización en tiempo real de la cola"""
    from ..models import User, Ticket

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.ticket_system or not user.ticket_system.is_enabled:
        return jsonify({'error': 'No encontrado'}), 404

    ticket_system = user.ticket_system

    # Turno actual
    current_ticket = ticket_system.get_current_ticket()
    current_data = None
    if current_ticket:
        current_data = {
            'ticket_number': current_ticket.ticket_number,
            'patient_name': current_ticket.patient_name if ticket_system.display_mode == 'detailed' else None,
            'type_name': current_ticket.type.name,
            'type_color': current_ticket.type.color
        }

    # Próximos turnos
    waiting_tickets = ticket_system.tickets.filter_by(status='waiting')\
        .order_by(Ticket.created_at).limit(10).all()

    waiting_data = []
    for tkt in waiting_tickets:
        waiting_data.append({
            'ticket_number': tkt.ticket_number,
            'patient_name': tkt.patient_name if ticket_system.display_mode == 'detailed' else None,
            'type_name': tkt.type.name,
            'type_color': tkt.type.color,
            'waiting_time': tkt.get_waiting_time()
        })

    return jsonify({
        'current': current_data,
        'waiting': waiting_data,
        'waiting_count': ticket_system.get_waiting_count()
    })

@bp.route('/turnos/<username>/ticket/<ticket_number>')
def ticket_status(username, ticket_number):
    """Ver estado de un turno específico"""
    from ..models import User, Ticket

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.ticket_system or not user.ticket_system.is_enabled:
        abort(404)

    ticket_system = user.ticket_system

    # Buscar turno por ticket_number
    ticket = ticket_system.tickets.filter_by(ticket_number=ticket_number.upper()).first()

    if not ticket:
        flash('Turno no encontrado', 'error')
        return redirect(url_for('public.tickets_public', username=username))

    # Calcular posición en cola
    position = ticket.get_position_in_queue()

    # Detectar si es un turno recién creado (viene del formulario)
    is_new_ticket = request.args.get('new', '0') == '1'

    card = user.cards.first()
    return render_template('public/tickets/ticket_status.html',
                         system=ticket_system,
                         ticket=ticket,
                         position=position,
                         username=username,
                         card=card,
                         is_new_ticket=is_new_ticket)

@bp.route('/turnos/<username>/ticket/<ticket_number>/status/json')
def ticket_status_json(username, ticket_number):
    """API JSON para estado del turno (para auto-actualización)"""
    from ..models import User, Ticket

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.ticket_system or not user.ticket_system.is_enabled:
        return jsonify({'error': 'No encontrado'}), 404

    ticket_system = user.ticket_system
    ticket = ticket_system.tickets.filter_by(ticket_number=ticket_number.upper()).first()

    if not ticket:
        return jsonify({'error': 'Turno no encontrado'}), 404

    return jsonify({
        'ticket_number': ticket.ticket_number,
        'status': ticket.status,
        'position': ticket.get_position_in_queue(),
        'waiting_time': ticket.get_waiting_time(),
        'type_name': ticket.type.name,
        'type_color': ticket.type.color,
        'current_ticket': ticket_system.get_current_ticket().ticket_number if ticket_system.get_current_ticket() else None
    })

@bp.route('/turnos/<username>/ticket/<ticket_number>/cancelar/<token>', methods=['GET', 'POST'])
def cancel_ticket_public(username, ticket_number, token):
    """Cancelar turno públicamente con token de seguridad"""
    from ..models import User, Ticket

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.ticket_system or not user.ticket_system.is_enabled:
        abort(404)

    ticket_system = user.ticket_system
    ticket = ticket_system.tickets.filter_by(ticket_number=ticket_number.upper()).first()

    if not ticket:
        flash('Turno no encontrado', 'error')
        return redirect(url_for('public.tickets_public', username=username))

    # Verificar token de cancelación
    if not ticket.cancellation_token or ticket.cancellation_token != token:
        flash('Token de cancelación inválido', 'error')
        return redirect(url_for('public.ticket_status', username=username, ticket_number=ticket_number))

    # Verificar que el turno pueda ser cancelado
    if ticket.status not in ['waiting', 'in_progress']:
        flash(f'No se puede cancelar un turno con estado: {ticket.status}', 'warning')
        return redirect(url_for('public.ticket_status', username=username, ticket_number=ticket_number))

    if request.method == 'POST':
        reason = request.form.get('reason', 'Cancelado por el paciente')
        ticket.cancel(reason)
        db.session.commit()

        flash(f'Turno {ticket_number} cancelado exitosamente', 'success')
        return redirect(url_for('public.my_tickets', username=username))

    card = user.cards.first()
    return render_template('public/tickets/cancel_ticket.html',
                         system=ticket_system,
                         ticket=ticket,
                         username=username,
                         card=card)

@bp.route('/turnos/<username>/check-in/<ticket_number>', methods=['POST'])
def check_in_ticket(username, ticket_number):
    """Registrar llegada del paciente al consultorio"""
    from ..models import User, Ticket

    user = User.query.filter(
        db.or_(
            User.email == username.lower(),
            User.email.contains(username.lower())
        )
    ).first()

    if not user or not user.ticket_system or not user.ticket_system.is_enabled:
        return jsonify({'success': False, 'message': 'Sistema no encontrado'}), 404

    ticket_system = user.ticket_system
    ticket = ticket_system.tickets.filter_by(ticket_number=ticket_number.upper()).first()

    if not ticket:
        return jsonify({'success': False, 'message': 'Turno no encontrado'}), 404

    if ticket.status != 'waiting':
        return jsonify({'success': False, 'message': 'Solo se puede hacer check-in de turnos en espera'}), 400

    if ticket.is_checked_in:
        return jsonify({'success': False, 'message': 'Ya has hecho check-in'}), 400

    # Registrar check-in
    ticket.check_in()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Check-in registrado exitosamente',
        'checked_in_at': ticket.checked_in_at.isoformat() if ticket.checked_in_at else None
    })

# ============================================================================
# SISTEMA DE CITAS - Rutas Públicas para Clientes
# ============================================================================

@bp.route('/c/<slug>/servicios/<int:service_id>/reservar', methods=['GET', 'POST'])
def book_appointment(slug, service_id):
    """Página pública para que clientes reserven citas para un servicio"""
    from ..models import Service, Appointment
    from ..dashboard.forms import AppointmentBookingForm
    from datetime import datetime, date

    # Buscar la card y el servicio
    card = Card.query.filter_by(slug=slug).first()

    if not card:
        abort(404)

    # Verificar si usuario está suspendido
    if card.owner.is_suspended:
        return render_template('public/suspended.html',
                             card=card,
                             reason=card.owner.suspension_reason)

    if not card.is_public:
        abort(404)

    # Buscar el servicio
    service = Service.query.filter_by(id=service_id, card_id=card.id).first()

    if not service or not service.is_visible:
        flash('Servicio no encontrado', 'error')
        return redirect(url_for('public.card_services', slug=slug))

    # Verificar que el servicio acepta citas
    if not service.accepts_appointments:
        flash('Este servicio no acepta reservas de citas', 'warning')
        return redirect(url_for('public.card_services', slug=slug))

    # Crear formulario con configuración de la card
    form = AppointmentBookingForm(
        phone_prefix=card.whatsapp_country or '+52',
        require_address=card.require_customer_address
    )

    if form.validate_on_submit():
        # Convertir fecha de string a date
        try:
            appointment_date = datetime.strptime(form.appointment_date.data, '%Y-%m-%d').date()
        except ValueError:
            flash('Fecha inválida', 'error')
            return redirect(url_for('public.book_appointment', slug=slug, service_id=service_id))

        # Verificar que la fecha no sea en el pasado
        if appointment_date < date.today():
            flash('No puedes reservar citas en fechas pasadas', 'error')
            return redirect(url_for('public.book_appointment', slug=slug, service_id=service_id))

        # Crear nueva cita
        appointment = Appointment(
            service_id=service.id,
            card_id=card.id,
            customer_name=form.customer_name.data,
            customer_phone_country=form.customer_phone_country.data,
            customer_phone=form.customer_phone.data,
            customer_address=form.customer_address.data,
            appointment_date=appointment_date,
            appointment_time=form.appointment_time.data,
            notes=form.notes.data,
            status='pending',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(appointment)
        db.session.commit()

        flash('¡Cita reservada exitosamente!', 'success')
        return redirect(url_for('public.appointment_confirmation', slug=slug, appointment_id=appointment.id))

    return render_template('public/appointments/book_appointment.html',
                         card=card,
                         service=service,
                         form=form)

@bp.route('/c/<slug>/cita/<int:appointment_id>/confirmacion')
def appointment_confirmation(slug, appointment_id):
    """Página de confirmación de cita"""
    from ..models import Appointment

    # Buscar la card
    card = Card.query.filter_by(slug=slug).first()

    if not card:
        abort(404)

    # Buscar la cita
    appointment = Appointment.query.filter_by(id=appointment_id, card_id=card.id).first()

    if not appointment:
        flash('Cita no encontrada', 'error')
        return redirect(url_for('public.card_view', slug=slug))

    return render_template('public/appointments/confirmation.html',
                         card=card,
                         appointment=appointment)