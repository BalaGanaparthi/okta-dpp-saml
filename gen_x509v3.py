#!/usr/bin/env python3
"""
Generate X509v3 certificate for SAML signing
"""
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta

# Generate private key
print("Generating RSA private key...")
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Certificate subject/issuer
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "okta-dpp-saml-production.up.railway.app"),
])

# Build X509v3 certificate
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
    datetime.utcnow() + timedelta(days=365)
).add_extension(
    x509.SubjectAlternativeName([
        x509.DNSName("okta-dpp-saml-production.up.railway.app"),
        x509.DNSName("localhost"),
    ]),
    critical=False,
).add_extension(
    x509.BasicConstraints(ca=False, path_length=None),
    critical=True,
).add_extension(
    x509.KeyUsage(
        digital_signature=True,
        key_encipherment=True,
        content_commitment=False,
        data_encipherment=False,
        key_agreement=False,
        key_cert_sign=False,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False
    ),
    critical=True,
).sign(private_key, hashes.SHA256(), default_backend())

# Save private key
with open('certs/saml.key', 'wb') as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))
print("✓ Private key saved to certs/saml.key")

# Save certificate
with open('certs/saml.crt', 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
print("✓ Certificate saved to certs/saml.crt")

print("\n✅ X509v3 certificate generation complete!")
print(f"Version: {cert.version.name}")
print(f"Serial: {hex(cert.serial_number)}")
print(f"Valid: {cert.not_valid_before_utc} to {cert.not_valid_after_utc}")
