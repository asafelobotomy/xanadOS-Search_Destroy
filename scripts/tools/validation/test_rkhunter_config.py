#!/usr/bin/env python3
"""Test RKHunter configuration generation to ensure no shell variable syntax issues."""

import sys
import os
import tempfile
import re

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app'))

from core.rkhunter_wrapper import RKHunterWrapper

def test_rkhunter_config():
    """Test that RKHunter configuration generates without shell variable syntax errors."""
    print("=== Testing RKHunter Configuration Generation ===")

    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as tmp_file:
        config_path = tmp_file.name

    try:
        # Initialize RKHunter wrapper
        rkhunter = RKHunterWrapper()

        # Generate configuration
        print("Generating RKHunter configuration...")
        rkhunter._initialize_config()

        # Read the generated configuration
        if os.path.exists(rkhunter.config_file):
            with open(rkhunter.config_file, 'r') as f:
                config_content = f.read()

            print("✓ Configuration generated successfully")

            # Check for problematic shell variable syntax
            shell_vars = re.findall(r'\$\w+', config_content)
            if shell_vars:
                print(f"❌ Found shell variables in configuration: {shell_vars}")
                return False
            else:
                print("✓ No shell variable syntax found")

            # Check DISABLE_TESTS line specifically
            disable_tests_lines = [line for line in config_content.split('\n') if 'DISABLE_TESTS' in line]
            if len(disable_tests_lines) == 1:
                print(f"✓ Single DISABLE_TESTS line: {disable_tests_lines[0].strip()}")
            else:
                print(f"❌ Multiple or missing DISABLE_TESTS lines: {len(disable_tests_lines)}")
                for line in disable_tests_lines:
                    print(f"   {line.strip()}")
                return False

            print("✓ RKHunter configuration is valid")
            return True

        else:
            print("❌ Configuration file was not created")
            return False

    except Exception as e:
        print(f"❌ Error testing RKHunter configuration: {e}")
        return False

    finally:
        # Clean up temporary file
        if os.path.exists(config_path):
            os.unlink(config_path)

if __name__ == "__main__":
    success = test_rkhunter_config()
    sys.exit(0 if success else 1)
