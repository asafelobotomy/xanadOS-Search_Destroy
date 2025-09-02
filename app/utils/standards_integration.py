#!/usr/bin/env python3
"""
Standardized Libraries Integration - Main configuration and utilities
=====================================================================
This module provides centralized access to all standardized libraries:
- System paths management
- Security standards enforcement
- Process management
- Performance optimization
- Configuration management
This creates a unified interface for compatibility and performance.
"""

import json
import logging
import os
import platform
import sys
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Union

from .performance_standards import (
    PERFORMANCE_OPTIMIZER,
    PerformanceLevel,
    optimize_for_scanning,
)
from .process_management import PROCESS_MANAGER, ProcessConfig
from .security_standards import SecurityLevel, SecurityStandards
from .system_paths import ApplicationPaths, SystemPaths


class ConfigurationLevel(Enum):
    """Configuration complexity levels"""

    MINIMAL = "minimal"
    STANDARD = "standard"
    ADVANCED = "advanced"
    EXPERT = "expert"


class StandardsManager:
    """Unified manager for all standardized libraries"""

    def __init__(self, app_name: str = "xanados-search-destroy"):
        self.app_name = app_name
        self.app_paths = ApplicationPaths(app_name)
        self.security_standards = SecurityStandards()
        self.process_manager = PROCESS_MANAGER
        self.performance_optimizer = PERFORMANCE_OPTIMIZER

        # Initialize directories
        self.app_paths.ensure_all_directories()

        # Setup logging
        self._setup_logging()

        # Current configuration
        self._config_cache = {}
        self._config_dirty = False

    def _setup_logging(self):
        """Setup centralized logging"""
        log_dir = self.app_paths.get_path("logs")
        log_file = log_dir / "standards.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        self.logger = logging.getLogger(f"{self.app_name}.standards")

    def get_unified_config(
        self, level: ConfigurationLevel = ConfigurationLevel.STANDARD
    ) -> Dict[str, Any]:
        """Get unified configuration for all standards"""

        # Map configuration levels to specific settings
        level_mappings = {
            ConfigurationLevel.MINIMAL: {
                "security_level": SecurityLevel.LOW,
                "performance_level": PerformanceLevel.BATTERY_SAVER,
                "max_threads": 2,
                "max_file_size": 50 * 1024 * 1024,  # 50MB
                "scan_depth": 3,
            },
            ConfigurationLevel.STANDARD: {
                "security_level": SecurityLevel.MEDIUM,
                "performance_level": PerformanceLevel.BALANCED,
                "max_threads": 4,
                "max_file_size": 100 * 1024 * 1024,  # 100MB
                "scan_depth": 5,
            },
            ConfigurationLevel.ADVANCED: {
                "security_level": SecurityLevel.HIGH,
                "performance_level": PerformanceLevel.PERFORMANCE,
                "max_threads": 8,
                "max_file_size": 200 * 1024 * 1024,  # 200MB
                "scan_depth": 8,
            },
            ConfigurationLevel.EXPERT: {
                "security_level": SecurityLevel.CRITICAL,
                "performance_level": PerformanceLevel.MAXIMUM,
                "max_threads": 16,
                "max_file_size": 500 * 1024 * 1024,  # 500MB
                "scan_depth": 12,
            },
        }

        base_settings = level_mappings[level]
        security_policy = self.security_standards.get_security_policy(
            base_settings["security_level"]
        )
        performance_settings = self.performance_optimizer.optimize_for_level(
            base_settings["performance_level"]
        )

        # Obtain app version from centralized source
        try:
            from app import get_version as _get_version  # local import

            _app_version = _get_version()
        except Exception:
            _app_version = "dev"

        unified_config = {
            "application": {
                "name": self.app_name,
                "version": _app_version,
                "config_level": level.value,
            },
            "paths": {
                "config_dir": str(self.app_paths.config_dir),
                "data_dir": str(self.app_paths.data_dir),
                "cache_dir": str(self.app_paths.cache_dir),
                "quarantine_dir": str(self.app_paths.quarantine_dir),
                "logs_dir": str(self.app_paths.logs_dir),
                "temp_dir": str(self.app_paths.temp_dir),
                "system_temp": SystemPaths.get_system_temp_dir(),
            },
            "security": {
                "level": base_settings["security_level"].value,
                "policy": asdict(security_policy),
                "allowed_binaries": list(self.security_standards.ALLOWED_BINARIES),
                "forbidden_paths": list(SystemPaths.FORBIDDEN_PATHS),
                "scan_paths": SystemPaths.get_common_scan_paths(),
                "excluded_paths": SystemPaths.get_excluded_scan_paths(),
            },
            "performance": {
                "level": base_settings["performance_level"].value,
                "max_threads": base_settings["max_threads"],
                "max_file_size": base_settings["max_file_size"],
                "scan_depth": base_settings["scan_depth"],
                "settings": performance_settings,
                "optimal_threads": self.performance_optimizer.get_optimal_thread_count(),
            },
            "process": {
                "timeout_default": 300,
                "safe_path": SystemPaths.SAFE_PATH,
                "max_concurrent": base_settings["max_threads"],
            },
        }

        return unified_config

    def save_config(self, config: Dict[str, Any], config_type: str = "main") -> bool:
        """Save configuration to file"""
        try:
            if config_type == "main":
                config_file = self.app_paths.main_config_file
            elif config_type == "user":
                config_file = self.app_paths.user_config_file
            else:
                config_file = self.app_paths.config_dir / f"{config_type}.json"

            # Ensure config directory exists
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, default=str)

            self.loginfo(
                "Configuration saved to %s".replace("%s", "{config_file}").replace(
                    "%d", "{config_file}"
                )
            )
            return True

        except Exception:
            self.logerror(
                "Failed to save configuration: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return False

    def load_config(self, config_type: str = "main") -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if config_type == "main":
                config_file = self.app_paths.main_config_file
            elif config_type == "user":
                config_file = self.app_paths.user_config_file
            else:
                config_file = self.app_paths.config_dir / f"{config_type}.json"

            if not config_file.exists():
                # Return default configuration
                return self.get_unified_config()

            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)

            self.loginfo(
                "Configuration loaded from %s".replace("%s", "{config_file}").replace(
                    "%d", "{config_file}"
                )
            )
            return config

        except Exception:
            self.logerror(
                "Failed to load configuration: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return self.get_unified_config()

    def validate_paths(self) -> Dict[str, bool]:
        """Validate all application paths"""
        validation_results = {}

        paths_to_check = [
            ("config_dir", self.app_paths.config_dir),
            ("data_dir", self.app_paths.data_dir),
            ("cache_dir", self.app_paths.cache_dir),
            ("quarantine_dir", self.app_paths.quarantine_dir),
            ("logs_dir", self.app_paths.logs_dir),
            ("temp_dir", self.app_paths.temp_dir),
        ]

        for name, path in paths_to_check:
            validation_results[name] = {
                "exists": path.exists(),
                "is_dir": path.is_dir() if path.exists() else False,
                "writable": os.access(path, os.W_OK) if path.exists() else False,
                "secure": self._check_path_security(path),
            }

        return validation_results

    def _check_path_security(self, path: Path) -> bool:
        """Check if path has secure permissions"""
        try:
            if not path.exists():
                return False

            stat_info = path.stat()
            mode = stat_info.st_mode & 0o777

            # Should be 700 (owner only)
            return mode == 0o700

        except Exception:
            return False

    def get_system_compatibility_info(self) -> Dict[str, Any]:
        """Get system compatibility information"""

        return {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable,
                "platform": sys.platform,
            },
            "paths": {
                "temp_dir": SystemPaths.get_system_temp_dir(),
                "home_dir": str(SystemPaths.get_user_home()),
                "xdg_config": str(SystemPaths.XDG_CONFIG_HOME),
                "xdg_data": str(SystemPaths.XDG_DATA_HOME),
                "xdg_cache": str(SystemPaths.XDG_CACHE_HOME),
            },
            "security": {
                "executables_found": self._check_security_executables(),
                "permissions_ok": all(self.validate_paths().values()),
            },
            "performance": {
                "cpu_count": self.performance_optimizer.get_current_metrics().cpu_percent,
                "optimal_threads": self.performance_optimizer.get_optimal_thread_count(),
            },
        }

    def _check_security_executables(self) -> Dict[str, bool]:
        """Check availability of security executables"""
        executables = ["clamscan", "freshclam", "rkhunter", "sudo"]  # pkexec removed
        results = {}

        for exe in executables:
            path = SystemPaths.get_executable_path(exe)
            results[exe] = path is not None

        return results

    def optimize_for_environment(self) -> Dict[str, Any]:
        """Optimize configuration based on current environment"""
        system_info = self.get_system_compatibility_info()
        current_metrics = self.performance_optimizer.get_current_metrics()

        # Determine optimal configuration level
        if current_metrics.memory_percent > 80:
            recommended_level = ConfigurationLevel.MINIMAL
        elif current_metrics.cpu_percent > 70:
            recommended_level = ConfigurationLevel.STANDARD
        else:
            recommended_level = ConfigurationLevel.ADVANCED

        # Generate optimized configuration
        optimized_config = self.get_unified_config(recommended_level)

        # Add environment-specific adjustments
        optimized_config["environment_adjustments"] = {
            "recommended_level": recommended_level.value,
            "reasons": self._get_optimization_reasons(current_metrics),
            "system_compatibility": system_info,
        }

        return optimized_config

    def _get_optimization_reasons(self, metrics) -> List[str]:
        """Get reasons for optimization recommendations"""
        reasons = []

        if metrics.memory_percent > 80:
            reasons.append("High memory usage detected")
        if metrics.cpu_percent > 70:
            reasons.append("High CPU usage detected")
        if metrics.thread_count > 10:
            reasons.append("High thread count detected")

        return reasons

    def create_migration_script(self, old_config: Dict[str, Any]) -> List[str]:
        """Create migration script for updating old configurations"""
        migration_steps = []

        # Check for old path structures
        if "temp_dir" in old_config and old_config["temp_dir"] in ["/tmp", "/var/tmp"]:
            migration_steps.append("Update temp_dir to use tempfile.gettempdir()")

        # Check for old security settings
        if "allowed_commands" in old_config:
            migration_steps.append(
                "Migrate allowed_commands to new ALLOWED_BINARIES format"
            )

        # Check for old performance settings
        if "max_workers" in old_config:
            migration_steps.append(
                "Migrate max_workers to performance-based thread management"
            )

        return migration_steps


# Global standards manager instance
STANDARDS_MANAGER = StandardsManager()


# Convenience functions
def get_app_config(
    level: ConfigurationLevel = ConfigurationLevel.STANDARD,
) -> Dict[str, Any]:
    """Get application configuration at specified level"""
    return STANDARDS_MANAGER.get_unified_config(level)


def get_secure_path(path_type: str) -> Path:
    """Get secure application path"""
    return STANDARDS_MANAGER.app_paths.get_path(path_type)


def execute_secure_command(command: Union[str, list], timeout: int = 300):
    """Execute command with security validation"""
    return STANDARDS_MANAGER.process_manager.execute_command(
        command, ProcessConfig(timeout=timeout)
    )


def optimize_performance(file_count: int = 1000):
    """Optimize performance for scanning operation"""

    return optimize_for_scanning(file_count)


def validate_system_compatibility() -> Dict[str, Any]:
    """Validate system compatibility"""
    return STANDARDS_MANAGER.get_system_compatibility_info()


def create_default_config_file():
    """Create default configuration file"""
    default_config = STANDARDS_MANAGER.get_unified_config()
    return STANDARDS_MANAGER.save_config(default_config, "main")
