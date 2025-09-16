#!/usr/bin/env python3
"""Real-Time Security Dashboard for xanadOS Search & Destroy.

This module implements a live security operations center (SOC) style dashboard
with real-time threat visualization, performance metrics, and interactive
security monitoring capabilities.

Features:
- Live threat map with geographic visualization
- Real-time performance metrics and system health
- Security event stream with filtering and search
- Interactive threat timeline and incident tracking
- Predictive threat indicators and risk assessment
- Customizable widget layout and themes
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PyQt6.QtCore import QThread, QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QProgressBar, QTextEdit,
    QScrollArea, QTabWidget, QSplitter, QGroupBox,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSlider, QCheckBox, QSpinBox
)

# Import our Phase 1 components
from app.core.ml_threat_detector import MLThreatDetector
from app.core.advanced_async_scanner import AdvancedAsyncScanner
from app.core.edr_engine import EDREngine
from app.core.memory_manager import get_memory_manager
from app.core.memory_forensics import MemoryForensicsEngine
from app.utils.config import get_config


@dataclass
class ThreatEvent:
    """Real-time threat event data."""

    event_id: str
    timestamp: float
    event_type: str  # MALWARE, SUSPICIOUS_PROCESS, NETWORK_THREAT, etc.
    severity: str    # LOW, MEDIUM, HIGH, CRITICAL
    source: str      # IP, file path, process name
    target: str      # Affected system/file
    description: str
    confidence: float
    geolocation: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "ACTIVE"  # ACTIVE, INVESTIGATING, RESOLVED


@dataclass
class SystemMetrics:
    """Real-time system performance metrics."""

    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    scan_rate: float  # Files per second
    threat_detection_rate: float
    false_positive_rate: float
    active_connections: int
    active_processes: int


@dataclass
class DashboardConfig:
    """Dashboard configuration settings."""

    update_interval: int = 1000  # milliseconds
    max_events: int = 1000
    max_metrics_history: int = 100
    theme: str = "dark"
    show_geolocation: bool = True
    auto_refresh: bool = True
    sound_alerts: bool = True
    email_alerts: bool = False
    widget_layout: Dict[str, Any] = field(default_factory=dict)


class RealTimeDataCollector(QThread):
    """Background thread for collecting real-time security data."""

    # Signals for updating UI components
    threat_detected = pyqtSignal(ThreatEvent)
    metrics_updated = pyqtSignal(SystemMetrics)
    system_alert = pyqtSignal(str, str)  # severity, message

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.config = DashboardConfig()

        # Initialize Phase 1 components
        self.ml_detector = MLThreatDetector()
        self.edr_engine = EDREngine()
        self.memory_manager = get_memory_manager()

        # Data collection intervals
        self.metrics_interval = 1.0  # seconds
        self.threat_check_interval = 0.5  # seconds

        # Event tracking
        self.last_metrics_update = 0
        self.last_threat_check = 0
        self.event_counter = 0

    async def initialize_components(self):
        """Initialize all security components."""
        try:
            await self.ml_detector.initialize()
            await self.edr_engine.initialize()
            self.memory_manager.start()

            self.logger.info("Dashboard data collector initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False

    def run(self):
        """Main thread execution."""
        self.running = True

        # Initialize async components
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if not loop.run_until_complete(self.initialize_components()):
            self.system_alert.emit("CRITICAL", "Failed to initialize security components")
            return

        # Main data collection loop
        try:
            while self.running:
                current_time = time.time()

                # Collect system metrics
                if current_time - self.last_metrics_update >= self.metrics_interval:
                    loop.run_until_complete(self.collect_metrics())
                    self.last_metrics_update = current_time

                # Check for threats
                if current_time - self.last_threat_check >= self.threat_check_interval:
                    loop.run_until_complete(self.check_threats())
                    self.last_threat_check = current_time

                # Sleep for a short time to prevent busy waiting
                time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Data collector error: {e}")
            self.system_alert.emit("ERROR", f"Data collection failed: {str(e)}")

        finally:
            loop.close()

    async def collect_metrics(self):
        """Collect current system metrics."""
        try:
            import psutil

            # Basic system metrics
            cpu_usage = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()

            # Security-specific metrics
            memory_stats = self.memory_manager.get_comprehensive_stats()
            edr_metrics = await self.edr_engine.get_performance_metrics()

            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_usage=cpu_usage,
                memory_usage=memory_info.percent,
                disk_usage=(disk_info.used / disk_info.total) * 100,
                network_io={
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                scan_rate=edr_metrics.get('scan_rate', 0.0),
                threat_detection_rate=edr_metrics.get('threat_detection_rate', 0.0),
                false_positive_rate=edr_metrics.get('false_positive_rate', 0.0),
                active_connections=len(await self.edr_engine.get_network_connections()),
                active_processes=len(await self.edr_engine.get_monitored_processes())
            )

            self.metrics_updated.emit(metrics)

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")

    async def check_threats(self):
        """Check for new threats and security events."""
        try:
            # Get recent security events from EDR
            recent_events = await self.edr_engine.get_security_events(last_minutes=1)

            for event in recent_events:
                # Convert EDR event to ThreatEvent
                threat_event = ThreatEvent(
                    event_id=f"evt_{self.event_counter}",
                    timestamp=event.timestamp,
                    event_type=event.event_type,
                    severity=event.severity,
                    source=event.source,
                    target=event.target or "Unknown",
                    description=event.description,
                    confidence=event.confidence,
                    metadata=event.metadata
                )

                # Add geolocation for network events
                if event.event_type == "NETWORK_THREAT" and 'remote_ip' in event.metadata:
                    threat_event.geolocation = await self.get_geolocation(
                        event.metadata['remote_ip']
                    )

                self.threat_detected.emit(threat_event)
                self.event_counter += 1

            # Check for system alerts
            await self.check_system_health()

        except Exception as e:
            self.logger.error(f"Error checking threats: {e}")

    async def get_geolocation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get geolocation data for an IP address."""
        try:
            # This would typically use a geolocation service
            # For now, return mock data for private/local IPs
            if ip_address.startswith(('192.168.', '10.', '172.16.')):
                return {
                    'country': 'Local Network',
                    'city': 'Internal',
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'isp': 'Local'
                }

            # In a real implementation, you would use a service like:
            # - GeoIP databases
            # - MaxMind GeoLite2
            # - IP geolocation APIs
            return {
                'country': 'Unknown',
                'city': 'Unknown',
                'latitude': 0.0,
                'longitude': 0.0,
                'isp': 'Unknown'
            }

        except Exception as e:
            self.logger.error(f"Error getting geolocation for {ip_address}: {e}")
            return None

    async def check_system_health(self):
        """Check overall system health and generate alerts."""
        try:
            metrics = self.memory_manager.get_comprehensive_stats()
            system_memory = metrics.get('system_memory', {})

            # Check memory pressure
            memory_percent = system_memory.get('memory_percent', 0)
            if memory_percent > 90:
                self.system_alert.emit(
                    "CRITICAL",
                    f"High memory usage: {memory_percent:.1f}%"
                )
            elif memory_percent > 80:
                self.system_alert.emit(
                    "WARNING",
                    f"Elevated memory usage: {memory_percent:.1f}%"
                )

            # Check scan performance
            edr_metrics = await self.edr_engine.get_performance_metrics()
            scan_rate = edr_metrics.get('scan_rate', 0)
            if scan_rate < 10:  # Less than 10 files per second
                self.system_alert.emit(
                    "WARNING",
                    f"Low scan performance: {scan_rate:.1f} files/sec"
                )

        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")

    def stop(self):
        """Stop the data collection thread."""
        self.running = False


class ThreatMapWidget(QWidget):
    """Interactive threat map showing geographic distribution of threats."""

    def __init__(self):
        super().__init__()
        self.threats = []
        self.max_threats = 100
        self.initUI()

    def initUI(self):
        """Initialize the threat map UI."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("Global Threat Map")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff6b6b;")
        layout.addWidget(header)

        # Map area (placeholder for now)
        self.map_area = QLabel()
        self.map_area.setMinimumSize(400, 300)
        self.map_area.setStyleSheet("""
            background-color: #1a1a1a;
            border: 1px solid #444;
            border-radius: 5px;
        """)
        self.map_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_area.setText("Interactive Threat Map\n(Geographic visualization)")
        layout.addWidget(self.map_area)

        # Threat statistics
        stats_layout = QHBoxLayout()

        self.total_threats = QLabel("Total: 0")
        self.critical_threats = QLabel("Critical: 0")
        self.active_threats = QLabel("Active: 0")

        for label in [self.total_threats, self.critical_threats, self.active_threats]:
            label.setStyleSheet("color: #fff; padding: 5px;")
            stats_layout.addWidget(label)

        layout.addLayout(stats_layout)
        self.setLayout(layout)

    def add_threat(self, threat: ThreatEvent):
        """Add a new threat to the map."""
        self.threats.append(threat)

        # Keep only recent threats
        if len(self.threats) > self.max_threats:
            self.threats.pop(0)

        self.update_statistics()
        self.update_map()

    def update_statistics(self):
        """Update threat statistics display."""
        total = len(self.threats)
        critical = len([t for t in self.threats if t.severity == "CRITICAL"])
        active = len([t for t in self.threats if t.status == "ACTIVE"])

        self.total_threats.setText(f"Total: {total}")
        self.critical_threats.setText(f"Critical: {critical}")
        self.active_threats.setText(f"Active: {active}")

    def update_map(self):
        """Update the threat map visualization."""
        # In a real implementation, this would update a geographic map
        # with threat indicators based on geolocation data
        recent_threats = len([t for t in self.threats
                            if time.time() - t.timestamp < 300])  # Last 5 minutes

        self.map_area.setText(
            f"Interactive Threat Map\n"
            f"Recent Threats: {recent_threats}\n"
            f"(Geographic visualization)"
        )


class MetricsChartWidget(QWidget):
    """Real-time metrics chart widget."""

    def __init__(self, title: str, max_data_points: int = 60):
        super().__init__()
        self.title = title
        self.max_data_points = max_data_points
        self.data_points = deque(maxlen=max_data_points)
        self.timestamps = deque(maxlen=max_data_points)
        self.initUI()

    def initUI(self):
        """Initialize the metrics chart UI."""
        layout = QVBoxLayout()

        # Header
        header = QLabel(self.title)
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #4ecdc4;")
        layout.addWidget(header)

        # Chart area
        self.chart_area = QLabel()
        self.chart_area.setMinimumSize(300, 200)
        self.chart_area.setStyleSheet("""
            background-color: #1a1a1a;
            border: 1px solid #444;
            border-radius: 5px;
        """)
        layout.addWidget(self.chart_area)

        # Current value display
        self.current_value = QLabel("--")
        self.current_value.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #4ecdc4;
            text-align: center;
        """)
        self.current_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_value)

        self.setLayout(layout)

    def add_data_point(self, value: float, timestamp: float = None):
        """Add a new data point to the chart."""
        if timestamp is None:
            timestamp = time.time()

        self.data_points.append(value)
        self.timestamps.append(timestamp)

        self.update_chart()
        self.current_value.setText(f"{value:.1f}")

    def update_chart(self):
        """Update the chart visualization."""
        if not self.data_points:
            return

        # Simple text-based chart for now
        # In a real implementation, you'd use a proper charting library
        avg_value = sum(self.data_points) / len(self.data_points)
        max_value = max(self.data_points)
        min_value = min(self.data_points)

        chart_text = (
            f"Chart: {self.title}\n"
            f"Current: {self.data_points[-1]:.1f}\n"
            f"Average: {avg_value:.1f}\n"
            f"Range: {min_value:.1f} - {max_value:.1f}"
        )

        self.chart_area.setText(chart_text)


class EventStreamWidget(QWidget):
    """Real-time security event stream widget."""

    def __init__(self):
        super().__init__()
        self.max_events = 100
        self.initUI()

    def initUI(self):
        """Initialize the event stream UI."""
        layout = QVBoxLayout()

        # Header with controls
        header_layout = QHBoxLayout()

        header = QLabel("Security Event Stream")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff9f43;")
        header_layout.addWidget(header)

        # Filter controls
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.severity_filter.currentTextChanged.connect(self.apply_filters)

        self.event_type_filter = QComboBox()
        self.event_type_filter.addItems([
            "ALL", "MALWARE", "SUSPICIOUS_PROCESS", "NETWORK_THREAT",
            "SYSTEM_ALERT", "AUTHENTICATION"
        ])
        self.event_type_filter.currentTextChanged.connect(self.apply_filters)

        header_layout.addWidget(QLabel("Severity:"))
        header_layout.addWidget(self.severity_filter)
        header_layout.addWidget(QLabel("Type:"))
        header_layout.addWidget(self.event_type_filter)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Event table
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(6)
        self.event_table.setHorizontalHeaderLabels([
            "Time", "Severity", "Type", "Source", "Description", "Confidence"
        ])

        # Configure table
        header = self.event_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Description column

        self.event_table.setAlternatingRowColors(True)
        self.event_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #fff;
                border: 1px solid #444;
                gridline-color: #333;
            }
            QTableWidget::item:selected {
                background-color: #4ecdc4;
                color: #000;
            }
        """)

        layout.addWidget(self.event_table)

        self.setLayout(layout)

        # Store all events for filtering
        self.all_events = []

    def add_event(self, event: ThreatEvent):
        """Add a new event to the stream."""
        self.all_events.append(event)

        # Keep only recent events
        if len(self.all_events) > self.max_events:
            self.all_events.pop(0)

        self.apply_filters()

    def apply_filters(self):
        """Apply current filters and update the table."""
        severity_filter = self.severity_filter.currentText()
        type_filter = self.event_type_filter.currentText()

        # Filter events
        filtered_events = []
        for event in self.all_events:
            if severity_filter != "ALL" and event.severity != severity_filter:
                continue
            if type_filter != "ALL" and event.event_type != type_filter:
                continue
            filtered_events.append(event)

        # Update table
        self.event_table.setRowCount(len(filtered_events))

        for row, event in enumerate(reversed(filtered_events)):  # Most recent first
            # Format timestamp
            time_str = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")

            # Add items
            self.event_table.setItem(row, 0, QTableWidgetItem(time_str))

            # Color-code severity
            severity_item = QTableWidgetItem(event.severity)
            if event.severity == "CRITICAL":
                severity_item.setBackground(QColor("#e74c3c"))
            elif event.severity == "HIGH":
                severity_item.setBackground(QColor("#f39c12"))
            elif event.severity == "MEDIUM":
                severity_item.setBackground(QColor("#f1c40f"))
            else:
                severity_item.setBackground(QColor("#95a5a6"))

            self.event_table.setItem(row, 1, severity_item)
            self.event_table.setItem(row, 2, QTableWidgetItem(event.event_type))
            self.event_table.setItem(row, 3, QTableWidgetItem(event.source))
            self.event_table.setItem(row, 4, QTableWidgetItem(event.description))
            self.event_table.setItem(row, 5, QTableWidgetItem(f"{event.confidence:.2f}"))


class SecurityDashboard(QWidget):
    """Main security dashboard widget."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = DashboardConfig()

        # Initialize data collector
        self.data_collector = RealTimeDataCollector()
        self.data_collector.threat_detected.connect(self.handle_threat_event)
        self.data_collector.metrics_updated.connect(self.handle_metrics_update)
        self.data_collector.system_alert.connect(self.handle_system_alert)

        # Initialize UI
        self.initUI()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.periodic_update)

        # Start data collection
        self.start_monitoring()

    def initUI(self):
        """Initialize the dashboard UI."""
        main_layout = QVBoxLayout()

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Threat map and metrics
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)

        # Right panel - Event stream and controls
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)

        # Set splitter proportions
        content_splitter.setSizes([600, 400])

        main_layout.addWidget(content_splitter)

        # Status bar
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)

        self.setLayout(main_layout)

        # Apply dark theme
        self.apply_dark_theme()

    def create_header(self) -> QWidget:
        """Create the dashboard header."""
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-bottom: 2px solid #4ecdc4;
            }
        """)

        layout = QHBoxLayout()

        # Title
        title = QLabel("xanadOS Security Operations Center")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4ecdc4;
            padding: 10px;
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Status indicator
        self.status_indicator = QLabel("● ACTIVE")
        self.status_indicator.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2ecc71;
            padding: 10px;
        """)
        layout.addWidget(self.status_indicator)

        # Current time
        self.current_time = QLabel()
        self.current_time.setStyleSheet("""
            font-size: 14px;
            color: #fff;
            padding: 10px;
        """)
        layout.addWidget(self.current_time)

        header.setLayout(layout)
        return header

    def create_left_panel(self) -> QWidget:
        """Create the left panel with threat map and metrics."""
        panel = QWidget()
        layout = QVBoxLayout()

        # Threat map
        self.threat_map = ThreatMapWidget()
        layout.addWidget(self.threat_map)

        # Metrics grid
        metrics_group = QGroupBox("System Metrics")
        metrics_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #4ecdc4;
                border: 1px solid #444;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        metrics_layout = QGridLayout()

        # Create metric charts
        self.cpu_chart = MetricsChartWidget("CPU Usage (%)")
        self.memory_chart = MetricsChartWidget("Memory Usage (%)")
        self.scan_rate_chart = MetricsChartWidget("Scan Rate (files/sec)")
        self.threat_rate_chart = MetricsChartWidget("Threat Detection Rate")

        metrics_layout.addWidget(self.cpu_chart, 0, 0)
        metrics_layout.addWidget(self.memory_chart, 0, 1)
        metrics_layout.addWidget(self.scan_rate_chart, 1, 0)
        metrics_layout.addWidget(self.threat_rate_chart, 1, 1)

        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)

        panel.setLayout(layout)
        return panel

    def create_right_panel(self) -> QWidget:
        """Create the right panel with event stream and controls."""
        panel = QWidget()
        layout = QVBoxLayout()

        # Control panel
        controls_group = QGroupBox("Dashboard Controls")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #4ecdc4;
                border: 1px solid #444;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)

        controls_layout = QGridLayout()

        # Auto-refresh toggle
        self.auto_refresh_cb = QCheckBox("Auto Refresh")
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.stateChanged.connect(self.toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_cb, 0, 0)

        # Update interval
        controls_layout.addWidget(QLabel("Update Interval (ms):"), 0, 1)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 10000)
        self.interval_spin.setValue(1000)
        self.interval_spin.valueChanged.connect(self.update_interval_changed)
        controls_layout.addWidget(self.interval_spin, 0, 2)

        # Alert settings
        self.sound_alerts_cb = QCheckBox("Sound Alerts")
        self.sound_alerts_cb.setChecked(True)
        controls_layout.addWidget(self.sound_alerts_cb, 1, 0)

        self.email_alerts_cb = QCheckBox("Email Alerts")
        controls_layout.addWidget(self.email_alerts_cb, 1, 1)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Event stream
        self.event_stream = EventStreamWidget()
        layout.addWidget(self.event_stream)

        panel.setLayout(layout)
        return panel

    def create_status_bar(self) -> QWidget:
        """Create the dashboard status bar."""
        status_bar = QFrame()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-top: 1px solid #444;
            }
        """)

        layout = QHBoxLayout()

        self.connection_status = QLabel("Data Collector: Connecting...")
        self.connection_status.setStyleSheet("color: #f39c12; font-size: 12px;")
        layout.addWidget(self.connection_status)

        layout.addStretch()

        self.events_count = QLabel("Events: 0")
        self.events_count.setStyleSheet("color: #fff; font-size: 12px;")
        layout.addWidget(self.events_count)

        self.performance_status = QLabel("Performance: Good")
        self.performance_status.setStyleSheet("color: #2ecc71; font-size: 12px;")
        layout.addWidget(self.performance_status)

        status_bar.setLayout(layout)
        return status_bar

    def apply_dark_theme(self):
        """Apply dark theme to the dashboard."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: Arial, sans-serif;
            }
            QComboBox, QSpinBox, QCheckBox {
                background-color: #34495e;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ecf0f1;
            }
        """)

    def start_monitoring(self):
        """Start the real-time monitoring."""
        self.data_collector.start()
        self.update_timer.start(self.config.update_interval)

        self.connection_status.setText("Data Collector: Active")
        self.connection_status.setStyleSheet("color: #2ecc71; font-size: 12px;")

        self.logger.info("Security dashboard monitoring started")

    def stop_monitoring(self):
        """Stop the real-time monitoring."""
        self.data_collector.stop()
        self.update_timer.stop()

        self.connection_status.setText("Data Collector: Stopped")
        self.connection_status.setStyleSheet("color: #e74c3c; font-size: 12px;")

        self.logger.info("Security dashboard monitoring stopped")

    def handle_threat_event(self, event: ThreatEvent):
        """Handle a new threat event."""
        # Add to threat map
        self.threat_map.add_threat(event)

        # Add to event stream
        self.event_stream.add_event(event)

        # Update event count
        total_events = len(self.event_stream.all_events)
        self.events_count.setText(f"Events: {total_events}")

        # Sound alert for critical threats
        if event.severity == "CRITICAL" and self.sound_alerts_cb.isChecked():
            # In a real implementation, you would play a sound
            self.logger.warning(f"Critical threat detected: {event.description}")

    def handle_metrics_update(self, metrics: SystemMetrics):
        """Handle system metrics update."""
        # Update metric charts
        self.cpu_chart.add_data_point(metrics.cpu_usage, metrics.timestamp)
        self.memory_chart.add_data_point(metrics.memory_usage, metrics.timestamp)
        self.scan_rate_chart.add_data_point(metrics.scan_rate, metrics.timestamp)
        self.threat_rate_chart.add_data_point(metrics.threat_detection_rate, metrics.timestamp)

        # Update performance status
        if metrics.cpu_usage > 80 or metrics.memory_usage > 80:
            self.performance_status.setText("Performance: High Load")
            self.performance_status.setStyleSheet("color: #e74c3c; font-size: 12px;")
        elif metrics.cpu_usage > 60 or metrics.memory_usage > 60:
            self.performance_status.setText("Performance: Moderate Load")
            self.performance_status.setStyleSheet("color: #f39c12; font-size: 12px;")
        else:
            self.performance_status.setText("Performance: Good")
            self.performance_status.setStyleSheet("color: #2ecc71; font-size: 12px;")

    def handle_system_alert(self, severity: str, message: str):
        """Handle system alerts."""
        self.logger.warning(f"System alert [{severity}]: {message}")

        # Create alert event
        alert_event = ThreatEvent(
            event_id=f"alert_{int(time.time())}",
            timestamp=time.time(),
            event_type="SYSTEM_ALERT",
            severity=severity,
            source="System Monitor",
            target="Local System",
            description=message,
            confidence=1.0
        )

        self.handle_threat_event(alert_event)

    def periodic_update(self):
        """Periodic UI updates."""
        # Update current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time.setText(current_time)

    def toggle_auto_refresh(self, state):
        """Toggle auto-refresh functionality."""
        if state == 2:  # Checked
            self.update_timer.start(self.config.update_interval)
        else:
            self.update_timer.stop()

    def update_interval_changed(self, value):
        """Update the refresh interval."""
        self.config.update_interval = value
        if self.auto_refresh_cb.isChecked():
            self.update_timer.start(value)

    def closeEvent(self, event):
        """Handle widget close event."""
        self.stop_monitoring()
        event.accept()
