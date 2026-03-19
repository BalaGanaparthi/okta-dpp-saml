#!/usr/bin/env python3
"""
Test the deployed SAML IdP on Railway
Verifies that the correct certificate is being used
"""
import requests
import sys
from lxml import etree
import hashlib
import base64
from datetime import datetime

# Configuration
RAILWAY_URL = "https://okta-dpp-saml-production.up.railway.app"
LOCAL_CERT_FILE = "certs/saml.crt"

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)

def get_cert_fingerprint(cert_pem):
    """Calculate SHA256 fingerprint of a certificate"""
    # Remove headers and whitespace
    cert_b64 = cert_pem.replace('-----BEGIN CERTIFICATE-----', '')
    cert_b64 = cert_b64.replace('-----END CERTIFICATE-----', '')
    cert_b64 = cert_b64.replace('\n', '').replace('\r', '').strip()

    # Decode and hash
    cert_der = base64.b64decode(cert_b64)
    fingerprint = hashlib.sha256(cert_der).hexdigest()

    # Format as colon-separated
    return ':'.join([fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2)])

def test_health_endpoint():
    """Test the health check endpoint"""
    print_header("1. Testing Health Endpoint")

    try:
        response = requests.get(f"{RAILWAY_URL}/health", timeout=10)

        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health endpoint is accessible")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Service: {health_data.get('service', 'unknown')}")
            print(f"   SAML Ready: {health_data.get('saml_ready', False)}")
            return True
        else:
            print(f"❌ Health endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to health endpoint: {e}")
        return False

def test_metadata_endpoint():
    """Test the SAML metadata endpoint and extract certificate"""
    print_header("2. Testing SAML Metadata Endpoint")

    try:
        response = requests.get(f"{RAILWAY_URL}/saml/metadata", timeout=10)

        if response.status_code != 200:
            print(f"❌ Metadata endpoint returned status {response.status_code}")
            return None

        print(f"✅ Metadata endpoint is accessible")

        # Parse the XML
        metadata_xml = response.content
        root = etree.fromstring(metadata_xml)

        # Extract certificate
        ns = {
            'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
            'ds': 'http://www.w3.org/2000/09/xmldsig#'
        }

        cert_elem = root.find('.//ds:X509Certificate', namespaces=ns)

        if cert_elem is not None:
            cert_b64 = cert_elem.text.strip()
            deployed_cert_pem = f"-----BEGIN CERTIFICATE-----\n{cert_b64}\n-----END CERTIFICATE-----"
            print(f"✅ Certificate found in metadata")
            print(f"   Certificate length: {len(cert_b64)} chars")
            return deployed_cert_pem
        else:
            print(f"❌ No certificate found in metadata")
            return None

    except Exception as e:
        print(f"❌ Failed to fetch metadata: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_certificates(deployed_cert_pem):
    """Compare deployed certificate with local certificate"""
    print_header("3. Comparing Certificates")

    try:
        # Load local certificate
        with open(LOCAL_CERT_FILE, 'r') as f:
            local_cert_pem = f.read()

        # Calculate fingerprints
        deployed_fingerprint = get_cert_fingerprint(deployed_cert_pem)
        local_fingerprint = get_cert_fingerprint(local_cert_pem)

        print(f"Deployed certificate fingerprint:")
        print(f"   {deployed_fingerprint}")
        print(f"\nLocal certificate fingerprint ({LOCAL_CERT_FILE}):")
        print(f"   {local_fingerprint}")

        if deployed_fingerprint == local_fingerprint:
            print(f"\n✅ MATCH: Deployed certificate matches local certificate")
            return True
        else:
            print(f"\n❌ MISMATCH: Certificates do NOT match!")
            print(f"\nThis means:")
            print(f"   - The deployment is using a different certificate file")
            print(f"   - OR the SAML_PRIVATE_KEY env var has an old key")
            print(f"\nAction required:")
            print(f"   1. Update Railway SAML_PRIVATE_KEY env variable")
            print(f"   2. Or remove the env variable to use certs/saml.key file")
            print(f"   3. Redeploy the application")
            return False

    except FileNotFoundError:
        print(f"❌ Local certificate file not found: {LOCAL_CERT_FILE}")
        return False
    except Exception as e:
        print(f"❌ Failed to compare certificates: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sso_endpoint():
    """Test that SSO endpoint is accessible"""
    print_header("4. Testing SSO Endpoint")

    try:
        # Try to access SSO endpoint without parameters (should return 400)
        response = requests.get(f"{RAILWAY_URL}/saml/sso", timeout=10)

        if response.status_code == 400:
            print(f"✅ SSO endpoint is accessible (returned expected 400 for missing SAMLRequest)")
            return True
        elif response.status_code == 200:
            print(f"✅ SSO endpoint is accessible")
            return True
        else:
            print(f"⚠️  SSO endpoint returned unexpected status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to access SSO endpoint: {e}")
        return False

def test_key_cert_matching():
    """Test that local key and cert match"""
    print_header("5. Testing Local Key/Certificate Pair")

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        # Load certificate
        with open(LOCAL_CERT_FILE, 'rb') as f:
            cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        # Load private key
        with open('certs/saml.key', 'rb') as f:
            key_data = f.read()
            private_key = serialization.load_pem_private_key(key_data, password=None, backend=default_backend())

        # Get public keys
        cert_public_key = cert.public_key()
        key_public_key = private_key.public_key()

        # Compare
        cert_public_numbers = cert_public_key.public_numbers()
        key_public_numbers = key_public_key.public_numbers()

        if cert_public_numbers.n == key_public_numbers.n and cert_public_numbers.e == key_public_numbers.e:
            print(f"✅ Local key and certificate are a matching pair")
            return True
        else:
            print(f"❌ Local key and certificate do NOT match!")
            return False

    except Exception as e:
        print(f"❌ Failed to verify key/cert pair: {e}")
        return False

def generate_env_var_format():
    """Generate the private key in environment variable format"""
    print_header("6. Environment Variable Format")

    try:
        with open('certs/saml.key', 'r') as f:
            key_content = f.read()

        # For Railway, you can usually paste the key as-is
        # But some systems need escaped newlines
        print("For Railway environment variable SAML_PRIVATE_KEY, use:")
        print("\nOption A - Direct paste (recommended for Railway UI):")
        print("-" * 80)
        print(key_content)
        print("-" * 80)

        print("\nOption B - Single line with \\n (for CLI/API):")
        print("-" * 80)
        escaped = key_content.replace('\n', '\\n')
        print(escaped)
        print("-" * 80)

        return True
    except Exception as e:
        print(f"❌ Failed to read key file: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🚀" * 40)
    print("RAILWAY DEPLOYMENT TEST")
    print(f"Testing: {RAILWAY_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀" * 40)

    results = {}

    # Run tests
    results['health'] = test_health_endpoint()

    deployed_cert = test_metadata_endpoint()
    results['metadata'] = deployed_cert is not None

    if deployed_cert:
        results['cert_match'] = compare_certificates(deployed_cert)
    else:
        results['cert_match'] = False
        print_header("3. Comparing Certificates")
        print("⏭️  Skipped (no deployed certificate found)")

    results['sso'] = test_sso_endpoint()
    results['local_pair'] = test_key_cert_matching()

    # Show environment variable format
    generate_env_var_format()

    # Summary
    print_header("SUMMARY")

    all_passed = all(results.values())

    print(f"\nTest Results:")
    print(f"  Health Endpoint:        {'✅ PASS' if results['health'] else '❌ FAIL'}")
    print(f"  Metadata Endpoint:      {'✅ PASS' if results['metadata'] else '❌ FAIL'}")
    print(f"  Certificate Match:      {'✅ PASS' if results['cert_match'] else '❌ FAIL'}")
    print(f"  SSO Endpoint:           {'✅ PASS' if results['sso'] else '❌ FAIL'}")
    print(f"  Local Key/Cert Pair:    {'✅ PASS' if results['local_pair'] else '❌ FAIL'}")

    if all_passed:
        print("\n" + "🎉" * 40)
        print("✅ ALL TESTS PASSED!")
        print("🎉" * 40)
        print("\nYour deployment is correctly configured.")
        print("The certificate in Okta should match the deployed certificate.")
        print("\nNext steps:")
        print("1. Verify the certificate in Okta matches the deployed one")
        print("2. Test SAML authentication flow")
        return 0
    else:
        print("\n" + "⚠️ " * 40)
        print("❌ SOME TESTS FAILED")
        print("⚠️ " * 40)

        if not results['cert_match']:
            print("\n🔥 CRITICAL: Certificate mismatch detected!")
            print("\nTO FIX:")
            print("1. Go to Railway dashboard:")
            print("   https://railway.app/project/<your-project-id>")
            print("\n2. Click on your service → Variables tab")
            print("\n3. Find SAML_PRIVATE_KEY variable")
            print("\n4. Update it with the private key shown above (Option A)")
            print("   Or delete the variable to use the certs/saml.key file")
            print("\n5. Redeploy the application")
            print("\n6. Run this test script again to verify")

        return 1

if __name__ == "__main__":
    sys.exit(main())
