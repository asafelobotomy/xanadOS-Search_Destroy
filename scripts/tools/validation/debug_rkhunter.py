#!/usr/bin/env python3
"""Debug RKHunter functionality step by step to identify what's failing."""

import logging
import os
import sys
import tempfile

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app'))

def setup_debug_logging():
    """Setup detailed logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(tempfile.mktemp(suffix='_rkhunter_debug.log', prefix='secure_'), mode='w')
        ]
    )

def test_rkhunter_step_by_step():
    """Test RKHunter functionality step by step with detailed debugging."""
    print("=" * 60)
    print("RKHunter Debug Test - Step by Step Analysis")
    print("=" * 60)

    setup_debug_logging()
    logger = logging.getLogger("rkhunter_debug")

    try:
        # Step 1: Check if RKHunter is installed
        print("\n1. Checking RKHunter installation...")
        import shutil
        from pathlib import Path

        # Check standard locations first (for root-only executables)
        possible_paths = [
            "/usr/bin/rkhunter",
            "/usr/local/bin/rkhunter",
            "/opt/rkhunter/bin/rkhunter",
        ]

        rkhunter_path = None
        for path in possible_paths:
            if Path(path).exists():
                rkhunter_path = path
                print(f"✓ RKHunter found at: {rkhunter_path}")
                break

        if not rkhunter_path:
            # Try which command as fallback
            rkhunter_path = shutil.which('rkhunter')
            if rkhunter_path:
                print(f"✓ RKHunter found via PATH: {rkhunter_path}")
            else:
                print("❌ RKHunter not found in standard locations or PATH")
                return False

        # Step 2: Import and initialize wrapper
        print("\n2. Importing RKHunter wrapper...")
        from core.rkhunter_wrapper import RKHunterWrapper

        print("\n3. Initializing RKHunter wrapper...")
        wrapper = RKHunterWrapper()
        print("✓ Wrapper initialized")
        print(f"  - Available: {wrapper.available}")
        print(f"  - Path: {wrapper.rkhunter_path}")
        print(f"  - Config path: {wrapper.config_path}")

        # Step 3: Test configuration creation
        print("\n4. Testing configuration creation...")
        wrapper._initialize_config()

        if wrapper.config_path.exists():
            print(f"✓ Configuration file created: {wrapper.config_path}")

            # Read and validate configuration
            with open(wrapper.config_path) as f:
                config_content = f.read()

            print(f"  - Config size: {len(config_content)} characters")

            # Check for problematic patterns
            if '$DISABLE_TESTS' in config_content:
                print("❌ Found problematic shell variable: $DISABLE_TESTS")
                # Show problematic lines
                for i, line in enumerate(config_content.split('\n'), 1):
                    if '$DISABLE_TESTS' in line:
                        print(f"    Line {i}: {line}")
                return False
            else:
                print("✓ No shell variables found in configuration")

            # Show DISABLE_TESTS configuration
            disable_lines = [line for line in config_content.split('\n') if 'DISABLE_TESTS' in line and not line.strip().startswith('#')]
            print(f"  - DISABLE_TESTS lines: {len(disable_lines)}")
            for line in disable_lines:
                print(f"    {line.strip()}")
        else:
            print(f"❌ Configuration file not created at: {wrapper.config_path}")
            return False

        # Step 4: Test basic RKHunter command
        print("\n5. Testing basic RKHunter command...")
        import subprocess
        try:
            # nosec B603 - subprocess call with controlled input

            result = subprocess.run([rkhunter_path, '--version'],
                                   check=False, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✓ RKHunter version check successful")
                print(f"  - Output: {result.stdout.strip()}")
            else:
                print(f"❌ RKHunter version check failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error running RKHunter version: {e}")
            return False

        # Step 5: Test configuration validation
        print("\n6. Testing configuration validation...")
        try:
            # nosec B603 - subprocess call with controlled input

            result = subprocess.run([rkhunter_path, '--configcheck', '--configfile', str(wrapper.config_path)],
                                   check=False, capture_output=True, text=True, timeout=30)
            print(f"  - Config check return code: {result.returncode}")
            if result.stdout:
                print(f"  - Stdout: {result.stdout[:300]}...")
            if result.stderr:
                print(f"  - Stderr: {result.stderr[:300]}...")

            if 'Unknown option name' in result.stderr or 'Unknown disabled test name' in result.stderr:
                print("❌ Configuration validation failed - found unknown options/tests")
                return False
            else:
                print("✓ Configuration appears valid")
        except Exception as e:
            print(f"❌ Error checking configuration: {e}")
            return False

        # Step 6: Test minimal scan
        print("\n7. Testing minimal RKHunter scan...")
        try:
            # Use a very limited scan to test basic functionality
            cmd = [rkhunter_path, '--check', '--sk', '--configfile', str(wrapper.config_path),
                   '--enable', 'system_commands', '--nocolors']
            print(f"  - Command: {' '.join(cmd)}")

            # nosec B603 - subprocess call with controlled input


            result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=120)
            print(f"  - Return code: {result.returncode}")

            if result.stdout:
                print(f"  - Stdout (last 300 chars): ...{result.stdout[-300:]}")
            if result.stderr:
                print(f"  - Stderr: {result.stderr[:300]}...")

            # Check for specific error patterns
            if 'Unknown disabled test name' in result.stderr:
                print("❌ Found 'Unknown disabled test name' error in stderr")
                return False
            elif result.returncode in (0, 1, 2):  # Normal RKHunter return codes
                print("✓ Minimal scan completed successfully")
            else:
                print(f"❌ Scan failed with unexpected return code: {result.returncode}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Scan timed out")
            return False
        except Exception as e:
            print(f"❌ Error running scan: {e}")
            return False

        # Step 7: Test wrapper scan method
        print("\n8. Testing wrapper scan method...")
        try:
            # Capture output for debugging
            output_lines = []
            def debug_callback(line):
                output_lines.append(line)
                if len(output_lines) <= 10:  # Show first 10 lines
                    print(f"    Scan output: {line}")
                elif len(output_lines) == 11:
                    print("    ... (output continues)")

            result = wrapper.scan_system_with_output_callback(
                test_categories=None,
                skip_keypress=True,
                update_database=False,
                output_callback=debug_callback
            )

            print(f"  - Scan ID: {result.scan_id}")
            print(f"  - Success: {result.success}")
            print(f"  - Error: {result.error_message}")
            print(f"  - Summary: {result.scan_summary}")
            print(f"  - Output lines captured: {len(output_lines)}")

            if result.success:
                print("✓ Wrapper scan completed successfully")
            else:
                print(f"❌ Wrapper scan failed: {result.error_message}")
                return False

        except Exception as e:
            print(f"❌ Error in wrapper scan: {e}")
            logger.exception("Wrapper scan exception details:")
            return False

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - RKHunter appears to be working correctly")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        logger.exception("Fatal error details:")
        return False

if __name__ == "__main__":
    success = test_rkhunter_step_by_step()

    print("\nDebug log saved to: /tmp/rkhunter_debug.log")

    if success:
        print("🎉 RKHunter debugging completed successfully!")
        sys.exit(0)
    else:
        print("💥 RKHunter debugging found issues that need to be resolved.")
        sys.exit(1)
