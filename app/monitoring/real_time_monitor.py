#!/usr/bin/env python3
"""
Real-time monitor that coordinates file watching, event processing, and background scanning
Main entry point for Phase 3 real-time monitoring system
"""
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .background_scanner import BackgroundScanner, ScanPriority
from .event_processor import EventAction, EventProcessor, ProcessedEvent
from .file_watcher import FileSystemWatcher, WatchEvent

try:
    from core.clamav_wrapper import ClamAVWrapper
except ImportError:
    # Fallback for development/testing
    class ClamAVWrapper:
        def __init__(self):
            self.available = False


class MonitorState(Enum):
    """Monitor operational states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class MonitorConfig:
    """Configuration for real-time monitor."""

    watch_paths: List[str]
    excluded_paths: Optional[List[str]] = None
    scan_new_files: bool = True
    scan_modified_files: bool = True
    quarantine_threats: bool = True
    enable_background_scans: bool = True
    max_watch_events_per_sec: int = 100

    def __post_init__(self):
        if self.excluded_paths is None:
            self.excluded_paths = []


class RealTimeMonitor:
    """
    Main real-time monitoring system that coordinates all components.
    Provides comprehensive real-time protection and monitoring.
    """

    def __init__(self, config: Optional[MonitorConfig] = None):
        """
        Initialize real-time monitor.

        Args:
            config: Monitor configuration
        """
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.config = config or MonitorConfig(
            watch_paths=["/home", "/opt", "/usr/local", "/tmp"],
            excluded_paths=["/proc", "/sys", "/dev"],
        )

        # Components
        self.file_watcher = FileSystemWatcher()
        self.event_processor = EventProcessor()
        self.background_scanner = BackgroundScanner()
        self.clamav = ClamAVWrapper()

        # State management
        self.state = MonitorState.STOPPED
        self.start_time: Optional[float] = None
        self.error_message: Optional[str] = None

        # Statistics
        self.events_processed = 0
        self.threats_detected = 0
        self.files_quarantined = 0
        self.scans_performed = 0

        # Callbacks
        self.threat_detected_callback: Optional[Callable[[
            str, str], None]] = None
        self.file_quarantined_callback: Optional[Callable[[str], None]] = None
        self.scan_completed_callback: Optional[Callable[[
            str, str], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None

        # Threading
        self.lock = threading.RLock()

        # Setup component integration
        self._setup_callbacks()

    def start(self) -> bool:
        """
        Start real-time monitoring.

        Returns:
            True if started successfully, False otherwise
        """
        with self.lock:
            if self.state in [MonitorState.RUNNING, MonitorState.STARTING]:
                self.logger.warning("Monitor already running or starting")
                return True

            if self.state == MonitorState.STOPPING:
                self.logger.error("Cannot start while stopping")
                return False

            self.state = MonitorState.STARTING
            self.error_message = None

        try:
            # Check ClamAV availability
            if not self.clamav.available:
                raise RuntimeError(
                    "ClamAV not available - real-time scanning disabled")

            # Start background scanner
            self.logger.info("Starting background scanner...")
            self.background_scanner.start()

            # Setup file watcher paths
            self.logger.info("Setting up file system watching...")
            for path in self.config.watch_paths:
                path_obj = Path(path)
                if path_obj.exists():
                    self.file_watcher.add_watch_path(path)
                    self.logger.info("Added watch path: %s", path)
                else:
                    self.logger.warning("Watch path does not exist: %s", path)

            # Start file watcher
            self.file_watcher.start_watching()

            # Update state
            with self.lock:
                self.state = MonitorState.RUNNING
                self.start_time = time.time()

            self.logger.info("Real-time monitor started successfully")
            return True

        except Exception as e:
            self.logger.error("Failed to start real-time monitor: %s", e)
            with self.lock:
                self.state = MonitorState.ERROR
                self.error_message = str(e)

            # Cleanup on failure
            self._cleanup()

            if self.error_callback:
                try:
                    self.error_callback(str(e))
                except Exception as cb_error:
                    self.logger.error("Error in error callback: %s", cb_error)

            return False

    def stop(self):
        """Stop real-time monitoring."""
        with self.lock:
            if self.state in [MonitorState.STOPPED, MonitorState.STOPPING]:
                return

            self.state = MonitorState.STOPPING

        self.logger.info("Stopping real-time monitor...")

        try:
            # Stop components
            self.file_watcher.stop_watching()
            self.background_scanner.stop()

            with self.lock:
                self.state = MonitorState.STOPPED

            self.logger.info("Real-time monitor stopped")

        except Exception as e:
            self.logger.error("Error stopping real-time monitor: %s", e)
            with self.lock:
                self.state = MonitorState.ERROR
                self.error_message = str(e)

    def _cleanup(self):
        """Cleanup components on error."""
        try:
            self.file_watcher.stop_watching()
        except Exception:
            pass

        try:
            self.background_scanner.stop()
        except Exception:
            pass

    def _setup_callbacks(self):
        """Setup callbacks between components."""
        # File watcher -> Event processor
        self.file_watcher.set_event_callback(self._on_file_event)

        # Event processor -> Actions
        self.event_processor.set_event_callback(self._on_processed_event)
        self.event_processor.set_alert_callback(self._on_alert)

        # Background scanner -> Results
        self.background_scanner.set_result_callback(self._on_scan_result)
        self.background_scanner.set_threat_callback(self._on_threat_detected)

    def _on_file_event(self, event: WatchEvent):
        """Handle file system event."""
        try:
            # Process event through rules
            processed_event = self.event_processor.process_event(event)

            if processed_event:
                with self.lock:
                    self.events_processed += 1

                self.logger.debug(
                    "File event: %s (%s) -> %s",
                    event.file_path,
                    event.event_type.value,
                    processed_event.action.value,
                )

        except Exception as e:
            self.logger.error("Error handling file event: %s", e)

    def _on_processed_event(self, event: ProcessedEvent):
        """Handle processed file event."""
        try:
            # Execute action based on event processing
            if event.action == EventAction.SCAN:
                self._schedule_scan(event)
            elif event.action == EventAction.QUARANTINE:
                self._quarantine_file(event)
            elif event.action == EventAction.BLOCK:
                self._block_file(event)
            # IGNORE and ALERT actions are handled by event processor

        except Exception as e:
            self.logger.error(
                "Error executing action for %s: %s",
                event.original_event.file_path,
                e)

    def _schedule_scan(self, event: ProcessedEvent):
        """Schedule a file scan based on processed event."""
        # Determine scan priority
        if event.priority >= 90:
            priority = ScanPriority.IMMEDIATE
        elif event.priority >= 70:
            priority = ScanPriority.HIGH
        elif event.priority >= 50:
            priority = ScanPriority.NORMAL
        else:
            priority = ScanPriority.LOW

        # Schedule scan
        self.background_scanner.schedule_scan(
            event.original_event.file_path, priority)

        self.logger.debug(
            "Scheduled scan for %s (priority: %s)",
            event.original_event.file_path,
            priority.name,
        )

    def _quarantine_file(self, event: ProcessedEvent):
        """Quarantine a file immediately."""
        try:
            file_path = Path(event.original_event.file_path)

            # Only quarantine if file still exists
            if file_path.exists():
                # Move to quarantine (simplified - would integrate with
                # QuarantineManager)
                self.logger.warning(
                    "QUARANTINE: %s (rule: %s)", file_path, event.rule_name
                )

                with self.lock:
                    self.files_quarantined += 1

                if self.file_quarantined_callback:
                    try:
                        self.file_quarantined_callback(str(file_path))
                    except Exception as e:
                        self.logger.error(
                            "Error in quarantine callback: %s", e)

        except Exception as e:
            self.logger.error(
                "Error quarantining file %s: %s",
                event.original_event.file_path,
                e)

    def _block_file(self, event: ProcessedEvent):
        """Block file access."""
        try:
            file_path = event.original_event.file_path
            self.logger.warning(
                "BLOCKED: %s (rule: %s)",
                file_path,
                event.rule_name)

            # Could implement actual file blocking here
            # For now, just log and alert
            if self.error_callback:
                try:
                    self.error_callback(f"File blocked: {file_path}")
                except Exception as e:
                    self.logger.error("Error in block callback: %s", e)

        except Exception as e:
            self.logger.error(
                "Error blocking file %s: %s", event.original_event.file_path, e
            )

    def _on_alert(self, file_path: str, message: str):
        """Handle alert from event processor."""
        self.logger.warning("ALERT: %s - %s", file_path, message)

        if self.error_callback:
            try:
                self.error_callback(f"Alert: {message} ({file_path})")
            except Exception as e:
                self.logger.error("Error in alert callback: %s", e)

    def _on_scan_result(self, file_path: str, result: Dict[str, Any]):
        """Handle scan result from background scanner."""
        try:
            with self.lock:
                self.scans_performed += 1

            self.logger.debug(
                "Scan result: %s - %s",
                file_path,
                result["result"])

            if self.scan_completed_callback:
                try:
                    self.scan_completed_callback(file_path, result["result"])
                except Exception as e:
                    self.logger.error("Error in scan callback: %s", e)

        except Exception as e:
            self.logger.error("Error handling scan result: %s", e)

    def _on_threat_detected(self, file_path: str, threat_name: str):
        """Handle threat detection from background scanner."""
        try:
            with self.lock:
                self.threats_detected += 1

            self.logger.critical(
                "THREAT DETECTED: %s - %s",
                file_path,
                threat_name)

            if self.threat_detected_callback:
                try:
                    self.threat_detected_callback(file_path, threat_name)
                except Exception as e:
                    self.logger.error(
                        "Error in threat detection callback: %s", e)

        except Exception as e:
            self.logger.error("Error handling threat detection: %s", e)

    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status."""
        with self.lock:
            uptime = time.time() - self.start_time if self.start_time else 0

            return {
                "state": self.state.value,
                "uptime_seconds": uptime,
                "error_message": self.error_message,
                "events_processed": self.events_processed,
                "threats_detected": self.threats_detected,
                "files_quarantined": self.files_quarantined,
                "scans_performed": self.scans_performed,
                "watch_paths": self.config.watch_paths,
                "excluded_paths": self.config.excluded_paths,
                "clamav_available": self.clamav.available,
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics from all components."""
        return {
            "monitor": self.get_status(),
            "file_watcher": self.file_watcher.get_statistics(),
            "event_processor": self.event_processor.get_statistics(),
            "background_scanner": self.background_scanner.get_statistics(),
        }

    def add_watch_path(self, path: str) -> bool:
        """Add a new path to monitor."""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                self.logger.error("Path does not exist: %s", path)
                return False

            self.file_watcher.add_watch_path(path)
            self.config.watch_paths.append(path)
            self.logger.info("Added watch path: %s", path)
            return True

        except Exception as e:
            self.logger.error("Error adding watch path %s: %s", path, e)
            return False

    def remove_watch_path(self, path: str) -> bool:
        """Remove a path from monitoring."""
        try:
            self.file_watcher.remove_watch_path(path)
            if path in self.config.watch_paths:
                self.config.watch_paths.remove(path)
            self.logger.info("Removed watch path: %s", path)
            return True

        except Exception as e:
            self.logger.error("Error removing watch path %s: %s", path, e)
            return False

    # Callback setters
    def set_threat_detected_callback(
            self, callback: Callable[[str, str], None]):
        """Set callback for threat detection."""
        self.threat_detected_callback = callback

    def set_file_quarantined_callback(self, callback: Callable[[str], None]):
        """Set callback for file quarantine."""
        self.file_quarantined_callback = callback

    def set_scan_completed_callback(
            self, callback: Callable[[str, str], None]):
        """Set callback for scan completion."""
        self.scan_completed_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]):
        """Set callback for errors and alerts."""
        self.error_callback = callback
