#!/usr/bin/env python3
"""
Compatibility shim for app/gui/settings_pages.py configuration functions

This file maintains backward compatibility for configuration-related functions from
the original settings_pages.py file. Configuration functionality has been consolidated into
app/core/unified_configuration_manager.py.

DEPRECATION NOTICE: This compatibility shim will be removed in a future version.
Please update imports to use:
    from app.core.unified_configuration_manager import create_*_config functions
"""

import warnings
from app.core.unified_configuration_manager import (
    RKHunterConfiguration,
    create_performance_config,
    get_config,
)

# Issue deprecation warning
warnings.warn(
    "Configuration functions from app.gui.settings_pages are deprecated. "
    "Use app.core.unified_configuration_manager instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


class RKHunterOptimizationWorker:
    """Deprecated - RKHunter optimization handled by unified configuration manager"""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "RKHunterOptimizationWorker is deprecated. RKHunter optimization is handled by unified configuration manager.",
            DeprecationWarning,
            stacklevel=2,
        )


class RKHunterStatusWidget:
    """Deprecated - RKHunter status handled by unified configuration manager"""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "RKHunterStatusWidget is deprecated. RKHunter status is handled by unified configuration manager.",
            DeprecationWarning,
            stacklevel=2,
        )


def build_scan_page(*args, **kwargs):
    """Deprecated - scan configuration handled by unified configuration manager"""
    warnings.warn(
        "build_scan_page() is deprecated. Scan configuration is handled by unified configuration manager.",
        DeprecationWarning,
        stacklevel=2,
    )


def build_ui_page(*args, **kwargs):
    """Deprecated - UI configuration handled by unified configuration manager"""
    warnings.warn(
        "build_ui_page() is deprecated. UI configuration is handled by unified configuration manager.",
        DeprecationWarning,
        stacklevel=2,
    )


def build_security_page(*args, **kwargs):
    """Deprecated - security configuration handled by unified configuration manager"""
    warnings.warn(
        "build_security_page() is deprecated. Security configuration is handled by unified configuration manager.",
        DeprecationWarning,
        stacklevel=2,
    )


def build_performance_page(*args, **kwargs):
    """Deprecated - performance configuration handled by unified configuration manager"""
    warnings.warn(
        "build_performance_page() is deprecated. Performance configuration is handled by unified configuration manager.",
        DeprecationWarning,
        stacklevel=2,
    )


__all__ = [
    "RKHunterOptimizationWorker",
    "RKHunterStatusWidget",
    "build_performance_page",
    "build_scan_page",
    "build_security_page",
    "build_ui_page",
]
