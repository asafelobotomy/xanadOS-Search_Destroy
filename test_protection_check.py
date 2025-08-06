#!/usr/bin/env python3
"""
Test the exit protection dialog functionality.
"""

import sys
import os
import time

# Add the app directory to the path so we can import modules
sys.path.insert(0, '/home/vm/Documents/xanadOS-Search_Destroy')

def test_protection_check():
    """Test if we can properly check protection status."""
    try:
        from app.utils.config import load_config
        from app.monitoring import RealTimeMonitor, MonitorConfig, MonitorState
        
        print("🔍 Testing protection status check logic...")
        
        # Load config
        config = load_config()
        monitoring_enabled = config.get('security_settings', {}).get('real_time_protection', False)
        print(f"📊 Config monitoring_enabled: {monitoring_enabled}")
        
        # Test monitor state check
        if monitoring_enabled:
            print("✅ Protection is enabled in config")
            print("🔍 Testing monitor state check logic...")
            
            # Create a test monitor
            watch_paths = [str(os.path.expanduser('~'))]
            excluded_paths = ['/proc', '/sys', '/dev', '/tmp']
            
            monitor_config = MonitorConfig(
                watch_paths=watch_paths,
                excluded_paths=excluded_paths,
                scan_new_files=True,
                scan_modified_files=False,
                quarantine_threats=False
            )
            
            test_monitor = RealTimeMonitor(monitor_config)
            print(f"🔧 Created test monitor, initial state: {test_monitor.state}")
            
            # Test state check condition
            state_check = hasattr(test_monitor, 'state') and test_monitor.state.name == 'RUNNING'
            print(f"🔍 State check (hasattr and state == 'RUNNING'): {state_check}")
            
            # Start the monitor to test
            print("▶️ Starting test monitor...")
            if test_monitor.start():
                print(f"✅ Monitor started successfully, state: {test_monitor.state}")
                state_check_after_start = hasattr(test_monitor, 'state') and test_monitor.state.name == 'RUNNING'
                print(f"🔍 State check after start: {state_check_after_start}")
                
                # Full condition check
                full_condition = monitoring_enabled and test_monitor and hasattr(test_monitor, 'state') and test_monitor.state.name == 'RUNNING'
                print(f"🎯 Full exit dialog condition would be: {full_condition}")
                
                # Stop the monitor
                print("⏹️ Stopping test monitor...")
                test_monitor.stop()
                print(f"🔍 State after stop: {test_monitor.state}")
            else:
                print("❌ Failed to start test monitor")
        else:
            print("⚫ Protection is disabled in config")
            print("🎯 Full exit dialog condition would be: False (protection disabled)")
        
        print("\n✅ Protection status check test completed!")
        
    except Exception as e:
        print(f"❌ Error testing protection check: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_protection_check()
