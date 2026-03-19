#!/usr/bin/env python3
"""
Generate a comparison guide for Okta configuration
Shows exactly what certificate should be in Okta
"""
import requests
from lxml import etree
import hashlib
import base64

RAILWAY_URL = "https://okta-dpp-saml-production.up.railway.app"

def get_cert_fingerprint(cert_pem):
    """Calculate SHA256 fingerprint of a certificate"""
    cert_b64 = cert_pem.replace('-----BEGIN CERTIFICATE-----', '')
    cert_b64 = cert_b64.replace('-----END CERTIFICATE-----', '')
    cert_b64 = cert_b64.replace('\n', '').replace('\r', '').strip()

    cert_der = base64.b64decode(cert_b64)
    fingerprint = hashlib.sha256(cert_der).hexdigest()

    return ':'.join([fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2)])

print("=" * 80)
print("OKTA CONFIGURATION VERIFICATION GUIDE")
print("=" * 80)

# Fetch deployed certificate
print("\nFetching certificate from deployment...")
response = requests.get(f"{RAILWAY_URL}/saml/metadata", timeout=10)
metadata_xml = response.content
root = etree.fromstring(metadata_xml)

ns = {
    'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
    'ds': 'http://www.w3.org/2000/09/xmldsig#'
}

cert_elem = root.find('.//ds:X509Certificate', namespaces=ns)
cert_b64 = cert_elem.text.strip()

# Format certificate for Okta
cert_lines = [cert_b64[i:i+64] for i in range(0, len(cert_b64), 64)]
cert_formatted = '\n'.join(cert_lines)
cert_pem = f"-----BEGIN CERTIFICATE-----\n{cert_formatted}\n-----END CERTIFICATE-----"

fingerprint = get_cert_fingerprint(cert_pem)

print("✅ Certificate retrieved successfully")
print(f"\nCertificate Fingerprint: {fingerprint}")

print("\n" + "=" * 80)
print("STEP-BY-STEP: VERIFY CERTIFICATE IN OKTA")
print("=" * 80)

print("""
1. Go to Okta Admin Console: https://bala-guardianlife-poc.oktapreview.com/admin

2. Navigate to: Applications → Applications

3. Find and click on your SAML app (the one with Entity ID ending in 'splsozflgjodzjmxdrar')

4. Click the "Sign On" tab

5. Under "SAML 2.0", click "View SAML setup instructions"
   OR click "Edit" and scroll to "Verification Certificate" section

6. Look for the Identity Provider's certificate section

7. Compare the certificate shown in Okta with this fingerprint:
""")

print(f"\n   Expected Fingerprint: {fingerprint}")

print("""
8. If the fingerprints DON'T match, update the certificate in Okta:

   a. Click "Edit" (if not already in edit mode)

   b. In the "SAML Settings" section, find:
      - "Identity Provider Certificate" OR
      - "X.509 Certificate" OR
      - "Signing Certificate"

   c. Paste this certificate (copy everything below):
""")

print("\n" + "-" * 80)
print(cert_pem)
print("-" * 80)

print("""
   d. Click "Save" or "Update"

   e. Wait a few seconds for Okta to update

9. Test the SAML flow again
""")

print("\n" + "=" * 80)
print("ALTERNATIVE: Import from Metadata URL")
print("=" * 80)

print(f"""
If your Okta app supports importing metadata, you can use this URL:

{RAILWAY_URL}/saml/metadata

Steps:
1. In Okta Admin → Your SAML App → Sign On tab
2. Click "Edit"
3. Look for "Import Metadata" or "Metadata URL" option
4. Paste: {RAILWAY_URL}/saml/metadata
5. Click "Import" or "Fetch"
6. Save

This will automatically configure the certificate and SSO URL.
""")

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

print(f"""
After updating the certificate in Okta:

1. Run this command to test again:
   python3 test_deployment.py

2. Try a SAML authentication:
   - Go to your Okta app
   - Click "Sign On"
   - You should be redirected to: {RAILWAY_URL}/saml/sso
   - Complete the authentication

3. Check Okta System Log for any errors:
   - Go to Reports → System Log
   - Filter by your username or app name
   - Look for successful authentication events

If you still see signature validation errors:
- The certificate fingerprints don't match
- Or there's a cache issue (try in incognito/private mode)
- Or check if Okta is using multiple certificates
""")

print("\n" + "=" * 80)
print("Done! Use the certificate above to update Okta.")
print("=" * 80)
