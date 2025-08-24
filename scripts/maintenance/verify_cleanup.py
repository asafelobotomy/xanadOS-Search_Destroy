#!/usr/bin/env python3
"""
Repository Cleanup Verification
Verifies that the xanadOS Search & Destroy repository is properly organized and functional.
"""

import os
import sys
from pathlib import Path

def check_repository_structure():
    """Verify the repository structure is clean and organized."""
    print("🔍 Verifying Repository Structure...")
    
    # Determine base directory dynamically (two levels up from this script if run from dev/)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Check for cache directories in application code
    app_cache_dirs = list(base_dir.glob("app/**/__pycache__"))
    if app_cache_dirs:
        print(f"❌ Found {len(app_cache_dirs)} cache directories in app/")
        return False
    else:
        print("✅ No cache directories found in application code")
    
    # Check for proper directory structure
    required_dirs = ["app", "docs", "scripts", "config", "tests", "archive", "dev"]
    missing_dirs = []
    for dir_name in required_dirs:
        if not (base_dir / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Missing required directories: {missing_dirs}")
        return False
    else:
        print("✅ All required directories present")
    
    # Check for documentation organization
    impl_docs = base_dir / "docs" / "implementation"
    if (impl_docs / "SECURITY_IMPROVEMENTS.md").exists() and (impl_docs / "scan_methods_audit.md").exists():
        print("✅ Documentation properly organized")
    else:
        print("❌ Documentation files not properly organized")
        return False
    
    return True

def check_application_imports():
    """Verify that the application can be imported without errors."""
    print("\n🔍 Verifying Application Imports...")
    
    try:
        # Add the app directory to Python path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
        
        # Try importing core modules
        import core.rkhunter_wrapper
        import gui.main_window
        import monitoring.real_time_monitor
        print("✅ Core application modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all verification checks."""
    print("🧹 xanadOS Search & Destroy - Repository Cleanup Verification")
    print("=" * 60)
    
    structure_ok = check_repository_structure()
    imports_ok = check_application_imports()
    
    print("\n" + "=" * 60)
    if structure_ok and imports_ok:
        print("🎉 Repository cleanup verification PASSED!")
        print("📁 Repository is clean, organized, and functional")
        return 0
    else:
        print("❌ Repository cleanup verification FAILED!")
        print("🔧 Some issues need to be addressed")
        return 1

if __name__ == "__main__":
    exit(main())
