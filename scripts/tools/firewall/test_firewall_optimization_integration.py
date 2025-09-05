#!/usr/bin/env python3
"""
Firewall Optimization Integration Test
=====================================

Tests the integration of firewall status optimization with the main window.
This validates that the optimization is properly applied and working.
"""

import logging
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_optimization_imports() -> bool:
    """Test that all optimization components can be imported."""
    try:
        from app.core.firewall_status_optimizer import FirewallStatusOptimizer
        from app.gui.firewall_optimization_patch import apply_firewall_optimization

        # Verify the imports are valid classes/functions
        assert (
            FirewallStatusOptimizer is not None
        ), "FirewallStatusOptimizer class not found"
        assert (
            apply_firewall_optimization is not None
        ), "apply_firewall_optimization function not found"

        logger.info("✅ All optimization components imported successfully")
        logger.info(f"   - FirewallStatusOptimizer: {FirewallStatusOptimizer}")
        logger.info(f"   - apply_firewall_optimization: {apply_firewall_optimization}")
        return True
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_firewall_detector() -> bool:
    """Test the basic firewall detector functionality."""
    try:
        from app.core.firewall_detector import FirewallDetector

        detector = FirewallDetector()
        status = detector.get_firewall_status()

        logger.info(
            f"✅ Firewall detector working: {status.get('firewall_name', 'Unknown')}"
        )
        logger.info(f"   Status: {status.get('status_text', 'Unknown')}")
        logger.info(f"   Active: {status.get('is_active', False)}")
        logger.info(f"   Method: {status.get('method', 'Unknown')}")

        return True
    except Exception as e:
        logger.error(f"❌ Firewall detector failed: {e}")
        return False


def test_optimization_standalone() -> bool:
    """Test the optimization system standalone."""
    try:
        from app.core.firewall_status_optimizer import FirewallStatusOptimizer

        optimizer = FirewallStatusOptimizer()

        # Test getting status
        status = optimizer.get_firewall_status(use_cache=False)
        logger.info(f"✅ Optimizer working: {status.get('firewall_name', 'Unknown')}")

        # Test performance stats
        stats = optimizer.get_performance_stats()
        logger.info(f"   Monitoring active: {stats.get('monitoring_active', False)}")
        logger.info(f"   Cache duration: {stats.get('cache_duration', 0)}s")

        # Start monitoring briefly
        optimizer.start_monitoring()
        time.sleep(2)

        stats = optimizer.get_performance_stats()
        logger.info(f"   Monitoring started: {stats.get('monitoring_active', False)}")

        optimizer.stop_monitoring()
        logger.info("✅ Optimization standalone test completed")

        return True
    except Exception as e:
        logger.error(f"❌ Optimization standalone test failed: {e}")
        return False


def test_file_monitoring() -> bool:
    """Test file monitoring capabilities."""
    try:
        from app.monitoring.file_watcher import FileSystemWatcher

        # Test basic file watcher initialization
        watcher = FileSystemWatcher(
            paths_to_watch=["/etc"],  # Safe path that exists
            event_callback=lambda event: None,
        )

        logger.info("✅ File watcher initialized successfully")

        # Get statistics
        stats = watcher.get_statistics()
        logger.info(f"   Backend: {stats.get('backend', 'Unknown')}")
        logger.info(f"   Paths watched: {stats.get('paths_watched', 0)}")

        return True
    except Exception as e:
        logger.error(f"❌ File monitoring test failed: {e}")
        return False


def test_mock_main_window_integration() -> bool:
    """Test integration with a mock main window."""
    try:
        from app.gui.firewall_optimization_patch import apply_firewall_optimization

        # Create a mock main window with minimal required attributes
        class MockMainWindow:
            def __init__(self) -> None:
                self.logger = logger
                self._firewall_status_cache = None

            def update_firewall_status_card(self) -> None:
                logger.info("Mock GUI update called")

        # Create mock window
        mock_window = MockMainWindow()

        # Apply optimization
        patch = apply_firewall_optimization(mock_window)

        if patch:
            logger.info("✅ Optimization applied to mock window")

            # Test getting stats
            stats = patch.get_optimization_stats()
            logger.info(
                f"   Optimization active: {stats.get('optimization_active', False)}"
            )

            # Test force refresh
            patch.force_refresh()
            logger.info("   Force refresh completed")

            return True
        else:
            logger.error("❌ Failed to apply optimization to mock window")
            return False

    except Exception as e:
        logger.error(f"❌ Mock integration test failed: {e}")
        return False


def main() -> int:
    """Run all integration tests."""
    print("Firewall Optimization Integration Test")
    print("=" * 40)

    tests = [
        ("Import Test", test_optimization_imports),
        ("Firewall Detector Test", test_firewall_detector),
        ("Optimization Standalone Test", test_optimization_standalone),
        ("File Monitoring Test", test_file_monitoring),
        ("Mock Integration Test", test_mock_main_window_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            print(f"❌ {test_name} ERROR")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Optimization integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
