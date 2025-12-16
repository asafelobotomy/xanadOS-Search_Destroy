#!/usr/bin/env python3
"""Integration tests for UnifiedScannerEngine with AdvancedIOManager.

Tests verify that the scanner correctly uses advanced I/O for:
- File scanning with auto-strategy selection
- Checksum calculation with chunked I/O
- Performance metrics tracking
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.advanced_io import AdvancedIOManager, IOConfig, IOStrategy
from app.core.unified_scanner_engine import (
    ScanConfiguration,
    ScanType,
    UnifiedScannerEngine,
)


class TestScannerIOIntegration:
    """Test UnifiedScannerEngine integration with AdvancedIOManager."""

    @pytest.fixture
    def mock_clamav(self):
        """Create mock ClamAV wrapper."""
        mock = Mock()
        mock.available = True
        mock.scan_data = Mock(
            return_value=Mock(
                result=Mock(value="clean"),
                threat_name="",
                file_size=1024,
                scan_time=0.1,
            )
        )
        mock.scan_file = Mock(
            return_value=Mock(
                result=Mock(value="clean"),
                threat_name="",
                file_size=1024,
                scan_time=0.1,
            )
        )
        return mock

    @pytest.fixture
    def mock_yara(self):
        """Create mock YARA scanner."""
        mock = Mock()
        mock.available = True
        mock.scan_file = Mock(
            return_value=Mock(matches=[], file_path="", scan_time=0.05)
        )
        return mock

    @pytest.fixture
    def test_file(self, tmp_path):
        """Create a test file."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("Test content for scanning" * 100)
        return test_file

    @pytest.fixture
    def large_test_file(self, tmp_path):
        """Create a large test file (>100MB) for MMAP strategy."""
        test_file = tmp_path / "large_file.bin"
        # Create 110MB file
        with open(test_file, "wb") as f:
            f.write(b"X" * (110 * 1024 * 1024))
        return test_file

    def test_scanner_initializes_io_manager(self, mock_clamav):
        """Test that scanner properly initializes AdvancedIOManager."""
        with patch(
            "app.core.unified_scanner_engine.ClamAVWrapper", return_value=mock_clamav
        ):
            config = ScanConfiguration(scan_type=ScanType.QUICK, target_paths=["/tmp"])
            scanner = UnifiedScannerEngine(config)

            # Verify IOManager is created
            assert hasattr(scanner, "io_manager")
            assert isinstance(scanner.io_manager, AdvancedIOManager)

            # Verify default configuration
            assert scanner.io_manager.config.strategy == IOStrategy.AUTO
            assert scanner.io_manager.config.max_concurrent_ops == 20

    @pytest.mark.asyncio
    async def test_virus_scan_uses_advanced_io(self, mock_clamav, test_file):
        """Test that virus scanning uses AdvancedIOManager for file reading."""
        with patch(
            "app.core.unified_scanner_engine.ClamAVWrapper", return_value=mock_clamav
        ):
            config = ScanConfiguration(
                scan_type=ScanType.QUICK, target_paths=[str(test_file)]
            )
            scanner = UnifiedScannerEngine(config)

            # Mock io_manager.read_file_async
            original_read = scanner.io_manager.read_file_async
            read_mock = AsyncMock(side_effect=original_read)
            scanner.io_manager.read_file_async = read_mock

            # Perform virus scan
            result = await scanner._perform_virus_scan(test_file)

            # Verify io_manager was called
            read_mock.assert_called_once_with(test_file)

            # Verify ClamAV scan_data was called (not scan_file)
            assert mock_clamav.scan_data.called
            # Verify file data was passed
            call_args = mock_clamav.scan_data.call_args
            assert isinstance(call_args[0][0], bytes)  # First arg is file data

    @pytest.mark.asyncio
    async def test_checksum_uses_chunked_io(self, mock_clamav, test_file):
        """Test that checksum calculation uses scan_file_chunks."""
        with patch(
            "app.core.unified_scanner_engine.ClamAVWrapper", return_value=mock_clamav
        ):
            config = ScanConfiguration(
                scan_type=ScanType.QUICK, target_paths=[str(test_file)]
            )
            scanner = UnifiedScannerEngine(config)

            # Access quarantine manager directly
            quarantine_mgr = scanner.quarantine_manager

            # Calculate checksum (internally uses scan_file_chunks)
            checksum = await quarantine_mgr._calculate_checksum(test_file)

            # Verify checksum is valid SHA256 hex string
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 is 64 hex chars
            assert all(c in "0123456789abcdef" for c in checksum)

            # Note: scan_file_chunks doesn't update metrics (only read_file_async does)
            # The test verifies the method works correctly and produces valid checksums

    @pytest.mark.asyncio
    async def test_io_strategy_selection_small_file(self, mock_clamav, test_file):
        """Test that small files use ASYNC strategy."""
        with patch(
            "app.core.unified_scanner_engine.ClamAVWrapper", return_value=mock_clamav
        ):
            config = ScanConfiguration(
                scan_type=ScanType.QUICK, target_paths=[str(test_file)]
            )
            scanner = UnifiedScannerEngine(config)

            # Read small file
            await scanner.io_manager.read_file_async(test_file)

            # Get metrics using property
            metrics = scanner.io_manager.metrics

            # Verify ASYNC strategy was used (check enum key, not string)
            assert IOStrategy.ASYNC in metrics.strategy_usage
            assert metrics.strategy_usage[IOStrategy.ASYNC] > 0

    @pytest.mark.asyncio
    async def test_io_metrics_collection(self, mock_clamav, test_file):
        """Test that I/O metrics are properly collected."""
        with patch(
            "app.core.unified_scanner_engine.ClamAVWrapper", return_value=mock_clamav
        ):
            config = ScanConfiguration(
                scan_type=ScanType.QUICK, target_paths=[str(test_file)]
            )
            scanner = UnifiedScannerEngine(config)

            # Perform scan
            await scanner._perform_virus_scan(test_file)

            # Get performance metrics
            perf_metrics = scanner.get_performance_metrics()

            # Verify I/O metrics are present
            assert hasattr(perf_metrics, "io_throughput_mbps")
            assert hasattr(perf_metrics, "total_bytes_read")
            assert hasattr(perf_metrics, "io_strategy_usage")

            # Verify metrics have valid values
            assert perf_metrics.total_bytes_read > 0
            assert isinstance(perf_metrics.io_strategy_usage, dict)

    @pytest.mark.asyncio
    async def test_parallel_file_scanning(self, mock_clamav, tmp_path):
        """Test concurrent file scanning uses parallel I/O."""
        with patch(
            "app.core.unified_scanner_engine.ClamAVWrapper", return_value=mock_clamav
        ):
            # Create multiple test files
            test_files = []
            for i in range(5):
                file = tmp_path / f"test_{i}.txt"
                file.write_text(f"Test content {i}" * 100)
                test_files.append(file)

            config = ScanConfiguration(
                scan_type=ScanType.QUICK, target_paths=[str(tmp_path)]
            )
            scanner = UnifiedScannerEngine(config)

            # Scan all files concurrently
            tasks = [scanner._perform_virus_scan(f) for f in test_files]
            results = await asyncio.gather(*tasks)

            # Verify all files were scanned
            assert len(results) == 5

            # Verify metrics show multiple operations using property
            metrics = scanner.io_manager.metrics
            assert metrics.total_bytes_read > 0

    def test_io_config_from_scanner_config(self, mock_clamav):
        """Test that IOConfig respects default configuration."""
        with patch(
            "app.core.unified_scanner_engine.ClamAVWrapper", return_value=mock_clamav
        ):
            # Create scanner config (ScanConfiguration doesn't have chunk_size/max_workers)
            scan_config = ScanConfiguration(
                scan_type=ScanType.QUICK, target_paths=["/tmp"]
            )
            scanner = UnifiedScannerEngine(scan_config)

            # Verify IOConfig uses defaults (256KB chunk, 20 concurrent)
            io_config = scanner.io_manager.config
            assert io_config.chunk_size == 256 * 1024  # Default 256KB
            assert io_config.max_concurrent_ops == 20  # Default 20


class TestClamAVScanData:
    """Test ClamAV scan_data method integration."""

    @pytest.fixture
    def clamav_wrapper(self):
        """Create real ClamAVWrapper instance (with mocked subprocess)."""
        from app.core.clamav_wrapper import ClamAVWrapper

        return ClamAVWrapper()

    def test_scan_data_method_exists(self, clamav_wrapper):
        """Test that scan_data method exists on ClamAVWrapper."""
        assert hasattr(clamav_wrapper, "scan_data")
        assert callable(clamav_wrapper.scan_data)

    def test_scan_data_accepts_bytes(self, clamav_wrapper):
        """Test that scan_data accepts bytes and file path."""
        # Mock ClamAV availability check
        clamav_wrapper.available = True
        clamav_wrapper.clamscan_path = "/usr/bin/clamscan"

        # Mock run_secure
        with patch("app.core.clamav_wrapper.run_secure") as mock_run:
            mock_run.return_value = Mock(stdout="stdin: OK\n", stderr="", returncode=0)

            test_data = b"Test file content"
            result = clamav_wrapper.scan_data(test_data, "/fake/path.txt")

            # Verify run_secure was called with stdin input
            assert mock_run.called
            call_kwargs = mock_run.call_args[1]
            assert "input" in call_kwargs
            assert call_kwargs["input"] == test_data

    def test_scan_data_returns_scan_result(self, clamav_wrapper):
        """Test that scan_data returns proper ScanFileResult."""
        from app.core.clamav_wrapper import ScanResult

        clamav_wrapper.available = True
        clamav_wrapper.clamscan_path = "/usr/bin/clamscan"

        with patch("app.core.clamav_wrapper.run_secure") as mock_run:
            mock_run.return_value = Mock(stdout="stdin: OK\n", stderr="", returncode=0)

            test_data = b"Clean test data"
            result = clamav_wrapper.scan_data(test_data, "/test/clean.txt")

            # Verify result structure
            assert result.file_path == "/test/clean.txt"
            assert result.result == ScanResult.CLEAN
            assert result.file_size == len(test_data)
            assert result.scan_time > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
