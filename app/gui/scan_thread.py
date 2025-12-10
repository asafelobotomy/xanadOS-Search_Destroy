#!/usr/bin/env python3
"""Scan thread for running file scans without blocking the UI."""

import logging
from typing import Dict, Any

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.file_scanner import FileScanner
from app.core.unified_threading_manager import CooperativeCancellationMixin


class ScanThread(QThread, CooperativeCancellationMixin):
    """Thread for running file scans without blocking the UI."""

    progress_updated = pyqtSignal(int)  # Progress percentage
    status_updated = pyqtSignal(str)  # Status message
    scan_detail_updated = pyqtSignal(str, str)  # file_path, status
    scan_completed = pyqtSignal(object)  # Scan results
    error_occurred = pyqtSignal(str)  # Error message

    def __init__(
        self,
        scanner: FileScanner,
        scan_path: str,
        quick_scan: bool = False,
        scan_options: Dict[str, Any] = None,
    ):
        super().__init__()
        self.scanner = scanner
        self.scan_path = scan_path
        self.quick_scan = quick_scan
        self.scan_options = scan_options or {}
        self.logger = logging.getLogger(__name__)
        self._scan_cancelled = False

    def stop_scan(self):
        """Request to stop the current scan safely."""
        self.cooperative_cancel()
        self._scan_cancelled = True
        self.logger.info("Scan cancellation requested")

    def run(self):
        """Execute the scan in the thread."""
        try:
            self.status_updated.emit("Starting scan...")
            self.progress_updated.emit(0)

            # Perform the scan
            scan_results = self.scanner.scan_directory(
                self.scan_path,
                quick_scan=self.quick_scan,
                **self.scan_options
            )

            if not self._scan_cancelled:
                self.progress_updated.emit(100)
                self.status_updated.emit("Scan completed")
                self.scan_completed.emit(scan_results)
            else:
                self.status_updated.emit("Scan cancelled")

        except Exception as e:
            self.logger.error(f"Error in scan thread: {e}")
            self.error_occurred.emit(str(e))
            self.status_updated.emit(f"Scan error: {e}")
