"""
========================================================
System Integration Layer
========================================================

Purpose:
--------
Acts as the "brain" the system.
- Initializes all system layers
- Starts all background threads
- Provides unified API for messaging, resolution, and network info
- Handles graceful startup/shutdown

========================================================
"""

import time
import threading
from typing import Dict, Any, Optional

# Import all system components needed for integration
from network_table import network_table
from discovery import announce_loop, listen_loop
from message import listener_loop, ack_checker_loop, persistence_loop, NODE_ID, NODE_NAME, DECLARED_ROLE, send_to_node
from service_registry import register_services_from_discovery, get_service_info as _get_service_info, get_all_services

# -------------------------------------------------------
# System Integrator
# -------------------------------------------------------

class SystemIntegrator:
    """
    Main integration class that connects all layers and starts all background threads.
    """

    def __init__(self):
        self.running = False
        self.resolver = None
        self.startup_time = time.time()

    def start(self):
        """
        Initialize system layers and start all background threads.
        """
        if self.running:
            print("[INTEGRATION] System already running")
            return

        print("[INTEGRATION] Starting system integration...")

        # Layer 5 storage initialization
        print("[INTEGRATION] Initializing Layer 5 storage...")
        from storage_layer import initialize_storage
        storage_ok = initialize_storage()
        print(f"[INTEGRATION] Layer 5 storage: {'READY' if storage_ok else 'FAILED (JSON fallback active)'}")

        # Start all background threads
        print("[INTEGRATION] Starting all background threads...")

        # Create threads list directly (FIXED: list literal)
        threads = [
            # Discovery threads
            threading.Thread(target=announce_loop, daemon=True, name="announce_loop"),
            threading.Thread(target=listen_loop, daemon=True, name="listen_loop"),

            # Message threads
            threading.Thread(target=listener_loop, daemon=True, name="listener_loop"),
            threading.Thread(target=ack_checker_loop, daemon=True, name="ack_checker_loop"),
            threading.Thread(target=persistence_loop, daemon=True, name="persistence_loop"),

            # Network table maintenance - define function inline
            threading.Thread(target=self._network_table_tasks, daemon=True, name="network_table_tasks")
        ]

        for t in threads:
            t.start()
            print(f"[INTEGRATION] Thread started: {t.name} (ID: {t.ident})")

        self.running = True
        print(f"[INTEGRATION] System is now running. Node ID: {NODE_ID}, Node Name: {NODE_NAME}, Role: {DECLARED_ROLE}")
        print(f"[INTEGRATION] Total devices in network table: {len(network_table)}")

    def _network_table_tasks(self):
        """Run network table background tasks (internal method)."""
        from network_table import state_maintenance_loop
        state_maintenance_loop()

    def stop(self):
        """
        Gracefully stop all system components.
        """
        self.running = False
        print("[INTEGRATION] System stopping...")

    # ---------------------------------------------------
    # Public API - Messaging
    # ---------------------------------------------------

    @staticmethod
    def send_message(target: str, payload: Any) -> bool:
        """
        Send a message to a target node.
        """
        try:
            send_to_node(target, payload)
            return True
        except Exception as e:
            print(f"[INTEGRATION] Failed to send message: {e}")
            return False

    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """
        Get current network information.
        """
        alive_devices = [d for d in network_table.values() if d.get("status") == "alive"]
        roles = {}
        services = {}

        for device in alive_devices:
            role = device.get("role", "unknown")
            roles[role] = roles.get(role, 0) + 1
            for svc in device.get("services", []):
                services[svc] = services.get(svc, 0) + 1

        return {
            "node_id": NODE_ID,
            "node_name": NODE_NAME,
            "role": DECLARED_ROLE,
            "total_devices": len(network_table),
            "alive_devices": len(alive_devices),
            "roles": roles,
            "services": services,
            "uptime": time.time() - integrator.startup_time
        }

    @staticmethod
    def get_device_info(device_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific device or this device.
        """
        target_id = device_id or NODE_ID
        info = network_table.get(target_id)
        if info:
            return {"device_id": target_id, **info}
        return None

    @staticmethod
    def get_service_info(service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get info about a specific service.
        """
        return _get_service_info(service_name)

    @staticmethod
    def get_all_services_info() -> Dict[str, Any]:
        """Get info about all registered services."""
        return get_all_services()

    @staticmethod
    def register_service(service_name: str, port: int = 5000, metadata: Optional[dict] = None) -> bool:
        """
        Register a new service from this device.

        Args:
            service_name: Name of the service to register
            port: Port the service runs on
            metadata: Optional service metadata (reserved for future use)
        """
        # metadata parameter is reserved for future use
        _ = metadata  # Explicitly mark as intentionally unused (FIXED)

        result = register_services_from_discovery(
            device_id=NODE_ID,
            services=[service_name],
            service_port=port,
            role=DECLARED_ROLE
        )
        success = len(result.get("accepted", [])) > 0
        if success:
            print(f"[INTEGRATION] Successfully registered service '{service_name}' on port {port}")
        else:
            print(f"[INTEGRATION] Failed to register service '{service_name}': {result.get('rejected', [])}")
        return success

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a simple health check of the system.
        """
        healthy_devices = sum(1 for d in network_table.values()
                              if d.get("status") == "alive" and d.get("health", 0) >= 0.5)
        return {
            "status": "HEALTHY" if self.running else "DEGRADED",
            "metrics": {
                "total_devices": len(network_table),
                "healthy_devices": healthy_devices,
                "uptime": time.time() - self.startup_time
            }
        }

# -------------------------------------------------------
# Global Instance
# -------------------------------------------------------

integrator = SystemIntegrator()

# -------------------------------------------------------
# Convenience Functions
# -------------------------------------------------------

def start_system():
    """Start the entire system."""
    integrator.start()

def stop_system():
    """Stop the entire system."""
    integrator.stop()

def resolve(name: str):
    """Resolve a .mtd name (not yet implemented)."""
    # 'name' parameter is intentionally unused in this placeholder
    _ = name  # Explicitly mark as unused (FIXED)
    raise NotImplementedError("Resolution not implemented yet")

def send_message(target, payload):
    """Send a message to a target node."""
    return integrator.send_message(target, payload)

def get_network_info():
    """Get current network information."""
    return integrator.get_network_info()

def get_device_info(device_id=None):
    """Get information about a specific device."""
    return integrator.get_device_info(device_id)

def get_service_info(service_name):
    """Get info about a specific service."""
    return integrator.get_service_info(service_name)

def get_all_services_info():
    """Get info about all registered services."""
    return integrator.get_all_services_info()

def register_service(service_name, port=5000, metadata=None):
    """Register a new service from this device."""
    return integrator.register_service(service_name, port, metadata)

def health_check():
    """Perform a system health check."""
    return integrator.health_check()

# -------------------------------------------------------
# Module Exports
# -------------------------------------------------------

__all__ = [
    'SystemIntegrator',
    'integrator',
    'start_system',
    'stop_system',
    'send_message',
    'get_network_info',
    'get_device_info',
    'get_service_info',
    'get_all_services_info',
    'register_service',
    'health_check',
    'register_services_from_discovery'  # ADDED: Now explicitly exported
]