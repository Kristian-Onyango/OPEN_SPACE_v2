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