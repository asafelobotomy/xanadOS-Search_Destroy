#!/usr/bin/env python3
"""Scan thread for running file scans without blocking the UI."""

import logging
from typing import Dict, Any, Union, List

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
        scan_path: Union[str, List[str]],
        quick_scan: bool = False,
        scan_options: Dict[str, Any] = None,
        effective_scan_type: str = None,
    ):
        super().__init__()
        self.scanner = scanner
        self.scan_path = scan_path
        self.quick_scan = quick_scan
        self.scan_options = scan_options or {}
        self.effective_scan_type = effective_scan_type  # Track actual scan type
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

            # Handle both single path and multiple paths
            if isinstance(self.scan_path, list):
                # Scan multiple directories (e.g., for quick scan)
                all_results = []
                total_paths = len(self.scan_path)

                for idx, path in enumerate(self.scan_path):
                    if self._scan_cancelled:
                        break

                    self.status_updated.emit(
                        f"Scanning {idx + 1}/{total_paths}: {path}"
                    )

                    try:
                        # Don't save individual reports - only save the combined result
                        scan_results = self.scanner.scan_directory(
                            path,
                            quick_scan=self.quick_scan,
                            effective_scan_type=self.effective_scan_type,
                            save_report=False,  # Don't save individual directory reports
                            **self.scan_options,
                        )
                        all_results.append(scan_results)
                    except Exception as e:
                        self.logger.warning(f"Error scanning {path}: {e}")
                        continue

                    # Update progress based on number of directories scanned
                    progress = int((idx + 1) / total_paths * 100)
                    self.progress_updated.emit(progress)

                # Combine results from all scans and save the combined report
                combined_results = self._combine_scan_results(all_results)

                # Save the combined report
                if combined_results and hasattr(self.scanner, "scan_report_manager"):
                    try:
                        self.scanner.scan_report_manager.save_scan_result(
                            combined_results
                        )
                        self.logger.info(
                            f"Saved combined scan report: {combined_results.scan_id}"
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to save combined report: {e}")

                scan_results = combined_results
            else:
                # Scan single directory
                scan_results = self.scanner.scan_directory(
                    self.scan_path,
                    quick_scan=self.quick_scan,
                    effective_scan_type=self.effective_scan_type,
                    **self.scan_options,
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

    def _combine_scan_results(self, results_list: List) -> Any:
        """Combine multiple scan results into a single result."""
        if not results_list:
            # Return empty dict or similar structure
            return {"scanned_files": 0, "threats_found": 0, "threats": [], "errors": []}

        if len(results_list) == 1:
            return results_list[0]

        # Import ScanResult to work with dataclass
        from app.utils.scan_reports import ScanResult, ThreatInfo
        from datetime import datetime

        # Combine results from multiple scans (all should be ScanResult dataclasses)
        first_result = results_list[0]

        # Create a combined result using the first result as template
        combined_threats = []
        combined_errors = []
        combined_paths = []
        total_scanned = 0
        total_threats = 0
        total_duration = 0.0
        total_files = 0

        for result in results_list:
            # Handle both ScanResult dataclass and dict formats
            if hasattr(result, "scanned_files"):
                # It's a ScanResult dataclass
                total_scanned += result.scanned_files
                total_threats += result.threats_found
                total_duration += result.duration
                total_files += result.total_files
                combined_threats.extend(result.threats)
                combined_errors.extend(result.errors)
                combined_paths.extend(result.scanned_paths)
            elif isinstance(result, dict):
                # It's a dictionary (fallback)
                total_scanned += result.get("scanned_files", 0)
                total_threats += result.get("threats_found", 0)
                total_duration += result.get("duration", 0.0)
                total_files += result.get("total_files", 0)

        # Create a new combined ScanResult
        combined_result = ScanResult(
            scan_id=(
                first_result.scan_id if hasattr(first_result, "scan_id") else "combined"
            ),
            scan_type=(
                first_result.scan_type if hasattr(first_result, "scan_type") else None
            ),
            start_time=(
                first_result.start_time
                if hasattr(first_result, "start_time")
                else datetime.now().isoformat()
            ),
            end_time=datetime.now().isoformat(),
            duration=total_duration,
            scanned_paths=combined_paths,
            total_files=total_files,
            scanned_files=total_scanned,
            threats_found=total_threats,
            threats=combined_threats,
            errors=combined_errors,
            scan_settings=(
                first_result.scan_settings
                if hasattr(first_result, "scan_settings")
                else {}
            ),
            engine_version=(
                first_result.engine_version
                if hasattr(first_result, "engine_version")
                else ""
            ),
            signature_version=(
                first_result.signature_version
                if hasattr(first_result, "signature_version")
                else ""
            ),
            success=total_threats == 0 and len(combined_errors) == 0,
        )

        return combined_result
