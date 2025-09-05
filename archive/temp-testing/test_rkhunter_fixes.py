#!/usr/bin/env python3
"""Test script to verify RKHunter status display fixes"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_status_fixes():
    """Test the fixed RKHunter status retrieval"""
    try:
        from app.core.rkhunter_optimizer import RKHunterOptimizer

        print("🔧 Testing RKHunter Status Display Fixes")
        print("=" * 50)

        # Initialize optimizer
        optimizer = RKHunterOptimizer()

        print("1. Testing RKHunter availability...")
        available = optimizer._ensure_rkhunter_available()
        print(f"   ✅ Available: {available}")

        if not available:
            print("   ❌ RKHunter not available - skipping detailed tests")
            return False

        print("\n2. Getting comprehensive status with fixes...")
        status = optimizer.get_current_status()

        print("\n🔍 Status Results:")
        print(f"   Version: {status.version}")
        print(f"   Database Version: {status.database_version}")
        print(f"   Config File: {status.config_file}")
        print(f"   Last Update: {status.last_update}")
        print(f"   Last Scan: {status.last_scan}")
        print(f"   Baseline Exists: {status.baseline_exists}")
        print(f"   Mirror Status: {status.mirror_status}")
        print(f"   Issues Found: {len(status.issues_found)}")

        if status.issues_found:
            print("   Issues Details:")
            for issue in status.issues_found[:3]:  # Show first 3 issues
                print(f"     • {issue}")
            if len(status.issues_found) > 3:
                print(f"     ... and {len(status.issues_found) - 3} more")

        print("\n🎯 Fix Verification:")

        # Check if "Unknown" values have been improved
        unknown_count = 0
        if status.version == "Unknown":
            unknown_count += 1
            print("   ❌ Version still shows 'Unknown'")
        else:
            print(f"   ✅ Version: {status.version}")

        if status.database_version == "Unknown":
            unknown_count += 1
            print("   ❌ Database version still shows 'Unknown'")
        else:
            print(f"   ✅ Database version: {status.database_version}")

        if status.mirror_status == "Config inaccessible":
            unknown_count += 1
            print("   ❌ Mirror status still shows 'Config inaccessible'")
        else:
            print(f"   ✅ Mirror status: {status.mirror_status}")

        print(f"\n📊 Summary: {3 - unknown_count}/3 status values improved")

        if unknown_count == 0:
            print("🎉 All status values successfully resolved!")
            return True
        else:
            print(f"⚠️  {unknown_count} values still need improvement")
            return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting RKHunter status fixes test...\n")
    success = test_status_fixes()
    print(f"\n{'🎉 Tests completed successfully!' if success else '⚠️ Some issues remain'}")
