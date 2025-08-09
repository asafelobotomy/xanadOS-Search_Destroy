# ARCHIVED 2025-08-09: ComboBox debugging from theme fixes
# Original location: debug_combobox_fixed.py
# Archive category: experimental
# ========================================


#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent

class NoWheelComboBox(QComboBox):
    """A QComboBox that completely ignores wheel events to prevent accidental changes."""

    def wheelEvent(self, event: QWheelEvent):
        """Completely ignore all wheel events."""
        event.ignore()
        
    def showPopup(self):
        """Override showPopup to ensure dark theme is applied to popup."""
        super().showPopup()
        
        # Apply theme to popup view after it's created
        popup_view = self.view()
        if popup_view:
            # Force dark theme styling on the popup
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
            
            # Also force background on popup frame if it exists
            parent = popup_view.parent()
            if parent and hasattr(parent, 'setStyleSheet'):
                parent.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a2a !important;
                        border: 1px solid #EE8980 !important;
                        border-radius: 4px !important;
                    }
                """)
                # Also check for grandparent containers
                grandparent = parent.parent()
                if grandparent and hasattr(grandparent, 'setStyleSheet'):
                    grandparent.setStyleSheet("""
                        QWidget {
                            background-color: #2a2a2a !important;
                        }
                    """)

class ComboBoxTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('ComboBox Debug Test - FIXED')
        self.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout()
        
        # Add test label
        label = QLabel('Testing FIXED ComboBox Styling:')
        layout.addWidget(label)
        
        # Create regular ComboBox
        regular_combo = QComboBox()
        regular_combo.addItems(['Fixed Option 1', 'Fixed Option 2', 'Fixed Option 3', 'Fixed Option 4'])
        layout.addWidget(regular_combo)
        
        # Create NoWheel ComboBox  
        nowheel_combo = NoWheelComboBox()
        nowheel_combo.addItems(['NoWheel Fixed 1', 'NoWheel Fixed 2', 'NoWheel Fixed 3', 'NoWheel Fixed 4'])
        layout.addWidget(nowheel_combo)
        
        # Fix regular ComboBox popup with dynamic method override
        original_showPopup = regular_combo.showPopup
        
        def enhanced_showPopup():
            original_showPopup()
            # Apply theme to popup view after it's created
            popup_view = regular_combo.view()
            if popup_view:
                # Force dark theme styling on the popup
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
                
                # Also force background on popup frame if it exists
                parent = popup_view.parent()
                if parent and hasattr(parent, 'setStyleSheet'):
                    parent.setStyleSheet("""
                        QFrame {
                            background-color: #2a2a2a !important;
                            border: 1px solid #EE8980 !important;
                            border-radius: 4px !important;
                        }
                    """)
        
        regular_combo.showPopup = enhanced_showPopup
        
        self.setLayout(layout)
        
        # Apply comprehensive dark theme styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #FFCDAA;
                font-size: 12px;
                font-weight: 500;
            }
            
            QLabel {
                color: #FFCDAA;
                font-weight: 600;
                margin: 10px;
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

def main():
    app = QApplication(sys.argv)
    
    # Force Fusion style for consistent theming
    app.setStyle('Fusion')
    print("✅ Set application style to Fusion")
    
    # Create and show the test window
    window = ComboBoxTestWindow()
    window.show()
    
    print("Fixed debug test window created.")
    print("Click on the dropdowns to see if they now use the correct dark theme.")
    print("Both dropdowns should now have dark backgrounds in their popup menus.")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
