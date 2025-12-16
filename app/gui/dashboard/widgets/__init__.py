"""Dashboard widget components.

Individual visualization components for the security dashboard.
"""

from .threat_timeline import ThreatTimelineWidget
from .threat_map import ThreatMapWidget
from .heatmap import SeverityHeatmapWidget

__all__ = [
    "ThreatTimelineWidget",
    "ThreatMapWidget",
    "SeverityHeatmapWidget",
]
