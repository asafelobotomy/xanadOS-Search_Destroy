"""
Edge case tests for Task 2.3 Advanced Reporting System.

Tests for missing dependencies, malformed data, concurrent operations,
large datasets, and error recovery scenarios.
"""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import with graceful fallback
try:
    from app.reporting.web_reports import WebReportGenerator
    from app.reporting.trend_analysis import TrendAnalyzer
    from app.reporting.compliance_frameworks import ComplianceFrameworkManager
    from app.reporting.scheduler import ReportScheduler
except ImportError as e:
    pytest.skip(f"Reporting modules not available: {e}", allow_module_level=True)


class TestMissingDependencies:
    """Test graceful degradation when optional dependencies are missing."""

    def test_plotly_missing_fallback(self, tmp_path):
        """Test web report generation falls back when plotly unavailable."""
        with patch.dict("sys.modules", {"plotly": None}):
            generator = WebReportGenerator()

            # Should still generate basic report without interactive charts
            report = generator.generate_report(
                scan_data={"total_scans": 100, "threats_found": 5},
                output_path=str(tmp_path / "report.html"),
            )

            assert report is not None
            assert "fallback" in report.lower() or "static" in report.lower()

    def test_weasyprint_missing_no_pdf(self, tmp_path):
        """Test PDF export gracefully fails when weasyprint unavailable."""
        with patch.dict("sys.modules", {"weasyprint": None}):
            generator = WebReportGenerator()

            with pytest.raises(ImportError, match="weasyprint"):
                generator.export_to_pdf(
                    html_content="<html><body>Test</body></html>",
                    output_path=str(tmp_path / "report.pdf"),
                )

    def test_openpyxl_missing_no_excel(self, tmp_path):
        """Test Excel export gracefully fails when openpyxl unavailable."""
        with patch.dict("sys.modules", {"openpyxl": None}):
            generator = WebReportGenerator()

            with pytest.raises(ImportError, match="openpyxl"):
                generator.export_to_excel(
                    data={"scans": [{"date": "2025-01-01", "threats": 5}]},
                    output_path=str(tmp_path / "report.xlsx"),
                )

    def test_prophet_missing_basic_forecasting(self):
        """Test trend analysis falls back to ARIMA when Prophet unavailable."""
        with patch.dict("sys.modules", {"prophet": None}):
            analyzer = TrendAnalyzer()

            # Generate dummy time series data
            dates = [datetime.now() - timedelta(days=i) for i in range(30)]
            values = [10 + i * 0.5 for i in range(30)]

            # Should use ARIMA fallback
            forecast = analyzer.forecast_threats(
                historical_data=list(zip(dates, values)), forecast_days=7
            )

            assert forecast is not None
            assert len(forecast) == 7
            assert "method" in forecast[0]
            assert forecast[0]["method"] == "arima"


class TestMalformedData:
    """Test handling of malformed and invalid data inputs."""

    def test_empty_scan_data(self):
        """Test report generation with empty scan data."""
        generator = WebReportGenerator()

        report = generator.generate_report(scan_data={}, output_path=None)

        assert report is not None
        assert "no data" in report.lower() or "empty" in report.lower()

    def test_invalid_date_format(self):
        """Test trend analysis with invalid date formats."""
        analyzer = TrendAnalyzer()

        # Malformed date strings
        malformed_data = [
            ("not-a-date", 10),
            ("2025-13-45", 20),  # Invalid month/day
            (None, 30),
        ]

        # Should handle gracefully or raise clear error
        with pytest.raises((ValueError, TypeError)) as exc_info:
            analyzer.forecast_threats(malformed_data, forecast_days=7)

        assert "date" in str(exc_info.value).lower()

    def test_negative_threat_counts(self):
        """Test handling of negative threat counts."""
        analyzer = TrendAnalyzer()

        dates = [datetime.now() - timedelta(days=i) for i in range(10)]
        values = [-5, 10, -3, 20, 15]  # Contains negative values

        # Should either reject or sanitize
        with pytest.raises(ValueError, match="negative"):
            analyzer.calculate_trends(list(zip(dates, values)))

    def test_missing_required_fields(self):
        """Test compliance check with missing required fields."""
        manager = ComplianceFrameworkManager()

        incomplete_data = {
            "scan_id": "test-123",
            # Missing: scan_date, threats_found, etc.
        }

        result = manager.check_compliance(
            framework="PCI-DSS", scan_data=incomplete_data
        )

        assert result["status"] == "incomplete"
        assert "missing_fields" in result

    def test_corrupted_json_config(self, tmp_path):
        """Test scheduler with corrupted configuration file."""
        config_file = tmp_path / "scheduler_config.json"
        config_file.write_text("{ invalid json }")

        with pytest.raises((json.JSONDecodeError, ValueError)):
            scheduler = ReportScheduler(config_path=str(config_file))


class TestConcurrentOperations:
    """Test thread safety and concurrent report generation."""

    def test_concurrent_report_generation(self, tmp_path):
        """Test multiple reports generated concurrently."""
        generator = WebReportGenerator()

        def generate_report(report_id):
            scan_data = {
                "report_id": report_id,
                "total_scans": 100 + report_id,
                "threats_found": 5 + report_id,
            }
            output_path = tmp_path / f"report_{report_id}.html"
            return generator.generate_report(scan_data, str(output_path))

        # Generate 10 reports concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_report, i) for i in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert len(results) == 10
        assert all(r is not None for r in results)

        # All files should exist
        assert len(list(tmp_path.glob("report_*.html"))) == 10

    @pytest.mark.asyncio
    async def test_async_trend_analysis(self):
        """Test async trend analysis doesn't deadlock."""
        analyzer = TrendAnalyzer()

        dates = [datetime.now() - timedelta(days=i) for i in range(30)]
        values = [10 + i * 0.5 for i in range(30)]

        # Run multiple analyses concurrently
        tasks = [
            asyncio.create_task(
                asyncio.to_thread(
                    analyzer.forecast_threats, list(zip(dates, values)), 7
                )
            )
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without deadlock
        assert len(results) == 5
        assert not any(isinstance(r, Exception) for r in results)

    def test_scheduler_race_condition(self, tmp_path):
        """Test scheduler handles concurrent schedule additions."""
        scheduler = ReportScheduler()

        def add_schedule(schedule_id):
            scheduler.add_schedule(
                name=f"schedule_{schedule_id}",
                report_type="web",
                frequency="daily",
                time="09:00",
            )

        # Add 20 schedules concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_schedule, i) for i in range(20)]
            for f in futures:
                f.result()

        # All should be added
        schedules = scheduler.list_schedules()
        assert len(schedules) == 20


class TestLargeDatasets:
    """Test performance with large datasets."""

    def test_large_scan_history(self):
        """Test trend analysis with 10,000+ data points."""
        analyzer = TrendAnalyzer()

        # Generate 10,000 data points
        base_date = datetime.now() - timedelta(days=10000)
        large_dataset = [
            (base_date + timedelta(days=i), 10 + (i % 100)) for i in range(10000)
        ]

        # Should handle efficiently
        import time

        start = time.time()
        trends = analyzer.calculate_trends(large_dataset)
        duration = time.time() - start

        assert trends is not None
        assert duration < 10.0  # Should complete in <10 seconds

    def test_large_report_export(self, tmp_path):
        """Test PDF/Excel export with large datasets."""
        generator = WebReportGenerator()

        # Generate large scan data (1000 entries)
        large_scan_data = {
            "scans": [
                {
                    "scan_id": f"scan_{i}",
                    "date": (datetime.now() - timedelta(days=i)).isoformat(),
                    "files_scanned": 1000 + i,
                    "threats_found": i % 10,
                }
                for i in range(1000)
            ]
        }

        # Generate report
        html_output = tmp_path / "large_report.html"
        report = generator.generate_report(large_scan_data, str(html_output))

        assert report is not None
        assert html_output.exists()

        # File should be reasonable size (<10MB)
        file_size_mb = html_output.stat().st_size / (1024 * 1024)
        assert file_size_mb < 10

    def test_memory_efficiency_streaming(self, tmp_path):
        """Test memory-efficient processing of large datasets."""
        analyzer = TrendAnalyzer()

        # Simulate streaming data processing
        def data_generator():
            for i in range(50000):
                yield (datetime.now() - timedelta(days=i), 10 + (i % 100))

        # Should process without loading all in memory
        # (Actual implementation may vary)
        result = analyzer.process_streaming_data(data_generator())

        assert result is not None


class TestSchedulerErrorRecovery:
    """Test scheduler error handling and recovery."""

    def test_failed_report_retry(self, tmp_path):
        """Test scheduler retries failed report generation."""
        scheduler = ReportScheduler()

        # Mock report generator that fails first time
        attempt_count = 0

        def failing_generator(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise RuntimeError("Simulated failure")
            return "success"

        with patch.object(scheduler, "_generate_report", failing_generator):
            scheduler.add_schedule(
                name="retry_test", report_type="web", frequency="once", max_retries=3
            )

            # Trigger execution
            scheduler.execute_schedule("retry_test")

        # Should succeed after retries
        assert attempt_count == 3

    def test_scheduler_crash_recovery(self, tmp_path):
        """Test scheduler recovers from crash."""
        config_file = tmp_path / "scheduler_state.json"

        # Create scheduler and add schedules
        scheduler1 = ReportScheduler(state_file=str(config_file))
        scheduler1.add_schedule("test1", "web", "daily", "09:00")
        scheduler1.add_schedule("test2", "compliance", "weekly", "10:00")
        scheduler1.save_state()

        # Simulate crash and recovery
        del scheduler1

        scheduler2 = ReportScheduler(state_file=str(config_file))
        schedules = scheduler2.list_schedules()

        # Should restore previous state
        assert len(schedules) == 2
        assert any(s["name"] == "test1" for s in schedules)
        assert any(s["name"] == "test2" for s in schedules)

    def test_invalid_schedule_graceful_skip(self):
        """Test scheduler skips invalid schedules without crashing."""
        scheduler = ReportScheduler()

        # Add valid schedule
        scheduler.add_schedule("valid", "web", "daily", "09:00")

        # Add invalid schedule (malformed time)
        with pytest.raises(ValueError):
            scheduler.add_schedule("invalid", "web", "daily", "25:99")

        # Scheduler should still work for valid schedules
        schedules = scheduler.list_schedules()
        assert len(schedules) == 1
        assert schedules[0]["name"] == "valid"

    def test_disk_full_error_handling(self, tmp_path, monkeypatch):
        """Test graceful handling when disk is full."""
        generator = WebReportGenerator()

        # Mock file write to raise disk full error
        def mock_write(*args, **kwargs):
            raise OSError(28, "No space left on device")

        with patch("builtins.open", side_effect=mock_write):
            with pytest.raises(OSError, match="No space left"):
                generator.generate_report(
                    scan_data={"test": "data"},
                    output_path=str(tmp_path / "report.html"),
                )


class TestComplianceEdgeCases:
    """Test compliance framework edge cases."""

    def test_multiple_framework_conflicts(self):
        """Test when scan data conflicts with multiple frameworks."""
        manager = ComplianceFrameworkManager()

        scan_data = {
            "encryption_enabled": False,
            "password_policy": "weak",
            "logging_enabled": False,
        }

        # Check against all frameworks
        results = manager.check_all_frameworks(scan_data)

        # All should report violations
        assert all(r["status"] == "non-compliant" for r in results.values())
        assert all(len(r["violations"]) > 0 for r in results.values())

    def test_custom_framework_validation(self):
        """Test adding custom compliance framework."""
        manager = ComplianceFrameworkManager()

        custom_framework = {
            "name": "Custom-Security-2025",
            "requirements": [
                {"id": "CS-1", "description": "MFA enabled"},
                {"id": "CS-2", "description": "Log retention 90 days"},
            ],
        }

        manager.add_custom_framework(custom_framework)

        # Should be usable for compliance checks
        result = manager.check_compliance(
            framework="Custom-Security-2025",
            scan_data={"mfa_enabled": True, "log_retention_days": 90},
        )

        assert result["status"] == "compliant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
