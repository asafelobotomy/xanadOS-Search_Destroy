#!/usr/bin/env python3
"""Advanced Memory Management System for xanadOS Search & Destroy.

This module implements sophisticated memory management strategies including:
- Memory pooling for frequent allocations
- Intelligent caching with LRU and size-based eviction
- Lazy loading for resource optimization
- Memory pressure monitoring and adaptation
- Garbage collection optimization

Features:
- Pre-allocated memory pools for different object types
- Multi-level caching system with smart eviction
- Memory usage monitoring and alerting
- Automatic memory pressure adaptation
- Performance metrics and optimization hints
"""

import gc
import logging
import mmap
import os
import sys
import threading
import time
import weakref
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Type, TypeVar, Union

import psutil

from app.utils.config import get_config

T = TypeVar('T')


class MemoryPressureLevel(Enum):
    """Memory pressure levels for adaptive management."""

    LOW = 1      # < 50% memory usage
    MEDIUM = 2   # 50-70% memory usage
    HIGH = 3     # 70-85% memory usage
    CRITICAL = 4 # > 85% memory usage


@dataclass
class MemoryMetrics:
    """Memory usage and performance metrics."""

    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    memory_percent: float
    pool_allocations: int = 0
    pool_deallocations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    gc_collections: int = 0
    pressure_level: MemoryPressureLevel = MemoryPressureLevel.LOW
    timestamp: float = field(default_factory=time.time)


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


class MemoryPool:
    """Pre-allocated memory pool for specific object types."""

    def __init__(self, object_factory: Callable[[], T], initial_size: int = 100, max_size: int = 1000):
        self.object_factory = object_factory
        self.initial_size = initial_size
        self.max_size = max_size
        self.pool = []
        self.allocated = set()
        self.lock = threading.Lock()

        # Statistics
        self.total_allocations = 0
        self.total_deallocations = 0
        self.peak_usage = 0

        # Initialize pool
        self._initialize_pool()

        self.logger = logging.getLogger(__name__)

    def _initialize_pool(self):
        """Initialize the memory pool with pre-allocated objects."""
        for _ in range(self.initial_size):
            try:
                obj = self.object_factory()
                self.pool.append(obj)
            except Exception as e:
                self.logger.warning(f"Failed to pre-allocate object: {e}")
                break

    def acquire(self) -> Optional[T]:
        """Acquire an object from the pool."""
        with self.lock:
            self.total_allocations += 1

            # Try to get from pool
            if self.pool:
                obj = self.pool.pop()
                self.allocated.add(id(obj))
                self.peak_usage = max(self.peak_usage, len(self.allocated))
                return obj

            # Pool is empty, create new object if under limit
            if len(self.allocated) < self.max_size:
                try:
                    obj = self.object_factory()
                    self.allocated.add(id(obj))
                    self.peak_usage = max(self.peak_usage, len(self.allocated))
                    return obj
                except Exception as e:
                    self.logger.error(f"Failed to create object: {e}")
                    return None

            # Pool is at max capacity
            self.logger.warning(f"Memory pool at capacity: {self.max_size}")
            return None

    def release(self, obj: T) -> bool:
        """Release an object back to the pool."""
        with self.lock:
            obj_id = id(obj)
            if obj_id not in self.allocated:
                return False

            self.allocated.remove(obj_id)
            self.total_deallocations += 1

            # Reset object state if possible
            if hasattr(obj, 'reset'):
                try:
                    obj.reset()
                except Exception as e:
                    self.logger.warning(f"Failed to reset object: {e}")
                    return True  # Don't return to pool

            # Return to pool if not at capacity
            if len(self.pool) < self.initial_size:
                self.pool.append(obj)

            return True

    def get_stats(self) -> PoolStats:
        """Get pool statistics."""
        with self.lock:
            return PoolStats(
                pool_name=f"Pool_{self.object_factory.__name__}",
                object_type=str(self.object_factory),
                pool_size=len(self.pool),
                allocated_count=len(self.allocated),
                available_count=len(self.pool),
                total_allocations=self.total_allocations,
                total_deallocations=self.total_deallocations,
                peak_usage=self.peak_usage
            )

    def clear(self):
        """Clear the pool and release all objects."""
        with self.lock:
            self.pool.clear()
            self.allocated.clear()


class LRUCache:
    """Thread-safe LRU cache with size and memory limits."""

    def __init__(self, max_items: int = 1000, max_memory_mb: int = 100):
        self.max_items = max_items
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.memory_usage = 0
        self.lock = threading.Lock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            else:
                self.misses += 1
                return None

    def put(self, key: str, value: Any) -> bool:
        """Put value in cache."""
        with self.lock:
            # Calculate memory usage
            value_size = self._get_object_size(value)

            # Check if value is too large
            if value_size > self.max_memory_bytes:
                self.logger.warning(f"Object too large for cache: {value_size} bytes")
                return False

            # Remove existing key if present
            if key in self.cache:
                old_value = self.cache.pop(key)
                self.memory_usage -= self._get_object_size(old_value)

            # Evict items if necessary
            while (len(self.cache) >= self.max_items or
                   self.memory_usage + value_size > self.max_memory_bytes):
                if not self.cache:
                    break
                self._evict_lru()

            # Add new item
            self.cache[key] = value
            self.memory_usage += value_size
            return True

    def _evict_lru(self):
        """Evict least recently used item."""
        if self.cache:
            key, value = self.cache.popitem(last=False)
            self.memory_usage -= self._get_object_size(value)
            self.evictions += 1

    def _get_object_size(self, obj: Any) -> int:
        """Estimate object size in bytes."""
        try:
            return sys.getsizeof(obj)
        except Exception:
            return 1024  # Default estimate

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.memory_usage = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            hit_ratio = self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
            return {
                'size': len(self.cache),
                'max_items': self.max_items,
                'memory_usage_mb': self.memory_usage / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_ratio': hit_ratio
            }


class LazyLoader:
    """Lazy loading wrapper for resource-intensive objects."""

    def __init__(self, factory: Callable[[], T], *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs
        self._instance = None
        self._loaded = False
        self.lock = threading.Lock()

    def get(self) -> T:
        """Get the lazily loaded instance."""
        if not self._loaded:
            with self.lock:
                if not self._loaded:  # Double-check locking
                    self._instance = self.factory(*self.args, **self.kwargs)
                    self._loaded = True

        return self._instance

    def is_loaded(self) -> bool:
        """Check if the instance has been loaded."""
        return self._loaded

    def unload(self):
        """Unload the instance to free memory."""
        with self.lock:
            self._instance = None
            self._loaded = False


class MemoryMonitor:
    """Monitor system memory usage and pressure."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history = []
        self.max_history = 100
        self.monitoring = False
        self.callbacks = []

    def start_monitoring(self, interval: float = 5.0):
        """Start memory monitoring."""
        if self.monitoring:
            return

        self.monitoring = True

        def monitor_loop():
            while self.monitoring:
                try:
                    metrics = self._collect_metrics()
                    self.metrics_history.append(metrics)

                    # Keep history size limited
                    if len(self.metrics_history) > self.max_history:
                        self.metrics_history.pop(0)

                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(metrics)
                        except Exception as e:
                            self.logger.error(f"Memory monitor callback error: {e}")

                    time.sleep(interval)

                except Exception as e:
                    self.logger.error(f"Memory monitoring error: {e}")
                    time.sleep(interval * 2)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

        self.logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring = False
        self.logger.info("Memory monitoring stopped")

    def _collect_metrics(self) -> MemoryMetrics:
        """Collect current memory metrics."""
        memory = psutil.virtual_memory()

        # Determine pressure level
        if memory.percent < 50:
            pressure = MemoryPressureLevel.LOW
        elif memory.percent < 70:
            pressure = MemoryPressureLevel.MEDIUM
        elif memory.percent < 85:
            pressure = MemoryPressureLevel.HIGH
        else:
            pressure = MemoryPressureLevel.CRITICAL

        return MemoryMetrics(
            total_memory_mb=memory.total / (1024 * 1024),
            used_memory_mb=memory.used / (1024 * 1024),
            available_memory_mb=memory.available / (1024 * 1024),
            memory_percent=memory.percent,
            pressure_level=pressure,
            gc_collections=sum(gc.get_stats())
        )

    def add_pressure_callback(self, callback: Callable[[MemoryMetrics], None]):
        """Add callback for memory pressure notifications."""
        self.callbacks.append(callback)

    def get_current_metrics(self) -> Optional[MemoryMetrics]:
        """Get the most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_pressure_level(self) -> MemoryPressureLevel:
        """Get current memory pressure level."""
        metrics = self.get_current_metrics()
        return metrics.pressure_level if metrics else MemoryPressureLevel.LOW


class AdvancedMemoryManager:
    """Advanced memory management system coordinator."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()

        # Core components
        self.monitor = MemoryMonitor()
        self.pools = {}
        self.caches = {}
        self.lazy_loaders = weakref.WeakValueDictionary()

        # Configuration
        self.gc_threshold_adjustments = True
        self.auto_pressure_response = True

        # Setup pressure response
        self.monitor.add_pressure_callback(self._handle_memory_pressure)

        # Initialize default caches
        self._initialize_default_caches()

    def start(self):
        """Start the memory management system."""
        self.monitor.start_monitoring()

        if self.gc_threshold_adjustments:
            self._optimize_gc_thresholds()

        self.logger.info("Advanced memory manager started")

    def stop(self):
        """Stop the memory management system."""
        self.monitor.stop_monitoring()
        self._cleanup_all()
        self.logger.info("Advanced memory manager stopped")

    def _initialize_default_caches(self):
        """Initialize default caches for common use cases."""
        self.caches['scan_results'] = LRUCache(max_items=500, max_memory_mb=50)
        self.caches['file_metadata'] = LRUCache(max_items=1000, max_memory_mb=25)
        self.caches['threat_analysis'] = LRUCache(max_items=200, max_memory_mb=30)
        self.caches['process_info'] = LRUCache(max_items=300, max_memory_mb=20)

    def create_pool(self, name: str, object_factory: Callable[[], T],
                   initial_size: int = 100, max_size: int = 1000) -> MemoryPool:
        """Create a new memory pool."""
        if name in self.pools:
            self.logger.warning(f"Pool {name} already exists")
            return self.pools[name]

        pool = MemoryPool(object_factory, initial_size, max_size)
        self.pools[name] = pool

        self.logger.info(f"Created memory pool: {name}")
        return pool

    def get_pool(self, name: str) -> Optional[MemoryPool]:
        """Get an existing memory pool."""
        return self.pools.get(name)

    def create_cache(self, name: str, max_items: int = 1000,
                    max_memory_mb: int = 100) -> LRUCache:
        """Create a new cache."""
        if name in self.caches:
            self.logger.warning(f"Cache {name} already exists")
            return self.caches[name]

        cache = LRUCache(max_items, max_memory_mb)
        self.caches[name] = cache

        self.logger.info(f"Created cache: {name}")
        return cache

    def get_cache(self, name: str) -> Optional[LRUCache]:
        """Get an existing cache."""
        return self.caches.get(name)

    def create_lazy_loader(self, name: str, factory: Callable[[], T],
                          *args, **kwargs) -> LazyLoader:
        """Create a lazy loader."""
        loader = LazyLoader(factory, *args, **kwargs)
        self.lazy_loaders[name] = loader

        self.logger.debug(f"Created lazy loader: {name}")
        return loader

    def get_lazy_loader(self, name: str) -> Optional[LazyLoader]:
        """Get an existing lazy loader."""
        return self.lazy_loaders.get(name)

    @contextmanager
    def memory_efficient_context(self, aggressive: bool = False) -> Generator[None, None, None]:
        """Context manager for memory-efficient operations."""
        # Pre-context setup
        original_threshold = None
        if aggressive:
            original_threshold = gc.get_threshold()
            gc.set_threshold(100, 10, 10)  # More aggressive GC

        try:
            yield
        finally:
            # Post-context cleanup
            if aggressive:
                gc.collect()  # Force collection
                if original_threshold:
                    gc.set_threshold(*original_threshold)

    def _handle_memory_pressure(self, metrics: MemoryMetrics):
        """Handle memory pressure events."""
        if not self.auto_pressure_response:
            return

        if metrics.pressure_level == MemoryPressureLevel.HIGH:
            self._moderate_pressure_response()
        elif metrics.pressure_level == MemoryPressureLevel.CRITICAL:
            self._critical_pressure_response()

    def _moderate_pressure_response(self):
        """Handle moderate memory pressure."""
        self.logger.info("Moderate memory pressure detected - initiating cleanup")

        # Clear least important caches partially
        for name, cache in self.caches.items():
            if name in ['file_metadata', 'process_info']:
                # Clear 25% of cache
                stats = cache.get_stats()
                items_to_clear = max(1, stats['size'] // 4)
                for _ in range(items_to_clear):
                    cache._evict_lru()

        # Force garbage collection
        gc.collect()

    def _critical_pressure_response(self):
        """Handle critical memory pressure."""
        self.logger.warning("Critical memory pressure detected - aggressive cleanup")

        # Clear all non-essential caches
        for name, cache in self.caches.items():
            if name != 'threat_analysis':  # Keep threat analysis cache
                cache.clear()

        # Unload lazy loaders
        for loader in self.lazy_loaders.values():
            if loader.is_loaded():
                loader.unload()

        # Force aggressive garbage collection
        gc.collect()
        gc.collect()  # Second pass for circular references

    def _optimize_gc_thresholds(self):
        """Optimize garbage collection thresholds based on system memory."""
        memory = psutil.virtual_memory()

        if memory.total > 8 * 1024 * 1024 * 1024:  # > 8GB
            # High memory system - less aggressive GC
            gc.set_threshold(1000, 15, 15)
        elif memory.total > 4 * 1024 * 1024 * 1024:  # > 4GB
            # Medium memory system - default GC
            gc.set_threshold(700, 10, 10)
        else:
            # Low memory system - more aggressive GC
            gc.set_threshold(400, 5, 5)

        self.logger.info(f"Optimized GC thresholds for {memory.total / (1024**3):.1f}GB system")

    def _cleanup_all(self):
        """Clean up all memory management resources."""
        # Clear all caches
        for cache in self.caches.values():
            cache.clear()

        # Clear all pools
        for pool in self.pools.values():
            pool.clear()

        # Force garbage collection
        gc.collect()

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory management statistics."""
        current_metrics = self.monitor.get_current_metrics()

        return {
            'system_memory': asdict(current_metrics) if current_metrics else {},
            'pools': {name: pool.get_stats() for name, pool in self.pools.items()},
            'caches': {name: cache.get_stats() for name, cache in self.caches.items()},
            'lazy_loaders': {
                name: {'loaded': loader.is_loaded()}
                for name, loader in self.lazy_loaders.items()
            },
            'gc_stats': {
                'counts': gc.get_count(),
                'threshold': gc.get_threshold(),
                'stats': gc.get_stats()
            }
        }

    def force_cleanup(self, aggressive: bool = False):
        """Force memory cleanup."""
        if aggressive:
            self._critical_pressure_response()
        else:
            self._moderate_pressure_response()


# Global memory manager instance
_memory_manager_instance = None


def get_memory_manager() -> AdvancedMemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = AdvancedMemoryManager()
    return _memory_manager_instance


# Convenience functions
def get_pool(name: str) -> Optional[MemoryPool]:
    """Get a memory pool by name."""
    return get_memory_manager().get_pool(name)


def get_cache(name: str) -> Optional[LRUCache]:
    """Get a cache by name."""
    return get_memory_manager().get_cache(name)


def memory_efficient(aggressive: bool = False):
    """Decorator for memory-efficient functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with get_memory_manager().memory_efficient_context(aggressive):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for common memory operations
def asdict(obj) -> Dict[str, Any]:
    """Convert dataclass to dictionary with error handling."""
    try:
        from dataclasses import asdict as dc_asdict
        return dc_asdict(obj)
    except Exception:
        return {'error': 'Could not serialize object'}
