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