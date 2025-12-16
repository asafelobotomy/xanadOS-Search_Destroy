#!/usr/bin/env python3
"""
Integrated Dashboard Demo - Task 2.1 Complete

Demonstrates all four dashboard widgets working together:
- Task 2.1.1: ThreatVisualizationWidget
- Task 2.1.2: PerformanceMetricsWidget
- Task 2.1.3: CustomizableLayoutManager
- Task 2.1.4: SecurityEventStreamWidget

Features:
- Fully integrated security dashboard
- Drag-and-drop widget repositioning
- Save/load custom layouts
- Live event stream
- Real-time threat visualization
- Performance metrics monitoring
- Event filtering and export

Author: xanadOS Security Team
Date: December 16, 2025
"""

import sys
from datetime import datetime
from pathlib import Path

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
    from PyQt6.QtCore import QTimer, Qt
except ImportError:
    print("Error: PyQt6 is required for the dashboard demo")
    print("Install with: pip install PyQt6")
    sys.exit(1)

from app.gui.dashboard import (
    # Task 2.1.1 - Threat Visualization
    ThreatVisualizationWidget,
    # Task 2.1.2 - Performance Metrics
    PerformanceMetricsWidget,
    # Task 2.1.3 - Customizable Layout
    CustomizableLayoutManager,
    # Task 2.1.4 - Event Stream
    SecurityEventStreamWidget,
    SecurityEventLog,
    SecurityEvent,
    EventType,
    EventSeverity,
)


class IntegratedSecurityDashboard(CustomizableLayoutManager):
    """
    Fully integrated security dashboard combining all widgets.

    This class extends CustomizableLayoutManager and adds all four
    dashboard widgets with automatic data synchronization.
    """

    def __init__(self):
        """Initialize the integrated dashboard."""
        super().__init__()

        # Set window properties
        self.setWindowTitle("xanadOS Security Dashboard - Integrated Demo")
        self.resize(1400, 900)

        # Create widgets
        self._create_widgets()

        # Setup widget integration
        self._setup_integration()

        # Start simulation
        self._start_simulation()

    def _create_widgets(self) -> None:
        """Create all dashboard widgets."""
        # Task 2.1.1 - Threat Visualization
        self.threat_widget = ThreatVisualizationWidget()
        self.threat_widget.setMinimumSize(400, 300)

        # Task 2.1.2 - Performance Metrics
        self.performance_widget = PerformanceMetricsWidget()
        self.performance_widget.setMinimumSize(400, 300)

        # Task 2.1.4 - Event Stream
        self.event_stream = SecurityEventStreamWidget(
            auto_refresh_ms=3000,  # 3 seconds
            page_size=50,
        )
        self.event_stream.setMinimumSize(600, 400)

        # Add widgets to layout manager
        self.add_widget(
            widget_id="threat_viz",
            widget=self.threat_widget,
            title="🎯 Threat Visualization",
            area="left",
            initial_visible=True,
        )

        self.add_widget(
            widget_id="performance",
            widget=self.performance_widget,
            title="📊 Performance Metrics",
            area="right",
            initial_visible=True,
        )

        self.add_widget(
            widget_id="event_stream",
            widget=self.event_stream,
            title="📜 Security Event Stream",
            area="bottom",
            initial_visible=True,
        )

    def _setup_integration(self) -> None:
        """Setup integration between widgets."""
        # Connect threat detection to event stream
        self.threat_widget.threat_detected.connect(self._on_threat_detected)

        # Connect scan metrics to event stream
        self.performance_widget.metric_updated.connect(self._on_metric_updated)

        # Connect event selection to details display
        self.event_stream.event_selected.connect(self._on_event_selected)

    def _start_simulation(self) -> None:
        """Start simulated security events."""
        # Simulation timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._simulate_events)
        self.sim_timer.start(5000)  # Every 5 seconds

        # Initial events
        self._add_initial_events()

    def _add_initial_events(self) -> None:
        """Add some initial events for demonstration."""
        events = [
            SecurityEvent(
                timestamp=datetime.utcnow().isoformat(),
                event_type=EventType.SCAN_START.value,
                severity=EventSeverity.INFO.value,
                source="system",
                message="Dashboard initialized - starting system scan",
                details={"scan_type": "quick", "targets": 500},
            ),
            SecurityEvent(
                timestamp=datetime.utcnow().isoformat(),
                event_type=EventType.UPDATE_COMPLETE.value,
                severity=EventSeverity.INFO.value,
                source="updater",
                message="Virus definitions updated successfully",
                details={"new_signatures": 1250, "version": "2025-12-16"},
            ),
        ]

        for event in events:
            self.event_stream.add_event(event)

    def _simulate_events(self) -> None:
        """Simulate security events for demonstration."""
        import random

        # Random event type
        event_types = [
            (
                EventType.SCAN_COMPLETE,
                EventSeverity.INFO,
                "Scanner",
                "Scan completed - {} files checked",
            ),
            (
                EventType.THREAT_DETECTED,
                EventSeverity.WARNING,
                "ClamAV",
                "Potential threat detected: {}",
            ),
            (EventType.USER_ACTION, EventSeverity.INFO, "User", "User initiated {}"),
            (
                EventType.CONFIG_CHANGED,
                EventSeverity.INFO,
                "System",
                "Configuration updated: {}",
            ),
        ]

        event_type, severity, source, message_template = random.choice(event_types)

        # Random details
        details_options = [
            {"files": random.randint(100, 1000), "threats": random.randint(0, 5)},
            {"file_path": f"/tmp/file_{random.randint(1, 100)}.dat"},
            {"action": random.choice(["quarantine", "delete", "ignore"])},
            {"setting": random.choice(["max_threads", "scan_depth", "auto_update"])},
        ]

        event = SecurityEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type.value,
            severity=severity.value,
            source=source,
            message=message_template.format(random.randint(1, 999)),
            details=random.choice(details_options),
        )

        self.event_stream.add_event(event)

        # Occasionally update performance metrics
        if random.random() < 0.3:
            self.performance_widget.update_scan_metrics(
                files_scanned=random.randint(100, 1000),
                threats_found=random.randint(0, 10),
                scan_duration=random.uniform(1.0, 60.0),
                avg_file_time=random.uniform(0.001, 0.1),
            )

        # Occasionally add threat
        if random.random() < 0.2:
            self.threat_widget.add_threat(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "threat_name": f"Test.Malware.{random.randint(1, 100)}",
                    "file_path": f"/tmp/suspicious_{random.randint(1, 50)}.exe",
                    "severity": random.choice(["low", "medium", "high", "critical"]),
                    "source": random.choice(["ClamAV", "YARA", "Hybrid"]),
                    "confidence": random.uniform(0.5, 1.0),
                }
            )

    def _on_threat_detected(self, threat_data: dict) -> None:
        """Handle threat detection from ThreatVisualizationWidget."""
        event = SecurityEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=EventType.THREAT_DETECTED.value,
            severity=EventSeverity.CRITICAL.value,
            source=threat_data.get("source", "Unknown"),
            message=f"Threat detected: {threat_data.get('threat_name', 'Unknown')}",
            details={
                "file_path": threat_data.get("file_path", ""),
                "severity": threat_data.get("severity", ""),
                "confidence": threat_data.get("confidence", 0.0),
            },
        )
        self.event_stream.add_event(event)

    def _on_metric_updated(self, metric_data: dict) -> None:
        """Handle metric updates from PerformanceMetricsWidget."""
        event = SecurityEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=EventType.SCAN_COMPLETE.value,
            severity=EventSeverity.INFO.value,
            source="Performance Monitor",
            message=f"Scan metrics updated: {metric_data.get('metric_name', 'Unknown')}",
            details=metric_data,
        )
        self.event_stream.add_event(event)

    def _on_event_selected(self, event_data: dict) -> None:
        """Handle event selection from SecurityEventStreamWidget."""
        # Could show details in a dialog or update other widgets
        details = event_data.get("details", "")
        if details:
            print(
                f"Event selected: {event_data.get('message', '')} - Details: {details}"
            )


def main():
    """Run the integrated dashboard demo."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern style

    # Create and show dashboard
    dashboard = IntegratedSecurityDashboard()
    dashboard.show()

    # Show welcome message
    QMessageBox.information(
        dashboard,
        "Welcome to xanadOS Security Dashboard",
        "This demo integrates all four dashboard widgets:\n\n"
        "• Threat Visualization (Task 2.1.1)\n"
        "• Performance Metrics (Task 2.1.2)\n"
        "• Customizable Layout (Task 2.1.3)\n"
        "• Security Event Stream (Task 2.1.4)\n\n"
        "Features:\n"
        "• Drag and drop widgets to rearrange\n"
        "• Save/load custom layouts\n"
        "• Filter and search events\n"
        "• Export events to CSV/JSON\n"
        "• Real-time threat monitoring\n\n"
        "Events will be simulated every 5 seconds.",
    )

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
