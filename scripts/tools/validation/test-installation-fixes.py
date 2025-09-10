#!/usr/bin/env python3
"""
Test script to validate UFW and ClamAV installation fixes
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.core.clamav_wrapper import ClamAVWrapper
    from app.core.elevated_runner import elevated_run
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running from the project root")
    sys.exit(1)


def test_ufw_installation():
    """Test UFW installation using the new simplified command."""
    print("🧪 Testing UFW installation...")

    # Test the new simplified command format
    cmd = ["pacman", "-S", "--noconfirm", "ufw"]

    try:
        print(f"   Running: {' '.join(cmd)}")
        result = elevated_run(
            cmd, timeout=300, capture_output=True, text=True, gui=True
        )

        if result.returncode == 0:
            print("✅ UFW installation successful")

            # Test UFW enable command
            print("   Testing UFW enable...")
            enable_result = elevated_run(
                ["ufw", "--force", "enable"],
                timeout=60,
                capture_output=True,
                text=True,
                gui=True,
            )

            if enable_result.returncode == 0:
                print("✅ UFW enabled successfully")
                return True
            else:
                print(f"❌ UFW enable failed: {enable_result.stderr}")
                return False
        else:
            print(f"❌ UFW installation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error during UFW installation: {e}")
        return False


def test_clamav_daemon_startup():
    """Test ClamAV daemon startup using the improved logic."""
    print("🧪 Testing ClamAV daemon startup...")

    try:
        wrapper = ClamAVWrapper()

        # Check initial daemon state
        if wrapper._is_clamd_running():
            print("   ClamAV daemon already running")
            return True

        print("   Starting ClamAV daemon...")
        success = wrapper.start_daemon()

        if success:
            print("✅ ClamAV daemon started successfully")

            # Test daemon connectivity
            print("   Testing daemon connectivity...")
            time.sleep(2)  # Give daemon time to initialize

            if wrapper._is_clamd_running():
                print("✅ ClamAV daemon is responding")
                return True
            else:
                print("❌ ClamAV daemon not responding")
                return False
        else:
            print("❌ Failed to start ClamAV daemon")
            return False

    except Exception as e:
        print(f"❌ Error during ClamAV daemon testing: {e}")
        return False


def main():
    """Run all tests."""
    print("🔧 UFW and ClamAV Installation/Startup Test")
    print("=" * 50)

    tests_passed = 0
    total_tests = 2

    # Test 1: UFW Installation
    if test_ufw_installation():
        tests_passed += 1

    print()

    # Test 2: ClamAV Daemon Startup
    if test_clamav_daemon_startup():
        tests_passed += 1

    print()
    print("📊 Test Results")
    print("=" * 20)
    print(f"Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All tests passed! The fixes are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
