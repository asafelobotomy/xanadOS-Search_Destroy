#!/usr/bin/env python3
"""
Test suite for the Safe Files (exclusion list) feature.

Tests the Priority 1 implementation:
- Adding files to safe list
- Removing files from safe list
- Checking if files are safe
- Integration with file scanner exclusion
"""

import tempfile
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_safe_files_config_storage():
    """Test that safe files are properly stored in configuration."""
    from app.core.unified_configuration_manager import get_config, save_config

    # Create a unique test file path for this test
    test_file = "/tmp/test_safe_file_storage_unique.txt"
    normalized_path = str(Path(test_file).resolve())

    # Get current config
    config = get_config()

    # Initialize safe_files list if not present
    if "scan_settings" not in config:
        config["scan_settings"] = {}

    # Clear any existing safe files for clean test
    config["scan_settings"]["safe_files"] = []
    save_config(config)

    # Add a safe file
    config = get_config()
    if "safe_files" not in config["scan_settings"]:
        config["scan_settings"]["safe_files"] = []

    config["scan_settings"]["safe_files"].append(normalized_path)
    save_config(config)

    # Verify it was saved
    config = get_config()
    safe_files = config.get("scan_settings", {}).get("safe_files", [])

    assert normalized_path in safe_files, "Safe file should be in the list"

    # Clean up - remove the file we added
    config["scan_settings"]["safe_files"] = [
        f for f in config["scan_settings"]["safe_files"] if f != normalized_path
    ]
    save_config(config)

    print("✅ Safe files config storage test passed")


def test_add_safe_file():
    """Test adding a file to the safe list."""
    try:
        from app.core.unified_configuration_manager import get_unified_config_manager
        import asyncio

        async def test():
            config_manager = await get_unified_config_manager()

            # Create a unique test file for this specific test
            test_file = "/tmp/test_safe_add_unique_xyz.txt"
            Path(test_file).touch()

            # Remove it first in case it exists from previous runs
            config_manager.remove_safe_file(test_file)

            # Now add to safe list
            print(f"Adding file: {test_file}")
            result = config_manager.add_safe_file(test_file)
            print(f"Add result: {result}")
            print(f"Safe files after add: {config_manager.get_safe_files()}")
            assert result is True, "Should successfully add new file"

            # Try adding again (should return False as already in list)
            result = config_manager.add_safe_file(test_file)
            assert result is False, "Should return False for duplicate"

            # Verify file is in list
            safe_files = config_manager.get_safe_files()
            normalized_path = str(Path(test_file).resolve())
            assert normalized_path in safe_files, "File should be in safe list"

            # Clean up
            config_manager.remove_safe_file(test_file)
            Path(test_file).unlink(missing_ok=True)

            print("✅ Add safe file test passed")

        asyncio.run(test())

    except ImportError as e:
        print(f"⚠️ Skipping async test (import error): {e}")


def test_remove_safe_file():
    """Test removing a file from the safe list."""
    try:
        from app.core.unified_configuration_manager import get_unified_config_manager
        import asyncio

        async def test():
            config_manager = await get_unified_config_manager()

            # Create and add a test file
            test_file = "/tmp/test_safe_remove.txt"
            Path(test_file).touch()
            config_manager.add_safe_file(test_file)

            # Remove from safe list
            result = config_manager.remove_safe_file(test_file)
            assert result is True, "Should successfully remove file"

            # Try removing again (should return False as not in list)
            result = config_manager.remove_safe_file(test_file)
            assert result is False, "Should return False for non-existent file"

            # Verify file is not in list
            safe_files = config_manager.get_safe_files()
            normalized_path = str(Path(test_file).resolve())
            assert normalized_path not in safe_files, "File should not be in safe list"

            # Clean up
            Path(test_file).unlink(missing_ok=True)

            print("✅ Remove safe file test passed")

        asyncio.run(test())

    except ImportError as e:
        print(f"⚠️ Skipping async test (import error): {e}")


def test_is_safe_file():
    """Test checking if a file is in the safe list."""
    try:
        from app.core.unified_configuration_manager import get_unified_config_manager
        import asyncio

        async def test():
            config_manager = await get_unified_config_manager()

            # Create test files
            safe_file = "/tmp/test_is_safe_true.txt"
            unsafe_file = "/tmp/test_is_safe_false.txt"
            Path(safe_file).touch()
            Path(unsafe_file).touch()

            # Add one file to safe list
            config_manager.add_safe_file(safe_file)

            # Test checks
            assert (
                config_manager.is_safe_file(safe_file) is True
            ), "Safe file should return True"
            assert (
                config_manager.is_safe_file(unsafe_file) is False
            ), "Unsafe file should return False"

            # Clean up
            config_manager.remove_safe_file(safe_file)
            Path(safe_file).unlink(missing_ok=True)
            Path(unsafe_file).unlink(missing_ok=True)

            print("✅ Is safe file test passed")

        asyncio.run(test())

    except ImportError as e:
        print(f"⚠️ Skipping async test (import error): {e}")


def test_scanner_exclusion_integration():
    """Test that FileScanner properly excludes safe files."""
    from app.core.file_scanner import FileScanner
    from app.core.unified_configuration_manager import get_config, save_config
    from pathlib import Path

    # Create a test file
    test_file = "/tmp/test_scanner_exclusion.txt"
    Path(test_file).touch()
    normalized_path = str(Path(test_file).resolve())

    # Add to safe files
    config = get_config()
    if "scan_settings" not in config:
        config["scan_settings"] = {}
    config["scan_settings"]["safe_files"] = [normalized_path]
    save_config(config)

    # Test exclusion
    scanner = FileScanner()
    exclusions = []  # Empty exclusion patterns

    # File should be excluded because it's in safe list
    is_excluded = scanner._is_excluded_file(Path(test_file), exclusions)

    assert is_excluded is True, "Safe file should be excluded from scanning"

    # Clean up
    config["scan_settings"]["safe_files"] = []
    save_config(config)
    Path(test_file).unlink(missing_ok=True)

    print("✅ Scanner exclusion integration test passed")


def test_safe_files_persistence():
    """Test that safe files persist across config reloads."""
    from app.core.unified_configuration_manager import get_config, save_config
    from pathlib import Path

    test_file = "/tmp/test_persistence.txt"
    normalized_path = str(Path(test_file).resolve())

    # Add safe file
    config = get_config()
    if "scan_settings" not in config:
        config["scan_settings"] = {}
    config["scan_settings"]["safe_files"] = [normalized_path]
    save_config(config)

    # Reload config
    config = get_config()
    safe_files = config.get("scan_settings", {}).get("safe_files", [])

    assert normalized_path in safe_files, "Safe files should persist after reload"

    # Clean up
    config["scan_settings"]["safe_files"] = []
    save_config(config)

    print("✅ Safe files persistence test passed")


if __name__ == "__main__":
    print("\n🧪 Testing Safe Files Feature Implementation")
    print("=" * 60)

    try:
        test_safe_files_config_storage()
        test_add_safe_file()
        test_remove_safe_file()
        test_is_safe_file()
        test_scanner_exclusion_integration()
        test_safe_files_persistence()

        print("\n" + "=" * 60)
        print("✅ All safe files feature tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
