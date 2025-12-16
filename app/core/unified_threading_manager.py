#!/usr/bin/env python3
from __future__ import annotations

"""
Unified Threading & Async Manager for xanadOS Search & Destroy
=============================================================

This module consolidates all threading and async functionality from:
- app/core/async_scanner_engine.py (828 lines) - Primary async scanner
- app/core/async_threat_detector.py (720 lines) - Async threat detection
- app/core/advanced_async_scanner.py (700 lines) - Advanced async patterns
- app/core/async_scanner.py (479 lines) - Basic async scanner
- app/gui/scan_thread.py (479 lines) - GUI scan threading
- app/core/async_integration.py (405 lines) - Async component integration
- app/core/async_file_metadata_cache.py (319 lines) - Async metadata cache
- app/core/async_resource_coordinator.py (281 lines) - Resource management
- app/gui/thread_cancellation.py (80 lines) - Thread cancellation

Note: File system monitoring was consolidated into app/monitoring/file_watcher.py
with integrated async support (fanotify + watchdog + async/await). See that
module for file monitoring functionality.

Features:
- Unified async/await patterns for modern Python
- Centralized resource coordination and semaphore management
- GUI thread management with cooperative cancellation
- Thread pool management with adaptive sizing
- Performance-optimized concurrent operations
- Memory-efficient async operations with backpressure
- Deadlock prevention and resource monitoring
- Unified logging and metrics collection

Total consolidation: 9 files (4,291 lines) → 1 unified system
File monitoring: Separate consolidation in app/monitoring/file_watcher.py
"""

import asyncio
import logging
import threading
import time
import types
import weakref
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from queue import Queue, PriorityQueue
from collections.abc import Callable, AsyncIterator
from typing import Any, Optional, Union
from weakref import WeakSet

import psutil

# Import AdaptiveWorkerPool from separate module to avoid circular imports
try:
    from .adaptive_worker_pool import AdaptiveWorkerPool

    HAS_ADAPTIVE_POOL = True
except ImportError:
    HAS_ADAPTIVE_POOL = False
    AdaptiveWorkerPool = None

try:
    from PyQt6.QtCore import QThread, pyqtSignal

    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False
    QThread = object  # Fallback base class

    def pyqtSignal(*args, **kwargs):
        return None


try:
    import aiofiles
    import aiofiles.os

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

# =============================================================================
# Core Enums and Data Classes
# =============================================================================


class ResourceType(Enum):
    """Types of resources managed by the coordinator."""

    FILE_IO = "file_io"
    NETWORK = "network"
    ML_COMPUTATION = "ml_computation"
    THREAT_ANALYSIS = "threat_analysis"
    DATABASE = "database"
    CACHE = "cache"
    GPU = "gpu"
    CPU_INTENSIVE = "cpu_intensive"
    SCAN_OPERATION = "scan_operation"
    GUI_THREAD = "gui_thread"


class TaskPriority(Enum):
    """Task priority levels for queue management."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class ThreadPoolType(Enum):
    """Types of thread pools available."""

    IO_BOUND = "io_bound"
    CPU_BOUND = "cpu_bound"
    MIXED = "mixed"
    GUI = "gui"


@dataclass
class ResourceLimits:
    """Resource limits configuration."""

    max_file_operations: int = 50
    max_network_connections: int = 20
    max_ml_operations: int = 5
    max_threat_analyses: int = 30
    max_database_connections: int = 10
    max_cache_operations: int = 100
    max_gpu_operations: int = 2
    max_cpu_intensive: int = 4
    max_scan_operations: int = 20
    max_gui_threads: int = 5


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""

    active_operations: dict[ResourceType, int] = field(default_factory=dict)
    peak_usage: dict[ResourceType, int] = field(default_factory=dict)
    total_operations: dict[ResourceType, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AsyncTaskRequest:
    """Request for async task execution."""

    task_id: str
    priority: TaskPriority
    coro: Any  # Coroutine to execute
    callback: Optional[Callable] = None
    timeout: Optional[float] = None
    resource_type: ResourceType = ResourceType.CPU_INTENSIVE
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThreadTaskRequest:
    """Request for thread pool task execution."""

    task_id: str
    priority: TaskPriority
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None
    timeout: Optional[float] = None
    pool_type: ThreadPoolType = ThreadPoolType.IO_BOUND
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CancellationMetric:
    """Metrics for thread/task cancellation tracking."""

    name: str
    requested_at: float
    finished_at: float
    latency: float
    graceful: bool


@dataclass
class PerformanceMetrics:
    """Performance metrics for threading and async operations."""

    total_async_tasks: int = 0
    total_thread_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    average_task_duration: float = 0.0
    peak_concurrent_operations: int = 0
    resource_utilization: dict[ResourceType, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# Cooperative Cancellation Mixin
# =============================================================================


class CooperativeCancellationMixin:
    """Mixin for cooperative thread/task cancellation with metrics."""

    def __init__(self):
        self.cancellation_requested_at: float | None = None
        self.cancellation_finished_at: float | None = None
        self._cancellation_name: str = "operation"
        self._graceful_flag: bool = False
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def cooperative_cancel(self, *, graceful: bool = True):
        """Mark cancellation request."""
        if self.cancellation_requested_at is None:
            self.cancellation_requested_at = time.time()
            self._graceful_flag = graceful
            self._logger.debug(f"Cancellation requested for {self._cancellation_name}")

    def mark_cancellation_complete(self):
        """Mark cancellation as complete and record metrics."""
        if (
            self.cancellation_finished_at is None
            and self.cancellation_requested_at is not None
        ):
            self.cancellation_finished_at = time.time()
            self._register_cancellation_metric()

    def cancellation_latency(self) -> float | None:
        """Get cancellation latency in seconds."""
        if self.cancellation_requested_at and self.cancellation_finished_at:
            return self.cancellation_finished_at - self.cancellation_requested_at
        return None

    def _register_cancellation_metric(self):
        """Register cancellation metric with global tracker."""
        if self.cancellation_requested_at and self.cancellation_finished_at:
            metric = CancellationMetric(
                name=self._cancellation_name,
                requested_at=self.cancellation_requested_at,
                finished_at=self.cancellation_finished_at,
                latency=self.cancellation_finished_at - self.cancellation_requested_at,
                graceful=self._graceful_flag,
            )
            # Register with unified manager
            from .unified_threading_manager import get_threading_manager

            manager = get_threading_manager()
            manager._record_cancellation_metric(metric)


# =============================================================================
# Resource Context Manager
# =============================================================================


class ResourceContext:
    """Context manager for resource acquisition and release."""

    def __init__(
        self,
        semaphore: asyncio.Semaphore,
        resource_type: ResourceType,
        coordinator: "AsyncResourceCoordinator",
        operation_id: Optional[str] = None,
    ):
        self.semaphore = semaphore
        self.resource_type = resource_type
        self.coordinator = coordinator
        self.operation_id = operation_id or f"{resource_type.value}_{id(self)}"
        self.acquired = False
        self.start_time: float | None = None

    async def __aenter__(self):
        """Acquire resource."""
        await self.semaphore.acquire()
        self.acquired = True
        self.start_time = time.time()
        await self.coordinator._track_resource_acquisition(
            self.resource_type, self.operation_id
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release resource."""
        if self.acquired:
            self.semaphore.release()
            if self.start_time:
                duration = time.time() - self.start_time
                await self.coordinator._track_resource_release(
                    self.resource_type, self.operation_id, duration
                )
            self.acquired = False


# =============================================================================
# Unified GUI Thread Class
# =============================================================================

if HAS_PYQT6:

    class UnifiedScanThread(QThread, CooperativeCancellationMixin):
        """Unified GUI thread for scan operations with cooperative cancellation."""

        # PyQt6 signals
        progress_updated = pyqtSignal(int)
        scan_completed = pyqtSignal(dict)
        status_updated = pyqtSignal(str)
        scan_detail_updated = pyqtSignal(dict)
        error_occurred = pyqtSignal(str)

        def __init__(
            self,
            scanner,
            path: str,
            quick_scan: bool = False,
            scan_options: Optional[dict[str, Any]] = None,
        ):
            QThread.__init__(self)
            CooperativeCancellationMixin.__init__(self)

            self.scanner = scanner
            self.path = path
            self.quick_scan = quick_scan
            self.scan_options = scan_options or {}
            self._cancelled = False
            self._current_scan_type = "quick" if quick_scan else "full"
            self._cancellation_name = f"scan_thread_{id(self)}"

        def stop_scan(self):
            """Stop scan with cooperative cancellation."""
            self.cooperative_cancel()
            self._cancelled = True
            self.requestInterruption()

            # Propagate cancellation to scanner
            if hasattr(self.scanner, "cancel_scan"):
                try:
                    self.scanner.cancel_scan()
                except Exception as e:
                    self.error_occurred.emit(f"Error cancelling scanner: {e}")

        def run(self):
            """Execute scan operation in thread."""
            try:
                # Set up scanner integration
                if hasattr(self.scanner, "_current_thread"):
                    self.scanner._current_thread = self

                # Reset scanner state
                if hasattr(self.scanner, "reset_scan_state"):
                    self.scanner.reset_scan_state()

                # Set up progress callbacks
                self._setup_callbacks()

                # Check for early cancellation
                if self.isInterruptionRequested() or self._cancelled:
                    self._emit_cancellation()
                    return

                # Execute scan
                self._execute_scan()

            except Exception as e:
                self.error_occurred.emit(f"Scan thread error: {e}")
                self.scan_completed.emit({"status": "error", "message": str(e)})
            finally:
                self.mark_cancellation_complete()

        def _setup_callbacks(self):
            """Set up progress and status callbacks."""

            def safe_progress_callback(progress, status):
                if self.isInterruptionRequested() or self._cancelled:
                    return
                try:
                    self.progress_updated.emit(int(progress))
                    self.status_updated.emit(str(status))
                except Exception as e:
                    self.error_occurred.emit(f"Progress callback error: {e}")

            def safe_detailed_progress_callback(detail_info):
                if self.isInterruptionRequested() or self._cancelled:
                    return
                try:
                    self.scan_detail_updated.emit(detail_info)
                except Exception as e:
                    self.error_occurred.emit(f"Detailed progress callback error: {e}")

            # Configure scanner callbacks
            if hasattr(self.scanner, "set_progress_callback"):
                self.scanner.set_progress_callback(safe_progress_callback)
            if hasattr(self.scanner, "set_detailed_progress_callback"):
                self.scanner.set_detailed_progress_callback(
                    safe_detailed_progress_callback
                )

        def _emit_cancellation(self):
            """Emit cancellation signals."""
            self.status_updated.emit("Scan cancelled")
            self.scan_completed.emit(
                {
                    "status": "cancelled",
                    "message": "Scan was cancelled",
                    "cancellation_latency": self.cancellation_latency(),
                }
            )

        def _execute_scan(self):
            """Execute the actual scan operation."""
            self.progress_updated.emit(0)
            self.status_updated.emit(f"Starting {self._current_scan_type} scan...")

            # Determine scan method based on type
            if self.quick_scan:
                if hasattr(self.scanner, "quick_scan_path"):
                    result = self.scanner.quick_scan_path(
                        self.path, **self.scan_options
                    )
                else:
                    result = self.scanner.scan_path(
                        self.path, quick=True, **self.scan_options
                    )
            else:
                result = self.scanner.scan_path(self.path, **self.scan_options)

            # Emit completion
            if not (self.isInterruptionRequested() or self._cancelled):
                self.progress_updated.emit(100)
                self.status_updated.emit("Scan completed")
                self.scan_completed.emit(
                    {
                        "status": "completed",
                        "result": result,
                        "scan_type": self._current_scan_type,
                    }
                )

else:
    # Fallback when PyQt6 is not available
    class UnifiedScanThread(CooperativeCancellationMixin):
        """Fallback thread class when PyQt6 is not available."""

        def __init__(self, *args, **kwargs):
            super().__init__()
            self._logger.warning(
                "PyQt6 not available, using fallback thread implementation"
            )


# =============================================================================
# Async Resource Coordinator
# =============================================================================


class AsyncResourceCoordinator:
    """Unified coordinator for managing async resources across components."""

    _instance: Optional["AsyncResourceCoordinator"] = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "AsyncResourceCoordinator":
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        """Initialize the resource coordinator."""
        if hasattr(self, "_initialized"):
            return

        self.logger = logging.getLogger(__name__)
        self.limits = limits or self._get_adaptive_limits()
        self.semaphores: dict[ResourceType, asyncio.Semaphore] = {}
        self._initialize_semaphores()
        self.usage = ResourceUsage()
        self._active_operations: WeakSet = WeakSet()
        self.start_time = time.time()
        self.monitoring_enabled = True
        self._stats_lock = asyncio.Lock()
        self._initialized = True

    def _get_adaptive_limits(self) -> ResourceLimits:
        """Calculate adaptive resource limits based on system capabilities."""
        try:
            # Get system information
            cpu_count = psutil.cpu_count(logical=False) or 4
            memory_gb = psutil.virtual_memory().total / (1024**3)

            # Calculate adaptive limits
            return ResourceLimits(
                max_file_operations=min(max(cpu_count * 8, 20), 100),
                max_network_connections=min(max(cpu_count * 4, 10), 50),
                max_ml_operations=min(max(cpu_count // 2, 2), 8),
                max_threat_analyses=min(max(cpu_count * 6, 15), 60),
                max_database_connections=min(max(cpu_count * 2, 5), 20),
                max_cache_operations=min(max(cpu_count * 12, 50), 200),
                max_gpu_operations=4 if memory_gb > 8 else 2,
                max_cpu_intensive=min(max(cpu_count, 2), 8),
                max_scan_operations=min(max(cpu_count * 4, 10), 40),
                max_gui_threads=min(max(cpu_count // 2, 2), 8),
            )
        except Exception as e:
            self.logger.warning(f"Failed to get adaptive limits: {e}, using defaults")
            return ResourceLimits()

    def _initialize_semaphores(self) -> None:
        """Initialize semaphores for each resource type."""
        resource_map = {
            ResourceType.FILE_IO: self.limits.max_file_operations,
            ResourceType.NETWORK: self.limits.max_network_connections,
            ResourceType.ML_COMPUTATION: self.limits.max_ml_operations,
            ResourceType.THREAT_ANALYSIS: self.limits.max_threat_analyses,
            ResourceType.DATABASE: self.limits.max_database_connections,
            ResourceType.CACHE: self.limits.max_cache_operations,
            ResourceType.GPU: self.limits.max_gpu_operations,
            ResourceType.CPU_INTENSIVE: self.limits.max_cpu_intensive,
            ResourceType.SCAN_OPERATION: self.limits.max_scan_operations,
            ResourceType.GUI_THREAD: self.limits.max_gui_threads,
        }

        for resource_type, limit in resource_map.items():
            self.semaphores[resource_type] = asyncio.Semaphore(limit)
            self.usage.active_operations[resource_type] = 0
            self.usage.peak_usage[resource_type] = 0
            self.usage.total_operations[resource_type] = 0

    def acquire_resource(
        self, resource_type: ResourceType, operation_id: Optional[str] = None
    ) -> ResourceContext:
        """Acquire a resource with automatic tracking and cleanup."""
        return ResourceContext(
            self.semaphores[resource_type], resource_type, self, operation_id
        )

    async def _track_resource_acquisition(
        self, resource_type: ResourceType, operation_id: str
    ):
        """Track resource acquisition."""
        async with self._stats_lock:
            self.usage.active_operations[resource_type] += 1
            self.usage.total_operations[resource_type] += 1

            # Update peak usage
            current = self.usage.active_operations[resource_type]
            if current > self.usage.peak_usage[resource_type]:
                self.usage.peak_usage[resource_type] = current

            self.usage.last_updated = datetime.utcnow()

    async def _track_resource_release(
        self, resource_type: ResourceType, operation_id: str, duration: float
    ):
        """Track resource release."""
        async with self._stats_lock:
            self.usage.active_operations[resource_type] -= 1
            self.usage.last_updated = datetime.utcnow()

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        return self.usage

    def get_semaphore(self, resource_type: ResourceType) -> asyncio.Semaphore:
        """Get semaphore for specific resource type."""
        return self.semaphores[resource_type]

    # Backward compatibility methods
    def get_file_semaphore(self) -> asyncio.Semaphore:
        """Get file I/O semaphore (for backward compatibility)."""
        return self.semaphores[ResourceType.FILE_IO]

    def get_ml_semaphore(self) -> asyncio.Semaphore:
        """Get ML computation semaphore (for backward compatibility)."""
        return self.semaphores[ResourceType.ML_COMPUTATION]

    def get_threat_semaphore(self) -> asyncio.Semaphore:
        """Get threat analysis semaphore (for backward compatibility)."""
        return self.semaphores[ResourceType.THREAT_ANALYSIS]


# =============================================================================
# Unified Threading & Async Manager
# =============================================================================


class UnifiedThreadingManager:
    """
    Unified manager for all threading and async operations.

    Consolidates functionality from:
    - Async scanners and threat detectors
    - GUI thread management
    - Resource coordination
    - Thread pool management
    - Performance monitoring
    """

    _instance: "UnifiedThreadingManager" | None = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "UnifiedThreadingManager":
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the unified threading manager."""
        if hasattr(self, "_initialized"):
            return

        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # Core components
        self.resource_coordinator = AsyncResourceCoordinator()

        # Thread pools with adaptive scaling
        self.thread_pools: dict[ThreadPoolType, ThreadPoolExecutor] = {}
        self.adaptive_pools: dict[ThreadPoolType, Any] = (
            {}
        )  # AdaptiveWorkerPool instances
        self._initialize_thread_pools()

        # Async components
        self.async_task_queue: asyncio.Queue = asyncio.Queue()
        self.active_async_tasks: WeakSet = WeakSet()
        self.task_semaphore = asyncio.Semaphore(20)  # Global async task limit

        # Thread task management
        self.thread_task_queue: Queue = PriorityQueue()
        self.active_thread_tasks: WeakSet = WeakSet()

        # Performance tracking
        self.metrics = PerformanceMetrics()
        self._cancellation_metrics: list[CancellationMetric] = []
        self._metrics_lock = threading.Lock()

        # Control flags
        self.running = True
        self._background_tasks: list[asyncio.Task] = []

        self._initialized = True
        self.logger.info("Unified Threading Manager initialized")

    def _initialize_thread_pools(self):
        """Initialize various thread pools for different workload types."""
        try:
            cpu_count = psutil.cpu_count(logical=False) or 4

            # IO-bound operations with adaptive worker pool (file scanning)
            if HAS_ADAPTIVE_POOL and AdaptiveWorkerPool:
                adaptive_pool = AdaptiveWorkerPool(
                    min_workers=None,  # Auto-calculate based on cores
                    max_workers=None,
                    adjustment_interval=5.0,
                    enable_monitoring=True,
                )
                initial_workers = adaptive_pool.current_workers
                self.thread_pools[ThreadPoolType.IO_BOUND] = ThreadPoolExecutor(
                    max_workers=initial_workers, thread_name_prefix="IO"
                )
                adaptive_pool.set_executor(self.thread_pools[ThreadPoolType.IO_BOUND])
                self.adaptive_pools[ThreadPoolType.IO_BOUND] = adaptive_pool
                self.logger.info(
                    f"IO-bound pool with adaptive scaling: {initial_workers} workers "
                    f"(min: {adaptive_pool.min_workers}, max: {adaptive_pool.max_workers})"
                )
            else:
                # Fallback without adaptive scaling
                self.thread_pools[ThreadPoolType.IO_BOUND] = ThreadPoolExecutor(
                    max_workers=min(cpu_count * 4, 32), thread_name_prefix="IO"
                )
                self.logger.info(
                    f"IO-bound pool: {min(cpu_count * 4, 32)} workers (fixed)"
                )

            # CPU-bound operations (computations, analysis)
            self.thread_pools[ThreadPoolType.CPU_BOUND] = ThreadPoolExecutor(
                max_workers=min(cpu_count, 8), thread_name_prefix="CPU"
            )

            # Mixed workloads
            self.thread_pools[ThreadPoolType.MIXED] = ThreadPoolExecutor(
                max_workers=min(cpu_count * 2, 16), thread_name_prefix="Mixed"
            )

            # GUI operations (if PyQt6 available)
            if HAS_PYQT6:
                self.thread_pools[ThreadPoolType.GUI] = ThreadPoolExecutor(
                    max_workers=min(cpu_count // 2, 4), thread_name_prefix="GUI"
                )

        except Exception as e:
            self.logger.error(f"Failed to initialize thread pools: {e}")
            # Fallback minimal configuration
            self.thread_pools[ThreadPoolType.IO_BOUND] = ThreadPoolExecutor(
                max_workers=4, thread_name_prefix="IO"
            )
            self.thread_pools[ThreadPoolType.CPU_BOUND] = ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="CPU"
            )

    async def start_background_services(self):
        """Start background services for task processing."""
        if not self.running:
            return

        # Start async task processor
        async_processor = asyncio.create_task(self._process_async_tasks())
        self._background_tasks.append(async_processor)

        # Start thread task processor
        thread_processor = asyncio.create_task(self._process_thread_tasks())
        self._background_tasks.append(thread_processor)

        self.logger.info("Background services started")

    async def shutdown(self):
        """Shutdown the threading manager and cleanup resources."""
        self.running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Shutdown thread pools
        for pool_type, pool in self.thread_pools.items():
            self.logger.debug(f"Shutting down {pool_type.value} thread pool")
            pool.shutdown(wait=True)

        self.logger.info("Unified Threading Manager shutdown complete")

    # ==========================================================================
    # Async Task Management
    # ==========================================================================

    async def submit_async_task(self, task_request: AsyncTaskRequest) -> Any:
        """Submit an async task for execution."""
        async with self.task_semaphore:
            try:
                start_time = time.time()

                # Acquire resource if needed
                async with self.resource_coordinator.acquire_resource(
                    task_request.resource_type, task_request.task_id
                ):
                    # Execute with timeout if specified
                    if task_request.timeout:
                        result = await asyncio.wait_for(
                            task_request.coro, timeout=task_request.timeout
                        )
                    else:
                        result = await task_request.coro

                    # Update metrics
                    duration = time.time() - start_time
                    await self._update_task_metrics(True, duration)

                    # Call callback if provided
                    if task_request.callback:
                        try:
                            await task_request.callback(result)
                        except Exception as e:
                            self.logger.error(
                                f"Callback error for task {task_request.task_id}: {e}"
                            )

                    return result

            except asyncio.TimeoutError:
                await self._update_task_metrics(False, 0)
                self.logger.warning(f"Task {task_request.task_id} timed out")
                raise
            except Exception as e:
                await self._update_task_metrics(False, 0)
                self.logger.error(f"Task {task_request.task_id} failed: {e}")
                raise

    async def _process_async_tasks(self):
        """Background processor for queued async tasks."""
        while self.running:
            try:
                # Get task from queue with timeout
                task_request = await asyncio.wait_for(
                    self.async_task_queue.get(), timeout=1.0
                )

                # Create and track task
                task = asyncio.create_task(self.submit_async_task(task_request))
                self.active_async_tasks.add(task)

                # Clean up completed tasks
                await self._cleanup_completed_async_tasks()

            except asyncio.TimeoutError:
                continue  # Normal timeout, check running flag
            except Exception as e:
                self.logger.error(f"Error processing async tasks: {e}")

    async def _cleanup_completed_async_tasks(self):
        """Clean up completed async tasks."""
        completed_tasks = [task for task in self.active_async_tasks if task.done()]
        for task in completed_tasks:
            try:
                self.active_async_tasks.discard(task)
                if task.exception():
                    self.logger.error(f"Async task failed: {task.exception()}")
            except Exception as e:
                self.logger.error(f"Error cleaning up task: {e}")

    # ==========================================================================
    # Thread Pool Management
    # ==========================================================================

    def submit_thread_task(self, task_request: ThreadTaskRequest) -> Any:
        """Submit a task to appropriate thread pool."""
        pool = self.thread_pools.get(task_request.pool_type)
        if not pool:
            raise ValueError(f"Thread pool {task_request.pool_type} not available")

        try:
            start_time = time.time()

            # Submit to thread pool
            future = pool.submit(
                task_request.func, *task_request.args, **task_request.kwargs
            )
            self.active_thread_tasks.add(future)

            # Handle timeout if specified
            if task_request.timeout:
                result = future.result(timeout=task_request.timeout)
            else:
                result = future.result()

            # Update metrics
            duration = time.time() - start_time
            self._update_thread_task_metrics(True, duration)

            # Call callback if provided
            if task_request.callback:
                try:
                    task_request.callback(result)
                except Exception as e:
                    self.logger.error(
                        f"Callback error for task {task_request.task_id}: {e}"
                    )

            return result

        except Exception as e:
            self._update_thread_task_metrics(False, 0)
            self.logger.error(f"Thread task {task_request.task_id} failed: {e}")
            raise
        finally:
            self.active_thread_tasks.discard(future)

    async def _process_thread_tasks(self):
        """Background processor for thread tasks."""
        while self.running:
            try:
                await asyncio.sleep(0.1)  # Yield control

                if not self.thread_task_queue.empty():
                    priority, task_request = self.thread_task_queue.get_nowait()

                    # Execute in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, self.submit_thread_task, task_request
                    )

            except Exception as e:
                self.logger.error(f"Error processing thread tasks: {e}")

    # ==========================================================================
    # GUI Thread Management
    # ==========================================================================

    def create_scan_thread(
        self,
        scanner,
        path: str,
        quick_scan: bool = False,
        scan_options: dict[str, Any] | None = None,
    ) -> "UnifiedScanThread":
        """Create a new unified scan thread."""
        if not HAS_PYQT6:
            raise RuntimeError("PyQt6 not available for GUI thread creation")

        thread = UnifiedScanThread(scanner, path, quick_scan, scan_options)
        self.logger.debug(f"Created scan thread for path: {path}")
        return thread

    # ==========================================================================
    # Resource Management
    # ==========================================================================

    @asynccontextmanager
    async def acquire_resource(
        self, resource_type: ResourceType, operation_id: str | None = None
    ):
        """Context manager for resource acquisition."""
        async with self.resource_coordinator.acquire_resource(
            resource_type, operation_id
        ):
            yield

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage statistics."""
        return self.resource_coordinator.get_resource_usage()

    # ==========================================================================
    # Metrics and Monitoring
    # ==========================================================================

    async def _update_task_metrics(self, success: bool, duration: float):
        """Update async task metrics."""
        with self._metrics_lock:
            self.metrics.total_async_tasks += 1
            if success:
                self.metrics.completed_tasks += 1
            else:
                self.metrics.failed_tasks += 1

            # Update average duration
            total_completed = self.metrics.completed_tasks
            if total_completed > 0:
                current_avg = self.metrics.average_task_duration
                self.metrics.average_task_duration = (
                    current_avg * (total_completed - 1) + duration
                ) / total_completed

            self.metrics.last_updated = datetime.utcnow()

    def _update_thread_task_metrics(self, success: bool, duration: float):
        """Update thread task metrics."""
        with self._metrics_lock:
            self.metrics.total_thread_tasks += 1
            if success:
                self.metrics.completed_tasks += 1
            else:
                self.metrics.failed_tasks += 1

            self.metrics.last_updated = datetime.utcnow()

    def _record_cancellation_metric(self, metric: CancellationMetric):
        """Record a cancellation metric."""
        with self._metrics_lock:
            self._cancellation_metrics.append(metric)
            self.metrics.cancelled_tasks += 1

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        with self._metrics_lock:
            return self.metrics

    def get_cancellation_metrics(self) -> list[CancellationMetric]:
        """Get all cancellation metrics."""
        with self._metrics_lock:
            return list(self._cancellation_metrics)

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    async def wait_for_completion(self, timeout: float | None = None):
        """Wait for all active tasks to complete."""
        async_tasks = list(self.active_async_tasks)

        if async_tasks:
            if timeout:
                await asyncio.wait_for(
                    asyncio.gather(*async_tasks, return_exceptions=True),
                    timeout=timeout,
                )
            else:
                await asyncio.gather(*async_tasks, return_exceptions=True)

    def get_active_task_count(self) -> dict[str, int]:
        """Get count of active tasks by type."""
        return {
            "async_tasks": len(self.active_async_tasks),
            "thread_tasks": len(self.active_thread_tasks),
            "total": len(self.active_async_tasks) + len(self.active_thread_tasks),
        }


# =============================================================================
# Global Manager Instance and Convenience Functions
# =============================================================================

_global_threading_manager: UnifiedThreadingManager | None = None


def get_threading_manager() -> UnifiedThreadingManager:
    """Get the global unified threading manager instance."""
    global _global_threading_manager
    if _global_threading_manager is None:
        _global_threading_manager = UnifiedThreadingManager()
    return _global_threading_manager


def get_resource_coordinator() -> AsyncResourceCoordinator:
    """Get the global resource coordinator instance."""
    return get_threading_manager().resource_coordinator


# Convenience functions for common operations
async def with_resource(resource_type: ResourceType, operation_id: str | None = None):
    """Context manager for resource acquisition."""
    manager = get_threading_manager()
    async with manager.acquire_resource(resource_type, operation_id):
        yield


def with_file_resource(operation_id: str | None = None):
    """Context manager for file I/O operations."""
    return with_resource(ResourceType.FILE_IO, operation_id)


def with_threat_analysis_resource(operation_id: str | None = None):
    """Context manager for threat analysis operations."""
    return with_resource(ResourceType.THREAT_ANALYSIS, operation_id)


def with_ml_resource(operation_id: str | None = None):
    """Context manager for ML computation operations."""
    return with_resource(ResourceType.ML_COMPUTATION, operation_id)


# Legacy compatibility functions
async def async_scan_directory(scanner, directory_path: str, recursive: bool = True):
    """Legacy compatibility function for async directory scanning."""
    manager = get_threading_manager()
    task_request = AsyncTaskRequest(
        task_id=f"scan_dir_{id(scanner)}",
        priority=TaskPriority.NORMAL,
        coro=scanner.scan_directory_async(directory_path, recursive),
        resource_type=ResourceType.SCAN_OPERATION,
    )
    return await manager.submit_async_task(task_request)


# =============================================================================
# Export List
# =============================================================================

__all__ = [
    # Core Classes
    "AsyncResourceCoordinator",
    "CooperativeCancellationMixin",
    "UnifiedScanThread",
    "UnifiedThreadingManager",
    # Data Classes
    "AsyncTaskRequest",
    "CancellationMetric",
    "PerformanceMetrics",
    "ResourceLimits",
    "ResourceType",
    "ResourceUsage",
    "TaskPriority",
    "ThreadPoolType",
    "ThreadTaskRequest",
    # Context Managers
    "ResourceContext",
    # Global Functions
    "get_resource_coordinator",
    "get_threading_manager",
    "with_file_resource",
    "with_ml_resource",
    "with_resource",
    "with_threat_analysis_resource",
    # Legacy Compatibility
    "async_scan_directory",
]
