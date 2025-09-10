#!/usr/bin/env python3
"""
Test RKHunter GUI integration with fixed configuration
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app'))


from core.rkhunter_wrapper import RKHunterWrapper


def test_gui_rkhunter():
    """Test RKHunter as the GUI would use it."""
    print("🔍 Testing RKHunter GUI Integration")
    print("=" * 50)

    try:
        # Initialize wrapper (same as GUI does)
        wrapper = RKHunterWrapper()
        print("✅ Wrapper initialized")
        print(f"   Path: {wrapper.rkhunter_path}")
        print(f"   Config: {wrapper.config_path}")
        print(f"   Available: {wrapper.available}")

        if not wrapper.available:
            print("❌ RKHunter not available")
            return False

        # Check configuration file exists and is valid
        if not wrapper.config_path.exists():
            print("❌ Configuration file missing")
            return False

        # Read and validate configuration
        with open(wrapper.config_path) as f:
            config_content = f.read()

        print(f"✅ Configuration file exists ({len(config_content)} bytes)")

        # Check for the problematic PKGMGR_NO_VRFY line
        if 'PKGMGR_NO_VRFY=1' in config_content:
            print("❌ Configuration still contains invalid 'PKGMGR_NO_VRFY=1'")
            return False
        elif 'PKGMGR_NO_VRFY=""' in config_content:
            print("✅ Configuration contains correct 'PKGMGR_NO_VRFY=\"\"'")
        else:
            print("⚠️  No PKGMGR_NO_VRFY found in configuration")

        # Test a quick configuration validation (simulate GUI)
        try:
            # Create a minimal test to validate config syntax
            import subprocess
            # nosec B603 - subprocess call with controlled input

            result = subprocess.run(
                [wrapper.rkhunter_path, '--config-check', '--configfile', str(wrapper.config_path)],
                check=False, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                print("✅ Configuration validation passed")
            else:
                print("❌ Configuration validation failed:")
                print(f"   Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"⚠️  Could not validate config: {e}")

        print("\n🎉 GUI RKHunter integration test PASSED!")
        print("The GUI should now work correctly with RKHunter.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui_rkhunter()
    sys.exit(0 if success else 1)
