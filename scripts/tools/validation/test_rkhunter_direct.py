#!/usr/bin/env python3
"""Simple test to validate RKHunter configuration directly."""

import os
import subprocess
import tempfile
import sys

def test_rkhunter_config_directly():
    """Test RKHunter configuration without Python dependencies."""
    print("=" * 50)
    print("Direct RKHunter Configuration Test")
    print("=" * 50)

    # Check if rkhunter is available
    rkhunter_path = subprocess.run(['which', 'rkhunter'], capture_output=True, text=True)
    if rkhunter_path.returncode != 0:
        print("❌ RKHunter not found in PATH")
        return False

    rkhunter_exe = rkhunter_path.stdout.strip()
    print(f"✓ RKHunter found: {rkhunter_exe}")

    # Create a test configuration with the same DISABLE_TESTS line
    config_content = '''# Test RKHunter configuration
LOGFILE=/tmp/rkhunter-test.log
DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps apps"
SCANROOTKITMODE=THOROUGH
PKGMGR=NONE
'''

    # Write config to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        print(f"✓ Test config created: {config_path}")
        print("Configuration content:")
        print(config_content)

        # Test configuration check
        print("\nTesting configuration validation...")
        result = subprocess.run([
            rkhunter_exe, '--configcheck', '--configfile', config_path
        ], capture_output=True, text=True, timeout=30)

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout:\n{result.stdout}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr}")

        # Check for the specific error
        if 'Unknown disabled test name' in result.stderr:
            print("❌ Found 'Unknown disabled test name' error!")

            # Try to identify which test is problematic
            if 'disable_tests' in result.stderr.lower():
                print("❌ The error is related to $disable_tests variable syntax")

            return False
        elif result.returncode == 0:
            print("✓ Configuration validation passed")
        else:
            print(f"⚠️  Configuration check returned {result.returncode} but no unknown test error")

        # Test a minimal scan
        print("\nTesting minimal scan...")
        result = subprocess.run([
            rkhunter_exe, '--check', '--sk', '--configfile', config_path,
            '--enable', 'system_commands', '--nocolors'
        ], capture_output=True, text=True, timeout=60)

        print(f"Scan return code: {result.returncode}")
        if 'Unknown disabled test name' in result.stderr:
            print("❌ Found 'Unknown disabled test name' error during scan!")
            print("Error details:")
            print(result.stderr)
            return False
        else:
            print("✓ No configuration errors found during scan")

        return True

    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.unlink(config_path)

if __name__ == "__main__":
    success = test_rkhunter_config_directly()
    if success:
        print("\n🎉 Direct configuration test passed!")
    else:
        print("\n💥 Direct configuration test failed!")

    sys.exit(0 if success else 1)
