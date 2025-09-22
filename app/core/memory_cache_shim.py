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

__all__ = [
    "CacheManager",
    "MemoryCache",
    "get_cache_manager",
    "memory_cache",
]


# Module-level function for compatibility
def get_cache_manager():
    """Get cache manager instance for compatibility."""
    return get_memory_manager()


# Default instance for compatibility
memory_cache = get_memory_manager()
