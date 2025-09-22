#!/usr/bin/env python3
"""
Compatibility shim for app/core/component_manager.py

This file maintains backward compatibility for code that imports from the original
component_manager.py file. Component management functionality has been consolidated into
app/core/unified_configuration_manager.py.

DEPRECATION NOTICE: This compatibility shim will be removed in a future version.
Please update imports to use:
    from app.core.unified_configuration_manager import ComponentState, etc.
"""

import warnings
from app.core.unified_configuration_manager import (
    ComponentInfo,
    ComponentState,
    get_unified_config_manager,
)

# Issue deprecation warning
warnings.warn(
    "app.core.component_manager is deprecated. Use app.core.unified_configuration_manager instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


class ComponentManager:
    """Deprecated - use UnifiedConfigurationManager instead"""

    def __init__(self):
        warnings.warn(
            "ComponentManager is deprecated. Use UnifiedConfigurationManager instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # This will be handled by the unified config manager

    def register_component(self, name: str, dependencies: list[str] = None):
        """Deprecated - handled by unified configuration manager"""
        pass

    def get_component(self, name: str):
        """Deprecated - handled by unified configuration manager"""
        return None


# Global instance
_component_manager = None


def get_component_manager():
    """Deprecated - use get_unified_config_manager() instead"""
    warnings.warn(
        "get_component_manager() is deprecated. Use get_unified_config_manager() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _component_manager
    if _component_manager is None:
        _component_manager = ComponentManager()
    return _component_manager


def get_component(name: str):
    """Deprecated - handled by unified configuration manager"""
    warnings.warn(
        "get_component() is deprecated. Component management is handled by unified configuration manager.",
        DeprecationWarning,
        stacklevel=2,
    )
    return None


__all__ = [
    "ComponentInfo",
    "ComponentManager",
    "ComponentState",
    "get_component",
    "get_component_manager",
]
