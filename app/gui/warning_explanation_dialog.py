#!/usr/bin/env python3
"""RKHunter Warning Explanation Dialog
Provides detailed explanations and guidance for each RKHunter warning.
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QMessageBox

from app.core.rkhunter_analyzer import SeverityLevel, WarningExplanation
from app.gui.theme_manager import get_theme_manager
from app.gui.themed_widgets import ThemedDialog

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class WarningExplanationDialog(ThemedDialog):
    """Dialog to display detailed warning explanations."""

    # Signals
    mark_as_safe = pyqtSignal(str)  # Emit warning text when marked as safe
    investigate_requested = pyqtSignal(str)  # Emit warning text for investigation

    def __init__(self, warning_text: str, explanation: WarningExplanation, parent=None):
        super().__init__(parent)
        self.warning_text = warning_text
        self.explanation = explanation
        self.parent_window = parent

        self.setWindowTitle("RKHunter Warning Explanation")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()

        # Theme is now handled by global theme manager automatically

    def _get_severity_icon(self) -> QPixmap:
        """Get icon based on severity level."""
        # Create a simple colored circle icon based on severity
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)

        # In a real implementation, you'd use proper icons
        # For now, we'll use the text-based icons from the analyzer
        {
            SeverityLevel.LOW: "ℹ️",
            SeverityLevel.MEDIUM: "⚠️",
            SeverityLevel.HIGH: "🚨",
            SeverityLevel.CRITICAL: "🔴",
        }.get(self.explanation.severity, "❓")

        # For simplicity, return empty pixmap (icon text will be in badge)
        return pixmap

    def _create_severity_badge(self) -> QLabel:
        """Create severity level badge."""
        badge = QLabel(self.explanation.severity.value.upper())
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setMinimumSize(80, 30)

        # Color based on severity - using theme colors where appropriate
        colors = {
            SeverityLevel.LOW: get_theme_manager().get_color("success"),  # Green
            SeverityLevel.MEDIUM: get_theme_manager().get_color(
                "warning"
            ),  # Yellow/Orange
            SeverityLevel.HIGH: get_theme_manager().get_color("warning"),  # Orange
            SeverityLevel.CRITICAL: get_theme_manager().get_color("error"),  # Red
        }

        color = colors.get(
            self.explanation.severity, get_theme_manager().get_color("muted_text")
        )
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
            }}
        """
        )

        return badge

    def _apply_styles(self):
        """Apply custom styles to the dialog."""
        # Removed: Now handled by global theme manager

    def get_theme_color(self, color_key):
        """Get theme-appropriate color from theme manager."""
        try:
            return get_theme_manager().get_color(color_key)
        except BaseException:
            # Fallback colors for dark theme if theme manager fails
            fallback_colors = {
                "background": "#1a1a1a",
                "secondary_bg": "#2a2a2a",
                "tertiary_bg": "#3a3a3a",
                "primary_text": "#FFCDAA",
                "secondary_text": "#999",
                "success": "#9CB898",
                "error": "#F14666",
                "warning": "#EE8980",
                "accent": "#F14666",
                "border": "#EE8980",
                "hover_bg": "#4a4a4a",
                "pressed_bg": "#2a2a2a",
            }
            return fallback_colors.get(color_key, "#FFCDAA")

    def _show_themed_message_box(self, msg_type, title, text, buttons=None):
        """Show a message box with proper theming."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)

        # Set message type
        if msg_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif msg_type == "information":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif msg_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        elif msg_type == "question":
            msg_box.setIcon(QMessageBox.Icon.Question)

        # Set buttons
        if buttons:
            msg_box.setStandardButtons(buttons)
        else:
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Apply theme-specific styling
        bg = self.get_theme_color("background")
        text_color = self.get_theme_color("primary_text")
        tertiary_bg = self.get_theme_color("tertiary_bg")
        border = self.get_theme_color("border")
        hover_bg = self.get_theme_color("hover_bg")
        pressed_bg = self.get_theme_color("pressed_bg")
        accent = self.get_theme_color("accent")
        success = self.get_theme_color("success")

        style = f"""
            QMessageBox {{
                background-color: {bg};
                color: {text_color};
                font-size: 12px;
                font-weight: 500;
                border: 2px solid {border};
                border-radius: 6px;
            }}
            QMessageBox QLabel {{
                color: {text_color};
                font-weight: 600;
                padding: 10px;
                line-height: 1.4;
            }}
            QMessageBox QPushButton {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 5px;
                padding: 8px 16px;
                color: {text_color};
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent};
                color: {text_color};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
            QMessageBox QPushButton:default {{
                background-color: {success};
                border-color: {success};
                color: {bg};
                font-weight: 700;
            }}
            QMessageBox QPushButton:default:hover {{
                background-color: {hover_bg};
                border-color: {hover_bg};
            }}
        """
        msg_box.setStyleSheet(style)

        return msg_box.exec()

    def _on_investigate(self):
        """Handle investigate button click."""
        self.investigate_requested.emit(self.warning_text)
        # You could also open a web search or documentation
        self._show_themed_message_box(
            "information",
            "Investigation Tips",
            f"To investigate this warning further:\n\n"
            f'1. Search online for: "{self.warning_text[:50]}..."\n'
            f"2. Check RKHunter documentation\n"
            f"3. Review recent system changes\n"
            f"4. Consult security forums if concerned",
        )

    def _on_mark_safe(self):
        """Handle mark as safe button click."""
        if not self.mark_safe_checkbox.isChecked():
            return

        reply = self._show_themed_message_box(
            "question",
            "Mark Warning as Safe",
            "Are you sure you want to mark this warning as safe?\n\n"
            "This will:\n"
            "• Hide this warning in future scans\n"
            "• Add it to the safe warnings list\n"
            "• Reduce the warning count in reports\n\n"
            "Only do this if you're confident the warning is harmless.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.mark_as_safe.emit(self.warning_text)
            self.accept()
