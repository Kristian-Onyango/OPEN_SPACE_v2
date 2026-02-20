"""
========================================================
Layer 2 — Local Name Resolution Protocol (.mtd)
========================================================

PURPOSE
-------
Layer 2 provides a DNS-like resolution mechanism for the
local mesh network.

It resolves human-readable `.mtd` names into concrete
network endpoints (devices or services).

This layer is:
- READ-ONLY
- SIDE EFFECT FREE
- CACHED
- DETERMINISTIC

Layer 2 NEVER:
- Registers devices or services
- Modifies the network table
- Decides routing or load balancing
- Performs health checks

Those responsibilities belong to other layers.

--------------------------------------------------------
Resolution Outcomes (STRICT CONTRACT)
--------------------------------------------------------
Layer 2 ONLY returns one of:

- OK        → Valid resolution
- NX        → Name does not exist
- CONFLICT  → Ambiguous resolution

No other states are allowed.

--------------------------------------------------------
Used By
--------------------------------------------------------
- Layer 3 (Service Protocol)
- Layer 4 (Messaging / Routing)

========================================================
"""

import time
import threading
from typing import Optional, Dict, Any, List
from service_registry import service_resolver  # NEW: Import service registry resolver

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

MTD_SUFFIX = ".mtd"
SERVICE_PREFIX = "svc."
CACHE_TTL = 30  # seconds

# -------------------------------------------------------
# Resolution Cache
# -------------------------------------------------------

class ResolutionCache:
    """
    Thread-safe in-memory cache for Layer 2 resolution results.

    Cache behavior:
    - Stores full resolution records
    - Automatically evicts stale entries
    - Stale == cache miss (never returned to caller)
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached resolution record.

        Returns:
            - record dict if valid
            - None if missing or stale
        """
        with self._lock:
            record = self._cache.get(key)
            if not record:
                return None

            if time.time() - record["cached_at"] > record["ttl"]:
                # Stale record → remove and treat as miss
                del self._cache[key]
                return None

            return record

    def set(self, key: str, record: Dict[str, Any]) -> None:
        """
        Store a resolution record in cache.
        """
        with self._lock:
            self._cache[key] = record


# -------------------------------------------------------
# Layer 2 Resolver
# -------------------------------------------------------

class Layer2Resolver:
    """
    Layer 2 Resolver (.mtd)

    Responsibilities:
    - Validate names
    - Resolve devices
    - Resolve services
    - Cache results

    Non-responsibilities:
    - Registration
    - Conflict resolution
    - Load balancing
    - Health scoring
    """

    def __init__(self, network_table):
        """
        Args:
            network_table:
                Read-only view of known devices.
                Expected structure: dict keyed by device_id
        """
        self.network_table = network_table
        self.cache = ResolutionCache()

    # ---------------------------------------------------
    # Public API
    # ---------------------------------------------------

    def resolve(self, name: str) -> Dict[str, Any]:
        """
        Resolve a `.mtd` name.

        This is the ONLY entry point exposed to other layers.

        Returns:
            Resolution record dict (OK / NX / CONFLICT)
        """
        key = name.lower().strip()

        cached = self.cache.get(key)
        if cached:
            return cached

        record = self._resolve_and_cache(key)
        return record

    # ---------------------------------------------------
    # Internal Resolution Logic
    # ---------------------------------------------------

    def _resolve_and_cache(self, name: str) -> Dict[str, Any]:
        """
        Perform resolution and store result in cache.
        """

        # Validate suffix
        if not name.endswith(MTD_SUFFIX):
            record = self._nx_record(name)
            self.cache.set(name, record)
            return record

        # Service resolution
        if name.startswith(SERVICE_PREFIX):
            record = self._resolve_service(name)
            self.cache.set(name, record)
            return record

        # Device resolution
        record = self._resolve_device(name)
        self.cache.set(name, record)
        return record

    # ---------------------------------------------------
    # Device Resolution
    # ---------------------------------------------------

    def _resolve_device(self, name: str) -> Dict[str, Any]:
        """
        Resolve a device name.

        Example:
            laptop.mtd → device record
        """
        hostname = name.replace(MTD_SUFFIX, "")

        matches = []
        for device_id, info in self.network_table.items():
            # Match by device name and require alive status
            if info.get("name") == hostname and info.get("status") == "alive":
                matches.append({
                    "device_id": device_id,
                    "name": info.get("name"),
                    "ip": info["ip"],
                    "port": 51000,  # Standard messaging port from message.py
                    "role": info.get("role"),
                    "role_trusted": info.get("role_trusted", False),
                    "health": info.get("health", 1.0)
                })

        if not matches:
            return self._nx_record(name)

        if len(matches) > 1:
            return self._conflict_record(name, "device", matches)

        return self._ok_record(name, "device", matches)

    # ---------------------------------------------------
    # Service Resolution (UPDATED TO USE LAYER 3)
    # ---------------------------------------------------

    def _resolve_service(self, name: str) -> Dict[str, Any]:
        """
        Resolve a service name using Layer 3 service registry.

        Example:
            svc.chat.mtd → service providers
        """
        service = (
            name
            .replace(SERVICE_PREFIX, "")
            .replace(MTD_SUFFIX, "")
        )

        # Use Layer 3 service registry instead of network_table
        providers = service_resolver.resolve_service(service)

        if not providers:
            return self._nx_record(name)

        # Format providers for Layer 2 response
        formatted_providers = []
        for provider in providers:
            formatted_providers.append({
                "device_id": provider["device_id"],
                "name": provider["name"],
                "ip": provider["ip"],
                "port": provider["port"],  # Use service port from registry
                "role": provider["role"],
                "role_trusted": provider["role_trusted"],
                "health": provider["health"],
                "service_metadata": provider.get("service_metadata", {})
            })

        # Multiple providers are VALID
        # Selection is delegated to Layer 4
        return self._ok_record(name, "service", formatted_providers)

    # ---------------------------------------------------
    # Record Builders (STATIC)
    # ---------------------------------------------------

    @staticmethod
    def _ok_record(
        name: str,
        rtype: str,
        records: List[dict]
    ) -> Dict[str, Any]:
        """
        Successful resolution record.
        """
        return {
            "status": "OK",
            "type": rtype,
            "name": name,
            "records": records,
            "ttl": CACHE_TTL,
            "cached_at": time.time()
        }

    @staticmethod
    def _nx_record(name: str) -> Dict[str, Any]:
        """
        Name does not exist.
        """
        return {
            "status": "NX",
            "type": None,
            "name": name,
            "records": [],
            "ttl": CACHE_TTL,
            "cached_at": time.time()
        }

    @staticmethod
    def _conflict_record(
        name: str,
        rtype: str,
        records: List[dict]
    ) -> Dict[str, Any]:
        """
        Ambiguous resolution.
        """
        return {
            "status": "CONFLICT",
            "type": rtype,
            "name": name,
            "records": records,
            "ttl": CACHE_TTL,
            "cached_at": time.time()
        }