#!/usr/bin/env python3
"""
Test that a freshly signed SAML response will validate correctly
This simulates what Okta does when it receives your SAML response
"""
from simple_saml import create_saml_response_simple
from signxml import XMLVerifier
from lxml import etree
import base64

print("=" * 80)
print("TESTING SIGNATURE VALIDATION (Simulating Okta)")
print("=" * 80)

# Load the current certificate and key
with open('certs/saml.crt', 'rb') as f:
    cert = f.read()

with open('certs/saml.key', 'rb') as f:
    key = f.read()

print("\n1. Creating SAML Response with current cert/key...")

# Create a test SAML response
saml_response_b64, saml_response_xml = create_saml_response_simple(
    entity_id='https://okta-dpp-saml-production.up.railway.app',
    acs_url='https://bala-guardianlife-poc.oktapreview.com/sso/saml2/0oawfjmsq71qRFLIN1d7',
    request_id='test_request_123',
    audience='https://www.okta.com/saml2/service-provider/splsozflgjodzjmxdrar',
    user_email='test@example.com',
    is_managed=True,
    is_compliant=True,
    cert=cert,
    key=key
)

print("   ✓ SAML Response created and signed")
print(f"   Base64 length: {len(saml_response_b64)} bytes")

# Decode and parse
print("\n2. Decoding SAML Response (what Okta does)...")
decoded_xml = base64.b64decode(saml_response_b64)
root = etree.fromstring(decoded_xml)
print("   ✓ SAML Response decoded and parsed")

# Extract the embedded certificate
print("\n3. Extracting embedded certificate from signature...")
ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
x509_elem = root.find('.//ds:X509Certificate', namespaces=ns)

if x509_elem is not None:
    embedded_cert_b64 = x509_elem.text.strip()
    embedded_cert_pem = f"-----BEGIN CERTIFICATE-----\n{embedded_cert_b64}\n-----END CERTIFICATE-----"
    print("   ✓ Embedded certificate extracted")

    # Compare fingerprints
    import hashlib

    def get_fingerprint(cert_pem):
        cert_b64 = cert_pem.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').replace('\n', '').strip()
        cert_der = base64.b64decode(cert_b64)
        fp = hashlib.sha256(cert_der).hexdigest()
        return ':'.join([fp[i:i+2].upper() for i in range(0, len(fp), 2)])

    embedded_fp = get_fingerprint(embedded_cert_pem)
    local_fp = get_fingerprint(cert.decode('utf-8'))

    print(f"   Embedded cert fingerprint: {embedded_fp}")
    print(f"   Local cert fingerprint:    {local_fp}")

    if embedded_fp == local_fp:
        print("   ✅ Fingerprints MATCH")
    else:
        print("   ❌ Fingerprints DO NOT MATCH")
else:
    print("   ❌ No certificate found in signature!")
    embedded_cert_pem = None

# Verify the signature (this is what Okta does!)
print("\n4. Verifying signature with embedded certificate (Okta's process)...")
print("   This simulates exactly what Okta will do...")

try:
    verifier = XMLVerifier()

    # Verify using embedded cert (this is what Okta does)
    if embedded_cert_pem:
        verified_data = verifier.verify(root, x509_cert=embedded_cert_pem.encode('utf-8'))
        print("   ✅ Signature VERIFIED with embedded certificate!")
        print("   ✅ This is what Okta should see!")

    # Also verify with local cert for comparison
    print("\n5. Verifying signature with local certificate (double-check)...")
    verifier2 = XMLVerifier()
    verified_data2 = verifier2.verify(root, x509_cert=cert)
    print("   ✅ Signature VERIFIED with local certificate!")

    print("\n" + "=" * 80)
    print("✅ SUCCESS: SIGNATURE VALIDATION PASSED!")
    print("=" * 80)
    print("\nWhat this means:")
    print("✓ Your certs/saml.key and certs/saml.crt are a matching pair")
    print("✓ The SAML response is signed correctly")
    print("✓ Okta WILL BE ABLE to verify the signature")
    print("✓ The signature validation error should be RESOLVED!")

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Ensure the certificate in Okta matches this fingerprint:")
    print(f"   {local_fp}")
    print("\n2. Try the SAML authentication flow again in Okta")
    print("\n3. The signature validation should now succeed!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ SIGNATURE VERIFICATION FAILED!")
    print(f"   Error: {e}")
    print("\n" + "=" * 80)
    print("This means there's still a problem:")
    print("- The key/cert pair don't match")
    print("- OR there's a signing issue")
    print("=" * 80)
    import traceback
    traceback.print_exc()
