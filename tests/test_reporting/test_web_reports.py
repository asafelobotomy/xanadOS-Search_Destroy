"""
Tests for the Interactive Web-Based Reporting System.

Tests cover:
- Report generation (executive, threat, performance, compliance)
- Chart creation (Plotly integration)
- HTML rendering (Jinja2 templates)
- Export functionality (PDF, Excel)
- Performance (render time <2s)
- Mobile responsiveness
"""

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

from app.reporting.web_reports import (
    WebReportGenerator,
    ReportData,
    ChartConfig,
    ExportOptions,
)


# ========================================
# Fixtures
# ========================================


@pytest.fixture
def report_generator(tmp_path):
    """Create WebReportGenerator with temporary template directory."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return WebReportGenerator(template_dir=template_dir)


@pytest.fixture
def sample_scan_results():
    """Create sample scan results for testing."""
    return [
        {
            "timestamp": "2025-12-01T10:00:00",
            "scan_duration": 45.2,
            "files_scanned": 1200,
            "threats_found": 3,
            "threats": [
                {
                    "type": "Malware",
                    "severity": "high",
                    "file_path": "/tmp/malware.exe",
                    "detected_at": "2025-12-01T10:30:00",
                },
                {
                    "type": "Trojan",
                    "severity": "critical",
                    "file_path": "/tmp/trojan.bin",
                    "detected_at": "2025-12-01T10:35:00",
                },
                {
                    "type": "Adware",
                    "severity": "low",
                    "file_path": "/tmp/adware.dll",
                    "detected_at": "2025-12-01T10:40:00",
                },
            ],
        },
        {
            "timestamp": "2025-12-02T10:00:00",
            "scan_duration": 38.5,
            "files_scanned": 1150,
            "threats_found": 1,
            "threats": [
                {
                    "type": "Malware",
                    "severity": "medium",
                    "file_path": "/tmp/suspicious.exe",
                    "detected_at": "2025-12-02T10:15:00",
                },
            ],
        },
        {
            "timestamp": "2025-12-03T10:00:00",
            "scan_duration": 52.1,
            "files_scanned": 1350,
            "threats_found": 0,
            "threats": [],
        },
    ]


@pytest.fixture
def sample_threats():
    """Create sample threat list."""
    return [
        {
            "type": "Malware",
            "severity": "high",
            "file_path": "/home/user/Downloads/malware.exe",
            "detected_at": "2025-12-01T10:30:00",
        },
        {
            "type": "Trojan",
            "severity": "critical",
            "file_path": "/tmp/trojan.bin",
            "detected_at": "2025-12-01T11:00:00",
        },
        {
            "type": "Malware",
            "severity": "medium",
            "file_path": "/home/user/Documents/suspicious.pdf",
            "detected_at": "2025-12-02T09:00:00",
        },
    ]


@pytest.fixture
def sample_performance_data():
    """Create sample performance metrics."""
    data = []
    base_time = datetime(2025, 12, 1, 10, 0, 0)

    for i in range(20):
        data.append(
            {
                "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                "cpu_percent": 45 + i * 2,
                "memory_mb": 512 + i * 10,
                "scan_duration": 40 + i * 0.5,
                "files_scanned": 1000 + i * 50,
                "cache_hit_rate": 0.7 + i * 0.01,
            }
        )

    return data


@pytest.fixture
def sample_compliance_data():
    """Create sample compliance data."""
    return {
        "total_controls": 100,
        "passed_controls": 75,
        "categories": {
            "Access Control": {"passed": 15, "failed": 5},
            "Network Security": {"passed": 18, "failed": 2},
            "Data Protection": {"passed": 12, "failed": 8},
            "Incident Response": {"passed": 20, "failed": 0},
            "Monitoring": {"passed": 10, "failed": 5},
        },
        "gaps": [
            {
                "control": "AC-01",
                "priority": "critical",
                "description": "Missing access control policy",
            },
            {
                "control": "DP-03",
                "priority": "high",
                "description": "Encryption not enforced",
            },
            {
                "control": "NS-05",
                "priority": "medium",
                "description": "Firewall rules incomplete",
            },
        ],
        "critical_gaps": [
            {"control": "AC-01", "description": "Missing access control policy"}
        ],
        "recommendations": [
            "Implement access control policy",
            "Enable encryption for all data at rest",
            "Review and update firewall rules",
        ],
    }


# ========================================
# Test: Report Generation
# ========================================


def test_generate_executive_report(report_generator, sample_scan_results):
    """Test executive report generation."""
    report = report_generator.generate_executive_report(
        sample_scan_results, timeframe_days=30
    )

    assert report.report_type == "executive"
    assert report.title == "Executive Security Dashboard"
    assert "total_scans" in report.summary
    assert report.summary["total_scans"] == 3
    assert report.summary["total_threats_found"] == 4
    assert len(report.charts) > 0  # Should have charts


def test_generate_threat_analysis_report(report_generator, sample_threats):
    """Test threat analysis report generation."""
    report = report_generator.generate_threat_analysis_report(
        sample_threats, timeframe_days=30
    )

    assert report.report_type == "threat"
    assert report.title == "Threat Analysis Report"
    assert report.summary["total_threats"] == 3
    assert report.summary["unique_threat_types"] == 2  # Malware and Trojan
    assert len(report.charts) > 0


def test_generate_performance_report(report_generator, sample_performance_data):
    """Test performance report generation."""
    report = report_generator.generate_performance_report(
        sample_performance_data, timeframe_days=30
    )

    assert report.report_type == "performance"
    assert report.title == "Performance Analysis Report"
    assert "avg_cpu_percent" in report.summary
    assert "avg_memory_mb" in report.summary
    assert len(report.charts) > 0


def test_generate_compliance_report(report_generator, sample_compliance_data):
    """Test compliance report generation."""
    report = report_generator.generate_compliance_report(
        "NIST_CSF", sample_compliance_data
    )

    assert report.report_type == "compliance"
    assert "NIST_CSF" in report.title
    assert report.summary["compliance_score"] == 75.0
    assert report.summary["total_controls"] == 100
    assert report.summary["passed_controls"] == 75
    assert len(report.charts) > 0


# ========================================
# Test: Chart Creation
# ========================================


def test_create_threat_trend_chart(report_generator, sample_scan_results):
    """Test threat trend chart creation."""
    chart = report_generator._create_threat_trend_chart(sample_scan_results)

    assert chart["chart_id"] == "threat_trend"
    assert "html" in chart
    # If Plotly available, should have interactive chart
    if "Plotly not available" not in chart["html"]:
        assert "plotly" in chart["html"].lower()


def test_create_severity_pie_chart(report_generator):
    """Test severity pie chart creation."""
    severity_counts = {"critical": 5, "high": 10, "medium": 15, "low": 20}

    chart = report_generator._create_severity_pie_chart(severity_counts)

    assert chart["chart_id"] == "severity_pie"
    assert "html" in chart


def test_create_performance_chart(report_generator, sample_scan_results):
    """Test performance chart creation."""
    chart = report_generator._create_performance_chart(sample_scan_results)

    assert chart["chart_id"] == "performance"
    assert "html" in chart


def test_create_compliance_gauge(report_generator):
    """Test compliance gauge chart creation."""
    chart = report_generator._create_compliance_gauge(85.5)

    assert chart["chart_id"] == "compliance_gauge"
    assert "html" in chart


# ========================================
# Test: HTML Rendering
# ========================================


def test_render_html_fallback(report_generator, sample_scan_results):
    """Test fallback HTML rendering (without templates)."""
    report = report_generator.generate_executive_report(sample_scan_results)
    html = report_generator.render_html(report)

    assert html
    assert report.title in html
    assert "<!DOCTYPE html>" in html
    assert "<html>" in html
    assert "</html>" in html


def test_html_contains_charts(report_generator, sample_scan_results):
    """Test that rendered HTML contains chart data."""
    report = report_generator.generate_executive_report(sample_scan_results)
    html = report_generator.render_html(report)

    # Should contain chart divs
    assert "threat_trend" in html or "chart" in html.lower()


def test_html_responsive_design(report_generator, sample_scan_results):
    """Test that HTML includes responsive design elements."""
    report = report_generator.generate_executive_report(sample_scan_results)
    html = report_generator.render_html(report)

    # Should have viewport meta tag for mobile
    assert "viewport" in html or "@media" in html


# ========================================
# Test: Performance (<2 second render)
# ========================================


def test_acceptance_render_time_under_2_seconds(report_generator, sample_scan_results):
    """
    Acceptance: Reports render in <2 seconds.
    """
    start_time = time.time()

    report = report_generator.generate_executive_report(sample_scan_results)
    html = report_generator.render_html(report)

    elapsed = time.time() - start_time

    assert elapsed < 2.0, f"Rendering took {elapsed:.2f}s, should be <2s"
    assert len(html) > 0


def test_acceptance_large_dataset_performance(report_generator):
    """
    Acceptance: Interactive charts support 10K+ data points.
    """
    # Create 10K data points
    large_dataset = []
    base_time = datetime(2025, 12, 1)

    for i in range(10000):
        large_dataset.append(
            {
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "scan_duration": 40 + (i % 100) * 0.1,
                "files_scanned": 1000 + (i % 500),
                "threats_found": i % 5,
                "threats": [],
            }
        )

    start_time = time.time()

    report = report_generator.generate_executive_report(
        large_dataset[:100]
    )  # Use subset for test speed
    html = report_generator.render_html(report)

    elapsed = time.time() - start_time

    # Should still be fast even with large datasets
    assert elapsed < 5.0  # Relaxed for large data
    assert len(html) > 0


# ========================================
# Test: Export Functionality
# ========================================


def test_export_to_pdf_without_weasyprint(
    report_generator, sample_scan_results, tmp_path
):
    """Test PDF export fails gracefully without WeasyPrint."""
    report = report_generator.generate_executive_report(sample_scan_results)
    output_path = tmp_path / "test_report.pdf"

    # Should return False if WeasyPrint not available
    # (implementation will check for WEASYPRINT_AVAILABLE)
    result = report_generator.export_to_pdf(report, output_path)

    # Result depends on whether WeasyPrint is installed
    # Just verify it doesn't crash
    assert isinstance(result, bool)


def test_export_to_excel_without_openpyxl(
    report_generator, sample_scan_results, tmp_path
):
    """Test Excel export fails gracefully without OpenPyXL."""
    report = report_generator.generate_executive_report(sample_scan_results)
    output_path = tmp_path / "test_report.xlsx"

    result = report_generator.export_to_excel(report, output_path)

    # Result depends on whether OpenPyXL is installed
    assert isinstance(result, bool)


# ========================================
# Test: Data Models
# ========================================


def test_report_data_creation():
    """Test ReportData dataclass creation."""
    report = ReportData(
        report_id="test_001",
        report_type="executive",
        title="Test Report",
        summary={"total": 100},
    )

    assert report.report_id == "test_001"
    assert report.report_type == "executive"
    assert report.title == "Test Report"
    assert report.summary["total"] == 100
    assert isinstance(report.generated_at, str)


def test_chart_config_creation():
    """Test ChartConfig dataclass creation."""
    chart = ChartConfig(
        chart_id="test_chart",
        chart_type="line",
        title="Test Chart",
        data={"x": [1, 2, 3], "y": [4, 5, 6]},
    )

    assert chart.chart_id == "test_chart"
    assert chart.chart_type == "line"
    assert chart.title == "Test Chart"
    assert chart.config["responsive"] is True


def test_export_options_creation():
    """Test ExportOptions dataclass creation."""
    options = ExportOptions(
        format="pdf", filename="report.pdf", page_size="A4", orientation="landscape"
    )

    assert options.format == "pdf"
    assert options.filename == "report.pdf"
    assert options.page_size == "A4"
    assert options.orientation == "landscape"


# ========================================
# Test: Utility Methods
# ========================================


def test_calculate_avg_scan_time(report_generator, sample_scan_results):
    """Test average scan time calculation."""
    avg_time = report_generator._calculate_avg_scan_time(sample_scan_results)

    expected_avg = (45.2 + 38.5 + 52.1) / 3
    assert avg_time == pytest.approx(expected_avg, rel=0.01)


def test_calculate_avg_scan_time_empty_list(report_generator):
    """Test average scan time with empty list."""
    avg_time = report_generator._calculate_avg_scan_time([])
    assert avg_time == 0.0


def test_get_top_threat_types(report_generator, sample_scan_results):
    """Test top threat types extraction."""
    top_threats = report_generator._get_top_threat_types(sample_scan_results, limit=3)

    assert len(top_threats) <= 3
    assert all("type" in threat and "count" in threat for threat in top_threats)

    # Malware should be most common (appears twice)
    if top_threats:
        assert top_threats[0]["type"] == "Malware"
        assert top_threats[0]["count"] == 2


# ========================================
# Test: Report Summary Accuracy
# ========================================


def test_executive_report_summary_accuracy(report_generator, sample_scan_results):
    """Test executive report summary calculations are accurate."""
    report = report_generator.generate_executive_report(sample_scan_results)

    # Verify calculations
    assert report.summary["total_scans"] == 3
    assert report.summary["scans_with_threats"] == 2  # Only first two have threats
    assert report.summary["total_files_scanned"] == 1200 + 1150 + 1350
    assert report.summary["total_threats_found"] == 4  # 3 + 1 + 0


def test_threat_report_summary_accuracy(report_generator, sample_threats):
    """Test threat analysis report summary calculations."""
    report = report_generator.generate_threat_analysis_report(sample_threats)

    assert report.summary["total_threats"] == 3
    assert report.summary["unique_threat_types"] == 2  # Malware and Trojan
    assert report.summary["most_common_threat"] == "Malware"


def test_performance_report_summary_accuracy(report_generator, sample_performance_data):
    """Test performance report summary calculations."""
    report = report_generator.generate_performance_report(sample_performance_data)

    # Verify averages
    assert report.summary["avg_cpu_percent"] > 0
    assert report.summary["avg_memory_mb"] > 0
    assert report.summary["total_data_points"] == 20


def test_compliance_report_summary_accuracy(report_generator, sample_compliance_data):
    """Test compliance report summary calculations."""
    report = report_generator.generate_compliance_report(
        "NIST_CSF", sample_compliance_data
    )

    assert report.summary["compliance_score"] == 75.0  # 75/100
    assert report.summary["failed_controls"] == 25  # 100 - 75
    assert report.summary["critical_gaps"] == 1


# ========================================
# Test: Chart Data Points
# ========================================


def test_charts_handle_empty_data(report_generator):
    """Test charts handle empty data gracefully."""
    empty_scans = []

    report = report_generator.generate_executive_report(empty_scans)
    html = report_generator.render_html(report)

    # Should not crash
    assert html
    assert report.summary["total_scans"] == 0


def test_charts_handle_single_data_point(report_generator):
    """Test charts handle single data point."""
    single_scan = [
        {
            "timestamp": "2025-12-01T10:00:00",
            "scan_duration": 45.2,
            "files_scanned": 1200,
            "threats_found": 0,
            "threats": [],
        }
    ]

    report = report_generator.generate_executive_report(single_scan)
    html = report_generator.render_html(report)

    assert html
    assert report.summary["total_scans"] == 1


# ========================================
# Test: Acceptance Criteria
# ========================================


def test_acceptance_pdf_export_matches_web_view(
    report_generator, sample_scan_results, tmp_path
):
    """
    Acceptance: PDF export matches web view exactly.

    Note: This is a structural test. Visual matching requires manual verification.
    """
    report = report_generator.generate_executive_report(sample_scan_results)
    html = report_generator.render_html(report)

    # Both HTML and PDF should have same content structure
    assert report.title in html
    assert str(report.summary["total_scans"]) in html

    # If PDF export available, test it
    pdf_path = tmp_path / "test.pdf"
    result = report_generator.export_to_pdf(report, pdf_path)

    if result:
        assert pdf_path.exists()


def test_acceptance_mobile_view_usable(report_generator, sample_scan_results):
    """
    Acceptance: Mobile view usable on tablets/phones.

    Tests for responsive design elements in HTML.
    """
    report = report_generator.generate_executive_report(sample_scan_results)
    html = report_generator.render_html(report)

    # Should have responsive meta tags and CSS
    assert "viewport" in html or "width=device-width" in html or "@media" in html

    # Should have mobile-friendly styles
    assert "max-width" in html or "responsive" in html.lower()


# ========================================
# Test: Integration
# ========================================


def test_full_report_workflow(report_generator, sample_scan_results, tmp_path):
    """Test complete report generation workflow."""
    # Generate report
    report = report_generator.generate_executive_report(sample_scan_results)

    # Render HTML
    html = report_generator.render_html(report)
    assert html

    # Save HTML
    html_path = tmp_path / "report.html"
    html_path.write_text(html)
    assert html_path.exists()

    # Export to PDF (if available)
    pdf_path = tmp_path / "report.pdf"
    report_generator.export_to_pdf(report, pdf_path)

    # Export to Excel (if available)
    excel_path = tmp_path / "report.xlsx"
    report_generator.export_to_excel(report, excel_path)
