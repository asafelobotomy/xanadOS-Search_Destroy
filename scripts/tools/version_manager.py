#!/usr/bin/env python3
"""
Centralized Version Management System
Keep all version references in sync by updating only the VERSION file.
"""

import sys
from pathlib import Path

def get_version():
    """Get current version from VERSION file."""
    try:
        version_file = Path(__file__).parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "dev"
    except Exception:
        return "dev"

def update_version_example():
    """Example of how to update version across the repository."""
    print("🔧 Centralized Version Management")
    print("=" * 40)
    print(f"Current version: {get_version()}")
    print("\n📝 To update version:")
    print("1. Edit the VERSION file")
    print("2. All components will automatically use the new version")
    print("\n✅ Components using centralized version:")
    print("   - Splash screen")
    print("   - User manual")
    print("   - Main window")
    print("   - Configuration system")
    print("   - Update components")

if __name__ == "__main__":
    update_version_example()
