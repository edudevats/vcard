"""Utility para eximir blueprints de la protección CSRF."""


def csrf_exempt_mobile(csrf_instance, blueprint):
    """Exime todos los endpoints de un blueprint de la validación CSRF.

    Necesario para la API móvil que usa Bearer Token en lugar de
    cookies/formularios de sesión.
    Debe llamarse ANTES de registrar el blueprint.
    """
    csrf_instance.exempt(blueprint)
