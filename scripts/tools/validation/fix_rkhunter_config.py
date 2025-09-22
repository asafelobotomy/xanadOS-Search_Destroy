#!/usr/bin/env python3
"""
RKHunter Configuration Recovery Tool
Fixes the PKGMGR_NO_VRFY configuration issue and ensures GUI compatibility
"""

import sys
from pathlib import Path


def fix_rkhunter_config():
    """Fix RKHunter configuration issues."""
    print("🔧 RKHunter Configuration Recovery Tool")
    print("=" * 50)

    # Configuration paths
    user_config_dir = Path.home() / ".config" / "search-and-destroy"
    user_config_file = user_config_dir / "rkhunter.conf"

    print(f"📁 User config directory: {user_config_dir}")
    print(f"📄 User config file: {user_config_file}")

    # Step 1: Remove old configuration to force regeneration
    if user_config_file.exists():
        print("🗑️  Removing old configuration file...")
        user_config_file.unlink()
        print("✅ Old configuration removed")
    else:
        print("ℹ️  No existing configuration to remove")

    # Step 2: Clear any cached configurations
    cache_patterns = [user_config_dir / "*.cache", user_config_dir / "rkhunter_*.tmp"]

    for pattern in cache_patterns:
        for file in user_config_dir.glob(pattern.name):
            if file.exists():
                print(f"🗑️  Removing cache file: {file}")
                file.unlink()

    # Step 3: Test the fix by initializing a new wrapper
    print("\n🔄 Testing configuration regeneration...")

    try:
        # Add the app directory to Python path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))
        from core.rkhunter_wrapper import RKHunterWrapper

        # Create new wrapper (this should generate new config)
        wrapper = RKHunterWrapper()

        if wrapper.available and wrapper.config_path.exists():
            print("✅ New configuration generated successfully")

            # Verify the fix
            with open(wrapper.config_path) as f:
                content = f.read()

            if 'PKGMGR_NO_VRFY=""' in content:
                print("✅ PKGMGR_NO_VRFY correctly set to empty string")
            elif "PKGMGR_NO_VRFY=1" in content:
                print("❌ PKGMGR_NO_VRFY still incorrectly set to '1'")
                return False
            else:
                print("⚠️  PKGMGR_NO_VRFY not found in configuration")

            # Show the relevant configuration lines
            print("\n📋 Key configuration settings:")
            for line in content.split("\n"):
                if any(keyword in line for keyword in ["PKGMGR", "DISABLE_TESTS"]):
                    print(f"   {line}")

            return True
        else:
            print("❌ Failed to generate new configuration")
            return False

    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False


def main():
    """Main function."""
    print("Starting RKHunter configuration recovery...\n")

    if fix_rkhunter_config():
        print("\n🎉 Configuration recovery completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Restart the GUI application if it's currently running")
        print("   2. Try running an RKHunter scan again")
        print("   3. The 'Invalid PKGMGR_NO_VRFY' error should be resolved")
        return 0
    else:
        print("\n❌ Configuration recovery failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
