#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add app directory to Python path for proper imports
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Suppress Wayland popup warnings if on Wayland
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ.setdefault('QT_WAYLAND_DISABLE_WINDOWDECORATION', '1')

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("S&D - Search & Destroy")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("xanadOS")
    app.setOrganizationDomain("xanados.org")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()