#!/usr/bin/env python3
"""
Configuration management for S&D - Search & Destroy
Clean rewrite to eliminate auto-save conflicts
"""

import json
import logging
import os
import shutil
import tempfile
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Import centralized version
from app import __version__

# XDG Base Directory specification paths
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

APP_NAME = "search-and-destroy"
CONFIG_DIR = Path(XDG_CONFIG_HOME) / APP_NAME
DATA_DIR = Path(XDG_DATA_HOME) / APP_NAME
CACHE_DIR = Path(XDG_CACHE_HOME) / APP_NAME


def _ensure_secure_dir(path: Path):
    """Create directory if missing and enforce 700 permissions (best-effort).

    This limits exposure of potentially sensitive security application data
    (quarantine, reports, logs, config). Failures to chmod are logged but not fatal.
    """
    path.mkdir(parents=True, exist_ok=True)
    try:
        # Only adjust on POSIX systems
        if os.name == "posix":
            current_mode = path.stat().st_mode & 0o777
            # Avoid relaxing if already more restrictive
            if current_mode != 0o700:
                path.chmod(0o700)
    except OSError as e:
        logging.getLogger(APP_NAME).warning("Could not set secure permissions on %s: %s", path, e)


_ensure_secure_dir(CONFIG_DIR)
_ensure_secure_dir(DATA_DIR)
_ensure_secure_dir(CACHE_DIR)

CONFIG_FILE = CONFIG_DIR / "config.json"
SCAN_REPORTS_DIR = DATA_DIR / "scan_reports"
QUARANTINE_DIR = DATA_DIR / "quarantine"
LOG_DIR = DATA_DIR / "logs"

# Create subdirectories
SCAN_REPORTS_DIR.mkdir(exist_ok=True)

# Create quarantine directory with secure permissions (0o700)
QUARANTINE_DIR.mkdir(exist_ok=True)
if os.name == "posix":  # Unix-like systems
    try:
        QUARANTINE_DIR.chmod(0o700)  # Only owner can read/write/execute
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not set secure permissions on quarantine directory: {e}")

LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    """Setup application logging with rotation."""
    logger = logging.getLogger(APP_NAME)
    if not logger.handlers:

        class _RateLimitFilter(logging.Filter):
            def __init__(self, interval=5):
                super().__init__()
                self.interval = interval
                self._last: dict[tuple[str, int], float] = {}

            def filter(self, record: logging.LogRecord) -> bool:
                key = (record.getMessage()[:120], record.levelno)
                now = time.time()
                last = self._last.get(key, 0)
                if now - last < self.interval:
                    return False
                self._last[key] = now
                return True

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler with rotation
        log_file = LOG_DIR / "application.log"
        file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler for debug
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)

        # Optional structured logging: avoid circular import by using module-level CONFIG_FILE
        try:
            with open(CONFIG_FILE, encoding="utf-8") as cf:
                cfg_json = json.load(cf)
            structured = cfg_json.get("advanced_settings", {}).get("structured_logging", False)
        except Exception:
            structured = False
        if structured:
            formatter = logging.Formatter(
                json.dumps(
                    {
                        "time": "%(asctime)s",
                        "logger": "%(name)s",
                        "level": "%(levelname)s",
                        "message": "%(message)s",
                    }
                )
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

        rate_filter = _RateLimitFilter(interval=5)
        file_handler.addFilter(rate_filter)
        console_handler.addFilter(rate_filter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    return logger


def load_config(file_path=None):
    """Load configuration from file. Return as-is without merging."""
    config_path = Path(file_path) if file_path else CONFIG_FILE

    if not config_path.exists():
        # Create initial config with minimal structure
        initial_config = create_initial_config()
        save_config(initial_config, str(config_path))
        return initial_config

    try:
        with open(config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)
            # Return config exactly as saved - no modifications
            return config
    except json.JSONDecodeError as e:
        logging.getLogger(APP_NAME).error("Invalid JSON in config file: %s", e)
        # Backup corrupted config and create new one
        shutil.move(str(config_path), str(config_path) + ".corrupted")
        initial_config = create_initial_config()
        save_config(initial_config, str(config_path))
        return initial_config


def _atomic_write_json(config_path: Path, config_data):
    """Internal helper split out for testability (atomic write + chmod)."""
    tmp_fd = None
    tmp_path = None
    try:
        _ensure_secure_dir(config_path.parent)
        tmp_fd, tmp_path = tempfile.mkstemp(prefix=".config.", dir=str(config_path.parent))
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
            json.dump(config_data, tmp_file, indent=4, sort_keys=True)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, config_path)
        if os.name == "posix":
            try:
                os.chmod(config_path, 0o600)
            except OSError:
                pass
    finally:
        if tmp_fd is not None and tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def save_config(config_data, file_path=None):
    """Atomically save configuration to file with restrictive permissions.

    Writes to a temporary file in the same directory and then uses os.replace
    to ensure readers never observe a partially written JSON file.
    Permissions are set to 600 (owner rw) on POSIX systems.
    """
    config_path = Path(file_path) if file_path else CONFIG_FILE
    try:
        _atomic_write_json(config_path, config_data)
    except OSError as e:
        logging.getLogger(APP_NAME).error("Failed to save config atomically: %s", e)


def update_config_setting(config_dict, section, key, value, file_path=None):
    """Update a specific setting in config and save to file immediately.

    Args:
        config_dict: The configuration dictionary to update
        section: Configuration section (e.g., 'ui_settings', 'scan_settings')
        key: Setting key within the section
        value: New value for the setting
        file_path: Optional custom file path (uses default if None)

    Returns:
        bool: True if successfully saved, False otherwise
    """
    try:
        # Ensure section exists
        if section not in config_dict:
            config_dict[section] = {}

        # Update the setting
        config_dict[section][key] = value

        # Save immediately to ensure persistence
        save_config(config_dict, file_path)
        return True

    except Exception as e:
        logging.getLogger(APP_NAME).error("Failed to update setting %s.%s: %s", section, key, e)
        return False


def update_multiple_settings(config_dict, updates, file_path=None):
    """Update multiple settings at once and save to file.

    Args:
        config_dict: The configuration dictionary to update
        updates: Dict of {section: {key: value}} format
        file_path: Optional custom file path (uses default if None)

    Returns:
        bool: True if successfully saved, False otherwise

    Example:
        updates = {
            'ui_settings': {'theme': 'dark', 'minimize_to_tray': True},
            'scan_settings': {'max_threads': 8}
        }
    """
    try:
        # Apply all updates
        for section, settings in updates.items():
            if section not in config_dict:
                config_dict[section] = {}

            for key, value in settings.items():
                config_dict[section][key] = value

        # Save once after all updates
        save_config(config_dict, file_path)
        return True

    except Exception as e:
        logging.getLogger(APP_NAME).error("Failed to update multiple settings: %s", e)
        return False


def get_config_setting(config_dict, section, key, default=None):
    """Get a specific setting from config with optional default.

    Args:
        config_dict: The configuration dictionary
        section: Configuration section
        key: Setting key within the section
        default: Default value if setting doesn't exist

    Returns:
        The setting value or default
    """
    return config_dict.get(section, {}).get(key, default)


def create_initial_config():
    """Create initial configuration with settings that auto-save."""
    return {
        "scan_settings": {
            "max_threads": 4,
            "timeout_seconds": 300,
            # Core ClamAV settings
            "scan_archives": True,
            "scan_email": True,
            "scan_ole2": True,
            "scan_pdf": True,
            "scan_html": True,
            "scan_executable": True,
            "max_filesize": "100M",
            "max_recursion": 16,
            "max_files": 10000,
            "pcre_match_limit": 10000,
            "pcre_recmatch_limit": 5000,
        },
        "ui_settings": {
            "theme": "auto",
            "show_hidden_files": False,
            "auto_update_definitions": True,
            "notifications_enabled": True,
            "minimize_to_tray": True,
            "show_scan_progress": True,
            "activity_log_retention": 100,
            "show_notifications": True,
        },
        "security_settings": {
            "quarantine_enabled": True,
            "auto_quarantine_threats": False,
            "scan_removable_media": True,
            "real_time_protection": False,
            "auto_update_definitions": True,
        },
        "advanced_settings": {
            "signature_sources": ["main.cvd", "daily.cvd", "bytecode.cvd"],
            "custom_signature_urls": [],
            "log_level": "INFO",
            "structured_logging": False,
            "scan_timeout": 300,
            "update_frequency": "daily",
            "scan_archives": True,
            "follow_symlinks": False,
            "scan_depth": 2,
            "file_filter": "all",
            "memory_limit": 1024,
            "exclusion_patterns": "",
        },
        "realtime_protection": {
            "monitor_modifications": True,
            "monitor_new_files": True,
            "scan_modified_files": False,
        },
        "rkhunter_settings": {
            "enabled": False,
            "run_with_full_scan": False,
            "auto_update": True,
            "categories": {
                "applications": False,
                "network": True,
                "rootkits": True,
                "system_commands": True,
                "system_integrity": True,
            },
        },
        "scheduled_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "02:00",
        },
        "paths": {
            "quarantine_dir": str(QUARANTINE_DIR),
            "scan_reports_dir": str(SCAN_REPORTS_DIR),
            "log_dir": str(LOG_DIR),
            "temp_dir": str(CACHE_DIR / "temp"),
        },
        "telemetry": {
            "enabled": True,
            "privacy_level": "anonymous",  # anonymous, aggregated, detailed
            "data_retention_days": 30,
            "export_enabled": False,
        },
        "rate_limits": {
            "file_scan": {"calls": 100, "period": 60.0, "burst": 20, "adaptive": True},
            "directory_scan": {
                "calls": 10,
                "period": 60.0,
                "burst": 5,
                "adaptive": True,
            },
            "virus_db_update": {"calls": 1, "period": 3600.0, "adaptive": False},
            "network_request": {
                "calls": 50,
                "period": 60.0,
                "burst": 10,
                "adaptive": True,
            },
            "quarantine_action": {"calls": 20, "period": 60.0, "adaptive": False},
            "system_command": {"calls": 5, "period": 60.0, "adaptive": False},
        },
        "performance": {
            "scan_batch_size": 50,
            "max_memory_mb": 256,
            "timer_interval": 1000,
            "debounce_delay": 0.5,
            "enable_async_scanning": True,
            "enable_memory_optimization": True,
        },
        "setup": {
            "first_time_setup_completed": False,
            "setup_version": __version__,
            "packages_installed": {"clamav": False, "ufw": False, "rkhunter": False},
            "last_setup_check": None,
        },
    }


def get_factory_defaults():
    """Get factory default settings - ONLY used when 'Default Settings' button is pressed."""
    return {
        "scan_settings": {
            "max_threads": 4,
            "timeout_seconds": 300,
            "scan_archives": True,
            "scan_email": True,
            "scan_ole2": True,
            "scan_pdf": True,
            "scan_html": True,
            "scan_executable": True,
            "max_filesize": "100M",
            "max_recursion": 16,
            "max_files": 10000,
            "pcre_match_limit": 10000,
            "pcre_recmatch_limit": 5000,
        },
        "ui_settings": {
            "theme": "auto",
            "show_hidden_files": False,
            "auto_update_definitions": True,
            "notifications_enabled": True,
            "minimize_to_tray": True,
            "show_scan_progress": True,
            "activity_log_retention": 100,
            "show_notifications": True,
        },
        "security_settings": {
            "quarantine_enabled": True,
            "auto_quarantine_threats": False,
            "scan_removable_media": True,
            "real_time_protection": False,
            "auto_update_definitions": True,
        },
        "advanced_settings": {
            "signature_sources": ["main.cvd", "daily.cvd", "bytecode.cvd"],
            "custom_signature_urls": [],
            "log_level": "INFO",
            "structured_logging": False,
            "scan_timeout": 300,
            "update_frequency": "daily",
            "scan_archives": True,
            "follow_symlinks": False,
            "scan_depth": 2,
            "file_filter": "all",
            "memory_limit": 1024,
            "exclusion_patterns": "",
        },
        "realtime_protection": {
            "monitor_modifications": True,
            "monitor_new_files": True,
            "scan_modified_files": False,
        },
        "rkhunter_settings": {
            "enabled": False,
            "run_with_full_scan": False,
            "auto_update": True,
            "categories": {
                "applications": False,
                "network": True,
                "rootkits": True,
                "system_commands": True,
                "system_integrity": True,
            },
        },
        "scheduled_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "02:00",
        },
        "paths": {
            "quarantine_dir": str(QUARANTINE_DIR),
            "scan_reports_dir": str(SCAN_REPORTS_DIR),
            "log_dir": str(LOG_DIR),
            "temp_dir": str(CACHE_DIR / "temp"),
        },
    }
