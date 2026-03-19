#!/usr/bin/env python3
"""
Test SAML signature generation and verification
"""
from lxml import etree
from signxml import XMLSigner, XMLVerifier, methods
import base64

# Load certificate and key
with open('certs/saml.crt', 'rb') as f:
    cert = f.read()

with open('certs/saml.key', 'rb') as f:
    key = f.read()

# Simple test XML
test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="_test123"
                Version="2.0">
    <saml:Issuer>https://test.example.com</saml:Issuer>
    <samlp:Status>
        <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </samlp:Status>
</samlp:Response>"""

print("=" * 70)
print("Testing SAML Signature")
print("=" * 70)

# Parse XML
root = etree.fromstring(test_xml.encode('utf-8'))
print("✓ XML parsed successfully")

# Sign the XML
print("\nSigning XML...")
signer = XMLSigner(
    method=methods.enveloped,
    signature_algorithm='rsa-sha256',
    digest_algorithm='sha256'
)

try:
    signed = signer.sign(root, key=key, cert=cert)
    print("✓ XML signed successfully")

    # Print the signed XML
    signed_xml = etree.tostring(signed, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    print("\nSigned XML:")
    print("=" * 70)
    print(signed_xml.decode('utf-8'))
    print("=" * 70)

    # Verify the signature
    print("\nVerifying signature...")
    verifier = XMLVerifier()

    # Try to verify
    verified = verifier.verify(signed, x509_cert=cert)
    print("✓ Signature verified successfully!")

    # Check what certificate is in the signature
    sig_elem = signed.find('.//{http://www.w3.org/2000/09/xmldsig#}Signature')
    if sig_elem is not None:
        x509_cert_elem = sig_elem.find('.//{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
        if x509_cert_elem is not None:
            embedded_cert = x509_cert_elem.text
            print(f"\n✓ Certificate embedded in signature (length: {len(embedded_cert)} chars)")

            # Compare with our certificate
            cert_str = cert.decode('utf-8')
            cert_content = cert_str.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').replace('\n', '').strip()

            if embedded_cert.strip() == cert_content.strip():
                print("✓ Embedded certificate matches certs/saml.crt")
            else:
                print("✗ WARNING: Embedded certificate does NOT match certs/saml.crt")
                print(f"  Expected length: {len(cert_content)}")
                print(f"  Actual length: {len(embedded_cert)}")
        else:
            print("✗ No X509Certificate element found in signature")
    else:
        print("✗ No Signature element found")

    print("\n" + "=" * 70)
    print("✅ Signature test PASSED - Signing and verification work correctly")
    print("=" * 70)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("❌ Signature test FAILED")
    print("=" * 70)
