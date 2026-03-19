#!/usr/bin/env python3
"""
Test signing and verifying a fresh SAML response
"""
import base64
import uuid
from datetime import datetime, timedelta
from lxml import etree
from signxml import XMLSigner, XMLVerifier, methods

# Load certificate and key
with open('certs/saml.crt', 'rb') as f:
    cert = f.read()

with open('certs/saml.key', 'rb') as f:
    key = f.read()

print("=" * 80)
print("TESTING FRESH SAML RESPONSE SIGNING")
print("=" * 80)

# Create a simple SAML Response
now = datetime.utcnow()
response_id = f"_{uuid.uuid4().hex}"
assertion_id = f"_{uuid.uuid4().hex}"
device_id = f"TEST-{uuid.uuid4().hex[:12].upper()}"

issue_instant = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
not_before = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
not_on_or_after = (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

SAML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                Destination="https://bala-guardianlife-poc.oktapreview.com/sso/saml2/0oawfjmsq71qRFLIN1d7"
                ID="{response_id}"
                InResponseTo="id6087551157895439496656930161"
                IssueInstant="{issue_instant}"
                Version="2.0">
    <saml:Issuer>https://okta-dpp-saml-production.up.railway.app</saml:Issuer>
    <samlp:Status>
        <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </samlp:Status>
    <saml:Assertion ID="{assertion_id}"
                    IssueInstant="{issue_instant}"
                    Version="2.0">
        <saml:Issuer>https://okta-dpp-saml-production.up.railway.app</saml:Issuer>
        <saml:Subject>
            <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">test@example.com</saml:NameID>
            <saml:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
                <saml:SubjectConfirmationData InResponseTo="id6087551157895439496656930161"
                                              NotOnOrAfter="{not_on_or_after}"
                                              Recipient="https://bala-guardianlife-poc.oktapreview.com/sso/saml2/0oawfjmsq71qRFLIN1d7"/>
            </saml:SubjectConfirmation>
        </saml:Subject>
        <saml:Conditions NotBefore="{not_before}" NotOnOrAfter="{not_on_or_after}">
            <saml:AudienceRestriction>
                <saml:Audience>https://www.okta.com/saml2/service-provider/splsozflgjodzjmxdrar</saml:Audience>
            </saml:AudienceRestriction>
        </saml:Conditions>
        <saml:AuthnStatement AuthnInstant="{issue_instant}" SessionIndex="{assertion_id}">
            <saml:AuthnContext>
                <saml:AuthnContextClassRef>urn:okta:saml:2.0:DevicePosture</saml:AuthnContextClassRef>
            </saml:AuthnContext>
        </saml:AuthnStatement>
    </saml:Assertion>
</samlp:Response>"""

response_xml = SAML_TEMPLATE.format(
    response_id=response_id,
    assertion_id=assertion_id,
    issue_instant=issue_instant,
    not_before=not_before,
    not_on_or_after=not_on_or_after
)

# Parse to element
response_elem = etree.fromstring(response_xml.encode('utf-8'))
print(f"✓ Created SAML Response with ID: {response_id}")

# Sign the response
print("\nSigning with certs/saml.key and certs/saml.crt...")
signer = XMLSigner(
    method=methods.enveloped,
    signature_algorithm='rsa-sha256',
    digest_algorithm='sha256'
)

try:
    signed_response = signer.sign(response_elem, key=key, cert=cert)
    print("✓ Signing completed")

    # Convert to string
    signed_xml = etree.tostring(signed_response, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    # Try to verify the signature immediately
    print("\nVerifying signature...")
    verifier = XMLVerifier()
    verified = verifier.verify(signed_response, x509_cert=cert)
    print("✅ SIGNATURE VERIFICATION SUCCESSFUL!")
    print("   The freshly signed SAML response signature is VALID")

    # Save for comparison
    with open('/tmp/fresh_signed.xml', 'wb') as f:
        f.write(signed_xml)
    print("\n✓ Saved to /tmp/fresh_signed.xml")

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("The signing process works correctly with the current key/cert.")
    print("The issue must be that the failing SAML response was signed")
    print("with a DIFFERENT key than certs/saml.key")
    print("\nCheck:")
    print("1. Is your app using the correct key file?")
    print("2. Do you have environment variables overriding the key?")
    print("3. Was the failing response generated before you updated the keys?")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
