#!/usr/bin/env python3
"""
Compatibility shim for app/utils/config.py

This file maintains backward compatibility for code that imports from the original
config.py file. All functionality has been consolidated into
app/core/unified_configuration_manager.py.

DEPRECATION NOTICE: This compatibility shim will be removed in a future version.
Please update imports to use:
    from app.core.unified_configuration_manager import get_config, save_config, etc.
"""

import warnings
from app.core.unified_configuration_manager import (
    # Core functions
    get_config,
    load_config,
    save_config,
    update_config_setting,
    update_multiple_settings,
    get_config_setting,
    get_factory_defaults,
    setup_logging,
    # Specialized functions
    get_api_security_config,
    get_secure_database_url,
    get_redis_config,
    # Constants and paths
    CONFIG_DIR,
    DATA_DIR,
    CACHE_DIR,
    APP_NAME,
    # Compatibility aliases
    XDG_CONFIG_HOME,
    XDG_DATA_HOME,
    XDG_CACHE_HOME,
)

# Issue deprecation warning
warnings.warn(
    "app.utils.config is deprecated. Use app.core.unified_configuration_manager instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy path constants for compatibility
SCAN_REPORTS_DIR = DATA_DIR / "scan_reports"
QUARANTINE_DIR = DATA_DIR / "quarantine"
LOG_DIR = DATA_DIR / "logs"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Ensure legacy directories exist
SCAN_REPORTS_DIR.mkdir(exist_ok=True)
QUARANTINE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


# Legacy function aliases
def create_initial_config():
    """Legacy function - use get_factory_defaults() instead"""
    warnings.warn(
        "create_initial_config() is deprecated. Use get_factory_defaults() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_factory_defaults()


def backup_database():
    """Legacy function - now handled automatically by unified config manager"""
    warnings.warn(
        "backup_database() is deprecated. Database backups are now handled automatically.",
        DeprecationWarning,
        stacklevel=2,
    )
    return True


def cleanup_old_backups(backup_dir, retention_days):
    """Legacy function - now handled automatically by unified config manager"""
    warnings.warn(
        "cleanup_old_backups() is deprecated. Backup cleanup is now handled automatically.",
        DeprecationWarning,
        stacklevel=2,
    )
    pass


# Ensure all original exports are available
__all__ = [
    # Core functions
    "get_config",
    "load_config",
    "save_config",
    "update_config_setting",
    "update_multiple_settings",
    "get_config_setting",
    "create_initial_config",
    "get_factory_defaults",
    "setup_logging",
    # Specialized functions
    "get_api_security_config",
    "get_secure_database_url",
    "get_redis_config",
    "backup_database",
    "cleanup_old_backups",
    # Constants
    "CONFIG_DIR",
    "DATA_DIR",
    "CACHE_DIR",
    "APP_NAME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_CACHE_HOME",
    "CONFIG_FILE",
    "SCAN_REPORTS_DIR",
    "QUARANTINE_DIR",
    "LOG_DIR",
]
