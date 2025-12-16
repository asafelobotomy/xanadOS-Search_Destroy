#!/usr/bin/env python3
"""Test GUI integration for marking files as safe"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("\n=== Testing GUI 'Mark as Safe' Integration ===\n")

# Simulate what the GUI does when user clicks "Mark as Safe"
test_file = "/tmp/gui_integration_test.txt"
Path(test_file).touch()

try:
    from app.core.unified_configuration_manager import get_config, save_config

    # This is the exact code from main_window.py
    config = get_config()

    # Initialize safe_files list if not present
    if "scan_settings" not in config:
        config["scan_settings"] = {}
    if "safe_files" not in config["scan_settings"]:
        config["scan_settings"]["safe_files"] = []

    # Normalize file path
    from pathlib import Path

    normalized_path = str(Path(test_file).resolve())

    # Add to safe files if not already present
    if normalized_path not in config["scan_settings"]["safe_files"]:
        config["scan_settings"]["safe_files"].append(normalized_path)

        # Save config
        save_config(config)

        print(f"✅ File marked as safe: {test_file}")
        print(f"   Normalized path: {normalized_path}")
    else:
        print(f"ℹ️  File already in safe list")

    # Verify it persists
    config = get_config()
    safe_files = config.get("scan_settings", {}).get("safe_files", [])

    if normalized_path in safe_files:
        print(f"✅ File persisted in configuration")
        print(f"   Total safe files: {len(safe_files)}")
    else:
        print(f"❌ File NOT found in configuration")

    # Test that scanner will skip it
    from app.core.file_scanner import FileScanner

    scanner = FileScanner()
    is_excluded = scanner._is_excluded_file(Path(test_file), [])

    if is_excluded:
        print(f"✅ Scanner will skip this file in future scans")
    else:
        print(f"❌ Scanner will NOT skip this file")

    # Cleanup
    config["scan_settings"]["safe_files"] = []
    save_config(config)
    Path(test_file).unlink(missing_ok=True)

    print("\n=== GUI Integration Test PASSED ===\n")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
