"""Real-time security dashboard components.

This package provides interactive visualization widgets for real-time
security monitoring and system performance tracking, including threat
timelines, geographic maps, performance metrics, event streams, and
customizable dashboard layouts.

Phase 2, Task 2.1: Real-Time Security Dashboard
"""

from .event_stream import (
    EventSeverity,
    EventType,
    SecurityEvent,
    SecurityEventLog,
    SecurityEventStreamWidget,
)
from .layout_manager import CustomizableLayoutManager, LayoutConfig, WidgetConfig
from .performance_metrics import PerformanceMetricsWidget
from .threat_visualization import ThreatVisualizationWidget

__all__ = [
    "CustomizableLayoutManager",
    "EventSeverity",
    "EventType",
    "LayoutConfig",
    "PerformanceMetricsWidget",
    "SecurityEvent",
    "SecurityEventLog",
    "SecurityEventStreamWidget",
    "ThreatVisualizationWidget",
    "WidgetConfig",
]
