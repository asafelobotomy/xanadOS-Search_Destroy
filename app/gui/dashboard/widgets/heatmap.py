"""Severity heatmap widget.

Displays threat severity distribution by type and location as a heatmap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections import defaultdict

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    import pyqtgraph as pg
    import numpy as np

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    QWidget = object


@dataclass
class HeatmapData:
    """Data point for heatmap visualization."""

    category_x: str  # e.g., threat type
    category_y: str  # e.g., location or time period
    value: float  # Severity score or count
    metadata: dict[str, Any] | None = None


class SeverityHeatmapWidget(QWidget):
    """Heatmap visualization of threat severity distribution.

    Displays a 2D heatmap showing threat patterns across two dimensions
    (e.g., threat type vs. time, or threat type vs. location).

    Features:
    - Color-coded severity levels
    - Configurable axes (type, location, time)
    - Hover tooltips with details
    - Auto-updating aggregation
    - Customizable color scales

    Signals:
        cell_clicked: Emitted when user clicks on a heatmap cell
    """

    cell_clicked = pyqtSignal(str, str, float)  # category_x, category_y, value

    def __init__(self, parent: QWidget | None = None):
        """Initialize severity heatmap widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "pyqtgraph and numpy are required for SeverityHeatmapWidget. "
                "Install with: pip install pyqtgraph numpy"
            )

        self.data_points: list[HeatmapData] = []
        self._aggregation_method = "count"  # count, sum, average, max

        self._setup_ui()

        # Auto-refresh timer (update every 5 seconds)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_heatmap)
        self._refresh_timer.start(5000)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Control bar
        control_layout = QHBoxLayout()

        # Title
        title_label = QLabel("Threat Severity Heatmap")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        control_layout.addWidget(title_label)

        control_layout.addStretch()

        # X-axis selector
        control_layout.addWidget(QLabel("X-Axis:"))
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.addItems(["Threat Type", "Location", "Time (Hour)"])
        self.x_axis_combo.currentTextChanged.connect(self._refresh_heatmap)
        control_layout.addWidget(self.x_axis_combo)

        # Y-axis selector
        control_layout.addWidget(QLabel("Y-Axis:"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.addItems(["Location", "Time (Hour)", "Threat Type"])
        self.y_axis_combo.setCurrentText("Time (Hour)")
        self.y_axis_combo.currentTextChanged.connect(self._refresh_heatmap)
        control_layout.addWidget(self.y_axis_combo)

        # Aggregation method
        control_layout.addWidget(QLabel("Aggregation:"))
        self.agg_combo = QComboBox()
        self.agg_combo.addItems(["Count", "Sum", "Average", "Max"])
        self.agg_combo.currentTextChanged.connect(self._on_aggregation_changed)
        control_layout.addWidget(self.agg_combo)

        layout.addLayout(control_layout)

        # Heatmap view
        self.heatmap_view = pg.ImageView()
        self.heatmap_view.ui.roiBtn.hide()  # Hide ROI button
        self.heatmap_view.ui.menuBtn.hide()  # Hide menu button
        layout.addWidget(self.heatmap_view)

        # Color scale legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Low"))

        # Color gradient bar (placeholder)
        gradient_label = QLabel()
        gradient_label.setFixedHeight(20)
        gradient_label.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 green, stop:0.5 yellow, stop:1 red);"
        )
        legend_layout.addWidget(gradient_label, stretch=1)

        legend_layout.addWidget(QLabel("High"))
        layout.addLayout(legend_layout)

        # Stats label
        self.stats_label = QLabel("Data Points: 0")
        layout.addWidget(self.stats_label)

    def add_data_point(self, data: HeatmapData) -> None:
        """Add a data point to the heatmap.

        Args:
            data: HeatmapData to add
        """
        # Thread-safe: Schedule on main thread
        QTimer.singleShot(0, lambda: self._add_data_point_internal(data))

    def _add_data_point_internal(self, data: HeatmapData) -> None:
        """Internal method to add data point (must run on main thread)."""
        self.data_points.append(data)
        self._update_stats()
        # Note: Heatmap refresh happens on timer

    def add_data_points(self, data_list: list[HeatmapData]) -> None:
        """Add multiple data points at once.

        Args:
            data_list: List of HeatmapData objects
        """
        for data in data_list:
            self.add_data_point(data)

    def clear_data(self) -> None:
        """Clear all data points."""
        self.data_points.clear()
        self._refresh_heatmap()
        self._update_stats()

    def _on_aggregation_changed(self, method: str) -> None:
        """Handle aggregation method change."""
        self._aggregation_method = method.lower()
        self._refresh_heatmap()

    def _refresh_heatmap(self) -> None:
        """Refresh the heatmap visualization."""
        if not self.data_points:
            # Clear heatmap if no data
            empty_data = np.zeros((1, 1))
            self.heatmap_view.setImage(empty_data)
            return

        # Get axis configurations
        x_axis = self.x_axis_combo.currentText()
        y_axis = self.y_axis_combo.currentText()

        # Aggregate data into 2D matrix
        matrix, x_labels, y_labels = self._aggregate_data(x_axis, y_axis)

        # Update heatmap
        self.heatmap_view.setImage(
            matrix.T, autoLevels=True
        )  # Transpose for correct orientation

        # Set color map (green -> yellow -> red)
        colors = [
            (0, (0, 255, 0)),  # Green at 0
            (128, (255, 255, 0)),  # Yellow at mid
            (255, (255, 0, 0)),  # Red at max
        ]
        cmap = pg.ColorMap(
            pos=[c[0] / 255.0 for c in colors], color=[c[1] for c in colors]
        )
        self.heatmap_view.setColorMap(cmap)

    def _aggregate_data(
        self, x_axis: str, y_axis: str
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Aggregate data points into a 2D matrix.

        Args:
            x_axis: X-axis category
            y_axis: Y-axis category

        Returns:
            (matrix, x_labels, y_labels)
        """
        # Collect unique categories
        x_categories = sorted(
            set(self._get_category(point, x_axis) for point in self.data_points)
        )
        y_categories = sorted(
            set(self._get_category(point, y_axis) for point in self.data_points)
        )

        # Create mapping from category to index
        x_map = {cat: i for i, cat in enumerate(x_categories)}
        y_map = {cat: i for i, cat in enumerate(y_categories)}

        # Initialize matrix
        matrix = np.zeros((len(x_categories), len(y_categories)))
        counts = np.zeros((len(x_categories), len(y_categories)))  # For averaging

        # Aggregate data
        for point in self.data_points:
            x_cat = self._get_category(point, x_axis)
            y_cat = self._get_category(point, y_axis)

            x_idx = x_map[x_cat]
            y_idx = y_map[y_cat]

            if self._aggregation_method == "count":
                matrix[x_idx, y_idx] += 1
            elif self._aggregation_method == "sum":
                matrix[x_idx, y_idx] += point.value
            elif self._aggregation_method in ("average", "max"):
                if self._aggregation_method == "average":
                    matrix[x_idx, y_idx] += point.value
                    counts[x_idx, y_idx] += 1
                else:  # max
                    matrix[x_idx, y_idx] = max(matrix[x_idx, y_idx], point.value)

        # Compute averages
        if self._aggregation_method == "average":
            with np.errstate(divide="ignore", invalid="ignore"):
                matrix = np.where(counts > 0, matrix / counts, 0)

        return matrix, x_categories, y_categories

    def _get_category(self, point: HeatmapData, axis: str) -> str:
        """Extract category value for a given axis.

        Args:
            point: HeatmapData point
            axis: Axis type (e.g., "Threat Type")

        Returns:
            Category string
        """
        if axis == "Threat Type":
            return point.category_x if point.category_x else "Unknown"
        elif axis == "Location":
            return point.category_y if point.category_y else "Unknown"
        elif axis == "Time (Hour)":
            # Extract hour from metadata if available
            if point.metadata and "timestamp" in point.metadata:
                from datetime import datetime

                ts = point.metadata["timestamp"]
                if isinstance(ts, datetime):
                    return f"{ts.hour:02d}:00"
            return "Unknown"

        return "Unknown"

    def _update_stats(self) -> None:
        """Update statistics label."""
        self.stats_label.setText(f"Data Points: {len(self.data_points)}")

    def get_data_count(self) -> int:
        """Get total number of data points.

        Returns:
            Number of data points
        """
        return len(self.data_points)
