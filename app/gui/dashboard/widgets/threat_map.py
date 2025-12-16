"""Geographic threat map widget.

Visualizes threat origins on a world map with location-based clustering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object


@dataclass
class ThreatLocation:
    """Represents a threat with geographic location."""

    latitude: float
    longitude: float
    threat_type: str
    severity: str  # "low", "medium", "high", "critical"
    count: int = 1  # Number of threats at this location
    metadata: dict[str, Any] | None = None


class ThreatMapWidget(QWidget):
    """Geographic visualization of threat origins.

    Displays threats on a world map with location clustering and
    severity-based coloring. Useful for identifying geographic patterns
    in threat sources.

    Features:
    - World map background
    - Location markers sized by threat count
    - Color-coded severity levels
    - Click to view location details
    - Zoom and pan controls

    Signals:
        location_clicked: Emitted when user clicks on a threat location
    """

    location_clicked = pyqtSignal(object)  # ThreatLocation

    def __init__(self, parent: QWidget | None = None):
        """Initialize threat map widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        if not PYQT6_AVAILABLE:
            raise ImportError("PyQt6 is required for ThreatMapWidget")

        self.locations: list[ThreatLocation] = []
        self._zoom_level = 1.0
        self._offset_x = 0
        self._offset_y = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Control bar
        control_layout = QHBoxLayout()

        # Title
        title_label = QLabel("Geographic Threat Distribution")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        control_layout.addWidget(title_label)

        control_layout.addStretch()

        # Zoom controls
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        control_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        control_layout.addWidget(zoom_out_btn)

        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        control_layout.addWidget(reset_btn)

        layout.addLayout(control_layout)

        # Map canvas (custom paint widget)
        self.map_canvas = MapCanvas(self)
        self.map_canvas.setMinimumHeight(400)
        layout.addWidget(self.map_canvas)

        # Stats label
        self.stats_label = QLabel("Threat Locations: 0")
        layout.addWidget(self.stats_label)

    def add_location(self, location: ThreatLocation) -> None:
        """Add a threat location to the map.

        Args:
            location: ThreatLocation to add
        """
        # Thread-safe: Schedule on main thread
        QTimer.singleShot(0, lambda: self._add_location_internal(location))

    def _add_location_internal(self, location: ThreatLocation) -> None:
        """Internal method to add location (must run on main thread)."""
        # Check if location already exists (cluster nearby threats)
        for existing in self.locations:
            if self._are_locations_close(existing, location):
                existing.count += location.count
                self.map_canvas.update()
                self._update_stats()
                return

        # Add new location
        self.locations.append(location)
        self.map_canvas.locations = self.locations
        self.map_canvas.update()
        self._update_stats()

    def _are_locations_close(
        self, loc1: ThreatLocation, loc2: ThreatLocation, threshold: float = 1.0
    ) -> bool:
        """Check if two locations are close enough to cluster.

        Args:
            loc1: First location
            loc2: Second location
            threshold: Distance threshold in degrees (default: 1.0)

        Returns:
            True if locations should be clustered
        """
        lat_diff = abs(loc1.latitude - loc2.latitude)
        lon_diff = abs(loc1.longitude - loc2.longitude)

        return lat_diff < threshold and lon_diff < threshold

    def clear_locations(self) -> None:
        """Clear all threat locations from the map."""
        self.locations.clear()
        self.map_canvas.locations = []
        self.map_canvas.update()
        self._update_stats()

    def zoom_in(self) -> None:
        """Zoom in on the map."""
        self._zoom_level = min(self._zoom_level * 1.2, 5.0)
        self.map_canvas.zoom_level = self._zoom_level
        self.map_canvas.update()

    def zoom_out(self) -> None:
        """Zoom out on the map."""
        self._zoom_level = max(self._zoom_level / 1.2, 0.5)
        self.map_canvas.zoom_level = self._zoom_level
        self.map_canvas.update()

    def reset_view(self) -> None:
        """Reset zoom and pan to default view."""
        self._zoom_level = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self.map_canvas.zoom_level = self._zoom_level
        self.map_canvas.offset_x = self._offset_x
        self.map_canvas.offset_y = self._offset_y
        self.map_canvas.update()

    def _update_stats(self) -> None:
        """Update statistics label."""
        total_threats = sum(loc.count for loc in self.locations)
        self.stats_label.setText(
            f"Threat Locations: {len(self.locations)} | Total Threats: {total_threats}"
        )


class MapCanvas(QWidget):
    """Custom widget for rendering the threat map."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.locations: list[ThreatLocation] = []
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

    def paintEvent(self, event) -> None:
        """Custom paint event to draw the map and threat markers."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), QColor(240, 248, 255))  # Light blue (ocean)

        # Draw simplified world map (landmasses as rectangles for now)
        # In production, would use actual map data or map tiles
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(QColor(220, 220, 200)))  # Beige (land)

        # Draw simplified continents (placeholder)
        width = self.width()
        height = self.height()

        # North America
        painter.drawRect(
            int(width * 0.15), int(height * 0.2), int(width * 0.2), int(height * 0.3)
        )
        # Europe/Africa
        painter.drawRect(
            int(width * 0.45), int(height * 0.25), int(width * 0.15), int(height * 0.4)
        )
        # Asia
        painter.drawRect(
            int(width * 0.65), int(height * 0.15), int(width * 0.25), int(height * 0.35)
        )

        # Draw threat markers
        for location in self.locations:
            self._draw_threat_marker(painter, location)

        # Draw grid lines
        painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))
        for i in range(1, 4):
            x = int(width * i / 4)
            painter.drawLine(x, 0, x, height)
            y = int(height * i / 4)
            painter.drawLine(0, y, width, y)

    def _draw_threat_marker(self, painter: QPainter, location: ThreatLocation) -> None:
        """Draw a threat marker on the map.

        Args:
            painter: QPainter instance
            location: ThreatLocation to draw
        """
        # Convert lat/lon to screen coordinates
        x, y = self._latlon_to_screen(location.latitude, location.longitude)

        # Determine color based on severity
        color_map = {
            "low": QColor(100, 200, 100),  # Green
            "medium": QColor(255, 200, 0),  # Yellow
            "high": QColor(255, 140, 0),  # Orange
            "critical": QColor(255, 50, 50),  # Red
        }
        color = color_map.get(location.severity.lower(), QColor(128, 128, 128))

        # Marker size based on threat count (logarithmic scale)
        import math

        base_size = 8
        size = int(base_size + math.log(location.count + 1) * 5)

        # Draw circle marker
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(int(x - size / 2), int(y - size / 2), size, size)

        # Draw count label if > 1
        if location.count > 1:
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(int(x - 10), int(y - size / 2 - 5), str(location.count))

    def _latlon_to_screen(self, latitude: float, longitude: float) -> tuple[int, int]:
        """Convert latitude/longitude to screen coordinates.

        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)

        Returns:
            (x, y) screen coordinates
        """
        # Simple Mercator projection
        width = self.width()
        height = self.height()

        # Normalize longitude (-180 to 180) to (0 to width)
        x = ((longitude + 180) / 360) * width

        # Normalize latitude (-90 to 90) to (height to 0) - inverted Y
        y = ((90 - latitude) / 180) * height

        # Apply zoom and offset
        x = int(x * self.zoom_level + self.offset_x)
        y = int(y * self.zoom_level + self.offset_y)

        return x, y
