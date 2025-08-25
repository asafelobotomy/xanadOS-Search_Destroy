#!/usr/bin/env python3
"""
Debug script to test firewall functionality comprehensively
"""
from core.firewall_detector import get_firewall_status, toggle_firewall

import os

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

def main():
    print("=== COMPREHENSIVE FIREWALL DEBUG ===\n")

    # 1. Environment check
    print("1. ENVIRONMENT VARIABLES:")
    env_vars = ["DISPLAY", "XAUTHORITY", "XDG_SESSION_TYPE", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY"]
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"   {var}: {value}")
    print()

    # 2. Command availability
    print("2. COMMAND AVAILABILITY:")
    import shutil

    commands = ["pkexec", "sudo", "ufw", "firewall-cmd", "iptables", "nft"]
    for cmd in commands:
        available = shutil.which(cmd) is not None
        print(f"   {cmd}: {'✅ Available' if available else '❌ Not found'}")
    print()

    # 3. Current firewall status
    print("3. CURRENT FIREWALL STATUS:")
    try:
        status = get_firewall_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   ❌ Error getting status: {e}")
    print()

    # 4. Test firewall toggle (dry run with debug)
    print("4. TESTING FIREWALL TOGGLE (ENABLE):")
    try:
        # Get current status first
        current_status = get_firewall_status()
        is_active = current_status.get("is_active", False)

        print(f"   Current firewall state: {'ACTIVE' if is_active else 'INACTIVE'}")
        print(f"   Will attempt to: {'DISABLE' if is_active else 'ENABLE'}")

        # Attempt toggle
        result = toggle_firewall(not is_active)
        print(f"   Toggle result:")
        for key, value in result.items():
            print(f"     {key}: {value}")

    except Exception as e:
        print(f"   ❌ Error during toggle: {e}")
        import traceback

        traceback.print_exc()
    print()

    # 5. Final status check
    print("5. FINAL FIREWALL STATUS:")
    try:
        status = get_firewall_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   ❌ Error getting final status: {e}")

if __name__ == "__main__":
    main()
