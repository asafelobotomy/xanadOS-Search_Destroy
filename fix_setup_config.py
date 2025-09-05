#!/usr/bin/env python3
"""Fix the setup configuration to prevent First Time Setup dialog from recurring.

This script adds the missing 'first_time_setup_completed' flag to the config file.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Get the config file path using the same logic as the app
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
APP_NAME = "search-and-destroy"
CONFIG_DIR = Path(XDG_CONFIG_HOME) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

def fix_setup_config():
    """Add the missing first_time_setup_completed flag to the config."""
    if not CONFIG_FILE.exists():
        print(f"Config file not found at {CONFIG_FILE}")
        return False

    try:
        # Load current config
        with open(CONFIG_FILE, encoding='utf-8') as f:
            config = json.load(f)

        print(f"Current config file: {CONFIG_FILE}")

        # Check if setup section exists
        if "setup" not in config:
            config["setup"] = {}
            print("Created missing 'setup' section")

        # Check if first_time_setup_completed is already set
        if config["setup"].get("first_time_setup_completed", False):
            print("✅ Setup is already marked as completed!")
            return True

        # Add the missing flag
        config["setup"]["first_time_setup_completed"] = True
        config["setup"]["last_setup_check"] = datetime.now().isoformat()
        config["setup"]["fixed_by_script"] = True

        # Save the updated config
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, sort_keys=True)

        print("✅ Successfully added first_time_setup_completed flag!")
        print("✅ The First Time Setup dialog should no longer appear on app launch.")

        return True

    except Exception as e:
        print(f"❌ Error fixing config: {e}")
        return False

if __name__ == "__main__":
    print("=== S&D - Search & Destroy Setup Fix ===")
    print("This script fixes the recurring First Time Setup dialog issue.\n")

    success = fix_setup_config()

    if success:
        print("\n🎉 Fix completed successfully!")
        print("You can now launch the application without seeing the setup dialog.")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")
        sys.exit(1)
