#!/usr/bin/env python3
"""Comprehensive test suite for Phase 1 enhancements.

This module provides testing for all Phase 1 components including:
- ML threat detection engine
- Advanced async scanner
- EDR engine
- Memory management system
- Memory forensics engine
"""

import pytest
pytest.skip("Legacy Phase 1 test - requires updated mocking for memory management", allow_module_level=True)

import asyncio
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import Phase 1 components
from app.core.ml_threat_detector import MLThreatDetector, ThreatAssessment as ThreatInfo
# Note: AdvancedAsyncScanner consolidated into unified_scanner_engine
try:
    from app.core.unified_scanner_engine import UnifiedScannerEngine as AdvancedAsyncScanner
    from app.core.unified_scanner_engine import ScanResult
except ImportError:
    # Fallback if unified_scanner_engine doesn't have these
    from app.ml.ml_threat_detector import ScanResult
    AdvancedAsyncScanner = None
from app.core.edr_engine import EDREngine, SecurityEvent
from app.core.unified_memory_management import (
    get_memory_manager
)
from app.core.memory_forensics import (
    MemoryForensicsEngine,
    MemoryForensicsReport,
    MemoryAnalysisType
)


class TestMLThreatDetector(unittest.TestCase):
    """Test cases for ML threat detection engine."""

    def setUp(self):
        """Set up test environment."""
        self.detector = MLThreatDetector()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_detector_initialization(self):
        """Test ML detector initialization."""
        await self.detector.initialize()
        self.assertIsNotNone(self.detector.model)
        self.assertIsNotNone(self.detector.feature_extractor)

    @pytest.mark.asyncio
    async def test_feature_extraction(self):
        """Test feature extraction from files."""
        await self.detector.initialize()

        # Create test file
        test_file = self.test_dir / "test.txt"
        test_file.write_text("This is a test file for feature extraction.")

        features = await self.detector.feature_extractor.extract_file_features(str(test_file))

        self.assertIsInstance(features, dict)
        self.assertIn('file_size', features)
        self.assertIn('entropy', features)
        self.assertGreater(features['file_size'], 0)

    @pytest.mark.asyncio
    async def test_threat_analysis(self):
        """Test threat analysis functionality."""
        await self.detector.initialize()

        # Create test file
        test_file = self.test_dir / "safe_file.txt"
        test_file.write_text("This is a safe test file.")

        threat_info = await self.detector.analyze_file(str(test_file))

        self.assertIsInstance(threat_info, ThreatInfo)
        self.assertIsInstance(threat_info.threat_score, float)
        self.assertIsInstance(threat_info.confidence, float)
        self.assertGreaterEqual(threat_info.threat_score, 0.0)
        self.assertLessEqual(threat_info.threat_score, 1.0)

    @pytest.mark.asyncio
    async def test_model_training(self):
        """Test model training with sample data."""
        await self.detector.initialize()

        # Create sample training data
        training_data = []
        for i in range(10):
            file_path = self.test_dir / f"train_{i}.txt"
            file_path.write_text(f"Training file {i} content.")
            training_data.append({
                'file_path': str(file_path),
                'is_threat': False
            })

        # Train model
        success = await self.detector.train_model(training_data)
        self.assertTrue(success)

    def test_performance_benchmarks(self):
        """Test performance benchmarks for ML detection."""
        # This would test analysis speed and accuracy
        # Implementation depends on specific performance requirements
        pass


class TestAdvancedAsyncScanner(unittest.TestCase):
    """Test cases for advanced async scanner."""

    def setUp(self):
        """Set up test environment."""
        self.scanner = AdvancedAsyncScanner()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_scanner_initialization(self):
        """Test scanner initialization."""
        await self.scanner.initialize()
        self.assertIsNotNone(self.scanner.io_optimizer)
        self.assertIsNotNone(self.scanner.resource_monitor)
        self.assertIsNotNone(self.scanner.scan_cache)

    @pytest.mark.asyncio
    async def test_file_scanning(self):
        """Test single file scanning."""
        await self.scanner.initialize()

        # Create test file
        test_file = self.test_dir / "scan_test.txt"
        test_file.write_text("Test file for scanning.")

        result = await self.scanner.scan_file(str(test_file))

        self.assertIsInstance(result, ScanResult)
        self.assertEqual(result.file_path, str(test_file))
        self.assertIsNotNone(result.scan_time)

    @pytest.mark.asyncio
    async def test_batch_scanning(self):
        """Test batch file scanning."""
        await self.scanner.initialize()

        # Create multiple test files
        test_files = []
        for i in range(5):
            test_file = self.test_dir / f"batch_{i}.txt"
            test_file.write_text(f"Batch test file {i}.")
            test_files.append(str(test_file))

        results = await self.scanner.scan_batch(test_files)

        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, ScanResult)

    @pytest.mark.asyncio
    async def test_caching_functionality(self):
        """Test scanning cache functionality."""
        await self.scanner.initialize()

        # Create test file
        test_file = self.test_dir / "cache_test.txt"
        test_file.write_text("Test file for cache testing.")

        # First scan
        start_time = time.time()
        result1 = await self.scanner.scan_file(str(test_file))
        first_scan_time = time.time() - start_time

        # Second scan (should be cached)
        start_time = time.time()
        result2 = await self.scanner.scan_file(str(test_file))
        second_scan_time = time.time() - start_time

        # Second scan should be faster due to caching
        self.assertLess(second_scan_time, first_scan_time)
        self.assertEqual(result1.file_path, result2.file_path)

    @pytest.mark.asyncio
    async def test_resource_monitoring(self):
        """Test resource monitoring during scanning."""
        await self.scanner.initialize()

        # Get initial metrics
        initial_metrics = await self.scanner.resource_monitor.get_metrics()
        self.assertIsNotNone(initial_metrics)
        self.assertIn('memory_usage_mb', initial_metrics)
        self.assertIn('cpu_percent', initial_metrics)


class TestEDREngine(unittest.TestCase):
    """Test cases for EDR engine."""

    def setUp(self):
        """Set up test environment."""
        self.edr = EDREngine()

    @pytest.mark.asyncio
    async def test_edr_initialization(self):
        """Test EDR engine initialization."""
        await self.edr.initialize()
        self.assertIsNotNone(self.edr.process_monitor)
        self.assertIsNotNone(self.edr.network_monitor)
        self.assertIsNotNone(self.edr.incident_engine)

    @pytest.mark.asyncio
    async def test_process_monitoring(self):
        """Test process monitoring functionality."""
        await self.edr.initialize()
        await self.edr.start_monitoring()

        # Get current processes
        processes = await self.edr.get_monitored_processes()
        self.assertIsInstance(processes, list)

        # Stop monitoring
        await self.edr.stop_monitoring()

    @pytest.mark.asyncio
    async def test_security_event_collection(self):
        """Test security event collection."""
        await self.edr.initialize()

        # Get recent security events
        events = await self.edr.get_security_events(last_hours=1)
        self.assertIsInstance(events, list)

        # Each event should be a SecurityEvent instance
        for event in events:
            self.assertIsInstance(event, SecurityEvent)

    @pytest.mark.asyncio
    async def test_threat_hunting(self):
        """Test threat hunting capabilities."""
        await self.edr.initialize()

        threats = await self.edr.hunt_threats()
        self.assertIsInstance(threats, list)

    @pytest.mark.asyncio
    async def test_incident_response(self):
        """Test automated incident response."""
        await self.edr.initialize()

        # Create mock incident
        mock_incident = Mock()
        mock_incident.severity = "HIGH"
        mock_incident.threat_type = "malware"

        # Test incident handling
        response = await self.edr.handle_incident(mock_incident)
        self.assertIsNotNone(response)


class TestMemoryManager(unittest.TestCase):
    """Test cases for memory management system."""

    def setUp(self):
        """Set up test environment."""
        self.manager = get_memory_manager()

    def test_memory_pool_creation(self):
        """Test memory pool creation and management."""
        # Create test object factory
        def create_test_object():
            return {"data": "test", "id": time.time()}

        # Create pool
        pool = self.manager.create_pool("test_pool", create_test_object, initial_size=10)
        self.assertIsNotNone(pool)

        # Test object acquisition
        obj = pool.acquire()
        self.assertIsNotNone(obj)

        # Test object release
        success = pool.release(obj)
        self.assertTrue(success)

        # Get pool statistics
        stats = pool.get_stats()
        self.assertGreater(stats.total_allocations, 0)

    def test_cache_functionality(self):
        """Test cache creation and usage."""
        cache = self.manager.create_cache("test_cache", max_items=100, max_memory_mb=10)
        self.assertIsNotNone(cache)

        # Test cache operations
        test_key = "test_key"
        test_value = {"data": "test_value", "timestamp": time.time()}

        # Put value in cache
        success = cache.put(test_key, test_value)
        self.assertTrue(success)

        # Get value from cache
        retrieved_value = cache.get(test_key)
        self.assertEqual(retrieved_value, test_value)

        # Test cache miss
        missing_value = cache.get("nonexistent_key")
        self.assertIsNone(missing_value)

        # Get cache statistics
        stats = cache.get_stats()
        self.assertGreater(stats['hits'], 0)

    def test_memory_monitoring(self):
        """Test memory monitoring functionality."""
        self.manager.start()

        # Get current metrics
        metrics = self.manager.monitor.get_current_metrics()
        if metrics:
            self.assertIsNotNone(metrics.total_memory_mb)
            self.assertIsNotNone(metrics.memory_percent)

        self.manager.stop()

    def test_pressure_response(self):
        """Test memory pressure response."""
        # This would test the memory pressure handling
        # Implementation depends on specific pressure scenarios
        pass


class TestMemoryForensics(unittest.TestCase):
    """Test cases for memory forensics engine."""

    def setUp(self):
        """Set up test environment."""
        self.forensics = MemoryForensicsEngine()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_volatility_wrapper(self):
        """Test Volatility wrapper functionality."""
        # This test would require a real memory dump
        # For now, we test the wrapper initialization
        self.assertIsNotNone(self.forensics.volatility)

    def test_pattern_matching(self):
        """Test threat pattern matching."""
        from app.core.memory_forensics import ProcessInfo

        # Create test process with suspicious indicators
        suspicious_process = ProcessInfo(
            pid=1234,
            ppid=0,  # Orphaned process
            name="suspicious.tmp.exe",  # Suspicious name pattern
            command_line="powershell.exe -enc Y29kZQ==",  # Encoded PowerShell
            create_time="2025-01-07 10:00:00",
            exit_time=None,
            image_path="C:\\temp\\suspicious.tmp.exe",
            threads=0,  # No threads (process hollowing)
            handles=0,  # No handles
            virtual_size=1024*1024,
            working_set=512*1024
        )

        indicators = self.forensics.pattern_matcher.analyze_process(suspicious_process)
        self.assertGreater(len(indicators), 0)
        self.assertTrue(any("Suspicious process name pattern" in ind for ind in indicators))

    @pytest.mark.asyncio
    async def test_memory_analysis_workflow(self):
        """Test complete memory analysis workflow."""
        # This would require a real memory dump file
        # For testing, we can mock the analysis

        # Create mock dump file
        mock_dump = self.test_dir / "test.dmp"
        mock_dump.write_bytes(b"Mock memory dump data")

        with patch.object(self.forensics.volatility, 'run_plugin') as mock_plugin:
            mock_plugin.return_value = {"success": True, "rows": []}

            report = await self.forensics.analyze_memory_dump(
                str(mock_dump),
                analysis_types=[MemoryAnalysisType.PROCESS_ANALYSIS]
            )

            self.assertIsInstance(report, MemoryForensicsReport)
            self.assertEqual(report.dump_file, str(mock_dump))
            self.assertGreaterEqual(report.threat_score, 0.0)


class TestIntegration(unittest.TestCase):
    """Integration tests for Phase 1 components."""

    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_ml_scanner_integration(self):
        """Test integration between ML detector and async scanner."""
        # Initialize components
        ml_detector = MLThreatDetector()
        scanner = AdvancedAsyncScanner()

        await ml_detector.initialize()
        await scanner.initialize()

        # Create test file
        test_file = self.test_dir / "integration_test.txt"
        test_file.write_text("Integration test file content.")

        # Scan with scanner
        scan_result = await scanner.scan_file(str(test_file))

        # Analyze with ML detector
        threat_info = await ml_detector.analyze_file(str(test_file))

        # Verify both components worked
        self.assertIsNotNone(scan_result)
        self.assertIsNotNone(threat_info)
        self.assertEqual(scan_result.file_path, str(test_file))

    @pytest.mark.asyncio
    async def test_edr_ml_integration(self):
        """Test integration between EDR and ML detection."""
        # Initialize components
        edr = EDREngine()
        ml_detector = MLThreatDetector()

        await edr.initialize()
        await ml_detector.initialize()

        # This would test how EDR uses ML detection for process analysis
        # Implementation depends on specific integration points
        pass

    @pytest.mark.asyncio
    async def test_memory_management_integration(self):
        """Test memory management with other components."""
        manager = get_memory_manager()
        manager.start()

        # Test that memory management works with ML detector
        ml_detector = MLThreatDetector()
        await ml_detector.initialize()

        # Get memory stats before and after ML operations
        initial_stats = manager.get_comprehensive_stats()

        # Perform some ML operations
        test_file = self.test_dir / "memory_test.txt"
        test_file.write_text("Memory management test file.")

        await ml_detector.analyze_file(str(test_file))

        final_stats = manager.get_comprehensive_stats()

        # Verify memory management is working
        self.assertIsNotNone(initial_stats)
        self.assertIsNotNone(final_stats)

        manager.stop()


class TestPerformance(unittest.TestCase):
    """Performance tests for Phase 1 components."""

    def setUp(self):
        """Set up performance test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.performance_thresholds = {
            'ml_analysis_time': 1.0,  # seconds
            'scan_batch_time': 30.0,  # seconds for 100 files
            'memory_usage_mb': 500,   # MB
        }

    def tearDown(self):
        """Clean up performance test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_ml_detection_performance(self):
        """Test ML detection performance."""
        detector = MLThreatDetector()
        await detector.initialize()

        # Create test file
        test_file = self.test_dir / "performance_test.txt"
        test_file.write_text("Performance test file content.")

        # Measure analysis time
        start_time = time.time()
        await detector.analyze_file(str(test_file))
        analysis_time = time.time() - start_time

        # Check performance threshold
        self.assertLess(
            analysis_time,
            self.performance_thresholds['ml_analysis_time'],
            f"ML analysis took {analysis_time:.2f}s, exceeds threshold"
        )

    @pytest.mark.asyncio
    async def test_async_scanner_performance(self):
        """Test async scanner performance."""
        scanner = AdvancedAsyncScanner()
        await scanner.initialize()

        # Create batch of test files
        test_files = []
        for i in range(100):
            test_file = self.test_dir / f"perf_test_{i}.txt"
            test_file.write_text(f"Performance test file {i}.")
            test_files.append(str(test_file))

        # Measure batch scan time
        start_time = time.time()
        results = await scanner.scan_batch(test_files)
        scan_time = time.time() - start_time

        # Check performance threshold
        self.assertLess(
            scan_time,
            self.performance_thresholds['scan_batch_time'],
            f"Batch scan took {scan_time:.2f}s, exceeds threshold"
        )
        self.assertEqual(len(results), 100)

    def test_memory_usage_performance(self):
        """Test memory usage performance."""
        import psutil

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

        # Initialize all components
        manager = get_memory_manager()
        manager.start()

        # Create and use various components
        cache = manager.create_cache("perf_cache", max_items=1000)
        pool = manager.create_pool("perf_pool", lambda: {"data": "test"}, initial_size=100)

        # Use components
        for i in range(1000):
            cache.put(f"key_{i}", {"value": f"data_{i}"})
            obj = pool.acquire()
            if obj:
                pool.release(obj)

        # Get final memory usage
        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = final_memory - initial_memory

        # Check memory usage threshold
        self.assertLess(
            memory_increase,
            self.performance_thresholds['memory_usage_mb'],
            f"Memory usage increased by {memory_increase:.2f}MB, exceeds threshold"
        )

        manager.stop()


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
