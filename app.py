"""
Okta Device Posture Provider (DPP)
SAML 2.0 Identity Provider with Device Posture Extensions
"""
import logging
import sys
from flask import Flask, request, render_template_string, redirect, make_response
from config import Config
from saml_handler import SAMLHandler
from device_checker import DeviceChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'change-this-to-random-secret-key'

# Load configuration
config = Config()

# Initialize handlers
saml_handler = SAMLHandler(config)
device_checker = DeviceChecker(config)


# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Device Posture Provider - Authentication</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .info-section {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .info-section h3 {
            margin-top: 0;
            color: #333;
            font-size: 16px;
        }
        .info-section p {
            margin: 5px 0;
            color: #555;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            box-sizing: border-box;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            width: 100%;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .error {
            background: #fee;
            border-left: 4px solid #f44;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            color: #c33;
        }
        .help-text {
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Device Posture Provider</h1>
        <p class="subtitle">Secure Authentication with Device Verification</p>

        {% if error %}
        <div class="error">
            <strong>Authentication Failed:</strong> {{ error }}
        </div>
        {% endif %}

        <div class="info-section">
            <h3>SAML Request Information</h3>
            <p><strong>From:</strong> {{ issuer }}</p>
            <p><strong>User:</strong> {{ subject or 'Not specified' }}</p>
            <p><strong>Device Posture Check:</strong> {{ 'Required' if device_posture_requested else 'Not Required' }}</p>
        </div>

        <form method="POST" action="{{ action }}">
            <input type="hidden" name="SAMLRequest" value="{{ saml_request }}">
            <input type="hidden" name="RelayState" value="{{ relay_state }}">

            <div class="form-group">
                <label>Device ID *</label>
                <input type="text" name="device_id" required
                       placeholder="e.g., MANAGED-ABC123 or MDM-XYZ789">
                <p class="help-text">For demo: use prefix MANAGED- or MDM- for managed devices</p>
            </div>

            <div class="form-group">
                <label>Device Vendor *</label>
                <input type="text" name="vendor" required placeholder="e.g., Apple, Dell, Samsung">
            </div>

            <div class="form-group">
                <label>Device Model *</label>
                <input type="text" name="model" required placeholder="e.g., MacBook Pro, iPhone 15">
            </div>

            <div class="form-group">
                <label>Operating System *</label>
                <select name="os" required>
                    <option value="">Select OS...</option>
                    <option value="Windows">Windows</option>
                    <option value="macOS">macOS</option>
                    <option value="iOS">iOS</option>
                    <option value="Android">Android</option>
                    <option value="Linux">Linux</option>
                </select>
            </div>

            <div class="form-group">
                <label>OS Version *</label>
                <input type="text" name="os_version" required placeholder="e.g., 14.1, 11.0">
            </div>

            <button type="submit">Authenticate with Device Posture</button>
        </form>
    </div>
</body>
</html>
"""

SAML_POST_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>SAML Response</title>
</head>
<body onload="document.forms[0].submit()">
    <form method="POST" action="{{ acs_url }}">
        <input type="hidden" name="SAMLResponse" value="{{ saml_response }}">
        {% if relay_state %}
        <input type="hidden" name="RelayState" value="{{ relay_state }}">
        {% endif %}
        <noscript>
            <button type="submit">Continue</button>
        </noscript>
    </form>
</body>
</html>
"""


@app.route('/')
def index():
    """Landing page"""
    return """
    <html>
    <head>
        <title>Device Posture Provider</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                padding: 40px;
                max-width: 600px;
            }
            h1 { color: #333; }
            .info { background: #f0f7ff; padding: 20px; border-radius: 5px; margin: 20px 0; }
            a { color: #667eea; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .endpoint {
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Okta Device Posture Provider</h1>
            <p>A SAML 2.0 Identity Provider with Okta Device Posture Extensions</p>

            <div class="info">
                <h3>Available Endpoints:</h3>
                <div class="endpoint">
                    <strong>SSO Endpoint:</strong><br>
                    <a href="/saml/sso">/saml/sso</a> (POST)
                </div>
                <div class="endpoint">
                    <strong>Metadata:</strong><br>
                    <a href="/saml/metadata">/saml/metadata</a>
                </div>
                <div class="endpoint">
                    <strong>Device Registration:</strong><br>
                    <a href="/admin/devices">/admin/devices</a>
                </div>
                <div class="endpoint">
                    <strong>Health Check:</strong><br>
                    <a href="/health">/health</a>
                </div>
            </div>

            <h3>Status</h3>
            <p>✅ Service is running</p>
            <p>Entity ID: <code>""" + config.get('saml.entity_id') + """</code></p>
        </div>
    </body>
    </html>
    """


@app.route('/saml/sso', methods=['GET', 'POST'])
def sso():
    """SAML SSO endpoint - handles AuthnRequest"""
    try:
        # Get SAMLRequest
        saml_request = request.form.get('SAMLRequest') or request.args.get('SAMLRequest')
        relay_state = request.form.get('RelayState') or request.args.get('RelayState', '')

        if not saml_request:
            return "Missing SAMLRequest parameter", 400

        # Parse SAML request
        request_data = saml_handler.parse_authn_request(saml_request)

        # If this is initial request, show login form
        if request.method == 'GET' or not request.form.get('device_id'):
            return render_template_string(
                LOGIN_TEMPLATE,
                saml_request=saml_request,
                relay_state=relay_state,
                action='/saml/sso',
                issuer=request_data.get('issuer', 'Unknown'),
                subject=request_data.get('subject'),
                device_posture_requested=request_data.get('device_posture_requested', False),
                error=None
            )

        # Process authentication with device posture
        device_id = request.form.get('device_id')
        vendor = request.form.get('vendor')
        model = request.form.get('model')
        os = request.form.get('os')
        os_version = request.form.get('os_version')
        user_id = request_data.get('subject') or 'user@example.com'

        # Check device posture
        device_posture = device_checker.check_device_posture(
            device_id, vendor, model, os, os_version, user_id
        )

        # Validate posture against requirements
        is_valid, error_message = device_checker.validate_posture(device_posture)

        if not is_valid:
            # Show error on login form
            return render_template_string(
                LOGIN_TEMPLATE,
                saml_request=saml_request,
                relay_state=relay_state,
                action='/saml/sso',
                issuer=request_data.get('issuer', 'Unknown'),
                subject=request_data.get('subject'),
                device_posture_requested=request_data.get('device_posture_requested', False),
                error=error_message
            ), 403

        # Create SAML response
        saml_response = saml_handler.create_authn_response(
            request_data, device_posture, is_success=True
        )

        # Return SAML response via POST form
        return render_template_string(
            SAML_POST_FORM,
            acs_url=request_data['acs_url'],
            saml_response=saml_response,
            relay_state=relay_state
        )

    except Exception as e:
        logger.error(f"SSO error: {e}", exc_info=True)
        return f"Authentication failed: {str(e)}", 500


@app.route('/saml/metadata')
def metadata():
    """SAML metadata endpoint"""
    try:
        metadata_xml = saml_handler.get_metadata()
        response = make_response(metadata_xml)
        response.headers['Content-Type'] = 'application/xml'
        return response
    except Exception as e:
        logger.error(f"Metadata error: {e}")
        return f"Failed to generate metadata: {str(e)}", 500


@app.route('/admin/devices', methods=['GET', 'POST'])
def admin_devices():
    """Device registration admin interface"""
    if request.method == 'POST':
        device_id = request.form.get('device_id')
        device_info = {
            'managed': request.form.get('managed') == 'true',
            'encrypted': request.form.get('encrypted') == 'true',
            'last_sync': request.form.get('last_sync', '')
        }
        device_checker.register_device(device_id, device_info)
        message = f"Device {device_id} registered successfully"
    else:
        message = None

    # List registered devices
    devices_html = ""
    for dev_id, dev_info in device_checker.device_registry.items():
        devices_html += f"""
        <tr>
            <td>{dev_id}</td>
            <td>{'✅' if dev_info.get('managed') else '❌'}</td>
            <td>{'✅' if dev_info.get('encrypted') else '❌'}</td>
            <td>{dev_info.get('last_sync', 'N/A')}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>Device Management</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background: #667eea; color: white; }}
            input, select {{ padding: 8px; margin: 5px; }}
            button {{ padding: 10px 20px; background: #667eea; color: white; border: none; cursor: pointer; }}
            .success {{ background: #dff0d8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>Device Management</h1>

        {'<div class="success">' + message + '</div>' if message else ''}

        <h2>Register New Device</h2>
        <form method="POST">
            <input type="text" name="device_id" placeholder="Device ID" required>
            <select name="managed">
                <option value="true">Managed</option>
                <option value="false">Not Managed</option>
            </select>
            <select name="encrypted">
                <option value="true">Encrypted</option>
                <option value="false">Not Encrypted</option>
            </select>
            <input type="datetime-local" name="last_sync">
            <button type="submit">Register Device</button>
        </form>

        <h2>Registered Devices</h2>
        <table>
            <tr>
                <th>Device ID</th>
                <th>Managed</th>
                <th>Encrypted</th>
                <th>Last Sync</th>
            </tr>
            {devices_html if devices_html else '<tr><td colspan="4">No devices registered</td></tr>'}
        </table>

        <br>
        <a href="/">← Back to Home</a>
    </body>
    </html>
    """


@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'Okta Device Posture Provider',
        'version': '1.0.0',
        'saml_ready': saml_handler.cert is not None
    }


if __name__ == '__main__':
    logger.info("Starting Okta Device Posture Provider...")
    logger.info(f"Entity ID: {config.get('saml.entity_id')}")
    logger.info(f"SSO URL: {config.get('saml.sso_url')}")

    # Check for certificates
    if not saml_handler.cert or not saml_handler.key:
        logger.warning("⚠️  SAML certificates not found. SAML responses will NOT be signed.")
        logger.warning("    Generate certificates using: python generate_certs.py")

    app.run(
        host=config.get('server.host', '0.0.0.0'),
        port=config.get('server.port', 8443),
        debug=config.get('server.debug', True)
    )
