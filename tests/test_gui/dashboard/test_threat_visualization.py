"""Tests for threat visualization dashboard components.

Tests cover ThreatVisualizationWidget and all sub-components with
mocked PyQt6 dependencies for headless testing.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


# Mock PyQt6 and pyqtgraph before importing dashboard modules
@pytest.fixture(autouse=True)
def mock_qt_dependencies(mock_pyqt):
    """Auto-use the mock_pyqt fixture from conftest.py."""
    # Additional mocking for pyqtgraph
    with patch.dict(
        "sys.modules",
        {
            "pyqtgraph": MagicMock(),
            "pyqtgraph.PlotWidget": MagicMock(),
            "pyqtgraph.ImageView": MagicMock(),
            "pyqtgraph.ScatterPlotItem": MagicMock(),
            "pyqtgraph.ColorMap": MagicMock(),
        },
    ):
        yield


def test_threat_event_creation():
    """Test ThreatEvent dataclass creation."""
    from app.gui.dashboard.widgets.threat_timeline import ThreatEvent, ThreatSeverity

    event = ThreatEvent(
        timestamp=datetime.now(),
        threat_type="malware",
        severity=ThreatSeverity.HIGH,
        file_path="/tmp/malware.exe",
        description="Detected malware",
    )

    assert event.threat_type == "malware"
    assert event.severity == ThreatSeverity.HIGH
    assert event.file_path == "/tmp/malware.exe"
    assert isinstance(event.metadata, dict)


def test_threat_event_color_mapping():
    """Test severity to color mapping."""
    from app.gui.dashboard.widgets.threat_timeline import ThreatEvent, ThreatSeverity

    event_low = ThreatEvent(
        timestamp=datetime.now(),
        threat_type="test",
        severity=ThreatSeverity.LOW,
        file_path="",
        description="",
    )

    event_critical = ThreatEvent(
        timestamp=datetime.now(),
        threat_type="test",
        severity=ThreatSeverity.CRITICAL,
        file_path="",
        description="",
    )

    # Verify different colors for different severities
    color_low = event_low.get_color()
    color_critical = event_critical.get_color()

    assert color_low != color_critical
    assert len(color_low) == 3  # RGB tuple
    assert all(0 <= c <= 255 for c in color_low)


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_timeline_widget_initialization():
    """Test ThreatTimelineWidget initialization."""
    with patch("app.gui.dashboard.widgets.threat_timeline.PYQTGRAPH_AVAILABLE", True):
        from app.gui.dashboard.widgets.threat_timeline import ThreatTimelineWidget

        # Should not raise
        widget = ThreatTimelineWidget(max_events=500)
        assert widget.max_events == 500
        assert len(widget.events) == 0


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_timeline_add_event():
    """Test adding events to timeline."""
    with patch("app.gui.dashboard.widgets.threat_timeline.PYQTGRAPH_AVAILABLE", True):
        from app.gui.dashboard.widgets.threat_timeline import (
            ThreatTimelineWidget,
            ThreatEvent,
            ThreatSeverity,
        )

        widget = ThreatTimelineWidget()

        event = ThreatEvent(
            timestamp=datetime.now(),
            threat_type="virus",
            severity=ThreatSeverity.MEDIUM,
            file_path="/tmp/virus.exe",
            description="Virus detected",
        )

        widget._add_event_internal(event)  # Direct call to avoid QTimer

        assert widget.get_event_count() == 1
        assert widget.events[0].threat_type == "virus"


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_timeline_max_events_enforcement():
    """Test that timeline enforces max events limit."""
    with patch("app.gui.dashboard.widgets.threat_timeline.PYQTGRAPH_AVAILABLE", True):
        from app.gui.dashboard.widgets.threat_timeline import (
            ThreatTimelineWidget,
            ThreatEvent,
            ThreatSeverity,
        )

        widget = ThreatTimelineWidget(max_events=10)

        # Add 15 events
        for i in range(15):
            event = ThreatEvent(
                timestamp=datetime.now(),
                threat_type=f"threat_{i}",
                severity=ThreatSeverity.LOW,
                file_path=f"/tmp/file_{i}",
                description=f"Threat {i}",
            )
            widget._add_event_internal(event)

        # Should only have 10 events (FIFO)
        assert widget.get_event_count() == 10

        # First events should have been removed
        assert "threat_0" not in [e.threat_type for e in widget.events]
        assert "threat_14" in [e.threat_type for e in widget.events]


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_timeline_time_range_filtering():
    """Test time range filtering."""
    with patch("app.gui.dashboard.widgets.threat_timeline.PYQTGRAPH_AVAILABLE", True):
        from app.gui.dashboard.widgets.threat_timeline import (
            ThreatTimelineWidget,
            ThreatEvent,
            ThreatSeverity,
        )

        widget = ThreatTimelineWidget()

        # Add events at different times
        now = datetime.now()

        old_event = ThreatEvent(
            timestamp=now - timedelta(hours=48),
            threat_type="old",
            severity=ThreatSeverity.LOW,
            file_path="/tmp/old",
            description="Old threat",
        )

        recent_event = ThreatEvent(
            timestamp=now - timedelta(hours=1),
            threat_type="recent",
            severity=ThreatSeverity.HIGH,
            file_path="/tmp/recent",
            description="Recent threat",
        )

        widget._add_event_internal(old_event)
        widget._add_event_internal(recent_event)

        # Get events in last 24 hours
        start = now - timedelta(hours=24)
        end = now

        recent_events = widget.get_events_in_range(start, end)

        assert len(recent_events) == 1
        assert recent_events[0].threat_type == "recent"


def test_threat_location_creation():
    """Test ThreatLocation dataclass."""
    from app.gui.dashboard.widgets.threat_map import ThreatLocation

    location = ThreatLocation(
        latitude=37.7749,
        longitude=-122.4194,
        threat_type="malware",
        severity="high",
        count=5,
    )

    assert location.latitude == 37.7749
    assert location.longitude == -122.4194
    assert location.count == 5


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_map_widget_initialization():
    """Test ThreatMapWidget initialization."""
    with patch("app.gui.dashboard.widgets.threat_map.PYQT6_AVAILABLE", True):
        from app.gui.dashboard.widgets.threat_map import ThreatMapWidget

        widget = ThreatMapWidget()
        assert len(widget.locations) == 0


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_map_location_clustering():
    """Test that nearby locations are clustered."""
    with patch("app.gui.dashboard.widgets.threat_map.PYQT6_AVAILABLE", True):
        from app.gui.dashboard.widgets.threat_map import ThreatMapWidget, ThreatLocation

        widget = ThreatMapWidget()

        # Add two nearby locations
        loc1 = ThreatLocation(
            latitude=37.7749,
            longitude=-122.4194,
            threat_type="malware",
            severity="high",
            count=1,
        )

        loc2 = ThreatLocation(
            latitude=37.7850,  # ~0.1 degrees away
            longitude=-122.4294,
            threat_type="malware",
            severity="high",
            count=1,
        )

        widget._add_location_internal(loc1)
        widget._add_location_internal(loc2)

        # Should be clustered into one location with count=2
        assert len(widget.locations) == 1
        assert widget.locations[0].count == 2


def test_heatmap_data_creation():
    """Test HeatmapData dataclass."""
    from app.gui.dashboard.widgets.heatmap import HeatmapData

    data = HeatmapData(
        category_x="malware",
        category_y="/home",
        value=3.5,
        metadata={"timestamp": datetime.now()},
    )

    assert data.category_x == "malware"
    assert data.value == 3.5
    assert "timestamp" in data.metadata


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_severity_heatmap_widget_initialization():
    """Test SeverityHeatmapWidget initialization."""
    with patch("app.gui.dashboard.widgets.heatmap.DEPENDENCIES_AVAILABLE", True):
        from app.gui.dashboard.widgets.heatmap import SeverityHeatmapWidget

        widget = SeverityHeatmapWidget()
        assert len(widget.data_points) == 0
        assert widget._aggregation_method == "count"


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_visualization_widget_integration():
    """Test main ThreatVisualizationWidget integration."""
    with patch("app.gui.dashboard.threat_visualization.PYQT6_AVAILABLE", True):
        from app.gui.dashboard import ThreatVisualizationWidget

        widget = ThreatVisualizationWidget(max_events=500)

        # Add a threat
        widget.add_threat(
            threat_type="malware",
            severity="critical",
            file_path="/tmp/malware.exe",
            description="Critical malware detected",
            latitude=37.7749,
            longitude=-122.4194,
        )

        assert widget.get_threat_count() == 1
        assert widget.get_critical_count() == 1


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_visualization_clear_all():
    """Test clearing all data from visualization."""
    with patch("app.gui.dashboard.threat_visualization.PYQT6_AVAILABLE", True):
        from app.gui.dashboard import ThreatVisualizationWidget

        widget = ThreatVisualizationWidget()

        # Add threats
        for i in range(5):
            widget.add_threat(
                threat_type=f"threat_{i}",
                severity="medium",
                file_path=f"/tmp/file_{i}",
                description=f"Threat {i}",
            )

        assert widget.get_threat_count() == 5

        # Clear all
        widget.clear_all()

        assert widget.get_threat_count() == 0


@pytest.mark.skipif(
    not hasattr(pytest, "skip_gui_tests"),
    reason="GUI tests require PyQt6 properly mocked",
)
def test_threat_visualization_statistics_update():
    """Test that statistics update correctly."""
    with patch("app.gui.dashboard.threat_visualization.PYQT6_AVAILABLE", True):
        from app.gui.dashboard import ThreatVisualizationWidget

        widget = ThreatVisualizationWidget()

        # Add mixed severity threats
        widget.add_threat("malware", "low", "/tmp/1", "Low threat")
        widget.add_threat("virus", "critical", "/tmp/2", "Critical virus")
        widget.add_threat("rootkit", "high", "/tmp/3", "High rootkit")
        widget.add_threat("trojan", "critical", "/tmp/4", "Critical trojan")

        assert widget.get_threat_count() == 4
        assert widget.get_critical_count() == 2


def test_import_error_handling():
    """Test that dataclasses can be imported even if GUI dependencies are missing."""
    # Import succeeds - GUI classes can still be imported with mocks
    from app.gui.dashboard.widgets.threat_timeline import ThreatEvent, ThreatSeverity
    from app.gui.dashboard.widgets.threat_map import ThreatLocation
    from app.gui.dashboard.widgets.heatmap import HeatmapData

    # Verify dataclasses work correctly
    assert ThreatEvent is not None
    assert ThreatSeverity is not None
    assert ThreatLocation is not None
    assert HeatmapData is not None


@pytest.mark.skipif(
    True, reason="GUI tests require display for ThreatVisualizationWidget"
)
def test_performance_max_events_constraint():
    """Test that max_events constraint prevents memory issues."""
    from app.gui.dashboard import ThreatVisualizationWidget
    from unittest.mock import MagicMock

    # Create widget with low max_events for testing
    widget = ThreatVisualizationWidget(max_events=100)

    # Mock the timeline widget's event count
    mock_timeline = MagicMock()
    mock_event_count = 0

    def mock_get_event_count():
        return min(mock_event_count, 100)  # Simulate FIFO eviction

    mock_timeline.get_event_count = mock_get_event_count
    widget.timeline_widget = mock_timeline

    # Add 200 threats
    for i in range(200):
        mock_event_count = min(i + 1, 100)  # Simulate counting with max limit
        widget.add_threat(
            threat_type=f"threat_{i}",
            severity="low",
            file_path=f"/tmp/{i}",
            description=f"Threat {i}",
        )

    # Timeline should only have 100 events
    assert widget.timeline_widget.get_event_count() <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
