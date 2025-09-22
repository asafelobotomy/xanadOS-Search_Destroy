#!/usr/bin/env python3
"""Backward compatibility shim for rkhunter_monitor_non_invasive.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_rkhunter_integration.py.

WARNING: This is a compatibility shim. Use unified_rkhunter_integration.py directly
for new code.
"""

import warnings

from app.core.unified_rkhunter_integration import (
    MonitoringMode,
    RKHunterStatusNonInvasive,
    UnifiedRKHunterMonitor,
    get_rkhunter_integration,
    get_rkhunter_status_non_invasive,
    record_rkhunter_activity,
)

# Issue deprecation warning
warnings.warn(
    "rkhunter_monitor_non_invasive.py is deprecated. Use unified_rkhunter_integration.py instead.",
    DeprecationWarning,
    stacklevel=2,
)


# Legacy aliases for backward compatibility (original implementation)
class RKHunterMonitorNonInvasive(UnifiedRKHunterMonitor):
    """Original non-invasive monitoring implementation for compatibility."""

    def __init__(self, cache_duration: int = 300):
        super().__init__(
            mode=MonitoringMode.NON_INVASIVE, cache_duration=cache_duration
        )

    def get_status_non_invasive(self, force_refresh: bool = False):
        """Original method name for compatibility."""
        return self.get_status_non_invasive(force_refresh)


__all__ = [
    "MonitoringMode",
    "RKHunterMonitorNonInvasive",
    "RKHunterStatusNonInvasive",
    "get_rkhunter_status_non_invasive",
    "record_rkhunter_activity",
    "rkhunter_monitor",
]


# Global instance for compatibility
rkhunter_monitor = RKHunterMonitorNonInvasive()


# Module-level function for compatibility
def get_rkhunter_monitor_non_invasive(cache_duration: int = 300):
    """Get non-invasive RKHunter monitor instance for compatibility."""
    return RKHunterMonitorNonInvasive(cache_duration)


# Default instance for compatibility
rkhunter_monitor_non_invasive = get_rkhunter_monitor_non_invasive()
