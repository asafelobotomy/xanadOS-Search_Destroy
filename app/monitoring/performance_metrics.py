#!/usr/bin/env python3
"""Performance metrics tracking for Real-Time Protection.

Comprehensive performance monitoring with JSON export for dashboards.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScanMetrics:
    """Metrics for a single scan operation."""

    file_path: str
    scan_duration: float
    file_size: int
    result: str  # "clean", "infected", "error"
    cached: bool
    priority: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceSnapshot:
    """Point-in-time performance snapshot."""

    timestamp: float
    uptime_seconds: float

    # Scan statistics
    scans_completed: int
    scans_per_hour: float
    average_scan_duration: float
    threats_detected: int

    # Cache performance
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float

    # Queue metrics
    queue_depth: int
    max_queue_depth: int

    # Worker utilization
    active_workers: int
    total_workers: int
    worker_utilization: float  # Percentage

    # Resource usage (if available)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0

    # Hybrid scanner (if enabled)
    clamav_detections: int = 0
    yara_detections: int = 0
    hybrid_detections: int = 0


class PerformanceMetrics:
    """Comprehensive performance tracking for Real-Time Protection.

    Features:
    - Scan duration tracking
    - Cache hit rate monitoring
    - Queue depth tracking
    - Worker utilization metrics
    - Threat detection rates
    - JSON export for dashboards
    """

    def __init__(self, export_interval: int = 300):
        """Initialize performance metrics.

        Args:
            export_interval: Seconds between auto-exports (default: 5 minutes)
        """
        self.logger = logging.getLogger(__name__)

        # Timing
        self.start_time = time.time()
        self.export_interval = export_interval
        self.last_export_time = self.start_time

        # Scan metrics
        self.recent_scans: list[ScanMetrics] = []
        self.max_recent_scans = 1000  # Keep last 1000 scans

        # Performance snapshots
        self.snapshots: list[PerformanceSnapshot] = []
        self.max_snapshots = 100  # Keep last 100 snapshots

        # Aggregated statistics
        self.total_scans = 0
        self.total_scan_time = 0.0
        self.total_threats = 0
        self.total_cache_hits = 0
        self.total_cache_misses = 0
        self.max_queue_depth_seen = 0

        # Worker tracking
        self.scaling_events: list[dict[str, Any]] = []
        self.max_scaling_events = 50

        self.logger.info(
            "Performance metrics initialized (export interval: %ds)", export_interval
        )

    def record_scan(self, metrics: ScanMetrics):
        """Record metrics for a completed scan.

        Args:
            metrics: Scan metrics to record
        """
        self.recent_scans.append(metrics)

        # Trim to max size
        if len(self.recent_scans) > self.max_recent_scans:
            self.recent_scans.pop(0)

        # Update aggregates
        self.total_scans += 1
        self.total_scan_time += metrics.scan_duration

        if metrics.result == "infected":
            self.total_threats += 1

        if metrics.cached:
            self.total_cache_hits += 1
        else:
            self.total_cache_misses += 1

    def record_snapshot(
        self,
        scanner_stats: dict[str, Any],
    ):
        """Record a performance snapshot from scanner statistics.

        Args:
            scanner_stats: Statistics dictionary from BackgroundScanner
        """
        now = time.time()
        uptime = now - self.start_time

        # Extract cache stats
        cache_stats = scanner_stats.get("cache", {})
        cache_hits = cache_stats.get("hits", 0)
        cache_misses = cache_stats.get("misses", 0)
        total_cache_ops = cache_hits + cache_misses
        cache_hit_rate = (
            (cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0.0
        )

        # Extract queue metrics
        queue_depth = scanner_stats.get("queued_scans", 0)
        if queue_depth > self.max_queue_depth_seen:
            self.max_queue_depth_seen = queue_depth

        # Extract worker metrics
        active_scans = scanner_stats.get("active_scans", 0)
        total_workers = scanner_stats.get("worker_threads", 1)
        worker_utilization = (
            (active_scans / total_workers * 100) if total_workers > 0 else 0.0
        )

        # Calculate average scan duration
        avg_scan_duration = (
            (self.total_scan_time / self.total_scans) if self.total_scans > 0 else 0.0
        )

        # Extract system monitor stats
        system_stats = scanner_stats.get("system_monitor", {}).get("current_load", {})
        cpu_percent = system_stats.get("cpu_percent", 0.0)
        memory_percent = system_stats.get("memory_percent", 0.0)

        # Extract hybrid scanner stats
        hybrid_stats = scanner_stats.get("hybrid_scanner", {}).get("detections", {})
        clamav_only = hybrid_stats.get("clamav_only", 0)
        yara_only = hybrid_stats.get("yara_only", 0)
        both_engines = hybrid_stats.get("both_engines", 0)

        # Create snapshot
        snapshot = PerformanceSnapshot(
            timestamp=now,
            uptime_seconds=uptime,
            scans_completed=scanner_stats.get("scans_completed", 0),
            scans_per_hour=scanner_stats.get("scans_per_hour", 0.0),
            average_scan_duration=avg_scan_duration,
            threats_detected=scanner_stats.get("threats_detected", 0),
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hit_rate,
            queue_depth=queue_depth,
            max_queue_depth=self.max_queue_depth_seen,
            active_workers=active_scans,
            total_workers=total_workers,
            worker_utilization=worker_utilization,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            clamav_detections=clamav_only,
            yara_detections=yara_only,
            hybrid_detections=both_engines,
        )

        self.snapshots.append(snapshot)

        # Trim to max size
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

        # Auto-export if interval elapsed
        if now - self.last_export_time >= self.export_interval:
            self.export_to_json()
            self.last_export_time = now

    def record_scaling_event(
        self,
        event_type: str,
        old_workers: int,
        new_workers: int,
        queue_depth: int,
        reason: str = "",
    ):
        """Record a worker scaling event.

        Args:
            event_type: "scale_up" or "scale_down"
            old_workers: Previous worker count
            new_workers: New worker count
            queue_depth: Queue depth at scaling time
            reason: Optional reason for scaling
        """
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "old_workers": old_workers,
            "new_workers": new_workers,
            "queue_depth": queue_depth,
            "reason": reason,
        }

        self.scaling_events.append(event)

        # Trim to max size
        if len(self.scaling_events) > self.max_scaling_events:
            self.scaling_events.pop(0)

        self.logger.info(
            "Scaling event: %s (%d → %d workers, queue: %d)",
            event_type,
            old_workers,
            new_workers,
            queue_depth,
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Dictionary with aggregated statistics
        """
        now = time.time()
        uptime = now - self.start_time

        # Calculate rates
        scans_per_hour = (self.total_scans / (uptime / 3600)) if uptime > 0 else 0.0
        threats_per_hour = (self.total_threats / (uptime / 3600)) if uptime > 0 else 0.0

        # Cache performance
        total_cache_ops = self.total_cache_hits + self.total_cache_misses
        cache_hit_rate = (
            (self.total_cache_hits / total_cache_ops * 100)
            if total_cache_ops > 0
            else 0.0
        )

        # Average scan time
        avg_scan_time = (
            (self.total_scan_time / self.total_scans) if self.total_scans > 0 else 0.0
        )

        return {
            "uptime_seconds": uptime,
            "total_scans": self.total_scans,
            "scans_per_hour": round(scans_per_hour, 2),
            "threats_detected": self.total_threats,
            "threats_per_hour": round(threats_per_hour, 2),
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "average_scan_duration_ms": round(avg_scan_time * 1000, 2),
            "max_queue_depth": self.max_queue_depth_seen,
            "scaling_events_count": len(self.scaling_events),
            "snapshots_recorded": len(self.snapshots),
        }

    def get_recent_performance(self, seconds: int = 300) -> dict[str, Any]:
        """Get performance metrics for recent time window.

        Args:
            seconds: Time window in seconds (default: 5 minutes)

        Returns:
            Dictionary with recent performance metrics
        """
        cutoff_time = time.time() - seconds

        # Filter recent scans
        recent = [s for s in self.recent_scans if s.timestamp >= cutoff_time]

        if not recent:
            return {
                "window_seconds": seconds,
                "scans": 0,
                "average_duration_ms": 0.0,
                "cache_hit_rate_percent": 0.0,
            }

        # Calculate metrics
        total_duration = sum(s.scan_duration for s in recent)
        cached_count = sum(1 for s in recent if s.cached)

        avg_duration = total_duration / len(recent)
        cache_rate = (cached_count / len(recent) * 100) if recent else 0.0

        return {
            "window_seconds": seconds,
            "scans": len(recent),
            "average_duration_ms": round(avg_duration * 1000, 2),
            "cache_hit_rate_percent": round(cache_rate, 2),
            "threats_detected": sum(1 for s in recent if s.result == "infected"),
        }

    def export_to_json(self, file_path: str | Path | None = None) -> str:
        """Export metrics to JSON file.

        Args:
            file_path: Optional custom export path

        Returns:
            Path to exported file
        """
        if file_path is None:
            # Default: export to cache/metrics directory
            from app.utils.config import CACHE_DIR

            metrics_dir = CACHE_DIR / "metrics"
            metrics_dir.mkdir(parents=True, exist_ok=True)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_path = metrics_dir / f"rt_protection_metrics_{timestamp}.json"
        else:
            file_path = Path(file_path)

        # Build export data
        export_data = {
            "export_timestamp": time.time(),
            "summary": self.get_summary(),
            "recent_5min": self.get_recent_performance(300),
            "recent_1hour": self.get_recent_performance(3600),
            "snapshots": [asdict(s) for s in self.snapshots[-20:]],  # Last 20 snapshots
            "scaling_events": self.scaling_events[-20:],  # Last 20 events
        }

        # Write to file
        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        self.logger.info("Metrics exported to: %s", file_path)
        return str(file_path)

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get data formatted for monitoring dashboards.

        Returns:
            Dictionary optimized for dashboard display
        """
        latest_snapshot = self.snapshots[-1] if self.snapshots else None

        dashboard = {
            "status": "operational" if self.total_scans > 0 else "initializing",
            "summary": self.get_summary(),
            "current": None,
            "trends": {
                "scans_per_hour": [],
                "cache_hit_rate": [],
                "worker_utilization": [],
            },
        }

        # Add current metrics
        if latest_snapshot:
            dashboard["current"] = {
                "scans_per_hour": round(latest_snapshot.scans_per_hour, 2),
                "cache_hit_rate_percent": round(latest_snapshot.cache_hit_rate, 2),
                "queue_depth": latest_snapshot.queue_depth,
                "worker_utilization_percent": round(
                    latest_snapshot.worker_utilization, 2
                ),
                "cpu_percent": round(latest_snapshot.cpu_percent, 1),
                "memory_percent": round(latest_snapshot.memory_percent, 1),
                "threats_detected": latest_snapshot.threats_detected,
            }

        # Add trend data (last 20 snapshots)
        for snapshot in self.snapshots[-20:]:
            dashboard["trends"]["scans_per_hour"].append(
                {
                    "timestamp": snapshot.timestamp,
                    "value": round(snapshot.scans_per_hour, 2),
                }
            )
            dashboard["trends"]["cache_hit_rate"].append(
                {
                    "timestamp": snapshot.timestamp,
                    "value": round(snapshot.cache_hit_rate, 2),
                }
            )
            dashboard["trends"]["worker_utilization"].append(
                {
                    "timestamp": snapshot.timestamp,
                    "value": round(snapshot.worker_utilization, 2),
                }
            )

        return dashboard
