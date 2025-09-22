#!/usr/bin/env python3
"""
DEPRECATED: Advanced Async Scanner Compatibility Shim

This module provides backward compatibility for the legacy advanced_async_scanner.py.
All functionality has been consolidated into unified_threading_manager.py.
"""

import warnings

warnings.warn(
    "app.core.advanced_async_scanner is deprecated. "
    "Use app.core.unified_threading_manager instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from app.core.unified_threading_manager import (
        AdvancedAsyncScanner,
        AsyncScannerEngine,
        ScanProgress,
        ScanResult,
    )
except ImportError:
    from app.core.async_scanner_engine import AsyncScannerEngine, ScanProgress, ScanResult
    AdvancedAsyncScanner = AsyncScannerEngine

__all__ = ['AdvancedAsyncScanner', 'AsyncScannerEngine', 'ScanProgress', 'ScanResult']
