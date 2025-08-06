#!/usr/bin/env python3
"""
Quick test to verify button text isn't being cut off
"""
import sys
import os
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Suppress Wayland warnings
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ.setdefault('QT_WAYLAND_DISABLE_WINDOWDECORATION', '1')

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class ButtonTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Button Text Test")
        self.setGeometry(100, 100, 500, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🔧 Button Text Cut-off Fix Test")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Hover over each button to test if text is fully visible:")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Test buttons with the exact same styling as the app
        quick_scan_btn = QPushButton("Quick Scan")
        quick_scan_btn.setObjectName("actionButton")
        quick_scan_btn.setMinimumSize(120, 40)
        
        update_btn = QPushButton("Update Definitions")
        update_btn.setObjectName("actionButton")
        update_btn.setMinimumSize(140, 40)
        
        about_btn = QPushButton("About")
        about_btn.setObjectName("actionButton")
        about_btn.setMinimumSize(80, 40)
        
        button_layout.addWidget(quick_scan_btn)
        button_layout.addWidget(update_btn)
        button_layout.addWidget(about_btn)
        
        layout.addLayout(button_layout)
        
        # Theme toggle
        theme_layout = QHBoxLayout()
        self.dark_btn = QPushButton("Dark Mode")
        self.light_btn = QPushButton("Light Mode")
        
        self.dark_btn.clicked.connect(self.apply_dark_theme)
        self.light_btn.clicked.connect(self.apply_light_theme)
        
        theme_layout.addWidget(self.dark_btn)
        theme_layout.addWidget(self.light_btn)
        layout.addLayout(theme_layout)
        
        # Result
        self.result_label = QLabel("✅ If text doesn't get cut off when hovering, the fix worked!")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14px; color: #28a745; font-weight: bold; margin-top: 20px;")
        layout.addWidget(self.result_label)
        
        layout.addStretch()
        
        # Start with dark theme
        self.apply_dark_theme()
        
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            #actionButton {
                background-color: #F14666;
                color: white;
                border: 4px solid #F14666;
                border-radius: 6px;
                font-weight: 700;
                padding: 12px 20px;
                min-width: 120px;
                text-align: center;
            }
            #actionButton:hover {
                background-color: #E6336B;
                border: 4px solid #EE8980;
                color: #ffffff;
                padding: 12px 20px;
            }
            #actionButton:pressed {
                background-color: #D12B5B;
                border: 4px solid #FFCDAA;
                padding: 12px 20px;
            }
        """)
        
    def apply_light_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fefefe;
                color: #2c2c2c;
            }
            #actionButton {
                background-color: #ffffff;
                color: #75BDE0;
                border: 4px solid #75BDE0;
                border-radius: 6px;
                font-weight: 700;
                padding: 12px 20px;
                min-width: 120px;
                text-align: center;
            }
            #actionButton:hover {
                background-color: #F8D49B;
                color: #2c2c2c;
                border: 4px solid #F8BC9B;
                padding: 12px 20px;
            }
            #actionButton:pressed {
                background-color: #F8BC9B;
                color: #1a1a1a;
                border: 4px solid #75BDE0;
                padding: 12px 20px;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = ButtonTestWindow()
    window.show()
    
    # Auto-close after 15 seconds
    QTimer.singleShot(15000, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
