#!/usr/bin/env python3
"""Backward compatibility shim for memory_cache.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_memory_management.py.

WARNING: This is a compatibility shim. Use unified_memory_management.py directly
for new code.
"""

import warnings

from app.core.unified_memory_management import (
    IntelligentCache,
    UnifiedMemoryManager,
    get_memory_manager,
    get_system_cache as get_unified_system_cache,
)

# Issue deprecation warning
warnings.warn(
    "memory_cache.py is deprecated. Use unified_memory_management.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy aliases for backward compatibility
MemoryCache = IntelligentCache
CacheManager = UnifiedMemoryManager


class SystemStatusCache:
    """Compatibility wrapper for SystemStatusCache interface."""

    def __init__(self):
        self._cache = get_unified_system_cache()
        self.refresh_callbacks = {}
        self._background_refresh_active = set()

    def register_refresh_callback(self, key: str, callback):
        """Register a callback to refresh stale data."""
        self.refresh_callbacks[key] = callback

    def get_system_status(self, component: str, factory=None):
        """Get system status with compatibility interface."""
        cache_key = f"status_{component}"

        # Try to get from cache
        cached_value = self._cache.get(cache_key)

        # If no cached value and we have a factory, get fresh data
        if cached_value is None and factory:
            try:
                cached_value = factory()
                self._cache.set(cache_key, cached_value, ttl=30)
            except Exception as e:
                print(f"Failed to refresh {component} status: {e}")
                return None

        return cached_value

    def set_system_status(self, component: str, status, ttl: float = 30):
        """Set system status in cache."""
        self._cache.set(f"status_{component}", status, ttl=ttl)

    def _trigger_background_refresh(self, component: str):
        """Trigger background refresh for compatibility."""
        if component in self.refresh_callbacks:
            try:
                self.refresh_callbacks[component]()
            except Exception as e:
                print(f"Background refresh failed for {component}: {e}")


__all__ = [
    "CacheManager",
    "MemoryCache",
    "SystemStatusCache",
    "get_cache_manager",
    "get_system_cache",
    "memory_cache",
]


# Module-level function for compatibility
def get_cache_manager():
    """Get cache manager instance for compatibility."""
    return get_memory_manager()


# Override get_system_cache to return compatibility wrapper
def get_system_cache():
    """Get system status cache instance with compatibility interface."""
    return SystemStatusCache()


# Default instance for compatibility
memory_cache = get_memory_manager()
