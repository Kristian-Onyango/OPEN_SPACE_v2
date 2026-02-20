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