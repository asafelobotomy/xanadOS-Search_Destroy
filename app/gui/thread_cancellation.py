#!/usr/bin/env python3
"""
DEPRECATED: Thread Cancellation Compatibility Shim

This module provides backward compatibility for the legacy thread_cancellation.py.
All functionality has been consolidated into unified_threading_manager.py.
"""

import warnings

warnings.warn(
    "app.gui.thread_cancellation is deprecated. "
    "Use app.core.unified_threading_manager instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from app.core.unified_threading_manager import (
        CooperativeCancellationMixin,
        ThreadState,
    )
except ImportError:
    from enum import Enum
    
    class ThreadState(Enum):
        IDLE = "idle"
        RUNNING = "running"
        CANCELLED = "cancelled"
    
    class CooperativeCancellationMixin:
        def __init__(self):
            self.state = ThreadState.IDLE

__all__ = ['CooperativeCancellationMixin', 'ThreadState']
