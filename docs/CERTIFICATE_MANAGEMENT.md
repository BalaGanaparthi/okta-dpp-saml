# Certificate Management

## Important: Pre-Generated Certificates Only

**This project uses PRE-GENERATED certificates that are committed to the repository.**

### ⚠️ Key Principles

1. **Certificates are generated ONCE** using `scripts/gen_x509v3.py` or `scripts/generate_certs.py`
2. **Certificates are stored in `certs/` folder** and committed to git
3. **NO certificate generation happens during deployment or runtime**
4. **The same certificates are used across all environments**

This approach ensures:
- ✅ Consistency across deployments
- ✅ No confusion about which certs are in use
- ✅ Faster deployment (no generation time)
- ✅ Predictable behavior
- ✅ Easy certificate management

---

## Certificate Location

```
certs/
├── saml.crt    # Public certificate (committed to git)
└── saml.key    # Private key (committed to git)
```

**Both files are tracked in git** (see `.gitignore` - .crt and .key are NOT ignored)

---

## How Certificates Are Used

### During Deployment (Railway/Docker)

1. **Build Phase:**
   ```dockerfile
   # Dockerfile just copies everything including certs
   COPY . .
   ```
   The pre-generated certificates in `certs/` are copied into the Docker image.

2. **Runtime:**
   ```python
   # src/saml_handler.py loads from files
   with open('certs/saml.crt', 'rb') as f:
       self.cert = f.read()

   with open('certs/saml.key', 'rb') as f:
       self.key = f.read()
   ```

### During Local Development

Same process - certificates are loaded from `certs/` folder.

---

## When to Generate New Certificates

Generate new certificates only when:
- ❗ Certificate is expiring soon (check validity period)
- ❗ Certificate is compromised or needs to be rotated
- ❗ Moving to a new domain/environment
- ❗ Security policy requires rotation

### How to Generate New Certificates

```bash
# Method 1: X509v3 certificate (recommended)
python3 scripts/gen_x509v3.py

# Method 2: Basic certificate
python3 scripts/generate_certs.py

# Verify the new certificates
python3 scripts/check_key_cert_match.py

# View certificate details
openssl x509 -in certs/saml.crt -noout -text
```

### After Generating New Certificates

1. **Test locally first:**
   ```bash
   python3 -m src.app
   ```

2. **Commit and push:**
   ```bash
   git add certs/saml.crt certs/saml.key
   git commit -m "Update SAML certificates"
   git push
   ```

3. **Update Okta:**
   - Go to Okta SAML app settings
   - Upload the new `certs/saml.crt`
   - Save configuration

4. **Verify deployment:**
   - Wait for Railway deployment to complete
   - Test SAML authentication flow

---

## Current Certificate Details

To check the current certificate:

```bash
# Show certificate info
openssl x509 -in certs/saml.crt -noout -text

# Show expiration date
openssl x509 -in certs/saml.crt -noout -enddate

# Verify key matches certificate
python3 scripts/check_key_cert_match.py
```

**Current Certificate:**
- **Generated:** March 22, 2026
- **Valid Until:** March 22, 2027
- **Subject:** okta-dpp-saml-production.up.railway.app
- **Key Type:** RSA 2048-bit
- **Algorithm:** SHA256withRSA

---

## Security Considerations

### Why Commit Certificates to Git?

For this **development/testing project**, it's acceptable to commit certificates because:
- These are self-signed certificates (not from a trusted CA)
- Used for SAML signing, not TLS/SSL
- Repository is under your control
- Makes deployment simpler

### For Production Systems

In production, consider:
- Using a proper Certificate Authority (CA)
- Storing certificates in a secrets manager (Vault, AWS Secrets Manager, etc.)
- Implementing certificate rotation automation
- Using separate certificates per environment
- Regular security audits

---

## Troubleshooting

### Certificate Files Not Found

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'certs/saml.crt'`

**Solution:**
1. Check if certs exist: `ls -la certs/`
2. If missing, generate them: `python3 scripts/gen_x509v3.py`
3. Commit them: `git add certs/ && git commit -m "Add certificates"`

### Certificate Validation Fails in Okta

**Error:** Okta rejects the SAML response signature

**Solution:**
1. Verify certificate is uploaded to Okta
2. Check certificate matches: `python3 scripts/check_key_cert_match.py`
3. Ensure certificate is the same one uploaded to Okta
4. Check certificate hasn't expired: `openssl x509 -in certs/saml.crt -noout -dates`

### Different Certificates on Local vs Deployed

**Error:** Works locally but fails in production

**Solution:**
1. Ensure certificates are committed: `git status certs/`
2. Push certificates: `git push`
3. Redeploy: Railway will pick up the committed certs
4. Update Okta with the correct certificate

---

## Certificate Rotation Schedule

**Recommended Schedule:**
- Review: Every 3 months
- Rotate: Every 6-12 months (before expiry)
- Emergency rotation: Immediately if compromised

**Rotation Process:**
1. Generate new certificates
2. Test locally
3. Commit and push
4. Update Okta configuration
5. Monitor SAML authentication
6. Document the rotation

---

## Commands Reference

```bash
# Generate new X509v3 certificate
python3 scripts/gen_x509v3.py

# Generate basic certificate
python3 scripts/generate_certs.py

# Verify key/cert match
python3 scripts/check_key_cert_match.py

# View certificate details
openssl x509 -in certs/saml.crt -noout -text

# Check expiration
openssl x509 -in certs/saml.crt -noout -enddate

# View certificate in PEM format
cat certs/saml.crt

# Test certificate loading
python3 -c "from src.saml_handler import SAMLHandler; from src.config import Config; h = SAMLHandler(Config()); print('✓ Certs loaded')"
```

---

## Summary

✅ **DO:**
- Use pre-generated certificates from `certs/` folder
- Commit certificates to git
- Generate certificates ONLY when needed
- Test locally before deploying
- Update Okta after certificate changes

❌ **DON'T:**
- Generate certificates during deployment
- Use environment variables for certificate content
- Generate certificates at runtime
- Use different certificates in different environments (for this project)

---

**The single source of truth for certificates: `certs/` folder in the repository**
