#!/usr/bin/env python3
"""
Performance Metrics Dashboard Demo - Task 2.1.2

Demonstrates the PerformanceMetricsWidget with:
- Real-time system monitoring (CPU, memory, disk I/O via psutil)
- Scanner performance tracking (simulated scan metrics)
- Alert system (configurable thresholds)
- Time range filtering (1min, 5min, 15min, 30min, 1hour)
- Historical analysis (average CPU, memory, throughput)

This demo showcases the integration between Phase 1's IOMetrics
and Phase 2's real-time performance monitoring.

Usage:
    python examples/performance_dashboard_demo.py
"""

import sys
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QLabel,
)
from PyQt6.QtCore import QTimer, Qt
from app.gui.dashboard.performance_metrics import PerformanceMetricsWidget
import random


class PerformanceDashboardDemo(QMainWindow):
    """Demo window showing PerformanceMetricsWidget with simulated scan activity."""

    def __init__(self):
        """Initialize the demo window."""
        super().__init__()
        self.setWindowTitle("Performance Metrics Dashboard - Task 2.1.2 Demo")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add title
        title = QLabel("Performance Metrics Dashboard - Real-time Monitoring")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Create performance metrics widget
        self.metrics_widget = PerformanceMetricsWidget(
            max_history=3600,  # 1 hour of history
            update_interval_ms=1000,  # Update every second
        )
        layout.addWidget(self.metrics_widget)

        # Connect alert signal
        self.metrics_widget.alert_triggered.connect(self.on_alert)

        # Add control buttons
        button_layout = QHBoxLayout()

        self.scan_button = QPushButton("🔍 Simulate Scan Activity")
        self.scan_button.clicked.connect(self.toggle_scan_simulation)
        self.scan_button.setStyleSheet("padding: 10px; font-size: 14px;")
        button_layout.addWidget(self.scan_button)

        clear_button = QPushButton("🗑️ Clear History")
        clear_button.clicked.connect(self.metrics_widget.clear_history)
        clear_button.setStyleSheet("padding: 10px; font-size: 14px;")
        button_layout.addWidget(clear_button)

        export_button = QPushButton("💾 Export Data")
        export_button.clicked.connect(self.metrics_widget.export_data)
        export_button.setStyleSheet("padding: 10px; font-size: 14px;")
        button_layout.addWidget(export_button)

        layout.addLayout(button_layout)

        # Add status bar
        self.status_label = QLabel("Status: Ready - System metrics updating every 1s")
        self.status_label.setStyleSheet(
            "padding: 5px; background-color: #e8f5e9; border-radius: 3px;"
        )
        layout.addWidget(self.status_label)

        # Timer for simulated scan activity
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.simulate_scan_metrics)
        self.scan_active = False
        self.scan_iteration = 0

        # Show initial statistics
        QTimer.singleShot(2000, self.show_initial_stats)

    def toggle_scan_simulation(self):
        """Toggle simulated scan activity."""
        if self.scan_active:
            # Stop simulation
            self.scan_timer.stop()
            self.scan_active = False
            self.scan_button.setText("🔍 Simulate Scan Activity")
            self.status_label.setText(
                "Status: Scan simulation stopped - System metrics only"
            )
            self.status_label.setStyleSheet(
                "padding: 5px; background-color: #e8f5e9; border-radius: 3px;"
            )
        else:
            # Start simulation
            self.scan_timer.start(1500)  # Update every 1.5 seconds
            self.scan_active = True
            self.scan_iteration = 0
            self.scan_button.setText("⏸️ Stop Scan Simulation")
            self.status_label.setText(
                "Status: Simulating high-performance scan activity..."
            )
            self.status_label.setStyleSheet(
                "padding: 5px; background-color: #fff3e0; border-radius: 3px;"
            )

    def simulate_scan_metrics(self):
        """Simulate realistic scan performance metrics."""
        self.scan_iteration += 1

        # Simulate varying scan workload patterns
        if self.scan_iteration < 10:
            # Initial ramp-up phase
            base_throughput = 500 + (self.scan_iteration * 200)
            base_files_per_sec = 100 + (self.scan_iteration * 50)
            cache_hit_rate = 0.1 + (self.scan_iteration * 0.05)
        elif self.scan_iteration < 40:
            # Sustained high-performance phase
            base_throughput = 2500
            base_files_per_sec = 800
            cache_hit_rate = 0.75
        elif self.scan_iteration < 50:
            # Cool-down phase
            remaining = 50 - self.scan_iteration
            base_throughput = 500 + (remaining * 40)
            base_files_per_sec = 100 + (remaining * 15)
            cache_hit_rate = 0.3 + (remaining * 0.009)
        else:
            # Reset cycle
            self.scan_iteration = 0
            base_throughput = 500
            base_files_per_sec = 100
            cache_hit_rate = 0.1

        # Add realistic variation
        throughput = base_throughput + random.uniform(-100, 200)
        files_per_sec = base_files_per_sec + random.uniform(-20, 40)
        cache_hit_rate = min(
            0.95, max(0.05, cache_hit_rate + random.uniform(-0.05, 0.05))
        )

        # Simulate varying file sizes
        avg_file_size = random.uniform(0.5, 8.0)

        # Simulate I/O strategy distribution based on file size
        if avg_file_size < 1.0:
            # Small files: prefer buffered I/O
            async_count = random.randint(50, 150)
            mmap_count = random.randint(10, 50)
            buffered_count = random.randint(200, 500)
        elif avg_file_size < 5.0:
            # Medium files: balanced strategy
            async_count = random.randint(100, 300)
            mmap_count = random.randint(100, 300)
            buffered_count = random.randint(100, 300)
        else:
            # Large files: prefer mmap
            async_count = random.randint(50, 150)
            mmap_count = random.randint(300, 600)
            buffered_count = random.randint(50, 150)

        # Simulate active workers based on scan intensity
        active_workers = random.randint(2, 8)

        # Add scan metrics to widget
        self.metrics_widget.add_scan_metrics(
            throughput_mbps=throughput,
            files_per_second=files_per_sec,
            avg_file_size_mb=avg_file_size,
            cache_hit_rate=cache_hit_rate,
            active_workers=active_workers,
            async_count=async_count,
            mmap_count=mmap_count,
            buffered_count=buffered_count,
        )

        # Update status with current metrics
        self.status_label.setText(
            f"Status: Scanning - {throughput:.1f} MB/s, "
            f"{files_per_sec:.0f} files/s, "
            f"{cache_hit_rate*100:.1f}% cache hits, "
            f"{active_workers} workers"
        )

    def on_alert(self, metric_name: str, value: float, threshold: float):
        """Handle alert triggered by metrics widget."""
        alert_text = (
            f"⚠️ ALERT: {metric_name} = {value:.1f} (threshold: {threshold:.1f})"
        )
        self.status_label.setText(alert_text)
        self.status_label.setStyleSheet(
            "padding: 5px; background-color: #ffebee; border-radius: 3px; color: #c62828;"
        )
        print(f"\n{alert_text}")

        # Reset to normal color after 3 seconds
        QTimer.singleShot(3000, self.reset_status_color)

    def reset_status_color(self):
        """Reset status bar to normal color."""
        if self.scan_active:
            self.status_label.setStyleSheet(
                "padding: 5px; background-color: #fff3e0; border-radius: 3px;"
            )
        else:
            self.status_label.setStyleSheet(
                "padding: 5px; background-color: #e8f5e9; border-radius: 3px;"
            )

    def show_initial_stats(self):
        """Display initial system statistics."""
        current_metrics = self.metrics_widget.get_current_system_metrics()
        if current_metrics:
            print("\n=== Initial System Metrics ===")
            print(f"CPU: {current_metrics.cpu_percent:.1f}%")
            print(
                f"Memory: {current_metrics.memory_percent:.1f}% "
                f"({current_metrics.memory_used_mb:.0f} MB / {current_metrics.memory_total_mb:.0f} MB)"
            )
            print(f"Disk Read: {current_metrics.disk_read_mbps:.2f} MB/s")
            print(f"Disk Write: {current_metrics.disk_write_mbps:.2f} MB/s")

            if current_metrics.cpu_per_core:
                print(
                    f"Per-core CPU: {', '.join([f'{c:.1f}%' for c in current_metrics.cpu_per_core])}"
                )

        # Show feature summary
        print("\n=== Performance Dashboard Features ===")
        print("✅ Real-time system monitoring (psutil integration)")
        print("✅ Three interactive charts (CPU/Memory, Disk I/O, Scan Performance)")
        print("✅ Time range filtering (1min, 5min, 15min, 30min, 1hour)")
        print("✅ Alert system (configurable CPU/memory/disk thresholds)")
        print("✅ Scanner integration (Phase 1 IOMetrics tracking)")
        print("✅ Historical analysis (average calculations over time)")
        print("✅ Circular buffer (max_history=3600 prevents memory bloat)")
        print("\nClick '🔍 Simulate Scan Activity' to see scanner performance metrics!")


def main():
    """Run the performance dashboard demo."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show demo window
    demo = PerformanceDashboardDemo()
    demo.show()

    print("=== Performance Metrics Dashboard Demo - Task 2.1.2 ===")
    print("Window opened - showing real-time system monitoring")
    print("\nFeatures demonstrated:")
    print("1. System Metrics: CPU, memory, disk I/O (via psutil)")
    print("2. Scan Metrics: Throughput, files/s, cache hits, I/O strategies")
    print("3. Alert System: Configurable thresholds with visual/signal alerts")
    print("4. Time Filtering: 1min, 5min, 15min, 30min, 1hour views")
    print("5. Historical Trends: Average calculations over time windows")
    print("\nInteractive Controls:")
    print("- Time Range Selector: Filter charts by time window")
    print("- Simulate Scan Activity: Add realistic scanner metrics")
    print("- Clear History: Reset all stored metrics")
    print("- Export Data: Save metrics to CSV/JSON (placeholder)")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
