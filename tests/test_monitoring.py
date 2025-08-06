#!/usr/bin/env python3
"""
Test script for Phase 3 real-time monitoring system
"""
import sys
import os
import time
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

try:
    from monitoring import RealTimeMonitor, MonitorConfig
    from utils.config import setup_logging
    
    def test_basic_monitoring():
        """Test basic monitoring functionality."""
        logger = setup_logging()
        
        # Create test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Testing real-time monitoring in: %s", temp_dir)
            
            # Create monitor configuration
            config = MonitorConfig(
                watch_paths=[temp_dir],
                excluded_paths=[],
                scan_new_files=True,
                scan_modified_files=True
            )
            
            # Initialize monitor
            monitor = RealTimeMonitor(config)
            
            # Set up callbacks
            def on_threat_detected(file_path, threat_name):
                logger.warning("THREAT DETECTED: %s - %s", file_path, threat_name)
            
            def on_scan_completed(file_path, result):
                logger.info("SCAN COMPLETED: %s - %s", file_path, result)
            
            def on_error(error_msg):
                logger.error("MONITOR ERROR: %s", error_msg)
            
            monitor.set_threat_detected_callback(on_threat_detected)
            monitor.set_scan_completed_callback(on_scan_completed)
            monitor.set_error_callback(on_error)
            
            # Start monitoring
            logger.info("Starting monitor...")
            if not monitor.start():
                logger.error("Failed to start monitor")
                return False
            
            # Get initial status
            status = monitor.get_status()
            logger.info("Monitor status: %s", status['state'])
            
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Hello, World!")
            logger.info("Created test file: %s", test_file)
            
            # Wait for events to be processed
            time.sleep(3)
            
            # Get statistics
            stats = monitor.get_statistics()
            logger.info("Monitor statistics:")
            for component, data in stats.items():
                logger.info("  %s: %s", component, data)
            
            # Stop monitoring
            logger.info("Stopping monitor...")
            monitor.stop()
            
            final_status = monitor.get_status()
            logger.info("Final status: %s", final_status['state'])
            
            return True
    
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
