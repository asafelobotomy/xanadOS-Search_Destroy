#!/usr/bin/env python3
"""
Memory optimization module for xanadOS Search & Destroy
Provides efficient memory management and resource optimization
"""

import gc
import logging
import sys
import threading
import time
import weakref
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import psutil


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    total_mb: float
    available_mb: float
    used_mb: float
    used_percent: float
    process_mb: float
    cache_mb: float


class MemoryPool:
    """Memory pool for efficient object reuse.

    Reduces garbage collection overhead for frequently created objects by
    reusing objects instead of creating/destroying them repeatedly.
    """

    def __init__(self, object_factory: Callable[[], object], max_size: int = 100):
        """Initialize memory pool.

        Args:
            object_factory: Zero-arg callable that creates a new object instance
            max_size: Maximum number of idle objects to retain
        """
        self.object_factory = object_factory
        self.max_size = max_size
        self.pool: List[object] = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def get_object(self) -> object:
        """Get an object from the pool or create a new one if empty."""
        with self.lock:
            if self.pool:
                return self.pool.pop()
        # Fallthrough outside lock (object_factory may be expensive)
        return self.object_factory()

    def return_object(self, obj: object) -> None:
        """Return an object to the pool if capacity allows."""
        with self.lock:
            if len(self.pool) < self.max_size:
                # Reset object state if it has a reset method
                reset = getattr(obj, "reset", None)
                if callable(reset):
                    try:
                        reset()
                    except Exception:  # Best effort; don't block returning
                        self.logger.debug("Object reset() failed", exc_info=True)
                self.pool.append(obj)


class StreamProcessor:
    """
    Stream processor for handling large files without loading entire content into memory.
    """

    def __init__(self, chunk_size: int = 64 * 1024):  # 64KB chunks
        """
        Initialize stream processor.

        Args:
            chunk_size: Size of chunks to process at a time
        """
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

    def process_file_stream(
        self, file_path: str, processor_func: Callable[[bytes], None]
    ):
        """
        Process file in chunks without loading entire file.

        Args:
            file_path: Path to file to process
            processor_func: Function to process each chunk
        """
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    processor_func(chunk)
        except Exception as e:
            # Use parameterized logging; include file path and exception
            self.logger.error("Error processing file stream %s: %s", file_path, e)
            raise


class MemoryOptimizer:
    """Monitors process/system memory and applies optimization strategies."""

    def __init__(self, memory_limit_mb: int = 512, gc_threshold: float = 0.8) -> None:
        self.memory_limit_mb = memory_limit_mb
        self.gc_threshold = gc_threshold
        self.logger = logging.getLogger(__name__)
        # Monitoring
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_interval = 5.0
        # Callbacks
        self.memory_warning_callback: Optional[Callable[[MemoryStats], None]] = None
        self.memory_critical_callback: Optional[Callable[[MemoryStats], None]] = None
        # Pools / caches
        self.pools: Dict[str, MemoryPool] = {}
        self.cache_refs: "weakref.WeakSet[object]" = weakref.WeakSet()

    def get_memory_stats(self) -> MemoryStats:
        try:
            system_memory = psutil.virtual_memory()
            if hasattr(system_memory, "total") and isinstance(system_memory.total, int):
                total_mb = system_memory.total / 1024 / 1024
                available_mb = system_memory.available / 1024 / 1024
                used_mb = system_memory.used / 1024 / 1024
                used_percent = system_memory.percent
            else:
                total_mb = 8192.0
                available_mb = 4096.0
                used_mb = 4096.0
                used_percent = 50.0
            try:
                process_memory = psutil.Process().memory_info()
                if hasattr(process_memory, "rss") and isinstance(
                    process_memory.rss, int
                ):
                    process_mb = process_memory.rss / 1024 / 1024
                else:
                    process_mb = 100.0
            except (AttributeError, TypeError):
                process_mb = 100.0
            cache_mb = 0.0
            if hasattr(system_memory, "cached"):
                cached = getattr(system_memory, "cached", 0)
                if isinstance(cached, int):
                    cache_mb = cached / 1024 / 1024
            return MemoryStats(
                total_mb, available_mb, used_mb, used_percent, process_mb, cache_mb
            )
        except Exception:  # pragma: no cover
            self.logerror(
                "Failed to get memory stats: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return MemoryStats(0, 0, 0, 0, 0, 0)

    def check_memory_pressure(self) -> bool:
        stats = self.get_memory_stats()
        if stats.process_mb > self.memory_limit_mb:
            self.logger.warning(
                "Process memory %.1f MB exceeds limit %d MB",
                stats.process_mb,
                self.memory_limit_mb,
            )
            return True
        if stats.used_percent > 90:
            self.logwarning(
                "System memory usage %.1f%% is critically high".replace(
                    "%s", "{stats.used_percent}"
                ).replace("%d", "{stats.used_percent}")
            )
            return True
        return False

    def optimize_memory(self, aggressive: bool = False) -> None:
        # Log action with proper parameterization
        self.logger.info("Performing memory optimization (aggressive=%s)", aggressive)
        collected = gc.collect()
        self.logger.debug("Garbage collected %d objects", collected)
        if aggressive:
            gc.collect(0)
            gc.collect(1)
            gc.collect(2)
            self._clear_caches()
            self._clear_pools()

    def _clear_caches(self) -> None:
        cleared = 0
        for cache_ref in list(self.cache_refs):
            try:
                if hasattr(cache_ref, "clear"):
                    cache_ref.clear()
                    cleared += 1
            except Exception:
                self.logger.debug("Error clearing cache", exc_info=True)
        self.logger.debug("Cleared %d caches", cleared)

    def _clear_pools(self) -> None:
        for name, pool in self.pools.items():
            with pool.lock:
                cleared = len(pool.pool)
                pool.pool.clear()
                self.logger.debug("Cleared pool '%s': %d objects", name, cleared)

    def register_cache(self, cache_obj: object) -> None:
        self.cache_refs.add(cache_obj)

    def register_pool(self, name: str, pool: MemoryPool) -> None:
        self.pools[name] = pool

    def _monitor_memory(self) -> None:
        while self.monitoring:
            try:
                stats = self.get_memory_stats()
                if stats.used_percent > 80 and self.memory_warning_callback:
                    self.memory_warning_callback(stats)
                if self.check_memory_pressure():
                    if self.memory_critical_callback:
                        self.memory_critical_callback(stats)
                    self.optimize_memory(aggressive=True)
                elif stats.process_mb > self.memory_limit_mb * self.gc_threshold:
                    self.optimize_memory(aggressive=False)
                time.sleep(self.monitor_interval)
            except Exception:
                self.logger.error("Memory monitoring error", exc_info=True)
                time.sleep(self.monitor_interval)

    def start_monitoring(self) -> None:
        if self.monitoring:
            return
        self.logger.info("Starting memory monitoring")
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self) -> None:
        if not self.monitoring:
            return
        self.logger.info("Stopping memory monitoring")
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

    def set_memory_warning_callback(
        self, callback: Callable[[MemoryStats], None]
    ) -> None:
        self.memory_warning_callback = callback

    def set_memory_critical_callback(
        self, callback: Callable[[MemoryStats], None]
    ) -> None:
        self.memory_critical_callback = callback


class CacheManager:
    """
    Intelligent cache manager with automatic eviction and memory awareness.
    """

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of cache entries
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.cache: Dict = {}
        self.access_times: Dict = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Memory tracking
        self.estimated_memory_mb = 0.0

    def get(self, key, default=None):
        """Get item from cache."""
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                return self.cache[key]
            return default

    def set(self, key, value):
        """Set item in cache with automatic eviction."""
        with self.lock:
            # Estimate memory usage

            item_size_mb = sys.getsizeof(value) / 1024 / 1024

            # Check if we need to evict
            if (
                len(self.cache) >= self.max_size
                or self.estimated_memory_mb + item_size_mb > self.max_memory_mb
            ):
                self._evict_lru()

            self.cache[key] = value
            self.access_times[key] = time.time()
            self.estimated_memory_mb += item_size_mb

    def _evict_lru(self):
        """Evict least recently used items."""
        if not self.cache:
            return

        # Sort by access time and remove oldest
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])
        evict_count = max(1, len(self.cache) // 4)  # Evict 25%

        for key, _ in sorted_items[:evict_count]:
            if key in self.cache:
                value = self.cache.pop(key)
                self.access_times.pop(key, None)

                # Update memory estimate

                item_size_mb = sys.getsizeof(value) / 1024 / 1024
                self.estimated_memory_mb = max(
                    0, self.estimated_memory_mb - item_size_mb
                )

        self.logdebug(
            "Evicted %d cache entries".replace("%s", "{evict_count}").replace(
                "%d", "{evict_count}"
            )
        )

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.estimated_memory_mb = 0.0

    def get_stats(self) -> Dict[str, float]:
        """Get cache statistics."""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "memory_mb": self.estimated_memory_mb,
                "max_memory_mb": self.max_memory_mb,
                "hit_ratio": getattr(self, "_hit_ratio", 0.0),
            }


# Global memory optimizer instance
memory_optimizer = MemoryOptimizer()

# Global cache manager instance
cache_manager = CacheManager()
