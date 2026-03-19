#!/usr/bin/env python3
"""
Advanced diagnostics for SAML signature issues
"""
import requests
import base64
from lxml import etree
import hashlib

RAILWAY_URL = "https://okta-dpp-saml-production.up.railway.app"

print("=" * 80)
print("ADVANCED SAML SIGNATURE DIAGNOSTICS")
print("=" * 80)

# 1. Check what certificate is actually deployed
print("\n[STEP 1] Fetching deployed certificate from metadata...")
response = requests.get(f"{RAILWAY_URL}/saml/metadata", timeout=10)
metadata_xml = response.content
root = etree.fromstring(metadata_xml)

ns = {
    'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
    'ds': 'http://www.w3.org/2000/09/xmldsig#'
}

cert_elem = root.find('.//ds:X509Certificate', namespaces=ns)
deployed_cert_b64 = cert_elem.text.strip()

print(f"✓ Deployed cert (first 50 chars): {deployed_cert_b64[:50]}...")

# Calculate fingerprint
def get_fingerprint(cert_b64):
    cert_der = base64.b64decode(cert_b64)
    fp = hashlib.sha256(cert_der).hexdigest()
    return ':'.join([fp[i:i+2].upper() for i in range(0, len(fp), 2)])

deployed_fp = get_fingerprint(deployed_cert_b64)
print(f"✓ Deployed cert fingerprint:\n  {deployed_fp}")

# 2. Compare with local cert
print("\n[STEP 2] Comparing with local certificate...")
with open('certs/saml.crt', 'r') as f:
    local_cert = f.read()
    local_cert_b64 = local_cert.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').replace('\n', '').strip()

local_fp = get_fingerprint(local_cert_b64)
print(f"✓ Local cert fingerprint:\n  {local_fp}")

if deployed_fp == local_fp:
    print("\n✅ Certificates MATCH - deployment is using the correct cert")
else:
    print("\n❌ Certificates DO NOT MATCH - deployment has different cert!")
    print("   This shouldn't happen. Railway might not have redeployed yet.")

# 3. Analyze the SAML response structure
print("\n[STEP 3] Analyzing SAML Response structure...")
print("\nCurrent implementation signs the <Response> element.")
print("Let's check if Okta expects a different signature location...\n")

# Load the failed SAML response
failed_response_b64 = "PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPHNhbWxwOlJlc3BvbnNlIHhtbG5zOnNhbWxwPSJ1cm46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA6cHJvdG9jb2wiIHhtbG5zOnNhbWw9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDphc3NlcnRpb24iIERlc3RpbmF0aW9uPSJodHRwczovL2JhbGEtZ3VhcmRpYW5saWZlLXBvYy5va3RhcHJldmlldy5jb20vc3NvL3NhbWwyLzBvYXdmam1zcTcxcVJGTElOMWQ3IiBJRD0iX2E4YTZjYTk0NmY4ZDQ1Y2U4NWQ3MGY4Y2U5YTQ0NDgyIiBJblJlc3BvbnNlVG89ImlkNjA4NzU1MTE1Nzg5NTQzOTQ5NjY1NjkzMDE2MSIgSXNzdWVJbnN0YW50PSIyMDI2LTAzLTE5VDA2OjU0OjU5LjAwMFoiIFZlcnNpb249IjIuMCI+CiAgICA8c2FtbDpJc3N1ZXI+aHR0cHM6Ly9va3RhLWRwcC1zYW1sLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHA8L3NhbWw6SXNzdWVyPgogICAgPHNhbWxwOlN0YXR1cz4KICAgICAgICA8c2FtbHA6U3RhdHVzQ29kZSBWYWx1ZT0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOnN0YXR1czpTdWNjZXNzIi8+CiAgICA8L3NhbWxwOlN0YXR1cz4KICAgIDxzYW1sOkFzc2VydGlvbiBJRD0iXzlmZDc1ZWE4NjY4NjQxZDk4ZjIyNDIzZTlhZDkzMTYzIiBJc3N1ZUluc3RhbnQ9IjIwMjYtMDMtMTlUMDY6NTQ6NTkuMDAwWiIgVmVyc2lvbj0iMi4wIj4KICAgICAgICA8c2FtbDpJc3N1ZXI+aHR0cHM6Ly9va3RhLWRwcC1zYW1sLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHA8L3NhbWw6SXNzdWVyPgogICAgICAgIDxzYW1sOlN1YmplY3Q+CiAgICAgICAgICAgIDxzYW1sOk5hbWVJRCBGb3JtYXQ9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjEuMTpuYW1laWQtZm9ybWF0OmVtYWlsQWRkcmVzcyI+YmFsYS5nYW5hcGFydGhpQG9rdGEuY29tPC9zYW1sOk5hbWVJRD4KICAgICAgICAgICAgPHNhbWw6U3ViamVjdENvbmZpcm1hdGlvbiBNZXRob2Q9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDpjbTpiZWFyZXIiPgogICAgICAgICAgICAgICAgPHNhbWw6U3ViamVjdENvbmZpcm1hdGlvbkRhdGEgSW5SZXNwb25zZVRvPSJpZDYwODc1NTExNTc4OTU0Mzk0OTY2NTY5MzAxNjEiIE5vdE9uT3JBZnRlcj0iMjAyNi0wMy0xOVQwNzo1NDo1OS4wMDBaIiBSZWNpcGllbnQ9Imh0dHBzOi8vYmFsYS1ndWFyZGlhbmxpZmUtcG9jLm9rdGFwcmV2aWV3LmNvbS9zc28vc2FtbDIvMG9hd2ZqbXNxNzFxUkZMSU4xZDciLz4KICAgICAgICAgICAgPC9zYW1sOlN1YmplY3RDb25maXJtYXRpb24+CiAgICAgICAgPC9zYW1sOlN1YmplY3Q+CiAgICAgICAgPHNhbWw6Q29uZGl0aW9ucyBOb3RCZWZvcmU9IjIwMjYtMDMtMTlUMDY6NTQ6NTkuMDAwWiIgTm90T25PckFmdGVyPSIyMDI2LTAzLTE5VDA3OjU0OjU5LjAwMFoiPgogICAgICAgICAgICA8c2FtbDpBdWRpZW5jZVJlc3RyaWN0aW9uPgogICAgICAgICAgICAgICAgPHNhbWw6QXVkaWVuY2U+aHR0cHM6Ly93d3cub2t0YS5jb20vc2FtbDIvc2VydmljZS1wcm92aWRlci9zcGxzb3pmbGdqb2R6am14ZHJhcjwvc2FtbDpBdWRpZW5jZT4KICAgICAgICAgICAgPC9zYW1sOkF1ZGllbmNlUmVzdHJpY3Rpb24+CiAgICAgICAgPC9zYW1sOkNvbmRpdGlvbnM+CiAgICAgICAgPHNhbWw6QXV0aG5TdGF0ZW1lbnQgQXV0aG5JbnN0YW50PSIyMDI2LTAzLTE5VDA2OjU0OjU5LjAwMFoiIFNlc3Npb25JbmRleD0iXzlmZDc1ZWE4NjY4NjQxZDk4ZjIyNDIzZTlhZDkzMTYzIj4KICAgICAgICAgICAgPHNhbWw6QXV0aG5Db250ZXh0PgogICAgICAgICAgICAgICAgPHNhbWw6QXV0aG5Db250ZXh0Q2xhc3NSZWY+dXJuOm9rdGE6c2FtbDoyLjA6RGV2aWNlUG9zdHVyZTwvc2FtbDpBdXRobkNvbnRleHRDbGFzc1JlZj4KICAgICAgICAgICAgICAgIDxzYW1sOkF1dGhuQ29udGV4dERlY2w+CiAgICAgICAgICAgICAgICAgICAgPEF1dGhlbnRpY2F0aW9uQ29udGV4dERlY2xhcmF0aW9uIHhtbG5zPSJ1cm46b2t0YTpzYW1sOjIuMDpEZXZpY2VQb3N0dXJlIj4KICAgICAgICAgICAgICAgICAgICAgICAgPEV4dGVuc2lvbj4KICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxEZXZpY2UgeG1sbnM9InVybjpva3RhOnNhbWw6Mi4wOkRldmljZVBvc3R1cmUiIElEPSJURVNULTIyQzA4MDY2NTQ2QyIgVmVuZG9yPSJUZXN0RFBQIiBNb2RlbD0iU2ltdWxhdG9yIiBPUz0iVGVzdE9TIiBPU1ZlcnNpb249IjEuMCI+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPFBvc3R1cmU+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIDxGYWN0IE5hbWU9IklzTWFuYWdlZCIgVmFsdWU9InRydWUiLz4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPEZhY3QgTmFtZT0iSXNDb21wbGlhbnQiIFZhbHVlPSJ0cnVlIi8+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgPC9Qb3N0dXJlPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgPC9EZXZpY2U+CiAgICAgICAgICAgICAgICAgICAgICAgIDwvRXh0ZW5zaW9uPgogICAgICAgICAgICAgICAgICAgIDwvQXV0aGVudGljYXRpb25Db250ZXh0RGVjbGFyYXRpb24+CiAgICAgICAgICAgICAgICA8L3NhbWw6QXV0aG5Db250ZXh0RGVjbD4KICAgICAgICAgICAgPC9zYW1sOkF1dGhuQ29udGV4dD4KICAgICAgICA8L3NhbWw6QXV0aG5TdGF0ZW1lbnQ+CiAgICA8L3NhbWw6QXNzZXJ0aW9uPgo8ZHM6U2lnbmF0dXJlIHhtbG5zOmRzPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwLzA5L3htbGRzaWcjIj48ZHM6U2lnbmVkSW5mbz48ZHM6Q2Fub25pY2FsaXphdGlvbk1ldGhvZCBBbGdvcml0aG09Imh0dHA6Ly93d3cudzMub3JnLzIwMDYvMTIveG1sLWMxNG4xMSIvPjxkczpTaWduYXR1cmVNZXRob2QgQWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNyc2Etc2hhMjU2Ii8+PGRzOlJlZmVyZW5jZSBVUkk9IiNfYThhNmNhOTQ2ZjhkNDVjZTg1ZDcwZjhjZTlhNDQ0ODIiPjxkczpUcmFuc2Zvcm1zPjxkczpUcmFuc2Zvcm0gQWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwLzA5L3htbGRzaWcjZW52ZWxvcGVkLXNpZ25hdHVyZSIvPjxkczpUcmFuc2Zvcm0gQWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDA2LzEyL3htbC1jMTRuMTEiLz48L2RzOlRyYW5zZm9ybXM+PGRzOkRpZ2VzdE1ldGhvZCBBbGdvcml0aG09Imh0dHA6Ly93d3cudzMub3JnLzIwMDEvMDQveG1sZW5jI3NoYTI1NiIvPjxkczpEaWdlc3RWYWx1ZT5tNGVkOTFBYW1wRUdWK2VwY1FVZmxTSy9lQzdLb081aTk5WllNaVhsQTkwPTwvZHM6RGlnZXN0VmFsdWU+PC9kczpSZWZlcmVuY2U+PC9kczpTaWduZWRJbmZvPjxkczpTaWduYXR1cmVWYWx1ZT5CSW9UMWZVTWQveDcvTjhiYXdOWHREdE80bUZ2QlhGbW95VkErM05jR3VhTTFXQ1I5ZHlZUUd3WmdZcUdsa0lrSHE3ZUZyL3hrNDhUOFd3alMwSkp1bmFxWkxUOXk0UXZMREZzazM0ZDJUczFETDNUVE9zTGp5OWJLVmZ2WGdZRVdQVlA1VkE5b2ZrWVNYb2ExR3JqcStjNHNUV2sxei82UXBKZXQ0UG5lK0E5eHA4eWZxUFdRVTgvd050MHRZRTVIazJ2QUNtVHlJbDcyVGhqRXp1NklDS25ERDZyWUp2U3lIblN1a0M3UTJwSC85TEJqWGhONUEwRVlwK25LbXY5aXZraFF4ZCt4UlA3YkNvcWQ1S3V0aGlTU2RUYUJ1RHhFSzl1aXhFc1VoZkJ6a0xHMm9sMUl4eUpOZjlNZEh0T0F2TU5JeThDSEYrdnM1cVc4SC9FWEE9PTwvZHM6U2lnbmF0dXJlVmFsdWU+PGRzOktleUluZm8+PGRzOlg1MDlEYXRhPjxkczpYNTA5Q2VydGlmaWNhdGU+TUlJRFVUQ0NBam1nQXdJQkFnSVViWG1QejNDcnFzNHpWejY5QnVhMVRIWVBKeTh3RFFZSktvWklodmNOQVFFTApCUUF3TWpFd01DNEdBMVVFQXd3bmIydDBZUzFrY0hBdGMyRnRiQzF3Y205a2RXTjBhVzl1TG5Wd0xuSmhhV3gzCllYa3VZWEJ3TUI0WERUSTJNRE14T0RFNE16Z3hOMW9YRFRJM01ETXhPREU0TXpneE4xb3dNakV3TUM0R0ExVUUKQXd3bmIydDBZUzFrY0hBdGMyRnRiQzF3Y205a2RXTjBhVzl1TG5Wd0xuSmhhV3gzWVhrdVlYQndNSUlCSWpBTgpCZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFydXRSWTJBczdrVUJPSEJQdUhaVGsvOTR2SVkyCjIwbUJrU2tGUXNHRHNLSGFrSGJGbVZrOWJMZm16eVowaUYxUWgzek1JL2ZxYWxGTEhrMGgvK0pIUXQwakNIN2gKNjJ5VzU0bjhxa2pqaWxvTFo4Rll2WkMxV3FnVXMvY1YrRU9yWitzVFdlWTVVR3hIb05ibnhiRlliMTBPK1BPZgpOcmpHWTV0M212VDhYZklTSm1GUjhKVkpVdFZ6VDI1N0M4dzh0L2FiOTVQUGd6N0k5eFJ1aktQWUxTV1lRaGMvCk1zcyt2bVJzaGpRRlpscUtCcjVCcVM4L09rTUxRenJDMDRIY052SUlKdkJhdUtHajJGcWl5UlhiSE9oOTYxVlgKSHJXRkZxY0dvc0E0RTlTTDZMNjdrS1g3M3JQWlIrQSt4UGsvR3FnSzZGZWZQUTNsWGVwSVJXRS9zUUlEQVFBQgpvMTh3WFRBOUJnTlZIUkVFTmpBMGdpZHZhM1JoTFdSd2NDMXpZVzFzTFhCeWIyUjFZM1JwYjI0dWRYQXVjbUZwCmJIZGhlUzVoY0hDQ0NXeHZZMkZzYUc5emREQU1CZ05WSFJNQkFmOEVBakFBTUE0R0ExVWREd0VCL3dRRUF3SUYKb0RBTkJna3Foa2lHOXcwQkFRc0ZBQU9DQVFFQU9wbHdhY1pJSHk1cHMrcnovWlYzdHg1UWhmTWVyZUJGMldLWQpnVE9MdUVzdmoxY2dNN3JrS3ZLcG8zM3E0Q0xWUG9RTkN1NzNSSUxLRGpIMzA1cmRjd3BaU0ozV1VCWGI4TzNEClNKbndITGRsS2NNYkNTb3l4WnBtbmllNnRmSGRuZ3d6WFVYM0tBV3c0OElvMUF1RVk1enZGa2ZxVVp2UzlNOTkKMXpVUU5ERUo2dU50TWdtVW1STUlONDNhSk5qbVJoYld4YWZYMUxDWlo5ZWhNTUJmNDJjenJsdnQ4RGdDNDd1TQoyTEh6RURqNkphUVkremhaL1UrUGFqNTZvd3dyb1FiRHRqUkF6RnNKckxLYjcwVVI5by9hMkF4NzRvay9DU2RXCnZSQ2hWMlozVTJSanJZdmZMdTgxaWtMVDIycTg1SElCMkFIK3lRRFRpSk9YRTFSRXh3PT0KPC9kczpYNTA5Q2VydGlmaWNhdGU+PC9kczpYNTA5RGF0YT48L2RzOktleUluZm8+PC9kczpTaWduYXR1cmU+PC9zYW1scDpSZXNwb25zZT4K"

decoded = base64.b64decode(failed_response_b64)
failed_root = etree.fromstring(decoded)

# Check signature location
sig_elem = failed_root.find('.//ds:Signature', namespaces=ns)
if sig_elem is not None:
    parent = sig_elem.getparent()
    parent_tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
    print(f"✓ Signature found as child of: <{parent_tag}>")

    # Check what element is referenced
    ref_elem = sig_elem.find('.//ds:Reference', namespaces=ns)
    if ref_elem is not None:
        uri = ref_elem.get('URI')
        print(f"✓ Signature references: {uri}")

        if uri.startswith('#_'):
            ref_id = uri[1:]
            # Find what element has this ID
            for elem in failed_root.iter():
                if elem.get('ID') == ref_id:
                    elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    print(f"✓ Referenced element: <{elem_tag} ID=\"{ref_id}\">")
                    break

print("\n[STEP 4] Checking signature placement options...")
print("""
SAML 2.0 allows signatures in different locations:

Option 1: Sign the <Response> (CURRENT)
  <Response ID="xxx">
    <Issuer>...</Issuer>
    <Status>...</Status>
    <Assertion>...</Assertion>
    <Signature>...</Signature>  ← Signs the entire Response
  </Response>

Option 2: Sign the <Assertion> (ALTERNATIVE)
  <Response>
    <Issuer>...</Issuer>
    <Status>...</Status>
    <Assertion ID="yyy">
      <Issuer>...</Issuer>
      <Subject>...</Subject>
      ...
      <Signature>...</Signature>  ← Signs just the Assertion
    </Assertion>
  </Response>

Option 3: Sign BOTH (MOST SECURE)
  <Response ID="xxx">
    <Issuer>...</Issuer>
    <Status>...</Status>
    <Assertion ID="yyy">
      <Issuer>...</Issuer>
      ...
      <Signature>...</Signature>  ← Signs the Assertion
    </Assertion>
    <Signature>...</Signature>  ← Signs the Response
  </Response>

Some SP implementations (including Okta) may prefer or require
the Assertion to be signed instead of the Response.
""")

print("\n[STEP 5] Possible root causes and solutions...")
print("""
POSSIBLE CAUSES:
1. ❌ Okta expects Assertion to be signed (not Response)
2. ❌ Certificate in Okta is still the old one (cache/update delay)
3. ❌ Railway didn't redeploy after deleting env var
4. ❌ Certificate format issue in Okta (spaces, line breaks)
5. ❌ Okta has multiple certificates and is using the wrong one

CLEVER SOLUTIONS TO TRY:
""")

print("\n[Solution 1] Sign the Assertion instead of Response")
print("  File: simple_saml.py")
print("  Change: Sign <Assertion> element instead of <Response>")
print("  Likelihood of fixing: 🔥 HIGH")

print("\n[Solution 2] Force Railway redeploy")
print("  Action: Make a dummy change and push to trigger rebuild")
print("  Command: echo '# redeploy' >> README.md && git commit -am 'Force redeploy' && git push")
print("  Likelihood of fixing: 🔥 MEDIUM")

print("\n[Solution 3] Check Okta certificate upload")
print("  Action: Re-upload certificate in Okta admin console")
print("  Details: Delete old cert, upload new one, SAVE, wait 60 seconds")
print("  Likelihood of fixing: 🔥 MEDIUM")

print("\n[Solution 4] Generate completely fresh key pair")
print("  Action: python3 gen_x509v3.py")
print("  Then: Upload NEW cert to Okta")
print("  Then: git add certs/* && git commit && git push")
print("  Likelihood of fixing: 🔥 LOW (but eliminates any corruption)")

print("\n[Solution 5] Add debug endpoint to show actual key being used")
print("  Action: Add /debug/key-info endpoint")
print("  Shows: Hash of key, cert fingerprint, which source (file/env)")
print("  Likelihood of fixing: 🔥 DIAGNOSTIC ONLY")

print("\n[Solution 6] Test with Okta's SAML validator")
print("  URL: https://samltest.id/")
print("  Action: Upload metadata, test SAML flow, check what fails")
print("  Likelihood of fixing: 🔥 DIAGNOSTIC ONLY")

print("\n" + "=" * 80)
print("RECOMMENDED NEXT STEPS:")
print("=" * 80)
print("1. Try Solution 1 (sign Assertion) - Most likely to work")
print("2. Try Solution 2 (force redeploy) - Quick to test")
print("3. Try Solution 3 (re-upload cert in Okta) - Verify Okta has it")
print("=" * 80)
