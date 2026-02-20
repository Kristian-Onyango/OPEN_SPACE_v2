import time
from typing import Dict, Any
from storage_protocol_core import StorageEngine, RecordNotFound, VersionConflict

# -------------------------------------------------------------------
# Extension 3: Persistent Service Registry
# -------------------------------------------------------------------

SERVICE_COLLECTION = "services"

class ServiceRegistry:
    """
    Authoritative, persistent service registry on top of Layer 5 StorageEngine.
    """

    def __init__(self, storage_engine: StorageEngine):
        self.storage = storage_engine

    # -------------------------
    # Service Registration
    # -------------------------

    def register_service(self, device_id: str, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new service for a device.
        service_info must contain at least:
            - service_id (str)
            - description (str, optional)
        """
        record_id = device_id

        try:
            # Get current record (may not exist)
            record = self.storage.get(SERVICE_COLLECTION, record_id)
            services = record["payload"].get("services", [])
        except RecordNotFound:
            services = []

        # Check for existing service
        service_id = service_info["service_id"]
        existing = [s for s in services if s["service_id"] == service_id]

        if existing:
            # Already registered; optionally update description/timestamp
            existing[0].update({
                "description": service_info.get("description", existing[0].get("description")),
                "updated_at": time.time()
            })
        else:
            # Add new service
            services.append({
                "service_id": service_id,
                "description": service_info.get("description", ""),
                "registered_at": time.time()
            })

        # Persist back (optimistic locking)
        payload = {"services": services}
        try:
            updated_record = self.storage.put(
                SERVICE_COLLECTION,
                record_id,
                payload,
                expected_version=record["version"] if 'record' in locals() else None
            )
        except VersionConflict as e:
            # Retry once (could implement more robust retry policy)
            record = self.storage.get(SERVICE_COLLECTION, record_id)
            payload = {"services": services}
            updated_record = self.storage.put(
                SERVICE_COLLECTION,
                record_id,
                payload,
                expected_version=record["version"]
            )

        return updated_record

    # -------------------------
    # Service Deregistration
    # -------------------------

    def deregister_service(self, device_id: str, service_id: str) -> None:
        """
        Remove a service from a device record.
        """
        record = self.storage.get(SERVICE_COLLECTION, device_id)
        services = record["payload"].get("services", [])

        new_services = [s for s in services if s["service_id"] != service_id]

        payload = {"services": new_services}
        self.storage.put(
            SERVICE_COLLECTION,
            device_id,
            payload,
            expected_version=record["version"]
        )

    # -------------------------
    # Queries
    # -------------------------

    def get_device_services(self, device_id: str) -> list:
        """
        Return all services registered by a device.
        """
        try:
            record = self.storage.get(SERVICE_COLLECTION, device_id)
            return record["payload"].get("services", [])
        except RecordNotFound:
            return []

    def find_service(self, service_id: str) -> list:
        """
        Search across all devices for a given service.
        Returns list of dicts: {device_id, service_info}
        """
        results = []
        for collection in [SERVICE_COLLECTION]:
            if collection not in self.storage._store:
                continue
            for device_id, versions in self.storage._store[collection].items():
                latest_version = max(versions.keys())
                record = versions[latest_version]
                for s in record["payload"].get("services", []):
                    if s["service_id"] == service_id:
                        results.append({
                            "device_id": device_id,
                            "service_info": s
                        })
        return results
