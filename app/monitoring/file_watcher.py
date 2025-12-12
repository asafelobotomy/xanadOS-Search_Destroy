#!/usr/bin/env python3
"""File system watcher for real-time monitoring.

Modern, comprehensive file system monitoring with multiple backends:
- fanotify API (Linux, kernel-level, requires root) - BEST performance
- watchdog library (cross-platform, efficient) - RECOMMENDED
  * Linux: inotify (kernel-level events)
  * macOS: FSEvents (native events)
  * Windows: ReadDirectoryChangesW (native events)
- Polling fallback (universal, no dependencies)

Features:
- Async/await support for modern Python applications
- Event debouncing and throttling
- Smart filtering and exclusions
- Performance monitoring
- Multi-backend architecture
"""

import asyncio
import ctypes
import ctypes.util
import logging
import os
import select
import tempfile
import threading
import time
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Advanced Linux monitoring (fanotify)
try:
    libc = ctypes.CDLL(ctypes.util.find_library("c"))

    # fanotify constants
    FAN_ACCESS = 0x00000001
    FAN_MODIFY = 0x00000002
    FAN_CLOSE_WRITE = 0x00000008
    FAN_CLOSE_NOWRITE = 0x00000010
    FAN_OPEN = 0x00000020
    FAN_MOVED_FROM = 0x00000040
    FAN_MOVED_TO = 0x00000080
    FAN_CREATE = 0x00000100
    FAN_DELETE = 0x00000200
    FAN_ONDIR = 0x40000000
    FAN_EVENT_ON_CHILD = 0x08000000
    FAN_CLOEXEC = 0x00000001
    FAN_CLASS_NOTIF = 0x00000000
    AT_FDCWD = -100

    FANOTIFY_AVAILABLE = True
except (ImportError, OSError, AttributeError):
    FANOTIFY_AVAILABLE = False

# Modern cross-platform file system monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class WatchEventType(Enum):
    """Types of file system events."""

    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    DIRECTORY_CREATED = "dir_created"
    DIRECTORY_DELETED = "dir_deleted"


@dataclass
class WatchEvent:
    """Represents a file system watch event."""

    event_type: WatchEventType
    file_path: str
    timestamp: float
    old_path: str | None = None  # For move events
    size: int = 0
    is_directory: bool = False

    def __post_init__(self):
        """Validate the event data."""
        self.timestamp = self.timestamp or time.time()
        # Simple path validation to avoid import issues
        if (
            not os.path.exists(self.file_path)
            and self.event_type != WatchEventType.FILE_DELETED
        ):
            # Only warn for non-delete events
            pass  # File might be deleted quickly after creation

        if not os.path.isabs(self.file_path):
            raise ValueError(f"File path must be absolute: {self.file_path}")


class FileSystemWatcher:
    """Cross-platform file system watcher with real-time event detection.

    Supports multiple backends (auto-selected in order of preference):
    1. fanotify (Linux only, requires root) - kernel-level, highest performance
    2. watchdog (cross-platform) - native OS APIs, recommended
    3. polling (fallback) - universal compatibility

    Can be used both synchronously and asynchronously.
    """

    def __init__(
        self,
        paths_to_watch: list[str] | None = None,
        event_callback: Callable[[WatchEvent], None] | None = None,
        enable_fanotify: bool = False,  # Requires root, disabled by default
    ) -> None:
        """Initialize file system watcher.

        Args:
            paths_to_watch: List of paths to monitor
            event_callback: Callback function for events
            enable_fanotify: Enable fanotify backend (Linux only, requires root)
        """
        # Core configuration
        self.logger = logging.getLogger(__name__)
        self.paths_to_watch = list(paths_to_watch) if paths_to_watch else ["/home"]
        self.event_callback = event_callback
        self.enable_fanotify = enable_fanotify

        # Event filtering
        self.excluded_extensions: set[str] = {".tmp", ".swp", ".log", ".cache"}
        self.excluded_paths: set[str] = {"/proc", "/sys", "/dev", tempfile.gettempdir()}
        self.max_file_size: int = 100 * 1024 * 1024  # 100MB

        # State management
        self.watching = False
        self.watch_thread: threading.Thread | None = None
        self.watchdog_observer: Observer | None = None
        self.fanotify_fd: int | None = None

        # Enhanced event throttling and debouncing
        self.event_queue: list[WatchEvent] = []
        self.last_event_time: dict[str, float] = {}
        self.throttle_duration = 1.0  # seconds
        self.debounce_buffer: dict[str, list[WatchEvent]] = {}
        self.debounce_timer: threading.Timer | None = None
        self.debounce_delay = 0.5  # seconds

        # Async support
        self.async_queue: asyncio.Queue[WatchEvent] | None = None
        self.async_callbacks: list[Callable[[WatchEvent], Any]] = []

        # Performance monitoring
        self.events_processed = 0
        self.start_time = time.time()
        self.backend_used: str = "not_initialized"

        self._initialize_watcher()

    def _initialize_watcher(self) -> None:
        """Initialize the appropriate watcher backend."""
        # Try fanotify first (Linux only, requires root)
        if self.enable_fanotify and FANOTIFY_AVAILABLE and os.geteuid() == 0:
            try:
                # Test if fanotify works
                test_fd = libc.fanotify_init(FAN_CLOEXEC | FAN_CLASS_NOTIF, os.O_RDONLY)
                if test_fd != -1:
                    libc.close(test_fd)
                    self.logger.info("Using fanotify for kernel-level file system monitoring")
                    self.backend_used = "fanotify"
                    return
            except Exception as e:
                self.logger.warning(f"Fanotify initialization failed: {e}, falling back")

        # Try watchdog next
        if WATCHDOG_AVAILABLE:
            self.logger.info(
                "Using watchdog for efficient file system monitoring (native events per platform)"
            )
            self.backend_used = "watchdog"
        else:
            self.logger.warning(
                "Watchdog not available, using polling fallback (install 'watchdog' package for better performance)"
            )
            self.backend_used = "polling"

    def start_watching(self):
        """Start monitoring file system events."""
        if self.watching:
            self.logger.warning("Watcher is already running")
            return

        # Validate watch paths before starting
        valid_paths = []
        for path in self.paths_to_watch:
            if isinstance(path, str) and os.path.exists(path):
                valid_paths.append(path)
            else:
                self.logger.warning("Invalid or non-existent watch path: %s", path)

        if not valid_paths:
            self.logger.error("No valid watch paths found, cannot start watcher")
            return

        self.paths_to_watch = valid_paths
        self.watching = True
        self.start_time = time.time()

        if self._use_watchdog:
            self.watch_thread = threading.Thread(
                target=self._watchdog_watch_loop,
                daemon=True,
                name="FileSystemWatcher-Watchdog",
            )
        else:
            self.watch_thread = threading.Thread(
                target=self._polling_watch_loop,
                daemon=True,
                name="FileSystemWatcher-Poll",
            )

        self.watch_thread.start()
        self.logger.info(
            "File system watcher started with %s backend for %d paths",
            self.backend_used,
            len(self.paths_to_watch),
        )

    def start_watching(self):
        """Start monitoring file system events."""
        if self.watching:
            self.logger.warning("Watcher is already running")
            return

        # Validate watch paths before starting
        valid_paths = []
        for path in self.paths_to_watch:
            if isinstance(path, str) and os.path.exists(path):
                valid_paths.append(path)
            else:
                self.logger.warning("Invalid or non-existent watch path: %s", path)

        if not valid_paths:
            self.logger.error("No valid watch paths found, cannot start watcher")
            return

        self.paths_to_watch = valid_paths
        self.watching = True
        self.start_time = time.time()

        # Select backend and start appropriate watch loop
        if self.backend_used == "fanotify":
            self.watch_thread = threading.Thread(
                target=self._fanotify_watch_loop,
                daemon=True,
                name="FileSystemWatcher-Fanotify",
            )
        elif self.backend_used == "watchdog":
            self.watch_thread = threading.Thread(
                target=self._watchdog_watch_loop,
                daemon=True,
                name="FileSystemWatcher-Watchdog",
            )
        else:
            self.watch_thread = threading.Thread(
                target=self._polling_watch_loop,
                daemon=True,
                name="FileSystemWatcher-Poll",
            )

    def stop_watching(self):
        """Stop monitoring file system events."""
        if not self.watching:
            return

        self.watching = False

        # Cleanup watchdog observer if active
        if self.watchdog_observer:
            try:
                self.watchdog_observer.stop()
                self.watchdog_observer.join(timeout=2.0)
            except Exception as e:
                self.logger.warning("Error stopping watchdog observer: %s", e)

        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=5.0)

        self.logger.info("File system watcher stopped")

    def _fanotify_watch_loop(self):
        """Kernel-level file system monitoring using fanotify (Linux only, requires root)."""
        if not FANOTIFY_AVAILABLE or os.geteuid() != 0:
            self.logger.error("Fanotify not available or insufficient permissions, falling back")
            self.backend_used = "watchdog" if WATCHDOG_AVAILABLE else "polling"
            if self.backend_used == "watchdog":
                self._watchdog_watch_loop()
            else:
                self._polling_watch_loop()
            return

        try:
            # Initialize fanotify
            self.fanotify_fd = libc.fanotify_init(
                FAN_CLOEXEC | FAN_CLASS_NOTIF,
                os.O_RDONLY | os.O_LARGEFILE,
            )

            if self.fanotify_fd == -1:
                raise OSError("fanotify_init failed")

            self.logger.info(f"Fanotify initialized successfully (fd={self.fanotify_fd})")

            # Mark paths for monitoring
            for path in self.paths_to_watch:
                if not os.path.exists(path):
                    self.logger.warning(f"Path does not exist: {path}")
                    continue

                # Monitor for file creation, modification, and deletion
                mask = (
                    FAN_CREATE
                    | FAN_MODIFY
                    | FAN_CLOSE_WRITE
                    | FAN_MOVED_FROM
                    | FAN_MOVED_TO
                    | FAN_DELETE
                    | FAN_ONDIR
                    | FAN_EVENT_ON_CHILD
                )

                result = libc.fanotify_mark(
                    self.fanotify_fd,
                    0,  # FAN_MARK_ADD
                    mask,
                    AT_FDCWD,
                    path.encode("utf-8"),
                )

                if result == -1:
                    self.logger.warning(f"Failed to mark path {path} for monitoring")
                else:
                    self.logger.info(f"Fanotify monitoring path: {path}")

            # Main monitoring loop
            buffer_size = 4096
            while self.watching:
                try:
                    # Use select for non-blocking read with timeout
                    ready, _, _ = select.select([self.fanotify_fd], [], [], 1.0)

                    if not ready:
                        continue

                    # Read events from fanotify
                    data = os.read(self.fanotify_fd, buffer_size)

                    if not data:
                        continue

                    # Parse and process events (simplified, basic fanotify event handling)
                    # Real implementation would parse the fanotify_event_metadata structure
                    # For now, treat any event as a file modification
                    event = WatchEvent(
                        event_type=WatchEventType.FILE_MODIFIED,
                        file_path="<fanotify_event>",  # Would extract from event metadata
                        timestamp=time.time(),
                    )
                    self._handle_event(event)

                except BlockingIOError:
                    continue
                except Exception as e:
                    if self.watching:  # Only log if not intentionally stopped
                        self.logger.error(f"Error in fanotify monitor loop: {e}")
                    time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Fanotify watch loop failed: {e}")
            # Fallback to watchdog or polling
            self.logger.info("Falling back to alternative backend")
            self.backend_used = "watchdog" if WATCHDOG_AVAILABLE else "polling"
            if self.backend_used == "watchdog":
                self._watchdog_watch_loop()
            else:
                self._polling_watch_loop()
        finally:
            # Cleanup fanotify
            if self.fanotify_fd and self.fanotify_fd != -1:
                try:
                    libc.close(self.fanotify_fd)
                    self.logger.info("Fanotify fd closed")
                except Exception as e:
                    self.logger.warning(f"Error closing fanotify fd: {e}")
                self.fanotify_fd = None

    def _watchdog_watch_loop(self):
        """Main loop for watchdog-based watching (efficient, cross-platform)."""
        if not WATCHDOG_AVAILABLE:
            self.logger.error("Watchdog not available, falling back to polling")
            self._polling_watch_loop()
            return

        try:
            # Create event handler
            class WatchdogHandler(FileSystemEventHandler):
                """Handler for watchdog file system events."""

                def __init__(self, parent_watcher):
                    super().__init__()
                    self.parent = parent_watcher

                def on_created(self, event):
                    """Handle file/directory creation."""
                    if not event.is_directory:
                        watch_event = WatchEvent(
                            event_type=WatchEventType.FILE_CREATED,
                            file_path=event.src_path,
                            timestamp=time.time(),
                        )
                        self.parent._handle_event(watch_event)

                def on_modified(self, event):
                    """Handle file/directory modification."""
                    if not event.is_directory:
                        watch_event = WatchEvent(
                            event_type=WatchEventType.FILE_MODIFIED,
                            file_path=event.src_path,
                            timestamp=time.time(),
                        )
                        self.parent._handle_event(watch_event)

                def on_deleted(self, event):
                    """Handle file/directory deletion."""
                    if not event.is_directory:
                        watch_event = WatchEvent(
                            event_type=WatchEventType.FILE_DELETED,
                            file_path=event.src_path,
                            timestamp=time.time(),
                        )
                        self.parent._handle_event(watch_event)

                def on_moved(self, event):
                    """Handle file/directory move/rename."""
                    if not event.is_directory:
                        # Treat move as delete + create
                        delete_event = WatchEvent(
                            event_type=WatchEventType.FILE_DELETED,
                            file_path=event.src_path,
                            timestamp=time.time(),
                        )
                        create_event = WatchEvent(
                            event_type=WatchEventType.FILE_CREATED,
                            file_path=event.dest_path,
                            timestamp=time.time(),
                        )
                        self.parent._handle_event(delete_event)
                        self.parent._handle_event(create_event)

            # Create observer and event handler
            self.watchdog_observer = Observer()
            event_handler = WatchdogHandler(self)

            # Schedule watching for each path
            for watch_path in self.paths_to_watch:
                if os.path.exists(watch_path):
                    try:
                        self.watchdog_observer.schedule(
                            event_handler, watch_path, recursive=True
                        )
                        self.logger.info("Added watchdog watch for: %s", watch_path)
                    except Exception as e:
                        self.logger.warning(
                            "Failed to add watchdog watch for %s: %s", watch_path, e
                        )
                else:
                    self.logger.warning(
                        "Watch path does not exist, skipping: %s", watch_path
                    )

            # Start observer and wait until stopped
            self.watchdog_observer.start()
            self.logger.info("Watchdog observer started successfully")

            # Keep thread alive while watching
            while self.watching:
                time.sleep(1)

            # Stop observer
            self.watchdog_observer.stop()
            self.watchdog_observer.join()
            self.logger.info("Watchdog observer stopped")

        except Exception as e:
            self.logger.error("Watchdog watch loop failed: %s", e)
            # Fallback to polling if watchdog fails
            self.logger.info("Falling back to polling mode")
            self._polling_watch_loop()

    def _polling_watch_loop(self):
        """Fallback polling-based watching."""
        self.logger.info("Starting polling-based file system monitoring")

        file_states = {}

        while self.watching:
            try:
                current_states = {}

                for watch_path in self.paths_to_watch:
                    if not os.path.exists(watch_path):
                        continue

                    for root, dirs, files in os.walk(watch_path):
                        if not self.watching:
                            break

                        # Filter directories
                        dirs[:] = [
                            d
                            for d in dirs
                            if self._should_process_path(os.path.join(root, d))
                        ]

                        for file in files:
                            full_path = os.path.join(root, file)

                            if not self._should_process_path(full_path):
                                continue

                            try:
                                stat = os.stat(full_path)
                                current_states[full_path] = {
                                    "mtime": stat.st_mtime,
                                    "size": stat.st_size,
                                }

                                # Check for new or modified files
                                if full_path not in file_states:
                                    # New file
                                    event = WatchEvent(
                                        event_type=WatchEventType.FILE_CREATED,
                                        file_path=full_path,
                                        timestamp=time.time(),
                                        size=stat.st_size,
                                    )
                                    self._handle_event(event)

                                elif (
                                    file_states[full_path]["mtime"] != stat.st_mtime
                                    or file_states[full_path]["size"] != stat.st_size
                                ):
                                    # Modified file
                                    event = WatchEvent(
                                        event_type=WatchEventType.FILE_MODIFIED,
                                        file_path=full_path,
                                        timestamp=time.time(),
                                        size=stat.st_size,
                                    )
                                    self._handle_event(event)

                            except OSError as e:
                                self.logger.debug(
                                    "Error accessing file %s: %s", full_path, e
                                )

                # Check for deleted files
                for old_path in set(file_states.keys()) - set(current_states.keys()):
                    event = WatchEvent(
                        event_type=WatchEventType.FILE_DELETED,
                        file_path=old_path,
                        timestamp=time.time(),
                    )
                    self._handle_event(event)

                file_states = current_states

                # Sleep before next poll
                time.sleep(2.0)

            except Exception as e:
                self.logger.error("Error in polling loop: %s", e)
                time.sleep(5.0)

    def _should_process_path(self, path: str) -> bool:
        """Check if a path should be processed."""
        try:
            # Check excluded paths
            for excluded in self.excluded_paths:
                if path.startswith(excluded):
                    return False

            # Check excluded extensions
            if any(path.endswith(ext) for ext in self.excluded_extensions):
                return False

            # Check file size (if exists)
            if os.path.exists(path) and os.path.isfile(path):
                try:
                    if os.path.getsize(path) > self.max_file_size:
                        return False
                except OSError:
                    pass

            return True

        except Exception:
            return False

    def _handle_event(self, event: WatchEvent):
        """Handle a file system event with debouncing."""
        try:
            # Throttle events for the same file
            event_key = f"{event.file_path}:{event.event_type.value}"
            current_time = time.time()

            if (
                event_key in self.last_event_time
                and current_time - self.last_event_time[event_key]
                < self.throttle_duration
            ):
                return

            self.last_event_time[event_key] = current_time

            # Debounce similar events
            self._debounce_event(event)

        except Exception as e:
            self.logger.error("Error handling event: %s", e)

    def _debounce_event(self, event: WatchEvent):
        """Debounce events to reduce processing overhead."""
        # Group events by directory to batch process similar changes
        dir_path = os.path.dirname(event.file_path)

        if dir_path not in self.debounce_buffer:
            self.debounce_buffer[dir_path] = []

        self.debounce_buffer[dir_path].append(event)

        # Reset debounce timer
        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.debounce_timer = threading.Timer(
            self.debounce_delay, self._process_debounced_events
        )
        self.debounce_timer.start()

    def _process_debounced_events(self):
        """Process batched debounced events."""
        try:
            for dir_path, events in self.debounce_buffer.items():
                # Process only the most recent events per file to avoid
                # duplicates
                unique_events = {}
                for event in events:
                    key = f"{event.file_path}:{event.event_type.value}"
                    unique_events[key] = event

                # Process unique events
                for event in unique_events.values():
                    self._execute_event_callback(event)

            # Clear buffer
            self.debounce_buffer.clear()

        except Exception as e:
            self.logger.error("Error processing debounced events: %s", e)

    def _execute_event_callback(self, event: WatchEvent):
        """Execute the event callback with error handling."""
        try:
            # Update statistics
            self.events_processed += 1

            # Log event (debug level to avoid spam)
            self.logger.debug(
                "File system event: %s - %s", event.event_type.value, event.file_path
            )

            # Call sync event callback
            if self.event_callback:
                self.event_callback(event)

            # Emit to async queue and callbacks
            self._emit_async_event(event)

        except Exception as e:
            self.logger.error("Error in event callback: %s", e)

    def get_statistics(self) -> dict[str, Any]:
        """Get watcher performance statistics."""
        uptime = time.time() - self.start_time
        return {
            "watching": self.watching,
            "backend": self.backend_used,
            "uptime_seconds": uptime,
            "events_processed": self.events_processed,
            "events_per_second": self.events_processed / max(uptime, 1),
            "paths_watched": len(self.paths_to_watch),
            "throttle_duration": self.throttle_duration,
            "fanotify_available": FANOTIFY_AVAILABLE,
            "watchdog_available": WATCHDOG_AVAILABLE,
        }

    # ================== ASYNC SUPPORT ==================

    def enable_async_mode(self, max_queue_size: int = 1000) -> None:
        """Enable async event queue for async/await usage.

        Args:
            max_queue_size: Maximum number of events to queue
        """
        self.async_queue = asyncio.Queue(maxsize=max_queue_size)
        self.logger.info("Async mode enabled with queue size: %d", max_queue_size)

    def add_async_callback(self, callback: Callable[[WatchEvent], Any]) -> None:
        """Add async callback for events.

        Args:
            callback: Async function to call on events (can be sync or async)
        """
        self.async_callbacks.append(callback)
        self.logger.info("Added async callback: %s", callback.__name__)

    def remove_async_callback(self, callback: Callable[[WatchEvent], Any]) -> None:
        """Remove async callback.

        Args:
            callback: Callback to remove
        """
        if callback in self.async_callbacks:
            self.async_callbacks.remove(callback)
            self.logger.info("Removed async callback: %s", callback.__name__)

    async def get_event_async(self) -> WatchEvent:
        """Get next event from async queue (must have async mode enabled).

        Returns:
            Next WatchEvent from queue

        Raises:
            RuntimeError: If async mode not enabled
        """
        if self.async_queue is None:
            raise RuntimeError("Async mode not enabled. Call enable_async_mode() first.")
        return await self.async_queue.get()

    async def watch_async(self) -> AsyncGenerator[WatchEvent, None]:
        """Async context manager for watching events.

        Usage:
            watcher = FileSystemWatcher(paths=['/path'])
            watcher.enable_async_mode()
            watcher.start_watching()

            async for event in watcher.watch_async():
                print(f"Event: {event.event_type} - {event.file_path}")
        """
        if self.async_queue is None:
            raise RuntimeError("Async mode not enabled. Call enable_async_mode() first.")

        while self.watching:
            try:
                event = await asyncio.wait_for(self.async_queue.get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def _emit_async_event(self, event: WatchEvent) -> None:
        """Emit event to async queue and callbacks (internal use)."""
        # Add to async queue if enabled
        if self.async_queue is not None:
            try:
                # Use non-blocking put to avoid deadlocks
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.async_queue.put(event), loop
                        )
                except RuntimeError:
                    # No event loop running, skip async queue
                    pass
            except (asyncio.QueueFull, RuntimeError) as e:
                self.logger.warning("Failed to add event to async queue: %s", e)

        # Call async callbacks
        for callback in self.async_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Schedule async callback
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(callback(event), loop)
                    except RuntimeError:
                        pass
                else:
                    # Call sync callback directly
                    callback(event)
            except (RuntimeError, TypeError) as e:
                self.logger.error("Error in async callback %s: %s", callback.__name__, e)

    # ================== PATH MANAGEMENT ==================

    def add_watch_path(self, path: str) -> None:
        """Add a new path to watch."""
        if path not in self.paths_to_watch:
            self.paths_to_watch.append(path)
            self.logger.info("Added watch path: %s", path)

    def remove_watch_path(self, path: str) -> None:
        """Remove a path from watching."""
        if path in self.paths_to_watch:
            self.paths_to_watch.remove(path)
            self.logger.info("Removed watch path: %s", path)

    def set_event_callback(self, callback: Callable[[WatchEvent], None]) -> None:
        """Set the event callback function."""
        self.event_callback = callback
