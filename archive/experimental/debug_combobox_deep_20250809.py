# ARCHIVED 2025-08-09: ComboBox debugging from theme fixes
# Original location: debug_combobox_deep.py
# Archive category: experimental
# ========================================


#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QWheelEvent

class DebugNoWheelComboBox(QComboBox):
    """A QComboBox with extensive debugging of popup behavior."""

    def __init__(self, parent=None, name="DebugCombo"):
        super().__init__(parent)
        self.debug_name = name
        self.main_window = None
        self.popup_count = 0
        print(f"🔧 {self.debug_name}: Created")
        
    def set_main_window(self, main_window):
        """Set reference to main window for theme access."""
        self.main_window = main_window
        print(f"🔧 {self.debug_name}: Main window reference set")

    def wheelEvent(self, event: QWheelEvent):
        """Completely ignore all wheel events."""
        event.ignore()
        print(f"🔧 {self.debug_name}: Wheel event ignored")
        
    def showPopup(self):
        """Override showPopup with extensive debugging."""
        self.popup_count += 1
        print(f"\n🚀 {self.debug_name}: showPopup() called - Count: {self.popup_count}")
        
        # Call the original showPopup
        super().showPopup()
        print(f"✅ {self.debug_name}: super().showPopup() completed")
        
        # Debug the popup view
        popup_view = self.view()
        if popup_view:
            print(f"📋 {self.debug_name}: Popup view found: {type(popup_view).__name__}")
            print(f"📋 {self.debug_name}: Popup view visible: {popup_view.isVisible()}")
            print(f"📋 {self.debug_name}: Popup view styleSheet before: '{popup_view.styleSheet()[:100]}...'")
            
            # Check parent hierarchy
            parent = popup_view.parent()
            if parent:
                print(f"👨‍👩‍👧‍👦 {self.debug_name}: Parent found: {type(parent).__name__}")
                print(f"👨‍👩‍👧‍👦 {self.debug_name}: Parent styleSheet: '{parent.styleSheet()[:50]}...'")
                
                grandparent = parent.parent()
                if grandparent:
                    print(f"👴 {self.debug_name}: Grandparent found: {type(grandparent).__name__}")
        
        # Apply theme styling
        self.apply_popup_styling()
        
        # Check styling after application
        if popup_view:
            print(f"📋 {self.debug_name}: Popup view styleSheet after: '{popup_view.styleSheet()[:100]}...'")
        
    def apply_popup_styling(self):
        """Apply proper styling to the popup view with debugging."""
        print(f"🎨 {self.debug_name}: apply_popup_styling() called")
        
        popup_view = self.view()
        if not popup_view:
            print(f"❌ {self.debug_name}: No popup view found")
            return
            
        # Force dark theme styling
        style = """
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
        """
        
        print(f"🎨 {self.debug_name}: Setting styleSheet on popup view")
        popup_view.setStyleSheet(style)
        print(f"✅ {self.debug_name}: StyleSheet applied to popup view")
        
        # Also force background on popup frame if it exists
        parent = popup_view.parent()
        if parent and hasattr(parent, 'setStyleSheet'):
            print(f"🎨 {self.debug_name}: Setting styleSheet on parent frame")
            parent.setStyleSheet("""
                QFrame {
                    background-color: #2a2a2a !important;
                    border: 1px solid #EE8980 !important;
                    border-radius: 4px !important;
                }
            """)
            print(f"✅ {self.debug_name}: StyleSheet applied to parent frame")
    
    def hidePopup(self):
        """Override hidePopup to debug when popup is hidden."""
        print(f"🔽 {self.debug_name}: hidePopup() called")
        super().hidePopup()
        print(f"✅ {self.debug_name}: hidePopup() completed")

class ComboBoxDebugWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.monitored_combos = []
        self.monitor_cycle = 0
        self.initUI()
        self.setup_monitoring()
        
    def initUI(self):
        self.setWindowTitle('ComboBox DEEP DEBUG - Event Tracing')
        self.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        # Add test label
        label = QLabel('DEEP DEBUG: Watch console for detailed popup behavior:')
        layout.addWidget(label)
        
        # Create debug ComboBoxes
        debug_combo1 = DebugNoWheelComboBox(name="Combo1")
        debug_combo1.addItems(['Debug Option 1', 'Debug Option 2', 'Debug Option 3', 'Debug Option 4'])
        debug_combo1.set_main_window(self)
        layout.addWidget(debug_combo1)
        
        debug_combo2 = DebugNoWheelComboBox(name="Combo2")
        debug_combo2.addItems(['Debug Choice A', 'Debug Choice B', 'Debug Choice C', 'Debug Choice D'])
        debug_combo2.set_main_window(self)
        layout.addWidget(debug_combo2)
        
        # Create a regular ComboBox with debugging wrapper
        regular_combo = QComboBox()
        regular_combo.addItems(['Regular 1', 'Regular 2', 'Regular 3', 'Regular 4'])
        layout.addWidget(regular_combo)
        
        # Store combos for monitoring
        self.monitored_combos = [debug_combo1, debug_combo2, regular_combo]
        
        # Wrap regular ComboBox with debugging
        self.wrap_regular_combo_with_debug(regular_combo, "RegularCombo")
        
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
    
    def wrap_regular_combo_with_debug(self, combo, name):
        """Add debugging wrapper to a regular ComboBox."""
        print(f"🔧 {name}: Wrapping with debug functionality")
        
        original_showPopup = combo.showPopup
        original_hidePopup = combo.hidePopup
        popup_count = [0]  # Use list to make it mutable in closure
        
        def debug_showPopup():
            popup_count[0] += 1
            print(f"\n🚀 {name}: showPopup() called - Count: {popup_count[0]}")
            
            original_showPopup()
            print(f"✅ {name}: original showPopup() completed")
            
            # Debug the popup view
            popup_view = combo.view()
            if popup_view:
                print(f"📋 {name}: Popup view found: {type(popup_view).__name__}")
                print(f"📋 {name}: Popup view visible: {popup_view.isVisible()}")
                print(f"📋 {name}: Popup view styleSheet before: '{popup_view.styleSheet()[:100]}...'")
                
                # Apply styling
                print(f"🎨 {name}: Applying dark theme styling")
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
                print(f"✅ {name}: StyleSheet applied")
                print(f"📋 {name}: Popup view styleSheet after: '{popup_view.styleSheet()[:100]}...'")
        
        def debug_hidePopup():
            print(f"🔽 {name}: hidePopup() called")
            original_hidePopup()
            print(f"✅ {name}: hidePopup() completed")
        
        combo.showPopup = debug_showPopup
        combo.hidePopup = debug_hidePopup
    
    def setup_monitoring(self):
        """Set up continuous monitoring of ComboBox popups."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_popup_styling)
        self.monitor_timer.start(200)  # Check every 200ms to reduce spam
        print("✅ Started continuous popup monitoring with debugging")
    
    def monitor_popup_styling(self):
        """Continuously monitor and debug popup styling for all ComboBoxes."""
        self.monitor_cycle += 1
        
        for i, combo in enumerate(self.monitored_combos):
            try:
                popup_view = combo.view()
                # Only log if popup is actually visible
                if popup_view and popup_view.isVisible():
                    if self.monitor_cycle % 5 == 0:  # Log every 5th cycle to reduce spam
                        print(f"🔍 Monitor Cycle {self.monitor_cycle}: Combo{i+1} popup visible, re-applying styling")
                    
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
            except Exception as e:
                if self.monitor_cycle % 20 == 0:  # Log errors occasionally
                    print(f"⚠️ Monitor error for combo {i+1}: {e}")

def main():
    app = QApplication(sys.argv)
    
    # Force Fusion style for consistent theming
    app.setStyle('Fusion')
    print("✅ Set application style to Fusion")
    print("🔍 Starting DEEP DEBUG mode - watch console output closely")
    print("📝 Click dropdowns multiple times and observe the detailed logs")
    
    # Create and show the test window
    window = ComboBoxDebugWindow()
    window.show()
    
    print("\n🚀 Deep debug window created.")
    print("📋 Console will show detailed popup behavior.")
    print("🔄 Monitor will log every 5 cycles to reduce spam.")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
