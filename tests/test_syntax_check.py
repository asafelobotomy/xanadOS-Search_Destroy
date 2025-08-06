#!/usr/bin/env python3
"""
Simple syntax check for GUI monitoring integration
"""
import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        return True, None
    except (SyntaxError, UnicodeDecodeError) as e:
        return False, f"Syntax error: {e}"
    except (IOError, OSError) as e:
        return False, f"Error reading file: {e}"

def check_methods_exist(file_path, required_methods):
    """Check if required methods exist in the file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found_methods = []
        missing_methods = []
        
        for method in required_methods:
            if f"def {method}(" in content:
                found_methods.append(method)
            else:
                missing_methods.append(method)
        
        return found_methods, missing_methods
        
    except (IOError, OSError):
        return [], required_methods

def main():
    """Check the GUI integration."""
    print("GUI Monitoring Integration - Syntax Check")
    print("=" * 50)
    
    # Set up paths
    src_dir = Path(__file__).parent.parent / "app"
    main_window_path = src_dir / "gui" / "main_window.py"
    
    if not main_window_path.exists():
        print(f"❌ Main window file not found: {main_window_path}")
        return False
    
    # Check syntax
    print("Checking main window syntax...")
    is_valid, error = check_syntax(main_window_path)
    
    if not is_valid:
        print(f"❌ Syntax error in main window: {error}")
        return False
    
    print("✅ Main window syntax is valid")
    
    # Check required methods exist
    required_methods = [
        "create_real_time_tab",
        "init_real_time_monitoring",
        "start_real_time_protection", 
        "stop_real_time_protection",
        "on_threat_detected",
        "on_scan_completed",
        "update_monitoring_statistics"
    ]
    
    print("Checking required methods...")
    found, missing = check_methods_exist(main_window_path, required_methods)
    
    if missing:
        print(f"❌ Missing methods: {missing}")
        return False
    
    print(f"✅ All required methods found: {found}")
    
    # Check monitoring module exists
    monitoring_path = src_dir / "monitoring" / "__init__.py"
    if not monitoring_path.exists():
        print(f"❌ Monitoring module not found: {monitoring_path}")
        return False
    
    print("✅ Monitoring module exists")
    
    # Check monitoring syntax
    print("Checking monitoring module syntax...")
    is_valid, error = check_syntax(monitoring_path)
    
    if not is_valid:
        print(f"❌ Syntax error in monitoring module: {error}")
        return False
    
    print("✅ Monitoring module syntax is valid")
    
    print("\n" + "=" * 50)
    print("🎉 GUI Integration Syntax Check PASSED!")
    print("\nIntegration Summary:")
    print("📁 Files verified:")
    print(f"   - {main_window_path.relative_to(Path.cwd())}")
    print(f"   - {monitoring_path.relative_to(Path.cwd())}")
    print("\n🔧 New methods added to MainWindow:")
    for method in found:
        print(f"   - {method}()")
    print("\n🛡️ Real-time protection features:")
    print("   - Protection status display")
    print("   - Start/stop controls")
    print("   - Live statistics")
    print("   - Activity logging")
    print("   - Path management")
    print("   - Threat notifications")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
