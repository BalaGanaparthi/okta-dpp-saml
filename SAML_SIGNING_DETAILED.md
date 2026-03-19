# SAML Response Creation and Signing - Detailed Source Code Analysis

## Overview
The SAML response is created and signed across 3 source files:
1. **`saml_handler.py`** - Loads the certificate and private key
2. **`app.py`** - Calls the SAML response creation function
3. **`simple_saml.py`** - Creates and signs the SAML response ⭐ MAIN FILE

---

## File 1: Certificate and Key Loading

### `saml_handler.py` (Lines 36-66)

**Purpose:** Loads the X.509 certificate and RSA private key that will be used for signing.

```python
36  def _load_certificates(self):
37      """Load SAML signing certificate and key"""
38      try:
39          # Load certificate from file
40          logger.debug(f"Loading certificate from {self.cert_file}")
41          with open(self.cert_file, 'rb') as f:
42              self.cert = f.read()
```

**Lines 40-42:** Load the certificate file
- `self.cert_file` = `'certs/saml.crt'` (from config.py)
- Opens file in binary mode (`'rb'`)
- Reads entire certificate into `self.cert` as bytes
- This is the **public certificate** that will be embedded in the signature

```python
43
44          # Load private key from environment variable or file
45          import os
46          env_key = os.getenv('SAML_PRIVATE_KEY')
47          if env_key:
48              logger.debug("Loading private key from SAML_PRIVATE_KEY environment variable")
49              # Handle escaped newlines in environment variable
50              env_key = env_key.replace('\\n', '\n')
51              self.key = env_key.encode('utf-8')
```

**Lines 46-51:** Load private key from environment variable (PRIORITY 1)
- **Line 46:** Check for `SAML_PRIVATE_KEY` environment variable
- **Line 47:** If environment variable exists, use it (this takes priority!)
- **Line 50:** Replace escaped newlines `\n` with actual newlines
- **Line 51:** Convert string to bytes and store in `self.key`
- ⚠️ **CRITICAL:** Environment variable is checked FIRST, before file!

```python
52          else:
53              logger.debug(f"Loading private key from {self.key_file}")
54              with open(self.key_file, 'rb') as f:
55                  self.key = f.read()
```

**Lines 52-55:** Load private key from file (PRIORITY 2 - fallback)
- **Line 52:** Only executes if `SAML_PRIVATE_KEY` env var doesn't exist
- `self.key_file` = `'certs/saml.key'` (from config.py)
- Opens file in binary mode
- Reads entire private key into `self.key` as bytes

```python
56
57          logger.info(f"✅ SAML certificates loaded successfully (cert: {len(self.cert)} bytes, key: {len(self.key)} bytes)")
58      except FileNotFoundError as e:
59          logger.warning(f"⚠️  Certificate files not found: {e}")
60          logger.warning("SAML responses will NOT be signed!")
61          self.cert = None
62          self.key = None
63      except Exception as e:
64          log_error(logger, e, "Failed to load SAML certificates")
65          self.cert = None
66          self.key = None
```

**Lines 57-66:** Logging and error handling
- **Line 57:** Logs successful load with byte counts
- **Lines 58-62:** If files not found, set cert and key to None (unsigned responses)
- **Lines 63-66:** Catch any other errors

**Result:** After this function runs:
- `saml_handler.cert` contains the X.509 certificate (bytes)
- `saml_handler.key` contains the RSA private key (bytes)

---

## File 2: Calling the SAML Response Generator

### `app.py` (Lines 368-381)

**Purpose:** Calls the function that creates and signs the SAML response.

```python
368     # Create SAML response using simple template
369     logger.info(f"Creating SAML response for user: {user_id}")
370     entity_id = config.get('saml.entity_id')
371     saml_response_b64, saml_response_xml = create_saml_response_simple(
372         entity_id=entity_id,
373         acs_url=request_data['acs_url'],
374         request_id=request_data['id'],
375         audience=request_data['issuer'],
376         user_email=user_id,
377         is_managed=is_managed,
378         is_compliant=is_compliant,
379         cert=saml_handler.cert,
380         key=saml_handler.key
381     )
```

**Line 370:** Get entity ID from config
- Example: `'https://okta-dpp-saml-production.up.railway.app'`

**Line 371:** Call the function from `simple_saml.py`
- Returns tuple: (base64_encoded_response, plain_xml_response)

**Parameters passed:**
- **Line 372:** `entity_id` - Your IdP's identifier
- **Line 373:** `acs_url` - Okta's Assertion Consumer Service URL (where to send response)
- **Line 374:** `request_id` - ID from Okta's original request (for InResponseTo)
- **Line 375:** `audience` - Okta's entity ID (for audience restriction)
- **Line 376:** `user_email` - User's email address
- **Line 377:** `is_managed` - Boolean, device is managed
- **Line 378:** `is_compliant` - Boolean, device is compliant
- **Line 379:** `cert` - Certificate loaded from `saml_handler` ⚠️
- **Line 380:** `key` - Private key loaded from `saml_handler` ⚠️

**Result:**
- `saml_response_b64` - Base64 encoded signed SAML response (ready to send)
- `saml_response_xml` - Plain XML for logging

---

## File 3: SAML Response Creation and Signing ⭐ MAIN FILE

### `simple_saml.py` (Lines 66-113)

This is the **MAIN FILE** where the SAML response is created and signed.

### Function Definition

```python
66  def create_saml_response_simple(entity_id, acs_url, request_id, audience, user_email,
67                                  is_managed, is_compliant, cert, key):
68      """Create SAML Response using template"""
```

**Lines 66-68:** Function signature
- Receives all parameters from `app.py`
- `cert` and `key` are the loaded certificate and private key

---

### PART 1: Generate Unique IDs and Timestamps (Lines 70-78)

```python
70      now = datetime.utcnow()
71      response_id = f"_{uuid.uuid4().hex}"
72      assertion_id = f"_{uuid.uuid4().hex}"
73      device_id = f"TEST-{uuid.uuid4().hex[:12].upper()}"
```

**Line 70:** Get current UTC time
- Example: `2026-03-19 06:54:59`

**Line 71:** Generate unique Response ID
- Uses UUID v4 (random)
- Converts to hex string (no dashes)
- Prepends underscore (SAML requirement for IDs)
- Example: `"_a8a6ca946f8d45ce85d70f8ce9a44482"`

**Line 72:** Generate unique Assertion ID
- Same format as response_id
- Example: `"_9fd75ea8668641d98f22423e9ad93163"`

**Line 73:** Generate Device ID
- Takes first 12 characters of UUID hex
- Converts to uppercase
- Prepends "TEST-"
- Example: `"TEST-22C08066546C"`

```python
75      # Format timestamps
76      issue_instant = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
77      not_before = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
78      not_on_or_after = (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
```

**Line 76:** Format issue instant timestamp
- ISO 8601 format with milliseconds
- Example: `"2026-03-19T06:54:59.000Z"`

**Line 77:** Format "not before" timestamp (same as issue instant)
- SAML response is valid starting now

**Line 78:** Format "not on or after" timestamp
- Add 1 hour to current time
- SAML response expires after 1 hour
- Example: `"2026-03-19T07:54:59.000Z"`

---

### PART 2: Fill the SAML Template (Lines 80-95)

```python
80      # Fill template
81      response_xml = SAML_RESPONSE_TEMPLATE.format(
82          response_id=response_id,
83          assertion_id=assertion_id,
84          device_id=device_id,
85          entity_id=entity_id,
86          acs_url=acs_url,
87          request_id=request_id,
88          audience=audience,
89          user_email=user_email,
90          issue_instant=issue_instant,
91          not_before=not_before,
92          not_on_or_after=not_on_or_after,
93          is_managed=str(is_managed).lower(),
94          is_compliant=str(is_compliant).lower()
95      )
```

**Line 81:** Use Python string `.format()` method
- Takes the template string (lines 11-63) which contains placeholders like `{response_id}`
- Replaces all placeholders with actual values

**Lines 82-94:** All the values being substituted into the template
- **Line 82:** Response ID (e.g., `_a8a6ca946f8d45ce85d70f8ce9a44482`)
- **Line 83:** Assertion ID (e.g., `_9fd75ea8668641d98f22423e9ad93163`)
- **Line 84:** Device ID (e.g., `TEST-22C08066546C`)
- **Line 85:** Entity ID (e.g., `https://okta-dpp-saml-production.up.railway.app`)
- **Line 86:** ACS URL (e.g., `https://bala-guardianlife-poc.oktapreview.com/sso/saml2/...`)
- **Line 87:** Request ID from Okta's original request
- **Line 88:** Audience - Okta's entity ID
- **Line 89:** User's email address
- **Line 90:** Issue instant timestamp
- **Line 91:** Not before timestamp
- **Line 92:** Not on or after timestamp
- **Line 93:** Is managed - converted to lowercase string ("true" or "false")
- **Line 94:** Is compliant - converted to lowercase string ("true" or "false")

**Result:** `response_xml` is now a complete XML string with all values filled in

---

### PART 3: Parse XML String to Element Tree (Line 98)

```python
97      # Parse to sign
98      response_elem = etree.fromstring(response_xml.encode('utf-8'))
```

**Line 98:** Convert string to lxml Element tree
- `response_xml.encode('utf-8')` - Convert string to bytes
- `etree.fromstring()` - Parse XML bytes into lxml Element tree object
- **Why?** The XMLSigner library needs an Element tree object, not a string
- `response_elem` is now an lxml Element with tag `{urn:oasis:names:tc:SAML:2.0:protocol}Response`

---

### PART 4: Sign the Response ⚠️ CRITICAL SECTION (Lines 100-110)

This is where the **digital signature** is created!

```python
100     # Sign the response
101     if cert and key:
102         signer = XMLSigner(
103             method=methods.enveloped,
104             signature_algorithm='rsa-sha256',
105             digest_algorithm='sha256'
106         )
107         signed_response = signer.sign(response_elem, key=key, cert=cert)
108         response_xml = etree.tostring(signed_response, pretty_print=True, xml_declaration=True, encoding='UTF-8')
```

**Line 101:** Check if certificate and key are available
- If either is None, skip signing (unsigned response)

**Lines 102-106:** Create XMLSigner object
- **Line 102:** `XMLSigner` from `signxml` library
- **Line 103:** `method=methods.enveloped`
  - "Enveloped" means signature goes INSIDE the element being signed
  - The `<ds:Signature>` will be a child of `<samlp:Response>`
- **Line 104:** `signature_algorithm='rsa-sha256'`
  - Use RSA encryption with SHA-256 hash
  - Standard for SAML 2.0
- **Line 105:** `digest_algorithm='sha256'`
  - Use SHA-256 to create the digest (hash) of the XML content

**Line 107:** ⭐ **THE ACTUAL SIGNING HAPPENS HERE** ⭐
```python
signed_response = signer.sign(response_elem, key=key, cert=cert)
```

**What `signer.sign()` does internally:**

1. **Canonicalization (C14N)**
   - Normalizes the XML (removes insignificant whitespace, orders attributes)
   - Uses C14N 1.1 algorithm: `http://www.w3.org/2006/12/xml-c14n11`

2. **Calculate Digest**
   - Creates SHA-256 hash of the canonicalized Response element
   - Example digest: `m4ed91AampEGV+epcQUflSK/eC7KoO5i99ZYMiXlA90=`
   - Stores in `<ds:DigestValue>` element

3. **Create SignedInfo Element**
   - Contains:
     - Canonicalization method
     - Signature algorithm (RSA-SHA256)
     - Reference to the element being signed (URI="#_{response_id}")
     - Digest method and value

4. **Sign the SignedInfo**
   - Canonicalizes the `<ds:SignedInfo>` element
   - **Uses the PRIVATE KEY to encrypt it with RSA**
   - This creates the actual signature
   - Example signature (truncated): `BIoT1fUMd/x7/N8bawNXt...`
   - Stores in `<ds:SignatureValue>` element

5. **Extract Certificate**
   - Takes the X.509 certificate (from `cert` parameter)
   - Removes PEM headers (`-----BEGIN CERTIFICATE-----`, etc.)
   - Removes newlines
   - Keeps only the base64 content
   - Stores in `<ds:X509Certificate>` element

6. **Build Complete Signature Element**
   ```xml
   <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
       <ds:SignedInfo>
           <ds:CanonicalizationMethod Algorithm="..."/>
           <ds:SignatureMethod Algorithm="rsa-sha256"/>
           <ds:Reference URI="#{response_id}">
               <ds:Transforms>...</ds:Transforms>
               <ds:DigestMethod Algorithm="sha256"/>
               <ds:DigestValue>m4ed91Aamp...</ds:DigestValue>
           </ds:Reference>
       </ds:SignedInfo>
       <ds:SignatureValue>BIoT1fUMd/x7...</ds:SignatureValue>
       <ds:KeyInfo>
           <ds:X509Data>
               <ds:X509Certificate>MIIDUTCCAjmg...</ds:X509Certificate>
           </ds:X509Data>
       </ds:KeyInfo>
   </ds:Signature>
   ```

7. **Insert Signature into Response**
   - Adds the `<ds:Signature>` element as a child of `<samlp:Response>`
   - Returns the modified Element tree

**Line 107 Result:**
- `signed_response` is now an lxml Element tree with the signature embedded

**Line 108:** Convert signed Element tree back to string
```python
response_xml = etree.tostring(signed_response, pretty_print=True, xml_declaration=True, encoding='UTF-8')
```
- `pretty_print=True` - Add indentation and newlines (for readability)
- `xml_declaration=True` - Add `<?xml version="1.0" encoding="UTF-8"?>`
- `encoding='UTF-8'` - Use UTF-8 encoding
- Returns bytes

```python
109     else:
110         response_xml = response_xml.encode('utf-8')
```

**Lines 109-110:** If no cert/key (unsigned)
- Just convert the original string to bytes
- No signature added

---

### PART 5: Base64 Encode (Line 113)

```python
112     # Base64 encode
113     return base64.b64encode(response_xml).decode('utf-8'), response_xml.decode('utf-8')
```

**Line 113:** Return two values
1. **First return value:** `base64.b64encode(response_xml).decode('utf-8')`
   - Takes the bytes (signed XML)
   - Base64 encodes it
   - Converts bytes to string
   - This is what gets sent to Okta in the HTML form
   - Example (truncated): `PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4K...`

2. **Second return value:** `response_xml.decode('utf-8')`
   - Takes the bytes (signed XML)
   - Decodes to string (for logging)
   - This is the plain XML that gets logged

---

## Complete Signature Structure

After line 107, the SAML response contains this signature:

```xml
<samlp:Response ID="_a8a6ca946f8d45ce85d70f8ce9a44482" ...>
    <saml:Issuer>...</saml:Issuer>
    <samlp:Status>...</samlp:Status>
    <saml:Assertion>...</saml:Assertion>

    <!-- THIS IS ADDED BY LINE 107 -->
    <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">

        <!-- What is being signed and how -->
        <ds:SignedInfo>
            <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2006/12/xml-c14n11"/>
            <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>

            <!-- Reference to the Response element -->
            <ds:Reference URI="#_a8a6ca946f8d45ce85d70f8ce9a44482">
                <ds:Transforms>
                    <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
                    <ds:Transform Algorithm="http://www.w3.org/2006/12/xml-c14n11"/>
                </ds:Transforms>
                <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>

                <!-- SHA256 hash of the Response element -->
                <ds:DigestValue>m4ed91AampEGV+epcQUflSK/eC7KoO5i99ZYMiXlA90=</ds:DigestValue>
            </ds:Reference>
        </ds:SignedInfo>

        <!-- RSA signature of the SignedInfo (encrypted with PRIVATE KEY) -->
        <ds:SignatureValue>BIoT1fUMd/x7/N8bawNXtDtO4mFvBXFm...</ds:SignatureValue>

        <!-- Certificate (PUBLIC KEY) for verification -->
        <ds:KeyInfo>
            <ds:X509Data>
                <ds:X509Certificate>
                    MIIDUTCCAjmgAwIBAgIUbXmPz3Crqs4zVz69Bua1THYPJy8w...
                </ds:X509Certificate>
            </ds:X509Data>
        </ds:KeyInfo>
    </ds:Signature>
</samlp:Response>
```

---

## Summary Table

| File | Lines | Purpose | Key Action |
|------|-------|---------|------------|
| `saml_handler.py` | 36-66 | Load credentials | Loads cert from file, key from env var or file |
| `app.py` | 368-381 | Orchestrate | Calls signing function with loaded credentials |
| `simple_saml.py` | 66-113 | **Create & Sign** | **Generates XML, signs with RSA, base64 encodes** |
| `simple_saml.py` | 107 | **⭐ SIGNING** | **`signer.sign(response_elem, key=key, cert=cert)`** |

---

## The Critical Bug

**Where the private key comes from (saml_handler.py:46-55):**
```python
env_key = os.getenv('SAML_PRIVATE_KEY')
if env_key:
    # USE ENVIRONMENT VARIABLE (checked FIRST!)
    self.key = env_key.encode('utf-8')
else:
    # USE FILE (only if env var doesn't exist)
    with open(self.key_file, 'rb') as f:
        self.key = f.read()
```

**The problem:**
1. Railway deployment has `SAML_PRIVATE_KEY` environment variable with OLD key
2. You generated NEW cert/key pair in `certs/saml.crt` and `certs/saml.key`
3. Code uses OLD key from environment variable to sign (line 107 in simple_saml.py)
4. You uploaded NEW certificate to Okta
5. Okta tries to verify signature with NEW certificate's public key
6. Signature was created with OLD private key
7. **Verification fails!** ❌

**Solution:**
Update the `SAML_PRIVATE_KEY` environment variable in Railway with the content from `certs/saml.key`.

---

## Verification Steps

After updating the environment variable:

1. **Redeploy** the Railway application
2. **Check logs** to see which key source is used:
   - Should see: `"Loading private key from SAML_PRIVATE_KEY environment variable"`
3. **Run test script**: `python3 test_deployment.py`
4. **Test SAML flow** in Okta
5. **Check Okta logs** - signature validation should succeed

---
