"""
Script para habilitar reservas de citas en el servicio de Eduardo Reyes
"""
from app import create_app, db
from app.models import Service, Card

app = create_app()

with app.app_context():
    # Buscar la tarjeta de Eduardo Reyes
    card = Card.query.filter_by(slug='eduardo-reyes-vtk1ab').first()

    if not card:
        print("ERROR: No se encontro la tarjeta 'eduardo-reyes-vtk1ab'")
        exit(1)

    print(f"OK Tarjeta encontrada: {card.name} (ID: {card.id})")

    # Obtener todos los servicios de esta tarjeta
    services = Service.query.filter_by(card_id=card.id).all()

    if not services:
        print("ERROR: No se encontraron servicios para esta tarjeta")
        exit(1)

    print(f"\n--- Servicios encontrados: {len(services)} ---")

    for service in services:
        print(f"\nServicio: {service.title}")
        print(f"  ID: {service.id}")
        print(f"  Visible: {service.is_visible}")
        print(f"  Acepta citas (antes): {service.accepts_appointments}")

        # Habilitar reservas de citas
        service.accepts_appointments = True

        print(f"  Acepta citas (despues): {service.accepts_appointments}")

    # Guardar cambios
    db.session.commit()

    print("\nOK Cambios guardados exitosamente!")
    print("\n--- Instrucciones ---")
    print(f"1. Visita: http://127.0.0.1:5000/c/{card.slug}/services")
    print(f"2. Deberias ver el boton 'Reservar Cita' en cada servicio")
    print(f"3. Tambien puedes gestionar las citas desde: http://127.0.0.1:5000/dashboard/appointments")
