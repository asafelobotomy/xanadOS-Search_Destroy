#!/usr/bin/env python3
"""Unified Scanner Engine for xanadOS Search & Destroy

This module consolidates all scanning functionality into a unified, high-performance
async engine with comprehensive features:

- High-performance async scanning with priority queues
- Intelligent resource management and I/O optimization
- Comprehensive quarantine management system
- Real-time progress tracking and statistics
- Memory-efficient file processing with caching
- Flexible configuration and batch processing

Consolidates functionality from:
- file_scanner.py (quarantine management, synchronous scanning)
- async_scanner.py (basic async scanning, progress tracking)
- async_scanner_engine.py (async engine, configuration)
- advanced_async_scanner.py (priority scheduling, optimization)
"""

import asyncio
import fnmatch
import gc
import hashlib
import json
import logging
import mmap
import os
import shutil
import time
from collections import deque
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os
import psutil

# Internal imports
from app.utils.config import get_config
from app.utils.scan_reports import ThreatLevel

from .adaptive_worker_pool import AdaptiveWorkerPool, WorkerPoolMetrics
from .advanced_io import AdvancedIOManager, IOConfig, IOStrategy
from .clamav_wrapper import ClamAVWrapper, ScanResult
from .input_validation import SecurityValidationError
from .rate_limiting import configure_rate_limits, rate_limit_manager

# Optional dependencies
try:
    import schedule  # type: ignore

    _SCHED_AVAILABLE = True
except Exception:
    schedule = None  # type: ignore
    _SCHED_AVAILABLE = False

try:
    from .async_threat_detector import AsyncThreatDetector
    from .async_resource_coordinator import get_resource_coordinator, ResourceType

    _ADVANCED_FEATURES = True
except Exception:
    _ADVANCED_FEATURES = False

# Note: File system monitoring is now in app/monitoring/file_watcher.py
# with integrated async support via enable_async_mode()

try:
    from .ml_threat_detector import get_threat_detector
    from .unified_security_engine import (
        SecurityEvent,
        ThreatLevel as SecurityThreatLevel,
    )

    _ML_AVAILABLE = True
except Exception:
    _ML_AVAILABLE = False


# Configure logging
logger = logging.getLogger(__name__)


# ================== ENUMS AND DATA STRUCTURES ==================


class ScanType(Enum):
    """Types of scans available."""

    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    REAL_TIME = "real_time"
    SCHEDULED = "scheduled"


class ScanStatus(Enum):
    """Scan status values."""

    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    SCANNING = "scanning"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class ScanPriority(Enum):
    """Scan priority levels for intelligent scheduling."""

    CRITICAL = 1  # System files, executables
    HIGH = 2  # User documents, downloads
    MEDIUM = 3  # Media files, archives
    LOW = 4  # Temporary files, cache
    BACKGROUND = 5  # Bulk operations


class QuarantineAction(Enum):
    """Actions that can be taken on quarantined files."""

    QUARANTINE = "quarantine"
    DELETE = "delete"
    RESTORE = "restore"
    IGNORE = "ignore"
    CLEAN = "clean"


@dataclass
class ScanConfiguration:
    """Configuration for a scan operation."""

    scan_type: ScanType
    target_paths: list[str]
    exclusions: list[str] | None = None
    max_file_size: int = 100 * 1024 * 1024  # 100MB default
    follow_symlinks: bool = False
    scan_archives: bool = True
    scan_compressed: bool = True
    deep_scan: bool = False
    priority: ScanPriority = ScanPriority.MEDIUM
    timeout: int = 3600  # 1 hour default
    quarantine_action: QuarantineAction = QuarantineAction.QUARANTINE


@dataclass
class ScanStatistics:
    """Statistics for a scan operation."""

    total_files: int = 0
    completed_files: int = 0
    infected_files: int = 0
    clean_files: int = 0
    errors: int = 0
    quarantined_files: int = 0
    bytes_scanned: int = 0
    scan_duration: float = 0.0
    throughput_fps: float = 0.0  # files per second
    throughput_bps: float = 0.0  # bytes per second


@dataclass
class ScanProgress:
    """Represents scan progress information."""

    total_files: int = 0
    completed_files: int = 0
    infected_files: int = 0
    errors: int = 0
    current_file: str = ""
    start_time: datetime | None = None
    estimated_completion: datetime | None = None
    throughput_fps: float = 0.0
    memory_usage_mb: float = 0.0

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100.0


@dataclass
class ScanBatch:
    """Represents a batch of files to scan."""

    files: list[str]
    batch_id: str
    priority: ScanPriority = ScanPriority.MEDIUM
    config: ScanConfiguration | None = None


@dataclass
class ScanRequest:
    """Represents a scan request with metadata."""

    file_path: str
    priority: ScanPriority
    timestamp: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class UnifiedScanResult:
    """Comprehensive scan result combining all scanner features."""

    file_path: str
    scan_id: str
    is_infected: bool
    threat_name: str = ""
    threat_level: ThreatLevel = ThreatLevel.CLEAN
    scan_duration: float = 0.0
    file_size: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    quarantine_path: str = ""
    action_taken: QuarantineAction = QuarantineAction.IGNORE
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass
class QuarantinedFile:
    """Represents a file in quarantine."""

    original_path: str
    quarantine_path: str
    threat_name: str
    timestamp: datetime
    file_size: int
    checksum: str
    quarantine_id: str


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics."""

    io_operations: int = 0
    memory_peak_mb: float = 0.0
    cpu_peak_percent: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    optimization_ratio: float = 0.0

    # Advanced I/O metrics
    io_throughput_mbps: float = 0.0
    io_strategy_usage: dict[str, int] = field(default_factory=dict)
    total_bytes_read: int = 0


# ================== MEMORY AND RESOURCE MANAGEMENT ==================


class MemoryMonitor:
    """Monitor and optimize memory usage during scanning operations."""

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = self.get_memory_usage()
        self.peak_memory = self.start_memory
        self.logger = logging.getLogger(__name__)

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def check_memory_pressure(self) -> bool:
        """Check if memory usage is too high."""
        current = self.get_memory_usage()
        self.peak_memory = max(self.peak_memory, current)

        # Trigger cleanup if using more than 80% of available memory
        available_memory = psutil.virtual_memory().available / 1024 / 1024
        return current > (available_memory * 0.8)

    def optimize_memory(self) -> None:
        """Optimize memory usage by triggering garbage collection."""
        if self.check_memory_pressure():
            self.logger.warning(
                f"High memory usage detected: {self.get_memory_usage():.1f}MB"
            )
            gc.collect()


class ResourceMonitor:
    """Monitor system resources during scanning."""

    def __init__(self):
        self.start_time = time.time()
        self.metrics = PerformanceMetrics()

    def update_metrics(self) -> None:
        """Update performance metrics."""
        self.metrics.memory_peak_mb = max(
            self.metrics.memory_peak_mb,
            psutil.Process().memory_info().rss / 1024 / 1024,
        )
        self.metrics.cpu_peak_percent = max(
            self.metrics.cpu_peak_percent, psutil.cpu_percent()
        )

    def should_throttle(self) -> bool:
        """Determine if scanning should be throttled."""
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent

        return cpu_usage > 90 or memory_usage > 85


# ================== I/O OPTIMIZATION ==================


class IOOptimizer:
    """Optimizes I/O operations for different file types and sizes."""

    def __init__(self):
        self.config = get_config()
        self.read_buffer_size = 64 * 1024  # 64KB default
        self.mmap_threshold = 10 * 1024 * 1024  # 10MB threshold for memory mapping

    def get_optimal_read_size(self, file_size: int) -> int:
        """Determine optimal read buffer size based on file size."""
        if file_size < 1024:  # < 1KB
            return file_size
        elif file_size < 64 * 1024:  # < 64KB
            return 4 * 1024  # 4KB
        elif file_size < 1024 * 1024:  # < 1MB
            return 16 * 1024  # 16KB
        else:
            return self.read_buffer_size

    def should_use_mmap(self, file_size: int) -> bool:
        """Determine if memory mapping should be used."""
        return file_size > self.mmap_threshold

    async def read_file_optimized(self, file_path: Path) -> bytes:
        """Read file with optimized I/O strategy."""
        file_size = file_path.stat().st_size

        if self.should_use_mmap(file_size):
            return await self._read_with_mmap(file_path)
        else:
            return await self._read_with_aiofiles(file_path, file_size)

    async def _read_with_mmap(self, file_path: Path) -> bytes:
        """Read large file using memory mapping."""
        loop = asyncio.get_event_loop()

        def _mmap_read():
            with open(file_path, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    return mm.read()

        return await loop.run_in_executor(None, _mmap_read)

    async def _read_with_aiofiles(self, file_path: Path, file_size: int) -> bytes:
        """Read file using async I/O."""
        buffer_size = self.get_optimal_read_size(file_size)

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read(buffer_size)


# ================== CACHING SYSTEM ==================


@dataclass
class CacheEntry:
    """Cache entry for scan results."""

    result: UnifiedScanResult
    timestamp: datetime
    access_count: int = 0

    def is_expired(self, max_age: timedelta = timedelta(hours=24)) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - self.timestamp > max_age


class ScanCache:
    """Intelligent caching system for scan results."""

    def __init__(self, max_size: int = 10000):
        self.cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.access_order = deque()
        self.lock = asyncio.Lock()

    async def get(self, file_hash: str) -> UnifiedScanResult | None:
        """Get cached scan result."""
        async with self.lock:
            if file_hash in self.cache:
                entry = self.cache[file_hash]
                if not entry.is_expired():
                    entry.access_count += 1
                    # Move to end (most recently used)
                    self.access_order.remove(file_hash)
                    self.access_order.append(file_hash)
                    return entry.result
                else:
                    # Remove expired entry
                    del self.cache[file_hash]
                    self.access_order.remove(file_hash)
            return None

    async def put(self, file_hash: str, result: UnifiedScanResult) -> None:
        """Cache scan result."""
        async with self.lock:
            # Remove oldest entries if cache is full
            while len(self.cache) >= self.max_size:
                oldest = self.access_order.popleft()
                del self.cache[oldest]

            self.cache[file_hash] = CacheEntry(result=result, timestamp=datetime.now())
            self.access_order.append(file_hash)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_access = sum(entry.access_count for entry in self.cache.values())
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_accesses": total_access,
            "hit_ratio": total_access / max(1, len(self.cache)),
        }


# ================== QUARANTINE MANAGEMENT ==================


class QuarantineManager:
    """Manages quarantined files with secure storage and tracking."""

    def __init__(self, quarantine_dir: str | None = None, io_manager=None):
        self.config = get_config()
        self.quarantine_dir = Path(
            quarantine_dir or self.config.get("quarantine_dir", "/tmp/quarantine")
        )
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.quarantine_dir / "quarantine_index.json"
        self.logger = logging.getLogger(__name__)
        self._quarantined_files: dict[str, QuarantinedFile] = {}
        self.io_manager = io_manager  # Will be set by UnifiedScannerEngine
        self._load_index()

    def _load_index(self) -> None:
        """Load quarantine index from disk."""
        try:
            if self.index_file.exists():
                with open(self.index_file) as f:
                    data = json.load(f)
                    for item in data:
                        qf = QuarantinedFile(**item)
                        self._quarantined_files[qf.quarantine_id] = qf
        except Exception as e:
            self.logger.error(f"Failed to load quarantine index: {e}")

    def _save_index(self) -> None:
        """Save quarantine index to disk."""
        try:
            data = [asdict(qf) for qf in self._quarantined_files.values()]
            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save quarantine index: {e}")

    async def quarantine_file(self, file_path: str, threat_name: str) -> str:
        """Quarantine a file and return the quarantine ID."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")

            # Generate unique quarantine ID using secure hash
            quarantine_id = f"q_{int(time.time())}_{hashlib.sha256(file_path.encode()).hexdigest()[:16]}"
            quarantine_path = self.quarantine_dir / quarantine_id

            # Calculate file checksum
            checksum = await self._calculate_checksum(source_path)

            # Move file to quarantine
            shutil.move(str(source_path), str(quarantine_path))

            # Create quarantine record
            quarantined_file = QuarantinedFile(
                original_path=file_path,
                quarantine_path=str(quarantine_path),
                threat_name=threat_name,
                timestamp=datetime.now(),
                file_size=quarantine_path.stat().st_size,
                checksum=checksum,
                quarantine_id=quarantine_id,
            )

            self._quarantined_files[quarantine_id] = quarantined_file
            self._save_index()

            self.logger.info(f"File quarantined: {file_path} -> {quarantine_id}")
            return quarantine_id

        except Exception as e:
            self.logger.error(f"Failed to quarantine file {file_path}: {e}")
            raise

    async def restore_file(self, quarantine_id: str) -> bool:
        """Restore a quarantined file to its original location."""
        try:
            if quarantine_id not in self._quarantined_files:
                return False

            qf = self._quarantined_files[quarantine_id]
            quarantine_path = Path(qf.quarantine_path)
            original_path = Path(qf.original_path)

            if not quarantine_path.exists():
                self.logger.error(f"Quarantined file not found: {quarantine_path}")
                return False

            # Ensure target directory exists
            original_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file back
            shutil.move(str(quarantine_path), str(original_path))

            # Remove from index
            del self._quarantined_files[quarantine_id]
            self._save_index()

            self.logger.info(f"File restored: {quarantine_id} -> {qf.original_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore file {quarantine_id}: {e}")
            return False

    async def delete_quarantined_file(self, quarantine_id: str) -> bool:
        """Permanently delete a quarantined file."""
        try:
            if quarantine_id not in self._quarantined_files:
                return False

            qf = self._quarantined_files[quarantine_id]
            quarantine_path = Path(qf.quarantine_path)

            if quarantine_path.exists():
                quarantine_path.unlink()

            del self._quarantined_files[quarantine_id]
            self._save_index()

            self.logger.info(f"Quarantined file deleted: {quarantine_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete quarantined file {quarantine_id}: {e}")
            return False

    def list_quarantined_files(self) -> list[QuarantinedFile]:
        """Get list of all quarantined files."""
        return list(self._quarantined_files.values())

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum using advanced I/O."""
        hasher = hashlib.sha256()

        # Use chunked reading for memory efficiency on large files
        async for chunk in self.io_manager.scan_file_chunks(file_path):
            hasher.update(chunk)

        return hasher.hexdigest()


# ================== MAIN UNIFIED SCANNER ENGINE ==================


class UnifiedScannerEngine:
    """Unified, high-performance async scanner engine with comprehensive features."""

    def __init__(self, config: ScanConfiguration | None = None):
        self.config = config or ScanConfiguration(
            scan_type=ScanType.QUICK,
            target_paths=[],
        )
        self.logger = logging.getLogger(__name__)

        # Core components
        self.clamav = ClamAVWrapper()
        self.memory_monitor = MemoryMonitor()
        self.resource_monitor = ResourceMonitor()
        self.io_optimizer = IOOptimizer()
        self.scan_cache = ScanCache()

        # Advanced I/O system with automatic strategy selection (create before quarantine manager)
        io_config = IOConfig(
            chunk_size=(
                config.chunk_size if hasattr(config, "chunk_size") else 256 * 1024
            ),
            max_concurrent_ops=(
                config.max_workers if hasattr(config, "max_workers") else 20
            ),
            strategy=IOStrategy.AUTO,  # Automatic selection based on file size
        )
        self.io_manager = AdvancedIOManager(io_config)
        self.logger.info(
            f"Advanced I/O initialized: chunk_size={io_config.chunk_size}, "
            f"max_concurrent={io_config.max_concurrent_ops}, strategy={io_config.strategy.name}"
        )

        # Quarantine manager (needs io_manager for checksums)
        self.quarantine_manager = QuarantineManager(io_manager=self.io_manager)

        # Progress tracking
        self.progress = ScanProgress()
        self.statistics = ScanStatistics()
        self.status = ScanStatus.NOT_STARTED

        # Adaptive worker pool for I/O-bound file scanning
        self.adaptive_pool = AdaptiveWorkerPool(
            min_workers=None,  # Use auto-calculated defaults
            max_workers=None,
            adjustment_interval=5.0,  # Adjust every 5 seconds
            enable_monitoring=True,
        )

        # Threading and concurrency with adaptive pool
        initial_workers = self.adaptive_pool.current_workers
        self.executor = ThreadPoolExecutor(max_workers=initial_workers)
        self.adaptive_pool.set_executor(self.executor)

        self.scan_queue: asyncio.Queue[ScanRequest] = asyncio.Queue()
        self.adaptive_pool.set_task_queue(self.scan_queue)

        self.active_scans: set[asyncio.Task] = set()
        self.scan_semaphore = asyncio.Semaphore(10)  # Limit concurrent scans

        self.logger.info(
            f"Initialized with adaptive worker pool: {initial_workers} workers "
            f"(min: {self.adaptive_pool.min_workers}, max: {self.adaptive_pool.max_workers})"
        )

        # Event handling
        self.progress_callbacks: list[Callable[[ScanProgress], None]] = []
        self.result_callbacks: list[Callable[[UnifiedScanResult], None]] = []

        # Cancel token
        self._cancel_event = asyncio.Event()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize the scanner engine."""
        self.logger.info("Initializing Unified Scanner Engine")
        self.status = ScanStatus.INITIALIZING

        # Initialize ClamAV
        if not await self._initialize_clamav():
            self.logger.warning(
                "ClamAV initialization failed, continuing without virus scanning"
            )

        # Start background tasks
        asyncio.create_task(self._process_scan_queue())
        asyncio.create_task(self._adaptive_pool_monitor())

        self.status = ScanStatus.NOT_STARTED
        self.logger.info("Scanner engine initialized successfully")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.logger.info("Cleaning up scanner engine")

        # Cancel all active scans
        await self.cancel_scan()

        # Wait for active scans to complete
        if self.active_scans:
            await asyncio.gather(*self.active_scans, return_exceptions=True)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        self.logger.info("Scanner engine cleanup complete")

    async def _initialize_clamav(self) -> bool:
        """Initialize ClamAV wrapper."""
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self.clamav.initialize)
        except Exception as e:
            self.logger.error(f"ClamAV initialization failed: {e}")
            return False

    # Progress and callback management
    def add_progress_callback(self, callback: Callable[[ScanProgress], None]) -> None:
        """Add a progress callback."""
        self.progress_callbacks.append(callback)

    def add_result_callback(
        self, callback: Callable[[UnifiedScanResult], None]
    ) -> None:
        """Add a result callback."""
        self.result_callbacks.append(callback)

    def _notify_progress(self) -> None:
        """Notify progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")

    def _notify_result(self, result: UnifiedScanResult) -> None:
        """Notify result callbacks."""
        for callback in self.result_callbacks:
            try:
                callback(result)
            except Exception as e:
                self.logger.error(f"Result callback error: {e}")

    # Main scanning methods
    async def scan_file(
        self, file_path: str, priority: ScanPriority = ScanPriority.MEDIUM
    ) -> UnifiedScanResult:
        """Scan a single file."""
        request = ScanRequest(file_path=file_path, priority=priority)

        await self.scan_queue.put(request)

        # Wait for result (simplified for single file)
        # In a full implementation, this would use a result queue or callback
        return await self._scan_file_internal(request)

    async def scan_directory(
        self, directory_path: str, recursive: bool = True
    ) -> AsyncIterator[UnifiedScanResult]:
        """Scan a directory and yield results."""
        self.status = ScanStatus.SCANNING
        self.progress.start_time = datetime.now()

        try:
            # Collect files to scan
            files_to_scan = await self._collect_files(directory_path, recursive)
            self.progress.total_files = len(files_to_scan)

            # Create scan requests
            for file_path in files_to_scan:
                priority = self._determine_file_priority(file_path)
                request = ScanRequest(file_path=file_path, priority=priority)
                await self.scan_queue.put(request)

            # Process results
            async for result in self._process_scan_results():
                yield result

        except Exception as e:
            self.logger.error(f"Directory scan error: {e}")
            self.status = ScanStatus.ERROR
            raise
        finally:
            self.status = ScanStatus.COMPLETED

    async def scan_batch(self, batch: ScanBatch) -> list[UnifiedScanResult]:
        """Scan a batch of files."""
        results = []

        for file_path in batch.files:
            request = ScanRequest(file_path=file_path, priority=batch.priority)
            result = await self._scan_file_internal(request)
            results.append(result)

        return results

    # Internal scanning implementation
    async def _scan_file_internal(self, request: ScanRequest) -> UnifiedScanResult:
        """Internal file scanning implementation."""
        file_path = request.file_path
        start_time = time.time()

        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return UnifiedScanResult(
                    file_path=file_path,
                    scan_id=self._generate_scan_id(),
                    is_infected=False,
                    error_message="File not found",
                )

            # Check cache first
            file_hash = await self._calculate_file_hash(path_obj)
            cached_result = await self.scan_cache.get(file_hash)
            if cached_result:
                return cached_result

            # Perform actual scan
            file_size = path_obj.stat().st_size
            scan_result = await self._perform_virus_scan(path_obj)

            # Create unified result
            result = UnifiedScanResult(
                file_path=file_path,
                scan_id=self._generate_scan_id(),
                is_infected=scan_result.is_infected,
                threat_name=scan_result.virus_name,
                threat_level=(
                    ThreatLevel.HIGH if scan_result.is_infected else ThreatLevel.CLEAN
                ),
                scan_duration=time.time() - start_time,
                file_size=file_size,
                metadata={
                    "file_hash": file_hash,
                    "clamav_result": (
                        scan_result.__dict__
                        if hasattr(scan_result, "__dict__")
                        else str(scan_result)
                    ),
                },
            )

            # Handle infected files
            if result.is_infected:
                await self._handle_infected_file(result)

            # Cache result
            await self.scan_cache.put(file_hash, result)

            # Update progress
            self.progress.completed_files += 1
            if result.is_infected:
                self.progress.infected_files += 1
            self._notify_progress()
            self._notify_result(result)

            # Record task time for adaptive pool performance tracking
            self.adaptive_pool.record_task_time(result.scan_duration)

            return result

        except Exception as e:
            self.logger.error(f"Error scanning file {file_path}: {e}")
            return UnifiedScanResult(
                file_path=file_path,
                scan_id=self._generate_scan_id(),
                is_infected=False,
                error_message=str(e),
                scan_duration=time.time() - start_time,
            )

    async def _perform_virus_scan(self, file_path: Path) -> ScanResult:
        """Perform virus scan using ClamAV with advanced I/O."""
        # Use advanced I/O manager to read file with optimal strategy
        # (ASYNC for small files, MMAP for large files, BUFFERED for medium)
        file_data = await self.io_manager.read_file_async(file_path)

        # Scan the file data in executor to avoid blocking
        loop = asyncio.get_event_loop()

        def _scan():
            return self.clamav.scan_data(file_data, str(file_path))

        return await loop.run_in_executor(self.executor, _scan)

    async def _handle_infected_file(self, result: UnifiedScanResult) -> None:
        """Handle infected file according to configuration."""
        action = self.config.quarantine_action

        try:
            if action == QuarantineAction.QUARANTINE:
                quarantine_id = await self.quarantine_manager.quarantine_file(
                    result.file_path, result.threat_name
                )
                result.quarantine_path = quarantine_id
                result.action_taken = QuarantineAction.QUARANTINE
                self.logger.info(
                    f"File quarantined: {result.file_path} -> {quarantine_id}"
                )

            elif action == QuarantineAction.DELETE:
                Path(result.file_path).unlink()
                result.action_taken = QuarantineAction.DELETE
                self.logger.info(f"Infected file deleted: {result.file_path}")

            elif action == QuarantineAction.IGNORE:
                result.action_taken = QuarantineAction.IGNORE
                self.logger.info(f"Infected file ignored: {result.file_path}")

        except Exception as e:
            self.logger.error(f"Failed to handle infected file {result.file_path}: {e}")
            result.error_message = f"Action failed: {e}"

    # Helper methods
    async def _collect_files(self, directory_path: str, recursive: bool) -> list[str]:
        """Collect files to scan from directory."""
        files = []
        path_obj = Path(directory_path)

        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"

        for file_path in path_obj.glob(pattern):
            if file_path.is_file():
                # Check exclusions
                if not self._is_excluded(str(file_path)):
                    files.append(str(file_path))

        return files

    def _is_excluded(self, file_path: str) -> bool:
        """Check if file should be excluded from scanning."""
        if not self.config.exclusions:
            return False

        for pattern in self.config.exclusions:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _determine_file_priority(self, file_path: str) -> ScanPriority:
        """Determine scan priority based on file characteristics."""
        path_obj = Path(file_path)

        # System files and executables get high priority
        if path_obj.suffix.lower() in [".exe", ".dll", ".so", ".dylib"]:
            return ScanPriority.CRITICAL

        # Documents and downloads get high priority
        if any(
            part in str(path_obj).lower()
            for part in ["download", "desktop", "documents"]
        ):
            return ScanPriority.HIGH

        # Media files get medium priority
        if path_obj.suffix.lower() in [".mp3", ".mp4", ".avi", ".jpg", ".png"]:
            return ScanPriority.MEDIUM

        # Temporary files get low priority
        if any(part in str(path_obj).lower() for part in ["temp", "tmp", "cache"]):
            return ScanPriority.LOW

        return ScanPriority.MEDIUM

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for caching."""
        hasher = hashlib.sha256()

        # Include file path, size, and mtime in hash for cache invalidation
        stat = file_path.stat()
        hasher.update(str(file_path).encode())
        hasher.update(str(stat.st_size).encode())
        hasher.update(str(stat.st_mtime).encode())

        return hasher.hexdigest()

    def _generate_scan_id(self) -> str:
        """Generate unique scan ID."""
        return f"scan_{int(time.time() * 1000)}_{os.getpid()}"

    # Queue processing
    async def _process_scan_queue(self) -> None:
        """Background task to process scan queue."""
        while not self._cancel_event.is_set():
            try:
                # Wait for scan request with timeout
                request = await asyncio.wait_for(self.scan_queue.get(), timeout=1.0)

                # Process request with semaphore
                async with self.scan_semaphore:
                    task = asyncio.create_task(self._scan_file_internal(request))
                    self.active_scans.add(task)

                    try:
                        await task
                    finally:
                        self.active_scans.discard(task)

            except TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing scan queue: {e}")

    async def _adaptive_pool_monitor(self) -> None:
        """Background task to monitor and adjust worker pool."""
        self.logger.info("Starting adaptive worker pool monitoring")

        while not self._cancel_event.is_set():
            try:
                # Sleep for adjustment interval
                await asyncio.sleep(self.adaptive_pool.adjustment_interval)

                # Attempt to adjust workers
                adjusted = self.adaptive_pool.adjust_workers()

                # Log metrics periodically (every 30 seconds)
                if int(time.time()) % 30 == 0:
                    status = self.adaptive_pool.get_status_dict()
                    self.logger.info(
                        f"Adaptive pool status: {status['current_workers']} workers, "
                        f"{status['total_adjustments']} adjustments "
                        f"(↑{status['scale_ups']}, ↓{status['scale_downs']}), "
                        f"Performance gain: {status['performance_gain_percent']}%"
                    )

            except asyncio.CancelledError:
                self.logger.info("Adaptive pool monitoring cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in adaptive pool monitoring: {e}")
                await asyncio.sleep(5.0)  # Back off on error

        self.logger.info("Adaptive worker pool monitoring stopped")

    async def _process_scan_results(self) -> AsyncIterator[UnifiedScanResult]:
        """Process and yield scan results."""
        # Simplified implementation - in practice would use result queues
        while self.progress.completed_files < self.progress.total_files:
            await asyncio.sleep(0.1)  # Wait for progress
            # Yield results as they become available
            # This is a placeholder - full implementation would track results

    # Control methods
    async def cancel_scan(self) -> None:
        """Cancel ongoing scan operations."""
        self.logger.info("Cancelling scan operations")
        self._cancel_event.set()
        self.status = ScanStatus.CANCELLED

        # Cancel all active tasks
        for task in self.active_scans:
            task.cancel()

    async def pause_scan(self) -> None:
        """Pause scanning operations."""
        self.status = ScanStatus.PAUSED
        # Implementation would pause queue processing

    async def resume_scan(self) -> None:
        """Resume scanning operations."""
        if self.status == ScanStatus.PAUSED:
            self.status = ScanStatus.SCANNING
            # Implementation would resume queue processing

    # Statistics and reporting
    def get_scan_statistics(self) -> ScanStatistics:
        """Get current scan statistics."""
        if self.progress.start_time:
            self.statistics.scan_duration = (
                datetime.now() - self.progress.start_time
            ).total_seconds()

        if self.statistics.scan_duration > 0:
            self.statistics.throughput_fps = (
                self.progress.completed_files / self.statistics.scan_duration
            )

        return self.statistics

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics including I/O statistics."""
        self.resource_monitor.update_metrics()

        cache_stats = self.scan_cache.get_cache_stats()
        self.resource_monitor.metrics.cache_hits = cache_stats.get("total_accesses", 0)

        # Add I/O metrics from AdvancedIOManager (use correct property name)
        io_metrics = self.io_manager.metrics  # Use metrics property
        self.resource_monitor.metrics.io_throughput_mbps = (
            io_metrics.avg_throughput_mbps
        )  # Property
        self.resource_monitor.metrics.total_bytes_read = io_metrics.total_bytes_read
        self.resource_monitor.metrics.io_strategy_usage = io_metrics.strategy_usage

        return self.resource_monitor.metrics


# ================== CONVENIENCE FUNCTIONS ==================


def create_quick_scan_config(target_paths: list[str]) -> ScanConfiguration:
    """Create configuration for quick scan."""
    return ScanConfiguration(
        scan_type=ScanType.QUICK,
        target_paths=target_paths,
        scan_archives=False,
        deep_scan=False,
        priority=ScanPriority.HIGH,
    )


def create_full_scan_config(target_paths: list[str]) -> ScanConfiguration:
    """Create configuration for full system scan."""
    return ScanConfiguration(
        scan_type=ScanType.FULL,
        target_paths=target_paths,
        scan_archives=True,
        scan_compressed=True,
        deep_scan=True,
        priority=ScanPriority.MEDIUM,
        timeout=7200,  # 2 hours
    )


def create_custom_scan_config(
    target_paths: list[str],
    exclusions: list[str] | None = None,
    priority: ScanPriority = ScanPriority.MEDIUM,
    **kwargs,
) -> ScanConfiguration:
    """Create custom scan configuration."""
    return ScanConfiguration(
        scan_type=ScanType.CUSTOM,
        target_paths=target_paths,
        exclusions=exclusions,
        priority=priority,
        **kwargs,
    )


# Module-level instance
_scanner_instance: UnifiedScannerEngine | None = None


def get_unified_scanner(
    config: ScanConfiguration | None = None,
) -> UnifiedScannerEngine:
    """Get unified scanner instance (singleton pattern)."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = UnifiedScannerEngine(config)
    return _scanner_instance


# Legacy compatibility aliases (will be used in shims)
AsyncFileScanner = UnifiedScannerEngine
AsyncScannerEngine = UnifiedScannerEngine
AdvancedAsyncScanner = UnifiedScannerEngine
FileScanner = UnifiedScannerEngine  # For synchronous compatibility


async def get_async_scanner() -> UnifiedScannerEngine:
    """Get async scanner instance (compatibility)."""
    return get_unified_scanner()


def get_scanner() -> UnifiedScannerEngine:
    """Get scanner instance (compatibility)."""
    return get_unified_scanner()
