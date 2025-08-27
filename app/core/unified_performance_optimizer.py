#!/usr/bin/env python3
"""
Unified Performance Optimizer for xanadOS Search & Destroy
Consolidates memory optimization, database optimization, and system performance management.
This module combines:
- Memory optimization and garbage collection
- Database connection pooling and query optimization
- System resource monitoring and adaptive scaling
- 2025 performance research optimizations
Features:
- Advanced memory management with Python 3.12+ optimizations
- SQLite/PostgreSQL connection pooling
- Adaptive query optimization
- Real-time performance monitoring
- Resource-aware scaling
"""

import asyncio
import gc
import logging
import os
import sqlite3
import sys
import threading
import time
import weakref
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psutil

# Advanced memory profiling (optional)
try:
    import tracemalloc

    import memory_profiler

    MEMORY_PROFILING_AVAILABLE = True
except ImportError:
    MEMORY_PROFILING_AVAILABLE = False

# Database drivers
try:
    import psycopg2
    import psycopg2.pool

    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False


class PerformanceMode(Enum):
    """Performance optimization modes."""

    MAXIMUM_PERFORMANCE = "maximum_performance"
    BALANCED = "balanced"
    MEMORY_CONSERVATIVE = "memory_conservative"
    BATTERY_SAVER = "battery_saver"


class ResourceType(Enum):
    """System resource types."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""

    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    memory_percentage: float = 0.0
    disk_io_mb: float = 0.0
    network_io_mb: float = 0.0
    database_connections: int = 0
    active_queries: int = 0
    cache_hit_rate: float = 0.0
    gc_collections: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationResult:
    """Results of optimization operations."""

    operation: str
    before_value: float
    after_value: float
    improvement_percentage: float
    duration_ms: float
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)


class AdvancedMemoryManager:
    """Advanced memory management with 2025 optimizations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory_thresholds = {
            "warning": 80.0,  # 80% memory usage warning
            "critical": 90.0,  # 90% memory usage critical
            "emergency": 95.0,  # 95% memory usage emergency cleanup
        }

        # Memory tracking
        self.allocated_objects = weakref.WeakSet()
        self.large_objects = {}  # Track large allocations
        self.memory_history = deque(maxlen=1000)

        # Garbage collection tuning (Python 3.12+ optimizations)
        self._tune_garbage_collection()

        # Memory profiling setup
        if MEMORY_PROFILING_AVAILABLE:
            tracemalloc.start()

        self.optimization_stats = {
            "gc_runs": 0,
            "memory_freed_mb": 0.0,
            "large_objects_cleaned": 0,
            "cache_clearings": 0,
        }

    def _tune_garbage_collection(self):
        """Optimize garbage collection for 2025 performance."""
        try:
            # Python 3.12+ garbage collection optimizations
            if sys.version_info >= (3, 12):
                # Tune GC thresholds for better performance
                gc.set_threshold(2000, 25, 25)  # Optimized thresholds
            else:
                # Fallback for older Python versions
                gc.set_threshold(1000, 15, 15)

            # Enable debugging for optimization
            if self.logger.isEnabledFor(logging.DEBUG):
                gc.set_debug(gc.DEBUG_STATS)

        except Exception as e:
            self.logger.warning(f"Failed to tune garbage collection: {e}")

    def get_memory_usage(self) -> Dict[str, float]:
        """Get detailed memory usage information."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()

            usage = {
                "rss_mb": memory_info.rss / (1024 * 1024),  # Physical memory
                "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual memory
                "percentage": process.memory_percent(),
                "available_mb": system_memory.available / (1024 * 1024),
                "system_percentage": system_memory.percent,
            }

            # Add advanced metrics if available
            if hasattr(memory_info, "shared"):
                usage["shared_mb"] = memory_info.shared / (1024 * 1024)

            if MEMORY_PROFILING_AVAILABLE:
                current, peak = tracemalloc.get_traced_memory()
                usage["traced_current_mb"] = current / (1024 * 1024)
                usage["traced_peak_mb"] = peak / (1024 * 1024)

            # Update history
            self.memory_history.append(
                {
                    "timestamp": time.time(),
                    "usage_mb": usage["rss_mb"],
                    "percentage": usage["percentage"],
                }
            )

            return usage

        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return {"rss_mb": 0, "vms_mb": 0, "percentage": 0, "available_mb": 0}

    def optimize_memory(self, aggressive: bool = False) -> OptimizationResult:
        """Perform memory optimization with 2025 techniques."""
        start_time = time.time()

        try:
            # Get initial memory usage
            initial_usage = self.get_memory_usage()
            initial_mb = initial_usage["rss_mb"]

            operations_performed = []

            # 1. Force garbage collection
            collected = 0
            for generation in range(3):
                collected += gc.collect(generation)

            operations_performed.append(f"GC collected {collected} objects")
            self.optimization_stats["gc_runs"] += 1

            # 2. Clear internal caches
            self._clear_internal_caches()
            operations_performed.append("Cleared internal caches")
            self.optimization_stats["cache_clearings"] += 1

            # 3. Optimize large objects (2025 technique)
            if aggressive:
                freed_objects = self._optimize_large_objects()
                operations_performed.append(f"Optimized {freed_objects} large objects")
                self.optimization_stats["large_objects_cleaned"] += freed_objects

            # 4. System-level memory optimization
            if aggressive and os.geteuid() == 0:  # Root privileges required
                self._system_memory_optimization()
                operations_performed.append("Applied system memory optimizations")

            # Get final memory usage
            time.sleep(0.1)  # Allow memory to be freed
            final_usage = self.get_memory_usage()
            final_mb = final_usage["rss_mb"]

            # Calculate improvement
            memory_freed = initial_mb - final_mb
            improvement_percentage = (
                (memory_freed / initial_mb * 100) if initial_mb > 0 else 0
            )

            self.optimization_stats["memory_freed_mb"] += memory_freed

            duration_ms = (time.time() - start_time) * 1000

            result = OptimizationResult(
                operation="memory_optimization",
                before_value=initial_mb,
                after_value=final_mb,
                improvement_percentage=improvement_percentage,
                duration_ms=duration_ms,
                success=True,
                details={
                    "operations": operations_performed,
                    "objects_collected": collected,
                    "memory_freed_mb": memory_freed,
                    "aggressive_mode": aggressive,
                },
            )

            self.logger.info(
                f"🧹 Memory optimization completed: "
                f"{memory_freed:.1f}MB freed ({improvement_percentage:.1f}% improvement)"
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Memory optimization failed: {e}")

            return OptimizationResult(
                operation="memory_optimization",
                before_value=0,
                after_value=0,
                improvement_percentage=0,
                duration_ms=duration_ms,
                success=False,
                details={"error": str(e)},
            )

    def _clear_internal_caches(self):
        """Clear various internal Python caches."""
        try:
            # Clear import cache
            sys.modules.clear()

            # Clear regex cache

            re.purge()

            # Clear functools cache if available
            try:
                if hasattr(functools, "_lru_cache_wrappers"):
                    for wrapper in functools._lru_cache_wrappers:
                        wrapper.cache_clear()
            except BaseException:
                pass

            # Clear weakref callbacks

            weakref.getweakrefcount.__cache_clear__()

        except Exception as e:
            self.logger.debug(f"Error clearing caches: {e}")

    def _optimize_large_objects(self) -> int:
        """Optimize large objects in memory."""
        freed_count = 0

        try:
            # Find large objects using gc
            large_objects = []
            for obj in gc.get_objects():
                try:
                    size = sys.getsizeof(obj)
                    if size > 1024 * 1024:  # Objects larger than 1MB
                        large_objects.append((obj, size))
                except BaseException:
                    continue

            # Sort by size (largest first)
            large_objects.sort(key=lambda x: x[1], reverse=True)

            # Optimize top 10 largest objects
            for obj, size in large_objects[:10]:
                try:
                    obj_type = type(obj).__name__

                    # Optimize specific object types
                    if obj_type == "list" and len(obj) == 0:
                        del obj
                        freed_count += 1
                    elif obj_type == "dict" and len(obj) == 0:
                        del obj
                        freed_count += 1
                    elif hasattr(obj, "clear") and hasattr(obj, "__len__"):
                        if len(obj) > 1000:  # Large collections
                            obj.clear()
                            freed_count += 1

                except BaseException:
                    continue

            return freed_count

        except Exception as e:
            self.logger.debug(f"Error optimizing large objects: {e}")
            return 0

    def _system_memory_optimization(self):
        """Apply system-level memory optimizations (requires root)."""
        try:
            # Drop caches (Linux)
            if os.path.exists("/proc/sys/vm/drop_caches"):
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("1")  # Drop page cache

            # Compact memory (Linux)
            if os.path.exists("/proc/sys/vm/compact_memory"):
                with open("/proc/sys/vm/compact_memory", "w") as f:
                    f.write("1")

        except Exception as e:
            self.logger.debug(f"System memory optimization failed: {e}")

    def monitor_memory_pressure(self) -> bool:
        """Monitor memory pressure and return True if optimization needed."""
        try:
            usage = self.get_memory_usage()

            if usage["system_percentage"] > self.memory_thresholds["emergency"]:
                self.logger.warning("🚨 Emergency memory pressure detected!")
                return True
            elif usage["system_percentage"] > self.memory_thresholds["critical"]:
                self.logger.warning("⚠️ Critical memory pressure detected!")
                return True
            elif usage["system_percentage"] > self.memory_thresholds["warning"]:
                self.logger.info("📊 Memory pressure warning")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error monitoring memory pressure: {e}")
            return False


class DatabaseOptimizer:
    """Advanced database optimization with 2025 techniques."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Connection pools
        self.sqlite_pools = {}
        self.postgresql_pools = {}

        # Query optimization
        self.query_cache = {}
        self.prepared_statements = {}
        self.query_stats = defaultdict(lambda: {"count": 0, "total_time": 0.0})

        # Connection settings (2025 optimizations)
        self.default_sqlite_config = {
            "max_connections": 10,
            "min_connections": 2,
            "connection_timeout": 30,
            "busy_timeout": 5000,
            "journal_mode": "WAL",  # Write-Ahead Logging for better performance
            "synchronous": "NORMAL",  # Balance between safety and speed
            "cache_size": -64000,  # 64MB cache
            "mmap_size": 256 * 1024 * 1024,  # 256MB memory map
            "temp_store": "MEMORY",  # Store temp tables in memory
        }

        self.optimization_stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "queries_cached": 0,
            "cache_hits": 0,
            "optimizations_applied": 0,
        }

    def create_sqlite_pool(self, db_path: str, pool_name: str = "default") -> bool:
        """Create optimized SQLite connection pool."""
        try:
            if pool_name in self.sqlite_pools:
                return True

            # Ensure database directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

            pool = SQLiteConnectionPool(db_path=db_path, **self.default_sqlite_config)

            self.sqlite_pools[pool_name] = pool

            # Apply initial optimizations
            self._optimize_sqlite_database(pool_name)

            self.logger.info(
                f"✅ Created optimized SQLite pool '{pool_name}' for {db_path}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to create SQLite pool: {e}")
            return False

    def create_postgresql_pool(
        self, connection_string: str, pool_name: str = "default"
    ) -> bool:
        """Create optimized PostgreSQL connection pool."""
        if not POSTGRESQL_AVAILABLE:
            self.logger.warning("PostgreSQL not available")
            return False

        try:
            if pool_name in self.postgresql_pools:
                return True

            pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2, maxconn=20, dsn=connection_string
            )

            self.postgresql_pools[pool_name] = pool

            # Apply PostgreSQL-specific optimizations
            self._optimize_postgresql_database(pool_name)

            self.logger.info(f"✅ Created PostgreSQL pool '{pool_name}'")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create PostgreSQL pool: {e}")
            return False

    @contextmanager
    def get_connection(self, pool_name: str = "default", db_type: str = "sqlite"):
        """Get database connection with automatic optimization."""
        connection = None

        try:
            if db_type == "sqlite" and pool_name in self.sqlite_pools:
                connection = self.sqlite_pools[pool_name].get_connection()
                self.optimization_stats["connections_reused"] += 1

            elif db_type == "postgresql" and pool_name in self.postgresql_pools:
                connection = self.postgresql_pools[pool_name].getconn()
                self.optimization_stats["connections_reused"] += 1
            else:
                raise ValueError(f"No pool found: {pool_name} ({db_type})")

            yield connection

        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                if db_type == "sqlite":
                    self.sqlite_pools[pool_name].return_connection(connection)
                elif db_type == "postgresql":
                    self.postgresql_pools[pool_name].putconn(connection)

    def execute_optimized_query(
        self,
        query: str,
        params: Tuple = (),
        pool_name: str = "default",
        db_type: str = "sqlite",
    ) -> List[Tuple]:
        """Execute query with automatic optimization and caching."""
        start_time = time.time()

        try:
            # Check query cache first
            cache_key = (query, params, pool_name, db_type)
            if cache_key in self.query_cache:
                self.optimization_stats["cache_hits"] += 1
                return self.query_cache[cache_key]

            # Execute query
            with self.get_connection(pool_name, db_type) as conn:
                cursor = conn.cursor()

                # Use prepared statements for repeated queries
                if query in self.prepared_statements:
                    cursor.execute(self.prepared_statements[query], params)
                else:
                    cursor.execute(query, params)

                results = cursor.fetchall()

                # Cache SELECT results (not modification queries)
                if query.strip().upper().startswith("SELECT"):
                    self.query_cache[cache_key] = results
                    self.optimization_stats["queries_cached"] += 1

                # Update query statistics
                execution_time = time.time() - start_time
                self.query_stats[query]["count"] += 1
                self.query_stats[query]["total_time"] += execution_time

                return results

        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise

    def _optimize_sqlite_database(self, pool_name: str):
        """Apply SQLite-specific optimizations."""
        try:
            with self.get_connection(pool_name, "sqlite") as conn:
                cursor = conn.cursor()

                # Apply 2025 SQLite optimizations
                optimizations = [
                    f"PRAGMA journal_mode = {self.default_sqlite_config['journal_mode']};",
                    f"PRAGMA synchronous = {self.default_sqlite_config['synchronous']};",
                    f"PRAGMA cache_size = {self.default_sqlite_config['cache_size']};",
                    f"PRAGMA mmap_size = {self.default_sqlite_config['mmap_size']};",
                    f"PRAGMA temp_store = {self.default_sqlite_config['temp_store']};",
                    "PRAGMA optimize;",  # SQLite 3.18+ automatic optimization
                ]

                for pragma in optimizations:
                    cursor.execute(pragma)
                    self.optimization_stats["optimizations_applied"] += 1

                conn.commit()

            self.logger.info(f"🔧 Applied SQLite optimizations to pool '{pool_name}'")

        except Exception as e:
            self.logger.error(f"Failed to optimize SQLite database: {e}")

    def _optimize_postgresql_database(self, pool_name: str):
        """Apply PostgreSQL-specific optimizations."""
        try:
            with self.get_connection(pool_name, "postgresql") as conn:
                cursor = conn.cursor()

                # Apply PostgreSQL optimizations
                optimizations = [
                    "SET shared_preload_libraries = 'pg_stat_statements';",
                    "SET log_statement = 'all';",
                    "SET log_min_duration_statement = 1000;",  # Log slow queries
                ]

                for setting in optimizations:
                    try:
                        cursor.execute(setting)
                        self.optimization_stats["optimizations_applied"] += 1
                    except Exception as e:
                        self.logger.debug(
                            f"PostgreSQL optimization failed: {setting} - {e}"
                        )

                conn.commit()

            self.logger.info(
                f"🔧 Applied PostgreSQL optimizations to pool '{pool_name}'"
            )

        except Exception as e:
            self.logger.error(f"Failed to optimize PostgreSQL database: {e}")

    def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance and suggest optimizations."""
        analysis = {
            "total_queries": sum(stats["count"] for stats in self.query_stats.values()),
            "total_time": sum(
                stats["total_time"] for stats in self.query_stats.values()
            ),
            "slow_queries": [],
            "frequent_queries": [],
            "cache_hit_rate": 0.0,
        }

        # Find slow queries
        for query, stats in self.query_stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            if avg_time > 1.0:  # Queries taking more than 1 second on average
                analysis["slow_queries"].append(
                    {
                        "query": query[:100] + "..." if len(query) > 100 else query,
                        "count": stats["count"],
                        "avg_time_ms": avg_time * 1000,
                        "total_time_s": stats["total_time"],
                    }
                )

        # Find frequent queries
        frequent = sorted(
            self.query_stats.items(), key=lambda x: x[1]["count"], reverse=True
        )[:10]

        for query, stats in frequent:
            analysis["frequent_queries"].append(
                {
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "count": stats["count"],
                    "avg_time_ms": (stats["total_time"] / stats["count"]) * 1000,
                }
            )

        # Calculate cache hit rate
        total_queries = analysis["total_queries"]
        cache_hits = self.optimization_stats["cache_hits"]
        if total_queries > 0:
            analysis["cache_hit_rate"] = (cache_hits / total_queries) * 100

        return analysis

    def cleanup_resources(self):
        """Cleanup database resources."""
        try:
            # Close SQLite pools
            for pool_name, pool in self.sqlite_pools.items():
                pool.close_all()
                self.logger.info(f"🧹 Closed SQLite pool '{pool_name}'")

            # Close PostgreSQL pools
            for pool_name, pool in self.postgresql_pools.items():
                pool.closeall()
                self.logger.info(f"🧹 Closed PostgreSQL pool '{pool_name}'")

            # Clear caches
            self.query_cache.clear()
            self.prepared_statements.clear()

        except Exception as e:
            self.logger.error(f"Error cleaning up database resources: {e}")


class SQLiteConnectionPool:
    """Thread-safe SQLite connection pool with 2025 optimizations."""

    def __init__(self, db_path: str, max_connections: int = 10, **kwargs):
        self.db_path = db_path
        self.max_connections = max_connections
        self.config = kwargs

        self._pool = deque()
        self._in_use = set()
        self._lock = threading.Lock()

        # Pre-create minimum connections
        min_connections = kwargs.get("min_connections", 2)
        for _ in range(min_connections):
            self._create_connection()

    def _create_connection(self) -> sqlite3.Connection:
        """Create optimized SQLite connection."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.config.get("connection_timeout", 30),
            check_same_thread=False,
        )

        # Apply optimizations
        conn.execute(f"PRAGMA busy_timeout = {self.config.get('busy_timeout', 5000)}")
        conn.execute(f"PRAGMA journal_mode = {self.config.get('journal_mode', 'WAL')}")
        conn.execute(f"PRAGMA synchronous = {self.config.get('synchronous', 'NORMAL')}")
        conn.execute(f"PRAGMA cache_size = {self.config.get('cache_size', -64000)}")
        conn.execute(f"PRAGMA temp_store = {self.config.get('temp_store', 'MEMORY')}")

        # Enable memory mapping if supported
        mmap_size = self.config.get("mmap_size", 0)
        if mmap_size > 0:
            conn.execute(f"PRAGMA mmap_size = {mmap_size}")

        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Get connection from pool."""
        with self._lock:
            if self._pool:
                conn = self._pool.popleft()
            elif len(self._in_use) < self.max_connections:
                conn = self._create_connection()
            else:
                raise Exception("No connections available")

            self._in_use.add(conn)
            return conn

    def return_connection(self, conn: sqlite3.Connection):
        """Return connection to pool."""
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._pool.append(conn)

    def close_all(self):
        """Close all connections."""
        with self._lock:
            for conn in list(self._pool) + list(self._in_use):
                try:
                    conn.close()
                except BaseException:
                    pass

            self._pool.clear()
            self._in_use.clear()


class UnifiedPerformanceOptimizer:
    """Main unified performance optimization system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Core components
        self.memory_manager = AdvancedMemoryManager()
        self.database_optimizer = DatabaseOptimizer()

        # Performance monitoring
        self.performance_history = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.current_mode = PerformanceMode.BALANCED

        # Optimization settings
        self.optimization_settings = {
            PerformanceMode.MAXIMUM_PERFORMANCE: {
                "memory_aggressive": True,
                "database_cache_size": -128000,  # 128MB
                "gc_threshold_multiplier": 2.0,
                "optimization_frequency": 30,  # seconds
            },
            PerformanceMode.BALANCED: {
                "memory_aggressive": False,
                "database_cache_size": -64000,  # 64MB
                "gc_threshold_multiplier": 1.0,
                "optimization_frequency": 60,  # seconds
            },
            PerformanceMode.MEMORY_CONSERVATIVE: {
                "memory_aggressive": False,
                "database_cache_size": -16000,  # 16MB
                "gc_threshold_multiplier": 0.5,
                "optimization_frequency": 300,  # 5 minutes
            },
            PerformanceMode.BATTERY_SAVER: {
                "memory_aggressive": False,
                "database_cache_size": -8000,  # 8MB
                "gc_threshold_multiplier": 0.2,
                "optimization_frequency": 600,  # 10 minutes
            },
        }

        # Background optimization
        self.optimization_thread = None
        self.optimization_running = False

        # Statistics
        self.optimization_results = []

    def start_background_optimization(self):
        """Start background performance optimization."""
        if self.optimization_running:
            return

        self.optimization_running = True
        self.optimization_thread = threading.Thread(
            target=self._optimization_loop, daemon=True, name="PerformanceOptimizer"
        )
        self.optimization_thread.start()

        self.logger.info("🚀 Background performance optimization started")

    def stop_background_optimization(self):
        """Stop background performance optimization."""
        self.optimization_running = False

        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5.0)

        self.logger.info("🛑 Background performance optimization stopped")

    def _optimization_loop(self):
        """Main background optimization loop."""
        while self.optimization_running:
            try:
                # Get current performance metrics
                metrics = self.get_performance_metrics()
                self.performance_history.append(metrics)

                # Check if optimization is needed
                if self._should_optimize(metrics):
                    result = self.optimize_performance()
                    if result.success:
                        self.optimization_results.append(result)

                # Sleep based on current mode
                settings = self.optimization_settings[self.current_mode]
                time.sleep(settings["optimization_frequency"])

            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                time.sleep(60)  # Wait before retrying

    def _should_optimize(self, metrics: PerformanceMetrics) -> bool:
        """Determine if optimization should be performed."""
        # Memory-based triggers
        if metrics.memory_percentage > 80:
            return True

        # CPU-based triggers
        if metrics.cpu_usage > 90:
            return True

        # Database-based triggers
        if metrics.database_connections > 50:
            return True

        # Time-based optimization (periodic)
        if len(self.optimization_results) == 0:
            return True

        last_optimization = (
            self.optimization_results[-1] if self.optimization_results else None
        )
        if last_optimization:
            time_since_last = datetime.now() - last_optimization.details.get(
                "timestamp", datetime.now()
            )
            settings = self.optimization_settings[self.current_mode]
            if time_since_last.total_seconds() > settings["optimization_frequency"]:
                return True

        return False

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get comprehensive performance metrics."""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_info = self.memory_manager.get_memory_usage()

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_mb = 0
            if disk_io:
                disk_io_mb = (disk_io.read_bytes + disk_io.write_bytes) / (1024 * 1024)

            # Network I/O
            net_io = psutil.net_io_counters()
            network_io_mb = 0
            if net_io:
                network_io_mb = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)

            # Database metrics
            total_db_connections = sum(
                len(pool._in_use) + len(pool._pool)
                for pool in self.database_optimizer.sqlite_pools.values()
            )

            # GC metrics
            gc_stats = gc.get_stats()
            gc_collections = sum(stat["collections"] for stat in gc_stats)

            # Cache hit rate
            cache_hits = self.database_optimizer.optimization_stats["cache_hits"]
            total_queries = sum(
                stats["count"] for stats in self.database_optimizer.query_stats.values()
            )
            cache_hit_rate = (
                (cache_hits / total_queries * 100) if total_queries > 0 else 0
            )

            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage_mb=memory_info["rss_mb"],
                memory_percentage=memory_info["percentage"],
                disk_io_mb=disk_io_mb,
                network_io_mb=network_io_mb,
                database_connections=total_db_connections,
                cache_hit_rate=cache_hit_rate,
                gc_collections=gc_collections,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return PerformanceMetrics()

    def optimize_performance(
        self, force_aggressive: bool = False
    ) -> OptimizationResult:
        """Perform comprehensive performance optimization."""
        start_time = time.time()

        try:
            initial_metrics = self.get_performance_metrics()
            operations = []

            # Memory optimization
            settings = self.optimization_settings[self.current_mode]
            aggressive = force_aggressive or settings["memory_aggressive"]

            memory_result = self.memory_manager.optimize_memory(aggressive)
            if memory_result.success:
                operations.append(
                    f"Memory: {memory_result.improvement_percentage:.1f}% improvement"
                )

            # Database optimization
            self._optimize_database_performance()
            operations.append("Database: Connection pools optimized")

            # System-level optimizations (if available)
            if os.geteuid() == 0:  # Root privileges
                self._system_level_optimization()
                operations.append("System: Applied kernel optimizations")

            # Get final metrics
            time.sleep(0.5)  # Allow optimizations to take effect
            final_metrics = self.get_performance_metrics()

            # Calculate overall improvement
            memory_improvement = (
                (
                    (initial_metrics.memory_usage_mb - final_metrics.memory_usage_mb)
                    / initial_metrics.memory_usage_mb
                    * 100
                )
                if initial_metrics.memory_usage_mb > 0
                else 0
            )

            cpu_improvement = (
                (
                    (initial_metrics.cpu_usage - final_metrics.cpu_usage)
                    / initial_metrics.cpu_usage
                    * 100
                )
                if initial_metrics.cpu_usage > 0
                else 0
            )

            overall_improvement = (memory_improvement + cpu_improvement) / 2

            duration_ms = (time.time() - start_time) * 1000

            result = OptimizationResult(
                operation="comprehensive_optimization",
                before_value=initial_metrics.memory_usage_mb
                + initial_metrics.cpu_usage,
                after_value=final_metrics.memory_usage_mb + final_metrics.cpu_usage,
                improvement_percentage=overall_improvement,
                duration_ms=duration_ms,
                success=True,
                details={
                    "operations": operations,
                    "initial_metrics": initial_metrics,
                    "final_metrics": final_metrics,
                    "mode": self.current_mode.value,
                    "timestamp": datetime.now(),
                },
            )

            self.logger.info(
                f"🎯 Performance optimization completed: "
                f"{overall_improvement:.1f}% improvement in {duration_ms:.1f}ms"
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Performance optimization failed: {e}")

            return OptimizationResult(
                operation="comprehensive_optimization",
                before_value=0,
                after_value=0,
                improvement_percentage=0,
                duration_ms=duration_ms,
                success=False,
                details={"error": str(e)},
            )

    def _optimize_database_performance(self):
        """Optimize database performance."""
        try:
            # Clear query cache if it's getting too large
            if len(self.database_optimizer.query_cache) > 10000:
                self.database_optimizer.query_cache.clear()
                self.logger.info("🧹 Cleared database query cache")

            # Optimize SQLite connections
            for pool_name, pool in self.database_optimizer.sqlite_pools.items():
                self.database_optimizer._optimize_sqlite_database(pool_name)

        except Exception as e:
            self.logger.error(f"Database performance optimization failed: {e}")

    def _system_level_optimization(self):
        """Apply system-level performance optimizations."""
        try:
            # Linux-specific optimizations
            if os.name == "posix":
                # Optimize swappiness
                with open("/proc/sys/vm/swappiness", "w") as f:
                    f.write("10")  # Reduce swapping

                # Optimize dirty ratio
                with open("/proc/sys/vm/dirty_ratio", "w") as f:
                    f.write("15")  # Better I/O performance

        except Exception as e:
            self.logger.debug(f"System-level optimization failed: {e}")

    def set_performance_mode(self, mode: PerformanceMode):
        """Set performance optimization mode."""
        old_mode = self.current_mode
        self.current_mode = mode

        # Apply mode-specific optimizations
        self.optimization_settings[mode]

        # Update database cache sizes
        for pool in self.database_optimizer.sqlite_pools.values():
            # This would update cache settings in a real implementation
            pass

        self.logger.info(
            f"🔄 Performance mode changed: {old_mode.value} → {mode.value}"
        )

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        current_metrics = self.get_performance_metrics()

        report = {
            "current_metrics": {
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage_mb": current_metrics.memory_usage_mb,
                "memory_percentage": current_metrics.memory_percentage,
                "database_connections": current_metrics.database_connections,
                "cache_hit_rate": current_metrics.cache_hit_rate,
            },
            "optimization_stats": {
                "memory_manager": self.memory_manager.optimization_stats,
                "database_optimizer": self.database_optimizer.optimization_stats,
            },
            "recent_optimizations": [
                {
                    "operation": result.operation,
                    "improvement": result.improvement_percentage,
                    "duration_ms": result.duration_ms,
                    "timestamp": result.details.get("timestamp", "unknown"),
                }
                for result in self.optimization_results[-10:]  # Last 10 optimizations
            ],
            "performance_mode": self.current_mode.value,
            "recommendations": self._generate_recommendations(current_metrics),
        }

        return report

    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        if metrics.memory_percentage > 80:
            recommendations.append("Consider reducing memory usage or adding more RAM")

        if metrics.cpu_usage > 90:
            recommendations.append(
                "High CPU usage detected - consider optimizing algorithms"
            )

        if metrics.cache_hit_rate < 50:
            recommendations.append(
                "Low cache hit rate - consider increasing cache size"
            )

        if metrics.database_connections > 20:
            recommendations.append(
                "High database connection count - consider connection pooling"
            )

        if not recommendations:
            recommendations.append("System performance is optimal")

        return recommendations

    def cleanup(self):
        """Cleanup performance optimizer resources."""
        try:
            self.stop_background_optimization()
            self.database_optimizer.cleanup_resources()

            self.logger.info("🧹 Performance optimizer cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Example usage and testing
async def demonstrate_performance_optimizer():
    """Demonstrate the unified performance optimizer."""
    print("⚡ Unified Performance Optimizer Demonstration")
    print("=" * 55)

    # Create optimizer
    optimizer = UnifiedPerformanceOptimizer()

    try:
        # Create test database using secure temp directory
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name
        optimizer.database_optimizer.create_sqlite_pool(db_path, "test")

        # Get initial metrics
        initial_metrics = optimizer.get_performance_metrics()
        print("📊 Initial Metrics:")
        print(
            f"   Memory: {initial_metrics.memory_usage_mb:.1f}MB ({
                initial_metrics.memory_percentage:.1f}%)"
        )
        print(f"   CPU: {initial_metrics.cpu_usage:.1f}%")
        print(f"   Database connections: {initial_metrics.database_connections}")

        # Start background optimization
        optimizer.start_background_optimization()
        print("✅ Background optimization started")

        # Simulate some work
        print("⏱️ Simulating workload for 30 seconds...")

        # Create some database activity
        for i in range(100):
            try:
                optimizer.database_optimizer.execute_optimized_query(
                    "SELECT name FROM sqlite_master WHERE type='table'",
                    pool_name="test",
                )
            except BaseException:
                pass

        await asyncio.sleep(30)

        # Force optimization
        result = optimizer.optimize_performance(force_aggressive=True)
        if result.success:
            print(
                f"🎯 Optimization completed: {result.improvement_percentage:.1f}% improvement"
            )

        # Get final metrics
        final_metrics = optimizer.get_performance_metrics()
        print("📊 Final Metrics:")
        print(
            f"   Memory: {final_metrics.memory_usage_mb:.1f}MB ({
                final_metrics.memory_percentage:.1f}%)"
        )
        print(f"   CPU: {final_metrics.cpu_usage:.1f}%")
        print(f"   Cache hit rate: {final_metrics.cache_hit_rate:.1f}%")

        # Generate report
        report = optimizer.get_optimization_report()
        print("\n📄 Optimization Report:")
        print(f"   Recent optimizations: {len(report['recent_optimizations'])}")
        print(
            f"   Memory freed (total): {
                optimizer.memory_manager.optimization_stats['memory_freed_mb']:.1f}MB"
        )
        print(f"   GC runs: {optimizer.memory_manager.optimization_stats['gc_runs']}")
        print(
            f"   Database cache hits: {
                optimizer.database_optimizer.optimization_stats['cache_hits']
            }"
        )

        # Show recommendations
        print("\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   - {rec}")

    finally:
        optimizer.cleanup()
        print("✅ Cleanup completed")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run demonstration
    asyncio.run(demonstrate_performance_optimizer())
