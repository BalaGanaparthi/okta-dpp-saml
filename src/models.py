"""
Data models for SAML Device Posture
"""
from typing import Dict
from datetime import datetime


class DevicePosture:
    """Device posture information - used as a data structure only"""

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
