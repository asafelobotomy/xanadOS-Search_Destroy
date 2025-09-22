#!/usr/bin/env python3
"""
Compatibility shim for app/utils/standards_integration.py

This file maintains backward compatibility for code that imports from the original
standards_integration.py file. Configuration functionality has been consolidated into
app/core/unified_configuration_manager.py.

DEPRECATION NOTICE: This compatibility shim will be removed in a future version.
Please update imports to use:
    from app.core.unified_configuration_manager import ConfigurationLevel, etc.
"""

import warnings
from typing import Any

from app.core.unified_configuration_manager import (
    ConfigurationLevel,
    get_config,
    save_config,
)
from app.utils.performance_standards import PERFORMANCE_OPTIMIZER
from app.utils.process_management import PROCESS_MANAGER
from app.utils.security_standards import SecurityStandards
from app.utils.system_paths import ApplicationPaths

# Issue deprecation warning
warnings.warn(
    "Configuration functions from app.utils.standards_integration are deprecated. "
    "Use app.core.unified_configuration_manager instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


class StandardsManager:
    """Deprecated - use UnifiedConfigurationManager instead"""

    def __init__(self, app_name: str = "xanados-search-destroy"):
        warnings.warn(
            "StandardsManager is deprecated. Use UnifiedConfigurationManager instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.app_name = app_name
        self.app_paths = ApplicationPaths(app_name)
        self.security_standards = SecurityStandards()
        self.process_manager = PROCESS_MANAGER
        self.performance_optimizer = PERFORMANCE_OPTIMIZER

        # Current configuration
        self._config_cache = {}
        self._config_dirty = False


# Global standards manager instance (deprecated)
STANDARDS_MANAGER = StandardsManager()


def get_app_config(
    level: ConfigurationLevel = ConfigurationLevel.STANDARD,
) -> dict[str, Any]:
    """Deprecated - use get_config() from unified_configuration_manager instead"""
    warnings.warn(
        "get_app_config() is deprecated. Use get_config() from unified_configuration_manager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_config()


def create_default_config_file() -> bool:
    """Deprecated - handled automatically by unified configuration manager"""
    warnings.warn(
        "create_default_config_file() is deprecated. Default config creation is handled automatically.",
        DeprecationWarning,
        stacklevel=2,
    )
    return True


def get_unified_config() -> dict[str, Any]:
    """Deprecated - use get_config() from unified_configuration_manager instead"""
    warnings.warn(
        "get_unified_config() is deprecated. Use get_config() from unified_configuration_manager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_config()


def load_config() -> dict[str, Any]:
    """Deprecated - use load_config() from unified_configuration_manager instead"""
    warnings.warn(
        "load_config() from standards_integration is deprecated. "
        "Use load_config() from unified_configuration_manager instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_config()


__all__ = [
    "ConfigurationLevel",
    "PERFORMANCE_OPTIMIZER",
    "PROCESS_MANAGER",
    "STANDARDS_MANAGER",
    "StandardsManager",
    "create_default_config_file",
    "get_app_config",
    "get_unified_config",
    "load_config",
    "save_config",
]
