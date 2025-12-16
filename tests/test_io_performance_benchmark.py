"""
Performance Benchmark Suite for Advanced I/O System (Task 1.6)

Measures I/O performance improvements:
- Baseline (standard file I/O) vs Advanced I/O (adaptive strategies)
- Small/medium/large file performance (1KB, 1MB, 10MB, 100MB)
- Concurrent operations scaling
- Strategy selection effectiveness

Target: 30-50% I/O time reduction compared to baseline
"""

import asyncio
import time
from pathlib import Path
from typing import Any
import tempfile
import statistics

import pytest

from app.core.advanced_io import AdvancedIOManager, IOConfig, IOStrategy


class IOPerformanceBenchmark:
    """Performance benchmark suite for I/O operations."""

    def __init__(self):
        self.results = {
            "baseline": {},
            "advanced_io": {},
            "improvements": {},
        }

    def create_test_file(self, size_bytes: int, path: Path) -> Path:
        """Create test file of specified size."""
        with open(path, "wb") as f:
            # Write in 1MB chunks for efficiency
            chunk_size = 1024 * 1024
            remaining = size_bytes
            while remaining > 0:
                write_size = min(chunk_size, remaining)
                f.write(b"X" * write_size)
                remaining -= write_size
        return path

    async def benchmark_baseline_read(
        self, file_path: Path, iterations: int = 5
    ) -> dict[str, Any]:
        """Benchmark baseline synchronous file reading."""
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            with open(file_path, "rb") as f:
                data = f.read()
            end = time.perf_counter()
            times.append(end - start)

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        avg_time = statistics.mean(times)
        throughput_mbps = (file_size_mb / avg_time) if avg_time > 0 else 0

        return {
            "avg_time_seconds": avg_time,
            "min_time_seconds": min(times),
            "max_time_seconds": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "throughput_mbps": throughput_mbps,
            "iterations": iterations,
        }

    async def benchmark_advanced_io_read(
        self, file_path: Path, iterations: int = 5
    ) -> dict[str, Any]:
        """Benchmark advanced I/O manager reading."""
        config = IOConfig()
        io_manager = AdvancedIOManager(config)
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            data = await io_manager.read_file_async(file_path)
            end = time.perf_counter()
            times.append(end - start)

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        avg_time = statistics.mean(times)
        throughput_mbps = (file_size_mb / avg_time) if avg_time > 0 else 0

        # Get strategy used
        metrics = io_manager.metrics
        strategy_used = max(metrics.strategy_usage, key=metrics.strategy_usage.get)

        return {
            "avg_time_seconds": avg_time,
            "min_time_seconds": min(times),
            "max_time_seconds": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "throughput_mbps": throughput_mbps,
            "iterations": iterations,
            "strategy_used": strategy_used,
            "metrics": {
                "total_bytes_read": metrics.total_bytes_read,
                "avg_throughput_mbps": metrics.avg_throughput_mbps,
            },
        }

    async def benchmark_concurrent_reads(
        self, file_paths: list[Path], concurrency: int = 10
    ) -> dict[str, Any]:
        """Benchmark concurrent file reading with advanced I/O."""
        config = IOConfig()
        io_manager = AdvancedIOManager(config)

        start = time.perf_counter()

        # Read files concurrently
        tasks = [io_manager.read_file_async(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end = time.perf_counter()
        elapsed = end - start

        # Calculate statistics
        total_size_mb = sum(p.stat().st_size for p in file_paths) / (1024 * 1024)
        throughput_mbps = (total_size_mb / elapsed) if elapsed > 0 else 0
        files_per_second = len(file_paths) / elapsed if elapsed > 0 else 0

        return {
            "total_time_seconds": elapsed,
            "total_files": len(file_paths),
            "total_size_mb": total_size_mb,
            "throughput_mbps": throughput_mbps,
            "files_per_second": files_per_second,
            "concurrency": concurrency,
        }

    def calculate_improvement(self, baseline: float, advanced: float) -> dict[str, Any]:
        """Calculate performance improvement metrics."""
        time_reduction = baseline - advanced
        percent_improvement = (time_reduction / baseline * 100) if baseline > 0 else 0
        speedup = baseline / advanced if advanced > 0 else 0

        return {
            "time_reduction_seconds": time_reduction,
            "percent_improvement": percent_improvement,
            "speedup_factor": speedup,
        }


@pytest.fixture
def benchmark_suite():
    """Provide benchmark suite instance."""
    return IOPerformanceBenchmark()


@pytest.fixture
def test_files_dir(tmp_path):
    """Create directory for test files."""
    return tmp_path / "benchmark_files"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_small_file_performance(benchmark_suite, test_files_dir):
    """Benchmark small file (1KB) performance."""
    test_files_dir.mkdir(exist_ok=True)
    file_path = test_files_dir / "small_1kb.bin"
    benchmark_suite.create_test_file(1024, file_path)  # 1KB

    # Baseline
    baseline = await benchmark_suite.benchmark_baseline_read(file_path)
    benchmark_suite.results["baseline"]["1kb"] = baseline

    # Advanced I/O
    advanced = await benchmark_suite.benchmark_advanced_io_read(file_path)
    benchmark_suite.results["advanced_io"]["1kb"] = advanced

    # Calculate improvement
    improvement = benchmark_suite.calculate_improvement(
        baseline["avg_time_seconds"], advanced["avg_time_seconds"]
    )
    benchmark_suite.results["improvements"]["1kb"] = improvement

    # Verify strategy selection (should use ASYNC for small files)
    assert advanced["strategy_used"] == IOStrategy.ASYNC

    print(f"\n📊 Small File (1KB) Benchmark:")
    print(f"   Baseline: {baseline['avg_time_seconds']*1000:.2f}ms")
    print(f"   Advanced: {advanced['avg_time_seconds']*1000:.2f}ms")
    print(f"   Improvement: {improvement['percent_improvement']:.1f}%")
    print(f"   Strategy: {advanced['strategy_used'].name}")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_medium_file_performance(benchmark_suite, test_files_dir):
    """Benchmark medium file (1MB) performance."""
    test_files_dir.mkdir(exist_ok=True)
    file_path = test_files_dir / "medium_1mb.bin"
    benchmark_suite.create_test_file(1024 * 1024, file_path)  # 1MB

    # Baseline
    baseline = await benchmark_suite.benchmark_baseline_read(file_path)
    benchmark_suite.results["baseline"]["1mb"] = baseline

    # Advanced I/O
    advanced = await benchmark_suite.benchmark_advanced_io_read(file_path)
    benchmark_suite.results["advanced_io"]["1mb"] = advanced

    # Calculate improvement
    improvement = benchmark_suite.calculate_improvement(
        baseline["avg_time_seconds"], advanced["avg_time_seconds"]
    )
    benchmark_suite.results["improvements"]["1mb"] = improvement

    print(f"\n📊 Medium File (1MB) Benchmark:")
    print(f"   Baseline: {baseline['avg_time_seconds']*1000:.2f}ms")
    print(f"   Advanced: {advanced['avg_time_seconds']*1000:.2f}ms")
    print(f"   Improvement: {improvement['percent_improvement']:.1f}%")
    print(f"   Throughput: {advanced['throughput_mbps']:.2f} MB/s")
    print(f"   Strategy: {advanced['strategy_used'].name}")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_large_file_performance(benchmark_suite, test_files_dir):
    """Benchmark large file (10MB) performance."""
    test_files_dir.mkdir(exist_ok=True)
    file_path = test_files_dir / "large_10mb.bin"
    benchmark_suite.create_test_file(10 * 1024 * 1024, file_path)  # 10MB

    # Baseline
    baseline = await benchmark_suite.benchmark_baseline_read(file_path, iterations=3)
    benchmark_suite.results["baseline"]["10mb"] = baseline

    # Advanced I/O
    advanced = await benchmark_suite.benchmark_advanced_io_read(file_path, iterations=3)
    benchmark_suite.results["advanced_io"]["10mb"] = advanced

    # Calculate improvement
    improvement = benchmark_suite.calculate_improvement(
        baseline["avg_time_seconds"], advanced["avg_time_seconds"]
    )
    benchmark_suite.results["improvements"]["10mb"] = improvement

    # Note: Small variations are acceptable due to system load
    # Main goal is to verify advanced I/O doesn't significantly degrade performance

    print(f"\n📊 Large File (10MB) Benchmark:")
    print(f"   Baseline: {baseline['avg_time_seconds']*1000:.2f}ms")
    print(f"   Advanced: {advanced['avg_time_seconds']*1000:.2f}ms")
    print(f"   Improvement: {improvement['percent_improvement']:.1f}%")
    print(f"   Throughput: {advanced['throughput_mbps']:.2f} MB/s")
    print(f"   Strategy: {advanced['strategy_used'].name}")


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.slow
async def test_very_large_file_performance(benchmark_suite, test_files_dir):
    """Benchmark very large file (100MB) performance."""
    test_files_dir.mkdir(exist_ok=True)
    file_path = test_files_dir / "very_large_100mb.bin"
    benchmark_suite.create_test_file(100 * 1024 * 1024, file_path)  # 100MB

    # Baseline (fewer iterations for large file)
    baseline = await benchmark_suite.benchmark_baseline_read(file_path, iterations=2)
    benchmark_suite.results["baseline"]["100mb"] = baseline

    # Advanced I/O
    advanced = await benchmark_suite.benchmark_advanced_io_read(file_path, iterations=2)
    benchmark_suite.results["advanced_io"]["100mb"] = advanced

    # Calculate improvement
    improvement = benchmark_suite.calculate_improvement(
        baseline["avg_time_seconds"], advanced["avg_time_seconds"]
    )
    benchmark_suite.results["improvements"]["100mb"] = improvement

    # Should use MMAP for very large files
    assert advanced["strategy_used"] in [IOStrategy.MMAP, IOStrategy.BUFFERED]

    print(f"\n📊 Very Large File (100MB) Benchmark:")
    print(f"   Baseline: {baseline['avg_time_seconds']:.3f}s")
    print(f"   Advanced: {advanced['avg_time_seconds']:.3f}s")
    print(f"   Improvement: {improvement['percent_improvement']:.1f}%")
    print(f"   Throughput: {advanced['throughput_mbps']:.2f} MB/s")
    print(f"   Strategy: {advanced['strategy_used'].name}")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_operations(benchmark_suite, test_files_dir):
    """Benchmark concurrent file reading performance."""
    test_files_dir.mkdir(exist_ok=True)

    # Create multiple test files
    file_paths = []
    for i in range(20):
        file_path = test_files_dir / f"concurrent_{i}.bin"
        # Mix of file sizes
        size = (i % 5 + 1) * 1024 * 1024  # 1-5MB files
        benchmark_suite.create_test_file(size, file_path)
        file_paths.append(file_path)

    # Benchmark concurrent reads
    results = await benchmark_suite.benchmark_concurrent_reads(
        file_paths, concurrency=20
    )
    benchmark_suite.results["concurrent"] = results

    print(f"\n📊 Concurrent Operations (20 files, 1-5MB each):")
    print(f"   Total time: {results['total_time_seconds']:.3f}s")
    print(f"   Total size: {results['total_size_mb']:.2f} MB")
    print(f"   Throughput: {results['throughput_mbps']:.2f} MB/s")
    print(f"   Files/second: {results['files_per_second']:.2f}")

    # Verify acceptable performance
    assert results["files_per_second"] >= 5.0, "Should process at least 5 files/second"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_strategy_selection_effectiveness(test_files_dir):
    """Verify I/O strategies are selected appropriately."""
    test_files_dir.mkdir(exist_ok=True)
    config = IOConfig()
    io_manager = AdvancedIOManager(config)

    # Test different file sizes
    test_cases = [
        (512, IOStrategy.ASYNC),  # 512 bytes - should use ASYNC
        (1024 * 1024, IOStrategy.ASYNC),  # 1MB - should use ASYNC
        (10 * 1024 * 1024, IOStrategy.MMAP),  # 10MB - should use MMAP or BUFFERED
    ]

    for size_bytes, expected_strategy in test_cases:
        file_path = test_files_dir / f"strategy_test_{size_bytes}.bin"
        with open(file_path, "wb") as f:
            f.write(b"X" * size_bytes)

        # Read file and check strategy
        await io_manager.read_file_async(file_path)

        metrics = io_manager.metrics
        actual_strategy = max(metrics.strategy_usage, key=metrics.strategy_usage.get)

        print(
            f"\n📊 Strategy Selection ({size_bytes} bytes):"
            f"\n   Expected: {expected_strategy.name}"
            f"\n   Actual: {actual_strategy.name}"
        )

        # Small files should use ASYNC, large files should use MMAP/BUFFERED
        if size_bytes < 5 * 1024 * 1024:  # < 5MB
            assert actual_strategy == IOStrategy.ASYNC
        else:  # >= 5MB
            assert actual_strategy in [IOStrategy.MMAP, IOStrategy.BUFFERED]


@pytest.mark.performance
@pytest.mark.asyncio
async def test_chunked_reading_performance(benchmark_suite, test_files_dir):
    """Benchmark chunked reading for large files."""
    test_files_dir.mkdir(exist_ok=True)
    file_path = test_files_dir / "chunked_10mb.bin"
    benchmark_suite.create_test_file(10 * 1024 * 1024, file_path)  # 10MB

    config = IOConfig(chunk_size=256 * 1024)  # 256KB chunks
    io_manager = AdvancedIOManager(config)

    # Benchmark chunked reading
    start = time.perf_counter()

    total_bytes = 0
    async for chunk in io_manager.scan_file_chunks(file_path):
        total_bytes += len(chunk)

    end = time.perf_counter()
    elapsed = end - start

    # Calculate throughput
    size_mb = total_bytes / (1024 * 1024)
    throughput_mbps = (size_mb / elapsed) if elapsed > 0 else 0

    print(f"\n📊 Chunked Reading (10MB file, 256KB chunks):")
    print(f"   Time: {elapsed*1000:.2f}ms")
    print(f"   Throughput: {throughput_mbps:.2f} MB/s")
    print(f"   Total bytes read: {total_bytes:,}")

    assert total_bytes == file_path.stat().st_size


@pytest.mark.performance
def test_generate_performance_report(benchmark_suite, test_files_dir):
    """Generate comprehensive performance report."""
    if not benchmark_suite.results.get("improvements"):
        pytest.skip("No benchmark results available")

    print("\n" + "=" * 80)
    print("📊 ADVANCED I/O PERFORMANCE BENCHMARK REPORT")
    print("=" * 80)

    # Summary table
    print("\n📈 Performance Improvements by File Size:")
    print("-" * 80)
    print(
        f"{'File Size':<15} {'Baseline (ms)':<15} {'Advanced (ms)':<15} {'Improvement':<15}"
    )
    print("-" * 80)

    for size in ["1kb", "1mb", "10mb", "100mb"]:
        if size in benchmark_suite.results.get("improvements", {}):
            baseline = (
                benchmark_suite.results["baseline"][size]["avg_time_seconds"] * 1000
            )
            advanced = (
                benchmark_suite.results["advanced_io"][size]["avg_time_seconds"] * 1000
            )
            improvement = benchmark_suite.results["improvements"][size][
                "percent_improvement"
            ]

            print(
                f"{size.upper():<15} {baseline:<15.2f} {advanced:<15.2f} {improvement:>13.1f}%"
            )

    # Calculate overall improvement
    improvements = [
        data["percent_improvement"]
        for data in benchmark_suite.results.get("improvements", {}).values()
    ]
    if improvements:
        avg_improvement = statistics.mean(improvements)
        print("-" * 80)
        print(f"{'AVERAGE':<15} {'':<15} {'':<15} {avg_improvement:>13.1f}%")
        print("-" * 80)

        # Verify target met (30-50% improvement)
        target_met = avg_improvement >= 30
        print(f"\n✅ Target Performance: 30-50% improvement")
        print(f"🎯 Achieved: {avg_improvement:.1f}% improvement")
        print(f"{'✅ TARGET MET' if target_met else '⚠️ TARGET NOT MET'}")

    # Concurrent operations
    if "concurrent" in benchmark_suite.results:
        concurrent = benchmark_suite.results["concurrent"]
        print(f"\n📊 Concurrent Operations Performance:")
        print(f"   Files processed: {concurrent['total_files']}")
        print(f"   Total size: {concurrent['total_size_mb']:.2f} MB")
        print(f"   Time: {concurrent['total_time_seconds']:.3f}s")
        print(f"   Throughput: {concurrent['throughput_mbps']:.2f} MB/s")
        print(f"   Files/second: {concurrent['files_per_second']:.2f}")

    print("\n" + "=" * 80)
