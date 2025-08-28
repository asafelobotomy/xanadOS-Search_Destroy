#!/usr/bin/env python3
"""
Centralized Version Management System
Keep all version references in sync by updating only the VERSION file.
"""

from pathlib import Path


def get_version() -> str:
    """Get current version from the repository root VERSION file.

    Falls back to 'dev' when missing or unreadable.
    """
    try:
        # Repo root is three levels up from this file: scripts/tools/version_manager.py
        repo_root = Path(__file__).resolve().parents[2]
        version_file = repo_root / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        return "dev"
    except (OSError, FileNotFoundError):
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
