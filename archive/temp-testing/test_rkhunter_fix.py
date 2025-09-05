#!/usr/bin/env python3
"""Test script to verify RKHunter status fixes"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_rkhunter_status():
    """Test RKHunter status retrieval"""
    try:
        from app.core.rkhunter_optimizer import RKHunterOptimizer

        print("=== Testing RKHunter Status Fixes ===")
        print()

        # Initialize optimizer
        optimizer = RKHunterOptimizer()

        print("1. Testing RKHunter availability...")
        available = optimizer._ensure_rkhunter_available()
        print(f"   Available: {available}")
        print()

        print("2. Getting current status...")
        status = optimizer.get_current_status()

        print("   Results:")
        print(f"   - Version: {status.version}")
        print(f"   - Database Version: {status.database_version}")
        print(f"   - Last Update: {status.last_update}")
        print(f"   - Last Scan: {status.last_scan}")
        print(f"   - Baseline Exists: {status.baseline_exists}")
        print(f"   - Mirror Status: {status.mirror_status}")
        print(f"   - Issues Found: {len(status.issues_found)}")

        if status.issues_found:
            print("   - Issues Details:")
            for issue in status.issues_found:
                print(f"     * {issue}")

        print()
        print("=== Test Results Summary ===")
        success_count = 0
        total_checks = 0

        # Check if we resolved "Unknown" values
        checks = [
            ("Version", status.version, status.version not in ["Unknown", "Not Available"]),
            ("Database Version", status.database_version, status.database_version not in ["Unknown", "Not Available"]),
            ("Mirror Status", status.mirror_status, status.mirror_status not in ["Unknown", "RKHunter not installed"])
        ]

        for name, value, is_success in checks:
            total_checks += 1
            if is_success:
                success_count += 1
                print(f"✅ {name}: {value}")
            else:
                print(f"❌ {name}: {value}")

        print()
        print(f"Success Rate: {success_count}/{total_checks} ({(success_count/total_checks)*100:.1f}%)")

        if success_count == total_checks:
            print("🎉 All checks passed! RKHunter status is working correctly.")
        elif success_count > 0:
            print("⚠️  Partial success. Some status values are still showing Unknown.")
        else:
            print("❌ All checks failed. RKHunter status is not working.")

        return success_count == total_checks

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rkhunter_status()
    sys.exit(0 if success else 1)
