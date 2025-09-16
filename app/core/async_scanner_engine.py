#!/usr/bin/env python3
"""
Async Scanner Engine for xanadOS Search & Destroy
Modernized core scanning engine with async/await patterns for high-performance scanning.
"""

import asyncio
import logging
import time
import types
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

from app.core.async_file_watcher import AsyncFileSystemWatcher
from app.core.async_threat_detector import AsyncThreatDetector, ScanResult
from app.core.async_resource_coordinator import get_resource_coordinator, ResourceType


class ScanType(Enum):
    """Types of scans available."""
    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    REAL_TIME = "real_time"
    SCHEDULED = "scheduled"


class ScanStatus(Enum):
    """Scan status values."""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    SCANNING = "scanning"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ScanConfiguration:
    """Configuration for a scan operation."""
    scan_type: ScanType
    target_paths: list[str]
    exclusions: list[str] | None = None
    max_file_size: int = 500 * 1024 * 1024  # 500MB default
    follow_symlinks: bool = False
    recursive: bool = True
    file_patterns: list[str] | None = None
    enable_heuristics: bool = True
    enable_behavioral: bool = True
    max_concurrent_files: int = 50
    priority_extensions: list[str] | None = None


@dataclass
class ScanStatistics:
    """Statistics from a scan operation."""
    scan_id: str
    start_time: datetime
    end_time: datetime | None = None
    files_scanned: int = 0
    threats_detected: int = 0
    errors_encountered: int = 0
    bytes_scanned: int = 0
    scan_duration_seconds: float = 0.0
    scan_rate_files_per_second: float = 0.0
    scan_rate_mb_per_second: float = 0.0
    status: ScanStatus = ScanStatus.NOT_STARTED


@dataclass
class ScanProgress:
    """Real-time scan progress information."""
    scan_id: str
    current_file: str | None = None
    files_processed: int = 0
    total_files: int = 0
    progress_percentage: float = 0.0
    threats_found: int = 0
    current_status: ScanStatus = ScanStatus.NOT_STARTED
    estimated_time_remaining: float = 0.0
    scan_rate: float = 0.0


class AsyncScannerEngine:
    """
    High-performance async scanner engine for xanadOS Search & Destroy.

    Features:
    - Concurrent file scanning with configurable limits
    - Real-time progress tracking and monitoring
    - Async file discovery and enumeration
    - Integration with async threat detector and file watcher
    - Memory-efficient streaming of large directory structures
    - Configurable scan policies and exclusions
    """

    def __init__(
        self,
        threat_detector: AsyncThreatDetector | None = None,
        file_watcher: AsyncFileSystemWatcher | None = None,
        max_concurrent_scans: int = 5,
        default_max_workers: int = 50,
    ) -> None:
        """Initialize the async scanner engine."""
        self.logger = logging.getLogger(__name__)

        # Component integration
        self.threat_detector = threat_detector or AsyncThreatDetector()
        self.file_watcher = file_watcher or AsyncFileSystemWatcher()

        # Configuration
        self.max_concurrent_scans = max_concurrent_scans
        self.default_max_workers = default_max_workers

        # Active scans tracking
        self.active_scans: dict[str, ScanStatistics] = {}
        self.scan_results: dict[str, list[ScanResult]] = {}
        self.scan_progress: dict[str, ScanProgress] = {}
        self.scan_semaphore = asyncio.Semaphore(max_concurrent_scans)

        # Real-time scanning
        self.real_time_enabled = False
        self.real_time_task: asyncio.Task[None] | None = None
        self._current_real_time_config: ScanConfiguration | None = None

        # Resource coordination
        self.resource_coordinator = get_resource_coordinator()

        # Performance tracking
        self.total_scans_completed = 0
        self.total_files_scanned = 0
        self.total_threats_detected = 0
        self.engine_start_time = time.time()

        self.logger.info(
            "Async scanner engine initialized (max_scans=%d, max_workers=%d)",
            max_concurrent_scans,
            default_max_workers
        )

    async def __aenter__(self) -> "AsyncScannerEngine":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        """Async context manager exit with cleanup."""
        await self.cleanup_async()

    async def cleanup_async(self) -> None:
        """Clean up async scanner engine resources."""
        try:
            self.logger.info("Starting async scanner engine cleanup...")

            # Cancel real-time scanning if running
            if self.real_time_task and not self.real_time_task.done():
                self.real_time_task.cancel()
                try:
                    await self.real_time_task
                except asyncio.CancelledError:
                    pass

            # Cancel any active scans
            for scan_id in list(self.active_scans.keys()):
                await self.cancel_scan_async(scan_id)

            # Clear tracking data
            self.active_scans.clear()
            self.scan_results.clear()
            self.scan_progress.clear()

            # Clean up components
            if hasattr(self.threat_detector, 'cleanup_async'):
                await self.threat_detector.cleanup_async()

            self.real_time_enabled = False

            self.logger.info("Async scanner engine cleanup completed")

        except Exception as e:
            self.logger.error("Error during scanner engine cleanup: %s", e)

    async def start_scan_async(
        self,
        config: ScanConfiguration,
        scan_id: str | None = None
    ) -> str:
        """Start an async scan operation."""
        if scan_id is None:
            scan_id = f"scan_{int(time.time() * 1000)}"

        # Validate scan configuration
        if not config.target_paths:
            raise ValueError("Target paths cannot be empty")

        # Check concurrent scan limits
        if len(self.active_scans) >= self.max_concurrent_scans:
            raise RuntimeError(
                f"Maximum concurrent scans ({self.max_concurrent_scans}) exceeded"
            )

        # Initialize scan tracking
        stats = ScanStatistics(
            scan_id=scan_id,
            start_time=datetime.now(),
            status=ScanStatus.INITIALIZING
        )

        progress = ScanProgress(
            scan_id=scan_id,
            current_status=ScanStatus.INITIALIZING
        )

        self.active_scans[scan_id] = stats
        self.scan_progress[scan_id] = progress
        self.scan_results[scan_id] = []

        # Start scan task
        asyncio.create_task(self._execute_scan_async(scan_id, config))

        self.logger.info("Started scan %s with %d target paths", scan_id, len(config.target_paths))
        return scan_id

    async def _execute_scan_async(self, scan_id: str, config: ScanConfiguration) -> None:
        """Execute the actual scan operation."""
        stats = self.active_scans[scan_id]
        progress = self.scan_progress[scan_id]

        try:
            async with self.scan_semaphore:
                stats.status = ScanStatus.SCANNING
                progress.current_status = ScanStatus.SCANNING

                # Discover files to scan
                self.logger.info("Discovering files for scan %s", scan_id)
                file_paths = await self._discover_files_async(config)

                progress.total_files = len(file_paths)
                self.logger.info("Found %d files to scan for %s", len(file_paths), scan_id)

                if not file_paths:
                    stats.status = ScanStatus.COMPLETED
                    progress.current_status = ScanStatus.COMPLETED
                    stats.end_time = datetime.now()
                    stats.scan_duration_seconds = (stats.end_time - stats.start_time).total_seconds()
                    return

                # Execute concurrent scanning
                scan_results = await self._scan_files_concurrently_async(
                    scan_id, file_paths, config
                )

                # Update final statistics
                self.scan_results[scan_id] = scan_results
                stats.status = ScanStatus.COMPLETED
                progress.current_status = ScanStatus.COMPLETED
                stats.end_time = datetime.now()
                stats.scan_duration_seconds = (stats.end_time - stats.start_time).total_seconds()

                # Calculate performance metrics
                if stats.scan_duration_seconds > 0:
                    stats.scan_rate_files_per_second = stats.files_scanned / stats.scan_duration_seconds
                    stats.scan_rate_mb_per_second = (stats.bytes_scanned / 1024 / 1024) / stats.scan_duration_seconds

                progress.progress_percentage = 100.0

                # Update global counters
                self.total_scans_completed += 1
                self.total_files_scanned += stats.files_scanned
                self.total_threats_detected += stats.threats_detected

                self.logger.info(
                    "Scan %s completed: %d files, %d threats, %.2fs",
                    scan_id,
                    stats.files_scanned,
                    stats.threats_detected,
                    stats.scan_duration_seconds
                )

        except Exception as e:
            self.logger.error("Error in scan %s: %s", scan_id, e)
            stats.status = ScanStatus.ERROR
            progress.current_status = ScanStatus.ERROR
            stats.end_time = datetime.now()
            stats.errors_encountered += 1

    async def _discover_files_async(self, config: ScanConfiguration) -> list[str]:
        """Discover files to scan based on configuration."""
        discovered_files = []

        try:
            for target_path in config.target_paths:
                if not await aiofiles.os.path.exists(target_path):
                    self.logger.warning("Target path does not exist: %s", target_path)
                    continue

                if await aiofiles.os.path.isfile(target_path):
                    # Single file target
                    if self._should_scan_file(target_path, config):
                        discovered_files.append(target_path)
                else:
                    # Directory target
                    files = await self._discover_directory_files_async(target_path, config)
                    discovered_files.extend(files)

            # Remove duplicates and sort
            discovered_files = sorted(set(discovered_files))

            # Apply priority ordering if specified
            if config.priority_extensions:
                discovered_files = self._sort_by_priority(discovered_files, config.priority_extensions)

            return discovered_files

        except Exception as e:
            self.logger.error("Error discovering files: %s", e)
            return []

    async def _discover_directory_files_async(
        self, directory_path: str, config: ScanConfiguration
    ) -> list[str]:
        """Discover files in a directory asynchronously."""
        discovered_files = []

        try:
            if config.recursive:
                # Use proper async directory traversal
                discovered_files = await self._async_walk_directory(directory_path, config)
            else:
                # Scan only direct files in directory
                try:
                    async with aiofiles.os.scandir(directory_path) as entries:
                        async for entry in entries:
                            if await aiofiles.os.path.isfile(entry.path):
                                if self._should_scan_file(entry.path, config):
                                    discovered_files.append(entry.path)
                except Exception as e:
                    self.logger.error("Error scanning directory %s: %s", directory_path, e)

            return discovered_files

        except Exception as e:
            self.logger.error("Error discovering files in %s: %s", directory_path, e)
            return []

    async def _async_walk_directory(self, directory_path: str, config: ScanConfiguration) -> list[str]:
        """Recursively discover files using async operations."""
        discovered_files = []
        directories_to_process = [directory_path]

        while directories_to_process:
            current_dir = directories_to_process.pop(0)

            try:
                # Check if directory should be excluded
                if config.exclusions and any(excl in current_dir for excl in config.exclusions):
                    continue

                async with aiofiles.os.scandir(current_dir) as entries:
                    async for entry in entries:
                        if await aiofiles.os.path.isfile(entry.path):
                            if self._should_scan_file(entry.path, config):
                                discovered_files.append(entry.path)
                        elif await aiofiles.os.path.isdir(entry.path):
                            # Add directory to process queue if following symlinks or it's not a symlink
                            if config.follow_symlinks or not await aiofiles.os.path.islink(entry.path):
                                directories_to_process.append(entry.path)

            except PermissionError:
                self.logger.warning("Permission denied accessing directory: %s", current_dir)
            except Exception as e:
                self.logger.error("Error processing directory %s: %s", current_dir, e)

        return discovered_files

    def _should_scan_file(self, file_path: str, config: ScanConfiguration) -> bool:
        """Determine if a file should be scanned based on configuration."""
        try:
            # Check exclusions
            if config.exclusions:
                for exclusion in config.exclusions:
                    if exclusion in file_path:
                        return False

            # Check file patterns
            if config.file_patterns:
                path_obj = Path(file_path)
                matches_pattern = any(
                    path_obj.match(pattern) for pattern in config.file_patterns
                )
                if not matches_pattern:
                    return False

            return True

        except Exception as e:
            self.logger.error("Error evaluating file %s: %s", file_path, e)
            return False

    def _sort_by_priority(self, file_paths: list[str], priority_extensions: list[str]) -> list[str]:
        """Sort files by priority extensions."""
        priority_files = []
        regular_files = []

        for file_path in file_paths:
            path_obj = Path(file_path)
            if path_obj.suffix.lower() in [ext.lower() for ext in priority_extensions]:
                priority_files.append(file_path)
            else:
                regular_files.append(file_path)

        return priority_files + regular_files

    async def _scan_files_concurrently_async(
        self, scan_id: str, file_paths: list[str], config: ScanConfiguration
    ) -> list[ScanResult]:
        """Scan files concurrently with progress tracking."""
        all_results = []
        stats = self.active_scans[scan_id]
        progress = self.scan_progress[scan_id]

        # Create semaphore for controlling file-level concurrency
        file_semaphore = asyncio.Semaphore(config.max_concurrent_files)

        async def scan_single_file(file_path: str) -> ScanResult:
            async with file_semaphore:
                try:
                    # Check file size limits
                    stat_result = await aiofiles.os.stat(file_path)
                    if stat_result.st_size > config.max_file_size:
                        return ScanResult(
                            file_path=file_path,
                            is_threat=False,
                            error="File exceeds size limit"
                        )

                    # Update progress
                    progress.current_file = file_path

                    # Perform the scan
                    result = await self.threat_detector.scan_file_async(file_path)

                    # Update statistics
                    stats.files_scanned += 1
                    stats.bytes_scanned += stat_result.st_size
                    progress.files_processed += 1

                    if result.is_threat:
                        stats.threats_detected += 1
                        progress.threats_found += 1

                    if result.error:
                        stats.errors_encountered += 1

                    # Update progress percentage
                    progress.progress_percentage = (
                        progress.files_processed / progress.total_files * 100
                    )

                    # Calculate estimated time remaining
                    elapsed = time.time() - stats.start_time.timestamp()
                    if progress.files_processed > 0:
                        rate = progress.files_processed / elapsed
                        remaining_files = progress.total_files - progress.files_processed
                        progress.estimated_time_remaining = remaining_files / rate if rate > 0 else 0
                        progress.scan_rate = rate

                    return result

                except Exception as e:
                    self.logger.error("Error scanning file %s: %s", file_path, e)
                    stats.errors_encountered += 1
                    return ScanResult(
                        file_path=file_path,
                        is_threat=False,
                        error=str(e)
                    )

        # Process files in batches to manage memory usage
        batch_size = min(config.max_concurrent_files, 100)

        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]

            # Create tasks for this batch
            tasks = [
                asyncio.create_task(scan_single_file(file_path))
                for file_path in batch
            ]

            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error("Exception in batch scan: %s", result)
                    stats.errors_encountered += 1
                elif isinstance(result, ScanResult):
                    all_results.append(result)

        return all_results

    async def get_scan_progress_async(self, scan_id: str) -> ScanProgress | None:
        """Get real-time progress for a scan."""
        return self.scan_progress.get(scan_id)

    async def get_scan_statistics_async(self, scan_id: str) -> ScanStatistics | None:
        """Get statistics for a scan."""
        return self.active_scans.get(scan_id)

    async def get_scan_results_async(self, scan_id: str) -> list[ScanResult] | None:
        """Get results for a completed scan."""
        return self.scan_results.get(scan_id)

    async def cancel_scan_async(self, scan_id: str) -> bool:
        """Cancel an active scan."""
        try:
            if scan_id in self.active_scans:
                stats = self.active_scans[scan_id]
                progress = self.scan_progress[scan_id]

                if stats.status in [ScanStatus.SCANNING, ScanStatus.INITIALIZING]:
                    stats.status = ScanStatus.CANCELLED
                    progress.current_status = ScanStatus.CANCELLED
                    stats.end_time = datetime.now()
                    stats.scan_duration_seconds = (stats.end_time - stats.start_time).total_seconds()

                    self.logger.info("Scan %s cancelled", scan_id)
                    return True

            return False

        except Exception as e:
            self.logger.error("Error cancelling scan %s: %s", scan_id, e)
            return False

    async def pause_scan_async(self, scan_id: str) -> bool:
        """Pause an active scan."""
        # Note: Actual pause implementation would require more complex task management
        # This is a simplified version for demonstration
        try:
            if scan_id in self.active_scans:
                stats = self.active_scans[scan_id]
                progress = self.scan_progress[scan_id]

                if stats.status == ScanStatus.SCANNING:
                    stats.status = ScanStatus.PAUSED
                    progress.current_status = ScanStatus.PAUSED

                    self.logger.info("Scan %s paused", scan_id)
                    return True

            return False

        except Exception as e:
            self.logger.error("Error pausing scan %s: %s", scan_id, e)
            return False

    async def resume_scan_async(self, scan_id: str) -> bool:
        """Resume a paused scan."""
        try:
            if scan_id in self.active_scans:
                stats = self.active_scans[scan_id]
                progress = self.scan_progress[scan_id]

                if stats.status == ScanStatus.PAUSED:
                    stats.status = ScanStatus.SCANNING
                    progress.current_status = ScanStatus.SCANNING

                    self.logger.info("Scan %s resumed", scan_id)
                    return True

            return False

        except Exception as e:
            self.logger.error("Error resuming scan %s: %s", scan_id, e)
            return False

    async def start_real_time_scanning_async(
        self, watch_paths: list[str], scan_config: ScanConfiguration | None = None
    ) -> bool:
        """Start real-time scanning of specified paths."""
        try:
            if self.real_time_enabled:
                self.logger.warning("Real-time scanning already enabled")
                return False

            if scan_config is None:
                scan_config = ScanConfiguration(
                    scan_type=ScanType.REAL_TIME,
                    target_paths=watch_paths,
                    max_concurrent_files=10
                )

            # Store config for use in event handler
            self._current_real_time_config = scan_config

            # Start file watcher for real-time events
            await self.file_watcher.start_watching()

            # Create real-time scanning task
            self.real_time_task = asyncio.create_task(
                self._real_time_scan_loop_async(scan_config)
            )

            self.real_time_enabled = True
            self.logger.info("Real-time scanning started for %d paths", len(watch_paths))
            return True

        except Exception as e:
            self.logger.error("Error starting real-time scanning: %s", e)
            return False

    async def _real_time_scan_loop_async(self, config: ScanConfiguration) -> None:
        """Main loop for real-time scanning."""
        try:
            # Set up the file watcher with callback for this scan session
            self.file_watcher.event_callback = self._handle_file_event_async  # type: ignore[assignment]

            while self.real_time_enabled:
                # The actual event handling is done via callback
                # Just sleep and let the callback handle events
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            self.logger.info("Real-time scan loop cancelled")
        except (OSError, RuntimeError) as e:
            self.logger.error("Error in real-time scan loop: %s", e)
        finally:
            # Clear the callback
            if hasattr(self.file_watcher, 'event_callback'):
                self.file_watcher.event_callback = None

    async def _handle_file_event_async(self, event: Any) -> None:
        """Handle file system events for real-time scanning."""
        try:
            # Check if it's a file creation or modification event
            if hasattr(event, 'event_type') and hasattr(event, 'file_path'):
                from app.monitoring.file_watcher import WatchEventType

                if event.event_type in [WatchEventType.FILE_CREATED, WatchEventType.FILE_MODIFIED]:
                    file_path = event.file_path

                    # Use current scan config or create a default one
                    config = getattr(self, '_current_real_time_config', create_quick_scan_config([]))

                    if self._should_scan_file(file_path, config):
                        self.logger.debug("Real-time scanning file: %s", file_path)

                        # Scan the file
                        async with self.resource_coordinator.acquire_resource(
                            ResourceType.FILE_IO
                        ) as _:
                            result = await self._scan_single_file_async(file_path, config)
                            await self._handle_scan_result_async(result)

        except Exception as e:
            self.logger.error("Error handling file event: %s", e)

    async def _scan_single_file_async(self, file_path: str, config: ScanConfiguration) -> ScanResult:
        """Scan a single file asynchronously."""
        try:
            return await self.threat_detector.scan_file_async(file_path)
        except Exception as e:
            self.logger.error("Error scanning file %s: %s", file_path, e)
            return ScanResult(
                file_path=file_path,
                is_threat=False,
                error=str(e)
            )

    async def _handle_scan_result_async(self, result: ScanResult) -> None:
        """Handle the result of a file scan."""
        try:
            if result.is_threat:
                threat_info = result.threat_detection.threat_type if result.threat_detection else "Unknown"
                self.logger.warning("Threat detected in %s: %s", result.file_path, threat_info)
                # Could trigger additional actions like quarantine here
            else:
                self.logger.debug("File clean: %s", result.file_path)
        except Exception as e:
            self.logger.error("Error handling scan result: %s", e)

    async def stop_real_time_scanning_async(self) -> bool:
        """Stop real-time scanning."""
        try:
            if not self.real_time_enabled:
                return False

            self.real_time_enabled = False

            if self.real_time_task:
                self.real_time_task.cancel()
                try:
                    await self.real_time_task
                except asyncio.CancelledError:
                    pass
                self.real_time_task = None

            await self.file_watcher.stop_watching()

            self.logger.info("Real-time scanning stopped")
            return True

        except Exception as e:
            self.logger.error("Error stopping real-time scanning: %s", e)
            return False

    async def get_engine_statistics_async(self) -> dict[str, Any]:
        """Get overall engine performance statistics."""
        uptime = time.time() - self.engine_start_time

        return {
            "uptime_seconds": uptime,
            "total_scans_completed": self.total_scans_completed,
            "total_files_scanned": self.total_files_scanned,
            "total_threats_detected": self.total_threats_detected,
            "active_scans": len(self.active_scans),
            "real_time_enabled": self.real_time_enabled,
            "max_concurrent_scans": self.max_concurrent_scans,
            "default_max_workers": self.default_max_workers,
            "average_files_per_scan": (
                self.total_files_scanned / self.total_scans_completed
                if self.total_scans_completed > 0 else 0
            ),
            "threat_detection_rate": (
                self.total_threats_detected / self.total_files_scanned
                if self.total_files_scanned > 0 else 0
            ),
        }

    async def cleanup_completed_scans_async(self, keep_recent: int = 10) -> int:
        """Clean up old completed scan data."""
        try:
            completed_scans = [
                scan_id for scan_id, stats in self.active_scans.items()
                if stats.status in [ScanStatus.COMPLETED, ScanStatus.CANCELLED, ScanStatus.ERROR]
            ]

            # Sort by completion time and keep only recent ones
            completed_scans.sort(
                key=lambda x: self.active_scans[x].end_time or datetime.min,
                reverse=True
            )

            scans_to_remove = completed_scans[keep_recent:]

            for scan_id in scans_to_remove:
                del self.active_scans[scan_id]
                self.scan_progress.pop(scan_id, None)
                self.scan_results.pop(scan_id, None)

            self.logger.info("Cleaned up %d completed scans", len(scans_to_remove))
            return len(scans_to_remove)

        except Exception as e:
            self.logger.error("Error cleaning up scans: %s", e)
            return 0

    async def shutdown_async(self) -> None:
        """Shutdown the scanner engine gracefully."""
        try:
            # Stop real-time scanning
            if self.real_time_enabled:
                await self.stop_real_time_scanning_async()

            # Cancel any active scans
            active_scan_ids = list(self.active_scans.keys())
            for scan_id in active_scan_ids:
                await self.cancel_scan_async(scan_id)

            # Shutdown components
            await self.threat_detector.shutdown_async()
            await self.file_watcher.stop_watching()

            self.logger.info("Scanner engine shutdown completed")

        except Exception as e:
            self.logger.error("Error during scanner engine shutdown: %s", e)


# Utility functions for scanner configuration
def create_quick_scan_config(target_paths: list[str]) -> ScanConfiguration:
    """Create a configuration for a quick scan."""
    return ScanConfiguration(
        scan_type=ScanType.QUICK,
        target_paths=target_paths,
        recursive=False,
        max_concurrent_files=20,
        priority_extensions=['.exe', '.dll', '.scr', '.bat', '.cmd', '.com'],
        file_patterns=['*.exe', '*.dll', '*.scr', '*.bat', '*.cmd', '*.com']
    )


def create_full_scan_config(target_paths: list[str]) -> ScanConfiguration:
    """Create a configuration for a full system scan."""
    return ScanConfiguration(
        scan_type=ScanType.FULL,
        target_paths=target_paths,
        recursive=True,
        max_concurrent_files=50,
        enable_heuristics=True,
        enable_behavioral=True,
        exclusions=[
            '/proc/', '/sys/', '/dev/', '/run/', '/tmp/',
            '.git/', '.svn/', '.hg/', '__pycache__/',
            'node_modules/', '.cache/', '.tmp/'
        ]
    )


def create_custom_scan_config(
    target_paths: list[str],
    **kwargs: Any
) -> ScanConfiguration:
    """Create a custom scan configuration with specific parameters."""
    return ScanConfiguration(
        scan_type=ScanType.CUSTOM,
        target_paths=target_paths,
        **kwargs
    )
