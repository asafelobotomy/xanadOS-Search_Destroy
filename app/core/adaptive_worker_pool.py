#!/usr/bin/env python3
"""
Adaptive Worker Pool for Dynamic Thread Scaling
===============================================

Provides intelligent ThreadPoolExecutor management with dynamic worker
scaling based on system resource utilization.

Research-based implementation following Python 3.13 best practices and
modern threading patterns for I/O-bound workloads.
"""

import logging
import os
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import asyncio
import psutil


@dataclass
class WorkerPoolMetrics:
    """Metrics for adaptive worker pool performance tracking."""

    current_workers: int = 0
    min_workers: int = 0
    max_workers: int = 0
    total_adjustments: int = 0
    scale_ups: int = 0
    scale_downs: int = 0
    avg_cpu_percent: float = 0.0
    avg_memory_percent: float = 0.0
    avg_queue_depth: float = 0.0
    last_adjustment: datetime | None = None
    performance_gain_percent: float = 0.0


class AdaptiveWorkerPool:
    """
    Dynamically adjusts ThreadPoolExecutor worker count based on system load.

    Monitors CPU usage, memory pressure, and task queue depth to optimize
    thread pool size for I/O-bound file scanning workloads.

    Based on research findings:
    - Python 3.13 default: min(32, (os.process_cpu_count() or 1) + 4)
    - I/O-bound workloads can use hundreds to thousands of threads
    - Context switching limits practical maximum
    - PEP 703 future-proofs for GIL-optional Python

    Target: 15-20% performance improvement through adaptive scaling.
    """

    def __init__(
        self,
        min_workers: int | None = None,
        max_workers: int | None = None,
        adjustment_interval: float = 5.0,
        enable_monitoring: bool = True,
    ):
        """
        Initialize adaptive worker pool.

        Args:
            min_workers: Minimum worker threads (default: based on CPU cores)
            max_workers: Maximum worker threads (default: based on CPU cores)
            adjustment_interval: Seconds between scaling adjustments
            enable_monitoring: Enable performance monitoring
        """
        self.logger = logging.getLogger(__name__)

        # Determine CPU core count (Python 3.13 compatible)
        try:
            # Prefer process_cpu_count (respects cgroup limits)
            self.cpu_cores = os.process_cpu_count() or os.cpu_count() or 4
        except AttributeError:
            # Fallback for Python < 3.13
            self.cpu_cores = os.cpu_count() or 4

        # Calculate defaults based on research findings
        # For I/O-bound workloads (file scanning), use higher multiplier
        default_min = max(4, self.cpu_cores)
        default_max = min(100, self.cpu_cores * 12)  # Can go higher for I/O

        self.min_workers = min_workers or default_min
        self.max_workers = max_workers or default_max
        self.adjustment_interval = adjustment_interval
        self.enable_monitoring = enable_monitoring

        # Current state
        self.current_workers = self.min_workers
        self._executor: ThreadPoolExecutor | None = None
        self._task_queue: asyncio.Queue | None = None

        # Monitoring and metrics
        self.metrics = WorkerPoolMetrics(
            current_workers=self.current_workers,
            min_workers=self.min_workers,
            max_workers=self.max_workers,
        )
        self._last_adjustment = time.time()
        self._baseline_performance: float | None = None
        self._recent_task_times: deque[float] = deque(maxlen=100)

        # Thresholds for scaling decisions
        self.scale_up_cpu_threshold = 40.0  # Low CPU indicates room for more threads
        self.scale_up_queue_threshold = 20  # High queue depth needs more workers
        self.scale_down_cpu_threshold = 80.0  # High CPU indicates over-threading
        self.scale_down_queue_threshold = 2  # Low queue depth allows fewer workers
        self.memory_pressure_threshold = 85.0  # High memory limits scaling

        self.logger.info(
            f"AdaptiveWorkerPool initialized: min={self.min_workers}, "
            f"max={self.max_workers}, cores={self.cpu_cores}"
        )

    def set_executor(self, executor: ThreadPoolExecutor) -> None:
        """Set the ThreadPoolExecutor to manage."""
        self._executor = executor
        self.current_workers = executor._max_workers

    def set_task_queue(self, queue: asyncio.Queue) -> None:
        """Set the task queue for monitoring depth."""
        self._task_queue = queue

    def should_adjust(self) -> bool:
        """Check if enough time has passed for adjustment."""
        return (time.time() - self._last_adjustment) >= self.adjustment_interval

    def get_system_metrics(self) -> dict[str, float]:
        """Collect current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            queue_depth = self._task_queue.qsize() if self._task_queue else 0

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "queue_depth": queue_depth,
                "available_memory_mb": memory.available / (1024 * 1024),
            }
        except Exception as e:
            self.logger.warning(f"Failed to collect system metrics: {e}")
            return {
                "cpu_percent": 50.0,
                "memory_percent": 50.0,
                "queue_depth": 0,
                "available_memory_mb": 0,
            }

    def calculate_optimal_workers(self, metrics: dict[str, float]) -> int:
        """
        Calculate optimal worker count based on system metrics.

        Scaling logic:
        - Scale UP: Low CPU + High queue depth + Available memory
        - Scale DOWN: High CPU + Low queue depth OR High memory pressure
        - MAINTAIN: Balanced conditions
        """
        cpu = metrics["cpu_percent"]
        memory = metrics["memory_percent"]
        queue_depth = int(metrics["queue_depth"])

        current = self.current_workers

        # Memory pressure limits all scaling
        if memory > self.memory_pressure_threshold:
            self.logger.debug(f"High memory pressure ({memory:.1f}%), limiting workers")
            return max(self.min_workers, current - 2)

        # High CPU with low queue = over-threading, scale down
        if (
            cpu > self.scale_down_cpu_threshold
            and queue_depth < self.scale_down_queue_threshold
        ):
            new_workers = max(self.min_workers, current - 2)
            self.logger.debug(
                f"High CPU ({cpu:.1f}%) + low queue ({queue_depth}), "
                f"scaling down: {current} → {new_workers}"
            )
            return new_workers

        # Low CPU with high queue = under-utilized, scale up
        if (
            cpu < self.scale_up_cpu_threshold
            and queue_depth > self.scale_up_queue_threshold
        ):
            new_workers = min(self.max_workers, current + 4)
            self.logger.debug(
                f"Low CPU ({cpu:.1f}%) + high queue ({queue_depth}), "
                f"scaling up: {current} → {new_workers}"
            )
            return new_workers

        # Gradual adjustment based on queue depth alone
        if queue_depth > self.scale_up_queue_threshold:
            # More work than workers, scale up gradually
            new_workers = min(self.max_workers, current + 2)
            self.logger.debug(
                f"High queue ({queue_depth}), gradual scale up: {current} → {new_workers}"
            )
            return new_workers

        if queue_depth < self.scale_down_queue_threshold and current > self.min_workers:
            # Very little work, scale down gradually
            new_workers = max(self.min_workers, current - 1)
            self.logger.debug(
                f"Low queue ({queue_depth}), gradual scale down: {current} → {new_workers}"
            )
            return new_workers

        # No adjustment needed
        return current

    def adjust_workers(self) -> bool:
        """
        Adjust worker count based on current system state.

        Returns:
            True if adjustment was made, False otherwise
        """
        if not self.should_adjust():
            return False

        if not self._executor:
            self.logger.warning("No executor set for adaptive pool")
            return False

        # Collect metrics
        metrics = self.get_system_metrics()
        optimal_workers = self.calculate_optimal_workers(metrics)

        # Update metrics
        if self.enable_monitoring:
            self._update_metrics(metrics)

        # Apply adjustment if needed
        if optimal_workers != self.current_workers:
            old_workers = self.current_workers
            self._resize_pool(optimal_workers)

            # Track adjustment
            self.metrics.total_adjustments += 1
            self.metrics.last_adjustment = datetime.utcnow()

            if optimal_workers > old_workers:
                self.metrics.scale_ups += 1
            else:
                self.metrics.scale_downs += 1

            self._last_adjustment = time.time()

            self.logger.info(
                f"Worker pool adjusted: {old_workers} → {optimal_workers} "
                f"(CPU: {metrics['cpu_percent']:.1f}%, "
                f"Mem: {metrics['memory_percent']:.1f}%, "
                f"Queue: {metrics['queue_depth']})"
            )

            return True

        self._last_adjustment = time.time()
        return False

    def _resize_pool(self, new_size: int) -> None:
        """
        Resize the thread pool executor.

        Note: ThreadPoolExecutor doesn't support dynamic resizing directly.
        We update _max_workers which affects future thread creation.
        Existing threads will naturally complete and not be replaced beyond new limit.
        """
        if not self._executor:
            return

        # Update max_workers attribute (affects future thread spawning)
        self._executor._max_workers = new_size
        self.current_workers = new_size
        self.metrics.current_workers = new_size

    def _update_metrics(self, system_metrics: dict[str, float]) -> None:
        """Update rolling average metrics."""
        # Update rolling averages (simple moving average)
        alpha = 0.2  # Smoothing factor

        self.metrics.avg_cpu_percent = (
            alpha * system_metrics["cpu_percent"]
            + (1 - alpha) * self.metrics.avg_cpu_percent
        )

        self.metrics.avg_memory_percent = (
            alpha * system_metrics["memory_percent"]
            + (1 - alpha) * self.metrics.avg_memory_percent
        )

        self.metrics.avg_queue_depth = (
            alpha * system_metrics["queue_depth"]
            + (1 - alpha) * self.metrics.avg_queue_depth
        )

    def record_task_time(self, duration: float) -> None:
        """Record task completion time for performance tracking."""
        self._recent_task_times.append(duration)

        # Calculate performance gain after baseline established
        if len(self._recent_task_times) >= 50:
            avg_time = sum(self._recent_task_times) / len(self._recent_task_times)

            if self._baseline_performance is None:
                self._baseline_performance = avg_time
            else:
                # Calculate percentage improvement (negative = slower, positive = faster)
                improvement = (
                    (self._baseline_performance - avg_time) / self._baseline_performance
                ) * 100
                self.metrics.performance_gain_percent = improvement

    def get_metrics(self) -> WorkerPoolMetrics:
        """Get current worker pool metrics."""
        return self.metrics

    def get_status_dict(self) -> dict[str, Any]:
        """Get status as dictionary for logging/monitoring."""
        return {
            "current_workers": self.current_workers,
            "min_workers": self.min_workers,
            "max_workers": self.max_workers,
            "total_adjustments": self.metrics.total_adjustments,
            "scale_ups": self.metrics.scale_ups,
            "scale_downs": self.metrics.scale_downs,
            "avg_cpu_percent": round(self.metrics.avg_cpu_percent, 1),
            "avg_memory_percent": round(self.metrics.avg_memory_percent, 1),
            "avg_queue_depth": round(self.metrics.avg_queue_depth, 1),
            "performance_gain_percent": round(self.metrics.performance_gain_percent, 2),
            "last_adjustment": (
                self.metrics.last_adjustment.isoformat()
                if self.metrics.last_adjustment
                else None
            ),
        }
