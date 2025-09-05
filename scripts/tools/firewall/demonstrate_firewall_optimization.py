#!/usr/bin/env python3
"""
Firewall Status Optimization Demonstration
==========================================

This script demonstrates the improved firewall status monitoring system
with immediate updates and minimal performance impact.

Usage:
    python demonstrate_firewall_optimization.py

Requirements:
    - PyQt6
    - Linux system with firewall (ufw, firewalld, etc.)
    - inotify support (for file monitoring)
"""

import logging
import sys
import time
from typing import Any

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app.core.firewall_detector import FirewallDetector
    from app.core.firewall_status_optimizer import FirewallStatusOptimizer
except ImportError as e:
    logger.error(f"Failed to import firewall modules: {e}")
    sys.exit(1)


class FirewallStatusDemo(QMainWindow):
    """Demonstration window showing optimized firewall status monitoring."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Firewall Status Optimization Demo")
        self.setGeometry(100, 100, 800, 600)

        # Initialize components
        self.firewall_detector = FirewallDetector()
        self.optimizer = FirewallStatusOptimizer(self.firewall_detector)

        # UI setup
        self.setup_ui()

        # Connect optimizer signals
        self.optimizer.status_changed.connect(self.on_status_changed)
        self.optimizer.cache_invalidated.connect(self.on_cache_invalidated)

        # Start monitoring
        self.optimizer.start_monitoring()

        # Update display timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second

        logger.info("Firewall status demo initialized")

    def setup_ui(self) -> None:
        """Set up the demonstration UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Status display
        self.status_label = QLabel("Firewall Status: Checking...")
        self.status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; padding: 10px;"
        )
        layout.addWidget(self.status_label)

        # Performance stats
        self.stats_label = QLabel("Performance Statistics:")
        layout.addWidget(self.stats_label)

        # Event log
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # Control buttons
        self.refresh_button = QPushButton("Force Refresh")
        self.refresh_button.clicked.connect(self.force_refresh)
        layout.addWidget(self.refresh_button)

        self.test_button = QPushButton("Simulate Firewall Change")
        self.test_button.clicked.connect(self.simulate_change)
        layout.addWidget(self.test_button)

    def on_status_changed(self, status: dict[str, Any]) -> None:
        """Handle firewall status changes."""
        timestamp = time.strftime("%H:%M:%S")
        status_text = status.get("status_text", "Unknown")
        firewall_name = status.get("firewall_name", "Unknown")

        # Update status display
        self.status_label.setText(f"Firewall Status: {status_text}")

        # Update status color
        if status.get("is_active", False):
            color = "green"
        else:
            color = "red"

        style = f"font-size: 16px; font-weight: bold; padding: 10px; color: {color};"
        self.status_label.setStyleSheet(style)

        # Log the change
        change_msg = f"Status changed: {firewall_name} - {status_text}"
        log_msg = f"[{timestamp}] {change_msg}"
        self.log_text.append(log_msg)

        logger.info(f"Status update: {status_text}")

    def on_cache_invalidated(self, cache_type: str) -> None:
        """Handle cache invalidation events."""
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] Cache invalidated: {cache_type}"
        self.log_text.append(log_msg)

        logger.info(f"Cache invalidated: {cache_type}")

    def update_display(self) -> None:
        """Update the performance statistics display."""
        try:
            stats = self.optimizer.get_performance_stats()

            stats_text = f"""Performance Statistics:
Monitoring Active: {stats.get("monitoring_active", False)}
Cache Duration: {stats.get("cache_duration", 0)}s
File Watcher Active: {stats.get("file_watcher_active", False)}
Last Status: {stats.get("last_status", "None")}
Callbacks Registered: {stats.get("callbacks_registered", 0)}"""

            if "events_processed" in stats:
                stats_text += f"\nEvents Processed: {stats['events_processed']}"

            if "uptime_seconds" in stats:
                uptime = stats["uptime_seconds"]
                stats_text += f"\nUptime: {uptime:.1f}s"

            self.stats_label.setText(stats_text)

        except Exception as e:
            logger.error(f"Error updating display: {e}")

    def force_refresh(self) -> None:
        """Force an immediate firewall status refresh."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] Manual refresh triggered")

        self.optimizer.force_refresh()
        logger.info("Manual refresh triggered")

    def simulate_change(self) -> None:
        """Simulate a firewall configuration change."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] Simulating firewall change...")

        # Invalidate cache to simulate a configuration change
        self.optimizer.invalidate_cache()

        # Trigger immediate refresh
        QTimer.singleShot(500, self.optimizer.force_refresh)

        logger.info("Simulated firewall change")

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Handle window close event."""
        logger.info("Shutting down firewall status demo")

        # Stop monitoring
        self.optimizer.stop_monitoring()

        # Stop timer
        self.update_timer.stop()

        if event is not None:
            event.accept()


def main() -> int:
    """Run the firewall status optimization demonstration."""
    print("Firewall Status Optimization Demonstration")
    print("==========================================")
    print()
    print("This demo shows the optimized firewall status monitoring system.")
    print("Key features demonstrated:")
    print("- Event-driven status updates")
    print("- Intelligent caching with fast/normal modes")
    print("- File system monitoring for immediate change detection")
    print("- Performance statistics and monitoring")
    print()
    print("Instructions:")
    print("1. Observe the current firewall status")
    print("2. Use 'Force Refresh' to manually update status")
    print("3. Use 'Simulate Change' to test cache invalidation")
    print("4. Change firewall state externally (e.g., 'sudo ufw enable/disable')")
    print("5. Watch for immediate status updates in the demo window")
    print()

    app = QApplication(sys.argv)

    try:
        demo = FirewallStatusDemo()
        demo.show()

        print("Demo window opened. Monitor the GUI for status changes.")
        print("Try changing your firewall status and watch for immediate updates!")

        return app.exec()

    except Exception as e:
        logger.error(f"Failed to start demo: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
