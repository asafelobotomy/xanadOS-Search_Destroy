#!/usr/bin/env python3
"""
Firewall Status Update Optimizer
=================================

Provides optimized, event-driven firewall status monitoring with minimal
performance impact. Implements immediate refresh triggers, cache invalidation,
and background monitoring for faster status updates.

Key Features:
- Event-driven status refresh (systemd service changes)
- Cache invalidation on firewall state changes
- Background monitoring with minimal overhead
- Immediate GUI update triggers
- Performance-optimized polling intervals
"""

import json
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from app.core.firewall_detector import FirewallDetector
from app.monitoring.file_watcher import FileSystemWatcher, WatchEvent


class FirewallStatusOptimizer(QObject):
    """Optimized firewall status monitoring with event-driven updates."""

    # Signals for Qt integration
    status_changed = pyqtSignal(dict)  # Emitted when firewall status changes
    cache_invalidated = pyqtSignal(str)  # Emitted when cache is invalidated

    def __init__(
        self, firewall_detector: FirewallDetector | None = None
    ) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Core components
        self.firewall_detector = firewall_detector or FirewallDetector()
        self.file_watcher: FileSystemWatcher | None = None

        # Optimized cache settings
        self.fast_cache_duration = 5  # 5 seconds for quick updates
        self.normal_cache_duration = 30  # 30 seconds for normal operation
        self.current_cache_duration = self.normal_cache_duration

        # Status tracking
        self._last_known_status: dict | None = None
        self._status_callbacks: list[Callable[[dict], None]] = []
        self._monitoring_active = False

        # Performance optimization
        cache_filename = "firewall_optimizer_cache.json"
        cache_dir = Path.home() / ".local/share/search-and-destroy"
        self.cache_file = cache_dir / cache_filename
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Timers for different update frequencies
        self.fast_timer = QTimer()
        self.normal_timer = QTimer()
        self.fast_timer.timeout.connect(self._fast_status_check)
        self.normal_timer.timeout.connect(self._normal_status_check)

        # Initialize monitoring
        self._initialize_file_monitoring()

    def _initialize_file_monitoring(self) -> None:
        """Initialize file system monitoring for service changes."""
        try:
            # Paths to monitor for firewall service changes
            monitor_paths = [
                "/etc/systemd/system",  # Systemd service files
                "/usr/lib/systemd/system",  # System service files
                "/run/systemd/system",  # Runtime service files
                "/etc/ufw",  # UFW configuration
                "/etc/firewalld",  # Firewalld configuration
                "/proc/sys/net",  # Network configuration changes
            ]

            # Filter to existing paths only
            existing_paths = [path for path in monitor_paths if os.path.exists(path)]

            if existing_paths:
                self.file_watcher = FileSystemWatcher(
                    paths_to_watch=existing_paths,
                    event_callback=self._handle_file_event,
                )
                path_count = len(existing_paths)
                msg = f"Initialized file monitoring for {path_count} paths"
                self.logger.info(msg)
            else:
                msg = "No firewall-related paths found for monitoring"
                self.logger.warning(msg)

        except Exception as e:
            self.logger.error(f"Failed to initialize file monitoring: {e}")

    def _handle_file_event(self, event: WatchEvent):
        """Handle file system events that might indicate firewall changes."""
        try:
            # Check if the event is related to firewall services
            relevant_patterns = [
                "ufw",
                "firewall",
                "iptables",
                "nftables",
                "service",
                "systemd",
                "network",
            ]

            file_path_lower = event.file_path.lower()

            is_relevant = any(
                pattern in file_path_lower for pattern in relevant_patterns
            )

            if is_relevant:
                event_type = event.event_type.value
                file_path = event.file_path
                msg = f"Firewall file event: {event_type} - {file_path}"
                self.logger.debug(msg)

                # Trigger immediate status refresh
                self._trigger_immediate_refresh()

        except Exception as e:
            self.logger.error(f"Error handling file event: {e}")

    def _trigger_immediate_refresh(self):
        """Trigger immediate firewall status refresh."""
        try:
            # Switch to fast refresh mode temporarily
            self._switch_to_fast_mode()

            # Clear cache to force fresh status check
            self.invalidate_cache()

            # Perform immediate status check
            QTimer.singleShot(100, self._immediate_status_check)

            self.logger.debug("Triggered immediate firewall status refresh")

        except Exception as e:
            self.logger.error(f"Error triggering immediate refresh: {e}")

    def _switch_to_fast_mode(self):
        """Switch to fast refresh mode for quicker updates."""
        self.current_cache_duration = self.fast_cache_duration

        # Stop normal timer and start fast timer
        self.normal_timer.stop()
        self.fast_timer.start(2000)  # Check every 2 seconds in fast mode

        # Auto-switch back to normal mode after 30 seconds
        QTimer.singleShot(30000, self._switch_to_normal_mode)

        self.logger.debug("Switched to fast refresh mode")

    def _switch_to_normal_mode(self):
        """Switch back to normal refresh mode."""
        self.current_cache_duration = self.normal_cache_duration

        # Stop fast timer and restart normal timer
        self.fast_timer.stop()
        self.normal_timer.start(10000)  # Check every 10 seconds in normal mode

        self.logger.debug("Switched to normal refresh mode")

    def _immediate_status_check(self):
        """Perform immediate status check and notify listeners."""
        try:
            status = self._get_fresh_status()
            self._handle_status_update(status)

        except Exception as e:
            self.logger.error(f"Error in immediate status check: {e}")

    def _fast_status_check(self):
        """Fast status check for rapid updates."""
        try:
            max_age = self.fast_cache_duration
            status = self.get_firewall_status(use_cache=True, max_age=max_age)
            self._handle_status_update(status)

        except Exception as e:
            self.logger.error(f"Error in fast status check: {e}")

    def _normal_status_check(self):
        """Normal status check for regular monitoring."""
        try:
            max_age = self.normal_cache_duration
            status = self.get_firewall_status(use_cache=True, max_age=max_age)
            self._handle_status_update(status)

        except Exception as e:
            self.logger.error(f"Error in normal status check: {e}")

    def _get_fresh_status(self) -> dict:
        """Get fresh firewall status without cache."""
        return self.firewall_detector.get_firewall_status()

    def _handle_status_update(self, status: dict):
        """Handle status update and notify if changed."""
        try:
            # Check if status actually changed
            if self._status_has_changed(status):
                self._last_known_status = status

                # Cache the new status
                self._cache_status(status)

                # Emit signal for Qt integration
                self.status_changed.emit(status)

                # Notify callbacks
                for callback in self._status_callbacks:
                    try:
                        callback(status)
                    except Exception as e:
                        self.logger.error(f"Error in status callback: {e}")

                status_text = status.get("status_text", "Unknown")
                self.logger.info(f"Firewall status changed: {status_text}")

        except Exception as e:
            self.logger.error(f"Error handling status update: {e}")

    def _status_has_changed(self, new_status: dict) -> bool:
        """Check if the status has actually changed."""
        if not self._last_known_status:
            return True

        # Compare key status indicators
        key_fields = ["is_active", "firewall_type", "status_text"]

        for field in key_fields:
            if self._last_known_status.get(field) != new_status.get(field):
                return True

        return False

    def _cache_status(self, status: dict):
        """Cache status with timestamp."""
        try:
            cache_data = {
                "status": status,
                "timestamp": time.time(),
                "cache_duration": self.current_cache_duration,
            }

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f)

        except Exception as e:
            self.logger.error(f"Error caching status: {e}")

    def _load_cached_status(self, max_age: int) -> dict | None:
        """Load cached status if still valid."""
        try:
            if not self.cache_file.exists():
                return None

            with open(self.cache_file) as f:
                cache_data = json.load(f)

            # Check cache age
            age = time.time() - cache_data.get("timestamp", 0)
            if age < max_age:
                return cache_data.get("status")

        except Exception as e:
            self.logger.debug(f"Error loading cached status: {e}")

        return None

    def get_firewall_status(self, use_cache: bool = True, max_age: int = None) -> dict:
        """Get firewall status with optimized caching."""
        if max_age is None:
            max_age = self.current_cache_duration

        # Try cache first if enabled
        if use_cache:
            cached_status = self._load_cached_status(max_age)
            if cached_status:
                return cached_status

        # Get fresh status
        status = self._get_fresh_status()

        # Cache the result
        self._cache_status(status)

        return status

    def invalidate_cache(self) -> None:
        """Invalidate the status cache to force fresh check."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()

            # Also invalidate the firewall detector's cache
            if hasattr(self.firewall_detector, "activity_tracker"):
                tracker = self.firewall_detector.activity_tracker
                activity_file = tracker.activity_file
                if activity_file.exists():
                    activity_file.unlink()

            self.cache_invalidated.emit("firewall_cache")
            self.logger.debug("Firewall status cache invalidated")

        except Exception as e:
            self.logger.error(f"Error invalidating cache: {e}")

    def add_status_callback(self, callback: Callable[[dict], None]):
        """Add a callback for status updates."""
        if callback not in self._status_callbacks:
            self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable[[dict], None]):
        """Remove a status callback."""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def start_monitoring(self) -> None:
        """Start optimized firewall status monitoring."""
        if self._monitoring_active:
            return

        try:
            # Start file watcher
            if self.file_watcher:
                self.file_watcher.start_watching()

            # Start normal timer
            self.normal_timer.start(10000)  # 10 seconds

            # Perform initial status check
            QTimer.singleShot(500, self._immediate_status_check)

            self._monitoring_active = True
            self.logger.info("Firewall status monitoring started")

        except Exception as e:
            self.logger.error(f"Error starting monitoring: {e}")

    def stop_monitoring(self) -> None:
        """Stop firewall status monitoring."""
        if not self._monitoring_active:
            return

        try:
            # Stop all timers
            self.fast_timer.stop()
            self.normal_timer.stop()

            # Stop file watcher
            if self.file_watcher:
                self.file_watcher.stop_watching()

            self._monitoring_active = False
            self.logger.info("Firewall status monitoring stopped")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")

    def force_refresh(self) -> None:
        """Force an immediate refresh of firewall status."""
        self.invalidate_cache()
        self._trigger_immediate_refresh()

    def get_performance_stats(self) -> dict:
        """Get performance statistics for monitoring."""
        file_watcher_active = bool(self.file_watcher and self.file_watcher.watching)

        if self._last_known_status:
            last_status = self._last_known_status.get("status_text", "Unknown")
        else:
            last_status = "None"

        stats = {
            "monitoring_active": self._monitoring_active,
            "cache_duration": self.current_cache_duration,
            "file_watcher_active": file_watcher_active,
            "last_status": last_status,
            "callbacks_registered": len(self._status_callbacks),
        }

        if self.file_watcher:
            stats.update(self.file_watcher.get_statistics())

        return stats


class FirewallStatusIntegration:
    """Integration helper for existing GUI components."""

    def __init__(self, main_window=None):
        self.main_window = main_window
        self.optimizer = FirewallStatusOptimizer()

        # Connect optimizer signals to GUI updates
        if main_window:
            self.optimizer.status_changed.connect(self._update_gui_status)
            self.optimizer.cache_invalidated.connect(self._on_cache_invalidated)

    def _update_gui_status(self, status: dict):
        """Update GUI when status changes."""
        has_method = hasattr(self.main_window, "update_firewall_status_card")
        if self.main_window and has_method:
            # Force immediate GUI update
            self.main_window._firewall_status_cache = status
            self.main_window.update_firewall_status_card()

    def _on_cache_invalidated(self, cache_type: str):
        """Handle cache invalidation."""
        has_cache = hasattr(self.main_window, "_firewall_status_cache")
        if self.main_window and has_cache:
            # Clear GUI cache
            self.main_window._firewall_status_cache = None

    def start_optimization(self):
        """Start the optimized monitoring."""
        self.optimizer.start_monitoring()

    def stop_optimization(self):
        """Stop the optimized monitoring."""
        self.optimizer.stop_monitoring()

    def force_refresh(self):
        """Force immediate status refresh."""
        self.optimizer.force_refresh()
