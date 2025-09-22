#!/usr/bin/env python3
"""Backward compatibility shim for rkhunter_wrapper.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_rkhunter_integration.py.

WARNING: This is a compatibility shim. Use unified_rkhunter_integration.py directly
for new code.
"""

import warnings

from app.core.unified_rkhunter_integration import (
    RKHunterFinding,
    RKHunterResult,
    RKHunterScanResult,
    RKHunterSeverity,
    UnifiedRKHunterIntegration,
    get_rkhunter_integration,
)

# Issue deprecation warning
warnings.warn(
    "rkhunter_wrapper.py is deprecated. Use unified_rkhunter_integration.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy aliases for backward compatibility
RKHunterWrapper = UnifiedRKHunterIntegration

__all__ = [
    "RKHunterFinding",
    "RKHunterResult",
    "RKHunterScanResult",
    "RKHunterSeverity",
    "RKHunterWrapper",
    "get_rkhunter_wrapper",
]


# Module-level function for compatibility
def get_rkhunter_wrapper():
    """Get RKHunter wrapper instance for compatibility."""
    return get_rkhunter_integration()


# Default instance for compatibility
rkhunter_wrapper = get_rkhunter_integration()
