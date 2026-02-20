"""
========================================================
Layer 5 — Unified Storage Facade
========================================================

Purpose:
--------
Single API for ALL persistence needs across all layers.
Uses existing Layer 5 modules as backend.
Maintains JSON as backup/fallback.

Design Principles:
1. Minimal changes to layers 1-4
2. JSON remains as backup
3. Integration.py handles initialization
4. Layers remain isolated (only call storage API)
========================================================
"""

import time
from typing import Dict, Any, Optional
from storage_protocol_core import StorageEngine, RecordNotFound
from storage_network_runtime import NetworkSnapshotStore
from storage_devices import DeviceRegistry

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

# Retention policies
SNAPSHOT_RETENTION_DAYS = 7
MAX_SNAPSHOTS = 50


# -------------------------------------------------------
# Storage Facade
# -------------------------------------------------------

class StorageFacade:
    """
    Unified storage API for all layers.
    Abstracts all Layer 5 modules behind simple interface.
    """

    def __init__(self):
        """Initialize all storage subsystems."""
        self.storage = StorageEngine()
        self.network_store = NetworkSnapshotStore(self.storage)
        self.device_registry = DeviceRegistry(self.storage)
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize storage system."""
        if self.initialized:
            return True

        try:
            # Load any existing state
            print("[STORAGE] Initializing Layer 5 storage facade")
            self.initialized = True
            return True
        except Exception as e:
            print(f"[STORAGE] Initialization failed: {e}")
            return False

    # ---------------------------------------------------
    # Network State (Layer 1)
    # ---------------------------------------------------

    def save_network_state(self, network_table: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save network table state.
        Called by Layer 1 (network_table.py).

        Returns:
            {"status": "success/error", "method": "layer5/json"}
        """
        try:
            # Save to Layer 5
            self.network_store.save_snapshot(network_table)

            # Also update device registry
            for device_id, info in network_table.items():
                if info.get("status") == "alive":
                    self._update_device_record(device_id, info)

            return {"status": "success", "method": "layer5"}
        except Exception as e:
            print(f"[STORAGE] Layer 5 save failed, using JSON fallback: {e}")
            return {"status": "fallback", "method": "json", "error": str(e)}

    def load_network_state(self) -> Optional[Dict[str, Any]]:
        """
        Load network state.
        Called during system startup.

        Returns:
            Network table or None
        """
        try:
            if self.network_store.snapshot_exists():
                snapshot = self.network_store.load_latest_snapshot()
                return snapshot.get("network_table")
        except RecordNotFound:
            pass
        except Exception as e:
            print(f"[STORAGE] Layer 5 load failed: {e}")

        return None  # Signal to use JSON fallback

    def _update_device_record(self, device_id: str, info: Dict[str, Any]) -> None:
        """Internal: Update device registry."""
        try:
            if not self.device_registry.device_exists(device_id):
                self.device_registry.register_device(device_id, {
                    "first_seen": time.time(),
                    "roles": [info.get("role", "unknown")],
                    "metadata": {
                        "name": info.get("name"),
                        "ip": info.get("ip"),
                        "services": info.get("services", [])
                    }
                })
        except Exception as e:
            print(f"[STORAGE] Device registry update failed: {e}")

    # ---------------------------------------------------
    # Service Registry (Layer 3)
    # ---------------------------------------------------

    def save_service_state(self, service_registry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save service registry state.
        Called by Layer 3 (service_registry.py).
        """
        # Currently just passes through - service_registry.py handles its own JSON
        # This is a placeholder for future Layer 5 integration
        return {"status": "success", "method": "json"}

    def load_service_state(self) -> Dict[str, Any]:
        """
        Load service registry state.
        """
        # Placeholder - returns empty dict to use JSON fallback
        return {}

    # ---------------------------------------------------
    # Message State (Layer 4)
    # ---------------------------------------------------

    def save_message_state(self, pending_acks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save pending ACKs state.
        Called by Layer 4 (message.py).
        """
        # Currently just passes through - message.py handles its own JSON
        return {"status": "success", "method": "json"}

    def load_message_state(self) -> Dict[str, Any]:
        """
        Load pending ACKs state.
        """
        # Placeholder - returns empty dict to use JSON fallback
        return {}

    # ---------------------------------------------------
    # System Snapshots
    # ---------------------------------------------------

    def create_system_snapshot(self, reason: str) -> Dict[str, Any]:
        """
        Create comprehensive system snapshot.
        Called by integration layer periodically.
        """
        try:
            # Import here to avoid circular imports
            from storage_system_state_snapshot import create_snapshot
            snapshot = create_snapshot(self.storage)
            return {"status": "success", "snapshot": snapshot}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        """
        try:
            total_records = 0
            collections = {}

            for collection, records in self.storage._store.items():
                count = sum(len(versions) for versions in records.values())
                collections[collection] = count
                total_records += count

            return {
                "status": "success",
                "total_records": total_records,
                "collections": collections,
                "initialized": self.initialized
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# -------------------------------------------------------
# Global Instance
# -------------------------------------------------------

# Global storage instance
storage = StorageFacade()


# Convenience functions
def initialize_storage() -> bool:
    """Initialize storage system."""
    return storage.initialize()


def save_network_state(network_table: Dict[str, Any]) -> Dict[str, Any]:
    """Save network state."""
    return storage.save_network_state(network_table)


def load_network_state() -> Optional[Dict[str, Any]]:
    """Load network state."""
    return storage.load_network_state()


def get_storage_stats() -> Dict[str, Any]:
    """Get storage statistics."""
    return storage.get_storage_stats()


# -------------------------------------------------------
# Exports
# -------------------------------------------------------

__all__ = [
    'StorageFacade',
    'storage',
    'initialize_storage',
    'save_network_state',
    'load_network_state',
    'get_storage_stats'
]