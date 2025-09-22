#!/usr/bin/env python3
"""
DEPRECATED: Async File Metadata Cache Compatibility Shim

This module provides backward compatibility for the legacy async_file_metadata_cache.py.
All functionality has been consolidated into unified_threading_manager.py.
"""

import warnings

warnings.warn(
    "app.core.async_file_metadata_cache is deprecated. "
    "Use app.core.unified_threading_manager instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from app.core.unified_threading_manager import AsyncFileMetadataCache
except ImportError:
    class AsyncFileMetadataCache:
        def __init__(self):
            pass

__all__ = ['AsyncFileMetadataCache']
