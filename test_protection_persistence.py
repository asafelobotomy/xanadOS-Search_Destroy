#!/usr/bin/env python3
"""
Test script to verify real-time protection state persistence.
"""

import json
import os
from pathlib import Path

def get_config_path():
    """Get the path to the configuration file."""
    config_dir = Path.home() / '.config' / 'search-and-destroy'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.json'

def check_config():
    """Check current configuration state."""
    config_file = get_config_path()
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            security_settings = config.get('security_settings', {})
            real_time_protection = security_settings.get('real_time_protection', False)
            
            print(f"📁 Config file: {config_file}")
            print(f"🛡️ Real-time protection setting: {real_time_protection}")
            print(f"⚙️ Security settings: {security_settings}")
            
            return real_time_protection
        except Exception as e:
            print(f"❌ Error reading config: {e}")
            return None
    else:
        print("📁 Config file does not exist yet")
        return None

def set_protection_enabled():
    """Set real-time protection to enabled in config."""
    config_file = get_config_path()
    
    config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading existing config, creating new: {e}")
    
    if 'security_settings' not in config:
        config['security_settings'] = {}
    
    config['security_settings']['real_time_protection'] = True
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Set real-time protection to enabled in config")
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

def set_protection_disabled():
    """Set real-time protection to disabled in config."""
    config_file = get_config_path()
    
    config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading existing config, creating new: {e}")
    
    if 'security_settings' not in config:
        config['security_settings'] = {}
    
    config['security_settings']['real_time_protection'] = False
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Set real-time protection to disabled in config")
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_protection_persistence.py check    - Check current config")
        print("  python test_protection_persistence.py enable   - Enable protection in config")
        print("  python test_protection_persistence.py disable  - Disable protection in config")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "check":
        check_config()
    elif command == "enable":
        set_protection_enabled()
        print("\nAfter setting to enabled:")
        check_config()
    elif command == "disable":
        set_protection_disabled()
        print("\nAfter setting to disabled:")
        check_config()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
