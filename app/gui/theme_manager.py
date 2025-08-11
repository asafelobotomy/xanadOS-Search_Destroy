#!/usr/bin/env python3
"""
Theme Manager - Centralized theming system for S&D Search & Destroy
Provides automatic theming for all GUI components without manual application.
"""

from typing import Dict, Optional, Any
from PyQt6.QtWidgets import QApplication, QWidget, QDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor


class ThemeManager(QObject):
    """
    Centralized theme management system that automatically applies themes
    to all GUI components through Qt's style system and custom stylesheets.
    """
    
    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str)  # theme_name
    
    def __init__(self):
        super().__init__()
        self._current_theme = "dark"
        self._theme_definitions = {
            "dark": {
                "name": "Dark",
                "colors": {
                    "background": "#1a1a1a",
                    "secondary_bg": "#2a2a2a", 
                    "tertiary_bg": "#3a3a3a",
                    "quaternary_bg": "#4a4a4a",
                    "primary_text": "#FFCDAA",
                    "secondary_text": "#CCCCCC",
                    "muted_text": "#999999",
                    "success": "#9CB898",
                    "error": "#F14666",
                    "warning": "#EE8980",
                    "info": "#7BB3F0",
                    "accent": "#F14666",
                    "border": "#EE8980",
                    "hover_bg": "#4a4a4a",
                    "pressed_bg": "#2a2a2a",
                    "selection_bg": "#F14666",
                    "selection_text": "#FFFFFF",
                    "disabled_bg": "#1f1f1f",
                    "disabled_text": "#666666",
                },
                "fonts": {
                    "base_size": 11,
                    "header_size": 16,
                    "small_size": 9,
                    "monospace_family": "Consolas, 'Courier New', monospace",
                    "ui_family": "Segoe UI, Tahoma, sans-serif",
                }
            },
            "light": {
                "name": "Light",
                "colors": {
                    "background": "#ffffff",
                    "secondary_bg": "#f8f9fa",
                    "tertiary_bg": "#eceef1", 
                    "quaternary_bg": "#e1e4e8",
                    "primary_text": "#1f1f23",
                    "secondary_text": "#444444",
                    "muted_text": "#666666",
                    "success": "#198754",
                    "error": "#dc3545",
                    "warning": "#fd7e14",
                    "info": "#0dcaf0",
                    "accent": "#0078d4",
                    "border": "#d0d5da",
                    "hover_bg": "#e6f2fb",
                    "pressed_bg": "#d0e8f7",
                    "selection_bg": "#0078d4",
                    "selection_text": "#ffffff",
                    "disabled_bg": "#f5f5f5",
                    "disabled_text": "#999999",
                },
                "fonts": {
                    "base_size": 11,
                    "header_size": 16,
                    "small_size": 9,
                    "monospace_family": "Consolas, 'Courier New', monospace",
                    "ui_family": "Segoe UI, Tahoma, sans-serif",
                }
            }
        }
        
        # Initialize application-wide stylesheet
        self._apply_global_theme()
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self._current_theme
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get available themes as {theme_id: display_name}."""
        return {
            theme_id: theme_data["name"] 
            for theme_id, theme_data in self._theme_definitions.items()
        }
    
    def get_color(self, color_key: str, theme: Optional[str] = None) -> str:
        """Get a color value from the current or specified theme."""
        theme_name = theme or self._current_theme
        theme_data = self._theme_definitions.get(theme_name, self._theme_definitions["dark"])
        return theme_data["colors"].get(color_key, "#FFFFFF")
    
    def get_font_property(self, font_key: str, theme: Optional[str] = None) -> Any:
        """Get a font property from the current or specified theme."""
        theme_name = theme or self._current_theme
        theme_data = self._theme_definitions.get(theme_name, self._theme_definitions["dark"])
        return theme_data["fonts"].get(font_key, 11)
    
    def set_theme(self, theme_name: str):
        """Change the current theme and apply it globally."""
        if theme_name not in self._theme_definitions:
            raise ValueError(f"Unknown theme: {theme_name}")
        
        self._current_theme = theme_name
        self._apply_global_theme()
        
        # Emit signal so existing widgets can update
        self.theme_changed.emit(theme_name)
    
    def _apply_global_theme(self):
        """Apply the current theme globally to the application."""
        app = QApplication.instance()
        if not app:
            return
        
        # Generate comprehensive stylesheet
        stylesheet = self._generate_global_stylesheet()
        app.setStyleSheet(stylesheet)
        
        # Set application palette for native Qt styling
        self._set_application_palette()
    
    def _generate_global_stylesheet(self) -> str:
        """Generate a comprehensive stylesheet for all Qt widgets."""
        c = self.get_color  # Shorthand
        f = self.get_font_property
        
        return f"""
        /* === GLOBAL APPLICATION STYLING === */
        QWidget {{
            background-color: {c('background')};
            color: {c('primary_text')};
            font-family: {f('ui_family')};
            font-size: {f('base_size')}px;
            selection-background-color: {c('selection_bg')};
            selection-color: {c('selection_text')};
        }}
        
        /* === MAIN WINDOW === */
        QMainWindow {{
            background-color: {c('background')};
            color: {c('primary_text')};
        }}
        
        /* === DIALOGS === */
        QDialog {{
            background-color: {c('background')};
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 8px;
        }}
        
        /* === MESSAGE BOXES === */
        QMessageBox {{
            background-color: {c('background')};
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            font-size: {f('base_size')}px;
            font-weight: 500;
        }}
        QMessageBox QLabel {{
            color: {c('primary_text')};
            font-weight: 600;
            padding: 10px;
            line-height: 1.4;
        }}
        QMessageBox QPushButton {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-radius: 5px;
            padding: 8px 16px;
            color: {c('primary_text')};
            font-weight: 600;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {c('hover_bg')};
            border-color: {c('accent')};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {c('pressed_bg')};
        }}
        QMessageBox QPushButton:default {{
            background-color: {c('success')};
            border-color: {c('success')};
            color: {c('background')};
            font-weight: 700;
        }}
        
        /* === BUTTONS === */
        QPushButton {{
            background-color: {c('secondary_bg')};
            border: 1px solid {c('border')};
            border-radius: 6px;
            padding: 8px 16px;
            color: {c('primary_text')};
            font-weight: 600;
            min-height: 24px;
        }}
        QPushButton:hover {{
            background-color: {c('hover_bg')};
            border-color: {c('accent')};
        }}
        QPushButton:pressed {{
            background-color: {c('pressed_bg')};
        }}
        QPushButton:disabled {{
            background-color: {c('disabled_bg')};
            color: {c('disabled_text')};
            border-color: {c('disabled_text')};
        }}
        QPushButton:default {{
            background-color: {c('accent')};
            border-color: {c('accent')};
            color: {c('background')};
        }}
        QPushButton:default:hover {{
            background-color: {c('hover_bg')};
        }}
        
        /* === LABELS === */
        QLabel {{
            color: {c('primary_text')};
            background-color: transparent;
        }}
        QLabel[class="header"] {{
            font-size: {f('header_size')}px;
            font-weight: 700;
            color: {c('accent')};
        }}
        QLabel[class="secondary"] {{
            color: {c('secondary_text')};
            font-size: {f('small_size')}px;
        }}
        QLabel[class="muted"] {{
            color: {c('muted_text')};
        }}
        
        /* === INPUT FIELDS === */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            padding: 8px;
            color: {c('primary_text')};
            selection-background-color: {c('selection_bg')};
            selection-color: {c('selection_text')};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {c('accent')};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {c('disabled_bg')};
            color: {c('disabled_text')};
            border-color: {c('disabled_text')};
        }}
        
        /* === GROUP BOXES === */
        QGroupBox {{
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            margin-top: 12px;
            background-color: {c('secondary_bg')};
            font-weight: 600;
            padding-top: 8px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 2px 8px;
            color: {c('accent')};
            font-weight: 700;
            font-size: {f('base_size') + 1}px;
        }}
        
        /* === COMBO BOXES === */
        QComboBox {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            padding: 6px 12px;
            color: {c('primary_text')};
            min-width: 120px;
        }}
        QComboBox:hover {{
            border-color: {c('accent')};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            border: 2px solid {c('accent')};
            width: 6px;
            height: 6px;
            border-top: none;
            border-right: none;
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c('secondary_bg')};
            border: 2px solid {c('border')};
            selection-background-color: {c('accent')};
            selection-color: {c('background')};
        }}
        
        /* === CHECK BOXES === */
        QCheckBox {{
            color: {c('primary_text')};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
        }}
        QCheckBox::indicator:unchecked {{
            border: 2px solid {c('border')};
            background-color: {c('background')};
            border-radius: 3px;
        }}
        QCheckBox::indicator:checked {{
            border: 2px solid {c('success')};
            background-color: {c('success')};
            border-radius: 3px;
        }}
        QCheckBox::indicator:hover {{
            border-color: {c('accent')};
        }}
        
        /* === RADIO BUTTONS === */
        QRadioButton {{
            color: {c('primary_text')};
            spacing: 8px;
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}
        QRadioButton::indicator:unchecked {{
            border: 2px solid {c('border')};
            background-color: {c('background')};
            border-radius: 8px;
        }}
        QRadioButton::indicator:checked {{
            border: 2px solid {c('accent')};
            background-color: {c('accent')};
            border-radius: 8px;
        }}
        
        /* === PROGRESS BARS === */
        QProgressBar {{
            border: 2px solid {c('border')};
            border-radius: 6px;
            background-color: {c('secondary_bg')};
            text-align: center;
            color: {c('primary_text')};
            font-weight: 600;
        }}
        QProgressBar::chunk {{
            background-color: {c('accent')};
            border-radius: 4px;
        }}
        
        /* === LIST WIDGETS === */
        QListWidget {{
            background-color: {c('secondary_bg')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            color: {c('primary_text')};
            selection-background-color: {c('accent')};
            selection-color: {c('background')};
        }}
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {c('border')};
        }}
        QListWidget::item:hover {{
            background-color: {c('hover_bg')};
        }}
        QListWidget::item:selected {{
            background-color: {c('accent')};
            color: {c('background')};
        }}
        
        /* === TREE WIDGETS === */
        QTreeWidget {{
            background-color: {c('secondary_bg')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            color: {c('primary_text')};
            selection-background-color: {c('accent')};
            selection-color: {c('background')};
        }}
        QTreeWidget::item {{
            padding: 4px;
            border-bottom: 1px solid {c('tertiary_bg')};
        }}
        QTreeWidget::item:hover {{
            background-color: {c('hover_bg')};
        }}
        QTreeWidget::item:selected {{
            background-color: {c('accent')};
            color: {c('background')};
        }}
        
        /* === SCROLL BARS === */
        QScrollBar:vertical {{
            background-color: {c('secondary_bg')};
            width: 14px;
            border-radius: 7px;
            border: 1px solid {c('border')};
        }}
        QScrollBar::handle:vertical {{
            background-color: {c('hover_bg')};
            border-radius: 6px;
            min-height: 20px;
            margin: 1px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c('accent')};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        QScrollBar:horizontal {{
            background-color: {c('secondary_bg')};
            height: 14px;
            border-radius: 7px;
            border: 1px solid {c('border')};
        }}
        QScrollBar::handle:horizontal {{
            background-color: {c('hover_bg')};
            border-radius: 6px;
            min-width: 20px;
            margin: 1px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c('accent')};
        }}
        
        /* === SCROLL AREAS === */
        QScrollArea {{
            border: 1px solid {c('border')};
            border-radius: 6px;
            background-color: {c('secondary_bg')};
        }}
        
        /* === TAB WIDGETS === */
        QTabWidget::pane {{
            border: 2px solid {c('border')};
            border-radius: 6px;
            background-color: {c('secondary_bg')};
        }}
        QTabBar::tab {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-bottom: none;
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            color: {c('primary_text')};
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {c('accent')};
            color: {c('background')};
        }}
        QTabBar::tab:hover {{
            background-color: {c('hover_bg')};
        }}
        
        /* === SLIDERS === */
        QSlider::groove:horizontal {{
            border: 1px solid {c('border')};
            height: 6px;
            background-color: {c('tertiary_bg')};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background-color: {c('accent')};
            border: 2px solid {c('border')};
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {c('hover_bg')};
            border-color: {c('accent')};
        }}
        
        /* === SPIN BOXES === */
        QSpinBox, QDoubleSpinBox {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            padding: 6px;
            color: {c('primary_text')};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {c('accent')};
        }}
        
        /* === MENU BAR === */
        QMenuBar {{
            background-color: {c('background')};
            color: {c('primary_text')};
            border-bottom: 1px solid {c('border')};
        }}
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
        }}
        QMenuBar::item:selected {{
            background-color: {c('hover_bg')};
        }}
        
        /* === MENUS === */
        QMenu {{
            background-color: {c('secondary_bg')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            color: {c('primary_text')};
        }}
        QMenu::item {{
            padding: 8px 20px;
        }}
        QMenu::item:selected {{
            background-color: {c('accent')};
            color: {c('background')};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {c('border')};
            margin: 4px 0;
        }}
        
        /* === STATUS BAR === */
        QStatusBar {{
            background-color: {c('secondary_bg')};
            color: {c('primary_text')};
            border-top: 1px solid {c('border')};
        }}
        
        /* === TOOL BARS === */
        QToolBar {{
            background-color: {c('secondary_bg')};
            border: 1px solid {c('border')};
            color: {c('primary_text')};
            spacing: 2px;
        }}
        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 6px;
            color: {c('primary_text')};
        }}
        QToolButton:hover {{
            background-color: {c('hover_bg')};
            border-color: {c('border')};
        }}
        QToolButton:pressed {{
            background-color: {c('pressed_bg')};
        }}
        
        /* === SPLITTERS === */
        QSplitter::handle {{
            background-color: {c('border')};
        }}
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        QSplitter::handle:hover {{
            background-color: {c('accent')};
        }}
        """
    
    def _set_application_palette(self):
        """Set the application palette for native Qt controls."""
        app = QApplication.instance()
        if not app:
            return
        
        palette = QPalette()
        
        # Convert hex colors to QColor
        def hex_to_qcolor(hex_color: str) -> QColor:
            return QColor(hex_color)
        
        # Base colors
        palette.setColor(QPalette.ColorRole.Window, hex_to_qcolor(self.get_color('background')))
        palette.setColor(QPalette.ColorRole.WindowText, hex_to_qcolor(self.get_color('primary_text')))
        palette.setColor(QPalette.ColorRole.Base, hex_to_qcolor(self.get_color('secondary_bg')))
        palette.setColor(QPalette.ColorRole.AlternateBase, hex_to_qcolor(self.get_color('tertiary_bg')))
        palette.setColor(QPalette.ColorRole.Text, hex_to_qcolor(self.get_color('primary_text')))
        palette.setColor(QPalette.ColorRole.Button, hex_to_qcolor(self.get_color('secondary_bg')))
        palette.setColor(QPalette.ColorRole.ButtonText, hex_to_qcolor(self.get_color('primary_text')))
        palette.setColor(QPalette.ColorRole.BrightText, hex_to_qcolor(self.get_color('accent')))
        palette.setColor(QPalette.ColorRole.Link, hex_to_qcolor(self.get_color('accent')))
        palette.setColor(QPalette.ColorRole.Highlight, hex_to_qcolor(self.get_color('selection_bg')))
        palette.setColor(QPalette.ColorRole.HighlightedText, hex_to_qcolor(self.get_color('selection_text')))
        
        # Disabled state
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, hex_to_qcolor(self.get_color('disabled_text')))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, hex_to_qcolor(self.get_color('disabled_text')))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, hex_to_qcolor(self.get_color('disabled_text')))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, hex_to_qcolor(self.get_color('disabled_bg')))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, hex_to_qcolor(self.get_color('disabled_bg')))
        
        app.setPalette(palette)
    
    def create_themed_message_box(self, parent: QWidget, msg_type: str, title: str, text: str, buttons=None) -> QMessageBox:
        """Create a message box that automatically uses the current theme."""
        msg_box = QMessageBox(parent)
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
        
        # Theme is automatically applied via global stylesheet
        return msg_box


# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager

def init_theming():
    """Initialize the theming system (call once at app startup)."""
    get_theme_manager()

def set_app_theme(theme_name: str):
    """Set the application theme."""
    get_theme_manager().set_theme(theme_name)

def get_theme_color(color_key: str) -> str:
    """Get a theme color (convenience function)."""
    return get_theme_manager().get_color(color_key)

def create_themed_message_box(parent: QWidget, msg_type: str, title: str, text: str, buttons=None) -> QMessageBox:
    """Create a themed message box (convenience function)."""
    return get_theme_manager().create_themed_message_box(parent, msg_type, title, text, buttons)
