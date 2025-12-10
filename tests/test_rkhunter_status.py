#!/usr/bin/env python3
"""Test script for RKHunter status functionality"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def test_rkhunter_availability():
    """Test RKHunter binary availability and permissions"""
    print("=== Testing RKHunter Binary Availability ===")

    # Check if binary exists and get permissions
    rkhunter_paths = ["/usr/bin/rkhunter", "/usr/local/bin/rkhunter", "/bin/rkhunter"]

    for path in rkhunter_paths:
        if os.path.exists(path):
            stat_info = os.stat(path)
            permissions = oct(stat_info.st_mode)
            print(f"✓ Found RKHunter at: {path}")
            print(f"  Permissions: {permissions}")
            print(f"  Owner: uid={stat_info.st_uid}, gid={stat_info.st_gid}")
            return path

    print("✗ RKHunter binary not found")
    return None


def test_rkhunter_optimizer():
    """Test RKHunter optimizer status retrieval."""
    print("\n=== Testing RKHunter Optimizer Status ===")

    try:
        from app.core.unified_rkhunter_integration import RKHunterOptimizer

        optimizer = RKHunterOptimizer()
        print("✓ RKHunter Optimizer initialized")
        print(f"  Available: {optimizer.rkhunter_available}")
        print(f"  Path: {optimizer.rkhunter_path}")

        # Test status retrieval
        print("\n--- Testing Status Retrieval ---")
        status = optimizer.get_current_status()

        print(f"  Version: {status.version}")
        print(f"  Config File: {status.config_file}")
        print(f"  Database Version: {status.database_version}")
        print(f"  Last Update: {status.last_update}")
        print(f"  Last Scan: {status.last_scan}")
        print(f"  Baseline Exists: {status.baseline_exists}")
        print(f"  Mirror Status: {status.mirror_status}")
        print(f"  Issues Found: {len(status.issues_found)} issues")

        return True

    except Exception as e:
        print(f"✗ Error testing optimizer: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_non_invasive_monitor():
    """Test non-invasive RKHunter monitoring."""
    print("\n=== Testing Non-Invasive Monitor ===")

    try:
        from app.core.unified_rkhunter_integration import UnifiedRKHunterMonitor
        # RKHunterMonitorNonInvasive is now UnifiedRKHunterMonitor

        monitor = RKHunterMonitorNonInvasive()
        print("✓ Non-invasive monitor initialized")

        # Test availability check
        available = monitor._check_rkhunter_availability()
        print(f"  RKHunter Available: {available}")

        # Test status collection
        status = monitor.get_status_non_invasive()
        print("\n--- Non-Invasive Status ---")
        print(f"  Available: {status.available}")
        print(f"  Version: {status.version}")
        print(f"  Config Exists: {status.config_exists}")
        print(f"  Config Readable: {status.config_readable}")
        print(f"  Database Exists: {status.database_exists}")
        print(f"  Last Scan Attempt: {status.last_scan_attempt}")
        print(f"  Installation Method: {status.installation_method}")
        print(f"  Issues Found: {len(status.issues_found)} issues")

        return True

    except Exception as e:
        print(f"✗ Error testing monitor: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_secure_subprocess():
    """Test secure subprocess functionality"""
    print("\n=== Testing Secure Subprocess ===")

    try:
        from app.core.secure_subprocess import run_secure

        # Test a simple command that should work
        result = run_secure(["which", "rkhunter"], check=False, capture_output=True)
        print("✓ Secure subprocess test completed")
        print(f"  Return code: {result.returncode}")
        print(f"  Output: {result.stdout.decode().strip() if result.stdout else 'None'}")

        return True

    except Exception as e:
        print(f"✗ Error testing secure subprocess: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🔍 RKHunter Status Investigation\n")

    # Test 1: Binary availability
    rkhunter_path = test_rkhunter_availability()

    # Test 2: Secure subprocess
    test_secure_subprocess()

    # Test 3: Non-invasive monitor
    test_non_invasive_monitor()

    # Test 4: RKHunter optimizer
    test_rkhunter_optimizer()

    print("\n🏁 Investigation Complete")


if __name__ == "__main__":
    main()
