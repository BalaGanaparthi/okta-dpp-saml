"""
Okta Device Posture Provider (DPP)
SAML 2.0 Identity Provider with Device Posture Extensions

For Railway: Use gunicorn from Procfile, not Flask dev server
"""
import sys
import os
import time
import json
from flask import Flask, request, render_template_string, redirect, make_response, jsonify

# Add parent directory to path to import from examples
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.saml_handler import SAMLHandler
from src.models import DevicePosture
from src.logger_config import setup_logging, get_logger, log_request, log_saml_event, log_device_check, log_error
from examples.simple_saml import create_saml_response_simple

# Initialize logging
setup_logging('okta-dpp')
logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'change-this-to-random-secret-key'

# Load configuration
config = Config()

# Initialize handlers
saml_handler = SAMLHandler(config)


# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Device Posture Verification</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 600px;
            margin: 50px auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        h1 { color: #333; text-align: center; }
        .user-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }
        .section { margin: 30px 0; }
        .section h3 { color: #555; margin-bottom: 15px; }
        .options { display: flex; gap: 15px; justify-content: center; }
        .option {
            flex: 1;
            border: 3px solid #ddd;
            padding: 20px;
            border-radius: 10px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }
        .option:hover { border-color: #667eea; }
        .option.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .option .icon { font-size: 40px; margin-bottom: 10px; }

        #submitBtn {
            width: 100%;
            padding: 20px;
            font-size: 20px;
            font-weight: bold;
            background: #ff9800;
            color: white;
            border: 3px solid #f57c00;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 30px;
        }
        #submitBtn:disabled {
            background: #ccc;
            border-color: #999;
            cursor: not-allowed;
        }
        #status {
            text-align: center;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            font-weight: bold;
        }
        .warning {background: #fff3cd; color: #856404; }
        .ready { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Device Posture Verification</h1>

        <div class="user-info">
            <strong>User:</strong> {{ subject or 'Not specified' }}
        </div>

        <form method="POST" action="{{ action }}" id="form">
            <input type="hidden" name="SAMLRequest" value="{{ saml_request }}">
            <input type="hidden" name="RelayState" value="{{ relay_state }}">
            <input type="hidden" name="is_managed" id="managedInput">
            <input type="hidden" name="is_compliant" id="compliantInput">

            <div class="section">
                <h3>Is Device Managed?</h3>
                <div class="options">
                    <div class="option" id="managedYes" onclick="select('managed', true)">
                        <div class="icon">✅</div>
                        <div>YES</div>
                    </div>
                    <div class="option" id="managedNo" onclick="select('managed', false)">
                        <div class="icon">❌</div>
                        <div>NO</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>Is Device Compliant?</h3>
                <div class="options">
                    <div class="option" id="compliantYes" onclick="select('compliant', true)">
                        <div class="icon">🔒</div>
                        <div>YES</div>
                    </div>
                    <div class="option" id="compliantNo" onclick="select('compliant', false)">
                        <div class="icon">🔓</div>
                        <div>NO</div>
                    </div>
                </div>
            </div>

            <div id="status" class="warning">
                ⚠️ Please select both options
            </div>

            <button type="submit" id="submitBtn" disabled>
                🚀 SUBMIT DEVICE POSTURE
            </button>
        </form>
    </div>

    <script>
        let state = { managed: null, compliant: null };

        function select(type, value) {
            state[type] = value;

            // Update UI
            if (type === 'managed') {
                document.getElementById('managedYes').classList.toggle('selected', value === true);
                document.getElementById('managedNo').classList.toggle('selected', value === false);
                document.getElementById('managedInput').value = value;
            } else {
                document.getElementById('compliantYes').classList.toggle('selected', value === true);
                document.getElementById('compliantNo').classList.toggle('selected', value === false);
                document.getElementById('compliantInput').value = value;
            }

            // Update button
            const btn = document.getElementById('submitBtn');
            const status = document.getElementById('status');

            if (state.managed !== null && state.compliant !== null) {
                btn.disabled = false;
                btn.style.background = '#4caf50';
                btn.style.borderColor = '#388e3c';
                status.className = 'ready';
                status.innerHTML = '✅ Ready: Managed=' + state.managed + ', Compliant=' + state.compliant;
            } else {
                btn.disabled = true;
                btn.style.background = '#ff9800';
                btn.style.borderColor = '#f57c00';
                status.className = 'warning';
                status.innerHTML = '⚠️ Please select both options';
            }
        }
    </script>
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
                    <strong>JWKS (Public Keys):</strong><br>
                    <a href="/.well-known/jwks.json">/.well-known/jwks.json</a>
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
    start_time = time.time()
    request_id = None
    user_id = None
    issuer = None

    try:
        # Get SAMLRequest
        saml_request = request.form.get('SAMLRequest') or request.args.get('SAMLRequest')
        relay_state = request.form.get('RelayState') or request.args.get('RelayState', '')

        logger.info(f"SAML SSO request received: method={request.method}, has_relay_state={bool(relay_state)}")

        if not saml_request:
            logger.warning("Missing SAMLRequest parameter")
            return "Missing SAMLRequest parameter", 400

        # Parse SAML request
        request_data = saml_handler.parse_authn_request(saml_request)
        request_id = request_data.get('id')
        user_id = request_data.get('subject')
        issuer = request_data.get('issuer')

        log_saml_event(
            logger, 'AuthnRequest received',
            request_id=request_id,
            user=user_id,
            issuer=issuer,
            details=f"Device posture: {request_data.get('device_posture_requested', False)}"
        )

        # If this is initial request, show login form
        if request.method == 'GET' or not request.form.get('is_managed'):
            logger.info(f"Showing login form for user: {user_id or 'unknown'}")
            duration_ms = (time.time() - start_time) * 1000
            log_request(logger, request.method, '/saml/sso', 200, duration_ms)
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

        # Process authentication with device posture - accept user's selections directly
        is_managed = request.form.get('is_managed', 'false').lower() == 'true'
        is_compliant = request.form.get('is_compliant', 'false').lower() == 'true'
        user_id = request_data.get('subject') or 'user@example.com'

        logger.info(f"✅ Device posture submission accepted: user={user_id}, managed={is_managed}, compliant={is_compliant}")

        # Create device posture object with user's selections (no actual checking)
        device_posture = DevicePosture(
            device_id='user-device',
            vendor='Unknown',
            model='Unknown',
            os='Unknown',
            os_version='1.0',
            user_id=user_id
        )

        # Set the boolean values directly from user's selection (no validation)
        device_posture.is_managed = is_managed
        device_posture.is_compliant = is_compliant
        device_posture.is_encrypted = is_managed  # Assume encrypted if managed

        logger.info(f"📋 Device posture set: Managed={is_managed}, Compliant={is_compliant}, Encrypted={is_managed}")

        # Create SAML response using simple template
        logger.info(f"Creating SAML response for user: {user_id}")
        entity_id = config.get('saml.entity_id')
        saml_response_b64, saml_response_xml = create_saml_response_simple(
            entity_id=entity_id,
            acs_url=request_data['acs_url'],
            request_id=request_data['id'],
            audience=request_data['issuer'],
            user_email=user_id,
            is_managed=is_managed,
            is_compliant=is_compliant,
            cert=saml_handler.cert,
            key=saml_handler.key
        )

        # Log the SAML Response XML
        logger.info("=" * 70)
        logger.info("SAML RESPONSE XML:")
        logger.info("=" * 70)
        logger.info(saml_response_xml)
        logger.info("=" * 70)

        saml_response = saml_response_b64

        log_saml_event(
            logger, 'AuthnResponse created',
            request_id=request_id,
            user=user_id,
            issuer=issuer,
            details='SUCCESS'
        )

        duration_ms = (time.time() - start_time) * 1000
        log_request(logger, request.method, '/saml/sso', 200, duration_ms)
        logger.info(f"SAML authentication successful for {user_id} in {duration_ms:.2f}ms")

        # Return SAML response via POST form
        return render_template_string(
            SAML_POST_FORM,
            acs_url=request_data['acs_url'],
            saml_response=saml_response,
            relay_state=relay_state
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error(logger, e, f"SSO endpoint error for user={user_id}, issuer={issuer}")
        log_request(logger, request.method, '/saml/sso', 500, duration_ms)
        return f"Authentication failed: {str(e)}", 500


@app.route('/saml/metadata')
def metadata():
    """SAML metadata endpoint"""
    start_time = time.time()
    try:
        logger.debug("Generating SAML metadata")
        metadata_xml = saml_handler.get_metadata()
        response = make_response(metadata_xml)
        response.headers['Content-Type'] = 'application/xml'

        duration_ms = (time.time() - start_time) * 1000
        log_request(logger, 'GET', '/saml/metadata', 200, duration_ms)
        logger.info(f"SAML metadata served successfully")
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error(logger, e, "Metadata generation failed")
        log_request(logger, 'GET', '/saml/metadata', 500, duration_ms)
        return f"Failed to generate metadata: {str(e)}", 500


@app.route('/health')
def health():
    """Health check endpoint"""
    start_time = time.time()
    health_status = {
        'status': 'healthy',
        'service': 'Okta Device Posture Provider',
        'version': '1.0.0',
        'saml_ready': saml_handler.cert is not None
    }

    duration_ms = (time.time() - start_time) * 1000
    logger.debug(f"Health check: {health_status}")
    log_request(logger, 'GET', '/health', 200, duration_ms)

    return health_status


@app.route('/.well-known/jwks.json')
def jwks():
    """JWKS endpoint - serves the public key in JWKS format"""
    start_time = time.time()
    try:
        # Read the public key from pub.json
        pub_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'certs', 'pub.json')
        logger.debug(f"Reading JWKS from {pub_json_path}")

        with open(pub_json_path, 'r') as f:
            jwk = json.load(f)

        # JWKS format requires a "keys" array
        jwks_response = {
            "keys": [jwk]
        }

        duration_ms = (time.time() - start_time) * 1000
        log_request(logger, 'GET', '/.well-known/jwks.json', 200, duration_ms)
        logger.info(f"JWKS served successfully (kid: {jwk.get('kid', 'unknown')})")

        response = jsonify(jwks_response)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'  # Allow CORS for public key
        return response

    except FileNotFoundError:
        duration_ms = (time.time() - start_time) * 1000
        log_error(logger, FileNotFoundError(f"pub.json not found at {pub_json_path}"), "JWKS file not found")
        log_request(logger, 'GET', '/.well-known/jwks.json', 404, duration_ms)
        return jsonify({"error": "JWKS not found"}), 404

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error(logger, e, "Failed to serve JWKS")
        log_request(logger, 'GET', '/.well-known/jwks.json', 500, duration_ms)
        return jsonify({"error": "Failed to load JWKS"}), 500


# Request logging middleware
@app.before_request
def before_request():
    """Log request details before processing"""
    request.start_time = time.time()
    if request.path != '/health':  # Don't log health checks
        logger.debug(f"Incoming request: {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def after_request(response):
    """Log response details after processing"""
    if hasattr(request, 'start_time') and request.path != '/health':
        duration_ms = (time.time() - request.start_time) * 1000
        logger.debug(f"Request completed: {request.method} {request.path} - {response.status_code} ({duration_ms:.2f}ms)")
    return response


if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Starting Okta Device Posture Provider")
    logger.info("=" * 70)
    logger.info(f"Version: 1.0.0")
    logger.info(f"Entity ID: {config.get('saml.entity_id')}")
    logger.info(f"SSO URL: {config.get('saml.sso_url')}")
    logger.info(f"Host: {config.get('server.host', '0.0.0.0')}")
    logger.info(f"Port: {config.get('server.port', 8443)}")
    logger.info(f"Debug Mode: {config.get('server.debug', True)}")

    # Check for certificates
    if saml_handler.cert and saml_handler.key:
        logger.info("✅ SAML certificates loaded successfully")
    else:
        logger.warning("⚠️  SAML certificates not found. SAML responses will NOT be signed.")
        logger.warning("    Generate certificates using: python3 scripts/gen_x509v3.py")

    # Device check configuration
    logger.info(f"Device checks - Require Managed: {config.get('device_checks.require_managed')}")
    logger.info(f"Device checks - Require Compliant: {config.get('device_checks.require_compliant')}")
    logger.info(f"Device checks - Require Encrypted: {config.get('device_checks.require_encrypted')}")

    logger.info("=" * 70)
    logger.info("Server starting...")
    logger.info("=" * 70)

    try:
        app.run(
            host=config.get('server.host', '0.0.0.0'),
            port=config.get('server.port', 8443),
            debug=config.get('server.debug', True)
        )
    except Exception as e:
        log_error(logger, e, "Failed to start application")
        sys.exit(1)
