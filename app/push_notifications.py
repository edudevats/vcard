import requests
import json
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import base64
import os
from flask import current_app

class PushNotificationService:
    """Service for sending push notifications using Web Push protocol"""

    def __init__(self):
        self.vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
        self.vapid_public_key = current_app.config.get('VAPID_PUBLIC_KEY')
        self.vapid_subject = current_app.config.get('VAPID_SUBJECT', 'mailto:admin@example.com')

    def send_notification(self, subscription, title, body, data=None, icon=None, badge=None):
        """Send a push notification to a single subscription"""
        if not self.vapid_private_key or not self.vapid_public_key:
            print("VAPID keys not configured, skipping push notification")
            return False

        try:
            # Prepare the payload
            payload = {
                'title': title,
                'body': body,
                'icon': icon or '/static/icons/icon-192x192.png',
                'badge': badge or '/static/icons/badge-72x72.png',
                'data': data or {},
                'timestamp': int(time.time())
            }

            # Convert subscription to dict if it's a model instance
            if hasattr(subscription, 'to_dict'):
                sub_dict = subscription.to_dict()
            else:
                sub_dict = subscription

            # Send the notification
            response = self._send_web_push(sub_dict, json.dumps(payload))

            if response.status_code == 201:
                print(f"Push notification sent successfully to {sub_dict['endpoint'][:50]}...")
                return True
            else:
                print(f"Failed to send push notification: {response.status_code} - {response.text}")
                # If subscription is expired/invalid, we should remove it
                if response.status_code in [400, 410]:
                    self._handle_invalid_subscription(subscription)
                return False

        except Exception as e:
            print(f"Error sending push notification: {e}")
            return False

    def send_notification_to_user(self, user_id, title, body, data=None, icon=None, badge=None):
        """Send push notification to all subscriptions of a user"""
        from .models import PushSubscription

        subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()

        if not subscriptions:
            print(f"No push subscriptions found for user {user_id}")
            return 0

        sent_count = 0
        for subscription in subscriptions:
            if self.send_notification(subscription, title, body, data, icon, badge):
                sent_count += 1

        return sent_count

    def _send_web_push(self, subscription_info, payload):
        """Send web push notification using HTTP requests"""
        endpoint = subscription_info['endpoint']
        p256dh = subscription_info['keys']['p256dh']
        auth = subscription_info['keys']['auth']

        # Generate the encryption keys
        salt = os.urandom(16)

        # Create the encrypted payload
        encrypted_payload = self._encrypt_payload(payload, p256dh, auth, salt)

        # Create JWT for VAPID
        jwt = self._create_vapid_jwt(endpoint)

        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Encoding': 'aes128gcm',
            'Encryption': f'keyid=p256dh;salt={base64.urlsafe_b64encode(salt).decode().rstrip("=")}',
            'Crypto-Key': f'p256dh={p256dh};dh={self.vapid_public_key}',
            'Authorization': f'WebPush {jwt}',
            'TTL': '2419200'  # 28 days
        }

        return requests.post(endpoint, data=encrypted_payload, headers=headers, timeout=10)

    def _encrypt_payload(self, payload, p256dh, auth, salt):
        """Encrypt the payload for Web Push"""
        # This is a simplified implementation
        # In production, you should use a proper Web Push encryption library
        # For now, we'll use a basic approach
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        import struct

        # Decode the keys
        server_public_key = base64.urlsafe_b64decode(self.vapid_public_key + '==')
        client_public_key = base64.urlsafe_b64decode(p256dh + '==')
        client_auth = base64.urlsafe_b64decode(auth + '==')

        # Generate ephemeral key pair
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()

        # Calculate shared secret
        shared_secret = private_key.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), client_public_key))

        # Derive encryption keys
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=client_auth,
            info=b'Content-Encoding: aes128gcm\x00',
            backend=default_backend()
        )
        key = hkdf.derive(shared_secret)

        # Split key into encryption key and nonce
        encryption_key = key[:16]
        nonce = key[16:32]

        # Encrypt payload
        cipher = Cipher(algorithms.AES(encryption_key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()

        # Add padding
        payload_bytes = payload.encode('utf-8')
        padding_length = 0
        padded_payload = struct.pack('!H', padding_length) + payload_bytes

        encrypted = encryptor.update(padded_payload) + encryptor.finalize()
        tag = encryptor.tag

        return encrypted + tag

    def _create_vapid_jwt(self, endpoint):
        """Create VAPID JWT token"""
        import jwt
        import time

        # Extract origin from endpoint
        from urllib.parse import urlparse
        origin = urlparse(endpoint).scheme + '://' + urlparse(endpoint).netloc

        now = int(time.time())

        payload = {
            'aud': origin,
            'exp': now + 43200,  # 12 hours
            'iat': now,
            'sub': self.vapid_subject
        }

        # Load private key
        private_key_pem = f"-----BEGIN PRIVATE KEY-----\n{self.vapid_private_key}\n-----END PRIVATE KEY-----"
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )

        # Sign JWT
        token = jwt.encode(payload, private_key, algorithm='ES256')
        return token

    def _handle_invalid_subscription(self, subscription):
        """Handle invalid/expired subscriptions"""
        try:
            from . import db
            if hasattr(subscription, 'delete'):
                db.session.delete(subscription)
                db.session.commit()
                print(f"Removed invalid subscription: {subscription}")
        except Exception as e:
            print(f"Error removing invalid subscription: {e}")

# Global instance
push_service = PushNotificationService()

def send_ticket_notification(user_id, ticket):
    """Send notification for new ticket in queue system"""
    title = f"Nuevo turno: {ticket.ticket_number}"
    body = f"Paciente: {ticket.patient_name} - Tipo: {ticket.type.name}"

    data = {
        'type': 'new_ticket',
        'ticket_id': ticket.id,
        'ticket_number': ticket.ticket_number,
        'url': f'/dashboard/tickets'
    }

    return push_service.send_notification_to_user(user_id, title, body, data)

def send_appointment_notification(user_id, appointment, notification_type='new'):
    """Send notification for appointment events"""

    # Customize title and body based on notification type
    if notification_type == 'new':
        title = "Nueva Cita Reservada"
        body = f"{appointment.customer_name} reservó {appointment.service.name} para el {appointment.appointment_date.strftime('%d/%m/%Y')} a las {appointment.appointment_time}"
    elif notification_type == 'confirmed':
        title = "Cita Confirmada"
        body = f"Cita con {appointment.customer_name} confirmada para {appointment.appointment_date.strftime('%d/%m/%Y')} a las {appointment.appointment_time}"
    elif notification_type == 'reminder':
        title = "Recordatorio de Cita"
        body = f"Cita con {appointment.customer_name} hoy a las {appointment.appointment_time}"
    else:
        title = "Actualización de Cita"
        body = f"La cita #{appointment.id} ha sido actualizada"

    data = {
        'type': f'appointment_{notification_type}',
        'appointment_id': appointment.id,
        'customer_name': appointment.customer_name,
        'service_name': appointment.service.name,
        'date': appointment.appointment_date.strftime('%Y-%m-%d'),
        'time': appointment.appointment_time,
        'url': '/dashboard/appointments'
    }

    return push_service.send_notification_to_user(user_id, title, body, data)