#!/usr/bin/env python3
"""Background scanner for continuous monitoring
Performs scheduled scans and processes file system events
"""

import glob
import logging
import os
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Empty, Queue
from typing import Any

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

        def do(self, _func, *_, **__):
            return self

    class _NoOpScheduler:
        def every(self, *_args, **_kwargs):
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
from .scan_priority import ScanPriority
from .scan_cache import ScanResultCache
from .smart_prioritizer import SmartPrioritizer
from .pre_processor import PreProcessor
from .system_monitor import SystemMonitor
from .performance_metrics import PerformanceMetrics, ScanMetrics

try:
    from app.core.hybrid_scanner import HybridScanner

    HYBRID_SCANNER_AVAILABLE = True
except ImportError:
    HYBRID_SCANNER_AVAILABLE = False


@dataclass
class ScanTask:
    """Represents a background scan task."""

    file_path: str
    priority: ScanPriority
    timestamp: float
    event_type: WatchEventType | None = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = 0.0  # Track when task was created for starvation prevention

    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()
        if self.created_at == 0.0:
            self.created_at = time.time()

    def get_age_seconds(self) -> float:
        """Get age of task in seconds."""
        return time.time() - self.created_at

    def should_boost_priority(self, starvation_threshold: int = 60) -> bool:
        """Check if task has been waiting long enough to boost priority.

        Args:
            starvation_threshold: Seconds before boosting priority

        Returns:
            True if task should have priority boosted
        """
        return self.get_age_seconds() > starvation_threshold


class BackgroundScanner:
    """Background scanner that processes file system events and performs scheduled scans."""

    def __init__(
        self,
        file_scanner: ClamAVWrapper | None = None,
        enable_cache: bool = True,
        enable_hybrid: bool = True,
        enable_system_monitor: bool = True,
    ):
        """Initialize background scanner.

        Args:
            file_scanner: ClamAV wrapper instance to use (for backward compatibility)
            enable_cache: Enable scan result caching (default: True)
            enable_hybrid: Enable hybrid multi-engine scanning (ClamAV + YARA)
            enable_system_monitor: Enable system load monitoring for adaptive scanning
        """
        self.logger = logging.getLogger(__name__)

        # Scanner setup - prefer hybrid if available
        self.hybrid_mode = enable_hybrid and HYBRID_SCANNER_AVAILABLE
        if self.hybrid_mode:
            self.file_scanner = HybridScanner(
                enable_clamav=True,
                enable_yara=True,
            )
            self.logger.info("Using hybrid multi-engine scanner (ClamAV + YARA)")
        else:
            self.file_scanner = file_scanner or ClamAVWrapper()
            if enable_hybrid:
                self.logger.warning(
                    "Hybrid scanner requested but not available, using ClamAV only"
                )

        # Task management
        self.scan_queue: Queue[ScanTask] = Queue()
        self.active_scans: set[str] = set()
        self.scan_results: dict[str, Any] = {}

        # Threading with adaptive scaling
        self.running = False
        self.worker_threads: list[threading.Thread] = []

        # Adaptive worker thread configuration
        cpu_count = os.cpu_count() or 2
        self.min_workers = 2
        self.max_workers = min(cpu_count, 8)  # Cap at 8 threads
        self.num_workers = self.min_workers
        self.target_workers = self.min_workers

        # Auto-scaling thresholds
        self.scale_up_threshold = 50  # Queue depth to trigger scale up
        self.scale_down_threshold = 10  # Queue depth to trigger scale down
        self.scaling_cooldown = 30.0  # Seconds between scaling operations
        self.last_scaling_time = 0.0

        # Performance optimizations
        self.scan_cache = ScanResultCache(ttl_hours=24) if enable_cache else None
        self.prioritizer = SmartPrioritizer()
        self.pre_processor = PreProcessor(
            scan_cache=self.scan_cache,
            active_scans=self.active_scans,
        )

        # System load monitoring
        self.system_monitor = SystemMonitor() if enable_system_monitor else None
        if self.system_monitor and not self.system_monitor.available:
            self.logger.warning("System monitor requested but psutil not available")
            self.system_monitor = None

        # Performance metrics tracking
        self.performance_metrics = PerformanceMetrics(
            export_interval=300
        )  # Export every 5 minutes

        # Scheduling
        self.scheduler = schedule
        if not SCHEDULE_AVAILABLE:
            self.logger.warning(
                "Python 'schedule' package not installed; background scan schedules disabled. "
                "Install with: pip install --user schedule"
            )
        self.scheduler_thread: threading.Thread | None = None

        # Event callbacks
        self.result_callback: Callable[[str, Any], None] | None = None
        self.threat_callback: Callable[[str, str], None] | None = None

        # Performance monitoring
        self.scans_completed = 0
        self.scans_skipped_cache = 0
        self.threats_detected = 0
        self.start_time = time.time()

        # Configuration
        self.scan_timeout = 30.0  # seconds
        self.max_concurrent_scans = 3
        self.immediate_scan_extensions: set[str] = {
            ".exe",
            ".dll",
            ".bat",
            ".sh",
            ".py",
            ".jar",
        }

        self._setup_scheduled_tasks()

    # --- Logger helper methods for consistent callsites (used across modules) ---
    def loginfo(self, message: str):
        """Info-level log wrapper."""
        self.logger.info("%s", message)

    def logdebug(self, message: str):
        """Debug-level log wrapper."""
        self.logger.debug("%s", message)

    def logwarning(self, message: str):
        """Warning-level log wrapper."""
        self.logger.warning("%s", message)

    def logerror(self, message: str):
        """Error-level log wrapper."""
        self.logger.error("%s", message)

    def start(self):
        """Start the background scanner."""
        if self.running:
            self.logger.warning("Background scanner already running")
            return

        self.running = True
        self.start_time = time.time()
        self.last_scaling_time = time.time()

        # Start initial worker threads
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

        self.logger.info(
            "Background scanner started with %d workers (adaptive: %d-%d)",
            self.num_workers,
            self.min_workers,
            self.max_workers,
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
        """Handle a file system event by scheduling appropriate scans.

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
        """Schedule a manual scan of a file.

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
        # Use smart prioritizer for risk-based priority
        base_priority = self.prioritizer.get_priority(event.file_path)

        # Boost priority for new files
        if event.event_type == WatchEventType.FILE_CREATED:
            if base_priority == ScanPriority.LOW:
                return ScanPriority.NORMAL
            elif base_priority == ScanPriority.NORMAL:
                return ScanPriority.HIGH
            # IMMEDIATE and HIGH stay the same

        return base_priority

    def _worker_loop(self):
        """Main worker loop for processing scan tasks."""
        while self.running:
            try:
                # Check system load before processing
                if self.system_monitor:
                    if self.system_monitor.should_pause_scanning():
                        self.logger.debug("Pausing due to critical system load")
                        time.sleep(2.0)
                        continue
                    elif self.system_monitor.should_throttle_scanning():
                        delay = self.system_monitor.get_recommended_delay()
                        self.logger.debug("Throttling scan (delay: %.1fs)", delay)
                        time.sleep(delay)

                # Get task from queue with timeout
                try:
                    task = self.scan_queue.get(timeout=1.0)
                except Empty:
                    continue

                # Starvation prevention: boost priority if task waiting too long
                if task.should_boost_priority(starvation_threshold=60):
                    original_priority = task.priority
                    # Boost one level
                    if task.priority == ScanPriority.LOW:
                        task.priority = ScanPriority.NORMAL
                    elif task.priority == ScanPriority.NORMAL:
                        task.priority = ScanPriority.HIGH
                    elif task.priority == ScanPriority.HIGH:
                        task.priority = ScanPriority.IMMEDIATE
                    # IMMEDIATE stays IMMEDIATE

                    if task.priority != original_priority:
                        self.logger.info(
                            "Boosted priority for %s: %s -> %s (waited %.1f seconds)",
                            task.file_path,
                            original_priority.name,
                            task.priority.name,
                            task.get_age_seconds(),
                        )

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

            # Pre-processor check - quick filtering before cache and scan
            should_scan, reason = self.pre_processor.should_scan(task.file_path)
            if not should_scan:
                self.scans_skipped_cache += 1
                self.logger.debug(
                    "Pre-processor skip for %s: %s",
                    task.file_path,
                    reason,
                )

                # Create result for skipped file
                self.scan_results[task.file_path] = {
                    "result": (
                        "clean"
                        if reason in ("safe_extension", "cached_clean")
                        else "skipped"
                    ),
                    "reason": reason,
                    "timestamp": time.time(),
                    "priority": task.priority.name,
                    "cached": reason == "cached_clean",
                }

                # Call result callback
                if self.result_callback:
                    try:
                        self.result_callback(
                            task.file_path, self.scan_results[task.file_path]
                        )
                    except Exception as e:
                        self.logger.error("Error in result callback: %s", e)

                return  # Skip actual scan

            start_time = time.time()
            self.logdebug(
                "Starting scan of %s".replace("%s", "{task.file_path}").replace(
                    "%d", "{task.file_path}"
                )
            )

            # Perform the scan (hybrid or standard)
            scan_result = self.file_scanner.scan_file(task.file_path)

            scan_time = time.time() - start_time

            # Handle hybrid vs standard scan results
            if self.hybrid_mode:
                # Hybrid scanner result
                infected = scan_result.infected
                threat_name = scan_result.virus_name
                threat_type = scan_result.scan_engine

                # Build result dict with hybrid details
                result_data = {
                    "result": "infected" if infected else "clean",
                    "threat_name": threat_name,
                    "threat_type": threat_type,
                    "threat_level": scan_result.threat_level,
                    "scan_time": scan_time,
                    "timestamp": time.time(),
                    "priority": task.priority.name,
                    "event_type": task.event_type.value if task.event_type else None,
                    "cached": False,
                    # Hybrid-specific fields
                    "scan_engine": scan_result.scan_engine,
                    "clamav_detected": scan_result.clamav_infected,
                    "clamav_virus": scan_result.clamav_virus,
                    "yara_detected": scan_result.yara_matched,
                    "yara_rules": scan_result.yara_rules,
                    "yara_severity": scan_result.yara_severity,
                    "detection_layers": scan_result.detection_layers,
                }
            else:
                # Standard ClamAV result
                infected = scan_result.result.value == "infected"
                threat_name = scan_result.threat_name

                result_data = {
                    "result": scan_result.result.value,
                    "threat_name": threat_name,
                    "threat_type": scan_result.threat_type,
                    "scan_time": scan_time,
                    "timestamp": time.time(),
                    "priority": task.priority.name,
                    "event_type": task.event_type.value if task.event_type else None,
                    "file_size": scan_result.file_size,
                    "error_message": scan_result.error_message,
                    "cached": False,
                }

            # Update statistics
            self.scans_completed += 1
            if infected:
                self.threats_detected += 1

            # Store result
            self.scan_results[task.file_path] = result_data

            # Record performance metrics
            file_size = result_data.get("file_size", 0)
            if not file_size and self.hybrid_mode:
                # Try to get file size
                try:
                    file_size = Path(task.file_path).stat().st_size
                except Exception:
                    file_size = 0

            self.performance_metrics.record_scan(
                ScanMetrics(
                    file_path=task.file_path,
                    scan_duration=scan_time,
                    file_size=file_size,
                    result="infected" if infected else "clean",
                    cached=False,
                    priority=task.priority.name,
                )
            )

            # Add to cache (if enabled and scan was successful)
            if self.scan_cache:
                cache_status = "infected" if infected else "clean"
                self.scan_cache.add_result(
                    task.file_path,
                    cache_status,
                    threat_name,
                )

            # Call callbacks
            if self.result_callback:
                try:
                    self.result_callback(task.file_path, result_data)
                except Exception:
                    self.logerror(
                        "Error in result callback: %s".replace("%s", "{e}").replace(
                            "%d", "{e}"
                        )
                    )

            if infected and self.threat_callback:
                try:
                    self.threat_callback(task.file_path, threat_name or "Unknown")
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

        # Schedule adaptive worker scaling check every 30 seconds
        self.scheduler.every(30).seconds.do(self._check_and_scale_workers)

        # Schedule performance snapshot every 60 seconds
        self.scheduler.every(60).seconds.do(self._record_performance_snapshot)

    def _check_and_scale_workers(self):
        """Check queue depth and adjust worker count if needed."""
        if not self.running:
            return

        # Check cooldown period
        now = time.time()
        if now - self.last_scaling_time < self.scaling_cooldown:
            return  # Too soon to scale again

        queue_depth = self.scan_queue.qsize()
        current_workers = len(self.worker_threads)

        # Determine target worker count
        if queue_depth > self.scale_up_threshold and current_workers < self.max_workers:
            # Scale up - queue is backing up
            old_workers = current_workers
            self.target_workers = min(current_workers + 1, self.max_workers)
            self._add_worker()
            new_workers = len(self.worker_threads)

            # Record scaling event
            self.performance_metrics.record_scaling_event(
                event_type="scale_up",
                old_workers=old_workers,
                new_workers=new_workers,
                queue_depth=queue_depth,
                reason="Queue depth exceeded threshold",
            )

            self.logger.info(
                "Scaling up: %d → %d workers (queue: %d items)",
                old_workers,
                new_workers,
                queue_depth,
            )
            self.last_scaling_time = now

        elif (
            queue_depth < self.scale_down_threshold
            and current_workers > self.min_workers
        ):
            # Scale down - workers idle
            old_workers = current_workers
            self.target_workers = max(current_workers - 1, self.min_workers)
            self._remove_worker()
            new_workers = len(self.worker_threads)

            # Record scaling event
            self.performance_metrics.record_scaling_event(
                event_type="scale_down",
                old_workers=old_workers,
                new_workers=new_workers,
                queue_depth=queue_depth,
                reason="Workers idle, queue empty",
            )

            self.logger.info(
                "Scaling down: %d → %d workers (queue: %d items)",
                old_workers,
                new_workers,
                queue_depth,
            )
            self.last_scaling_time = now

    def _record_performance_snapshot(self):
        """Record a performance snapshot for metrics tracking."""
        if not self.running:
            return

        stats = self.get_statistics()
        self.performance_metrics.record_snapshot(stats)

    def _add_worker(self):
        """Add a new worker thread."""
        if not self.running:
            return

        worker_id = len(self.worker_threads)
        thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"BackgroundScanner-{worker_id}",
        )
        thread.start()
        self.worker_threads.append(thread)
        self.num_workers = len(self.worker_threads)
        self.logger.debug("Added worker thread #%d", worker_id)

    def _remove_worker(self):
        """Remove a worker thread (gracefully)."""
        if len(self.worker_threads) <= self.min_workers:
            return  # Don't go below minimum

        # Workers will naturally exit when queue is empty and running=False
        # We just update the count - next worker to find empty queue will exit
        if self.worker_threads:
            self.worker_threads.pop()
            self.num_workers = len(self.worker_threads)
            self.logger.debug("Removed worker thread (target: %d)", self.num_workers)

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

    def get_statistics(self) -> dict[str, Any]:
        """Get scanner performance statistics."""
        uptime = time.time() - self.start_time
        stats = {
            "running": self.running,
            "uptime_seconds": uptime,
            "scans_completed": self.scans_completed,
            "scans_skipped_cache": self.scans_skipped_cache,
            "threats_detected": self.threats_detected,
            "scans_per_hour": self.scans_completed / max(uptime / 3600, 1),
            "active_scans": len(self.active_scans),
            "queued_scans": self.scan_queue.qsize(),
            "cached_results": len(self.scan_results),
            "worker_threads": len(self.worker_threads),
            "hybrid_mode": self.hybrid_mode,
            # Adaptive scaling metrics
            "adaptive_scaling": {
                "enabled": True,
                "current_workers": len(self.worker_threads),
                "min_workers": self.min_workers,
                "max_workers": self.max_workers,
                "target_workers": self.target_workers,
                "scale_up_threshold": self.scale_up_threshold,
                "scale_down_threshold": self.scale_down_threshold,
                "time_since_last_scale": time.time() - self.last_scaling_time,
            },
        }

        # Add cache statistics if enabled
        if self.scan_cache:
            stats["cache"] = self.scan_cache.get_statistics()

        # Add pre-processor statistics
        stats["pre_processor"] = self.pre_processor.get_statistics()

        # Add hybrid scanner statistics if enabled
        if self.hybrid_mode and hasattr(self.file_scanner, "get_statistics"):
            stats["hybrid_scanner"] = self.file_scanner.get_statistics()

        # Add system monitor statistics if enabled
        if self.system_monitor:
            stats["system_monitor"] = self.system_monitor.get_statistics()

        # Add performance metrics summary
        stats["performance_metrics"] = self.performance_metrics.get_summary()

        return stats

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get the performance metrics tracker.

        Returns:
            PerformanceMetrics instance for advanced querying
        """
        return self.performance_metrics

    def export_performance_metrics(self, file_path: str | Path | None = None) -> str:
        """Export performance metrics to JSON file.

        Args:
            file_path: Optional custom export path

        Returns:
            Path to exported file
        """
        return self.performance_metrics.export_to_json(file_path)

    def get_recent_results(self, limit: int = 100) -> list[dict[str, Any]]:
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
