# ARCHIVED 2025-08-09: ComboBox debugging from theme fixes
# Original location: debug_combobox_enhanced.py
# Archive category: experimental
# ========================================


#!/usr/bin/env python3
"""Enhanced debug script to test ComboBox styling fixes with persistent popup styling."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtGui import QWheelEvent

class NoWheelComboBox(QComboBox):
    """A QComboBox that completely ignores wheel events to prevent accidental changes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Store reference to main window for theme access
        self.main_window = None
        self.current_theme = "dark"  # Default for debug
        
    def set_main_window(self, main_window):
        """Set reference to main window for theme access."""
        self.main_window = main_window

    def wheelEvent(self, event: QWheelEvent):
        """Completely ignore all wheel events."""
        event.ignore()
        
    def showPopup(self):
        """Override showPopup to ensure dark theme is applied to popup every time."""
        super().showPopup()
        
        # Apply theme styling every time the popup is shown
        self.apply_popup_styling()
        
    def apply_popup_styling(self):
        """Apply proper styling to the popup view."""
        popup_view = self.view()
        if not popup_view:
            return
            
        # Determine current theme
        is_dark_theme = self.current_theme == "dark"
            
        if is_dark_theme:
            # Dark theme styling
            popup_view.setStyleSheet("""
                QListView {
                    background-color: #2a2a2a !important;
                    border: 1px solid #EE8980 !important;
                    border-radius: 4px !important;
                    color: #FFCDAA !important;
                    selection-background-color: #F14666 !important;
                    selection-color: #ffffff !important;
                    outline: none !important;
                }
                QListView::item {
                    padding: 8px 12px;
                    min-height: 20px;
                    border: none;
                }
                QListView::item:hover {
                    background-color: #EE8980 !important;
                    color: #ffffff !important;
                }
                QListView::item:selected {
                    background-color: #F14666 !important;
                    color: #ffffff !important;
                }
            """)
        else:
            # Light theme styling
            popup_view.setStyleSheet("""
                QListView {
                    background-color: #ffffff !important;
                    border: 1px solid #F8D49B !important;
                    border-radius: 4px !important;
                    color: #2c2c2c !important;
                    selection-background-color: #75BDE0 !important;
                    selection-color: #ffffff !important;
                    outline: none !important;
                }
                QListView::item {
                    padding: 8px 12px;
                    min-height: 20px;
                    border: none;
                }
                QListView::item:hover {
                    background-color: #F8BC9B !important;
                    color: #2c2c2c !important;
                }
                QListView::item:selected {
                    background-color: #75BDE0 !important;
                    color: #ffffff !important;
                }
            """)
            
        # Also force background on popup frame containers
        parent = popup_view.parent()
        if parent and hasattr(parent, 'setStyleSheet'):
            if is_dark_theme:
                parent.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a2a !important;
                        border: 1px solid #EE8980 !important;
                        border-radius: 4px !important;
                    }
                """)
            else:
                parent.setStyleSheet("""
                    QFrame {
                        background-color: #ffffff !important;
                        border: 1px solid #F8D49B !important;
                        border-radius: 4px !important;
                    }
                """)
            
            # Also check for grandparent containers
            grandparent = parent.parent()
            if grandparent and hasattr(grandparent, 'setStyleSheet'):
                bg_color = "#2a2a2a" if is_dark_theme else "#ffffff"
                grandparent.setStyleSheet(f"""
                    QWidget {{
                        background-color: {bg_color} !important;
                    }}
                """)

def fix_regular_combobox_popup(combo, theme="dark"):
    """Fix styling for regular ComboBox popup."""
    original_showPopup = combo.showPopup
    
    def enhanced_showPopup():
        original_showPopup()
        # Apply theme to popup view after it's created
        popup_view = combo.view()
        if popup_view:
            # Force theme styling on the popup every time
            if theme == "dark":
                popup_view.setStyleSheet("""
                    QListView {
                        background-color: #2a2a2a !important;
                        border: 1px solid #EE8980 !important;
                        border-radius: 4px !important;
                        color: #FFCDAA !important;
                        selection-background-color: #F14666 !important;
                        selection-color: #ffffff !important;
                        outline: none !important;
                    }
                    QListView::item {
                        padding: 8px 12px;
                        min-height: 20px;
                        border: none;
                    }
                    QListView::item:hover {
                        background-color: #EE8980 !important;
                        color: #ffffff !important;
                    }
                    QListView::item:selected {
                        background-color: #F14666 !important;
                        color: #ffffff !important;
                    }
                """)
            
            # Also force background on popup frame containers
            parent = popup_view.parent()
            if parent and hasattr(parent, 'setStyleSheet'):
                if theme == "dark":
                    parent.setStyleSheet("""
                        QFrame {
                            background-color: #2a2a2a !important;
                            border: 1px solid #EE8980 !important;
                            border-radius: 4px !important;
                        }
                    """)
    
    combo.showPopup = enhanced_showPopup

def main():
    app = QApplication(sys.argv)
    
    # Force Fusion style for consistency
    try:
        app.setStyle('Fusion')
        print("✅ Set application style to Fusion")
    except Exception as e:
        print(f"⚠️ Could not set Fusion style: {e}")
    
    # Create main window
    window = QWidget()
    window.setWindowTitle("ComboBox Debug Test - ENHANCED FIX")
    window.setGeometry(100, 100, 400, 300)
    
    # Apply dark theme to window
    window.setStyleSheet("""
        QWidget {
            background-color: #1a1a1a;
            color: #FFCDAA;
            font-size: 12px;
        }
        QComboBox {
            background-color: #3a3a3a;
            border: 2px solid #EE8980;
            border-radius: 6px;
            padding: 10px 16px;
            color: #FFCDAA;
            font-weight: 500;
            font-size: 12px;
            min-width: 120px;
        }
        QComboBox:focus {
            border-color: #F14666;
            background-color: #2a2a2a;
        }
        QComboBox:hover {
            border-color: #F14666;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left-width: 1px;
            border-left-color: #EE8980;
            border-left-style: solid;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            background-color: #4a4a4a;
        }
        QComboBox::drop-down:hover {
            background-color: #F14666;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #FFCDAA;
            width: 0px;
            height: 0px;
        }
    """)
    
    # Create layout
    layout = QVBoxLayout()
    
    # Add label
    label = QLabel("Testing ENHANCED ComboBox Styling:")
    layout.addWidget(label)
    
    # Create regular ComboBox
    regular_combo = QComboBox()
    regular_combo.addItems(["Enhanced Option 1", "Enhanced Option 2", "Enhanced Option 3", "Enhanced Option 4"])
    regular_combo.setCurrentText("Enhanced Option 1")
    layout.addWidget(regular_combo)
    
    # Create NoWheelComboBox  
    nowheel_combo = NoWheelComboBox()
    nowheel_combo.addItems(["NoWheel Enhanced 1", "NoWheel Enhanced 2", "NoWheel Enhanced 3", "NoWheel Enhanced 4"])
    nowheel_combo.setCurrentText("NoWheel Enhanced 3")
    layout.addWidget(nowheel_combo)
    
    # Apply enhanced popup fixes
    fix_regular_combobox_popup(regular_combo, "dark")
    
    window.setLayout(layout)
    window.show()
    
    print("Enhanced debug test window created.")
    print("Click on the dropdowns multiple times to test persistent styling.")
    print("The styling should remain consistent across all popup openings.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
