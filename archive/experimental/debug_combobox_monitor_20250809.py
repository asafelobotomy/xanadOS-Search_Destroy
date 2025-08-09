# ARCHIVED 2025-08-09: ComboBox debugging from theme fixes
# Original location: debug_combobox_monitor.py
# Archive category: experimental
# ========================================


#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QWheelEvent

class EnhancedNoWheelComboBox(QComboBox):
    """A QComboBox with continuous popup styling enforcement."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None
        
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
            
        # Force dark theme styling
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

class ComboBoxTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.monitored_combos = []
        self.initUI()
        self.setup_monitoring()
        
    def initUI(self):
        self.setWindowTitle('ComboBox Debug Test - ENHANCED MONITORING')
        self.setGeometry(300, 300, 450, 350)
        
        layout = QVBoxLayout()
        
        # Add test label
        label = QLabel('Testing ENHANCED ComboBox Styling with Continuous Monitoring:')
        layout.addWidget(label)
        
        # Create regular ComboBox
        regular_combo = QComboBox()
        regular_combo.addItems(['Enhanced Option 1', 'Enhanced Option 2', 'Enhanced Option 3', 'Enhanced Option 4'])
        layout.addWidget(regular_combo)
        
        # Create Enhanced NoWheel ComboBox  
        enhanced_combo = EnhancedNoWheelComboBox()
        enhanced_combo.addItems(['NoWheel Enhanced 1', 'NoWheel Enhanced 2', 'NoWheel Enhanced 3', 'NoWheel Enhanced 4'])
        enhanced_combo.set_main_window(self)
        layout.addWidget(enhanced_combo)
        
        # Store combos for monitoring
        self.monitored_combos = [regular_combo, enhanced_combo]
        
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
    
    def setup_monitoring(self):
        """Set up continuous monitoring of ComboBox popups."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_popup_styling)
        self.monitor_timer.start(50)  # Check every 50ms
        print("✅ Started continuous popup monitoring")
    
    def monitor_popup_styling(self):
        """Continuously monitor and enforce popup styling for all ComboBoxes."""
        for combo in self.monitored_combos:
            try:
                popup_view = combo.view()
                # Only apply styling if popup is actually visible
                if popup_view and popup_view.isVisible():
                    # Re-apply styling to combat any overrides
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
                    
                    # Also fix parent containers
                    parent = popup_view.parent()
                    if parent and hasattr(parent, 'setStyleSheet'):
                        parent.setStyleSheet("""
                            QFrame {
                                background-color: #2a2a2a !important;
                                border: 1px solid #EE8980 !important;
                                border-radius: 4px !important;
                            }
                        """)
            except Exception:
                # Ignore errors from deleted widgets
                pass

def main():
    app = QApplication(sys.argv)
    
    # Force Fusion style for consistent theming
    app.setStyle('Fusion')
    print("✅ Set application style to Fusion")
    
    # Create and show the test window
    window = ComboBoxTestWindow()
    window.show()
    
    print("Enhanced debug test window created.")
    print("Click on the dropdowns multiple times to test continuous styling enforcement.")
    print("Both dropdowns should maintain dark backgrounds even after multiple opens.")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
