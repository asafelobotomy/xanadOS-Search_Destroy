#!/usr/bin/env python3
"""Integration test for Phase 2 components of xanadOS Search & Destroy.

This test validates that all Phase 2 components integrate properly:
- Real-time security dashboard
- Intelligent automation system
- Advanced reporting system
- API-first architecture
- Deep learning integration
- GPU acceleration system
"""

import asyncio
import logging
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any
import torch
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_gpu_acceleration():
    """Test GPU acceleration system."""
    logger.info("Testing GPU acceleration system...")
    
    try:
        from app.gpu.acceleration import get_gpu_acceleration
        
        gpu_manager = get_gpu_acceleration()
        
        # Initialize
        success = await gpu_manager.initialize()
        assert success, "GPU acceleration initialization failed"
        
        # Get status
        status = gpu_manager.get_acceleration_status()
        logger.info(f"GPU acceleration status: {status['active_accelerators']}")
        
        # Test model inference acceleration
        dummy_model = torch.nn.Sequential(
            torch.nn.Linear(10, 5),
            torch.nn.ReLU(),
            torch.nn.Linear(5, 2)
        )
        dummy_input = torch.randn(1, 10)
        
        result = await gpu_manager.accelerate_model_inference(dummy_model, dummy_input)
        assert result is not None, "GPU inference failed"
        assert result.shape == (1, 2), "GPU inference output shape incorrect"
        
        logger.info("✅ GPU acceleration system test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ GPU acceleration test failed: {e}")
        return False


async def test_deep_learning():
    """Test deep learning components."""
    logger.info("Testing deep learning integration...")
    
    try:
        from app.ml.deep_learning import DeepLearningThreatDetector
        
        detector = DeepLearningThreatDetector()
        await detector.initialize()
        
        # Test file analysis
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"This is a test file content")
            tmp_file.flush()
            
            result = await detector.analyze_file(tmp_file.name)
            assert 'threat_score' in result, "Deep learning analysis missing threat_score"
            assert 0.0 <= result['threat_score'] <= 1.0, "Invalid threat score range"
        
        # Test log analysis
        log_entries = [
            "INFO: Normal operation",
            "WARNING: Suspicious activity detected",
            "ERROR: Failed login attempt"
        ]
        
        log_result = await detector.analyze_logs(log_entries)
        assert 'overall_risk' in log_result, "Log analysis missing overall_risk"
        
        logger.info("✅ Deep learning integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Deep learning test failed: {e}")
        return False


async def test_api_architecture():
    """Test API architecture components."""
    logger.info("Testing API architecture...")
    
    try:
        from app.api.security_api import SecurityAPI
        from app.api.client_sdk import SecurityAPIClient
        
        # Test API initialization
        api = SecurityAPI()
        await api.initialize()
        
        # Test client SDK
        client = SecurityAPIClient(base_url="http://localhost:8000")
        
        # Basic validation that components can be imported and initialized
        logger.info("✅ API architecture test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ API architecture test failed: {e}")
        return False


async def test_reporting_system():
    """Test advanced reporting system."""
    logger.info("Testing advanced reporting system...")
    
    try:
        from app.reporting.advanced_reporting import SecurityReportingEngine
        
        reporting_engine = SecurityReportingEngine()
        await reporting_engine.initialize()
        
        # Generate a basic test report
        mock_data = {
            'threats_detected': 5,
            'files_scanned': 1000,
            'scan_duration': 120.5,
            'high_risk_files': 2,
            'medium_risk_files': 3,
            'low_risk_files': 0
        }
        
        # Test threat analysis
        threat_analyzer = reporting_engine.threat_analyzer
        analysis = await threat_analyzer.analyze_threat_landscape(mock_data)
        assert 'threat_categories' in analysis, "Threat analysis missing categories"
        
        logger.info("✅ Advanced reporting system test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Reporting system test failed: {e}")
        return False


async def test_intelligent_automation():
    """Test intelligent automation system."""
    logger.info("Testing intelligent automation system...")
    
    try:
        from app.core.intelligent_automation import IntelligentAutomationEngine
        
        automation_engine = IntelligentAutomationEngine()
        await automation_engine.initialize()
        
        # Test learning engine
        learning_engine = automation_engine.learning_engine
        
        # Simulate threat detection events
        events = [
            {'type': 'file_threat', 'severity': 'high', 'timestamp': time.time()},
            {'type': 'network_threat', 'severity': 'medium', 'timestamp': time.time()},
            {'type': 'process_threat', 'severity': 'low', 'timestamp': time.time()}
        ]
        
        for event in events:
            await learning_engine.learn_from_detection(event)
        
        # Test prediction
        prediction = await learning_engine.predict_threat_likelihood({'type': 'file_threat'})
        assert 0.0 <= prediction <= 1.0, "Invalid prediction range"
        
        logger.info("✅ Intelligent automation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Intelligent automation test failed: {e}")
        return False


async def test_dashboard_components():
    """Test dashboard components."""
    logger.info("Testing dashboard components...")
    
    try:
        # Test web dashboard (API components)
        from app.api.web_dashboard import create_app
        
        app = create_app()
        assert app is not None, "Web dashboard app creation failed"
        
        # Test Qt dashboard (basic import)
        from app.gui.security_dashboard import SecurityDashboard
        
        # Note: We can't fully test Qt GUI in headless environment
        # but we can verify imports and basic initialization
        
        logger.info("✅ Dashboard components test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dashboard components test failed: {e}")
        return False


async def test_integration_workflow():
    """Test complete integration workflow."""
    logger.info("Testing complete integration workflow...")
    
    try:
        # 1. Initialize GPU acceleration
        from app.gpu.acceleration import get_gpu_acceleration
        gpu_manager = get_gpu_acceleration()
        await gpu_manager.initialize()
        
        # 2. Initialize deep learning
        from app.ml.deep_learning import DeepLearningThreatDetector
        ml_detector = DeepLearningThreatDetector()
        await ml_detector.initialize()
        
        # 3. Initialize automation
        from app.core.intelligent_automation import IntelligentAutomationEngine
        automation = IntelligentAutomationEngine()
        await automation.initialize()
        
        # 4. Initialize reporting
        from app.reporting.advanced_reporting import SecurityReportingEngine
        reporting = SecurityReportingEngine()
        await reporting.initialize()
        
        # 5. Test workflow: File analysis -> ML detection -> Automation -> Reporting
        
        # Create test file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"Test malware signature")
            tmp_file.flush()
            
            # ML analysis
            ml_result = await ml_detector.analyze_file(tmp_file.name)
            threat_score = ml_result.get('threat_score', 0.0)
            
            # Automation response
            if threat_score > 0.5:
                await automation.learning_engine.learn_from_detection({
                    'type': 'file_threat',
                    'severity': 'high',
                    'file_path': tmp_file.name,
                    'threat_score': threat_score
                })
            
            # Generate report
            report_data = {
                'threats_detected': 1 if threat_score > 0.5 else 0,
                'files_scanned': 1,
                'scan_duration': 1.0,
                'high_risk_files': 1 if threat_score > 0.8 else 0,
                'medium_risk_files': 1 if 0.5 < threat_score <= 0.8 else 0,
                'low_risk_files': 1 if threat_score <= 0.5 else 0
            }
            
            analysis = await reporting.threat_analyzer.analyze_threat_landscape(report_data)
            assert analysis is not None, "Integration workflow failed"
        
        logger.info("✅ Integration workflow test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration workflow test failed: {e}")
        return False


async def run_phase2_tests():
    """Run all Phase 2 integration tests."""
    logger.info("="*60)
    logger.info("STARTING PHASE 2 INTEGRATION TESTS")
    logger.info("="*60)
    
    tests = [
        ("GPU Acceleration", test_gpu_acceleration),
        ("Deep Learning", test_deep_learning),
        ("API Architecture", test_api_architecture),
        ("Reporting System", test_reporting_system),
        ("Intelligent Automation", test_intelligent_automation),
        ("Dashboard Components", test_dashboard_components),
        ("Integration Workflow", test_integration_workflow)
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            results[test_name] = result
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
            failed += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("PHASE 2 INTEGRATION TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal Tests: {len(tests)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 ALL PHASE 2 TESTS PASSED! 🎉")
    else:
        logger.info(f"\n⚠️  {failed} tests failed. Review logs for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_phase2_tests())
    sys.exit(0 if success else 1)