#!/usr/bin/env python3
"""Backward compatibility shim for memory_optimizer.py

This file maintains backward compatibility during the consolidation process.
All functionality has been moved to unified_memory_management.py.

WARNING: This is a compatibility shim. Use unified_memory_management.py directly
for new code.
"""

import warnings

from app.core.unified_memory_management import (
    UnifiedMemoryManager,
    get_memory_manager,
)

# Issue deprecation warning
warnings.warn(
    "memory_optimizer.py is deprecated. Use unified_memory_management.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy aliases for backward compatibility
MemoryOptimizer = UnifiedMemoryManager

__all__ = [
    "MemoryOptimizer",
    "get_memory_optimizer",
]


# Module-level function for compatibility
def get_memory_optimizer():
    """Get memory optimizer instance for compatibility."""
    return get_memory_manager()


# Default instance for compatibility
memory_optimizer = get_memory_manager()
