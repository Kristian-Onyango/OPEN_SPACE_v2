"""
Main Entry Point - Local-First Internet Substrate
=================================================
Starts the entire system using the integration layer.
"""

import sys
import time
from integration import start_system, integrator
from network_table import print_network_state

print("🔥 MAIN.PY STARTED - LINE 1")
print(f"🔥 Python version: {sys.version}")

def main():
    """
    Main system startup sequence.
    """
    print("=" * 60)
    print("Local-First Internet Substrate")
    print("=" * 60)

    # Phase 1: Start system integration (all threads now handled internally)
    print("[BOOT] Starting system integration and background services...")
    start_system()

    # Give threads a moment to initialize
    time.sleep(2)

    # Show active threads
    print("\n" + "=" * 60)
    import threading
    print(f"[MAIN] ACTIVE THREADS: {threading.active_count()}")
    print("=" * 60)
    for i, thread in enumerate(threading.enumerate()):
        print(f"  {i + 1}. {thread.name} (daemon: {thread.daemon}) - alive: {thread.is_alive()}")
    print("=" * 60 + "\n")

    print("[BOOT] All services started")
    print("[BOOT] System is now operational")
    print("=" * 60)

    # Main loop: print network state and health periodically
    try:
        counter = 0
        while True:
            # Print network state every 30 seconds
            if counter % 3 == 0:
                print_network_state()

            # Print system health every 60 seconds
            if counter % 6 == 0:
                health = integrator.health_check()
                print(f"[HEALTH] Status: {health['status']}, "
                      f"Devices: {health['metrics']['healthy_devices']}/{health['metrics']['total_devices']}")

            counter += 1
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Graceful shutdown initiated...")
        integrator.stop()
        print("[SHUTDOWN] System stopped")

if __name__ == "__main__":
    main()
