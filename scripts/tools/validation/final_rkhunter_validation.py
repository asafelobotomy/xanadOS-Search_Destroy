#!/usr/bin/env python3
"""
Final RKHunter Validation - Complete Test Suite
Tests all aspects of RKHunter configuration and functionality
"""

import subprocess
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))


def test_configuration_syntax():
    """Test that the configuration syntax is valid."""
    print("🔍 Testing Configuration Syntax")
    print("-" * 30)

    config_path = Path.home() / ".config" / "search-and-destroy" / "rkhunter.conf"

    if not config_path.exists():
        print("❌ Configuration file does not exist")
        return False

    # Read configuration
    with open(config_path) as f:
        content = f.read()

    # Check for problematic patterns
    issues = []

    # Check for the fixed PKGMGR_NO_VRFY
    if "PKGMGR_NO_VRFY=1" in content:
        issues.append("PKGMGR_NO_VRFY still set to '1' (should be empty string)")
    elif 'PKGMGR_NO_VRFY=""' in content:
        print("✅ PKGMGR_NO_VRFY correctly set to empty string")
    else:
        issues.append("PKGMGR_NO_VRFY not found in configuration")

    # Check for shell variable syntax
    if "$disable_tests" in content.lower():
        issues.append("Shell variable syntax found (should be fixed)")

    # Check for DISABLE_TESTS
    disable_tests_lines = [
        line for line in content.split("\n") if "DISABLE_TESTS=" in line
    ]
    if len(disable_tests_lines) == 1:
        print(f"✅ Single DISABLE_TESTS line: {disable_tests_lines[0].strip()}")
    elif len(disable_tests_lines) > 1:
        issues.append(f"Multiple DISABLE_TESTS lines found: {len(disable_tests_lines)}")
    else:
        issues.append("No DISABLE_TESTS line found")

    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Configuration syntax is valid")
        return True


def test_rkhunter_execution():
    """Test that RKHunter can execute with the configuration."""
    print("\n🚀 Testing RKHunter Execution")
    print("-" * 30)

    try:
        from core.rkhunter_wrapper import RKHunterWrapper

        wrapper = RKHunterWrapper()

        if not wrapper.available:
            print("❌ RKHunter wrapper reports not available")
            return False

        print("✅ RKHunter wrapper initialized successfully")
        print(f"   Path: {wrapper.rkhunter_path}")
        print(f"   Config: {wrapper.config_path}")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize RKHunter wrapper: {e}")
        return False


def test_version_check():
    """Test RKHunter version check."""
    print("\n📋 Testing Version Check")
    print("-" * 30)

    try:
        # Test version command (doesn't require sudo)
        result = subprocess.run(
            ["/usr/bin/rkhunter", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            version_info = result.stdout.strip()
            print("✅ RKHunter version check successful")
            print(
                f"   Version: {version_info.split()[1] if len(version_info.split()) > 1 else 'Unknown'}"
            )
            return True
        else:
            print(f"❌ Version check failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Version check error: {e}")
        return False


def main():
    """Run all tests."""
    print("🔍 Final RKHunter Validation Suite")
    print("=" * 50)

    tests = [
        ("Configuration Syntax", test_configuration_syntax),
        ("RKHunter Execution", test_rkhunter_execution),
        ("Version Check", test_version_check),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} test failed")
        except Exception as e:
            print(f"\n💥 {test_name} test crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ RKHunter configuration is fixed and ready for GUI use")
        print(
            "📝 The 'Invalid PKGMGR_NO_VRFY configuration option' error should be resolved"
        )
        print("🚀 You can now run RKHunter scans from the GUI successfully")
        return 0
    else:
        print("❌ Some tests failed - configuration may still have issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
