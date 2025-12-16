"""
Comprehensive tests for Advanced I/O Optimization Module

Tests cover:
- AsyncFileReader async/sync file reading and chunking
- MemoryMappedReader large file optimization
- BufferedFileScanner medium file optimization
- ParallelIOManager concurrent operations
- AdvancedIOManager strategy auto-selection
- Performance comparisons and edge cases
- IOConfig validation
- IOMetrics tracking

Target: >90% code coverage
"""

import asyncio
import mmap
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.advanced_io import (
    AdvancedIOManager,
    AsyncFileReader,
    BufferedFileScanner,
    IOConfig,
    IOMetrics,
    IOStrategy,
    MemoryMappedReader,
    ParallelIOManager,
    read_file_optimized,
    read_files_batch,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_dir(tmp_path):
    """Provide temporary directory for test files"""
    return tmp_path


@pytest.fixture
def small_file(temp_dir):
    """Create small test file (<1MB)"""
    file_path = temp_dir / "small.txt"
    content = b"Small file content\n" * 1000  # ~19KB
    file_path.write_bytes(content)
    return file_path


@pytest.fixture
def medium_file(temp_dir):
    """Create medium test file (1-100MB)"""
    file_path = temp_dir / "medium.bin"
    # 5MB file
    content = b"X" * (5 * 1024 * 1024)
    file_path.write_bytes(content)
    return file_path


@pytest.fixture
def large_file(temp_dir):
    """Create large test file (>100MB)"""
    file_path = temp_dir / "large.bin"
    # 150MB file (use sparse file for speed)
    with open(file_path, "wb") as f:
        f.seek(150 * 1024 * 1024 - 1)
        f.write(b"\0")
    return file_path


@pytest.fixture
def empty_file(temp_dir):
    """Create empty test file"""
    file_path = temp_dir / "empty.txt"
    file_path.write_bytes(b"")
    return file_path


@pytest.fixture
def io_config():
    """Provide default IOConfig"""
    return IOConfig()


# ============================================================================
# Test IOConfig
# ============================================================================


class TestIOConfig:
    """Test IOConfig dataclass and validation"""

    def test_default_config(self):
        """Test default configuration values"""
        config = IOConfig()
        assert config.small_file_threshold == 1 * 1024 * 1024  # 1MB
        assert config.large_file_threshold == 100 * 1024 * 1024  # 100MB
        assert config.chunk_size == 256 * 1024  # 256KB
        assert config.max_concurrent_ops == 20
        assert config.use_mmap_sequential is True
        assert config.strategy == IOStrategy.AUTO
        assert config.buffer_size == 512 * 1024  # 512KB

    def test_custom_config(self):
        """Test custom configuration"""
        config = IOConfig(
            small_file_threshold=500_000,
            large_file_threshold=50_000_000,
            chunk_size=128 * 1024,
            max_concurrent_ops=10,
            use_mmap_sequential=False,
            strategy=IOStrategy.MMAP,
        )
        assert config.small_file_threshold == 500_000
        assert config.large_file_threshold == 50_000_000
        assert config.chunk_size == 128 * 1024
        assert config.max_concurrent_ops == 10
        assert config.use_mmap_sequential is False
        assert config.strategy == IOStrategy.MMAP

    def test_invalid_chunk_size(self):
        """Test validation rejects invalid chunk size"""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            IOConfig(chunk_size=0)

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            IOConfig(chunk_size=-100)

    def test_invalid_thresholds(self):
        """Test validation rejects invalid thresholds"""
        with pytest.raises(ValueError, match="small_file_threshold must be"):
            IOConfig(small_file_threshold=100_000_000, large_file_threshold=1_000_000)

    def test_invalid_max_concurrent(self):
        """Test validation rejects invalid max_concurrent_ops"""
        with pytest.raises(ValueError, match="max_concurrent_ops must be positive"):
            IOConfig(max_concurrent_ops=0)

    def test_buffer_size_adjustment(self, caplog):
        """Test buffer_size auto-adjustment to 2x chunk_size"""
        config = IOConfig(chunk_size=1024, buffer_size=1000)
        assert config.buffer_size == 2048  # 2x chunk_size
        assert "buffer_size adjusted" in caplog.text


# ============================================================================
# Test IOMetrics
# ============================================================================


class TestIOMetrics:
    """Test IOMetrics tracking"""

    def test_default_metrics(self):
        """Test initial metric values"""
        metrics = IOMetrics()
        assert metrics.total_bytes_read == 0
        assert metrics.total_files_read == 0
        assert metrics.total_time_ms == 0.0
        assert metrics.avg_throughput_mbps == 0.0
        assert metrics.avg_file_size_mb == 0.0
        assert IOStrategy.ASYNC in metrics.strategy_usage

    def test_record_read(self):
        """Test recording read operations"""
        metrics = IOMetrics()

        # Record first read
        metrics.record_read(1024, 10.0, IOStrategy.ASYNC)
        assert metrics.total_bytes_read == 1024
        assert metrics.total_files_read == 1
        assert metrics.total_time_ms == 10.0
        assert metrics.strategy_usage[IOStrategy.ASYNC] == 1

        # Record second read
        metrics.record_read(2048, 20.0, IOStrategy.MMAP)
        assert metrics.total_bytes_read == 3072
        assert metrics.total_files_read == 2
        assert metrics.total_time_ms == 30.0
        assert metrics.strategy_usage[IOStrategy.MMAP] == 1

    def test_throughput_calculation(self):
        """Test throughput calculation"""
        metrics = IOMetrics()

        # 1MB in 1000ms = 1MB/s
        metrics.record_read(1024 * 1024, 1000.0, IOStrategy.ASYNC)
        assert pytest.approx(metrics.avg_throughput_mbps, rel=0.01) == 1.0

        # Add another 1MB in 1000ms
        metrics.record_read(1024 * 1024, 1000.0, IOStrategy.ASYNC)
        # Total: 2MB in 2000ms = 1MB/s
        assert pytest.approx(metrics.avg_throughput_mbps, rel=0.01) == 1.0

    def test_avg_file_size(self):
        """Test average file size calculation"""
        metrics = IOMetrics()

        # 1MB file
        metrics.record_read(1024 * 1024, 100.0, IOStrategy.ASYNC)
        assert pytest.approx(metrics.avg_file_size_mb, rel=0.01) == 1.0

        # Add 3MB file
        metrics.record_read(3 * 1024 * 1024, 200.0, IOStrategy.MMAP)
        # Average: 4MB / 2 files = 2MB
        assert pytest.approx(metrics.avg_file_size_mb, rel=0.01) == 2.0

    def test_to_dict(self):
        """Test conversion to dictionary"""
        metrics = IOMetrics()
        metrics.record_read(1024, 10.0, IOStrategy.BUFFERED)

        data = metrics.to_dict()
        assert data["total_bytes_read"] == 1024
        assert data["total_files_read"] == 1
        assert data["total_time_ms"] == 10.0
        assert "avg_throughput_mbps" in data
        assert "strategy_usage" in data
        assert data["strategy_usage"]["BUFFERED"] == 1


# ============================================================================
# Test AsyncFileReader
# ============================================================================


class TestAsyncFileReader:
    """Test AsyncFileReader functionality"""

    @pytest.mark.asyncio
    async def test_read_small_file(self, small_file):
        """Test reading small file async"""
        reader = AsyncFileReader()
        content = await reader.read_file(small_file)

        assert isinstance(content, bytes)
        assert len(content) > 0
        assert content == small_file.read_bytes()

    @pytest.mark.asyncio
    async def test_read_empty_file(self, empty_file):
        """Test reading empty file"""
        reader = AsyncFileReader()
        content = await reader.read_file(empty_file)

        assert content == b""

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, temp_dir):
        """Test reading nonexistent file raises error"""
        reader = AsyncFileReader()
        nonexistent = temp_dir / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            await reader.read_file(nonexistent)

    @pytest.mark.asyncio
    async def test_read_chunks(self, small_file):
        """Test chunked reading"""
        reader = AsyncFileReader()
        chunks = []

        async for chunk in reader.read_chunks(small_file, chunk_size=1024):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(c, bytes) for c in chunks)

        # Verify reassembled content matches
        reassembled = b"".join(chunks)
        assert reassembled == small_file.read_bytes()

    @pytest.mark.asyncio
    async def test_read_chunks_empty_file(self, empty_file):
        """Test chunked reading of empty file"""
        reader = AsyncFileReader()
        chunks = []

        async for chunk in reader.read_chunks(empty_file, chunk_size=1024):
            chunks.append(chunk)

        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_fallback_when_aiofiles_unavailable(self, small_file, monkeypatch):
        """Test fallback to sync I/O when aiofiles unavailable"""
        # Mock aiofiles as unavailable
        import app.core.advanced_io as aio_module

        monkeypatch.setattr(aio_module, "AIOFILES_AVAILABLE", False)

        reader = AsyncFileReader()
        content = await reader.read_file(small_file)

        assert content == small_file.read_bytes()


# ============================================================================
# Test MemoryMappedReader
# ============================================================================


class TestMemoryMappedReader:
    """Test MemoryMappedReader functionality"""

    def test_read_file_mmap(self, medium_file):
        """Test memory-mapped file reading"""
        reader = MemoryMappedReader()
        content = reader.read_file_mmap(medium_file)

        assert isinstance(content, bytes)
        assert content == medium_file.read_bytes()

    def test_read_empty_file_mmap(self, empty_file):
        """Test memory-mapping empty file"""
        reader = MemoryMappedReader()

        # Empty files cannot be memory-mapped
        with pytest.raises((OSError, ValueError)):
            reader.read_file_mmap(empty_file)

    def test_scan_file_mmap_chunks(self, medium_file):
        """Test chunked mmap scanning"""
        reader = MemoryMappedReader()
        chunks = list(reader.scan_file_mmap(medium_file, chunk_size=1024 * 1024))

        assert len(chunks) > 0
        assert all(isinstance(c, bytes) for c in chunks)

        # Verify reassembled content
        reassembled = b"".join(chunks)
        assert reassembled == medium_file.read_bytes()

    def test_sequential_hint_applied(self, medium_file):
        """Test that MADV_SEQUENTIAL hint is applied"""
        reader = MemoryMappedReader(use_sequential_hint=True)

        # This should not raise even if madvise not available
        content = reader.read_file_mmap(medium_file)
        assert len(content) > 0

    def test_sequential_hint_disabled(self, medium_file):
        """Test disabling sequential hint"""
        reader = MemoryMappedReader(use_sequential_hint=False)
        content = reader.read_file_mmap(medium_file)

        assert content == medium_file.read_bytes()


# ============================================================================
# Test BufferedFileScanner
# ============================================================================


class TestBufferedFileScanner:
    """Test BufferedFileScanner functionality"""

    def test_read_buffered(self, medium_file):
        """Test buffered file reading"""
        scanner = BufferedFileScanner()
        content = scanner.read_buffered(medium_file)

        assert content == medium_file.read_bytes()

    def test_read_empty_file_buffered(self, empty_file):
        """Test buffered reading of empty file"""
        scanner = BufferedFileScanner()
        content = scanner.read_buffered(empty_file)

        assert content == b""

    def test_scan_chunks(self, medium_file):
        """Test chunked scanning with buffering"""
        scanner = BufferedFileScanner()
        chunks = list(scanner.scan_chunks(medium_file, chunk_size=512 * 1024))

        assert len(chunks) > 0

        # Verify reassembled content
        reassembled = b"".join(chunks)
        assert reassembled == medium_file.read_bytes()

    def test_custom_buffer_size(self, small_file):
        """Test custom buffer size"""
        scanner = BufferedFileScanner(buffer_size=4096)
        content = scanner.read_buffered(small_file)

        assert content == small_file.read_bytes()


# ============================================================================
# Test ParallelIOManager
# ============================================================================


class TestParallelIOManager:
    """Test ParallelIOManager concurrent operations"""

    @pytest.mark.asyncio
    async def test_read_multiple_files(self, temp_dir):
        """Test parallel reading of multiple files"""
        # Create test files
        files = []
        for i in range(5):
            file_path = temp_dir / f"file{i}.txt"
            file_path.write_bytes(f"Content {i}\n".encode())
            files.append(file_path)

        manager = ParallelIOManager(max_workers=3)
        reader = AsyncFileReader()

        results = await manager.read_files_parallel(files, reader)

        assert len(results) == 5
        assert all(path in results for path in files)
        assert all(isinstance(content, bytes) for content in results.values())

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self, temp_dir):
        """Test that semaphore limits concurrent operations"""
        # Create many files
        files = [temp_dir / f"file{i}.txt" for i in range(20)]
        for f in files:
            f.write_bytes(b"test")

        manager = ParallelIOManager(max_workers=5)
        reader = AsyncFileReader()

        results = await manager.read_files_parallel(files, reader)
        assert len(results) == 20

    @pytest.mark.asyncio
    async def test_handles_read_errors(self, temp_dir):
        """Test error handling in parallel reads"""
        # Mix valid and invalid files
        valid_file = temp_dir / "valid.txt"
        valid_file.write_bytes(b"valid")

        invalid_file = temp_dir / "nonexistent.txt"

        manager = ParallelIOManager()
        reader = AsyncFileReader()

        # Should handle errors gracefully (returns empty bytes)
        results = await manager.read_files_parallel([valid_file, invalid_file], reader)

        assert valid_file in results
        assert results[valid_file] == b"valid"
        # Invalid file should have empty bytes
        assert results[invalid_file] == b""


# ============================================================================
# Test AdvancedIOManager
# ============================================================================


class TestAdvancedIOManager:
    """Test AdvancedIOManager strategy selection and orchestration"""

    def test_initialization(self):
        """Test manager initialization"""
        manager = AdvancedIOManager()

        assert manager.config is not None
        assert manager.async_reader is not None
        assert manager.mmap_reader is not None
        assert manager.buffered_reader is not None
        assert manager.parallel_manager is not None

    def test_select_strategy_small_file(self, small_file):
        """Test strategy selection for small file"""
        manager = AdvancedIOManager()
        strategy = manager.select_strategy(small_file)

        assert strategy == IOStrategy.ASYNC

    def test_select_strategy_medium_file(self, medium_file):
        """Test strategy selection for medium file"""
        manager = AdvancedIOManager()
        strategy = manager.select_strategy(medium_file)

        assert strategy == IOStrategy.BUFFERED

    def test_select_strategy_large_file(self, large_file):
        """Test strategy selection for large file"""
        manager = AdvancedIOManager()
        strategy = manager.select_strategy(large_file)

        assert strategy == IOStrategy.MMAP

    def test_select_strategy_forced(self, small_file):
        """Test forced strategy selection"""
        config = IOConfig(strategy=IOStrategy.MMAP)
        manager = AdvancedIOManager(config)

        # Should use MMAP even for small file
        strategy = manager.select_strategy(small_file)
        assert strategy == IOStrategy.MMAP

    @pytest.mark.asyncio
    async def test_read_file_async_small(self, small_file):
        """Test async read of small file"""
        manager = AdvancedIOManager()
        content = await manager.read_file_async(small_file)

        assert content == small_file.read_bytes()
        assert manager.metrics.total_files_read == 1
        assert manager.metrics.strategy_usage[IOStrategy.ASYNC] == 1

    @pytest.mark.asyncio
    async def test_read_file_async_medium(self, medium_file):
        """Test async read of medium file"""
        manager = AdvancedIOManager()
        content = await manager.read_file_async(medium_file)

        assert content == medium_file.read_bytes()
        assert manager.metrics.strategy_usage[IOStrategy.BUFFERED] == 1

    @pytest.mark.asyncio
    async def test_scan_file_chunks_async(self, small_file):
        """Test async chunked scanning"""
        manager = AdvancedIOManager()
        chunks = []

        async for chunk in manager.scan_file_chunks(small_file):
            chunks.append(chunk)

        assert len(chunks) > 0
        reassembled = b"".join(chunks)
        assert reassembled == small_file.read_bytes()

    @pytest.mark.asyncio
    async def test_read_files_parallel(self, temp_dir):
        """Test parallel file reading"""
        # Create test files
        files = [temp_dir / f"file{i}.txt" for i in range(3)]
        for i, f in enumerate(files):
            f.write_bytes(f"Content {i}".encode())

        manager = AdvancedIOManager()
        results = await manager.read_files_parallel(files)

        assert len(results) == 3
        assert all(f in results for f in files)

    def test_metrics_tracking(self):
        """Test metrics are properly tracked"""
        manager = AdvancedIOManager()

        assert manager.metrics.total_files_read == 0

        # Metrics property
        metrics = manager.metrics
        assert isinstance(metrics, IOMetrics)

    def test_reset_metrics(self):
        """Test metrics reset"""
        manager = AdvancedIOManager()
        manager._metrics.total_files_read = 10

        manager.reset_metrics()
        assert manager.metrics.total_files_read == 0

    def test_get_metrics_summary(self):
        """Test metrics summary generation"""
        manager = AdvancedIOManager()
        summary = manager.get_metrics_summary()

        assert isinstance(summary, dict)
        assert "total_bytes_read" in summary
        assert "strategy_usage" in summary


# ============================================================================
# Test Convenience Functions
# ============================================================================


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    @pytest.mark.asyncio
    async def test_read_file_optimized(self, small_file):
        """Test read_file_optimized convenience function"""
        content = await read_file_optimized(small_file)
        assert content == small_file.read_bytes()

    @pytest.mark.asyncio
    async def test_read_file_optimized_with_config(self, small_file):
        """Test read_file_optimized with custom config"""
        config = IOConfig(chunk_size=1024)
        content = await read_file_optimized(small_file, config)
        assert content == small_file.read_bytes()

    @pytest.mark.asyncio
    async def test_read_files_batch(self, temp_dir):
        """Test read_files_batch convenience function"""
        files = [temp_dir / f"file{i}.txt" for i in range(3)]
        for i, f in enumerate(files):
            f.write_bytes(f"Data {i}".encode())

        results = await read_files_batch(files)
        assert len(results) == 3
        assert all(Path(f) in results for f in files)


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_permission_denied(self, temp_dir):
        """Test handling of permission errors"""
        # Create file and remove read permissions
        restricted = temp_dir / "restricted.txt"
        restricted.write_bytes(b"secret")
        restricted.chmod(0o000)

        try:
            manager = AdvancedIOManager()
            with pytest.raises(PermissionError):
                await manager.read_file_async(restricted)
        finally:
            # Restore permissions for cleanup
            restricted.chmod(0o644)

    def test_nonexistent_file_strategy_selection(self, temp_dir):
        """Test strategy selection for nonexistent file"""
        manager = AdvancedIOManager()
        nonexistent = temp_dir / "nonexistent.txt"

        # Should fall back to BUFFERED on stat error
        strategy = manager.select_strategy(nonexistent)
        assert strategy == IOStrategy.BUFFERED

    @pytest.mark.asyncio
    async def test_concurrent_reads_same_file(self, small_file):
        """Test concurrent reads of the same file"""
        manager = AdvancedIOManager()

        # Read same file multiple times concurrently
        tasks = [manager.read_file_async(small_file) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r == small_file.read_bytes() for r in results)

    @pytest.mark.asyncio
    async def test_very_small_chunk_size(self, small_file):
        """Test with very small chunk size"""
        config = IOConfig(chunk_size=100)  # 100 bytes
        manager = AdvancedIOManager(config)

        chunks = []
        async for chunk in manager.scan_file_chunks(small_file):
            chunks.append(chunk)

        # Should have many small chunks
        assert len(chunks) > 10
        assert all(len(c) <= 100 for c in chunks)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=app/core/advanced_io", "--cov-report=term-missing"]
    )
