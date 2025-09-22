#!/usr/bin/env python3
"""Backward compatibility shim for rkhunter_optimizer.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_rkhunter_integration.py.

WARNING: This is a compatibility shim. Use unified_rkhunter_integration.py directly
for new code.
"""

import warnings

from app.core.unified_rkhunter_integration import (
    OptimizationReport,
    RKHunterConfig,
    RKHunterStatus,
    UnifiedRKHunterIntegration,
    get_rkhunter_integration,
)

# Issue deprecation warning
warnings.warn(
    "rkhunter_optimizer.py is deprecated. Use unified_rkhunter_integration.py instead.",
    DeprecationWarning,
    stacklevel=2,
)


# Legacy aliases for backward compatibility
class RKHunterOptimizer:
    """Compatibility wrapper for RKHunter optimizer functionality."""

    def __init__(self, config=None):
        self.integration = get_rkhunter_integration(config)

    def optimize_configuration(self):
        """Optimize RKHunter configuration."""
        return self.integration.optimize_configuration()


__all__ = [
    "OptimizationReport",
    "RKHunterConfig",
    "RKHunterOptimizer",
    "RKHunterStatus",
    "get_rkhunter_optimizer",
]


# Module-level function for compatibility
def get_rkhunter_optimizer(config=None):
    """Get RKHunter optimizer instance for compatibility."""
    return RKHunterOptimizer(config)


# Default instance for compatibility
rkhunter_optimizer = get_rkhunter_optimizer()
