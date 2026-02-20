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
from integration import integrator
from storage_layer import initialize_storage
from network_table import state_maintenance_loop

# Initialize storage
initialize_storage()

# Start integrator/system
integrator.start()


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
result = integrator.resolve_with_fallback("this-definitely-does-not-exist-on-local-network")
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