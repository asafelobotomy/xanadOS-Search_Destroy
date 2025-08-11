#!/usr/bin/env python3
"""
Optimized Theme Manager - High-performance theming system for S&D Search & Destroy
Eliminates redundant theme applications and caches expensive operations.
"""

import re
import time
from typing import Dict, Optional, Any, Tuple
from functools import lru_cache
from PyQt6.QtWidgets import QApplication, QWidget, QDialog, QMessageBox, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import QObject, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt6.QtGui import QPalette, QColor

class OptimizedThemeManager(QObject):
    """
    High-performance theme management system with caching and optimization.
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
                    # === REFINED PROFESSIONAL THEME (matching original design) ===
                    # Header colors - beautiful strawberry gradient
                    "header_gradient_start": "#e57373",   # Softer coral/salmon
                    "header_gradient_end": "#c62828",     # Deeper red
                    "header_text": "#ffffff",             # Pure white header text
                    
                    # Core colors cached for performance
                    "background": "#2b2b2b",              # Refined dark gray
                    "secondary_bg": "#363636",            # Medium dark gray for cards
                    "tertiary_bg": "#404040",             # Interactive elements
                    "card_bg": "#333333",                 # Card backgrounds
                    "elevated_bg": "#3d3d3d",             # Dialogs and modals
                    
                    # Enhanced accent palette - strawberry theme
                    "strawberry_primary": "#c62828",       # Deeper professional red
                    "strawberry_coral": "#e57373",        # Softer coral
                    "strawberry_peach": "#ffab91",        # Warm peach for highlights
                    "strawberry_sage": "#81c784",         # Sage green for success
                    
                    "primary_text": "#ffffff",
                    "secondary_text": "#e0e0e0",
                    "accent": "#c62828",
                    "accent_hover": "#d32f2f",
                    "accent_pressed": "#b71c1c",
                    "border": "#555555",
                    "success": "#81c784",
                    "success_bright": "#9CB898",
                    "warning": "#ffb74d",
                    "warning_bright": "#FFD54F",
                    "error": "#e57373",
                    "error_bright": "#EF5350",
                    "info_bright": "#42A5F5",
                    "disabled_text": "#888888",
                    "disabled_bg": "#1a1a1a",
                    "selection_bg": "#0d47a1",
                    "selection_text": "#ffffff",
                    "shadow": "#000000",
                    "glow": "#0d47a1"
                },
                "fonts": {
                    "ui_family": "Segoe UI, Arial, sans-serif",
                    "base_size": 12,
                    "small_size": 10,
                    "large_size": 14
                }
            },
            "light": {
                "name": "Light (Clean)",
                "colors": {
                    "background": "#ffffff",
                    "secondary_bg": "#f5f5f5",
                    "tertiary_bg": "#eeeeee",
                    "card_bg": "#fafafa",
                    "elevated_bg": "#ffffff",
                    "primary_text": "#212121",
                    "secondary_text": "#757575",
                    "accent": "#1976d2",
                    "accent_hover": "#1565c0",
                    "accent_pressed": "#0d47a1",
                    "border": "#e0e0e0",
                    "success": "#4caf50",
                    "warning": "#ff9800",
                    "error": "#f44336",
                    "disabled_text": "#bdbdbd",
                    "disabled_bg": "#f5f5f5",
                    "selection_bg": "#e3f2fd",
                    "selection_text": "#0d47a1",
                    "shadow": "#000000",
                    "glow": "#2196f3"
                },
                "fonts": {
                    "ui_family": "Segoe UI, Arial, sans-serif",
                    "base_size": 12,
                    "small_size": 10,
                    "large_size": 14
                }
            }
        }
        
        # Performance optimizations
        self._stylesheet_cache: Dict[str, str] = {}
        self._processed_css_cache: Dict[str, str] = {}
        self._palette_cache: Dict[str, QPalette] = {}
        self._last_theme_application = 0
        self._min_theme_interval = 0.1  # Minimum 100ms between theme applications
        
        # Debounce timer for theme applications
        self._theme_timer = QTimer()
        self._theme_timer.setSingleShot(True)
        self._theme_timer.timeout.connect(self._perform_theme_application)
        self._pending_theme = None
        
        # Initialize with base theme
        self._apply_global_theme()
    
    @lru_cache(maxsize=128)
    def get_color(self, color_key: str, theme_name: Optional[str] = None) -> str:
        """Get a color value from the current or specified theme. Cached for performance."""
        theme = self._theme_definitions.get(theme_name or self._current_theme, {})
        colors = theme.get("colors", {})
        return colors.get(color_key, "#ffffff")
    
    @lru_cache(maxsize=64)
    def get_font_property(self, font_key: str, theme_name: Optional[str] = None) -> Any:
        """Get a font property from the current or specified theme. Cached for performance."""
        theme = self._theme_definitions.get(theme_name or self._current_theme, {})
        fonts = theme.get("fonts", {})
        return fonts.get(font_key, 12)
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self._current_theme
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get available themes as {theme_id: display_name}."""
        return {
            theme_id: definition.get("name", theme_id.title())
            for theme_id, definition in self._theme_definitions.items()
        }
    
    def _detect_system_theme(self) -> str:
        """Detect the system theme preference."""
        try:
            app = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.ColorRole.Window)
                return "dark" if window_color.lightness() < 128 else "light"
        except Exception:
            pass
        return "dark"
    
    def set_theme(self, theme_name: str):
        """
        Change the current theme with debouncing to prevent performance issues.
        """
        # Handle auto theme by detecting system preference
        if theme_name == "auto":
            actual_theme = self._detect_system_theme()
        else:
            if theme_name not in self._theme_definitions:
                raise ValueError(f"Unknown theme: {theme_name}")
            actual_theme = theme_name
        
        # Skip if theme hasn't changed
        if actual_theme == self._current_theme:
            return
        
        # Debounce theme applications to prevent performance issues
        current_time = time.time()
        if (current_time - self._last_theme_application) < self._min_theme_interval:
            # Defer the theme application
            self._pending_theme = actual_theme
            self._theme_timer.start(100)  # 100ms delay
            return
        
        self._current_theme = actual_theme
        self._clear_caches()  # Clear caches when theme changes
        self._apply_global_theme()
        self._last_theme_application = current_time
        
        # Emit signal for any widgets that need manual updates
        self.theme_changed.emit(actual_theme)
    
    def _perform_theme_application(self):
        """Perform the deferred theme application."""
        if self._pending_theme:
            theme = self._pending_theme
            self._pending_theme = None
            self._current_theme = theme
            self._clear_caches()
            self._apply_global_theme()
            self._last_theme_application = time.time()
            self.theme_changed.emit(theme)
    
    def _clear_caches(self):
        """Clear all performance caches when theme changes."""
        self._stylesheet_cache.clear()
        self._processed_css_cache.clear()
        self._palette_cache.clear()
        # Clear LRU caches
        self.get_color.cache_clear()
        self.get_font_property.cache_clear()
    
    @lru_cache(maxsize=8)
    def _generate_optimized_stylesheet(self, theme_name: str) -> str:
        """Generate optimized stylesheet for a specific theme. Cached."""
        # Use cached version if available
        if theme_name in self._stylesheet_cache:
            return self._stylesheet_cache[theme_name]
        
        # Generate enhanced stylesheet with original visual appeal
        c = lambda key: self.get_color(key, theme_name)
        f = lambda key: self.get_font_property(key, theme_name)
        
        # Enhanced styles matching the original beautiful design
        stylesheet = f"""
        /* === ENHANCED GLOBAL STYLING === */
        QWidget {{
            background-color: {c('background')};
            color: {c('primary_text')};
            font-family: {f('ui_family')};
            font-size: {f('base_size')}px;
        }}
        
        /* === BEAUTIFUL HEADER STYLING === */
        QFrame#headerFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 {c('header_gradient_start')}, 
                        stop:1 {c('header_gradient_end')});
            border: none;
            border-radius: 12px;
            padding: 20px;
            margin: 10px;
        }}
        
        QLabel#headerTitle {{
            color: {c('header_text')};
            font-size: {f('large_size') + 8}px;
            font-weight: 700;
            background: transparent;
        }}
        
        /* === ENHANCED CARD STYLING === */
        QFrame[cardStyle="true"], QGroupBox {{
            background-color: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 12px;
            padding: 15px;
            margin: 5px;
        }}
        
        QGroupBox::title {{
            color: {c('primary_text')};
            font-weight: 600;
            font-size: {f('base_size') + 1}px;
            padding: 5px 10px;
            background-color: {c('tertiary_bg')};
            border-radius: 6px;
            border: 1px solid {c('border')};
        }}
        
        /* === STATUS CARDS WITH ENHANCED STYLING === */
        QFrame#statusCard {{
            background-color: {c('card_bg')};
            border: 2px solid {c('border')};
            border-radius: 12px;
            padding: 20px;
            margin: 8px;
        }}
        
        QLabel#statusTitle {{
            color: {c('secondary_text')};
            font-size: {f('small_size')}px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        QLabel#statusValue {{
            font-size: {f('large_size') + 4}px;
            font-weight: 700;
            padding: 5px 0;
        }}
        
        QLabel#statusSubtext {{
            color: {c('secondary_text')};
            font-size: {f('small_size')}px;
            font-weight: 500;
        }}
        
        /* === ENHANCED BUTTON STYLING === */
        QPushButton {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 12px 20px;
            color: {c('primary_text')};
            font-weight: 600;
            font-size: {f('base_size')}px;
            min-height: 32px;
        }}
        QPushButton:hover {{
            background-color: {c('accent_hover')};
            border-color: {c('accent_hover')};
            color: {c('header_text')};
        }}
        QPushButton:pressed {{
            background-color: {c('accent_pressed')};
            border-color: {c('accent')};
        }}
        
        /* === PRIMARY ACTION BUTTONS === */
        QPushButton[buttonStyle="primary"] {{
            background-color: {c('strawberry_primary')};
            border-color: {c('strawberry_primary')};
            color: {c('header_text')};
            font-weight: 700;
        }}
        QPushButton[buttonStyle="primary"]:hover {{
            background-color: {c('strawberry_coral')};
            border-color: {c('strawberry_coral')};
        }}
        
        /* === SUCCESS BUTTONS === */
        QPushButton[buttonStyle="success"] {{
            background-color: {c('strawberry_sage')};
            border-color: {c('strawberry_sage')};
            color: {c('header_text')};
            font-weight: 700;
        }}
        
        /* === TAB NAVIGATION STYLING === */
        QTabWidget::pane {{
            border: 2px solid {c('border')};
            border-radius: 8px;
            background-color: {c('secondary_bg')};
            padding: 5px;
        }}
        
        QTabBar::tab {{
            background-color: {c('tertiary_bg')};
            border: 2px solid {c('border')};
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            margin-right: 2px;
            color: {c('secondary_text')};
            font-weight: 600;
        }}
        
        QTabBar::tab:selected {{
            background-color: {c('strawberry_primary')};
            border-color: {c('strawberry_primary')};
            color: {c('header_text')};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {c('accent_hover')};
            color: {c('primary_text')};
        }}
        
        /* === ACTIVITY REPORT STYLING === */
        QFrame#activityReport {{
            background-color: {c('card_bg')};
            border: 2px solid {c('strawberry_primary')};
            border-radius: 12px;
            padding: 20px;
            margin: 10px;
        }}
        
        QScrollArea {{
            background-color: {c('secondary_bg')};
            border: 1px solid {c('border')};
            border-radius: 6px;
        }}
        
        /* === ENHANCED DIALOG STYLING === */
        QDialog {{
            background-color: {c('elevated_bg')};
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 12px;
        }}
        
        /* === TEXT DISPLAY STYLING === */
        QTextEdit, QPlainTextEdit {{
            background-color: {c('secondary_bg')};
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px;
            selection-background-color: {c('selection_bg')};
            selection-color: {c('selection_text')};
        }}
        
        /* === INPUT FIELD STYLING === */
        QLineEdit {{
            background-color: {c('secondary_bg')};
            color: {c('primary_text')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            padding: 10px;
            font-size: {f('base_size')}px;
        }}
        QLineEdit:focus {{
            border-color: {c('strawberry_primary')};
            background-color: {c('tertiary_bg')};
        }}
        
        /* === PROGRESS BAR STYLING === */
        QProgressBar {{
            background-color: {c('secondary_bg')};
            border: 2px solid {c('border')};
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {c('strawberry_coral')}, 
                        stop:1 {c('strawberry_primary')});
            border-radius: 6px;
        }}
        
        /* === STATUS COLORS === */
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
        
        # Cache the result
        self._stylesheet_cache[theme_name] = stylesheet
        return stylesheet
    
    @lru_cache(maxsize=16)
    def _process_qt_stylesheet_cached(self, css_hash: str, css: str) -> str:
        """Process CSS with caching to avoid redundant regex operations."""
        if css_hash in self._processed_css_cache:
            return self._processed_css_cache[css_hash]
        
        # Optimized regex patterns (compiled once)
        if not hasattr(self, '_compiled_patterns'):
            self._compiled_patterns = [
                re.compile(r'^\\s*transition[^;]*;.*$', re.MULTILINE),
                re.compile(r'^\\s*transform[^;]*;.*$', re.MULTILINE),
                re.compile(r'^\\s*box-shadow[^;]*;.*$', re.MULTILINE),
                re.compile(r'^\\s*text-shadow[^;]*;.*$', re.MULTILINE),
            ]
        
        processed_css = css
        for pattern in self._compiled_patterns:
            processed_css = pattern.sub('', processed_css)
        
        # Clean up whitespace efficiently
        processed_css = re.sub(r'\\n\\s*\\n+', '\\n\\n', processed_css)
        
        # Cache the result
        self._processed_css_cache[css_hash] = processed_css
        return processed_css
    
    def _apply_global_theme(self):
        """Apply the current theme globally with optimization."""
        app = QApplication.instance()
        if not app:
            return
        
        # Generate optimized stylesheet
        stylesheet = self._generate_optimized_stylesheet(self._current_theme)
        
        # Process the stylesheet (with caching)
        css_hash = str(hash(stylesheet))
        processed_stylesheet = self._process_qt_stylesheet_cached(css_hash, stylesheet)
        
        # Apply stylesheet
        app.setStyleSheet(processed_stylesheet)
        
        # Set application palette (cached)
        self._set_application_palette_cached()
    
    @lru_cache(maxsize=8)
    def _create_palette_for_theme(self, theme_name: str) -> QPalette:
        """Create a palette for a specific theme. Cached."""
        palette = QPalette()
        
        # Convert hex colors to QColor efficiently
        def hex_to_qcolor(hex_color: str) -> QColor:
            return QColor(hex_color)
        
        # Essential palette colors only
        palette.setColor(QPalette.ColorRole.Window, hex_to_qcolor(self.get_color('background', theme_name)))
        palette.setColor(QPalette.ColorRole.WindowText, hex_to_qcolor(self.get_color('primary_text', theme_name)))
        palette.setColor(QPalette.ColorRole.Base, hex_to_qcolor(self.get_color('secondary_bg', theme_name)))
        palette.setColor(QPalette.ColorRole.Text, hex_to_qcolor(self.get_color('primary_text', theme_name)))
        palette.setColor(QPalette.ColorRole.Button, hex_to_qcolor(self.get_color('tertiary_bg', theme_name)))
        palette.setColor(QPalette.ColorRole.ButtonText, hex_to_qcolor(self.get_color('primary_text', theme_name)))
        palette.setColor(QPalette.ColorRole.Highlight, hex_to_qcolor(self.get_color('selection_bg', theme_name)))
        palette.setColor(QPalette.ColorRole.HighlightedText, hex_to_qcolor(self.get_color('selection_text', theme_name)))
        
        return palette
    
    def _set_application_palette_cached(self):
        """Set the application palette using cached palettes."""
        app = QApplication.instance()
        if not app:
            return
        
        # Use cached palette
        palette = self._create_palette_for_theme(self._current_theme)
        app.setPalette(palette)
    
    def apply_component_styling(self, widget, style_type: str):
        """Apply specific styling to components to match original design."""
        if style_type == "header":
            widget.setObjectName("headerFrame")
            widget.setProperty("cardStyle", True)
        elif style_type == "status_card":
            widget.setObjectName("statusCard")
        elif style_type == "activity_report":
            widget.setObjectName("activityReport")
        elif style_type == "primary_button":
            widget.setProperty("buttonStyle", "primary")
        elif style_type == "success_button":
            widget.setProperty("buttonStyle", "success")
        elif style_type == "status_title":
            widget.setObjectName("statusTitle")
        elif style_type == "status_value":
            widget.setObjectName("statusValue")
        elif style_type == "status_subtext":
            widget.setObjectName("statusSubtext")
        elif style_type == "header_title":
            widget.setObjectName("headerTitle")
        
        # Refresh widget styling
        widget.style().polish(widget)

    def apply_qt_effects(self, widget: QWidget, effect_type: str = "button"):
        """Apply Qt-native effects to widgets (optimized for performance)."""
        if effect_type == "button" and isinstance(widget, QPushButton):
            # Only apply effects if not already applied
            if not hasattr(widget, '_effects_applied'):
                self._setup_lightweight_button_effects(widget)
                widget._effects_applied = True
    
    def _setup_lightweight_button_effects(self, button: QPushButton):
        """Setup lightweight button effects without expensive animations."""
        # Use simple state changes instead of animations for better performance
        original_style_sheet = button.styleSheet()
        
        def on_enter():
            button.setProperty("hovered", True)
            button.style().polish(button)
        
        def on_leave():
            button.setProperty("hovered", False) 
            button.style().polish(button)
        
        # Override events with lightweight handlers
        button.enterEvent = lambda e: on_enter()
        button.leaveEvent = lambda e: on_leave()
    
    def create_themed_message_box(self, parent: QWidget, msg_type: str, title: str, text: str, buttons=None) -> QMessageBox:
        """Create a themed message box efficiently."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        # Set message type
        icon_map = {
            "warning": QMessageBox.Icon.Warning,
            "information": QMessageBox.Icon.Information,
            "critical": QMessageBox.Icon.Critical,
            "question": QMessageBox.Icon.Question
        }
        if msg_type in icon_map:
            msg_box.setIcon(icon_map[msg_type])
        
        # Set buttons
        if buttons:
            msg_box.setStandardButtons(buttons)
        else:
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        return msg_box


# Optimized global instance management
_optimized_theme_manager = None

def get_optimized_theme_manager() -> OptimizedThemeManager:
    """Get the optimized theme manager instance."""
    global _optimized_theme_manager
    if _optimized_theme_manager is None:
        _optimized_theme_manager = OptimizedThemeManager()
    return _optimized_theme_manager

def set_app_theme_optimized(theme_name: str):
    """Set the application theme using optimized manager."""
    get_optimized_theme_manager().set_theme(theme_name)

def get_theme_color_optimized(color_key: str) -> str:
    """Get a theme color efficiently."""
    return get_optimized_theme_manager().get_color(color_key)

def apply_optimized_effects(widget: QWidget, effect_type: str = "button"):
    """Apply optimized effects to a widget."""
    get_optimized_theme_manager().apply_qt_effects(widget, effect_type)

def apply_component_styling(widget: QWidget, style_type: str):
    """Apply component styling to match original design."""
    get_optimized_theme_manager().apply_component_styling(widget, style_type)

def style_header(widget: QWidget):
    """Style a widget as a header with gradient background."""
    apply_component_styling(widget, "header")

def style_status_card(widget: QWidget):
    """Style a widget as a status card."""
    apply_component_styling(widget, "status_card")

def style_primary_button(widget: QPushButton):
    """Style a button as primary action button."""
    apply_component_styling(widget, "primary_button")

def style_success_button(widget: QPushButton):
    """Style a button as success button."""
    apply_component_styling(widget, "success_button")
