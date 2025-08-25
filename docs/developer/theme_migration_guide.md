# !/usr/bin/env python3

"""
Theme Migration Script
Automatically converts existing dialogs to use the new centralized theming system.
"""

import os
import re
from pathlib import Path

def migrate_dialog_files():
    """Convert all dialog files to use the new theming system."""

    gui_dir = Path(**file**).parent

## Files to update

    dialog_files = [
        "all_warnings_dialog.py",
        "rkhunter_components.py",
        "update_components.py",

## Add other dialog files as needed

    ]

    for file_name in dialog_files:
        file_path = gui_dir / file_name
        if not file_path.exists():
            continue

        print(f"Migrating {file_name}...")

## Read file content

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

## Add import for ThemedDialog

        if "from .themed_widgets import" not in content:

## Find the last PyQt6 import

            import_pattern = r'(from PyQt6\.QtWidgets import[^)]+\))'
            match = re.search(import_pattern, content, re.DOTALL)
            if match:
                insertion_point = match.end()
                content = (content[:insertion_point] +
                          '\nfrom .themed_widgets import ThemedDialog, ThemedWidget' +
                          content[insertion_point:])

## Replace QDialog inheritance with ThemedDialog

        content = re.sub(
            r'class (\w+)\(QDialog\):',
            r'class \1(ThemedDialog):',
            content
        )

## Remove manual theme application methods

        content = re.sub(

            r'def _apply_theme\(self._?\n(?:._?\n)_?._?(?=\n    def|\nclass|\Z)',
            '',

            content,
            flags=re.DOTALL
        )

## Replace QMessageBox calls with themed versions

        content = re.sub(

            r'QMessageBox\.(information|warning|critical|question)\(',
            r'self.show_themed_message_box("\1", ',

            content
        )

## Write back the modified content

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Migrated {file_name}")

def create_theme_usage_guide():
    """Create a guide for developers on using the new theming system."""

    guide_content = """# Theme System Usage Guide

## Overview

The new centralized theming system automatically applies consistent themes to all GUI components without manual intervention.

## Quick Start

### For New Dialogs

```Python
from .themed_widgets import ThemedDialog

class MyDialog(ThemedDialog):
    def **init**(self, parent=None):
        super().**init**(parent)

## Your dialog setup here

## Theme is automatically applied

```text

### For New Widgets

```Python
from .themed_widgets import ThemedWidget

class MyWidget(ThemedWidget):
    def **init**(self, parent=None):
        super().**init**(parent)

## Your widget setup here

## Theme is automatically applied 2

```text

### For Message Boxes

```Python

## Instead of QMessageBox.information(...)

self.show_themed_message_box("information", "Title", "Message")

## Instead of QMessageBox.warning(...)

self.show_themed_message_box("warning", "Title", "Message")

```text

### For Existing Widgets (Migration)

```Python
from .themed_widgets import make_widget_themed

## Convert existing widget to themed

existing_widget = QWidget()
make_widget_themed(existing_widget)

```text

## Theme Colors

Get theme colors anywhere in your themed widgets:

```Python

## Get current theme colors

bg_color = self.get_theme_color("background")
text_color = self.get_theme_color("primary_text")
accent_color = self.get_theme_color("accent")

```text

Available color keys:

- `background` - Main background color
- `secondary_bg` - Secondary background
- `tertiary_bg` - Tertiary background
- `primary_text` - Main text color
- `secondary_text` - Secondary text color
- `muted_text` - Muted/disabled text
- `success` - Success color
- `error` - Error color
- `warning` - Warning color
- `info` - Info color
- `accent` - Accent/highlight color
- `border` - Border color
- `hover_bg` - Hover background
- `pressed_bg` - Pressed background
- `selection_bg` - Selection background
- `selection_text` - Selection text color

## Changing Themes

```Python
from .theme_manager import set_app_theme

## Change to light theme

set_app_theme("light")

## Change to dark theme

set_app_theme("dark")

```text

## Custom Styling

For custom styling that needs to respond to theme changes:

```Python
class MyThemedWidget(ThemedWidget):
    def _apply_theme(self):
        """Override this method for custom theme application."""
        super()._apply_theme()

## Your custom theming logic here

        custom_color = self.get_theme_color("accent")
        self.setStyleSheet(f"border: 2px solid {custom_color};")

```text

## Benefits

1. **Automatic theming** - All widgets themed consistently
2. **Global theme changes** - Change theme once, applies everywhere
3. **No manual intervention** - Themes automatically applied to new components
4. **Consistent appearance** - Same look across all components
5. **Easy maintenance** - Update theme definitions in one place

## Migration from Old System

1. Replace `QDialog`with`ThemedDialog`
2. Replace `QWidget`with`ThemedWidget`
3. Remove manual `_apply_theme()` methods
4. Replace `QMessageBox`calls with`show_themed_message_box()`
5. Use `get_theme_color()` instead of hardcoded colors

The new system handles everything automatically!
"""

    guide_path = Path(**file**).parent / "THEME_SYSTEM_GUIDE.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)

    print(f"✓ Created theme usage guide: {guide_path}")

if **name** == "**main**":
    print("🎨 Migrating to centralized theming system...")
    migrate_dialog_files()
    create_theme_usage_guide()
    print("✅ Migration complete!")
    print("\nNext steps:")
    print("1. Test the application to ensure theming works correctly")
    print("2. Read THEME_SYSTEM_GUIDE.md for usage instructions")
    print("3. Remove any remaining manual theme application code")
