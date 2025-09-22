#!/usr/bin/env python3
"""Backward compatibility shim for rkhunter_analyzer.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_rkhunter_integration.py.

WARNING: This is a compatibility shim. Use unified_rkhunter_integration.py directly
for new code.
"""

import warnings

from app.core.unified_rkhunter_integration import (
    RKHunterWarningAnalyzer,
    SeverityLevel,
    WarningCategory,
    WarningExplanation,
)

# Issue deprecation warning
warnings.warn(
    "rkhunter_analyzer.py is deprecated. Use unified_rkhunter_integration.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy aliases are already properly named in the unified module
__all__ = [
    "RKHunterWarningAnalyzer",
    "SeverityLevel",
    "WarningCategory",
    "WarningExplanation",
    "get_rkhunter_analyzer",
]


# Module-level function for compatibility
def get_rkhunter_analyzer():
    """Get RKHunter analyzer instance for compatibility."""
    return RKHunterWarningAnalyzer()


# Default instance for compatibility
rkhunter_analyzer = get_rkhunter_analyzer()
