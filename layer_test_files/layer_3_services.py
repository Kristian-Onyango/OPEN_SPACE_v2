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