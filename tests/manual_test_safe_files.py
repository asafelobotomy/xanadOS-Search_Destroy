#!/usr/bin/env python3
"""Simple manual test of safe files feature"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.unified_configuration_manager import get_config, save_config

print("\n=== Safe Files Feature Manual Test ===\n")

# Test 1: Add a file via config functions
print("1. Adding file via get_config/save_config...")
config = get_config()
if "scan_settings" not in config:
    config["scan_settings"] = {}
if "safe_files" not in config["scan_settings"]:
    config["scan_settings"]["safe_files"] = []

test_file = "/tmp/manual_test_safe.txt"
normalized = str(Path(test_file).resolve())

# Clear first
config["scan_settings"]["safe_files"] = []
save_config(config)

# Add
config = get_config()
config["scan_settings"]["safe_files"].append(normalized)
save_config(config)

# Verify
config = get_config()
if normalized in config["scan_settings"]["safe_files"]:
    print(f"   ✅ File added successfully: {normalized}")
else:
    print(f"   ❌ File NOT in list")

# Test 2: Check scanner exclusion
print("\n2. Testing scanner exclusion...")
from app.core.file_scanner import FileScanner

Path(test_file).touch()
scanner = FileScanner()
is_excluded = scanner._is_excluded_file(Path(test_file), [])

if is_excluded:
    print(f"   ✅ File is properly excluded from scans")
else:
    print(f"   ❌ File is NOT excluded")

# Cleanup
config = get_config()
config["scan_settings"]["safe_files"] = []
save_config(config)
Path(test_file).unlink(missing_ok=True)

print("\n=== Test Complete ===\n")
