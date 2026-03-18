"""
Device Posture Checker
Validates device compliance and management status
"""
from typing import Dict, List, Optional
from datetime import datetime
from logger_config import get_logger, log_device_check, log_error

logger = get_logger(__name__)


class DevicePosture:
    """Device posture information"""

    def __init__(self, device_id: str, vendor: str, model: str,
                 os: str, os_version: str, user_id: str):
        self.device_id = device_id
        self.vendor = vendor
        self.model = model
        self.os = os
        self.os_version = os_version
        self.user_id = user_id
        self.is_managed = False
        self.is_compliant = False
        self.is_encrypted = False
        self.last_check = None
        self.additional_facts = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'device_id': self.device_id,
            'vendor': self.vendor,
            'model': self.model,
            'os': self.os,
            'os_version': self.os_version,
            'user_id': self.user_id,
            'is_managed': self.is_managed,
            'is_compliant': self.is_compliant,
            'is_encrypted': self.is_encrypted,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'additional_facts': self.additional_facts
        }


class DeviceChecker:
    """Device posture verification"""

    def __init__(self, config):
        self.config = config
        self.device_registry = {}  # Simulated device database

    def register_device(self, device_id: str, device_info: Dict):
        """Register a device in the system"""
        self.device_registry[device_id] = device_info
        logger.info(
            f"📱 Device registered - ID: {device_id}, "
            f"Managed: {device_info.get('managed', False)}, "
            f"Encrypted: {device_info.get('encrypted', False)}"
        )

    def check_device_posture(self, device_id: str, vendor: str, model: str,
                            os: str, os_version: str, user_id: str) -> DevicePosture:
        """
        Check device posture and return compliance status

        Args:
            device_id: Unique device identifier
            vendor: Device vendor/manufacturer
            model: Device model
            os: Operating system name
            os_version: OS version
            user_id: User identifier

        Returns:
            DevicePosture object with compliance information
        """
        logger.info(f"🔍 Checking device posture - ID: {device_id}, User: {user_id}, OS: {os} {os_version}")

        posture = DevicePosture(device_id, vendor, model, os, os_version, user_id)
        posture.last_check = datetime.utcnow()

        # Check if device is registered (managed)
        posture.is_managed = self._check_managed(device_id)
        logger.debug(f"  ├─ Management check: {'✓ Managed' if posture.is_managed else '✗ Not Managed'}")

        # Check OS compliance
        posture.is_compliant = self._check_os_compliance(os, os_version)
        logger.debug(f"  ├─ Compliance check: {'✓ Compliant' if posture.is_compliant else '✗ Non-Compliant'}")

        # Check encryption status (simulated)
        posture.is_encrypted = self._check_encryption(device_id)
        logger.debug(f"  ├─ Encryption check: {'✓ Encrypted' if posture.is_encrypted else '✗ Not Encrypted'}")

        # Additional checks
        posture.additional_facts = self._additional_checks(device_id, os)
        logger.debug(f"  └─ Additional facts: {len(posture.additional_facts)} checks performed")

        logger.info(
            f"✅ Device check completed - {device_id}: "
            f"Managed={posture.is_managed}, "
            f"Compliant={posture.is_compliant}, "
            f"Encrypted={posture.is_encrypted}"
        )

        return posture

    def _check_managed(self, device_id: str) -> bool:
        """Check if device is managed"""
        # In production, this would query MDM/UEM system
        # For demo: check if device is in registry
        if device_id in self.device_registry:
            return self.device_registry[device_id].get('managed', False)

        # For demo purposes, consider devices with specific patterns as managed
        return device_id.startswith('MANAGED-') or device_id.startswith('MDM-')

    def _check_os_compliance(self, os: str, os_version: str) -> bool:
        """Check if OS version meets minimum requirements"""
        allowed_os = self.config.get('device_checks.allowed_os', [])

        # Check if OS is allowed
        if os not in allowed_os:
            logger.warning(f"OS {os} not in allowed list")
            return False

        # Check minimum version
        min_versions = self.config.get('device_checks.min_os_versions', {})
        if os in min_versions:
            min_version = min_versions[os]
            try:
                if self._compare_versions(os_version, min_version) < 0:
                    logger.warning(f"OS version {os_version} below minimum {min_version}")
                    return False
            except ValueError as e:
                logger.error(f"Version comparison failed: {e}")
                return False

        return True

    def _check_encryption(self, device_id: str) -> bool:
        """Check if device storage is encrypted"""
        # In production, query MDM for encryption status
        if device_id in self.device_registry:
            return self.device_registry[device_id].get('encrypted', False)

        # For demo: assume devices with certain patterns are encrypted
        return device_id.startswith('MANAGED-') or device_id.startswith('SEC-')

    def _additional_checks(self, device_id: str, os: str) -> Dict:
        """Perform additional device checks"""
        facts = {}

        # Check for jailbreak/root (simulated)
        facts['IsJailbroken'] = 'false'

        # Check for antivirus (for Windows/macOS)
        if os in ['Windows', 'macOS']:
            facts['HasAntivirus'] = 'true'

        # Check firewall status
        facts['FirewallEnabled'] = 'true'

        # Check last sync time (simulated)
        if device_id in self.device_registry:
            last_sync = self.device_registry[device_id].get('last_sync')
            if last_sync:
                facts['LastSync'] = last_sync

        # Screen lock enabled
        facts['ScreenLockEnabled'] = 'true'

        return facts

    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare version strings
        Returns: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]

        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        return 0

    def validate_posture(self, posture: DevicePosture) -> tuple[bool, Optional[str]]:
        """
        Validate if device posture meets requirements

        Returns:
            Tuple of (is_valid, error_message)
        """
        require_managed = self.config.get('device_checks.require_managed', True)
        require_compliant = self.config.get('device_checks.require_compliant', False)
        require_encrypted = self.config.get('device_checks.require_encrypted', False)

        logger.debug(
            f"Validating posture - Requirements: "
            f"Managed={require_managed}, Compliant={require_compliant}, Encrypted={require_encrypted}"
        )

        if require_managed and not posture.is_managed:
            logger.warning(f"❌ Validation failed: Device {posture.device_id} is not managed (required)")
            return False, "DEVICE_NOT_MANAGED"

        if require_compliant and not posture.is_compliant:
            logger.warning(f"❌ Validation failed: Device {posture.device_id} is not compliant (required)")
            return False, "DEVICE_NOT_COMPLIANT"

        if require_encrypted and not posture.is_encrypted:
            logger.warning(f"❌ Validation failed: Device {posture.device_id} is not encrypted (required)")
            return False, "DEVICE_NOT_ENCRYPTED"

        logger.info(f"✅ Validation passed for device {posture.device_id}")
        return True, None
