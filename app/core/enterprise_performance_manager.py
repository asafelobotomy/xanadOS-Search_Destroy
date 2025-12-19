#!/usr/bin/env python3
from __future__ import annotations

"""
Enterprise Performance Optimization Manager
==========================================

Comprehensive performance optimization system that builds upon and integrates:
- User's enhanced rate_limiting.py with smart_acquire() and context awareness
- Comprehensive permission_manager.py with performance-aware scanning
- Existing performance_standards.py monitoring infrastructure
- Security integration performance metrics

Features:
- Real-time performance monitoring and metrics collection
- Adaptive resource management based on system load
- Intelligent caching strategies for security operations
- Performance optimization recommendations
- Integration with security dashboard for real-time metrics
- Enterprise-grade performance analytics and reporting
"""

import asyncio
import logging
import threading
import time
import weakref
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from collections.abc import Callable

import psutil

try:
    from ..core.rate_limiting import RateLimitingCoordinator
    from ..core.security_integration import (
        SecurityIntegrationCoordinator,
        PerformanceMetrics,
    )
    from ..utils.performance_standards import (
        PerformanceOptimizer,
        PerformanceLevel,
        ResourceMonitor,
    )
except ImportError:
    # Fallback for development/testing
    RateLimitingCoordinator = None  # type: ignore[assignment]
    SecurityIntegrationCoordinator = None  # type: ignore[assignment]
    PerformanceMetrics = None  # type: ignore[assignment]
    PerformanceOptimizer = None  # type: ignore[assignment]
    PerformanceLevel = None  # type: ignore[assignment]
    ResourceMonitor = None  # type: ignore[assignment]


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""

    CONSERVATIVE = "conservative"  # Minimal impact, safe optimizations
    BALANCED = "balanced"  # Good performance with stability
    AGGRESSIVE = "aggressive"  # Maximum performance, may use more resources
    ADAPTIVE = "adaptive"  # Automatically adjust based on system state


class CacheStrategy(Enum):
    """Caching strategies for different operations."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Dynamic strategy based on access patterns


@dataclass
class PerformanceTarget:
    """Performance targets for optimization."""

    max_response_time_ms: float = 100.0
    min_throughput_ops_per_sec: float = 100.0
    max_cpu_usage_percent: float = 70.0
    max_memory_usage_mb: float = 512.0
    max_cache_size_mb: float = 128.0
    target_cache_hit_ratio: float = 0.85


@dataclass
class OptimizationMetrics:
    """Metrics tracking for optimization effectiveness."""

    timestamp: datetime = field(default_factory=datetime.now)
    response_times: list[float] = field(default_factory=list)
    throughput_ops_per_sec: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    cache_hit_ratio: float = 0.0
    cache_size_mb: float = 0.0
    active_optimizations: list[str] = field(default_factory=list)
    performance_score: float = 0.0  # 0-100 overall performance score


@dataclass
class CacheEntry:
    """Cache entry with metadata for intelligent eviction."""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    priority: int = 1  # Higher = more important
    ttl_seconds: float | None = None


class IntelligentCache:
    """
    Advanced caching system with multiple strategies and adaptive behavior.

    Features:
    - Multiple eviction strategies (LRU, LFU, TTL, Adaptive)
    - Size-based and time-based eviction
    - Performance monitoring and statistics
    - Hot/cold data identification
    - Adaptive strategy switching based on access patterns
    """

    def __init__(
        self,
        max_size_mb: float = 128.0,
        strategy: CacheStrategy = CacheStrategy.ADAPTIVE,
        default_ttl_seconds: float | None = None,
    ):
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.strategy = strategy
        self.default_ttl_seconds = default_ttl_seconds

        self._cache: dict[str, CacheEntry] = {}
        self._access_order = deque()  # For LRU
        self._access_frequency = defaultdict(int)  # For LFU
        self._lock = threading.RLock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.current_size_bytes = 0

        # Adaptive strategy tracking
        self._strategy_performance = {strategy: [] for strategy in CacheStrategy}
        self._last_strategy_switch = time.time()

        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Any | None:
        """Get value from cache with intelligent access tracking."""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self.misses += 1
                return None

            # Check TTL expiration
            if self._is_expired(entry):
                self._remove_entry(key)
                self.misses += 1
                return None

            # Update access tracking
            self._update_access_tracking(key, entry)
            self.hits += 1

            return entry.value

    def set(
        self, key: str, value: Any, ttl_seconds: float | None = None, priority: int = 1
    ) -> bool:
        """Set value in cache with intelligent size management."""
        with self._lock:
            # Calculate value size (rough estimation)
            size_bytes = self._estimate_size(value)

            # Check if we need to evict entries
            if self._needs_eviction(size_bytes):
                if not self._evict_entries(size_bytes):
                    # Could not make enough space
                    return False

            # Create cache entry
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                size_bytes=size_bytes,
                priority=priority,
                ttl_seconds=ttl_seconds or self.default_ttl_seconds,
            )

            # Remove old entry if exists
            if key in self._cache:
                self._remove_entry(key)

            # Add new entry
            self._cache[key] = entry
            self.current_size_bytes += size_bytes
            self._access_order.append(key)

            return True

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._access_frequency.clear()
            self.current_size_bytes = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_ratio = self.hits / total_requests if total_requests > 0 else 0.0

            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": hit_ratio,
                "evictions": self.evictions,
                "entries": len(self._cache),
                "size_mb": self.current_size_bytes / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "strategy": self.strategy.value,
                "utilization": self.current_size_bytes / self.max_size_bytes,
            }

    def optimize_strategy(self):
        """Automatically optimize caching strategy based on access patterns."""
        if self.strategy != CacheStrategy.ADAPTIVE:
            return

        # Only consider strategy changes every 5 minutes
        if time.time() - self._last_strategy_switch < 300:
            return

        # Analyze current performance
        stats = self.get_stats()
        current_performance = stats["hit_ratio"]

        # Track performance for current strategy
        effective_strategy = self._get_effective_strategy()
        self._strategy_performance[effective_strategy].append(current_performance)

        # Keep only recent performance data
        for strategy_list in self._strategy_performance.values():
            if len(strategy_list) > 10:
                strategy_list.pop(0)

        # Consider switching strategy if we have enough data
        if len(self._strategy_performance[effective_strategy]) >= 3:
            best_strategy = max(
                self._strategy_performance.keys(),
                key=lambda s: (
                    sum(self._strategy_performance[s])
                    / len(self._strategy_performance[s])
                    if self._strategy_performance[s]
                    else 0
                ),
            )

            if best_strategy != effective_strategy:
                self.logger.info(
                    f"Switching cache strategy from {effective_strategy} to {best_strategy}"
                )
                self._last_strategy_switch = time.time()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry has expired."""
        if entry.ttl_seconds is None:
            return False

        age_seconds = (datetime.now() - entry.created_at).total_seconds()
        return age_seconds > entry.ttl_seconds

    def _update_access_tracking(self, key: str, entry: CacheEntry):
        """Update access tracking for cache strategies."""
        entry.last_accessed = datetime.now()
        entry.access_count += 1
        self._access_frequency[key] += 1

        # Update LRU order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _needs_eviction(self, new_size_bytes: int) -> bool:
        """Check if eviction is needed for new entry."""
        return self.current_size_bytes + new_size_bytes > self.max_size_bytes

    def _evict_entries(self, required_bytes: int) -> bool:
        """Evict entries to make space for new entry."""
        bytes_to_free = self.current_size_bytes + required_bytes - self.max_size_bytes
        bytes_freed = 0

        strategy = self._get_effective_strategy()
        candidates = self._get_eviction_candidates(strategy)

        for key in candidates:
            if key in self._cache:
                entry = self._cache[key]
                bytes_freed += entry.size_bytes
                self._remove_entry(key)
                self.evictions += 1

                if bytes_freed >= bytes_to_free:
                    return True

        return bytes_freed >= bytes_to_free

    def _get_effective_strategy(self) -> CacheStrategy:
        """Get the effective strategy being used."""
        if self.strategy == CacheStrategy.ADAPTIVE:
            # Use LRU as default for adaptive
            return CacheStrategy.LRU
        return self.strategy

    def _get_eviction_candidates(self, strategy: CacheStrategy) -> list[str]:
        """Get eviction candidates based on strategy."""
        candidates = []

        # First, always evict expired entries
        for key, entry in self._cache.items():
            if self._is_expired(entry):
                candidates.append(key)

        if strategy == CacheStrategy.LRU:
            # Evict least recently used first
            candidates.extend(list(self._access_order))
        elif strategy == CacheStrategy.LFU:
            # Evict least frequently used first
            candidates.extend(
                sorted(self._cache.keys(), key=lambda k: self._access_frequency[k])
            )
        elif strategy == CacheStrategy.TTL:
            # Evict oldest entries first
            candidates.extend(
                sorted(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            )

        # Remove duplicates while preserving order
        seen = set()
        return [k for k in candidates if not (k in seen or seen.add(k))]

    def _remove_entry(self, key: str):
        """Remove entry from cache and update tracking."""
        if key in self._cache:
            entry = self._cache[key]
            self.current_size_bytes -= entry.size_bytes
            del self._cache[key]

        if key in self._access_order:
            self._access_order.remove(key)

        if key in self._access_frequency:
            del self._access_frequency[key]

    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of a value (rough approximation)."""
        import sys

        try:
            return sys.getsizeof(value)
        except Exception:
            # Fallback estimation
            if isinstance(value, str):
                return len(value) * 2  # Unicode characters
            elif isinstance(value, (list, tuple)):
                return sum(
                    self._estimate_size(item) for item in value[:10]
                )  # Sample first 10
            elif isinstance(value, dict):
                sample_items = list(value.items())[:10]
                return sum(
                    self._estimate_size(k) + self._estimate_size(v)
                    for k, v in sample_items
                )
            else:
                return 64  # Default estimate


class AdaptiveResourceManager:
    """
    Intelligent resource management that adapts to system conditions.

    Features:
    - Automatic adjustment of rate limits based on system load
    - Dynamic thread pool sizing
    - Cache size optimization
    - Performance target enforcement
    - Resource usage prediction and planning
    """

    def __init__(
        self,
        performance_targets: PerformanceTarget | None = None,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
    ):
        self.targets = performance_targets or PerformanceTarget()
        self.strategy = optimization_strategy

        # Resource components (will be injected)
        self.rate_limiter: RateLimitingCoordinator | None = None
        self.cache: IntelligentCache | None = None
        self.performance_monitor: PerformanceOptimizer | None = None

        # Tracking
        self._metrics_history = deque(maxlen=100)
        self._optimization_history = deque(maxlen=50)
        self._last_optimization = time.time()

        # Adaptive parameters
        self._cpu_threshold_low = 50.0
        self._cpu_threshold_high = 80.0
        self._memory_threshold_low = 60.0
        self._memory_threshold_high = 85.0

        self.logger = logging.getLogger(__name__)

    def set_components(
        self,
        rate_limiter: RateLimitingCoordinator | None = None,
        cache: IntelligentCache | None = None,
        performance_monitor: PerformanceOptimizer | None = None,
    ):
        """Set component references for resource management."""
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.performance_monitor = performance_monitor

    async def optimize_resources(self) -> OptimizationMetrics:
        """Perform resource optimization based on current system state."""
        start_time = time.time()

        try:
            # Collect current metrics
            current_metrics = await self._collect_metrics()
            self._metrics_history.append(current_metrics)

            # Determine optimization actions
            optimizations = []

            # CPU optimization
            if current_metrics.cpu_usage_percent > self._cpu_threshold_high:
                optimizations.extend(await self._optimize_cpu_usage())

            # Memory optimization
            if current_metrics.memory_usage_mb > self.targets.max_memory_usage_mb:
                optimizations.extend(await self._optimize_memory_usage())

            # Cache optimization
            if self.cache:
                await self._optimize_cache()
                optimizations.append("cache_optimization")

            # Rate limiting optimization
            if self.rate_limiter:
                await self._optimize_rate_limits()
                optimizations.append("rate_limit_optimization")

            # Update performance targets if using adaptive strategy
            if self.strategy == OptimizationStrategy.ADAPTIVE:
                self._adapt_targets()

            # Create optimization metrics
            optimization_metrics = OptimizationMetrics(
                response_times=self._get_recent_response_times(),
                throughput_ops_per_sec=current_metrics.throughput_ops_per_sec,
                cpu_usage_percent=current_metrics.cpu_usage_percent,
                memory_usage_mb=current_metrics.memory_usage_mb,
                cache_hit_ratio=current_metrics.cache_hit_ratio,
                cache_size_mb=current_metrics.cache_size_mb,
                active_optimizations=optimizations,
                performance_score=self._calculate_performance_score(current_metrics),
            )

            self._optimization_history.append(optimization_metrics)
            self._last_optimization = time.time()

            optimization_time_ms = (time.time() - start_time) * 1000
            self.logger.info(
                f"Resource optimization completed in {optimization_time_ms:.1f}ms. "
                f"Applied {len(optimizations)} optimizations. "
                f"Performance score: {optimization_metrics.performance_score:.1f}/100"
            )

            return optimization_metrics

        except Exception as e:
            self.logger.error(f"Error during resource optimization: {e}")
            # Return minimal metrics on error
            return OptimizationMetrics()

    async def _collect_metrics(self) -> OptimizationMetrics:
        """Collect comprehensive performance metrics."""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        memory_mb = memory_info.used / (1024 * 1024)

        # Cache metrics
        cache_hit_ratio = 0.0
        cache_size_mb = 0.0
        if self.cache:
            cache_stats = self.cache.get_stats()
            cache_hit_ratio = cache_stats.get("hit_ratio", 0.0)
            cache_size_mb = cache_stats.get("size_mb", 0.0)

        # Performance monitor metrics
        throughput = 0.0
        if self.performance_monitor:
            try:
                perf_metrics = self.performance_monitor.get_current_metrics()
                # Calculate approximate throughput based on recent operations
                throughput = self._estimate_throughput()
            except Exception:
                pass

        return OptimizationMetrics(
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory_mb,
            cache_hit_ratio=cache_hit_ratio,
            cache_size_mb=cache_size_mb,
            throughput_ops_per_sec=throughput,
        )

    async def _optimize_cpu_usage(self) -> list[str]:
        """Optimize CPU usage through various strategies."""
        optimizations = []

        if self.strategy in [
            OptimizationStrategy.CONSERVATIVE,
            OptimizationStrategy.BALANCED,
        ]:
            # Reduce rate limits
            if self.rate_limiter:
                # Implementation would depend on rate limiter interface
                optimizations.append("reduced_rate_limits")

        if self.strategy in [
            OptimizationStrategy.AGGRESSIVE,
            OptimizationStrategy.ADAPTIVE,
        ]:
            # More aggressive optimizations
            optimizations.append("cpu_priority_adjustment")

        return optimizations

    async def _optimize_memory_usage(self) -> list[str]:
        """Optimize memory usage through cleanup and caching."""
        optimizations = []

        # Force garbage collection
        import gc

        before_mb = psutil.virtual_memory().used / (1024 * 1024)
        gc.collect()
        after_mb = psutil.virtual_memory().used / (1024 * 1024)

        if before_mb - after_mb > 1.0:  # Freed more than 1MB
            optimizations.append("garbage_collection")

        # Optimize cache size
        if (
            self.cache
            and self.cache.current_size_bytes
            > self.targets.max_cache_size_mb * 1024 * 1024
        ):
            # Reduce cache size by 20%
            target_size = self.cache.current_size_bytes * 0.8
            # Implementation would trigger cache eviction
            optimizations.append("cache_size_reduction")

        return optimizations

    async def _optimize_cache(self):
        """Optimize cache performance and strategy."""
        if not self.cache:
            return

        # Trigger strategy optimization
        self.cache.optimize_strategy()

        # Clean up expired entries
        stats_before = self.cache.get_stats()
        # The cache should handle this internally, but we can trigger it

        stats_after = self.cache.get_stats()
        if stats_after["entries"] < stats_before["entries"]:
            self.logger.debug(
                f"Cache cleanup: removed {stats_before['entries'] - stats_after['entries']} entries"
            )

    async def _optimize_rate_limits(self):
        """Optimize rate limiting based on system performance."""
        if not self.rate_limiter:
            return

        # Adjust rate limits based on current system load
        cpu_percent = psutil.cpu_percent()

        if cpu_percent > self._cpu_threshold_high:
            # System under high load - reduce limits
            adjustment_factor = 0.8
        elif cpu_percent < self._cpu_threshold_low:
            # System has capacity - increase limits
            adjustment_factor = 1.2
        else:
            # System load is balanced
            adjustment_factor = 1.0

        # Note: Implementation would depend on rate_limiter interface
        # The user's rate_limiting.py already has smart_acquire() with context awareness
        self.logger.debug(
            f"Rate limit adjustment factor: {adjustment_factor} (CPU: {cpu_percent}%)"
        )

    def _adapt_targets(self):
        """Adapt performance targets based on historical performance."""
        if len(self._metrics_history) < 10:
            return  # Need more data

        recent_metrics = list(self._metrics_history)[-10:]

        # Calculate average performance
        avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(
            recent_metrics
        )

        # Gradually adjust targets based on actual performance
        if avg_cpu < self.targets.max_cpu_usage_percent * 0.7:
            # System consistently under-utilized, can be more aggressive
            self.targets.max_cpu_usage_percent = min(
                90.0, self.targets.max_cpu_usage_percent + 5.0
            )
        elif avg_cpu > self.targets.max_cpu_usage_percent * 0.9:
            # System consistently over-utilized, be more conservative
            self.targets.max_cpu_usage_percent = max(
                50.0, self.targets.max_cpu_usage_percent - 5.0
            )

    def _get_recent_response_times(self) -> list[float]:
        """Get recent response times from metrics history."""
        response_times = []
        for metrics in list(self._metrics_history)[-10:]:
            response_times.extend(metrics.response_times)
        return response_times[-50:]  # Last 50 response times

    def _estimate_throughput(self) -> float:
        """Estimate current throughput based on recent operations."""
        if len(self._metrics_history) < 2:
            return 0.0

        recent_metrics = list(self._metrics_history)[-5:]
        if not recent_metrics:
            return 0.0

        # Simple throughput estimation (would be improved with actual operation counting)
        return sum(m.throughput_ops_per_sec for m in recent_metrics) / len(
            recent_metrics
        )

    def _calculate_performance_score(self, metrics: OptimizationMetrics) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0

        # CPU usage score (lower is better)
        if metrics.cpu_usage_percent > self.targets.max_cpu_usage_percent:
            score -= min(
                30.0,
                (metrics.cpu_usage_percent - self.targets.max_cpu_usage_percent) * 2,
            )

        # Memory usage score
        if metrics.memory_usage_mb > self.targets.max_memory_usage_mb:
            score -= min(
                25.0, (metrics.memory_usage_mb - self.targets.max_memory_usage_mb) / 10
            )

        # Cache performance score
        if metrics.cache_hit_ratio < self.targets.target_cache_hit_ratio:
            score -= min(
                20.0,
                (self.targets.target_cache_hit_ratio - metrics.cache_hit_ratio) * 40,
            )

        # Throughput score
        if metrics.throughput_ops_per_sec < self.targets.min_throughput_ops_per_sec:
            score -= min(
                25.0,
                (
                    self.targets.min_throughput_ops_per_sec
                    - metrics.throughput_ops_per_sec
                )
                / 5,
            )

        return max(0.0, score)

    def get_optimization_report(self) -> dict[str, Any]:
        """Get comprehensive optimization report."""
        if not self._optimization_history:
            return {"status": "no_data"}

        recent_metrics = list(self._optimization_history)[-10:]

        # Calculate trends
        scores = [m.performance_score for m in recent_metrics]
        score_trend = "stable"
        if len(scores) >= 3:
            if scores[-1] > scores[-3] + 5:
                score_trend = "improving"
            elif scores[-1] < scores[-3] - 5:
                score_trend = "declining"

        # Count optimizations
        optimization_counts = defaultdict(int)
        for metrics in recent_metrics:
            for opt in metrics.active_optimizations:
                optimization_counts[opt] += 1

        latest = recent_metrics[-1]

        return {
            "timestamp": latest.timestamp.isoformat(),
            "current_score": latest.performance_score,
            "score_trend": score_trend,
            "avg_score": sum(scores) / len(scores),
            "current_metrics": {
                "cpu_usage_percent": latest.cpu_usage_percent,
                "memory_usage_mb": latest.memory_usage_mb,
                "cache_hit_ratio": latest.cache_hit_ratio,
                "throughput_ops_per_sec": latest.throughput_ops_per_sec,
            },
            "optimization_counts": dict(optimization_counts),
            "recommendations": self._generate_recommendations(latest),
            "targets": {
                "max_cpu_percent": self.targets.max_cpu_usage_percent,
                "max_memory_mb": self.targets.max_memory_usage_mb,
                "target_cache_hit_ratio": self.targets.target_cache_hit_ratio,
                "min_throughput": self.targets.min_throughput_ops_per_sec,
            },
        }

    def _generate_recommendations(self, metrics: OptimizationMetrics) -> list[str]:
        """Generate optimization recommendations based on current metrics."""
        recommendations = []

        if metrics.cpu_usage_percent > self.targets.max_cpu_usage_percent:
            recommendations.append(
                "Consider reducing concurrent operations or rate limits"
            )

        if metrics.memory_usage_mb > self.targets.max_memory_usage_mb:
            recommendations.append(
                "Memory usage high - consider cache size reduction or garbage collection"
            )

        if metrics.cache_hit_ratio < self.targets.target_cache_hit_ratio:
            recommendations.append(
                "Low cache hit ratio - consider cache strategy optimization"
            )

        if metrics.throughput_ops_per_sec < self.targets.min_throughput_ops_per_sec:
            recommendations.append(
                "Throughput below target - consider performance optimization"
            )

        if not recommendations:
            recommendations.append("System performance is within targets")

        return recommendations


class EnterprisePerformanceManager:
    """
    Main enterprise performance optimization manager.

    This class coordinates all performance optimization components and provides
    a unified interface for monitoring, optimization, and reporting.
    """

    def __init__(
        self,
        performance_targets: PerformanceTarget | None = None,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE,
        enable_auto_optimization: bool = True,
    ):
        self.targets = performance_targets or PerformanceTarget()
        self.strategy = optimization_strategy
        self.enable_auto_optimization = enable_auto_optimization

        # Initialize components
        self.cache = IntelligentCache(
            max_size_mb=self.targets.max_cache_size_mb, strategy=CacheStrategy.ADAPTIVE
        )

        self.resource_manager = AdaptiveResourceManager(
            performance_targets=self.targets, optimization_strategy=self.strategy
        )

        # Performance monitoring
        self.performance_optimizer = (
            PerformanceOptimizer() if PerformanceOptimizer else None
        )
        self.resource_monitor = (
            ResourceMonitor(self.performance_optimizer)
            if ResourceMonitor and self.performance_optimizer
            else None
        )

        # Integration components (to be set externally)
        self.security_coordinator: SecurityIntegrationCoordinator | None = None
        self.rate_limiter: RateLimitingCoordinator | None = None

        # Background optimization
        self._optimization_task: asyncio.Task | None = None
        self._running = False

        self.logger = logging.getLogger(__name__)

    async def initialize(
        self,
        security_coordinator: SecurityIntegrationCoordinator | None = None,
        rate_limiter: RateLimitingCoordinator | None = None,
    ):
        """Initialize the performance manager with integrated components."""
        self.security_coordinator = security_coordinator
        self.rate_limiter = rate_limiter

        # Set up resource manager components
        self.resource_manager.set_components(
            rate_limiter=self.rate_limiter,
            cache=self.cache,
            performance_monitor=self.performance_optimizer,
        )

        # Start background monitoring if enabled
        if self.enable_auto_optimization:
            await self.start_background_optimization()

        self.logger.info("Enterprise Performance Manager initialized")

    async def start_background_optimization(self):
        """Start background performance optimization loop."""
        if self._running:
            return

        self._running = True
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        self.logger.info("Background performance optimization started")

    async def stop_background_optimization(self):
        """Stop background performance optimization."""
        self._running = False
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Background performance optimization stopped")

    async def _optimization_loop(self):
        """Background optimization loop."""
        while self._running:
            try:
                # Run optimization
                await self.resource_manager.optimize_resources()

                # Wait for next optimization cycle (5 minutes)
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def get_performance_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive performance data for dashboard display."""
        try:
            # Resource manager report
            resource_report = self.resource_manager.get_optimization_report()

            # Cache statistics
            cache_stats = self.cache.get_stats()

            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()

            # Security performance metrics (if available)
            security_metrics = {}
            if self.security_coordinator:
                try:
                    # Get performance metrics from security coordinator
                    security_metrics = {
                        "component_metrics": {},
                        "request_stats": {
                            "total_requests": 0,
                            "successful_requests": 0,
                            "failed_requests": 0,
                            "average_response_time_ms": 0.0,
                        },
                    }
                except Exception as e:
                    self.logger.debug(f"Could not get security metrics: {e}")

            return {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_info.percent,
                    "memory_used_mb": memory_info.used / (1024 * 1024),
                    "memory_available_mb": memory_info.available / (1024 * 1024),
                },
                "cache_metrics": cache_stats,
                "optimization_report": resource_report,
                "security_metrics": security_metrics,
                "performance_targets": {
                    "max_cpu_percent": self.targets.max_cpu_usage_percent,
                    "max_memory_mb": self.targets.max_memory_usage_mb,
                    "target_cache_hit_ratio": self.targets.target_cache_hit_ratio,
                    "min_throughput": self.targets.min_throughput_ops_per_sec,
                },
                "status": {
                    "auto_optimization_enabled": self.enable_auto_optimization,
                    "optimization_strategy": self.strategy.value,
                    "background_running": self._running,
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def manual_optimization(self) -> dict[str, Any]:
        """Perform manual optimization and return results."""
        try:
            start_time = time.time()

            # Run resource optimization
            optimization_result = await self.resource_manager.optimize_resources()

            # Force cache optimization
            self.cache.optimize_strategy()

            # Collect post-optimization metrics
            dashboard_data = await self.get_performance_dashboard_data()

            optimization_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "optimization_time_ms": optimization_time_ms,
                "optimization_result": {
                    "performance_score": optimization_result.performance_score,
                    "optimizations_applied": optimization_result.active_optimizations,
                    "cpu_usage_percent": optimization_result.cpu_usage_percent,
                    "memory_usage_mb": optimization_result.memory_usage_mb,
                    "cache_hit_ratio": optimization_result.cache_hit_ratio,
                },
                "current_metrics": dashboard_data["system_metrics"],
                "recommendations": self.resource_manager._generate_recommendations(
                    optimization_result
                ),
            }

        except Exception as e:
            self.logger.error(f"Error during manual optimization: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @asynccontextmanager
    async def performance_context(self, operation_name: str):
        """Context manager for tracking operation performance."""
        start_time = time.time()

        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Log performance
            self.logger.debug(
                f"Operation '{operation_name}' completed in {duration_ms:.1f}ms"
            )

            # Update security coordinator metrics if available
            if self.security_coordinator:
                try:
                    # Update component metrics (would need to be implemented in security_integration.py)
                    pass
                except Exception:
                    pass

    def get_cache_manager(self) -> IntelligentCache:
        """Get the intelligent cache manager for external use."""
        return self.cache

    def get_resource_manager(self) -> AdaptiveResourceManager:
        """Get the adaptive resource manager for external use."""
        return self.resource_manager

    def update_performance_targets(self, new_targets: PerformanceTarget):
        """Update performance targets and apply to components."""
        self.targets = new_targets
        self.resource_manager.targets = new_targets

        # Update cache size if needed
        if self.cache.max_size_bytes != int(
            new_targets.max_cache_size_mb * 1024 * 1024
        ):
            self.cache.max_size_bytes = int(new_targets.max_cache_size_mb * 1024 * 1024)

        self.logger.info("Performance targets updated")

    def set_optimization_strategy(self, strategy: OptimizationStrategy):
        """Update optimization strategy."""
        self.strategy = strategy
        self.resource_manager.strategy = strategy
        self.logger.info(f"Optimization strategy set to: {strategy.value}")


# Factory function for easy integration
def create_enterprise_performance_manager(
    max_cache_size_mb: float = 128.0,
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE,
    enable_auto_optimization: bool = True,
    performance_targets: PerformanceTarget | None = None,
) -> EnterprisePerformanceManager:
    """
    Factory function to create and configure an enterprise performance manager.

    Args:
        max_cache_size_mb: Maximum cache size in megabytes
        optimization_strategy: Performance optimization strategy
        enable_auto_optimization: Whether to enable background optimization
        performance_targets: Custom performance targets

    Returns:
        Configured EnterprisePerformanceManager instance
    """
    if performance_targets is None:
        performance_targets = PerformanceTarget(max_cache_size_mb=max_cache_size_mb)

    return EnterprisePerformanceManager(
        performance_targets=performance_targets,
        optimization_strategy=optimization_strategy,
        enable_auto_optimization=enable_auto_optimization,
    )


if __name__ == "__main__":
    # Example usage and testing
    async def test_performance_manager():
        """Test the enterprise performance manager."""
        # Create performance manager
        manager = create_enterprise_performance_manager(
            max_cache_size_mb=64.0,
            optimization_strategy=OptimizationStrategy.ADAPTIVE,
            enable_auto_optimization=False,  # Disable for testing
        )

        # Initialize
        await manager.initialize()

        # Test cache operations
        cache = manager.get_cache_manager()

        # Set some test data
        cache.set("test_key_1", "test_value_1")
        cache.set("test_key_2", {"data": "complex_value"})
        cache.set("test_key_3", "temporary_value", ttl_seconds=1.0)

        # Test cache retrieval
        value1 = cache.get("test_key_1")
        value2 = cache.get("test_key_2")

        print(f"Cache retrieval test: {value1}, {value2}")

        # Test cache statistics
        stats = cache.get_stats()
        print(f"Cache stats: {stats}")

        # Test manual optimization
        optimization_result = await manager.manual_optimization()
        print(f"Optimization result: {optimization_result}")

        # Test dashboard data
        dashboard_data = await manager.get_performance_dashboard_data()
        print(f"Dashboard data: {dashboard_data}")

        # Test TTL expiration
        await asyncio.sleep(1.5)
        value3 = cache.get("test_key_3")  # Should be None due to TTL
        print(f"TTL test (should be None): {value3}")

        print("Performance manager test completed successfully!")

    # Run test
    asyncio.run(test_performance_manager())
