#!/usr/bin/env python3
"""
Unit tests for S&D - Search & Destroy GUI components
"""
import os

import sys

from unittest.mock import Mock

import ast

import unittest

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# Mock PyQt6 before any imports
mock_pyqt6_modules = ["PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui"]

for module in mock_pyqt6_modules:
    sys.modules[module] = Mock()

# Mock other dependencies
mock_modules = ["pyclamd", "requests", "schedule", "psutil"]

for module in mock_modules:
    sys.modules[module] = Mock()

class TestMainWindow(unittest.TestCase):
    """Test cases for MainWindow class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary package structure for imports
        if "scanner" not in sys.modules:
            sys.modules["scanner"] = Mock()
        if "scanner.file_scanner" not in sys.modules:
            sys.modules["scanner.file_scanner"] = Mock()
        if "utils" not in sys.modules:
            sys.modules["utils"] = Mock()
        if "utils.config" not in sys.modules:
            sys.modules["utils.config"] = Mock()
        if "utils.scan_reports" not in sys.modules:
            sys.modules["utils.scan_reports"] = Mock()

        # Mock specific classes
        mock_file_scanner = Mock()
        mock_config = Mock()
        mock_scan_reports = Mock()

        sys.modules["scanner.file_scanner"].FileScanner = mock_file_scanner
        sys.modules["utils.config"].Config = mock_config
        sys.modules["utils.scan_reports"].ScanReportManager = mock_scan_reports

    def test_main_window_syntax(self):
        """Test that main_window.py has valid Python syntax"""
        main_window_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "gui", "main_window.py"
        )
        try:
            with open(main_window_path, "r", encoding="utf-8") as f:
                ast.parse(f.read())
            # If we get here, the syntax is valid
        except Exception as e:
            self.fail(f"Syntax error in main_window.py: {e}")

    def test_scan_thread_syntax(self):
        """Test that scan_thread.py has valid Python syntax"""
        scan_thread_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "gui", "scan_thread.py"
        )
        try:
            with open(scan_thread_path, "r", encoding="utf-8") as f:
                code = f.read()
            ast.parse(code)
            # If we get here, the syntax is valid
        except Exception as e:
            self.fail(f"Syntax error in scan_thread.py: {e}")

class TestApplicationStructure(unittest.TestCase):
    """Test cases for overall application structure"""

    def test_main_entry_point(self):
        """Test that main.py has correct structure"""
        try:
            main_path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
            with open(main_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Parse the code to ensure it's valid Python
            tree = ast.parse(code)

            # Check for main function
            has_main_function = any(
                isinstance(node, ast.FunctionDef) and node.name == "main" for node in ast.walk(tree)
            )
            self.assertTrue(has_main_function, "main.py should have a main() function")

        except FileNotFoundError as e:
            self.fail(f"Could not find main.py: {e}")
        except SyntaxError as e:
            self.fail(f"Syntax error in main.py: {e}")

    def test_pyqt6_consistency(self):
        """Test that all GUI files use PyQt6 consistently"""
        base_path = os.path.join(os.path.dirname(__file__), "..")
        gui_files = [
            os.path.join(base_path, "app", "gui", "main_window.py"),
            os.path.join(base_path, "app", "gui", "scan_thread.py"),
        ]

        for file_path in gui_files:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check that PyQt5 is not imported
                self.assertNotIn("from PyQt5", content, f"{file_path} should not import PyQt5")
                self.assertNotIn("import PyQt5", content, f"{file_path} should not import PyQt5")

                # If PyQt is imported, it should be PyQt6
                if "PyQt" in content:
                    self.assertIn(
                        "PyQt6", content, f"{file_path} should use PyQt6 if importing PyQt"
                    )

class TestRequirements(unittest.TestCase):
    """Test cases for project requirements and dependencies"""

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists and is readable"""
        base_path = os.path.join(os.path.dirname(__file__), "..")
        requirements_path = os.path.join(base_path, "requirements.txt")
        self.assertTrue(os.path.exists(requirements_path), "requirements.txt should exist")

        with open(requirements_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("PyQt6", content, "PyQt6 should be in requirements")
        self.assertIn("psutil", content, "psutil should be in requirements")

        # Check that pyclamd version is correct (not 1.0.0 which doesn't exist)
        self.assertNotIn("pyclamd>=1.0.0", content, "pyclamd>=1.0.0 does not exist")

    def test_icons_exist(self):
        """Test that application icons exist"""
        base_path = os.path.join(os.path.dirname(__file__), "..")
        icons_dir = os.path.join(base_path, "packaging", "icons")
        self.assertTrue(os.path.exists(icons_dir), "packaging/icons directory should exist")

        # Check for SVG icon (Prefer io.github.* naming per Flathub guidelines)
        svg_icon = os.path.join(icons_dir, "io.github.asafelobotomy.SearchAndDestroy.svg")
        self.assertTrue(os.path.exists(svg_icon), "SVG icon should exist")

        # Check for icon placeholders (or actual PNG files)
        sizes = [16, 32, 48, 64, 128]
        for size in sizes:
            png_icon = os.path.join(
                icons_dir, f"io.github.asafelobotomy.SearchAndDestroy-{size}.png"
            )
            placeholder = os.path.join(
                icons_dir, f"io.github.asafelobotomy.SearchAndDestroy-{size}.png.placeholder"
            )

            icon_exists = os.path.exists(png_icon) or os.path.exists(placeholder)
            self.assertTrue(
                icon_exists, f"Icon for size {size}x{size} should exist (PNG or placeholder)"
            )

class TestCodeQuality(unittest.TestCase):
    """Test cases for code quality and standards"""

    def test_no_syntax_errors(self):
        """Test that all Python files have correct syntax"""
        python_files = []

        # Find all Python files in app directory
        src_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        for file_path in python_files:
            with self.subTest(file_path=file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    ast.parse(code)
                except SyntaxError as e:
                    self.fail(f"Syntax error in {file_path}: {e}")

if __name__ == "__main__":
    # Change to the tests directory for relative path imports
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run the tests
    unittest.main(verbosity=2)
