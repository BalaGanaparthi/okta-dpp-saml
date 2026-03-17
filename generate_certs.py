#!/usr/bin/env python3
"""
Generate self-signed certificates for SAML signing
"""
import os
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_self_signed_cert(output_dir='certs'):
    """Generate self-signed certificate and private key"""

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate private key
    print("Generating RSA private key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Generate certificate
    print("Generating self-signed certificate...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Device Posture Provider"),
        x509.NameAttribute(NameOID.COMMON_NAME, "dpp.example.com"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=3650)  # Valid for 10 years
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("dpp.example.com"),
            x509.DNSName("localhost"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())

    # Write private key to file
    key_path = os.path.join(output_dir, 'saml.key')
    with open(key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"✓ Private key saved to: {key_path}")

    # Write certificate to file
    cert_path = os.path.join(output_dir, 'saml.crt')
    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"✓ Certificate saved to: {cert_path}")

    print("\n✅ Certificate generation complete!")
    print("Note: These are self-signed certificates for development/testing only.")


if __name__ == '__main__':
    generate_self_signed_cert()
