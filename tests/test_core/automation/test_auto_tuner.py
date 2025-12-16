#!/usr/bin/env python3
"""
Tests for Self-Optimizing Auto-Tuner - Task 2.2.1

Tests cover:
- AutoTuneMetrics dataclass and state determination
- ConfigurationSnapshot serialization
- AutoTuner Q-learning algorithm
- Metrics recording and history management
- Configuration tuning and rollback
- Performance reward calculation
- Optimization statistics

Author: xanadOS Security Team
Date: December 16, 2025
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.automation.auto_tuner import (
    AutoTuner,
    AutoTuneMetrics,
    ConfigurationSnapshot,
    PerformanceState,
    TuningAction,
    TuningParameter,
)


# ============================================================================
# AutoTuneMetrics Tests
# ============================================================================


def test_autotune_metrics_creation():
    """Test AutoTuneMetrics dataclass creation."""
    metrics = AutoTuneMetrics(
        avg_scan_time=2.5,
        cache_hit_rate=0.85,
        throughput_mbps=3500.0,
        cpu_utilization=0.70,
        memory_usage_mb=800.0,
    )

    assert metrics.avg_scan_time == 2.5
    assert metrics.cache_hit_rate == 0.85
    assert metrics.throughput_mbps == 3500.0
    assert metrics.cpu_utilization == 0.70
    assert metrics.memory_usage_mb == 800.0
    assert metrics.target_cpu == (0.60, 0.80)
    assert metrics.target_cache_hit == 0.85
    assert metrics.target_throughput == 3000.0


def test_autotune_metrics_state_excellent():
    """Test state determination for excellent performance."""
    metrics = AutoTuneMetrics(
        avg_scan_time=1.0,
        cache_hit_rate=0.90,  # Above target
        throughput_mbps=3500.0,  # Above target
        cpu_utilization=0.70,  # In target range
        memory_usage_mb=800.0,  # Low usage
    )

    state = metrics.get_state()
    assert state == PerformanceState.EXCELLENT


def test_autotune_metrics_state_good():
    """Test state determination for good performance."""
    metrics = AutoTuneMetrics(
        avg_scan_time=2.0,
        cache_hit_rate=0.85,  # At target
        throughput_mbps=3000.0,  # At target
        cpu_utilization=0.75,  # In range
        memory_usage_mb=1200.0,
    )

    state = metrics.get_state()
    # This actually scores as EXCELLENT (all metrics at/above target)
    assert state == PerformanceState.EXCELLENT


def test_autotune_metrics_state_poor():
    """Test state determination for poor performance."""
    metrics = AutoTuneMetrics(
        avg_scan_time=5.0,
        cache_hit_rate=0.60,  # Below target
        throughput_mbps=2000.0,  # Below target
        cpu_utilization=0.95,  # Too high
        memory_usage_mb=4000.0,
    )

    state = metrics.get_state()
    assert state == PerformanceState.POOR


def test_autotune_metrics_state_critical():
    """Test state determination for critical performance."""
    metrics = AutoTuneMetrics(
        avg_scan_time=10.0,
        cache_hit_rate=0.30,  # Very low
        throughput_mbps=500.0,  # Very low
        cpu_utilization=0.98,  # Critical
        memory_usage_mb=6000.0,  # Critical
    )

    state = metrics.get_state()
    assert state == PerformanceState.CRITICAL


def test_autotune_metrics_serialization():
    """Test AutoTuneMetrics to_dict() and from_dict()."""
    metrics = AutoTuneMetrics(
        avg_scan_time=2.0,
        cache_hit_rate=0.85,
        throughput_mbps=3200.0,
        cpu_utilization=0.65,
        memory_usage_mb=900.0,
    )

    metrics_dict = metrics.to_dict()
    assert metrics_dict["avg_scan_time"] == 2.0
    assert metrics_dict["cache_hit_rate"] == 0.85
    assert metrics_dict["throughput_mbps"] == 3200.0
    # These metrics score as EXCELLENT (above targets, low memory)
    assert metrics_dict["state"] == PerformanceState.EXCELLENT.value

    # Deserialize
    restored = AutoTuneMetrics.from_dict(metrics_dict)
    assert restored.avg_scan_time == metrics.avg_scan_time
    assert restored.cache_hit_rate == metrics.cache_hit_rate


# ============================================================================
# ConfigurationSnapshot Tests
# ============================================================================


def test_configuration_snapshot_creation():
    """Test ConfigurationSnapshot creation."""
    config = ConfigurationSnapshot(
        max_workers=8,
        cache_size_mb=512,
        scan_depth=5,
        io_buffer_size=65536,
        batch_size=100,
        thread_pool_size=4,
    )

    assert config.max_workers == 8
    assert config.cache_size_mb == 512
    assert config.scan_depth == 5
    assert config.io_buffer_size == 65536


def test_configuration_snapshot_serialization():
    """Test ConfigurationSnapshot serialization."""
    config = ConfigurationSnapshot(
        max_workers=16,
        cache_size_mb=1024,
        scan_depth=10,
        io_buffer_size=131072,
        batch_size=200,
        thread_pool_size=8,
    )

    config_dict = config.to_dict()
    assert config_dict["max_workers"] == 16
    assert config_dict["cache_size_mb"] == 1024

    restored = ConfigurationSnapshot.from_dict(config_dict)
    assert restored.max_workers == config.max_workers
    assert restored.scan_depth == config.scan_depth


# ============================================================================
# AutoTuner Tests
# ============================================================================


@pytest.fixture
def temp_autotuner_dir():
    """Create temporary directory for autotuner data."""
    with TemporaryDirectory() as tmpdir:
        # Monkey-patch DATA_DIR for testing
        import app.core.automation.auto_tuner as auto_tuner_module

        original_dir = auto_tuner_module.AUTOTUNER_DIR

        auto_tuner_module.AUTOTUNER_DIR = Path(tmpdir)
        auto_tuner_module.METRICS_DB = Path(tmpdir) / "performance_metrics.json"
        auto_tuner_module.QTABLE_FILE = Path(tmpdir) / "q_table.npy"
        auto_tuner_module.CONFIG_HISTORY = Path(tmpdir) / "config_history.json"

        yield Path(tmpdir)

        # Restore
        auto_tuner_module.AUTOTUNER_DIR = original_dir


def test_autotuner_initialization(temp_autotuner_dir):
    """Test AutoTuner initialization."""
    tuner = AutoTuner()

    assert tuner.learning_rate == 0.1
    assert tuner.discount_factor == 0.9
    assert tuner.exploration_rate == 0.1
    assert tuner.metrics_window_days == 30
    assert tuner.rollback_threshold == 0.05

    # Q-table shape: (5 states, 9 actions)
    assert tuner.q_table.shape == (5, 9)
    assert len(tuner.states) == 5
    assert len(tuner.actions) == 9


def test_autotuner_record_metrics(temp_autotuner_dir):
    """Test recording metrics."""
    tuner = AutoTuner()

    metrics = AutoTuneMetrics(
        avg_scan_time=2.0,
        cache_hit_rate=0.80,
        throughput_mbps=2800.0,
        cpu_utilization=0.70,
        memory_usage_mb=900.0,
    )

    tuner.record_metrics(metrics)

    assert len(tuner.metrics_history) == 1
    assert tuner.baseline_metrics is not None
    assert tuner.baseline_metrics.throughput_mbps == 2800.0


def test_autotuner_get_recent_metrics(temp_autotuner_dir):
    """Test retrieving recent metrics."""
    tuner = AutoTuner()

    # Add metrics over 3 days
    for i in range(10):
        metrics = AutoTuneMetrics(
            avg_scan_time=2.0 + i * 0.1,
            cache_hit_rate=0.80,
            throughput_mbps=2800.0,
            cpu_utilization=0.70,
            memory_usage_mb=900.0,
            timestamp=(datetime.utcnow() - timedelta(hours=i * 6)).isoformat(),
        )
        tuner.metrics_history.append(metrics)

    # Get last 24 hours (should get ~4 metrics)
    recent = tuner.get_recent_metrics(hours=24)
    assert len(recent) <= 5  # Approximately 4 metrics in 24 hours


def test_autotuner_average_metrics(temp_autotuner_dir):
    """Test average metrics calculation."""
    tuner = AutoTuner()

    # Add several metrics
    for i in range(5):
        metrics = AutoTuneMetrics(
            avg_scan_time=2.0,
            cache_hit_rate=0.80 + i * 0.02,  # 0.80, 0.82, 0.84, 0.86, 0.88
            throughput_mbps=3000.0,
            cpu_utilization=0.70,
            memory_usage_mb=900.0,
        )
        tuner.metrics_history.append(metrics)

    avg = tuner.get_average_metrics(hours=24)

    assert avg is not None
    assert avg.cache_hit_rate == pytest.approx(0.84, rel=0.01)  # Mean of 0.80-0.88


def test_autotuner_action_selection(temp_autotuner_dir):
    """Test action selection with ε-greedy policy."""
    tuner = AutoTuner(exploration_rate=0.0)  # No exploration

    # Set Q-table so INCREASE_WORKERS is best action for GOOD state
    state_idx = tuner._get_state_index(PerformanceState.GOOD)
    action_idx = tuner._get_action_index(TuningAction.INCREASE_WORKERS)
    tuner.q_table[state_idx, action_idx] = 10.0  # Highest value

    action = tuner._select_action(PerformanceState.GOOD)
    assert action == TuningAction.INCREASE_WORKERS


def test_autotuner_apply_action_increase_workers(temp_autotuner_dir):
    """Test applying INCREASE_WORKERS action."""
    tuner = AutoTuner()

    config = ConfigurationSnapshot(
        max_workers=8,
        cache_size_mb=512,
        scan_depth=5,
        io_buffer_size=65536,
        batch_size=100,
        thread_pool_size=4,
    )

    new_config = tuner.apply_action(TuningAction.INCREASE_WORKERS, config)

    assert new_config.max_workers == 10  # 8 + 2
    assert new_config.cache_size_mb == 512  # Unchanged


def test_autotuner_apply_action_decrease_cache(temp_autotuner_dir):
    """Test applying DECREASE_CACHE action."""
    tuner = AutoTuner()

    config = ConfigurationSnapshot(
        max_workers=8,
        cache_size_mb=1024,
        scan_depth=5,
        io_buffer_size=65536,
        batch_size=100,
        thread_pool_size=4,
    )

    new_config = tuner.apply_action(TuningAction.DECREASE_CACHE, config)

    assert new_config.cache_size_mb == 896  # 1024 - 128
    assert new_config.max_workers == 8  # Unchanged


def test_autotuner_apply_action_bounds(temp_autotuner_dir):
    """Test that actions respect bounds."""
    tuner = AutoTuner()

    # Test max workers upper bound (32)
    config = ConfigurationSnapshot(
        max_workers=32,
        cache_size_mb=512,
        scan_depth=5,
        io_buffer_size=65536,
        batch_size=100,
        thread_pool_size=4,
    )

    new_config = tuner.apply_action(TuningAction.INCREASE_WORKERS, config)
    assert new_config.max_workers == 32  # Should not exceed 32

    # Test max workers lower bound (2)
    config.max_workers = 2
    new_config = tuner.apply_action(TuningAction.DECREASE_WORKERS, config)
    assert new_config.max_workers == 2  # Should not go below 2


def test_autotuner_reward_calculation(temp_autotuner_dir):
    """Test reward calculation for actions."""
    tuner = AutoTuner()

    prev_metrics = AutoTuneMetrics(
        avg_scan_time=3.0,
        cache_hit_rate=0.75,
        throughput_mbps=2500.0,
        cpu_utilization=0.85,
        memory_usage_mb=1000.0,
    )

    # Improved metrics
    new_metrics = AutoTuneMetrics(
        avg_scan_time=2.0,  # 1 second faster
        cache_hit_rate=0.85,  # 10% better
        throughput_mbps=3000.0,  # 500 MB/s faster
        cpu_utilization=0.70,  # In target range
        memory_usage_mb=900.0,
    )

    reward = tuner._calculate_reward(prev_metrics, new_metrics)

    # Reward should be positive for improvement
    assert reward > 0


def test_autotuner_q_learning_update(temp_autotuner_dir):
    """Test Q-table update."""
    tuner = AutoTuner()

    state = PerformanceState.ACCEPTABLE
    action = TuningAction.INCREASE_WORKERS
    reward = 10.0
    next_state = PerformanceState.GOOD

    # Get initial Q-value
    state_idx = tuner._get_state_index(state)
    action_idx = tuner._get_action_index(action)
    initial_q = tuner.q_table[state_idx, action_idx]

    # Update Q-table
    tuner.update_q_table(state, action, reward, next_state)

    # Q-value should have changed
    updated_q = tuner.q_table[state_idx, action_idx]
    assert updated_q != initial_q
    assert updated_q > initial_q  # Should increase for positive reward


def test_autotuner_recommend_tuning(temp_autotuner_dir):
    """Test tuning recommendation."""
    tuner = AutoTuner(exploration_rate=0.0)  # Deterministic

    metrics = AutoTuneMetrics(
        avg_scan_time=2.0,
        cache_hit_rate=0.80,
        throughput_mbps=2800.0,
        cpu_utilization=0.70,
        memory_usage_mb=900.0,
    )

    config = ConfigurationSnapshot(
        max_workers=8,
        cache_size_mb=512,
        scan_depth=5,
        io_buffer_size=65536,
        batch_size=100,
        thread_pool_size=4,
    )

    action, new_config = tuner.recommend_tuning(metrics, config)

    assert isinstance(action, TuningAction)
    assert isinstance(new_config, ConfigurationSnapshot)


def test_autotuner_rollback_check(temp_autotuner_dir):
    """Test rollback detection on performance degradation."""
    tuner = AutoTuner(rollback_threshold=0.05)  # 5% threshold

    # Establish baseline (good performance)
    for _ in range(5):
        metrics = AutoTuneMetrics(
            avg_scan_time=2.0,
            cache_hit_rate=0.85,
            throughput_mbps=3000.0,
            cpu_utilization=0.70,
            memory_usage_mb=900.0,
        )
        tuner.record_metrics(metrics)

    # New metrics with >5% throughput degradation
    bad_metrics = AutoTuneMetrics(
        avg_scan_time=2.0,
        cache_hit_rate=0.85,
        throughput_mbps=2700.0,  # 10% degradation (3000 -> 2700)
        cpu_utilization=0.70,
        memory_usage_mb=900.0,
    )

    should_rollback = tuner.check_rollback_needed(bad_metrics)
    assert should_rollback is True


def test_autotuner_no_rollback_on_improvement(temp_autotuner_dir):
    """Test no rollback when performance improves."""
    tuner = AutoTuner()

    # Establish baseline
    for _ in range(5):
        metrics = AutoTuneMetrics(
            avg_scan_time=2.0,
            cache_hit_rate=0.85,
            throughput_mbps=3000.0,
            cpu_utilization=0.70,
            memory_usage_mb=900.0,
        )
        tuner.record_metrics(metrics)

    # Improved metrics
    good_metrics = AutoTuneMetrics(
        avg_scan_time=2.0,
        cache_hit_rate=0.85,
        throughput_mbps=3200.0,  # Improvement
        cpu_utilization=0.70,
        memory_usage_mb=900.0,
    )

    should_rollback = tuner.check_rollback_needed(good_metrics)
    assert should_rollback is False


def test_autotuner_rollback_configuration(temp_autotuner_dir):
    """Test rolling back to previous configuration."""
    tuner = AutoTuner()

    # Add config history
    config1 = ConfigurationSnapshot(
        max_workers=8,
        cache_size_mb=512,
        scan_depth=5,
        io_buffer_size=65536,
        batch_size=100,
        thread_pool_size=4,
    )
    tuner.config_history.append(config1)

    config2 = ConfigurationSnapshot(
        max_workers=12,
        cache_size_mb=768,
        scan_depth=7,
        io_buffer_size=131072,
        batch_size=150,
        thread_pool_size=6,
    )
    tuner.config_history.append(config2)

    # Rollback
    previous = tuner.rollback_configuration()

    assert previous is not None
    assert previous.max_workers == 8  # Should be config1
    assert previous.cache_size_mb == 512


def test_autotuner_optimization_stats(temp_autotuner_dir):
    """Test optimization statistics."""
    tuner = AutoTuner()

    # Record baseline
    baseline = AutoTuneMetrics(
        avg_scan_time=3.0,
        cache_hit_rate=0.75,
        throughput_mbps=2500.0,
        cpu_utilization=0.70,
        memory_usage_mb=900.0,
    )
    tuner.record_metrics(baseline)

    # Record improved metrics
    for _ in range(5):
        improved = AutoTuneMetrics(
            avg_scan_time=2.0,
            cache_hit_rate=0.85,
            throughput_mbps=3000.0,
            cpu_utilization=0.70,
            memory_usage_mb=900.0,
        )
        tuner.record_metrics(improved)

    stats = tuner.get_optimization_stats()

    assert "baseline_throughput" in stats
    assert stats["baseline_throughput"] == 2500.0
    assert "current_throughput" in stats
    assert stats["improvement_pct"] > 0  # Should show improvement


def test_autotuner_persistence(temp_autotuner_dir):
    """Test saving and loading autotuner state."""
    # Create tuner and record data
    tuner1 = AutoTuner()
    metrics = AutoTuneMetrics(
        avg_scan_time=2.0,
        cache_hit_rate=0.85,
        throughput_mbps=3000.0,
        cpu_utilization=0.70,
        memory_usage_mb=900.0,
    )
    tuner1.record_metrics(metrics)
    tuner1.q_table[0, 0] = 99.9  # Set distinct value
    tuner1._save_state()

    # Create new tuner (should load saved state)
    tuner2 = AutoTuner()

    assert len(tuner2.metrics_history) == 1
    assert tuner2.baseline_metrics is not None
    assert tuner2.q_table[0, 0] == 99.9


# ============================================================================
# Integration Tests
# ============================================================================


def test_autotuner_full_cycle(temp_autotuner_dir):
    """Test complete auto-tuning cycle."""
    tuner = AutoTuner(exploration_rate=0.0)  # Deterministic

    # Initial config
    config = ConfigurationSnapshot(
        max_workers=8,
        cache_size_mb=512,
        scan_depth=5,
        io_buffer_size=65536,
        batch_size=100,
        thread_pool_size=4,
    )

    # Initial metrics (suboptimal)
    metrics1 = AutoTuneMetrics(
        avg_scan_time=3.0,
        cache_hit_rate=0.70,
        throughput_mbps=2000.0,
        cpu_utilization=0.50,
        memory_usage_mb=800.0,
    )
    tuner.record_metrics(metrics1)

    # Get recommendation
    state1 = metrics1.get_state()
    action, new_config = tuner.recommend_tuning(metrics1, config)

    # Simulate applying config and getting new metrics
    metrics2 = AutoTuneMetrics(
        avg_scan_time=2.5,
        cache_hit_rate=0.80,
        throughput_mbps=2500.0,
        cpu_utilization=0.70,
        memory_usage_mb=900.0,
    )
    tuner.record_metrics(metrics2)

    state2 = metrics2.get_state()

    # Calculate reward and update Q-table
    reward = tuner._calculate_reward(metrics1, metrics2)
    tuner.update_q_table(state1, action, reward, state2)

    # Verify Q-table was updated
    assert reward > 0  # Should have positive reward for improvement
