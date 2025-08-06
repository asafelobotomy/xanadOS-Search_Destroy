#!/usr/bin/env python3
"""
Light mode button text clipping test - focused on the bottom text issue
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

class LightModeButtonTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Light Mode Button Text Fix Test")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🔧 Light Mode Button Text Test")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #2c2c2c;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Test: Hover over buttons - bottom of text should NOT be cut off")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("font-size: 14px; margin-bottom: 20px; color: #666;")
        layout.addWidget(instructions)
        
        # Before/After comparison
        before_label = QLabel("BEFORE: padding: 12px 20px (text gets cut off)")
        before_label.setStyleSheet("font-size: 12px; color: #dc3545; font-weight: bold;")
        layout.addWidget(before_label)
        
        # Old style buttons (with the problem)
        old_layout = QHBoxLayout()
        old_quick = QPushButton("Quick Scan")
        old_update = QPushButton("Update Definitions") 
        old_about = QPushButton("About")
        
        for btn in [old_quick, old_update, old_about]:
            btn.setObjectName("oldActionButton")
            btn.setMinimumSize(120, 40)
            
        old_layout.addWidget(old_quick)
        old_layout.addWidget(old_update)
        old_layout.addWidget(old_about)
        layout.addLayout(old_layout)
        
        layout.addWidget(QLabel(""))  # Spacer
        
        after_label = QLabel("AFTER: padding: 15px 22px + line-height: 1.2 (text should be fine)")
        after_label.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold;")
        layout.addWidget(after_label)
        
        # New style buttons (with the fix)
        new_layout = QHBoxLayout()
        new_quick = QPushButton("Quick Scan")
        new_update = QPushButton("Update Definitions")
        new_about = QPushButton("About")
        
        for btn in [new_quick, new_update, new_about]:
            btn.setObjectName("newActionButton")
            btn.setMinimumSize(120, 40)
            
        new_layout.addWidget(new_quick)
        new_layout.addWidget(new_update)
        new_layout.addWidget(new_about)
        layout.addLayout(new_layout)
        
        layout.addStretch()
        
        # Apply light mode styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fefefe;
                color: #2c2c2c;
            }
            
            /* OLD STYLE - with the problem */
            #oldActionButton {
                background-color: #ffffff;
                color: #75BDE0;
                border: 4px solid #75BDE0;
                border-radius: 6px;
                font-weight: 700;
                padding: 12px 20px;
                min-width: 120px;
                text-align: center;
            }
            #oldActionButton:hover {
                background-color: #F8D49B;
                color: #2c2c2c;
                border: 4px solid #F8BC9B;
                padding: 12px 20px;
            }
            
            /* NEW STYLE - with the fix */
            #newActionButton {
                background-color: #ffffff;
                color: #75BDE0;
                border: 4px solid #75BDE0;
                border-radius: 6px;
                font-weight: 700;
                padding: 15px 22px;
                min-width: 120px;
                text-align: center;
                line-height: 1.2;
                font-size: 13px;
            }
            #newActionButton:hover {
                background-color: #F8D49B;
                color: #2c2c2c;
                border: 4px solid #F8BC9B;
                padding: 15px 22px;
                line-height: 1.2;
                font-size: 13px;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = LightModeButtonTest()
    window.show()
    
    print("🔧 Light Mode Button Text Fix Test")
    print("=" * 40)
    print("✅ Applied fixes:")
    print("   • Increased padding: 12px 20px → 15px 22px")
    print("   • Added line-height: 1.2")
    print("   • Set font-size: 13px")
    print("   • Consistent across all button states")
    print()
    print("🎯 Test: Hover over the 'AFTER' buttons")
    print("   Bottom of text should NOT be cut off!")
    
    # Auto-close after 20 seconds
    QTimer.singleShot(20000, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
