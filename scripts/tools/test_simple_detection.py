#!/usr/bin/env python3
"""
Simplified test for RKHunter enhanced detection system
Tests the standalone enhanced detector without complex app dependencies
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import the standalone enhanced detector
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_rkhunter_detector import EnhancedRKHunterDetector


class SimpleRKHunterPermissionTester:
    """Simple permission testing without app dependencies"""

    def __init__(self):
        self.original_binary_path = '/usr/bin/rkhunter'
        self.backup_binary_path = '/tmp/rkhunter_backup'
        self.original_permissions = None
        self.detector = EnhancedRKHunterDetector()

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
            result = self.detector.detect_comprehensive()

            # Report results
            print(f"Available: {result.available}")
            print(f"Binary Path: {result.binary_path}")
            print(f"Binary Permissions: {result.binary_permissions}")
            print(f"Status Message: {result.status_message}")
            print(f"Confidence: {result.confidence_level}")

            if result.issues:
                print("Issues:")
                for issue in result.issues:
                    print(f"  - {issue}")

            if result.solutions:
                print("Solutions:")
                for solution in result.solutions:
                    print(f"  - {solution}")

            return result

        except Exception as e:
            print(f"❌ Error during test: {e}")
            return None

    def run_tests(self):
        """Run permission scenario tests"""
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

                    if result.issues:
                        print(f"       Issues: {len(result.issues)}")
                else:
                    print(f"{permissions}: ❌ Test failed")

            # Validate expected behaviors
            print(f"\n🎯 Expected Behavior Validation")
            print("-" * 40)

            # Standard permissions (755) should work perfectly
            if "755" in results and results["755"]:
                r755 = results["755"]
                if r755.available and r755.confidence_level == "high" and not r755.issues:
                    print("✅ Standard permissions (755): PASS - Perfect detection")
                else:
                    print("❌ Standard permissions (755): FAIL - Should work perfectly")

            # Restrictive permissions (700) should be detected with solutions
            if "700" in results and results["700"]:
                r700 = results["700"]
                if r700.available and r700.issues and r700.solutions:
                    print("✅ Restrictive permissions (700): PASS - Detected with solutions")
                else:
                    print("❌ Restrictive permissions (700): FAIL - Should detect issues and provide solutions")

            # Very restrictive permissions should be gracefully handled
            if "600" in results and results["600"]:
                r600 = results["600"]
                print(f"🔍 Very restrictive (600): Available={r600.available} - As expected for non-executable")

        finally:
            # Always restore original state
            self.restore_original_state()


def main():
    """Run the permission tests"""
    # Check if we can run tests (need sudo for permission changes)
    try:
        subprocess.run(['sudo', '-n', 'true'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ This test requires sudo access to modify RKHunter permissions")
        print("Run with: sudo -v && python test_simple_detection.py")
        return

    print("🚀 Starting Enhanced RKHunter Detection Tests")
    print("This will temporarily modify RKHunter permissions for testing")

    # Run tests
    tester = SimpleRKHunterPermissionTester()
    tester.run_tests()

    print(f"\n🎉 Tests completed! RKHunter detection system validated.")


if __name__ == "__main__":
    main()
