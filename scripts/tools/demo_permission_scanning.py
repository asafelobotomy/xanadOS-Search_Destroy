#!/usr/bin/env python3
"""
Demonstration script for the permission-aware scanning system.
This script shows how the new permission handling works when scanning
directories that require administrator privileges.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.permission_manager import (
    PermissionChecker,
    PrivilegedScanner,
)


def demo_permission_detection():
    """Demonstrate permission detection capabilities."""
    print("🔍 Permission Detection Demonstration")
    print("=" * 50)

    checker = PermissionChecker()

    test_paths = [
        "/",  # Root filesystem
        "/proc",  # Process filesystem
        "/sys",  # System filesystem
        "/tmp",  # Temporary directory
        "/home",  # Home directories
        "/root",  # Root home directory
        os.path.expanduser("~"),  # Current user home
    ]

    for path in test_paths:
        if os.path.exists(path):
            requires_root = checker.requires_root_access(path)
            can_access, error = checker.test_directory_access(path)

            status = "🔒 PRIVILEGED" if requires_root else "✅ NORMAL"
            access = "✅ ACCESSIBLE" if can_access else f"❌ BLOCKED: {error}"

            print(f"{status:<15} {access:<30} {path}")
        else:
            print(f"⚠️  MISSING      N/A                            {path}")


def demo_privileged_scanner():
    """Demonstrate the privileged scanner workflow."""
    print("\n🛡️  Privileged Scanner Demonstration")
    print("=" * 50)

    scanner = PrivilegedScanner()

    print(f"Sudo available: {'✅ YES' if scanner.is_sudo_available() else '❌ NO'}")

    # Test different scan scenarios
    test_scenarios = [
        ("Home Directory", os.path.expanduser("~")),
        ("Root Filesystem", "/"),
        ("Process Filesystem", "/proc"),
    ]

    for name, path in test_scenarios:
        print(f"\n📁 Scenario: {name} ({path})")

        if os.path.exists(path):
            should_proceed, permission_mode, privileged_paths = (
                scanner.prepare_scan_with_permissions(
                    path, parent_widget=None  # No GUI for this demo
                )
            )

            print(f"   Should proceed: {'✅ YES' if should_proceed else '❌ NO'}")
            print(f"   Permission mode: {permission_mode}")
            print(f"   Privileged paths found: {len(privileged_paths)}")

            if privileged_paths:
                print("   Protected directories:")
                for priv_path in privileged_paths[:5]:  # Show first 5
                    print(f"     • {priv_path}")
                if len(privileged_paths) > 5:
                    print(f"     ... and {len(privileged_paths) - 5} more")
        else:
            print("   ⚠️  Path does not exist")


def demo_permission_modes():
    """Demonstrate different permission handling modes."""
    print("\n⚙️  Permission Mode Demonstration")
    print("=" * 50)

    modes = {
        "normal": "Standard scanning without special permission handling",
        "skip_privileged": "Skip directories requiring root access",
        "sudo": "Request administrator authentication for protected directories",
    }

    for mode, description in modes.items():
        print(f"🔧 {mode.upper():<15} - {description}")

    print("\n💡 Usage in FileScanner:")
    print("   scanner.scan_directory(")
    print("       '/path/to/scan',")
    print("       permission_mode='skip_privileged',")
    print("       privileged_paths=['/proc', '/root'],")
    print("       # ... other options")
    print("   )")


def main():
    """Run the complete demonstration."""
    print("🚀 xanadOS Search & Destroy - Permission-Aware Scanning Demo")
    print("=" * 70)
    print()
    print("This demonstration shows the new permission handling system that")
    print("resolves the '[Errno 13] Permission denied' issues when scanning")
    print("system directories like /proc/1/cwd.")
    print()

    try:
        demo_permission_detection()
        demo_privileged_scanner()
        demo_permission_modes()

        print("\n" + "=" * 70)
        print("✅ Permission-aware scanning demonstration completed successfully!")
        print()
        print("Key benefits:")
        print("• Users are informed about permission requirements before scanning")
        print("• Clear choices for handling privileged directories")
        print("• No more silent failures or unexpected permission errors")
        print("• Maintains security while providing flexibility")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
