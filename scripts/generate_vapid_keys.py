#!/usr/bin/env python3
"""
Script to generate VAPID keys for push notifications
"""
import base64
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

def generate_vapid_keys():
    """Generate VAPID key pair for push notifications"""
    # Generate ECDSA P-256 key pair
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Get public key
    public_key = private_key.public_key()

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key to uncompressed format
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # Base64url encode the keys
    private_b64 = base64.urlsafe_b64encode(private_pem).decode('utf-8').rstrip('=')
    public_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')

    return private_b64, public_b64

def main():
    print("Generating VAPID keys for push notifications...")
    private_key, public_key = generate_vapid_keys()

    print("\nVAPID Keys Generated Successfully!")
    print("=" * 50)
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_SUBJECT=mailto:admin@atscard.app")
    print("=" * 50)
    print("\nAdd these environment variables to your .env file:")
    print("VAPID_PRIVATE_KEY=" + private_key)
    print("VAPID_PUBLIC_KEY=" + public_key)
    print("VAPID_SUBJECT=mailto:admin@atscard.app")

    # Also create/update .env file
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"\nUpdating existing {env_file} file...")
    else:
        print(f"\nCreating {env_file} file...")

    with open(env_file, 'a') as f:
        f.write(f"\n# VAPID keys for push notifications\n")
        f.write(f"VAPID_PRIVATE_KEY={private_key}\n")
        f.write(f"VAPID_PUBLIC_KEY={public_key}\n")
        f.write(f"VAPID_SUBJECT=mailto:admin@atscard.app\n")

    print(f"Keys added to {env_file}")
    print("\nRestart your application to load the new environment variables.")

if __name__ == '__main__':
    main()