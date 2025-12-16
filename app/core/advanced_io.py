"""
Advanced I/O Optimization Module

Provides high-performance file I/O strategies for the scanner:
- AsyncFileReader: Async I/O using aiofiles for concurrent operations
- MemoryMappedReader: Memory-mapped files for large file optimization
- BufferedFileScanner: Optimized buffered reads for medium files
- ParallelIOManager: Concurrent multi-file operations
- AdvancedIOManager: Automatic strategy selection and orchestration

Target: 30-50% I/O time reduction through adaptive strategies.
"""

import asyncio
import logging
import mmap
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import AsyncIterator, Iterator

try:
    import aiofiles

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

logger = logging.getLogger(__name__)


class IOStrategy(Enum):
    """I/O strategy selection based on file characteristics"""

    ASYNC = auto()  # aiofiles for concurrent small files
    MMAP = auto()  # Memory-mapped for large files (>100MB)
    BUFFERED = auto()  # Optimized buffered reads for medium files
    AUTO = auto()  # Automatic strategy selection


@dataclass
class IOConfig:
    """I/O optimization configuration"""

    # File size thresholds for strategy selection
    small_file_threshold: int = 1 * 1024 * 1024  # 1MB
    large_file_threshold: int = 100 * 1024 * 1024  # 100MB

    # Chunk size for streaming reads (256KB default)
    chunk_size: int = 256 * 1024

    # Maximum concurrent I/O operations
    max_concurrent_ops: int = 20

    # mmap optimization hints
    use_mmap_sequential: bool = True  # Hint sequential access pattern

    # I/O strategy (AUTO for automatic selection)
    strategy: IOStrategy = IOStrategy.AUTO

    # Buffering strategy for buffered reads
    buffer_size: int = 512 * 1024  # 512KB buffer (2x chunk_size)

    def __post_init__(self):
        """Validate configuration values"""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.small_file_threshold >= self.large_file_threshold:
            raise ValueError("small_file_threshold must be < large_file_threshold")
        if self.max_concurrent_ops <= 0:
            raise ValueError("max_concurrent_ops must be positive")

        # Ensure buffer_size is at least 2x chunk_size
        if self.buffer_size < self.chunk_size * 2:
            self.buffer_size = self.chunk_size * 2
            logger.warning(
                f"buffer_size adjusted to {self.buffer_size} "
                f"(2x chunk_size for optimal performance)"
            )


@dataclass
class IOMetrics:
    """I/O performance metrics tracking"""

    total_bytes_read: int = 0
    total_files_read: int = 0
    total_time_ms: float = 0.0
    strategy_usage: dict[IOStrategy, int] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize strategy usage counters"""
        if not self.strategy_usage:
            self.strategy_usage = {
                IOStrategy.ASYNC: 0,
                IOStrategy.MMAP: 0,
                IOStrategy.BUFFERED: 0,
            }

    @property
    def avg_throughput_mbps(self) -> float:
        """Calculate average throughput in MB/s"""
        if self.total_time_ms == 0:
            return 0.0
        time_seconds = self.total_time_ms / 1000.0
        bytes_per_second = self.total_bytes_read / time_seconds
        return bytes_per_second / (1024 * 1024)  # Convert to MB/s

    @property
    def avg_file_size_mb(self) -> float:
        """Calculate average file size in MB"""
        if self.total_files_read == 0:
            return 0.0
        bytes_per_file = self.total_bytes_read / self.total_files_read
        return bytes_per_file / (1024 * 1024)

    def record_read(self, bytes_read: int, time_ms: float, strategy: IOStrategy):
        """Record a file read operation"""
        self.total_bytes_read += bytes_read
        self.total_files_read += 1
        self.total_time_ms += time_ms
        self.strategy_usage[strategy] = self.strategy_usage.get(strategy, 0) + 1

    def to_dict(self) -> dict:
        """Convert metrics to dictionary"""
        return {
            "total_bytes_read": self.total_bytes_read,
            "total_files_read": self.total_files_read,
            "total_time_ms": self.total_time_ms,
            "avg_throughput_mbps": self.avg_throughput_mbps,
            "avg_file_size_mb": self.avg_file_size_mb,
            "strategy_usage": {
                s.name: count for s, count in self.strategy_usage.items()
            },
        }


class AsyncFileReader:
    """Async file reading using aiofiles library"""

    def __init__(self):
        if not AIOFILES_AVAILABLE:
            logger.warning("aiofiles not available, falling back to sync I/O")

    async def read_file(self, path: Path) -> bytes:
        """
        Read entire file asynchronously.

        Args:
            path: Path to file to read

        Returns:
            File contents as bytes

        Raises:
            OSError: If file cannot be read
        """
        if not AIOFILES_AVAILABLE:
            # Fallback to sync read in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._read_file_sync, path)

        async with aiofiles.open(path, mode="rb") as f:
            return await f.read()

    def _read_file_sync(self, path: Path) -> bytes:
        """Synchronous file read (fallback)"""
        with open(path, "rb") as f:
            return f.read()

    async def read_chunks(self, path: Path, chunk_size: int) -> AsyncIterator[bytes]:
        """
        Async generator yielding file chunks.

        Args:
            path: Path to file to read
            chunk_size: Size of each chunk in bytes

        Yields:
            File chunks as bytes
        """
        if not AIOFILES_AVAILABLE:
            # Fallback to sync generator
            for chunk in self._read_chunks_sync(path, chunk_size):
                yield chunk
                await asyncio.sleep(0)  # Yield control to event loop
            return

        async with aiofiles.open(path, mode="rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def _read_chunks_sync(self, path: Path, chunk_size: int) -> Iterator[bytes]:
        """Synchronous chunk reader (fallback)"""
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk


class MemoryMappedReader:
    """Memory-mapped file reading for large files"""

    def __init__(self, use_sequential_hint: bool = True):
        """
        Initialize mmap reader.

        Args:
            use_sequential_hint: Use MADV_SEQUENTIAL hint for optimization
        """
        self.use_sequential_hint = use_sequential_hint

    def read_file_mmap(self, path: Path) -> bytes:
        """
        Read entire file using memory mapping.

        Args:
            path: Path to file to read

        Returns:
            File contents as bytes

        Raises:
            OSError: If file cannot be mapped
        """
        with open(path, "rb") as f:
            # Create read-only memory map
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Hint sequential access pattern for OS optimization
                if self.use_sequential_hint:
                    try:
                        mm.madvise(mmap.MADV_SEQUENTIAL)
                    except (AttributeError, OSError):
                        # madvise not available on all platforms
                        pass

                # Read entire mapped region
                return mm[:]

    def scan_file_mmap(self, path: Path, chunk_size: int) -> Iterator[bytes]:
        """
        Generator scanning mmap in chunks.

        Args:
            path: Path to file to read
            chunk_size: Size of each chunk in bytes

        Yields:
            File chunks as bytes
        """
        with open(path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Apply sequential access hint
                if self.use_sequential_hint:
                    try:
                        mm.madvise(mmap.MADV_SEQUENTIAL)
                    except (AttributeError, OSError):
                        pass

                # Scan in chunks
                offset = 0
                map_size = len(mm)

                while offset < map_size:
                    end_offset = min(offset + chunk_size, map_size)
                    yield mm[offset:end_offset]
                    offset = end_offset


class BufferedFileScanner:
    """Optimized buffered file reading for medium files"""

    def __init__(self, buffer_size: int = 512 * 1024):
        """
        Initialize buffered scanner.

        Args:
            buffer_size: Size of read buffer (default 512KB)
        """
        self.buffer_size = buffer_size

    def read_buffered(self, path: Path) -> bytes:
        """
        Read entire file with optimized buffering.

        Args:
            path: Path to file to read

        Returns:
            File contents as bytes
        """
        with open(path, "rb", buffering=self.buffer_size) as f:
            return f.read()

    def scan_chunks(self, path: Path, chunk_size: int) -> Iterator[bytes]:
        """
        Generator yielding buffered chunks.

        Args:
            path: Path to file to read
            chunk_size: Size of each chunk in bytes

        Yields:
            File chunks as bytes
        """
        # Use buffer size 2x chunk size for read-ahead optimization
        buffer_size = max(self.buffer_size, chunk_size * 2)

        with open(path, "rb", buffering=buffer_size) as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk


class ParallelIOManager:
    """Manage concurrent file I/O operations"""

    def __init__(self, max_workers: int = 20):
        """
        Initialize parallel I/O manager.

        Args:
            max_workers: Maximum concurrent I/O operations
        """
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)

    async def read_files_parallel(
        self, file_paths: list[Path], async_reader: AsyncFileReader
    ) -> dict[Path, bytes]:
        """
        Read multiple files concurrently.

        Args:
            file_paths: List of file paths to read
            async_reader: AsyncFileReader instance to use

        Returns:
            Dictionary mapping file paths to their contents
        """

        async def read_single(path: Path) -> tuple[Path, bytes]:
            """Read single file with semaphore control"""
            async with self.semaphore:
                try:
                    content = await async_reader.read_file(path)
                    return (path, content)
                except Exception as e:
                    logger.error(f"Failed to read {path}: {e}")
                    return (path, b"")

        # Execute all reads concurrently
        tasks = [read_single(p) for p in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return dict(results)


class AdvancedIOManager:
    """Main I/O manager with automatic strategy selection"""

    def __init__(self, config: IOConfig | None = None):
        """
        Initialize advanced I/O manager.

        Args:
            config: I/O configuration (uses defaults if None)
        """
        self.config = config or IOConfig()

        # Initialize strategy implementations
        self.async_reader = AsyncFileReader()
        self.mmap_reader = MemoryMappedReader(self.config.use_mmap_sequential)
        self.buffered_reader = BufferedFileScanner(self.config.buffer_size)
        self.parallel_manager = ParallelIOManager(self.config.max_concurrent_ops)

        # Performance metrics
        self._metrics = IOMetrics()

        logger.info(
            f"AdvancedIOManager initialized: "
            f"strategy={self.config.strategy.name}, "
            f"chunk_size={self.config.chunk_size}, "
            f"max_concurrent={self.config.max_concurrent_ops}"
        )

    def select_strategy(self, file_path: Path) -> IOStrategy:
        """
        Auto-select optimal I/O strategy based on file size.

        Args:
            file_path: Path to file

        Returns:
            Selected IOStrategy
        """
        # Use configured strategy if not AUTO
        if self.config.strategy != IOStrategy.AUTO:
            return self.config.strategy

        # Get file size
        try:
            file_size = file_path.stat().st_size
        except OSError as e:
            logger.warning(f"Cannot stat {file_path}: {e}, using BUFFERED")
            return IOStrategy.BUFFERED

        # Select based on file size thresholds
        if file_size < self.config.small_file_threshold:
            return IOStrategy.ASYNC
        elif file_size > self.config.large_file_threshold:
            return IOStrategy.MMAP
        else:
            return IOStrategy.BUFFERED

    async def read_file_async(self, path: Path) -> bytes:
        """
        Read file using optimal strategy.

        Args:
            path: Path to file to read

        Returns:
            File contents as bytes
        """
        strategy = self.select_strategy(path)
        start_time = time.perf_counter()

        try:
            # Execute read using selected strategy
            if strategy == IOStrategy.ASYNC:
                content = await self.async_reader.read_file(path)
            elif strategy == IOStrategy.MMAP:
                # mmap is sync, run in executor
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(
                    None, self.mmap_reader.read_file_mmap, path
                )
            else:  # BUFFERED
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(
                    None, self.buffered_reader.read_buffered, path
                )

            # Record metrics
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._metrics.record_read(len(content), elapsed_ms, strategy)

            logger.debug(
                f"Read {path.name} ({len(content)} bytes) using {strategy.name} "
                f"in {elapsed_ms:.2f}ms"
            )

            return content

        except Exception as e:
            logger.error(f"Failed to read {path} with {strategy.name}: {e}")
            raise

    async def scan_file_chunks(self, path: Path) -> AsyncIterator[bytes]:
        """
        Async generator for file chunks.

        Args:
            path: Path to file to scan

        Yields:
            File chunks as bytes
        """
        strategy = self.select_strategy(path)

        if strategy == IOStrategy.ASYNC:
            # Async chunks from aiofiles
            async for chunk in self.async_reader.read_chunks(
                path, self.config.chunk_size
            ):
                yield chunk

        elif strategy == IOStrategy.MMAP:
            # Convert sync mmap generator to async
            for chunk in self.mmap_reader.scan_file_mmap(path, self.config.chunk_size):
                yield chunk
                await asyncio.sleep(0)  # Yield control to event loop

        else:  # BUFFERED
            # Convert sync buffered generator to async
            for chunk in self.buffered_reader.scan_chunks(path, self.config.chunk_size):
                yield chunk
                await asyncio.sleep(0)  # Yield control to event loop

    async def read_files_parallel(self, file_paths: list[Path]) -> dict[Path, bytes]:
        """
        Read multiple files concurrently.

        Args:
            file_paths: List of file paths to read

        Returns:
            Dictionary mapping file paths to their contents
        """
        return await self.parallel_manager.read_files_parallel(
            file_paths, self.async_reader
        )

    @property
    def metrics(self) -> IOMetrics:
        """Get current I/O metrics"""
        return self._metrics

    def reset_metrics(self):
        """Reset performance metrics"""
        self._metrics = IOMetrics()
        logger.info("I/O metrics reset")

    def get_metrics_summary(self) -> dict:
        """
        Get metrics summary as dictionary.

        Returns:
            Dictionary with performance metrics
        """
        return self._metrics.to_dict()


# Module-level convenience functions
async def read_file_optimized(
    file_path: str | Path, config: IOConfig | None = None
) -> bytes:
    """
    Convenience function to read a file with optimal I/O strategy.

    Args:
        file_path: Path to file to read
        config: Optional I/O configuration

    Returns:
        File contents as bytes
    """
    manager = AdvancedIOManager(config)
    return await manager.read_file_async(Path(file_path))


async def read_files_batch(
    file_paths: list[str | Path], config: IOConfig | None = None
) -> dict[Path, bytes]:
    """
    Convenience function to read multiple files in parallel.

    Args:
        file_paths: List of file paths to read
        config: Optional I/O configuration

    Returns:
        Dictionary mapping file paths to their contents
    """
    manager = AdvancedIOManager(config)
    paths = [Path(p) for p in file_paths]
    return await manager.read_files_parallel(paths)
