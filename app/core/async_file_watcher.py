#!/usr/bin/env python3
"""
Async File System Watcher for xanadOS Search & Destroy
Modernized version with async/await patterns and non-blocking I/O operations.
"""

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

import aiofiles
import aiofiles.os

# Import from the original file watcher for compatibility
from app.monitoring.file_watcher import WatchEvent, WatchEventType


@dataclass
class AsyncFileStats:
    """Async-friendly file statistics."""
    size: int
    mtime: float
    exists: bool = True


class AsyncFileSystemWatcher:
    """
    Async file system watcher using modern async/await patterns.

    Features:
    - Non-blocking file I/O using aiofiles
    - Async event handling with proper context management
    - Configurable batch processing and concurrency limits
    - Memory-efficient async generators for large directory scans
    - Proper async cancellation support
    """

    def __init__(
        self,
        paths_to_watch: list[str] | None = None,
        event_callback: Callable[[WatchEvent], None] | None = None,
        max_workers: int = 10,
        poll_interval: float = 1.0,
    ) -> None:
        """Initialize async file system watcher."""
        self.logger = logging.getLogger(__name__)

        # Watch configuration
        self.paths_to_watch = paths_to_watch or []
        self.event_callback = event_callback
        self.max_workers = max_workers
        self.poll_interval = poll_interval

        # Async state management
        self.watching = False
        self.watch_task: asyncio.Task | None = None
        self.semaphore: asyncio.Semaphore | None = None

        # File state tracking
        self.file_states: dict[str, AsyncFileStats] = {}
        self.last_scan_time = time.time()

        # Event filtering and throttling
        self.excluded_paths = {'/proc', '/sys', '/tmp', '/dev'}
        self.excluded_extensions = {'.tmp', '.log', '.cache'}
        self.max_file_size = 100 * 1024 * 1024  # 100MB

        # Performance monitoring
        self.events_processed = 0
        self.scan_operations = 0
        self.start_time = time.time()

        self.logger.info(
            "Async file watcher initialized for %d paths",
            len(self.paths_to_watch)
        )

    async def start_watching(self) -> bool:
        """Start async file system monitoring."""
        if self.watching:
            self.logger.warning("Async watcher is already running")
            return False

        # Validate paths asynchronously
        valid_paths = await self._validate_watch_paths()
        if not valid_paths:
            self.logger.error("No valid watch paths found")
            return False

        self.paths_to_watch = valid_paths
        self.watching = True
        self.start_time = time.time()

        # Initialize async components
        await self._setup_async_components()

        # Start the async monitoring task
        self.watch_task = asyncio.create_task(self._async_watch_loop())

        self.logger.info(
            "Async file system monitoring started for %d paths",
            len(self.paths_to_watch)
        )
        return True

    async def stop_watching(self) -> None:
        """Stop async file system monitoring."""
        if not self.watching:
            return

        self.watching = False

        if self.watch_task and not self.watch_task.done():
            self.watch_task.cancel()
            try:
                await self.watch_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Async file system monitoring stopped")

    async def _setup_async_components(self) -> None:
        """Setup async components that require an event loop."""
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_workers)

    async def _validate_watch_paths(self) -> list[str]:
        """Validate watch paths asynchronously."""
        valid_paths = []

        for path in self.paths_to_watch:
            if isinstance(path, str):
                try:
                    if await aiofiles.os.path.exists(path):
                        valid_paths.append(path)
                    else:
                        self.logger.warning("Path does not exist: %s", path)
                except Exception as e:
                    self.logger.error("Error validating path %s: %s", path, e)
            else:
                self.logger.warning("Invalid path type: %s", type(path))

        return valid_paths

    async def _async_watch_loop(self) -> None:
        """Main async monitoring loop."""
        self.logger.info("Starting async file system monitoring loop")

        try:
            while self.watching:
                scan_start = time.time()

                # Perform async directory scan
                await self._scan_directories_async()

                scan_duration = time.time() - scan_start
                self.scan_operations += 1

                # Log performance metrics periodically
                if self.scan_operations % 100 == 0:
                    await self._log_performance_metrics()

                # Adaptive sleep based on scan duration
                sleep_time = max(
                    self.poll_interval - scan_duration,
                    0.1  # Minimum sleep
                )
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            self.logger.info("Async watch loop cancelled")
            raise
        except Exception as e:
            self.logger.error("Error in async watch loop: %s", e)
            raise

    async def _scan_directories_async(self) -> None:
        """Scan all watch directories asynchronously."""
        tasks = []

        for watch_path in self.paths_to_watch:
            if self.semaphore:
                async with self.semaphore:
                    task = asyncio.create_task(
                        self._scan_single_directory_async(watch_path)
                    )
                    tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _scan_single_directory_async(self, directory: str) -> None:
        """Scan a single directory asynchronously."""
        try:
            current_states: dict[str, AsyncFileStats] = {}

            # Use async generator for memory-efficient directory traversal
            async for file_path in self._walk_directory_async(directory):
                if not self.watching:
                    break

                if not await self._should_process_path_async(file_path):
                    continue

                # Get file stats asynchronously
                try:
                    stat_result = await aiofiles.os.stat(file_path)
                    file_stats = AsyncFileStats(
                        size=stat_result.st_size,
                        mtime=stat_result.st_mtime
                    )
                    current_states[file_path] = file_stats

                    # Check for changes
                    await self._check_file_changes_async(file_path, file_stats)

                except OSError as e:
                    # File might have been deleted during scan
                    self.logger.debug("Error accessing file %s: %s", file_path, e)
                    continue

            # Check for deleted files
            await self._check_deleted_files_async(directory, current_states)

            # Update file states for this directory
            directory_files = {
                path: stats for path, stats in current_states.items()
                if path.startswith(directory)
            }
            self.file_states.update(directory_files)

        except Exception as e:
            self.logger.error("Error scanning directory %s: %s", directory, e)

    async def _walk_directory_async(self, directory: str) -> AsyncIterator[str]:
        """Async generator for directory traversal."""
        try:
            # Use asyncio to make os.walk non-blocking
            def sync_walk() -> list[str]:
                result = []
                for root, dirs, files in os.walk(directory):
                    # Filter directories in-place
                    dirs[:] = [
                        d for d in dirs
                        if not any(
                            os.path.join(root, d).startswith(excluded)
                            for excluded in self.excluded_paths
                        )
                    ]

                    for file in files:
                        file_path = os.path.join(root, file)
                        result.append(file_path)
                return result

            # Run the sync operation in a thread pool
            loop = asyncio.get_event_loop()

            file_paths = await loop.run_in_executor(None, sync_walk)
            for file_path in file_paths:
                if not self.watching:
                    break
                yield file_path
                # Yield control periodically
                if hash(file_path) % 10 == 0:
                    await asyncio.sleep(0)

        except Exception as e:
            self.logger.error("Error walking directory %s: %s", directory, e)

    async def _should_process_path_async(self, file_path: str) -> bool:
        """Check if a path should be processed (async version)."""
        try:
            # Check excluded paths
            for excluded in self.excluded_paths:
                if file_path.startswith(excluded):
                    return False

            # Check excluded extensions
            if any(file_path.endswith(ext) for ext in self.excluded_extensions):
                return False

            # Check file size asynchronously
            try:
                if await aiofiles.os.path.isfile(file_path):
                    stat_result = await aiofiles.os.stat(file_path)
                    if stat_result.st_size > self.max_file_size:
                        return False
            except OSError:
                # File might not exist or be accessible
                return False

            return True

        except Exception:
            return False

    async def _check_file_changes_async(
        self, file_path: str, current_stats: AsyncFileStats
    ) -> None:
        """Check for file changes and emit events asynchronously."""
        try:
            previous_stats = self.file_states.get(file_path)

            if previous_stats is None:
                # New file
                await self._emit_event_async(
                    WatchEvent(
                        event_type=WatchEventType.FILE_CREATED,
                        file_path=file_path,
                        timestamp=time.time(),
                        size=current_stats.size
                    )
                )
            elif (
                previous_stats.mtime != current_stats.mtime or
                previous_stats.size != current_stats.size
            ):
                # Modified file
                await self._emit_event_async(
                    WatchEvent(
                        event_type=WatchEventType.FILE_MODIFIED,
                        file_path=file_path,
                        timestamp=time.time(),
                        size=current_stats.size
                    )
                )

        except Exception as e:
            self.logger.error("Error checking file changes for %s: %s", file_path, e)

    async def _check_deleted_files_async(
        self, directory: str, current_states: dict[str, AsyncFileStats]
    ) -> None:
        """Check for deleted files and emit events asynchronously."""
        try:
            # Find files that were tracked but no longer exist
            directory_files = {
                path: stats for path, stats in self.file_states.items()
                if path.startswith(directory)
            }

            deleted_files = set(directory_files.keys()) - set(current_states.keys())

            for deleted_path in deleted_files:
                await self._emit_event_async(
                    WatchEvent(
                        event_type=WatchEventType.FILE_DELETED,
                        file_path=deleted_path,
                        timestamp=time.time()
                    )
                )

        except Exception as e:
            self.logger.error("Error checking deleted files in %s: %s", directory, e)

    async def _emit_event_async(self, event: WatchEvent) -> None:
        """Emit a file system event asynchronously."""
        try:
            self.events_processed += 1

            # Log event at debug level
            self.logger.debug(
                "Async file event: %s - %s",
                event.event_type.value,
                event.file_path
            )

            # Call event callback asynchronously if it's an async function
            if self.event_callback:
                if asyncio.iscoroutinefunction(self.event_callback):
                    await self.event_callback(event)
                else:
                    # Run sync callback in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self.event_callback, event)

        except Exception as e:
            self.logger.error("Error emitting async event: %s", e)

    async def _log_performance_metrics(self) -> None:
        """Log performance metrics asynchronously."""
        uptime = time.time() - self.start_time
        events_per_second = self.events_processed / max(uptime, 1)
        scans_per_second = self.scan_operations / max(uptime, 1)

        self.logger.info(
            "Async watcher metrics: %d events (%.2f/s), %d scans (%.2f/s), uptime: %.1fs",
            self.events_processed,
            events_per_second,
            self.scan_operations,
            scans_per_second,
            uptime
        )

    async def add_watch_path_async(self, path: str) -> bool:
        """Add a new path to watch asynchronously."""
        try:
            if await aiofiles.os.path.exists(path):
                if path not in self.paths_to_watch:
                    self.paths_to_watch.append(path)
                    self.logger.info("Added async watch path: %s", path)
                    return True
                else:
                    self.logger.warning("Path already being watched: %s", path)
                    return False
            else:
                self.logger.error("Path does not exist: %s", path)
                return False
        except Exception as e:
            self.logger.error("Error adding watch path %s: %s", path, e)
            return False

    async def remove_watch_path_async(self, path: str) -> bool:
        """Remove a path from watching asynchronously."""
        try:
            if path in self.paths_to_watch:
                self.paths_to_watch.remove(path)

                # Clean up file states for this path
                files_to_remove = [
                    file_path for file_path in self.file_states.keys()
                    if file_path.startswith(path)
                ]
                for file_path in files_to_remove:
                    del self.file_states[file_path]

                self.logger.info("Removed async watch path: %s", path)
                return True
            else:
                self.logger.warning("Path not being watched: %s", path)
                return False
        except Exception as e:
            self.logger.error("Error removing watch path %s: %s", path, e)
            return False

    def set_async_event_callback(
        self, callback: Callable[[WatchEvent], None] | Callable[[WatchEvent], Any]
    ) -> None:
        """Set the async event callback function."""
        self.event_callback = callback
        self.logger.info("Async event callback set")

    async def get_statistics_async(self) -> dict[str, Any]:
        """Get watcher performance statistics asynchronously."""
        uptime = time.time() - self.start_time

        return {
            "watching": self.watching,
            "backend": "async_polling",
            "uptime_seconds": uptime,
            "events_processed": self.events_processed,
            "events_per_second": self.events_processed / max(uptime, 1),
            "scan_operations": self.scan_operations,
            "scans_per_second": self.scan_operations / max(uptime, 1),
            "paths_watched": len(self.paths_to_watch),
            "files_tracked": len(self.file_states),
            "max_workers": self.max_workers,
            "poll_interval": self.poll_interval,
        }

    async def __aenter__(self) -> "AsyncFileSystemWatcher":
        """Async context manager entry."""
        await self.start_watching()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop_watching()


# Async utility functions for file operations
async def async_file_exists(file_path: str) -> bool:
    """Check if file exists asynchronously."""
    try:
        return await aiofiles.os.path.exists(file_path)
    except Exception:
        return False


async def async_get_file_size(file_path: str) -> int:
    """Get file size asynchronously."""
    try:
        stat_result = await aiofiles.os.stat(file_path)
        return stat_result.st_size
    except Exception:
        return 0


async def async_read_file_chunk(file_path: str, chunk_size: int = 8192) -> AsyncIterator[bytes]:
    """Read file in chunks asynchronously."""
    try:
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(chunk_size):
                yield chunk
    except Exception as e:
        logging.error("Error reading file %s: %s", file_path, e)


async def async_calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate file hash asynchronously using secure crypto."""
    try:
        # Read file asynchronously and hash incrementally
        if algorithm.lower() == 'sha256':
            from cryptography.hazmat.primitives import hashes
            digest = hashes.Hash(hashes.SHA256())
        elif algorithm.lower() == 'sha512':
            from cryptography.hazmat.primitives import hashes
            digest = hashes.Hash(hashes.SHA512())
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        async for chunk in async_read_file_chunk(file_path):
            digest.update(chunk)

        return digest.finalize().hex()

    except Exception as e:
        logging.error("Error calculating hash for %s: %s", file_path, e)
        return ""
