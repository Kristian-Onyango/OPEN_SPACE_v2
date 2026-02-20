"""
Layer 5 — Authoritative Snapshot Extension
============================

Provides authoritative system-wide state snapshots.

Snapshots are immutable views of the latest records
across all storage collections at a single point in time.
"""

from typing import Dict, Any
import time
from storage_protocol_core import RecordNotFound

SNAPSHOT_COLLECTION = "network_snapshots"
LATEST_SNAPSHOT_ID = "latest"

def create_snapshot(storage) -> Dict[str, Any]:
    """
    Capture a snapshot of the entire authoritative state.

    This function:
    - Reads latest records from all collections
    - Freezes them into a single snapshot payload
    - Stores the snapshot using optimistic locking
    """

    snapshot_payload: Dict[str, Dict[str, Any]] = {}

    #Enumerate all collections safely via storage API
    for collection_name in storage.list_collections():
        snapshot_payload[collection_name] = storage.list_latest_records(
            collection_name
        )

    # Try to fetch existing snapshot to enforce versioning
    try:
        existing = storage.get(SNAPSHOT_COLLECTION, LATEST_SNAPSHOT_ID)
        expected_version = existing["version"]
    except RecordNotFound: # Exception:
        expected_version = None

    return storage.put(
        collection = SNAPSHOT_COLLECTION,
        record_id = LATEST_SNAPSHOT_ID,
        payload = {
            "collections": snapshot_payload,
            "captured_at": time.time()
        },
        expected_version=expected_version
    )

def load_latest_snapshot(storage) -> Dict[str, Any]:
    """
    Retrieve the most recent authoritative snapshot.

    Used by:
    - Layer 3 bootstrap
    - Recovery mechanisms
    """

    return storage.get(SNAPSHOT_COLLECTION, LATEST_SNAPSHOT_ID)