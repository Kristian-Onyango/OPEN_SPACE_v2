"""
Layer 5 Extension — Network Snapshot Store
==========================================

Purpose:
- Persist last-known network_table
- Enable warm restart of Layer 3
- No runtime decisions

Depends on:
- StorageEngine (Layer 5 core)
"""

import time
from typing import Dict, Any
from storage_protocol_core import StorageEngine, RecordNotFound

SNAPSHOT_COLLECTION = "network_snapshots"
LATEST_SNAPSHOT_ID = "latest"

class NetworkSnapshotStore:
    """
    Versioned persistence for network state snapshots.
    """

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    # ------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------

    def save_snapshot(self, network_table: Dict[str, Any]) ->Dict[str, Any]:
        """
                Persist a snapshot of the current network state.

                Called by Layer 3:
                - periodically
                - on graceful shutdown
        """

        payload = {
            "timestamp": time.time(),
            "device_count": len(network_table),
            "network_table": network_table
        }

        return self.storage.put(
            collection=SNAPSHOT_COLLECTION,
            record_id=LATEST_SNAPSHOT_ID,
            payload=payload,
            expected_version=None
        )

    # ------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------

    def load_latest_snapshot(self) -> Dict[str, Any]:
        """
             Load the most recent network snapshot.
             Used during Layer 3 bootstrap.
        """

        return self.storage.get(
            collection=SNAPSHOT_COLLECTION,
            record_id=LATEST_SNAPSHOT_ID
        )
    def snapshot_exists(self) -> bool:
        """
        Check whether any snapshot exists.
        """
        try:
            self.load_latest_snapshot()
            return True
        except RecordNotFound:
            return False