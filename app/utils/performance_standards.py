#!/usr/bin/env python3
"""
Performance Standards Library - Centralized performance optimization utilities
==============================================================================
This library provides standardized performance management for:
- Resource monitoring and optimization
- Memory management and garbage collection
- CPU usage optimization
- I/O optimization
- Caching strategies
"""

import gc
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil


class PerformanceLevel(Enum):
    """Performance optimization levels"""

    BATTERY_SAVER = "battery_saver"
    BALANCED = "balanced"
    PERFORMANCE = "performance"
    MAXIMUM = "maximum"


class ResourceType(Enum):
    """Types of system resources"""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class PerformanceMetrics:
    """Performance metrics data"""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    thread_count: int
    open_files: int


@dataclass
class PerformanceConfig:
    """Performance configuration settings"""

    max_cpu_percent: float = 80.0
    max_memory_percent: float = 85.0
    max_threads: int = 8
    gc_frequency: int = 100  # Operations before GC
    cache_size: int = 1000
    io_buffer_size: int = 65536  # 64KB
    enable_profiling: bool = False


class PerformanceOptimizer:
    """Performance optimization and monitoring"""

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.metrics_history: deque = deque(maxlen=1000)
        self.operation_counter = 0
        self._cache: Dict[str, Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._lock = threading.Lock()

        # Performance thresholds by level
        self.performance_settings = {
            PerformanceLevel.BATTERY_SAVER: {
                "max_threads": 2,
                "gc_frequency": 50,
                "cache_size": 500,
                "scan_depth": 3,
                "scan_speed": "slow",
            },
            PerformanceLevel.BALANCED: {
                "max_threads": 4,
                "gc_frequency": 100,
                "cache_size": 1000,
                "scan_depth": 5,
                "scan_speed": "normal",
            },
            PerformanceLevel.PERFORMANCE: {
                "max_threads": 8,
                "gc_frequency": 200,
                "cache_size": 2000,
                "scan_depth": 8,
                "scan_speed": "fast",
            },
            PerformanceLevel.MAXIMUM: {
                "max_threads": 16,
                "gc_frequency": 500,
                "cache_size": 5000,
                "scan_depth": 12,
                "scan_speed": "maximum",
            },
        }

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()

            # Process-specific metrics
            process = psutil.Process()
            thread_count = process.num_threads()
            open_files = len(process.open_files())

            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io_read=disk_io.read_bytes if disk_io else 0,
                disk_io_write=disk_io.write_bytes if disk_io else 0,
                network_sent=network_io.bytes_sent if network_io else 0,
                network_recv=network_io.bytes_recv if network_io else 0,
                thread_count=thread_count,
                open_files=open_files,
            )

            with self._lock:
                self.metrics_history.append(metrics)

            return metrics

        except Exception:
            # Return empty metrics on error
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_io_read=0,
                disk_io_write=0,
                network_sent=0,
                network_recv=0,
                thread_count=0,
                open_files=0,
            )

    def optimize_for_level(self, level: PerformanceLevel) -> Dict[str, Any]:
        """Optimize settings for performance level"""
        settings = self.performance_settings[level]

        # Update configuration
        self.config.max_threads = settings["max_threads"]
        self.config.gc_frequency = settings["gc_frequency"]
        self.config.cache_size = settings["cache_size"]

        # Clear cache if size changed
        if len(self._cache) > self.config.cache_size:
            self._clear_cache()

        return settings

    def track_operation(self):
        """Track an operation for performance monitoring"""
        self.operation_counter += 1

        # Trigger garbage collection based on frequency
        if self.operation_counter % self.config.gc_frequency == 0:
            self.force_garbage_collection()

    def force_garbage_collection(self):
        """Force garbage collection to free memory"""
        collected = gc.collect()
        return collected

    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key in self._cache:
                self._cache_hits += 1
                return self._cache[key]
            else:
                self._cache_misses += 1
                return None

    def cache_set(self, key: str, value: Any):
        """Set value in cache"""
        with self._lock:
            # Implement LRU eviction if cache is full
            if len(self._cache) >= self.config.cache_size:
                # Remove oldest items (simple FIFO for now)
                keys_to_remove = list(self._cache.keys())[: len(self._cache) // 2]
                for k in keys_to_remove:
                    del self._cache[k]

            self._cache[key] = value

    def _clear_cache(self):
        """Clear the cache"""
        with self._lock:
            self._cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = (
                (self._cache_hits / total_requests) if total_requests > 0 else 0.0
            )

            return {
                "cache_size": len(self._cache),
                "max_cache_size": self.config.cache_size,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": hit_rate,
            }

    def analyze_performance(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Analyze performance over time window"""
        current_time = time.time()
        window_start = current_time - (window_minutes * 60)

        with self._lock:
            # Filter metrics in time window
            recent_metrics = [
                m for m in self.metrics_history if m.timestamp >= window_start
            ]

        if not recent_metrics:
            return {"error": "No metrics available"}

        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]

        analysis = {
            "window_minutes": window_minutes,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
            },
            "threads": {
                "avg": sum(m.thread_count for m in recent_metrics)
                / len(recent_metrics),
                "max": max(m.thread_count for m in recent_metrics),
            },
        }

        # Add recommendations
        analysis["recommendations"] = self._get_performance_recommendations(analysis)

        return analysis

    def _get_performance_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Get performance recommendations based on analysis"""
        recommendations = []

        if analysis["cpu"]["avg"] > 80:
            recommendations.append(
                "High CPU usage detected - consider reducing scan threads"
            )

        if analysis["memory"]["avg"] > 85:
            recommendations.append(
                "High memory usage - increase garbage collection frequency"
            )

        if analysis["threads"]["max"] > self.config.max_threads:
            recommendations.append("Thread count exceeds limit - optimize concurrency")

        cache_stats = self.get_cache_stats()
        if cache_stats["hit_rate"] < 0.5:
            recommendations.append(
                "Low cache hit rate - consider increasing cache size"
            )

        return recommendations

    def get_optimal_thread_count(self) -> int:
        """Get optimal thread count based on system resources"""
        cpu_count = psutil.cpu_count()
        current_metrics = self.get_current_metrics()

        # Reduce threads if CPU is heavily loaded
        if current_metrics.cpu_percent > 80:
            return max(1, cpu_count // 2)
        elif current_metrics.cpu_percent > 60:
            return max(2, int(cpu_count * 0.75))
        else:
            return min(self.config.max_threads, cpu_count)


class ResourceMonitor:
    """Monitor system resources and provide alerts"""

    def __init__(self, optimizer: PerformanceOptimizer):
        self.optimizer = optimizer
        self.alerts: List[Dict[str, Any]] = []
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self, interval: float = 10.0):
        """Start resource monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,)
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)

    def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = self.optimizer.get_current_metrics()
                self._check_thresholds(metrics)
                time.sleep(interval)
            except Exception:
                continue

    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check if metrics exceed thresholds"""
        config = self.optimizer.config

        if metrics.cpu_percent > config.max_cpu_percent:
            self.alerts.append(
                {
                    "timestamp": metrics.timestamp,
                    "type": "cpu_high",
                    "value": metrics.cpu_percent,
                    "threshold": config.max_cpu_percent,
                    "message": f"CPU usage {metrics.cpu_percent:.1f}% exceeds threshold {
                        config.max_cpu_percent
                    }%",
                }
            )

        if metrics.memory_percent > config.max_memory_percent:
            self.alerts.append(
                {
                    "timestamp": metrics.timestamp,
                    "type": "memory_high",
                    "value": metrics.memory_percent,
                    "threshold": config.max_memory_percent,
                    "message": f"Memory usage {metrics.memory_percent:.1f}% exceeds threshold {
                        config.max_memory_percent
                    }%",
                }
            )

        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-limit:]


# Global performance optimizer instance
PERFORMANCE_OPTIMIZER = PerformanceOptimizer()


# Convenience functions
@contextmanager
def performance_monitoring(level: PerformanceLevel = PerformanceLevel.BALANCED):
    """Context manager for performance monitoring"""
    PERFORMANCE_OPTIMIZER.optimize_for_level(level)
    monitor = ResourceMonitor(PERFORMANCE_OPTIMIZER)
    monitor.start_monitoring()
    try:
        yield PERFORMANCE_OPTIMIZER
    finally:
        monitor.stop_monitoring()


def optimize_for_scanning(file_count: int = 1000) -> Dict[str, Any]:
    """Optimize settings for file scanning based on file count"""
    if file_count < 100:
        level = PerformanceLevel.BATTERY_SAVER
    elif file_count < 1000:
        level = PerformanceLevel.BALANCED
    elif file_count < 10000:
        level = PerformanceLevel.PERFORMANCE
    else:
        level = PerformanceLevel.MAXIMUM

    return PERFORMANCE_OPTIMIZER.optimize_for_level(level)


def get_performance_metrics() -> PerformanceMetrics:
    """Get current performance metrics"""
    return PERFORMANCE_OPTIMIZER.get_current_metrics()


def force_cleanup():
    """Force memory cleanup and garbage collection"""
    return PERFORMANCE_OPTIMIZER.force_garbage_collection()
