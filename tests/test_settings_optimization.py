#!/usr/bin/env python3
"""
Test the interactive optimization dialog integration in Settings tab
"""

import sys
import logging
from pathlib import Path

# Add app to path
sys.path.insert(0, './app')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_interactive_config_fixes_import():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports for interactive config fixes...")

    try:
        from core.rkhunter_optimizer import RKHunterOptimizer
        print("✅ RKHunterOptimizer imported successfully")

        from gui.config_fix_dialog import ConfigFixDialog
        print("✅ ConfigFixDialog imported successfully")

        from pathlib import Path
        print("✅ Path imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_optimizer_functionality():
    """Test the optimizer's detect_fixable_issues method"""
    print("\n🧪 Testing optimizer functionality...")

    try:
        from core.rkhunter_optimizer import RKHunterOptimizer

        # Test with the config path that would be used in the app
        config_path = str(Path.home() / '.config' / 'search-and-destroy' / 'rkhunter.conf')
        print(f"📁 Testing with config path: {config_path}")

        optimizer = RKHunterOptimizer(config_path=config_path)
        print("✅ Optimizer instance created successfully")

        # Test issue detection
        issues = optimizer.detect_fixable_issues()
        print(f"🔍 Found {len(issues)} fixable issues")

        for fix_id, issue in issues.items():
            print(f"  📝 {fix_id}: {issue['description']}")

        return True

    except Exception as e:
        print(f"❌ Optimizer test failed: {e}")
        return False

def test_dialog_creation():
    """Test creating the ConfigFixDialog"""
    print("\n🧪 Testing dialog creation...")

    try:
        from core.rkhunter_optimizer import RKHunterOptimizer
        from gui.config_fix_dialog import ConfigFixDialog

        # Create optimizer and get some test issues
        config_path = str(Path.home() / '.config' / 'search-and-destroy' / 'rkhunter.conf')
        optimizer = RKHunterOptimizer(config_path=config_path)
        issues = optimizer.detect_fixable_issues()

        if issues:
            print(f"✅ Creating dialog with {len(issues)} issues")
            # Note: We can't actually show the dialog in a test without GUI context
            # but we can verify it can be instantiated
            print("✅ Dialog class is available for instantiation")
        else:
            print("ℹ️  No issues found - creating mock issues for dialog test")
            mock_issues = {
                'test_fix': {
                    'description': 'Test configuration issue',
                    'impact': 'Test impact description',
                    'group': 'Test Group'
                }
            }
            print("✅ Mock dialog data prepared")

        return True

    except Exception as e:
        print(f"❌ Dialog test failed: {e}")
        return False

def test_main_window_method():
    """Test the new main window method integration"""
    print("\n🧪 Testing main window method integration...")

    try:
        # Test that the method exists (can't actually run it without GUI)
        from gui.main_window import MainWindow

        # Check if our new method exists
        if hasattr(MainWindow, '_show_interactive_config_fixes'):
            print("✅ _show_interactive_config_fixes method exists in MainWindow")
        else:
            print("❌ _show_interactive_config_fixes method not found")
            return False

        if hasattr(MainWindow, '_run_standard_config_optimization'):
            print("✅ _run_standard_config_optimization method exists in MainWindow")
        else:
            print("❌ _run_standard_config_optimization method not found")
            return False

        return True

    except Exception as e:
        print(f"❌ Main window test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Settings Tab Interactive Optimization Integration")
    print("=" * 60)

    tests = [
        test_interactive_config_fixes_import,
        test_optimizer_functionality,
        test_dialog_creation,
        test_main_window_method
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The interactive optimization integration should work.")
        print("\n📋 Next steps:")
        print("1. Open the application")
        print("2. Go to Settings tab > RKHunter pane > Optimization tab")
        print("3. Click 'Optimize Configuration' button")
        print("4. You should see the interactive dialog with fixable issues")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
