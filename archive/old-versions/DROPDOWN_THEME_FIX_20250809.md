# ARCHIVED 2025-08-09: Consolidated into organized structure
# Original location: docs/implementation/bug-fixes/DROPDOWN_THEME_FIX.md
# Archive category: old-versions
# ========================================


# Dropdown Theme Fix Summary

## Problem
The dropdown menus (QComboBox widgets) in the GUI were using the system's Breeze theme instead of the application's custom dark/light themes, causing visual inconsistency.

## Root Cause
Qt applications can inherit system-level styling for certain widgets, particularly popup/dropdown elements, even when custom stylesheets are applied. This happens because:

1. Qt's default behavior favors system integration over application-specific styling
2. Dropdown popup widgets can be created as separate top-level windows that don't inherit parent stylesheets
3. The application was using the default Qt style instead of forcing a consistent base style

## Solutions Implemented

### 1. Application-Level Style Control (`app/main.py`)
- **Set Fusion Style**: Force Qt to use 'Fusion' style instead of system style
- **Disable Native Widgets**: Set `AA_DontUseNativeDialogs` and `AA_DontUseNativeMenuBar` attributes to prevent system theme leakage

```python
# Force Qt to use Fusion style to avoid system theme interference
app.setStyle('Fusion')
app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
```

### 2. Enhanced Platform Configuration (`app/gui/main_window.py`)
- **Updated `_configure_platform_dropdown_behavior()`**: Added more comprehensive platform-specific settings
- **Added Style Setting**: Attempt to set Fusion style at widget level as fallback

### 3. Custom ComboBox Implementation (`app/gui/main_window.py`)
- **Enhanced `NoWheelComboBox`**: Added theme inheritance logic
- **Popup Theme Override**: Force popup widgets to use application theme
- **Delayed Styling**: Apply styling after popup is shown using QTimer

### 4. Theme Application Enhancement (`app/gui/main_window.py`)
- **Added `_ensure_combobox_theming()`**: Method to enforce theme on all combo boxes
- **Enhanced `_get_combo_popup_stylesheet()`**: Comprehensive popup styling for both dark and light themes
- **Updated `apply_theme()`**: Call theme enforcement after theme application

## Files Modified

1. **`app/main.py`**
   - Added Qt style forcing and platform attributes
   - Added Qt import for attributes

2. **`app/gui/main_window.py`**
   - Enhanced `NoWheelComboBox` class with theme inheritance
   - Added comprehensive dropdown popup styling methods
   - Updated platform configuration for better theme control
   - Enhanced theme application workflow

## Testing

To test the fix:

1. Run the application: `python app/main.py`
2. Open any dropdown menu (scan type, file filter, etc.)
3. Verify the dropdown list uses the application's dark theme with orange/red accents instead of system Breeze theme
4. Check both dark and light theme modes

## Expected Behavior

- **Before Fix**: Dropdown lists showed white background with blue accents (Breeze theme)
- **After Fix**: Dropdown lists show:
  - **Dark Theme**: Dark gray background (#2a2a2a) with orange (#EE8980) and red (#F14666) accents
  - **Light Theme**: White background with sky blue (#75BDE0) and peach (#F8BC9B) accents

## Technical Notes

- The fix uses multiple fallback mechanisms to ensure theme consistency
- Some linting errors are expected due to PyQt6's dynamic nature
- The solution maintains compatibility across different Linux desktop environments
- Platform-specific attributes help prevent interference from Wayland/X11 window managers
