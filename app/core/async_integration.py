#!/usr/bin/env python3
"""
DEPRECATED: Async Integration Compatibility Shim

This module provides backward compatibility for the legacy async_integration.py.
All functionality has been consolidated into unified_threading_manager.py.
"""

import warnings

warnings.warn(
    "app.core.async_integration is deprecated. "
    "Use app.core.unified_threading_manager instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from app.core.unified_threading_manager import AsyncIntegrationManager
except ImportError:
    class AsyncIntegrationManager:
        def __init__(self):
            pass

__all__ = ['AsyncIntegrationManager']
