"""
SAML 2.0 Handler with Okta Device Posture Extensions
"""
import base64
import uuid
from datetime import datetime, timedelta
from lxml import etree
from defusedxml import lxml as defused_lxml
from signxml import XMLSigner, XMLVerifier, methods
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import Optional, Dict, Tuple
from logger_config import get_logger, log_saml_event, log_error

logger = get_logger(__name__)


class SAMLHandler:
    """SAML 2.0 request and response handler with Okta extensions"""

    # SAML Namespaces
    NS = {
        'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
        'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'okta': 'urn:okta:saml:2.0:DevicePosture'
    }

    def __init__(self, config):
        self.config = config
        self.entity_id = config.get('saml.entity_id')
        self.sso_url = config.get('saml.sso_url')
        self.cert_file = config.get('saml.cert_file')
        self.key_file = config.get('saml.key_file')
        self._load_certificates()

    def _load_certificates(self):
        """Load SAML signing certificate and key"""
        try:
            logger.debug(f"Loading certificates from {self.cert_file} and {self.key_file}")
            with open(self.cert_file, 'rb') as f:
                self.cert = f.read()
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
            logger.info(f"✅ SAML certificates loaded successfully (cert: {len(self.cert)} bytes, key: {len(self.key)} bytes)")
        except FileNotFoundError as e:
            logger.warning(f"⚠️  Certificate files not found: {e}")
            logger.warning("SAML responses will NOT be signed!")
            self.cert = None
            self.key = None
        except Exception as e:
            log_error(logger, e, "Failed to load SAML certificates")
            self.cert = None
            self.key = None

    def parse_authn_request(self, saml_request: str) -> Dict:
        """
        Parse SAML AuthnRequest

        Args:
            saml_request: Base64 encoded SAML request

        Returns:
            Dictionary with parsed request data
        """
        try:
            # Decode base64
            decoded = base64.b64decode(saml_request)

            # Log the full SAML Request XML
            logger.info("=" * 80)
            logger.info("SAML REQUEST XML:")
            logger.info("=" * 80)
            try:
                logger.info(decoded.decode('utf-8'))
            except:
                logger.info(decoded)
            logger.info("=" * 80)

            # Parse XML securely using defusedxml
            root = defused_lxml.fromstring(decoded)

            # Extract request details
            request_data = {
                'id': root.get('ID'),
                'issue_instant': root.get('IssueInstant'),
                'destination': root.get('Destination'),
                'acs_url': root.get('AssertionConsumerServiceURL'),
                'issuer': None,
                'subject': None,
                'device_posture_requested': False
            }

            # Extract Issuer
            issuer_elem = root.find('.//saml:Issuer', namespaces=self.NS)
            if issuer_elem is not None:
                request_data['issuer'] = issuer_elem.text

            # Extract Subject
            subject_elem = root.find('.//saml:Subject/saml:NameID', namespaces=self.NS)
            if subject_elem is not None:
                request_data['subject'] = subject_elem.text

            # Check for Device Posture context
            authn_context = root.findall('.//samlp:RequestedAuthnContext/samlp:AuthnContextClassRef',
                                        namespaces=self.NS)
            for ctx in authn_context:
                if ctx.text == self.config.get('okta.namespace'):
                    request_data['device_posture_requested'] = True
                    logger.info("✓ Device Posture authentication requested")
                    break

            logger.info(
                f"📥 Parsed AuthnRequest - ID: {request_data['id'][:16]}..., "
                f"Issuer: {request_data['issuer'].split('/')[-1] if request_data['issuer'] and '/' in request_data['issuer'] else request_data['issuer']}, "
                f"Subject: {request_data['subject']}, "
                f"Device Posture: {request_data['device_posture_requested']}"
            )

            return request_data

        except Exception as e:
            log_error(logger, e, "Failed to parse AuthnRequest")
            raise

    def create_authn_response(self, request_data: Dict, device_posture,
                             is_success: bool = True,
                             status_message: Optional[str] = None) -> str:
        """
        Create SAML Response with Okta Device Posture extensions

        Args:
            request_data: Parsed request data
            device_posture: DevicePosture object
            is_success: Whether authentication succeeded
            status_message: Error message if authentication failed

        Returns:
            Base64 encoded SAML Response
        """
        response_id = f"_{uuid.uuid4().hex}"
        assertion_id = f"_{uuid.uuid4().hex}"
        issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        not_before = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        not_on_or_after = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Determine status code
        if is_success:
            status_code = 'urn:oasis:names:tc:SAML:2.0:status:Success'
        else:
            status_code = 'urn:oasis:names:tc:SAML:2.0:status:AuthnFailed'

        # Build SAML Response
        samlp_ns = self.NS['samlp']
        saml_ns = self.NS['saml']

        response = etree.Element(
            f'{{{samlp_ns}}}Response',
            ID=response_id,
            Version='2.0',
            IssueInstant=issue_instant,
            Destination=request_data['acs_url'],
            InResponseTo=request_data['id']
        )

        # Issuer
        issuer = etree.SubElement(response, f'{{{saml_ns}}}Issuer')
        issuer.text = self.entity_id

        # Status
        status = etree.SubElement(response, f'{{{samlp_ns}}}Status')
        status_code_elem = etree.SubElement(status, f'{{{samlp_ns}}}StatusCode',
                                           Value=status_code)
        if status_message:
            status_msg = etree.SubElement(status, f'{{{samlp_ns}}}StatusMessage')
            status_msg.text = status_message

        # Only add Assertion if authentication succeeded
        if is_success:
            assertion = etree.SubElement(response, f'{{{saml_ns}}}Assertion',
                                        ID=assertion_id,
                                        Version='2.0',
                                        IssueInstant=issue_instant)

            # Assertion Issuer
            assertion_issuer = etree.SubElement(assertion, f'{{{saml_ns}}}Issuer')
            assertion_issuer.text = self.entity_id

            # Subject
            subject = etree.SubElement(assertion, f'{{{saml_ns}}}Subject')
            name_id = etree.SubElement(subject, f'{{{saml_ns}}}NameID',
                                      Format=self.config.get('saml.name_id_format'))
            name_id.text = device_posture.user_id

            subject_confirmation = etree.SubElement(subject, f'{{{saml_ns}}}SubjectConfirmation',
                                                   Method='urn:oasis:names:tc:SAML:2.0:cm:bearer')
            subject_conf_data = etree.SubElement(subject_confirmation,
                                                f'{{{saml_ns}}}SubjectConfirmationData',
                                                InResponseTo=request_data['id'],
                                                NotOnOrAfter=not_on_or_after,
                                                Recipient=request_data['acs_url'])

            # Conditions
            conditions = etree.SubElement(assertion, f'{{{saml_ns}}}Conditions',
                                        NotBefore=not_before,
                                        NotOnOrAfter=not_on_or_after)
            audience_restriction = etree.SubElement(conditions, f'{{{saml_ns}}}AudienceRestriction')
            audience = etree.SubElement(audience_restriction, f'{{{saml_ns}}}Audience')
            audience.text = request_data['issuer']

            # AuthnStatement with Device Posture
            authn_statement = etree.SubElement(assertion, f'{{{saml_ns}}}AuthnStatement',
                                              AuthnInstant=issue_instant,
                                              SessionIndex=assertion_id)

            authn_context = etree.SubElement(authn_statement, f'{{{saml_ns}}}AuthnContext')
            authn_context_class = etree.SubElement(authn_context,
                                                  f'{{{saml_ns}}}AuthnContextClassRef')
            authn_context_class.text = self.config.get('okta.namespace')

            # AuthnContextDecl with Device Posture Extension
            authn_context_decl = etree.SubElement(authn_context,
                                                 f'{{{saml_ns}}}AuthnContextDecl')

            # Extension element for Device Posture
            extension = etree.SubElement(authn_context_decl, 'Extension')

            # Device element with Okta namespace
            device = etree.SubElement(extension, f'{{{self.NS["okta"]}}}Device')

            # Device metadata
            device_id = etree.SubElement(device, f'{{{self.NS["okta"]}}}DeviceID')
            device_id.text = device_posture.device_id

            vendor = etree.SubElement(device, f'{{{self.NS["okta"]}}}Vendor')
            vendor.text = device_posture.vendor

            model = etree.SubElement(device, f'{{{self.NS["okta"]}}}Model')
            model.text = device_posture.model

            os_elem = etree.SubElement(device, f'{{{self.NS["okta"]}}}OS')
            os_elem.text = device_posture.os

            os_version = etree.SubElement(device, f'{{{self.NS["okta"]}}}OSVersion')
            os_version.text = device_posture.os_version

            # Posture section
            posture = etree.SubElement(device, f'{{{self.NS["okta"]}}}Posture')

            # Required: IsManaged fact
            managed_fact = etree.SubElement(posture, f'{{{self.NS["okta"]}}}Fact',
                                           Name='IsManaged',
                                           Value=str(device_posture.is_managed).lower())

            # Optional: Additional facts
            compliant_fact = etree.SubElement(posture, f'{{{self.NS["okta"]}}}Fact',
                                             Name='IsCompliant',
                                             Value=str(device_posture.is_compliant).lower())

            encrypted_fact = etree.SubElement(posture, f'{{{self.NS["okta"]}}}Fact',
                                             Name='IsEncrypted',
                                             Value=str(device_posture.is_encrypted).lower())

            # Add additional custom facts
            for fact_name, fact_value in device_posture.additional_facts.items():
                custom_fact = etree.SubElement(posture, f'{{{self.NS["okta"]}}}Fact',
                                              Name=fact_name,
                                              Value=str(fact_value))

            # Attribute Statement (optional - for additional user attributes)
            attr_statement = etree.SubElement(assertion, f'{{{saml_ns}}}AttributeStatement')

            # Add email attribute
            email_attr = etree.SubElement(attr_statement, f'{{{saml_ns}}}Attribute',
                                         Name='email',
                                         NameFormat='urn:oasis:names:tc:SAML:2.0:attrname-format:basic')
            email_value = etree.SubElement(email_attr, f'{{{saml_ns}}}AttributeValue')
            email_value.text = device_posture.user_id

        # Sign the response if certificates are available
        if self.cert and self.key:
            logger.debug("Signing SAML response with X.509 certificate")
            response = self._sign_xml(response)
        else:
            logger.warning("⚠️  SAML response NOT signed (certificates not available)")

        # Convert to string and base64 encode
        response_str = etree.tostring(response, pretty_print=False, xml_declaration=True,
                                     encoding='UTF-8')

        # Log the full SAML Response XML
        logger.info("=" * 80)
        logger.info("SAML RESPONSE XML:")
        logger.info("=" * 80)
        try:
            # Pretty print for readability
            pretty_response = etree.tostring(response, pretty_print=True, xml_declaration=True,
                                           encoding='UTF-8')
            logger.info(pretty_response.decode('utf-8'))
        except:
            logger.info(response_str)
        logger.info("=" * 80)

        response_b64 = base64.b64encode(response_str).decode('utf-8')

        logger.info(
            f"📤 Created SAML Response - ID: {response_id[:16]}..., "
            f"Status: {status_code.split(':')[-1]}, "
            f"User: {device_posture.user_id if is_success else 'N/A'}, "
            f"Signed: {'Yes' if self.cert and self.key else 'No'}, "
            f"Size: {len(response_b64)} bytes"
        )

        if is_success:
            logger.info(
                f"Device Posture Facts - IsManaged: {device_posture.is_managed}, "
                f"IsCompliant: {device_posture.is_compliant}, "
                f"IsEncrypted: {device_posture.is_encrypted}"
            )

        return response_b64

    def _sign_xml(self, xml_element):
        """Sign XML element using XMLSigner"""
        try:
            logger.debug("Signing XML with RSA-SHA256")
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm='rsa-sha256',
                digest_algorithm='sha256'
            )

            signed = signer.sign(xml_element, key=self.key, cert=self.cert)
            logger.debug("✓ XML signature created successfully")
            return signed
        except Exception as e:
            log_error(logger, e, "XML signing failed")
            return xml_element

    def get_metadata(self) -> str:
        """Generate SAML metadata XML for the IdP"""
        samlp_ns = self.NS['samlp']
        saml_ns = self.NS['saml']
        ds_ns = self.NS['ds']

        metadata = etree.Element(
            f'{{{saml_ns}}}EntityDescriptor',
            entityID=self.entity_id,
            nsmap={'saml': saml_ns, 'ds': ds_ns}
        )

        idp_sso = etree.SubElement(metadata, f'{{{saml_ns}}}IDPSSODescriptor',
                                  protocolSupportEnumeration='urn:oasis:names:tc:SAML:2.0:protocol')

        # Add certificate if available
        if self.cert:
            key_descriptor = etree.SubElement(idp_sso, f'{{{saml_ns}}}KeyDescriptor',
                                            use='signing')
            key_info = etree.SubElement(key_descriptor, f'{{{ds_ns}}}KeyInfo')
            x509_data = etree.SubElement(key_info, f'{{{ds_ns}}}X509Data')
            x509_cert = etree.SubElement(x509_data, f'{{{ds_ns}}}X509Certificate')

            # Extract certificate content without headers
            cert_content = self.cert.decode('utf-8')
            cert_content = cert_content.replace('-----BEGIN CERTIFICATE-----', '')
            cert_content = cert_content.replace('-----END CERTIFICATE-----', '')
            cert_content = cert_content.replace('\n', '')
            x509_cert.text = cert_content

        # Name ID Format
        name_id_format = etree.SubElement(idp_sso, f'{{{saml_ns}}}NameIDFormat')
        name_id_format.text = self.config.get('saml.name_id_format')

        # SSO Service
        sso_service = etree.SubElement(idp_sso, f'{{{saml_ns}}}SingleSignOnService',
                                       Binding='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
                                       Location=self.sso_url)

        metadata_str = etree.tostring(metadata, pretty_print=True, xml_declaration=True,
                                     encoding='UTF-8')
        return metadata_str.decode('utf-8')
