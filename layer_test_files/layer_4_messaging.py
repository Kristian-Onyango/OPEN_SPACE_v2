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
if os.path.exists("../pending_acks.json"):
    with open("../pending_acks.json", "r") as f:
        pending = json.load(f)
    print(f"  pending_acks.json: {len(pending)} pending messages")
    print("  ✓ Persistence file exists")
else:
    print("  ⚠️  pending_acks.json not found (normal if no pending)")

print("\n✅ LAYER 4 MESSAGING TESTS COMPLETE")
print("Check other device console for received messages and ACKs!")