#!/usr/bin/env python3
"""
DEPRECATED: Async File Watcher Compatibility Shim

This module provides backward compatibility for the legacy async_file_watcher.py.
All functionality has been consolidated into unified_threading_manager.py.
"""

import warnings

warnings.warn(
    "app.core.async_file_watcher is deprecated. "
    "Use app.core.unified_threading_manager instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from app.core.unified_threading_manager import AsyncFileWatcher
except ImportError:
    import asyncio
    from pathlib import Path
    
    class AsyncFileWatcher:
        def __init__(self):
            pass
            
        async def watch_directory(self, path: Path):
            await asyncio.sleep(0.1)

__all__ = ['AsyncFileWatcher']
