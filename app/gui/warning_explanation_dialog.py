#!/usr/bin/env python3
"""
RKHunter Warning Explanation Dialog
Provides detailed explanations and guidance for RKHunter warnings
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QWidget, QFrame, QGroupBox,
    QCheckBox, QMessageBox
)

from app.core.rkhunter_analyzer import WarningExplanation, SeverityLevel
from app.gui.themed_widgets import ThemedDialog


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
        
        # Apply parent theme if available
        if parent and hasattr(parent, "current_theme"):
            self._apply_theme(parent.current_theme)
        else:
            # Default to dark for consistency
            self._apply_theme("dark")
    def _apply_theme(self, theme_name):
        """Apply theme styling to this dialog (supports dark & light)."""
        # Determine if using light theme heuristically
        is_light = theme_name == "light"
        bg = self.get_theme_color("background") if not is_light else "#ffffff"
        secondary_bg = self.get_theme_color("secondary_bg") if not is_light else "#f7f7f9"
        tertiary_bg = self.get_theme_color("tertiary_bg") if not is_light else "#ededf0"
        text = self.get_theme_color("primary_text") if not is_light else "#222222"
        border = self.get_theme_color("border") if not is_light else "#d0d0d5"
        accent = self.get_theme_color("accent") if not is_light else "#0078d4"
        hover_bg = self.get_theme_color("hover_bg") if not is_light else "#e6f2fb"
        pressed_bg = self.get_theme_color("pressed_bg") if not is_light else "#cfe6f7"
        
        style = f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QGroupBox {{
                color: {text};
                border: 2px solid {border};
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 0.8em;
                background-color: {secondary_bg};
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 10px 0 10px;
                color: {accent};
                font-weight: 700;
                font-size: 14px;
            }}
            QLabel {{
                color: {text};
                font-weight: 500;
            }}
            QTextEdit {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 6px;
                color: {text};
                font-family: monospace;
                font-size: 10px;
                selection-background-color: {accent};
                selection-color: {bg};
            }}
            QCheckBox {{
                color: {text};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {border};
                background-color: {bg};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {accent};
                background-color: {accent};
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {secondary_bg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 8px 16px;
                color: {text};
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
            QScrollArea {{
                border: 1px solid {border};
                border-radius: 6px;
                background-color: {secondary_bg};
            }}
            QScrollBar:vertical {{
                background-color: {secondary_bg};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {hover_bg};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {accent};
            }}
        """
        self.setStyleSheet(style)
        # Common issue indicator
        if self.explanation.is_common:
            common_group = QGroupBox("ℹ️ Good to Know")
            common_layout = QVBoxLayout(common_group)
            common_label = QLabel("This is a common warning that often occurs during normal system operation. It's usually not a cause for concern.")
            common_label.setWordWrap(True)
            common_label.setObjectName("commonLabel")  # For themed styling
            # Theme will be applied later - don't hard-code styles here
            common_layout.addWidget(common_label)
            scroll_layout.addWidget(common_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Mark as safe checkbox and button
        self.mark_safe_checkbox = QCheckBox("I understand this warning and want to mark it as safe")
        button_layout.addWidget(self.mark_safe_checkbox)
        
        button_layout.addStretch()
        
        # Investigate button
        investigate_btn = QPushButton("🔍 Investigate Further")
        investigate_btn.clicked.connect(self._on_investigate)
        button_layout.addWidget(investigate_btn)
        
        # Mark as safe button
        mark_safe_btn = QPushButton("✅ Mark as Safe")
        mark_safe_btn.clicked.connect(self._on_mark_safe)
        mark_safe_btn.setEnabled(False)
        self.mark_safe_checkbox.toggled.connect(mark_safe_btn.setEnabled)
        button_layout.addWidget(mark_safe_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _get_severity_icon(self) -> QPixmap:
        """Get icon based on severity level."""
        # Create a simple colored circle icon based on severity
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # In a real implementation, you'd use proper icons
        # For now, we'll use the text-based icons from the analyzer
        icon_text = {
            SeverityLevel.LOW: "ℹ️",
            SeverityLevel.MEDIUM: "⚠️",
            SeverityLevel.HIGH: "🚨",
            SeverityLevel.CRITICAL: "🔴"
        }.get(self.explanation.severity, "❓")
        
        # For simplicity, return empty pixmap (icon text will be in badge)
        return pixmap
    
    def _create_severity_badge(self) -> QLabel:
        """Create severity level badge."""
        badge = QLabel(self.explanation.severity.value.upper())
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setMinimumSize(80, 30)
        
        # Color based on severity
        colors = {
            SeverityLevel.LOW: "#28a745",      # Green
            SeverityLevel.MEDIUM: "#ffc107",   # Yellow  
            SeverityLevel.HIGH: "#fd7e14",     # Orange
            SeverityLevel.CRITICAL: "#dc3545"  # Red
        }
        
        color = colors.get(self.explanation.severity, "#6c757d")
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
        return badge
    
    def _apply_styles(self):
        """Apply custom styles to the dialog."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
    
    def get_theme_color(self, color_type):
        """Get theme-appropriate color from parent or fallback."""
        if self.parent_window and hasattr(self.parent_window, 'get_theme_color'):
            return self.parent_window.get_theme_color(color_type)
        
        # Fallback colors for dark theme
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
        return fallback_colors.get(color_type, "#FFCDAA")
    
    def _apply_theme(self, theme_name):
        """Apply theme styling to this dialog."""
        bg = self.get_theme_color("background")
        secondary_bg = self.get_theme_color("secondary_bg")
        tertiary_bg = self.get_theme_color("tertiary_bg")
        text = self.get_theme_color("primary_text")
        secondary_text = self.get_theme_color("secondary_text")
        success = self.get_theme_color("success")
        error = self.get_theme_color("error")
        border = self.get_theme_color("border")
        hover_bg = self.get_theme_color("hover_bg")
        pressed_bg = self.get_theme_color("pressed_bg")
        accent = self.get_theme_color("accent")
        
        style = f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QGroupBox {{
                color: {text};
                border: 2px solid {border};
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 0.8em;
                background-color: {secondary_bg};
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 10px 0 10px;
                color: {accent};
                font-weight: 700;
                font-size: 14px;
            }}
            QLabel {{
                color: {text};
                font-weight: 500;
            }}
            QTextEdit {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 6px;
                color: {text};
                font-family: monospace;
                font-size: 10px;
                selection-background-color: {accent};
                selection-color: {bg};
            }}
            QCheckBox {{
                color: {text};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {border};
                background-color: {bg};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {success};
                background-color: {success};
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 5px;
                padding: 8px 16px;
                color: {text};
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent};
                color: {text};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
                border-color: {accent};
            }}
            QPushButton#primaryButton {{
                background-color: {success};
                border: 2px solid {success};
                color: {bg};
                font-weight: 700;
            }}
            QPushButton#primaryButton:hover {{
                background-color: {hover_bg};
                border-color: {success};
            }}
            QPushButton#dangerButton {{
                background-color: {error};
                border: 2px solid {error};
                color: {bg};
                font-weight: 700;
            }}
            QPushButton#dangerButton:hover {{
                background-color: {hover_bg};
                border-color: {error};
            }}
            /* Category label styling */
            QLabel[objectName="categoryLabel"] {{
                color: {secondary_text};
                font-size: 10px;
            }}
            /* Technical details styling */
            QLabel[objectName="techLabel"] {{
                color: {secondary_text};
                font-style: italic;
            }}
            /* Common warning styling */
            QLabel[objectName="commonLabel"] {{
                color: {success};
                font-weight: bold;
            }}
        """
        self.setStyleSheet(style)
    
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
            f"1. Search online for: \"{self.warning_text[:50]}...\"\n"
            f"2. Check RKHunter documentation\n"
            f"3. Review recent system changes\n"
            f"4. Consult security forums if concerned"
        )
    
    def _on_mark_safe(self):
        """Handle mark as safe button click."""
        if not self.mark_safe_checkbox.isChecked():
            return
            
        reply = self._show_themed_message_box(
            "question",
            "Mark Warning as Safe",
            f"Are you sure you want to mark this warning as safe?\n\n"
            f"This will:\n"
            f"• Hide this warning in future scans\n"
            f"• Add it to the safe warnings list\n"
            f"• Reduce the warning count in reports\n\n"
            f"Only do this if you're confident the warning is harmless.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.mark_as_safe.emit(self.warning_text)
            self.accept()
