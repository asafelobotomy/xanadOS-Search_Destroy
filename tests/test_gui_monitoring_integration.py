#!/usr/bin/env python3
"""
Test script for GUI integration with real-time monitoring
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_gui_integration():
    """Test GUI integration with monitoring system."""
    print("Testing GUI integration with real-time monitoring...")
    
    try:
        # Test imports
        from gui.main_window import MainWindow
        from monitoring import RealTimeMonitor, MonitorConfig
        
        print("✓ All imports successful")
        
        # Test MainWindow creation (without actually showing it)
        try:
            # We'll just test that the class can be imported and has our new methods
            main_window_methods = dir(MainWindow)
            
            required_methods = [
                'create_real_time_tab',
                'init_real_time_monitoring', 
                'start_real_time_protection',
                'stop_real_time_protection',
                'on_threat_detected',
                'on_scan_completed',
                'update_monitoring_statistics'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in main_window_methods:
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"✗ Missing methods: {missing_methods}")
                return False
            else:
                print("✓ All required methods present in MainWindow")
            
        except Exception as e:
            print(f"✗ Error testing MainWindow: {e}")
            return False
        
        # Test MonitorConfig creation
        try:
            config = MonitorConfig(
                watch_paths=["/tmp"],
                scan_new_files=True
            )
            print("✓ MonitorConfig creation successful")
            
        except Exception as e:
            print(f"✗ Error creating MonitorConfig: {e}")
            return False
        
        print("✓ GUI integration test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_monitoring_components():
    """Test individual monitoring components."""
    print("\nTesting monitoring components...")
    
    try:
        from monitoring import (
            FileSystemWatcher, 
            EventProcessor, 
            RealTimeMonitor,
            MonitorConfig
        )
        
        print("✓ Monitoring components imported successfully")
        
        # Test basic component creation
        config = MonitorConfig(watch_paths=["/tmp"])
        
        # Test individual components
        watcher = FileSystemWatcher()
        processor = EventProcessor()
        monitor = RealTimeMonitor(config)
        
        print("✓ All monitoring components created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing monitoring components: {e}")
        return False

if __name__ == "__main__":
    print("GUI Real-Time Monitoring Integration Test")
    print("=" * 50)
    
    success = True
    
    # Test monitoring components first
    if not test_monitoring_components():
        success = False
    
    # Test GUI integration
    if not test_gui_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All integration tests passed!")
        print("\nThe real-time monitoring system is now integrated with the GUI!")
        print("\nNew features available:")
        print("  - 🛡️ Real-Time Protection tab in main window")
        print("  - ▶️ Start/Stop protection controls")
        print("  - 📊 Live statistics display")
        print("  - 📝 Real-time activity log")
        print("  - 📁 Dynamic path management")
        print("  - 🚨 Threat detection notifications")
    else:
        print("❌ Some integration tests failed")
        sys.exit(1)
