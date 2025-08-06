#!/usr/bin/env python3
"""
Test script to simulate different exit scenarios for the protection dialog.
"""

import subprocess
import time
import os
import signal

def find_app_process():
    """Find the running app process."""
    try:
        result = subprocess.run(['pgrep', '-f', 'python -m app.main'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
        return None
    except Exception as e:
        print(f"Error finding process: {e}")
        return None

def test_graceful_exit():
    """Test graceful exit by sending SIGTERM."""
    pid = find_app_process()
    if pid:
        print(f"Found app process with PID: {pid}")
        print("Sending SIGTERM to test graceful exit handling...")
        os.kill(pid, signal.SIGTERM)
        print("SIGTERM sent. Check if dialog appears.")
        return True
    else:
        print("No app process found.")
        return False

def test_force_kill():
    """Force kill the app (for emergency testing)."""
    pid = find_app_process()
    if pid:
        print(f"Force killing app process with PID: {pid}")
        os.kill(pid, signal.SIGKILL)
        return True
    else:
        print("No app process found.")
        return False

def check_app_running():
    """Check if app is still running."""
    pid = find_app_process()
    if pid:
        print(f"App is still running with PID: {pid}")
        return True
    else:
        print("App is not running.")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_exit_dialog.py check     - Check if app is running")
        print("  python test_exit_dialog.py graceful  - Test graceful exit (SIGTERM)")
        print("  python test_exit_dialog.py kill      - Force kill app (SIGKILL)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "check":
        check_app_running()
    elif command == "graceful":
        test_graceful_exit()
    elif command == "kill":
        test_force_kill()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
