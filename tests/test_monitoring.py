#!/usr/bin/env python3
"""
Test script for Phase 3 real-time monitoring system
"""
from pathlib import Path

import os

import sys
import tempfile

import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

try:
    from monitoring import MonitorConfig, RealTimeMonitor
    from utils.config import setup_logging

    def test_basic_monitoring():
        """Test basic monitoring functionality (assert-based, no return)."""
        logger = setup_logging()

        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Testing real-time monitoring in: %s", temp_dir)

            config = MonitorConfig(
                watch_paths=[temp_dir],
                excluded_paths=[],
                scan_new_files=True,
                scan_modified_files=True,
            )

            monitor = RealTimeMonitor(config)

            # Simple callbacks (smoke validation)
            events = {"threats": [], "completed": [], "errors": []}

            def on_threat_detected(file_path, threat_name):
                events["threats"].append((file_path, threat_name))

            def on_scan_completed(file_path, result):
                events["completed"].append((file_path, result))

            def on_error(error_msg):
                events["errors"].append(error_msg)

            monitor.set_threat_detected_callback(on_threat_detected)
            monitor.set_scan_completed_callback(on_scan_completed)
            monitor.set_error_callback(on_error)

            logger.info("Starting monitor...")
            assert monitor.start(), "Failed to start monitor"

            status = monitor.get_status()
            logger.info("Monitor status: %s", status["state"])
            assert status["state"] in {"running", "active"}

            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Hello, World!")
            logger.info("Created test file: %s", test_file)

            time.sleep(3)

            stats = monitor.get_statistics()
            assert isinstance(stats, dict) and stats, "Statistics should not be empty"
            # Ensure no errors recorded during basic operation
            assert not events["errors"], f"Unexpected monitor errors: {events['errors']}"

            logger.info("Stopping monitor...")
            monitor.stop()

            final_status = monitor.get_status()
            logger.info("Final status: %s", final_status["state"])
            assert final_status["state"] in {"stopped", "idle"}

    if __name__ == "__main__":
        print("Testing Phase 3 Real-Time Monitoring System")
        print("=" * 50)

        try:
            success = test_basic_monitoring()
            if success:
                print("✓ Basic monitoring test completed successfully")
            else:
                print("✗ Basic monitoring test failed")
                sys.exit(1)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

except ImportError as e:
    print(f"Import error - monitoring modules may have issues: {e}")
    sys.exit(1)
