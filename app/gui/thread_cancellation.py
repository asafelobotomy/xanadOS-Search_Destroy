"""Cooperative thread cancellation utilities.
Provides a mixin to standardize cancellation across QThread subclasses.
Tracks cancellation request and completion times for latency metrics.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class CancellationMetric:
    name: str
    requested_at: float
    finished_at: float
    latency: float
    graceful: bool


_CANCELLATION_METRICS: list[CancellationMetric] = []
_METRICS_LOCK = threading.Lock()


class CooperativeCancellationMixin:
    cancellation_requested_at: float | None = None
    cancellation_finished_at: float | None = None
    _cancellation_name: str = "thread"
    _graceful_flag: bool = False

    def _register_cancellation_metric(
        self,
    ):  # pragma: no cover (simple logging wrapper)
        if self.cancellation_requested_at and self.cancellation_finished_at:
            metric = CancellationMetric(
                name=self._cancellation_name,
                requested_at=self.cancellation_requested_at,
                finished_at=self.cancellation_finished_at,
                latency=self.cancellation_finished_at - self.cancellation_requested_at,
                graceful=self._graceful_flag,
            )
            with _METRICS_LOCK:
                _CANCELLATION_METRICS.append(metric)
            logger.info(
                "CANCEL_METRIC name=%s latency=%.3fs graceful=%s",
                metric.name,
                metric.latency,
                metric.graceful,
            )

    def cooperative_cancel(self, *, graceful: bool = True):
        """Mark cancellation request; subclass stop_scan should call this first."""
        if self.cancellation_requested_at is None:
            self.cancellation_requested_at = time.time()
            self._graceful_flag = graceful

    def mark_cancellation_complete(self):
        if (
            self.cancellation_finished_at is None
            and self.cancellation_requested_at is not None
        ):
            self.cancellation_finished_at = time.time()
            self._register_cancellation_metric()

    def cancellation_latency(self) -> float | None:
        if self.cancellation_requested_at and self.cancellation_finished_at:
            return self.cancellation_finished_at - self.cancellation_requested_at
        return None

    @staticmethod
    def all_cancellation_metrics() -> list[CancellationMetric]:
        with _METRICS_LOCK:
            return list(_CANCELLATION_METRICS)


__all__ = [
    "CancellationMetric",
    "CooperativeCancellationMixin",
]
