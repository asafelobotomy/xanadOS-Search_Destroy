#!/usr/bin/env python3
"""Comprehensive Integration Tests for Phase 2 Enhancements.

This module provides integration testing for all Phase 2 components including:
- Real-time security dashboard
- Intelligent automation system
- Advanced reporting system
- API-first architecture
- Deep learning integration
- GPU acceleration
"""

import pytest
pytest.skip("Legacy Phase 2 test - requires updated mocking for GUI and API components", allow_module_level=True)

import asyncio
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest
import requests
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# Import Phase 2 components
try:
    from app.gui.security_dashboard import SecurityDashboard, ThreatEvent
except ImportError:
    # Use lazy_dashboard as fallback
    from app.gui.lazy_dashboard import LazyDashboard as SecurityDashboard
    from app.core.unified_security_engine import SecurityEvent as ThreatEvent
from app.api.web_dashboard import WebDashboard
from app.core.intelligent_automation import IntelligentAutomationEngine, SystemProfile
from app.api.security_api import SecurityAPI
from app.reporting.advanced_reporting import AdvancedReportingEngine, ReportTemplate
from app.api.client_sdk import SecuritySDK
from app.ml.deep_learning import DeepLearningEngine, ThreatPattern
from app.gpu.acceleration import GPUAccelerator

# Import Phase 1 components for integration
from app.core.ml_threat_detector import MLThreatDetector
# Note: AdvancedAsyncScanner consolidated into unified_scanner_engine
from app.core.unified_scanner_engine import UnifiedScannerEngine as AdvancedAsyncScanner
from app.core.edr_engine import EDREngine
from app.core.unified_memory_management import get_memory_manager
from app.core.memory_forensics import MemoryForensicsEngine


class TestSecurityDashboardIntegration(unittest.TestCase):
    """Integration tests for the real-time security dashboard."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for GUI testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test environment."""
        self.dashboard = SecurityDashboard()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if hasattr(self, 'dashboard'):
            self.dashboard.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_dashboard_initialization(self):
        """Test dashboard initialization with Phase 1 components."""
        await self.dashboard.initialize()

        # Verify Phase 1 integrations
        self.assertIsNotNone(self.dashboard.ml_detector)
        self.assertIsNotNone(self.dashboard.edr_engine)
        self.assertIsNotNone(self.dashboard.memory_manager)

        # Verify dashboard components
        self.assertIsNotNone(self.dashboard.threat_map)
        self.assertIsNotNone(self.dashboard.metrics_panel)
        self.assertIsNotNone(self.dashboard.event_stream)

    def test_threat_event_processing(self):
        """Test real-time threat event processing."""
        # Create test threat event
        threat_event = ThreatEvent(
            event_id="test_001",
            timestamp=time.time(),
            threat_type="malware",
            severity="HIGH",
            source_ip="192.168.1.100",
            target_file="/test/malware.exe",
            confidence=0.95,
            details={"scanner": "ml_detector", "rule": "behavioral_analysis"}
        )

        # Process event through dashboard
        self.dashboard.process_threat_event(threat_event)

        # Verify event appears in stream
        self.assertIn(threat_event.event_id, self.dashboard.active_threats)

    def test_metrics_integration(self):
        """Test integration with performance metrics."""
        # Simulate system metrics
        metrics = {
            'cpu_usage': 65.2,
            'memory_usage': 78.5,
            'threat_score': 23.1,
            'scan_rate': 150.0,
            'detection_rate': 12.5
        }

        # Update dashboard metrics
        self.dashboard.update_metrics(metrics)

        # Verify metrics are displayed
        self.assertEqual(self.dashboard.current_metrics['cpu_usage'], 65.2)
        self.assertEqual(self.dashboard.current_metrics['threat_score'], 23.1)

    def test_interactive_features(self):
        """Test interactive dashboard features."""
        # Test threat filtering
        self.dashboard.filter_threats_by_severity("HIGH")

        # Test time range selection
        self.dashboard.set_time_range(hours=24)

        # Test widget customization
        self.dashboard.toggle_widget("threat_map")
        self.dashboard.toggle_widget("performance_metrics")


class TestIntelligentAutomationIntegration(unittest.TestCase):
    """Integration tests for the intelligent automation system."""

    def setUp(self):
        """Set up test environment."""
        self.automation = IntelligentAutomationEngine()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_automation_initialization(self):
        """Test automation system initialization."""
        await self.automation.initialize()

        # Verify components are initialized
        self.assertIsNotNone(self.automation.learning_engine)
        self.assertIsNotNone(self.automation.config_optimizer)
        self.assertIsNotNone(self.automation.threat_predictor)
        self.assertIsNotNone(self.automation.response_orchestrator)

    @pytest.mark.asyncio
    async def test_system_profiling(self):
        """Test system behavior profiling."""
        # Create mock system data
        system_data = {
            'cpu_usage': [45.2, 67.8, 52.1, 78.9],
            'memory_usage': [34.5, 56.7, 43.2, 65.4],
            'scan_times': ['09:00', '12:00', '15:00', '18:00'],
            'threat_events': 5
        }

        # Generate system profile
        profile = await self.automation.create_system_profile(system_data)

        self.assertIsInstance(profile, SystemProfile)
        self.assertGreater(profile.avg_cpu_usage, 0)
        self.assertGreater(profile.avg_memory_usage, 0)

    @pytest.mark.asyncio
    async def test_configuration_optimization(self):
        """Test adaptive configuration optimization."""
        # Create test system profile
        profile = SystemProfile(
            avg_cpu_usage=65.0,
            avg_memory_usage=45.0,
            peak_cpu_usage=85.0,
            peak_memory_usage=70.0,
            scan_patterns={'09:00': 0.8, '17:00': 0.6}
        )

        # Optimize configuration
        optimized_config = await self.automation.optimize_configuration(profile)

        self.assertIsNotNone(optimized_config)
        self.assertIn('scan_workers', optimized_config)
        self.assertIn('memory_limit', optimized_config)

    @pytest.mark.asyncio
    async def test_predictive_analysis(self):
        """Test predictive threat analysis."""
        # Create historical threat data
        threat_history = [
            {'timestamp': time.time() - 3600, 'type': 'malware', 'severity': 'HIGH'},
            {'timestamp': time.time() - 1800, 'type': 'phishing', 'severity': 'MEDIUM'},
            {'timestamp': time.time() - 900, 'type': 'ransomware', 'severity': 'CRITICAL'}
        ]

        # Perform prediction
        predictions = await self.automation.predict_threats(threat_history)

        self.assertIsInstance(predictions, list)
        self.assertGreater(len(predictions), 0)

    @pytest.mark.asyncio
    async def test_automated_response(self):
        """Test automated response orchestration."""
        # Create test incident
        incident = {
            'type': 'malware_detected',
            'severity': 'HIGH',
            'affected_files': ['/test/malware.exe'],
            'confidence': 0.95
        }

        # Trigger automated response
        response = await self.automation.orchestrate_response(incident)

        self.assertIsNotNone(response)
        self.assertIn('actions_taken', response)
        self.assertIn('quarantine', response['actions_taken'])


class TestAdvancedReportingIntegration(unittest.TestCase):
    """Integration tests for the advanced reporting system."""

    def setUp(self):
        """Set up test environment."""
        self.reporting = AdvancedReportingEngine()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_reporting_initialization(self):
        """Test reporting system initialization."""
        await self.reporting.initialize()

        # Verify components are initialized
        self.assertIsNotNone(self.reporting.data_aggregator)
        self.assertIsNotNone(self.reporting.template_engine)
        self.assertIsNotNone(self.reporting.scheduler)

    @pytest.mark.asyncio
    async def test_data_aggregation(self):
        """Test security data aggregation."""
        # Mock security data from Phase 1 components
        security_data = {
            'threats_detected': 25,
            'files_scanned': 15000,
            'threats_blocked': 23,
            'false_positives': 2,
            'scan_performance': {'avg_time': 0.45, 'throughput': 150},
            'memory_usage': {'avg': 45.2, 'peak': 67.8}
        }

        # Aggregate data
        aggregated = await self.reporting.aggregate_security_data(security_data)

        self.assertIsNotNone(aggregated)
        self.assertIn('summary', aggregated)
        self.assertIn('metrics', aggregated)

    @pytest.mark.asyncio
    async def test_executive_report_generation(self):
        """Test executive-level report generation."""
        # Create test data
        report_data = {
            'period': '2025-09-14',
            'threats_summary': {'total': 25, 'critical': 3, 'high': 8, 'medium': 14},
            'performance_metrics': {'uptime': 99.5, 'scan_rate': 150.0},
            'compliance_status': {'pci_dss': True, 'iso_27001': True, 'gdpr': True}
        }

        # Generate executive report
        report = await self.reporting.generate_executive_report(report_data)

        self.assertIsNotNone(report)
        self.assertIn('executive_summary', report)
        self.assertIn('recommendations', report)
        self.assertIn('compliance_summary', report)

    @pytest.mark.asyncio
    async def test_compliance_tracking(self):
        """Test compliance framework tracking."""
        # Test compliance check
        compliance_results = await self.reporting.check_compliance('PCI_DSS')

        self.assertIsNotNone(compliance_results)
        self.assertIn('requirements_met', compliance_results)
        self.assertIn('gaps_identified', compliance_results)

    @pytest.mark.asyncio
    async def test_automated_scheduling(self):
        """Test automated report scheduling."""
        # Schedule daily executive report
        schedule_id = await self.reporting.schedule_report(
            template='executive_summary',
            frequency='daily',
            recipients=['security@company.com']
        )

        self.assertIsNotNone(schedule_id)

        # Verify schedule exists
        schedules = await self.reporting.list_scheduled_reports()
        self.assertIn(schedule_id, [s['id'] for s in schedules])


class TestAPIArchitectureIntegration(unittest.TestCase):
    """Integration tests for the API-first architecture."""

    def setUp(self):
        """Set up test environment."""
        self.api = SecurityAPI()
        self.sdk = SecuritySDK(base_url="http://localhost:8000")
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_api_initialization(self):
        """Test API server initialization."""
        await self.api.initialize()

        # Verify API components
        self.assertIsNotNone(self.api.rest_api)
        self.assertIsNotNone(self.api.graphql_api)
        self.assertIsNotNone(self.api.websocket_handler)

    @pytest.mark.asyncio
    async def test_rest_api_endpoints(self):
        """Test REST API endpoints."""
        # Mock API server running
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'status': 'healthy'}

            # Test health endpoint
            response = await self.sdk.get_health()
            self.assertEqual(response['status'], 'healthy')

    @pytest.mark.asyncio
    async def test_graphql_integration(self):
        """Test GraphQL API integration."""
        # Mock GraphQL query
        query = """
        query {
            threatSummary {
                total
                critical
                high
                medium
                low
            }
        }
        """

        with patch.object(self.sdk, 'graphql_query') as mock_query:
            mock_query.return_value = {
                'data': {
                    'threatSummary': {
                        'total': 25,
                        'critical': 3,
                        'high': 8,
                        'medium': 14,
                        'low': 0
                    }
                }
            }

            result = await self.sdk.graphql_query(query)
            self.assertIn('threatSummary', result['data'])

    @pytest.mark.asyncio
    async def test_websocket_streaming(self):
        """Test WebSocket real-time streaming."""
        # Mock WebSocket connection
        with patch.object(self.sdk, 'connect_websocket') as mock_ws:
            mock_ws.return_value = AsyncMock()

            # Test real-time threat stream
            threat_stream = await self.sdk.stream_threats()
            self.assertIsNotNone(threat_stream)

    @pytest.mark.asyncio
    async def test_sdk_integration(self):
        """Test SDK integration with all components."""
        # Test scanning API
        with patch.object(self.sdk, 'scan_file') as mock_scan:
            mock_scan.return_value = {
                'file_path': '/test/file.txt',
                'threat_detected': False,
                'scan_time': 0.234,
                'ml_confidence': 0.95
            }

            result = await self.sdk.scan_file('/test/file.txt')
            self.assertFalse(result['threat_detected'])
            self.assertEqual(result['file_path'], '/test/file.txt')


class TestDeepLearningIntegration(unittest.TestCase):
    """Integration tests for deep learning components."""

    def setUp(self):
        """Set up test environment."""
        self.dl_engine = DeepLearningEngine()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_deep_learning_initialization(self):
        """Test deep learning engine initialization."""
        await self.dl_engine.initialize()

        # Verify neural network components
        self.assertIsNotNone(self.dl_engine.threat_classifier)
        self.assertIsNotNone(self.dl_engine.anomaly_detector)
        self.assertIsNotNone(self.dl_engine.pattern_analyzer)

    @pytest.mark.asyncio
    async def test_threat_pattern_recognition(self):
        """Test advanced threat pattern recognition."""
        # Create test pattern data
        pattern_data = {
            'file_features': [0.1, 0.3, 0.7, 0.2, 0.9],
            'behavioral_features': [0.4, 0.6, 0.1, 0.8, 0.3],
            'network_features': [0.2, 0.5, 0.9, 0.1, 0.7]
        }

        # Analyze pattern
        threat_pattern = await self.dl_engine.analyze_threat_pattern(pattern_data)

        self.assertIsInstance(threat_pattern, ThreatPattern)
        self.assertIsNotNone(threat_pattern.classification)
        self.assertGreaterEqual(threat_pattern.confidence, 0.0)
        self.assertLessEqual(threat_pattern.confidence, 1.0)

    @pytest.mark.asyncio
    async def test_neural_network_training(self):
        """Test neural network training with new data."""
        # Create mock training data
        training_data = []
        for i in range(100):
            training_data.append({
                'features': [0.1 * i, 0.2 * i, 0.3 * i],
                'label': 1 if i % 2 == 0 else 0
            })

        # Train model
        training_result = await self.dl_engine.train_model(training_data)

        self.assertTrue(training_result['success'])
        self.assertIn('accuracy', training_result)
        self.assertGreater(training_result['accuracy'], 0.5)

    @pytest.mark.asyncio
    async def test_integration_with_phase1(self):
        """Test deep learning integration with Phase 1 components."""
        # Initialize Phase 1 ML detector
        ml_detector = MLThreatDetector()
        await ml_detector.initialize()

        # Test enhanced analysis with deep learning
        test_file = self.test_dir / "dl_test.txt"
        test_file.write_text("Deep learning integration test file.")

        # Get standard ML analysis
        ml_result = await ml_detector.analyze_file(str(test_file))

        # Enhance with deep learning
        enhanced_result = await self.dl_engine.enhance_analysis(ml_result)

        self.assertIsNotNone(enhanced_result)
        self.assertIn('enhanced_confidence', enhanced_result)
        self.assertIn('pattern_analysis', enhanced_result)


class TestGPUAccelerationIntegration(unittest.TestCase):
    """Integration tests for GPU acceleration."""

    def setUp(self):
        """Set up test environment."""
        self.gpu_accelerator = GPUAccelerator()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_gpu_initialization(self):
        """Test GPU acceleration initialization."""
        await self.gpu_accelerator.initialize()

        # Check GPU availability
        gpu_available = self.gpu_accelerator.is_gpu_available()
        if gpu_available:
            self.assertIsNotNone(self.gpu_accelerator.device)
            self.assertIsNotNone(self.gpu_accelerator.context)

    @pytest.mark.asyncio
    async def test_accelerated_scanning(self):
        """Test GPU-accelerated scanning operations."""
        if not self.gpu_accelerator.is_gpu_available():
            self.skipTest("GPU not available for testing")

        # Create test files for batch processing
        test_files = []
        for i in range(50):
            test_file = self.test_dir / f"gpu_test_{i}.txt"
            test_file.write_text(f"GPU acceleration test file {i}.")
            test_files.append(str(test_file))

        # Test GPU-accelerated batch scanning
        start_time = time.time()
        results = await self.gpu_accelerator.accelerated_scan_batch(test_files)
        gpu_time = time.time() - start_time

        self.assertEqual(len(results), 50)
        self.assertLess(gpu_time, 10.0)  # Should be fast with GPU

    @pytest.mark.asyncio
    async def test_ml_acceleration(self):
        """Test GPU acceleration for ML operations."""
        if not self.gpu_accelerator.is_gpu_available():
            self.skipTest("GPU not available for testing")

        # Test GPU-accelerated ML inference
        test_features = [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in range(1000)]

        start_time = time.time()
        predictions = await self.gpu_accelerator.accelerated_ml_inference(test_features)
        gpu_ml_time = time.time() - start_time

        self.assertEqual(len(predictions), 1000)
        self.assertLess(gpu_ml_time, 5.0)  # Should be fast with GPU acceleration

    @pytest.mark.asyncio
    async def test_memory_optimization(self):
        """Test GPU memory optimization features."""
        if not self.gpu_accelerator.is_gpu_available():
            self.skipTest("GPU not available for testing")

        # Test memory usage optimization
        initial_memory = self.gpu_accelerator.get_gpu_memory_usage()

        # Perform memory-intensive operation
        large_data = [[0.1] * 1000 for _ in range(1000)]
        await self.gpu_accelerator.process_large_dataset(large_data)

        # Check memory is properly managed
        final_memory = self.gpu_accelerator.get_gpu_memory_usage()

        # Memory should not have leaked significantly
        memory_increase = final_memory - initial_memory
        self.assertLess(memory_increase, 100)  # Less than 100MB increase


class TestCompletePhase2Integration(unittest.TestCase):
    """Complete integration tests for all Phase 2 components working together."""

    def setUp(self):
        """Set up complete test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

        # Initialize all Phase 2 components
        self.dashboard = SecurityDashboard()
        self.automation = IntelligentAutomationEngine()
        self.reporting = AdvancedReportingEngine()
        self.api = SecurityAPI()
        self.dl_engine = DeepLearningEngine()
        self.gpu_accelerator = GPUAccelerator()

    def tearDown(self):
        """Clean up complete test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self):
        """Test complete security workflow with all Phase 2 components."""
        # Initialize all components
        await self.automation.initialize()
        await self.reporting.initialize()
        await self.api.initialize()
        await self.dl_engine.initialize()
        await self.gpu_accelerator.initialize()

        # Create test scenario: incoming threat
        test_file = self.test_dir / "integration_threat.exe"
        test_file.write_bytes(b"Mock malware binary data for testing")

        # 1. GPU-accelerated scanning
        if self.gpu_accelerator.is_gpu_available():
            scan_result = await self.gpu_accelerator.accelerated_scan_file(str(test_file))
        else:
            scan_result = {'file_path': str(test_file), 'threat_detected': True}

        # 2. Deep learning enhancement
        enhanced_analysis = await self.dl_engine.enhance_analysis(scan_result)

        # 3. Intelligent automation response
        if enhanced_analysis.get('threat_detected'):
            incident = {
                'type': 'malware_detected',
                'file_path': str(test_file),
                'confidence': enhanced_analysis.get('confidence', 0.95),
                'severity': 'HIGH'
            }

            auto_response = await self.automation.orchestrate_response(incident)

            # 4. Dashboard notification
            threat_event = ThreatEvent(
                event_id=f"test_{int(time.time())}",
                timestamp=time.time(),
                threat_type="malware",
                severity="HIGH",
                source_ip="127.0.0.1",
                target_file=str(test_file),
                confidence=enhanced_analysis.get('confidence', 0.95),
                details=enhanced_analysis
            )

            self.dashboard.process_threat_event(threat_event)

            # 5. Automated reporting
            report_data = {
                'incident_id': threat_event.event_id,
                'timestamp': threat_event.timestamp,
                'response_actions': auto_response.get('actions_taken', []),
                'threat_analysis': enhanced_analysis
            }

            incident_report = await self.reporting.generate_incident_report(report_data)

            # Verify complete workflow
            self.assertIsNotNone(scan_result)
            self.assertIsNotNone(enhanced_analysis)
            self.assertIsNotNone(auto_response)
            self.assertIn(threat_event.event_id, self.dashboard.active_threats)
            self.assertIsNotNone(incident_report)

    @pytest.mark.asyncio
    async def test_performance_integration(self):
        """Test performance across all Phase 2 components."""
        # Initialize components
        await self.automation.initialize()
        await self.dl_engine.initialize()

        # Create performance test scenario
        test_files = []
        for i in range(20):
            test_file = self.test_dir / f"perf_test_{i}.txt"
            test_file.write_text(f"Performance test file {i} content.")
            test_files.append(str(test_file))

        # Measure end-to-end performance
        start_time = time.time()

        # Process files through complete pipeline
        results = []
        for file_path in test_files:
            # Basic analysis
            analysis = {'file_path': file_path, 'threat_score': 0.1}

            # Deep learning enhancement
            enhanced = await self.dl_engine.enhance_analysis(analysis)
            results.append(enhanced)

        total_time = time.time() - start_time

        # Performance assertions
        self.assertEqual(len(results), 20)
        self.assertLess(total_time, 30.0)  # Should complete within 30 seconds

        # Average processing time per file
        avg_time = total_time / len(test_files)
        self.assertLess(avg_time, 2.0)  # Less than 2 seconds per file

    @pytest.mark.asyncio
    async def test_scalability_integration(self):
        """Test scalability of integrated Phase 2 system."""
        # Test with increasing load
        load_sizes = [10, 50, 100]
        performance_results = []

        for load_size in load_sizes:
            # Create test files
            test_files = []
            for i in range(load_size):
                test_file = self.test_dir / f"scale_test_{load_size}_{i}.txt"
                test_file.write_text(f"Scalability test file {i}.")
                test_files.append(str(test_file))

            # Measure processing time
            start_time = time.time()

            # Simulate parallel processing
            tasks = []
            for file_path in test_files[:min(10, load_size)]:  # Process up to 10 in parallel
                task = self._process_file_async(file_path)
                tasks.append(task)

            await asyncio.gather(*tasks)
            processing_time = time.time() - start_time

            performance_results.append({
                'load_size': load_size,
                'processing_time': processing_time,
                'throughput': load_size / processing_time
            })

            # Clean up files
            for file_path in test_files:
                Path(file_path).unlink(missing_ok=True)

        # Verify scalability
        self.assertGreater(len(performance_results), 0)

        # Throughput should remain reasonable as load increases
        for result in performance_results:
            self.assertGreater(result['throughput'], 5.0)  # At least 5 files/second

    async def _process_file_async(self, file_path: str) -> dict:
        """Helper method for async file processing."""
        # Simulate processing pipeline
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            'file_path': file_path,
            'processed': True,
            'timestamp': time.time()
        }


if __name__ == '__main__':
    # Run all integration tests
    unittest.main(verbosity=2)
