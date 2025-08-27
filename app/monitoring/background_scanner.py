#!/usr/bin/env python3
"""
Background scanner for continuous monitoring
Performs scheduled scans and processes file system events
"""

import glob
import logging
import tempfile
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import schedule  # type: ignore

    SCHEDULE_AVAILABLE = True
except ImportError:  # pragma: no cover - env dependent
    # Provide a minimal no-op scheduler so the module can load without the dependency
    SCHEDULE_AVAILABLE = False

    class _NoOpJob:
        def __init__(self):
            self.interval = None

        # Chainable API stubs
        def at(self, _time_str: str):
            return self

        def hours(self):
            return self

        def hour(self):
            return self

        def day(self):
            return self

        def do(self, _func, *_, **__):  # noqa: D401 - mimic schedule API
            return self

    class _NoOpScheduler:
        def every(self, *_args, **_kwargs):  # noqa: D401 - mimic schedule API
            return _NoOpJob()

        def run_pending(self):
            return None

    schedule = _NoOpScheduler()  # type: ignore

try:
    from app.core.clamav_wrapper import ClamAVWrapper
except ImportError:
    # Fallback for development/testing
    class ClamAVWrapper:  # type: ignore[no-redef]
        """Lightweight mock for ClamAVWrapper used in tests/dev when import fails."""

        def __init__(self):
            self.available = False

        def scan_file(self, _path):
            class ScanResult(Enum):
                """Mock scan result categories used by the fallback scanner."""

                CLEAN = "clean"
                INFECTED = "infected"
                ERROR = "error"

            @dataclass
            class Result:
                """Mock scan result object returned by the fallback scanner."""

                result: ScanResult = ScanResult.CLEAN
                threat_name: str = None
                threat_type: str = None
                file_size: int = 0
                error_message: str = None

            return Result()


from .file_watcher import WatchEvent, WatchEventType


class ScanPriority(Enum):
    """Priority levels for scan tasks."""

    IMMEDIATE = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class ScanTask:
    """Represents a background scan task."""

    file_path: str
    priority: ScanPriority
    timestamp: float
    event_type: Optional[WatchEventType] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class BackgroundScanner:
    """Background scanner that processes file system events and performs scheduled scans."""

    def __init__(self, file_scanner: Optional[ClamAVWrapper] = None):
        """Initialize background scanner.

        Args:
            file_scanner: ClamAV wrapper instance to use
        """
        self.logger = logging.getLogger(__name__)
        self.file_scanner = file_scanner or ClamAVWrapper()

        # Task management
        self.scan_queue: Queue[ScanTask] = Queue()
        self.active_scans: Set[str] = set()
        self.scan_results: Dict[str, Any] = {}

        # Threading
        self.running = False
        self.worker_threads: List[threading.Thread] = []
        self.num_workers = 2

        # Scheduling
        self.scheduler = schedule
        if not SCHEDULE_AVAILABLE:
            self.logger.warning(
                "Python 'schedule' package not installed; background scan schedules disabled. "
                "Install with: pip install --user schedule"
            )
        self.scheduler_thread: Optional[threading.Thread] = None

        # Event callbacks
        self.result_callback: Optional[Callable[[str, Any], None]] = None
        self.threat_callback: Optional[Callable[[str, str], None]] = None

        # Performance monitoring
        self.scans_completed = 0
        self.threats_detected = 0
        self.start_time = time.time()

        # Configuration
        self.scan_timeout = 30.0  # seconds
        self.max_concurrent_scans = 3
        self.immediate_scan_extensions: Set[str] = {
            ".exe",
            ".dll",
            ".bat",
            ".sh",
            ".py",
            ".jar",
        }

        self._setup_scheduled_tasks()

    # --- Logger helper methods for consistent callsites (used across modules) ---
    def loginfo(self, message: str):  # noqa: D401 - thin wrapper
        """Info-level log wrapper."""
        self.logger.info("%s", message)

    def logdebug(self, message: str):  # noqa: D401 - thin wrapper
        """Debug-level log wrapper."""
        self.logger.debug("%s", message)

    def logwarning(self, message: str):  # noqa: D401 - thin wrapper
        """Warning-level log wrapper."""
        self.logger.warning("%s", message)

    def logerror(self, message: str):  # noqa: D401 - thin wrapper
        """Error-level log wrapper."""
        self.logger.error("%s", message)

    def start(self):
        """Start the background scanner."""
        if self.running:
            self.logger.warning("Background scanner already running")
            return

        self.running = True
        self.start_time = time.time()

        # Start worker threads
        for i in range(self.num_workers):
            thread = threading.Thread(
                target=self._worker_loop, daemon=True, name=f"BackgroundScanner-{i}"
            )
            thread.start()
            self.worker_threads.append(thread)

        # Start scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True, name="BackgroundScanner-Scheduler"
        )
        self.scheduler_thread.start()

        self.loginfo(
            "Background scanner started with %d workers".replace(
                "%s", "{self.num_workers}"
            ).replace("%d", "{self.num_workers}")
        )

    def stop(self):
        """Stop the background scanner."""
        if not self.running:
            return

        self.running = False

        # Stop scheduler
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)

        # Stop workers
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)

        self.worker_threads.clear()
        self.logger.info("Background scanner stopped")

    def handle_file_event(self, event: WatchEvent):
        """
        Handle a file system event by scheduling appropriate scans.

        Args:
            event: File system event to process
        """
        try:
            # Skip if file doesn't exist or is a directory
            if event.is_directory or not Path(event.file_path).exists():
                return

            # Determine scan priority based on event type and file
            priority = self._determine_scan_priority(event)

            # Create scan task
            task = ScanTask(
                file_path=event.file_path,
                priority=priority,
                timestamp=event.timestamp,
                event_type=event.event_type,
            )

            # Add to queue if not already scanning
            if event.file_path not in self.active_scans:
                self.scan_queue.put(task)
                self.logger.debug(
                    "Queued scan for %s (priority: %s)", event.file_path, priority.name
                )

        except Exception:
            self.logerror(
                "Error handling file event for %s: %s".replace(
                    "%s", "{event.file_path, e}"
                ).replace("%d", "{event.file_path, e}")
            )

    def schedule_scan(
        self, file_path: str, priority: ScanPriority = ScanPriority.NORMAL
    ):
        """
        Schedule a manual scan of a file.

        Args:
            file_path: Path to file to scan
            priority: Scan priority
        """
        task = ScanTask(file_path=file_path, priority=priority, timestamp=time.time())

        self.scan_queue.put(task)
        self.loginfo(
            "Scheduled manual scan for %s".replace("%s", "{file_path}").replace(
                "%d", "{file_path}"
            )
        )

    def _determine_scan_priority(self, event: WatchEvent) -> ScanPriority:
        """Determine scan priority based on file event."""
        file_path = Path(event.file_path)

        # Immediate priority for suspicious files
        if file_path.suffix.lower() in self.immediate_scan_extensions:
            return ScanPriority.IMMEDIATE

        # High priority for new files
        if event.event_type == WatchEventType.FILE_CREATED:
            return ScanPriority.HIGH

        # Normal priority for modified files
        if event.event_type == WatchEventType.FILE_MODIFIED:
            return ScanPriority.NORMAL

        return ScanPriority.LOW

    def _worker_loop(self):
        """Main worker loop for processing scan tasks."""
        while self.running:
            try:
                # Get task from queue with timeout
                try:
                    task = self.scan_queue.get(timeout=1.0)
                except Empty:
                    continue

                # Check if we're at max concurrent scans
                if len(self.active_scans) >= self.max_concurrent_scans:
                    # Re-queue task and wait
                    self.scan_queue.put(task)
                    time.sleep(0.5)
                    continue

                # Process the task
                self._process_scan_task(task)

            except Exception:
                self.logerror(
                    "Error in worker loop: %s".replace("%s", "{e}").replace("%d", "{e}")
                )
                time.sleep(1.0)

    def _process_scan_task(self, task: ScanTask):
        """Process a single scan task."""
        try:
            # Add to active scans
            self.active_scans.add(task.file_path)

            start_time = time.time()
            self.logdebug(
                "Starting scan of %s".replace("%s", "{task.file_path}").replace(
                    "%d", "{task.file_path}"
                )
            )

            # Perform the scan
            scan_result = self.file_scanner.scan_file(task.file_path)

            scan_time = time.time() - start_time

            # Update statistics
            self.scans_completed += 1
            if scan_result.result.value == "infected":
                self.threats_detected += 1

            # Store result
            self.scan_results[task.file_path] = {
                "result": scan_result.result.value,
                "threat_name": scan_result.threat_name,
                "threat_type": scan_result.threat_type,
                "scan_time": scan_time,
                "timestamp": time.time(),
                "priority": task.priority.name,
                "event_type": task.event_type.value if task.event_type else None,
                "file_size": scan_result.file_size,
                "error_message": scan_result.error_message,
            }

            # Call callbacks
            if self.result_callback:
                try:
                    self.result_callback(
                        task.file_path, self.scan_results[task.file_path]
                    )
                except Exception:
                    self.logerror(
                        "Error in result callback: %s".replace("%s", "{e}").replace(
                            "%d", "{e}"
                        )
                    )

            if scan_result.result.value == "infected" and self.threat_callback:
                try:
                    self.threat_callback(
                        task.file_path, scan_result.threat_name or "Unknown"
                    )
                except Exception:
                    self.logerror(
                        "Error in threat callback: %s".replace("%s", "{e}").replace(
                            "%d", "{e}"
                        )
                    )

            self.logger.info(
                "Scan completed: %s - %s (%s)",
                task.file_path,
                scan_result.result.value,
                scan_result.threat_name if scan_result.threat_name else "Clean",
            )

        except Exception:
            self.logerror(
                "Error scanning %s: %s".replace("%s", "{task.file_path, e}").replace(
                    "%d", "{task.file_path, e}"
                )
            )

            # Retry if under retry limit
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.timestamp = time.time() + (
                    task.retry_count * 60
                )  # Exponential backoff
                self.scan_queue.put(task)
                self.logger.info(
                    "Retrying scan of %s (attempt %d/%d)",
                    task.file_path,
                    task.retry_count,
                    task.max_retries,
                )

        finally:
            # Remove from active scans
            self.active_scans.discard(task.file_path)

    def _setup_scheduled_tasks(self):
        """Setup scheduled background tasks."""
        # Schedule daily full system scan at 2 AM
        self.scheduler.every().day.at("02:00").do(self._schedule_full_scan)

        # Schedule hourly quick scan of common directories
        self.scheduler.every().hour.do(self._schedule_quick_scan)

        # Schedule cleanup of old results every 6 hours
        self.scheduler.every(6).hours.do(self._cleanup_old_results)

    def _scheduler_loop(self):
        """Run scheduled tasks."""
        while self.running:
            try:
                self.scheduler.run_pending()
                time.sleep(60)  # Check every minute
            except Exception:
                self.logerror(
                    "Error in scheduler loop: %s".replace("%s", "{e}").replace(
                        "%d", "{e}"
                    )
                )
                time.sleep(60)

    def _schedule_full_scan(self):
        """Schedule a full system scan."""
        self.logger.info("Scheduling full system scan")
        common_paths = ["/home", "/opt", "/usr/local"]

        for path in common_paths:
            if Path(path).exists():
                self.schedule_scan(path, ScanPriority.LOW)

    def _schedule_quick_scan(self):
        """Schedule a quick scan of common directories."""
        self.logger.info("Scheduling quick scan")
        quick_paths = [tempfile.gettempdir(), "/home/*/Downloads"]

        for path_pattern in quick_paths:
            # Expand path pattern and scan
            for path in glob.glob(path_pattern):
                if Path(path).exists():
                    self.schedule_scan(path, ScanPriority.NORMAL)

    def _cleanup_old_results(self):
        """Clean up old scan results to prevent memory bloat."""
        current_time = time.time()
        cutoff_time = current_time - (24 * 60 * 60)  # 24 hours

        old_results = [
            path
            for path, result in self.scan_results.items()
            if result.get("timestamp", 0) < cutoff_time
        ]

        for path in old_results:
            del self.scan_results[path]

        if old_results:
            logging.getLogger(__name__).info(
                "Cleaned up %d old scan results", len(old_results)
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get scanner performance statistics."""
        uptime = time.time() - self.start_time
        return {
            "running": self.running,
            "uptime_seconds": uptime,
            "scans_completed": self.scans_completed,
            "threats_detected": self.threats_detected,
            "scans_per_hour": self.scans_completed / max(uptime / 3600, 1),
            "active_scans": len(self.active_scans),
            "queued_scans": self.scan_queue.qsize(),
            "cached_results": len(self.scan_results),
            "worker_threads": len(self.worker_threads),
        }

    def get_recent_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent scan results."""
        results = []
        for path, result in self.scan_results.items():
            results.append({"file_path": path, **result})

        # Sort by timestamp, most recent first
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return results[:limit]

    def set_result_callback(self, callback: Callable[[str, Any], None]):
        """Set callback for scan results."""
        self.result_callback = callback

    def set_threat_callback(self, callback: Callable[[str, str], None]):
        """Set callback for threat detection."""
        self.threat_callback = callback
