#!/usr/bin/env python3
"""
Test button text with minimal padding approach
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

class MinimalPaddingTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔧 Minimal Padding Button Test")
        self.setGeometry(100, 100, 600, 350)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🎯 Reduced Padding + Min-Height Approach")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Testing: padding: 6px 12px + min-height: 32px + line-height: 1.3")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("font-size: 12px; margin-bottom: 10px; color: #666;")
        layout.addWidget(instructions)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Test buttons
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
        
        # Theme buttons
        theme_layout = QHBoxLayout()
        self.dark_btn = QPushButton("Dark Theme")
        self.light_btn = QPushButton("Light Theme")
        
        self.dark_btn.clicked.connect(self.apply_dark_theme)
        self.light_btn.clicked.connect(self.apply_light_theme)
        
        theme_layout.addWidget(self.dark_btn)
        theme_layout.addWidget(self.light_btn)
        layout.addLayout(theme_layout)
        
        # Status
        self.status_label = QLabel("✨ Hover over buttons to test text visibility")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; margin-top: 20px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Start with light theme to test the problematic one
        self.apply_light_theme()
        
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
                padding: 6px 12px;
                min-width: 120px;
                min-height: 32px;
                text-align: center;
                line-height: 1.3;
                font-size: 13px;
            }
            #actionButton:hover {
                background-color: #F8D49B;
                color: #2c2c2c;
                border: 4px solid #F8BC9B;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            #actionButton:pressed {
                background-color: #F8BC9B;
                color: #1a1a1a;
                border: 4px solid #75BDE0;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
        """)
        self.status_label.setText("🌞 Light Mode: Check if text bottom is visible")
        self.status_label.setStyleSheet("color: #75BDE0; font-size: 14px; margin-top: 20px; font-weight: bold;")
        
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
                padding: 6px 12px;
                min-width: 120px;
                min-height: 32px;
                text-align: center;
                line-height: 1.3;
                font-size: 13px;
            }
            #actionButton:hover {
                background-color: #E6336B;
                border: 4px solid #EE8980;
                color: #ffffff;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            #actionButton:pressed {
                background-color: #D12B5B;
                border: 4px solid #FFCDAA;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
        """)
        self.status_label.setText("🌙 Dark Mode: Check if text bottom is visible")
        self.status_label.setStyleSheet("color: #F14666; font-size: 14px; margin-top: 20px; font-weight: bold;")

def main():
    app = QApplication(sys.argv)
    window = MinimalPaddingTestWindow()
    window.show()
    
    print("🔧 Testing minimal padding approach:")
    print("   • Reduced padding from 15px 22px to 6px 12px")
    print("   • Added min-height: 32px for consistent button height")  
    print("   • Increased line-height from 1.2 to 1.3 for better text spacing")
    print("   • Kept text-align: center and font-size: 13px")
    print()
    print("📝 Test both themes and hover over all buttons!")
    
    # Auto-close after 20 seconds
    QTimer.singleShot(20000, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
