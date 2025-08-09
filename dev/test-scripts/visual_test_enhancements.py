#!/usr/bin/env python3
"""
Visual test for scan enhancements - shows the GUI with all new features
"""

import sys
import os
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from gui.main_window import MainWindow

def main():
    """Launch the application to visually inspect the enhancements."""
    app = QApplication(sys.argv)
    window = MainWindow()
    
    print("🚀 Launching xanadOS Search & Destroy with Scan Enhancements")
    print("=" * 60)
    print()
    print("✨ New Features Available:")
    print("  📊 Scan Tab:")
    print("    • Scan Type Selector (Quick/Full/Custom)")
    print("    • Advanced Options Panel (collapsible)")
    print("    • Enhanced scan configuration")
    print()
    print("  ⚙️  Settings Tab:")
    print("    • Scheduled Scan Management")
    print("    • Frequency and time selection")
    print("    • Next scan display")
    print()
    print("  🎨 UI Improvements:")
    print("    • Professional styling for new elements")
    print("    • Consistent theme integration")
    print("    • Intuitive user experience")
    print()
    print("Navigate to the 'Scan' tab to see the new scan type selector")
    print("and advanced options panel.")
    print()
    print("Check the 'Settings' tab for scheduled scan configuration.")
    print()
    print("Close the window to exit.")
    print("=" * 60)
    
    # Show the window
    window.show()
    
    # Set window title to indicate this is the enhanced version
    window.setWindowTitle("xanadOS Search & Destroy - Enhanced Scanning")
    
    # Optionally switch to scan tab to highlight the new features
    if hasattr(window, 'tab_widget'):
        # Find the scan tab index
        for i in range(window.tab_widget.count()):
            if window.tab_widget.tabText(i) == "Scan":
                window.tab_widget.setCurrentIndex(i)
                break
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
