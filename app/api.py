from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from . import db
from .models import PushSubscription
import json

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/push-subscription', methods=['POST'])
@login_required
def save_push_subscription():
    """Save push notification subscription for the current user"""
    try:
        data = request.get_json()

        if not data or 'endpoint' not in data or 'keys' not in data:
            return jsonify({'error': 'Invalid subscription data'}), 400

        # Extract subscription data
        endpoint = data['endpoint']
        p256dh = data['keys'].get('p256dh')
        auth = data['keys'].get('auth')

        if not all([endpoint, p256dh, auth]):
            return jsonify({'error': 'Missing subscription keys'}), 400

        # Check if subscription already exists
        existing = PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=endpoint
        ).first()

        if existing:
            # Update existing subscription
            existing.p256dh = p256dh
            existing.auth = auth
            existing.user_agent = request.headers.get('User-Agent')
        else:
            # Create new subscription
            subscription = PushSubscription(
                user_id=current_user.id,
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(subscription)

        db.session.commit()

        return jsonify({'success': True, 'message': 'Subscription saved'})

    except Exception as e:
        db.session.rollback()
        print(f'Error saving push subscription: {e}')
        return jsonify({'error': 'Failed to save subscription'}), 500

@bp.route('/push-subscription', methods=['DELETE'])
@login_required
def delete_push_subscription():
    """Delete push notification subscription for the current user"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')

        if not endpoint:
            return jsonify({'error': 'Endpoint required'}), 400

        # Delete subscription
        deleted = PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=endpoint
        ).delete()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Deleted {deleted} subscription(s)'
        })

    except Exception as e:
        db.session.rollback()
        print(f'Error deleting push subscription: {e}')
        return jsonify({'error': 'Failed to delete subscription'}), 500

@bp.route('/pwa-analytics', methods=['POST'])
def pwa_analytics():
    """Collect PWA usage analytics"""
    try:
        # This endpoint accepts analytics data from the PWA
        # For now, we'll just acknowledge receipt
        # In the future, this could store analytics data
        return jsonify({'success': True})
    except Exception as e:
        print(f'Error processing PWA analytics: {e}')
        return jsonify({'error': 'Failed to process analytics'}), 500

@bp.route('/vapid-public-key')
def get_vapid_public_key():
    """Get VAPID public key for push notifications"""
    from flask import current_app
    public_key = current_app.config.get('VAPID_PUBLIC_KEY')
    if not public_key:
        return jsonify({'error': 'VAPID keys not configured'}), 500
    return jsonify({'publicKey': public_key})