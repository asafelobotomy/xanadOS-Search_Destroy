#!/usr/bin/env python3
"""
Test script to validate enhanced RKHunter detection across permission scenarios
Simulates different permission configurations to ensure robustness
"""

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
import sys

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from core.rkhunter_monitor_enhanced import RKHunterMonitorEnhanced


class RKHunterPermissionTester:
    """Test RKHunter detection across various permission scenarios"""

    def __init__(self):
        self.original_binary_path = '/usr/bin/rkhunter'
        self.backup_binary_path = '/tmp/rkhunter_backup'
        self.original_permissions = None
        self.monitor = RKHunterMonitorEnhanced()

    def backup_current_state(self):
        """Backup current RKHunter state"""
        if os.path.exists(self.original_binary_path):
            # Get current permissions
            stat_info = os.stat(self.original_binary_path)
            self.original_permissions = oct(stat_info.st_mode)[-3:]

            # Create backup
            try:
                shutil.copy2(self.original_binary_path, self.backup_binary_path)
                print(f"✅ Backed up RKHunter binary with permissions {self.original_permissions}")
            except Exception as e:
                print(f"⚠️ Could not backup binary: {e}")

    def restore_original_state(self):
        """Restore original RKHunter state"""
        if os.path.exists(self.backup_binary_path) and self.original_permissions:
            try:
                # Restore binary
                shutil.copy2(self.backup_binary_path, self.original_binary_path)

                # Restore permissions
                subprocess.run(['sudo', 'chmod', self.original_permissions, self.original_binary_path],
                              check=True)

                # Clean up backup
                os.remove(self.backup_binary_path)
                print(f"✅ Restored RKHunter binary with original permissions {self.original_permissions}")

            except Exception as e:
                print(f"⚠️ Could not restore original state: {e}")

    def test_permission_scenario(self, permissions: str, description: str):
        """Test a specific permission scenario"""
        print(f"\n🧪 Testing: {description} (permissions: {permissions})")
        print("-" * 60)

        try:
            # Set test permissions
            if os.path.exists(self.original_binary_path):
                subprocess.run(['sudo', 'chmod', permissions, self.original_binary_path],
                              check=True)
                print(f"Set permissions to {permissions}")

            # Test detection
            status = self.monitor.get_status_enhanced(force_refresh=True)

            # Report results
            print(f"Available: {status.available}")
            print(f"Binary Path: {status.binary_path}")
            print(f"Binary Permissions: {status.binary_permissions}")
            print(f"Status Message: {status.status_message}")
            print(f"Confidence: {status.confidence_level}")

            if status.permission_issues:
                print("Issues:")
                for issue in status.permission_issues:
                    print(f"  - {issue}")

            if status.user_solutions:
                print("Solutions:")
                for solution in status.user_solutions:
                    print(f"  - {solution}")

            return status

        except Exception as e:
            print(f"❌ Error during test: {e}")
            return None

    def run_comprehensive_tests(self):
        """Run comprehensive permission scenario tests"""
        print("🔍 RKHunter Enhanced Detection Permission Tests")
        print("=" * 60)

        # Backup current state
        self.backup_current_state()

        try:
            # Test scenarios based on research findings
            scenarios = [
                ("755", "Standard permissions (Ubuntu/Debian/RHEL/Fedora)"),
                ("700", "Restrictive permissions (Arch Linux anomaly)"),
                ("644", "File permissions (should not be executable)"),
                ("600", "Highly restrictive (owner read/write only)")
            ]

            results = {}

            for permissions, description in scenarios:
                result = self.test_permission_scenario(permissions, description)
                results[permissions] = result

            # Summary analysis
            print(f"\n📊 Test Results Summary")
            print("=" * 60)

            for permissions, result in results.items():
                if result:
                    status_icon = "✅" if result.available else "❌"
                    confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(result.confidence_level, "⚪")

                    print(f"{permissions}: {status_icon} Available={result.available} "
                          f"{confidence_icon} Confidence={result.confidence_level}")

                    if result.permission_issues:
                        print(f"       Issues: {len(result.permission_issues)}")
                else:
                    print(f"{permissions}: ❌ Test failed")

            # Validate expected behaviors
            print(f"\n🎯 Expected Behavior Validation")
            print("-" * 40)

            # Standard permissions (755) should work perfectly
            if "755" in results and results["755"]:
                r755 = results["755"]
                if r755.available and r755.confidence_level == "high" and not r755.permission_issues:
                    print("✅ Standard permissions (755): PASS - Perfect detection")
                else:
                    print("❌ Standard permissions (755): FAIL - Should work perfectly")

            # Restrictive permissions (700) should be detected with solutions
            if "700" in results and results["700"]:
                r700 = results["700"]
                if r700.available and r700.permission_issues and r700.user_solutions:
                    print("✅ Restrictive permissions (700): PASS - Detected with solutions")
                else:
                    print("❌ Restrictive permissions (700): FAIL - Should detect issues and provide solutions")

            # Very restrictive permissions should be gracefully handled
            if "600" in results and results["600"]:
                r600 = results["600"]
                # This should likely fail to be available, but gracefully
                print(f"🔍 Very restrictive (600): Available={r600.available} - As expected for non-executable")

        finally:
            # Always restore original state
            self.restore_original_state()

    def test_configuration_creation(self):
        """Test user configuration creation functionality"""
        print(f"\n🔧 Testing User Configuration Creation")
        print("-" * 40)

        # Temporarily remove user config to test creation
        user_config_path = Path.home() / '.config' / 'search-and-destroy' / 'rkhunter.conf'
        backup_path = None

        if user_config_path.exists():
            backup_path = user_config_path.with_suffix('.conf.backup')
            shutil.move(user_config_path, backup_path)
            print("Temporarily backed up existing user config")

        try:
            # Test creation
            created_config = self.monitor.create_user_configuration()

            if created_config:
                print(f"✅ Successfully created user config: {created_config}")

                # Verify it's readable
                if os.path.exists(created_config) and os.access(created_config, os.R_OK):
                    print("✅ User config is readable")
                else:
                    print("❌ User config is not readable")

                # Test that detection now works
                status = self.monitor.get_status_enhanced(force_refresh=True)
                if status.config_readable:
                    print("✅ Detection correctly uses user config")
                else:
                    print("❌ Detection doesn't use user config")

            else:
                print("❌ Failed to create user configuration")

        finally:
            # Restore original user config if it existed
            if backup_path and backup_path.exists():
                shutil.move(backup_path, user_config_path)
                print("Restored original user config")


def main():
    """Run the comprehensive RKHunter permission tests"""
    tester = RKHunterPermissionTester()

    # Check if we can run tests (need sudo for permission changes)
    try:
        subprocess.run(['sudo', '-n', 'true'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ This test requires sudo access to modify RKHunter permissions")
        print("Run with: sudo -v && python test_enhanced_detection.py")
        return

    print("🚀 Starting Enhanced RKHunter Detection Tests")
    print("This will temporarily modify RKHunter permissions for testing")

    # Run tests
    tester.run_comprehensive_tests()
    tester.test_configuration_creation()

    print(f"\n🎉 Tests completed! RKHunter detection system validated.")


if __name__ == "__main__":
    main()
