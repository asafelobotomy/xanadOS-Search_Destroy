#!/usr/bin/env python3
"""
DEPRECATED: Async Scanner Compatibility Shim

This module provides backward compatibility for the legacy async_scanner.py.
All functionality has been consolidated into unified_threading_manager.py.
"""

import warnings

warnings.warn(
    "app.core.async_scanner is deprecated. "
    "Use app.core.unified_threading_manager instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from app.core.unified_threading_manager import (
        AsyncScanner,
        AsyncScannerEngine,
        ScanProgress,
        ScanResult,
    )
except ImportError:
    from app.core.async_scanner_engine import AsyncScannerEngine, ScanProgress, ScanResult
    AsyncScanner = AsyncScannerEngine

__all__ = ['AsyncScanner', 'AsyncScannerEngine', 'ScanProgress', 'ScanResult']
