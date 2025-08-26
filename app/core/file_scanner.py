#!/usr/bin/env python3
"""
Enhanced file scanner with quarantine management and scheduling for S&D - Search & Destroy
"""

import gc
import hashlib
import os
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional
import json
import fnmatch
from app.utils.config import load_config, setup_logging
from app.utils.scan_reports import (
    ScanReportManager,
    ScanResult as ReportScanResult,
    ThreatInfo,
    ThreatLevel,
    ScanType,
)
from .input_validation import (
    FileSizeMonitor,
    PathValidator,
    SecurityValidationError,
    validate_scan_request,
)
from .rate_limiting import configure_rate_limits, rate_limit_manager

import psutil

from .clamav_wrapper import ClamAVWrapper, ScanFileResult, ScanResult


# Optional scheduler dependency
try:
    import schedule  # type: ignore

    _SCHED_AVAILABLE = True
except Exception:
    schedule = None  # type: ignore
    _SCHED_AVAILABLE = False


class MemoryMonitor:
    """Monitor and optimize memory usage during scanning operations."""

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = self.get_memory_usage()
        self.peak_memory = self.start_memory

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def check_memory_pressure(self, max_memory_mb: float = 256) -> bool:
        """Check if memory usage is approaching limits."""
        current_memory = self.get_memory_usage()
        self.peak_memory = max(self.peak_memory, current_memory)
        return current_memory > max_memory_mb

    def force_garbage_collection(self):
        """Force garbage collection to free memory."""
        gc.collect()

    def get_stats(self) -> dict:
        """Get memory usage statistics."""
        current = self.get_memory_usage()
        return {
            "current_mb": current,
            "peak_mb": self.peak_memory,
            "start_mb": self.start_memory,
            "increase_mb": current - self.start_memory,
        }


class QuarantineAction(Enum):
    """Actions that can be taken on quarantined files."""

    RESTORE = "restore"
    DELETE = "delete"
    SUBMIT_SAMPLE = "submit_sample"


@dataclass
class QuarantinedFile:
    """Information about a quarantined file."""

    original_path: str
    quarantine_path: str
    threat_name: str
    threat_type: str
    quarantine_date: datetime
    file_hash: str
    file_size: int
    scan_id: str


class QuarantineManager:
    """Manages quarantined files and actions."""

    def __init__(self):
        self.logger = setup_logging()
        self.config = load_config()
        self.quarantine_dir = Path(self.config["paths"]["quarantine_dir"])
        self.quarantine_dir.mkdir(exist_ok=True)

        # Create subdirectories
        self.quarantine_files_dir = self.quarantine_dir / "files"
        self.quarantine_metadata_dir = self.quarantine_dir / "metadata"

        for directory in [self.quarantine_files_dir, self.quarantine_metadata_dir]:
            directory.mkdir(exist_ok=True)

    def quarantine_file(
        self, file_path: str, threat_name: str, threat_type: str, scan_id: str
    ) -> bool:
        """Move a file to quarantine."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.error("File to quarantine not found: %s", file_path)
                return False

            # Generate unique quarantine filename
            file_hash = self._calculate_file_hash(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_filename = f"{timestamp}_{file_hash}_{source_path.name}"
            quarantine_path = self.quarantine_files_dir / quarantine_filename

            # Move file to quarantine
            shutil.move(str(source_path), str(quarantine_path))

            # Create metadata
            metadata = QuarantinedFile(
                original_path=str(source_path),
                quarantine_path=str(quarantine_path),
                threat_name=threat_name,
                threat_type=threat_type,
                quarantine_date=datetime.now(),
                file_hash=file_hash,
                file_size=quarantine_path.stat().st_size,
                scan_id=scan_id,
            )

            # Save metadata
            metadata_file = self.quarantine_metadata_dir / f"{quarantine_filename}.json"
            import json

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(asdict(metadata), f, indent=2, default=str)

            self.logger.info("File quarantined: %s -> %s", file_path, str(quarantine_path))
            return True

        except (OSError, IOError, shutil.Error) as e:
            self.logger.error("Failed to quarantine file %s: %s", file_path, e)
            return False

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (OSError, IOError):
            return "unknown"

    def list_quarantined_files(self) -> List[QuarantinedFile]:
        """List all quarantined files."""
        quarantined_files = []

        for metadata_file in self.quarantine_metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Convert datetime string back to datetime object
                data["quarantine_date"] = datetime.fromisoformat(data["quarantine_date"])
                quarantined_files.append(QuarantinedFile(**data))

            except (json.JSONDecodeError, IOError, TypeError, ValueError) as e:
                self.logger.warning("Failed to load quarantine metadata %s: %s", metadata_file, e)
                continue

        return sorted(quarantined_files, key=lambda x: x.quarantine_date, reverse=True)

    def restore_file(self, quarantine_path: str, original_path: Optional[str] = None) -> bool:
        """Restore a file from quarantine."""
        try:
            quarantine_file = Path(quarantine_path)
            if not quarantine_file.exists():
                self.logger.error("Quarantined file not found: %s", quarantine_path)
                return False

            # Find metadata
            metadata_file = self.quarantine_metadata_dir / f"{quarantine_file.name}.json"
            if not metadata_file.exists():
                self.logger.error("Quarantine metadata not found: %s", metadata_file)
                return False

            # Load metadata

            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Determine restore path
            restore_path = Path(original_path) if original_path else Path(metadata["original_path"])

            # Ensure destination directory exists
            restore_path.parent.mkdir(parents=True, exist_ok=True)

            # Restore file
            shutil.move(str(quarantine_file), str(restore_path))

            # Remove metadata
            metadata_file.unlink()

            self.logger.info("File restored: %s -> %s", quarantine_path, str(restore_path))
            return True

        except (OSError, IOError, shutil.Error, json.JSONDecodeError) as e:
            self.logger.error("Failed to restore file %s: %s", quarantine_path, e)
            return False

    def delete_quarantined_file(self, quarantine_path: str) -> bool:
        """Permanently delete a quarantined file."""
        try:
            quarantine_file = Path(quarantine_path)
            if quarantine_file.exists():
                quarantine_file.unlink()

            # Remove metadata
            metadata_file = self.quarantine_metadata_dir / f"{quarantine_file.name}.json"
            if metadata_file.exists():
                metadata_file.unlink()

            self.logger.info("Quarantined file deleted: %s", quarantine_path)
            return True

        except (OSError, IOError) as e:
            self.logger.error("Failed to delete quarantined file %s: %s", quarantine_path, e)
            return False

    def cleanup_old_quarantine(self, days_to_keep: int = 30) -> None:
        """Clean up old quarantined files."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0

        for quarantined_file in self.list_quarantined_files():
            if quarantined_file.quarantine_date < cutoff_date:
                if self.delete_quarantined_file(quarantined_file.quarantine_path):
                    deleted_count += 1

        if deleted_count > 0:
            self.logger.info("Cleaned up %d old quarantined files", deleted_count)


class FileScanner:
    """Enhanced file scanner with quarantine management and scheduling."""

    def __init__(self, clamav_wrapper: Optional[ClamAVWrapper] = None):
        self.logger = setup_logging()
        self.config = load_config()
        self.clamav_wrapper = clamav_wrapper or ClamAVWrapper()
        self.quarantine_manager = QuarantineManager()
        self.scan_report_manager = ScanReportManager()

        # Security components
        self.path_validator = PathValidator()
        self.size_monitor = FileSizeMonitor()

        # Rate limiting
        self.rate_limiter = rate_limit_manager
        configure_rate_limits(self.config)

        # Memory optimization: Add file batching and monitoring
        self.memory_monitor = MemoryMonitor()
        self.batch_size = self.config.get("performance", {}).get("scan_batch_size", 50)
        self.max_memory_usage = self.config.get("performance", {}).get("max_memory_mb", 256)

        # Threading and progress tracking
        self._scan_progress = 0.0
        self._scan_running = False
        self._scan_cancelled = False
        self._current_scan_id = None
        self._total_files_to_scan = 0
        self._files_completed = 0
        self._current_thread = None  # Reference to QThread for interruption checks

        # Callbacks
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.detailed_progress_callback: Optional[Callable[[dict], None]] = (
            None  # New detailed callback
        )
        self.result_callback: Optional[Callable[[ScanFileResult], None]] = None

        # Scheduled scanning
        self._scheduler_thread = None
        self._scheduler_running = False
        self._scheduler_stop_event = threading.Event()

        # Initialize scheduled scans if enabled
        if self.config.get("security_settings", {}).get("scheduled_scanning", False):
            self.start_scheduler()

    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """Set callback for scan progress updates."""
        self.progress_callback = callback

    def set_detailed_progress_callback(self, callback: Callable[[dict], None]) -> None:
        """Set callback for detailed scan progress updates."""
        self.detailed_progress_callback = callback

    def set_result_callback(self, callback: Callable[[ScanFileResult], None]) -> None:
        """Set callback for individual scan results."""
        self.result_callback = callback

    def update_virus_definitions(self) -> bool:
        """Update virus definitions using the ClamAV wrapper.

        Returns:
            bool: True if update was successful, False otherwise
        """
        self.logger.info("Updating virus definitions...")

        # Call the update method in the ClamAV wrapper
        return self.clamav_wrapper.update_virus_definitions()

    def scan_file(self, file_path: str, scan_id: Optional[str] = None, **kwargs) -> ScanFileResult:
        """Scan a single file with security validation and rate limiting."""

        # Apply rate limiting for file scans
        if not self.rate_limiter.acquire("file_scan"):
            wait_time = self.rate_limiter.wait_time("file_scan")
            self.logger.warning(
                "Rate limit exceeded for file scan. Wait time: %.2f seconds", wait_time
            )
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message=f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.",
            )

        if not scan_id:
            scan_id = self.scan_report_manager.generate_scan_id()

        self.logger.info("Scanning file: %s", file_path)

        # Security validation before scanning
        try:
            is_valid, error_msg = self.path_validator.validate_file_for_scan(file_path)
            if not is_valid:
                self.logger.warning(
                    "Security validation failed for %s: %s", file_path, error_msg
                )
                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.ERROR,
                    error_message=f"Security validation failed: {error_msg}",
                )

            # Check file size limits
            if not self.size_monitor.check_can_process_file(file_path):
                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.ERROR,
                    error_message="File size exceeds limits or scan quota reached",
                )

        except SecurityValidationError as e:
            self.logger.error(
                "Security validation error for %s: %s", file_path, str(e)
            )
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message=f"Security validation error: {e}",
            )

        # Only report file-level progress if this is a single file scan
        # For multi-file scans, progress is reported by scan_files method
        if hasattr(self, "_total_files_to_scan") and self._total_files_to_scan > 1:
            # Multi-file scan - don't report individual file progress
            pass
        else:
            # Single file scan - report individual progress
            if self.progress_callback:
                self.progress_callback(0.0, f"Scanning {Path(file_path).name}")

        # Performance optimization: Check if file should be scanned
        scan_type = kwargs.get("scan_type", "full")
        quick_scan = scan_type.lower() in ["quick", "fast", "basic"]

        if not self.clamav_wrapper.should_scan_file(file_path, quick_scan=quick_scan):
            # Return clean result for skipped files
            result = ScanFileResult(
                file_path=file_path,
                result=ScanResult.CLEAN,
                file_size=(Path(file_path).stat().st_size if Path(file_path).exists() else 0),
                scan_time=0.001,  # Minimal time for skipped file
            )
            if self.result_callback:
                self.result_callback(result)
            return result

        # Perform scan with optimization flags
        kwargs["quick_scan"] = quick_scan
        result = self.clamav_wrapper.scan_file(file_path, **kwargs)

        # Record processed file for size monitoring
        self.size_monitor.record_processed_file(file_path)

        # Handle infected files
        if result.result == ScanResult.INFECTED:
            self._handle_infected_file(result, scan_id)

        # Only report completion for single file scans
        if not hasattr(self, "_total_files_to_scan") or self._total_files_to_scan <= 1:
            if self.progress_callback:
                self.progress_callback(
                    100.0,
                    f"Completed {Path(file_path).name}",
                )

        # Notify result
        if self.result_callback:
            self.result_callback(result)

        return result

    def validate_scan_directory(self, directory_path: str) -> dict:
        """Validate a directory before scanning with comprehensive security checks."""

        # Use the comprehensive validation function
        validation_result = validate_scan_request(directory_path)

        if not validation_result["valid"]:
            self.logger.warning("Directory validation failed: %s", validation_result["errors"])
        else:
            self.logger.info(
                "Directory validation passed. Estimated %d files, %d bytes",
                validation_result["estimated_files"],
                validation_result["estimated_size"],
            )

            # Log warnings if any
            for warning in validation_result["warnings"]:
                self.logger.warning("Validation warning: %s", warning)

        return validation_result

    def scan_files(
        self,
        file_paths: List[str],
        scan_type=None,
        max_workers: int = 4,
        timeout: Optional[int] = None,
        save_report: bool = True,
        **kwargs,
    ):
        """Scan multiple files with progress tracking and enhanced reporting."""
        from app.utils.scan_reports import ScanResult as ReportScanResult
        from app.utils.scan_reports import ScanType, ThreatInfo, ThreatLevel

        if scan_type is None:
            scan_type = ScanType.CUSTOM

        # Memory optimization: Use batched processing for large file sets
        if len(file_paths) > self.batch_size:
            return self._scan_files_batched(
                file_paths, scan_type, max_workers, save_report=save_report, **kwargs
            )

        """Scan multiple files with threading support."""
        scan_id = self.scan_report_manager.generate_scan_id()
        self._current_scan_id = scan_id
        self._scan_running = True
        self._scan_cancelled = False

        # Set total files for progress calculation
        self._total_files_to_scan = len(file_paths)
        self._files_completed = 0

        start_time = datetime.now()

        # Initialize scan result
        scan_result = ReportScanResult(
            scan_id=scan_id,
            scan_type=scan_type,
            start_time=start_time.isoformat(),
            end_time="",
            duration=0.0,
            scanned_paths=[],
            total_files=len(file_paths),
            scanned_files=0,
            threats_found=0,
            threats=[],
            errors=[],
            scan_settings=kwargs,
            engine_version="",
            signature_version="",
            success=False,
        )

        # Get engine version
        engine_version, sig_version = self.clamav_wrapper.get_engine_version()
        scan_result.engine_version = engine_version
        scan_result.signature_version = sig_version

        try:
            # Set up timeout protection
            scan_timeout = timeout or kwargs.get("timeout", 1800)  # Default 30 minutes
            scan_start_time = time.time()

            executor = ThreadPoolExecutor(max_workers=max_workers)
            try:
                # Submit all scan tasks
                future_to_path = {
                    executor.submit(self.scan_file, file_path, scan_id, **kwargs): file_path
                    for file_path in file_paths
                }

                completed = 0
                for future in as_completed(future_to_path, timeout=scan_timeout):
                    # Check for cancellation (supports both manual flag and Qt6 interruption)
                    if self._scan_cancelled:
                        self.logger.info("Scan cancelled by user - shutting down executor")
                        # Cancel all pending futures immediately
                        for pending_future in future_to_path:
                            if not pending_future.done():
                                pending_future.cancel()
                        # Shutdown executor immediately without waiting
                        executor.shutdown(wait=False)
                        break

                    # Additional check for Qt6 thread interruption if thread reference available
                    if hasattr(self, "_current_thread") and self._current_thread:
                        if hasattr(self._current_thread, "isInterruptionRequested"):
                            if self._current_thread.isInterruptionRequested():
                                self.logger.info(
                                    "Scan interrupted via Qt6 thread interruption - shutting down executor"
                                )
                                self._scan_cancelled = True
                                # Cancel all pending futures immediately
                                for pending_future in future_to_path:
                                    if not pending_future.done():
                                        pending_future.cancel()
                                # Shutdown executor immediately without waiting
                                executor.shutdown(wait=False)
                                break

                    # Check for timeout
                    if time.time() - scan_start_time > scan_timeout:
                        self.logger.warning("Scan timeout reached, stopping")
                        self._scan_cancelled = True
                        # Cancel all pending futures immediately
                        for pending_future in future_to_path:
                            if not pending_future.done():
                                pending_future.cancel()
                        # Shutdown executor immediately without waiting
                        executor.shutdown(wait=False)
                        break

                    file_path = future_to_path[future]
                    completed += 1

                    try:
                        file_result = future.result()
                        scan_result.scanned_files += 1

                        if file_result.result == ScanResult.INFECTED:
                            scan_result.threats_found += 1
                            threat_info = ThreatInfo(
                                file_path=file_result.file_path,
                                threat_name=file_result.threat_name,
                                threat_type=file_result.threat_type,
                                threat_level=ThreatLevel.INFECTED,
                                action_taken="detected",
                                timestamp=datetime.now().isoformat(),
                                file_size=file_result.file_size,
                                file_hash="",  # Would calculate if needed
                            )
                            scan_result.threats.append(threat_info)

                        elif file_result.result == ScanResult.ERROR:
                            scan_result.errors.append(f"{file_path}: {file_result.error_message}")

                    except Exception as e:
                        scan_result.errors.append(f"{file_path}: {str(e)}")
                        self.logger.error(
                            "Error scanning %s: %s", file_path, str(e)
                        )

                    # Update overall progress with better status message
                    progress = (completed / len(file_paths)) * 100
                    self._scan_progress = progress
                    files_remaining = len(file_paths) - completed

                    if self.progress_callback:
                        # Show current file being scanned and overall progress
                        current_file = Path(file_path).name
                        # Truncate filename if too long to keep "Remaining:" visible
                        max_filename_length = (
                            25  # Very conservative length to ensure "Remaining:" stays visible
                        )
                        if len(current_file) > max_filename_length:
                            current_file = current_file[: max_filename_length - 3] + "..."
                        status_msg = f"Scanning: {current_file} | Remaining: {files_remaining}"
                        self.progress_callback(progress, status_msg)

                    # Emit detailed progress information for results display
                    if self.detailed_progress_callback:
                        current_dir = str(
                            Path(file_path).parent.resolve()
                        )  # Use resolve() for consistent paths
                        detail_info = {
                            "type": "file_scanned",
                            "current_directory": current_dir,
                            "current_file": Path(file_path).name,
                            "files_completed": completed,
                            "files_remaining": files_remaining,
                            "total_files": len(file_paths),
                            "progress_percent": progress,
                            "scan_result": (file_result.result.value if file_result else "clean"),
                        }
                        self.detailed_progress_callback(detail_info)

            except Exception:
                self.logger.error(
                    "Error during scan execution: %s", str(e)
                )
                self._scan_cancelled = True
            finally:
                # Always cleanup the executor
                if "executor" in locals():
                    try:
                        executor.shutdown(wait=False)  # Don't wait for completion
                    except Exception:
                        self.logger.warning(
                            "Error shutting down executor: %s", str(e)
                        )

            # Check if scan was cancelled - return early without saving
            if self._scan_cancelled:
                self.logger.info("Scan cancelled, returning without saving results")
                scan_result.success = False
                scan_result.end_time = datetime.now().isoformat()
                scan_result.duration = (datetime.now() - start_time).total_seconds()
                return scan_result

            # Finalize scan result
            end_time = datetime.now()
            scan_result.end_time = end_time.isoformat()
            scan_result.duration = (end_time - start_time).total_seconds()
            scan_result.scanned_paths = file_paths
            scan_result.success = not self._scan_cancelled

            # Clean up temporary attributes
            if hasattr(self, "_total_files_to_scan"):
                delattr(self, "_total_files_to_scan")
            if hasattr(self, "_files_completed"):
                delattr(self, "_files_completed")

            # Save scan report (conditional based on save_report parameter)
            if save_report:
                print("\n💾 === FILESCANNER SAVE REPORT ===")
                print(f"DEBUG: FileScanner saving scan report: {scan_result.scan_id}")
                print(f"DEBUG: Scan type: {scan_result.scan_type}")
                print(f"DEBUG: Files scanned: {scan_result.scanned_files}")
                print(f"DEBUG: Threats found: {scan_result.threats_found}")
                print(
                    f"DEBUG: Report will be saved to: {
                        self.scan_report_manager.daily_reports
                    }/scan_{scan_result.scan_id}.json"
                )
                try:
                    saved_path = self.scan_report_manager.save_scan_result(scan_result)
                    print(f"DEBUG: ✅ FileScanner report saved successfully to: {saved_path}")
                except Exception as e:
                    print(f"DEBUG: ❌ FileScanner report save failed: {e}")
                    import traceback

                    traceback.print_exc()
                    raise
            else:
                print("\n💾 === FILESCANNER SKIP REPORT SAVE ===")
                print(f"DEBUG: Skipping report save for scan: {scan_result.scan_id}")
                print(f"DEBUG: Files scanned: {scan_result.scanned_files}")
                print("DEBUG: This is part of a multi-directory scan")

            self.logger.info(
                "Scan completed: %s - %d files scanned, %d threats found",
                scan_id,
                scan_result.scanned_files,
                scan_result.threats_found,
            )

        except Exception as e:
            scan_result.errors.append(f"Scan error: {str(e)}")
            scan_result.success = False
            self.logger.error("Scan failed: %s", str(e))

        finally:
            self._scan_running = False
            self._current_scan_id = None

        return scan_result

    def scan_directory(
        self,
        directory_path: str,
        scan_type=None,
        include_hidden: bool = False,
        save_report: bool = True,
        **kwargs,
    ):
        """Scan all files in a directory with security validation."""
        from app.utils.scan_reports import ScanType

        if scan_type is None:
            scan_type = ScanType.CUSTOM
        """Scan a directory recursively."""
        directory_obj = Path(directory_path)

        # Debug scan options to verify they're being received
        print("\n🔍 === FILESCANNER SCAN OPTIONS DEBUG ===")
        print(f"DEBUG: Directory: {directory_path}")
        print(f"DEBUG: Scan type: {scan_type}")
        print(f"DEBUG: Include hidden: {include_hidden}")
        print(f"DEBUG: Scan options received: {kwargs}")
        if "file_filter" in kwargs:
            print(f"DEBUG: File filter: {kwargs['file_filter']}")
        if "depth" in kwargs:
            print(f"DEBUG: Depth limit: {kwargs['depth']}")
        if "memory_limit" in kwargs:
            print(f"DEBUG: Memory limit: {kwargs['memory_limit']}")
        if "exclusions" in kwargs:
            print(f"DEBUG: Exclusions: {kwargs['exclusions']}")

        if not directory_obj.exists() or not directory_obj.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")

        # Collect all files
        file_paths = []
        # Enhanced memory and performance protection
        MAX_FILES_LIMIT = kwargs.get("max_files", 1000)  # Reduced default limit
        MEMORY_LIMIT_MB = kwargs.get("memory_limit_mb", 512)  # Memory limit

        # Handle depth limiting
        scan_depth = kwargs.get("depth", None)
        if scan_depth is not None:
            try:
                max_depth = int(scan_depth)
            except (TypeError, ValueError):
                max_depth = None
        else:
            max_depth = None

        # Always instantiate a MemoryMonitor (previous conditional check was ineffective)
        memory_monitor = MemoryMonitor()

        # Use different scanning approach based on depth limit
        if max_depth is not None:
            # Depth-limited scanning
            for file_path in self._scan_directory_with_depth(directory_obj, max_depth):
                if hasattr(self, "_scan_cancelled") and self._scan_cancelled:
                    self.logger.info("📁 File collection cancelled by manual flag")
                    break

                # Additional check for Qt6 thread interruption if thread reference available
                if hasattr(self, "_current_thread") and self._current_thread:
                    if hasattr(self._current_thread, "isInterruptionRequested"):
                        if self._current_thread.isInterruptionRequested():
                            self.logger.info(
                                "📁 File collection cancelled by Qt6 thread interruption"
                            )
                            self._scan_cancelled = True
                            break

                if file_path.is_file():
                    # Skip hidden files unless requested
                    if not include_hidden and any(part.startswith(".") for part in file_path.parts):
                        continue

                    # Apply file filter options if specified
                    if "file_filter" in kwargs:
                        file_filter = kwargs["file_filter"]
                        if file_filter == "executables":
                            # Only scan executable files
                            if not self._is_executable_file(file_path):
                                continue
                        elif file_filter == "documents":
                            # Only scan document files
                            if not self._is_document_file(file_path):
                                continue
                        elif file_filter == "archives":
                            # Only scan archive files
                            if not self._is_archive_file(file_path):
                                continue
                        # 'all' or other values scan all files (default behavior)

                    # Apply exclusion patterns if specified
                    if "exclusions" in kwargs:
                        exclusions = kwargs["exclusions"]
                        if self._is_excluded_file(file_path, exclusions):
                            continue

                    # Memory and performance checks (same as below)
                    if memory_monitor and memory_monitor.check_memory_pressure(MEMORY_LIMIT_MB):
                        self.logger.warning("Memory pressure detected, limiting file collection")
                        memory_monitor.force_garbage_collection()
                        MAX_FILES_LIMIT = min(MAX_FILES_LIMIT, len(file_paths) + 100)

                    file_paths.append(str(file_path))

                    # Check limits and interruption (same as below)
                    if len(file_paths) >= MAX_FILES_LIMIT:
                        self.logger.warning(
                            "Reached file limit (%d) in directory: %s. Scanning first %d files only.",
                            MAX_FILES_LIMIT,
                            directory_path,
                            MAX_FILES_LIMIT,
                        )
                        break

                    # More frequent interruption checks for large scans (every 100 files)
                    if len(file_paths) % 100 == 0:
                        # Check for Qt6 thread interruption
                        if hasattr(self, "_current_thread") and self._current_thread:
                            if hasattr(self._current_thread, "isInterruptionRequested"):
                                if self._current_thread.isInterruptionRequested():
                                    self.logger.info(
                                        f"📁 File collection interrupted after {
                                            len(file_paths)
                                        } files"
                                    )
                                    self._scan_cancelled = True
                                    break

                    # Periodic memory check for large directories
                    if len(file_paths) % 500 == 0 and memory_monitor:
                        if memory_monitor.check_memory_pressure(MEMORY_LIMIT_MB * 0.8):
                            self.logger.warning(
                                "Memory pressure during file collection, forcing GC"
                            )
                            memory_monitor.force_garbage_collection()
        else:
            # Regular recursive scanning (existing logic)
            for file_path in directory_obj.rglob("*"):
                # Check for cancellation (both manual flag and Qt6 interruption)
                if hasattr(self, "_scan_cancelled") and self._scan_cancelled:
                    self.logger.info("📁 File collection cancelled by manual flag")
                    break

                # Additional check for Qt6 thread interruption if thread reference available
                if hasattr(self, "_current_thread") and self._current_thread:
                    if hasattr(self._current_thread, "isInterruptionRequested"):
                        if self._current_thread.isInterruptionRequested():
                            self.logger.info(
                                "📁 File collection cancelled by Qt6 thread interruption"
                            )
                            self._scan_cancelled = True
                            break

                if file_path.is_file():
                    # Skip hidden files unless requested
                    if not include_hidden and any(part.startswith(".") for part in file_path.parts):
                        continue

                    # Apply file filter options if specified
                    if "file_filter" in kwargs:
                        file_filter = kwargs["file_filter"]
                        if file_filter == "executables":
                            # Only scan executable files
                            if not self._is_executable_file(file_path):
                                continue
                        elif file_filter == "documents":
                            # Only scan document files
                            if not self._is_document_file(file_path):
                                continue
                        elif file_filter == "archives":
                            # Only scan archive files
                            if not self._is_archive_file(file_path):
                                continue
                        # 'all' or other values scan all files (default behavior)

                    # Apply exclusion patterns if specified
                    if "exclusions" in kwargs:
                        exclusions = kwargs["exclusions"]
                        if self._is_excluded_file(file_path, exclusions):
                            continue

                    # Check memory pressure
                    if memory_monitor and memory_monitor.check_memory_pressure(MEMORY_LIMIT_MB):
                        self.logger.warning("Memory pressure detected, limiting file collection")
                        memory_monitor.force_garbage_collection()
                        MAX_FILES_LIMIT = min(MAX_FILES_LIMIT, len(file_paths) + 100)

                    file_paths.append(str(file_path))

                    # More frequent interruption checks for large scans (every 100 files)
                    if len(file_paths) % 100 == 0:
                        # Check for Qt6 thread interruption
                        if hasattr(self, "_current_thread") and self._current_thread:
                            if hasattr(self._current_thread, "isInterruptionRequested"):
                                if self._current_thread.isInterruptionRequested():
                                    self.logger.info(
                                        f"📁 File collection interrupted after {
                                            len(file_paths)
                                        } files"
                                    )
                                    self._scan_cancelled = True
                                    break

                    # Safety check: prevent scanning too many files at once
                    if len(file_paths) >= MAX_FILES_LIMIT:
                        self.logger.warning(
                            "Reached file limit (%d) in directory: %s. Scanning first %d files only.",
                            MAX_FILES_LIMIT,
                            directory_path,
                            MAX_FILES_LIMIT,
                        )
                        break

                    # Periodic memory check for large directories
                    if len(file_paths) % 500 == 0 and memory_monitor:
                        if memory_monitor.check_memory_pressure(MEMORY_LIMIT_MB * 0.8):
                            self.logger.warning(
                                "Memory pressure during file collection, forcing GC"
                            )
                            memory_monitor.force_garbage_collection()

        self.logger.info("Found %d files in directory: %s", len(file_paths), directory_path)

        return self.scan_files(file_paths, scan_type, save_report=save_report, **kwargs)

    def _handle_infected_file(self, result: ScanFileResult, scan_id: str) -> None:
        """Handle an infected file according to configuration."""
        auto_quarantine = self.config.get("security_settings", {}).get(
            "auto_quarantine_threats", False
        )

        if auto_quarantine:
            success = self.quarantine_manager.quarantine_file(
                result.file_path, result.threat_name, result.threat_type, scan_id
            )

            if success:
                self.logger.warning(
                    "Infected file quarantined: %s (%s)",
                    result.file_path,
                    result.threat_name,
                )
            else:
                self.logger.error(
                    "Failed to quarantine infected file: %s (%s)",
                    result.file_path,
                    result.threat_name,
                )

    def cancel_scan(self) -> None:
        """Cancel the current scan."""
        if self._scan_running:
            self._scan_cancelled = True
            self.logger.info("Scan cancellation requested")

    def reset_scan_state(self) -> None:
        """Reset scan state for a new scan - clears cancellation flags."""
        self._scan_cancelled = False
        self._scan_running = False
        self.logger.info("🔄 FileScanner state reset for new scan")

    def get_scan_progress(self) -> float:
        """Get current scan progress (0-100)."""
        return self._scan_progress

    def is_scanning(self) -> bool:
        """Check if a scan is currently running."""
        return self._scan_running

    def start_scheduler(self) -> None:
        """Start the scheduled scan scheduler."""
        if self._scheduler_running and self._scheduler_thread and self._scheduler_thread.is_alive():
            self.logger.info("Scheduler is already running")
            return

        if not _SCHED_AVAILABLE:
            self.logger.warning(
                "Scheduled scanning enabled but 'schedule' module is not available; skipping scheduler start"
            )
            return

        self._scheduler_running = True
        # Clear the stop event before starting
        self._scheduler_stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Scan scheduler started")

    def stop_scheduler(self) -> None:
        """Stop the scheduled scan scheduler."""
        self._scheduler_running = False
        # Signal the event to wake up the scheduler thread immediately
        self._scheduler_stop_event.set()

        if self._scheduler_thread and self._scheduler_thread.is_alive():
            # With event-based stopping, thread should stop almost immediately
            self._scheduler_thread.join(timeout=2.0)
            if self._scheduler_thread.is_alive():
                self.logger.warning("Scheduler thread did not stop gracefully")

        # Reset the event for next time
        self._scheduler_stop_event.clear()
        self.logger.info("Scan scheduler stopped")

    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        # Setup scheduled scans based on configuration
        if not _SCHED_AVAILABLE:
            self.logger.debug("Schedule module not available; scheduler loop exiting")
            return
        schedule_config = self.config.get("advanced_settings", {})
        update_frequency = schedule_config.get("update_frequency", "daily")
        update_time = schedule_config.get("update_time", "02:00")
        definition_update = schedule_config.get("auto_update_definitions", True)

        # Schedule virus definition updates
        if definition_update:
            # Update definitions daily at 1 AM
            schedule.every().day.at("01:00").do(self.update_virus_definitions)
            self.logger.info("Scheduled daily virus definition updates at 01:00")

        # Schedule system scans
        if update_frequency == "daily":
            schedule.every().day.at(update_time).do(self._scheduled_scan)
            self.logger.info(f"Scheduled daily scans at {update_time}")
        elif update_frequency == "weekly":
            schedule.every().sunday.at(update_time).do(self._scheduled_scan)
            self.logger.info(f"Scheduled weekly scans on Sunday at {update_time}")
        elif update_frequency == "monthly":
            # Schedule first Sunday of each month (monthly approximation)
            schedule.every(4).weeks.at(update_time).do(self._scheduled_scan)
            self.logger.info(f"Scheduled monthly scans every 4 weeks at {update_time}")

        while self._scheduler_running:
            schedule.run_pending()
            # Use event-based waiting for immediate response to stop signals
            # Wait for up to 60 seconds, but can be interrupted immediately
            if self._scheduler_stop_event.wait(timeout=60):
                # Event was set, we should stop
                break

    def _scheduled_scan(self) -> None:
        """Perform a scheduled scan."""
        if self._scan_running:
            self.logger.info("Skipping scheduled scan - another scan is running")
            return

        self.logger.info("Starting scheduled scan")

        # Get scan paths from configuration or use defaults
        scan_paths = self.config.get("advanced_settings", {}).get(
            "scheduled_scan_paths",
            [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Documents"),
                tempfile.gettempdir(),
            ],
        )

        # Filter existing paths
        existing_paths = [path for path in scan_paths if Path(path).exists()]

        if existing_paths:
            try:
                for path in existing_paths:
                    self.scan_directory(path, ScanType.SCHEDULED)
            except Exception as e:
                self.logger.error("Scheduled scan failed: %s", str(e))

    def _scan_files_batched(
        self,
        file_paths: List[str],
        scan_type,
        max_workers: int = 4,
        save_report: bool = True,
        **kwargs,
    ):
        """Scan files in batches to optimize memory usage."""

        scan_id = self.scan_report_manager.generate_scan_id()
        self._current_scan_id = scan_id
        self._scan_running = True
        self._scan_cancelled = False

        # Set total files for progress calculation
        self._total_files_to_scan = len(file_paths)
        self._files_completed = 0

        start_time = datetime.now()

        # Initialize combined scan result
        combined_result = ReportScanResult(
            scan_id=scan_id,
            scan_type=scan_type,
            start_time=start_time.isoformat(),
            end_time="",
            duration=0.0,
            scanned_paths=[],
            total_files=len(file_paths),
            scanned_files=0,
            threats_found=0,
            threats=[],
            errors=[],
            scan_settings=kwargs,
            engine_version="",
            signature_version="",
            success=False,
        )

        # Get engine version
        engine_version, sig_version = self.clamav_wrapper.get_engine_version()
        combined_result.engine_version = engine_version
        combined_result.signature_version = sig_version

        try:
            # Process files in batches
            for batch_start in range(0, len(file_paths), self.batch_size):
                if self._scan_cancelled:
                    break

                batch_end = min(batch_start + self.batch_size, len(file_paths))
                batch_files = file_paths[batch_start:batch_end]

                # Check memory pressure before each batch
                if self.memory_monitor.check_memory_pressure(self.max_memory_usage):
                    self.logger.warning("Memory pressure detected, forcing garbage collection")
                    self.memory_monitor.force_garbage_collection()

                # Process batch with reduced worker count if needed
                batch_workers = min(max_workers, len(batch_files))

                with ThreadPoolExecutor(max_workers=batch_workers) as executor:
                    future_to_path = {
                        executor.submit(self.scan_file, file_path, scan_id, **kwargs): file_path
                        for file_path in batch_files
                    }

                    for future in as_completed(future_to_path):
                        if self._scan_cancelled:
                            break

                        file_path = future_to_path[future]
                        try:
                            result = future.result()
                            combined_result.scanned_files += 1
                            combined_result.scanned_paths.append(file_path)

                            if result.result == ScanResult.INFECTED:
                                combined_result.threats_found += 1

                                # Calculate file info for threat
                                file_size = 0
                                file_hash = "unknown"
                                try:
                                    file_stat = Path(file_path).stat()
                                    file_size = file_stat.st_size
                                    file_hash = hashlib.sha256(
                                        Path(file_path).read_bytes()
                                    ).hexdigest()[:16]  # Short hash
                                except (OSError, IOError):
                                    pass

                                threat_info = ThreatInfo(
                                    file_path=file_path,
                                    threat_name=result.threat_name or "Unknown",
                                    threat_type="malware",
                                    threat_level=ThreatLevel.INFECTED,
                                    action_taken="detected",
                                    timestamp=datetime.now().isoformat(),
                                    file_size=file_size,
                                    file_hash=file_hash,
                                )
                                combined_result.threats.append(threat_info)

                        except Exception as e:
                            self.logger.error(
                                "Error scanning %s: %s", file_path, str(e)
                            )
                            combined_result.errors.append(f"Error scanning {file_path}: {str(e)}")

                        # Update progress
                        self._files_completed += 1
                        progress = (self._files_completed / self._total_files_to_scan) * 100
                        if self.progress_callback:
                            self.progress_callback(
                                progress,
                                f"Scanned {self._files_completed}/{self._total_files_to_scan} files",
                            )

                # Small delay between batches to prevent system overload
                time.sleep(0.1)

            # Finalize results
            end_time = datetime.now()
            combined_result.end_time = end_time.isoformat()
            combined_result.duration = (end_time - start_time).total_seconds()
            combined_result.success = True

            # Log memory usage statistics
            memory_stats = self.memory_monitor.get_stats()
            self.logger.info(
                "Batched scan completed. Memory usage - Current: %.1fMB, Peak: %.1fMB",
                memory_stats["current_mb"],
                memory_stats["peak_mb"],
            )

        except Exception as e:
            self.logger.error("Batched scan failed: %s", str(e))
            combined_result.errors.append(f"Scan failed: {str(e)}")
        finally:
            self._scan_running = False

            # Save scan report (conditional based on save_report parameter)
            if save_report:
                try:
                    print("\n💾 === FILESCANNER BATCHED SAVE REPORT ===")
                    print(
                        f"DEBUG: FileScanner saving batched scan report: {combined_result.scan_id}"
                    )
                    print(f"DEBUG: Batched scan type: {combined_result.scan_type}")
                    print(f"DEBUG: Total files scanned: {combined_result.scanned_files}")
                    print(f"DEBUG: Total threats found: {combined_result.threats_found}")
                    self.scan_report_manager.save_scan_result(combined_result)
                    print("DEBUG: ✅ FileScanner batched report saved successfully")
                except Exception as e:
                    print(f"DEBUG: ❌ FileScanner batched report save failed: {e}")
                    self.logger.error(
                        "Failed to save scan report: %s", str(e)
                    )
            else:
                print("\n💾 === FILESCANNER BATCHED SKIP REPORT SAVE ===")
                print(f"DEBUG: Skipping batched report save for scan: {combined_result.scan_id}")
                print(f"DEBUG: Total files scanned: {combined_result.scanned_files}")
                print("DEBUG: This is part of a multi-directory scan")

        return combined_result

    def _scan_directory_with_depth(self, directory_obj, max_depth):
        """Scan directory with depth limitation."""

        def _recursive_scan(current_dir, current_depth):
            if current_depth > max_depth:
                return

            try:
                for item in current_dir.iterdir():
                    yield item
                    if item.is_dir() and current_depth < max_depth:
                        yield from _recursive_scan(item, current_depth + 1)
            except (OSError, PermissionError):
                # Skip directories we can't access
                pass

        return _recursive_scan(directory_obj, 0)

    def _is_executable_file(self, file_path):
        """Check if a file is executable."""
        try:
            # Check file extension
            executable_extensions = {
                ".exe",
                ".bat",
                ".cmd",
                ".com",
                ".scr",
                ".pif",
                ".app",
                ".deb",
                ".rpm",
                ".dmg",
                ".pkg",
                ".msi",
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                ".py",
                ".pl",
                ".rb",
                ".js",
                ".jar",
                ".bin",
                ".run",
            }
            if file_path.suffix.lower() in executable_extensions:
                return True

            # Check if file has execute permissions (Unix-like systems)
            if hasattr(os, "access"):
                return os.access(file_path, os.X_OK)

            return False
        except (OSError, AttributeError):
            return False

    def _is_document_file(self, file_path):
        """Check if a file is a document."""
        document_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".txt",
            ".rtf",
            ".odt",
            ".ods",
            ".odp",
            ".csv",
            ".xml",
            ".html",
            ".htm",
            ".md",
            ".tex",
            ".epub",
            ".mobi",
        }
        return file_path.suffix.lower() in document_extensions

    def _is_archive_file(self, file_path):
        """Check if a file is an archive."""
        archive_extensions = {
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".tar.gz",
            ".tar.bz2",
            ".tar.xz",
            ".tgz",
            ".tbz2",
            ".cab",
            ".iso",
            ".dmg",
            ".img",
        }
        return file_path.suffix.lower() in archive_extensions

    def _is_excluded_file(self, file_path, exclusions):
        """Check if a file matches any exclusion pattern."""

        file_str = str(file_path)
        for pattern in exclusions:
            if fnmatch.fnmatch(file_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True
        return False
