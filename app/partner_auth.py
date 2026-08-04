from functools import wraps
from flask import request, jsonify
from . import db
from .models import PartnerApiKey

def partner_api_key_required(f):
    """
    Decorador que valida la API Key de Partner enviada en las cabeceras.
    Soporta:
    - X-API-Key: vcard_sk_...
    - Authorization: Bearer vcard_sk_...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key_raw = request.headers.get('X-API-Key')
        if not api_key_raw:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key_raw = auth_header[7:]

        if not api_key_raw:
            return jsonify({'error': 'Cabecera X-API-Key o Authorization Bearer requerida'}), 401

        if not api_key_raw.startswith('vcard_sk_') or len(api_key_raw) < 15:
            return jsonify({'error': 'Formato de API Key inválido'}), 401

        prefix = api_key_raw[:10]
        keys = PartnerApiKey.query.filter_by(key_prefix=prefix, is_active=True).all()
        matched_key = None
        for key_obj in keys:
            if key_obj.verify_key(api_key_raw):
                matched_key = key_obj
                break

        if not matched_key:
            return jsonify({'error': 'API Key inválida o inactiva'}), 401

        try:
            matched_key.touch_last_used()
            db.session.commit()
        except Exception:
            db.session.rollback()

        return f(matched_key, *args, **kwargs)

    return decorated
