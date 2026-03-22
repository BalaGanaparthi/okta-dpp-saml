"""
Configuration management for Device Posture Provider
"""
import os
import yaml
from pathlib import Path


class Config:
    """Configuration class for DPP"""

    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return self._default_config()

    def _default_config(self):
        """Default configuration with environment variable support"""
        return {
            'server': {
                'host': os.getenv('HOST', '0.0.0.0'),
                'port': int(os.getenv('PORT', '8443')),
                'debug': os.getenv('FLASK_ENV', 'development') != 'production'
            },
            'saml': {
                'entity_id': os.getenv('SAML_ENTITY_ID', 'https://dpp.example.com'),
                'sso_url': os.getenv('SAML_SSO_URL', 'https://dpp.example.com/saml/sso'),
                'acs_url': os.getenv('SAML_ACS_URL', 'https://dpp.example.com/saml/acs'),
                'cert_file': 'certs/saml.crt',
                'key_file': 'certs/saml.key',
                'name_id_format': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
                'valid_hours': 1
            },
            'okta': {
                'namespace': 'urn:okta:saml:2.0:DevicePosture',
                'entity_id': os.getenv('OKTA_ENTITY_ID', 'http://www.okta.com/<your-okta-id>'),
                'acs_url': os.getenv('OKTA_ACS_URL', 'https://<your-okta-domain>/sso/saml2/<app-id>')
            },
            'device_checks': {
                'require_managed': os.getenv('REQUIRE_MANAGED', 'true').lower() == 'true',
                'require_compliant': os.getenv('REQUIRE_COMPLIANT', 'false').lower() == 'true',
                'require_encrypted': os.getenv('REQUIRE_ENCRYPTED', 'false').lower() == 'true',
                'allowed_os': ['Windows', 'macOS', 'iOS', 'Android', 'Linux'],
                'min_os_versions': {
                    'Windows': '10.0',
                    'macOS': '12.0',
                    'iOS': '15.0',
                    'Android': '11.0'
                }
            }
        }

    def get(self, key, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
