"""
Okta Device Posture Provider (DPP)
SAML 2.0 Identity Provider with Device Posture Extensions
"""
import sys
import time
from flask import Flask, request, render_template_string, redirect, make_response
from config import Config
from saml_handler import SAMLHandler
from device_checker import DeviceChecker
from logger_config import setup_logging, get_logger, log_request, log_saml_event, log_device_check, log_error

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
device_checker = DeviceChecker(config)


# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Device Posture Verification</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }

        /* Animated background particles */
        body::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: particle-animation 20s linear infinite;
            z-index: 0;
        }

        @keyframes particle-animation {
            0% { transform: translate(0, 0); }
            100% { transform: translate(-50px, -50px); }
        }

        .container {
            background: rgba(255, 255, 255, 0.98);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3), 0 0 100px rgba(102, 126, 234, 0.1);
            padding: 50px 40px;
            max-width: 600px;
            width: 100%;
            position: relative;
            z-index: 1;
            backdrop-filter: blur(10px);
            animation: slideUp 0.5s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .logo {
            font-size: 64px;
            margin-bottom: 15px;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        h1 {
            color: #2d3748;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: #718096;
            font-size: 16px;
            font-weight: 400;
        }

        .info-badge {
            background: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 35px;
            border: 2px solid rgba(102, 126, 234, 0.2);
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(102, 126, 234, 0.1);
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            color: #4a5568;
            font-weight: 600;
            font-size: 14px;
        }

        .info-value {
            color: #2d3748;
            font-weight: 500;
            font-size: 14px;
        }

        .posture-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        .posture-card {
            background: white;
            border: 3px solid #e2e8f0;
            border-radius: 16px;
            padding: 30px 20px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .posture-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 0;
        }

        .posture-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }

        .posture-card.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: scale(1.05);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }

        .posture-card.selected .icon {
            color: white;
        }

        .posture-card.selected .label,
        .posture-card.selected .description {
            color: white;
        }

        .posture-card > * {
            position: relative;
            z-index: 1;
        }

        .icon {
            font-size: 48px;
            margin-bottom: 15px;
            transition: transform 0.3s ease;
        }

        .posture-card:hover .icon {
            transform: scale(1.1);
        }

        .posture-card.selected .icon {
            transform: scale(1.15);
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
        }

        .label {
            font-size: 18px;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 8px;
        }

        .description {
            font-size: 13px;
            color: #718096;
            line-height: 1.4;
        }

        .section-title {
            font-size: 14px;
            font-weight: 700;
            color: #4a5568;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }

        .section-title::before {
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
            margin-right: 10px;
        }

        .submit-btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }

        .submit-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }

        .submit-btn:active:not(:disabled) {
            transform: translateY(0);
        }

        .submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .submit-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }

        .submit-btn:hover::before {
            width: 300px;
            height: 300px;
        }

        .submit-btn span {
            position: relative;
            z-index: 1;
        }

        .error {
            background: linear-gradient(135deg, #fee 0%, #fdd 100%);
            border-left: 4px solid #e53e3e;
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 12px;
            color: #c53030;
            animation: shake 0.5s;
            box-shadow: 0 4px 15px rgba(229, 62, 62, 0.2);
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }

        .error strong {
            display: block;
            margin-bottom: 5px;
            font-size: 16px;
        }

        .help-text {
            text-align: center;
            color: #a0aec0;
            font-size: 13px;
            margin-top: 20px;
            line-height: 1.6;
        }

        /* Responsive */
        @media (max-width: 600px) {
            .posture-grid {
                grid-template-columns: 1fr;
            }

            .container {
                padding: 35px 25px;
            }

            h1 {
                font-size: 26px;
            }
        }

        /* Selection checkmark */
        .checkmark {
            position: absolute;
            top: 15px;
            right: 15px;
            width: 30px;
            height: 30px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transform: scale(0);
            transition: all 0.3s ease;
        }

        .posture-card.selected .checkmark {
            opacity: 1;
            transform: scale(1);
        }

        .checkmark::after {
            content: '✓';
            color: #667eea;
            font-size: 18px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🛡️</div>
            <h1>Device Posture Verification</h1>
            <p class="subtitle">Confirm your device security status</p>
        </div>

        {% if error %}
        <div class="error">
            <strong>⚠️ Verification Failed</strong>
            {{ error }}
        </div>
        {% endif %}

        <div class="info-badge">
            <div class="info-row">
                <span class="info-label">Organization</span>
                <span class="info-value">{{ issuer.split('/')[-1][:20] if issuer else 'Unknown' }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">User</span>
                <span class="info-value">{{ subject or 'Not specified' }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Verification</span>
                <span class="info-value">{{ 'Required ✓' if device_posture_requested else 'Optional' }}</span>
            </div>
        </div>

        <form method="POST" action="{{ action }}" id="postureForm">
            <input type="hidden" name="SAMLRequest" value="{{ saml_request }}">
            <input type="hidden" name="RelayState" value="{{ relay_state }}">
            <input type="hidden" name="is_managed" id="isManagedInput" value="">
            <input type="hidden" name="is_compliant" id="isCompliantInput" value="">

            <div class="section-title">Device Management Status</div>
            <div class="posture-grid">
                <div class="posture-card" onclick="selectOption('managed', true)" id="managedYes">
                    <div class="checkmark"></div>
                    <div class="icon">✅</div>
                    <div class="label">Managed</div>
                    <div class="description">Device is enrolled in MDM/UEM</div>
                </div>
                <div class="posture-card" onclick="selectOption('managed', false)" id="managedNo">
                    <div class="checkmark"></div>
                    <div class="icon">❌</div>
                    <div class="label">Not Managed</div>
                    <div class="description">Device is not managed</div>
                </div>
            </div>

            <div class="section-title">Compliance Status</div>
            <div class="posture-grid">
                <div class="posture-card" onclick="selectOption('compliant', true)" id="compliantYes">
                    <div class="checkmark"></div>
                    <div class="icon">🔒</div>
                    <div class="label">Compliant</div>
                    <div class="description">Meets security requirements</div>
                </div>
                <div class="posture-card" onclick="selectOption('compliant', false)" id="compliantNo">
                    <div class="checkmark"></div>
                    <div class="icon">🔓</div>
                    <div class="label">Non-Compliant</div>
                    <div class="description">Does not meet requirements</div>
                </div>
            </div>

            <!-- Submit Section -->
            <div class="submit-section" style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #e2e8f0;">
                <div id="selectionStatus" style="text-align: center; margin-bottom: 15px; padding: 10px; background: #fff3cd; border-radius: 8px; color: #856404;">
                    ⚠️ Please select both options above to continue
                </div>
                <button type="submit" class="submit-btn" id="submitBtn" style="display: block !important; visibility: visible !important; width: 100%; padding: 18px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; font-size: 18px; font-weight: 700; cursor: pointer; opacity: 0.5;">
                    <span>🚀 Submit Device Posture</span>
                </button>
                <p class="help-text" style="text-align: center; color: #a0aec0; font-size: 13px; margin-top: 15px;">
                    Your selections will be included in the SAML response sent to the application
                </p>
            </div>
        </form>
    </div>

    <script>
        let selections = {
            managed: null,
            compliant: null
        };

        function updateSubmitButton() {
            const submitBtn = document.getElementById('submitBtn');
            const statusDiv = document.getElementById('selectionStatus');

            if (selections.managed !== null && selections.compliant !== null) {
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
                submitBtn.style.cursor = 'pointer';
                statusDiv.innerHTML = '✅ Ready to submit: Managed=' + selections.managed + ', Compliant=' + selections.compliant;
                statusDiv.style.background = '#d4edda';
                statusDiv.style.color = '#155724';
            } else {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.5';
                submitBtn.style.cursor = 'not-allowed';
                let missing = [];
                if (selections.managed === null) missing.push('Management Status');
                if (selections.compliant === null) missing.push('Compliance Status');
                statusDiv.innerHTML = '⚠️ Please select: ' + missing.join(' and ');
                statusDiv.style.background = '#fff3cd';
                statusDiv.style.color = '#856404';
            }
        }

        function selectOption(type, value) {
            selections[type] = value;

            // Update UI for managed
            if (type === 'managed') {
                document.getElementById('managedYes').classList.toggle('selected', value === true);
                document.getElementById('managedNo').classList.toggle('selected', value === false);
                document.getElementById('isManagedInput').value = value;
            }

            // Update UI for compliant
            if (type === 'compliant') {
                document.getElementById('compliantYes').classList.toggle('selected', value === true);
                document.getElementById('compliantNo').classList.toggle('selected', value === false);
                document.getElementById('isCompliantInput').value = value;
            }

            updateSubmitButton();
        }

        // Prevent form submission if not all options selected
        document.getElementById('postureForm').addEventListener('submit', function(e) {
            if (selections.managed === null || selections.compliant === null) {
                e.preventDefault();
                alert('Please select both Management Status and Compliance Status before submitting.');
            }
        });

        // Initialize button state on page load
        updateSubmitButton();
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

        # Create device posture object with user's selections
        from device_checker import DevicePosture
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

        # Create SAML response
        logger.info(f"Creating SAML response for user: {user_id}")
        saml_response = saml_handler.create_authn_response(
            request_data, device_posture, is_success=True
        )

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


@app.route('/admin/devices', methods=['GET', 'POST'])
def admin_devices():
    """Device registration admin interface"""
    start_time = time.time()

    if request.method == 'POST':
        device_id = request.form.get('device_id')
        device_info = {
            'managed': request.form.get('managed') == 'true',
            'encrypted': request.form.get('encrypted') == 'true',
            'last_sync': request.form.get('last_sync', '')
        }
        logger.info(f"Registering device: {device_id}, managed={device_info['managed']}, encrypted={device_info['encrypted']}")
        device_checker.register_device(device_id, device_info)
        message = f"Device {device_id} registered successfully"
        duration_ms = (time.time() - start_time) * 1000
        log_request(logger, 'POST', '/admin/devices', 200, duration_ms)
    else:
        message = None
        duration_ms = (time.time() - start_time) * 1000
        log_request(logger, 'GET', '/admin/devices', 200, duration_ms)

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
        logger.warning("    Generate certificates using: python generate_certs.py")

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
