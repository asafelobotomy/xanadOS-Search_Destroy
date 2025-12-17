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
        logging.getLogger(APP_NAME).warning(
            "Could not set secure permissions on %s: %s", path, e
        )


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
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
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
            structured = cfg_json.get("advanced_settings", {}).get(
                "structured_logging", False
            )
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
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=".config.", dir=str(config_path.parent)
        )
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
        logging.getLogger(APP_NAME).error(
            "Failed to update setting %s.%s: %s", section, key, e
        )
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
        "ml_scanning": {
            "enabled": False,  # ML scanning disabled by default
            "model_name": "malware_detector_rf",
            "model_version": None,  # None = use production model
            "confidence_threshold": 0.7,
            "fallback_to_signature": True,  # Use ClamAV if ML fails
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


def get_config(file_path=None):
    """Compatibility function - alias for load_config.

    This function maintains backward compatibility with components
    that expect get_config() instead of load_config().
    """
    return load_config(file_path)


def get_api_security_config():
    """Get API security configuration with secure defaults.

    Returns:
        dict: API security configuration with auto-generated secrets if needed
    """
    import secrets
    import string

    config = load_config()

    # Ensure api_security section exists
    if "api_security" not in config:
        config["api_security"] = {}

    api_config = config["api_security"]

    # Database configuration
    if "database" not in api_config:
        api_config["database"] = {}

    db_config = api_config["database"]

    # Set secure database path if not configured
    if not db_config.get("path"):
        secure_db_path = DATA_DIR / "security_api.db"
        db_config.update(
            {
                "type": "sqlite",
                "path": str(secure_db_path),
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "echo": False,
                "backup_enabled": True,
                "backup_retention_days": 30,
            }
        )

    # Redis configuration with environment variable support
    if "redis" not in api_config:
        api_config["redis"] = {}

    redis_config = api_config["redis"]
    redis_config.setdefault("host", os.environ.get("REDIS_HOST", "localhost"))
    redis_config.setdefault("port", int(os.environ.get("REDIS_PORT", "6379")))
    redis_config.setdefault("db", int(os.environ.get("REDIS_DB", "0")))
    redis_config.setdefault("password", os.environ.get("REDIS_PASSWORD", ""))
    redis_config.setdefault(
        "ssl", os.environ.get("REDIS_SSL", "false").lower() == "true"
    )
    redis_config.setdefault("connection_pool_size", 10)
    redis_config.setdefault("socket_timeout", 30)
    redis_config.setdefault("retry_on_timeout", True)

    # JWT configuration with auto-generated secret
    if "jwt" not in api_config:
        api_config["jwt"] = {}

    jwt_config = api_config["jwt"]

    # Generate secure secret key if not set (check env first)
    if not jwt_config.get("secret_key"):
        # Check environment variable first
        env_secret = os.environ.get("JWT_SECRET_KEY")
        if env_secret and len(env_secret) >= 32:
            jwt_config["secret_key"] = env_secret
        else:
            # Generate 64-character secure random key
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
            secret_key = "".join(secrets.choice(alphabet) for _ in range(64))
            jwt_config["secret_key"] = secret_key

            # Log warning about generated key
            logging.getLogger(APP_NAME).warning(
                "Generated random JWT secret key. For production, set JWT_SECRET_KEY environment variable."
            )

    # Set JWT defaults with environment variable overrides
    jwt_config.setdefault("algorithm", os.environ.get("JWT_ALGORITHM", "HS256"))
    jwt_config.setdefault(
        "access_token_expire_minutes",
        int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", "15")),
    )
    jwt_config.setdefault(
        "refresh_token_expire_days", int(os.environ.get("JWT_REFRESH_EXPIRE_DAYS", "7"))
    )
    jwt_config.setdefault(
        "issuer", os.environ.get("JWT_ISSUER", "xanadOS-Security-API")
    )
    jwt_config.setdefault("audience", os.environ.get("JWT_AUDIENCE", "xanadOS-clients"))
    jwt_config.setdefault("auto_rotate_keys", True)
    jwt_config.setdefault("key_rotation_days", 30)

    # Rate limiting configuration with environment variable support
    if "rate_limiting" not in api_config:
        api_config["rate_limiting"] = {}

    rate_config = api_config["rate_limiting"]
    rate_config.setdefault(
        "enabled", os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
    )
    rate_config.setdefault(
        "requests_per_minute", int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))
    )
    rate_config.setdefault(
        "requests_per_hour", int(os.environ.get("RATE_LIMIT_PER_HOUR", "1000"))
    )
    rate_config.setdefault(
        "requests_per_day", int(os.environ.get("RATE_LIMIT_PER_DAY", "10000"))
    )
    rate_config.setdefault("burst_limit", int(os.environ.get("RATE_LIMIT_BURST", "10")))

    # IP lists from environment (comma-separated)
    env_whitelist = os.environ.get("RATE_LIMIT_WHITELIST_IPS", "")
    env_blacklist = os.environ.get("RATE_LIMIT_BLACKLIST_IPS", "")

    rate_config.setdefault(
        "whitelist_ips", env_whitelist.split(",") if env_whitelist else []
    )
    rate_config.setdefault(
        "blacklist_ips", env_blacklist.split(",") if env_blacklist else []
    )

    # Advanced rate limiting features
    rate_config.setdefault(
        "enable_adaptive_limits",
        os.environ.get("RATE_LIMIT_ADAPTIVE", "false").lower() == "true",
    )
    rate_config.setdefault(
        "dos_protection_threshold",
        int(os.environ.get("RATE_LIMIT_DOS_THRESHOLD", "1000")),
    )
    rate_config.setdefault(
        "geo_blocking_enabled",
        os.environ.get("RATE_LIMIT_GEO_BLOCKING", "false").lower() == "true",
    )

    # API keys configuration
    if "api_keys" not in api_config:
        api_config["api_keys"] = {
            "max_keys_per_user": 10,
            "default_rate_limit": 1000,
            "key_length": 32,
            "auto_expire_days": 365,
            "require_permissions": True,
        }

    # Security configuration with environment overrides
    if "security" not in api_config:
        api_config["security"] = {}

    security_config = api_config["security"]
    security_config.setdefault(
        "require_https", os.environ.get("API_REQUIRE_HTTPS", "true").lower() == "true"
    )
    security_config.setdefault(
        "allowed_origins",
        os.environ.get("API_ALLOWED_ORIGINS", "localhost,127.0.0.1").split(","),
    )
    security_config.setdefault(
        "max_request_size_mb", int(os.environ.get("API_MAX_REQUEST_SIZE_MB", "10"))
    )
    security_config.setdefault(
        "enable_cors", os.environ.get("API_ENABLE_CORS", "false").lower() == "true"
    )
    security_config.setdefault("csrf_protection", True)
    security_config.setdefault("input_validation", True)
    security_config.setdefault("sql_injection_protection", True)
    security_config.setdefault("xss_protection", True)

    # Save updated configuration
    save_config(config)

    return api_config


def get_secure_database_url():
    """Get secure database URL with proper configuration.

    Returns:
        str: SQLAlchemy database URL with security options
    """
    api_config = get_api_security_config()
    db_config = api_config["database"]

    if db_config["type"] == "sqlite":
        db_path = db_config["path"]
        # Ensure directory exists with secure permissions
        db_file = Path(db_path)
        _ensure_secure_dir(db_file.parent)

        # SQLite URL with security options
        return f"sqlite:///{db_path}?check_same_thread=false"

    # Add support for other database types here
    # elif db_config["type"] == "postgresql":
    #     return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    else:
        raise ValueError(f"Unsupported database type: {db_config['type']}")


def get_redis_config():
    """Get Redis configuration.

    Returns:
        dict: Redis connection configuration
    """
    api_config = get_api_security_config()
    return api_config["redis"]


def backup_database():
    """Create a backup of the database if backup is enabled.

    Returns:
        bool: True if backup was created or not needed, False on error
    """
    try:
        api_config = get_api_security_config()
        db_config = api_config["database"]

        if not db_config.get("backup_enabled", True):
            return True

        if db_config["type"] == "sqlite":
            import shutil
            from datetime import datetime

            db_path = Path(db_config["path"])
            if not db_path.exists():
                return True  # No database to backup

            # Create backup directory
            backup_dir = db_path.parent / "backups"
            _ensure_secure_dir(backup_dir)

            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"security_api_backup_{timestamp}.db"

            shutil.copy2(db_path, backup_path)

            # Clean old backups
            retention_days = db_config.get("backup_retention_days", 30)
            cleanup_old_backups(backup_dir, retention_days)

            logging.getLogger(APP_NAME).info(f"Database backup created: {backup_path}")
            return True

    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Database backup failed: {e}")
        return False


def cleanup_old_backups(backup_dir: Path, retention_days: int):
    """Clean up old database backups.

    Args:
        backup_dir: Directory containing backups
        retention_days: Number of days to retain backups
    """
    try:
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(days=retention_days)

        for backup_file in backup_dir.glob("security_api_backup_*.db"):
            if backup_file.stat().st_mtime < cutoff_time.timestamp():
                backup_file.unlink()
                logging.getLogger(APP_NAME).info(f"Deleted old backup: {backup_file}")

    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Backup cleanup failed: {e}")
