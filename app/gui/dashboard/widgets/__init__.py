"""Dashboard widget components.

Individual visualization components for the security dashboard.
"""

from .heatmap import SeverityHeatmapWidget
from .threat_map import ThreatMapWidget
from .threat_timeline import ThreatTimelineWidget

__all__ = [
    "SeverityHeatmapWidget",
    "ThreatMapWidget",
    "ThreatTimelineWidget",
]
