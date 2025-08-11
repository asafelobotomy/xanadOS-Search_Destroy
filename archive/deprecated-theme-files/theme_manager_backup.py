#!/usr/bin/env python3
"""
Theme Manager - Centralized theming system for S&D Search & Destroy
Provides automatic theming for all GUI components without manual application.
"""

from typing import Dict, Optional, Any
from PyQt6.QtWidgets import QApplication, QWidget, QDialog, QMessageBox, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import QObject, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
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
                "name": "Dark (Professional)",
                "colors": {
                    # === REFINED PROFESSIONAL THEME (matching Application Updates dialog) ===
                    # Header colors - more muted and sophisticated
                    "header_gradient_start": "#e57373",   # Softer coral/salmon
                    "header_gradient_end": "#c62828",     # Deeper but less harsh red
                    "header_text": "#ffffff",             # Pure white header text
                    
                    # Core Application Colors - sophisticated grays like the dialog
                    "background": "#2b2b2b",              # Refined dark gray (not pure black)
                    "secondary_bg": "#363636",            # Medium dark gray for cards
                    "tertiary_bg": "#404040",             # Interactive elements background
                    "card_bg": "#333333",                 # Card backgrounds - more sophisticated
                    "elevated_bg": "#3d3d3d",             # Dialogs and modals - matches updates dialog
                    
                    # Refined accent palette - more professional
                    "strawberry_primary": "#c62828",       # Deeper, more professional red
                    "strawberry_coral": "#e57373",        # Softer coral
                    "strawberry_peach": "#ffab91",        # Warm peach for highlights
                    "strawberry_sage": "#81c784",         # Sage green for success
                    
                    # Text Colors - better contrast ratios
                    "primary_text": "#ffffff",            # Pure white for primary text
                    "secondary_text": "#e0e0e0",          # Light gray for secondary info
                    "muted_text": "#b0b0b0",              # Muted gray for subtle content
                    "accent_text": "#e57373",             # Softer coral for emphasis
                    "contrast_text": "#ffffff",           # High contrast white
                    
                    # Interactive States - more refined and professional
                    "accent": "#c62828",                  # Professional deep red for primary actions
                    "accent_hover": "#e57373",            # Softer coral on hover
                    "accent_pressed": "#b71c1c",          # Deeper red when pressed
                    "focus_ring": "#e57373",              # Softer coral focus indicators
                    "glow": "rgba(229, 115, 115, 0.3)",   # Softer glow effect
                    
                    # State Colors - semantic meanings (more muted)
                    "success": "#4caf50",                 # Green for success
                    "success_border": "#388e3c",          # Success borders
                    "warning": "#ff9800",                 # Orange for warnings  
                    "warning_border": "#f57c00",          # Warning borders
                    "error": "#f44336",                   # Red for errors
                    "error_border": "#d32f2f",            # Error borders
                    
                    # Border System - hierarchical border colors
                    "border": "#c62828",                  # Professional red borders (outer containers/main borders)
                    "border_light": "#e57373",            # Lighter coral borders for subtle divisions
                    "border_accent": "#c62828",           # Professional red accent borders (outer)
                    "border_inner": "#ff8a80",            # Warm coral for inner borders and subdivisions (less pink, more coral)
                    "border_muted": "#404040",            # Subtle borders that blend well (for very minimal divisions)
                    "separator": "#c62828",               # Section separators - elegant red accent
                    
                    # Interaction Feedback - refined and professional
                    "hover_bg": "#404040",                # Lighter hover backgrounds
                    "pressed_bg": "#2b2b2b",             # Pressed backgrounds
                    "selection_bg": "#c62828",            # Professional red selection
                    "selection_text": "#ffffff",          # Selection text
                    
                    # Visual Depth & Effects - softer and more professional
                    "shadow": "rgba(0, 0, 0, 0.5)",       # Softer shadows
                    "gradient_bg_start": "#333333",       # Sophisticated gradient start
                    "gradient_bg_end": "#2b2b2b",         # Refined gradient end
                },
                "fonts": {
                    "base_size": 14,                      # Increased from 11px for better readability
                    "header_size": 18,                    # Increased from 16px for better hierarchy
                    "small_size": 12,                     # Increased from 9px - much more readable
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
                    "base_size": 14,                      # Increased from 11px for better readability
                    "header_size": 18,                    # Increased from 16px for better hierarchy
                    "small_size": 12,                     # Increased from 9px - much more readable
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
    
    def _detect_system_theme(self) -> str:
        """Detect the system theme preference."""
        try:
            app = QApplication.instance()
            if app:
                # Check if the system is using dark mode
                palette = app.palette()
                window_color = palette.color(QPalette.ColorRole.Window)
                # If the window background is dark, assume dark theme
                return "dark" if window_color.lightness() < 128 else "light"
        except Exception:
            pass
        # Default to dark theme if detection fails
        return "dark"
    
    def _process_qt_stylesheet(self, css: str) -> str:
        """
        Process CSS to remove unsupported properties and add Qt-compatible alternatives.
        """
        import re
        
        # Remove unsupported CSS properties that cause warnings
        unsupported_patterns = [
            r'^\s*transition[^;]*;.*$',      # Remove transition properties
            r'^\s*transform[^;]*;.*$',       # Remove transform properties  
            r'^\s*box-shadow[^;]*;.*$',      # Remove box-shadow properties
            r'^\s*text-shadow[^;]*;.*$',     # Remove text-shadow properties
        ]
        
        processed_css = css
        for pattern in unsupported_patterns:
            processed_css = re.sub(pattern, '', processed_css, flags=re.MULTILINE)
        
        # Add Qt-compatible alternatives for some effects
        
        # Replace hover effects that used transform with margin adjustments
        processed_css = re.sub(
            r'([^}]*):hover\s*\{([^}]*)\}',
            lambda m: self._enhance_hover_state(m.group(0)),
            processed_css
        )
        
        # Clean up extra whitespace and empty lines
        processed_css = re.sub(r'\n\s*\n+', '\n\n', processed_css)
        processed_css = re.sub(r'^\s+', '', processed_css, flags=re.MULTILINE)
        
        return processed_css
    
    def _enhance_hover_state(self, hover_rule: str) -> str:
        """
        Enhance hover states with Qt-compatible effects instead of transforms.
        """
        # For buttons that had translateY effects, we can use margin adjustments
        if 'QPushButton' in hover_rule:
            # Add subtle margin effect for button press simulation
            if ':hover' in hover_rule and 'margin' not in hover_rule:
                hover_rule = hover_rule.replace('{', '{\n            margin: 1px;')
        
        return hover_rule
    
    def apply_qt_effects(self, widget: QWidget, effect_type: str = "button"):
        """
        Apply Qt-native effects to widgets to replace CSS effects that don't work.
        """
        if effect_type == "button" and isinstance(widget, QPushButton):
            self._setup_button_effects(widget)
        elif effect_type == "shadow":
            self._setup_shadow_effect(widget)
    
    def _setup_button_effects(self, button: QPushButton):
        """Setup hover and press animations for buttons."""
        # Store original geometry for animations
        if not hasattr(button, '_original_geometry'):
            button._original_geometry = button.geometry()
        
        # Create animations
        button._hover_animation = QPropertyAnimation(button, b"geometry")
        button._hover_animation.setDuration(150)
        button._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Connect hover events
        original_enter_event = button.enterEvent
        original_leave_event = button.leaveEvent
        original_press_event = button.mousePressEvent
        original_release_event = button.mouseReleaseEvent
        
        def enhanced_enter_event(event):
            """Enhanced mouse enter with animation."""
            original_enter_event(event)
            if hasattr(button, '_hover_animation'):
                current_geo = button.geometry()
                new_geo = QRect(current_geo.x(), current_geo.y() - 1, 
                               current_geo.width(), current_geo.height())
                button._hover_animation.setStartValue(current_geo)
                button._hover_animation.setEndValue(new_geo)
                button._hover_animation.start()
        
        def enhanced_leave_event(event):
            """Enhanced mouse leave with animation."""
            original_leave_event(event)
            if hasattr(button, '_hover_animation'):
                current_geo = button.geometry()
                new_geo = QRect(current_geo.x(), current_geo.y() + 1,
                               current_geo.width(), current_geo.height())
                button._hover_animation.setStartValue(current_geo)
                button._hover_animation.setEndValue(new_geo)
                button._hover_animation.start()
        
        def enhanced_press_event(event):
            """Enhanced mouse press with animation."""
            original_press_event(event)
            if hasattr(button, '_hover_animation'):
                current_geo = button.geometry()
                new_geo = QRect(current_geo.x(), current_geo.y() + 1,
                               current_geo.width(), current_geo.height())
                button._hover_animation.setStartValue(current_geo)
                button._hover_animation.setEndValue(new_geo)
                button._hover_animation.start()
        
        def enhanced_release_event(event):
            """Enhanced mouse release with animation."""
            original_release_event(event)
            if hasattr(button, '_hover_animation'):
                current_geo = button.geometry()
                new_geo = QRect(current_geo.x(), current_geo.y() - 1,
                               current_geo.width(), current_geo.height())
                button._hover_animation.setStartValue(current_geo)
                button._hover_animation.setEndValue(new_geo)
                button._hover_animation.start()
        
        button.enterEvent = enhanced_enter_event
        button.leaveEvent = enhanced_leave_event
        button.mousePressEvent = enhanced_press_event
        button.mouseReleaseEvent = enhanced_release_event
    
    def _setup_shadow_effect(self, widget: QWidget):
        """Setup drop shadow effect as alternative to CSS box-shadow."""
        shadow = QGraphicsDropShadowEffect()
        
        # Get current theme colors
        theme = self._theme_definitions.get(self._current_theme, {})
        colors = theme.get("colors", {})
        
        # Configure shadow based on theme
        shadow_color = QColor(colors.get("shadow", "#000000"))
        shadow_color.setAlpha(100)  # Semi-transparent
        
        shadow.setBlurRadius(8)
        shadow.setColor(shadow_color)
        shadow.setOffset(2, 2)
        
        widget.setGraphicsEffect(shadow)
    
    def setup_widget_effects(self, widget: QWidget):
        """
        Automatically setup Qt effects for a widget based on its type.
        Call this method when creating new widgets to get enhanced effects.
        """
        if isinstance(widget, QPushButton):
            self.apply_qt_effects(widget, "button")
        
        # Apply shadow effects to certain widget types
        widget_types_with_shadow = [QDialog, QMessageBox]
        if any(isinstance(widget, wtype) for wtype in widget_types_with_shadow):
            self.apply_qt_effects(widget, "shadow")
    
    def set_theme(self, theme_name: str):
        """Change the current theme and apply it globally."""
        # Handle auto theme by detecting system preference
        if theme_name == "auto":
            actual_theme = self._detect_system_theme()
        else:
            if theme_name not in self._theme_definitions:
                raise ValueError(f"Unknown theme: {theme_name}")
            actual_theme = theme_name
        
        self._current_theme = actual_theme
        self._apply_global_theme()
        
        # Emit signal so existing widgets can update
        self.theme_changed.emit(actual_theme)
    
    def _apply_global_theme(self):
        """Apply the current theme globally to the application."""
        app = QApplication.instance()
        if not app:
            return
        
        # Generate comprehensive stylesheet
        stylesheet = self._generate_global_stylesheet()
        
        # Process the stylesheet to remove unsupported CSS properties
        processed_stylesheet = self._process_qt_stylesheet(stylesheet)
        
        app.setStyleSheet(processed_stylesheet)
        
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
        
        /* === MAIN WINDOW (Solid colors, no gradients) === */
        QMainWindow {{
            background-color: {c('background')};
            color: {c('primary_text')};
        }}
        
        /* === DIALOGS === */
        QDialog {{
            background-color: {c('elevated_bg')};
            color: {c('primary_text')};
            border: 2px solid {c('border_accent')};
            border-radius: 12px;
        }}
        
        /* === MESSAGE BOXES === */
        QMessageBox {{
            background-color: {c('elevated_bg')};
            color: {c('primary_text')};
            border: 2px solid {c('border_accent')};
            border-radius: 10px;
            font-size: {f('base_size') + 1}px;
            font-weight: 500;
        }}
        QMessageBox QLabel {{
            color: {c('primary_text')};
            font-weight: 600;
            padding: 15px;
            line-height: 1.5;
            background: transparent;
            font-size: {f('base_size') + 1}px;
        }}
        QMessageBox QPushButton {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px 20px;
            color: {c('primary_text')};
            font-weight: 600;
            min-width: 90px;
            min-height: 32px;
            font-size: {f('base_size')}px;
            transition: all 0.15s ease-in-out;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {c('accent_hover')};
            border-color: {c('accent_hover')};
            color: {c('contrast_text')};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {c('accent_pressed')};
            border-color: {c('accent')};
        }}
        QMessageBox QPushButton:default {{
            background-color: {c('success')};
            border-color: {c('success')};
            color: {c('contrast_text')};
            font-weight: 700;
        }}
        
        /* === ENHANCED BUTTONS === */
        QPushButton {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px 18px;
            color: {c('primary_text')};
            font-weight: 600;
            font-size: {f('base_size')}px;
            min-height: 28px;
            transition: all 0.12s ease-out;
        }}
        QPushButton:hover {{
            background-color: {c('accent_hover')};
            border-color: {c('accent_hover')};
            color: {c('contrast_text')};
            transform: translateY(-1px);
        }}
        QPushButton:pressed {{
            background-color: {c('accent_pressed')};
            border-color: {c('accent')};
            transform: translateY(1px);
        }}
        QPushButton:disabled {{
            background-color: {c('pressed_bg')};
            color: {c('muted_text')};
            border-color: {c('border_muted')};
        }}
        QPushButton:default {{
            background-color: {c('accent')};
            border-color: {c('accent')};
            color: {c('contrast_text')};
            font-weight: 700;
        }}
        QPushButton:default:hover {{
            background-color: {c('accent_hover')};
        }}
        
        /* === ENHANCED LABELS === */
        QLabel {{
            color: {c('primary_text')};
            background-color: transparent;
        }}
        QLabel[class="header"] {{
            font-size: {f('header_size')}px;
            font-weight: 700;
            color: {c('accent_text')};
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
            color: {c('accent_text')};
            padding: 8px;
        }}
        QLabel[class="success"] {{
            color: {c('success')};
            font-weight: 600;
        }}
        QLabel[class="warning"] {{
            color: {c('warning')};
            font-weight: 600;
        }}
        QLabel[class="error"] {{
            color: {c('error')};
            font-weight: 600;
        }}
        
        /* === ENHANCED INPUT FIELDS === */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px;
            color: {c('primary_text')};
            selection-background-color: {c('selection_bg')};
            selection-color: {c('selection_text')};
            transition: border-color 0.15s ease-in-out;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {c('focus_ring')};
            background: {c('card_bg')};
            box-shadow: 0 0 0 2px {c('glow')};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {c('pressed_bg')};
            color: {c('muted_text')};
            border-color: {c('border_muted')};
        }}
        
        /* === ENHANCED GROUP BOXES === */
        QGroupBox {{
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 12px;
            margin-top: 15px;
            background-color: {c('card_bg')};
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
            background-color: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 8px 15px;
            color: {c('primary_text')};
            font-size: {f('base_size')}px;
            min-width: 130px;
            transition: all 0.15s ease-in-out;
        }}
        QComboBox:hover {{
            border-color: {c('focus_ring')};
            background-color: {c('card_bg')};
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
            transition: all 0.15s ease-in-out;
        }}
        QCheckBox::indicator:checked {{
            border: 2px solid {c('success')};
            background-color: {c('success')};
            border-radius: 4px;
            transition: all 0.15s ease-in-out;
        }}
        QCheckBox::indicator:checked:hover {{
            border-color: {c('strawberry_sage')};
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
            background-color: {c('card_bg')};
            border-radius: 9px;
            transition: all 0.15s ease-in-out;
        }}
        QRadioButton::indicator:unchecked:hover {{
            border-color: {c('focus_ring')};
        }}
        QRadioButton::indicator:checked {{
            border: 2px solid {c('accent')};
            background-color: {c('accent')};
            border-radius: 9px;
            transition: all 0.15s ease-in-out;
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
            background-color: {c('accent')};
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
            border-bottom: 1px solid {c('border_inner')};
            border-radius: 4px;
            transition: background-color 0.15s ease-in-out;
        }}
        QListWidget::item:hover {{
            background-color: {c('hover_bg')};
        }}
        QListWidget::item:selected {{
            background-color: {c('accent')};
            color: {c('contrast_text')};
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
            border-bottom: 1px solid {c('border_inner')};
            transition: background-color 0.15s ease-in-out;
        }}
        QTreeWidget::item:hover {{
            background: {c('hover_bg')};
        }}
        QTreeWidget::item:selected {{
            background-color: {c('accent')};
            color: {c('contrast_text')};
        }}
        
        /* === ENHANCED SCROLL BARS === */
        QScrollBar:vertical {{
            background: {c('secondary_bg')};
            width: 16px;
            border-radius: 8px;
            border: 1px solid {c('border')};
        }}
        QScrollBar::handle:vertical {{
            background-color: {c('accent')};
            border-radius: 7px;
            min-height: 25px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {c('accent_hover')};
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
            background-color: {c('accent')};
            border-radius: 7px;
            min-width: 25px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {c('accent_hover')};
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
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border_inner')};
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            color: {c('primary_text')};
            margin-right: 3px;
            font-weight: 600;
            font-size: {f('base_size')}px;
            transition: all 0.12s ease-out;
        }}
        QTabBar::tab:selected {{
            background-color: {c('accent')};
            color: {c('contrast_text')};
            border-color: {c('accent')};
        }}
        QTabBar::tab:selected:hover {{
            background-color: {c('accent_hover')};
            color: {c('contrast_text')};
            border-color: {c('accent_hover')};
        }}
        QTabBar::tab:hover {{
            background-color: {c('hover_bg')};
            border-color: {c('focus_ring')};
        }}
        
        /* === ENHANCED SLIDERS === */
        QSlider::groove:horizontal {{
            border: 2px solid {c('border')};
            height: 8px;
            background: {c('tertiary_bg')};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background-color: {c('accent')};
            border: 2px solid {c('accent_pressed')};
            width: 20px;
            margin: -8px 0;
            border-radius: 10px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {c('accent_hover')};
            border-color: {c('accent')};
        }}
        
        /* === ENHANCED SPIN BOXES === */
        QSpinBox, QDoubleSpinBox {{
            background-color: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 8px;
            color: {c('primary_text')};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {c('focus_ring')};
            background-color: {c('card_bg')};
            box-shadow: 0 0 0 2px {c('glow')};
        }}
        
        /* === ENHANCED MENU BAR === */
        QMenuBar {{
            background-color: {c('secondary_bg')};
            color: {c('primary_text')};
            border-bottom: 2px solid {c('border_accent')};
            font-weight: 600;
        }}
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 15px;
            border-radius: 6px;
        }}
        QMenuBar::item:selected {{
            background-color: {c('hover_bg')};
            color: {c('accent_text')};
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
            background-color: {c('accent')};
            color: {c('contrast_text')};
        }}
        QMenu::separator {{
            height: 2px;
            background: {c('border')};
            margin: 6px 0;
        }}
        
        /* === ENHANCED STATUS BAR === */
        QStatusBar {{
            background-color: {c('secondary_bg')};
            color: {c('primary_text')};
            border-top: 2px solid {c('border_accent')};
            font-weight: 500;
        }}
        
        /* === ENHANCED TOOL BARS === */
        QToolBar {{
            background-color: {c('secondary_bg')};
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
            background-color: {c('hover_bg')};
            border-color: {c('focus_ring')};
        }}
        QToolButton:pressed {{
            background-color: {c('pressed_bg')};
        }}
        
        /* === ENHANCED SPLITTERS === */
        QSplitter::handle {{
            background-color: {c('accent')};
        }}
        QSplitter::handle:horizontal {{
            width: 4px;
        }}
        QSplitter::handle:vertical {{
            height: 4px;
        }}
        QSplitter::handle:hover {{
            background-color: {c('accent_hover')};
        }}
        
        /* === CUSTOM CARD STYLING === */
        QFrame[class="card"] {{
            background-color: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 12px;
            padding: 15px;
        }}
        QFrame[class="elevated-card"] {{
            background-color: {c('elevated_bg')};
            border: 2px solid {c('border_light')};
            border-radius: 12px;
            padding: 15px;
        }}
        
        /* === STATUS CARDS (Dashboard) === */
        QFrame#statusCard {{
            background-color: {c('elevated_bg')};
            border: 2px solid {c('border')};
            border-radius: 15px;
            padding: 20px;
            min-height: 120px;
            min-width: 200px;
        }}
        QFrame#statusCard:hover {{
            background-color: {c('hover_bg')};
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
            background-color: {c('card_bg')};
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

def setup_widget_effects(widget: QWidget):
    """Setup Qt effects for a widget (convenience function)."""
    get_theme_manager().setup_widget_effects(widget)

def apply_button_effects(button: QPushButton):
    """Apply enhanced effects to a button (convenience function)."""
    get_theme_manager().apply_qt_effects(button, "button")

def apply_shadow_effect(widget: QWidget):
    """Apply shadow effect to a widget (convenience function)."""
    get_theme_manager().apply_qt_effects(widget, "shadow")
