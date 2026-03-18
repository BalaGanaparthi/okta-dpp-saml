# Logging Guide

## Overview

The Device Posture Provider now includes a comprehensive logging system designed for production monitoring, debugging, and troubleshooting.

## Features

### Multi-Level Logging
- **DEBUG**: Detailed technical information for debugging
- **INFO**: General operational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages with stack traces
- **CRITICAL**: Critical system failures

### Output Destinations
- **Console**: Real-time logging to stdout (always enabled)
- **Application Log**: `logs/okta-dpp.log` (rotating, 10MB max, 5 backups)
- **Error Log**: `logs/okta-dpp-error.log` (ERROR and above only)

### Log Format
```
[2026-03-18 12:34:56] INFO [app.sso:145] SAML SSO request received: method=POST, has_relay_state=True
```

Components:
- Timestamp with milliseconds
- Log level
- Module.function:line_number
- Message

## Configuration

### Environment Variables

```bash
# Set log level
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Set log directory
export LOG_DIR=logs  # Default: ./logs
```

### Railway Configuration

In Railway, set environment variable:
```
LOG_LEVEL=INFO
```

The system automatically falls back to console-only logging if file system is unavailable.

## Logging Examples

### HTTP Requests
```
[2026-03-18 12:34:56] INFO Incoming request: POST /saml/sso from 192.168.1.1
[2026-03-18 12:34:56] INFO Request completed: POST /saml/sso - 200 (45.23ms)
```

### SAML Events
```
[2026-03-18 12:34:56] INFO 📥 Parsed AuthnRequest - ID: _abc12345678..., Issuer: exkabc123demo, Subject: user@example.com, Device Posture: True
[2026-03-18 12:34:57] INFO 📤 Created SAML Response - ID: _def98765432..., Status: Success, User: user@example.com, Signed: Yes, Size: 4567 bytes
```

### Device Checks
```
[2026-03-18 12:34:56] INFO 🔍 Checking device posture - ID: MANAGED-123, User: user@example.com, OS: macOS 14.1
[2026-03-18 12:34:56] DEBUG   ├─ Management check: ✓ Managed
[2026-03-18 12:34:56] DEBUG   ├─ Compliance check: ✓ Compliant
[2026-03-18 12:34:56] DEBUG   ├─ Encryption check: ✓ Encrypted
[2026-03-18 12:34:56] DEBUG   └─ Additional facts: 5 checks performed
[2026-03-18 12:34:56] INFO ✅ Device check completed - MANAGED-123: Managed=True, Compliant=True, Encrypted=True
```

### Device Posture Facts
```
[2026-03-18 12:34:57] INFO Device Posture Facts - IsManaged: True, IsCompliant: True, IsEncrypted: True
```

### Validation
```
[2026-03-18 12:34:56] DEBUG Validating posture - Requirements: Managed=True, Compliant=False, Encrypted=False
[2026-03-18 12:34:56] INFO ✅ Validation passed for device MANAGED-123
```

### Errors
```
[2026-03-18 12:34:56] ERROR Error: cannot import name 'verify' | Context: SSO endpoint error for user=user@example.com, issuer=http://www.okta.com/exkabc123
[2026-03-18 12:34:56] ERROR Traceback (most recent call last):
  File "/app/saml_handler.py", line 10, in <module>
    from signxml import XMLSigner, XMLVerifier, methods
ImportError: cannot import name 'verify' from 'OpenSSL.crypto'
```

### Startup Messages
```
[2026-03-18 12:34:55] INFO ======================================================================
[2026-03-18 12:34:55] INFO Starting Okta Device Posture Provider
[2026-03-18 12:34:55] INFO ======================================================================
[2026-03-18 12:34:55] INFO Version: 1.0.0
[2026-03-18 12:34:55] INFO Entity ID: https://dpp.example.com
[2026-03-18 12:34:55] INFO SSO URL: https://dpp.example.com/saml/sso
[2026-03-18 12:34:55] INFO Host: 0.0.0.0
[2026-03-18 12:34:55] INFO Port: 8443
[2026-03-18 12:34:55] INFO Debug Mode: False
[2026-03-18 12:34:55] INFO ✅ SAML certificates loaded successfully (cert: 1234 bytes, key: 5678 bytes)
[2026-03-18 12:34:55] INFO Device checks - Require Managed: True
[2026-03-18 12:34:55] INFO Device checks - Require Compliant: False
[2026-03-18 12:34:55] INFO Device checks - Require Encrypted: False
[2026-03-18 12:34:55] INFO ======================================================================
[2026-03-18 12:34:55] INFO Server starting...
[2026-03-18 12:34:55] INFO ======================================================================
```

## Structured Logging Functions

### log_request(logger, method, path, status_code, duration_ms)
Logs HTTP request details with timing.

```python
log_request(logger, 'POST', '/saml/sso', 200, 45.23)
# Output: [INFO] POST /saml/sso - 200 (45.23ms)
```

### log_saml_event(logger, event_type, request_id, user, issuer, details)
Logs SAML protocol events.

```python
log_saml_event(
    logger, 'AuthnRequest received',
    request_id='_abc123',
    user='user@example.com',
    issuer='http://www.okta.com/exkabc123',
    details='Device posture: True'
)
# Output: [INFO] SAML AuthnRequest received [ID: _abc123...] [User: user@example.com] [Issuer: exkabc123] - Device posture: True
```

### log_device_check(logger, device_id, user, is_managed, is_compliant, result)
Logs device posture check results.

```python
log_device_check(logger, 'MANAGED-123', 'user@example.com', True, True, True)
# Output: [INFO] Device Check [PASS] - Device: MANAGED-123, User: user@example.com, Managed: True, Compliant: True
```

### log_error(logger, error, context)
Logs errors with context and stack trace.

```python
log_error(logger, exception, "Failed to parse SAML request")
# Output: [ERROR] Error: <error message> | Context: Failed to parse SAML request
# Followed by full stack trace
```

### log_security_event(logger, event_type, details, severity)
Logs security-related events.

```python
log_security_event(logger, 'FAILED_AUTH', 'Device not managed', 'WARNING')
# Output: [WARNING] SECURITY [FAILED_AUTH] - Device not managed
```

## Monitoring in Railway

### View Logs
```bash
# Real-time logs
railway logs --follow

# Filter by level
railway logs | grep ERROR

# Last 100 lines
railway logs --tail 100
```

### In Railway Dashboard
1. Go to your project
2. Click "Deployments"
3. Select active deployment
4. View "Build Logs" or "Application Logs"

## Log Rotation

Automatic rotation when files reach 10MB:
- Keeps 5 backup files
- Old files: `okta-dpp.log.1`, `okta-dpp.log.2`, etc.
- Oldest files are automatically deleted

## Performance Impact

Logging is optimized for minimal performance impact:
- Async file writes
- Buffered I/O
- Debug logs disabled in production by default
- Health check endpoint logging disabled

## Troubleshooting

### No log files created
**Cause**: No write permissions or running in Railway
**Solution**: Logs automatically fall back to console only

### Too many logs
**Solution**: Increase log level
```bash
export LOG_LEVEL=WARNING  # Only WARNING, ERROR, CRITICAL
```

### Missing stack traces
**Cause**: Using logger.error() without exc_info
**Solution**: Use `log_error()` helper or `logger.error("msg", exc_info=True)`

### Debug logs not showing
**Cause**: LOG_LEVEL set to INFO or higher
**Solution**: Set LOG_LEVEL=DEBUG

## Best Practices

1. **Use appropriate log levels**
   - DEBUG: Detailed diagnostic information
   - INFO: Normal operations
   - WARNING: Unexpected but handled situations
   - ERROR: Error conditions
   - CRITICAL: System failures

2. **Include context**
   - User ID, Device ID, Request ID
   - Timing information
   - Related entity identifiers

3. **Don't log sensitive data**
   - Passwords, tokens, API keys
   - Full SAML assertions
   - Personal information (unless required)

4. **Use structured logging**
   - Use helper functions when available
   - Include key-value pairs for easy parsing
   - Format consistently

5. **Log at the right place**
   - Entry points (requests received)
   - Exit points (responses sent)
   - State changes
   - Errors and exceptions
   - Security events

## Integration with Monitoring Tools

### Prometheus/Grafana
Parse logs for metrics:
- Request count by status code
- Response time percentiles
- Error rates
- SAML authentication success/failure rates

### ELK Stack (Elasticsearch, Logstash, Kibana)
- Ship logs to Logstash
- Index in Elasticsearch
- Visualize in Kibana

### Datadog/New Relic
- Forward logs to APM platform
- Correlate with metrics and traces
- Set up alerts on error rates

### Sentry
For error tracking, integrate Sentry:
```python
import sentry_sdk
sentry_sdk.init(dsn="your-dsn")
```

## Log Analysis Examples

### Find failed authentications
```bash
grep "FAIL" logs/okta-dpp.log
grep "Device Posture Facts - IsManaged: False" logs/okta-dpp.log
```

### Count requests by endpoint
```bash
grep "Request completed" logs/okta-dpp.log | cut -d' ' -f6 | sort | uniq -c
```

### Average response time
```bash
grep "Request completed" logs/okta-dpp.log | grep -oP '\(\K[0-9.]+' | awk '{s+=$1} END {print s/NR}'
```

### Errors in last hour
```bash
tail -1000 logs/okta-dpp-error.log
```

### Authentication timeline for user
```bash
grep "user@example.com" logs/okta-dpp.log
```

## Summary

The comprehensive logging system provides:
- ✅ Production-ready monitoring
- ✅ Detailed debugging information
- ✅ Security audit trail
- ✅ Performance tracking
- ✅ Error diagnostics
- ✅ Railway/cloud compatible
- ✅ Structured and parseable output
- ✅ Automatic rotation and management
- ✅ Multiple output destinations
- ✅ Environment-based configuration

This makes troubleshooting Railway deployment issues much easier!
