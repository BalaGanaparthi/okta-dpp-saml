#!/usr/bin/env python3
"""
Test utilities for Device Posture Provider
"""
import base64
import requests
from lxml import etree


def create_sample_saml_request(destination="http://localhost:8443/saml/sso",
                               acs_url="http://localhost:8443/test/acs",
                               issuer="http://www.okta.com/test"):
    """Create a sample SAML AuthnRequest"""

    saml_ns = 'urn:oasis:names:tc:SAML:2.0:assertion'
    samlp_ns = 'urn:oasis:names:tc:SAML:2.0:protocol'

    authn_request = etree.Element(
        f'{{{samlp_ns}}}AuthnRequest',
        nsmap={'samlp': samlp_ns, 'saml': saml_ns},
        ID='_test123456789',
        Version='2.0',
        IssueInstant='2024-01-01T00:00:00Z',
        Destination=destination,
        AssertionConsumerServiceURL=acs_url
    )

    # Issuer
    issuer_elem = etree.SubElement(authn_request, f'{{{saml_ns}}}Issuer')
    issuer_elem.text = issuer

    # Subject (optional)
    subject = etree.SubElement(authn_request, f'{{{saml_ns}}}Subject')
    name_id = etree.SubElement(subject, f'{{{saml_ns}}}NameID',
                               Format='urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress')
    name_id.text = 'testuser@example.com'

    # RequestedAuthnContext with Device Posture
    requested_context = etree.SubElement(authn_request, f'{{{samlp_ns}}}RequestedAuthnContext',
                                        Comparison='minimum')
    context_ref = etree.SubElement(requested_context, f'{{{saml_ns}}}AuthnContextClassRef')
    context_ref.text = 'urn:okta:saml:2.0:DevicePosture'

    # Convert to base64
    xml_str = etree.tostring(authn_request, xml_declaration=True, encoding='UTF-8')
    b64_request = base64.b64encode(xml_str).decode('utf-8')

    return b64_request


def test_sso_endpoint(base_url="http://localhost:8443"):
    """Test SSO endpoint with sample request"""
    print("Testing SSO endpoint...")

    # Create sample SAML request
    saml_request = create_sample_saml_request(
        destination=f"{base_url}/saml/sso",
        acs_url=f"{base_url}/test/acs"
    )

    # Send request
    response = requests.post(
        f"{base_url}/saml/sso",
        data={'SAMLRequest': saml_request},
        allow_redirects=False
    )

    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)}")

    if response.status_code == 200:
        print("✓ SSO endpoint is accessible")
        if 'Device Posture Provider' in response.text:
            print("✓ Login form displayed correctly")
        return True
    else:
        print("✗ SSO endpoint returned unexpected status")
        return False


def test_metadata_endpoint(base_url="http://localhost:8443"):
    """Test metadata endpoint"""
    print("\nTesting metadata endpoint...")

    response = requests.get(f"{base_url}/saml/metadata")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ Metadata endpoint is accessible")

        # Parse XML
        try:
            root = etree.fromstring(response.content)
            print("✓ Metadata is valid XML")

            # Check for EntityDescriptor
            if 'EntityDescriptor' in root.tag:
                print("✓ Contains EntityDescriptor")
                entity_id = root.get('entityID')
                print(f"  Entity ID: {entity_id}")
            return True
        except Exception as e:
            print(f"✗ Failed to parse metadata: {e}")
            return False
    else:
        print("✗ Metadata endpoint returned unexpected status")
        return False


def test_health_endpoint(base_url="http://localhost:8443"):
    """Test health check endpoint"""
    print("\nTesting health endpoint...")

    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✓ Health endpoint is accessible")

            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Service: {data.get('service')}")
            print(f"  SAML Ready: {data.get('saml_ready')}")
            return True
        else:
            print("✗ Health endpoint returned unexpected status")
            return False
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
        return False


def test_device_registration(base_url="http://localhost:8443"):
    """Test device registration"""
    print("\nTesting device registration...")

    device_data = {
        'device_id': 'TEST-DEVICE-001',
        'managed': 'true',
        'encrypted': 'true',
        'last_sync': '2024-01-01T00:00:00'
    }

    try:
        response = requests.post(f"{base_url}/admin/devices", data=device_data)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✓ Device registration endpoint is accessible")
            if 'registered successfully' in response.text:
                print("✓ Device registered successfully")
            return True
        else:
            print("✗ Device registration failed")
            return False
    except Exception as e:
        print(f"✗ Device registration error: {e}")
        return False


def run_all_tests(base_url="http://localhost:8443"):
    """Run all tests"""
    print("=" * 60)
    print("Device Posture Provider - Test Suite")
    print("=" * 60)
    print(f"Testing against: {base_url}\n")

    results = []

    # Test health endpoint first
    results.append(("Health Check", test_health_endpoint(base_url)))

    # Test metadata
    results.append(("SAML Metadata", test_metadata_endpoint(base_url)))

    # Test SSO
    results.append(("SSO Endpoint", test_sso_endpoint(base_url)))

    # Test device registration
    results.append(("Device Registration", test_device_registration(base_url)))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")

    return failed == 0


if __name__ == '__main__':
    import sys

    # Check if custom URL provided
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8443"

    success = run_all_tests(url)
    sys.exit(0 if success else 1)
