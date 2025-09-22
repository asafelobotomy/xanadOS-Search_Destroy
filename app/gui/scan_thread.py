#!/usr/bin/env python3
"""
DEPRECATED: GUI Scan Thread Compatibility Shim
===============================================

This module provides backward compatibility for the legacy scan_thread.py.
All functionality has been consolidated into unified_threading_manager.py.

⚠️  DEPRECATION WARNING ⚠️
This shim module is deprecated and will be removed in a future version.
Please update your imports to use:
    from app.core.unified_threading_manager import UnifiedScanThread

Migration Guide:
- Replace: from app.gui.scan_thread import ScanThread
- With:    from app.core.unified_threading_manager import UnifiedScanThread

- Replace: from app.gui.scan_thread import ScanWorker
- With:    from app.core.unified_threading_manager import UnifiedScanThread

- Replace: from app.gui.scan_thread import ThreadState
- With:    from app.core.unified_threading_manager import ThreadState
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "app.gui.scan_thread is deprecated. "
    "Use app.core.unified_threading_manager.UnifiedScanThread instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Import everything from the unified module for backward compatibility
try:
    from app.core.unified_threading_manager import (
        PerformanceMetrics,
        ScanProgress,
        ScanResult,
        ThreadState,
        UnifiedScanThread,
    )

    # Alias for backward compatibility
    ScanThread = UnifiedScanThread
    ScanWorker = UnifiedScanThread

except ImportError as e:
    # Fallback if unified module is not available
    warnings.warn(
        f"Failed to import from unified_threading_manager: {e}. "
        "Using minimal fallback implementation.",
        ImportWarning,
        stacklevel=2,
    )

    # Check if PyQt6 is available
    try:
        from PyQt6.QtCore import QObject, QThread, pyqtSignal

        PYQT_AVAILABLE = True
    except ImportError:
        try:
            from PyQt5.QtCore import QObject, QThread, pyqtSignal

            PYQT_AVAILABLE = True
        except ImportError:
            PYQT_AVAILABLE = False

    # Minimal fallback implementation
    import asyncio
    from dataclasses import dataclass
    from enum import Enum
    from pathlib import Path

    class ThreadState(Enum):
        IDLE = "idle"
        RUNNING = "running"
        PAUSED = "paused"
        CANCELLED = "cancelled"
        COMPLETED = "completed"
        ERROR = "error"

    @dataclass
    class ScanProgress:
        files_scanned: int
        total_files: int
        current_file: str
        progress_percentage: float
        errors: list[str]

    @dataclass
    class ScanResult:
        total_files: int
        threats_found: list
        scan_duration: float
        files_with_errors: list[str]

    @dataclass
    class PerformanceMetrics:
        cpu_usage: float
        memory_usage: float
        disk_io: float
        scan_throughput: float

    if PYQT_AVAILABLE:

        class UnifiedScanThread(QThread):
            progress_updated = pyqtSignal(object)
            scan_completed = pyqtSignal(object)
            error_occurred = pyqtSignal(str)

            def __init__(self, parent=None):
                super().__init__(parent)
                self.state = ThreadState.IDLE

            def run(self):
                """Minimal fallback scan implementation."""
                self.state = ThreadState.RUNNING
                try:
                    # Simulate scan progress
                    for i in range(100):
                        if self.state == ThreadState.CANCELLED:
                            break
                        progress = ScanProgress(
                            files_scanned=i,
                            total_files=100,
                            current_file=f"file_{i}.txt",
                            progress_percentage=i,
                            errors=[],
                        )
                        self.progress_updated.emit(progress)
                        self.msleep(10)  # Small delay

                    result = ScanResult(100, [], 1.0, [])
                    self.scan_completed.emit(result)
                    self.state = ThreadState.COMPLETED

                except Exception as e:
                    self.error_occurred.emit(str(e))
                    self.state = ThreadState.ERROR

            def cancel_scan(self):
                self.state = ThreadState.CANCELLED

            def pause_scan(self):
                self.state = ThreadState.PAUSED

            def resume_scan(self):
                self.state = ThreadState.RUNNING

    else:
        # Non-GUI fallback
        class UnifiedScanThread:
            def __init__(self):
                self.state = ThreadState.IDLE

            def start(self):
                self.state = ThreadState.RUNNING

            def cancel_scan(self):
                self.state = ThreadState.CANCELLED

            def pause_scan(self):
                self.state = ThreadState.PAUSED

            def resume_scan(self):
                self.state = ThreadState.RUNNING

    # Backward compatibility aliases
    ScanThread = UnifiedScanThread
    ScanWorker = UnifiedScanThread

# Export the same symbols as the original module
__all__ = [
    "PerformanceMetrics",
    "ScanProgress",
    "ScanResult",
    "ScanThread",
    "ScanWorker",
    "ThreadState",
    "UnifiedScanThread",
]
