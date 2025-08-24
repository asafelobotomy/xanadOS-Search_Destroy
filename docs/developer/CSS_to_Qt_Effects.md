# CSS to Qt Effects Migration Guide

This document explains how the xanadOS Search & Destroy application handles CSS effects that aren't supported by Qt's stylesheet system, and provides Qt-native alternatives.

## Problem: Unsupported CSS Properties

Qt's stylesheet system doesn't support modern CSS properties like:
- `transition` - CSS animations
- `transform` - CSS transforms (translateY, scale, rotate, etc.)
- `box-shadow` - Drop shadows
- `text-shadow` - Text shadows

These properties cause "Unknown property" warnings and don't work.

## Solution: Qt-Native Effects System

The `ThemeManager` now includes a CSS preprocessor and Qt-native effects system:

### 1. CSS Preprocessing

The `_process_qt_stylesheet()` method automatically:
- Removes unsupported CSS properties to eliminate warnings
- Cleans up whitespace and formatting
- Provides fallbacks where possible

### 2. Qt-Native Effect Alternatives

#### Button Hover/Press Effects (replaces CSS transforms)

**Original CSS:**
```css
QPushButton:hover {
    transform: translateY(-1px);
    transition: all 0.12s ease-out;
}
QPushButton:pressed {
    transform: translateY(1px);
}
```

**Qt Alternative:**
```python
from app.gui.theme_manager import apply_button_effects

button = QPushButton("My Button")
apply_button_effects(button)  # Adds smooth animations
```

This creates smooth geometry animations using `QPropertyAnimation`.

#### Drop Shadows (replaces CSS box-shadow)

**Original CSS:**
```css
QDialog {
    box-shadow: 0 0 0 2px #rgba(255,255,255,0.3);
}
```

**Qt Alternative:**
```python
from app.gui.theme_manager import apply_shadow_effect

dialog = QDialog()
apply_shadow_effect(dialog)  # Adds QGraphicsDropShadowEffect
```

#### Auto-Setup for Widgets

**Automatic Effect Application:**
```python
from app.gui.theme_manager import setup_widget_effects

# Automatically applies appropriate effects based on widget type
setup_widget_effects(my_widget)
```

## Usage Examples

### 1. Enhanced Buttons

```python
from PyQt6.QtWidgets import QPushButton
from app.gui.theme_manager import apply_button_effects

button = QPushButton("Click Me")
apply_button_effects(button)

# Button now has:
# - Smooth hover animations (moves up 1px)
# - Press feedback (moves down 1px)
# - Easing curves for natural motion
```

### 2. Dialogs with Shadows

```python
from PyQt6.QtWidgets import QDialog
from app.gui.theme_manager import apply_shadow_effect

dialog = QDialog()
apply_shadow_effect(dialog)

# Dialog now has:
# - Subtle drop shadow
# - Theme-aware shadow color
# - Proper alpha blending
```

### 3. Auto-Setup During Widget Creation

```python
from app.gui.theme_manager import setup_widget_effects

class MyCustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

        # Automatically apply effects based on widget types
        setup_widget_effects(self)

        # Or apply to specific child widgets
        for button in self.findChildren(QPushButton):
            setup_widget_effects(button)
```

## Technical Details

### Animation System

The button effects use Qt's `QPropertyAnimation` with:
- **Duration**: 150ms (matches original CSS timing)
- **Easing**: `QEasingCurve.Type.OutCubic` (smooth deceleration)
- **Property**: `geometry` (for position changes)

### Shadow System

Drop shadows use `QGraphicsDropShadowEffect` with:
- **Blur Radius**: 8px
- **Offset**: (2, 2) pixels
- **Color**: Theme-aware shadow color with transparency
- **Performance**: Hardware-accelerated when available

### CSS Preprocessing

The preprocessor uses regex patterns to:
1. Remove unsupported properties
2. Clean up formatting
3. Preserve all supported Qt stylesheet features
4. Maintain theme color variables

## Migration Notes

### For Existing Code

No changes needed! The CSS preprocessing happens automatically when themes are applied.

### For New Widgets

Add effect setup in widget constructors:

```python
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        setup_widget_effects(self)  # Add this line
```

### Performance Considerations

- **Animations**: Lightweight, GPU-accelerated when available
- **Shadows**: Cached and reused efficiently
- **CSS Processing**: Done once per theme change, not per widget

## Demo

Run the effects demo to see the system in action:

```bash
python dev/qt_effects_demo.py
```

## Benefits

1. **✅ No More CSS Warnings**: Clean console output
2. **✅ Smooth Animations**: Better than CSS transitions in Qt
3. **✅ Theme Integration**: Effects match current theme colors
4. **✅ Performance**: Native Qt effects are optimized
5. **✅ Compatibility**: Works across all Qt platforms
6. **✅ Maintainable**: Centralized effect management

## API Reference

### Functions

- `apply_button_effects(button)` - Add hover/press animations to buttons
- `apply_shadow_effect(widget)` - Add drop shadow to any widget
- `setup_widget_effects(widget)` - Auto-apply effects based on widget type

### Theme Manager Methods

- `_process_qt_stylesheet(css)` - Preprocess CSS to remove unsupported properties
- `apply_qt_effects(widget, effect_type)` - Apply specific effect types
- `_setup_button_effects(button)` - Internal button animation setup
- `_setup_shadow_effect(widget)` - Internal shadow effect setup

This system provides a seamless upgrade from CSS effects to Qt-native effects while maintaining the visual design and improving performance.
