"""
========================================================
Layer 4 — Messaging Protocol
========================================================

Purpose:
--------
Provides reliable, UDP-based messaging within the local
mesh network using:

- ACKs (acknowledgements)
- Retries
- Message state tracking
- Device health updates
- Persistent pending message storage
- Safe recovery on restart
- Full ACK tracking & retries

This layer is responsible for **message delivery guarantees**
and asynchronous **state management**.

========================================================
"""

import socket
import json
import threading
import time
import uuid
import os
import re  # ADDED: For IP pattern matching
from network_table import network_table, record_success, record_failure
from service_registry import update_provider_health
from discovery import DEVICE_ID, DEVICE_NAME

# -----------------------------
# CONFIGURATION
# -----------------------------

NODE_ID = DEVICE_ID
NODE_NAME = DEVICE_NAME
DECLARED_ROLE = "game"
LOCAL_PORT = 51000
ACK_TIMEOUT = 2.0
MAX_RETRIES = 1
SAVE_INTERVAL = 5  # seconds for saving pending ACKs to disk
PENDING_FILE = "pending_acks.json"

# -----------------------------
# PENDING ACKS / STATE
# -----------------------------
pending_ACKS = {}
_pending_lock = threading.Lock()  # thread safety

# NOTE: Socket creation removed from module level!
# Each function now creates its own socket to avoid binding conflicts.
# This is necessary for direct Ethernet testing with hardcoded IPs.
#
# WHEN YOU RETURN TO NORMAL NETWORK WITH BROADCAST:
# You can revert to a single shared socket if desired, but keeping
# per-function sockets is safer and works in all scenarios.

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def get_target_nodes_by_role(role):
    """
    Returns live, trusted devices matching the given role.
    Health >= 0.5 is required for sending messages.
    """
    targets = []
    for device_id, info in network_table.items():
        if info.get("role") == role and info.get("role_trusted") and info.get("health", 1.0) >= 0.5:
            targets.append({"id": device_id, "ip": info["ip"], "name": info.get("name")})
    return targets


def send_to_node(target_name_or_id, payload):
    """
    Sends a message to a single node.
    Tracks state in `pending_ACKS` for retries and ACKs.
    Now accepts: device_id, device_name, OR IP address
    """
    # Create a new socket for this send operation
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Check if target is an IP address first
    ip_pattern = r'^\d+\.\d+\.\d+\.\d+$'
    if re.match(ip_pattern, target_name_or_id):
        # Direct IP send - bypass network table lookup
        target_ip = target_name_or_id

        # Build message
        message_id = str(uuid.uuid4())
        message = {
            "type": "MSG",
            "message_id": message_id,
            "from": NODE_ID,
            "role": DECLARED_ROLE,
            "to": target_ip,  # Store IP as string
            "timestamp": time.time(),
            "payload": payload
        }

        # Send message directly to IP
        sock.sendto(json.dumps(message).encode("utf-8"), (target_ip, LOCAL_PORT))

        # Find device ID from network table if possible (for health tracking)
        target_device_id = None
        for device_id, info in network_table.items():
            if info.get("ip") == target_ip:
                target_device_id = device_id
                break

        # Track in pending ACKs (use IP as target_id if no device found)
        with _pending_lock:
            pending_ACKS[message_id] = {
                "target_id": target_device_id or target_ip,  # Store IP if no device ID
                "target_ip": target_ip,  # Always store IP
                "payload": payload,
                "timestamp": time.time(),
                "retries": 0
            }

        print(f"[SEND] Sent message {message_id} to {target_ip}")
        sock.close()
        return

    # Original device lookup logic (for device_id or name)
    target = None
    target_id = None
    for device_id, info in network_table.items():
        if device_id == target_name_or_id or info.get("name") == target_name_or_id:
            target = info
            target_id = device_id
            break

    if not target or not target_id:
        print(f"[SEND] Node {target_name_or_id} not found")
        sock.close()
        return

    if target.get("status") != "alive":
        print(f"[SEND] Node {target_name_or_id} is not alive")
        sock.close()
        return

    # Build message
    message_id = str(uuid.uuid4())
    message = {
        "type": "MSG",
        "message_id": message_id,
        "from": NODE_ID,
        "role": DECLARED_ROLE,
        "to": target_id,
        "timestamp": time.time(),
        "payload": payload
    }

    # Send message
    sock.sendto(json.dumps(message).encode("utf-8"), (target["ip"], LOCAL_PORT))
    sock.close()

    # Track in pending ACKs
    with _pending_lock:
        pending_ACKS[message_id] = {
            "target_id": target_id,
            "target_ip": target["ip"],  # Store IP for retries
            "payload": payload,
            "timestamp": time.time(),
            "retries": 0
        }

    print(f"[SEND] Sent message {message_id} to {target['name']} ({target['ip']})")


def send_to_role(role, payload):
    """
    Broadcasts a message to all trusted devices with the given role.
    """
    targets = get_target_nodes_by_role(role)
    for node in targets:
        send_to_node(node["id"], payload)


# -----------------------------
# ACK / RETRY HANDLING
# -----------------------------

def handle_incoming_packet(data, addr):
    """
    Handles incoming messages and ACKs.
    Updates device health and acknowledges messages.
    """
    try:
        msg = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return

    msg_type = msg.get("type")
    if msg_type == "MSG":
        # Validate sender
        sender_id = msg.get("from")
        message_id = msg.get("message_id")
        if not sender_id or not message_id:
            return

        # Verify trusted node
        node_info = network_table.get(sender_id)
        if not node_info or not node_info.get("role_trusted"):
            print(f"[RECV] Rejected message from untrusted node {sender_id}")
            return

        # Create socket for sending ACK
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Send ACK back
        ack = {
            "type": "ACK",
            "message_id": message_id,
            "from": NODE_ID,
            "to": sender_id,
            "timestamp": time.time()
        }
        sock.sendto(json.dumps(ack).encode("utf-8"), addr)
        sock.close()

        # Update node health (Layer 1)
        record_success(sender_id)

        # Update service health (Layer 3)
        update_provider_health(sender_id, success=True)

        # Deliver payload to app
        print(f"[RECV] Message from {node_info.get('name', sender_id)}: {msg.get('payload')}")

    elif msg_type == "ACK":
        # Process incoming ACK
        message_id = msg.get("message_id")
        target_id = msg.get("from")  # ACK sender

        with _pending_lock:
            if message_id in pending_ACKS:
                print(f"[ACK] Received for {message_id}")

                # Update node health (Layer 1)
                record_success(target_id)

                # Update service health (Layer 3)
                update_provider_health(target_id, success=True)

                del pending_ACKS[message_id]


def check_ack_timeouts():
    """
    Periodically checks pending messages and retries if necessary.
    Updates device health on timeout/failure.
    """
    now = time.time()
    to_delete = []

    with _pending_lock:
        for msg_id, info in pending_ACKS.items():
            elapsed = now - info["timestamp"]
            if elapsed > ACK_TIMEOUT:
                target_id = info["target_id"]
                target_ip = info.get("target_ip")  # Get stored IP
                info["retries"] += 1
                print(f"[TIMEOUT] ACK not received for {msg_id} (retry {info['retries']})")

                # Penalize device health for missed ACK
                if isinstance(target_id, str) and not target_id.startswith("192.168."):
                    record_failure(target_id)

                update_provider_health(target_id if isinstance(target_id, str) and not target_id.startswith("192.168.") else None, success=False)

                if info["retries"] <= MAX_RETRIES:
                    # Retry sending - use stored IP
                    if target_ip:
                        print(f"[RETRY] Resending message {msg_id} to {target_ip}")
                        # Create socket for retry
                        retry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        retry_sock.sendto(json.dumps({
                            "type": "MSG",
                            "message_id": msg_id,
                            "from": NODE_ID,
                            "role": DECLARED_ROLE,
                            "to": target_id,
                            "timestamp": time.time(),
                            "payload": info["payload"]
                        }).encode("utf-8"), (target_ip, LOCAL_PORT))
                        retry_sock.close()
                        info["timestamp"] = now
                    else:
                        # Fallback to network table lookup
                        target_info = network_table.get(target_id) if isinstance(target_id, str) and not target_id.startswith("192.168.") else None
                        if target_info:
                            print(f"[RETRY] Resending message {msg_id} to {target_info.get('name')}")
                            retry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            retry_sock.sendto(json.dumps({
                                "type": "MSG",
                                "message_id": msg_id,
                                "from": NODE_ID,
                                "role": DECLARED_ROLE,
                                "to": target_id,
                                "timestamp": time.time(),
                                "payload": info["payload"]
                            }).encode("utf-8"), (target_info["ip"], LOCAL_PORT))
                            retry_sock.close()
                            info["timestamp"] = now
                else:
                    # Max retries reached → remove from pending
                    print(f"[FAIL] Max retries reached for {msg_id}")
                    if isinstance(target_id, str) and not target_id.startswith("192.168."):
                        record_failure(target_id)
                    update_provider_health(target_id if isinstance(target_id, str) and not target_id.startswith("192.168.") else None, success=False)
                    to_delete.append(msg_id)

        # Remove failed messages
        for mid in to_delete:
            del pending_ACKS[mid]


# -----------------------------
# PERSISTENCE
# -----------------------------

def save_pending_acks():
    """Save pending messages to disk"""
    with _pending_lock:
        try:
            with open(PENDING_FILE, "w") as f:
                json.dump(pending_ACKS, f, indent=2)
        except Exception as e:
            print(f"[SAVE ERROR] {e}")


def load_pending_acks():
    """Load pending messages from disk on startup"""
    global pending_ACKS
    if not os.path.exists(PENDING_FILE):
        return

    try:
        with open(PENDING_FILE, "r") as f:
            with _pending_lock:
                pending_ACKS = json.load(f)
    except Exception as e:
        print(f"[LOAD ERROR] {e}")


def persistence_loop():
    """Daemon to periodically save pending ACKs"""
    while True:
        save_pending_acks()
        time.sleep(SAVE_INTERVAL)


# -----------------------------
# THREADS
# -----------------------------

def listener_loop():
    """Listen for incoming messages and ACKs"""
    print("[LISTENER DEBUG] Function started")
    try:
        print("[LISTENER DEBUG] Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("[LISTENER DEBUG] Socket created, binding to port 51000...")
        sock.bind(("", LOCAL_PORT))
        print(f"[LISTENER DEBUG] Successfully bound to port {LOCAL_PORT}")
        print("[LISTENER] Started listening for messages...")

        while True:
            # print("[LISTENER DEBUG] Waiting for data...")  # Commented to reduce noise
            data, addr = sock.recvfrom(4096)
            # print(f"[LISTENER DEBUG] Received {len(data)} bytes from {addr}")  # Commented to reduce noise
            handle_incoming_packet(data, addr)
    except Exception as e:
        print(f"[LISTENER ERROR] CRASHED: {e}")
        import traceback
        traceback.print_exc()


def ack_checker_loop():
    """Check for timeouts and retry pending messages"""
    print("[ACK CHECKER] Started monitoring ACKs...")
    while True:
        check_ack_timeouts()
        time.sleep(0.5)  # Twice per second


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    load_pending_acks()

    # Start threads
    threading.Thread(target=listener_loop, daemon=True).start()
    threading.Thread(target=ack_checker_loop, daemon=True).start()
    threading.Thread(target=persistence_loop, daemon=True).start()

    print("[SYSTEM] Messaging system running with persistent state. Press Ctrl+C to exit.")

    # Keep main thread alive
    while True:
        time.sleep(10)