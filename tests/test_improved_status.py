#!/usr/bin/env python3
"""Test script to validate the improved RKHunter database status detection."""

import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_database_detection():
    """Test the improved database version detection."""
    print("🔍 Testing Improved RKHunter Database Detection\n")

    try:
        from app.core.rkhunter_optimizer import RKHunterOptimizer

        print("=== Testing RKHunter Optimizer with Improved Detection ===")
        optimizer = RKHunterOptimizer()

        print(f"✓ RKHunter Available: {optimizer.rkhunter_path is not None}")
        print(f"  Path: {optimizer.rkhunter_path}")

        print("\n--- Testing Individual Methods ---")

        # Test database version detection
        db_version = optimizer._get_database_version()
        print(f"  Database Version: {db_version}")

        # Test mirror status
        mirror_status = optimizer._check_mirror_status()
        print(f"  Mirror Status: {mirror_status}")

        # Test full status with improvements
        print("\n--- Testing Full Status Retrieval ---")
        status = optimizer.get_current_status()
        print(f"  Version: {status.version}")
        print(f"  Config File: {status.config_file}")
        print(f"  Database Version: {status.database_version}")
        print(f"  Last Update: {status.last_update}")
        print(f"  Last Scan: {status.last_scan}")
        print(f"  Baseline Exists: {status.baseline_exists}")
        print(f"  Mirror Status: {status.mirror_status}")
        print(f"  Issues Found: {len(status.issues_found)} issues")

        # Show specific improvements
        print("\n--- Status Improvements Analysis ---")
        improvements = []
        if status.database_version != "Unknown":
            improvements.append("✅ Database version now detected")
        if status.mirror_status not in ["Unknown", "Config inaccessible"]:
            improvements.append("✅ Mirror status now accessible")
        if status.version != "Unknown":
            improvements.append("✅ RKHunter version detection working")

        if improvements:
            for improvement in improvements:
                print(f"  {improvement}")
        else:
            print("  ⚠️ Some status values still showing as Unknown")

        return status

    except Exception as e:
        print(f"❌ Error testing optimizer: {e}")
        import traceback
        traceback.print_exc()
        return None

def direct_database_test():
    """Direct test of database file reading."""
    print("\n=== Direct Database File Testing ===")

    import subprocess

    # Test direct reading of database file
    try:
        result = subprocess.run(
            ["sudo", "head", "-5", "/var/lib/rkhunter/db/rkhunter.dat"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✓ Direct database file access successful:")
            for line in result.stdout.split('\n')[:5]:
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"❌ Database file access failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Direct test failed: {e}")

def main():
    """Main test function."""
    print("🚀 RKHunter Status Detection Improvement Validation\n")

    # Test improved detection
    status = test_database_detection()

    # Direct database test
    direct_database_test()

    print("\n🏁 Testing Complete")

    if status:
        success_count = sum(1 for value in [
            status.version, status.database_version, status.mirror_status
        ] if value != "Unknown")
        print(f"📊 Status Detection Success: {success_count}/3 values resolved")

if __name__ == "__main__":
    main()
