"""Interactive threat timeline widget.

Provides real-time visualization of security threats on a timeline with
zoom, pan, and filtering capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from enum import Enum

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QComboBox,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    import pyqtgraph as pg

    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    # Fallback for testing/headless environments
    QWidget = object  # type: ignore[assignment,misc]


class ThreatSeverity(Enum):
    """Threat severity levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ThreatEvent:
    """Represents a security threat event."""

    timestamp: datetime
    threat_type: str
    severity: ThreatSeverity
    file_path: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_color(self) -> tuple[int, int, int]:
        """Get color for threat severity visualization."""
        colors = {
            ThreatSeverity.LOW: (100, 200, 100),  # Green
            ThreatSeverity.MEDIUM: (255, 200, 0),  # Yellow
            ThreatSeverity.HIGH: (255, 140, 0),  # Orange
            ThreatSeverity.CRITICAL: (255, 50, 50),  # Red
        }
        return colors.get(self.severity, (128, 128, 128))


class ThreatTimelineWidget(QWidget):
    """Interactive timeline widget for visualizing threats over time.

    Features:
    - Real-time threat event plotting
    - Interactive zoom and pan controls
    - Severity-based color coding
    - Time range filtering (1h, 24h, 7d, 30d)
    - Event details on hover
    - Maximum event buffer (1000 events default)

    Signals:
        event_clicked: Emitted when user clicks on a threat event
        time_range_changed: Emitted when time range filter changes
    """

    event_clicked = pyqtSignal(object)  # ThreatEvent
    time_range_changed = pyqtSignal(str)  # time_range (e.g., "24h")

    def __init__(self, max_events: int = 1000, parent: QWidget | None = None):
        """Initialize threat timeline widget.

        Args:
            max_events: Maximum number of events to display (prevents memory issues)
            parent: Parent widget
        """
        super().__init__(parent)

        if not PYQTGRAPH_AVAILABLE:
            raise ImportError(
                "pyqtgraph is required for ThreatTimelineWidget. "
                "Install with: pip install pyqtgraph"
            )

        self.max_events = max_events
        self.events: list[ThreatEvent] = []
        self._setup_ui()

        # Auto-refresh timer (update every 1 second)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_plot)
        self._refresh_timer.start(1000)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Control bar
        control_layout = QHBoxLayout()

        # Time range selector
        control_layout.addWidget(QLabel("Time Range:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["1h", "6h", "24h", "7d", "30d", "All"])
        self.time_range_combo.setCurrentText("24h")
        self.time_range_combo.currentTextChanged.connect(self._on_time_range_changed)
        control_layout.addWidget(self.time_range_combo)

        # Severity filter
        control_layout.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All", "Low", "Medium", "High", "Critical"])
        self.severity_combo.currentTextChanged.connect(self._refresh_plot)
        control_layout.addWidget(self.severity_combo)

        # Clear button
        self.clear_btn = QPushButton("Clear Events")
        self.clear_btn.clicked.connect(self.clear_events)
        control_layout.addWidget(self.clear_btn)

        control_layout.addStretch()

        # Event count label
        self.event_count_label = QLabel("Events: 0")
        control_layout.addWidget(self.event_count_label)

        layout.addLayout(control_layout)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.setLabel("left", "Severity")
        self.plot_widget.setLabel("bottom", "Time")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=False)  # Only horizontal zoom/pan

        layout.addWidget(self.plot_widget)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Severity: "))

        for severity in ThreatSeverity:
            color_label = QLabel("■")
            r, g, b = ThreatEvent(
                timestamp=datetime.now(),
                threat_type="",
                severity=severity,
                file_path="",
                description="",
            ).get_color()
            color_label.setStyleSheet(f"color: rgb({r}, {g}, {b}); font-size: 20px;")
            legend_layout.addWidget(color_label)
            legend_layout.addWidget(QLabel(severity.name.capitalize()))

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

    def add_event(self, event: ThreatEvent) -> None:
        """Add a threat event to the timeline.

        Args:
            event: ThreatEvent to add
        """
        # Thread-safe: Schedule on main thread
        QTimer.singleShot(0, lambda: self._add_event_internal(event))

    def _add_event_internal(self, event: ThreatEvent) -> None:
        """Internal method to add event (must run on main thread)."""
        self.events.append(event)

        # Enforce max events limit (FIFO)
        if len(self.events) > self.max_events:
            self.events.pop(0)

        self._refresh_plot()

    def add_events(self, events: list[ThreatEvent]) -> None:
        """Add multiple threat events at once.

        Args:
            events: List of ThreatEvent objects
        """
        for event in events:
            self.add_event(event)

    def clear_events(self) -> None:
        """Clear all events from the timeline."""
        self.events.clear()
        self._refresh_plot()

    def _on_time_range_changed(self, time_range: str) -> None:
        """Handle time range selection change."""
        self.time_range_changed.emit(time_range)
        self._refresh_plot()

    def _get_time_filter(self) -> datetime | None:
        """Get cutoff timestamp based on selected time range."""
        time_range = self.time_range_combo.currentText()

        if time_range == "All":
            return None

        now = datetime.now()

        if time_range == "1h":
            return now - timedelta(hours=1)
        elif time_range == "6h":
            return now - timedelta(hours=6)
        elif time_range == "24h":
            return now - timedelta(hours=24)
        elif time_range == "7d":
            return now - timedelta(days=7)
        elif time_range == "30d":
            return now - timedelta(days=30)

        return None

    def _get_severity_filter(self) -> ThreatSeverity | None:
        """Get severity filter based on selection."""
        severity_text = self.severity_combo.currentText()

        if severity_text == "All":
            return None

        severity_map = {
            "Low": ThreatSeverity.LOW,
            "Medium": ThreatSeverity.MEDIUM,
            "High": ThreatSeverity.HIGH,
            "Critical": ThreatSeverity.CRITICAL,
        }

        return severity_map.get(severity_text)

    def _refresh_plot(self) -> None:
        """Refresh the plot with current events."""
        # Clear existing plot
        self.plot_widget.clear()

        # Apply filters
        time_filter = self._get_time_filter()
        severity_filter = self._get_severity_filter()

        filtered_events = [
            event
            for event in self.events
            if (time_filter is None or event.timestamp >= time_filter)
            and (severity_filter is None or event.severity == severity_filter)
        ]

        # Update event count
        self.event_count_label.setText(f"Events: {len(filtered_events)}")

        if not filtered_events:
            return

        # Prepare data for plotting
        timestamps = [(event.timestamp.timestamp()) for event in filtered_events]
        severity_values = [event.severity.value for event in filtered_events]
        colors = [event.get_color() for event in filtered_events]

        # Create scatter plot with color-coded severity
        scatter = pg.ScatterPlotItem(
            x=timestamps, y=severity_values, pen=None, brush=colors, size=10, symbol="o"
        )

        self.plot_widget.addItem(scatter)

        # Set y-axis range (severity levels 1-4)
        self.plot_widget.setYRange(0.5, 4.5)

        # Set x-axis to show time labels
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            self.plot_widget.setXRange(min_time, max_time)

            # Format x-axis as timestamps
            axis = self.plot_widget.getAxis("bottom")
            axis.setLabel("Time")

    def get_event_count(self) -> int:
        """Get total number of events in buffer.

        Returns:
            Number of events currently stored
        """
        return len(self.events)

    def get_events_in_range(self, start: datetime, end: datetime) -> list[ThreatEvent]:
        """Get events within a specific time range.

        Args:
            start: Start timestamp
            end: End timestamp

        Returns:
            List of events within the range
        """
        return [event for event in self.events if start <= event.timestamp <= end]
