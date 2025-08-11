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
                    "background": "#1e1e1e",
                    "secondary_bg": "#2d2d2d", 
                    "tertiary_bg": "#404040",
                    "quaternary_bg": "#4f4f4f",
                    "card_bg": "#252525",
                    "elevated_bg": "#323232",
                    "primary_text": "#FFCDAA",
                    "secondary_text": "#E0E0E0",
                    "muted_text": "#B0B0B0",
                    "success": "#4CAF50",
                    "success_bright": "#66BB6A",
                    "error": "#F44336",
                    "error_bright": "#EF5350",
                    "warning": "#FF9800",
                    "warning_bright": "#FFA726",
                    "info": "#2196F3",
                    "info_bright": "#42A5F5",
                    "accent": "#FF5722",
                    "accent_bright": "#FF7043",
                    "accent_dark": "#D84315",
                    "border": "#555555",
                    "border_light": "#777777",
                    "border_dark": "#333333",
                    "hover_bg": "#404040",
                    "hover_accent": "#FF7043",
                    "pressed_bg": "#2a2a2a",
                    "selection_bg": "#FF5722",
                    "selection_text": "#FFFFFF",
                    "disabled_bg": "#1a1a1a",
                    "disabled_text": "#666666",
                    "shadow": "#00000080",
                    "glow": "#FF572240",
                    "gradient_start": "#2d2d2d",
                    "gradient_end": "#1e1e1e",
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
                    "background": "#fafafa",
                    "secondary_bg": "#ffffff",
                    "tertiary_bg": "#f5f5f5", 
                    "quaternary_bg": "#eeeeee",
                    "card_bg": "#ffffff",
                    "elevated_bg": "#ffffff",
                    "primary_text": "#212121",
                    "secondary_text": "#424242",
                    "muted_text": "#757575",
                    "success": "#4CAF50",
                    "success_bright": "#66BB6A",
                    "error": "#F44336",
                    "error_bright": "#EF5350",
                    "warning": "#FF9800",
                    "warning_bright": "#FFA726",
                    "info": "#2196F3",
                    "info_bright": "#42A5F5",
                    "accent": "#FF5722",
                    "accent_bright": "#FF7043",
                    "accent_dark": "#D84315",
                    "border": "#e0e0e0",
                    "border_light": "#f5f5f5",
                    "border_dark": "#bdbdbd",
                    "hover_bg": "#f0f0f0",
                    "hover_accent": "#FF7043",
                    "pressed_bg": "#e8e8e8",
                    "selection_bg": "#FF5722",
                    "selection_text": "#ffffff",
                    "disabled_bg": "#f9f9f9",
                    "disabled_text": "#bdbdbd",
                    "shadow": "#00000020",
                    "glow": "#FF572230",
                    "gradient_start": "#ffffff",
                    "gradient_end": "#f5f5f5",
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
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('gradient_start')}, 
                                        stop: 1 {c('gradient_end')});
            color: {c('primary_text')};
        }}
        
        /* === DIALOGS === */
        QDialog {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('elevated_bg')}, 
                                        stop: 1 {c('secondary_bg')});
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 12px;
        }}
        
        /* === MESSAGE BOXES === */
        QMessageBox {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('elevated_bg')}, 
                                        stop: 1 {c('card_bg')});
            color: {c('primary_text')};
            border: 2px solid {c('border_light')};
            border-radius: 10px;
            font-size: {f('base_size')}px;
            font-weight: 500;
        }}
        QMessageBox QLabel {{
            color: {c('primary_text')};
            font-weight: 600;
            padding: 15px;
            line-height: 1.5;
            background: transparent;
        }}
        QMessageBox QPushButton {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('tertiary_bg')}, 
                                        stop: 1 {c('secondary_bg')});
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px 20px;
            color: {c('primary_text')};
            font-weight: 600;
            min-width: 90px;
            min-height: 32px;
        }}
        QMessageBox QPushButton:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('hover_accent')}, 
                                        stop: 1 {c('accent')});
            border-color: {c('accent_bright')};
            color: white;
        }}
        QMessageBox QPushButton:pressed {{
            background: {c('pressed_bg')};
            border-color: {c('accent_dark')};
        }}
        QMessageBox QPushButton:default {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('success_bright')}, 
                                        stop: 1 {c('success')});
            border-color: {c('success')};
            color: white;
            font-weight: 700;
        }}
        
        /* === ENHANCED BUTTONS === */
        QPushButton {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('tertiary_bg')}, 
                                        stop: 1 {c('secondary_bg')});
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px 18px;
            color: {c('primary_text')};
            font-weight: 600;
            min-height: 28px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('hover_accent')}, 
                                        stop: 1 {c('accent')});
            border-color: {c('accent_bright')};
            color: white;
            transform: translateY(-1px);
        }}
        QPushButton:pressed {{
            background: {c('pressed_bg')};
            border-color: {c('accent_dark')};
            transform: translateY(1px);
        }}
        QPushButton:disabled {{
            background: {c('disabled_bg')};
            color: {c('disabled_text')};
            border-color: {c('disabled_text')};
        }}
        QPushButton:default {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('accent')});
            border-color: {c('accent')};
            color: white;
            font-weight: 700;
        }}
        QPushButton:default:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent')}, 
                                        stop: 1 {c('accent_dark')});
        }}
        
        /* === ENHANCED LABELS === */
        QLabel {{
            color: {c('primary_text')};
            background-color: transparent;
        }}
        QLabel[class="header"] {{
            font-size: {f('header_size')}px;
            font-weight: 700;
            color: {c('accent')};
            text-shadow: 1px 1px 2px {c('shadow')};
        }}
        QLabel[class="secondary"] {{
            color: {c('secondary_text')};
            font-size: {f('small_size')}px;
        }}
        QLabel[class="muted"] {{
            color: {c('muted_text')};
        }}
        QLabel[class="card-title"] {{
            font-size: {f('base_size') + 2}px;
            font-weight: 700;
            color: {c('accent')};
            padding: 8px;
        }}
        
        /* === ENHANCED INPUT FIELDS === */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('card_bg')}, 
                                        stop: 1 {c('tertiary_bg')});
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px;
            color: {c('primary_text')};
            selection-background-color: {c('selection_bg')};
            selection-color: {c('selection_text')};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {c('accent')};
            background: {c('card_bg')};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {c('disabled_bg')};
            color: {c('disabled_text')};
            border-color: {c('disabled_text')};
        }}
        
        /* === ENHANCED GROUP BOXES === */
        QGroupBox {{
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 12px;
            margin-top: 15px;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('card_bg')}, 
                                        stop: 1 {c('secondary_bg')});
            font-weight: 600;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 18px;
            padding: 4px 12px;
            color: {c('accent')};
            font-weight: 700;
            font-size: {f('base_size') + 2}px;
            background: {c('card_bg')};
            border: 1px solid {c('border')};
            border-radius: 6px;
        }}
        
        /* === ENHANCED COMBO BOXES === */
        QComboBox {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('card_bg')}, 
                                        stop: 1 {c('tertiary_bg')});
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 8px 15px;
            color: {c('primary_text')};
            min-width: 130px;
        }}
        QComboBox:hover {{
            border-color: {c('accent')};
            background: {c('card_bg')};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 25px;
        }}
        QComboBox::down-arrow {{
            border: 3px solid {c('accent')};
            width: 8px;
            height: 8px;
            border-top: none;
            border-right: none;
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 6px;
            selection-background-color: {c('accent')};
            selection-color: white;
        }}
        
        /* === ENHANCED CHECK BOXES === */
        QCheckBox {{
            color: {c('primary_text')};
            spacing: 10px;
            font-weight: 500;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
        }}
        QCheckBox::indicator:unchecked {{
            border: 2px solid {c('border')};
            background: {c('card_bg')};
            border-radius: 4px;
        }}
        QCheckBox::indicator:checked {{
            border: 2px solid {c('success')};
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('success_bright')}, 
                                        stop: 1 {c('success')});
            border-radius: 4px;
        }}
        QCheckBox::indicator:hover {{
            border-color: {c('accent')};
        }}
        
        /* === ENHANCED RADIO BUTTONS === */
        QRadioButton {{
            color: {c('primary_text')};
            spacing: 10px;
            font-weight: 500;
        }}
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
        }}
        QRadioButton::indicator:unchecked {{
            border: 2px solid {c('border')};
            background: {c('card_bg')};
            border-radius: 9px;
        }}
        QRadioButton::indicator:checked {{
            border: 2px solid {c('accent')};
            background: qradialGradient(cx: 0.5, cy: 0.5, radius: 1,
                                        fx: 0.5, fy: 0.5,
                                        stop: 0 {c('accent')}, 
                                        stop: 0.7 {c('accent')}, 
                                        stop: 1 {c('card_bg')});
            border-radius: 9px;
        }}
        
        /* === ENHANCED PROGRESS BARS === */
        QProgressBar {{
            border: 2px solid {c('border')};
            border-radius: 8px;
            background: {c('secondary_bg')};
            text-align: center;
            color: {c('primary_text')};
            font-weight: 600;
            font-size: {f('base_size') + 1}px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                        stop: 0 {c('success')}, 
                                        stop: 1 {c('success_bright')});
            border-radius: 6px;
        }}
        
        /* === ENHANCED LIST WIDGETS === */
        QListWidget {{
            background: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 10px;
            color: {c('primary_text')};
            selection-background-color: {c('accent')};
            selection-color: white;
            alternate-background-color: {c('secondary_bg')};
        }}
        QListWidget::item {{
            padding: 12px;
            border-bottom: 1px solid {c('border')};
            border-radius: 4px;
        }}
        QListWidget::item:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('hover_bg')}, 
                                        stop: 1 {c('tertiary_bg')});
        }}
        QListWidget::item:selected {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('accent')});
            color: white;
            font-weight: 600;
        }}
        
        /* === ENHANCED TREE WIDGETS === */
        QTreeWidget {{
            background: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 10px;
            color: {c('primary_text')};
            selection-background-color: {c('accent')};
            selection-color: white;
            alternate-background-color: {c('secondary_bg')};
        }}
        QTreeWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {c('border_light')};
        }}
        QTreeWidget::item:hover {{
            background: {c('hover_bg')};
        }}
        QTreeWidget::item:selected {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('accent')});
            color: white;
        }}
        
        /* === ENHANCED SCROLL BARS === */
        QScrollBar:vertical {{
            background: {c('secondary_bg')};
            width: 16px;
            border-radius: 8px;
            border: 1px solid {c('border')};
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                        stop: 0 {c('accent')}, 
                                        stop: 1 {c('accent_bright')});
            border-radius: 7px;
            min-height: 25px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('hover_accent')});
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        QScrollBar:horizontal {{
            background: {c('secondary_bg')};
            height: 16px;
            border-radius: 8px;
            border: 1px solid {c('border')};
        }}
        QScrollBar::handle:horizontal {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent')}, 
                                        stop: 1 {c('accent_bright')});
            border-radius: 7px;
            min-width: 25px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('hover_accent')});
        }}
        
        /* === ENHANCED SCROLL AREAS === */
        QScrollArea {{
            border: 2px solid {c('border')};
            border-radius: 10px;
            background: {c('card_bg')};
        }}
        
        /* === ENHANCED TAB WIDGETS === */
        QTabWidget::pane {{
            border: 2px solid {c('border')};
            border-radius: 10px;
            background: {c('card_bg')};
            top: -2px;
        }}
        QTabBar::tab {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('tertiary_bg')}, 
                                        stop: 1 {c('secondary_bg')});
            border: 2px solid {c('border')};
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            color: {c('primary_text')};
            margin-right: 3px;
            font-weight: 600;
        }}
        QTabBar::tab:selected {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('accent')});
            color: white;
            border-color: {c('accent')};
        }}
        QTabBar::tab:hover {{
            background: {c('hover_bg')};
        }}
        
        /* === ENHANCED SLIDERS === */
        QSlider::groove:horizontal {{
            border: 2px solid {c('border')};
            height: 8px;
            background: {c('tertiary_bg')};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('accent')});
            border: 2px solid {c('accent_dark')};
            width: 20px;
            margin: -8px 0;
            border-radius: 10px;
        }}
        QSlider::handle:horizontal:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('hover_accent')}, 
                                        stop: 1 {c('accent_bright')});
            border-color: {c('accent')};
        }}
        
        /* === ENHANCED SPIN BOXES === */
        QSpinBox, QDoubleSpinBox {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('card_bg')}, 
                                        stop: 1 {c('tertiary_bg')});
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 8px;
            color: {c('primary_text')};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {c('accent')};
            background: {c('card_bg')};
        }}
        
        /* === ENHANCED MENU BAR === */
        QMenuBar {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('secondary_bg')}, 
                                        stop: 1 {c('background')});
            color: {c('primary_text')};
            border-bottom: 2px solid {c('border')};
            font-weight: 600;
        }}
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 15px;
            border-radius: 6px;
        }}
        QMenuBar::item:selected {{
            background: {c('hover_bg')};
            color: {c('accent')};
        }}
        
        /* === ENHANCED MENUS === */
        QMenu {{
            background: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            color: {c('primary_text')};
        }}
        QMenu::item {{
            padding: 10px 25px;
            border-radius: 4px;
            margin: 2px;
        }}
        QMenu::item:selected {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('accent_bright')}, 
                                        stop: 1 {c('accent')});
            color: white;
        }}
        QMenu::separator {{
            height: 2px;
            background: {c('border')};
            margin: 6px 0;
        }}
        
        /* === ENHANCED STATUS BAR === */
        QStatusBar {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('secondary_bg')}, 
                                        stop: 1 {c('background')});
            color: {c('primary_text')};
            border-top: 2px solid {c('border')};
            font-weight: 500;
        }}
        
        /* === ENHANCED TOOL BARS === */
        QToolBar {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('secondary_bg')}, 
                                        stop: 1 {c('background')});
            border: 2px solid {c('border')};
            color: {c('primary_text')};
            spacing: 4px;
            border-radius: 6px;
        }}
        QToolButton {{
            background-color: transparent;
            border: 2px solid transparent;
            border-radius: 6px;
            padding: 8px;
            color: {c('primary_text')};
        }}
        QToolButton:hover {{
            background: {c('hover_bg')};
            border-color: {c('accent')};
        }}
        QToolButton:pressed {{
            background: {c('pressed_bg')};
        }}
        
        /* === ENHANCED SPLITTERS === */
        QSplitter::handle {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                        stop: 0 {c('border')}, 
                                        stop: 0.5 {c('accent')}, 
                                        stop: 1 {c('border')});
        }}
        QSplitter::handle:horizontal {{
            width: 4px;
        }}
        QSplitter::handle:vertical {{
            height: 4px;
        }}
        QSplitter::handle:hover {{
            background: {c('accent')};
        }}
        
        /* === CUSTOM CARD STYLING === */
        QFrame[class="card"] {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('card_bg')}, 
                                        stop: 1 {c('secondary_bg')});
            border: 2px solid {c('border')};
            border-radius: 12px;
            padding: 15px;
        }}
        QFrame[class="elevated-card"] {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('elevated_bg')}, 
                                        stop: 1 {c('card_bg')});
            border: 2px solid {c('border_light')};
            border-radius: 12px;
            padding: 15px;
        }}
        
        /* === STATUS CARDS (Dashboard) === */
        QFrame#statusCard {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('elevated_bg')}, 
                                        stop: 1 {c('card_bg')});
            border: 2px solid {c('border')};
            border-radius: 15px;
            padding: 20px;
            min-height: 120px;
            min-width: 200px;
        }}
        QFrame#statusCard:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('hover_bg')}, 
                                        stop: 1 {c('elevated_bg')});
            border-color: {c('accent')};
            transform: translateY(-2px);
        }}
        
        /* Status Card Components */
        QLabel#cardTitle {{
            color: {c('primary_text')};
            font-size: {f('base_size') + 2}px;
            font-weight: 700;
            padding: 5px 0;
        }}
        QLabel#cardValue {{
            font-size: {f('header_size') + 6}px;
            font-weight: 800;
            padding: 8px 0;
            text-shadow: 1px 1px 2px {c('shadow')};
        }}
        QLabel#cardDescription {{
            color: {c('secondary_text')};
            font-size: {f('small_size') + 1}px;
            font-weight: 500;
            line-height: 1.4;
            padding: 5px 0;
        }}
        
        /* === ACTIVITY REPORT STYLING === */
        QFrame#activityReport {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 {c('card_bg')}, 
                                        stop: 1 {c('secondary_bg')});
            border: 2px solid {c('border')};
            border-radius: 12px;
            padding: 20px;
        }}
        
        /* === TAB STYLING ENHANCEMENTS === */
        QTabWidget {{
            background: transparent;
        }}
        QTabWidget::tab-bar {{
            alignment: left;
        }}
        
        /* === ENHANCED STATUS COLORS === */
        .status-active {{
            color: {c('success_bright')};
        }}
        .status-inactive {{
            color: {c('error_bright')};
        }}
        .status-warning {{
            color: {c('warning_bright')};
        }}
        .status-info {{
            color: {c('info_bright')};
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

def toggle_theme():
    """Toggle between light and dark themes (for testing)."""
    current = get_theme_manager().get_current_theme()
    new_theme = "light" if current == "dark" else "dark"
    set_app_theme(new_theme)
    return new_theme
