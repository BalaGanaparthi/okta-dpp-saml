#!/usr/bin/env python3
"""
Test the new assertion-signing implementation
"""
from simple_saml_sign_assertion import create_saml_response_simple
from signxml import XMLVerifier
from lxml import etree
import base64

print("=" * 80)
print("TESTING ASSERTION SIGNING (New Implementation)")
print("=" * 80)

# Load cert and key
with open('certs/saml.crt', 'rb') as f:
    cert = f.read()

with open('certs/saml.key', 'rb') as f:
    key = f.read()

print("\n1. Creating SAML Response with ASSERTION signing...")
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

print("\n2. Analyzing the signed response...")
decoded_xml = base64.b64decode(saml_response_b64)
root = etree.fromstring(decoded_xml)

ns = {
    'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
    'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
    'ds': 'http://www.w3.org/2000/09/xmldsig#'
}

# Check where signatures are
response_sig = root.find('.//ds:Signature', namespaces=ns)
if response_sig is not None:
    parent = response_sig.getparent()
    parent_tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
    print(f"   ✓ Signature found as child of: <{parent_tag}>")

    # Check what it references
    ref = response_sig.find('.//ds:Reference', namespaces=ns)
    if ref is not None:
        uri = ref.get('URI')
        print(f"   ✓ Signature references: {uri}")

        # Check if it's the Assertion
        assertion = root.find('.//saml:Assertion', namespaces=ns)
        if assertion is not None:
            assertion_id = assertion.get('ID')
            if uri == f"#{assertion_id}":
                print(f"   ✅ CORRECT: Signature is on the Assertion!")
            else:
                print(f"   ❌ Wrong: Signature references {uri}, but Assertion ID is {assertion_id}")

# Verify the signature
print("\n3. Verifying signature...")
try:
    verifier = XMLVerifier()
    # Find what's signed
    signed_elem = None
    if response_sig is not None:
        signed_elem = response_sig.getparent()

    if signed_elem is not None:
        verified = verifier.verify(signed_elem, x509_cert=cert)
        print("   ✅ Signature VERIFIED!")
        print("   ✅ This should work with Okta!")
    else:
        print("   ❌ Could not find signed element")

except Exception as e:
    print(f"   ❌ Verification failed: {e}")

print("\n" + "=" * 80)
print("STRUCTURE COMPARISON")
print("=" * 80)
print("""
OLD (Response signing):
<Response ID="xxx">
  <Issuer>...</Issuer>
  <Status>...</Status>
  <Assertion>...</Assertion>
  <Signature>...</Signature>  ← Signs Response
</Response>

NEW (Assertion signing):
<Response ID="xxx">
  <Issuer>...</Issuer>
  <Status>...</Status>
  <Assertion ID="yyy">
    <Issuer>...</Issuer>
    <Subject>...</Subject>
    ...
    <Signature>...</Signature>  ← Signs Assertion
  </Assertion>
</Response>
""")

print("\n" + "=" * 80)
print("TO APPLY THIS FIX:")
print("=" * 80)
print("1. Backup the old file:")
print("   cp simple_saml.py simple_saml_OLD.py")
print("\n2. Replace with new version:")
print("   cp simple_saml_sign_assertion.py simple_saml.py")
print("\n3. Commit and push:")
print("   git add simple_saml.py")
print("   git commit -m 'Sign Assertion instead of Response for Okta compatibility'")
print("   git push")
print("\n4. Wait for Railway to redeploy (1-2 minutes)")
print("\n5. Test SAML flow in Okta again")
print("=" * 80)
