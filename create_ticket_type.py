"""
Script para crear un tipo de ticket de ejemplo para el admin
"""
from app import create_app, db
from app.models import User, TicketSystem, TicketType

app = create_app()

with app.app_context():
    # Buscar el usuario admin
    admin = User.query.filter_by(email='admin@test.com').first()

    if not admin:
        print("ERROR: Usuario admin@test.com no encontrado")
        exit(1)

    print(f"OK Usuario encontrado: {admin.email}")

    # Verificar que tenga sistema de tickets
    if not admin.ticket_system:
        print("ERROR: El usuario no tiene sistema de tickets activado")
        exit(1)

    print(f"OK Sistema de tickets activo")

    # Verificar si ya hay tipos de tickets
    existing_types = admin.ticket_system.get_active_types()
    print(f"Tipos de tickets existentes: {len(existing_types)}")

    if existing_types:
        print("\nTipos existentes:")
        for t in existing_types:
            print(f"  - {t.name} (Prefijo: {t.prefix}, Color: {t.color})")

    # Crear tipo de ticket de ejemplo si no existe
    if len(existing_types) == 0:
        print("\nCreando tipo de ticket de ejemplo...")

        ticket_type = TicketType(
            ticket_system_id=admin.ticket_system.id,
            name='Consulta General',
            description='Consulta medica general',
            color='#3b82f6',
            estimated_duration=30,
            prefix='A',
            is_active=True,
            order_index=1
        )

        db.session.add(ticket_type)
        db.session.commit()

        print(f"OK Tipo de ticket creado: {ticket_type.name} (Prefijo: {ticket_type.prefix})")
    else:
        print("\nYa existen tipos de tickets, no se creo ninguno nuevo")

    # Mostrar resumen final
    print("\n=== RESUMEN ===")
    print(f"Sistema de tickets: {'ACTIVO' if admin.ticket_system.is_enabled else 'INACTIVO'}")
    print(f"Tipos de tickets activos: {admin.ticket_system.ticket_types.filter_by(is_active=True).count()}")
    print(f"Aceptando turnos: {'SI' if admin.ticket_system.is_accepting_tickets else 'NO'}")
