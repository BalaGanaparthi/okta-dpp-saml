# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Device Posture Provider                      │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │   Flask      │      │    SAML      │      │   Device     │    │
│  │   App        │─────▶│   Handler    │◀────▶│   Checker    │    │
│  │  (app.py)    │      │(saml_handler)│      │(device_check)│    │
│  └──────────────┘      └──────────────┘      └──────────────┘    │
│         │                      │                      │             │
│         │                      │                      ▼             │
│         ▼                      ▼              ┌──────────────┐    │
│  ┌──────────────┐      ┌──────────────┐      │   Device     │    │
│  │   Config     │      │   Certs &    │      │   Registry   │    │
│  │  (config.py) │      │   Crypto     │      │  (In-Memory) │    │
│  └──────────────┘      └──────────────┘      └──────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ SAML 2.0 + Device Posture
                                ▼
                        ┌──────────────┐
                        │     Okta     │
                        │  (Service    │
                        │   Provider)  │
                        └──────────────┘
```

## Component Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                            External Actors                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌──────────┐           ┌──────────┐           ┌──────────┐         │
│   │   User   │           │   Okta   │           │  Admin   │         │
│   │  Browser │           │   IdP    │           │   User   │         │
│   └────┬─────┘           └────┬─────┘           └────┬─────┘         │
│        │                      │                      │                │
└────────┼──────────────────────┼──────────────────────┼────────────────┘
         │                      │                      │
         │ HTTPS                │ SAML 2.0             │ HTTPS (Admin)
         │                      │ + Device Posture     │
         ▼                      ▼                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Web Server Layer (Flask)                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│   │  / (Index)  │    │ /saml/sso   │    │ /admin/*    │             │
│   │   Endpoint  │    │  (SSO Auth) │    │  (Device    │             │
│   └─────────────┘    └─────────────┘    │   Mgmt)     │             │
│                                          └─────────────┘             │
│   ┌─────────────┐    ┌─────────────┐                                 │
│   │/saml/meta   │    │  /health    │                                 │
│   │  data       │    │  (Monitor)  │                                 │
│   └─────────────┘    └─────────────┘                                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Business Logic Layer                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              SAML Handler (saml_handler.py)                  │    │
│  ├──────────────────────────────────────────────────────────────┤    │
│  │  • parse_authn_request()    - Decode & parse SAML request   │    │
│  │  • create_authn_response()  - Build SAML response           │    │
│  │  • _sign_xml()              - Sign with X.509 cert          │    │
│  │  • get_metadata()           - Generate IdP metadata         │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │           Device Checker (device_checker.py)                 │    │
│  ├──────────────────────────────────────────────────────────────┤    │
│  │  • check_device_posture()   - Main verification entry       │    │
│  │  • _check_managed()         - MDM enrollment check          │    │
│  │  • _check_os_compliance()   - OS version validation         │    │
│  │  • _check_encryption()      - Disk encryption check         │    │
│  │  • validate_posture()       - Policy enforcement            │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          Data Access Layer                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐   │
│  │   Config Mgmt    │    │   Certificate    │    │   Device     │   │
│  │   (config.py)    │    │    Storage       │    │   Registry   │   │
│  │                  │    │   (certs/*)      │    │  (dict/DB)   │   │
│  │  • YAML parser   │    │                  │    │              │   │
│  │  • Dot notation  │    │  • saml.crt      │    │ • In-memory  │   │
│  │  • Defaults      │    │  • saml.key      │    │ • Extensible │   │
│  └──────────────────┘    └──────────────────┘    └──────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
User                  Okta (SP)              DPP (IdP)              MDM/UEM
 │                        │                       │                    │
 │  1. Access App         │                       │                    │
 ├───────────────────────▶│                       │                    │
 │                        │                       │                    │
 │                        │  2. SAML AuthnRequest │                    │
 │                        │   (with Device        │                    │
 │                        │    Posture context)   │                    │
 │                        ├──────────────────────▶│                    │
 │                        │                       │                    │
 │                        │  3. Redirect to Login │                    │
 │◀───────────────────────┴───────────────────────┤                    │
 │                                                 │                    │
 │  4. Enter Device Info                           │                    │
 │  (Device ID, OS, Version, etc.)                 │                    │
 ├────────────────────────────────────────────────▶│                    │
 │                                                 │                    │
 │                                                 │  5. Check Device   │
 │                                                 │     Management     │
 │                                                 ├───────────────────▶│
 │                                                 │                    │
 │                                                 │  6. Device Status  │
 │                                                 │◀───────────────────┤
 │                                                 │  (Managed: Y/N,    │
 │                                                 │   Compliant: Y/N,  │
 │                                                 │   Encrypted: Y/N)  │
 │                                                 │                    │
 │                                                 │ 7. Validate Policy │
 │                                                 │    & Build SAML    │
 │                                                 │    Response        │
 │                                                 │                    │
 │  8. POST SAMLResponse                           │                    │
 │     (with Device Posture data)                  │                    │
 │◀────────────────────────────────────────────────┤                    │
 │                                                                      │
 │  9. POST to Okta ACS                                                 │
 ├─────────────────────▶                                                │
 │                        │                                             │
 │                        │ 10. Validate SAML                           │
 │                        │     & Device Posture                        │
 │                        │                                             │
 │  11. Grant Access      │                                             │
 │     (or Deny based     │                                             │
 │      on posture)       │                                             │
 │◀───────────────────────┤                                             │
 │                        │                                             │
```

## SAML Message Structure

### AuthnRequest (Okta → DPP)

```xml
<samlp:AuthnRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="_abc123..."
    Version="2.0"
    IssueInstant="2024-01-01T00:00:00Z"
    Destination="https://dpp.example.com/saml/sso"
    AssertionConsumerServiceURL="https://okta.com/sso/saml2/...">

    <saml:Issuer>http://www.okta.com/exkabc123</saml:Issuer>

    <saml:Subject>
        <saml:NameID>user@example.com</saml:NameID>
    </saml:Subject>

    <samlp:RequestedAuthnContext Comparison="minimum">
        <saml:AuthnContextClassRef>
            urn:okta:saml:2.0:DevicePosture    ← Device Posture Required
        </saml:AuthnContextClassRef>
    </samlp:RequestedAuthnContext>

</samlp:AuthnRequest>
```

### SAML Response (DPP → Okta)

```xml
<samlp:Response
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="_response123..."
    Version="2.0"
    IssueInstant="2024-01-01T00:00:05Z"
    InResponseTo="_abc123..."
    Destination="https://okta.com/sso/saml2/...">

    <saml:Issuer>https://dpp.example.com</saml:Issuer>

    <samlp:Status>
        <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </samlp:Status>

    <saml:Assertion ID="_assertion456..." Version="2.0" IssueInstant="...">

        <saml:Issuer>https://dpp.example.com</saml:Issuer>

        <saml:Subject>
            <saml:NameID>user@example.com</saml:NameID>
            <saml:SubjectConfirmation Method="...">
                <saml:SubjectConfirmationData InResponseTo="_abc123..." .../>
            </saml:SubjectConfirmation>
        </saml:Subject>

        <saml:Conditions NotBefore="..." NotOnOrAfter="...">
            <saml:AudienceRestriction>
                <saml:Audience>http://www.okta.com/exkabc123</saml:Audience>
            </saml:AudienceRestriction>
        </saml:Conditions>

        <saml:AuthnStatement AuthnInstant="..." SessionIndex="...">
            <saml:AuthnContext>
                <saml:AuthnContextClassRef>
                    urn:okta:saml:2.0:DevicePosture
                </saml:AuthnContextClassRef>

                <saml:AuthnContextDecl>
                    <Extension>
                        ┌─────────────────────────────────────────┐
                        │     Device Posture Extension (Okta)    │
                        └─────────────────────────────────────────┘
                        <okta:Device xmlns:okta="urn:okta:saml:2.0:DevicePosture">
                            <okta:DeviceID>MANAGED-ABC123</okta:DeviceID>
                            <okta:Vendor>Apple</okta:Vendor>
                            <okta:Model>MacBook Pro</okta:Model>
                            <okta:OS>macOS</okta:OS>
                            <okta:OSVersion>14.1</okta:OSVersion>

                            <okta:Posture>
                                <okta:Fact Name="IsManaged" Value="true"/>     ← Required
                                <okta:Fact Name="IsCompliant" Value="true"/>   ← Optional
                                <okta:Fact Name="IsEncrypted" Value="true"/>   ← Optional
                                <okta:Fact Name="IsJailbroken" Value="false"/> ← Custom
                                <okta:Fact Name="HasAntivirus" Value="true"/>  ← Custom
                            </okta:Posture>
                        </okta:Device>
                    </Extension>
                </saml:AuthnContextDecl>
            </saml:AuthnContext>
        </saml:AuthnStatement>

        <saml:AttributeStatement>
            <saml:Attribute Name="email">
                <saml:AttributeValue>user@example.com</saml:AttributeValue>
            </saml:Attribute>
        </saml:AttributeStatement>

    </saml:Assertion>

</samlp:Response>
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       Configuration Flow                        │
└─────────────────────────────────────────────────────────────────┘

config.yaml ──▶ Config() ──▶ app.py
                   │            │
                   ├──────────▶ saml_handler.py
                   │            │
                   └──────────▶ device_checker.py


┌─────────────────────────────────────────────────────────────────┐
│                    Device Registration Flow                     │
└─────────────────────────────────────────────────────────────────┘

Admin ──▶ /admin/devices ──▶ DeviceChecker.register_device()
                                      │
                                      ▼
                              device_registry{}
                                      │
                                      ▼
                              (Used during auth)


┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                          │
└─────────────────────────────────────────────────────────────────┘

SAMLRequest ──▶ parse_authn_request()
                        │
                        ▼
                   request_data{}
                        │
                        ├──▶ User Input (device info)
                        │
                        ▼
             check_device_posture()
                        │
                ┌───────┴───────┐
                │               │
                ▼               ▼
         _check_managed()  _check_os_compliance()
                │               │
                │       ┌───────┴───────┐
                │       │               │
                ▼       ▼               ▼
         device_registry  _check_encryption()
                │               │
                └───────┬───────┘
                        │
                        ▼
                  DevicePosture{}
                        │
                        ▼
                validate_posture()
                        │
                ┌───────┴───────┐
                │               │
            SUCCESS          FAILURE
                │               │
                ▼               ▼
       create_authn_response(is_success=True/False)
                │
                ├──▶ Build XML with Device Posture
                │
                ├──▶ _sign_xml()
                │
                └──▶ Base64 encode
                        │
                        ▼
                  SAMLResponse
                        │
                        ▼
                  POST to Okta
```

## Class Diagram

```
┌─────────────────────────────────┐
│          Config                 │
├─────────────────────────────────┤
│ - config: dict                  │
│ - config_file: str              │
├─────────────────────────────────┤
│ + __init__(config_file)         │
│ + get(key, default)             │
│ + save()                        │
│ + _load_config()                │
│ + _default_config()             │
└─────────────────────────────────┘
                 △
                 │ uses
                 │
┌────────────────┼────────────────────┬────────────────┐
│                │                    │                │
▼                ▼                    ▼                ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   SAMLHandler    │    │  DeviceChecker   │    │   Flask App      │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ - config         │    │ - config         │    │ - saml_handler   │
│ - entity_id      │    │ - device_registry│    │ - device_checker │
│ - cert           │    ├──────────────────┤    │ - config         │
│ - key            │    │ + register_device│    ├──────────────────┤
├──────────────────┤    │ + check_posture  │    │ + index()        │
│ + parse_authn    │    │ + validate_      │    │ + sso()          │
│ + create_response│    │   posture        │    │ + metadata()     │
│ + get_metadata   │    │ + _check_managed │    │ + admin_devices()│
│ + _sign_xml      │    │ + _check_os      │    │ + health()       │
└──────────────────┘    │ + _check_encrypt │    └──────────────────┘
                        │ + _compare_vers  │
                        └──────────────────┘
                                 │
                                 │ creates
                                 ▼
                        ┌──────────────────┐
                        │  DevicePosture   │
                        ├──────────────────┤
                        │ - device_id      │
                        │ - vendor         │
                        │ - model          │
                        │ - os             │
                        │ - os_version     │
                        │ - is_managed     │
                        │ - is_compliant   │
                        │ - is_encrypted   │
                        │ - additional_    │
                        │   facts          │
                        ├──────────────────┤
                        │ + to_dict()      │
                        └──────────────────┘
```

## Deployment Architecture

### Single Instance (Development)

```
┌──────────────────────────────────┐
│         Server                   │
│  ┌────────────────────────────┐  │
│  │   Flask App :8443          │  │
│  │   (Python Process)         │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │   Config & Certs           │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### Production (Load Balanced)

```
                        ┌──────────────┐
                        │   Internet   │
                        └──────┬───────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Load Balancer /   │
                    │  Reverse Proxy     │
                    │  (Nginx/HAProxy)   │
                    └────────┬───────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  DPP #1    │  │  DPP #2    │  │  DPP #3    │
     │  :8443     │  │  :8443     │  │  :8443     │
     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   PostgreSQL    │
                 │   (Device DB)   │
                 └─────────────────┘
```

### Kubernetes Deployment

```
┌───────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                     Ingress Controller                  │ │
│  │                  (TLS Termination)                      │ │
│  └───────────────────────┬─────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                      Service                            │ │
│  │                   (okta-dpp:443)                        │ │
│  └───────────────────────┬─────────────────────────────────┘ │
│                          │                                   │
│        ┌─────────────────┼─────────────────┐                │
│        │                 │                 │                │
│        ▼                 ▼                 ▼                │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │  Pod #1  │     │  Pod #2  │     │  Pod #3  │           │
│  │  (DPP)   │     │  (DPP)   │     │  (DPP)   │           │
│  └────┬─────┘     └────┬─────┘     └────┬─────┘           │
│       │                │                │                   │
│       │  ┌─────────────┴────────────┐   │                  │
│       │  │                          │   │                  │
│       ▼  ▼                          ▼   ▼                  │
│  ┌──────────────┐           ┌──────────────┐              │
│  │  ConfigMap   │           │   Secret     │              │
│  │  (config)    │           │  (certs)     │              │
│  └──────────────┘           └──────────────┘              │
│                                                             │
└───────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Transport Security                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • TLS 1.2/1.3                                           │  │
│  │  • Valid SSL certificates                                │  │
│  │  • HSTS headers                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Layer 2: Application Security                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • XML signature verification (defusedxml)               │  │
│  │  • SAML response signing                                 │  │
│  │  • Input validation                                      │  │
│  │  • CSRF protection                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Layer 3: Authentication & Authorization                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Device posture validation                             │  │
│  │  • Policy enforcement                                    │  │
│  │  • Admin endpoint protection                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Layer 4: Data Protection                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Certificate storage security                          │  │
│  │  • Configuration encryption                              │  │
│  │  • Audit logging                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

```
┌──────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Application Metrics                                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • Authentication rate (auth/sec)                      │ │
│  │  • Success/failure ratio                               │ │
│  │  • Response time (p50, p95, p99)                       │ │
│  │  • Device posture status distribution                  │ │
│  │  • Error rates by type                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│                   Prometheus                                 │
│                          │                                   │
│                          ▼                                   │
│                      Grafana                                 │
│                                                              │
│  Logs                                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • Authentication logs                                 │ │
│  │  • Device check logs                                   │ │
│  │  • Error logs                                          │ │
│  │  • Audit logs                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│               ELK Stack / Loki                               │
│                                                              │
│  Alerts                                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • High error rate                                     │ │
│  │  • Response time degradation                           │ │
│  │  • Certificate expiration                              │ │
│  │  • Service unavailability                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│            PagerDuty / Slack / Email                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | Flask 3.0.0 | HTTP server & routing |
| **SAML Processing** | lxml 5.1.0 | XML parsing |
| **XML Signing** | signxml 3.2.2 | Digital signatures |
| **Cryptography** | cryptography 41.0.7 | Certificate operations |
| **Configuration** | PyYAML 6.0.1 | YAML parsing |
| **Security** | defusedxml 0.7.1 | Secure XML parsing |
| **Date Handling** | python-dateutil 2.8.2 | Timestamp operations |
| **Containerization** | Docker | Deployment |
| **Orchestration** | Kubernetes (optional) | Scaling |
| **Reverse Proxy** | Nginx / HAProxy | Load balancing |
| **Monitoring** | Prometheus + Grafana | Observability |

---

This architecture is designed for:
- ✅ **Scalability** - Stateless design for horizontal scaling
- ✅ **Security** - Multiple security layers
- ✅ **Maintainability** - Modular, well-documented code
- ✅ **Extensibility** - Easy to add new features
- ✅ **Reliability** - Health checks and monitoring
- ✅ **Performance** - Optimized for high throughput
