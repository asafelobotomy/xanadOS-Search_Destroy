#!/usr/bin/env python3
"""
Qt Effects Demo - Shows the enhanced button effects and shadows
that replace CSS transitions, transforms, and box-shadows.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QDialog
from PyQt6.QtCore import Qt
from app.gui.theme_manager import get_theme_manager, setup_widget_effects, apply_button_effects, apply_shadow_effect


class EffectsDemo(QMainWindow):
    """Demonstration of Qt-native effects that replace CSS effects."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Effects Demo - CSS Alternative Effects")
        self.setGeometry(100, 100, 600, 400)
        
        # Initialize theming
        get_theme_manager().set_theme("dark")
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the demo interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Qt Effects Demo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "These buttons use Qt-native animations instead of CSS transitions/transforms.\n"
            "Hover and click to see the enhanced effects!"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("margin: 10px; color: #cccccc;")
        layout.addWidget(desc)
        
        # Button examples
        button_layout = QHBoxLayout()
        
        # Standard button with enhanced effects
        btn1 = QPushButton("Enhanced Button")
        btn1.setMinimumSize(150, 50)
        apply_button_effects(btn1)  # Apply Qt animations
        button_layout.addWidget(btn1)
        
        # Another button
        btn2 = QPushButton("Hover Me!")
        btn2.setMinimumSize(150, 50)
        apply_button_effects(btn2)
        button_layout.addWidget(btn2)
        
        # Button that opens a dialog with shadow
        btn3 = QPushButton("Open Dialog")
        btn3.setMinimumSize(150, 50)
        apply_button_effects(btn3)
        btn3.clicked.connect(self.show_shadow_dialog)
        button_layout.addWidget(btn3)
        
        layout.addLayout(button_layout)
        
        # Auto-setup effects for the main window
        setup_widget_effects(self)
        
    def show_shadow_dialog(self):
        """Show a dialog with shadow effects."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Shadow Effect Demo")
        dialog.setModal(True)
        dialog.resize(300, 200)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("This dialog uses Qt's QGraphicsDropShadowEffect\ninstead of CSS box-shadow")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        close_btn = QPushButton("Close")
        apply_button_effects(close_btn)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        # Apply shadow effect to the dialog
        apply_shadow_effect(dialog)
        
        dialog.exec()


def main():
    """Run the effects demo."""
    app = QApplication(sys.argv)
    
    # Setup theming
    get_theme_manager().set_theme("auto")
    
    demo = EffectsDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
