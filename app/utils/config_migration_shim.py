#!/usr/bin/env python3
"""
Compatibility shim for app/utils/config_migration.py

This file maintains backward compatibility for code that imports from the original
config_migration.py file. All functionality has been consolidated into
app/core/unified_configuration_manager.py.

DEPRECATION NOTICE: This compatibility shim will be removed in a future version.
Please update imports to use:
    from app.core.unified_configuration_manager import run_full_migration, etc.
"""

import warnings
from app.core.unified_configuration_manager import (
    migrate_hardcoded_database,
    migrate_environment_variables,
    run_full_migration,
    validate_migration,
)

# Issue deprecation warning
warnings.warn(
    "app.utils.config_migration is deprecated. Use app.core.unified_configuration_manager instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "migrate_hardcoded_database",
    "migrate_environment_variables",
    "run_full_migration",
    "validate_migration",
]
