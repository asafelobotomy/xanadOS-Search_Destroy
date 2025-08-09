# ARCHIVED 2025-08-09: Scrollbar testing from theme fixes
# Original location: debug_scrollbar_test.py
# Archive category: experimental
# ========================================


#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QWheelEvent

class ScrollbarComboBox(QComboBox):
    """A QComboBox with enhanced scrollbar styling instead of arrows."""

    def __init__(self, parent=None, name="ScrollbarCombo"):
        super().__init__(parent)
        self.debug_name = name
        print(f"🔧 {self.debug_name}: Created with scrollbar styling")
        
    def wheelEvent(self, event: QWheelEvent):
        """Completely ignore all wheel events."""
        event.ignore()
        
    def showPopup(self):
        """Override showPopup to ensure scrollbar styling is applied."""
        super().showPopup()
        print(f"🚀 {self.debug_name}: showPopup() called - applying scrollbar styling")
        
        # Apply scrollbar styling to popup view
        popup_view = self.view()
        if popup_view:
            print(f"📋 {self.debug_name}: Applying enhanced scrollbar styling")
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
                QScrollBar:vertical {
                    background-color: #3a3a3a !important;
                    border: 1px solid #EE8980 !important;
                    border-radius: 6px !important;
                    width: 16px !important;
                    margin: 0px 0px 0px 0px !important;
                }
                QScrollBar::handle:vertical {
                    background-color: #EE8980 !important;
                    border: none !important;
                    border-radius: 5px !important;
                    min-height: 30px !important;
                    margin: 2px !important;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #F14666 !important;
                }
                QScrollBar::handle:vertical:pressed {
                    background-color: #E03256 !important;
                }
                QScrollBar::add-line:vertical {
                    height: 0px !important;
                    width: 0px !important;
                    subcontrol-position: bottom !important;
                    subcontrol-origin: margin !important;
                    background: transparent !important;
                    border: none !important;
                }
                QScrollBar::sub-line:vertical {
                    height: 0px !important;
                    width: 0px !important;
                    subcontrol-position: top !important;
                    subcontrol-origin: margin !important;
                    background: transparent !important;
                    border: none !important;
                }
                QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                    width: 0px !important;
                    height: 0px !important;
                    background: transparent !important;
                    border: none !important;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: transparent !important;
                    border: none !important;
                }
            """)
            print(f"✅ {self.debug_name}: Enhanced scrollbar styling applied")

class ScrollbarTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.monitored_combos = []
        self.initUI()
        self.setup_monitoring()
        
    def initUI(self):
        self.setWindowTitle('ComboBox Scrollbar Test - NO ARROWS!')
        self.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        # Add test label
        label = QLabel('SCROLLBAR TEST: Should show scrollbars instead of arrows:')
        layout.addWidget(label)
        
        # Create ComboBoxes with many items to force scrolling
        combo1 = ScrollbarComboBox(name="LongList1")
        for i in range(50):  # Many items to force scrollbar
            combo1.addItem(f"Long Option {i+1} - This is a test item with lots of text")
        layout.addWidget(combo1)
        
        combo2 = ScrollbarComboBox(name="LongList2")
        for i in range(30):  # Many items to force scrollbar
            combo2.addItem(f"Another Choice {i+1} - More text to make scrolling necessary")
        layout.addWidget(combo2)
        
        combo3 = ScrollbarComboBox(name="LongList3")
        for i in range(25):  # Many items to force scrollbar
            combo3.addItem(f"Item {i+1} - Even more text content here")
        layout.addWidget(combo3)
        
        # Store combos for monitoring
        self.monitored_combos = [combo1, combo2, combo3]
        
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
                font-size: 14px;
            }
            
            QComboBox {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                padding: 10px 16px;
                color: #FFCDAA;
                font-weight: 500;
                font-size: 12px;
                min-width: 200px;
                min-height: 30px;
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
    
    def setup_monitoring(self):
        """Set up continuous monitoring of ComboBox popups."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_popup_styling)
        self.monitor_timer.start(200)  # Check every 200ms
        print("✅ Started scrollbar popup monitoring")
    
    def monitor_popup_styling(self):
        """Continuously monitor and enforce scrollbar styling."""
        for i, combo in enumerate(self.monitored_combos):
            try:
                popup_view = combo.view()
                # Only apply styling if popup is actually visible
                if popup_view and popup_view.isVisible():
                    # Re-apply scrollbar styling to ensure it persists
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
                        QScrollBar:vertical {
                            background-color: #3a3a3a !important;
                            border: 1px solid #EE8980 !important;
                            border-radius: 6px !important;
                            width: 16px !important;
                            margin: 0px 0px 0px 0px !important;
                        }
                        QScrollBar::handle:vertical {
                            background-color: #EE8980 !important;
                            border: none !important;
                            border-radius: 5px !important;
                            min-height: 30px !important;
                            margin: 2px !important;
                        }
                        QScrollBar::handle:vertical:hover {
                            background-color: #F14666 !important;
                        }
                        QScrollBar::handle:vertical:pressed {
                            background-color: #E03256 !important;
                        }
                        QScrollBar::add-line:vertical {
                            height: 0px !important;
                            width: 0px !important;
                            subcontrol-position: bottom !important;
                            subcontrol-origin: margin !important;
                            background: transparent !important;
                            border: none !important;
                        }
                        QScrollBar::sub-line:vertical {
                            height: 0px !important;
                            width: 0px !important;
                            subcontrol-position: top !important;
                            subcontrol-origin: margin !important;
                            background: transparent !important;
                            border: none !important;
                        }
                        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                            width: 0px !important;
                            height: 0px !important;
                            background: transparent !important;
                            border: none !important;
                        }
                        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                            background: transparent !important;
                            border: none !important;
                        }
                    """)
            except Exception:
                pass

def main():
    app = QApplication(sys.argv)
    
    # Force Fusion style for consistent theming
    app.setStyle('Fusion')
    print("✅ Set application style to Fusion")
    print("🎯 Testing ComboBox scrollbars instead of arrows")
    print("📜 ComboBoxes will have many items to force scrollbar display")
    
    # Create and show the test window
    window = ScrollbarTestWindow()
    window.show()
    
    print("\n🚀 Scrollbar test window created.")
    print("📋 Each ComboBox has 25-50 items to force scrollbar appearance.")
    print("🔍 Look for scrollbars instead of up/down arrows in dropdowns.")
    print("🎨 Scrollbars should be themed with orange/red colors.")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
