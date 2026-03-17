# Okta Device Posture Provider (DPP)

A Python-based SAML 2.0 Identity Provider implementation with Okta Device Posture extensions. This service validates device compliance and management status before allowing authentication.

## Features

### Core Functionality
- ✅ **SAML 2.0 Protocol** - Full SAML 2.0 IdP implementation
- ✅ **Okta Device Posture Extensions** - Implements `urn:okta:saml:2.0:DevicePosture` namespace
- ✅ **Device Management Verification** - Checks if devices are enrolled in MDM/UEM
- ✅ **Compliance Checking** - Validates OS versions and security policies
- ✅ **Encryption Status** - Verifies device storage encryption
- ✅ **SAML Response Signing** - Digital signatures using X.509 certificates
- ✅ **Device Registration** - Admin interface for managing known devices

### Device Posture Checks
- Device ID validation
- Vendor and model tracking
- Operating system and version compliance
- Management status (MDM enrollment)
- Encryption status
- Additional custom facts (jailbreak detection, antivirus, firewall, etc.)

### SAML Extensions
The implementation includes Okta-specific SAML extensions:
- Device metadata in `AuthnContextDecl/Extension`
- Required `IsManaged` fact
- Optional compliance and security facts
- Custom device attributes

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│    Okta     │  SAML   │     DPP      │  Check  │   Device    │
│   (Okta)    │◄───────►│   Service    │◄───────►│  Registry   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │     MDM      │
                        │   (Future)   │
                        └──────────────┘
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or extract the repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Generate SAML certificates**
```bash
python generate_certs.py
```
This creates self-signed certificates in the `certs/` directory.

4. **Configure the service**
Edit `config.yaml` to set your Okta organization details:
```yaml
okta:
  entity_id: http://www.okta.com/exk<your-app-id>
  acs_url: https://<your-org>.okta.com/sso/saml2/<app-id>
```

5. **Run the service**
```bash
python app.py
```

The service will start on `http://0.0.0.0:8443`

## Configuration

### Server Settings
```yaml
server:
  host: 0.0.0.0      # Listen address
  port: 8443          # Listen port
  debug: true         # Enable debug mode
```

### SAML Settings
```yaml
saml:
  entity_id: https://dpp.example.com        # Your IdP entity ID
  sso_url: https://dpp.example.com/saml/sso  # SSO endpoint
  cert_file: certs/saml.crt                 # Signing certificate
  key_file: certs/saml.key                  # Private key
```

### Device Check Policies
```yaml
device_checks:
  require_managed: true      # Must be enrolled in MDM
  require_compliant: false   # Must meet compliance policies
  require_encrypted: false   # Must have encrypted storage

  allowed_os:               # Permitted operating systems
    - Windows
    - macOS
    - iOS
    - Android

  min_os_versions:          # Minimum OS versions
    Windows: "10.0"
    macOS: "12.0"
    iOS: "15.0"
    Android: "11.0"
```

## Usage

### Endpoints

#### `GET /`
Landing page with service information and endpoint links.

#### `POST /saml/sso`
SAML Single Sign-On endpoint. Accepts SAML AuthnRequest with device posture context.

**Parameters:**
- `SAMLRequest` - Base64 encoded SAML AuthnRequest
- `RelayState` - Optional relay state

#### `GET /saml/metadata`
Returns SAML metadata XML for IdP configuration.

#### `GET/POST /admin/devices`
Device registration and management interface.

#### `GET /health`
Health check endpoint returning service status.

### Device Registration

For demo purposes, devices can be pre-registered:

1. Navigate to `http://localhost:8443/admin/devices`
2. Enter device information:
   - Device ID
   - Management status (Managed/Not Managed)
   - Encryption status
   - Last sync time
3. Click "Register Device"

**Demo Device ID Patterns:**
- Devices with ID starting with `MANAGED-` or `MDM-` are automatically considered managed
- Devices with `SEC-` prefix are considered encrypted

### Testing Authentication

1. **Configure Okta:**
   - Create a new SAML 2.0 app integration
   - Set SSO URL to: `https://<your-dpp-host>:8443/saml/sso`
   - Upload SAML metadata from `/saml/metadata` endpoint
   - Enable device posture authentication context

2. **Initiate Authentication:**
   - Start SAML flow from Okta
   - You'll be redirected to the DPP login page
   - Enter device information
   - Submit for authentication

3. **View Results:**
   - If device passes posture checks → Authentication succeeds
   - If device fails checks → Error message displayed

## SAML Request/Response Flow

### 1. Okta Sends AuthnRequest
```xml
<samlp:AuthnRequest>
  <saml:Issuer>http://www.okta.com/exk...</saml:Issuer>
  <samlp:RequestedAuthnContext>
    <saml:AuthnContextClassRef>
      urn:okta:saml:2.0:DevicePosture
    </saml:AuthnContextClassRef>
  </samlp:RequestedAuthnContext>
</samlp:AuthnRequest>
```

### 2. DPP Validates Device Posture
- Checks device management status
- Validates OS version compliance
- Verifies encryption status
- Performs additional security checks

### 3. DPP Returns SAML Response with Device Posture
```xml
<saml:Response>
  <saml:Assertion>
    <saml:AuthnStatement>
      <saml:AuthnContext>
        <saml:AuthnContextDecl>
          <Extension>
            <okta:Device>
              <okta:DeviceID>MANAGED-123</okta:DeviceID>
              <okta:Vendor>Apple</okta:Vendor>
              <okta:Model>MacBook Pro</okta:Model>
              <okta:OS>macOS</okta:OS>
              <okta:OSVersion>14.1</okta:OSVersion>
              <okta:Posture>
                <okta:Fact Name="IsManaged" Value="true"/>
                <okta:Fact Name="IsCompliant" Value="true"/>
                <okta:Fact Name="IsEncrypted" Value="true"/>
              </okta:Posture>
            </okta:Device>
          </Extension>
        </saml:AuthnContextDecl>
      </saml:AuthnContext>
    </saml:AuthnStatement>
  </saml:Assertion>
</saml:Response>
```

## Extending the Implementation

### Custom Device Checks

Add custom verification logic in `device_checker.py`:

```python
def _additional_checks(self, device_id: str, os: str) -> Dict:
    facts = {}

    # Add your custom checks
    facts['CustomCheck'] = self._my_custom_check(device_id)

    return facts
```

### Integration with MDM/UEM

Replace simulated checks with real MDM API calls:

```python
def _check_managed(self, device_id: str) -> bool:
    # Call your MDM API
    response = mdm_api.check_enrollment(device_id)
    return response.is_enrolled
```

### Database Integration

Replace in-memory device registry with a database:

```python
from sqlalchemy import create_engine
from models import Device

def check_device_posture(self, device_id, ...):
    device = session.query(Device).filter_by(id=device_id).first()
    # ... rest of logic
```

## Suggested Additional Features

### 1. **Database Persistence**
- Store device registry in PostgreSQL/MySQL
- Track authentication history
- Device posture audit logs

### 2. **MDM Integration**
- **Microsoft Intune** API integration
- **Jamf Pro** (macOS/iOS)
- **VMware Workspace ONE**
- **Google Workspace** device management
- **Kandji** for Apple devices

### 3. **Advanced Device Attestation**
- **iOS DeviceCheck** API integration
- **Android SafetyNet** attestation
- **Windows TPM** attestation
- Hardware-backed key verification

### 4. **Policy Engine**
- Rule-based device policies
- Time-based access controls
- Risk scoring system
- Conditional access based on location/network

### 5. **Monitoring & Analytics**
- Prometheus metrics export
- Authentication success/failure rates
- Device compliance trends
- Real-time alerting (Slack, PagerDuty)

### 6. **Security Enhancements**
- Rate limiting and DDoS protection
- Request replay attack prevention
- Certificate pinning
- SAML encryption (in addition to signing)
- OAuth 2.0 client credentials for API access

### 7. **API Endpoints**
- RESTful API for device management
- Webhook notifications
- Bulk device import/export
- Compliance reporting API

### 8. **UI Improvements**
- React/Vue.js admin dashboard
- Device compliance visualization
- Real-time authentication monitoring
- Self-service device enrollment

### 9. **Multi-Tenancy**
- Support multiple organizations
- Tenant isolation
- Per-tenant policy configuration

### 10. **Compliance Reporting**
- Generate compliance reports (PDF/CSV)
- Automated compliance checks
- Integration with GRC tools
- SIEM integration (Splunk, ELK)

## Security Considerations

### Production Deployment
- ✅ Use valid SSL/TLS certificates (not self-signed)
- ✅ Enable HTTPS only (disable HTTP)
- ✅ Implement rate limiting
- ✅ Add authentication for admin endpoints
- ✅ Use secure session management
- ✅ Enable SAML response encryption
- ✅ Implement request replay protection
- ✅ Regular security audits
- ✅ Keep dependencies updated

### Certificate Management
- Rotate signing certificates regularly
- Store private keys securely (HSM, vault)
- Use strong key sizes (2048-bit minimum)
- Monitor certificate expiration

## Troubleshooting

### Certificate Errors
```
SAML certificates not found
```
**Solution:** Run `python generate_certs.py` to generate certificates.

### Device Not Managed Error
```
DEVICE_NOT_MANAGED
```
**Solution:**
- Register device via `/admin/devices` endpoint
- Or use device ID with `MANAGED-` or `MDM-` prefix

### OS Version Compliance Error
```
DEVICE_NOT_COMPLIANT
```
**Solution:** Ensure OS version meets minimum requirements in `config.yaml`

### SAML Parsing Error
```
Failed to parse AuthnRequest
```
**Solution:** Check that SAMLRequest is properly base64 encoded

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/
```

### Code Structure
```
.
├── app.py              # Main Flask application
├── saml_handler.py     # SAML request/response processing
├── device_checker.py   # Device posture verification
├── config.py           # Configuration management
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── generate_certs.py   # Certificate generation utility
└── certs/             # SAML certificates
    ├── saml.crt
    └── saml.key
```

## License

This is a sample implementation for educational and development purposes.

## Support

For issues, questions, or contributions, please refer to the project repository.

## References

- [Okta Device Posture IdP Documentation](https://help.okta.com/oie/en-us/content/topics/identity-engine/devices/device-assurance-device-posture-idp.htm)
- [SAML 2.0 Specification](http://docs.oasis-open.org/security/saml/v2.0/)
- [Okta SAML Technical Overview](https://developer.okta.com/docs/concepts/saml/)
