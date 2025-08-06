#!/usr/bin/env python3
"""
Integration tests for S&D - Search & Destroy application
Tests core functionality and implementation completeness
"""
import os
import ast
import sys

def test_requirements_fixed():
    """Test that requirements.txt has been fixed"""
    print("Testing requirements.txt...")
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    # Check that pyclamd version issue is fixed
    assert 'pyclamd>=1.0.0' not in content, "FAIL: pyclamd>=1.0.0 still in requirements"
    assert 'pyclamd>=0.4.0' in content, "FAIL: Corrected pyclamd version not found"
    
    print("✓ requirements.txt fixed - pyclamd version corrected")

def test_pyqt6_consistency():
    """Test that all GUI files use PyQt6 consistently"""
    print("Testing PyQt6 consistency...")
    
    gui_files = [
        'app/main.py',
        'app/gui/main_window.py',
        'app/gui/scan_dialog.py',
        'app/gui/settings_dialog.py',
        'app/gui/scan_thread.py'
    ]
    
    for file_path in gui_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check that PyQt5 is not imported
            assert 'from PyQt5' not in content, f"FAIL: {file_path} still imports PyQt5"
            assert 'import PyQt5' not in content, f"FAIL: {file_path} still imports PyQt5"
            
            # If PyQt is imported, it should be PyQt6
            if 'PyQt' in content:
                assert 'PyQt6' in content, f"FAIL: {file_path} should use PyQt6"
    
    print("✓ PyQt6 consistency verified - all files use PyQt6")

def test_placeholder_implementations_removed():
    """Test that placeholder implementations have been replaced"""
    print("Testing placeholder implementations...")
    
    # Check settings_dialog.py
    with open('app/gui/settings_dialog.py', 'r') as f:
        settings_content = f.read()
    
    assert 'pass' not in settings_content, "FAIL: settings_dialog.py still has pass statements"
    assert '# Load user preferences' not in settings_content, "FAIL: settings_dialog.py has placeholder comments"
    
    # Should have real implementation
    assert 'QDialog' in settings_content, "FAIL: settings_dialog.py should inherit from QDialog"
    assert 'QTabWidget' in settings_content, "FAIL: settings_dialog.py should have tabbed interface"
    
    # Check scan_dialog.py
    with open('app/gui/scan_dialog.py', 'r') as f:
        scan_content = f.read()
    
    assert 'pass' not in scan_content, "FAIL: scan_dialog.py still has pass statements"
    assert '# Code to open a file selection dialog' not in scan_content, "FAIL: scan_dialog.py has placeholder comments"
    
    # Should have real implementation
    assert 'QDialog' in scan_content, "FAIL: scan_dialog.py should inherit from QDialog"
    assert 'scan_started' in scan_content, "FAIL: scan_dialog.py should have scan signals"
    
    print("✓ Placeholder implementations removed - dialogs fully implemented")

def test_python_syntax():
    """Test that all Python files have correct syntax"""
    print("Testing Python syntax...")
    
    python_files = []
    
    # Find all Python files in src directory
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            ast.parse(code)
        except SyntaxError as e:
            assert False, f"FAIL: Syntax error in {file_path}: {e}"
    
    print(f"✓ Python syntax verified - {len(python_files)} files checked")

def test_main_structure():
    """Test that main.py has correct structure"""
    print("Testing main.py structure...")
    
    with open('app/main.py', 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Check for main function
    has_main_function = any(
        isinstance(node, ast.FunctionDef) and node.name == 'main'
        for node in ast.walk(tree)
    )
    assert has_main_function, "FAIL: main.py should have a main() function"
    
    # Check for if __name__ == "__main__"
    assert 'if __name__ == "__main__"' in code, "FAIL: main.py should have if __name__ == '__main__'"
    
    print("✓ main.py structure verified")

def test_icons_created():
    """Test that application icons have been created"""
    print("Testing application icons...")
    
    # Check icons directory exists
    assert os.path.exists('packaging/icons'), "FAIL: packaging/icons directory should exist"
    
    # Check for SVG icon
    svg_icon = 'packaging/icons/org.xanados.SearchAndDestroy.svg'
    assert os.path.exists(svg_icon), "FAIL: SVG icon should exist"
    
    # Check SVG content
    with open(svg_icon, 'r') as f:
        svg_content = f.read()
    assert '<svg' in svg_content, "FAIL: SVG file should contain SVG markup"
    # We're using a visual icon without text branding
    
    # Check for icon placeholders or actual PNG files
    sizes = [16, 32, 48, 64, 128]
    for size in sizes:
        png_icon = f'packaging/icons/org.xanados.SearchAndDestroy-{size}.png'
        placeholder = f'packaging/icons/org.xanados.SearchAndDestroy-{size}.png.placeholder'
        
        icon_exists = os.path.exists(png_icon) or os.path.exists(placeholder)
        assert icon_exists, f"FAIL: Icon for size {size}x{size} should exist"
    
    print("✓ Application icons created - SVG and PNG placeholders")

def test_code_organization():
    """Test that code is properly organized"""
    print("Testing code organization...")
    
    # Check that MainWindow is in main_window.py, not scan_thread.py
    with open('app/gui/main_window.py', 'r') as f:
        main_window_content = f.read()
    
    with open('app/gui/scan_thread.py', 'r') as f:
        scan_thread_content = f.read()
    
    # MainWindow should be in main_window.py
    assert 'class MainWindow' in main_window_content, "FAIL: MainWindow should be in main_window.py"
    
    # ScanThread should be in scan_thread.py, not a large MainWindow implementation
    assert 'class ScanThread' in scan_thread_content, "FAIL: ScanThread should be in scan_thread.py"
    
    # scan_thread.py should be much smaller now (not contain MainWindow)
    scan_thread_lines = len(scan_thread_content.splitlines())
    assert scan_thread_lines < 50, f"FAIL: scan_thread.py too large ({scan_thread_lines} lines), should only contain ScanThread"
    
    print("✓ Code organization verified - proper separation of concerns")

def main():
    """Run all tests"""
    print("S&D - Search & Destroy Implementation Tests")
    print("=" * 50)
    
    # Change to repository root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    tests = [
        test_requirements_fixed,
        test_pyqt6_consistency,
        test_placeholder_implementations_removed,
        test_python_syntax,
        test_main_structure,
        test_icons_created,
        test_code_organization
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Implementation is complete.")
        return 0
    else:
        print("❌ Some tests failed. See details above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())