from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QProgressBar, QTextEdit,
                             QFileDialog, QRadioButton, QButtonGroup, QCheckBox,
                             QComboBox, QSpinBox, QFormLayout, QSplitter,
                             QListWidget, QListWidgetItem, QMessageBox, QWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from .scan_thread import ScanThread
from ..scanner.file_scanner import FileScanner
from ..utils.config import load_config, save_config


class ScanDialog(QDialog):
    scan_started = pyqtSignal()
    scan_completed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Scan - S&D Search & Destroy")
        self.setModal(True)
        self.resize(800, 600)
        
        self.config = load_config()
        self.scanner = FileScanner()
        self.current_scan_thread = None
        self.scan_results = None
        
        self.init_ui()
        
        # Apply the same theme as the parent window
        if parent and hasattr(parent, 'config') and 'theme' in parent.config:
            self.apply_theme(parent.config['theme'])
        else:
            self.apply_theme('dark')  # Default to dark theme
        
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
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create splitter for two-column layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Scan configuration
        left_panel = self.create_scan_config_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Scan progress and results
        right_panel = self.create_scan_results_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 450])
        layout.addWidget(splitter)
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.start_btn = QPushButton("Start Scan")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self.start_scan)
        
        self.stop_btn = QPushButton("Stop Scan")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
    def create_scan_config_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scan type selection
        type_group = QGroupBox("Scan Type")
        type_layout = QVBoxLayout(type_group)
        
        self.scan_type_group = QButtonGroup()
        
        self.quick_scan_rb = QRadioButton("Quick Scan")
        self.quick_scan_rb.setChecked(True)
        self.quick_scan_rb.setToolTip("Scan common system locations and user directories")
        
        self.full_scan_rb = QRadioButton("Full System Scan")
        self.full_scan_rb.setToolTip("Scan entire system (may take several hours)")
        
        self.custom_scan_rb = QRadioButton("Custom Scan")
        self.custom_scan_rb.setToolTip("Scan specific files or directories")
        
        self.scan_type_group.addButton(self.quick_scan_rb, 0)
        self.scan_type_group.addButton(self.full_scan_rb, 1)
        self.scan_type_group.addButton(self.custom_scan_rb, 2)
        
        type_layout.addWidget(self.quick_scan_rb)
        type_layout.addWidget(self.full_scan_rb)
        type_layout.addWidget(self.custom_scan_rb)
        
        layout.addWidget(type_group)
        
        # Custom scan targets
        self.targets_group = QGroupBox("Scan Targets")
        targets_layout = QVBoxLayout(self.targets_group)
        
        targets_buttons_layout = QHBoxLayout()
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file_target)
        add_dir_btn = QPushButton("Add Directory")
        add_dir_btn.clicked.connect(self.add_directory_target)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_target)
        
        targets_buttons_layout.addWidget(add_file_btn)
        targets_buttons_layout.addWidget(add_dir_btn)
        targets_buttons_layout.addWidget(remove_btn)
        targets_buttons_layout.addStretch()
        
        targets_layout.addLayout(targets_buttons_layout)
        
        self.targets_list = QListWidget()
        self.targets_list.setMaximumHeight(120)
        targets_layout.addWidget(self.targets_list)
        
        layout.addWidget(self.targets_group)
        
        # Scan options
        options_group = QGroupBox("Scan Options")
        options_layout = QFormLayout(options_group)
        
        self.scan_archives_cb = QCheckBox("Scan inside archives")
        self.scan_archives_cb.setChecked(True)
        
        self.scan_emails_cb = QCheckBox("Scan email files")
        self.scan_emails_cb.setChecked(True)
        
        self.scan_office_cb = QCheckBox("Scan Office documents")
        self.scan_office_cb.setChecked(True)
        
        self.heuristic_scan_cb = QCheckBox("Enable heuristic scanning")
        self.heuristic_scan_cb.setChecked(False)
        
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 1000)
        self.max_file_size_spin.setValue(100)
        self.max_file_size_spin.setSuffix(" MB")
        
        self.scan_timeout_spin = QSpinBox()
        self.scan_timeout_spin.setRange(60, 3600)
        self.scan_timeout_spin.setValue(300)
        self.scan_timeout_spin.setSuffix(" seconds")
        
        options_layout.addRow("", self.scan_archives_cb)
        options_layout.addRow("", self.scan_emails_cb)
        options_layout.addRow("", self.scan_office_cb)
        options_layout.addRow("", self.heuristic_scan_cb)
        options_layout.addRow("Max file size:", self.max_file_size_spin)
        options_layout.addRow("Timeout per file:", self.scan_timeout_spin)
        
        layout.addWidget(options_group)
        
        # Actions on threats
        actions_group = QGroupBox("Action on Threats")
        actions_layout = QVBoxLayout(actions_group)
        
        self.action_group = QButtonGroup()
        
        self.report_only_rb = QRadioButton("Report only")
        self.report_only_rb.setChecked(True)
        
        self.quarantine_rb = QRadioButton("Quarantine infected files")
        self.delete_rb = QRadioButton("Delete infected files")
        
        self.action_group.addButton(self.report_only_rb, 0)
        self.action_group.addButton(self.quarantine_rb, 1)
        self.action_group.addButton(self.delete_rb, 2)
        
        actions_layout.addWidget(self.report_only_rb)
        actions_layout.addWidget(self.quarantine_rb)
        actions_layout.addWidget(self.delete_rb)
        
        layout.addWidget(actions_group)
        
        # Connect signals for enabling/disabling custom targets
        self.scan_type_group.buttonToggled.connect(self.on_scan_type_changed)
        self.on_scan_type_changed()  # Initial state
        
        layout.addStretch()
        return widget
        
    def create_scan_results_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Progress section
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.status_label = QLabel("Ready to start scan")
        self.status_label.setWordWrap(True)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgressBar")
        
        self.scan_stats_label = QLabel("Files scanned: 0 | Threats found: 0 | Time elapsed: 00:00")
        self.scan_stats_label.setFont(QFont("monospace", 9))
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.scan_stats_label)
        
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setObjectName("resultsText")
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("monospace", 10))
        
        results_layout.addWidget(self.results_text)
        layout.addWidget(results_group)
        
        return widget
        
    def apply_theme(self, theme_name):
        """Apply the specified theme to the scan dialog."""
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
            
            QPushButton:disabled {
                background-color: #404040;
                color: #666666;
                border-color: #666666;
            }
            
            QProgressBar {
                border: 2px solid #EE8980;
                border-radius: 5px;
                text-align: center;
                height: 22px;
                background-color: #404040;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QProgressBar::chunk {
                background-color: #9CB898;
                width: 2px;
                border-radius: 3px;
            }
            
            QTextEdit {
                border: 2px solid #EE8980;
                border-radius: 5px;
                background-color: #404040;
                color: #FFCDAA;
                font-weight: 500;
                selection-background-color: #F14666;
                selection-color: #ffffff;
            }
            
            QTextEdit:focus {
                border-color: #F14666;
                background-color: #454545;
            }
            
            QListWidget {
                border: 2px solid #EE8980;
                border-radius: 5px;
                background-color: #404040;
                color: #FFCDAA;
                font-weight: 500;
                alternate-background-color: #454545;
                selection-background-color: #F14666;
                selection-color: #ffffff;
            }
            
            QListWidget:focus {
                border-color: #F14666;
            }
            
            QRadioButton {
                color: #FFCDAA;
                font-weight: 600;
                spacing: 10px;
                margin: 5px;
            }
            
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #EE8980;
                border-radius: 9px;
                background-color: #404040;
            }
            
            QRadioButton::indicator:hover {
                border-color: #F14666;
                background-color: #454545;
            }
            
            QRadioButton::indicator:checked {
                background-color: #9CB898;
                border-color: #9CB898;
            }
            
            QCheckBox {
                color: #FFCDAA;
                font-weight: 600;
                spacing: 10px;
                margin: 3px;
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
            
            QLabel {
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QSpinBox, QComboBox {
                border: 2px solid #EE8980;
                border-radius: 5px;
                background-color: #404040;
                color: #FFCDAA;
                padding: 6px;
                font-weight: 500;
                selection-background-color: #F14666;
                selection-color: #ffffff;
            }
            
            QSpinBox:focus, QComboBox:focus {
                border-color: #F14666;
                background-color: #454545;
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
            
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999999;
                border-color: #dddddd;
            }
            
            QProgressBar {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                text-align: center;
                height: 24px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QProgressBar::chunk {
                background-color: #75BDE0;
                width: 1px;
                border-radius: 4px;
            }
            
            QTextEdit {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 400;
                font-size: 11px;
                padding: 5px;
            }
            
            QTextEdit:focus {
                border-color: #75BDE0;
            }
            
            QListWidget {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 500;
                font-size: 11px;
                alternate-background-color: #F8F8F8;
                padding: 3px;
            }
            
            QListWidget:focus {
                border-color: #75BDE0;
            }
            
            QListWidget::item {
                padding: 4px;
                border-radius: 3px;
            }
            
            QListWidget::item:selected {
                background-color: #F8D49B;
                color: #2c2c2c;
            }
            
            QRadioButton {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
                spacing: 10px;
                margin: 6px;
            }
            
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #F8D49B;
                border-radius: 9px;
                background-color: #ffffff;
            }
            
            QRadioButton::indicator:hover {
                border-color: #75BDE0;
                background-color: #fafafa;
            }
            
            QRadioButton::indicator:checked {
                background-color: #75BDE0;
                border-color: #75BDE0;
            }
            
            QCheckBox {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
                spacing: 10px;
                margin: 4px;
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
            
            QLabel {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QSpinBox, QComboBox {
                border: 2px solid #F8D49B;
                border-radius: 5px;
                background-color: #ffffff;
                color: #2c2c2c;
                padding: 6px;
                font-weight: 500;
                font-size: 11px;
            }
            
            QSpinBox:focus, QComboBox:focus {
                border-color: #75BDE0;
                background-color: #fafafa;
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
            
            /* Scan results text styling with Sunrise palette */
            #resultsText {
                font-weight: 400;
                line-height: 1.5;
                color: #2c2c2c;
                background-color: #ffffff;
                border: 2px solid #F8D49B;
                border-radius: 6px;
                padding: 8px;
                font-family: 'monospace', 'Consolas', 'Courier New';
                font-size: 11px;
            }
            
            #resultsText:focus {
                border-color: #75BDE0;
                background-color: #fafafa;
            }
        """)
        
    def on_scan_type_changed(self):
        """Enable/disable custom targets based on scan type"""
        is_custom = self.custom_scan_rb.isChecked()
        self.targets_group.setEnabled(is_custom)
        
        if not is_custom:
            self.targets_list.clear()
            
    def add_file_target(self):
        """Add a file to scan targets"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select files to scan")
        for file_path in files:
            item = QListWidgetItem(f"📄 {file_path}")
            item.setData(Qt.ItemDataRole.UserRole, ('file', file_path))
            self.targets_list.addItem(item)
            
    def add_directory_target(self):
        """Add a directory to scan targets"""
        directory = QFileDialog.getExistingDirectory(self, "Select directory to scan")
        if directory:
            item = QListWidgetItem(f"📁 {directory}")
            item.setData(Qt.ItemDataRole.UserRole, ('directory', directory))
            self.targets_list.addItem(item)
            
    def remove_target(self):
        """Remove selected target from list"""
        current_row = self.targets_list.currentRow()
        if current_row >= 0:
            self.targets_list.takeItem(current_row)
            
    def get_scan_targets(self):
        """Get list of paths to scan based on scan type"""
        if self.quick_scan_rb.isChecked():
            import os
            return [
                os.path.expanduser("~"),
                "/tmp",
                "/var/tmp"
            ]
        elif self.full_scan_rb.isChecked():
            return ["/"]
        else:  # Custom scan
            targets = []
            for i in range(self.targets_list.count()):
                item = self.targets_list.item(i)
                target_type, path = item.data(Qt.ItemDataRole.UserRole)
                targets.append(path)
            return targets
            
    def get_scan_options(self):
        """Get scan options based on UI settings"""
        return {
            'scan_archives': self.scan_archives_cb.isChecked(),
            'scan_emails': self.scan_emails_cb.isChecked(),
            'scan_office': self.scan_office_cb.isChecked(),
            'heuristic_scan': self.heuristic_scan_cb.isChecked(),
            'max_file_size_mb': self.max_file_size_spin.value(),
            'timeout_seconds': self.scan_timeout_spin.value(),
            'action_on_threats': self.action_group.checkedId()
        }
        
    def start_scan(self):
        """Start the scan process"""
        targets = self.get_scan_targets()
        
        if not targets:
            self.show_themed_message_box("warning", "Warning", "Please select at least one target to scan.")
            return
            
        # Validate custom targets exist
        if self.custom_scan_rb.isChecked():
            import os
            missing_targets = [t for t in targets if not os.path.exists(t)]
            if missing_targets:
                self.show_themed_message_box("warning", "Warning", 
                                  f"The following targets do not exist:\n" + 
                                  "\n".join(missing_targets))
                return
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        self.status_label.setText("Initializing scan...")
        
        # Configure scanner with options
        options = self.get_scan_options()
        # Apply scan options to scanner
        if hasattr(self.scanner, 'set_scan_options'):
            self.scanner.set_scan_options(options)
        
        # Start scan thread
        self.current_scan_thread = ScanThread(self.scanner, targets[0])  # For now, scan first target
        self.current_scan_thread.progress_updated.connect(self.progress_bar.setValue)
        self.current_scan_thread.status_updated.connect(self.status_label.setText)
        self.current_scan_thread.scan_completed.connect(self.on_scan_completed)
        self.current_scan_thread.start()
        
        # Start timer for updating stats
        self.scan_start_time = QTimer()
        self.scan_start_time.timeout.connect(self.update_scan_stats)
        self.scan_start_time.start(1000)  # Update every second
        
        self.scan_started.emit()
        
    def stop_scan(self):
        """Stop the current scan"""
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            self.current_scan_thread.terminate()
            self.on_scan_completed({'status': 'cancelled'})
            
    def on_scan_completed(self, result):
        """Handle scan completion"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        
        if hasattr(self, 'scan_start_time'):
            self.scan_start_time.stop()
            
        self.scan_results = result
        
        if 'error' in result:
            self.status_label.setText(f"Scan failed: {result['error']}")
            self.results_text.setText(f"Scan Error:\n{result['error']}")
        elif result.get('status') == 'cancelled':
            self.status_label.setText("Scan cancelled by user")
            self.results_text.setText("Scan was cancelled.")
        else:
            self.status_label.setText("Scan completed successfully")
            self.display_scan_results(result)
            
        self.scan_completed.emit(result)
        
    def display_scan_results(self, result):
        """Display detailed scan results"""
        output = "=== SCAN COMPLETED ===\n\n"
        
        # Summary
        output += f"Files scanned: {result.get('files_scanned', 0)}\n"
        output += f"Threats found: {result.get('threats_found', 0)}\n"
        output += f"Scan time: {result.get('scan_time', 'Unknown')}\n"
        output += f"Scan type: {self.get_scan_type_name()}\n\n"
        
        # Threats details
        threats = result.get('threats', [])
        if threats:
            output += "=== THREATS DETECTED ===\n\n"
            for i, threat in enumerate(threats, 1):
                output += f"{i}. {threat.get('file', 'Unknown file')}\n"
                output += f"   Threat: {threat.get('threat', 'Unknown')}\n"
                output += f"   Type: {threat.get('type', 'Unknown')}\n"
                output += f"   Action: {threat.get('action', 'None')}\n\n"
        else:
            output += "No threats detected. Your system appears to be clean.\n\n"
            
        # Clean files (if any)
        clean_files = result.get('clean_files', [])
        if clean_files and len(clean_files) <= 50:  # Only show if not too many
            output += "=== CLEAN FILES ===\n\n"
            for clean_file in clean_files[:50]:
                output += f"✓ {clean_file}\n"
            if len(clean_files) > 50:
                output += f"... and {len(clean_files) - 50} more files\n"
                
        self.results_text.setText(output)
        
    def update_scan_stats(self):
        """Update scan statistics during scanning"""
        # Show elapsed time and basic statistics
        # Real-time stats would require scanner progress callback integration
        if hasattr(self, 'scan_start_time') and self.scan_start_time:
            # Basic elapsed time display could be implemented here
            return
        return
        
    def get_scan_type_name(self):
        """Get human-readable scan type name"""
        if self.quick_scan_rb.isChecked():
            return "Quick Scan"
        elif self.full_scan_rb.isChecked():
            return "Full System Scan"
        else:
            return "Custom Scan"