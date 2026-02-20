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
