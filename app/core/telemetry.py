#!/usr/bin/env python3
"""
Anonymous telemetry module for xanadOS Search & Destroy
Collects usage analytics while preserving privacy
"""

import hashlib
import json
import logging
import queue
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from app.utils.config import CACHE_DIR
import tempfile
import platform


@dataclass
class TelemetryEvent:
    """Represents a telemetry event."""

    event_type: str
    timestamp: float
    session_id: str
    data: Dict[str, Any]
    privacy_level: str = "anonymous"  # anonymous, aggregated, detailed


class PrivacyManager:
    """Manages privacy settings and data anonymization."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._salt = None

    def get_salt(self) -> str:
        """Get or create a consistent salt for hashing."""
        if self._salt is None:
            try:
                salt_file = Path(CACHE_DIR) / "telemetry_salt"

                if salt_file.exists():
                    with open(salt_file, "r") as f:
                        self._salt = f.read().strip()
                else:
                    self._salt = str(uuid.uuid4())
                    salt_file.parent.mkdir(exist_ok=True)
                    with open(salt_file, "w") as f:
                        f.write(self._salt)

            except Exception as e:
                self.logger.warning(f"Could not load/save salt: {e}")
                self._salt = str(uuid.uuid4())

        return self._salt

    def anonymize_path(self, path: str) -> str:
        """Anonymize file paths while preserving useful information."""
        if not path:
            return ""

        p = Path(path)

        # Hash the directory structure but keep file extension
        dir_hash = hashlib.sha256((str(p.parent) + self.get_salt()).encode()).hexdigest()[:8]

        extension = p.suffix.lower() if p.suffix else ""

        return f"path_{dir_hash}{extension}"

    def anonymize_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or anonymize personally identifiable information."""
        anonymized = {}

        for key, value in data.items():
            if key in ["username", "hostname", "ip_address", "mac_address"]:
                # Skip PII data
                continue
            elif key in ["file_path", "directory_path", "scan_path"]:
                anonymized[key] = self.anonymize_path(str(value)) if value else ""
            elif key == "file_size" and isinstance(value, (int, float)):
                # Round file size to nearest 1KB for privacy
                anonymized[key] = round(value / 1024) * 1024
            elif isinstance(value, str) and len(value) > 100:
                # Truncate very long strings that might contain sensitive data
                anonymized[key] = f"<truncated_{len(value)}_chars>"
            else:
                anonymized[key] = value

        return anonymized


class TelemetryCollector:
    """Collects and manages telemetry events."""

    def __init__(self, enabled: bool = True, privacy_level: str = "anonymous"):
        self.logger = logging.getLogger(__name__)
        self.enabled = enabled
        self.privacy_level = privacy_level
        self.privacy_manager = PrivacyManager()

        # Session management
        self.session_id = str(uuid.uuid4())
        self.session_start = time.time()

        # Event storage
        self.events_queue = queue.Queue(maxsize=1000)
        self.events_lock = threading.RLock()

        # Periodic flush
        self.flush_interval = 300  # 5 minutes
        self.last_flush = time.time()

        # Storage path
        try:
            self.storage_path = Path(CACHE_DIR) / "telemetry"
            self.storage_path.mkdir(exist_ok=True)
        except ImportError:
            # Use secure temp directory

            self.storage_path = Path(tempfile.gettempdir()) / "xanados_telemetry"
            self.storage_path.mkdir(exist_ok=True, mode=0o700)  # Secure permissions

        # Initialize aggregated counters
        self.counters = {
            "scans_performed": 0,
            "threats_detected": 0,
            "files_quarantined": 0,
            "scan_errors": 0,
            "session_duration": 0,
            "gui_interactions": 0,
        }

        self.logger.info(f"Telemetry initialized - enabled: {enabled}, privacy: {privacy_level}")

    def record_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        privacy_level: Optional[str] = None,
    ):
        """Record a telemetry event."""
        if not self.enabled:
            return

        try:
            event_data = data or {}
            effective_privacy = privacy_level or self.privacy_level

            # Apply privacy filtering based on level
            if effective_privacy == "anonymous":
                event_data = self.privacy_manager.anonymize_user_data(event_data)

            event = TelemetryEvent(
                event_type=event_type,
                timestamp=time.time(),
                session_id=self.session_id,
                data=event_data,
                privacy_level=effective_privacy,
            )

            # Update counters
            self._update_counters(event_type, event_data)

            # Queue event
            try:
                self.events_queue.put_nowait(event)
            except queue.Full:
                self.logger.warning("Telemetry queue full, dropping event")

            # Periodic flush
            if time.time() - self.last_flush > self.flush_interval:
                self._flush_events()

        except Exception as e:
            self.logger.error(f"Failed to record telemetry event: {e}")

    def _update_counters(self, event_type: str, data: Dict[str, Any]):
        """Update aggregated counters."""
        with self.events_lock:
            if event_type == "scan_completed":
                self.counters["scans_performed"] += 1
                if data.get("threats_found", 0) > 0:
                    self.counters["threats_detected"] += data["threats_found"]
            elif event_type == "file_quarantined":
                self.counters["files_quarantined"] += 1
            elif event_type == "scan_error":
                self.counters["scan_errors"] += 1
            elif event_type == "gui_interaction":
                self.counters["gui_interactions"] += 1

            # Update session duration
            self.counters["session_duration"] = time.time() - self.session_start

    def _flush_events(self):
        """Flush events to storage."""
        if not self.enabled:
            return

        try:
            events_to_flush = []

            # Collect events from queue
            while True:
                try:
                    event = self.events_queue.get_nowait()
                    events_to_flush.append(event)
                except queue.Empty:
                    break

            if not events_to_flush:
                return

            # Write to storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telemetry_{timestamp}_{self.session_id[:8]}.json"
            filepath = self.storage_path / filename

            with open(filepath, "w") as f:
                json.dump(
                    {
                        "metadata": {
                            "version": "1.0",
                            "session_id": self.session_id,
                            "timestamp": timestamp,
                            "privacy_level": self.privacy_level,
                            "event_count": len(events_to_flush),
                        },
                        "counters": self.counters.copy(),
                        "events": [asdict(event) for event in events_to_flush],
                    },
                    f,
                    indent=2,
                )

            self.last_flush = time.time()
            self.logger.debug(f"Flushed {len(events_to_flush)} telemetry events")

        except Exception as e:
            self.logger.error(f"Failed to flush telemetry events: {e}")

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        with self.events_lock:
            return {
                "session_id": self.session_id,
                "session_duration": time.time() - self.session_start,
                "counters": self.counters.copy(),
                "privacy_level": self.privacy_level,
                "events_queued": self.events_queue.qsize(),
            }

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old telemetry data."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        try:
            for file_path in self.storage_path.glob("telemetry_*.json"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    self.logger.debug(f"Removed old telemetry file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old telemetry data: {e}")

    def export_summary(self, output_path: str):
        """Export aggregated summary for analysis."""
        try:
            summary = {
                "export_timestamp": datetime.now().isoformat(),
                "session_summary": self.get_session_summary(),
                "system_info": self._get_anonymous_system_info(),
            }

            with open(output_path, "w") as f:
                json.dump(summary, f, indent=2)

            self.logger.info(f"Telemetry summary exported to: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to export telemetry summary: {e}")

    def _get_anonymous_system_info(self) -> Dict[str, Any]:
        """Get anonymous system information for analytics."""
        info = {
            "platform": "unknown",
            "python_version": "unknown",
            "app_version": "unknown",
        }

        try:
            info["platform"] = platform.system()
            info["python_version"] = platform.python_version()

            # Try to get app version
            try:
                with open(Path(__file__).parent.parent.parent / "VERSION", "r") as f:
                    info["app_version"] = f.read().strip()
            except FileNotFoundError:
                pass

        except ImportError:
            pass

        return info

    def shutdown(self):
        """Shutdown telemetry and flush remaining events."""
        if self.enabled:
            self._flush_events()
            self.logger.info("Telemetry shutdown completed")


class TelemetryManager:
    """High-level telemetry management."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize telemetry based on configuration
        enabled = self.config.get("telemetry", {}).get("enabled", True)
        privacy_level = self.config.get("telemetry", {}).get("privacy_level", "anonymous")

        self.collector = TelemetryCollector(enabled, privacy_level)
        self.logger = logging.getLogger(__name__)

        # Record initialization
        self.collector.record_event(
            "app_initialized",
            {"timestamp": datetime.now().isoformat(), "privacy_level": privacy_level},
        )

    def record_scan_event(
        self,
        scan_type: str,
        file_count: int,
        duration: float,
        threats_found: int = 0,
        errors: int = 0,
    ):
        """Record a scan completion event."""
        self.collector.record_event(
            "scan_completed",
            {
                "scan_type": scan_type,
                "file_count": file_count,
                "duration_seconds": round(duration, 2),
                "threats_found": threats_found,
                "errors": errors,
                "files_per_second": (round(file_count / duration, 2) if duration > 0 else 0),
            },
        )

    def record_threat_event(self, threat_type: str, action_taken: str):
        """Record a threat detection event."""
        self.collector.record_event(
            "threat_detected",
            {"threat_type": threat_type, "action_taken": action_taken},
        )

    def record_gui_interaction(self, component: str, action: str):
        """Record a GUI interaction event."""
        self.collector.record_event("gui_interaction", {"component": component, "action": action})

    def record_performance_metrics(self, metrics: Dict[str, Any]):
        """Record performance metrics."""
        self.collector.record_event("performance_metrics", metrics)

    def record_error(self, error_type: str, component: str, details: str = ""):
        """Record an error event."""
        self.collector.record_event(
            "error_occurred",
            {
                "error_type": error_type,
                "component": component,
                "details": details[:200],  # Limit details length
            },
        )

    def get_privacy_settings(self) -> Dict[str, Any]:
        """Get current privacy settings."""
        return {
            "enabled": self.collector.enabled,
            "privacy_level": self.collector.privacy_level,
            "data_retention_days": 30,
            "anonymous_only": self.collector.privacy_level == "anonymous",
        }

    def update_privacy_settings(self, enabled: bool, privacy_level: str):
        """Update privacy settings."""
        self.collector.enabled = enabled
        self.collector.privacy_level = privacy_level

        self.collector.record_event(
            "privacy_settings_changed",
            {"enabled": enabled, "privacy_level": privacy_level},
        )

    def shutdown(self):
        """Shutdown telemetry."""
        self.collector.record_event(
            "app_shutdown",
            {"session_duration": self.collector.counters["session_duration"]},
        )
        self.collector.shutdown()


# Global telemetry manager instance
_telemetry_manager = None


def get_telemetry_manager(config: Optional[Dict[str, Any]] = None) -> TelemetryManager:
    """Get or create global telemetry manager."""
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager(config)
    return _telemetry_manager


def initialize_telemetry(config: Optional[Dict[str, Any]] = None):
    """Initialize global telemetry system."""
    return get_telemetry_manager(config)


def shutdown_telemetry():
    """Shutdown global telemetry system."""
    global _telemetry_manager
    if _telemetry_manager:
        _telemetry_manager.shutdown()
        _telemetry_manager = None


# Convenience functions
def record_scan(scan_type: str, file_count: int, duration: float, **kwargs):
    """Record a scan event."""
    get_telemetry_manager().record_scan_event(scan_type, file_count, duration, **kwargs)


def record_threat(threat_type: str, action_taken: str):
    """Record a threat event."""
    get_telemetry_manager().record_threat_event(threat_type, action_taken)


def record_gui_action(component: str, action: str):
    """Record a GUI interaction."""
    get_telemetry_manager().record_gui_interaction(component, action)


def record_performance(metrics: Dict[str, Any]):
    """Record performance metrics."""
    get_telemetry_manager().record_performance_metrics(metrics)


def record_error(error_type: str, component: str, details: str = ""):
    """Record an error."""
    get_telemetry_manager().record_error(error_type, component, details)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Test telemetry
    config = {"telemetry": {"enabled": True, "privacy_level": "anonymous"}}

    tm = initialize_telemetry(config)

    # Record some test events
    record_scan("full_system", 1000, 30.5, threats_found=2)
    record_threat("virus", "quarantined")
    record_gui_action("main_window", "scan_button_clicked")
    record_performance({"cpu_usage": 45.2, "memory_mb": 150.3})

    # Print session summary
    print("Session Summary:", tm.collector.get_session_summary())

    # Shutdown
    shutdown_telemetry()
