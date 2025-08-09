# ARCHIVED 2025-08-09: ComboBox debugging from theme fixes
# Original location: debug_combobox_styling.py
# Archive category: experimental
# ========================================


#!/usr/bin/env python3
"""
Debug script to test ComboBox styling issues
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    
    # Force Fusion style like the main app
    try:
        app.setStyle('Fusion')
        print("✅ Set application style to Fusion")
    except Exception as e:
        print(f"❌ Could not set Fusion style: {e}")
    
    # Platform attributes like main app
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
    
    window = QWidget()
    window.setWindowTitle("ComboBox Debug Test")
    window.setGeometry(100, 100, 400, 300)
    
    layout = QVBoxLayout()
    
    label = QLabel("Testing ComboBox Styling:")
    layout.addWidget(label)
    
    # Test regular QComboBox
    combo1 = QComboBox()
    combo1.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])
    layout.addWidget(combo1)
    
    # Test NoWheelComboBox equivalent
    from gui.main_window import NoWheelComboBox
    combo2 = NoWheelComboBox()
    combo2.addItems(["NoWheel 1", "NoWheel 2", "NoWheel 3", "NoWheel 4"])
    layout.addWidget(combo2)
    
    window.setLayout(layout)
    
    # Apply the exact same dark theme styling as main window
    window.setStyleSheet("""
        QWidget {
            background-color: #1a1a1a;
            color: #FFCDAA;
            font-size: 12px;
            font-weight: 500;
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

        QComboBox QAbstractItemView {
            background-color: #2a2a2a;
            border: 1px solid #EE8980;
            border-radius: 4px;
            color: #FFCDAA;
            selection-background-color: #F14666;
            selection-color: #ffffff;
            outline: none;
            margin: 0px;
            padding: 0px;
        }

        QComboBox QAbstractItemView::item {
            padding: 8px 12px;
            min-height: 20px;
            border: none;
            margin: 0px;
        }

        QComboBox QAbstractItemView::item:hover {
            background-color: #EE8980;
            color: #ffffff;
            border: none;
        }

        QComboBox QAbstractItemView::item:selected {
            background-color: #F14666;
            color: #ffffff;
            border: none;
        }

        /* Fix dropdown popup frame - more specific selectors to override system theme */
        QComboBox QListView {
            background-color: #2a2a2a !important;
            border: 1px solid #EE8980 !important;
            border-radius: 4px !important;
            color: #FFCDAA !important;
            selection-background-color: #F14666 !important;
            selection-color: #ffffff !important;
            outline: none !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        QComboBox QFrame {
            background-color: #2a2a2a !important;
            border: 1px solid #EE8980 !important;
            border-radius: 4px !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        /* Target all possible popup container elements */
        QComboBox QWidget {
            background-color: #2a2a2a !important;
            border: none !important;
            color: #FFCDAA !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        QComboBox QScrollArea {
            background-color: #2a2a2a !important;
            border: none !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        QComboBox QScrollArea QWidget {
            background-color: #2a2a2a !important;
            border: none !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        QComboBox QScrollBar {
            background-color: #3a3a3a !important;
            border: none !important;
            width: 12px !important;
            margin: 0px !important;
        }

        QComboBox QScrollBar::handle {
            background-color: #EE8980 !important;
            border: none !important;
            border-radius: 6px !important;
            min-height: 20px !important;
            margin: 2px !important;
        }

        QComboBox QScrollBar::handle:hover {
            background-color: #F14666 !important;
        }

        QComboBox QScrollBar::add-line, QComboBox QScrollBar::sub-line {
            border: none !important;
            background: none !important;
            color: none !important;
            subcontrol-origin: margin !important;
            subcontrol-position: right !important;
            width: 0px !important;
            height: 0px !important;
        }

        QComboBox QScrollBar::add-page, QComboBox QScrollBar::sub-page {
            background: none !important;
            border: none !important;
        }
        
        /* Force all popup widgets to use dark theme - most aggressive override */
        QComboBox * {
            background-color: #2a2a2a !important;
            color: #FFCDAA !important;
            border: none !important;
            margin: 0px !important;
        }

        /* Target the popup window container itself */
        QComboBox QListView::item {
            padding: 8px 12px !important;
            min-height: 20px !important;
            border: none !important;
            margin: 0px !important;
            background-color: transparent !important;
        }

        /* Universal ComboBox theming for dialogs and child windows */
        QDialog QComboBox,
        QDialog QComboBox * {
            background-color: #2a2a2a !important;
            color: #FFCDAA !important;
            border: 1px solid #EE8980 !important;
            border-radius: 4px !important;
        }

        QDialog QComboBox QListView,
        QDialog QComboBox QAbstractItemView {
            background-color: #2a2a2a !important;
            color: #FFCDAA !important;
            border: 1px solid #EE8980 !important;
            selection-background-color: #F14666 !important;
            selection-color: #ffffff !important;
        }

        /* Ensure all child widgets and popups inherit theme */
        * QComboBox,
        * QComboBox * {
            background-color: #2a2a2a !important;
            color: #FFCDAA !important;
        }
    """)
    
    window.show()
    
    print("Debug test window created.")
    print("Click on the dropdowns to see if they use the correct dark theme.")
    print("If they still show white borders, the issue is deeper than stylesheet application.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
