#!/usr/bin/env python3
"""System load monitoring for adaptive scanning.

Monitors system resources to prevent scan operations from degrading performance.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class SystemLoad:
    """Current system load metrics."""

    cpu_percent: float
    memory_percent: float
    disk_io_percent: float
    timestamp: float
    load_level: str  # "low", "medium", "high", "critical"

    @property
    def is_high_load(self) -> bool:
        """Check if system is under high load."""
        return self.load_level in ("high", "critical")

    @property
    def is_critical_load(self) -> bool:
        """Check if system is under critical load."""
        return self.load_level == "critical"

    def __str__(self) -> str:
        """String representation."""
        return (
            f"CPU: {self.cpu_percent:.1f}%, "
            f"Memory: {self.memory_percent:.1f}%, "
            f"Load: {self.load_level}"
        )


class SystemMonitor:
    """Monitor system resources for adaptive scanning.

    Features:
    - CPU usage tracking
    - Memory usage tracking
    - Disk I/O monitoring
    - Load level assessment
    - Throttling recommendations
    """

    # Thresholds for load levels
    THRESHOLDS = {
        "low": {"cpu": 50, "memory": 60},
        "medium": {"cpu": 70, "memory": 75},
        "high": {"cpu": 85, "memory": 85},
        "critical": {"cpu": 95, "memory": 95},
    }

    def __init__(
        self,
        cpu_threshold_high: float = 80.0,
        cpu_threshold_critical: float = 90.0,
        memory_threshold_high: float = 85.0,
    ):
        """Initialize system monitor.

        Args:
            cpu_threshold_high: CPU usage % for high load
            cpu_threshold_critical: CPU usage % for critical load
            memory_threshold_high: Memory usage % for high load
        """
        self.logger = logging.getLogger(__name__)

        if not PSUTIL_AVAILABLE:
            self.logger.warning(
                "psutil not available - install with: pip install psutil"
            )
            self.available = False
            return

        self.available = True

        # Thresholds
        self.cpu_threshold_high = cpu_threshold_high
        self.cpu_threshold_critical = cpu_threshold_critical
        self.memory_threshold_high = memory_threshold_high

        # Statistics
        self.checks_performed = 0
        self.high_load_detected = 0
        self.critical_load_detected = 0

        # Last check cache
        self._last_check: SystemLoad | None = None
        self._last_check_time = 0.0
        self._cache_duration = 1.0  # Cache for 1 second

        self.logger.info(
            "System monitor initialized - CPU: %.1f%%/%.1f%%, Memory: %.1f%%",
            cpu_threshold_high,
            cpu_threshold_critical,
            memory_threshold_high,
        )

    def get_current_load(self, use_cache: bool = True) -> SystemLoad | None:
        """Get current system load metrics.

        Args:
            use_cache: Use cached result if recent (within 1 second)

        Returns:
            SystemLoad object or None if unavailable
        """
        if not self.available:
            return None

        # Check cache
        now = time.time()
        if use_cache and self._last_check:
            if now - self._last_check_time < self._cache_duration:
                return self._last_check

        try:
            self.checks_performed += 1

            # Get CPU usage (1 second interval for accuracy)
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Get disk I/O (basic metric)
            disk_io = psutil.disk_io_counters()
            # Simplified: use read/write count as proxy
            disk_io_percent = 0.0  # Not easily calculable without interval

            # Assess load level
            load_level = self._assess_load_level(cpu_percent, memory_percent)

            # Track high load events
            if load_level == "high":
                self.high_load_detected += 1
            elif load_level == "critical":
                self.critical_load_detected += 1

            # Create load object
            load = SystemLoad(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_io_percent=disk_io_percent,
                timestamp=now,
                load_level=load_level,
            )

            # Cache result
            self._last_check = load
            self._last_check_time = now

            return load

        except Exception as e:
            self.logger.error("Failed to get system load: %s", e)
            return None

    def _assess_load_level(self, cpu_percent: float, memory_percent: float) -> str:
        """Assess system load level.

        Args:
            cpu_percent: Current CPU usage %
            memory_percent: Current memory usage %

        Returns:
            Load level: "low", "medium", "high", "critical"
        """
        # Critical: Either metric above critical threshold
        if cpu_percent >= self.cpu_threshold_critical:
            return "critical"
        if memory_percent >= 95.0:  # Memory critical threshold
            return "critical"

        # High: Either metric above high threshold
        if cpu_percent >= self.cpu_threshold_high:
            return "high"
        if memory_percent >= self.memory_threshold_high:
            return "high"

        # Medium: Either metric moderately elevated
        if cpu_percent >= 60.0 or memory_percent >= 70.0:
            return "medium"

        # Low: Normal operation
        return "low"

    def should_throttle_scanning(self) -> bool:
        """Check if scanning should be throttled due to high load.

        Returns:
            True if should throttle, False otherwise
        """
        load = self.get_current_load()
        if not load:
            return False  # If unavailable, don't throttle

        return load.is_high_load

    def should_pause_scanning(self) -> bool:
        """Check if scanning should be paused due to critical load.

        Returns:
            True if should pause, False otherwise
        """
        load = self.get_current_load()
        if not load:
            return False  # If unavailable, don't pause

        return load.is_critical_load

    def get_recommended_worker_count(self, max_workers: int = 4) -> int:
        """Get recommended worker count based on system load.

        Args:
            max_workers: Maximum number of workers

        Returns:
            Recommended worker count (1 to max_workers)
        """
        load = self.get_current_load()
        if not load:
            return max_workers  # If unavailable, use max

        # Adjust based on load level
        if load.load_level == "critical":
            return 1  # Minimal workers
        elif load.load_level == "high":
            return max(1, max_workers // 2)  # Half workers
        elif load.load_level == "medium":
            return max(2, int(max_workers * 0.75))  # 75% workers
        else:
            return max_workers  # Full workers

    def get_recommended_delay(self) -> float:
        """Get recommended delay between scans (seconds).

        Returns:
            Delay in seconds (0.0 to 2.0)
        """
        load = self.get_current_load()
        if not load:
            return 0.0  # If unavailable, no delay

        # Adaptive delay based on load
        if load.load_level == "critical":
            return 2.0  # Long delay
        elif load.load_level == "high":
            return 1.0  # Medium delay
        elif load.load_level == "medium":
            return 0.5  # Short delay
        else:
            return 0.0  # No delay

    def get_statistics(self) -> dict[str, Any]:
        """Get monitor statistics.

        Returns:
            Dictionary with statistics
        """
        current_load = self.get_current_load()

        stats = {
            "available": self.available,
            "checks_performed": self.checks_performed,
            "high_load_events": self.high_load_detected,
            "critical_load_events": self.critical_load_detected,
            "thresholds": {
                "cpu_high": self.cpu_threshold_high,
                "cpu_critical": self.cpu_threshold_critical,
                "memory_high": self.memory_threshold_high,
            },
        }

        if current_load:
            stats["current_load"] = {
                "cpu_percent": round(current_load.cpu_percent, 1),
                "memory_percent": round(current_load.memory_percent, 1),
                "load_level": current_load.load_level,
                "should_throttle": current_load.is_high_load,
                "should_pause": current_load.is_critical_load,
            }

        return stats
