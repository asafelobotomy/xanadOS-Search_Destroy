#!/usr/bin/env python3
"""Unified Memory Management System for xanadOS Search & Destroy

This consolidated module combines all memory management functionality:
- Advanced memory pooling and allocation strategies
- Intelligent caching with TTL and LRU eviction
- Memory pressure monitoring and adaptive optimization
- Stream processing for large files
- Garbage collection optimization
- Performance metrics and monitoring

Consolidates:
- memory_manager.py (650 lines)
- memory_optimizer.py (342 lines)
- memory_cache.py (249 lines)
- memory components from unified_performance_optimizer.py

Risk Mitigation: Backward compatibility maintained through import shims.
"""

import gc
import logging
import mmap
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

import psutil

try:
    from PyQt6.QtCore import QTimer

    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

from app.utils.config import get_config

T = TypeVar("T")

# ============================================================================
# Core Data Structures and Enums
# ============================================================================


class MemoryPressureLevel(Enum):
    """Memory pressure levels for adaptive management."""

    LOW = 1  # < 50% memory usage
    MEDIUM = 2  # 50-70% memory usage
    HIGH = 3  # 70-85% memory usage
    CRITICAL = 4  # > 85% memory usage


@dataclass
class MemoryMetrics:
    """Comprehensive memory usage and performance metrics."""

    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    memory_percent: float
    process_mb: float = 0.0
    cache_mb: float = 0.0
    pool_allocations: int = 0
    pool_deallocations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    gc_collections: int = 0
    pressure_level: MemoryPressureLevel = MemoryPressureLevel.LOW
    timestamp: float = field(default_factory=time.time)


@dataclass
class CacheEntry:
    """Cache entry with metadata and TTL support."""

    value: Any
    timestamp: float
    ttl: float  # Time to live in seconds
    access_count: int = 0
    last_access: float = 0.0

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() - self.timestamp > self.ttl

    def is_stale(self, stale_threshold: float = 0.8) -> bool:
        """Check if entry is getting stale (80% of TTL by default)."""
        elapsed = time.time() - self.timestamp
        return elapsed > (self.ttl * stale_threshold)

    def access(self) -> None:
        """Mark this entry as accessed."""
        self.access_count += 1
        self.last_access = time.time()


@dataclass
class PoolStats:
    """Memory pool statistics."""

    pool_name: str
    object_type: str
    pool_size: int
    allocated_count: int
    available_count: int
    total_allocations: int
    total_deallocations: int
    peak_usage: int
    creation_time: float = field(default_factory=time.time)


# ============================================================================
# Memory Pool Implementation
# ============================================================================


class UnifiedMemoryPool:
    """Advanced memory pool with statistics and adaptive sizing."""

    def __init__(
        self,
        object_factory: Callable[[], T],
        initial_size: int = 100,
        max_size: int = 1000,
        name: str = "default",
    ):
        self.object_factory = object_factory
        self.initial_size = initial_size
        self.max_size = max_size
        self.name = name
        self.pool: list[T] = []
        self.allocated: set[int] = set()
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.total_allocations = 0
        self.total_deallocations = 0
        self.peak_usage = 0
        self.creation_time = time.time()

        # Initialize pool
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the pool with initial objects."""
        try:
            for _ in range(self.initial_size):
                obj = self.object_factory()
                self.pool.append(obj)
        except Exception as e:
            self.logger.error("Failed to initialize memory pool %s: %s", self.name, e)

    def get_object(self) -> T:
        """Get an object from the pool or create a new one."""
        with self.lock:
            if self.pool:
                obj = self.pool.pop()
                self.allocated.add(id(obj))
                self.total_allocations += 1
                self.peak_usage = max(self.peak_usage, len(self.allocated))
                return obj

        # Create new object outside lock
        obj = self.object_factory()
        with self.lock:
            self.allocated.add(id(obj))
            self.total_allocations += 1
            self.peak_usage = max(self.peak_usage, len(self.allocated))
        return obj

    def return_object(self, obj: T) -> None:
        """Return an object to the pool."""
        obj_id = id(obj)
        with self.lock:
            if obj_id not in self.allocated:
                return  # Object not from this pool

            self.allocated.discard(obj_id)
            self.total_deallocations += 1

            if len(self.pool) < self.max_size:
                # Reset object state if possible
                reset_method = getattr(obj, "reset", None)
                if callable(reset_method):
                    try:
                        reset_method()
                    except Exception:
                        self.logger.debug("Object reset failed for pool %s", self.name)
                        return  # Don't return broken objects

                self.pool.append(obj)

    def get_stats(self) -> PoolStats:
        """Get pool statistics."""
        with self.lock:
            return PoolStats(
                pool_name=self.name,
                object_type=(
                    self.object_factory.__name__
                    if hasattr(self.object_factory, "__name__")
                    else str(type(self.object_factory))
                ),
                pool_size=len(self.pool),
                allocated_count=len(self.allocated),
                available_count=len(self.pool),
                total_allocations=self.total_allocations,
                total_deallocations=self.total_deallocations,
                peak_usage=self.peak_usage,
                creation_time=self.creation_time,
            )


# ============================================================================
# Intelligent Cache Implementation
# ============================================================================


class IntelligentCache:
    """Advanced cache with TTL, LRU eviction, and intelligent features."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "refreshes": 0,
            "expired_cleanups": 0,
        }

        # Background cleanup
        self._cleanup_thread: threading.Thread | None = None
        self._stop_cleanup = threading.Event()
        self._start_background_cleanup()

    def _start_background_cleanup(self):
        """Start background cleanup thread."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._background_cleanup,
                daemon=True,
                name=f"CacheCleanup-{id(self)}",
            )
            self._cleanup_thread.start()

    def _background_cleanup(self):
        """Background thread for cleaning expired entries."""
        while not self._stop_cleanup.wait(60):  # Cleanup every 60 seconds
            try:
                self._cleanup_expired()
            except Exception as e:
                self.logger.error("Cache cleanup error: %s", e)

    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._access_order.pop(key, None)
                self._stats["expired_cleanups"] += 1

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with LRU tracking."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return default

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._access_order.pop(key, None)
                self._stats["misses"] += 1
                self._stats["expired_cleanups"] += 1
                return default

            # Update access tracking
            entry.access()
            self._access_order.move_to_end(key)
            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Set value in cache with automatic eviction."""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl

            # Evict if at capacity and key is new
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            # Create/update entry
            self._cache[key] = CacheEntry(
                value=value, timestamp=time.time(), ttl=ttl, last_access=time.time()
            )
            self._access_order[key] = None
            self._access_order.move_to_end(key)

    def _evict_lru(self):
        """Evict least recently used item."""
        if self._access_order:
            lru_key = next(iter(self._access_order))
            del self._cache[lru_key]
            del self._access_order[lru_key]
            self._stats["evictions"] += 1

    def get_or_set(
        self, key: str, factory: Callable[[], Any], ttl: float | None = None
    ) -> Any:
        """Get value or set it using factory function."""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
            self._stats["refreshes"] += 1
        return value

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_ratio": (
                    self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                    if (self._stats["hits"] + self._stats["misses"]) > 0
                    else 0.0
                ),
            }

    def shutdown(self):
        """Shutdown background cleanup."""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)


# ============================================================================
# Stream Processing for Large Files
# ============================================================================


class StreamProcessor:
    """Memory-efficient stream processor for large files."""

    def __init__(self, chunk_size: int = 64 * 1024):  # 64KB chunks
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

    def process_file_stream(
        self, file_path: str, processor_func: Callable[[bytes], None]
    ):
        """Process file in chunks without loading entire file."""
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    processor_func(chunk)
        except Exception as e:
            self.logger.error("Error processing file stream %s: %s", file_path, e)

    def process_memory_mapped(
        self, file_path: str, processor_func: Callable[[memoryview], None]
    ):
        """Process file using memory mapping for very large files."""
        try:
            with open(file_path, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    # Process in chunks
                    for i in range(0, len(mmapped_file), self.chunk_size):
                        chunk = mmapped_file[i : i + self.chunk_size]
                        processor_func(chunk)
        except Exception as e:
            self.logger.error(
                "Error processing memory-mapped file %s: %s", file_path, e
            )


# ============================================================================
# Unified Memory Manager - Main Class
# ============================================================================


class UnifiedMemoryManager:
    """Unified memory management system combining all memory functionality."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process()

        # Component initialization
        self.pools: dict[str, UnifiedMemoryPool] = {}
        self.cache = IntelligentCache()
        self.stream_processor = StreamProcessor()

        # Memory monitoring
        self._monitoring_enabled = True
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()

        # Performance tracking
        self.start_memory = self._get_memory_usage()
        self.peak_memory = self.start_memory

        # GC optimization
        self._gc_threshold_adjustments = 0

        self.logger.info("Unified Memory Manager initialized")
        self._start_monitoring()

    def _start_monitoring(self):
        """Start background memory monitoring."""
        if self._monitoring_enabled and (
            self._monitor_thread is None or not self._monitor_thread.is_alive()
        ):
            self._monitor_thread = threading.Thread(
                target=self._memory_monitor_loop, daemon=True, name="MemoryMonitor"
            )
            self._monitor_thread.start()

    def _memory_monitor_loop(self):
        """Background memory monitoring loop."""
        while not self._stop_monitoring.wait(30):  # Check every 30 seconds
            try:
                metrics = self.get_memory_metrics()

                # Auto-optimize based on pressure
                if metrics.pressure_level == MemoryPressureLevel.HIGH:
                    self.optimize_memory(aggressive=False)
                elif metrics.pressure_level == MemoryPressureLevel.CRITICAL:
                    self.optimize_memory(aggressive=True)

            except Exception as e:
                self.logger.error("Memory monitoring error: %s", e)

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def get_memory_metrics(self) -> MemoryMetrics:
        """Get comprehensive memory metrics."""
        # System memory
        memory = psutil.virtual_memory()

        # Process memory
        process_mb = self._get_memory_usage()

        # Update peak
        self.peak_memory = max(self.peak_memory, process_mb)

        # Cache stats
        cache_stats = self.cache.get_stats()

        # Pool stats
        total_pool_allocations = sum(
            pool.total_allocations for pool in self.pools.values()
        )
        total_pool_deallocations = sum(
            pool.total_deallocations for pool in self.pools.values()
        )

        # Determine pressure level
        pressure_level = MemoryPressureLevel.LOW
        if memory.percent > 85:
            pressure_level = MemoryPressureLevel.CRITICAL
        elif memory.percent > 70:
            pressure_level = MemoryPressureLevel.HIGH
        elif memory.percent > 50:
            pressure_level = MemoryPressureLevel.MEDIUM

        return MemoryMetrics(
            total_memory_mb=memory.total / 1024 / 1024,
            used_memory_mb=memory.used / 1024 / 1024,
            available_memory_mb=memory.available / 1024 / 1024,
            memory_percent=memory.percent,
            process_mb=process_mb,
            pool_allocations=total_pool_allocations,
            pool_deallocations=total_pool_deallocations,
            cache_hits=cache_stats["hits"],
            cache_misses=cache_stats["misses"],
            cache_evictions=cache_stats["evictions"],
            gc_collections=gc.get_count()[0],
            pressure_level=pressure_level,
        )

    def create_pool(
        self,
        name: str,
        object_factory: Callable[[], T],
        initial_size: int = 100,
        max_size: int = 1000,
    ) -> UnifiedMemoryPool:
        """Create a new memory pool."""
        pool = UnifiedMemoryPool(object_factory, initial_size, max_size, name)
        self.pools[name] = pool
        self.logger.info(
            "Created memory pool '%s' with initial_size=%d, max_size=%d",
            name,
            initial_size,
            max_size,
        )
        return pool

    def get_pool(self, name: str) -> UnifiedMemoryPool | None:
        """Get existing memory pool by name."""
        return self.pools.get(name)

    def optimize_memory(self, aggressive: bool = False) -> dict[str, Any]:
        """Perform memory optimization."""
        start_memory = self._get_memory_usage()
        operations = []

        try:
            # 1. Cache cleanup
            self.cache._cleanup_expired()
            operations.append("Cache cleanup")

            # 2. Garbage collection
            if aggressive:
                # Full GC cycle
                gc.collect()
                gc.collect()
                gc.collect()
                operations.append("Aggressive GC")
            else:
                gc.collect()
                operations.append("Standard GC")

            # 3. Pool optimization
            for pool in self.pools.values():
                # Could implement pool shrinking here
                pass

            # 4. System-level optimization (if aggressive)
            if aggressive:
                try:
                    # Adjust GC thresholds for better performance
                    current_thresholds = gc.get_threshold()
                    if self._gc_threshold_adjustments < 3:  # Limit adjustments
                        gc.set_threshold(
                            current_thresholds[0] * 2,
                            current_thresholds[1] * 2,
                            current_thresholds[2] * 2,
                        )
                        self._gc_threshold_adjustments += 1
                        operations.append("GC threshold adjustment")
                except Exception:
                    pass

            end_memory = self._get_memory_usage()
            memory_freed = start_memory - end_memory

            result = {
                "success": True,
                "memory_freed_mb": memory_freed,
                "operations": operations,
                "start_memory_mb": start_memory,
                "end_memory_mb": end_memory,
            }

            self.logger.info(
                "Memory optimization completed: freed %.2f MB", memory_freed
            )
            return result

        except Exception as e:
            self.logger.error("Memory optimization failed: %s", e)
            return {"success": False, "error": str(e), "operations": operations}

    def check_memory_pressure(self, max_memory_mb: float = 256) -> bool:
        """Check if memory usage is approaching limits."""
        current_memory = self._get_memory_usage()
        return current_memory > max_memory_mb

    def force_garbage_collection(self):
        """Force garbage collection to free memory."""
        gc.collect()

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive memory management statistics."""
        metrics = self.get_memory_metrics()

        return {
            "memory_metrics": metrics,
            "cache_stats": self.cache.get_stats(),
            "pool_stats": {name: pool.get_stats() for name, pool in self.pools.items()},
            "start_memory_mb": self.start_memory,
            "peak_memory_mb": self.peak_memory,
            "gc_threshold_adjustments": self._gc_threshold_adjustments,
        }

    def shutdown(self):
        """Shutdown memory manager and cleanup resources."""
        self.logger.info("Shutting down Unified Memory Manager")

        # Stop monitoring
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        # Shutdown cache
        self.cache.shutdown()

        # Clear pools
        self.pools.clear()

        self.logger.info("Unified Memory Manager shutdown complete")


# ============================================================================
# Module-level instances and backward compatibility
# ============================================================================

# Global instance
_unified_memory_manager = None
_manager_lock = threading.Lock()


def get_memory_manager() -> UnifiedMemoryManager:
    """Get the global unified memory manager instance."""
    global _unified_memory_manager
    with _manager_lock:
        if _unified_memory_manager is None:
            _unified_memory_manager = UnifiedMemoryManager()
        return _unified_memory_manager


# Backward compatibility aliases
MemoryStats = MemoryMetrics  # Alias for compatibility
MemoryPool = UnifiedMemoryPool  # Alias for compatibility
ModernMemoryCache = IntelligentCache  # Alias for compatibility

# For memory_optimizer.py compatibility
memory_optimizer = get_memory_manager()
cache_manager = get_memory_manager().cache


# For memory_cache.py compatibility
def get_system_cache() -> IntelligentCache:
    """Get system cache for backward compatibility."""
    return get_memory_manager().cache


# ============================================================================
# System Status Cache (specialized cache)
# ============================================================================


class SystemStatusCache(IntelligentCache):
    """Specialized cache for system status information."""

    def __init__(self):
        super().__init__(max_size=500, default_ttl=30)  # 30 second TTL for system info

    def cache_system_info(
        self, key: str, info_func: Callable[[], Any], ttl: float = 30
    ) -> Any:
        """Cache system information with automatic refresh."""
        return self.get_or_set(key, info_func, ttl)


# Initialize module
logger = logging.getLogger(__name__)
logger.info("Unified Memory Management module initialized")


# ============================================================================
# Decorator for Memory Efficient Functions
# ============================================================================


def memory_efficient(func: Callable) -> Callable:
    """Decorator to ensure memory-efficient execution of functions.

    This decorator:
    - Monitors memory usage before and after function execution
    - Triggers garbage collection if memory pressure is detected
    - Logs memory statistics for performance monitoring
    """
    def wrapper(*args, **kwargs):
        # Get memory before
        manager = get_memory_manager()
        before_metrics = manager.get_memory_metrics()

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Check memory after
            after_metrics = manager.get_memory_metrics()

            # If memory increased significantly, trigger GC
            memory_increase = after_metrics.used_memory_mb - before_metrics.used_memory_mb
            if memory_increase > 100:  # More than 100MB increase
                logger.debug(
                    f"Function {func.__name__} increased memory by {memory_increase:.1f}MB, "
                    "triggering garbage collection"
                )
                gc.collect()

            return result

        except Exception as e:
            # Clean up on error
            gc.collect()
            raise e

    return wrapper
