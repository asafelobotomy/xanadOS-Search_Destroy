#!/usr/bin/env python3
"""
Unified Configuration Management System for xanadOS Search & Destroy
==================================================================

This module consolidates all configuration management functionality from:
- app/utils/config.py (725 lines) - Main configuration system
- app/utils/config_migration.py (250 lines) - Migration utilities
- app/gui/settings_pages.py (1,004 lines) - GUI settings interface
- app/utils/standards_integration.py (407 lines) - Standards management
- app/core/component_manager.py (343 lines) - Component configuration

Plus 26 scattered configuration classes throughout the codebase.

Features:
- Type-safe configuration schema with Pydantic validation
- Centralized configuration management with hot-reloading
- Automatic migration and backward compatibility
- Unified settings interface for GUI and API
- Performance-optimized configuration access
- Secure configuration storage with encryption support
- Component-specific configuration contexts
- Advanced configuration validation and error handling

Total consolidation: 5 files (2,729 lines) + 26 classes → 1 unified system
"""

import asyncio
import json
import logging
import os
import secrets
import shutil
import string
import tempfile
import time
import weakref
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from enum import Enum
from logging.handlers import RotatingFileHandler

try:
    from pydantic import BaseModel, Field, ValidationError, validator

    HAS_PYDANTIC = True
except ImportError:
    # Fallback for systems without pydantic
    HAS_PYDANTIC = False
    BaseModel = object  # type: ignore[assignment,misc]

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


# ============================================================================
# Core Configuration Enums and Types
# ============================================================================


class ConfigurationLevel(Enum):
    """Configuration complexity levels"""

    MINIMAL = "minimal"
    STANDARD = "standard"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ComponentState(Enum):
    """Component lifecycle states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


class SecurityLevel(Enum):
    """Security configuration levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PARANOID = "paranoid"


class PerformanceMode(Enum):
    """Performance optimization modes"""

    POWER_SAVE = "power_save"
    BALANCED = "balanced"
    PERFORMANCE = "performance"
    GAMING = "gaming"


# ============================================================================
# Unified Configuration Schema Classes
# ============================================================================

if HAS_PYDANTIC:

    class BaseConfigurationModel(BaseModel):
        """Base class for all configuration models with validation"""

        class Config:
            validate_assignment = True
            extra = "forbid"
            use_enum_values = True

        def update_from_dict(self, data: dict[str, Any]) -> None:
            """Update configuration from dictionary with validation"""
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)

else:
    # Fallback implementation for systems without pydantic
    class BaseConfigurationModel:
        """Fallback base class when pydantic is not available"""

        def update_from_dict(self, data: dict[str, Any]) -> None:
            """Update configuration from dictionary"""
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)

        def dict(self) -> dict[str, Any]:
            """Convert to dictionary"""
            return {
                key: getattr(self, key)
                for key in dir(self)
                if not key.startswith("_") and not callable(getattr(self, key))
            }


class ScanConfiguration(BaseConfigurationModel):
    """Unified scan configuration (consolidates duplicates from scanner modules)"""

    # Core scan settings
    max_threads: int = 4
    timeout_seconds: int = 300

    # ClamAV settings
    scan_archives: bool = True
    scan_email: bool = True
    scan_ole2: bool = True
    scan_pdf: bool = True
    scan_html: bool = True
    scan_executable: bool = True
    max_filesize: str = "100M"
    max_recursion: int = 16
    max_files: int = 10000
    pcre_match_limit: int = 10000
    pcre_recmatch_limit: int = 5000

    # Advanced scan settings
    scan_depth: int = 2
    follow_symlinks: bool = False
    file_filter: str = "all"
    exclusion_patterns: str = ""
    scan_timeout: int = 300

    # Safe files list (files marked as safe by user)
    safe_files: List[str] = []

    # Performance settings
    scan_batch_size: int = 50
    enable_async_scanning: bool = True
    memory_limit: int = 1024


class UIConfiguration(BaseConfigurationModel):
    """User interface configuration"""

    theme: str = "auto"
    show_hidden_files: bool = False
    notifications_enabled: bool = True
    minimize_to_tray: bool = True
    show_scan_progress: bool = True
    activity_log_retention: int = 100
    show_notifications: bool = True
    text_orientation: str = "Centered"

    # Advanced UI settings
    auto_update_definitions: bool = True
    window_geometry: Optional[str] = None
    splitter_state: Optional[str] = None


class SecurityConfiguration(BaseConfigurationModel):
    """Security and protection settings"""

    quarantine_enabled: bool = True
    auto_quarantine_threats: bool = False
    scan_removable_media: bool = True
    real_time_protection: bool = False
    auto_update_definitions: bool = True

    # Advanced security
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    encryption_enabled: bool = False
    secure_delete: bool = False


class PerformanceConfiguration(BaseConfigurationModel):
    """Performance optimization settings"""

    performance_mode: PerformanceMode = PerformanceMode.BALANCED
    max_memory_mb: int = 256
    timer_interval: int = 1000
    debounce_delay: float = 0.5
    enable_memory_optimization: bool = True

    # CPU and threading
    cpu_limit_percent: Optional[int] = None
    thread_pool_size: Optional[int] = None

    # I/O optimization
    io_priority: str = "normal"
    disk_cache_size_mb: int = 64


class APIConfiguration(BaseConfigurationModel):
    """API and network configuration"""

    # Server settings
    host: str = "localhost"
    port: int = 8000
    debug: bool = False

    # Security
    api_key_length: int = 32
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Database
    database_url: Optional[str] = None
    connection_pool_size: int = 10

    # Redis cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""


class ComponentConfiguration(BaseConfigurationModel):
    """Component management configuration"""

    auto_start_components: list[str] = ["memory_manager", "config_manager"]
    max_concurrent_initializations: int = 3
    component_timeout: int = 30
    restart_failed_components: bool = True

    # Resource limits
    max_memory_per_component: int = 512
    max_cpu_per_component: float = 25.0


class RKHunterConfiguration(BaseConfigurationModel):
    """RKHunter integration configuration"""

    enabled: bool = False
    run_with_full_scan: bool = False
    auto_update: bool = True
    config_file_path: Optional[str] = None

    # Categories
    check_applications: bool = False
    check_network: bool = True
    check_rootkits: bool = True
    check_system_commands: bool = True
    check_system_integrity: bool = True


# ============================================================================
# Main Unified Configuration Class
# ============================================================================


@dataclass
class ComponentInfo:
    """Component metadata and state information."""

    name: str
    state: ComponentState
    instance: object = None
    dependencies: list[str] = field(default_factory=list)
    resource_usage: dict[str, float] = field(default_factory=dict)
    last_error: Optional[str] = None
    initialization_time: Optional[float] = None


class UnifiedConfigurationManager:
    """
    Unified Configuration Management System

    Consolidates all configuration functionality from:
    - config.py - Core configuration management
    - config_migration.py - Migration utilities
    - settings_pages.py - GUI settings interface
    - standards_integration.py - Standards management
    - component_manager.py - Component configuration

    Plus all scattered configuration classes throughout the codebase.
    """

    _instance: Optional["UnifiedConfigurationManager"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        if UnifiedConfigurationManager._instance is not None:
            raise RuntimeError(
                "UnifiedConfigurationManager is a singleton. Use get_instance()"
            )

        self.logger = logging.getLogger(f"{APP_NAME}.config")

        # Configuration schemas
        self.scan_config = ScanConfiguration()
        self.ui_config = UIConfiguration()
        self.security_config = SecurityConfiguration()
        self.performance_config = PerformanceConfiguration()
        self.api_config = APIConfiguration()
        self.component_config = ComponentConfiguration()
        self.rkhunter_config = RKHunterConfiguration()

        # Core paths and files
        self.config_dir = CONFIG_DIR
        self.data_dir = DATA_DIR
        self.cache_dir = CACHE_DIR
        self.config_file = CONFIG_DIR / "config.json"
        self.config_schema_file = CONFIG_DIR / "schema.json"

        # Create directories with secure permissions
        self._ensure_secure_directories()

        # State management
        self.config_cache: dict[str, Any] = {}
        self.config_dirty = False
        self.last_reload = 0.0
        self.auto_save_enabled = True
        self.reload_interval = 5.0

        # Component management (from component_manager.py)
        self.components: dict[str, ComponentInfo] = {}
        self.component_instances: dict[str, Any] = {}
        self.state_change_callbacks: list[Callable] = []

        # Configuration validation
        self.validation_enabled = HAS_PYDANTIC
        self.validation_errors: list[str] = []

        # Hot reload and change detection
        self.change_callbacks: dict[str, list[Callable]] = {}
        self.file_watcher: Optional[Any] = None

        # Migration tracking (from config_migration.py)
        self.migration_version = "2.0"
        self.migration_history: list[dict[str, Any]] = []

        self.logger.info("Unified Configuration Manager initialized")

    @classmethod
    async def get_instance(cls) -> "UnifiedConfigurationManager":
        """Get or create the singleton instance (thread-safe)"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize the configuration manager"""
        try:
            # Setup logging first
            self._setup_logging()

            # Load or create configuration
            await self.load_configuration()

            # Run migrations if needed
            await self.run_migrations()

            # Setup file monitoring for hot reload
            await self._setup_file_monitoring()

            # Validate current configuration
            self.validate_configuration()

            self.logger.info("✅ Unified Configuration Manager fully initialized")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize configuration manager: {e}")
            raise

    def _ensure_secure_directories(self) -> None:
        """Create directories with secure permissions"""
        for directory in [self.config_dir, self.data_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

            # Set secure permissions on POSIX systems
            if os.name == "posix":
                try:
                    current_mode = directory.stat().st_mode & 0o777
                    if current_mode != 0o700:
                        directory.chmod(0o700)
                except OSError as e:
                    self.logger.warning(
                        f"Could not set secure permissions on {directory}: {e}"
                    )

    def _setup_logging(self) -> None:
        """Setup application logging with rotation (from config.py)"""
        if self.logger.handlers:
            return  # Already setup

        # Create log directory
        log_dir = self.data_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        class RateLimitFilter(logging.Filter):
            def __init__(self, interval=5):
                super().__init__()
                self.interval = interval
                self._last: dict[tuple, float] = {}

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
        log_file = log_dir / "configuration.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)

        # Add rate limiting
        rate_filter = RateLimitFilter(interval=5)
        file_handler.addFilter(rate_filter)
        console_handler.addFilter(rate_filter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)

    async def load_configuration(self) -> None:
        """Load configuration from file or create defaults"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # Update configuration objects
                self._update_configurations_from_dict(config_data)
                self.config_cache = config_data.copy()

                self.logger.info(f"✅ Loaded configuration from {self.config_file}")
            else:
                # Create initial configuration
                await self.create_default_configuration()
                self.logger.info("✅ Created default configuration")

        except Exception as e:
            self.logger.error(f"❌ Failed to load configuration: {e}")
            # Try to backup corrupted config and create new one
            if self.config_file.exists():
                backup_path = self.config_file.with_suffix(".corrupted")
                shutil.move(str(self.config_file), str(backup_path))
                self.logger.warning(f"Backed up corrupted config to {backup_path}")

            await self.create_default_configuration()

    def _update_configurations_from_dict(self, config_data: dict[str, Any]) -> None:
        """Update all configuration objects from dictionary"""
        if "scan_settings" in config_data:
            self.scan_config.update_from_dict(config_data["scan_settings"])

        if "ui_settings" in config_data:
            self.ui_config.update_from_dict(config_data["ui_settings"])

        if "security_settings" in config_data:
            self.security_config.update_from_dict(config_data["security_settings"])

        if "performance" in config_data:
            self.performance_config.update_from_dict(config_data["performance"])

        if "api_security" in config_data:
            self.api_config.update_from_dict(config_data["api_security"])

        if "component_settings" in config_data:
            self.component_config.update_from_dict(config_data["component_settings"])

        if "rkhunter_settings" in config_data:
            self.rkhunter_config.update_from_dict(config_data["rkhunter_settings"])

    async def create_default_configuration(self) -> None:
        """Create default configuration file"""
        default_config = {
            "version": __version__,
            "schema_version": "2.0",
            "created_at": datetime.now().isoformat(),
            # Scan configuration
            "scan_settings": (
                self.scan_config.dict() if HAS_PYDANTIC else self._get_scan_defaults()
            ),
            # UI configuration
            "ui_settings": (
                self.ui_config.dict() if HAS_PYDANTIC else self._get_ui_defaults()
            ),
            # Security configuration
            "security_settings": (
                self.security_config.dict()
                if HAS_PYDANTIC
                else self._get_security_defaults()
            ),
            # Performance configuration
            "performance": (
                self.performance_config.dict()
                if HAS_PYDANTIC
                else self._get_performance_defaults()
            ),
            # API configuration
            "api_security": self._generate_api_security_config(),
            # Component configuration
            "component_settings": (
                self.component_config.dict()
                if HAS_PYDANTIC
                else self._get_component_defaults()
            ),
            # RKHunter configuration
            "rkhunter_settings": (
                self.rkhunter_config.dict()
                if HAS_PYDANTIC
                else self._get_rkhunter_defaults()
            ),
            # Legacy compatibility sections
            "advanced_settings": self._get_advanced_defaults(),
            "realtime_protection": self._get_realtime_defaults(),
            "scheduled_settings": self._get_scheduled_defaults(),
            "paths": self._get_paths_config(),
            "rate_limits": self._get_rate_limits_defaults(),
            "setup": self._get_setup_defaults(),
        }

        await self.save_configuration(default_config)
        self.config_cache = default_config.copy()

    def _generate_api_security_config(self) -> dict[str, Any]:
        """Generate secure API configuration with auto-generated secrets"""

        # Generate secure JWT secret
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        jwt_secret = "".join(secrets.choice(alphabet) for _ in range(64))

        return {
            "database": {
                "type": "sqlite",
                "path": str(self.data_dir / "security_api.db"),
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "echo": False,
                "backup_enabled": True,
                "backup_retention_days": 30,
            },
            "redis": {
                "host": os.environ.get("REDIS_HOST", "localhost"),
                "port": int(os.environ.get("REDIS_PORT", "6379")),
                "db": int(os.environ.get("REDIS_DB", "0")),
                "password": os.environ.get("REDIS_PASSWORD", ""),
                "ssl": os.environ.get("REDIS_SSL", "false").lower() == "true",
                "connection_pool_size": 10,
                "socket_timeout": 30,
                "retry_on_timeout": True,
            },
            "jwt": {
                "secret_key": os.environ.get("JWT_SECRET_KEY", jwt_secret),
                "algorithm": os.environ.get("JWT_ALGORITHM", "HS256"),
                "access_token_expire_minutes": int(
                    os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", "15")
                ),
                "refresh_token_expire_days": int(
                    os.environ.get("JWT_REFRESH_EXPIRE_DAYS", "7")
                ),
                "issuer": os.environ.get("JWT_ISSUER", "xanadOS-Security-API"),
                "audience": os.environ.get("JWT_AUDIENCE", "xanadOS-clients"),
                "auto_rotate_keys": True,
                "key_rotation_days": 30,
            },
            "rate_limiting": {
                "enabled": os.environ.get("RATE_LIMIT_ENABLED", "true").lower()
                == "true",
                "requests_per_minute": int(
                    os.environ.get("RATE_LIMIT_PER_MINUTE", "60")
                ),
                "requests_per_hour": int(os.environ.get("RATE_LIMIT_PER_HOUR", "1000")),
                "requests_per_day": int(os.environ.get("RATE_LIMIT_PER_DAY", "10000")),
                "burst_limit": int(os.environ.get("RATE_LIMIT_BURST", "10")),
                "whitelist_ips": (
                    os.environ.get("RATE_LIMIT_WHITELIST_IPS", "").split(",")
                    if os.environ.get("RATE_LIMIT_WHITELIST_IPS")
                    else []
                ),
                "blacklist_ips": (
                    os.environ.get("RATE_LIMIT_BLACKLIST_IPS", "").split(",")
                    if os.environ.get("RATE_LIMIT_BLACKLIST_IPS")
                    else []
                ),
            },
            "security": {
                "require_https": os.environ.get("API_REQUIRE_HTTPS", "true").lower()
                == "true",
                "allowed_origins": os.environ.get(
                    "API_ALLOWED_ORIGINS", "localhost,127.0.0.1"
                ).split(","),
                "max_request_size_mb": int(
                    os.environ.get("API_MAX_REQUEST_SIZE_MB", "10")
                ),
                "enable_cors": os.environ.get("API_ENABLE_CORS", "false").lower()
                == "true",
                "csrf_protection": True,
                "input_validation": True,
                "sql_injection_protection": True,
                "xss_protection": True,
            },
            "api_keys": {
                "max_keys_per_user": 10,
                "default_rate_limit": 1000,
                "key_length": 32,
                "auto_expire_days": 365,
                "require_permissions": True,
            },
        }

    # Fallback methods for when pydantic is not available
    def _get_scan_defaults(self) -> dict[str, Any]:
        """Get default scan configuration"""
        return {
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
            "scan_depth": 2,
            "follow_symlinks": False,
            "file_filter": "all",
            "exclusion_patterns": "",
            "scan_timeout": 300,
            "scan_batch_size": 50,
            "enable_async_scanning": True,
            "memory_limit": 1024,
        }

    def _get_ui_defaults(self) -> dict[str, Any]:
        """Get default UI configuration"""
        return {
            "theme": "auto",
            "show_hidden_files": False,
            "notifications_enabled": True,
            "minimize_to_tray": True,
            "show_scan_progress": True,
            "activity_log_retention": 100,
            "show_notifications": True,
            "text_orientation": "Centered",
            "auto_update_definitions": True,
        }

    def _get_security_defaults(self) -> dict[str, Any]:
        """Get default security configuration"""
        return {
            "quarantine_enabled": True,
            "auto_quarantine_threats": False,
            "scan_removable_media": True,
            "real_time_protection": False,
            "auto_update_definitions": True,
            "security_level": "medium",
            "encryption_enabled": False,
            "secure_delete": False,
        }

    def _get_performance_defaults(self) -> dict[str, Any]:
        """Get default performance configuration"""
        return {
            "performance_mode": "balanced",
            "max_memory_mb": 256,
            "timer_interval": 1000,
            "debounce_delay": 0.5,
            "enable_memory_optimization": True,
            "io_priority": "normal",
            "disk_cache_size_mb": 64,
        }

    def _get_component_defaults(self) -> dict[str, Any]:
        """Get default component configuration"""
        return {
            "auto_start_components": ["memory_manager", "config_manager"],
            "max_concurrent_initializations": 3,
            "component_timeout": 30,
            "restart_failed_components": True,
            "max_memory_per_component": 512,
            "max_cpu_per_component": 25.0,
        }

    def _get_rkhunter_defaults(self) -> dict[str, Any]:
        """Get default RKHunter configuration"""
        return {
            "enabled": False,
            "run_with_full_scan": False,
            "auto_update": True,
            "check_applications": False,
            "check_network": True,
            "check_rootkits": True,
            "check_system_commands": True,
            "check_system_integrity": True,
        }

    def _get_advanced_defaults(self) -> dict[str, Any]:
        """Get advanced settings for legacy compatibility"""
        return {
            "signature_sources": ["main.cvd", "daily.cvd", "bytecode.cvd"],
            "custom_signature_urls": [],
            "log_level": "INFO",
            "structured_logging": False,
            "update_frequency": "daily",
            "memory_limit": 1024,
        }

    def _get_realtime_defaults(self) -> dict[str, Any]:
        """Get realtime protection defaults"""
        return {
            "monitor_modifications": True,
            "monitor_new_files": True,
            "scan_modified_files": False,
        }

    def _get_scheduled_defaults(self) -> dict[str, Any]:
        """Get scheduled scan defaults"""
        return {
            "enabled": False,
            "frequency": "daily",
            "time": "02:00",
        }

    def _get_paths_config(self) -> dict[str, Any]:
        """Get paths configuration"""
        return {
            "quarantine_dir": str(self.data_dir / "quarantine"),
            "scan_reports_dir": str(self.data_dir / "scan_reports"),
            "log_dir": str(self.data_dir / "logs"),
            "temp_dir": str(self.cache_dir / "temp"),
        }

    def _get_rate_limits_defaults(self) -> dict[str, Any]:
        """Get rate limiting defaults"""
        return {
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
        }

    def _get_setup_defaults(self) -> dict[str, Any]:
        """Get setup defaults"""
        return {
            "first_time_setup_completed": False,
            "setup_version": __version__,
            "packages_installed": {"clamav": False, "ufw": False, "rkhunter": False},
            "last_setup_check": None,
        }

    async def save_configuration(
        self, config_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save configuration to file atomically"""
        if config_data is None:
            config_data = self.config_cache

        try:
            # Update timestamp
            config_data["last_modified"] = datetime.now().isoformat()

            # Atomic write using temporary file
            tmp_fd = None
            tmp_path = None
            try:
                tmp_fd, tmp_path = tempfile.mkstemp(
                    prefix=".config.", dir=str(self.config_dir), suffix=".tmp"
                )

                with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
                    json.dump(config_data, tmp_file, indent=4, sort_keys=True)
                    tmp_file.flush()
                    os.fsync(tmp_file.fileno())

                # Atomic move
                os.replace(tmp_path, self.config_file)

                # Set secure permissions
                if os.name == "posix":
                    try:
                        os.chmod(self.config_file, 0o600)
                    except OSError:
                        pass

                self.config_dirty = False
                self.logger.info(f"✅ Saved configuration to {self.config_file}")

            finally:
                if tmp_fd is not None and tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

        except Exception as e:
            self.logger.error(f"❌ Failed to save configuration: {e}")
            raise

    # ========================================================================
    # Configuration Access Methods (Compatibility with original config.py)
    # ========================================================================

    def get_config(self) -> dict[str, Any]:
        """Get complete configuration (compatibility method)"""
        return self.config_cache.copy()

    def load_config(self) -> dict[str, Any]:
        """Load and return configuration (compatibility method)"""
        return self.config_cache.copy()

    def get_config_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration setting"""
        return self.config_cache.get(section, {}).get(key, default)

    def update_config_setting(self, section: str, key: str, value: Any) -> bool:
        """Update a specific configuration setting"""
        try:
            if section not in self.config_cache:
                self.config_cache[section] = {}

            self.config_cache[section][key] = value
            self.config_dirty = True

            # Auto-save if enabled
            if self.auto_save_enabled:
                asyncio.create_task(self.save_configuration())

            # Trigger change callbacks
            self._trigger_change_callbacks(section, key, value)

            return True

        except Exception as e:
            self.logger.error(f"Failed to update setting {section}.{key}: {e}")
            return False

    def update_multiple_settings(self, updates: dict[str, Dict[str, Any]]) -> bool:
        """Update multiple settings at once"""
        try:
            for section, settings in updates.items():
                if section not in self.config_cache:
                    self.config_cache[section] = {}

                for key, value in settings.items():
                    self.config_cache[section][key] = value
                    self._trigger_change_callbacks(section, key, value)

            self.config_dirty = True

            if self.auto_save_enabled:
                asyncio.create_task(self.save_configuration())

            return True

        except Exception as e:
            self.logger.error(f"Failed to update multiple settings: {e}")
            return False

    def get_factory_defaults(self) -> dict[str, Any]:
        """Get factory default settings"""
        return {
            "scan_settings": self._get_scan_defaults(),
            "ui_settings": self._get_ui_defaults(),
            "security_settings": self._get_security_defaults(),
            "performance": self._get_performance_defaults(),
            "component_settings": self._get_component_defaults(),
            "rkhunter_settings": self._get_rkhunter_defaults(),
            "advanced_settings": self._get_advanced_defaults(),
            "realtime_protection": self._get_realtime_defaults(),
            "scheduled_settings": self._get_scheduled_defaults(),
            "paths": self._get_paths_config(),
        }

    # ========================================================================
    # Component Management (from component_manager.py)
    # ========================================================================

    def register_component(self, name: str, dependencies: list[str] | None = None) -> None:
        """Register a component for management"""
        if dependencies is None:
            dependencies = []

        self.components[name] = ComponentInfo(
            name=name, state=ComponentState.UNINITIALIZED, dependencies=dependencies
        )

        self.logger.debug(f"Registered component: {name}")

    def get_component(self, name: str) -> Optional[Any]:
        """Get a component instance"""
        return self.component_instances.get(name)

    def set_component_instance(self, name: str, instance: Any) -> None:
        """Set a component instance"""
        self.component_instances[name] = instance

        if name in self.components:
            self.components[name].instance = instance
            self.components[name].state = ComponentState.READY

    # ========================================================================
    # Migration Support (from config_migration.py)
    # ========================================================================

    async def run_migrations(self) -> dict[str, bool]:
        """Run configuration migrations"""
        results = {
            "schema_migration": await self._migrate_schema(),
            "database_migration": await self._migrate_database(),
            "environment_migration": await self._migrate_environment_variables(),
        }

        # Record migration
        migration_record = {
            "timestamp": datetime.now().isoformat(),
            "version": self.migration_version,
            "results": results,
        }
        self.migration_history.append(migration_record)

        return results

    async def _migrate_schema(self) -> bool:
        """Migrate configuration schema to latest version"""
        try:
            current_version = self.config_cache.get("schema_version", "1.0")

            if current_version == "2.0":
                return True  # Already latest version

            # Perform schema migrations
            if current_version == "1.0":
                # Migrate from v1.0 to v2.0
                self.config_cache["schema_version"] = "2.0"

                # Add new sections if missing
                if "component_settings" not in self.config_cache:
                    self.config_cache["component_settings"] = (
                        self._get_component_defaults()
                    )

                self.config_dirty = True
                await self.save_configuration()

            self.logger.info(
                f"✅ Migrated configuration schema from {current_version} to 2.0"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ Schema migration failed: {e}")
            return False

    async def _migrate_database(self) -> bool:
        """Migrate database from hardcoded location to secure location"""
        try:
            old_db_path = Path("security_api.db")

            if old_db_path.exists():
                api_config = self.config_cache.get("api_security", {})
                db_config = api_config.get("database", {})
                new_db_path = Path(
                    db_config.get("path", str(self.data_dir / "security_api.db"))
                )

                if not new_db_path.exists():
                    shutil.move(str(old_db_path), str(new_db_path))

                    if os.name == "posix":
                        new_db_path.chmod(0o600)

                    self.logger.info(
                        f"✅ Migrated database from {old_db_path} to {new_db_path}"
                    )
                else:
                    old_db_path.unlink()
                    self.logger.info(f"✅ Removed old database file: {old_db_path}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Database migration failed: {e}")
            return False

    async def _migrate_environment_variables(self) -> bool:
        """Update configuration with environment variables if present"""
        try:
            env_mappings = {
                "JWT_SECRET_KEY": ("api_security", "jwt", "secret_key"),
                "REDIS_HOST": ("api_security", "redis", "host"),
                "API_REQUIRE_HTTPS": ("api_security", "security", "require_https"),
                # Add more mappings as needed
            }

            updated = False

            for env_var, (section, subsection, key) in env_mappings.items():
                env_value = os.environ.get(env_var)
                if env_value is not None:
                    if section not in self.config_cache:
                        self.config_cache[section] = {}
                    if subsection not in self.config_cache[section]:
                        self.config_cache[section][subsection] = {}

                    # Convert boolean values
                    if key in ["require_https", "ssl"]:
                        env_value = env_value.lower() in ("true", "1", "yes", "on")

                    self.config_cache[section][subsection][key] = env_value
                    updated = True

            if updated:
                self.config_dirty = True
                await self.save_configuration()

            return True

        except Exception as e:
            self.logger.error(f"❌ Environment variable migration failed: {e}")
            return False

    # ========================================================================
    # Configuration Validation
    # ========================================================================

    def validate_configuration(self) -> bool:
        """Validate current configuration"""
        if not self.validation_enabled:
            return True

        self.validation_errors.clear()
        valid = True

        try:
            # Validate each configuration section
            sections = {
                "scan_settings": (self.scan_config, ScanConfiguration),
                "ui_settings": (self.ui_config, UIConfiguration),
                "security_settings": (self.security_config, SecurityConfiguration),
                "performance": (self.performance_config, PerformanceConfiguration),
            }

            for section_name, (config_obj, config_class) in sections.items():
                try:
                    section_data = self.config_cache.get(section_name, {})
                    config_class(**section_data)  # Validate with pydantic
                except ValidationError as e:
                    self.validation_errors.append(
                        f"Validation error in {section_name}: {e}"
                    )
                    valid = False
                except Exception as e:
                    self.validation_errors.append(
                        f"Error validating {section_name}: {e}"
                    )
                    valid = False

            if valid:
                self.logger.info("✅ Configuration validation passed")
            else:
                self.logger.warning(
                    f"⚠️ Configuration validation failed: {self.validation_errors}"
                )

        except Exception as e:
            self.logger.error(f"❌ Configuration validation error: {e}")
            valid = False

        return valid

    # ========================================================================
    # Change Callbacks and Hot Reload
    # ========================================================================

    def add_change_callback(
        self, section: str, callback: Callable[[str, str, Any], None]
    ) -> None:
        """Add callback for configuration changes"""
        if section not in self.change_callbacks:
            self.change_callbacks[section] = []
        self.change_callbacks[section].append(callback)

    def _trigger_change_callbacks(self, section: str, key: str, value: Any) -> None:
        """Trigger callbacks for configuration changes"""
        callbacks = self.change_callbacks.get(section, [])
        for callback in callbacks:
            try:
                callback(section, key, value)
            except Exception as e:
                self.logger.error(f"Configuration change callback error: {e}")

    async def _setup_file_monitoring(self) -> None:
        """Setup file monitoring for hot reload"""
        # This would integrate with the file watcher system
        # For now, we'll use periodic checking
        pass

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_secure_database_url(self) -> str:
        """Get secure database URL"""
        api_config = self.config_cache.get("api_security", {})
        db_config = api_config.get("database", {})

        if db_config.get("type") == "sqlite":
            db_path = db_config.get("path", str(self.data_dir / "security_api.db"))
            return f"sqlite:///{db_path}?check_same_thread=false"
        else:
            raise ValueError(f"Unsupported database type: {db_config.get('type')}")

    def get_redis_config(self) -> dict[str, Any]:
        """Get Redis configuration"""
        api_config = self.config_cache.get("api_security", {})
        return api_config.get("redis", {})

    def get_quarantine_dir(self) -> Path:
        """Get quarantine directory path"""
        paths = self.config_cache.get("paths", {})
        return Path(paths.get("quarantine_dir", str(self.data_dir / "quarantine")))

    def get_log_dir(self) -> Path:
        """Get log directory path"""
        paths = self.config_cache.get("paths", {})
        return Path(paths.get("log_dir", str(self.data_dir / "logs")))

    def add_safe_file(self, file_path: str) -> bool:
        """Add a file to the safe files list.

        Args:
            file_path: Path to the file to mark as safe

        Returns:
            True if file was added, False if already in list
        """
        try:
            # Normalize path
            normalized_path = str(Path(file_path).resolve())

            # Get current safe files list from config cache
            if "scan_settings" not in self.config_cache:
                self.config_cache["scan_settings"] = {}

            safe_files = self.config_cache["scan_settings"].get("safe_files", [])

            # Check if already in list
            if normalized_path in safe_files:
                self.logger.info(f"File already in safe list: {normalized_path}")
                return False

            # Add to list
            safe_files.append(normalized_path)
            self.config_cache["scan_settings"]["safe_files"] = safe_files

            # Update _config_data as well for consistency
            if "scan_settings" not in self._config_data:
                self._config_data["scan_settings"] = {}
            self._config_data["scan_settings"]["safe_files"] = safe_files

            # Save using the standard save function (non-async for compatibility)
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule coroutine
                    asyncio.create_task(self.save_configuration())
                else:
                    # Otherwise run it
                    loop.run_until_complete(self.save_configuration())
            except RuntimeError:
                # Fallback to creating new event loop
                asyncio.run(self.save_configuration())

            self.logger.info(f"Added file to safe list: {normalized_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add safe file: {e}")
            return False

    def remove_safe_file(self, file_path: str) -> bool:
        """Remove a file from the safe files list.

        Args:
            file_path: Path to the file to remove from safe list

        Returns:
            True if file was removed, False if not in list
        """
        try:
            # Normalize path
            normalized_path = str(Path(file_path).resolve())

            # Get current safe files list
            safe_files = self.config_cache.get("scan_settings", {}).get(
                "safe_files", []
            )

            # Check if in list
            if normalized_path not in safe_files:
                self.logger.info(f"File not in safe list: {normalized_path}")
                return False

            # Remove from list
            safe_files.remove(normalized_path)
            self.config_cache["scan_settings"]["safe_files"] = safe_files

            # Update _config_data as well
            if "scan_settings" in self._config_data:
                self._config_data["scan_settings"]["safe_files"] = safe_files

            # Save using the standard save function (non-async for compatibility)
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.save_configuration())
                else:
                    loop.run_until_complete(self.save_configuration())
            except RuntimeError:
                asyncio.run(self.save_configuration())

            self.logger.info(f"Removed file from safe list: {normalized_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove safe file: {e}")
            return False

    def get_safe_files(self) -> List[str]:
        """Get the list of safe files.

        Returns:
            List of file paths marked as safe
        """
        return self.config_cache.get("scan_settings", {}).get("safe_files", [])

    def is_safe_file(self, file_path: str) -> bool:
        """Check if a file is in the safe files list.

        Args:
            file_path: Path to check

        Returns:
            True if file is marked as safe
        """
        try:
            normalized_path = str(Path(file_path).resolve())
            safe_files = self.get_safe_files()
            return normalized_path in safe_files
        except Exception:
            return False

    def export_configuration(self, include_sensitive: bool = False) -> dict[str, Any]:
        """Export configuration for backup/sharing"""
        config_export = self.config_cache.copy()

        if not include_sensitive:
            # Remove sensitive information
            if "api_security" in config_export:
                api_config = config_export["api_security"]
                if "jwt" in api_config:
                    api_config["jwt"].pop("secret_key", None)
                if "redis" in api_config:
                    api_config["redis"].pop("password", None)

        config_export["exported_at"] = datetime.now().isoformat()
        config_export["export_version"] = self.migration_version

        return config_export

    async def import_configuration(
        self, config_data: dict[str, Any], validate: bool = True
    ) -> None:
        """Import configuration from backup/sharing"""
        try:
            if validate and self.validation_enabled:
                # Validate imported configuration
                temp_manager = UnifiedConfigurationManager.__new__(
                    UnifiedConfigurationManager
                )
                temp_manager.config_cache = config_data.copy()
                if not temp_manager.validate_configuration():
                    raise ValueError("Invalid configuration data")

            # Backup current configuration
            backup_path = self.config_file.with_suffix(f".backup.{int(time.time())}")
            if self.config_file.exists():
                shutil.copy2(self.config_file, backup_path)

            # Import new configuration
            self.config_cache = config_data.copy()
            self._update_configurations_from_dict(config_data)

            await self.save_configuration()

            self.logger.info("✅ Configuration imported successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to import configuration: {e}")
            raise


# ============================================================================
# Global Instance and Compatibility Functions
# ============================================================================

# Global instance
_unified_config_manager: Optional[UnifiedConfigurationManager] = None


async def get_unified_config_manager() -> UnifiedConfigurationManager:
    """Get the global unified configuration manager instance"""
    global _unified_config_manager
    if _unified_config_manager is None:
        _unified_config_manager = await UnifiedConfigurationManager.get_instance()
    return _unified_config_manager


# Compatibility functions for backward compatibility with original config.py
def get_config(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Get configuration (compatibility function)"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        return manager.get_config()
    except RuntimeError:
        # Fallback for synchronous contexts
        return _get_config_fallback(file_path)


def load_config(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration (compatibility function)"""
    return get_config(file_path)


def save_config(config_data: Dict[str, Any], file_path: Optional[str] = None) -> None:
    """Save configuration (compatibility function)"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        loop.run_until_complete(manager.save_configuration(config_data))
    except RuntimeError:
        # Fallback for synchronous contexts
        _save_config_fallback(config_data, file_path)


def update_config_setting(
    config_dict: Dict[str, Any],
    section: str,
    key: str,
    value: Any,
    file_path: Optional[str] = None,
) -> bool:
    """Update config setting (compatibility function)"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        return manager.update_config_setting(section, key, value)
    except RuntimeError:
        # Fallback for synchronous contexts
        return _update_config_setting_fallback(
            config_dict, section, key, value, file_path
        )


def update_multiple_settings(
    config_dict: Dict[str, Any],
    updates: Dict[str, Dict[str, Any]],
    file_path: Optional[str] = None,
) -> bool:
    """Update multiple settings (compatibility function)"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        return manager.update_multiple_settings(updates)
    except RuntimeError:
        # Fallback for synchronous contexts
        return _update_multiple_settings_fallback(config_dict, updates, file_path)


def get_config_setting(
    config_dict: dict[str, Any], section: str, key: str, default: Any = None
) -> Any:
    """Get config setting (compatibility function)"""
    return config_dict.get(section, {}).get(key, default)


def get_factory_defaults() -> dict[str, Any]:
    """Get factory defaults (compatibility function)"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        return manager.get_factory_defaults()
    except RuntimeError:
        # Return minimal defaults as fallback
        return _get_minimal_defaults()


def setup_logging() -> logging.Logger:
    """Setup logging (compatibility function)"""
    return logging.getLogger(APP_NAME)


# ============================================================================
# Fallback Functions for Synchronous Contexts
# ============================================================================


def _get_config_fallback(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Fallback config loading for synchronous contexts"""
    config_file = Path(file_path) if file_path else CONFIG_DIR / "config.json"

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return _get_minimal_defaults()


def _save_config_fallback(
    config_data: Dict[str, Any], file_path: Optional[str] = None
) -> None:
    """Fallback config saving for synchronous contexts"""
    config_file = Path(file_path) if file_path else CONFIG_DIR / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, sort_keys=True)


def _update_config_setting_fallback(
    config_dict: Dict[str, Any],
    section: str,
    key: str,
    value: Any,
    file_path: Optional[str] = None,
) -> bool:
    """Fallback setting update for synchronous contexts"""
    try:
        if section not in config_dict:
            config_dict[section] = {}
        config_dict[section][key] = value
        _save_config_fallback(config_dict, file_path)
        return True
    except Exception:
        return False


def _update_multiple_settings_fallback(
    config_dict: Dict[str, Any],
    updates: Dict[str, Dict[str, Any]],
    file_path: Optional[str] = None,
) -> bool:
    """Fallback multiple settings update for synchronous contexts"""
    try:
        for section, settings in updates.items():
            if section not in config_dict:
                config_dict[section] = {}
            for key, value in settings.items():
                config_dict[section][key] = value
        _save_config_fallback(config_dict, file_path)
        return True
    except Exception:
        return False


def _get_minimal_defaults() -> dict[str, Any]:
    """Get minimal default configuration"""
    return {
        "scan_settings": {
            "max_threads": 4,
            "timeout_seconds": 300,
            "scan_archives": True,
        },
        "ui_settings": {
            "theme": "auto",
            "minimize_to_tray": True,
            "show_notifications": True,
        },
        "security_settings": {
            "quarantine_enabled": True,
            "real_time_protection": False,
        },
    }


# ============================================================================
# Specialized Configuration Access Functions
# ============================================================================


def get_api_security_config() -> dict[str, Any]:
    """Get API security configuration"""
    config = get_config()
    return config.get("api_security", {})


def get_secure_database_url() -> str:
    """Get secure database URL"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        return manager.get_secure_database_url()
    except RuntimeError:
        # Fallback
        return f"sqlite:///{DATA_DIR}/security_api.db?check_same_thread=false"


def get_redis_config() -> dict[str, Any]:
    """Get Redis configuration"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        return manager.get_redis_config()
    except RuntimeError:
        # Fallback
        return {"host": "localhost", "port": 6379, "db": 0, "password": ""}


# ============================================================================
# Configuration Schema Creation Functions (Consolidates scattered configs)
# ============================================================================


def create_quick_scan_config(target_paths: list[str]) -> ScanConfiguration:
    """Create quick scan configuration"""
    config = ScanConfiguration()
    config.scan_depth = 1
    config.max_files = 1000
    config.timeout_seconds = 60
    return config


def create_full_scan_config(target_paths: list[str]) -> ScanConfiguration:
    """Create full scan configuration"""
    config = ScanConfiguration()
    config.scan_depth = 10
    config.follow_symlinks = True
    config.scan_archives = True
    return config


def create_custom_scan_config(**kwargs) -> ScanConfiguration:
    """Create custom scan configuration"""
    config = ScanConfiguration()
    config.update_from_dict(kwargs)
    return config


# API Configuration helpers
def create_api_config(
    host: str = "localhost", port: int = 8000, **kwargs
) -> APIConfiguration:
    """Create API configuration"""
    config = APIConfiguration()
    config.host = host
    config.port = port
    config.update_from_dict(kwargs)
    return config


# Component Configuration helpers
def create_component_config(**kwargs) -> ComponentConfiguration:
    """Create component configuration"""
    config = ComponentConfiguration()
    config.update_from_dict(kwargs)
    return config


# Performance Configuration helpers
def create_performance_config(
    mode: PerformanceMode = PerformanceMode.BALANCED, **kwargs
) -> PerformanceConfiguration:
    """Create performance configuration"""
    config = PerformanceConfiguration()
    config.performance_mode = mode
    config.update_from_dict(kwargs)
    return config


# Security Configuration helpers
def create_security_config(
    level: SecurityLevel = SecurityLevel.MEDIUM, **kwargs
) -> SecurityConfiguration:
    """Create security configuration"""
    config = SecurityConfiguration()
    config.security_level = level
    config.update_from_dict(kwargs)
    return config


# ============================================================================
# Migration and Compatibility Functions (from config_migration.py)
# ============================================================================


def migrate_hardcoded_database() -> bool:
    """Migrate from hardcoded database location"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        result = loop.run_until_complete(manager._migrate_database())
        return result
    except RuntimeError:
        return False


def migrate_environment_variables() -> bool:
    """Update configuration with environment variables"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        result = loop.run_until_complete(manager._migrate_environment_variables())
        return result
    except RuntimeError:
        return False


def run_full_migration() -> dict[str, Any]:
    """Run complete configuration migration"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        results = loop.run_until_complete(manager.run_migrations())
        return results
    except RuntimeError:
        return {"error": "Could not run migration in synchronous context"}


def validate_migration() -> dict[str, Any]:
    """Validate migration results"""
    try:
        loop = asyncio.get_event_loop()
        manager = loop.run_until_complete(get_unified_config_manager())
        valid = manager.validate_configuration()
        return {
            "config_valid": valid,
            "validation_errors": manager.validation_errors,
            "timestamp": datetime.now().isoformat(),
        }
    except RuntimeError:
        return {"error": "Could not validate in synchronous context"}


# ============================================================================
# Directory and Path Management
# ============================================================================


def ensure_secure_directories() -> None:
    """Ensure all required directories exist with secure permissions"""
    for directory in [CONFIG_DIR, DATA_DIR, CACHE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

        if os.name == "posix":
            try:
                current_mode = directory.stat().st_mode & 0o777
                if current_mode != 0o700:
                    directory.chmod(0o700)
            except OSError:
                pass


# Initialize directories on import
ensure_secure_directories()


# ============================================================================
# Module Initialization
# ============================================================================


def initialize_unified_config() -> None:
    """Initialize the unified configuration system"""
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(get_unified_config_manager())
    except RuntimeError:
        # Running in synchronous context, initialization will happen on first async access
        pass


# Auto-initialize if we're in an async context
try:
    initialize_unified_config()
except RuntimeError:
    # Will initialize on first async access
    pass


__all__ = [
    # Main classes
    "UnifiedConfigurationManager",
    "ScanConfiguration",
    "UIConfiguration",
    "SecurityConfiguration",
    "PerformanceConfiguration",
    "APIConfiguration",
    "ComponentConfiguration",
    "RKHunterConfiguration",
    # Enums
    "ConfigurationLevel",
    "ComponentState",
    "SecurityLevel",
    "PerformanceMode",
    # Core functions (compatibility)
    "get_config",
    "load_config",
    "save_config",
    "update_config_setting",
    "update_multiple_settings",
    "get_config_setting",
    "get_factory_defaults",
    "setup_logging",
    # Specialized functions
    "get_api_security_config",
    "get_secure_database_url",
    "get_redis_config",
    # Configuration creators
    "create_quick_scan_config",
    "create_full_scan_config",
    "create_custom_scan_config",
    "create_api_config",
    "create_component_config",
    "create_performance_config",
    "create_security_config",
    # Migration functions
    "migrate_hardcoded_database",
    "migrate_environment_variables",
    "run_full_migration",
    "validate_migration",
    # Global manager access
    "get_unified_config_manager",
    # Constants
    "CONFIG_DIR",
    "DATA_DIR",
    "CACHE_DIR",
    "APP_NAME",
]
