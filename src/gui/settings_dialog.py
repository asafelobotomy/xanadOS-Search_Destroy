from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QGroupBox, QPushButton, QCheckBox,
                             QSpinBox, QFormLayout, QMessageBox, QWidget)
from PyQt6.QtCore import pyqtSignal

from ..utils.config import load_config, save_config


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.setWindowTitle("Settings - S&D Search & Destroy")
        self.setModal(True)
        self.resize(600, 400)
        
        self.init_ui()
        self.load_current_settings()
        
        # Apply the same theme as the parent window
        if parent and hasattr(parent, 'config') and 'theme' in parent.config:
            self.apply_theme(parent.config['theme'])
        else:
            self.apply_theme('dark')  # Default to dark theme
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget for different setting categories
        self.tab_widget = QTabWidget()
        
        self.create_scan_settings_tab()
        self.create_general_settings_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.ok_btn)
        
        layout.addLayout(buttons_layout)
        
    def show_themed_message_box(self, msg_type, title, text):
        """Show a message box with proper theming based on current theme."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        # Set message type
        if msg_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif msg_type == "information":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif msg_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Get current theme from parent or default to dark
        current_theme = 'dark'
        if self.parent() and hasattr(self.parent(), 'current_theme'):
            current_theme = self.parent().current_theme
        
        # Apply theme-specific styling
        if current_theme == 'dark':
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2b2b2b;
                    color: #FFCDAA;
                    font-size: 12px;
                    font-weight: 500;
                }
                QMessageBox QLabel {
                    color: #FFCDAA;
                    font-weight: 600;
                    padding: 10px;
                }
                QMessageBox QPushButton {
                    background-color: #404040;
                    border: 2px solid #EE8980;
                    border-radius: 5px;
                    padding: 8px 16px;
                    color: #FFCDAA;
                    font-weight: 600;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #505050;
                    border-color: #F14666;
                    color: #ffffff;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #606060;
                }
                QMessageBox QPushButton:default {
                    background-color: #9CB898;
                    border-color: #9CB898;
                    color: #2b2b2b;
                    font-weight: 700;
                }
                QMessageBox QPushButton:default:hover {
                    background-color: #B2CEB0;
                    border-color: #B2CEB0;
                }
            """)
        else:
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #fefefe;
                    color: #2c2c2c;
                    font-size: 12px;
                    font-weight: 500;
                }
                QMessageBox QLabel {
                    color: #2c2c2c;
                    font-weight: 600;
                    padding: 10px;
                }
                QMessageBox QPushButton {
                    background-color: #F8D49B;
                    border: 1px solid #F8BC9B;
                    border-radius: 6px;
                    padding: 8px 16px;
                    color: #2c2c2c;
                    font-weight: 600;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #F8BC9B;
                    border-color: #F89B9B;
                    color: #1a1a1a;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #F89B9B;
                    border-color: #75BDE0;
                }
                QMessageBox QPushButton:default {
                    background-color: #75BDE0;
                    border: 2px solid #75BDE0;
                    color: #ffffff;
                    font-weight: 700;
                }
                QMessageBox QPushButton:default:hover {
                    background-color: #5AADD4;
                    border-color: #5AADD4;
                }
            """)
        
        return msg_box.exec()
        
    def create_scan_settings_tab(self):
        scan_widget = QWidget()
        layout = QVBoxLayout(scan_widget)
        
        # Scan options group
        scan_group = QGroupBox("Scan Options")
        scan_form = QFormLayout(scan_group)
        
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 16)
        self.max_threads_spin.setValue(4)
        scan_form.addRow("Max Threads:", self.max_threads_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 3600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSuffix(" seconds")
        scan_form.addRow("Scan Timeout:", self.timeout_spin)
        
        self.scan_archives_cb = QCheckBox("Scan Archive Files")
        self.scan_archives_cb.setChecked(True)
        scan_form.addRow(self.scan_archives_cb)
        
        self.follow_symlinks_cb = QCheckBox("Follow Symbolic Links")
        self.follow_symlinks_cb.setChecked(False)
        scan_form.addRow(self.follow_symlinks_cb)
        
        layout.addWidget(scan_group)
        layout.addStretch()
        
        self.tab_widget.addTab(scan_widget, "Scanning")
        
    def create_general_settings_tab(self):
        general_widget = QWidget()
        layout = QVBoxLayout(general_widget)
        
        # UI options group
        ui_group = QGroupBox("User Interface")
        ui_form = QFormLayout(ui_group)
        
        self.minimize_to_tray_cb = QCheckBox("Minimize to System Tray")
        self.minimize_to_tray_cb.setChecked(True)
        ui_form.addRow(self.minimize_to_tray_cb)
        
        self.show_notifications_cb = QCheckBox("Show Notifications")
        self.show_notifications_cb.setChecked(True)
        ui_form.addRow(self.show_notifications_cb)
        
        self.auto_update_cb = QCheckBox("Auto-update Virus Definitions")
        self.auto_update_cb.setChecked(True)
        ui_form.addRow(self.auto_update_cb)
        
        layout.addWidget(ui_group)
        layout.addStretch()
        
        self.tab_widget.addTab(general_widget, "General")
        
    def load_current_settings(self):
        """Load current settings from config"""
        try:
            # Scan settings
            scan_settings = self.config.get('scan_settings', {})
            self.max_threads_spin.setValue(scan_settings.get('max_threads', 4))
            self.timeout_spin.setValue(scan_settings.get('timeout_seconds', 300))
            
            # UI settings
            ui_settings = self.config.get('ui_settings', {})
            self.minimize_to_tray_cb.setChecked(ui_settings.get('minimize_to_tray', True))
            self.show_notifications_cb.setChecked(ui_settings.get('show_notifications', True))
            
            # Security settings
            security_settings = self.config.get('security_settings', {})
            self.auto_update_cb.setChecked(security_settings.get('auto_update_definitions', True))
            
            # Advanced settings
            advanced_settings = self.config.get('advanced_settings', {})
            self.scan_archives_cb.setChecked(advanced_settings.get('scan_archives', True))
            self.follow_symlinks_cb.setChecked(advanced_settings.get('follow_symlinks', False))
            
        except Exception as e:
            self.show_themed_message_box("warning", "Warning", f"Could not load settings: {str(e)}")
            
    def accept(self):
        """Save settings and close dialog"""
        try:
            # Update config with new values
            self.config['scan_settings']['max_threads'] = self.max_threads_spin.value()
            self.config['scan_settings']['timeout_seconds'] = self.timeout_spin.value()
            
            self.config['ui_settings']['minimize_to_tray'] = self.minimize_to_tray_cb.isChecked()
            self.config['ui_settings']['show_notifications'] = self.show_notifications_cb.isChecked()
            
            self.config['security_settings']['auto_update_definitions'] = self.auto_update_cb.isChecked()
            
            self.config['advanced_settings']['scan_archives'] = self.scan_archives_cb.isChecked()
            self.config['advanced_settings']['follow_symlinks'] = self.follow_symlinks_cb.isChecked()
            
            # Save config to file
            save_config(self.config)
            
            self.settings_changed.emit()
            self.show_themed_message_box("information", "Settings", "Settings saved successfully!")
            
        except Exception as e:
            self.show_themed_message_box("warning", "Error", f"Could not save settings: {str(e)}")
            return
            
        super().accept()

    def apply_theme(self, theme_name):
        """Apply the specified theme to the settings dialog."""
        if theme_name == 'dark':
            self.apply_dark_theme()
        elif theme_name == 'light':
            self.apply_light_theme()
        else:  # system or fallback
            self.apply_light_theme()

    def apply_dark_theme(self):
        """Apply dark theme styling using Strawberry color palette for optimal readability."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #FFCDAA;
                font-size: 12px;
                font-weight: 500;
            }
            
            QGroupBox {
                font-weight: 600;
                border: 2px solid #EE8980;
                border-radius: 6px;
                margin-top: 1em;
                padding-top: 0.6em;
                background-color: #353535;
                color: #FFCDAA;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #F14666;
                font-weight: 700;
                font-size: 13px;
            }
            
            QPushButton {
                background-color: #404040;
                border: 1px solid #EE8980;
                border-radius: 5px;
                padding: 8px 14px;
                min-width: 80px;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #505050;
                border-color: #F14666;
                color: #ffffff;
            }
            
            QPushButton:pressed {
                background-color: #606060;
                border-color: #F14666;
            }
            
            QPushButton:default {
                background-color: #9CB898;
                border: 2px solid #9CB898;
                color: #2b2b2b;
                font-weight: 700;
            }
            
            QPushButton:default:hover {
                background-color: #B2CEB0;
                border-color: #B2CEB0;
            }
            
            QTabWidget::pane {
                border: 2px solid #EE8980;
                border-radius: 6px;
                top: -1px;
                background-color: #353535;
            }
            
            QTabBar::tab {
                background-color: #404040;
                border: 1px solid #EE8980;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 8px 14px;
                margin-right: 3px;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QTabBar::tab:selected {
                background-color: #353535;
                border-bottom: 2px solid #353535;
                border-left: 2px solid #F14666;
                border-right: 2px solid #F14666;
                border-top: 2px solid #F14666;
                color: #F14666;
                font-weight: 700;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #505050;
                border-color: #F14666;
                color: #ffffff;
            }
            
            QLabel {
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QLineEdit, QSpinBox, QComboBox {
                border: 2px solid #EE8980;
                border-radius: 5px;
                background-color: #404040;
                color: #FFCDAA;
                padding: 6px;
                font-weight: 500;
                selection-background-color: #F14666;
                selection-color: #ffffff;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #F14666;
                background-color: #454545;
            }
            
            QCheckBox {
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #EE8980;
                border-radius: 4px;
                background-color: #404040;
            }
            
            QCheckBox::indicator:hover {
                border-color: #F14666;
                background-color: #454545;
            }
            
            QCheckBox::indicator:checked {
                background-color: #9CB898;
                border-color: #9CB898;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik04LjUgMUwzLjUgNkwxLjUgNCIgc3Ryb2tlPSIjMmIyYjJiIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4=);
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: #EE8980;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                width: 25px;
            }
            
            QComboBox::drop-down:hover {
                background-color: #F14666;
            }
            
            QComboBox::down-arrow {
                border: 3px solid #FFCDAA;
                border-top: none;
                border-right: none;
                width: 8px;
                height: 8px;
                margin: 2px;
            }
            
            QComboBox QAbstractItemView {
                border: 2px solid #F14666;
                border-radius: 4px;
                background-color: #404040;
                color: #FFCDAA;
                selection-background-color: #EE8980;
                selection-color: #ffffff;
            }
        """)

    def apply_light_theme(self):
        """Apply light theme styling using Sunrise color palette for optimal readability."""
        self.setStyleSheet("""
            QDialog {
                background-color: #fefefe;
                color: #2c2c2c;
                font-size: 12px;
                font-weight: 500;
            }
            
            QGroupBox {
                font-weight: 600;
                border: 2px solid #75BDE0;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 0.8em;
                background-color: #ffffff;
                color: #2c2c2c;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #75BDE0;
                font-weight: 700;
                font-size: 13px;
            }
            
            QPushButton {
                background-color: #F8D49B;
                border: 1px solid #F8BC9B;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QPushButton:hover {
                background-color: #F8BC9B;
                border-color: #F89B9B;
                color: #1a1a1a;
            }
            
            QPushButton:pressed {
                background-color: #F89B9B;
                border-color: #75BDE0;
            }
            
            QPushButton:default {
                background-color: #75BDE0;
                border: 2px solid #75BDE0;
                color: #ffffff;
                font-weight: 700;
            }
            
            QPushButton:default:hover {
                background-color: #5AADD4;
                border-color: #5AADD4;
            }
            
            QTabWidget::pane {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                top: -1px;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #F8D49B;
                border: 1px solid #F8BC9B;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 3px;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 2px solid #ffffff;
                border-left: 2px solid #75BDE0;
                border-right: 2px solid #75BDE0;
                border-top: 2px solid #75BDE0;
                color: #75BDE0;
                font-weight: 700;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #F8BC9B;
                color: #1a1a1a;
            }
            
            QLabel {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QLineEdit, QSpinBox, QComboBox {
                border: 2px solid #F8D49B;
                border-radius: 5px;
                background-color: #ffffff;
                color: #2c2c2c;
                padding: 6px;
                font-weight: 500;
                font-size: 11px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #75BDE0;
                background-color: #fafafa;
            }
            
            QCheckBox {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #F8D49B;
                border-radius: 4px;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:hover {
                border-color: #75BDE0;
                background-color: #fafafa;
            }
            
            QCheckBox::indicator:checked {
                background-color: #75BDE0;
                border-color: #75BDE0;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik04LjUgMUwzLjUgNkwxLjUgNCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: #F8BC9B;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                width: 25px;
            }
            
            QComboBox::drop-down:hover {
                background-color: #F89B9B;
            }
            
            QComboBox::down-arrow {
                border: 3px solid #2c2c2c;
                border-top: none;
                border-right: none;
                width: 8px;
                height: 8px;
                margin: 2px;
            }
            
            QComboBox QAbstractItemView {
                border: 2px solid #75BDE0;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c2c2c;
                selection-background-color: #F8D49B;
                selection-color: #2c2c2c;
            }
        """)
