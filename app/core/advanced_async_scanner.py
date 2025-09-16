#!/usr/bin/env python3
"""Advanced Async Scanning Engine for xanadOS Search & Destroy.

This module implements high-performance async scanning with:
- Intelligent I/O scheduling and prioritization
- Resource-aware adaptive scanning
- Parallel processing optimization
- Memory-efficient file handling
- Real-time performance monitoring

Features:
- Priority-based scan queue management
- Adaptive worker pool scaling
- I/O optimization for different file types
- Memory-mapped file processing for large files
- Intelligent caching and batching
- Resource usage monitoring and throttling
"""

import asyncio
import logging
import mmap
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import aiofiles
import psutil

from app.core.clamav_wrapper import ClamAVWrapper
from app.core.ml_threat_detector import get_threat_detector
from app.core.unified_security_engine import SecurityEvent, ThreatLevel
from app.utils.config import get_config


class ScanPriority(Enum):
    """Scan priority levels for intelligent scheduling."""

    CRITICAL = 1    # System files, executables
    HIGH = 2        # User documents, downloads
    MEDIUM = 3      # Media files, archives
    LOW = 4         # Temporary files, cache
    BACKGROUND = 5  # Bulk operations


class ScanType(Enum):
    """Types of scans supported."""

    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    REALTIME = "realtime"
    DEEP = "deep"


@dataclass
class ScanRequest:
    """Scan request with priority and metadata."""

    path: Path
    scan_type: ScanType
    priority: ScanPriority
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    estimated_size: int = 0

    def __lt__(self, other):
        """Priority comparison for queue ordering."""
        return self.priority.value < other.priority.value


@dataclass
class ScanResult:
    """Comprehensive scan result."""

    path: Path
    scan_type: ScanType
    threat_level: ThreatLevel
    scan_time: float
    file_size: int
    threats_found: List[str]
    ml_assessment: Optional[Any] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Real-time performance tracking."""

    files_scanned: int = 0
    bytes_scanned: int = 0
    scan_time_total: float = 0.0
    average_scan_time: float = 0.0
    throughput_mbps: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    io_wait_time: float = 0.0
    cache_hit_ratio: float = 0.0


class IOOptimizer:
    """Intelligent I/O optimization for different file types."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.file_type_cache = {}
        self.optimal_chunk_sizes = {
            'small': 64 * 1024,      # 64KB for small files
            'medium': 256 * 1024,    # 256KB for medium files
            'large': 1024 * 1024,    # 1MB for large files
            'huge': 4 * 1024 * 1024, # 4MB for huge files
        }

    def get_optimal_chunk_size(self, file_size: int) -> int:
        """Determine optimal chunk size based on file size."""
        if file_size < 1024 * 1024:  # < 1MB
            return self.optimal_chunk_sizes['small']
        elif file_size < 10 * 1024 * 1024:  # < 10MB
            return self.optimal_chunk_sizes['medium']
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return self.optimal_chunk_sizes['large']
        else:
            return self.optimal_chunk_sizes['huge']

    def should_use_memory_mapping(self, file_size: int) -> bool:
        """Determine if memory mapping should be used."""
        # Use memory mapping for large files (> 10MB) but not huge files (> 1GB)
        return 10 * 1024 * 1024 < file_size < 1024 * 1024 * 1024

    async def read_file_optimized(self, file_path: Path) -> bytes:
        """Read file using optimized method based on size."""
        try:
            file_size = file_path.stat().st_size

            if self.should_use_memory_mapping(file_size):
                return await self._read_with_mmap(file_path)
            else:
                return await self._read_with_chunks(file_path, file_size)

        except Exception as e:
            self.logger.error(f"Optimized file read failed for {file_path}: {e}")
            raise

    async def _read_with_mmap(self, file_path: Path) -> bytes:
        """Read file using memory mapping for large files."""
        def _mmap_read():
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    return mmapped_file.read()

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _mmap_read)

    async def _read_with_chunks(self, file_path: Path, file_size: int) -> bytes:
        """Read file in optimized chunks."""
        chunk_size = self.get_optimal_chunk_size(file_size)

        async with aiofiles.open(file_path, 'rb') as f:
            chunks = []
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
            return b''.join(chunks)


class ResourceMonitor:
    """Monitor and manage system resources during scanning."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.io_threshold = 90.0
        self.monitoring = False
        self.metrics_history = deque(maxlen=100)

    async def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                await asyncio.sleep(1.0)  # Monitor every second
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(5.0)

    async def _collect_metrics(self) -> Dict[str, float]:
        """Collect current resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'disk_read_mb': disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
            'disk_write_mb': disk_io.write_bytes / (1024 * 1024) if disk_io else 0,
            'timestamp': time.time()
        }

    def should_throttle(self) -> bool:
        """Determine if scanning should be throttled."""
        if not self.metrics_history:
            return False

        latest = self.metrics_history[-1]
        return (
            latest['cpu_percent'] > self.cpu_threshold or
            latest['memory_percent'] > self.memory_threshold
        )

    def get_optimal_worker_count(self) -> int:
        """Calculate optimal number of workers based on resources."""
        if not self.metrics_history:
            return min(4, os.cpu_count() or 1)

        latest = self.metrics_history[-1]
        cpu_usage = latest['cpu_percent']
        memory_usage = latest['memory_percent']

        # Reduce workers if resources are under pressure
        max_workers = os.cpu_count() or 1

        if cpu_usage > 70 or memory_usage > 70:
            return max(1, max_workers // 2)
        elif cpu_usage > 50 or memory_usage > 50:
            return max(2, max_workers * 3 // 4)
        else:
            return max_workers


class ScanCache:
    """Intelligent caching system for scan results."""

    def __init__(self, max_size: int = 10000):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)

    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key for file."""
        try:
            stat = file_path.stat()
            return f"{file_path}:{stat.st_mtime}:{stat.st_size}"
        except OSError:
            return str(file_path)

    def get(self, file_path: Path) -> Optional[ScanResult]:
        """Get cached scan result."""
        key = self._get_cache_key(file_path)
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None

    def put(self, file_path: Path, result: ScanResult):
        """Cache scan result."""
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        key = self._get_cache_key(file_path)
        self.cache[key] = result
        self.access_times[key] = time.time()

    def _evict_lru(self):
        """Evict least recently used entries."""
        if not self.access_times:
            return

        # Remove 10% of cache (LRU)
        to_remove = max(1, len(self.cache) // 10)
        lru_keys = sorted(self.access_times.keys(), key=lambda k: self.access_times[k])

        for key in lru_keys[:to_remove]:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)

    def get_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total_requests = getattr(self, '_total_requests', 0)
        cache_hits = getattr(self, '_cache_hits', 0)
        return cache_hits / total_requests if total_requests > 0 else 0.0


class AdvancedAsyncScanner:
    """High-performance async scanning engine."""

    def __init__(self, max_workers: Optional[int] = None):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()

        # Core components
        self.scan_queue = asyncio.PriorityQueue()
        self.results_queue = asyncio.Queue()
        self.max_workers = max_workers or min(8, (os.cpu_count() or 1) + 4)
        self.workers = []
        self.is_running = False

        # Optimization components
        self.io_optimizer = IOOptimizer()
        self.resource_monitor = ResourceMonitor()
        self.scan_cache = ScanCache()

        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.start_time = time.time()

        # Scanning engines
        self.clamav = ClamAVWrapper()
        self.ml_detector = get_threat_detector()

        # File type priorities
        self.priority_mapping = {
            '.exe': ScanPriority.CRITICAL,
            '.sh': ScanPriority.CRITICAL,
            '.py': ScanPriority.HIGH,
            '.pdf': ScanPriority.HIGH,
            '.doc': ScanPriority.HIGH,
            '.docx': ScanPriority.HIGH,
            '.zip': ScanPriority.MEDIUM,
            '.tar': ScanPriority.MEDIUM,
            '.mp4': ScanPriority.LOW,
            '.mp3': ScanPriority.LOW,
            '.jpg': ScanPriority.LOW,
            '.png': ScanPriority.LOW,
        }

    async def start(self):
        """Start the scanning engine."""
        if self.is_running:
            return

        self.is_running = True
        self.start_time = time.time()

        # Start resource monitoring
        await self.resource_monitor.start_monitoring()

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

        # Start result processor
        asyncio.create_task(self._result_processor())

        self.logger.info(f"Advanced async scanner started with {self.max_workers} workers")

    async def stop(self):
        """Stop the scanning engine."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop resource monitoring
        await self.resource_monitor.stop_monitoring()

        # Cancel workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        self.logger.info("Advanced async scanner stopped")

    async def queue_scan(self, path: Union[str, Path], scan_type: ScanType = ScanType.QUICK,
                        callback: Optional[Callable] = None) -> bool:
        """Queue a file or directory for scanning."""
        try:
            path_obj = Path(path)

            if not path_obj.exists():
                self.logger.warning(f"Path does not exist: {path}")
                return False

            if path_obj.is_file():
                await self._queue_file(path_obj, scan_type, callback)
            elif path_obj.is_dir():
                await self._queue_directory(path_obj, scan_type, callback)

            return True

        except Exception as e:
            self.logger.error(f"Failed to queue scan for {path}: {e}")
            return False

    async def _queue_file(self, file_path: Path, scan_type: ScanType, callback: Optional[Callable]):
        """Queue a single file for scanning."""
        try:
            # Determine priority based on file extension
            priority = self._get_file_priority(file_path)

            # Get file size for optimization
            file_size = file_path.stat().st_size

            request = ScanRequest(
                path=file_path,
                scan_type=scan_type,
                priority=priority,
                callback=callback,
                estimated_size=file_size,
                metadata={'is_file': True}
            )

            await self.scan_queue.put(request)

        except Exception as e:
            self.logger.error(f"Failed to queue file {file_path}: {e}")

    async def _queue_directory(self, dir_path: Path, scan_type: ScanType, callback: Optional[Callable]):
        """Queue all files in a directory for scanning."""
        try:
            file_count = 0

            for file_path in dir_path.rglob('*'):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    await self._queue_file(file_path, scan_type, callback)
                    file_count += 1

                    # Yield control periodically for large directories
                    if file_count % 100 == 0:
                        await asyncio.sleep(0.01)

            self.logger.info(f"Queued {file_count} files from directory {dir_path}")

        except Exception as e:
            self.logger.error(f"Failed to queue directory {dir_path}: {e}")

    def _get_file_priority(self, file_path: Path) -> ScanPriority:
        """Determine scan priority based on file characteristics."""
        # Check extension-based priority
        suffix = file_path.suffix.lower()
        if suffix in self.priority_mapping:
            return self.priority_mapping[suffix]

        # Check location-based priority
        path_str = str(file_path).lower()
        if any(danger in path_str for danger in ['/bin/', '/sbin/', '/usr/bin/']):
            return ScanPriority.CRITICAL
        elif any(user_dir in path_str for user_dir in ['/home/', '/downloads/', '/documents/']):
            return ScanPriority.HIGH
        elif any(temp_dir in path_str for temp_dir in ['/tmp/', '/var/tmp/', '/cache/']):
            return ScanPriority.LOW

        return ScanPriority.MEDIUM

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if file should be skipped."""
        # Skip very large files (> 2GB) for quick scans
        try:
            if file_path.stat().st_size > 2 * 1024 * 1024 * 1024:
                return True
        except OSError:
            return True

        # Skip system files and special files
        skip_patterns = [
            '/proc/', '/sys/', '/dev/',
            '.git/', '__pycache__/',
            '.sock', '.lock'
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)

    async def _worker(self, worker_id: str):
        """Worker task for processing scan requests."""
        self.logger.debug(f"Worker {worker_id} started")

        while self.is_running:
            try:
                # Check if we should throttle due to resource constraints
                if self.resource_monitor.should_throttle():
                    await asyncio.sleep(0.5)
                    continue

                # Get next scan request with timeout
                try:
                    request = await asyncio.wait_for(self.scan_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Process the scan request
                result = await self._process_scan_request(request)

                # Put result in results queue
                await self.results_queue.put(result)

                # Call callback if provided
                if request.callback:
                    try:
                        await request.callback(result)
                    except Exception as e:
                        self.logger.error(f"Callback error for {request.path}: {e}")

                # Mark task as done
                self.scan_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(0.1)

        self.logger.debug(f"Worker {worker_id} stopped")

    async def _process_scan_request(self, request: ScanRequest) -> ScanResult:
        """Process a single scan request."""
        scan_start = time.time()

        try:
            # Check cache first
            cached_result = self.scan_cache.get(request.path)
            if cached_result and request.scan_type == ScanType.QUICK:
                self.logger.debug(f"Cache hit for {request.path}")
                return cached_result

            # Perform the actual scan
            result = await self._scan_file(request)

            # Cache the result
            if result.error is None:
                self.scan_cache.put(request.path, result)

            # Update performance metrics
            scan_time = time.time() - scan_start
            self._update_metrics(result, scan_time)

            return result

        except Exception as e:
            scan_time = time.time() - scan_start
            self.logger.error(f"Scan failed for {request.path}: {e}")

            return ScanResult(
                path=request.path,
                scan_type=request.scan_type,
                threat_level=ThreatLevel.LOW,
                scan_time=scan_time,
                file_size=request.estimated_size,
                threats_found=[],
                error=str(e)
            )

    async def _scan_file(self, request: ScanRequest) -> ScanResult:
        """Perform the actual file scanning."""
        file_path = request.path
        file_size = request.estimated_size

        threats_found = []
        threat_level = ThreatLevel.LOW
        ml_assessment = None

        # ClamAV scanning
        if self.clamav.is_available():
            clamav_result = await self._run_clamav_scan(file_path)
            if clamav_result.get('threats'):
                threats_found.extend(clamav_result['threats'])
                threat_level = ThreatLevel.HIGH

        # ML-based analysis for suspicious files
        if request.scan_type in [ScanType.DEEP, ScanType.FULL]:
            ml_assessment = await self._run_ml_analysis(file_path)
            if ml_assessment and ml_assessment.threat_level.value > threat_level.value:
                threat_level = ml_assessment.threat_level

        return ScanResult(
            path=file_path,
            scan_type=request.scan_type,
            threat_level=threat_level,
            scan_time=0.0,  # Will be updated by caller
            file_size=file_size,
            threats_found=threats_found,
            ml_assessment=ml_assessment,
            performance_metrics={}
        )

    async def _run_clamav_scan(self, file_path: Path) -> Dict[str, Any]:
        """Run ClamAV scan on file."""
        try:
            # Run ClamAV scan in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.clamav.scan_file, str(file_path)
            )
            return result
        except Exception as e:
            self.logger.error(f"ClamAV scan failed for {file_path}: {e}")
            return {'threats': [], 'error': str(e)}

    async def _run_ml_analysis(self, file_path: Path) -> Optional[Any]:
        """Run ML-based threat analysis."""
        try:
            # Create synthetic security events for ML analysis
            # In a real implementation, this would use actual events
            from app.core.unified_security_engine import EventType, SecurityEvent

            events = [
                SecurityEvent(
                    event_type=EventType.FILE_ACCESSED,
                    timestamp=time.time(),
                    source_path=str(file_path),
                    threat_level=ThreatLevel.LOW
                )
            ]

            assessment = await self.ml_detector.analyze_behavior(events)
            return assessment

        except Exception as e:
            self.logger.error(f"ML analysis failed for {file_path}: {e}")
            return None

    def _update_metrics(self, result: ScanResult, scan_time: float):
        """Update performance metrics."""
        self.metrics.files_scanned += 1
        self.metrics.bytes_scanned += result.file_size
        self.metrics.scan_time_total += scan_time

        if self.metrics.files_scanned > 0:
            self.metrics.average_scan_time = self.metrics.scan_time_total / self.metrics.files_scanned

        if scan_time > 0 and result.file_size > 0:
            throughput = (result.file_size / (1024 * 1024)) / scan_time  # MB/s
            self.metrics.throughput_mbps = throughput

        # Update cache hit ratio
        self.metrics.cache_hit_ratio = self.scan_cache.get_hit_ratio()

    async def _result_processor(self):
        """Process scan results and generate reports."""
        while self.is_running:
            try:
                result = await asyncio.wait_for(self.results_queue.get(), timeout=1.0)

                # Log significant findings
                if result.threats_found:
                    self.logger.warning(f"Threats found in {result.path}: {result.threats_found}")
                elif result.threat_level.value > ThreatLevel.LOW.value:
                    self.logger.info(f"Suspicious activity detected in {result.path}: {result.threat_level.name}")

                # Here you could add more result processing logic
                # such as generating reports, updating databases, etc.

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Result processor error: {e}")

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        # Update real-time metrics
        if self.resource_monitor.metrics_history:
            latest = self.resource_monitor.metrics_history[-1]
            self.metrics.memory_usage_mb = (
                psutil.virtual_memory().used / (1024 * 1024)
            )
            self.metrics.cpu_usage_percent = latest.get('cpu_percent', 0.0)

        return self.metrics

    async def wait_for_completion(self):
        """Wait for all queued scans to complete."""
        await self.scan_queue.join()


# Global scanner instance
_scanner_instance = None


def get_scanner() -> AdvancedAsyncScanner:
    """Get the global scanner instance."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = AdvancedAsyncScanner()
    return _scanner_instance
