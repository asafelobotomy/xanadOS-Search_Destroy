"""
Performance Monitoring Framework for xanadOS Search & Destroy.

Provides comprehensive performance metrics collection, baseline benchmarking,
and automated regression testing for scanner, reporting, and dashboard operations.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil


@dataclass
class PerformanceMetric:
    """Individual performance metric measurement."""

    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    memory_delta_mb: float
    cpu_percent: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def timestamp(self) -> str:
        """ISO timestamp of measurement."""
        return datetime.fromtimestamp(self.start_time).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class PerformanceSLA:
    """Service Level Agreement for performance."""

    operation: str
    max_duration_ms: float
    max_memory_mb: float
    description: str

    def check_compliance(self, metric: PerformanceMetric) -> tuple[bool, list[str]]:
        """Check if metric meets SLA."""
        violations = []

        if metric.duration_ms > self.max_duration_ms:
            violations.append(
                f"Duration {metric.duration_ms:.2f}ms exceeds SLA {self.max_duration_ms}ms"
            )

        if abs(metric.memory_delta_mb) > self.max_memory_mb:
            violations.append(
                f"Memory delta {metric.memory_delta_mb:.2f}MB exceeds SLA {self.max_memory_mb}MB"
            )

        return (len(violations) == 0, violations)


class PerformanceMonitor:
    """Context manager for measuring performance."""

    def __init__(self, operation: str, **metadata):
        self.operation = operation
        self.metadata = metadata
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.memory_before: float | None = None
        self.memory_after: float | None = None
        self.cpu_percent: float | None = None

    def __enter__(self):
        """Start performance monitoring."""
        import os

        self.process = psutil.Process(os.getpid())

        self.start_time = time.time()
        self.memory_before = self.process.memory_info().rss / 1024 / 1024
        self.cpu_percent = self.process.cpu_percent(interval=None)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop performance monitoring and record metric."""
        self.end_time = time.time()
        self.memory_after = self.process.memory_info().rss / 1024 / 1024
        self.cpu_percent = self.process.cpu_percent(interval=None)

        if exc_type is None:  # Only record successful operations
            metric = PerformanceMetric(
                operation=self.operation,
                start_time=self.start_time,
                end_time=self.end_time,
                duration_ms=(self.end_time - self.start_time) * 1000,
                memory_before_mb=self.memory_before,
                memory_after_mb=self.memory_after,
                memory_delta_mb=self.memory_after - self.memory_before,
                cpu_percent=self.cpu_percent,
                metadata=self.metadata,
            )

            PerformanceRegistry.record(metric)

    @property
    def duration_ms(self) -> float | None:
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


class PerformanceRegistry:
    """Central registry for performance metrics."""

    _metrics: list[PerformanceMetric] = []
    _slas: dict[str, PerformanceSLA] = {}
    _baseline_file: Path | None = None

    @classmethod
    def record(cls, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        cls._metrics.append(metric)

        # Check SLA compliance if defined
        if metric.operation in cls._slas:
            sla = cls._slas[metric.operation]
            compliant, violations = sla.check_compliance(metric)

            if not compliant:
                print(f"⚠️  SLA VIOLATION for {metric.operation}:")
                for violation in violations:
                    print(f"   - {violation}")

    @classmethod
    def define_sla(cls, sla: PerformanceSLA) -> None:
        """Define an SLA for an operation."""
        cls._slas[sla.operation] = sla

    @classmethod
    def get_metrics(
        cls, operation: str | None = None, since: datetime | None = None
    ) -> list[PerformanceMetric]:
        """Get recorded metrics with optional filtering."""
        metrics = cls._metrics

        if operation:
            metrics = [m for m in metrics if m.operation == operation]

        if since:
            since_timestamp = since.timestamp()
            metrics = [m for m in metrics if m.start_time >= since_timestamp]

        return metrics

    @classmethod
    def get_statistics(cls, operation: str) -> dict[str, float]:
        """Get statistical summary for an operation."""
        metrics = cls.get_metrics(operation=operation)

        if not metrics:
            return {}

        durations = [m.duration_ms for m in metrics]
        memory_deltas = [m.memory_delta_mb for m in metrics]

        return {
            "count": len(metrics),
            "duration_mean_ms": sum(durations) / len(durations),
            "duration_min_ms": min(durations),
            "duration_max_ms": max(durations),
            "duration_p50_ms": sorted(durations)[len(durations) // 2],
            "duration_p95_ms": sorted(durations)[int(len(durations) * 0.95)],
            "duration_p99_ms": sorted(durations)[int(len(durations) * 0.99)],
            "memory_mean_mb": sum(memory_deltas) / len(memory_deltas),
            "memory_max_mb": max(memory_deltas),
        }

    @classmethod
    def save_baseline(cls, filepath: str | Path) -> None:
        """Save current metrics as performance baseline."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        baseline_data = {"created_at": datetime.now().isoformat(), "operations": {}}

        # Get unique operations
        operations = set(m.operation for m in cls._metrics)

        for operation in operations:
            stats = cls.get_statistics(operation)
            if stats:
                baseline_data["operations"][operation] = stats

        with open(filepath, "w") as f:
            json.dump(baseline_data, f, indent=2)

        cls._baseline_file = filepath
        print(f"✅ Baseline saved to {filepath}")

    @classmethod
    def load_baseline(cls, filepath: str | Path) -> dict[str, Any]:
        """Load performance baseline for comparison."""
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Baseline file not found: {filepath}")

        with open(filepath) as f:
            baseline = json.load(f)

        cls._baseline_file = filepath
        return baseline

    @classmethod
    def compare_to_baseline(
        cls, baseline_file: str | Path | None = None
    ) -> dict[str, Any]:
        """Compare current performance to baseline."""
        if baseline_file:
            baseline = cls.load_baseline(baseline_file)
        elif cls._baseline_file:
            baseline = cls.load_baseline(cls._baseline_file)
        else:
            raise ValueError("No baseline file specified or loaded")

        comparison = {
            "baseline_date": baseline["created_at"],
            "comparison_date": datetime.now().isoformat(),
            "regressions": [],
            "improvements": [],
            "unchanged": [],
        }

        for operation, baseline_stats in baseline["operations"].items():
            current_stats = cls.get_statistics(operation)

            if not current_stats:
                continue

            # Compare p95 duration (key metric)
            baseline_p95 = baseline_stats.get("duration_p95_ms", 0)
            current_p95 = current_stats.get("duration_p95_ms", 0)

            change_percent = (
                ((current_p95 - baseline_p95) / baseline_p95 * 100)
                if baseline_p95 > 0
                else 0
            )

            result = {
                "operation": operation,
                "baseline_p95_ms": baseline_p95,
                "current_p95_ms": current_p95,
                "change_percent": change_percent,
                "change_ms": current_p95 - baseline_p95,
            }

            if change_percent > 10:  # >10% slower = regression
                comparison["regressions"].append(result)
            elif change_percent < -10:  # >10% faster = improvement
                comparison["improvements"].append(result)
            else:
                comparison["unchanged"].append(result)

        return comparison

    @classmethod
    def generate_report(cls, output_file: str | Path | None = None) -> str:
        """Generate performance report."""
        operations = set(m.operation for m in cls._metrics)

        report_lines = [
            "# Performance Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Metrics: {len(cls._metrics)}",
            "",
            "## Performance by Operation",
            "",
        ]

        for operation in sorted(operations):
            stats = cls.get_statistics(operation)

            report_lines.extend(
                [
                    f"### {operation}",
                    f"- Count: {stats['count']}",
                    f"- Mean Duration: {stats['duration_mean_ms']:.2f}ms",
                    f"- P50 Duration: {stats['duration_p50_ms']:.2f}ms",
                    f"- P95 Duration: {stats['duration_p95_ms']:.2f}ms",
                    f"- P99 Duration: {stats['duration_p99_ms']:.2f}ms",
                    f"- Memory (Mean): {stats['memory_mean_mb']:.2f}MB",
                    "",
                ]
            )

            # Check SLA
            if operation in cls._slas:
                sla = cls._slas[operation]
                # Get latest metric for this operation
                latest_metrics = [m for m in cls._metrics if m.operation == operation]
                if latest_metrics:
                    latest = latest_metrics[-1]
                    compliant, violations = sla.check_compliance(latest)

                    if compliant:
                        report_lines.append(f"✅ SLA Compliant")
                    else:
                        report_lines.append(f"❌ SLA Violations:")
                        for violation in violations:
                            report_lines.append(f"   - {violation}")
                    report_lines.append("")

        report = "\n".join(report_lines)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"✅ Report saved to {output_file}")

        return report

    @classmethod
    def clear(cls) -> None:
        """Clear all recorded metrics."""
        cls._metrics.clear()


# ============================================================================
# PREDEFINED SLAs
# ============================================================================

# Scanner Operations
SCANNER_SLAS = [
    PerformanceSLA(
        operation="scan_file",
        max_duration_ms=100,
        max_memory_mb=50,
        description="Single file scan should complete in <100ms",
    ),
    PerformanceSLA(
        operation="scan_directory",
        max_duration_ms=5000,
        max_memory_mb=200,
        description="Directory scan (100 files) should complete in <5s",
    ),
]

# Reporting Operations
REPORTING_SLAS = [
    PerformanceSLA(
        operation="generate_web_report",
        max_duration_ms=2000,
        max_memory_mb=100,
        description="Web report generation should complete in <2s",
    ),
    PerformanceSLA(
        operation="trend_analysis",
        max_duration_ms=1000,
        max_memory_mb=50,
        description="Trend analysis (1000 points) should complete in <1s",
    ),
    PerformanceSLA(
        operation="compliance_check",
        max_duration_ms=500,
        max_memory_mb=30,
        description="Compliance check should complete in <500ms",
    ),
]

# Dashboard Operations
DASHBOARD_SLAS = [
    PerformanceSLA(
        operation="dashboard_refresh",
        max_duration_ms=200,
        max_memory_mb=20,
        description="Dashboard refresh should complete in <200ms",
    ),
    PerformanceSLA(
        operation="chart_render",
        max_duration_ms=500,
        max_memory_mb=30,
        description="Chart rendering should complete in <500ms",
    ),
]


def register_all_slas():
    """Register all predefined SLAs."""
    for sla in SCANNER_SLAS + REPORTING_SLAS + DASHBOARD_SLAS:
        PerformanceRegistry.define_sla(sla)


# Auto-register SLAs on module import
register_all_slas()


if __name__ == "__main__":
    # Example usage
    print("Performance Monitoring Framework Example\n")

    # Simulate some operations
    for i in range(10):
        with PerformanceMonitor("scan_file", file_size_kb=100 + i * 10):
            time.sleep(0.05 + i * 0.01)  # Simulate work

    # Generate report
    print(PerformanceRegistry.generate_report())

    # Save baseline
    PerformanceRegistry.save_baseline("performance_baseline.json")
