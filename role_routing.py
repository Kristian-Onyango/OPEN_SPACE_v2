"""
Layer 2 - Role Based Routing
============================

This module allows messages to be sent ONLY to nodes
that match a specific role (game, chat, cache, etc).

It relies entirely on:
- The Network Table from Layer 1
- The messaging primitive from Layer 4 (reliable messaging)

This file does NOT start threads.
It is called by higher-level application logic.

IMPORTANT: This is a convenience wrapper around Layer 4 messaging
that adds role-based filtering. All messages go through Layer 4
for reliability (ACKs, retries, health tracking).
"""

import time
from typing import List, Dict, Any
from message import send_to_node  # Use Layer 4's reliable messaging

# -----------------------------
# ROLE-BASED ROUTING (LAYER 2 WRAPPER)
# -----------------------------

def send_to_role_via_routing(role: str, message_type: str, content: Any, sender_name: str) -> Dict[str, Any]:
    """
    Sends a message to ALL alive and healthy nodes with a specific role.

    Parameters:
    - role        : target role (e.g. "game", "chat", "cache", "storage")
    - message_type: logical message category (e.g. "GAME_STATE", "CHAT_MESSAGE")
    - content     : actual payload (string or dict)
    - sender_name : human-readable sender identity

    This function:
    - Iterates over the Network Table (imported from message.py)
    - Filters by role, alive status, AND health threshold (>= 0.5)
    - Uses Layer 4's reliable messaging (ACKs, retries, health tracking)
    - Returns summary of sent messages

    Returns:
        {
            "sent_count": int,
            "failed_count": int,
            "target_nodes": List[str],
            "failed_nodes": List[str]
        }
    """
    from message import network_table  # Import the actual network table

    results = {
        "sent_count": 0,
        "failed_count": 0,
        "target_nodes": [],
        "failed_nodes": []
    }

    for device_id, info in network_table.items():
        # Skip dead or unhealthy nodes
        if info.get("status") != "alive":
            continue

        # Skip nodes with low health (same threshold as messaging layer)
        if info.get("health", 1.0) < 0.5:
            continue

        # Skip nodes that do not match role
        if info.get("role") != role:
            continue

        # Skip untrusted roles
        if not info.get("role_trusted", False):
            continue

        # Prepare payload for Layer 4 messaging
        payload = {
            "protocol_layer": 2,
            "routing_type": "role_based",
            "message_type": message_type,
            "from_name": sender_name,
            "to_role": role,
            "original_timestamp": time.time(),
            "content": content
        }

        try:
            # Use Layer 4's reliable messaging system
            # This gives us ACKs, retries, and health tracking automatically
            send_to_node(device_id, payload)

            results["sent_count"] += 1
            results["target_nodes"].append({
                "device_id": device_id,
                "name": info.get("name", "unknown"),
                "ip": info["ip"]
            })

        except Exception as e:
            print(f"[ROLE ROUTING] Failed to send to {info.get('name', device_id[:8])}: {e}")
            results["failed_count"] += 1
            results["failed_nodes"].append({
                "device_id": device_id,
                "name": info.get("name", "unknown"),
                "error": str(e)
            })

    print(f"[ROLE ROUTING] Sent '{message_type}' to {results['sent_count']} '{role}' nodes "
          f"({results['failed_count']} failed)")

    return results


def get_role_members(role: str, require_alive: bool = True, min_health: float = 0.5) -> List[Dict[str, Any]]:
    """
    Get all nodes with a specific role (for application use).

    Parameters:
    - role: Target role to filter by
    - require_alive: If True, only return nodes with status="alive"
    - min_health: Minimum health score required (0.0 to 1.0)

    Returns:
    List of node information dictionaries
    """
    from message import network_table

    members = []

    for device_id, info in network_table.items():
        if require_alive and info.get("status") != "alive":
            continue

        if info.get("health", 1.0) < min_health:
            continue

        if info.get("role") != role:
            continue

        if not info.get("role_trusted", False):
            continue

        members.append({
            "device_id": device_id,
            "name": info.get("name", "unknown"),
            "ip": info["ip"],
            "role": info.get("role"),
            "health": info.get("health", 1.0),
            "status": info.get("status"),
            "last_seen": info.get("last_seen", 0)
        })

    return members


def broadcast_to_all_roles(message_type: str, content: Any, sender_name: str,
                          excluded_roles: List[str] = None) -> Dict[str, Any]:
    """
    Send a message to nodes of ALL roles (except excluded ones).

    Useful for system announcements, maintenance, etc.
    """
    from message import network_table
    from allowed_roles import ALLOWED_ROLES

    excluded_roles = excluded_roles or []
    results = {}

    for role in ALLOWED_ROLES:
        if role == "unknown" or role in excluded_roles:
            continue

        results[role] = send_to_role_via_routing(
            role=role,
            message_type=message_type,
            content=content,
            sender_name=sender_name
        )

    total_sent = sum(r["sent_count"] for r in results.values())
    total_failed = sum(r["failed_count"] for r in results.values())

    print(f"[BROADCAST] Sent to {total_sent} total nodes across {len(results)} roles "
          f"({total_failed} total failures)")

    return {
        "total_sent": total_sent,
        "total_failed": total_failed,
        "by_role": results
    }