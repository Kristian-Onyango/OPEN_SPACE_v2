#layer 1 
#discovery.py

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
if __name__ == "__main__":
    print("Starting Discovery Protocol v0")
    print(f"Device Name: {DEVICE_NAME}")
    print(f"Device ID: {DEVICE_ID}")
    print(f"Services: {SERVICES}")
    print("-" * 40)

    threading.Thread(target=announce_loop, daemon=True).start()
    threading.Thread(target=listen_loop, daemon=True).start()

    while True:
        print_network_state()
        time.sleep(10)
