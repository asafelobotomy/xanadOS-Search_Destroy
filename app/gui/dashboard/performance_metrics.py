"""Performance metrics dashboard widget.

Real-time visualization of system resource usage and scan performance metrics.
Integrates with Phase 1 IOMetrics tracking for comprehensive monitoring.

Phase 2, Task 2.1.2: Performance Metrics Dashboard
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import psutil

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QGroupBox,
        QPushButton,
        QComboBox,
        QGridLayout,
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal

    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

try:
    import pyqtgraph as pg
    import numpy as np

    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False


@dataclass
class SystemMetrics:
    """System resource usage metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_read_mbps: float
    disk_write_mbps: float

    # Per-core CPU usage (optional)
    cpu_per_core: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_total_mb": self.memory_total_mb,
            "disk_read_mbps": self.disk_read_mbps,
            "disk_write_mbps": self.disk_write_mbps,
            "cpu_per_core": self.cpu_per_core,
        }


@dataclass
class ScanMetrics:
    """Scanner performance metrics from IOMetrics integration."""

    timestamp: datetime
    throughput_mbps: float
    files_per_second: float
    avg_file_size_mb: float
    cache_hit_rate: float = 0.0
    active_workers: int = 0

    # Strategy usage distribution
    async_count: int = 0
    mmap_count: int = 0
    buffered_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "throughput_mbps": self.throughput_mbps,
            "files_per_second": self.files_per_second,
            "avg_file_size_mb": self.avg_file_size_mb,
            "cache_hit_rate": self.cache_hit_rate,
            "active_workers": self.active_workers,
            "async_count": self.async_count,
            "mmap_count": self.mmap_count,
            "buffered_count": self.buffered_count,
        }


@dataclass
class AlertThresholds:
    """Resource usage alert thresholds."""

    cpu_warning: float = 80.0  # %
    cpu_critical: float = 95.0  # %
    memory_warning: float = 85.0  # %
    memory_critical: float = 95.0  # %
    disk_warning_mbps: float = 100.0  # MB/s
    throughput_low_warning: float = 500.0  # MB/s (below this is slow)


class PerformanceMetricsWidget(QWidget):
    """Real-time performance metrics dashboard.

    Features:
    - System resource monitoring (CPU, memory, disk I/O)
    - Scan performance tracking (throughput, files/s)
    - Historical trends with configurable time ranges
    - Resource usage alerts
    - Integration with Phase 1 IOMetrics

    Signals:
        alert_triggered: Emitted when resource threshold exceeded
        metrics_updated: Emitted when metrics are refreshed
    """

    alert_triggered = pyqtSignal(str, float, float)  # metric_name, value, threshold
    metrics_updated = pyqtSignal()

    def __init__(
        self,
        max_history: int = 3600,  # 1 hour at 1s intervals
        update_interval_ms: int = 1000,  # 1 second
        parent: QWidget | None = None,
    ):
        """Initialize performance metrics widget.

        Args:
            max_history: Maximum number of data points to retain
            update_interval_ms: Update interval in milliseconds
            parent: Parent widget
        """
        super().__init__(parent)

        if not PYQT6_AVAILABLE:
            raise ImportError("PyQt6 is required for PerformanceMetricsWidget")

        if not PYQTGRAPH_AVAILABLE:
            raise ImportError("pyqtgraph is required for performance charts")

        self.max_history = max_history
        self.update_interval_ms = update_interval_ms

        # Data storage
        self.system_metrics: deque[SystemMetrics] = deque(maxlen=max_history)
        self.scan_metrics: deque[ScanMetrics] = deque(maxlen=max_history)

        # Alert thresholds
        self.thresholds = AlertThresholds()

        # Disk I/O counters for delta calculation
        self._last_disk_io = psutil.disk_io_counters()
        self._last_disk_time = datetime.now()

        # Setup UI
        self._setup_ui()

        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_metrics)
        self.update_timer.start(self.update_interval_ms)

        # Initial metrics collection
        self._update_metrics()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("⚡ System Performance Metrics")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        # Time range selector
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Time Range:"))

        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(
            ["1 min", "5 min", "15 min", "30 min", "1 hour", "All"]
        )
        self.time_range_combo.setCurrentText("5 min")
        self.time_range_combo.currentTextChanged.connect(self._on_time_range_changed)
        controls_layout.addWidget(self.time_range_combo)

        controls_layout.addStretch()

        # Clear history button
        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.clicked.connect(self.clear_history)
        controls_layout.addWidget(clear_btn)

        # Export button
        export_btn = QPushButton("💾 Export Data")
        export_btn.clicked.connect(self.export_data)
        controls_layout.addWidget(export_btn)

        layout.addLayout(controls_layout)

        # Statistics summary
        stats_group = QGroupBox("Current Statistics")
        stats_layout = QGridLayout(stats_group)

        # CPU stats
        stats_layout.addWidget(QLabel("<b>CPU:</b>"), 0, 0)
        self.cpu_label = QLabel("0.0%")
        stats_layout.addWidget(self.cpu_label, 0, 1)

        # Memory stats
        stats_layout.addWidget(QLabel("<b>Memory:</b>"), 0, 2)
        self.memory_label = QLabel("0.0%")
        stats_layout.addWidget(self.memory_label, 0, 3)

        # Disk I/O stats
        stats_layout.addWidget(QLabel("<b>Disk Read:</b>"), 1, 0)
        self.disk_read_label = QLabel("0.0 MB/s")
        stats_layout.addWidget(self.disk_read_label, 1, 1)

        stats_layout.addWidget(QLabel("<b>Disk Write:</b>"), 1, 2)
        self.disk_write_label = QLabel("0.0 MB/s")
        stats_layout.addWidget(self.disk_write_label, 1, 3)

        # Scan throughput stats
        stats_layout.addWidget(QLabel("<b>Scan Throughput:</b>"), 2, 0)
        self.throughput_label = QLabel("0.0 MB/s")
        stats_layout.addWidget(self.throughput_label, 2, 1)

        stats_layout.addWidget(QLabel("<b>Files/s:</b>"), 2, 2)
        self.files_per_sec_label = QLabel("0.0")
        stats_layout.addWidget(self.files_per_sec_label, 2, 3)

        layout.addWidget(stats_group)

        # Create charts if pyqtgraph available
        if PYQTGRAPH_AVAILABLE:
            # CPU & Memory chart
            cpu_mem_group = QGroupBox("CPU & Memory Usage")
            cpu_mem_layout = QVBoxLayout(cpu_mem_group)

            self.cpu_mem_plot = pg.PlotWidget()
            self.cpu_mem_plot.setLabel("left", "Usage (%)")
            self.cpu_mem_plot.setLabel("bottom", "Time (s)")
            self.cpu_mem_plot.setYRange(0, 100)
            self.cpu_mem_plot.addLegend()

            self.cpu_curve = self.cpu_mem_plot.plot(
                pen=pg.mkPen(color="r", width=2), name="CPU"
            )
            self.memory_curve = self.cpu_mem_plot.plot(
                pen=pg.mkPen(color="b", width=2), name="Memory"
            )

            cpu_mem_layout.addWidget(self.cpu_mem_plot)
            layout.addWidget(cpu_mem_group)

            # Disk I/O chart
            disk_group = QGroupBox("Disk I/O")
            disk_layout = QVBoxLayout(disk_group)

            self.disk_plot = pg.PlotWidget()
            self.disk_plot.setLabel("left", "Throughput (MB/s)")
            self.disk_plot.setLabel("bottom", "Time (s)")
            self.disk_plot.addLegend()

            self.disk_read_curve = self.disk_plot.plot(
                pen=pg.mkPen(color="g", width=2), name="Read"
            )
            self.disk_write_curve = self.disk_plot.plot(
                pen=pg.mkPen(color="orange", width=2), name="Write"
            )

            disk_layout.addWidget(self.disk_plot)
            layout.addWidget(disk_group)

            # Scan performance chart
            scan_group = QGroupBox("Scan Performance")
            scan_layout = QVBoxLayout(scan_group)

            self.scan_plot = pg.PlotWidget()
            self.scan_plot.setLabel("left", "Throughput (MB/s)")
            self.scan_plot.setLabel("bottom", "Time (s)")
            self.scan_plot.addLegend()

            self.scan_throughput_curve = self.scan_plot.plot(
                pen=pg.mkPen(color="cyan", width=2), name="Scan Throughput"
            )

            scan_layout.addWidget(self.scan_plot)
            layout.addWidget(scan_group)
        else:
            # Placeholder if pyqtgraph not available
            placeholder = QLabel("⚠️ pyqtgraph not installed - charts disabled")
            placeholder.setStyleSheet("color: orange; padding: 20px;")
            layout.addWidget(placeholder)

    def _update_metrics(self):
        """Update system and scan metrics."""
        now = datetime.now()

        # Collect system metrics
        cpu_percent = psutil.cpu_percent(interval=0)
        memory = psutil.virtual_memory()

        # Calculate disk I/O delta
        current_disk_io = psutil.disk_io_counters()
        time_delta = (now - self._last_disk_time).total_seconds()

        if time_delta > 0 and self._last_disk_io:
            bytes_read_delta = (
                current_disk_io.read_bytes - self._last_disk_io.read_bytes
            )
            bytes_write_delta = (
                current_disk_io.write_bytes - self._last_disk_io.write_bytes
            )

            disk_read_mbps = (bytes_read_delta / time_delta) / (1024 * 1024)
            disk_write_mbps = (bytes_write_delta / time_delta) / (1024 * 1024)
        else:
            disk_read_mbps = 0.0
            disk_write_mbps = 0.0

        self._last_disk_io = current_disk_io
        self._last_disk_time = now

        # Create system metrics record
        sys_metrics = SystemMetrics(
            timestamp=now,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_total_mb=memory.total / (1024 * 1024),
            disk_read_mbps=disk_read_mbps,
            disk_write_mbps=disk_write_mbps,
            cpu_per_core=psutil.cpu_percent(interval=0, percpu=True),
        )

        self.system_metrics.append(sys_metrics)

        # Update statistics labels
        self.cpu_label.setText(f"{cpu_percent:.1f}%")
        self.memory_label.setText(f"{memory.percent:.1f}%")
        self.disk_read_label.setText(f"{disk_read_mbps:.1f} MB/s")
        self.disk_write_label.setText(f"{disk_write_mbps:.1f} MB/s")

        # Check alert thresholds
        self._check_alerts(sys_metrics)

        # Update charts
        self._update_charts()

        # Emit signal
        self.metrics_updated.emit()

    def add_scan_metrics(
        self,
        throughput_mbps: float,
        files_per_second: float = 0.0,
        avg_file_size_mb: float = 0.0,
        cache_hit_rate: float = 0.0,
        active_workers: int = 0,
        async_count: int = 0,
        mmap_count: int = 0,
        buffered_count: int = 0,
    ):
        """Add scan performance metrics.

        This method should be called by the scanner engine to report
        performance metrics from Phase 1 IOMetrics tracking.

        Args:
            throughput_mbps: Scan throughput in MB/s
            files_per_second: Files processed per second
            avg_file_size_mb: Average file size in MB
            cache_hit_rate: Cache hit rate (0.0-1.0)
            active_workers: Number of active worker threads
            async_count: Number of async I/O operations
            mmap_count: Number of mmap operations
            buffered_count: Number of buffered I/O operations
        """
        metrics = ScanMetrics(
            timestamp=datetime.now(),
            throughput_mbps=throughput_mbps,
            files_per_second=files_per_second,
            avg_file_size_mb=avg_file_size_mb,
            cache_hit_rate=cache_hit_rate,
            active_workers=active_workers,
            async_count=async_count,
            mmap_count=mmap_count,
            buffered_count=buffered_count,
        )

        self.scan_metrics.append(metrics)

        # Update labels
        self.throughput_label.setText(f"{throughput_mbps:.1f} MB/s")
        self.files_per_sec_label.setText(f"{files_per_second:.1f}")

        # Update charts
        self._update_charts()

    def _update_charts(self):
        """Update all performance charts."""
        if not PYQTGRAPH_AVAILABLE or not self.system_metrics:
            return

        # Get time range filter
        time_range_text = self.time_range_combo.currentText()
        filtered_metrics = self._filter_by_time_range(time_range_text)

        if not filtered_metrics:
            return

        # Extract data arrays
        timestamps = [
            (m.timestamp - filtered_metrics[0].timestamp).total_seconds()
            for m in filtered_metrics
        ]
        cpu_data = [m.cpu_percent for m in filtered_metrics]
        memory_data = [m.memory_percent for m in filtered_metrics]
        disk_read_data = [m.disk_read_mbps for m in filtered_metrics]
        disk_write_data = [m.disk_write_mbps for m in filtered_metrics]

        # Update CPU & Memory chart
        self.cpu_curve.setData(timestamps, cpu_data)
        self.memory_curve.setData(timestamps, memory_data)

        # Update Disk I/O chart
        self.disk_read_curve.setData(timestamps, disk_read_data)
        self.disk_write_curve.setData(timestamps, disk_write_data)

        # Update Scan Performance chart (if scan metrics available)
        if self.scan_metrics:
            filtered_scan = self._filter_scan_by_time_range(time_range_text)
            if filtered_scan:
                scan_timestamps = [
                    (m.timestamp - filtered_scan[0].timestamp).total_seconds()
                    for m in filtered_scan
                ]
                scan_throughput = [m.throughput_mbps for m in filtered_scan]
                self.scan_throughput_curve.setData(scan_timestamps, scan_throughput)

    def _filter_by_time_range(self, time_range: str) -> list[SystemMetrics]:
        """Filter metrics by time range."""
        if time_range == "All" or not self.system_metrics:
            return list(self.system_metrics)

        # Parse time range
        time_map = {
            "1 min": timedelta(minutes=1),
            "5 min": timedelta(minutes=5),
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 hour": timedelta(hours=1),
        }

        delta = time_map.get(time_range, timedelta(minutes=5))
        cutoff = datetime.now() - delta

        return [m for m in self.system_metrics if m.timestamp >= cutoff]

    def _filter_scan_by_time_range(self, time_range: str) -> list[ScanMetrics]:
        """Filter scan metrics by time range."""
        if time_range == "All" or not self.scan_metrics:
            return list(self.scan_metrics)

        time_map = {
            "1 min": timedelta(minutes=1),
            "5 min": timedelta(minutes=5),
            "15 min": timedelta(minutes=15),
            "30 min": timedelta(minutes=30),
            "1 hour": timedelta(hours=1),
        }

        delta = time_map.get(time_range, timedelta(minutes=5))
        cutoff = datetime.now() - delta

        return [m for m in self.scan_metrics if m.timestamp >= cutoff]

    def _on_time_range_changed(self, time_range: str):
        """Handle time range selection change."""
        self._update_charts()

    def _check_alerts(self, metrics: SystemMetrics):
        """Check if any metrics exceed alert thresholds."""
        # CPU alerts
        if metrics.cpu_percent >= self.thresholds.cpu_critical:
            self.alert_triggered.emit(
                "CPU", metrics.cpu_percent, self.thresholds.cpu_critical
            )
        elif metrics.cpu_percent >= self.thresholds.cpu_warning:
            self.alert_triggered.emit(
                "CPU", metrics.cpu_percent, self.thresholds.cpu_warning
            )

        # Memory alerts
        if metrics.memory_percent >= self.thresholds.memory_critical:
            self.alert_triggered.emit(
                "Memory", metrics.memory_percent, self.thresholds.memory_critical
            )
        elif metrics.memory_percent >= self.thresholds.memory_warning:
            self.alert_triggered.emit(
                "Memory", metrics.memory_percent, self.thresholds.memory_warning
            )

        # Disk I/O alerts
        total_disk_io = metrics.disk_read_mbps + metrics.disk_write_mbps
        if total_disk_io >= self.thresholds.disk_warning_mbps:
            self.alert_triggered.emit(
                "Disk I/O", total_disk_io, self.thresholds.disk_warning_mbps
            )

    def clear_history(self):
        """Clear all historical metrics."""
        self.system_metrics.clear()
        self.scan_metrics.clear()
        self._update_charts()

    def export_data(self):
        """Export metrics data to JSON."""
        # Placeholder for export functionality
        # TODO: Implement CSV/JSON export
        print("Export functionality - TODO")

    def get_current_system_metrics(self) -> SystemMetrics | None:
        """Get the most recent system metrics."""
        return self.system_metrics[-1] if self.system_metrics else None

    def get_current_scan_metrics(self) -> ScanMetrics | None:
        """Get the most recent scan metrics."""
        return self.scan_metrics[-1] if self.scan_metrics else None

    def get_average_cpu(self, minutes: int = 5) -> float:
        """Get average CPU usage over last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [m.cpu_percent for m in self.system_metrics if m.timestamp >= cutoff]
        return sum(recent) / len(recent) if recent else 0.0

    def get_average_memory(self, minutes: int = 5) -> float:
        """Get average memory usage over last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [
            m.memory_percent for m in self.system_metrics if m.timestamp >= cutoff
        ]
        return sum(recent) / len(recent) if recent else 0.0

    def get_average_throughput(self, minutes: int = 5) -> float:
        """Get average scan throughput over last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [m.throughput_mbps for m in self.scan_metrics if m.timestamp >= cutoff]
        return sum(recent) / len(recent) if recent else 0.0
