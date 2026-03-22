# Utility Scripts

This directory contains utility and diagnostic scripts for the OKTA Device Policy Proxy project.

## Certificate Management

### `generate_certs.py`
Generates self-signed certificates for SAML authentication testing.

**Usage:**
```bash
python scripts/generate_certs.py
```

### `gen_x509v3.py`
Generates X509v3 certificates with specific extensions required for SAML.

**Usage:**
```bash
python scripts/gen_x509v3.py
```

### `check_key_cert_match.py`
Verifies that a private key matches its corresponding certificate.

**Usage:**
```bash
python scripts/check_key_cert_match.py
```

## SAML Diagnostics

### `diagnose_signature_issue.py`
Comprehensive diagnostic tool for troubleshooting SAML signature issues with Okta.

**Usage:**
```bash
python scripts/diagnose_signature_issue.py
```

### `verify_okta_config.py`
Validates Okta configuration settings and connectivity.

**Usage:**
```bash
python scripts/verify_okta_config.py
```

### `verify_okta_response.py`
Analyzes and validates SAML responses from Okta for debugging purposes.

**Usage:**
```bash
python scripts/verify_okta_response.py
```

## Deployment

### `railway-deploy.sh`
Automated deployment script for Railway.app hosting platform.

**Usage:**
```bash
./scripts/railway-deploy.sh
```

## Notes

- Most scripts require the virtual environment to be activated
- Certificate scripts will output files to the `certs/` directory
- Diagnostic scripts may require environment variables to be configured
