"""
========================================================
Layer 3 — Service Protocol & Registry
========================================================

PURPOSE
-------
Authoritative service registration and discovery system.

This layer:
- Registers services from device announcements
- Provides service discovery queries
- Enforces role-based service policies
- Maintains persistent service state

Depends on:
- Layer 1 (network_table) for device status
- Layer 2 (resolver) for service queries

Used by:
- Layer 2 (resolver) for service resolution
- Applications for service discovery
========================================================
"""

import json
import time
import threading
import os
from typing import Dict, List, Any, Optional

# Import shared network table
from network_table import network_table, record_success, record_failure

# -----------------------------
# CONFIGURATION
# -----------------------------

PROVIDER_TTL = 30  # Providers must re-announce every 30 seconds
STATE_FILE = "service_registry.json"

# Role → allowed services policy (ENFORCEMENT)
ROLE_SERVICE_POLICY = {
    "game": ["games", "chat", "matchmaking"],
    "chat": ["chat", "messaging", "presence"],
    "cache": ["cache", "storage", "cdn"],
    "storage": ["storage", "backup", "files"],
    "unknown": []  # Unknown roles can't register services
}

# Service → default metadata
SERVICE_METADATA = {
    "games": {"protocol": "udp", "stateful": True, "version": 1},
    "chat": {"protocol": "tcp", "stateful": True, "version": 1},
    "storage": {"protocol": "tcp", "stateful": False, "version": 1},
    "cache": {"protocol": "udp", "stateful": False, "version": 1}
}

# -----------------------------
# SERVICE REGISTRY (AUTHORITATIVE)
# -----------------------------
"""
Structure:
service_name -> {
    "providers": {
        device_id: {
            "last_announce": timestamp,
            "metadata": {...},
            "health": float
        }
    },
    "metadata": {
        "protocol": str,
        "version": int,
        "stateful": bool
    },
    "policy": {
        "min_providers": int,
        "min_health": float,
        "load_balancing": "round_robin"|"health_based"
    }
}
"""
service_registry: Dict[str, Dict[str, Any]] = {}
_registry_lock = threading.Lock()


# -----------------------------
# PERSISTENCE
# -----------------------------

def save_registry():
    """Persist service registry to disk."""
    try:
        with _registry_lock:
            with open(STATE_FILE, "w") as f:
                # Only save active providers (not expired)
                clean_registry = {}
                now = time.time()

                for service, data in service_registry.items():
                    active_providers = {}
                    for device_id, provider_info in data["providers"].items():
                        if now - provider_info["last_announce"] <= PROVIDER_TTL:
                            active_providers[device_id] = provider_info

                    if active_providers:  # Only save services with active providers
                        clean_registry[service] = {
                            "providers": active_providers,
                            "metadata": data["metadata"],
                            "policy": data["policy"]
                        }

                json.dump(clean_registry, f, indent=2)
    except Exception as e:
        print(f"[SERVICE REGISTRY] Save error: {e}")


def load_registry():
    """Load service registry from disk at startup."""
    global service_registry

    if not os.path.exists(STATE_FILE):
        return

    try:
        with open(STATE_FILE, "r") as f:
            with _registry_lock:
                service_registry = json.load(f)
                # Convert timestamps
                for service_data in service_registry.values():
                    for provider_info in service_data["providers"].values():
                        provider_info["last_announce"] = float(provider_info["last_announce"])
    except Exception as e:
        print(f"[SERVICE REGISTRY] Load error: {e}")


def persistence_loop():
    """Background thread to periodically save registry."""
    while True:
        save_registry()
        time.sleep(10)  # Save every 10 seconds


# -----------------------------
# SERVICE REGISTRATION (FROM LAYER 1 DISCOVERY)
# -----------------------------

def register_services_from_discovery(device_id: str, services: List[str],
                                     service_port: int = 5000, role: str = "unknown") -> Dict[str, Any]:
    """
    Register services announced by a device via DISCOVERY_ANNOUNCE.

    Called by Layer 1 when receiving discovery announcements.

    Args:
        device_id: UUID of the announcing device
        services: List of service names offered
        service_port: Port services are available on
        role: Device's role for policy enforcement

    Returns:
        Registration result with accepted/rejected services
    """
    if not services:
        return {"accepted": [], "rejected": [], "reason": "No services provided"}

    accepted = []
    rejected = []

    with _registry_lock:
        for service in services:
            # 1. Check role-based policy
            allowed_services = ROLE_SERVICE_POLICY.get(role, [])
            if service not in allowed_services:
                rejected.append({"service": service, "reason": f"Role '{role}' not allowed to offer '{service}'"})
                continue

            # 2. Check if device exists in network table
            device_info = network_table.get(device_id)
            if not device_info:
                rejected.append({"service": service, "reason": "Device not in network table"})
                continue

            # 3. Get or create service entry
            service_entry = service_registry.setdefault(service, {
                "providers": {},
                "metadata": SERVICE_METADATA.get(service, {
                    "protocol": "tcp",
                    "stateful": False,
                    "version": 1
                }),
                "policy": {
                    "min_providers": 1,
                    "min_health": 0.3,
                    "load_balancing": "health_based"
                }
            })

            # 4. Register/update provider
            now = time.time()
            service_entry["providers"][device_id] = {
                "last_announce": now,
                "metadata": {
                    "port": service_port,
                    "ip": device_info.get("ip", "0.0.0.0"),
                    "device_name": device_info.get("name", "unknown"),
                    "role": role
                },
                "health": device_info.get("health", 1.0)
            }

            accepted.append(service)

            print(
                f"[SERVICE REG] {device_info.get('name', device_id[:8])} registered '{service}' on port {service_port}")

    return {
        "accepted": accepted,
        "rejected": rejected,
        "total_accepted": len(accepted),
        "total_rejected": len(rejected)
    }


# -----------------------------
# SERVICE QUERIES (USED BY LAYER 2 RESOLVER)
# -----------------------------

def get_service_providers(service_name: str, require_alive: bool = True,
                          min_health: float = 0.5) -> List[Dict[str, Any]]:
    """
    Get active providers for a service.

    Called by Layer 2 resolver for service resolution.

    Args:
        service_name: Service to query
        require_alive: Only return providers with alive devices
        min_health: Minimum health score required

    Returns:
        List of provider information
    """
    now = time.time()
    providers = []

    with _registry_lock:
        service_entry = service_registry.get(service_name)
        if not service_entry:
            return []

        for device_id, provider_info in service_entry["providers"].items():
            # Check if provider announcement is recent
            if now - provider_info["last_announce"] > PROVIDER_TTL:
                continue

            # Check device status in network table
            device_info = network_table.get(device_id)
            if not device_info:
                continue

            if require_alive and device_info.get("status") != "alive":
                continue

            # Check health requirements
            device_health = device_info.get("health", 0.0)
            if device_health < min_health:
                continue

            # Combine registry info with current device info
            providers.append({
                "device_id": device_id,
                "name": device_info.get("name", "unknown"),
                "ip": device_info.get("ip", "0.0.0.0"),
                "port": provider_info["metadata"].get("port", 5000),
                "role": device_info.get("role", "unknown"),
                "role_trusted": device_info.get("role_trusted", False),
                "health": device_health,
                "last_announce": provider_info["last_announce"],
                "service_metadata": service_entry["metadata"]
            })

    # Sort by health (highest first) for load balancing
    providers.sort(key=lambda x: x["health"], reverse=True)

    return providers


def get_service_info(service_name: str) -> Optional[Dict[str, Any]]:
    """
    Get complete service information.

    Args:
        service_name: Service to query

    Returns:
        Service information including metadata and active providers
    """
    with _registry_lock:
        service_entry = service_registry.get(service_name)
        if not service_entry:
            return None

        # Get current active providers
        providers = get_service_providers(service_name)

        return {
            "name": service_name,
            "metadata": service_entry["metadata"],
            "policy": service_entry["policy"],
            "providers": providers,
            "total_providers": len(providers),
            "total_registered": len(service_entry["providers"])
        }


def get_all_services() -> Dict[str, Any]:
    """
    Get information about all registered services.
    """
    with _registry_lock:
        result = {}
        for service_name in service_registry.keys():
            info = get_service_info(service_name)
            if info:
                result[service_name] = info
        return result


# -----------------------------
# SERVICE HEALTH & MAINTENANCE
# -----------------------------

def cleanup_expired_providers():
    """Remove providers that haven't re-announced."""
    while True:
        now = time.time()
        expired_count = 0

        with _registry_lock:
            for service_name, service_entry in list(service_registry.items()):
                providers = service_entry["providers"]

                # Find expired providers
                expired = [
                    device_id for device_id, info in providers.items()
                    if now - info["last_announce"] > PROVIDER_TTL
                ]

                # Remove expired
                for device_id in expired:
                    del providers[device_id]
                    expired_count += 1

                # Remove empty services
                if not providers:
                    del service_registry[service_name]

        if expired_count > 0:
            print(f"[SERVICE REG] Cleaned up {expired_count} expired providers")

        time.sleep(30)  # Run every 30 seconds


def update_provider_health(device_id: str, success: bool):
    """
    Update health score for all services provided by a device.

    Called by messaging layer when interactions succeed/fail.

    Args:
        device_id: Device to update
        success: True for success, False for failure
    """
    with _registry_lock:
        for service_entry in service_registry.values():
            if device_id in service_entry["providers"]:
                if success:
                    # Increment health (capped at 1.0)
                    current = service_entry["providers"][device_id].get("health", 1.0)
                    service_entry["providers"][device_id]["health"] = min(1.0, current + 0.05)
                else:
                    # Decrement health (floored at 0.0)
                    current = service_entry["providers"][device_id].get("health", 1.0)
                    service_entry["providers"][device_id]["health"] = max(0.0, current - 0.15)


# -----------------------------
# INTEGRATION WITH DISCOVERY (HOOKS)
# -----------------------------

def process_discovery_announcement(device_id: str, announcement_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a DISCOVERY_ANNOUNCE message.

    This should be called from discover.py when receiving announcements.

    Args:
        device_id: Sender device ID
        announcement_data: Full announcement JSON

    Returns:
        Registration results
    """
    services = announcement_data.get("services", [])
    service_port = announcement_data.get("service_port", 5000)
    role = announcement_data.get("role", "unknown")

    return register_services_from_discovery(
        device_id=device_id,
        services=services,
        service_port=service_port,
        role=role
    )


# -----------------------------
# LAYER 2 RESOLVER INTEGRATION
# -----------------------------

class ServiceResolver:
    """
    Layer 2-compatible service resolver.

    This class provides the interface that Layer 2 expects.
    """

    @staticmethod
    def resolve_service(service_name: str) -> List[Dict[str, Any]]:
        """
        Resolve a service to its providers.

        This is the function that should be called by Layer 2 resolver.
        """
        return get_service_providers(service_name, require_alive=True, min_health=0.5)

    @staticmethod
    def service_exists(service_name: str) -> bool:
        """Check if a service is registered."""
        with _registry_lock:
            return service_name in service_registry

    @staticmethod
    def get_service_metadata(service_name: str) -> Optional[Dict[str, Any]]:
        """Get service metadata."""
        with _registry_lock:
            service_entry = service_registry.get(service_name)
            return service_entry["metadata"] if service_entry else None


# -----------------------------
# INITIALIZATION & STARTUP
# -----------------------------

def initialize_service_registry():
    """Initialize and start the service registry."""
    print("[SERVICE REG] Initializing service registry...")

    # Load persisted state
    load_registry()

    # Start maintenance threads
    threading.Thread(target=cleanup_expired_providers, daemon=True).start()
    threading.Thread(target=persistence_loop, daemon=True).start()

    # Print initial state
    service_count = len(service_registry)
    total_providers = sum(len(s["providers"]) for s in service_registry.values())
    print(f"[SERVICE REG] Loaded {service_count} services with {total_providers} providers")

    return True


# -----------------------------
# PUBLIC API
# -----------------------------

# Create global instance
service_resolver = ServiceResolver()

# Export main functions
__all__ = [
    'initialize_service_registry',
    'process_discovery_announcement',
    'get_service_providers',
    'get_service_info',
    'get_all_services',
    'update_provider_health',
    'service_resolver'
]

# Auto-initialize on import
initialize_service_registry()