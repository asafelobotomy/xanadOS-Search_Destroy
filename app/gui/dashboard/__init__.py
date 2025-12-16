"""Real-time security dashboard components.

This package provides interactive visualization widgets for real-time
security monitoring and system performance tracking, including threat
timelines, geographic maps, performance metrics, event streams, and
customizable dashboard layouts.

Phase 2, Task 2.1: Real-Time Security Dashboard
"""

from .threat_visualization import ThreatVisualizationWidget
from .performance_metrics import PerformanceMetricsWidget
from .layout_manager import CustomizableLayoutManager, WidgetConfig, LayoutConfig
from .event_stream import (
    SecurityEventStreamWidget,
    SecurityEventLog,
    SecurityEvent,
    EventType,
    EventSeverity,
)

__all__ = [
    "ThreatVisualizationWidget",
    "PerformanceMetricsWidget",
    "CustomizableLayoutManager",
    "WidgetConfig",
    "LayoutConfig",
    "SecurityEventStreamWidget",
    "SecurityEventLog",
    "SecurityEvent",
    "EventType",
    "EventSeverity",
]
