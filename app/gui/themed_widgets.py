#!/usr/bin/env python3
"""Themed Widget Mixins - Base classes for theme-aware G    # Add theming methods to the widget
    widget.get_theme_color = lambda color_key: get_theme_manager().get_color(color_key)
    widget.get_theme_font_property = lambda font_key: get_theme_manager().get_font_property(font_key)
    widget.show_themed_message_box = lambda msg_type, title, text, buttons=None: get_theme_manager().create_themed_message_box(widget, msg_type, title, text, buttons).exec()
    # Connect to theme changes
    theme_manager = get_theme_manager()onents
Automatically handle theme changes and provide theme utilities.
"""

from PyQt6.QtWidgets import QDialog, QWidget

from .theme_manager import get_theme_manager


class ThemedWidgetMixin:
    """Mixin class for widgets that automatically respond to theme changes.
    Inherit from this to get automatic theme updating capabilities.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect to theme changes
        theme_manager = get_theme_manager()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        # Apply initial theme
        self._apply_theme()

    def _on_theme_changed(self, theme_name: str):
        """Called when the global theme changes."""
        self._apply_theme()

    def _apply_theme(self):
        """Apply the current theme to this widget.
        Override this method in subclasses for custom theming.
        Default implementation does nothing as global stylesheet handles most cases.
        """
        pass

    def get_theme_color(self, color_key: str) -> str:
        """Get a color from the current theme."""
        return get_theme_manager().get_color(color_key)

    def get_theme_font_property(self, font_key: str):
        """Get a font property from the current theme."""
        return get_theme_manager().get_font_property(font_key)

    def show_themed_message_box(self, msg_type: str, title: str, text: str, buttons=None):
        """Show a themed message box."""
        msg_box = get_theme_manager().create_themed_message_box(
            self, msg_type, title, text, buttons
        )
        return msg_box.exec()


class ThemedDialog(QDialog, ThemedWidgetMixin):
    """Base class for dialogs with automatic theming.
    Use this instead of QDialog for consistent theming.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        # ThemedWidgetMixin.__init__ is called automatically via super()


class ThemedWidget(QWidget, ThemedWidgetMixin):
    """Base class for widgets with automatic theming.
    Use this instead of QWidget for consistent theming.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        # ThemedWidgetMixin.__init__ is called automatically via super()


# Utility functions for existing widgets
def make_widget_themed(widget: QWidget):
    """Add theming capabilities to an existing widget instance.
    This is useful for widgets that can't inherit from ThemedWidget.
    """
    # Add theming methods to the widget
    widget.get_theme_color = lambda color_key: get_theme_manager().get_color(color_key)
    widget.get_theme_font_property = lambda font_key: get_theme_manager().get_font_property(
        font_key
    )
    widget.show_themed_message_box = (
        lambda msg_type, title, text, buttons=None: get_theme_manager()
        .create_themed_message_box(widget, msg_type, title, text, buttons)
        .exec()
    )

    # Connect to theme changes
    theme_manager = get_theme_manager()
    if hasattr(widget, "_apply_theme"):
        theme_manager.theme_changed.connect(widget._apply_theme)

    return widget


def apply_widget_class_styles(widget_class: str, **style_properties):
    """Apply CSS class-like styling to widgets.
    Usage: apply_widget_class_styles("header", font_size="16px", font_weight="bold")
    """
    get_theme_manager()
    # This would extend the global stylesheet - for now, use the class attribute approach
    # You can set widget.setProperty("class", "header") and it will be styled via CSS
    pass
