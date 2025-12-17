"""
Integration tests for performance monitoring framework.
"""

import time
from pathlib import Path

import pytest

from app.utils.performance_monitor import (
    PerformanceMetric,
    PerformanceMonitor,
    PerformanceRegistry,
    PerformanceSLA,
)


class TestPerformanceMonitoring:
    """Test performance monitoring framework."""

    def setup_method(self):
        """Clear registry before each test."""
        PerformanceRegistry.clear()

    def test_performance_monitor_context_manager(self):
        """Test basic performance monitoring."""
        with PerformanceMonitor("test_operation"):
            time.sleep(0.1)

        metrics = PerformanceRegistry.get_metrics("test_operation")
        assert len(metrics) == 1

        metric = metrics[0]
        assert metric.operation == "test_operation"
        assert 90 < metric.duration_ms < 150  # ~100ms ±tolerance
        assert metric.memory_delta_mb >= 0  # Should track memory

    def test_multiple_operations_tracking(self):
        """Test tracking multiple different operations."""
        for i in range(5):
            with PerformanceMonitor("operation_a"):
                time.sleep(0.01)

        for i in range(3):
            with PerformanceMonitor("operation_b"):
                time.sleep(0.02)

        metrics_a = PerformanceRegistry.get_metrics("operation_a")
        metrics_b = PerformanceRegistry.get_metrics("operation_b")

        assert len(metrics_a) == 5
        assert len(metrics_b) == 3

    def test_performance_statistics(self):
        """Test statistical aggregation of metrics."""
        # Record operations with varying durations
        durations = [0.01, 0.02, 0.03, 0.04, 0.05]
        for duration in durations:
            with PerformanceMonitor("test_stats"):
                time.sleep(duration)

        stats = PerformanceRegistry.get_statistics("test_stats")

        assert stats["count"] == 5
        assert stats["duration_min_ms"] < stats["duration_max_ms"]
        assert stats["duration_p50_ms"] < stats["duration_p95_ms"]

    def test_sla_compliance_check(self):
        """Test SLA compliance checking."""
        # Define strict SLA
        sla = PerformanceSLA(
            operation="fast_op",
            max_duration_ms=50,
            max_memory_mb=10,
            description="Should complete in <50ms",
        )
        PerformanceRegistry.define_sla(sla)

        # Fast operation (compliant)
        with PerformanceMonitor("fast_op"):
            time.sleep(0.02)  # 20ms

        metrics = PerformanceRegistry.get_metrics("fast_op")
        compliant, violations = sla.check_compliance(metrics[0])

        assert compliant is True
        assert len(violations) == 0

    def test_sla_violation_detection(self):
        """Test SLA violation detection."""
        # Define strict SLA
        sla = PerformanceSLA(
            operation="slow_op",
            max_duration_ms=50,
            max_memory_mb=10,
            description="Should complete in <50ms",
        )
        PerformanceRegistry.define_sla(sla)

        # Slow operation (non-compliant)
        with PerformanceMonitor("slow_op"):
            time.sleep(0.1)  # 100ms (exceeds 50ms SLA)

        metrics = PerformanceRegistry.get_metrics("slow_op")
        compliant, violations = sla.check_compliance(metrics[0])

        assert compliant is False
        assert len(violations) > 0
        assert "duration" in violations[0].lower()

    def test_baseline_save_and_load(self, tmp_path):
        """Test saving and loading performance baselines."""
        # Record some metrics
        for i in range(10):
            with PerformanceMonitor("baseline_test"):
                time.sleep(0.01)

        # Save baseline
        baseline_file = tmp_path / "baseline.json"
        PerformanceRegistry.save_baseline(baseline_file)

        assert baseline_file.exists()

        # Clear and load
        PerformanceRegistry.clear()
        baseline = PerformanceRegistry.load_baseline(baseline_file)

        assert "operations" in baseline
        assert "baseline_test" in baseline["operations"]
        assert baseline["operations"]["baseline_test"]["count"] == 10

    def test_baseline_comparison_regression(self, tmp_path):
        """Test detection of performance regressions."""
        baseline_file = tmp_path / "baseline.json"

        # Record baseline (fast operations)
        for i in range(10):
            with PerformanceMonitor("comparison_test"):
                time.sleep(0.01)  # 10ms

        PerformanceRegistry.save_baseline(baseline_file)
        PerformanceRegistry.clear()

        # Record new metrics (slower - regression)
        for i in range(10):
            with PerformanceMonitor("comparison_test"):
                time.sleep(0.03)  # 30ms (3x slower)

        comparison = PerformanceRegistry.compare_to_baseline(baseline_file)

        assert len(comparison["regressions"]) > 0
        assert comparison["regressions"][0]["operation"] == "comparison_test"
        assert comparison["regressions"][0]["change_percent"] > 10

    def test_baseline_comparison_improvement(self, tmp_path):
        """Test detection of performance improvements."""
        baseline_file = tmp_path / "baseline.json"

        # Record baseline (slow operations)
        for i in range(10):
            with PerformanceMonitor("improvement_test"):
                time.sleep(0.03)  # 30ms

        PerformanceRegistry.save_baseline(baseline_file)
        PerformanceRegistry.clear()

        # Record new metrics (faster - improvement)
        for i in range(10):
            with PerformanceMonitor("improvement_test"):
                time.sleep(0.01)  # 10ms (3x faster)

        comparison = PerformanceRegistry.compare_to_baseline(baseline_file)

        assert len(comparison["improvements"]) > 0
        assert comparison["improvements"][0]["operation"] == "improvement_test"
        assert comparison["improvements"][0]["change_percent"] < -10

    def test_performance_report_generation(self, tmp_path):
        """Test performance report generation."""
        # Record diverse operations
        operations = ["scan_file", "generate_report", "check_compliance"]

        for operation in operations:
            for i in range(5):
                with PerformanceMonitor(operation):
                    time.sleep(0.01 * (hash(operation) % 5 + 1))

        # Generate report
        report_file = tmp_path / "performance_report.md"
        report = PerformanceRegistry.generate_report(report_file)

        assert report_file.exists()
        assert "Performance Report" in report

        # Should include all operations
        for operation in operations:
            assert operation in report

    def test_metadata_tracking(self):
        """Test tracking custom metadata with metrics."""
        with PerformanceMonitor("metadata_test", file_size=1024, file_type="binary"):
            time.sleep(0.01)

        metrics = PerformanceRegistry.get_metrics("metadata_test")
        metric = metrics[0]

        assert metric.metadata["file_size"] == 1024
        assert metric.metadata["file_type"] == "binary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
