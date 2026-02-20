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

_threads_started = False

def start_network_table_background_tasks():
    global _threads_started

    if _threads_started:
        print("[NETWORK] Background tasks already running")
        return

    load_network_state() # Hydrate network table before discovery traffic arrives

    threading.Thread(
        target=state_maintenance_loop,
        daemon=True
    ).start()

    threading.Thread(
        target=persistence_loop,
        daemon=True
    ).start()

    _threads_started = True
    print("[NETWORK] Background tasks started")
