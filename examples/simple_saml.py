"""
Simple SAML Response Generator using string template
"""
import base64
import uuid
from datetime import datetime, timedelta
from signxml import XMLSigner, methods
from lxml import etree

from src.logger_config import get_logger, log_saml_event, log_error

logger = get_logger(__name__)

SAML_RESPONSE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                Destination="{acs_url}"
                ID="{response_id}"
                InResponseTo="{request_id}"
                IssueInstant="{issue_instant}"
                Version="2.0">
    <saml:Issuer>{entity_id}</saml:Issuer>
    <samlp:Status>
        <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </samlp:Status>
    <saml:Assertion ID="{assertion_id}"
                    IssueInstant="{issue_instant}"
                    Version="2.0">
        <saml:Issuer>{entity_id}</saml:Issuer>
        <saml:Subject>
            <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{user_email}</saml:NameID>
            <saml:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
                <saml:SubjectConfirmationData InResponseTo="{request_id}"
                                              NotOnOrAfter="{not_on_or_after}"
                                              Recipient="{acs_url}"/>
            </saml:SubjectConfirmation>
        </saml:Subject>
        <saml:Conditions NotBefore="{not_before}" NotOnOrAfter="{not_on_or_after}">
            <saml:AudienceRestriction>
                <saml:Audience>{audience}</saml:Audience>
            </saml:AudienceRestriction>
        </saml:Conditions>
        <saml:AuthnStatement AuthnInstant="{issue_instant}" SessionIndex="{assertion_id}">
            <saml:AuthnContext>
                <saml:AuthnContextClassRef>urn:okta:saml:2.0:DevicePosture</saml:AuthnContextClassRef>
                <saml:AuthnContextDecl>
                    <AuthenticationContextDeclaration xmlns="urn:okta:saml:2.0:DevicePosture">
                        <Extension>
                            <Device xmlns="urn:okta:saml:2.0:DevicePosture"
                                    ID="{device_id}"
                                    Vendor="TestDPP"
                                    Model="Simulator"
                                    OS="TestOS"
                                    OSVersion="1.0">
                                <Posture>
                                    <Fact Name="IsManaged" Value="{is_managed}"/>
                                    <Fact Name="IsCompliant" Value="{is_compliant}"/>
                                </Posture>
                            </Device>
                        </Extension>
                    </AuthenticationContextDeclaration>
                </saml:AuthnContextDecl>
            </saml:AuthnContext>
        </saml:AuthnStatement>
    </saml:Assertion>
</samlp:Response>"""


def create_saml_response_simple(entity_id, acs_url, request_id, audience, user_email,
                                is_managed, is_compliant, cert, key):
    """Create SAML Response using template"""

    now = datetime.utcnow()
    response_id = f"_{uuid.uuid4().hex}"
    assertion_id = f"_{uuid.uuid4().hex}"
    device_id = f"TEST-{uuid.uuid4().hex[:12].upper()}"

    # Format timestamps
    issue_instant = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    not_before = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    not_on_or_after = (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

    # Fill template
    response_xml = SAML_RESPONSE_TEMPLATE.format(
        response_id=response_id,
        assertion_id=assertion_id,
        device_id=device_id,
        entity_id=entity_id,
        acs_url=acs_url,
        request_id=request_id,
        audience=audience,
        user_email=user_email,
        issue_instant=issue_instant,
        not_before=not_before,
        not_on_or_after=not_on_or_after,
        is_managed=str(is_managed).lower(),
        is_compliant=str(is_compliant).lower()
    )

    # Parse to sign
    response_elem = etree.fromstring(response_xml.encode('utf-8'))

    # Sign the ASSERTION (not the Response) for Okta compatibility
    if cert and key:
        # Find the Assertion element
        ns = {'saml': 'urn:oasis:names:tc:SAML:2.0:assertion'}
        assertion_elem = response_elem.find('.//saml:Assertion', namespaces=ns)

        if assertion_elem is not None:
            # Sign the Assertion
            # signer = XMLSigner(
            #     method=methods.enveloped,
            #     signature_algorithm='rsa-sha256',
            #     digest_algorithm='sha256'
            # )

            logger.info("Signing XML with RSA-SHA256 \w assertion_id = {assertion_id}" )
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
                c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"
            )

            # Sign and get the signed assertion
            # signed_assertion = signer.sign(assertion_elem, key=key, cert=cert,reference_uri=f"#{assertion_id}")

            signed_assertion = signer.sign(
                assertion_elem,
                key=key.encode('utf-8'),
                cert=cert.encode('utf-8'),
                reference_uri=f"#{assertion_id}"
            )

            # Replace the unsigned assertion with the signed one
            parent = assertion_elem.getparent()
            parent.replace(assertion_elem, signed_assertion)

        response_xml = etree.tostring(response_elem, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    else:
        response_xml = response_xml.encode('utf-8')

    # Base64 encode
    return base64.b64encode(response_xml).decode('utf-8'), response_xml.decode('utf-8')
