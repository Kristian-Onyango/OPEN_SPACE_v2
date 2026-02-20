
allowed roles.py
# -----------------------------
# ROLE POLICY (LOCAL TRUST RULES)
# -----------------------------

# Allowed roles in the system.
# Anything else will be downgraded to "unknown"

ALLOWED_ROLES = {
    "game",
    "chat",
    "cache",
    "storage",
    "unknown"
}
demo.py
"""
Demo Script - Test System Integration
=====================================

Tests that all layers work together correctly.
"""

import time
from integration import integrator, resolve, send_message, get_network_info


def test_resolution():
    """Test Layer 2 name resolution."""
    print("\n" + "=" * 60)
    print("TEST 1: Name Resolution")
    print("=" * 60)

    # Get this device's name
    from message import NODE_NAME

    # Test device resolution
    print(f"1. Resolving own device: {NODE_NAME}.mtd")
    result = resolve(f"{NODE_NAME}.mtd")
    print(f"   Result: {result['status']}")
    if result['status'] == "OK":
        print(f"   Found: {len(result['records'])} device(s)")
        for rec in result['records']:
            print(f"   - {rec['name']} at {rec['ip']}:{rec['port']}")

    # Test service resolution
    print("\n2. Resolving services: svc.games.mtd")
    result = resolve("svc.games.mtd")
    print(f"   Result: {result['status']}")
    if result['status'] == "OK":
        print(f"   Found: {len(result['records'])} provider(s)")
        for rec in result['records']:
            print(f"   - {rec['name']} at {rec['ip']}:{rec['port']}")

    # Test non-existent name
    print("\n3. Resolving non-existent: nonexistent.mtd")
    result = resolve("nonexistent.mtd")
    print(f"   Result: {result['status']} (should be NX)")

    return result['status'] == "OK"


def test_messaging():
    """Test Layer 4 messaging."""
    print("\n" + "=" * 60)
    print("TEST 2: Messaging")
    print("=" * 60)

    # Get network info
    network = get_network_info()
    print(f"Network has {network['alive_devices']} alive devices")

    if network['alive_devices'] > 1:
        # Find another device to message
        from network_table import network_table
        other_devices = []
        from message import NODE_ID

        for device_id, info in network_table.items():
            if device_id != NODE_ID and info.get('status') == 'alive':
                other_devices.append((device_id, info))

        if other_devices:
            target_id, target_info = other_devices[0]
            print(f"Sending test message to: {target_info.get('name', target_id[:8])}")

            # Create test message
            test_msg = {
                "test": True,
                "timestamp": time.time(),
                "message": "Hello from system test!"
            }

            # Send message
            success = send_message(target_id, test_msg)
            print(f"Message sent: {success}")
            if success:
                print("Note: Check other device's console for message receipt")
            return success
        else:
            print("No other devices available for messaging test")
            return True  # Not a failure, just no targets
    else:
        print("Only this device in network (need at least 2 for messaging test)")
        return True  # Not a failure


def test_system_info():
    """Test system information APIs."""
    print("\n" + "=" * 60)
    print("TEST 3: System Information")
    print("=" * 60)

    # Get system info
    info = get_network_info()
    print("System Information:")
    print(f"  Node: {info['node_name']} ({info['node_id'][:8]}...)")
    print(f"  Role: {info['role']}")
    print(f"  Uptime: {info['uptime']:.1f}s")
    print(f"  Devices: {info['alive_devices']}/{info['total_devices']} alive")

    # Get health check
    health = integrator.health_check()
    print("\nHealth Check:")
    print(f"  Status: {health['status']}")
    print(f"  Components: {', '.join([k for k, v in health['components'].items() if v])}")
    print(f"  Metrics: {health['metrics']}")

    return health['status'] == "HEALTHY"


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("SYSTEM INTEGRATION TEST SUITE")
    print("=" * 60)

    # Wait for system to stabilize
    print("Waiting 5 seconds for system to stabilize...")
    time.sleep(5)

    results = []

    # Run tests
    results.append(("Resolution", test_resolution()))
    results.append(("Messaging", test_messaging()))
    results.append(("System Info", test_system_info()))
    results.append(("Service Registry", test_service_registry()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED - System is properly integrated!")
    else:
        print("SOME TESTS FAILED - Check system integration")
    print("=" * 60)

    return all_passed




if __name__ == "__main__":
    # First ensure system is started
    from integration import start_system

    start_system()

    # Run tests
    run_all_tests()

    # Keep running for manual testing
    print("\nSystem is running. Press Ctrl+C to exit.")
    print("Open another terminal and run this script to test multi-device operation.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDemo complete.")


def test_service_registry():
    """Test Layer 3 service registry."""
    print("\n" + "=" * 60)
    print("TEST 4: Service Registry")
    print("=" * 60)

    from service_registry import get_all_services

    # Get all services
    all_services = get_all_services()
    print(f"Registered services: {len(all_services)}")

    for service_name, service_info in all_services.items():
        print(f"\nService: {service_name}")
        print(f"  Providers: {service_info['total_providers']} active")
        print(f"  Protocol: {service_info['metadata'].get('protocol', 'unknown')}")

        for provider in service_info['providers'][:3]:  # Show first 3
            print(f"  - {provider['name']} (health: {provider['health']:.1f})")

    # Test service registration from this device
    from integration import integrator
    test_service = "test_service_" + str(int(time.time()))

    print(f"\nRegistering test service: {test_service}")
    success = integrator.register_service(test_service, port=6000)
    print(f"Registration: {'✅ Success' if success else '❌ Failed'}")

    # Verify it appears
    service_info = integrator.get_service_info(test_service)
    if service_info:
        print(f"Verified: {test_service} has {service_info['total_providers']} provider(s)")
        return True
    else:
        print(f"Failed: {test_service} not found in registry")
        return False

discovery.py
import socket
import json
import time
import uuid
import os
import threading
from network_table import update_network_table, print_network_state
from service_registry import process_discovery_announcement  # NEW: Import service registry

# ------------
# CONFIGURATION
# ------------
DISCOVERY_PORT = 37020
BROADCAST_ADDRESS = '255.255.255.255'
ANNOUNCE_INTERVAL = 5  # seconds

# ------------------
# DEVICE IDENTITY
# ------------------

DEVICE_ID_FILE = "device_id.txt"

# Load or create persistent device ID
if os.path.exists(DEVICE_ID_FILE):
    with open(DEVICE_ID_FILE, "r") as f:
        DEVICE_ID = f.read().strip()
else:
    DEVICE_ID = str(uuid.uuid4())
    with open(DEVICE_ID_FILE, "w") as f:
        f.write(DEVICE_ID)
DEVICE_NAME = socket.gethostname()

SERVICES = ["games"]  # toy service
SERVICE_PORT = 5000  # toy port

# -----------------------------
# THIS NODE'S DECLARED ROLE
# -----------------------------

DECLARED_ROLE = "game"  # To be changed later and controlled by admin

# --------------
# UDP SOCKET & ANNOUNCE LOOP
# --------------
"""""
    When this program runs, it should:
        -Periodically send a UDP broadcast message
        -Containing its identity and offered services
        -To the local network
"""""


def announce_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # OS permission to send packets to broadcast address

    while True:
        message = {
            "protocol_version": 1,
            "type": "DISCOVERY_ANNOUNCE",
            "device_id": DEVICE_ID,
            "device_name": DEVICE_NAME,
            "role": DECLARED_ROLE,
            "services": SERVICES,
            "service_port": SERVICE_PORT,
            "timestamp": time.time()
        }

        data = json.dumps(message).encode('utf-8')
        sock.sendto(data, (BROADCAST_ADDRESS, DISCOVERY_PORT))
        print("Broadcasted discovery announce")
        time.sleep(ANNOUNCE_INTERVAL)


# --------------
# LISTEN LOOP (UPDATED WITH SERVICE REGISTRY)
# --------------
"""""
    WHAT THE LISTEN LOOP MUST DO

        -Conceptually, it does only this:
        -Bind to the discovery port
        -Wait for UDP packets
        -Decode the message
        -Extract sender identity
        -React (for now: print)

    NOW ALSO:
        -Process service registrations with Layer 3
"""""


def listen_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                    1)  # Solves OSError: [Errno 98] Address already in use: if Two processes listen on the same port,Or you restart quickly
    sock.bind(("", DISCOVERY_PORT))

    while True:
        data, addr = sock.recvfrom(4096)
        sender_ip = addr[0]

        try:
            message = json.loads(data.decode('utf-8'))
        except json.JSONDecodeError:
            continue

        msg_type = message.get("type")
        device_id = message.get("device_id")

        if not msg_type or not device_id:
            continue

        # Ignore our own broadcasts
        if device_id == DEVICE_ID:
            continue

        # -----------------------------
        # DISCOVERY ANNOUNCE (UPDATED)
        # -----------------------------
        if msg_type == "DISCOVERY_ANNOUNCE":

            received_role = message.get("role")
            services = message.get("services", [])  # NEW: Get services
            service_port = message.get("service_port", 5000)  # NEW: Get service port

            # Update network table (Layer 1)
            update_network_table(
                device_id=device_id,
                ip=sender_ip,
                name=message.get("device_name"),
                role=received_role,
                services=services,  # NEW: Pass services
                service_port=service_port  # NEW: Pass service port
            )

            # Register services with Layer 3 service registry
            registration_result = process_discovery_announcement(
                device_id=device_id,
                announcement_data=message
            )

            # Log registration results
            if registration_result["rejected"]:
                display_name = message.get("device_name") or device_id[:8]
                print(
                    f"[DISCOVERY] Service registration rejected for {display_name}: {registration_result['rejected']}")

        # -----------------------------
        # HELLO HANDSHAKE
        # -----------------------------
        elif msg_type == "HELLO":
            update_network_table(
                device_id=device_id,
                ip=sender_ip,
                name=message.get("name"),
                role=message.get("role", "unknown")
            )

        # Print discovered device info safely
        display_name = message.get("device_name") or message.get("name") or device_id[:8]
        services_list = message.get("services", [])
        services_str = f", Services: {services_list}" if services_list else ""
        print(f"Discovered device at {sender_ip}")
        print(f"  Name: {display_name}{services_str}")
        print("-" * 40)


# --------------
# MAIN
# --------------
print("Starting Discovery Protocol v0")
print(f"Device Name: {DEVICE_NAME}")
print(f"Device ID: {DEVICE_ID}")
print(f"Services: {SERVICES}")
print("-" * 40)

threading.Thread(target=announce_loop, daemon=True).start()
threading.Thread(target=listen_loop, daemon=True).start()

# Keep main thread alive
while True:
    print_network_state()
    time.sleep(10)
integration.py
"""
========================================================
System Integration Layer
========================================================

Purpose:
--------
Ensures all system layers are properly connected and initialized.
Provides a unified API for the entire system.

This layer:
- Initializes all components
- Manages cross-layer dependencies
- Provides public API endpoints
- Handles graceful startup/shutdown

========================================================
"""

import threading
import time
from typing import Dict, Any, List, Optional
# Import all system components
from network_table import network_table
from resolver import Layer2Resolver
from message import NODE_ID, NODE_NAME, DECLARED_ROLE, send_to_node, send_to_role
from service_registry import get_service_info as get_service_info_from_registry
from service_registry import get_all_services
from service_registry import register_services_from_discovery

# -------------------------------------------------------
# System Integrator
# -------------------------------------------------------

class SystemIntegrator:
    """
    Main integration class that connects all layers.
    """

    def __init__(self):
        self.running = False
        self.resolver = None
        self.startup_time = time.time()

    def start(self):
        """
        Initialize and start all system layers.
        """
        if self.running:
            print("[INTEGRATION] System already running")
            return

        print("[INTEGRATION] Starting system integration...")

        # Initialize Layer 5 storage
        print("[INTEGRATION] Initializing Layer 5 storage...")
        from storage_layer import initialize_storage
        storage_ok = initialize_storage()
        print(f"[INTEGRATION] Layer 5 storage: {'READY' if storage_ok else 'FAILED (JSON fallback active)'}")

        # Initialize Layer 2 Resolver
        self.resolver = Layer2Resolver(network_table)
        print(f"[INTEGRATION] Layer 2 Resolver initialized")

        # Start Layer 6 Internet Gateway (if internet available)
        internet_available = self.is_internet_available()
        if internet_available:
            gateway_started = self.start_internet_gateway()
            print(f"[INTEGRATION] Layer 6 gateway: {'STARTED' if gateway_started else 'FAILED'}")
        else:
            print("[INTEGRATION] Layer 6 gateway: SKIPPED (no internet)")

        # System is now running
        self.running = True

        # Print system info
        print(f"[INTEGRATION] System initialized successfully")
        print(f"  Node ID: {NODE_ID}")
        print(f"  Node Name: {NODE_NAME}")
        print(f"  Role: {DECLARED_ROLE}")
        print(f"  Devices in network: {len(network_table)}")
        print(f"  Internet available: {'YES' if internet_available else 'NO'}")
        print("[INTEGRATION] System ready")

    def stop(self):
        """
        Gracefully stop all system components.
        """
        self.running = False
        print("[INTEGRATION] System stopping...")

    # ---------------------------------------------------
    # Public API - Resolution
    # ---------------------------------------------------

    def resolve(self, name: str) -> Dict[str, Any]:
        """
        Resolve a .mtd name to network address(es).

        Args:
            name: Name to resolve (e.g., "alpha.mtd", "svc.chat.mtd")

        Returns:
            Resolution record with status and records

        Raises:
            RuntimeError: If system is not initialized
        """
        if not self.running:
            raise RuntimeError("System not initialized. Call start() first.")

        if not self.resolver:
            return {"status": "ERROR", "error": "Resolver not initialized"}

        return self.resolver.resolve(name)

    def resolve_device(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a device name (convenience wrapper).

        Args:
            device_name: Device name without .mtd suffix

        Returns:
            Device information or None if not found
        """
        result = self.resolve(f"{device_name}.mtd")
        if result["status"] == "OK" and result["records"]:
            return result["records"][0]
        return None

    def resolve_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Resolve a service name (convenience wrapper).

        Args:
            service_name: Service name without svc. prefix or .mtd suffix

        Returns:
            List of service providers
        """
        result = self.resolve(f"svc.{service_name}.mtd")
        if result["status"] == "OK":
            return result["records"]
        return []

    # ---------------------------------------------------
    # Public API - Messaging
    # ---------------------------------------------------

    @staticmethod
    def send_message(target: str, payload: Any) -> bool:
        """
        Send a message to a target (device ID or name).

        Args:
            target: Device ID or device name
            payload: Message content

        Returns:
            True if sent successfully
        """
        try:
            send_to_node(target, payload)
            return True
        except Exception as e:
            print(f"[INTEGRATION] Failed to send message: {e}")
            return False

    @staticmethod
    def send_to_role(role: str, payload: Any) -> int:
        """
        Send message to all devices with a specific role.

        Args:
            role: Target role (game, chat, cache, storage)
            payload: Message content

        Returns:
            Number of devices messages were sent to
        """
        try:
            # Use message.py's send_to_role which already handles filtering
            send_to_role(role, payload)

            # Count how many devices match the role
            from network_table import get_devices_by_role
            matching_devices = get_devices_by_role(role, require_alive=True, min_health=0.5)
            return len(matching_devices)
        except Exception as e:
            print(f"[INTEGRATION] Failed to send to role {role}: {e}")
            return 0

    # ---------------------------------------------------
    # Public API - Network Information
    # ---------------------------------------------------

    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """
        Get current network information.
        """
        from network_table import network_table

        alive_devices = [d for d in network_table.values() if d.get("status") == "alive"]
        roles = {}
        for device in alive_devices:
            role = device.get("role", "unknown")
            roles[role] = roles.get(role, 0) + 1

        services = {}
        for device in alive_devices:
            for service in device.get("services", []):
                services[service] = services.get(service, 0) + 1

        return {
            "node_id": NODE_ID,
            "node_name": NODE_NAME,
            "role": DECLARED_ROLE,
            "total_devices": len(network_table),
            "alive_devices": len(alive_devices),
            "roles": roles,
            "services": services,
            "uptime": time.time() - SystemIntegrator._get_startup_time()
        }

    @staticmethod
    def _get_startup_time() -> float:
        """Get the startup time for the current instance."""
        # This is a workaround since static methods can't access instance attributes
        # In a real implementation, you might want to track this differently
        try:
            from integration import integrator
            return integrator.startup_time
        except (ImportError, AttributeError):
            return time.time()

    @staticmethod
    def get_device_info(device_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific device or this device.

        Args:
            device_id: Device ID or None for this device

        Returns:
            Device information or None
        """
        from network_table import network_table

        target_id = device_id or NODE_ID
        device_info = network_table.get(target_id)

        if device_info:
            return {
                "device_id": target_id,
                **device_info
            }
        return None

    # ---------------------------------------------------
    # Public API - Service Registry
    # ---------------------------------------------------

    @staticmethod
    def get_service_info(service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific service from Layer 3 registry.

        Args:
            service_name: Name of the service

        Returns:
            Service information or None if not found
        """
        return get_service_info_from_registry(service_name)

    @staticmethod
    def get_all_services_info() -> Dict[str, Any]:
        """
        Get information about all registered services.
        """
        return get_all_services()

    @staticmethod
    def register_service(service_name: str, port: int = 5000, metadata: Optional[Dict] = None) -> bool:
        """
        Register a new service from this device.

        For applications to announce custom services.

        Args:
            service_name: Name of the service to register
            port: Port the service runs on
            metadata: Optional service metadata

        Returns:
            True if registration was successful
        """
        from discovery import SERVICES, SERVICE_PORT, DECLARED_ROLE

        # Update local services list
        if service_name not in SERVICES:
            SERVICES.append(service_name)
            print(f"[INTEGRATION] Added {service_name} to local services list")

        # Register with service registry
        result = register_services_from_discovery(
            device_id=NODE_ID,
            services=[service_name],
            service_port=port,
            role=DECLARED_ROLE
        )

        success = len(result["accepted"]) > 0

        if success:
            print(f"[INTEGRATION] Successfully registered service '{service_name}' on port {port}")
        else:
            print(f"[INTEGRATION] Failed to register service '{service_name}': {result.get('rejected', [])}")

        return success

    @staticmethod
    def get_storage_stats() -> Dict[str, Any]:
        """
        Get Layer 5 storage statistics.

        Returns:
            Storage statistics or error information
        """
        try:
            from storage_layer import get_storage_stats as get_layer5_stats
            return get_layer5_stats()
        except Exception as e:
            return {"status": "error", "error": str(e), "message": "Layer 5 not available"}

    # ---------------------------------------------------
    # System Health
    # ---------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        """
        Perform system health check.

        Returns:
            Health status with component details
        """
        from network_table import network_table

        # Check if resolver is working
        resolver_ok = self.resolver is not None

        # Check network table
        table_ok = isinstance(network_table, dict)

        # Count healthy devices
        healthy_devices = 0
        if table_ok:
            healthy_devices = sum(1 for d in network_table.values()
                                 if d.get("status") == "alive" and d.get("health", 0) >= 0.5)

        # Test resolution if possible
        resolution_ok = False
        if resolver_ok and table_ok:
            try:
                # Try to resolve our own device
                result = self.resolve(f"{NODE_NAME}.mtd")
                resolution_ok = result["status"] in ["OK", "NX"]
            except Exception as e:
                print(f"[INTEGRATION] Resolution test failed: {e}")
                resolution_ok = False

        # Determine overall status
        components_ok = all([resolver_ok, table_ok, resolution_ok])

        return {
            "status": "HEALTHY" if components_ok else "DEGRADED",
            "components": {
                "resolver": resolver_ok,
                "network_table": table_ok,
                "resolution": resolution_ok
            },
            "metrics": {
                "total_devices": len(network_table) if table_ok else 0,
                "healthy_devices": healthy_devices,
                "system_uptime": time.time() - self.startup_time
            }
        }

    # ---------------------------------------------------
    # Public API - Layer 6 Internet Gateway
    # ---------------------------------------------------

    def start_internet_gateway(self, listen_port: int = 8080) -> bool:
        """
        Start the Layer 6 internet gateway.

        Args:
            listen_port: Port for clients to connect to gateway

        Returns:
            True if gateway started successfully
        """
        try:
            from internet_fallback import InternetGateway

            self.gateway = InternetGateway(listen_port=listen_port)
            self.gateway.start()

            print(f"[INTEGRATION] Layer 6 gateway started on port {listen_port}")
            return True

        except Exception as e:
            print(f"[INTEGRATION] Failed to start internet gateway: {e}")
            return False

    @staticmethod
    def is_internet_available() -> bool:
        """
        Check if internet connectivity is available.

        Returns:
            True if internet appears to be accessible
        """
        import socket

        try:
            # Quick test to common DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    @staticmethod
    def resolve_with_fallback(name: str) -> Dict[str, Any]:
        """
        Resolve name with local-first, internet-fallback logic.

        Args:
            name: Name to resolve

        Returns:
            Resolution result with source indicator
        """
        from integration import integrator

        # 1. Try local resolution first
        local_result = integrator.resolve(name)

        if local_result["status"] == "OK":
            return {
                **local_result,
                "source": "local",
                "gateway_used": False
            }

        # 2. If local fails and internet is available, mark for internet fallback
        if SystemIntegrator.is_internet_available():
            return {
                "status": "INTERNET_FALLBACK",
                "name": name,
                "source": "internet",
                "gateway_used": True,
                "gateway_port": 8080  # Default gateway port
            }

        # 3. Both local and internet unavailable
        return {
            **local_result,  # Returns NX status
            "source": "none",
            "gateway_used": False
        }


# -------------------------------------------------------
# Global Instance
# -------------------------------------------------------

# Create global integrator instance
integrator = SystemIntegrator()

# -------------------------------------------------------
# Convenience Functions
# -------------------------------------------------------

def start_system() -> None:
    """Start the entire system."""
    integrator.start()

def stop_system() -> None:
    """Stop the entire system."""
    integrator.stop()

def resolve(name: str) -> Dict[str, Any]:
    """Resolve a .mtd name."""
    return integrator.resolve(name)

def send_message(target: str, payload: Any) -> bool:
    """Send a message to a target."""
    return SystemIntegrator.send_message(target, payload)

def get_network_info() -> Dict[str, Any]:
    """Get network information."""
    return SystemIntegrator.get_network_info()

def get_service_info(service_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific service."""
    return SystemIntegrator.get_service_info(service_name)

def get_all_services_info() -> Dict[str, Any]:
    """Get information about all registered services."""
    return SystemIntegrator.get_all_services_info()

def register_service(service_name: str, port: int = 5000, metadata: Optional[Dict] = None) -> bool:
    """Register a new service from this device."""
    return SystemIntegrator.register_service(service_name, port, metadata)

def get_device_info(device_id: str = None) -> Optional[Dict[str, Any]]:
    """Get information about a specific device."""
    return SystemIntegrator.get_device_info(device_id)

def health_check() -> Dict[str, Any]:
    """Perform system health check."""
    return integrator.health_check()

def get_storage_stats() -> Dict[str, Any]:
    """Get Layer 5 storage statistics."""
    return SystemIntegrator.get_storage_stats()

def start_internet_gateway(listen_port: int = 8080) -> bool:
    """Start the Layer 6 internet gateway."""
    return integrator.start_internet_gateway(listen_port)

def is_internet_available() -> bool:
    """Check if internet connectivity is available."""
    return SystemIntegrator.is_internet_available()

def resolve_with_fallback(name: str) -> Dict[str, Any]:
    """Resolve name with local-first, internet-fallback logic."""
    return SystemIntegrator.resolve_with_fallback(name)

# -------------------------------------------------------
# Module Exports
# -------------------------------------------------------

__all__ = [
    # Classes
    'SystemIntegrator',

    # Global instance
    'integrator',

    # Convenience functions
    'start_system',
    'stop_system',
    'resolve',
    'send_message',
    'get_network_info',
    'get_service_info',
    'get_all_services_info',
    'register_service',
    'get_device_info',
    'health_check',
    'start_internet_gateway',
    'is_internet_available',
    'resolve_with_fallback',

    # Service registry functions (explicitly exported)
    'register_services_from_discovery'
]
internet_fallback.py
"""
Layer 6 — Internet Egress & Fallback Gateway
===========================================

Responsibilities:
- Transparent internet egress
- Automatic fallback routing
- Session-aware forwarding
- No user interaction
- No persistence logic

Consumes:
- Layer 3 (resolution / services)
- Layer 4 (delivery attempt / messaging)
- Layer 5 (authoritative snapshots, policies)

This layer MAY touch the public internet.
"""

import socket
import threading
import time
from typing import Dict, Tuple, Optional

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443

SOCKET_TIMEOUT = 5.0
MAX_RETRIES = 2

BUFFER_SIZE = 8192

# ---------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------

class GatewaySession:
    """
    Tracks a single client → internet session.
    """

    def __init__(self, client_addr: Tuple[str, int], target: Tuple[str, int]):
        self.client_addr = client_addr
        self.target = target
        self.created_at = time.time()
        self.last_activity = time.time()
        self.bytes_up = 0
        self.bytes_down = 0

# ---------------------------------------------------------------------
# GATEWAY CORE
# ---------------------------------------------------------------------


class InternetGateway:
    """
    Layer 6 Gateway Core.

    Listens locally, forwards externally.
    Acts as a transparent proxy / NAT-equivalent.
    """

    def __init__(self, listen_ip:str = "0.0.0.0", listen_port: int = 8080):
        self.listen_ip = listen_ip
        self.listen_port = listen_port

        self.sessions: Dict[Tuple[str, int], GatewaySession] = {}
        self._lock = threading.Lock()

        self.running = False


    # -----------------------------------------------------------------
    # START / STOP
    # -----------------------------------------------------------------

    def start(self):
        """
        Start the gateway listener.
        """
        self.running = True
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()

        print(f"[L6] Gateway listening on {self.listen_ip}:{self.listen_port}")

    def stop(self):
        self.running = False

# -----------------------------------------------------------------
# LISTENER
# -----------------------------------------------------------------
    def _listen_loop(self):
        """
        Accept incoming client connections.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.listen_ip, self.listen_port))
        server_sock.listen(128)

        while self.running:
            try:
                client_sock, client_addr = server_sock.accept()
                handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                handler.start()
            except Exception as e:
                print(f"[L6] Listener error: {e}")



# -----------------------------------------------------------------
# CLIENT HANDLING
# -----------------------------------------------------------------

def _handle_client(self, client_sock: socket.socket, client_addr):
    """
    Handle one client connection.
    """
    client_sock.settimeout(SOCKET_TIMEOUT) # the socket will raise a timeout exception instead of blocking forever If the client stops responding

    try:
        initial_data = client_sock.recv(BUFFER_SIZE)
        if not initial_data:
            client_sock.close()
            return

        #Resolve destination (VERY naive MVP)
        target = self._extract_target(initial_data)
        if not target:
            client_sock.close()
            return

        session = GatewaySession(client_addr, target)

        with self._lock:
            self.sessions[client_addr] = session

        self._forward_session(client_sock, session, initial_data)

    except Exception as e:
        print(f"[L6] Client error {client_addr}: {e}")

    finally:
        client_sock.close()
        with self._lock:
            self.sessions.pop(client_addr, None)

# -----------------------------------------------------------------
# FORWARDING
# -----------------------------------------------------------------

def _forward_session(
        self,
        client_sock: socket.socket,
        session: GatewaySession,
        first_payload: bytes
):
    """
    Forward traffic between client and internet.
    """
    target_ip, target_port = session.target

    try:
        upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream.settimeout(SOCKET_TIMEOUT)
        upstream.connect((target_ip, target_port))

        # Send initial payload
        upstream.sendall(first_payload)

        # Bidirectional relay
        threading.Thread(
            target=self._relay,
            args=(client_sock, upstream, session, True),
            daemon=True
        ).start()

        self._relay(upstream, client_sock, session, False)

    except Exception as e:
        print(f"[L6] Upstream error {session.target}: {e}")


def _relay(
        self,
        source: socket.socket,
        destination: socket.socket,
        session: GatewaySession,
        upstream: bool
):
    """
    Relay bytes between sockets.
    """
    try:
        while True:
            data = source.recv(BUFFER_SIZE)
            if not data:
                break

            destination.sendall(data)

            session.last_activity = time.time()
            if upstream:
                session.bytes_up += len(data)
            else:
                session.bytes_down += len(data)

    except Exception:
        pass

# -----------------------------------------------------------------
# TARGET RESOLUTION (MVP)
# -----------------------------------------------------------------

    def _extract_target(self, payload: bytes) -> Optional[Tuple[str, int]]:
        """
        Extract target host from HTTP payload.
        This is intentionally naive and will be replaced later.
        """
        try:
            text = payload.decode(errors="ignore")
            for line in text.split("\r\n"):
                if line.lower().startswith("host:"):
                    host = line.split(":", 1)[1].strip()
                    if ":" in host:
                        h, p = host.split(":")
                        return h, int(p)
                    return host, DEFAULT_HTTP_PORT
        except Exception:
            return None

        return None
main.py
"""
Main Entry Point - Local-First Internet Substrate
=================================================

Starts all system layers and manages the complete stack.
"""
print("🔥 MAIN.PY STARTED - LINE 1")
import sys

print(f"🔥 Python version: {sys.version}")

import threading
import time
from discovery import announce_loop, listen_loop
from network_table import state_maintenance_loop, print_network_state
from message import listener_loop, ack_checker_loop, persistence_loop, load_pending_acks
from integration import integrator, start_system


def main():
    """
    Main system startup sequence.
    """
    print("=" * 60)
    print("Local-First Internet Substrate")
    print("=" * 60)

    # Phase 1: Initialize Layer 5 storage
    print("[BOOT] Phase 1: Initializing Layer 5 storage...")
    from storage_layer import initialize_storage
    initialize_storage()

    # Phase 2: Load persistent state
    print("[BOOT] Phase 2: Loading persistent state...")
    load_pending_acks()
    print("[BOOT] Persistent state loaded")

    # Phase 3: Start system integration
    print("[BOOT] Phase 3: Starting system integration...")
    start_system()

    # Phase 4: Start all background threads with verbose logging
    print("[BOOT] Phase 4: Starting background services...")

    # Layer 1 threads
    print("[MAIN] Starting announce_loop thread...")
    t1 = threading.Thread(target=announce_loop, daemon=True)
    t1.start()
    print(f"[MAIN] announce_loop started (ID: {t1.ident})")

    print("[MAIN] Starting listen_loop thread...")
    t2 = threading.Thread(target=listen_loop, daemon=True)
    t2.start()
    print(f"[MAIN] listen_loop started (ID: {t2.ident})")

    print("[MAIN] Starting state_maintenance_loop thread...")
    t3 = threading.Thread(target=state_maintenance_loop, daemon=True)
    t3.start()
    print(f"[MAIN] state_maintenance_loop started (ID: {t3.ident})")

    # CRITICAL: Message listener thread
    print("[MAIN] 🟢 Starting listener_loop thread (MESSAGING)...")
    t4 = threading.Thread(target=listener_loop, daemon=True)
    t4.start()
    print(f"[MAIN] 🟢 listener_loop started (ID: {t4.ident})")

    # Give listener thread time to initialize
    print("[MAIN] Waiting 2 seconds for listener to initialize...")
    time.sleep(2)

    print("[MAIN] Starting ack_checker_loop thread...")
    t5 = threading.Thread(target=ack_checker_loop, daemon=True)
    t5.start()
    print(f"[MAIN] ack_checker_loop started (ID: {t5.ident})")

    print("[MAIN] Starting persistence_loop thread...")
    t6 = threading.Thread(target=persistence_loop, daemon=True)
    t6.start()
    print(f"[MAIN] persistence_loop started (ID: {t6.ident})")

    # Show all active threads
    time.sleep(1)
    print("\n" + "=" * 60)
    print(f"[MAIN] ACTIVE THREADS: {threading.active_count()}")
    print("=" * 60)
    for i, thread in enumerate(threading.enumerate()):
        print(f"  {i + 1}. {thread.name} (daemon: {thread.daemon}) - alive: {thread.is_alive()}")
    print("=" * 60 + "\n")

    print("[BOOT] All services started")
    print("[BOOT] System is now operational")
    print("=" * 60)

    # Main loop
    try:
        counter = 0
        while True:
            # Print network state every 30 seconds
            if counter % 3 == 0:
                print_network_state()

            # Print system health every 60 seconds
            if counter % 6 == 0:
                health = integrator.health_check()
                print(f"[HEALTH] Status: {health['status']}, "
                      f"Devices: {health['metrics']['healthy_devices']}/{health['metrics']['total_devices']}")

            counter += 1
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Graceful shutdown initiated...")
        integrator.stop()
        print("[SHUTDOWN] System stopped")


if __name__ == "__main__":
    main()

message.py
"""
Main Entry Point - Local-First Internet Substrate
=================================================

Starts all system layers and manages the complete stack.
"""
print("🔥 MAIN.PY STARTED - LINE 1")
import sys

print(f"🔥 Python version: {sys.version}")

import threading
import time
from discovery import announce_loop, listen_loop
from network_table import state_maintenance_loop, print_network_state
from message import listener_loop, ack_checker_loop, persistence_loop, load_pending_acks
from integration import integrator, start_system


def main():
    """
    Main system startup sequence.
    """
    print("=" * 60)
    print("Local-First Internet Substrate")
    print("=" * 60)

    # Phase 1: Initialize Layer 5 storage
    print("[BOOT] Phase 1: Initializing Layer 5 storage...")
    from storage_layer import initialize_storage
    initialize_storage()

    # Phase 2: Load persistent state
    print("[BOOT] Phase 2: Loading persistent state...")
    load_pending_acks()
    print("[BOOT] Persistent state loaded")

    # Phase 3: Start system integration
    print("[BOOT] Phase 3: Starting system integration...")
    start_system()

    # Phase 4: Start all background threads with verbose logging
    print("[BOOT] Phase 4: Starting background services...")

    # Layer 1 threads
    print("[MAIN] Starting announce_loop thread...")
    t1 = threading.Thread(target=announce_loop, daemon=True)
    t1.start()
    print(f"[MAIN] announce_loop started (ID: {t1.ident})")

    print("[MAIN] Starting listen_loop thread...")
    t2 = threading.Thread(target=listen_loop, daemon=True)
    t2.start()
    print(f"[MAIN] listen_loop started (ID: {t2.ident})")

    print("[MAIN] Starting state_maintenance_loop thread...")
    t3 = threading.Thread(target=state_maintenance_loop, daemon=True)
    t3.start()
    print(f"[MAIN] state_maintenance_loop started (ID: {t3.ident})")

    # CRITICAL: Message listener thread
    print("[MAIN] 🟢 Starting listener_loop thread (MESSAGING)...")
    t4 = threading.Thread(target=listener_loop, daemon=True)
    t4.start()
    print(f"[MAIN] 🟢 listener_loop started (ID: {t4.ident})")

    # Give listener thread time to initialize
    print("[MAIN] Waiting 2 seconds for listener to initialize...")
    time.sleep(2)

    print("[MAIN] Starting ack_checker_loop thread...")
    t5 = threading.Thread(target=ack_checker_loop, daemon=True)
    t5.start()
    print(f"[MAIN] ack_checker_loop started (ID: {t5.ident})")

    print("[MAIN] Starting persistence_loop thread...")
    t6 = threading.Thread(target=persistence_loop, daemon=True)
    t6.start()
    print(f"[MAIN] persistence_loop started (ID: {t6.ident})")

    # Show all active threads
    time.sleep(1)
    print("\n" + "=" * 60)
    print(f"[MAIN] ACTIVE THREADS: {threading.active_count()}")
    print("=" * 60)
    for i, thread in enumerate(threading.enumerate()):
        print(f"  {i + 1}. {thread.name} (daemon: {thread.daemon}) - alive: {thread.is_alive()}")
    print("=" * 60 + "\n")

    print("[BOOT] All services started")
    print("[BOOT] System is now operational")
    print("=" * 60)

    # Main loop
    try:
        counter = 0
        while True:
            # Print network state every 30 seconds
            if counter % 3 == 0:
                print_network_state()

            # Print system health every 60 seconds
            if counter % 6 == 0:
                health = integrator.health_check()
                print(f"[HEALTH] Status: {health['status']}, "
                      f"Devices: {health['metrics']['healthy_devices']}/{health['metrics']['total_devices']}")

            counter += 1
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Graceful shutdown initiated...")
        integrator.stop()
        print("[SHUTDOWN] System stopped")


if __name__ == "__main__":
    main()
resolver.py
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
network_table.py
"""
Network Table - Layer 1 Core Storage
Persistent device registry with health tracking and services support.
"""
import time
import threading
import json
import os
from allowed_roles import ALLOWED_ROLES

# -----------------------------
# NETWORK TABLE
# -----------------------------
# Global in-memory table of known nodes
# Key   -> device_id (UUID)
# Value -> metadata about the node
network_table = {}

NODE_TIMEOUT = 15  # seconds before a node is considered dead
STATE_FILE = "network_state.json"


# -----------------------------
# PERSISTENCE FUNCTIONS (Layer 2.2)
# -----------------------------

def save_network_state():
    """
    Persist the network table to disk and Layer 5 storage.
    JSON remains as backup if Layer 5 fails.
    """
    try:
        # 1. Always save to JSON (backup/fallback)
        with open(STATE_FILE, "w") as f:
            json.dump(network_table, f, indent=2)

        # 2. Try to save to Layer 5 (primary)
        from storage_layer import save_network_state as save_to_layer5
        result = save_to_layer5(network_table)

        if result.get("method") == "layer5":
            print(f"[NETWORK] State saved to Layer 5 storage")
        elif result.get("method") == "json":
            print(f"[NETWORK] Layer 5 failed, using JSON only: {result.get('error', 'unknown')}")

    except Exception as e:
        print(f"[PERSISTENCE ERROR] Failed to save state: {e}")


def load_network_state():
    """
    Load network table from Layer 5 or JSON backup.
    """
    global network_table

    # 1. Try Layer 5 first (primary)
    try:
        from storage_layer import load_network_state as load_from_layer5
        layer5_data = load_from_layer5()
        if layer5_data:
            print("[NETWORK] Loaded from Layer 5 storage")
            network_table = layer5_data
            return
    except Exception as e:
        print(f"[NETWORK] Layer 5 load failed, trying JSON: {e}")

    # 2. Fall back to JSON file
    if not os.path.exists(STATE_FILE):
        print("[NETWORK] No persistent state found (first run)")
        return

    try:
        with open(STATE_FILE, "r") as f:
            network_table = json.load(f)
            # Convert string timestamps to float if needed
            for entry in network_table.values():
                if "last_seen" in entry:
                    entry["last_seen"] = float(entry["last_seen"])
        print("[NETWORK] Loaded from JSON backup")
    except Exception as e:
        print(f"[PERSISTENCE ERROR] Failed to load state: {e}")

    # After loading network_table, remove ALL entries for THIS device ID
    # except the current one
    current_id = None  # You need to pass this from discover.py
    to_delete = []
    for device_id, info in network_table.items():
        if info.get("ip") == "192.168.2.110" and device_id != current_id:
            to_delete.append(device_id)
    for device_id in to_delete:
        del network_table[device_id]


def persistence_loop():
    """
    Background thread to periodically save network state.
    """
    while True:
        save_network_state()
        time.sleep(5)


# -----------------------------
# ROLE SANITIZATION / ENFORCEMENT
# -----------------------------

def sanitize_role(role):
    """
    Ensures only allowed roles are accepted.
    Prevents accidental/malicious role injection.
    """
    return role if role in ALLOWED_ROLES else "unknown"


# -----------------------------
# UPDATE / INSERT NODE (UPDATED FOR SERVICES)
# -----------------------------

def update_network_table(device_id, ip, name=None, role="unknown", services=None, service_port=5000):
    """
    Updates or inserts a node entry in the network table.
    ROLE ENFORCEMENT RULE:
        - First observed role is authoritative.
        - Node cannot change role at runtime.

    NEW: Now includes services and service_port support.
    """
    current_time = time.time()

    claimed_role = sanitize_role(role)
    role_trusted = claimed_role in ALLOWED_ROLES

    entry = network_table.get(device_id)

    if entry is None:
        # New node - include services
        network_table[device_id] = {
            "name": name,
            "ip": ip,
            "last_seen": current_time,
            "role": claimed_role,
            "role_trusted": role_trusted,
            "status": "alive",
            "health": 1.0,  # Start with full health
            "services": services or [],  # NEW: Store services list
            "service_port": service_port  # NEW: Store service port
        }
    else:
        # Refresh existing node
        entry["ip"] = ip
        entry["last_seen"] = current_time
        entry["status"] = "alive"

        if name is not None:
            entry["name"] = name

        # Update services if provided
        if services is not None:
            entry["services"] = services
            entry["service_port"] = service_port

        # ---- ROLE CONSISTENCY ENFORCEMENT ----
        if entry["role"] != claimed_role:
            print(
                f"[ROLE WARNING] Node {device_id[:8]} attempted role change "
                f"from '{entry['role']}' to '{claimed_role}'. Ignored."
            )
        else:
            entry["role_trusted"] = role_trusted


# -----------------------------
# NODE HEALTH / EXPIRY
# -----------------------------

def expire_stale_nodes():
    """
    Mark nodes as dead if they haven't been seen recently.
    """
    current_time = time.time()
    for info in network_table.values():
        if current_time - info["last_seen"] > NODE_TIMEOUT:
            info["status"] = "dead"


def state_maintenance_loop():
    """
    Background thread to maintain network state.
    """
    while True:
        expire_stale_nodes()
        time.sleep(5)


# ----------------------------------------
#  NODE INTERACTIONS-SUCCESS OR FAILURE
# ----------------------------------------

def record_success(node_id):
    """
    Record successful interaction with a node.
    Increments health score, capped at 1.0.
    """
    if node_id in network_table:
        current_health = network_table[node_id].get("health", 1.0)
        network_table[node_id]["health"] = min(1.0, current_health + 0.1)
        print(f"[HEALTH] Node {node_id[:8]} health +0.1 → {network_table[node_id]['health']:.1f}")


def record_failure(node_id):
    """
    Record failed interaction with a node.
    Decrements health score, floored at 0.0.
    """
    if node_id in network_table:
        current_health = network_table[node_id].get("health", 1.0)
        network_table[node_id]["health"] = max(0.0, current_health - 0.3)
        print(f"[HEALTH] Node {node_id[:8]} health -0.3 → {network_table[node_id]['health']:.1f}")
        if network_table[node_id]["health"] <= 0.3:
            network_table[node_id]["status"] = "unhealthy"


# -----------------------------
# NETWORK STATE PRINTING
# -----------------------------

def print_network_state():
    """
    Prints current network table in readable format.
    """
    print("\n--- NETWORK STATE ---")
    for device_id, info in network_table.items():
        display_name = info.get("name") or device_id[:8]
        services = info.get("services", [])
        services_str = f", Services: {services}" if services else ""
        print(
            f"ID: {device_id} | "
            f"Name: {display_name} | "
            f"IP: {info['ip']} | "
            f"Role: {info['role']} (Trusted: {info['role_trusted']}) | "
            f"Status: {info['status']} | "
            f"Health: {info.get('health', 1.0):.1f}"
            f"{services_str}"
        )
    print("----------------------\n")


# -----------------------------
# PUBLIC API FUNCTIONS (NEW)
# -----------------------------

def get_device(device_id):
    """
    Get device information by ID.
    """
    return network_table.get(device_id)


def get_devices_by_role(role, require_alive=True, min_health=0.5):
    """
    Get all devices with a specific role.
    """
    devices = []
    for device_id, info in network_table.items():
        if info.get("role") != role:
            continue
        if require_alive and info.get("status") != "alive":
            continue
        if info.get("health", 1.0) < min_health:
            continue
        devices.append({"device_id": device_id, **info})
    return devices


def get_service_providers(service_name):
    """
    Get all devices that offer a specific service.
    """
    providers = []
    for device_id, info in network_table.items():
        if service_name in info.get("services", []) and info.get("status") == "alive":
            providers.append({
                "device_id": device_id,
                "ip": info["ip"],
                "name": info.get("name"),
                "port": info.get("service_port", 5000),
                "health": info.get("health", 1.0)
            })
    return providers


# -----------------------------
# INITIALIZATION
# -----------------------------
load_network_state()  # Hydrate network table before discovery traffic arrives

# Start background threads
threading.Thread(target=state_maintenance_loop, daemon=True).start()
threading.Thread(target=persistence_loop, daemon=True).start()
role_routing.py
"""
Layer 2 - Role Based Routing
============================

This module allows messages to be sent ONLY to nodes
that match a specific role (game, chat, cache, etc).

It relies entirely on:
- The Network Table from Layer 1
- The messaging primitive from Layer 4 (reliable messaging)

This file does NOT start threads.
It is called by higher-level application logic.

IMPORTANT: This is a convenience wrapper around Layer 4 messaging
that adds role-based filtering. All messages go through Layer 4
for reliability (ACKs, retries, health tracking).
"""

import time
from typing import List, Dict, Any
from message import send_to_node  # Use Layer 4's reliable messaging

# -----------------------------
# ROLE-BASED ROUTING (LAYER 2 WRAPPER)
# -----------------------------

def send_to_role_via_routing(role: str, message_type: str, content: Any, sender_name: str) -> Dict[str, Any]:
    """
    Sends a message to ALL alive and healthy nodes with a specific role.

    Parameters:
    - role        : target role (e.g. "game", "chat", "cache", "storage")
    - message_type: logical message category (e.g. "GAME_STATE", "CHAT_MESSAGE")
    - content     : actual payload (string or dict)
    - sender_name : human-readable sender identity

    This function:
    - Iterates over the Network Table (imported from message.py)
    - Filters by role, alive status, AND health threshold (>= 0.5)
    - Uses Layer 4's reliable messaging (ACKs, retries, health tracking)
    - Returns summary of sent messages

    Returns:
        {
            "sent_count": int,
            "failed_count": int,
            "target_nodes": List[str],
            "failed_nodes": List[str]
        }
    """
    from message import network_table  # Import the actual network table

    results = {
        "sent_count": 0,
        "failed_count": 0,
        "target_nodes": [],
        "failed_nodes": []
    }

    for device_id, info in network_table.items():
        # Skip dead or unhealthy nodes
        if info.get("status") != "alive":
            continue

        # Skip nodes with low health (same threshold as messaging layer)
        if info.get("health", 1.0) < 0.5:
            continue

        # Skip nodes that do not match role
        if info.get("role") != role:
            continue

        # Skip untrusted roles
        if not info.get("role_trusted", False):
            continue

        # Prepare payload for Layer 4 messaging
        payload = {
            "protocol_layer": 2,
            "routing_type": "role_based",
            "message_type": message_type,
            "from_name": sender_name,
            "to_role": role,
            "original_timestamp": time.time(),
            "content": content
        }

        try:
            # Use Layer 4's reliable messaging system
            # This gives us ACKs, retries, and health tracking automatically
            send_to_node(device_id, payload)

            results["sent_count"] += 1
            results["target_nodes"].append({
                "device_id": device_id,
                "name": info.get("name", "unknown"),
                "ip": info["ip"]
            })

        except Exception as e:
            print(f"[ROLE ROUTING] Failed to send to {info.get('name', device_id[:8])}: {e}")
            results["failed_count"] += 1
            results["failed_nodes"].append({
                "device_id": device_id,
                "name": info.get("name", "unknown"),
                "error": str(e)
            })

    print(f"[ROLE ROUTING] Sent '{message_type}' to {results['sent_count']} '{role}' nodes "
          f"({results['failed_count']} failed)")

    return results


def get_role_members(role: str, require_alive: bool = True, min_health: float = 0.5) -> List[Dict[str, Any]]:
    """
    Get all nodes with a specific role (for application use).

    Parameters:
    - role: Target role to filter by
    - require_alive: If True, only return nodes with status="alive"
    - min_health: Minimum health score required (0.0 to 1.0)

    Returns:
    List of node information dictionaries
    """
    from message import network_table

    members = []

    for device_id, info in network_table.items():
        if require_alive and info.get("status") != "alive":
            continue

        if info.get("health", 1.0) < min_health:
            continue

        if info.get("role") != role:
            continue

        if not info.get("role_trusted", False):
            continue

        members.append({
            "device_id": device_id,
            "name": info.get("name", "unknown"),
            "ip": info["ip"],
            "role": info.get("role"),
            "health": info.get("health", 1.0),
            "status": info.get("status"),
            "last_seen": info.get("last_seen", 0)
        })

    return members


def broadcast_to_all_roles(message_type: str, content: Any, sender_name: str,
                          excluded_roles: List[str] = None) -> Dict[str, Any]:
    """
    Send a message to nodes of ALL roles (except excluded ones).

    Useful for system announcements, maintenance, etc.
    """
    from message import network_table
    from allowed_roles import ALLOWED_ROLES

    excluded_roles = excluded_roles or []
    results = {}

    for role in ALLOWED_ROLES:
        if role == "unknown" or role in excluded_roles:
            continue

        results[role] = send_to_role_via_routing(
            role=role,
            message_type=message_type,
            content=content,
            sender_name=sender_name
        )

    total_sent = sum(r["sent_count"] for r in results.values())
    total_failed = sum(r["failed_count"] for r in results.values())

    print(f"[BROADCAST] Sent to {total_sent} total nodes across {len(results)} roles "
          f"({total_failed} total failures)")

    return {
        "total_sent": total_sent,
        "total_failed": total_failed,
        "by_role": results
    }
service_registry.py
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
storage_devices.py
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

storage_layer.py
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
storage_network_runtime.py
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
storage_persistence_service_registry.py
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

storage_protocol_core.py
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



storage_snapshot_lifecycle_retension.py
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

storage_system_state_snapshot.py
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
layer1discovery.py
#PHASE 2: Test Layer 1 (Discovery) - Two Devices Required
# test_layer1_discovery.py
"""
Test 1: Announce Loop (broadcasting)
Test 2: Listen Loop (receiving)
Test 3: Network Table (storing)
Test 4: Service Announcement
Test 5: Health & Timeout

RUN THIS ON TWO DEVICES SIMULTANEOUSLY
"""
import time
import threading
from discovery import announce_loop, listen_loop, DEVICE_ID, DEVICE_NAME, SERVICES
from network_table import network_table, print_network_state, NODE_TIMEOUT

print("="*60)
print("PHASE 2: TESTING LAYER 1 DISCOVERY")
print("="*60)
print(f"Device ID: {DEVICE_ID}")
print(f"Device Name: {DEVICE_NAME}")
print(f"Services: {SERVICES}")
print("\n⚠️  RUN THIS TEST ON 2+ DEVICES ON SAME NETWORK")
input("Press Enter when both devices are ready...")

# Start discovery threads
threading.Thread(target=announce_loop, daemon=True).start()
threading.Thread(target=listen_loop, daemon=True).start()

print("\n[TEST 2.1] Discovery Running - Waiting 15 seconds...")
time.sleep(15)

# Test 2.1: Device Discovery
print("\n[TEST 2.1] Device Discovery")
print_network_state()
if len(network_table) > 1:  # At least self + 1 other
    print(f"  ✓ Discovered {len(network_table)-1} other device(s)")
else:
    print("  ✗ No other devices discovered (FAIL)")
    print("    Check: Firewall, UDP port 37020, same network")

# Test 2.2: Service Announcement
print("\n[TEST 2.2] Service Announcement")
found_services = False
for device_id, info in network_table.items():
    if device_id != DEVICE_ID and info.get("services"):
        print(f"  ✓ Device {info.get('name')} offers: {info.get('services')}")
        found_services = True
if not found_services:
    print("  ⚠️  No services discovered from other devices")

# Test 2.3: Role & Trust
print("\n[TEST 2.3] Role Enforcement")
for device_id, info in network_table.items():
    if device_id != DEVICE_ID:
        print(f"  Device {info.get('name')}: role={info['role']}, trusted={info['role_trusted']}")

# Test 2.4: Health Tracking (Run for 30 seconds then kill one device)
print("\n[TEST 2.4] Health & Timeout (Manual Test)")
print("1. Keep both devices running - health should be 1.0")
print("2. Kill ONE device (Ctrl+C)")
print(f"3. Within {NODE_TIMEOUT} seconds, its status should change to 'dead'")
input("Press Enter when ready to monitor...")

for i in range(NODE_TIMEOUT + 5):
    time.sleep(1)
    print_network_state()

print("\n✅ LAYER 1 DISCOVERY TESTS COMPLETE")
layer2resolver.py
# PHASE 3: Test Layer 2 (Resolver) - Standalone + Layer 1
# test_layer2_resolver.py
"""
Test 1: Device Resolution (.mtd)
Test 2: Service Resolution (svc.*.mtd)
Test 3: Cache TTL
Test 4: Error Cases (NX, CONFLICT)

REQUIRES: Layer 1 running (devices in network_table)
"""
from resolver import Layer2Resolver
from network_table import network_table
import time

print("=" * 60)
print("PHASE 3: TESTING LAYER 2 RESOLVER")
print("=" * 60)

# Initialize resolver
resolver = Layer2Resolver(network_table)

# Test 3.1: Device Resolution
print("\n[TEST 3.1] Device Name Resolution")
if len(network_table) > 0:
    # Get first device (could be self or other)
    test_device_id = list(network_table.keys())[0]
    test_device_name = network_table[test_device_id].get("name", "unknown")

    result = resolver.resolve(f"{test_device_name}.mtd")
    print(f"  Resolving: {test_device_name}.mtd")
    print(f"  Status: {result['status']}")

    if result['status'] == "OK":
        print(f"  ✓ Found device: {result['records'][0]['ip']}")
    else:
        print(f"  ✗ Resolution failed")
else:
    print("  ⚠️  No devices in network table - run Layer 1 first")

# Test 3.2: Non-existent Device
print("\n[TEST 3.2] Non-existent Device (NX)")
result = resolver.resolve("nonexistent-device.mtd")
print(f"  Resolving: nonexistent-device.mtd")
print(f"  Status: {result['status']}")
print(f"  ✓ Expected NX: {'NX' in result['status']}")

# Test 3.3: Service Resolution
print("\n[TEST 3.3] Service Resolution")
# Try to resolve games service (default in discover.py)
result = resolver.resolve("svc.games.mtd")
print(f"  Resolving: svc.games.mtd")
print(f"  Status: {result['status']}")
if result['status'] == "OK":
    print(f"  ✓ Found {len(result['records'])} provider(s)")
    for p in result['records']:
        print(f"    - {p['name']} at {p['ip']}:{p['port']}")
else:
    print("  ⚠️  No game services discovered")

# Test 3.4: Invalid Name Format
print("\n[TEST 3.4] Invalid Name Format")
result = resolver.resolve("invalid-name-without-dot")
print(f"  Resolving: invalid-name-without-dot")
print(f"  Status: {result['status']}")
print(f"  ✓ Rejected (no .mtd): {'NX' in result['status']}")

# Test 3.5: Cache Test
print("\n[TEST 3.5] Resolution Cache (TTL 30s)")
start = time.time()
result1 = resolver.resolve(f"{test_device_name}.mtd" if len(network_table) > 0 else "test.mtd")
result2 = resolver.resolve(f"{test_device_name}.mtd" if len(network_table) > 0 else "test.mtd")
print(f"  First resolution: {result1.get('cached_at', 0)}")
print(f"  Second resolution: {result2.get('cached_at', 0)}")
if result1.get('cached_at') == result2.get('cached_at'):
    print("  ✓ Cache working (same timestamp)")
else:
    print("  ⚠️  Cache miss (different timestamps)")

print("\n✅ LAYER 2 RESOLVER TESTS COMPLETE")
layer3services.py
# PHASE 4: Test Layer 3 (Services) - Standalone + Layer 1
# test_layer3_services.py
"""
Test 1: Service Registration
Test 2: Role-Based Policy Enforcement
Test 3: Service Discovery
Test 4: TTL Expiration
Test 5: Health Integration

REQUIRES: Layer 1 running (devices in network_table)
"""
from service_registry import (
    register_services_from_discovery,
    get_service_providers,
    get_service_info,
    get_all_services,
    update_provider_health,
    service_resolver
)
from network_table import update_network_table

print("="*60)
print("PHASE 4: TESTING LAYER 3 SERVICE REGISTRY")
print("="*60)

# Test 4.1: Service Registration
print("\n[TEST 4.1] Service Registration")
# Create a test device in network table first
test_device_id = "test_device_123"
update_network_table(
    device_id=test_device_id,
    ip="192.168.1.99",
    name="TestDevice",
    role="game",
    services=["chat", "games"],
    service_port=6000
)

result = register_services_from_discovery(
    device_id=test_device_id,
    services=["chat", "games", "unauthorized"],
    service_port=6000,
    role="game"
)

print(f"  Accepted: {result['accepted']}")
print(f"  Rejected: {result['rejected']}")
if "chat" in result['accepted'] and "games" in result['accepted']:
    print("  ✓ Valid services accepted")
if "unauthorized" in result['rejected']:
    print("  ✓ Unauthorized service rejected (role policy working)")

# Test 4.2: Service Discovery
print("\n[TEST 4.2] Service Discovery")
providers = get_service_providers("chat")
print(f"  Chat providers: {len(providers)}")
for p in providers:
    print(f"    - {p['name']} at {p['ip']}:{p['port']} (health: {p['health']})")

# Test 4.3: Service Info
print("\n[TEST 4.3] Service Information")
info = get_service_info("chat")
if info:
    print(f"  Service: chat")
    print(f"  Protocol: {info['metadata'].get('protocol')}")
    print(f"  Providers: {info['total_providers']}")
    print(f"  Policy: {info['policy']}")

# Test 4.4: All Services
print("\n[TEST 4.4] All Registered Services")
all_services = get_all_services()
print(f"  Total services: {len(all_services)}")
for name, data in all_services.items():
    print(f"    - {name}: {data['total_providers']} providers")

# Test 4.5: Health Updates
print("\n[TEST 4.5] Provider Health Tracking")
# Get initial health
before = get_service_providers("chat")[0]['health']
print(f"  Initial health: {before}")

# Update health (success)
update_provider_health(test_device_id, success=True)
after_success = get_service_providers("chat")[0]['health']
print(f"  After success (+0.05): {after_success}")

# Update health (failure)
update_provider_health(test_device_id, success=False)
after_failure = get_service_providers("chat")[0]['health']
print(f"  After failure (-0.15): {after_failure}")

# Test 4.6: Layer 2 Resolver Integration
print("\n[TEST 4.6] Layer 2 Integration (service_resolver)")
providers = service_resolver.resolve_service("chat")
print(f"  service_resolver returns {len(providers)} providers")
print(f"  Sorted by health (highest first):")
for p in providers[:2]:  # Show top 2
    print(f"    - {p['name']}: health {p['health']}")

print("\n✅ LAYER 3 SERVICE REGISTRY TESTS COMPLETE")
layer4messaging.py
# PHASE 5: Test Layer 4 (Messaging) - Two Devices Required
# test_layer4_messaging.py
"""
Test 1: Send to Node (Direct)
Test 2: Send to Role (Broadcast)
Test 3: ACK/Retry Mechanism
Test 4: Health Integration
Test 5: Persistence (pending_acks.json)

REQUIRES: Layers 1-3 working, TWO DEVICES
"""
from message import send_to_node, send_to_role, NODE_ID, NODE_NAME
from network_table import network_table, print_network_state
import time

print("="*60)
print("PHASE 5: TESTING LAYER 4 MESSAGING")
print("="*60)
print(f"Local Device: {NODE_NAME} ({NODE_ID[:8]}...)")
print("\n⚠️  RUN THIS TEST ON 2+ DEVICES")
input("Press Enter when both devices are ready...")

# Show network state
print_network_state()

# Find another device
other_device = None
for device_id, info in network_table.items():
    if device_id != NODE_ID and info.get("status") == "alive":
        other_device = (device_id, info)
        break

if not other_device:
    print("❌ No other devices found! Run Layer 1 test first.")
    exit()

target_id, target_info = other_device
print(f"\nFound peer: {target_info.get('name')} ({target_id[:8]}...)")

# Test 5.1: Direct Message
print("\n[TEST 5.1] Direct Message (send_to_node)")
test_payload = {
    "type": "test",
    "message": f"Hello from {NODE_NAME}",
    "timestamp": time.time()
}
print(f"  Sending: {test_payload}")
send_to_node(target_id, test_payload)
print("  ✓ Message sent (check peer console for ACK)")

# Test 5.2: Role Broadcast
print("\n[TEST 5.2] Role Broadcast (send_to_role)")
role_payload = {
    "type": "broadcast_test",
    "message": f"Broadcast from {NODE_NAME}"
}
print(f"  Broadcasting to role 'game'")
send_to_role("game", role_payload)
print("  ✓ Broadcast sent (check all peers)")

# Test 5.3: ACK Timeout (Manual Test)
print("\n[TEST 5.3] ACK/Retry System")
print("  1. Normal operation: Should see ACK within 2 seconds")
print("  2. Kill peer device - Should see timeout after 2s, retry, then failure")
input("  Press Enter to test normal ACK...")
send_to_node(target_id, {"test": "normal_ack"})
time.sleep(3)

# Test 5.4: Health Impact
print("\n[TEST 5.4] Message Success/Failure → Health Update")
print("  Check network_table health scores:")
print(f"  Peer health before: {target_info.get('health', 1.0)}")
print("  Sending 5 successful messages...")
for i in range(5):
    send_to_node(target_id, {"seq": i, "test": "health_test"})
    time.sleep(0.5)

# Reload network table to see updated health
from network_table import network_table as updated_table
new_health = updated_table.get(target_id, {}).get('health', 0)
print(f"  Peer health after: {new_health}")

# Test 5.5: Persistence
print("\n[TEST 5.5] Message Persistence")
import os
import json
if os.path.exists("pending_acks.json"):
    with open("pending_acks.json", "r") as f:
        pending = json.load(f)
    print(f"  pending_acks.json: {len(pending)} pending messages")
    print("  ✓ Persistence file exists")
else:
    print("  ⚠️  pending_acks.json not found (normal if no pending)")

print("\n✅ LAYER 4 MESSAGING TESTS COMPLETE")
print("Check other device console for received messages and ACKs!")
layer5storage.py
#PHASE 1: Test Layer 5 (Storage) - Standalone
# test_layer5_storage.py
"""
Test 1: Core Storage Engine
Test 2: Device Registry
Test 3: Network Snapshots
Test 4: Service Registry Storage
Test 5: System Snapshots
"""
from storage_protocol_core import StorageEngine, VersionConflict
from storage_devices import DeviceRegistry
from storage_network_runtime import NetworkSnapshotStore
import time

print("=" * 60)
print("PHASE 1: TESTING LAYER 5 STORAGE")
print("=" * 60)

# Test 1.1: Core Storage Engine
print("\n[TEST 1.1] Core Storage Engine")
storage = StorageEngine()
try:
    # Put a record
    record = storage.put("test_collection", "record_1", {"data": "hello"}, None)
    print(f"  ✓ Created record v{record['version']}")

    # Get it back
    retrieved = storage.get("test_collection", "record_1")
    print(f"  ✓ Retrieved record v{retrieved['version']}")

    # Update with version check
    updated = storage.put("test_collection", "record_1", {"data": "world"}, 1)
    print(f"  ✓ Updated record v{updated['version']}")

    # Version conflict test
    try:
        storage.put("test_collection", "record_1", {"data": "fail"}, 1)
        print("  ✗ Version conflict NOT caught (FAIL)")
    except VersionConflict:
        print("  ✓ Version conflict correctly caught")

    print("  ✅ Core Storage Engine PASSED")
except Exception as e:
    print(f"  ❌ Core Storage Engine FAILED: {e}")

# Test 1.2: Device Registry
print("\n[TEST 1.2] Device Registry")
registry = DeviceRegistry(storage)
try:
    # Register device
    result = registry.register_device("device_123", {
        "first_seen": time.time(),
        "public_key": "abc123",
        "roles": ["game"],
        "metadata": {"name": "TestDevice", "ip": "192.168.1.10"}
    })
    print(f"  ✓ Registered device v{result['version']}")

    # Get device
    device = registry.get_device("device_123")
    print(f"  ✓ Retrieved device: {device['payload']['metadata']['name']}")

    # Check exists
    exists = registry.device_exists("device_123")
    print(f"  ✓ Device exists: {exists}")

    print("  ✅ Device Registry PASSED")
except Exception as e:
    print(f"  ❌ Device Registry FAILED: {e}")

# Test 1.3: Network Snapshots
print("\n[TEST 1.3] Network Snapshot Store")
snapshot_store = NetworkSnapshotStore(storage)
try:
    # Save snapshot
    test_network = {
        "device_123": {"name": "Alpha", "ip": "192.168.1.10", "status": "alive"},
        "device_456": {"name": "Beta", "ip": "192.168.1.11", "status": "alive"}
    }
    result = snapshot_store.save_snapshot(test_network)
    print(f"  ✓ Saved network snapshot v{result['version']}")

    # Load snapshot
    loaded = snapshot_store.load_latest_snapshot()
    count = loaded['payload']['device_count']
    print(f"  ✓ Loaded snapshot with {count} devices")

    print("  ✅ Network Snapshot Store PASSED")
except Exception as e:
    print(f"  ❌ Network Snapshot Store FAILED: {e}")

# Run this file alone first
if __name__ == "__main__":
    print("\n✅ LAYER 5 STORAGE TESTS COMPLETE")
layer6gateway.py
# PHASE 6: Test Layer 6 (Gateway) - Standalone + Internet
# test_layer6_gateway.py
"""
Test 1: Gateway Start/Stop
Test 2: HTTP Forwarding
Test 3: HTTPS Forwarding
Test 4: Internet Detection
Test 5: Fallback Resolution

REQUIRES: Internet connection (for actual tests)
"""
from internet_fallback import InternetGateway
from integration import is_internet_available, resolve_with_fallback
import socket
import time
import requests

print("=" * 60)
print("PHASE 6: TESTING LAYER 6 INTERNET GATEWAY")
print("=" * 60)

# Test 6.1: Internet Detection
print("\n[TEST 6.1] Internet Connectivity")
if is_internet_available():
    print("  ✓ Internet available")
else:
    print("  ⚠️  No internet - gateway tests will be limited")

# Test 6.2: Gateway Start/Stop
print("\n[TEST 6.2] Gateway Lifecycle")
gateway = InternetGateway(listen_port=8081)  # Different port to avoid conflict
print("  Starting gateway...")
gateway.start()
time.sleep(1)

# Check if port is listening
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 8081))
    if result == 0:
        print("  ✓ Gateway listening on port 8081")
    else:
        print(f"  ✗ Port 8081 not listening (error {result})")
    sock.close()
except Exception as e:
    print(f"  ✗ Failed to connect: {e}")

gateway.stop()
print("  ✓ Gateway stopped")

# Test 6.3: HTTP Forwarding (Requires Internet)
if is_internet_available():
    print("\n[TEST 6.3] HTTP Forwarding")
    gateway = InternetGateway(listen_port=8082)
    gateway.start()
    time.sleep(1)

    try:
        # Configure requests to use gateway
        proxies = {
            'http': 'http://localhost:8082',
            'https': 'http://localhost:8082'
        }

        print("  Sending HTTP request via gateway...")
        response = requests.get('http://example.com', proxies=proxies, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ HTTP request successful (status {response.status_code})")
            print(f"  ✓ Gateway forwarded {len(response.content)} bytes")
        else:
            print(f"  ✗ HTTP request failed: {response.status_code}")
    except Exception as e:
        print(f"  ✗ HTTP test failed: {e}")
    finally:
        gateway.stop()
else:
    print("\n[TEST 6.3] HTTP Forwarding - SKIPPED (no internet)")

# Test 6.4: Fallback Resolution (Integration Test)
print("\n[TEST 6.4] Fallback Resolution")
# Try to resolve something that definitely doesn't exist locally
result = resolve_with_fallback("this-definitely-does-not-exist-on-local-network")
print(f"  Resolution result:")
print(f"    Status: {result.get('status', 'unknown')}")
print(f"    Source: {result.get('source', 'unknown')}")
if result.get('source') == 'internet':
    print("  ✓ Fallback to internet working")
elif result.get('source') == 'none':
    print("  ⚠️  No internet fallback available")
else:
    print(f"  ⚠️  Unexpected source: {result.get('source')}")

print("\n✅ LAYER 6 GATEWAY TESTS COMPLETE")