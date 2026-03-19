#!/usr/bin/env python3
"""
Check if private key matches certificate
"""
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

print("=" * 80)
print("CHECKING IF PRIVATE KEY MATCHES CERTIFICATE")
print("=" * 80)

# Load certificate
with open('certs/saml.crt', 'rb') as f:
    cert_data = f.read()
    cert = x509.load_pem_x509_certificate(cert_data, default_backend())

# Load private key
with open('certs/saml.key', 'rb') as f:
    key_data = f.read()
    private_key = serialization.load_pem_private_key(key_data, password=None, backend=default_backend())

# Get public key from certificate
cert_public_key = cert.public_key()

# Get public key from private key
key_public_key = private_key.public_key()

# Get public key numbers for comparison
cert_public_numbers = cert_public_key.public_numbers()
key_public_numbers = key_public_key.public_numbers()

print("\n1. Certificate Public Key:")
print(f"   Modulus (first 50 chars): {str(cert_public_numbers.n)[:50]}...")
print(f"   Exponent: {cert_public_numbers.e}")

print("\n2. Private Key's Public Key:")
print(f"   Modulus (first 50 chars): {str(key_public_numbers.n)[:50]}...")
print(f"   Exponent: {key_public_numbers.e}")

if cert_public_numbers.n == key_public_numbers.n and cert_public_numbers.e == key_public_numbers.e:
    print("\n✅ MATCH: Private key corresponds to the certificate")
    print("=" * 80)
else:
    print("\n❌ MISMATCH: Private key does NOT match the certificate!")
    print("=" * 80)
    print("\nThis explains why Okta rejects the signature:")
    print("- The SAML response is signed with certs/saml.key")
    print("- But certs/saml.key does NOT match certs/saml.crt")
    print("- You uploaded certs/saml.crt to Okta")
    print("- So Okta cannot verify the signature")
    print("\nSOLUTION: Generate a new matching certificate and key pair!")
