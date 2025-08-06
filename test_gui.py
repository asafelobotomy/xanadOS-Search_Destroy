#!/usr/bin/env python3
"""Simple test to check if the GUI starts correctly."""
import sys
import os
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Suppress Wayland warnings
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ.setdefault('QT_WAYLAND_DISABLE_WINDOWDECORATION', '1')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel

def test_basic_gui():
    """Test if PyQt6 GUI can start."""
    app = QApplication(sys.argv)
    
    # Create a simple test window
    window = QMainWindow()
    window.setWindowTitle("GUI Test")
    window.setGeometry(100, 100, 400, 300)
    
    central_widget = QWidget()
    layout = QVBoxLayout()
    label = QLabel("✅ GUI Test Successful!\nPyQt6 is working correctly.")
    label.setStyleSheet("font-size: 16px; padding: 20px;")
    layout.addWidget(label)
    central_widget.setLayout(layout)
    window.setCentralWidget(central_widget)
    
    window.show()
    print("✅ Basic GUI test successful!")
    
    # Close after 2 seconds
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(2000, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    try:
        result = test_basic_gui()
        print(f"✅ Test completed with exit code: {result}")
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        sys.exit(1)
