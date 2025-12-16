#!/usr/bin/env python3
"""
Self-Optimizing Performance Tuner - Task 2.2.1

Implements reinforcement learning-based automatic performance optimization
for scan parameters, cache configuration, and resource allocation.

Features:
- Q-learning agent for parameter optimization
- Dynamic cache size tuning based on hit rate
- Worker pool optimization using historical patterns
- I/O strategy preference learning
- Safe rollback on performance degradation
- 30-day performance metrics tracking

Performance Targets:
- 10-15% performance improvement over baseline
- Rollback triggers on >5% performance drop
- Configuration changes logged for audit
- Manual override available for all parameters

Author: xanadOS Security Team
Date: December 16, 2025
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from app.utils.config import DATA_DIR, load_config, save_config


logger = logging.getLogger(__name__)


# Auto-tuner data directory
AUTOTUNER_DIR = DATA_DIR / "autotuner"
AUTOTUNER_DIR.mkdir(parents=True, exist_ok=True)

METRICS_DB = AUTOTUNER_DIR / "performance_metrics.json"
QTABLE_FILE = AUTOTUNER_DIR / "q_table.npy"
CONFIG_HISTORY = AUTOTUNER_DIR / "config_history.json"


class TuningParameter(Enum):
    """Parameters that can be auto-tuned."""

    MAX_WORKERS = "max_workers"
    CACHE_SIZE_MB = "cache_size_mb"
    SCAN_DEPTH = "scan_depth"
    IO_BUFFER_SIZE = "io_buffer_size"
    BATCH_SIZE = "batch_size"
    THREAD_POOL_SIZE = "thread_pool_size"


class PerformanceState(Enum):
    """Discrete performance states for Q-learning."""

    EXCELLENT = "excellent"  # All metrics in optimal range
    GOOD = "good"  # Most metrics acceptable
    ACCEPTABLE = "acceptable"  # Some degradation
    POOR = "poor"  # Significant issues
    CRITICAL = "critical"  # Severe performance problems


class TuningAction(Enum):
    """Actions the tuner can take."""

    INCREASE_WORKERS = "increase_workers"
    DECREASE_WORKERS = "decrease_workers"
    INCREASE_CACHE = "increase_cache"
    DECREASE_CACHE = "decrease_cache"
    INCREASE_DEPTH = "increase_depth"
    DECREASE_DEPTH = "decrease_depth"
    INCREASE_BUFFER = "increase_buffer"
    DECREASE_BUFFER = "decrease_buffer"
    NO_ACTION = "no_action"


@dataclass
class AutoTuneMetrics:
    """
    Performance metrics for auto-tuning decisions.

    Metrics tracked:
    - avg_scan_time: Average time per scan (seconds)
    - cache_hit_rate: Cache hit rate (0.0-1.0)
    - throughput_mbps: Throughput in MB/s
    - cpu_utilization: CPU usage (0.0-1.0)
    - memory_usage_mb: Memory usage in MB
    """

    avg_scan_time: float
    cache_hit_rate: float
    throughput_mbps: float
    cpu_utilization: float
    memory_usage_mb: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Target ranges for optimal performance
    target_cpu: tuple[float, float] = (0.60, 0.80)  # 60-80% CPU
    target_cache_hit: float = 0.85  # 85%+ cache hit rate
    target_throughput: float = 3000.0  # 3 GB/s (3000 MB/s)

    def get_state(self) -> PerformanceState:
        """Determine performance state from metrics."""
        score = 0

        # CPU utilization scoring
        if self.target_cpu[0] <= self.cpu_utilization <= self.target_cpu[1]:
            score += 2
        elif (
            self.cpu_utilization < self.target_cpu[0] * 0.5
            or self.cpu_utilization > 0.95
        ):
            score -= 2
        else:
            score += 1

        # Cache hit rate scoring
        if self.cache_hit_rate >= self.target_cache_hit:
            score += 2
        elif self.cache_hit_rate >= 0.70:
            score += 1
        else:
            score -= 1

        # Throughput scoring
        if self.throughput_mbps >= self.target_throughput:
            score += 2
        elif self.throughput_mbps >= self.target_throughput * 0.7:
            score += 1
        else:
            score -= 1

        # Memory scoring (penalize excessive usage)
        if self.memory_usage_mb < 1000:
            score += 1
        elif self.memory_usage_mb > 5000:
            score -= 2

        # Map score to state
        if score >= 5:
            return PerformanceState.EXCELLENT
        elif score >= 3:
            return PerformanceState.GOOD
        elif score >= 0:
            return PerformanceState.ACCEPTABLE
        elif score >= -3:
            return PerformanceState.POOR
        else:
            return PerformanceState.CRITICAL

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "avg_scan_time": self.avg_scan_time,
            "cache_hit_rate": self.cache_hit_rate,
            "throughput_mbps": self.throughput_mbps,
            "cpu_utilization": self.cpu_utilization,
            "memory_usage_mb": self.memory_usage_mb,
            "timestamp": self.timestamp,
            "state": self.get_state().value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoTuneMetrics:
        """Create from dictionary."""
        return cls(
            avg_scan_time=data["avg_scan_time"],
            cache_hit_rate=data["cache_hit_rate"],
            throughput_mbps=data["throughput_mbps"],
            cpu_utilization=data["cpu_utilization"],
            memory_usage_mb=data["memory_usage_mb"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )


@dataclass
class ConfigurationSnapshot:
    """Snapshot of current configuration."""

    max_workers: int
    cache_size_mb: int
    scan_depth: int
    io_buffer_size: int
    batch_size: int
    thread_pool_size: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfigurationSnapshot:
        """Create from dictionary."""
        return cls(**data)


class AutoTuner:
    """
    Self-optimizing performance tuner using Q-learning.

    Features:
    - Learns optimal configuration from historical performance
    - Automatically adjusts parameters based on workload
    - Safe rollback on performance degradation
    - 30-day performance metrics window
    - Audit logging for all changes

    Q-Learning Parameters:
    - Learning rate (α): 0.1
    - Discount factor (γ): 0.9
    - Exploration rate (ε): 0.1 (10% random actions)
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        exploration_rate: float = 0.1,
        metrics_window_days: int = 30,
        rollback_threshold: float = 0.05,  # 5% degradation
    ):
        """
        Initialize the auto-tuner.

        Args:
            learning_rate: Q-learning learning rate (α)
            discount_factor: Q-learning discount factor (γ)
            exploration_rate: Probability of random action (ε)
            metrics_window_days: Days of metrics to retain
            rollback_threshold: Performance degradation threshold for rollback
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.metrics_window_days = metrics_window_days
        self.rollback_threshold = rollback_threshold

        # Performance metrics history (30-day window)
        self.metrics_history: deque[AutoTuneMetrics] = deque(maxlen=1000)

        # Configuration history
        self.config_history: deque[ConfigurationSnapshot] = deque(maxlen=100)

        # Q-table: Q(state, action) -> expected reward
        # States: 5 (EXCELLENT, GOOD, ACCEPTABLE, POOR, CRITICAL)
        # Actions: 9 (see TuningAction)
        self.q_table = np.zeros((5, 9))

        # State-action mapping
        self.states = list(PerformanceState)
        self.actions = list(TuningAction)

        # Baseline metrics for comparison
        self.baseline_metrics: AutoTuneMetrics | None = None

        # Current configuration
        self.current_config: ConfigurationSnapshot | None = None

        # Load persisted data
        self._load_state()

    def _load_state(self) -> None:
        """Load persisted metrics and Q-table."""
        # Load metrics history
        if METRICS_DB.exists():
            with open(METRICS_DB, "r") as f:
                data = json.load(f)
                for metric_dict in data.get("metrics", []):
                    self.metrics_history.append(AutoTuneMetrics.from_dict(metric_dict))

                # Set baseline if available
                if data.get("baseline"):
                    self.baseline_metrics = AutoTuneMetrics.from_dict(data["baseline"])

        # Load Q-table
        if QTABLE_FILE.exists():
            self.q_table = np.load(QTABLE_FILE)

        # Load config history
        if CONFIG_HISTORY.exists():
            with open(CONFIG_HISTORY, "r") as f:
                data = json.load(f)
                for config_dict in data.get("configs", []):
                    self.config_history.append(
                        ConfigurationSnapshot.from_dict(config_dict)
                    )

    def _save_state(self) -> None:
        """Persist metrics and Q-table."""
        # Save metrics history
        with open(METRICS_DB, "w") as f:
            json.dump(
                {
                    "metrics": [m.to_dict() for m in self.metrics_history],
                    "baseline": (
                        self.baseline_metrics.to_dict()
                        if self.baseline_metrics
                        else None
                    ),
                },
                f,
                indent=2,
            )

        # Save Q-table
        np.save(QTABLE_FILE, self.q_table)

        # Save config history
        with open(CONFIG_HISTORY, "w") as f:
            json.dump(
                {
                    "configs": [c.to_dict() for c in self.config_history],
                },
                f,
                indent=2,
            )

    def record_metrics(self, metrics: AutoTuneMetrics) -> None:
        """Record new performance metrics."""
        self.metrics_history.append(metrics)

        # Set baseline on first metrics
        if self.baseline_metrics is None:
            self.baseline_metrics = metrics
            logger.info(f"Baseline metrics established: {metrics.to_dict()}")

        # Cleanup old metrics (>30 days)
        cutoff = datetime.utcnow() - timedelta(days=self.metrics_window_days)
        while (
            self.metrics_history
            and datetime.fromisoformat(self.metrics_history[0].timestamp) < cutoff
        ):
            self.metrics_history.popleft()

        self._save_state()

    def get_recent_metrics(self, hours: int = 24) -> list[AutoTuneMetrics]:
        """Get metrics from last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            m
            for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff
        ]

    def get_average_metrics(self, hours: int = 24) -> AutoTuneMetrics | None:
        """Calculate average metrics over time window."""
        recent = self.get_recent_metrics(hours)
        if not recent:
            return None

        return AutoTuneMetrics(
            avg_scan_time=np.mean([m.avg_scan_time for m in recent]),
            cache_hit_rate=np.mean([m.cache_hit_rate for m in recent]),
            throughput_mbps=np.mean([m.throughput_mbps for m in recent]),
            cpu_utilization=np.mean([m.cpu_utilization for m in recent]),
            memory_usage_mb=np.mean([m.memory_usage_mb for m in recent]),
        )

    def _get_state_index(self, state: PerformanceState) -> int:
        """Get index for state in Q-table."""
        return self.states.index(state)

    def _get_action_index(self, action: TuningAction) -> int:
        """Get index for action in Q-table."""
        return self.actions.index(action)

    def _select_action(self, state: PerformanceState) -> TuningAction:
        """Select action using ε-greedy policy."""
        if np.random.random() < self.exploration_rate:
            # Exploration: random action
            return np.random.choice(self.actions)
        else:
            # Exploitation: best action from Q-table
            state_idx = self._get_state_index(state)
            action_idx = np.argmax(self.q_table[state_idx])
            return self.actions[action_idx]

    def _calculate_reward(
        self,
        prev_metrics: AutoTuneMetrics,
        new_metrics: AutoTuneMetrics,
    ) -> float:
        """
        Calculate reward for action.

        Reward components:
        - Throughput improvement: +10 per 100 MB/s increase
        - Cache hit rate improvement: +20 per 10% increase
        - CPU optimization: +5 if in target range
        - Scan time reduction: +10 per second saved
        - Penalties for degradation
        """
        reward = 0.0

        # Throughput reward
        throughput_delta = new_metrics.throughput_mbps - prev_metrics.throughput_mbps
        reward += (throughput_delta / 100.0) * 10.0

        # Cache hit rate reward
        cache_delta = new_metrics.cache_hit_rate - prev_metrics.cache_hit_rate
        reward += (cache_delta / 0.1) * 20.0

        # CPU utilization reward (bonus for target range)
        if (
            new_metrics.target_cpu[0]
            <= new_metrics.cpu_utilization
            <= new_metrics.target_cpu[1]
        ):
            reward += 5.0

        # Scan time reward (faster is better)
        time_delta = prev_metrics.avg_scan_time - new_metrics.avg_scan_time
        reward += time_delta * 10.0

        # Penalty for excessive resource usage
        if new_metrics.cpu_utilization > 0.95:
            reward -= 10.0
        if new_metrics.memory_usage_mb > 5000:
            reward -= 5.0

        return reward

    def update_q_table(
        self,
        state: PerformanceState,
        action: TuningAction,
        reward: float,
        next_state: PerformanceState,
    ) -> None:
        """Update Q-table using Q-learning update rule."""
        state_idx = self._get_state_index(state)
        action_idx = self._get_action_index(action)
        next_state_idx = self._get_state_index(next_state)

        # Q-learning update: Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        current_q = self.q_table[state_idx, action_idx]
        max_next_q = np.max(self.q_table[next_state_idx])

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[state_idx, action_idx] = new_q
        self._save_state()

    def apply_action(
        self,
        action: TuningAction,
        current_config: ConfigurationSnapshot,
    ) -> ConfigurationSnapshot:
        """Apply tuning action to configuration."""
        new_config = ConfigurationSnapshot(
            max_workers=current_config.max_workers,
            cache_size_mb=current_config.cache_size_mb,
            scan_depth=current_config.scan_depth,
            io_buffer_size=current_config.io_buffer_size,
            batch_size=current_config.batch_size,
            thread_pool_size=current_config.thread_pool_size,
        )

        # Apply action with safe bounds
        if action == TuningAction.INCREASE_WORKERS:
            new_config.max_workers = min(current_config.max_workers + 2, 32)
        elif action == TuningAction.DECREASE_WORKERS:
            new_config.max_workers = max(current_config.max_workers - 2, 2)
        elif action == TuningAction.INCREASE_CACHE:
            new_config.cache_size_mb = min(current_config.cache_size_mb + 128, 2048)
        elif action == TuningAction.DECREASE_CACHE:
            new_config.cache_size_mb = max(current_config.cache_size_mb - 128, 256)
        elif action == TuningAction.INCREASE_DEPTH:
            new_config.scan_depth = min(current_config.scan_depth + 1, 15)
        elif action == TuningAction.DECREASE_DEPTH:
            new_config.scan_depth = max(current_config.scan_depth - 1, 3)
        elif action == TuningAction.INCREASE_BUFFER:
            new_config.io_buffer_size = min(current_config.io_buffer_size * 2, 1048576)
        elif action == TuningAction.DECREASE_BUFFER:
            new_config.io_buffer_size = max(current_config.io_buffer_size // 2, 8192)

        return new_config

    def recommend_tuning(
        self,
        current_metrics: AutoTuneMetrics,
        current_config: ConfigurationSnapshot,
    ) -> tuple[TuningAction, ConfigurationSnapshot]:
        """
        Recommend tuning action based on current state.

        Returns:
            Tuple of (action, new_config)
        """
        state = current_metrics.get_state()
        action = self._select_action(state)
        new_config = self.apply_action(action, current_config)

        logger.info(
            f"Tuning recommendation: state={state.value}, action={action.value}, "
            f"config_changes={self._config_diff(current_config, new_config)}"
        )

        return action, new_config

    def _config_diff(
        self,
        old: ConfigurationSnapshot,
        new: ConfigurationSnapshot,
    ) -> dict[str, tuple[Any, Any]]:
        """Calculate configuration differences."""
        diff = {}
        for field in [
            "max_workers",
            "cache_size_mb",
            "scan_depth",
            "io_buffer_size",
            "batch_size",
            "thread_pool_size",
        ]:
            old_val = getattr(old, field)
            new_val = getattr(new, field)
            if old_val != new_val:
                diff[field] = (old_val, new_val)
        return diff

    def check_rollback_needed(
        self,
        new_metrics: AutoTuneMetrics,
        baseline_window_hours: int = 24,
    ) -> bool:
        """
        Check if rollback is needed due to performance degradation.

        Args:
            new_metrics: Current metrics
            baseline_window_hours: Hours to average for baseline

        Returns:
            True if rollback needed (>5% degradation)
        """
        baseline = self.get_average_metrics(baseline_window_hours)
        if not baseline:
            return False

        # Check throughput degradation
        throughput_degradation = (
            baseline.throughput_mbps - new_metrics.throughput_mbps
        ) / baseline.throughput_mbps

        if throughput_degradation > self.rollback_threshold:
            logger.warning(
                f"Rollback needed: throughput degraded by {throughput_degradation*100:.1f}% "
                f"(threshold: {self.rollback_threshold*100:.1f}%)"
            )
            return True

        return False

    def rollback_configuration(self) -> ConfigurationSnapshot | None:
        """Rollback to previous configuration."""
        if len(self.config_history) < 2:
            logger.warning("No previous configuration to rollback to")
            return None

        # Get second-to-last config (last is current)
        previous_config = self.config_history[-2]
        logger.info(f"Rolling back to configuration from {previous_config.timestamp}")

        return previous_config

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get optimization statistics."""
        if not self.metrics_history or not self.baseline_metrics:
            return {}

        recent = self.get_average_metrics(24)
        if not recent:
            return {}

        return {
            "baseline_throughput": self.baseline_metrics.throughput_mbps,
            "current_throughput": recent.throughput_mbps,
            "improvement_pct": (
                (recent.throughput_mbps - self.baseline_metrics.throughput_mbps)
                / self.baseline_metrics.throughput_mbps
                * 100
            ),
            "baseline_cache_hit": self.baseline_metrics.cache_hit_rate,
            "current_cache_hit": recent.cache_hit_rate,
            "total_metrics_recorded": len(self.metrics_history),
            "total_config_changes": len(self.config_history),
            "q_table_max_values": self.q_table.max(axis=1).tolist(),
        }
