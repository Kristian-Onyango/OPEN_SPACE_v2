"""
Layer 5 — Extension 5: Snapshot Lifecycle & Retention
----------------------------------------------------

Manages:
- Snapshot history
- Active snapshot pointer
- Retention policy
- Rollback

Does NOT modify StorageEngine.
"""

import time
from typing import Dict, Any , Optional

# -------------------------------------------------------------------
# Snapshot Constants
# -------------------------------------------------------------------

SNAPSHOT_COLLECTION = "network_snapshots"
SNAPSHOT_INDEX_ID = "snapshot_index"
ACTIVE_SNAPSHOT_ID = "active"


# -------------------------------------------------------------------
# Snapshot Lifecycle Manager
# -------------------------------------------------------------------

class SnapshotLifecycleManager:
    """
    Governs authoritative snapshot lifecycle.

    This class:
    - Writes snapshots
    - Tracks snapshot history
    - Enforces retention limits
    - Enables rollback

    It does NOT decide *when* snapshots are taken.
    """

    def __init__(self, storage):
        self.storage = storage

    # ---------------------------------------------------------------
    # Snapshot Creation
    # ---------------------------------------------------------------

    def create_snapshot(
        self,
        network_state: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """
        Persist a new authoritative snapshot.

        Args:
            network_state: Validated Layer 3 network table
            reason: Human-readable explanation (audit trail)
        """
        timestamp = time.time()
        snapshot_id = f"snapshot-{int(timestamp)}"

        snapshot_payload = {
            "snapshot_id": snapshot_id,
            "created_at": timestamp,
            "reason": reason,
            "network_state": network_state
        }

        # Store snapshot
        snapshot_record = self.storage.put(
            SNAPSHOT_COLLECTION,
            snapshot_id,
            snapshot_payload
        )

        # Update snapshot index
        self._update_snapshot_index(snapshot_id)

        # Mark as active
        self._set_active_snapshot(snapshot_id)

        return snapshot_record

    # ---------------------------------------------------------------
    # Snapshot Retrieval
    # ---------------------------------------------------------------

    def get_active_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the currently active authoritative snapshot.
        """
        try:
            active = self.storage.get(
                SNAPSHOT_COLLECTION,
                ACTIVE_SNAPSHOT_ID
            )
            return self.storage.get(
                SNAPSHOT_COLLECTION,
                active["payload"]["snapshot_id"]
            )
        except Exception:
            return None

    # ---------------------------------------------------------------
    # Rollback
    # ---------------------------------------------------------------

    def rollback_to_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Promote an older snapshot to active status.
        """
        snapshot = self.storage.get(
            SNAPSHOT_COLLECTION,
            snapshot_id
        )

        self._set_active_snapshot(snapshot_id)

        return snapshot

    # ---------------------------------------------------------------
    # Retention Policy
    # ---------------------------------------------------------------

    def enforce_retention(self, max_snapshots: int) -> None:
        """
        Enforce snapshot retention policy.
        Deletes oldest snapshots beyond limit.
        """
        index = self._load_snapshot_index()
        snapshots = index["snapshots"]

        if len(snapshots) <= max_snapshots:
            return

        to_delete = snapshots[:-max_snapshots]

        for snapshot_id in to_delete:
            self.storage.delete(
                SNAPSHOT_COLLECTION,
                snapshot_id
            )

        index["snapshots"] = snapshots[-max_snapshots:]
        self._save_snapshot_index(index)

    # ---------------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------------

    def _update_snapshot_index(self, snapshot_id: str) -> None:
        """
        Append snapshot ID to index.
        """
        index = self._load_snapshot_index()
        index["snapshots"].append(snapshot_id)
        self._save_snapshot_index(index)

    def _set_active_snapshot(self, snapshot_id: str) -> None:
        """
        Update active snapshot pointer.
        """
        self.storage.put(
            SNAPSHOT_COLLECTION,
            ACTIVE_SNAPSHOT_ID,
            {"snapshot_id": snapshot_id}
        )

    def _load_snapshot_index(self) -> Dict[str, Any]:
        """
        Load or initialize snapshot index.
        """
        try:
            record = self.storage.get(
                SNAPSHOT_COLLECTION,
                SNAPSHOT_INDEX_ID
            )
            return record["payload"]
        except Exception:
            return {"snapshots": []}

    def _save_snapshot_index(self, index: Dict[str, Any]) -> None:
        """
        Persist snapshot index.
        """
        self.storage.put(
            SNAPSHOT_COLLECTION,
            SNAPSHOT_INDEX_ID,
            index
        )
