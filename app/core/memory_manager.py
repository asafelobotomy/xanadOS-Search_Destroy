#!/usr/bin/env python3
"""Backward compatibility shim for memory_manager.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_memory_management.py.

WARNING: This is a compatibility shim. Use unified_memory_management.py directly
for new code.
"""

import warnings

from app.core.unified_memory_management import (
    MemoryMetrics,
    MemoryPressureLevel,
    UnifiedMemoryManager,
    UnifiedMemoryPool,
    get_memory_manager,
)

# Issue deprecation warning
warnings.warn(
    "memory_manager.py is deprecated. Use unified_memory_management.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy aliases for backward compatibility
AdvancedMemoryManager = UnifiedMemoryManager
MemoryPool = UnifiedMemoryPool
MemoryStats = MemoryMetrics

# Expose pressure level enum for compatibility
__all__ = [
    "AdvancedMemoryManager",
    "MemoryPool",
    "MemoryPressureLevel",
    "MemoryStats",
    "PoolStats",
    "get_memory_manager",
    "get_memory_manager_instance",
    "memory_manager",
]


# For any existing imports that expect specific classes
class PoolStats:
    """Compatibility class for pool statistics."""

    pass


# Module-level function for compatibility
def get_memory_manager_instance():
    """Get memory manager instance for compatibility."""
    return get_memory_manager()


# Default instance for compatibility
memory_manager = get_memory_manager()
