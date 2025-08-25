#!/usr/bin/env python3
"""
File system watcher for real-time monitoring
Uses inotify on Linux for efficient file system event detection
"""

import logging
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

# Try to import inotify, fallback to polling if not available
try:
    import inotify.adapters
    import inotify.constants

    INOTIFY_AVAILABLE = True
except ImportError:
    INOTIFY_AVAILABLE = False


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
    old_path: Optional[str] = None  # For move events
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
    """Cross-platform file system watcher with real-time event detection."""

    def __init__(
        self,
        paths_to_watch: Optional[List[str]] = None,
        event_callback: Optional[Callable[[WatchEvent], None]] = None,
    ) -> None:
        """Initialize file system watcher.

        Args:
            paths_to_watch: List of paths to monitor
            event_callback: Callback function for events
        """
        # Core configuration
        self.logger = logging.getLogger(__name__)
        self.paths_to_watch = list(paths_to_watch) if paths_to_watch else ["/home"]
        self.event_callback = event_callback

        # Event filtering
        self.excluded_extensions: Set[str] = {".tmp", ".swp", ".log", ".cache"}
        self.excluded_paths: Set[str] = {"/proc", "/sys", "/dev", tempfile.gettempdir()}
        self.max_file_size: int = 100 * 1024 * 1024  # 100MB

        # State management
        self.watching = False
        self.watch_thread: Optional[threading.Thread] = None
        self.inotify_adapter: Optional["inotify.adapters.Inotify"] = None

        # Enhanced event throttling and debouncing
        self.event_queue: List[WatchEvent] = []
        self.last_event_time: Dict[str, float] = {}
        self.throttle_duration = 1.0  # seconds
        self.debounce_buffer: Dict[str, List[WatchEvent]] = {}
        self.debounce_timer: Optional[threading.Timer] = None
        self.debounce_delay = 0.5  # seconds

        # Performance monitoring
        self.events_processed = 0
        self.start_time = time.time()

        self._initialize_watcher()

    def _initialize_watcher(self):
        """Initialize the appropriate watcher backend."""
        if INOTIFY_AVAILABLE:
            self.logger.info("Using inotify for file system monitoring")
            self._use_inotify = True
        else:
            self.logger.warning("inotify not available, using polling fallback")
            self._use_inotify = False

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

        if self._use_inotify:
            self.watch_thread = threading.Thread(
                target=self._inotify_watch_loop, daemon=True, name="FileSystemWatcher"
            )
        else:
            self.watch_thread = threading.Thread(
                target=self._polling_watch_loop,
                daemon=True,
                name="FileSystemWatcher-Poll",
            )

        self.watch_thread.start()
        self.logger.info(
            "File system watcher started for %d paths", len(self.paths_to_watch)
        )

    def stop_watching(self):
        """Stop monitoring file system events."""
        if not self.watching:
            return

        self.watching = False

        if self.inotify_adapter:
            # inotify cleanup happens automatically
            pass

        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=5.0)

        self.logger.info("File system watcher stopped")

    def _inotify_watch_loop(self):
        """Main loop for inotify-based watching."""
        try:
            # inotify.adapters.InotifyTree expects single path, not list
            # We need to create multiple adapters or use Inotify with manual
            # add_watch
            self.inotify_adapter = inotify.adapters.Inotify()

            # Add watches for each path
            for watch_path in self.paths_to_watch:
                if os.path.exists(watch_path):
                    try:
                        self.inotify_adapter.add_watch(
                            watch_path,
                            mask=(
                                inotify.constants.IN_CREATE
                                | inotify.constants.IN_MODIFY
                                | inotify.constants.IN_DELETE
                                | inotify.constants.IN_MOVED_FROM
                                | inotify.constants.IN_MOVED_TO
                                | inotify.constants.IN_CLOSE_WRITE
                            ),
                        )
                        self.logger.info("Added inotify watch for: %s", watch_path)
                    except Exception as e:
                        self.logger.warning(
                            "Failed to add inotify watch for %s: %s", watch_path, e
                        )
                else:
                    self.logger.warning(
                        "Watch path does not exist, skipping: %s", watch_path
                    )

            for event in self.inotify_adapter.event_gen(yield_nones=False):
                if not self.watching:
                    break

                try:
                    self._process_inotify_event(event)
                except Exception as e:
                    self.logger.error("Error processing inotify event: %s", e)

        except Exception as e:
            self.logger.error("inotify watch loop failed: %s", e)
            # Fallback to polling
            self._polling_watch_loop()

    def _process_inotify_event(self, event):
        """Process a single inotify event."""
        (_, type_names, path, filename) = event

        if not filename:
            return

        full_path = os.path.join(path, filename)

        # Apply filters
        if not self._should_process_path(full_path):
            return

        # Determine event type
        if "IN_CREATE" in type_names:
            if "IN_ISDIR" in type_names:
                event_type = WatchEventType.DIRECTORY_CREATED
            else:
                event_type = WatchEventType.FILE_CREATED
        elif "IN_MODIFY" in type_names or "IN_CLOSE_WRITE" in type_names:
            event_type = WatchEventType.FILE_MODIFIED
        elif "IN_DELETE" in type_names:
            if "IN_ISDIR" in type_names:
                event_type = WatchEventType.DIRECTORY_DELETED
            else:
                event_type = WatchEventType.FILE_DELETED
        elif "IN_MOVED_FROM" in type_names or "IN_MOVED_TO" in type_names:
            event_type = WatchEventType.FILE_MOVED
        else:
            return  # Unhandled event type

        # Create watch event
        try:
            file_size = 0
            is_directory = "IN_ISDIR" in type_names

            if not is_directory and os.path.exists(full_path):
                try:
                    file_size = os.path.getsize(full_path)
                except (OSError, IOError):
                    file_size = 0

            watch_event = WatchEvent(
                event_type=event_type,
                file_path=full_path,
                timestamp=time.time(),
                size=file_size,
                is_directory=is_directory,
            )

            self._handle_event(watch_event)

        except Exception as e:
            self.logger.error("Error creating watch event for %s: %s", full_path, e)

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

                            except (OSError, IOError) as e:
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
                except (OSError, IOError):
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

            # Call event callback
            if self.event_callback:
                self.event_callback(event)

        except Exception as e:
            self.logger.error("Error in event callback: %s", e)

    def get_statistics(self) -> Dict[str, Any]:
        """Get watcher performance statistics."""
        uptime = time.time() - self.start_time
        return {
            "watching": self.watching,
            "backend": "inotify" if self._use_inotify else "polling",
            "uptime_seconds": uptime,
            "events_processed": self.events_processed,
            "events_per_second": self.events_processed / max(uptime, 1),
            "paths_watched": len(self.paths_to_watch),
            "throttle_duration": self.throttle_duration,
        }

    def add_watch_path(self, path: str):
        """Add a new path to watch."""
        if path not in self.paths_to_watch:
            self.paths_to_watch.append(path)
            self.logger.info("Added watch path: %s", path)

    def remove_watch_path(self, path: str):
        """Remove a path from watching."""
        if path in self.paths_to_watch:
            self.paths_to_watch.remove(path)
            self.logger.info("Removed watch path: %s", path)

    def set_event_callback(self, callback: Callable[[WatchEvent], None]):
        """Set the event callback function."""
        self.event_callback = callback
