"""
Layer 5 — Storage Protocol
==========================

Responsibilities:
- Authoritative persistence
- Versioned record storage
- Thread-safe read/write
- Optimistic concurrency control
- NO routing, NO caching, NO business logic

Used by:
- Layer 4 (coordination)
- Layer 6 (observability, auditing)

This layer is storage-engine agnostic.
"""

import threading
import time
from typing import Dict, Any, Optional


# ===================================================================
# Storage Errors (CORE, FROZEN)
# ===================================================================

class StorageError(Exception):
    """Base class for all Layer 5 storage failures."""
    pass


class RecordNotFound(StorageError):
    """Raised when an authoritative record does not exist."""
    pass


class VersionConflict(StorageError):
    """
    Raised when a write/delete is attempted against a stale version.
    Enforces optimistic concurrency control.
    """
    pass


# ===================================================================
# Storage Record Model (CORE)
# ===================================================================

def build_record(
    record_id: str,
    payload: Dict[str, Any],
    version: int
) -> Dict[str, Any]:
    """
    Construct a canonical versioned storage record.

    This is the ONLY record shape Layer 5 stores.
    """
    return {
        "id": record_id,
        "version": version,
        "payload": payload,
        "created_at": time.time()
    }


# ===================================================================
# Storage Engine (Authoritative, In-Memory Reference)
# ===================================================================

class StorageEngine:
    """
    Thread-safe authoritative storage engine.

    This is a reference in-memory implementation.
    It intentionally prioritizes correctness over performance.

    Can later be replaced by:
    - disk-backed engine
    - SQLite
    - distributed KV store
    - consensus-backed storage

    WITHOUT changing the public API.
    """

    def __init__(self):
        # Structure:
        # {
        #   collection_name: {
        #       record_id: {
        #           version_number: record
        #       }
        #   }
        # }
        self._store: Dict[str, Dict[str, Dict[int, Dict[str, Any]]]] = {}
        self._lock = threading.Lock()

    # ---------------------------------------------------------------
    # READ API
    # ---------------------------------------------------------------

    def get(
        self,
        collection: str,
        record_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve the latest version of a record.

        Raises:
            RecordNotFound
        """
        with self._lock:
            if collection not in self._store:
                raise RecordNotFound(record_id)

            versions = self._store[collection].get(record_id)
            if not versions:
                raise RecordNotFound(record_id)

            latest_version = max(versions.keys())
            return versions[latest_version]

    # ---------------------------------------------------------------
    # WRITE API
    # ---------------------------------------------------------------

    def put(
        self,
        collection: str,
        record_id: str,
        payload: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Insert or update a record using optimistic locking.

        Args:
            expected_version:
                - None → blind write (create or overwrite)
                - int  → must match current version

        Raises:
            VersionConflict
        """
        with self._lock:
            if collection not in self._store:
                self._store[collection] = {}

            records = self._store[collection].setdefault(record_id, {})
            current_version = max(records.keys()) if records else 0

            if expected_version is not None and expected_version != current_version:
                raise VersionConflict(
                    f"Expected v{expected_version}, found v{current_version}"
                )

            new_version = current_version + 1
            record = build_record(record_id, payload, new_version)
            records[new_version] = record

            return record

    # ---------------------------------------------------------------
    # DELETE API
    # ---------------------------------------------------------------

    def delete(
        self,
        collection: str,
        record_id: str,
        expected_version: Optional[int] = None
    ) -> None:
        """
        Delete a record, optionally version-checked.

        Raises:
            RecordNotFound
            VersionConflict
        """
        with self._lock:
            records = self._store.get(collection, {}).get(record_id)
            if not records:
                raise RecordNotFound(record_id)

            current_version = max(records.keys())

            if expected_version is not None and expected_version != current_version:
                raise VersionConflict(
                    f"Expected v{expected_version}, found v{current_version}"
                )

            del self._store[collection][record_id]

            # Optional cleanup: remove empty collection
            if not self._store[collection]:
                del self._store[collection]


