# Quick Start Guide

Get your Device Posture Provider running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Generate SAML Certificates

```bash
python generate_certs.py
```

This creates:
- `certs/saml.crt` - Public certificate
- `certs/saml.key` - Private key

## Step 3: Configure (Optional)

Edit `config.yaml` to customize:
- Server host/port
- Device check policies
- Okta organization details

## Step 4: Run the Service

```bash
python app.py
```

The service starts on `http://0.0.0.0:8443`

## Step 5: Test the Service

### View the Landing Page
Open your browser to: `http://localhost:8443`

### Check SAML Metadata
Visit: `http://localhost:8443/saml/metadata`

### Register a Test Device
1. Go to: `http://localhost:8443/admin/devices`
2. Register a device:
   - Device ID: `MANAGED-TEST-001`
   - Status: Managed
   - Encrypted: Yes

### Test Authentication Flow

You can test with a sample SAML request. Create a file `test_request.xml`:

```xml
<?xml version="1.0"?>
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    ID="_test123"
                    Version="2.0"
                    IssueInstant="2024-01-01T00:00:00Z"
                    Destination="http://localhost:8443/saml/sso"
                    AssertionConsumerServiceURL="http://localhost:8443/test/acs">
  <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">http://www.okta.com/test</saml:Issuer>
  <samlp:RequestedAuthnContext>
    <saml:AuthnContextClassRef xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
      urn:okta:saml:2.0:DevicePosture
    </saml:AuthnContextClassRef>
  </samlp:RequestedAuthnContext>
</samlp:AuthnRequest>
```

## Integrating with Okta

### 1. Create SAML App in Okta

1. Log into your Okta admin console
2. Applications → Create App Integration
3. Select "SAML 2.0"
4. Configure:
   - **Single sign on URL**: `https://<your-dpp-host>:8443/saml/sso`
   - **Audience URI**: `https://dpp.example.com` (or your entity_id)
   - **Default RelayState**: (leave empty)
   - **Name ID format**: EmailAddress
   - **Application username**: Email

### 2. Configure Authentication Context

In the SAML settings, add:
- **Authentication context class**: `urn:okta:saml:2.0:DevicePosture`

### 3. Upload Metadata (Optional)

Upload the metadata from: `http://<your-dpp-host>:8443/saml/metadata`

### 4. Create Device Assurance Policy

1. Security → Device Integrations
2. Add your DPP as a device posture provider
3. Create device assurance policy referencing your DPP

### 5. Test

1. Assign users to the SAML app
2. User attempts to access the app
3. User is redirected to DPP for device verification
4. DPP checks device posture and returns result to Okta

## Testing Scenarios

### ✅ Successful Authentication
- Device ID: `MANAGED-ABC123` or `MDM-XYZ789`
- OS: macOS 14.1 or Windows 10.0+
- Result: Authentication succeeds

### ❌ Device Not Managed
- Device ID: `UNMANAGED-001`
- Result: `DEVICE_NOT_MANAGED` error

### ❌ OS Not Compliant
- Device ID: `MANAGED-OLD`
- OS: Windows 8.0 (below minimum)
- Result: `DEVICE_NOT_COMPLIANT` error

## Troubleshooting

### Port Already in Use
```bash
# Change port in config.yaml
server:
  port: 9443
```

### Certificate Not Found
```bash
# Regenerate certificates
python generate_certs.py
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Next Steps

- Review `README.md` for detailed documentation
- Customize device checks in `device_checker.py`
- Integrate with your MDM system
- Add database persistence
- Deploy to production with proper SSL/TLS

## Demo Mode

The application includes demo shortcuts:
- Device IDs starting with `MANAGED-` or `MDM-` are automatically managed
- Device IDs starting with `SEC-` are considered encrypted
- Use `/admin/devices` to register specific devices

## Production Checklist

Before deploying to production:

- [ ] Replace self-signed certificates with valid SSL/TLS certs
- [ ] Update `config.yaml` with production URLs
- [ ] Enable authentication for `/admin/*` endpoints
- [ ] Integrate with real MDM/UEM system
- [ ] Add database for device registry
- [ ] Set up monitoring and logging
- [ ] Implement rate limiting
- [ ] Review security settings
- [ ] Test failover scenarios
- [ ] Document runbooks

Happy device posturing! 🛡️
