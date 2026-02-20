# 🧪 System Test Results

## 📋 Test Run Information
- **Date:** [2026--DD]
- **Devices Used:** [List device names/IPs]
- **Network:** [WiFi/Ethernet, same subnet?]
- **Python Version:** [3.x]

---

## ✅ PHASE 1: Layer 5 Storage
**File:** `layer_5_storage.py`

**Devices Required:** 1

**Duration:** ~2 minutes

### Expected Results:
```
============================================================
PHASE 1: TESTING LAYER 5 STORAGE
============================================================

[TEST 1.1] Core Storage Engine
  ✓ Created record v1
  ✓ Retrieved record v1
  ✓ Updated record v2
  ✓ Version conflict correctly caught
  ✅ Core Storage Engine PASSED

[TEST 1.2] Device Registry
  ✓ Registered device v1
  ✓ Retrieved device: TestDevice
  ✓ Device exists: True
  ✅ Device Registry PASSED

[TEST 1.3] Network Snapshot Store
  ✓ Saved network snapshot v1
  ✓ Loaded snapshot with 2 devices
  ✅ Network Snapshot Store PASSED

✅ LAYER 5 STORAGE TESTS COMPLETE
```
### Issues Found:
```

| Issue | Cause | Fix |
|-------|-------|-----|
| | | |
| | | |
```

NOTES
```
### Notes:
- Storage works independently of network
- If this fails, EVERYTHING else will fail
- Check: storage_layer.py imports, file permissions

---
```
## ✅ PHASE 2: Layer 1 Discovery
**File:** `layer_1_discovery.py`
**Devices Required:** 2+ (SAME NETWORK)
**Duration:** ~2 minutes

### Expected Results:
```
--- NETWORK STATE ---
ID: 2d35e418-3394-4401-9b3a-9c26990ee9b4 | Name: fedora | IP: 192.168.2.110 | Role: game (Trusted: True) | Status: dead | Health: 1.0, Services: ['games']
Broadcasted discovery announce
[NETWORK] State saved to Layer 5 storage
ID: 33f3bdcb-96a3-49ae-b36b-6d246a880ffa | Name: localhost | IP: 192.168.2.100 | Role: game (Trusted: True) | Status: dead | Health: 1.0, Services: ['games']
ID: 15335d15-f57c-42bb-a45e-4d4a734bd7ba | Name: fedora | IP: 192.168.2.110 | Role: game (Trusted: True) | Status: dead | Health: 1.0, Services: ['games']
ID: 27dc16d4-a71b-4122-9642-23b05145f42f | Name: fedora | IP: 192.168.2.110 | Role: game (Trusted: True) | Status: dead | Health: 1.0, Services: ['games']
ID: 2cffaf91-156c-436d-a8a4-4e53ee5e1f17 | Name: localhost | IP: 192.168.2.100 | Role: game (Trusted: True) | Status: dead | Health: 1.0, Services: ['games']
ID: 4e05e9ac-0766-495e-842e-4342e1e4aab1 | Name: localhost | IP: 192.168.2.100 | Role: game (Trusted: True) | Status: dead | Health: 1.0, Services: ['games']
ID: 968ffa09-e684-40ad-b728-23a2353350ce | Name: localhost | IP: 192.168.2.100 | Role: game (Trusted: True) | Status: alive | Health: 1.0, Services: ['games']
----------------------
```
### Issues Found:
```

| Issue | Cause | Fix |
|-------|-------|-----|
| No devices discovered | Firewall blocking UDP 37020 | Add firewall rule |
| No devices discovered | Wrong network segment | Both devices on same WiFi |
| No devices discovered | Discovery not started | Check main.py or test file |
```
NOTES
```
### Notes:
- **MUST test with 2+ physical devices** (VMs often block broadcast)
- Wait 15 seconds for discovery
- Watch for `Broadcasted discovery announce` messages

### Known False Positives:
- Device sees itself only (not a failure if other device not running)

---
```
## ✅ PHASE 3: Layer 2 Resolver
**File:** `layer_2_resolver.py`
**Devices Required:** 1 (needs Layer 1 running)
**Duration:** ~1 minute

### Expected Results:
```
============================================================
PHASE 3: TESTING LAYER 2 RESOLVER
============================================================

[TEST 3.1] Device Name Resolution
  Resolving: fedora.mtd
  Status: NX
  ✗ Resolution failed

[TEST 3.2] Non-existent Device (NX)
  Resolving: nonexistent-device.mtd
  Status: NX
  ✓ Expected NX: True

[TEST 3.3] Service Resolution
  Resolving: svc.games.mtd
  Status: NX
  ⚠️  No game services discovered

[TEST 3.4] Invalid Name Format
  Resolving: invalid-name-without-dot
  Status: NX
  ✓ Rejected (no .mtd): True

[TEST 3.5] Resolution Cache (TTL 30s)
  First resolution: 1770900241.3513172
  Second resolution: 1770900241.3513172
  ✓ Cache working (same timestamp)

✅ LAYER 2 RESOLVER TESTS COMPLETE
```
### Issues Found:
```

| Issue | Cause | Fix |
|-------|-------|-----|
| NX status for known device | network_table empty | Run Layer 1 test first |
| NX status for known device | Device name mismatch | Check info.get("name") vs hostname |
| CONFLICT status | Duplicate device names | Rename one device |
```

NOTES
```
### Notes:
- Depends entirely on Layer 1's network_table
- If Layer 1 passes but Layer 2 fails → resolver.py has bug

---
```

## ✅ PHASE 4: Layer 3 Services
**File:** `test_layer3_services.py`
**Devices Required:** 1
**Duration:** ~2 minutes

### Expected Results:
```
============================================================
PHASE 4: TESTING LAYER 3 SERVICE REGISTRY
============================================================

[TEST 4.1] Service Registration
[SERVICE REG] TestDevice registered 'chat' on port 6000
[SERVICE REG] TestDevice registered 'games' on port 6000
  Accepted: ['chat', 'games']
  Rejected: [{'service': 'unauthorized', 'reason': "Role 'game' not allowed to offer 'unauthorized'"}]
  ✓ Valid services accepted

[TEST 4.2] Service Discovery
  Chat providers: 1
    - TestDevice at 192.168.1.99:6000 (health: 1.0)

[TEST 4.3] Service Information
[NETWORK] State saved to Layer 5 storage
[NETWORK] State saved to Layer 5 storage
[NETWORK] State saved to Layer 5 storage
^
```

### Issues Found:
```
| Issue | Cause | Fix |
|-------|-------|-----|
| All services rejected | Role policy mismatch | Check ROLE_SERVICE_POLICY |
| No providers found | TTL expired (30s) | Re-announce services |
| Health not updating | Layer 4 not calling update_provider_health | Check message.py integration |
```

NOTES
```
### Notes:
- Test creates fake device in network_table
- 30-second TTL - services expire fast
- Health updates should show +0.05/-0.15 changes
```
## ✅ PHASE 5: Layer 4 Messaging
**File:** `test_layer4_messaging.py`
**Devices Required:** 2+
**Duration:** ~3 minutes

### Expected Results (SENDER):
```

```
### Expected Results (RECEIVER):
```

```
### Issues Found:
````
| Issue | Cause | Fix |
|-------|-------|-----|
| "Node not found" | Device not in network_table | Run Layer 1 test first |
| No ACK received | Firewall blocking UDP 51000 | Add firewall rule |
| "Node is not alive" | Health < 0.5 | Check health scores |
| Timeout on every message | Device offline | Check peer is running |

### Critical Check:
- You MUST see `[ACK] Received for ...` on SENDER
- You MUST see `[RECV] Message from ...` on RECEIVER
- Both are required for messaging to work

---
```