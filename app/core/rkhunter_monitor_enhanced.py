#!/usr/bin/env python3
"""Backward compatibility shim for rkhunter_monitor_enhanced.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_rkhunter_integration.py.

WARNING: This is a compatibility shim. Use unified_rkhunter_integration.py directly
for new code.
"""

import warnings

from app.core.unified_rkhunter_integration import (
    MonitoringMode,
    RKHunterStatusEnhanced,
    UnifiedRKHunterMonitor,
    get_rkhunter_integration,
    get_rkhunter_status_enhanced,
)

# Issue deprecation warning
warnings.warn(
    "rkhunter_monitor_enhanced.py is deprecated. Use unified_rkhunter_integration.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy aliases for backward compatibility
RKHunterMonitorEnhanced = UnifiedRKHunterMonitor


# Backward compatibility - provide original interface (resolves duplicate class conflict)
class RKHunterMonitorNonInvasive(UnifiedRKHunterMonitor):
    """Backward compatibility wrapper for non-invasive monitoring."""

    def __init__(self):
        super().__init__(mode=MonitoringMode.NON_INVASIVE)

    def get_status_non_invasive(self, force_refresh: bool = False):
        """Backward compatibility method."""
        return self.get_status_non_invasive(force_refresh)


__all__ = [
    "MonitoringMode",
    "RKHunterMonitorEnhanced",
    "RKHunterMonitorNonInvasive",
    "RKHunterStatusEnhanced",
    "get_rkhunter_status_enhanced",
]


# Module-level function for compatibility
def get_rkhunter_monitor_enhanced():
    """Get enhanced RKHunter monitor instance for compatibility."""
    integration = get_rkhunter_integration()
    return integration.monitor


# Default instance for compatibility
rkhunter_monitor_enhanced = get_rkhunter_monitor_enhanced()
