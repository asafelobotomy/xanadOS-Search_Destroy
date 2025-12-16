"""
Tests for adaptive worker pool scaling functionality.

Tests the AdaptiveWorkerPool class and its integration with
UnifiedScannerEngine and UnifiedThreadingManager.
"""

import asyncio
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.adaptive_worker_pool import AdaptiveWorkerPool, WorkerPoolMetrics


@pytest.fixture
def adaptive_pool():
    """Create an AdaptiveWorkerPool instance for testing."""
    return AdaptiveWorkerPool(
        min_workers=2,
        max_workers=16,
        adjustment_interval=1.0,  # Faster for tests
    )


@pytest.fixture
def mock_executor():
    """Create a mock ThreadPoolExecutor."""
    executor = MagicMock()
    executor._max_workers = 4
    executor._threads = set()
    return executor


@pytest.fixture
def mock_queue():
    """Create a mock asyncio.Queue."""
    queue = MagicMock()
    queue.qsize = MagicMock(return_value=0)
    return queue


class TestAdaptiveWorkerPoolInitialization:
    """Test AdaptiveWorkerPool initialization and configuration."""

    def test_auto_calculate_workers(self):
        """Test automatic worker calculation based on CPU cores."""
        pool = AdaptiveWorkerPool()

        # Should use process_cpu_count() or cpu_count()
        cpu_count = (
            os.process_cpu_count()
            if hasattr(os, "process_cpu_count")
            else os.cpu_count() or 1
        )

        assert pool.min_workers == max(4, cpu_count)
        assert pool.max_workers == min(100, cpu_count * 12)
        assert pool.current_workers == pool.min_workers

    def test_custom_worker_limits(self):
        """Test custom min/max worker configuration."""
        pool = AdaptiveWorkerPool(min_workers=8, max_workers=32)

        assert pool.min_workers == 8
        assert pool.max_workers == 32
        assert pool.current_workers == 8

    def test_adjustment_interval_configuration(self):
        """Test custom adjustment interval."""
        pool = AdaptiveWorkerPool(adjustment_interval=10.0)

        assert pool.adjustment_interval == 10.0


class TestSystemMetrics:
    """Test system metrics collection."""

    def test_get_system_metrics_without_executor(self, adaptive_pool):
        """Test metrics collection without executor configured."""
        metrics = adaptive_pool.get_system_metrics()

        assert isinstance(metrics, dict)
        assert 0.0 <= metrics["cpu_percent"] <= 100.0
        assert 0.0 <= metrics["memory_percent"] <= 100.0
        assert metrics["queue_depth"] == 0

    def test_get_system_metrics_with_executor(
        self, adaptive_pool, mock_executor, mock_queue
    ):
        """Test metrics collection with executor and queue."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)
        mock_queue.qsize.return_value = 15

        metrics = adaptive_pool.get_system_metrics()

        assert metrics["queue_depth"] == 15

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    def test_metrics_use_psutil(self, mock_memory, mock_cpu, adaptive_pool):
        """Test that metrics use psutil for accurate readings."""
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=67.3, available=1024 * 1024 * 1024)

        metrics = adaptive_pool.get_system_metrics()

        assert metrics["cpu_percent"] == 45.5
        assert metrics["memory_percent"] == 67.3


class TestWorkerCalculation:
    """Test optimal worker calculation algorithm."""

    def test_scale_up_low_cpu_high_queue(
        self, adaptive_pool, mock_executor, mock_queue
    ):
        """Test scaling up when CPU is low and queue is backlogged."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)

        # Simulate low CPU, high queue
        with patch.object(adaptive_pool, "get_system_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 30.0,
                "memory_percent": 50.0,
                "queue_depth": 25,
                "available_memory_mb": 2000,
            }

            metrics = adaptive_pool.get_system_metrics()
            optimal = adaptive_pool.calculate_optimal_workers(metrics)

            # Should recommend scaling up
            assert optimal > 4

    def test_scale_down_high_cpu_low_queue(
        self, adaptive_pool, mock_executor, mock_queue
    ):
        """Test scaling down when CPU is high and queue is empty."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)
        adaptive_pool.current_workers = 12  # Start high

        with patch.object(adaptive_pool, "get_system_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 85.0,
                "memory_percent": 60.0,
                "queue_depth": 1,
                "available_memory_mb": 1500,
            }

            metrics = adaptive_pool.get_system_metrics()
            optimal = adaptive_pool.calculate_optimal_workers(metrics)

            # Should recommend scaling down
            assert optimal < 12

    def test_no_scaling_memory_pressure(self, adaptive_pool, mock_executor, mock_queue):
        """Test that high memory pressure prevents scaling up."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)

        with patch.object(adaptive_pool, "get_system_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 20.0,  # Low CPU - would normally scale up
                "memory_percent": 90.0,  # High memory - should prevent scaling
                "queue_depth": 30,
                "available_memory_mb": 500,
            }

            metrics = adaptive_pool.get_system_metrics()
            optimal = adaptive_pool.calculate_optimal_workers(metrics)

            # Should not scale beyond current due to memory pressure
            assert optimal <= 4

    def test_respects_min_max_bounds(self, adaptive_pool, mock_executor):
        """Test that worker count stays within configured bounds."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.min_workers = 4
        adaptive_pool.max_workers = 16

        with patch.object(adaptive_pool, "get_system_metrics") as mock_metrics:
            # Try to scale below min
            mock_metrics.return_value = {
                "cpu_percent": 95.0,
                "memory_percent": 30.0,
                "queue_depth": 0,
                "available_memory_mb": 3000,
            }
            metrics = adaptive_pool.get_system_metrics()
            optimal = adaptive_pool.calculate_optimal_workers(metrics)
            assert optimal >= adaptive_pool.min_workers

            # Try to scale above max
            mock_metrics.return_value = {
                "cpu_percent": 10.0,
                "memory_percent": 20.0,
                "queue_depth": 100,
                "available_memory_mb": 4000,
            }
            metrics = adaptive_pool.get_system_metrics()
            optimal = adaptive_pool.calculate_optimal_workers(metrics)
            assert optimal <= adaptive_pool.max_workers


class TestWorkerAdjustment:
    """Test actual worker pool adjustment."""

    def test_adjust_workers_scales_up(self, adaptive_pool, mock_executor, mock_queue):
        """Test that adjust_workers increases pool size when needed."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)
        mock_executor._max_workers = 4

        with (
            patch.object(adaptive_pool, "should_adjust", return_value=True),
            patch.object(adaptive_pool, "calculate_optimal_workers", return_value=8),
        ):
            adjusted = adaptive_pool.adjust_workers()

            assert adjusted is True
            assert mock_executor._max_workers == 8
            assert adaptive_pool.current_workers == 8

    def test_adjust_workers_scales_down(self, adaptive_pool, mock_executor, mock_queue):
        """Test that adjust_workers decreases pool size when needed."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)
        mock_executor._max_workers = 12
        adaptive_pool.current_workers = 12

        with (
            patch.object(adaptive_pool, "should_adjust", return_value=True),
            patch.object(adaptive_pool, "calculate_optimal_workers", return_value=6),
        ):
            adjusted = adaptive_pool.adjust_workers()

            assert adjusted is True
            assert mock_executor._max_workers == 6
            assert adaptive_pool.current_workers == 6

    def test_no_adjustment_when_optimal(self, adaptive_pool, mock_executor, mock_queue):
        """Test that no adjustment occurs when already at optimal size."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)
        mock_executor._max_workers = 8
        adaptive_pool.current_workers = 8

        with (
            patch.object(adaptive_pool, "should_adjust", return_value=True),
            patch.object(adaptive_pool, "calculate_optimal_workers", return_value=8),
        ):
            adjusted = adaptive_pool.adjust_workers()

            assert adjusted is False
            assert mock_executor._max_workers == 8

    def test_tracks_scaling_events(self, adaptive_pool, mock_executor, mock_queue):
        """Test that scaling events are tracked in metrics."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)

        initial_count = adaptive_pool.metrics.total_adjustments

        with (
            patch.object(adaptive_pool, "should_adjust", return_value=True),
            patch.object(adaptive_pool, "calculate_optimal_workers", return_value=10),
        ):
            adaptive_pool.adjust_workers()

        assert adaptive_pool.metrics.total_adjustments == initial_count + 1


class TestPerformanceTracking:
    """Test performance metrics tracking."""

    def test_record_task_time(self, adaptive_pool):
        """Test recording task completion times."""
        adaptive_pool.record_task_time(1.5)
        adaptive_pool.record_task_time(2.0)
        adaptive_pool.record_task_time(1.8)

        assert len(adaptive_pool._recent_task_times) == 3
        assert 1.5 in adaptive_pool._recent_task_times

    def test_task_time_window_limit(self, adaptive_pool):
        """Test that task times are limited to window size."""
        # Record more than window size (100)
        for i in range(150):
            adaptive_pool.record_task_time(float(i))

        assert len(adaptive_pool._recent_task_times) == 100

    def test_performance_improvement_tracking(self, adaptive_pool):
        """Test that performance improvements are tracked."""
        # Record baseline (50 required for baseline establishment)
        for _ in range(50):
            adaptive_pool.record_task_time(2.0)

        # Record improvements
        for _ in range(50):
            adaptive_pool.record_task_time(1.5)

        status = adaptive_pool.get_status_dict()

        # Should show improvement (positive percentage = faster)
        assert status["performance_gain_percent"] > 0


class TestStatusReporting:
    """Test status dictionary generation."""

    def test_get_status_dict_structure(self, adaptive_pool, mock_executor, mock_queue):
        """Test that status dict contains all expected keys."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)

        status = adaptive_pool.get_status_dict()

        expected_keys = {
            "current_workers",
            "min_workers",
            "max_workers",
            "total_adjustments",
            "scale_ups",
            "scale_downs",
            "avg_cpu_percent",
            "avg_memory_percent",
            "avg_queue_depth",
            "performance_gain_percent",
            "last_adjustment",
        }

        assert set(status.keys()) == expected_keys

    def test_status_dict_values(self, adaptive_pool):
        """Test that status dict contains valid values."""
        status = adaptive_pool.get_status_dict()

        assert isinstance(status["current_workers"], int)
        assert isinstance(status["min_workers"], int)
        assert isinstance(status["max_workers"], int)
        assert isinstance(status["total_adjustments"], int)
        assert isinstance(status["performance_gain_percent"], float)


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_sustained_high_load_scenario(
        self, adaptive_pool, mock_executor, mock_queue
    ):
        """Test behavior under sustained high load."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)

        # Simulate high load over time
        with (
            patch.object(adaptive_pool, "should_adjust", return_value=True),
            patch.object(adaptive_pool, "get_system_metrics") as mock_metrics,
        ):
            mock_metrics.return_value = {
                "cpu_percent": 35.0,
                "memory_percent": 50.0,
                "queue_depth": 50,
                "available_memory_mb": 2000,
            }

            # Multiple adjustment cycles
            for _ in range(5):
                adaptive_pool.adjust_workers()
                await asyncio.sleep(0.1)

            # Should have scaled up
            assert adaptive_pool.current_workers > 4

    @pytest.mark.asyncio
    async def test_load_decrease_scenario(
        self, adaptive_pool, mock_executor, mock_queue
    ):
        """Test scaling down after load decreases."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)
        adaptive_pool.current_workers = 12
        mock_executor._max_workers = 12

        # Simulate decreasing load
        with (
            patch.object(adaptive_pool, "should_adjust", return_value=True),
            patch.object(adaptive_pool, "get_system_metrics") as mock_metrics,
        ):
            mock_metrics.return_value = {
                "cpu_percent": 75.0,
                "memory_percent": 40.0,
                "queue_depth": 1,
                "available_memory_mb": 2500,
            }

            # Multiple adjustment cycles
            for _ in range(5):
                adaptive_pool.adjust_workers()
                await asyncio.sleep(0.1)

            # Should have scaled down
            assert adaptive_pool.current_workers < 12

    def test_rapid_fluctuation_stability(
        self, adaptive_pool, mock_executor, mock_queue
    ):
        """Test that rapid load changes don't cause instability."""
        adaptive_pool.set_executor(mock_executor)
        adaptive_pool.set_task_queue(mock_queue)

        initial_workers = adaptive_pool.current_workers

        # Simulate rapid fluctuations
        with patch.object(adaptive_pool, "get_system_metrics") as mock_metrics:
            for i in range(10):
                # Alternate between high and low load
                if i % 2 == 0:
                    mock_metrics.return_value = {
                        "cpu_percent": 20.0,
                        "memory_percent": 40.0,
                        "queue_depth": 30,
                        "available_memory_mb": 2000,
                    }
                else:
                    mock_metrics.return_value = {
                        "cpu_percent": 80.0,
                        "memory_percent": 40.0,
                        "queue_depth": 0,
                        "available_memory_mb": 2000,
                    }

                adaptive_pool.adjust_workers()

        # Workers should still be reasonable (smoothing factor helps)
        assert (
            adaptive_pool.min_workers
            <= adaptive_pool.current_workers
            <= adaptive_pool.max_workers
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
