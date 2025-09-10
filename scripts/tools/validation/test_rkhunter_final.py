#!/usr/bin/env python3
"""Final comprehensive test of RKHunter functionality after fixes."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "app"))

import logging
import subprocess

from core.rkhunter_wrapper import RKHunterWrapper


def test_rkhunter_comprehensive():
    """Comprehensive test of RKHunter functionality."""
    print("=" * 60)
    print("🔍 RKHunter Comprehensive Functionality Test")
    print("=" * 60)

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Test 1: Wrapper initialization
    print("\n1. Testing wrapper initialization...")
    wrapper = RKHunterWrapper()
    print(f"   ✓ Available: {wrapper.available}")
    print(f"   ✓ Path: {wrapper.rkhunter_path}")
    print(f"   ✓ Config path: {wrapper.config_path}")

    if not wrapper.available:
        print("   ❌ RKHunter not available - aborting tests")
        return False

    # Test 2: Functionality check
    print("\n2. Testing functionality...")
    functional = wrapper.is_functional()
    print(f"   ✓ Functional: {functional}")

    if not functional:
        print("   ❌ RKHunter not functional - aborting tests")
        return False

    # Test 3: Configuration generation
    print("\n3. Testing configuration generation...")

    # Remove old config to force regeneration
    if wrapper.config_path.exists():
        wrapper.config_path.unlink()
        print("   ✓ Removed old configuration")

    wrapper._initialize_config()

    if wrapper.config_path.exists():
        print("   ✓ Configuration file created")

        # Read and validate configuration
        with open(wrapper.config_path) as f:
            config_content = f.read()

        # Check for shell variables
        shell_vars = [
            line.strip()
            for line in config_content.split("\n")
            if "$" in line and not line.strip().startswith("#")
        ]
        if shell_vars:
            print(f"   ❌ Found shell variables: {shell_vars}")
            return False
        else:
            print("   ✓ No shell variables found")

        # Check DISABLE_TESTS configuration
        disable_lines = [
            line.strip()
            for line in config_content.split("\n")
            if "DISABLE_TESTS" in line and not line.strip().startswith("#")
        ]
        print(f"   ✓ DISABLE_TESTS lines: {len(disable_lines)}")
        if len(disable_lines) == 1:
            print(f"   ✓ Single DISABLE_TESTS line: {disable_lines[0]}")
        else:
            print(f"   ❌ Expected 1 DISABLE_TESTS line, found {len(disable_lines)}")
            return False
    else:
        print("   ❌ Configuration file not created")
        return False

    # Test 4: Configuration validation with RKHunter
    print("\n4. Testing configuration validation...")
    try:
        # nosec B603 - subprocess call with controlled input

        result = subprocess.run(
            [
                "/usr/bin/sudo",
                "/usr/bin/rkhunter",
                "--configcheck",
                "--configfile",
                str(wrapper.config_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if "Unknown" in result.stderr or "Error" in result.stderr:
            print("   ⚠️  Configuration warnings:")
            for line in result.stderr.split("\n"):
                if "Unknown" in line or "Error" in line:
                    print(f"      {line}")
        else:
            print("   ✓ Configuration validation passed")
    except Exception as e:
        print(f"   ⚠️  Could not validate configuration: {e}")

    # Test 5: Minimal scan test
    print("\n5. Testing minimal scan...")
    try:
        scan_output = []

        def output_callback(line):
            scan_output.append(line)

        result = wrapper.scan_system_with_output_callback(
            test_categories=None,
            skip_keypress=True,
            update_database=False,
            output_callback=output_callback,
        )

        print("   ✓ Scan completed")
        print(f"   ✓ Success: {result.success}")
        print(f"   ✓ Summary: {result.scan_summary}")
        print(f"   ✓ Output lines: {len(scan_output)}")

        if result.error_message:
            print(f"   ⚠️  Error message: {result.error_message}")

        # Check for the original error
        error_found = False
        for line in scan_output:
            if "Unknown disabled test name" in line and "$disable_tests" in line:
                print(f"   ❌ Original error still present: {line}")
                error_found = True
                break

        if not error_found:
            print("   ✓ Original '$disable_tests' error resolved")

        return result.success and not error_found

    except Exception as e:
        print(f"   ❌ Scan test failed: {e}")
        return False


def main():
    """Main test function."""
    try:
        success = test_rkhunter_comprehensive()

        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL TESTS PASSED - RKHunter is working correctly!")
            print("✓ Configuration issue resolved")
            print("✓ Scans execute without errors")
            print("✓ No shell variable syntax problems")
        else:
            print("💥 SOME TESTS FAILED - Issues still need resolution")
        print("=" * 60)

        return 0 if success else 1

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
