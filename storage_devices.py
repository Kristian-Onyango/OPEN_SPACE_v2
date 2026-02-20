"""
Layer 5 Extension — Device Registry
===================================

Purpose:
- Persist authoritative device identity
- Survive restarts
- Act as source of truth for Layer 3

Depends on:
- StorageEngine (Layer 5 core)
"""

from typing import Dict, Any
from storage_protocol_core import StorageEngine, RecordNotFound


DEVICE_COLLECTION = "devices"


class DeviceRegistry:
    """
    Authoritative device identity storage.
    """

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    # ------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------

    def register_device(self, device_id: str, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a device authoritatively.

        This should only be called the FIRST time a device is seen.
        """
        payload = {
            "device_id": device_id,
            "first_seen": info.get("first_seen"),
            "public_key": info.get("public_key"),
            "roles": info.get("roles", []),
            "metadata": info.get("metadata", {})
        }

        return self.storage.put(
            collection=DEVICE_COLLECTION,
            record_id=device_id,
            payload=payload,
            expected_version=None
        )

    # ------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------

    def get_device(self, device_id: str) -> Dict[str, Any]:
        """
        Retrieve authoritative device identity.
        """
        return self.storage.get(
            collection=DEVICE_COLLECTION,
            record_id=device_id
        )

    def device_exists(self, device_id: str) -> bool:
        """
        Check if a device is already known.
        """
        try:
            self.get_device(device_id)
            return True
        except RecordNotFound:
            return False
