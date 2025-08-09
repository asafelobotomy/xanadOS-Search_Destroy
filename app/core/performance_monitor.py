#!/usr/bin/env python3
"""
Performance monitoring and optimization system for S&D - Search & Destroy
"""
import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

import psutil


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_io_sent: int
    network_io_recv: int
    file_handles: int
    threads: int


@dataclass
class ComponentMetrics:
    """Performance metrics for specific components."""

    component_name: str
    cpu_time: float
    memory_usage: float
    operation_count: int
    last_activity: datetime
    status: str  # 'active', 'idle', 'disabled'


class PerformanceMonitor:
    """Monitor system performance and provide optimization recommendations."""

    def __init__(self):
        self.process = psutil.Process()
        self.monitoring_active = False
        self.metrics_history: List[PerformanceMetrics] = []
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.monitoring_thread: Optional[threading.Thread] = None

        # Configuration
        self.sample_interval = 5.0  # seconds
        self.history_limit = 100  # Keep last 100 samples

        # Performance thresholds
        self.thresholds = {
            "cpu_warning": 50.0,
            "cpu_critical": 80.0,
            "memory_warning": 400.0,  # MB - Increased for PyQt6 GUI application
            "memory_critical": 800.0,  # MB - More reasonable for modern systems
            "file_handles_warning": 100,
            "file_handles_critical": 200,
        }

        # Optimization callbacks
        self.optimization_callbacks: List[Callable] = []
        
        # Warning suppression to reduce spam
        self.last_warning_time = {}
        self.warning_cooldown = 30.0  # seconds between same warning types

    def start_monitoring(self):
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True, name="PerformanceMonitor")
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)

                # Maintain history limit
                if len(self.metrics_history) > self.history_limit:
                    self.metrics_history = self.metrics_history[-self.history_limit:]

                # Check for performance issues
                self._analyze_performance(metrics)

                time.sleep(self.sample_interval)

            except Exception as e:
                print(f"Error in performance monitoring: {e}")
                time.sleep(1.0)

    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            # CPU and memory
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()

            # I/O stats
            io_counters = (
                self.process.io_counters()
                if hasattr(self.process, "io_counters")
                else None
            )
            disk_read = io_counters.read_bytes if io_counters else 0
            disk_write = io_counters.write_bytes if io_counters else 0

            # Network (system-wide approximation)
            net_io = psutil.net_io_counters()

            # File handles and threads
            try:
                file_handles = (
                    self.process.num_fds() if hasattr(
                        self.process, "num_fds") else 0)
            except (psutil.AccessDenied, AttributeError):
                file_handles = 0

            threads = self.process.num_threads()

            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_io_read=disk_read,
                disk_io_write=disk_write,
                network_io_sent=net_io.bytes_sent,
                network_io_recv=net_io.bytes_recv,
                file_handles=file_handles,
                threads=threads,
            )

        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_io_read=0,
                disk_io_write=0,
                network_io_sent=0,
                network_io_recv=0,
                file_handles=0,
                threads=0,
            )

    def _analyze_performance(self, metrics: PerformanceMetrics):
        """Analyze performance and trigger optimizations if needed."""
        issues = []
        current_time = time.time()

        # Check CPU usage
        if metrics.cpu_percent > self.thresholds["cpu_critical"]:
            if self._should_warn("cpu_critical", current_time):
                issues.append(f"Critical CPU usage: {metrics.cpu_percent:.1f}%")
            self._trigger_cpu_optimization()
        elif metrics.cpu_percent > self.thresholds["cpu_warning"]:
            if self._should_warn("cpu_warning", current_time):
                issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        # Check memory usage
        if metrics.memory_mb > self.thresholds["memory_critical"]:
            if self._should_warn("memory_critical", current_time):
                issues.append(f"Critical memory usage: {metrics.memory_mb:.1f}MB")
            self._trigger_memory_optimization()
        elif metrics.memory_mb > self.thresholds["memory_warning"]:
            if self._should_warn("memory_warning", current_time):
                issues.append(f"High memory usage: {metrics.memory_mb:.1f}MB")

        # Check file handles
        if metrics.file_handles > self.thresholds["file_handles_critical"]:
            if self._should_warn("file_handles_critical", current_time):
                issues.append(
                    f"Critical file handle usage: {metrics.file_handles}")
        elif metrics.file_handles > self.thresholds["file_handles_warning"]:
            if self._should_warn("file_handles_warning", current_time):
                issues.append(f"High file handle usage: {metrics.file_handles}")

        if issues:
            print(f"Performance issues detected: {', '.join(issues)}")

    def _should_warn(self, warning_type: str, current_time: float) -> bool:
        """Check if we should show a warning based on cooldown period."""
        last_time = self.last_warning_time.get(warning_type, 0)
        if current_time - last_time >= self.warning_cooldown:
            self.last_warning_time[warning_type] = current_time
            return True
        return False

    def _trigger_cpu_optimization(self):
        """Trigger CPU optimization measures."""
        for callback in self.optimization_callbacks:
            try:
                callback("cpu_pressure")
            except Exception as e:
                print(f"Error in optimization callback: {e}")

    def _trigger_memory_optimization(self):
        """Trigger memory optimization measures."""
        import gc

        gc.collect()

        for callback in self.optimization_callbacks:
            try:
                callback("memory_pressure")
            except Exception as e:
                print(f"Error in optimization callback: {e}")

    def add_optimization_callback(self, callback: Callable[[str], None]):
        """Add callback for performance optimization events."""
        self.optimization_callbacks.append(callback)

    def record_component_activity(
        self,
        component_name: str,
        cpu_time: float = 0.0,
        memory_usage: float = 0.0,
        operation_count: int = 1,
    ):
        """Record activity for a specific component."""
        if component_name not in self.component_metrics:
            self.component_metrics[component_name] = ComponentMetrics(
                component_name=component_name,
                cpu_time=0.0,
                memory_usage=0.0,
                operation_count=0,
                last_activity=datetime.now(),
                status="active",
            )

        metrics = self.component_metrics[component_name]
        metrics.cpu_time += cpu_time
        metrics.memory_usage = max(metrics.memory_usage, memory_usage)
        metrics.operation_count += operation_count
        metrics.last_activity = datetime.now()
        metrics.status = "active"

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_average_metrics(self, minutes: int = 5) -> Optional[Dict]:
        """Get average metrics over the specified time period."""
        if not self.metrics_history:
            return None

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return None

        avg_metrics = {
            "cpu_percent": sum(
                m.cpu_percent for m in recent_metrics) /
            len(recent_metrics),
            "memory_mb": sum(
                m.memory_mb for m in recent_metrics) /
            len(recent_metrics),
            "memory_percent": sum(
                m.memory_percent for m in recent_metrics) /
            len(recent_metrics),
            "threads": sum(
                m.threads for m in recent_metrics) /
            len(recent_metrics),
            "file_handles": sum(
                m.file_handles for m in recent_metrics) /
            len(recent_metrics),
            "sample_count": len(recent_metrics),
        }

        return avg_metrics

    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        current = self.get_current_metrics()
        average = self.get_average_metrics(5)

        if not current:
            return {"status": "no_data"}

        # Calculate performance score (0-100, higher is better)
        performance_score = 100

        if current.cpu_percent > 50:
            performance_score -= (current.cpu_percent - 50) * 0.8

        if current.memory_mb > 200:
            performance_score -= (current.memory_mb - 200) * 0.2

        performance_score = max(0, min(100, performance_score))

        return {
            "status": "active" if self.monitoring_active else "inactive",
            "performance_score": performance_score,
            "current": asdict(current) if current else None,
            "average_5min": average,
            "component_count": len(self.component_metrics),
            "active_components": [
                name
                for name, metrics in self.component_metrics.items()
                if metrics.status == "active"
            ],
            "optimization_suggestions": self._get_optimization_suggestions(),
        }

    def _get_optimization_suggestions(self) -> List[str]:
        """Generate optimization suggestions based on current metrics."""
        suggestions = []
        current = self.get_current_metrics()

        if not current:
            return suggestions

        if current.cpu_percent > 70:
            suggestions.append(
                "Consider reducing scan frequency or file monitoring scope"
            )

        if current.memory_mb > 300:
            suggestions.append(
                "Memory usage is high - consider enabling file batching")

        if current.file_handles > 50:
            suggestions.append(
                "Many file handles open - consider optimizing file watching"
            )

        if current.threads > 10:
            suggestions.append(
                "Multiple threads active - consider thread pool optimization"
            )

        # Component-specific suggestions
        file_watcher_active = any(
            "file" in name.lower() or "watch" in name.lower()
            for name in self.component_metrics.keys()
        )

        if file_watcher_active and current.cpu_percent > 30:
            suggestions.append(
                "File monitoring may be consuming CPU - consider adjusting watch paths"
            )

        return suggestions

    def save_performance_report(self, filepath: str):
        """Save performance report to file."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_performance_summary(),
            "component_metrics": {
                name: asdict(metrics)
                for name, metrics in self.component_metrics.items()
            },
            "recent_metrics": [
                # Last 20 samples
                asdict(m) for m in self.metrics_history[-20:]
            ],
        }

        try:
            with open(filepath, "w") as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving performance report: {e}")


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
