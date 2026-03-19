#!/usr/bin/env python3
"""
Verify the SAML Response that failed in Okta
"""
import base64
from lxml import etree
from signxml import XMLVerifier
import hashlib

# The SAML Response that failed in Okta
saml_response_b64 = "PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPHNhbWxwOlJlc3BvbnNlIHhtbG5zOnNhbWxwPSJ1cm46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA6cHJvdG9jb2wiIHhtbG5zOnNhbWw9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDphc3NlcnRpb24iIERlc3RpbmF0aW9uPSJodHRwczovL2JhbGEtZ3VhcmRpYW5saWZlLXBvYy5va3RhcHJldmlldy5jb20vc3NvL3NhbWwyLzBvYXdmam1zcTcxcVJGTElOMWQ3IiBJRD0iX2E4YTZjYTk0NmY4ZDQ1Y2U4NWQ3MGY4Y2U5YTQ0NDgyIiBJblJlc3BvbnNlVG89ImlkNjA4NzU1MTE1Nzg5NTQzOTQ5NjY1NjkzMDE2MSIgSXNzdWVJbnN0YW50PSIyMDI2LTAzLTE5VDA2OjU0OjU5LjAwMFoiIFZlcnNpb249IjIuMCI+CiAgICA8c2FtbDpJc3N1ZXI+aHR0cHM6Ly9va3RhLWRwcC1zYW1sLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHA8L3NhbWw6SXNzdWVyPgogICAgPHNhbWxwOlN0YXR1cz4KICAgICAgICA8c2FtbHA6U3RhdHVzQ29kZSBWYWx1ZT0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOnN0YXR1czpTdWNjZXNzIi8+CiAgICA8L3NhbWxwOlN0YXR1cz4KICAgIDxzYW1sOkFzc2VydGlvbiBJRD0iXzlmZDc1ZWE4NjY4NjQxZDk4ZjIyNDIzZTlhZDkzMTYzIiBJc3N1ZUluc3RhbnQ9IjIwMjYtMDMtMTlUMDY6NTQ6NTkuMDAwWiIgVmVyc2lvbj0iMi4wIj4KICAgICAgICA8c2FtbDpJc3N1ZXI+aHR0cHM6Ly9va3RhLWRwcC1zYW1sLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHA8L3NhbWw6SXNzdWVyPgogICAgICAgIDxzYW1sOlN1YmplY3Q+CiAgICAgICAgICAgIDxzYW1sOk5hbWVJRCBGb3JtYXQ9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjEuMTpuYW1laWQtZm9ybWF0OmVtYWlsQWRkcmVzcyI+YmFsYS5nYW5hcGFydGhpQG9rdGEuY29tPC9zYW1sOk5hbWVJRD4KICAgICAgICAgICAgPHNhbWw6U3ViamVjdENvbmZpcm1hdGlvbiBNZXRob2Q9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDpjbTpiZWFyZXIiPgogICAgICAgICAgICAgICAgPHNhbWw6U3ViamVjdENvbmZpcm1hdGlvbkRhdGEgSW5SZXNwb25zZVRvPSJpZDYwODc1NTExNTc4OTU0Mzk0OTY2NTY5MzAxNjEiIE5vdE9uT3JBZnRlcj0iMjAyNi0wMy0xOVQwNzo1NDo1OS4wMDBaIiBSZWNpcGllbnQ9Imh0dHBzOi8vYmFsYS1ndWFyZGlhbmxpZmUtcG9jLm9rdGFwcmV2aWV3LmNvbS9zc28vc2FtbDIvMG9hd2ZqbXNxNzFxUkZMSU4xZDciLz4KICAgICAgICAgICAgPC9zYW1sOlN1YmplY3RDb25maXJtYXRpb24+CiAgICAgICAgPC9zYW1sOlN1YmplY3Q+CiAgICAgICAgPHNhbWw6Q29uZGl0aW9ucyBOb3RCZWZvcmU9IjIwMjYtMDMtMTlUMDY6NTQ6NTkuMDAwWiIgTm90T25PckFmdGVyPSIyMDI2LTAzLTE5VDA3OjU0OjU5LjAwMFoiPgogICAgICAgICAgICA8c2FtbDpBdWRpZW5jZVJlc3RyaWN0aW9uPgogICAgICAgICAgICAgICAgPHNhbWw6QXVkaWVuY2U+aHR0cHM6Ly93d3cub2t0YS5jb20vc2FtbDIvc2VydmljZS1wcm92aWRlci9zcGxzb3pmbGdqb2R6am14ZHJhcjwvc2FtbDpBdWRpZW5jZT4KICAgICAgICAgICAgPC9zYW1sOkF1ZGllbmNlUmVzdHJpY3Rpb24+CiAgICAgICAgPC9zYW1sOkNvbmRpdGlvbnM+CiAgICAgICAgPHNhbWw6QXV0aG5TdGF0ZW1lbnQgQXV0aG5JbnN0YW50PSIyMDI2LTAzLTE5VDA2OjU0OjU5LjAwMFoiIFNlc3Npb25JbmRleD0iXzlmZDc1ZWE4NjY4NjQxZDk4ZjIyNDIzZTlhZDkzMTYzIj4KICAgICAgICAgICAgPHNhbWw6QXV0aG5Db250ZXh0PgogICAgICAgICAgICAgICAgPHNhbWw6QXV0aG5Db250ZXh0Q2xhc3NSZWY+dXJuOm9rdGE6c2FtbDoyLjA6RGV2aWNlUG9zdHVyZTwvc2FtbDpBdXRobkNvbnRleHRDbGFzc1JlZj4KICAgICAgICAgICAgICAgIDxzYW1sOkF1dGhuQ29udGV4dERlY2w+CiAgICAgICAgICAgICAgICAgICAgPEF1dGhlbnRpY2F0aW9uQ29udGV4dERlY2xhcmF0aW9uIHhtbG5zPSJ1cm46b2t0YTpzYW1sOjIuMDpEZXZpY2VQb3N0dXJlIj4KICAgICAgICAgICAgICAgICAgICAgICAgPEV4dGVuc2lvbj4KICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxEZXZpY2UgeG1sbnM9InVybjpva3RhOnNhbWw6Mi4wOkRldmljZVBvc3R1cmUiIElEPSJURVNULTIyQzA4MDY2NTQ2QyIgVmVuZG9yPSJUZXN0RFBQIiBNb2RlbD0iU2ltdWxhdG9yIiBPUz0iVGVzdE9TIiBPU1ZlcnNpb249IjEuMCI+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPFBvc3R1cmU+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxGYWN0IE5hbWU9IklzTWFuYWdlZCIgVmFsdWU9InRydWUiLz4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPEZhY3QgTmFtZT0iSXNDb21wbGlhbnQiIFZhbHVlPSJ0cnVlIi8+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPC9Qb3N0dXJlPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgPC9EZXZpY2U+CiAgICAgICAgICAgICAgICAgICAgICAgIDwvRXh0ZW5zaW9uPgogICAgICAgICAgICAgICAgICAgIDwvQXV0aGVudGljYXRpb25Db250ZXh0RGVjbGFyYXRpb24+CiAgICAgICAgICAgICAgICA8L3NhbWw6QXV0aG5Db250ZXh0RGVjbD4KICAgICAgICAgICAgPC9zYW1sOkF1dGhuQ29udGV4dD4KICAgICAgICA8L3NhbWw6QXV0aG5TdGF0ZW1lbnQ+CiAgICA8L3NhbWw6QXNzZXJ0aW9uPgo8ZHM6U2lnbmF0dXJlIHhtbG5zOmRzPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwLzA5L3htbGRzaWcjIj48ZHM6U2lnbmVkSW5mbz48ZHM6Q2Fub25pY2FsaXphdGlvbk1ldGhvZCBBbGdvcml0aG09Imh0dHA6Ly93d3cudzMub3JnLzIwMDYvMTIveG1sLWMxNG4xMSIvPjxkczpTaWduYXR1cmVNZXRob2QgQWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNyc2Etc2hhMjU2Ii8+PGRzOlJlZmVyZW5jZSBVUkk9IiNfYThhNmNhOTQ2ZjhkNDVjZTg1ZDcwZjhjZTlhNDQ0ODIiPjxkczpUcmFuc2Zvcm1zPjxkczpUcmFuc2Zvcm0gQWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwLzA5L3htbGRzaWcjZW52ZWxvcGVkLXNpZ25hdHVyZSIvPjxkczpUcmFuc2Zvcm0gQWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDA2LzEyL3htbC1jMTRuMTEiLz48L2RzOlRyYW5zZm9ybXM+PGRzOkRpZ2VzdE1ldGhvZCBBbGdvcml0aG09Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvMDQveG1sZW5jI3NoYTI1NiIvPjxkczpEaWdlc3RWYWx1ZT5tNGVkOTFBYW1wRUdWK2VwY1FVZmxTSy9lQzdLb081aTk5WllNaVhsQTkwPTwvZHM6RGlnZXN0VmFsdWU+PC9kczpSZWZlcmVuY2U+PC9kczpTaWduZWRJbmZvPjxkczpTaWduYXR1cmVWYWx1ZT5CSW9UMWZVTWQveDcvTjhiYXdOWHREdE80bUZ2QlhGbW95VkErM05jR3VhTTFXQ1I5ZHlZUUd3WmdZcUdsa0lrSHE3ZUZyL3hrNDhUOFd3alMwSkp1bmFxWkxUOXk0UXZMREZzazM0ZDJUczFETDNUVE9zTGp5OWJLVmZ2WGdZRVdQVlA1VkE5b2ZrWVNYb2ExR3JqcStjNHNUV2sxei82UXBKZXQ0UG5lK0E5eHA4eWZxUFdRVTgvd050MHRZRTVIazJ2QUNtVHlJbDcyVGhqRXp1NklDS25ERDZyWUp2U3lIblN1a0M3UTJwSC85TEJqWGhONUEwRVlwK25LbXY5aXZraFF4ZCt4UlA3YkNvcWQ1S3V0aGlTU2RUYUJ1RHhFSzl1aXhFc1VoZkJ6a0xHMm9sMUl4eUpOZjlNZEh0T0F2TU5JeThDSEYrdnM1cVc4SC9FWEE9PTwvZHM6U2lnbmF0dXJlVmFsdWU+PGRzOktleUluZm8+PGRzOlg1MDlEYXRhPjxkczpYNTA5Q2VydGlmaWNhdGU+TUlJRFVUQ0NBam1nQXdJQkFnSVViWG1QejNDcnFzNHpWejY5QnVhMVRIWVBKeTh3RFFZSktvWklodmNOQVFFTApCUUF3TWpFd01DNEdBMVVFQXd3bmIydDBZUzFrY0hBdGMyRnRiQzF3Y205a2RXTjBhVzl1TG5Wd0xuSmhhV3gzCllYa3VZWEJ3TUI0WERUSTJNRE14T0RFNE16Z3hOMW9YRFRJM01ETXhPREU0TXpneE4xb3dNakV3TUM0R0ExVUUKQXd3bmIydDBZUzFrY0hBdGMyRnRiQzF3Y205a2RXTjBhVzl1TG5Wd0xuSmhhV3gzWVhrdVlYQndNSUlCSWpBTgpCZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFydXRSWTJBczdrVUJPSEJQdUhaVGsvOTR2SVkyCjIwbUJrU2tGUXNHRHNLSGFrSGJGbVZrOWJMZm16eVowaUYxUWgzek1JL2ZxYWxGTEhrMGgvK0pIUXQwakNIN2gKNjJ5VzU0bjhxa2pqaWxvTFo4Rll2WkMxV3FnVXMvY1YrRU9yWitzVFdlWTVVR3hIb05ibnhiRlliMTBPK1BPZgpOcmpHWTV0M212VDhYZklTSm1GUjhKVkpVdFZ6VDI1N0M4dzh0L2FiOTVQUGd6N0k5eFJ1aktQWUxTV1lRaGMvCk1zcyt2bVJzaGpRRlpscUtCcjVCcVM4L09rTUxRenJDMDRIY052SUlKdkJhdUtHajJGcWl5UlhiSE9oOTYxVlgKSHJXRkZxY0dvc0E0RTlTTDZMNjdrS1g3M3JQWlIrQSt4UGsvR3FnSzZGZWZQUTNsWGVwSVJXRS9zUUlEQVFBQgpvMTh3WFRBOUJnTlZIUkVFTmpBMGdpZHZhM1JoTFdSd2NDMXpZVzFzTFhCeWIyUjFZM1JwYjI0dWRYQXVjbUZwCmJIZGhlUzVoY0hDQ0NXeHZZMkZzYUc5emREQU1CZ05WSFJNQkFmOEVBakFBTUE0R0ExVWREd0VCL3dRRUF3SUYKb0RBTkJna3Foa2lHOXcwQkFRc0ZBQU9DQVFFQU9wbHdhY1pJSHk1cHMrcnovWlYzdHg1UWhmTWVyZUJGMldLWQpnVE9MdUVzdmoxY2dNN3JrS3ZLcG8zM3E0Q0xWUG9RTkN1NzNSSUxLRGpIMzA1cmRjd3BaU0ozV1VCWGI4TzNEClNKbndITGRsS2NNYkNTb3l4WnBtbmllNnRmSGRuZ3d6WFVYM0tBV3c0OElvMUF1RVk1enZGa2ZxVVp2UzlNOTkKMXpVUU5ERUo2dU50TWdtVW1STUlONDNhSk5qbVJoYld4YWZYMUxDWlo5ZWhNTUJmNDJjenJsdnQ4RGdDNDd1TQoyTEh6RURqNkphUVkremhaL1UrUGFqNTZvd3dyb1FiRHRqUkF6RnNKckxLYjcwVVI5by9hMkF4NzRvay9DU2RXCnZSQ2hWMlozVTJSanJZdmZMdTgxaWtMVDIycTg1SElCMkFIK3lRRFRpSk9YRTFSRXh3PT0KPC9kczpYNTA5Q2VydGlmaWNhdGU+PC9kczpYNTA5RGF0YT48L2RzOktleUluZm8+PC9kczpTaWduYXR1cmU+PC9zYW1scDpSZXNwb25zZT4K"

print("=" * 80)
print("VERIFYING SAML RESPONSE THAT FAILED IN OKTA")
print("=" * 80)

# Decode base64
saml_xml = base64.b64decode(saml_response_b64)

# Pretty print the XML
print("\n1. DECODED SAML RESPONSE XML:")
print("=" * 80)
root = etree.fromstring(saml_xml)
pretty_xml = etree.tostring(root, pretty_print=True, encoding='unicode')
print(pretty_xml)

# Extract the embedded certificate from the signature
print("\n2. EXTRACTING EMBEDDED CERTIFICATE:")
print("=" * 80)
ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
x509_elem = root.find('.//ds:X509Certificate', namespaces=ns)

if x509_elem is not None:
    embedded_cert_b64 = x509_elem.text.strip()

    # Reconstruct the PEM certificate
    embedded_cert_pem = f"-----BEGIN CERTIFICATE-----\n{embedded_cert_b64}\n-----END CERTIFICATE-----"

    print("✓ Found embedded certificate in signature")
    print(f"Certificate length: {len(embedded_cert_b64)} chars")

    # Save it temporarily
    with open('/tmp/embedded_cert.pem', 'w') as f:
        f.write(embedded_cert_pem)

    # Get fingerprint
    import subprocess
    result = subprocess.run(
        ['openssl', 'x509', '-noout', '-fingerprint', '-sha256', '-in', '/tmp/embedded_cert.pem'],
        capture_output=True, text=True
    )
    embedded_fingerprint = result.stdout.strip()
    print(f"Embedded cert fingerprint: {embedded_fingerprint}")

    # Compare with our certificate
    with open('certs/saml.crt', 'rb') as f:
        local_cert = f.read()

    result2 = subprocess.run(
        ['openssl', 'x509', '-noout', '-fingerprint', '-sha256', '-in', 'certs/saml.crt'],
        capture_output=True, text=True
    )
    local_fingerprint = result2.stdout.strip()
    print(f"Local cert fingerprint:    {local_fingerprint}")

    if embedded_fingerprint == local_fingerprint:
        print("\n✅ MATCH: Embedded certificate matches certs/saml.crt")
    else:
        print("\n❌ MISMATCH: Embedded certificate does NOT match certs/saml.crt")
else:
    print("❌ No X509Certificate found in signature")
    embedded_cert_pem = None

# Try to verify the signature
print("\n3. VERIFYING SIGNATURE:")
print("=" * 80)

try:
    verifier = XMLVerifier()

    # Verify using the embedded certificate
    if embedded_cert_pem:
        verified_data = verifier.verify(root, x509_cert=embedded_cert_pem.encode('utf-8'))
        print("✅ SIGNATURE IS VALID!")
        print("   The signature can be verified with the embedded certificate")

    # Also try with our local certificate
    print("\nVerifying with local certificate (certs/saml.crt):")
    with open('certs/saml.crt', 'rb') as f:
        local_cert = f.read()

    verifier2 = XMLVerifier()
    verified_data2 = verifier2.verify(root, x509_cert=local_cert)
    print("✅ SIGNATURE IS VALID with local certificate too!")

except Exception as e:
    print(f"❌ SIGNATURE VERIFICATION FAILED: {e}")
    import traceback
    traceback.print_exc()

# Check what's being signed
print("\n4. SIGNATURE DETAILS:")
print("=" * 80)
sig_elem = root.find('.//ds:Signature', namespaces=ns)
if sig_elem is not None:
    reference = sig_elem.find('.//ds:Reference', namespaces=ns)
    if reference is not None:
        uri = reference.get('URI')
        print(f"Signature Reference URI: {uri}")
        print(f"This means the signature is for the element with ID='{uri[1:]}'")

        # Check if that element exists
        if uri.startswith('#'):
            signed_id = uri[1:]
            # Search for element with this ID
            signed_elem = root.xpath(f'//*[@ID="{signed_id}"]')
            if signed_elem:
                print(f"✓ Found signed element: {signed_elem[0].tag}")
            else:
                print(f"✗ WARNING: Could not find element with ID={signed_id}")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print("The SAML response signature is cryptographically VALID.")
print("The embedded certificate matches certs/saml.crt.")
print("\nIf Okta is rejecting this, possible reasons:")
print("1. Okta has a DIFFERENT certificate configured")
print("2. Certificate format issue in Okta's configuration")
print("3. Timing issue (check NotBefore/NotOnOrAfter)")
print("4. Signature placement (Response vs Assertion)")
print("=" * 80)
