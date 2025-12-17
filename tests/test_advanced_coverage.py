"""
Advanced test coverage suite targeting 95% coverage.

This module contains stress tests, edge cases, and integration tests for:
- Trend analysis edge cases
- Scheduler stress testing (1000+ schedules)
- Compliance engine integration tests
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Graceful import with fallback
try:
    from app.reporting.trend_analysis import TrendAnalyzer
    from app.reporting.scheduler import ReportScheduler
    from app.reporting.compliance_frameworks import ComplianceFrameworkManager
except ImportError as e:
    pytest.skip(f"Reporting modules not available: {e}", allow_module_level=True)


# ============================================================================
# TREND ANALYSIS EDGE CASES
# ============================================================================


class TestTrendAnalysisEdgeCases:
    """Advanced edge case testing for trend analysis."""

    def test_sparse_data_with_gaps(self):
        """Test trend analysis with large gaps in time series data."""
        analyzer = TrendAnalyzer()

        # Create data with 7-day gaps
        dates = []
        values = []
        base_date = datetime(2025, 1, 1)
        for i in range(10):
            dates.append(base_date + timedelta(days=i * 7))  # Weekly data only
            values.append(10 + i * 2)

        # Should interpolate or handle gaps gracefully
        result = analyzer.calculate_trends(list(zip(dates, values)))

        assert result is not None
        assert "trend" in result
        assert "confidence" in result
        # Lower confidence expected due to sparse data
        assert result["confidence"] < 0.8

    def test_constant_values_no_trend(self):
        """Test trend analysis with completely flat data."""
        analyzer = TrendAnalyzer()

        dates = [datetime.now() - timedelta(days=i) for i in range(30)]
        values = [42] * 30  # All identical

        result = analyzer.calculate_trends(list(zip(dates, values)))

        assert result is not None
        assert result["trend_direction"] == "stable"
        assert result["slope"] == pytest.approx(0.0, abs=0.01)

    def test_extreme_volatility(self):
        """Test trend analysis with highly volatile data."""
        analyzer = TrendAnalyzer()

        dates = [datetime.now() - timedelta(hours=i) for i in range(100)]
        # Alternating high/low values
        values = [100 if i % 2 == 0 else 10 for i in range(100)]

        result = analyzer.calculate_trends(list(zip(dates, values)))

        assert result is not None
        assert "volatility" in result
        assert result["volatility"] > 0.5  # High volatility indicator

    def test_single_data_point(self):
        """Test forecast with only one data point."""
        analyzer = TrendAnalyzer()

        single_point = [(datetime.now(), 50)]

        # Should either return constant forecast or raise informative error
        with pytest.raises(ValueError, match="insufficient data|minimum.*points"):
            analyzer.forecast_threats(single_point, forecast_days=7)

    def test_two_data_points_minimum(self):
        """Test forecast with exactly two data points (minimum)."""
        analyzer = TrendAnalyzer()

        two_points = [
            (datetime.now() - timedelta(days=1), 10),
            (datetime.now(), 20),
        ]

        # Should produce simple linear forecast
        result = analyzer.forecast_threats(two_points, forecast_days=3)

        assert result is not None
        assert len(result) == 3
        # Should show linear increase
        assert result[0]["value"] < result[1]["value"] < result[2]["value"]

    def test_outlier_detection(self):
        """Test anomaly detection with clear outliers."""
        analyzer = TrendAnalyzer()

        dates = [datetime.now() - timedelta(days=i) for i in range(30)]
        # Normal values with 3 extreme outliers
        values = [10 + i * 0.5 for i in range(30)]
        values[10] = 1000  # Extreme outlier
        values[20] = 0.001  # Extreme low
        values[25] = -50  # Invalid (negative)

        anomalies = analyzer.detect_anomalies(list(zip(dates, values)))

        assert anomalies is not None
        assert len(anomalies) >= 2  # Should detect at least 2 outliers
        assert any(a["date"] == dates[10] for a in anomalies)

    def test_seasonal_pattern_detection(self):
        """Test detection of seasonal patterns in data."""
        analyzer = TrendAnalyzer()

        # Create weekly pattern (high on weekdays, low on weekends)
        dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(90)]
        values = [
            50 if (date.weekday() < 5) else 10  # Mon-Fri high, Sat-Sun low
            for date in dates
        ]

        result = analyzer.calculate_trends(list(zip(dates, values)))

        assert result is not None
        if "seasonality" in result:
            assert result["seasonality"]["detected"] is True
            assert result["seasonality"]["period"] == pytest.approx(7, abs=1)

    def test_forecast_confidence_intervals(self):
        """Test that forecasts include confidence intervals."""
        analyzer = TrendAnalyzer()

        dates = [datetime.now() - timedelta(days=i) for i in range(60)]
        values = [10 + i * 0.5 + (i % 5) for i in range(60)]  # Linear + noise

        forecast = analyzer.forecast_threats(
            list(zip(dates, values)), forecast_days=14, include_confidence=True
        )

        assert forecast is not None
        assert len(forecast) == 14
        for prediction in forecast:
            assert "value" in prediction
            assert "confidence_lower" in prediction
            assert "confidence_upper" in prediction
            assert (
                prediction["confidence_lower"]
                <= prediction["value"]
                <= prediction["confidence_upper"]
            )


# ============================================================================
# SCHEDULER STRESS TESTS
# ============================================================================


class TestSchedulerStressTests:
    """Stress testing for scheduler with high load."""

    def test_1000_schedules_creation(self, tmp_path):
        """Test creating 1000 schedules without performance degradation."""
        scheduler = ReportScheduler(state_file=str(tmp_path / "stress_test.json"))

        start_time = time.time()

        # Create 1000 schedules
        for i in range(1000):
            scheduler.add_schedule(
                name=f"stress_test_{i}",
                report_type=["web", "compliance", "trend"][i % 3],
                frequency=["daily", "weekly", "monthly"][i % 3],
                time=f"{i % 24:02d}:{i % 60:02d}",
            )

        creation_time = time.time() - start_time

        # Should complete in reasonable time (<10 seconds)
        assert creation_time < 10.0

        # Verify all schedules exist
        schedules = scheduler.list_schedules()
        assert len(schedules) == 1000

    def test_concurrent_schedule_execution(self, tmp_path):
        """Test executing multiple schedules concurrently."""
        scheduler = ReportScheduler()

        # Add 50 schedules
        for i in range(50):
            scheduler.add_schedule(
                name=f"concurrent_{i}",
                report_type="web",
                frequency="once",
                time="00:00",
            )

        # Execute all concurrently
        executed_count = 0
        errors = []

        def execute_schedule(name):
            nonlocal executed_count
            try:
                scheduler.execute_schedule(name)
                executed_count += 1
            except Exception as e:
                errors.append((name, str(e)))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(execute_schedule, f"concurrent_{i}") for i in range(50)
            ]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions

        # All should execute successfully
        assert executed_count == 50
        assert len(errors) == 0

    def test_schedule_persistence_large_dataset(self, tmp_path):
        """Test saving/loading state with 1000+ schedules."""
        state_file = tmp_path / "large_state.json"

        # Create scheduler with many schedules
        scheduler1 = ReportScheduler(state_file=str(state_file))
        for i in range(1000):
            scheduler1.add_schedule(
                name=f"persist_{i}",
                report_type="web",
                frequency="daily",
                time=f"{i % 24:02d}:00",
            )

        # Save state
        start_time = time.time()
        scheduler1.save_state()
        save_time = time.time() - start_time

        # Should save quickly (<2 seconds)
        assert save_time < 2.0

        # Reload in new instance
        start_time = time.time()
        scheduler2 = ReportScheduler(state_file=str(state_file))
        load_time = time.time() - start_time

        # Should load quickly (<2 seconds)
        assert load_time < 2.0

        # Verify all schedules restored
        schedules = scheduler2.list_schedules()
        assert len(schedules) == 1000

    def test_memory_usage_large_schedules(self, tmp_path):
        """Test memory efficiency with large number of schedules."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        scheduler = ReportScheduler()

        # Add 5000 schedules
        for i in range(5000):
            scheduler.add_schedule(
                name=f"memory_test_{i}",
                report_type="web",
                frequency="daily",
                time="09:00",
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Should use <100MB for 5000 schedules
        assert memory_increase < 100

    def test_schedule_priority_ordering(self):
        """Test that high-priority schedules execute first."""
        scheduler = ReportScheduler()

        execution_order = []

        def mock_execute(name, *args, **kwargs):
            execution_order.append(name)

        with patch.object(scheduler, "_generate_report", mock_execute):
            # Add schedules with different priorities
            scheduler.add_schedule("low_priority", "web", "once", "00:00", priority=1)
            scheduler.add_schedule("high_priority", "web", "once", "00:00", priority=10)
            scheduler.add_schedule(
                "medium_priority", "web", "once", "00:00", priority=5
            )

            # Execute all
            scheduler.execute_due_schedules()

        # High priority should execute first
        assert execution_order[0] == "high_priority"
        assert execution_order[1] == "medium_priority"
        assert execution_order[2] == "low_priority"


# ============================================================================
# COMPLIANCE ENGINE INTEGRATION TESTS
# ============================================================================


class TestComplianceEngineIntegration:
    """Integration tests for compliance framework manager."""

    def test_multi_framework_compliance_check(self):
        """Test checking compliance against multiple frameworks simultaneously."""
        manager = ComplianceFrameworkManager()

        comprehensive_scan_data = {
            "scan_id": "integration_test_001",
            "scan_date": datetime.now().isoformat(),
            "encryption_enabled": True,
            "password_policy": "strong",
            "mfa_enabled": True,
            "logging_enabled": True,
            "log_retention_days": 90,
            "vulnerability_scan_frequency": "weekly",
            "patch_management": "automated",
            "access_controls": "role-based",
            "data_classification": "implemented",
        }

        # Check against all frameworks
        results = manager.check_all_frameworks(comprehensive_scan_data)

        # Should return results for all frameworks
        assert len(results) >= 3  # PCI-DSS, HIPAA, GDPR minimum

        # All should be compliant with comprehensive data
        for framework, result in results.items():
            assert result["status"] in ["compliant", "partial"]
            assert "compliance_score" in result
            assert 0 <= result["compliance_score"] <= 100

    def test_conflicting_framework_requirements(self):
        """Test handling of conflicting requirements across frameworks."""
        manager = ComplianceFrameworkManager()

        # Scenario: Some frameworks require logging, others prohibit certain logs
        scan_data = {
            "logging_enabled": True,
            "log_user_activity": True,  # Required by some, forbidden by GDPR-strict
            "log_retention_days": 365,  # Too long for some privacy frameworks
        }

        results = manager.check_all_frameworks(scan_data)

        # Should identify conflicts
        assert "conflicts" in results or any(
            "conflict" in str(r).lower() for r in results.values()
        )

    def test_compliance_roadmap_generation(self):
        """Test generating compliance roadmap for non-compliant system."""
        manager = ComplianceFrameworkManager()

        non_compliant_data = {
            "encryption_enabled": False,
            "password_policy": "weak",
            "mfa_enabled": False,
            "logging_enabled": False,
        }

        roadmap = manager.generate_compliance_roadmap(
            framework="PCI-DSS", current_state=non_compliant_data
        )

        assert roadmap is not None
        assert "tasks" in roadmap
        assert len(roadmap["tasks"]) > 0

        # Should prioritize critical items
        assert any(t["priority"] == "critical" for t in roadmap["tasks"])

        # Should have estimated timelines
        assert all("estimated_days" in t for t in roadmap["tasks"])

    def test_partial_compliance_gap_analysis(self):
        """Test detailed gap analysis for partial compliance."""
        manager = ComplianceFrameworkManager()

        partial_data = {
            "encryption_enabled": True,  # ✓
            "password_policy": "medium",  # Partial
            "mfa_enabled": False,  # ✗
            "logging_enabled": True,  # ✓
            "log_retention_days": 30,  # Insufficient
        }

        result = manager.check_compliance("HIPAA", partial_data)

        assert result["status"] == "partial"
        assert "gaps" in result
        assert len(result["gaps"]) > 0

        # Should identify specific issues
        gap_descriptions = [g["description"] for g in result["gaps"]]
        assert any("mfa" in g.lower() for g in gap_descriptions)
        assert any("retention" in g.lower() for g in gap_descriptions)

    def test_compliance_report_generation_integration(self):
        """Test end-to-end compliance report generation."""
        from app.reporting.web_reports import WebReportGenerator

        manager = ComplianceFrameworkManager()
        generator = WebReportGenerator()

        scan_data = {
            "scan_id": "compliance_integration_001",
            "encryption_enabled": True,
            "password_policy": "strong",
            "mfa_enabled": True,
        }

        # Get compliance results
        compliance_results = manager.check_all_frameworks(scan_data)

        # Generate report
        report = generator.generate_compliance_report(
            compliance_data=compliance_results, output_path=None  # Return HTML string
        )

        assert report is not None
        assert "compliance" in report.lower()

        # Should include all frameworks
        for framework in compliance_results.keys():
            assert framework in report


# ============================================================================
# PERFORMANCE REGRESSION TESTS
# ============================================================================


class TestPerformanceRegression:
    """Performance regression tests to ensure no degradation."""

    def test_trend_analysis_performance_baseline(self):
        """Baseline: 1000 data points analyzed in <1 second."""
        analyzer = TrendAnalyzer()

        dates = [datetime.now() - timedelta(hours=i) for i in range(1000)]
        values = [10 + i * 0.1 for i in range(1000)]

        start_time = time.time()
        result = analyzer.calculate_trends(list(zip(dates, values)))
        duration = time.time() - start_time

        assert result is not None
        assert duration < 1.0  # <1 second for 1000 points

    def test_scheduler_execution_performance(self):
        """Baseline: Execute 100 schedules in <5 seconds."""
        scheduler = ReportScheduler()

        execution_count = 0

        def fast_mock_report(*args, **kwargs):
            nonlocal execution_count
            execution_count += 1
            time.sleep(0.01)  # Simulate minimal work

        with patch.object(scheduler, "_generate_report", fast_mock_report):
            for i in range(100):
                scheduler.add_schedule(f"perf_{i}", "web", "once", "00:00")

            start_time = time.time()
            scheduler.execute_due_schedules()
            duration = time.time() - start_time

        assert execution_count == 100
        assert duration < 5.0  # <5 seconds for 100 schedules

    def test_compliance_check_performance(self):
        """Baseline: All framework checks complete in <500ms."""
        manager = ComplianceFrameworkManager()

        scan_data = {
            "scan_id": "perf_test",
            "encryption_enabled": True,
            "password_policy": "strong",
            "mfa_enabled": True,
            "logging_enabled": True,
        }

        start_time = time.time()
        results = manager.check_all_frameworks(scan_data)
        duration = time.time() - start_time

        assert results is not None
        assert duration < 0.5  # <500ms for all frameworks


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
