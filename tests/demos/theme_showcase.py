#!/usr/bin/env python3
"""
Theme Showcase - Demonstrate all three stunning themes:
1. Dark (Professional) - Sophisticated strawberry/coral theme
2. Light (Aurora) - Breathtaking aurora borealis inspired
3. High Contrast (Accessibility) - Maximum accessibility compliance
Press F12 to cycle through all themes!
"""

import os
import sys

from gui.theme_manager import get_theme_manager, toggle_theme
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))


class ThemeShowcaseWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 xanadOS Search & Destroy - Theme Showcase")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("🌈 Theme Showcase Spectacular")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("headerTitle")
        # Font size now controlled by theme manager
        layout.addWidget(title)

        # Theme descriptions
        desc = QLabel(
            "🌟 <b>Dark (Professional)</b>: Sophisticated strawberry/coral with elegant gradients<br>"
            "🌞 <b>Light (Summer Breeze)</b>: Refreshing sky blue, seafoam, peach & yellow palette<br>"
            "🔍 <b>High Contrast (Accessibility)</b>: Maximum WCAG compliance for all users<br><br>"
            "🎯 Each theme is carefully crafted for different user preferences!"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 14px; line-height: 1.6; margin: 10px;")
        layout.addWidget(desc)

        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)

        # Theme control buttons
        self.cycle_btn = QPushButton("🔄 Cycle All Themes (F12)")
        self.cycle_btn.clicked.connect(self.cycle_themes)
        self.cycle_btn.setObjectName("primaryButton")
        self.cycle_btn.setMinimumHeight(50)
        button_layout.addWidget(self.cycle_btn)

        dark_btn = QPushButton("🌙 Dark Theme")
        dark_btn.clicked.connect(lambda: self.set_specific_theme("dark"))
        dark_btn.setMinimumHeight(50)
        button_layout.addWidget(dark_btn)

        light_btn = QPushButton("🌞 Summer Breeze")
        light_btn.clicked.connect(lambda: self.set_specific_theme("light"))
        light_btn.setMinimumHeight(50)
        button_layout.addWidget(light_btn)

        contrast_btn = QPushButton("🔍 High Contrast")
        contrast_btn.clicked.connect(lambda: self.set_specific_theme("high_contrast"))
        contrast_btn.setMinimumHeight(50)
        button_layout.addWidget(contrast_btn)

        layout.addWidget(button_container)

        # Demo elements container
        demo_container = QWidget()
        demo_layout = QVBoxLayout(demo_container)
        demo_layout.setSpacing(15)

        # Status display
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; padding: 15px; border: 2px solid; border-radius: 10px;"
        )
        demo_layout.addWidget(self.status_label)

        # Demo buttons to show theme effects
        demo_btn_container = QWidget()
        demo_btn_layout = QHBoxLayout(demo_btn_container)

        primary_demo = QPushButton("Primary Action")
        primary_demo.setObjectName("primaryButton")
        primary_demo.setMinimumHeight(40)
        demo_btn_layout.addWidget(primary_demo)

        secondary_demo = QPushButton("Secondary Action")
        secondary_demo.setMinimumHeight(40)
        demo_btn_layout.addWidget(secondary_demo)

        success_demo = QPushButton("Success State")
        success_demo.setStyleSheet(
            "background-color: " + get_theme_manager().get_color("success") + "; color: white;"
        )
        success_demo.setMinimumHeight(40)
        demo_btn_layout.addWidget(success_demo)

        demo_layout.addWidget(demo_btn_container)
        layout.addWidget(demo_container)

        # Instructions
        instructions = QLabel(
            "💡 <b>Instructions:</b><br>"
            "• Press F12 to cycle through all themes<br>"
            "• Click theme buttons to switch directly<br>"
            "• Notice the stunning visual differences!<br>"
            "• Each theme maintains full functionality"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 12px; color: gray; margin-top: 20px;")
        layout.addWidget(instructions)

        # Apply current theme and update status
        self.update_display()
        get_theme_manager()._apply_global_theme()

    def cycle_themes(self):
        """Cycle through all themes."""
        toggle_theme()
        self.update_display()
        self.show_theme_message()

    def set_specific_theme(self, theme_name):
        """Set a specific theme."""
        get_theme_manager().set_theme(theme_name)
        self.update_display()
        self.show_theme_message()

    def update_display(self):
        """Update the status display."""
        current_theme = get_theme_manager().get_current_theme()
        theme_name = get_theme_manager().get_theme_display_name(current_theme)

        # Update status with theme-specific styling
        if current_theme == "dark":
            self.status_label.setText(f"🌙 Current Theme: {theme_name}")
            self.status_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; padding: 15px; border: 2px solid #c62828; border-radius: 10px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c62828, stop:1 #e57373); color: white;"
            )
        elif current_theme == "light":
            self.status_label.setText(f"🌞 Current Theme: {theme_name}")
            self.status_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; padding: 15px; border: 2px solid #87CEEB; border-radius: 10px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #87CEEB, stop:1 #93E9BE); color: white;"
            )
        else:  # high_contrast
            self.status_label.setText(f"🔍 Current Theme: {theme_name}")
            self.status_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; padding: 15px; border: 3px solid #000000; border-radius: 10px; background: #ffffff; color: #000000;"
            )

    def show_theme_message(self):
        """Show a themed message about the current theme."""
        current_theme = get_theme_manager().get_current_theme()
        # Display name not used directly in the message body; keep call minimal
        _ = get_theme_manager().get_theme_display_name(current_theme)

        if current_theme == "dark":
            message = (
                "🌙 Dark (Professional) Theme Active!\n\n"
                "✨ Features:\n"
                "• Sophisticated strawberry/coral color palette\n"
                "• Elegant gradients and visual depth\n"
                "• Professional appearance for security software\n"
                "• Excellent for low-light environments"
            )
        elif current_theme == "light":
            message = (
                "🌞 Light (Summer Breeze) Theme Active!\n\n"
                "🌊 Features:\n"
                "• Refreshing summer color palette\n"
                "• Sky blue → seafoam → peach → yellow gradients\n"
                "• Bright and energizing without being harsh\n"
                "• Perfect for productive daytime work"
            )
        else:
            message = (
                "🔍 High Contrast (Accessibility) Theme Active!\n\n"
                "♿ Features:\n"
                "• Maximum WCAG AAA accessibility compliance\n"
                "• 21:1 contrast ratios for all text\n"
                "• Clear borders and high contrast colors\n"
                "• Designed for users with visual impairments"
            )

        msg = QMessageBox(self)
        msg.setWindowTitle("Theme Activated")
        msg.setText(message)
        msg.exec()


def main():
    app = QApplication(sys.argv)

    # Initialize theme system
    get_theme_manager()

    window = ThemeShowcaseWindow()
    window.show()

    print("🎨 Theme Showcase Window opened!")
    print("🌟 Available themes:")
    print("   1. Dark (Professional) - Sophisticated strawberry/coral")
    print("   2. Light (Summer Breeze) - Refreshing sky blue, seafoam, peach & yellow")
    print("   3. High Contrast (Accessibility) - Maximum WCAG compliance")
    print("🎯 Press F12 to cycle through all themes!")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
