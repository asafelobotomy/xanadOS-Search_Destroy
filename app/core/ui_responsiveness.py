#!/usr/bin/env python3
"""GUI responsiveness improvements for xanadOS Search & Destroy
Provides non-blocking UI operations and smooth user experience
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QProgressBar


@dataclass
class UITask:
    """Represents a UI task to be executed."""

    task_id: str
    callback: callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    priority: int = 1  # Lower number = higher priority


class ResponsiveUI(QObject):
    """Manager for responsive UI operations.
    Prevents UI freezing during long-running operations.
    """

    # Signals for thread-safe UI updates
    update_progress = pyqtSignal(int, str)  # progress, message
    update_status = pyqtSignal(str)  # status message
    show_notification = pyqtSignal(str, str)  # title, message
    task_completed = pyqtSignal(str, object)  # task_id, result

    def __init__(self, main_window=None):
        """Initialize responsive UI manager.

        Args:
            main_window: Main application window
        """
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)

        # UI update timer for smooth animations
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._process_ui_updates)
        self.ui_timer.start(16)  # ~60 FPS

        # Task queue for background operations
        self.pending_tasks = []
        self.task_timer = QTimer()
        self.task_timer.timeout.connect(self._process_background_tasks)
        self.task_timer.start(50)  # Process tasks every 50ms

        # Animation manager
        self.animations = {}
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(33)  # ~30 FPS for animations

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect UI update signals."""
        self.update_progress.connect(self._handle_progress_update)
        self.update_status.connect(self._handle_status_update)
        self.show_notification.connect(self._handle_notification)
        self.task_completed.connect(self._handle_task_completion)

    def schedule_task(
        self, task_id: str, callback: Callable, *args, priority: int = 1, **kwargs
    ):
        """Schedule a background task.

        Args:
            task_id: Unique task identifier
            callback: Function to execute
            args: Function arguments
            priority: Task priority (lower = higher priority)
            kwargs: Function keyword arguments
        """
        task = UITask(task_id, callback, args, kwargs, priority)

        # Insert task based on priority
        inserted = False
        for i, existing_task in enumerate(self.pending_tasks):
            if priority < existing_task.priority:
                self.pending_tasks.insert(i, task)
                inserted = True
                break

        if not inserted:
            self.pending_tasks.append(task)

        self.logdebug(
            "Scheduled task '%s' with priority %d".replace(
                "%s", "{task_id, priority}"
            ).replace("%d", "{task_id, priority}")
        )

    def _process_background_tasks(self):
        """Process queued background tasks."""
        if not self.pending_tasks:
            return

        # Process one task per timer tick to maintain responsiveness
        task = self.pending_tasks.pop(0)

        try:
            start_time = time.time()
            result = task.callback(*task.args, **task.kwargs)
            execution_time = time.time() - start_time

            self.logger.debug(
                "Completed task '%s' in %.3fs", task.task_id, execution_time
            )

            # Emit completion signal
            self.task_completed.emit(task.task_id, result)

        except Exception:
            self.logerror(
                "Task '%s' failed: %s".replace("%s", "{task.task_id, e}").replace(
                    "%d", "{task.task_id, e}"
                )
            )
            self.task_completed.emit(task.task_id, None)

    def _process_ui_updates(self):
        """Process queued UI updates."""
        # Force processing of any pending events
        QApplication.processEvents()

    def _update_animations(self):
        """Update UI animations."""
        current_time = time.time()

        # Update progress bar animations
        for widget_id, animation in list(self.animations.items()):
            if animation["type"] == "progress_smooth":
                self._update_progress_animation(widget_id, animation, current_time)
            elif animation["type"] == "pulse":
                self._update_pulse_animation(widget_id, animation, current_time)

    def _update_progress_animation(
        self, widget_id: str, animation: dict, current_time: float
    ):
        """Update smooth progress bar animation."""
        widget = animation.get("widget")
        if not widget:
            return

        target_value = animation["target_value"]
        current_value = widget.value()

        if current_value != target_value:
            # Smooth interpolation
            diff = target_value - current_value
            step = max(1, abs(diff) // 10)  # Move 10% of remaining distance

            if diff > 0:
                new_value = min(target_value, current_value + step)
            else:
                new_value = max(target_value, current_value - step)

            widget.setValue(new_value)

    def _update_pulse_animation(
        self, widget_id: str, animation: dict, current_time: float
    ):
        """Update pulsing animation."""
        widget = animation.get("widget")
        if not widget:
            return

        # Calculate pulse opacity based on time
        pulse_duration = animation.get("duration", 2.0)
        phase = (current_time % pulse_duration) / pulse_duration
        # Smooth pulse between 0.5 and 1.0
        opacity = 0.5 + 0.5 * abs(2 * phase - 1)

        widget.setWindowOpacity(opacity)

    def smooth_progress_update(self, progress_bar: QProgressBar, target_value: int):
        """Update progress bar with smooth animation.

        Args:
            progress_bar: Progress bar widget
            target_value: Target progress value
        """
        widget_id = f"progress_{id(progress_bar)}"

        self.animations[widget_id] = {
            "type": "progress_smooth",
            "widget": progress_bar,
            "target_value": target_value,
            "start_time": time.time(),
        }

    def start_pulse_animation(self, widget, duration: float = 2.0):
        """Start pulsing animation on widget.

        Args:
            widget: Widget to animate
            duration: Pulse duration in seconds
        """
        widget_id = f"pulse_{id(widget)}"

        self.animations[widget_id] = {
            "type": "pulse",
            "widget": widget,
            "duration": duration,
            "start_time": time.time(),
        }

    def stop_animation(self, widget):
        """Stop animation on widget.

        Args:
            widget: Widget to stop animating
        """
        widget_id = f"progress_{id(widget)}"
        if widget_id in self.animations:
            del self.animations[widget_id]

        widget_id = f"pulse_{id(widget)}"
        if widget_id in self.animations:
            del self.animations[widget_id]

    def _handle_progress_update(self, progress: int, message: str):
        """Handle progress update signal."""
        if self.main_window and hasattr(self.main_window, "progress_bar"):
            self.smooth_progress_update(self.main_window.progress_bar, progress)

        if self.main_window and hasattr(self.main_window, "status_label"):
            self.main_window.status_label.setText(message)

    def _handle_status_update(self, status: str):
        """Handle status update signal."""
        if self.main_window and hasattr(self.main_window, "status_label"):
            self.main_window.status_label.setText(status)

    def _handle_notification(self, title: str, message: str):
        """Handle notification display."""
        self.loginfo(
            "Notification: %s - %s".replace("%s", "{title, message}").replace(
                "%d", "{title, message}"
            )
        )
        # Could integrate with system notifications here

    def _handle_task_completion(self, task_id: str, result: Any):
        """Handle task completion."""
        self.logdebug(
            "Task '%s' completed with result: %s".replace(
                "%s", "{task_id, result}"
            ).replace("%d", "{task_id, result}")
        )


class ScanProgressManager(QObject):
    """Manages scan progress display and updates."""

    # Signals for progress updates
    progress_updated = pyqtSignal(int, str, dict)  # progress, message, stats
    scan_completed = pyqtSignal(dict)  # final statistics
    error_occurred = pyqtSignal(str)  # error message

    def __init__(self):
        """Initialize scan progress manager."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Progress tracking
        self.total_files = 0
        self.scanned_files = 0
        self.infected_files = 0
        self.errors = 0
        self.start_time = 0

        # Update throttling
        self.last_update = 0
        self.update_interval = 0.1  # Update UI every 100ms max

    def start_scan(self, total_files: int):
        """Start scan progress tracking.

        Args:
            total_files: Total number of files to scan
        """
        self.total_files = total_files
        self.scanned_files = 0
        self.infected_files = 0
        self.errors = 0
        self.start_time: float = time.time()

        self.loginfo(
            "Started scan progress tracking for %d files".replace(
                "%s", "{total_files}"
            ).replace("%d", "{total_files}")
        )
        self._emit_progress_update()

    def update_progress(
        self,
        scanned: int = 1,
        infected: int = 0,
        errors: int = 0,
        current_file: str = "",
    ):
        """Update scan progress.

        Args:
            scanned: Number of files scanned (increment)
            infected: Number of infected files found (increment)
            errors: Number of errors encountered (increment)
            current_file: Currently scanning file
        """
        self.scanned_files += scanned
        self.infected_files += infected
        self.errors += errors

        # Throttle updates to prevent UI flooding
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self._emit_progress_update(current_file)
            self.last_update = current_time

    def _emit_progress_update(self, current_file: str = ""):
        """Emit progress update signal."""
        if self.total_files > 0:
            progress = int((self.scanned_files / self.total_files) * 100)
        else:
            progress = 0

        # Calculate scan statistics
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0 and self.scanned_files > 0:
            files_per_second = self.scanned_files / elapsed_time
            if files_per_second > 0:
                remaining_files = self.total_files - self.scanned_files
                eta_seconds = remaining_files / files_per_second
            else:
                eta_seconds = 0
        else:
            files_per_second = 0
            eta_seconds = 0

        # Format progress message
        if current_file:
            message = f"Scanning: {current_file}"
        else:
            message = f"Scanned {self.scanned_files} of {self.total_files} files"

        stats = {
            "scanned": self.scanned_files,
            "total": self.total_files,
            "infected": self.infected_files,
            "errors": self.errors,
            "elapsed_time": elapsed_time,
            "files_per_second": files_per_second,
            "eta_seconds": eta_seconds,
        }

        self.progress_updated.emit(progress, message, stats)

    def finish_scan(self):
        """Finish scan and emit final statistics."""
        final_stats = {
            "total_files": self.total_files,
            "scanned_files": self.scanned_files,
            "infected_files": self.infected_files,
            "errors": self.errors,
            "scan_time": time.time() - self.start_time,
        }

        self.scan_completed.emit(final_stats)
        self.loginfo(
            "Scan completed: %s".replace("%s", "{final_stats}").replace(
                "%d", "{final_stats}"
            )
        )

    def report_error(self, error_message: str):
        """Report scan error.

        Args:
            error_message: Error description
        """
        self.errors += 1
        self.error_occurred.emit(error_message)
        self.logerror(
            "Scan error: %s".replace("%s", "{error_message}").replace(
                "%d", "{error_message}"
            )
        )


class LoadingIndicator(QObject):
    """Manages loading indicators and busy states."""

    def __init__(self, main_window=None):
        """Initialize loading indicator.

        Args:
            main_window: Main application window
        """
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)

        # Loading states
        self.loading_operations = set()
        self.busy_cursor_active = False

    def start_loading(self, operation_id: str, message: str = "Loading..."):
        """Start loading indicator.

        Args:
            operation_id: Unique operation identifier
            message: Loading message to display
        """
        self.loading_operations.add(operation_id)

        if not self.busy_cursor_active:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.busy_cursor_active = True

        if self.main_window and hasattr(self.main_window, "status_label"):
            self.main_window.status_label.setText(message)

        self.logdebug(
            "Started loading for operation '%s'".replace(
                "%s", "{operation_id}"
            ).replace("%d", "{operation_id}")
        )

    def stop_loading(self, operation_id: str):
        """Stop loading indicator.

        Args:
            operation_id: Operation identifier to stop
        """
        self.loading_operations.discard(operation_id)

        if not self.loading_operations and self.busy_cursor_active:
            QApplication.restoreOverrideCursor()
            self.busy_cursor_active = False

        self.logdebug(
            "Stopped loading for operation '%s'".replace(
                "%s", "{operation_id}"
            ).replace("%d", "{operation_id}")
        )

    def is_loading(self, operation_id: str | None = None) -> bool:
        """Check if loading indicator is active.

        Args:
            operation_id: Specific operation to check (optional)

        Returns:
            True if loading is active
        """
        if operation_id:
            return operation_id in self.loading_operations
        return len(self.loading_operations) > 0


# Global instances
responsive_ui: Optional["ResponsiveUI"] = None
scan_progress: Optional["ScanProgressManager"] = None
loading_indicator: Optional["LoadingIndicator"] = None


def initialize_responsive_ui(main_window=None) -> None:
    """Initialize global responsive UI components."""
    global responsive_ui, scan_progress, loading_indicator

    responsive_ui = ResponsiveUI(main_window)  # type: ignore
    scan_progress = ScanProgressManager()  # type: ignore
    loading_indicator = LoadingIndicator(main_window)  # type: ignore

    # Connect progress manager to responsive UI
    if responsive_ui and scan_progress:
        scan_progress.progress_updated.connect(responsive_ui.update_progress)
        scan_progress.error_occurred.connect(
            lambda msg: responsive_ui.show_notification.emit("Scan Error", msg)
        )


def get_responsive_ui() -> Optional["ResponsiveUI"]:
    """Get global responsive UI instance."""
    return responsive_ui


def get_scan_progress() -> Optional["ScanProgressManager"]:
    """Get global scan progress manager."""
    return scan_progress


def get_loading_indicator() -> Optional["LoadingIndicator"]:
    """Get global loading indicator."""
    return loading_indicator
