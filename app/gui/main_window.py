import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QProgressBar, QTextEdit, 
                             QTabWidget, QGroupBox, QListWidget, QListWidgetItem,
                             QSplitter, QFrame, QStatusBar, QMenuBar, QMenu,
                             QFileDialog, QMessageBox, QSystemTrayIcon, QProgressDialog,
                             QCheckBox, QSpinBox, QFormLayout, QScrollArea, QDialog, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QShortcut, QKeySequence, QMouseEvent, QWheelEvent

from gui.scan_thread import ScanThread
from gui.rkhunter_components import RKHunterScanDialog, RKHunterScanThread
from core.file_scanner import FileScanner
from core.rkhunter_wrapper import RKHunterWrapper, RKHunterScanResult
from utils.config import load_config, save_config
from utils.scan_reports import ScanReportManager, ScanResult, ScanType, ThreatInfo, ThreatLevel
from monitoring import RealTimeMonitor, MonitorConfig, MonitorState


class ClickableFrame(QFrame):
    """A clickable frame widget."""
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class NoWheelComboBox(QComboBox):
    """A QComboBox that ignores wheel events to prevent accidental changes."""
    
    def wheelEvent(self, event: QWheelEvent):
        """Ignore wheel events when the combo box doesn't have focus."""
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.scanner = FileScanner()
        self.rkhunter = RKHunterWrapper()
        self.report_manager = ScanReportManager()
        self.current_scan_thread = None
        self.current_rkhunter_thread = None
        
        # Quick scan state tracking
        self.is_quick_scan_running = False
        
        # Initialize real-time monitoring
        self.real_time_monitor = None
        self.monitoring_enabled = self.config.get('security_settings', {}).get('real_time_protection', False)
        
        # Theme management - default to dark mode
        self.current_theme = self.config.get('theme', 'dark')
        
        self.init_ui()
        self.setup_system_tray()
        self.setup_accessibility()  # Add accessibility features
        self.apply_theme()
        
        # Initialize real-time monitoring (with error handling)
        self.init_real_time_monitoring_safe()
        
        # Use QTimer to update status after UI is fully initialized
        QTimer.singleShot(100, self.update_definition_status)
        QTimer.singleShot(200, self.update_protection_ui_after_init)
        # Add a safety net timer to ensure status is never left as "Initializing..."
        QTimer.singleShot(1000, self.ensure_protection_status_final)
        
        # Load persisted activity logs after UI is created
        QTimer.singleShot(500, self.load_activity_logs)
        
        # Set up periodic activity log saving (every 30 seconds)
        self.activity_save_timer = QTimer()
        self.activity_save_timer.timeout.connect(self.save_activity_logs)
        self.activity_save_timer.start(30000)  # 30 seconds
        
    def get_theme_color(self, color_type):
        """Get theme-appropriate color for any UI element."""
        if self.current_theme == "dark":
            colors = {
                'background': '#1a1a1a',
                'secondary_bg': '#2a2a2a',
                'tertiary_bg': '#3a3a3a',
                'primary_text': '#FFCDAA',
                'secondary_text': '#666',
                'success': '#9CB898',
                'error': '#F14666', 
                'warning': '#EE8980',
                'accent': '#F14666',
                'border': '#EE8980',
                'hover_bg': '#4a4a4a',
                'pressed_bg': '#2a2a2a',
                'selection_bg': '#F14666',
                'disabled_text': '#666'
            }
        else:  # light theme
            colors = {
                'background': '#fefefe',
                'secondary_bg': '#ffffff',
                'tertiary_bg': '#f5f5f5',
                'primary_text': '#2c2c2c',
                'secondary_text': '#666',
                'success': '#75BDE0',
                'error': '#F89B9B',
                'warning': '#F8BC9B',
                'accent': '#75BDE0',
                'border': '#F8D49B',
                'hover_bg': '#F8BC9B',
                'pressed_bg': '#F89B9B',
                'selection_bg': '#75BDE0',
                'disabled_text': '#999'
            }
        return colors.get(color_type, colors['primary_text'])
    
    def get_status_color(self, status_type):
        """Get theme-appropriate color for status indicators."""
        if self.current_theme == "dark":
            colors = {
                'success': '#9CB898',    # Sage Green for dark theme
                'error': '#F14666',      # Deep Strawberry for dark theme
                'warning': '#EE8980'     # Coral for dark theme
            }
        else:  # light theme
            colors = {
                'success': '#75BDE0',    # Sky Blue for light theme
                'error': '#F89B9B',      # Coral Pink for light theme
                'warning': '#F8BC9B'     # Peach Orange for light theme
            }
        return colors.get(status_type, colors['error'])
        
    def init_ui(self):
        self.setWindowTitle("S&D - Search & Destroy")
        self.setMinimumSize(1000, 750)
        self.resize(1200, 850)
        
        # Set window icon
        icon_path = Path(__file__).parent.parent.parent / 'packaging' / 'icons' / 'org.xanados.SearchAndDestroy.svg'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section
        self.create_header_section(main_layout)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.create_dashboard_tab()  # Add dashboard as first tab
        self.create_scan_tab()
        self.create_real_time_tab()
        self.create_reports_tab()
        self.create_quarantine_tab()
        self.create_settings_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.create_status_bar()
        
        # Menu bar
        self.create_menu_bar()
        
    def create_header_section(self, layout):
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        
        # App icon and title
        title_layout = QHBoxLayout()
        
        # Load and display the actual S&D icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(128, 128)  # Restored to 128x128 as requested
        self.update_icon_for_theme()
        title_layout.addWidget(self.icon_label)
        
        # App title
        title_label = QLabel("S&D - Search & Destroy")
        title_label.setObjectName("appTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        self.quick_scan_btn = QPushButton("Quick Scan")
        self.quick_scan_btn.setObjectName("actionButton")
        self.quick_scan_btn.setMinimumSize(120, 40)  # Increased size to prevent text cutoff
        self.quick_scan_btn.clicked.connect(self.quick_scan)
        
        # Update definitions button with status
        update_container = QVBoxLayout()
        update_btn = QPushButton("Update Definitions")
        update_btn.setObjectName("actionButton")
        update_btn.setMinimumSize(140, 40)  # Increased size for longer text
        update_btn.clicked.connect(self.update_definitions)
        
        # Last update status label
        self.last_update_label = QLabel("Checking...")
        self.last_update_label.setObjectName("lastUpdateLabel")
        self.last_update_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Last checked status label
        self.last_checked_label = QLabel("Checking...")
        self.last_checked_label.setObjectName("lastCheckedLabel")
        self.last_checked_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        update_container.addWidget(update_btn)
        update_container.addWidget(self.last_update_label)
        update_container.addWidget(self.last_checked_label)
        update_container_widget = QWidget()
        update_container_widget.setLayout(update_container)
        
        about_btn = QPushButton("About")
        about_btn.setObjectName("actionButton")
        about_btn.setMinimumSize(80, 40)  # Increased size to prevent text cutoff
        about_btn.clicked.connect(self.show_about)
        
        actions_layout.addWidget(self.quick_scan_btn)
        actions_layout.addWidget(update_container_widget)
        actions_layout.addWidget(about_btn)
        
        header_layout.addLayout(actions_layout)
        layout.addWidget(header_frame)
        
    def create_dashboard_tab(self):
        """Create an overview dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Security Status Overview
        status_row = QHBoxLayout()
        status_row.setSpacing(15)
        
        # Protection Status Card - using strawberry palette
        self.protection_card = self.create_clickable_status_card(
            "Real-Time Protection",
            "Active" if self.monitoring_enabled else "Inactive",
            "#9CB898" if self.monitoring_enabled else "#F14666",
            "Your system is being monitored" if self.monitoring_enabled else "Click to enable protection"
        )
        # Connect the click signal
        self.protection_card.clicked.connect(self.toggle_protection_from_dashboard)
        
        # Last Scan Card
        self.last_scan_card = self.create_status_card(
            "Last Scan",
            "Not scanned yet",  # Will be updated dynamically
            "#17a2b8",
            "Full system scan status"
        )
        
        # Threats Card - using strawberry palette
        self.threats_card = self.create_status_card(
            "Threats Found",
            "0",  # Will be updated dynamically
            "#9CB898",
            "No threats detected in recent scans"
        )
        
        status_row.addWidget(self.protection_card)
        status_row.addWidget(self.last_scan_card)
        status_row.addWidget(self.threats_card)
        
        layout.addLayout(status_row)
        
        # Real-Time Protection Activity (expanded to fill the space)
        activity_group = QGroupBox("Real-Time Protection Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.dashboard_activity = QListWidget()
        # Remove height restriction to allow it to expand
        self.dashboard_activity.setAlternatingRowColors(True)
        # Set custom styling for activity list
        self.setup_activity_list_styling()
        activity_layout.addWidget(self.dashboard_activity)
        
        # Show more link
        show_more_btn = QPushButton("View All Activity →")
        show_more_btn.setFlat(True)
        show_more_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))  # Go to protection tab
        activity_layout.addWidget(show_more_btn)
        
        layout.addWidget(activity_group)
        
        layout.addStretch()
        
        # Add as first tab
        self.tab_widget.addTab(dashboard_widget, "Dashboard")
        
    def create_status_card(self, title, value, color, description):
        """Create a modern status card widget."""
        card = QFrame()
        card.setObjectName("statusCard")
        card.setFrameStyle(QFrame.Shape.Box)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Medium)
        title_label.setFont(title_font)
        
        # Value (main status)
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        
        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("cardDescription")
        desc_label.setWordWrap(True)
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_label.setFont(desc_font)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        
        return card

    def create_clickable_status_card(self, title, value, color, description):
        """Create a clickable modern status card widget."""
        card = ClickableFrame()
        card.setObjectName("statusCard")
        card.setFrameStyle(QFrame.Shape.Box)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Medium)
        title_label.setFont(title_font)
        
        # Value (main status)
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        
        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("cardDescription")
        desc_label.setWordWrap(True)
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_label.setFont(desc_font)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        
        return card

    def toggle_protection_from_dashboard(self):
        """Toggle protection when the dashboard status card is clicked."""
        # If monitor wasn't initialized, try to initialize it first
        if self.real_time_monitor is None:
            print("🔄 Initializing monitoring system from dashboard...")
            success = self.init_real_time_monitoring_safe()
            if not success:
                self.add_activity_message("❌ Cannot toggle protection: Monitoring system unavailable")
                return
        
        self.monitoring_enabled = not self.monitoring_enabled
        self.update_protection_status_card()
        
        # Update the protection tab if it exists
        if hasattr(self, 'protection_toggle_btn'):
            if self.monitoring_enabled:
                self.start_real_time_protection()
            else:
                self.stop_real_time_protection()
        else:
            # Just update the config if the protection tab doesn't exist yet
            self.config['security_settings'] = self.config.get('security_settings', {})
            self.config['security_settings']['real_time_protection'] = self.monitoring_enabled
            save_config(self.config)
            
            if self.monitoring_enabled:
                self.add_activity_message("🛡️ Real-time protection enabled from dashboard")
            else:
                self.add_activity_message("Real-time protection disabled from dashboard")
    
    def update_protection_status_card(self):
        """Update the protection status card with current state."""
        if hasattr(self, 'protection_card'):
            # Find the card's value label and update it
            for child in self.protection_card.findChildren(QLabel):
                if child.objectName() == "cardValue":
                    child.setText("Active" if self.monitoring_enabled else "Inactive")
                    child.setStyleSheet(f"color: {'#9CB898' if self.monitoring_enabled else '#F14666'}; font-size: 20px; font-weight: bold;")
                elif child.objectName() == "cardDescription":
                    child.setText("Your system is being monitored" if self.monitoring_enabled else "Click to enable protection")

    def update_protection_ui_after_init(self):
        """Update Protection tab UI after full initialization to ensure state consistency."""
        print("🔄 Updating Protection tab UI after initialization...")
        
        if hasattr(self, 'protection_status_label') and hasattr(self, 'protection_toggle_btn'):
            if self.monitoring_enabled:
                # Check if the monitor is actually running
                if self.real_time_monitor and hasattr(self.real_time_monitor, 'state') and self.real_time_monitor.state.name == 'RUNNING':
                    self.protection_status_label.setText("🛡️ Active")
                    color = self.get_status_color('success')
                    self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                    self.protection_toggle_btn.setText("Stop")
                    print("✅ Protection tab UI updated to Active state")
                else:
                    # Monitoring was supposed to be enabled but isn't running - reset
                    print("⚠️ Monitoring was enabled but not running - resetting to inactive")
                    self.monitoring_enabled = False
                    self.protection_status_label.setText("❌ Failed to restore")
                    color = self.get_status_color('error')
                    self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                    self.protection_toggle_btn.setText("Start")
                    
                    # Update config to reflect actual state
                    if 'security_settings' not in self.config:
                        self.config['security_settings'] = {}
                    self.config['security_settings']['real_time_protection'] = False
                    save_config(self.config)
            else:
                self.protection_status_label.setText("🔴 Inactive")
                color = self.get_status_color('error')
                self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("Start")
                print("✅ Protection tab UI updated to Inactive state")
            
            # Also update the dashboard card
            self.update_protection_status_card()
        else:
            print("⚠️ Protection tab UI elements not found - skipping update")
    
    def ensure_protection_status_final(self):
        """Final safety net to ensure protection status is never left as 'Initializing...'"""
        print("🔍 Running final protection status check...")
        
        if hasattr(self, 'protection_status_label'):
            current_text = self.protection_status_label.text()
            if "Initializing" in current_text:
                print("⚠️ Found status still showing 'Initializing...', forcing to Inactive")
                # Force status to Inactive if still showing Initializing
                self.protection_status_label.setText("🔴 Inactive")
                color = self.get_status_color('error')
                self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                if hasattr(self, 'protection_toggle_btn'):
                    self.protection_toggle_btn.setText("Start")
                print("✅ Protection status forced to Inactive state")
            else:
                print(f"✅ Protection status is properly set to: {current_text}")
        else:
            print("⚠️ Protection status label not found")

    def create_scan_tab(self):
        scan_widget = QWidget()
        layout = QVBoxLayout(scan_widget)
        
        # Path selection and controls
        controls_group = QGroupBox("Scan Location")
        controls_layout = QVBoxLayout(controls_group)
        
        # Quick scan presets
        presets_label = QLabel("Quick Scan Options:")
        presets_label.setObjectName("presetLabel")
        controls_layout.addWidget(presets_label)
        
        presets_layout = QHBoxLayout()
        
        home_scan_btn = QPushButton("Scan Home Folder")
        home_scan_btn.setObjectName("presetButton")
        home_scan_btn.setToolTip("Scan your home directory for threats")
        home_scan_btn.clicked.connect(lambda: self.set_scan_path(str(Path.home())))
        
        downloads_scan_btn = QPushButton("Scan Downloads")
        downloads_scan_btn.setObjectName("presetButton")
        downloads_scan_btn.setToolTip("Scan Downloads folder for threats")
        downloads_scan_btn.clicked.connect(lambda: self.set_scan_path(str(Path.home() / "Downloads")))
        
        custom_scan_btn = QPushButton("Choose Custom Folder...")
        custom_scan_btn.setObjectName("presetButton")
        custom_scan_btn.setToolTip("Select a specific folder to scan")
        custom_scan_btn.clicked.connect(self.select_scan_path)
        
        presets_layout.addWidget(home_scan_btn)
        presets_layout.addWidget(downloads_scan_btn)
        presets_layout.addWidget(custom_scan_btn)
        presets_layout.addStretch()
        
        controls_layout.addLayout(presets_layout)
        
        # Selected path display
        path_layout = QHBoxLayout()
        path_label_desc = QLabel("Selected path:")
        self.path_label = QLabel("Please select a path")
        self.path_label.setObjectName("pathLabel")
        
        path_layout.addWidget(path_label_desc)
        path_layout.addWidget(self.path_label, 1)
        controls_layout.addLayout(path_layout)
        
        # Scan buttons
        scan_buttons_layout = QHBoxLayout()
        self.start_scan_btn = QPushButton("Start Scan")
        self.start_scan_btn.setObjectName("primaryButton")
        self.start_scan_btn.clicked.connect(self.start_scan)
        
        self.stop_scan_btn = QPushButton("Stop Scan")
        self.stop_scan_btn.setObjectName("dangerButton")
        self.stop_scan_btn.clicked.connect(self.stop_scan)
        self.stop_scan_btn.setEnabled(False)
        
        # RKHunter button
        self.rkhunter_scan_btn = QPushButton("🔍 RKHunter Scan")
        self.rkhunter_scan_btn.setObjectName("specialButton")
        self.rkhunter_scan_btn.setToolTip("Run RKHunter rootkit detection scan\n(Configure scan categories in Settings → Scanning)")
        
        # Check if RKHunter is available (non-intrusive check)
        rkhunter_available = self.rkhunter.is_available()
        
        if rkhunter_available:
            self.rkhunter_scan_btn.clicked.connect(self.start_rkhunter_scan)
        else:
            self.rkhunter_scan_btn.setText("📦 Setup RKHunter")
            self.rkhunter_scan_btn.setToolTip("RKHunter not available - click to install or configure")
            self.rkhunter_scan_btn.clicked.connect(self.install_rkhunter)
        
        scan_buttons_layout.addWidget(self.start_scan_btn)
        scan_buttons_layout.addWidget(self.stop_scan_btn)
        scan_buttons_layout.addWidget(self.rkhunter_scan_btn)
        scan_buttons_layout.addStretch()
        controls_layout.addLayout(scan_buttons_layout)
        
        layout.addWidget(controls_group)
        
        # Progress section
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgressBar")
        self.status_label = QLabel("Ready to scan")
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setObjectName("resultsText")
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(scan_widget, "Scan")
        
    def create_reports_tab(self):
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        
        # Reports controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Reports")
        refresh_btn.clicked.connect(self.refresh_reports)
        
        export_btn = QPushButton("Export Reports")
        export_btn.clicked.connect(self.export_reports)
        
        delete_all_btn = QPushButton("Delete All Reports")
        delete_all_btn.clicked.connect(self.delete_all_reports)
        color = self.get_status_color('error')
        delete_all_btn.setStyleSheet(f"color: {color};")  # Theme-appropriate red to indicate destructive action
        
        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(export_btn)
        controls_layout.addWidget(delete_all_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Reports list
        self.reports_list = QListWidget()
        self.reports_list.itemClicked.connect(self.load_report)
        
        # Report viewer
        self.report_viewer = QTextEdit()
        self.report_viewer.setObjectName("reportViewer")
        self.report_viewer.setReadOnly(True)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.reports_list)
        splitter.addWidget(self.report_viewer)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(reports_widget, "Reports")
        
        # Initialize reports list
        self.refresh_reports()
        
    def create_quarantine_tab(self):
        quarantine_widget = QWidget()
        layout = QVBoxLayout(quarantine_widget)
        
        # Quarantine controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_quarantine)
        restore_btn = QPushButton("Restore Selected")
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        
        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(restore_btn)
        controls_layout.addWidget(delete_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Quarantine list
        self.quarantine_list = QListWidget()
        layout.addWidget(self.quarantine_list)
        
        self.tab_widget.addTab(quarantine_widget, "Quarantine")
        
    def create_settings_tab(self):
        """Create the settings tab with full settings interface."""
        settings_widget = QWidget()
        settings_widget.setObjectName("settingsTabWidget")
        
        # Main layout with proper spacing
        main_layout = QVBoxLayout(settings_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create scrollable area for settings
        scroll_area = QScrollArea()
        scroll_area.setObjectName("settingsScrollArea")
        scroll_content = QWidget()
        scroll_content.setObjectName("settingsScrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # SCAN SETTINGS SECTION
        scan_group = QGroupBox("Scan Settings")
        scan_layout = QFormLayout(scan_group)
        scan_layout.setSpacing(15)
        
        # Max threads setting
        self.settings_max_threads_spin = QSpinBox()
        self.settings_max_threads_spin.setRange(1, 16)
        self.settings_max_threads_spin.setValue(4)
        self.settings_max_threads_spin.setMinimumHeight(35)
        scan_layout.addRow(QLabel("Max Threads:"), self.settings_max_threads_spin)
        
        # Scan timeout setting
        self.settings_timeout_spin = QSpinBox()
        self.settings_timeout_spin.setRange(30, 3600)
        self.settings_timeout_spin.setValue(300)
        self.settings_timeout_spin.setSuffix(" seconds")
        self.settings_timeout_spin.setMinimumHeight(35)
        scan_layout.addRow(QLabel("Scan Timeout:"), self.settings_timeout_spin)
        
        # Scan archives checkbox
        self.settings_scan_archives_cb = QCheckBox("Scan Archive Files")
        self.settings_scan_archives_cb.setChecked(True)
        self.settings_scan_archives_cb.setMinimumHeight(35)
        scan_layout.addRow(self.settings_scan_archives_cb)
        
        # Follow symlinks checkbox
        self.settings_follow_symlinks_cb = QCheckBox("Follow Symbolic Links")
        self.settings_follow_symlinks_cb.setChecked(False)
        self.settings_follow_symlinks_cb.setMinimumHeight(35)
        scan_layout.addRow(self.settings_follow_symlinks_cb)
        
        scroll_layout.addWidget(scan_group)
        
        # USER INTERFACE SETTINGS SECTION
        ui_group = QGroupBox("User Interface Settings")
        ui_layout = QFormLayout(ui_group)
        ui_layout.setSpacing(15)
        
        # Minimize to tray checkbox
        self.settings_minimize_to_tray_cb = QCheckBox("Minimize to System Tray")
        self.settings_minimize_to_tray_cb.setChecked(True)
        self.settings_minimize_to_tray_cb.setMinimumHeight(35)
        ui_layout.addRow(self.settings_minimize_to_tray_cb)
        
        # Show notifications checkbox
        self.settings_show_notifications_cb = QCheckBox("Show Notifications")
        self.settings_show_notifications_cb.setChecked(True)
        self.settings_show_notifications_cb.setMinimumHeight(35)
        ui_layout.addRow(self.settings_show_notifications_cb)
        
        # Activity log retention setting
        self.settings_activity_retention_combo = NoWheelComboBox()
        self.settings_activity_retention_combo.addItems(["10", "25", "50", "100", "200"])
        self.settings_activity_retention_combo.setCurrentText("100")  # Default to 100
        self.settings_activity_retention_combo.setMinimumHeight(35)
        self.settings_activity_retention_combo.setToolTip("Number of recent activity messages to retain between sessions")
        self.settings_activity_retention_combo.currentTextChanged.connect(self.on_retention_setting_changed)
        ui_layout.addRow(QLabel("Activity Log Retention:"), self.settings_activity_retention_combo)
        
        scroll_layout.addWidget(ui_group)
        
        # SECURITY SETTINGS SECTION
        security_group = QGroupBox("Security Settings")
        security_layout = QFormLayout(security_group)
        security_layout.setSpacing(15)
        
        # Auto-update definitions checkbox
        self.settings_auto_update_cb = QCheckBox("Auto-update Virus Definitions")
        self.settings_auto_update_cb.setChecked(True)
        self.settings_auto_update_cb.setMinimumHeight(35)
        security_layout.addRow(self.settings_auto_update_cb)
        
        scroll_layout.addWidget(security_group)
        
        # REAL-TIME PROTECTION SETTINGS SECTION
        protection_group = QGroupBox("Real-Time Protection Settings")
        protection_layout = QFormLayout(protection_group)
        protection_layout.setSpacing(15)
        
        # Monitor file modifications
        self.settings_monitor_modifications_cb = QCheckBox("Monitor File Modifications")
        self.settings_monitor_modifications_cb.setChecked(True)
        self.settings_monitor_modifications_cb.setMinimumHeight(35)
        protection_layout.addRow(self.settings_monitor_modifications_cb)
        
        # Monitor new files
        self.settings_monitor_new_files_cb = QCheckBox("Monitor New Files")
        self.settings_monitor_new_files_cb.setChecked(True)
        self.settings_monitor_new_files_cb.setMinimumHeight(35)
        protection_layout.addRow(self.settings_monitor_new_files_cb)
        
        # Scan modified files immediately
        self.settings_scan_modified_cb = QCheckBox("Scan Modified Files Immediately")
        self.settings_scan_modified_cb.setChecked(False)
        self.settings_scan_modified_cb.setMinimumHeight(35)
        protection_layout.addRow(self.settings_scan_modified_cb)
        
        scroll_layout.addWidget(protection_group)
        
        # RKHUNTER SETTINGS SECTION
        rkhunter_group = QGroupBox("RKHunter Integration")
        rkhunter_layout = QVBoxLayout(rkhunter_group)
        rkhunter_layout.setSpacing(15)
        
        # Create two-column layout
        two_column_layout = QHBoxLayout()
        two_column_layout.setSpacing(20)
        
        # LEFT COLUMN - Basic Settings
        left_column = QGroupBox("Settings")
        left_layout = QVBoxLayout(left_column)
        left_layout.setSpacing(15)
        
        self.settings_enable_rkhunter_cb = QCheckBox("Enable RKHunter Integration")
        self.settings_enable_rkhunter_cb.setChecked(False)
        self.settings_enable_rkhunter_cb.setToolTip("Enable integration with RKHunter rootkit detection")
        self.settings_enable_rkhunter_cb.setMinimumHeight(35)
        left_layout.addWidget(self.settings_enable_rkhunter_cb)
        
        self.settings_run_rkhunter_with_full_scan_cb = QCheckBox("Run RKHunter with Full System Scans")
        self.settings_run_rkhunter_with_full_scan_cb.setChecked(False)
        self.settings_run_rkhunter_with_full_scan_cb.setToolTip("Automatically run RKHunter when performing full system scans")
        self.settings_run_rkhunter_with_full_scan_cb.setMinimumHeight(35)
        left_layout.addWidget(self.settings_run_rkhunter_with_full_scan_cb)
        
        self.settings_rkhunter_auto_update_cb = QCheckBox("Auto-update RKHunter Database")
        self.settings_rkhunter_auto_update_cb.setChecked(True)
        self.settings_rkhunter_auto_update_cb.setToolTip("Automatically update RKHunter database before scans")
        self.settings_rkhunter_auto_update_cb.setMinimumHeight(35)
        left_layout.addWidget(self.settings_rkhunter_auto_update_cb)
        
        # Add stretch to push checkboxes to top
        left_layout.addStretch()
        
        # RIGHT COLUMN - Scan Categories
        right_column = QGroupBox("Default Scan Categories")
        right_layout = QVBoxLayout(right_column)
        
        # Create scrollable area for checkboxes
        scroll_area_rk = QScrollArea()
        scroll_widget_rk = QWidget()
        scroll_layout_rk = QVBoxLayout(scroll_widget_rk)
        scroll_layout_rk.setSpacing(8)
        scroll_layout_rk.setContentsMargins(5, 5, 5, 5)
        
        # Define test categories with descriptions - organized by priority
        self.settings_rkhunter_test_categories = {
            'system_commands': {
                'name': 'System Commands',
                'description': 'Check system command integrity and known rootkit modifications',
                'default': True,
                'priority': 1
            },
            'rootkits': {
                'name': 'Rootkits & Trojans',
                'description': 'Scan for known rootkits, trojans, and malware signatures',
                'default': True,
                'priority': 1
            },
            'system_integrity': {
                'name': 'System Integrity',
                'description': 'Verify filesystem integrity, system configs, and startup files',
                'default': True,
                'priority': 2
            },
            'network': {
                'name': 'Network Security',
                'description': 'Check network interfaces, ports, and packet capture tools',
                'default': True,
                'priority': 2
            },
            'applications': {
                'name': 'Applications',
                'description': 'Check for hidden processes, files, and suspicious applications',
                'default': False,
                'priority': 3
            }
        }
        
        # Create checkboxes in a single row layout
        self.settings_rkhunter_category_checkboxes = {}
        
        # Sort categories by priority and name for better organization
        sorted_categories = sorted(
            self.settings_rkhunter_test_categories.items(),
            key=lambda x: (x[1]['priority'], x[1]['name'])
        )
        
        # Create a single row with all 5 categories - centered
        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)
        row_layout.setContentsMargins(10, 5, 10, 5)
        
        # Add left stretch to center the items
        row_layout.addStretch(1)
        
        # Add all items to a single row
        for category_id, category_info in sorted_categories:
            # Create compact item container
            item_layout = QVBoxLayout()
            item_layout.setSpacing(3)
            item_layout.setContentsMargins(5, 4, 5, 4)
            
            # Checkbox with appropriate height
            checkbox = QCheckBox(category_info['name'])
            checkbox.setChecked(category_info['default'])
            checkbox.setToolTip(category_info['description'])
            checkbox.setMinimumHeight(20)
            checkbox.setStyleSheet("font-weight: bold; font-size: 11px;")
            
            # Description with better sizing for visibility
            desc_label = QLabel(category_info['description'])
            desc_color = self.get_theme_color('secondary_text')
            desc_label.setStyleSheet(
                f"color: {desc_color}; font-size: 9px; margin: 0px; padding: 2px; line-height: 1.2;"
            )
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(45)  # Increased height for better text visibility
            desc_label.setMinimumHeight(45)  # Fixed height for consistency
            desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            item_layout.addWidget(checkbox)
            item_layout.addWidget(desc_label)
            
            # Create item widget with increased dimensions for better text visibility
            item_widget = QWidget()
            item_widget.setLayout(item_layout)
            item_widget.setFixedWidth(135)  # Increased width from 110px to 135px
            item_widget.setFixedHeight(75)  # Increased height from 52px to 75px
            
            bg_color = self.get_theme_color('secondary_bg')
            hover_color = self.get_theme_color('hover_bg')
            item_widget.setStyleSheet(f"""
                QWidget {{
                    border: none;
                    border-radius: 6px;
                    background-color: {bg_color};
                    margin: 3px;
                }}
                QWidget:hover {{
                    background-color: {hover_color};
                }}
            """)
            
            row_layout.addWidget(item_widget)
            self.settings_rkhunter_category_checkboxes[category_id] = checkbox
        
        # Add right stretch to center the items
        row_layout.addStretch(1)
        
        # Add the single row to the main layout
        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        scroll_layout_rk.addWidget(row_widget)
        
        # Add minimal stretch
        scroll_layout_rk.addStretch(1)
        
        scroll_area_rk.setWidget(scroll_widget_rk)
        scroll_area_rk.setMaximumHeight(95)  # Increased height for larger cards
        scroll_area_rk.setMinimumHeight(95)  # Fixed height for larger cards
        scroll_area_rk.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area_rk.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # No vertical scroll needed
        
        border_color = self.get_theme_color('border')
        scroll_bg = self.get_theme_color('tertiary_bg')
        scroll_area_rk.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {border_color};
                border-radius: 4px;
                background-color: {scroll_bg};
            }}
        """)
        
        right_layout.addWidget(scroll_area_rk)
        
        # Quick select buttons for RKHunter categories
        quick_select_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_rkhunter_categories)
        select_all_btn.setMaximumWidth(150)
        select_all_btn.setMinimumHeight(35)
        
        select_recommended_btn = QPushButton("Recommended")
        select_recommended_btn.clicked.connect(self.select_recommended_rkhunter_categories)
        select_recommended_btn.setToolTip("Select recommended test categories for most users")
        select_recommended_btn.setMaximumWidth(150)
        select_recommended_btn.setMinimumHeight(35)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_rkhunter_categories)
        select_none_btn.setMaximumWidth(150)
        select_none_btn.setMinimumHeight(35)
        
        quick_select_layout.addWidget(select_all_btn)
        quick_select_layout.addWidget(select_recommended_btn)
        quick_select_layout.addWidget(select_none_btn)
        quick_select_layout.addStretch()
        
        right_layout.addLayout(quick_select_layout)
        
        # Add columns to two-column layout
        two_column_layout.addWidget(left_column)
        two_column_layout.addWidget(right_column)
        
        # Set column widths (40% left, 60% right)
        left_column.setMaximumWidth(300)
        right_column.setMinimumWidth(400)
        
        # Add two-column layout to main RKHunter layout
        rkhunter_layout.addLayout(two_column_layout)
        
        scroll_layout.addWidget(rkhunter_group)
        
        # Add stretch to push everything to the top
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        main_layout.addWidget(scroll_area)
        
        # SETTINGS CONTROL BUTTONS
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Load defaults button
        load_defaults_btn = QPushButton("Reset to Defaults")
        load_defaults_btn.clicked.connect(self.load_default_settings)
        load_defaults_btn.setMinimumHeight(40)
        load_defaults_btn.setMinimumWidth(140)
        
        # Save settings button
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.clicked.connect(self.save_settings)
        save_settings_btn.setMinimumHeight(40)
        save_settings_btn.setMinimumWidth(120)
        save_settings_btn.setObjectName("primaryButton")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(load_defaults_btn)
        buttons_layout.addWidget(save_settings_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Load current settings
        self.load_current_settings()
        
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def create_real_time_tab(self):
        """Create the real-time protection tab with improved three-column layout."""
        real_time_widget = QWidget()
        
        # Main horizontal layout with proper spacing
        main_layout = QHBoxLayout(real_time_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # LEFT PANEL: Recent Activity (largest panel)
        left_panel = QVBoxLayout()
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        activity_layout.setSpacing(10)  # Add spacing between elements
        activity_layout.setContentsMargins(10, 10, 10, 15)  # Add bottom margin for button
        
        self.activity_list = QListWidget()
        self.activity_list.setMinimumHeight(350)  # Reduce height to make room for button
        activity_layout.addWidget(self.activity_list)
        
        # Add Clear Logs button with proper spacing
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_activity_logs)
        clear_logs_btn.setMinimumHeight(35)
        clear_logs_btn.setMaximumWidth(120)
        clear_logs_btn.setObjectName("dangerButton")
        clear_logs_btn.setToolTip("Clear all activity logs from both Protection tab and Dashboard")
        
        # Center the button with proper spacing
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # Add top margin
        button_layout.addStretch()
        button_layout.addWidget(clear_logs_btn)
        button_layout.addStretch()
        activity_layout.addLayout(button_layout)
        
        left_panel.addWidget(activity_group)
        left_panel.addStretch()
        
        # CENTER PANEL: Protection Status and Statistics (compact but well-spaced)
        center_panel = QVBoxLayout()
        center_panel.setSpacing(20)
        
        # Protection Status section
        status_group = QGroupBox("Protection Status")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(15)
        
        # Protection status display with better styling
        self.protection_status_label = QLabel("🔄 Initializing...")
        self.protection_status_label.setObjectName("protectionStatus")
        self.protection_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.protection_status_label.setMinimumHeight(40)
        self.protection_status_label.setStyleSheet("font-size: 14px; padding: 10px; font-weight: bold;")
        status_layout.addWidget(self.protection_status_label)
        
        # Control button - centered and prominent
        self.protection_toggle_btn = QPushButton("Start")
        self.protection_toggle_btn.clicked.connect(self.toggle_real_time_protection)
        self.protection_toggle_btn.setMinimumHeight(40)
        self.protection_toggle_btn.setMinimumWidth(120)
        self.protection_toggle_btn.setObjectName("primaryButton")
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.protection_toggle_btn)
        button_layout.addStretch()
        status_layout.addLayout(button_layout)
        
        center_panel.addWidget(status_group)
        
        # Protection Statistics section
        stats_group = QGroupBox("Protection Statistics")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(10)
        
        # Create a more organized stats display
        stats_container = QVBoxLayout()
        
        # Events row
        events_layout = QHBoxLayout()
        events_layout.addWidget(QLabel("Events Processed:"))
        self.events_processed_label = QLabel("0")
        self.events_processed_label.setStyleSheet(f"font-weight: bold; color: {self.get_theme_color('accent')};")
        events_layout.addStretch()
        events_layout.addWidget(self.events_processed_label)
        stats_container.addLayout(events_layout)
        
        # Threats row
        threats_layout = QHBoxLayout()
        threats_layout.addWidget(QLabel("Threats Detected:"))
        self.threats_detected_label = QLabel("0")
        self.threats_detected_label.setStyleSheet(f"font-weight: bold; color: {self.get_theme_color('error')};")
        threats_layout.addStretch()
        threats_layout.addWidget(self.threats_detected_label)
        stats_container.addLayout(threats_layout)
        
        # Scans row
        scans_layout = QHBoxLayout()
        scans_layout.addWidget(QLabel("Scans Performed:"))
        self.scans_performed_label = QLabel("0")
        self.scans_performed_label.setStyleSheet(f"font-weight: bold; color: {self.get_theme_color('success')};")
        scans_layout.addStretch()
        scans_layout.addWidget(self.scans_performed_label)
        stats_container.addLayout(scans_layout)
        
        # Uptime row
        uptime_layout = QHBoxLayout()
        uptime_layout.addWidget(QLabel("Uptime:"))
        self.uptime_label = QLabel("00:00:00")
        self.uptime_label.setStyleSheet(f"font-weight: bold; color: {self.get_theme_color('warning')};")
        uptime_layout.addStretch()
        uptime_layout.addWidget(self.uptime_label)
        stats_container.addLayout(uptime_layout)
        
        stats_layout.addLayout(stats_container)
        center_panel.addWidget(stats_group)
        center_panel.addStretch()
        
        # RIGHT PANEL: Monitored Paths
        right_panel = QVBoxLayout()
        paths_group = QGroupBox("Monitored Paths")
        paths_layout = QVBoxLayout(paths_group)
        
        self.paths_list = QListWidget()
        self.paths_list.setMinimumHeight(300)  # Give it good height
        paths_layout.addWidget(self.paths_list)
        
        # Path control buttons
        paths_controls = QHBoxLayout()
        add_path_btn = QPushButton("Add Path")
        add_path_btn.clicked.connect(self.add_watch_path)
        add_path_btn.setMinimumHeight(35)
        
        remove_path_btn = QPushButton("Remove Path")
        remove_path_btn.clicked.connect(self.remove_watch_path)
        remove_path_btn.setMinimumHeight(35)
        remove_path_btn.setObjectName("dangerButton")
        
        paths_controls.addWidget(add_path_btn)
        paths_controls.addWidget(remove_path_btn)
        paths_layout.addLayout(paths_controls)
        
        right_panel.addWidget(paths_group)
        right_panel.addStretch()
        
        # Add panels to main layout with proper proportions
        main_layout.addLayout(left_panel, 2)    # 40% - Recent Activity (largest)
        main_layout.addLayout(center_panel, 1)  # 30% - Status & Stats (compact)
        main_layout.addLayout(right_panel, 1)   # 30% - Monitored Paths
        
        self.tab_widget.addTab(real_time_widget, "Protection")
        
    def init_real_time_monitoring_safe(self):
        """Safely initialize the real-time monitoring system with better error handling."""
        print("🔧 Initializing real-time monitoring system...")
        try:
            # Create monitor configuration with safer defaults
            watch_paths = self.config.get('watch_paths', [str(Path.home())])  # Just monitor home directory initially
            excluded_paths = self.config.get('excluded_paths', ['/proc', '/sys', '/dev', '/tmp'])
            
            # Ensure paths are properly formatted and validated
            if isinstance(watch_paths, list):
                watch_paths = [str(path) for path in watch_paths if path and os.path.exists(str(path))]
            else:
                watch_paths = [str(watch_paths)] if watch_paths and os.path.exists(str(watch_paths)) else []
            
            # Fallback to home directory if no valid paths
            if not watch_paths:
                home_path = str(Path.home())
                if os.path.exists(home_path):
                    watch_paths = [home_path]
                else:
                    print("❌ No valid watch paths found, monitoring disabled")
                    return False
                
            if isinstance(excluded_paths, list):
                excluded_paths = [str(path) for path in excluded_paths]
            else:
                excluded_paths = [str(excluded_paths)]
            
            print(f"📁 Valid watch paths: {watch_paths}")
            print(f"🚫 Excluded paths: {excluded_paths}")
            
            monitor_config = MonitorConfig(
                watch_paths=watch_paths,
                excluded_paths=excluded_paths,
                scan_new_files=True,
                scan_modified_files=False,  # Start with less aggressive monitoring
                quarantine_threats=False    # Don't auto-quarantine initially for testing
            )
            
            # Create real-time monitor
            self.real_time_monitor = RealTimeMonitor(monitor_config)
            print("✅ RealTimeMonitor created successfully")
            
            # Set up callbacks only if the methods exist
            if hasattr(self.real_time_monitor, 'set_threat_detected_callback'):
                self.real_time_monitor.set_threat_detected_callback(self.on_threat_detected)
                print("✅ Threat detection callback set")
            
            if hasattr(self.real_time_monitor, 'set_scan_completed_callback'):
                self.real_time_monitor.set_scan_completed_callback(self.on_scan_completed)
                print("✅ Scan completion callback set")
                
            if hasattr(self.real_time_monitor, 'set_error_callback'):
                self.real_time_monitor.set_error_callback(self.on_monitoring_error)
                print("✅ Error callback set")
            
            # Set up timer to update statistics
            self.stats_timer = QTimer()
            self.stats_timer.timeout.connect(self.update_monitoring_statistics)
            self.stats_timer.start(10000)  # Update every 10 seconds (less frequent)
            print("✅ Statistics timer started")
            
            # Set initial status based on saved configuration
            if hasattr(self, 'protection_status_label'):
                if self.monitoring_enabled:
                    # If protection was enabled before, restore it
                    print("🔄 Restoring real-time protection from saved state...")
                    if self.real_time_monitor and self.real_time_monitor.start():
                        self.protection_status_label.setText("🛡️ Active")
                        color = self.get_status_color('success')
                        self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                        if hasattr(self, 'protection_toggle_btn'):
                            self.protection_toggle_btn.setText("Stop")
                        print("✅ Real-time protection restored successfully!")
                        self.add_activity_message("✅ Real-time protection restored from previous session")
                    else:
                        # Failed to start, reset to inactive
                        print("❌ Failed to restore real-time protection")
                        self.monitoring_enabled = False
                        self.protection_status_label.setText("❌ Failed to restore")
                        color = self.get_status_color('error')
                        self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                        if hasattr(self, 'protection_toggle_btn'):
                            self.protection_toggle_btn.setText("Start")
                        self.add_activity_message("❌ Failed to restore real-time protection from previous session")
                        # Update config to reflect failure
                        if 'security_settings' not in self.config:
                            self.config['security_settings'] = {}
                        self.config['security_settings']['real_time_protection'] = False
                        save_config(self.config)
                else:
                    # Protection is disabled, set inactive status
                    self.protection_status_label.setText("🔴 Inactive")
                    color = self.get_status_color('error')
                    self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                    if hasattr(self, 'protection_toggle_btn'):
                        self.protection_toggle_btn.setText("Start")
            
            print("✅ Real-time monitoring initialized successfully!")
            return True
                
        except (ImportError, AttributeError, OSError) as e:
            print(f"❌ Failed to initialize monitoring: {e}")
            # Create a dummy monitor for UI purposes
            self.real_time_monitor = None
            self.add_activity_message(f"⚠️ Monitoring system offline: {str(e)}")
            
            # Ensure status is never left as "Initializing..." - set to inactive
            if hasattr(self, 'protection_status_label'):
                self.protection_status_label.setText("🔴 Inactive")
                color = self.get_status_color('error')
                self.protection_status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; padding: 5px;")
                if hasattr(self, 'protection_toggle_btn'):
                    self.protection_toggle_btn.setText("Start")
                print("✅ Status reset to Inactive after initialization failure")
            
            return False

    def init_real_time_monitoring(self):
        """Initialize the real-time monitoring system."""
        try:
            # Create monitor configuration
            watch_paths = self.config.get('watch_paths', ['/home', '/opt', '/tmp'])
            excluded_paths = self.config.get('excluded_paths', ['/proc', '/sys', '/dev'])
            
            monitor_config = MonitorConfig(
                watch_paths=watch_paths,
                excluded_paths=excluded_paths,
                scan_new_files=True,
                scan_modified_files=True,
                quarantine_threats=True
            )
            
            # Create real-time monitor
            self.real_time_monitor = RealTimeMonitor(monitor_config)
            
            # Set up callbacks
            self.real_time_monitor.set_threat_detected_callback(self.on_threat_detected)
            self.real_time_monitor.set_scan_completed_callback(self.on_scan_completed)
            self.real_time_monitor.set_error_callback(self.on_monitoring_error)
            
            # Set up timer to update statistics
            self.stats_timer = QTimer()
            self.stats_timer.timeout.connect(self.update_monitoring_statistics)
            self.stats_timer.start(5000)  # Update every 5 seconds
            
            # Auto-start if enabled (temporarily disabled)
            # if self.monitoring_enabled:
            #     QTimer.singleShot(2000, self.start_real_time_protection)
            # else:
            # Set initial status to Inactive when monitoring is disabled by default
            if hasattr(self, 'protection_status_label'):
                self.protection_status_label.setText("🔴 Inactive")
                self.protection_status_label.setStyleSheet(f"color: {self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")
                
        except (ImportError, AttributeError, RuntimeError) as e:
            self.add_activity_message(f"❌ Failed to initialize monitoring: {e}")
            
    def toggle_real_time_protection(self):
        """Toggle real-time protection on/off."""
        # Check current state by looking at the button text
        if "Start" in self.protection_toggle_btn.text():
            self.start_real_time_protection()
        else:
            self.stop_real_time_protection()
            
    def start_real_time_protection(self):
        """Start real-time protection."""
        try:
            # If monitor wasn't initialized, try to initialize it now
            if self.real_time_monitor is None:
                print("🔄 Monitor not initialized, attempting to initialize...")
                success = self.init_real_time_monitoring_safe()
                if not success:
                    self.add_activity_message("❌ Cannot start protection: Monitoring system unavailable")
                    return
            
            if self.real_time_monitor and self.real_time_monitor.start():
                self.protection_status_label.setText("🛡️ Active")
                self.protection_status_label.setStyleSheet(f"color: {self.get_theme_color('success')}; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("Stop")
                self.add_activity_message("✅ Real-time protection started")
                self.status_bar.showMessage("Real-time protection active")
                
                # Save activity logs immediately for important events
                self.save_activity_logs()
                
                # Save user preference
                self.monitoring_enabled = True
                if 'security_settings' not in self.config:
                    self.config['security_settings'] = {}
                self.config['security_settings']['real_time_protection'] = True
                save_config(self.config)
                
                # Update dashboard card to reflect the change
                self.update_protection_status_card()
                
                # Update paths list
                self.update_paths_list()
                
                # Start or restart the statistics timer
                if hasattr(self, 'stats_timer'):
                    self.stats_timer.start(5000)  # Update every 5 seconds
                else:
                    self.stats_timer = QTimer()
                    self.stats_timer.timeout.connect(self.update_monitoring_statistics)
                    self.stats_timer.start(5000)
                
                # Update statistics immediately to show current state
                self.update_monitoring_statistics()
            else:
                self.protection_status_label.setText("❌ Failed")
                self.protection_status_label.setStyleSheet(f"color: {self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")
                # Keep button as "Start" since protection failed to start
                self.protection_toggle_btn.setText("Start")
                self.add_activity_message("❌ Failed to start real-time protection")
                
                # Make sure dashboard shows failure state
                self.monitoring_enabled = False
                self.update_protection_status_card()
                
        except (AttributeError, RuntimeError, OSError) as e:
            self.add_activity_message(f"❌ Error starting protection: {e}")
            # Ensure button stays as "Start" if there was an error
            self.protection_toggle_btn.setText("Start")
            # Make sure dashboard shows error state
            self.monitoring_enabled = False
            self.update_protection_status_card()
    
    def stop_real_time_protection(self):
        """Stop real-time protection."""
        try:
            if self.real_time_monitor:
                self.real_time_monitor.stop()
                self.protection_status_label.setText("🔴 Inactive")
                self.protection_status_label.setStyleSheet(f"color: {self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("Start")
                self.add_activity_message("🛑 Real-time protection stopped")
                self.status_bar.showMessage("🛑 Real-time protection stopped")
                
                # Save activity logs immediately for important events
                self.save_activity_logs()
                
                # Save user preference
                self.monitoring_enabled = False
                if 'security_settings' not in self.config:
                    self.config['security_settings'] = {}
                self.config['security_settings']['real_time_protection'] = False
                save_config(self.config)
                
                # Update dashboard card to reflect the change
                self.update_protection_status_card()
                
                # Stop the statistics timer when protection is stopped
                if hasattr(self, 'stats_timer'):
                    self.stats_timer.stop()
                
                # Reset statistics display to show monitoring is stopped
                if hasattr(self, 'events_processed_label'):
                    self.events_processed_label.setText("0")
                if hasattr(self, 'threats_detected_label'):
                    self.threats_detected_label.setText("0")
                if hasattr(self, 'scans_performed_label'):
                    self.scans_performed_label.setText("0")
                if hasattr(self, 'uptime_label'):
                    self.uptime_label.setText("00:00:00")
                
        except (AttributeError, RuntimeError) as e:
            self.add_activity_message(f"❌ Error stopping protection: {e}")
            # If stopping failed, we can't be sure of the state, so show error and allow retry
            self.protection_status_label.setText("❌ Error")
            self.protection_status_label.setStyleSheet(f"color: {self.get_theme_color('error')}; font-weight: bold; font-size: 12px; padding: 5px;")
    
    def on_threat_detected(self, file_path: str, threat_name: str):
        """Handle threat detection callback."""
        message = f"🚨 THREAT DETECTED: {threat_name} in {file_path}"
        self.add_activity_message(message)
        
        # Show system notification
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage(
                "Threat Detected!",
                f"Found {threat_name} in {file_path}",
                QSystemTrayIcon.MessageIcon.Critical,
                5000
            )
        
        # Update status bar
        self.status_bar.showMessage(f"Threat detected: {threat_name}", 10000)
    
    def on_scan_completed(self, file_path: str, result: str):
        """Handle scan completion callback."""
        if result != "clean":
            message = f"🔍 Scan completed: {file_path} - {result}"
            self.add_activity_message(message)
    
    def on_monitoring_error(self, error_message: str):
        """Handle monitoring error callback."""
        self.add_activity_message(f"⚠️ Monitoring error: {error_message}")
    
    def add_activity_message(self, message: str):
        """Add a message to the activity list."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        # Get current retention setting
        retention = self.get_activity_retention_setting()
        
        # Add to main activity list if it exists
        if hasattr(self, 'activity_list'):
            # Add to top of list
            item = QListWidgetItem(full_message)
            self.activity_list.insertItem(0, item)
            
            # Keep only last N items based on retention setting
            while self.activity_list.count() > retention:
                self.activity_list.takeItem(self.activity_list.count() - 1)
        
        # Also add to dashboard activity list if it exists
        if hasattr(self, 'dashboard_activity'):
            # Add to top of dashboard list
            item = QListWidgetItem(full_message)
            self.dashboard_activity.insertItem(0, item)
            
            # Keep only last 20 items on dashboard for brevity
            while self.dashboard_activity.count() > 20:
                self.dashboard_activity.takeItem(self.dashboard_activity.count() - 1)
        
        # Save activity logs periodically (but not on every single message to avoid excessive I/O)
        # We'll save on app close, settings changes, and periodically
    
    def save_activity_logs(self):
        """Save current activity logs to persistent storage."""
        try:
            from utils.config import DATA_DIR
            activity_log_file = DATA_DIR / 'activity_logs.json'
            
            # Get current retention setting
            retention = self.get_activity_retention_setting()
            
            # Collect activity messages from the primary activity list
            activity_messages = []
            
            # Primary activity list (Protection tab) has the full history
            if hasattr(self, 'activity_list') and self.activity_list.count() > 0:
                for i in range(min(self.activity_list.count(), retention)):
                    item = self.activity_list.item(i)
                    if item:
                        activity_messages.append(item.text())
            
            # Only save if we have messages
            if activity_messages:
                # Save to file
                with open(activity_log_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'retention_setting': retention,
                        'messages': activity_messages
                    }, f, indent=2)
                print(f"Saved {len(activity_messages)} activity log entries")
            else:
                # If no messages, remove the file to start fresh
                if activity_log_file.exists():
                    activity_log_file.unlink()
                
        except Exception as e:
            print(f"Failed to save activity logs: {e}")
    
    def load_activity_logs(self):
        """Load persisted activity logs on startup."""
        try:
            from utils.config import DATA_DIR
            activity_log_file = DATA_DIR / 'activity_logs.json'
            
            if not activity_log_file.exists():
                return
            
            with open(activity_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = data.get('messages', [])
            if not messages:
                return
            
            # Get current retention setting from config (not UI which may not be ready yet)
            retention = self.config.get('ui_settings', {}).get('activity_log_retention', 100)
            
            # Limit messages to current retention setting
            messages = messages[:retention]
            
            # Clear existing lists first
            if hasattr(self, 'activity_list'):
                self.activity_list.clear()
            if hasattr(self, 'dashboard_activity'):
                self.dashboard_activity.clear()
            
            # Add messages in correct chronological order (newest first, as they were saved)
            for message in messages:
                if hasattr(self, 'activity_list'):
                    item = QListWidgetItem(message)
                    self.activity_list.addItem(item)
                
                # Add to dashboard activity (limited to 20 items)
                if hasattr(self, 'dashboard_activity') and self.dashboard_activity.count() < 20:
                    item = QListWidgetItem(message)
                    self.dashboard_activity.addItem(item)
            
            print(f"Loaded {len(messages)} activity log entries")
            
        except Exception as e:
            print(f"Failed to load activity logs: {e}")
    
    def get_activity_retention_setting(self):
        """Get the current activity retention setting."""
        if hasattr(self, 'settings_activity_retention_combo'):
            return int(self.settings_activity_retention_combo.currentText())
        return self.config.get('ui_settings', {}).get('activity_log_retention', 100)
    
    def clear_activity_logs(self):
        """Clear all activity logs from both Protection tab and Dashboard."""
        try:
            # Show confirmation dialog
            reply = self.show_themed_message_box(
                "question", 
                "Clear Activity Logs", 
                "Are you sure you want to clear all activity logs?\n\n"
                "This will remove all activity entries from both the Protection tab and Dashboard.\n"
                "This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Clear both activity lists
                if hasattr(self, 'activity_list'):
                    self.activity_list.clear()
                    
                if hasattr(self, 'dashboard_activity'):
                    self.dashboard_activity.clear()
                
                # Remove the saved activity log file
                try:
                    from utils.config import DATA_DIR
                    activity_log_file = DATA_DIR / 'activity_logs.json'
                    if activity_log_file.exists():
                        activity_log_file.unlink()
                except Exception as e:
                    print(f"Warning: Could not remove activity log file: {e}")
                
                # Add a confirmation message to the logs
                self.add_activity_message("🗑️ Activity logs cleared by user")
                
                # Show success message
                self.show_themed_message_box(
                    "information",
                    "Logs Cleared",
                    "All activity logs have been cleared successfully."
                )
                
        except Exception as e:
            print(f"Error clearing activity logs: {e}")
            self.show_themed_message_box(
                "warning",
                "Error",
                f"Failed to clear activity logs: {str(e)}"
            )
    
    def on_retention_setting_changed(self, new_value):
        """Handle changes to the activity log retention setting."""
        try:
            new_retention = int(new_value)
            
            # Trim current activity lists to new size
            if hasattr(self, 'activity_list'):
                while self.activity_list.count() > new_retention:
                    self.activity_list.takeItem(self.activity_list.count() - 1)
            
            # Save settings immediately when changed
            self.config['ui_settings']['activity_log_retention'] = new_retention
            from utils.config import save_config
            save_config(self.config)
            
        except ValueError:
            print(f"Invalid retention value: {new_value}")
    
    def update_monitoring_statistics(self):
        """Update the monitoring statistics display."""
        if self.real_time_monitor:
            try:
                stats = self.real_time_monitor.get_statistics()
                monitor_stats = stats.get('monitor', {})
                
                # Update each statistic with null checking
                if hasattr(self, 'events_processed_label'):
                    events = monitor_stats.get('events_processed', 0)
                    self.events_processed_label.setText(str(events))
                
                if hasattr(self, 'threats_detected_label'):
                    threats = monitor_stats.get('threats_detected', 0)
                    self.threats_detected_label.setText(str(threats))
                
                if hasattr(self, 'scans_performed_label'):
                    scans = monitor_stats.get('scans_performed', 0)
                    self.scans_performed_label.setText(str(scans))
                
                if hasattr(self, 'uptime_label'):
                    uptime = monitor_stats.get('uptime_seconds', 0)
                    if uptime > 0:
                        hours = int(uptime // 3600)
                        minutes = int((uptime % 3600) // 60)
                        seconds = int(uptime % 60)
                        self.uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                    else:
                        self.uptime_label.setText("00:00:00")
                        
                # Also update the dashboard cards with current statistics
                if hasattr(self, 'threats_card'):
                    threats = monitor_stats.get('threats_detected', 0)
                    for child in self.threats_card.findChildren(QLabel):
                        if child.objectName() == "cardValue":
                            child.setText(str(threats))
                            break
                    
            except (AttributeError, ValueError, KeyError) as e:
                # Log the error for debugging but don't crash the UI
                print(f"⚠️ Error updating monitoring statistics: {e}")
        else:
            # If monitor is not available, ensure all statistics show 0
            if hasattr(self, 'events_processed_label'):
                self.events_processed_label.setText("0")
            if hasattr(self, 'threats_detected_label'):
                self.threats_detected_label.setText("0")
            if hasattr(self, 'scans_performed_label'):
                self.scans_performed_label.setText("0")
            if hasattr(self, 'uptime_label'):
                self.uptime_label.setText("00:00:00")
    
    def update_paths_list(self):
        """Update the monitored paths list."""
        if hasattr(self, 'paths_list') and self.real_time_monitor:
            self.paths_list.clear()
            config = self.real_time_monitor.config
            for path in config.watch_paths:
                self.paths_list.addItem(f"📁 {path}")
    
    def add_watch_path(self):
        """Add a new path to monitor."""
        path = QFileDialog.getExistingDirectory(self, "Select Directory to Monitor")
        if path and self.real_time_monitor:
            if self.real_time_monitor.add_watch_path(path):
                self.update_paths_list()
                self.add_activity_message(f"📁 Added watch path: {path}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add watch path: {path}")
    
    def remove_watch_path(self):
        """Remove a path from monitoring."""
        current_item = self.paths_list.currentItem()
        if current_item and self.real_time_monitor:
            path = current_item.text().replace("📁 ", "")
            if self.real_time_monitor.remove_watch_path(path):
                self.update_paths_list()
                self.add_activity_message(f"📁 Removed watch path: {path}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to remove watch path: {path}")
        
    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        self.setStatusBar(self.status_bar)
        
    def create_menu_bar(self):
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        
        # File menu
        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        file_menu.addAction(exit_action)
        
        # View menu for theme selection
        view_menu = QMenu("View", self)
        menu_bar.addMenu(view_menu)
        
        # Theme submenu
        theme_menu = QMenu("Theme", self)
        view_menu.addMenu(theme_menu)
        
        # Theme actions
        self.dark_theme_action = QAction("Dark Mode", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self.set_theme('dark'))
        theme_menu.addAction(self.dark_theme_action)
        
        self.light_theme_action = QAction("Light Mode", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self.set_theme('light'))
        theme_menu.addAction(self.light_theme_action)
        
        self.system_theme_action = QAction("System Default", self)
        self.system_theme_action.setCheckable(True)
        self.system_theme_action.triggered.connect(lambda: self.set_theme('system'))
        theme_menu.addAction(self.system_theme_action)
        
        # Set initial theme state
        self.update_theme_menu()
        
        # Help menu
        help_menu = QMenu("Help", self)
        menu_bar.addMenu(help_menu)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_system_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create a system tray icon
        app_icon = QIcon()
        icon_path = Path(__file__).parent.parent.parent / 'packaging' / 'icons' / 'org.xanados.SearchAndDestroy.svg'
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
        else:
            # Create a default icon if the SVG is not found
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.blue)
            app_icon = QIcon(pixmap)
            
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip("S&D - Search & Destroy")
        
        # Create system tray menu
        tray_menu = QMenu(self)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show)
        tray_menu.addAction(open_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
    def setup_accessibility(self):
        """Set up accessibility features including keyboard shortcuts and ARIA-like labels."""
        # Keyboard shortcuts
        self.quick_scan_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quick_scan_shortcut.activated.connect(self.quick_scan)
        
        self.update_definitions_shortcut = QShortcut(QKeySequence("Ctrl+U"), self)
        self.update_definitions_shortcut.activated.connect(self.update_definitions)
        
        # Tab navigation shortcuts
        self.dashboard_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        self.dashboard_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(0))
        
        self.scan_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        self.scan_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(1))
        
        self.protection_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        self.protection_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(2))
        
        # Help shortcut
        self.help_shortcut = QShortcut(QKeySequence("F1"), self)
        self.help_shortcut.activated.connect(self.show_about)
        
        # Refresh shortcut
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.activated.connect(self.refresh_reports)
        
        # Set accessible names and descriptions for better screen reader support
        self.tab_widget.setAccessibleName("Main application tabs")
        self.tab_widget.setAccessibleDescription("Navigate between different application functions")
        
        # Set status bar accessibility
        if hasattr(self, 'status_bar'):
            self.status_bar.setAccessibleName("Application status")
        
    def apply_theme(self):
        """Apply the current theme to the application."""
        if self.current_theme == 'dark':
            self.apply_dark_theme()
        elif self.current_theme == 'light':
            self.apply_light_theme()
        else:  # system
            self.apply_system_theme()
        
        # Update the icon for the new theme
        if hasattr(self, 'icon_label'):
            self.update_icon_for_theme()
    
    def set_theme(self, theme):
        """Set the application theme and save to config."""
        self.current_theme = theme
        self.config['theme'] = theme
        save_config(self.config)
        self.apply_theme()
        self.update_theme_menu()
    
    def update_theme_menu(self):
        """Update the theme menu to reflect the current selection."""
        self.dark_theme_action.setChecked(self.current_theme == 'dark')
        self.light_theme_action.setChecked(self.current_theme == 'light')
        self.system_theme_action.setChecked(self.current_theme == 'system')
    
    def update_icon_for_theme(self):
        """Update the application icon based on the current theme."""
        icon_path = Path(__file__).parent.parent.parent / 'packaging' / 'icons' / 'org.xanados.SearchAndDestroy-128.png'
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            
            # Convert to black and white in dark mode
            if self.current_theme == 'dark':
                pixmap = self.convert_to_black_and_white(pixmap)
            
            scaled_pixmap = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            # Fallback to colored circle if icon not found
            fallback_color = "#404040" if self.current_theme == 'dark' else "#2196F3"
            self.icon_label.setStyleSheet(f"background-color: {fallback_color}; border-radius: 64px;")
    
    def convert_to_black_and_white(self, pixmap):
        """Convert a colored pixmap to black and white by desaturating colors."""
        # Convert pixmap to image for processing
        image = pixmap.toImage()
        
        # Create a simple desaturated version using a more efficient approach
        # Convert to Format_ARGB32 for easier pixel manipulation
        if image.format() != image.Format.Format_ARGB32:
            image = image.convertToFormat(image.Format.Format_ARGB32)
        
        width = image.width()
        height = image.height()
        
        # Process pixels in chunks for better performance
        for y in range(height):
            for x in range(width):
                pixel = image.pixel(x, y)
                
                # Extract ARGB components
                alpha = (pixel >> 24) & 0xFF
                red = (pixel >> 16) & 0xFF
                green = (pixel >> 8) & 0xFF
                blue = pixel & 0xFF
                
                # Calculate luminance using standard formula
                luminance = int(0.299 * red + 0.587 * green + 0.114 * blue)
                
                # Create grayscale pixel maintaining alpha
                gray_pixel = (alpha << 24) | (luminance << 16) | (luminance << 8) | luminance
                image.setPixel(x, y, gray_pixel)
        
        return QPixmap.fromImage(image)
    
    def show_themed_message_box(self, msg_type, title, text, buttons=None):
        """Show a message box with proper theming."""
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
        elif msg_type == "question":
            msg_box.setIcon(QMessageBox.Icon.Question)
        
        # Set buttons
        if buttons:
            msg_box.setStandardButtons(buttons)
        else:
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply theme-specific styling  
        bg = self.get_theme_color('background')
        text = self.get_theme_color('primary_text')
        tertiary_bg = self.get_theme_color('tertiary_bg')
        border = self.get_theme_color('border')
        hover_bg = self.get_theme_color('hover_bg')
        pressed_bg = self.get_theme_color('pressed_bg')
        accent = self.get_theme_color('accent')
        success = self.get_theme_color('success')
        
        style = f"""
            QMessageBox {{
                background-color: {bg};
                color: {text};
                font-size: 12px;
                font-weight: 500;
                border: 2px solid {border};
                border-radius: 6px;
            }}
            QMessageBox QLabel {{
                color: {text};
                font-weight: 600;
                padding: 10px;
                line-height: 1.4;
            }}
            QMessageBox QPushButton {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 5px;
                padding: 8px 16px;
                color: {text};
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent};
                color: {text};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
            QMessageBox QPushButton:default {{
                background-color: {success};
                border-color: {success};
                color: {bg};
                font-weight: 700;
            }}
            QMessageBox QPushButton:default:hover {{
                background-color: {hover_bg};
                border-color: {hover_bg};
            }}
        """
        msg_box.setStyleSheet(style)
        
        return msg_box.exec()
    
    def setup_activity_list_styling(self):
        """Set up proper styling for the activity list with theme-aware colors."""
        bg = self.get_theme_color('background')
        secondary_bg = self.get_theme_color('secondary_bg')
        text = self.get_theme_color('primary_text')
        accent = self.get_theme_color('accent')
        border = self.get_theme_color('border')
        hover_bg = self.get_theme_color('hover_bg')
        selection_bg = self.get_theme_color('selection_bg')
        
        activity_style = f"""
            QListWidget {{
                background-color: {secondary_bg};
                color: {text};
                alternate-background-color: rgba(117, 189, 224, 0.1);
                selection-background-color: {accent};
                selection-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid rgba(238, 137, 128, 0.2);
            }}
            QListWidget::item:hover {{
                background-color: {hover_bg};
            }}
            QListWidget::item:selected {{
                background-color: {accent};
                color: {bg};
                font-weight: 600;
            }}
        """
        
        if hasattr(self, 'dashboard_activity'):
            self.dashboard_activity.setStyleSheet(activity_style)
        
        # Also apply styling to other activity lists
        if hasattr(self, 'activity_list'):
            self.activity_list.setStyleSheet(activity_style)
        
        # Apply styling to reports list
        if hasattr(self, 'reports_list'):
            style = self._get_list_widget_style()
            self.reports_list.setStyleSheet(style)
        
        # Apply styling to quarantine list  
        if hasattr(self, 'quarantine_list'):
            style = self._get_list_widget_style()
            self.quarantine_list.setStyleSheet(style)
            
        # Apply styling to paths list
        if hasattr(self, 'paths_list'):
            style = self._get_list_widget_style()
            self.paths_list.setStyleSheet(style)
    
    def _get_list_widget_style(self):
        """Get consistent list widget styling based on current theme."""
        if self.current_theme == 'dark':
            return """
                QListWidget {
                    background-color: #2a2a2a;
                    color: #FFCDAA;
                    selection-background-color: #F14666;
                    selection-color: #ffffff;
                    border: 1px solid #EE8980;
                    border-radius: 6px;
                }
                QListWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid rgba(238, 137, 128, 0.1);
                }
                QListWidget::item:hover {
                    background-color: rgba(241, 70, 102, 0.1);
                }
                QListWidget::item:selected {
                    background-color: #F14666;
                    color: #ffffff;
                    font-weight: 600;
                }
            """
        else:  # light theme
            return """
                QListWidget {
                    background-color: #ffffff;
                    color: #2c2c2c;
                    selection-background-color: #75BDE0;
                    selection-color: #ffffff;
                    border: 1px solid #75BDE0;
                    border-radius: 6px;
                }
                QListWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid rgba(117, 189, 224, 0.1);
                }
                QListWidget::item:hover {
                    background-color: rgba(117, 189, 224, 0.15);
                    color: #1a1a1a;
                }
                QListWidget::item:selected {
                    background-color: #75BDE0;
                    color: #ffffff;
                    font-weight: 600;
                }
                QListWidget::item:selected:hover {
                    background-color: #5AADD4;
                    color: #ffffff;
                }
            """
    
    def apply_dark_theme(self):
        """Apply dark theme styling using Strawberry color palette for optimal readability."""
        # Based on Color Theory principles:
        # - F14666 (Deep Strawberry): Primary accent, high energy/attention
        # - EE8980 (Coral): Secondary accent, warm complement  
        # - FFCDAA (Peach Cream): Main text, high contrast on dark
        # - 9CB898 (Sage Green): Success states, natural balance
        # Dark neutrals (https://www.uxdesigninstitute.com/blog/what-is-a-gui/#1a1a1a, #2a2a2a, #3a3a3a) for depth hierarchy
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #FFCDAA;
                font-size: 12px;
                font-weight: 500;
            }
            
            QGroupBox {
                font-weight: 600;
                border: 2px solid #EE8980;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 0.8em;
                background-color: #2a2a2a;
                color: #FFCDAA;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 10px 0 10px;
                color: #F14666;
                font-weight: 700;
                font-size: 14px;
            }
            
            QPushButton {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 80px;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #F14666;
                color: #ffffff;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
                border-color: #F14666;
            }
            
            QPushButton#primaryButton {
                background-color: #9CB898;
                border: 2px solid #9CB898;
                color: #1a1a1a;
                font-weight: 700;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #ACC8A8;
                border-color: #9CB898;
                color: #000000;
            }
            
            QPushButton#dangerButton {
                background-color: #F14666;
                border: 2px solid #F14666;
                color: #ffffff;
                font-weight: 700;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #FF5676;
                border-color: #F14666;
                color: #ffffff;
            }
            
            QProgressBar {
                border: 2px solid #EE8980;
                border-radius: 6px;
                text-align: center;
                height: 24px;
                background-color: #3a3a3a;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QProgressBar::chunk {
                background-color: #9CB898;
                border-radius: 4px;
                margin: 2px;
            }
            
            QTabWidget::pane {
                border: 2px solid #EE8980;
                border-radius: 8px;
                top: -1px;
                background-color: #2a2a2a;
            }
            
            QTabBar::tab {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 3px;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QTabBar::tab:selected {
                background-color: #2a2a2a;
                border-bottom: 2px solid #2a2a2a;
                border-left: 2px solid #F14666;
                border-right: 2px solid #F14666;
                border-top: 2px solid #F14666;
                color: #F14666;
                font-weight: 700;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #4a4a4a;
                border-color: #F14666;
                color: #ffffff;
            }
            
            QHeaderView::section {
                background-color: #3a3a3a;
                padding: 6px;
                border: 1px solid #EE8980;
                border-left: none;
                border-top: none;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QTextEdit, QListWidget {
                border: 2px solid #EE8980;
                border-radius: 6px;
                background-color: #3a3a3a;
                color: #FFCDAA;
                font-weight: 500;
                selection-background-color: #F14666;
                selection-color: #ffffff;
                padding: 5px;
            }
            
            QTextEdit:focus, QListWidget:focus {
                border-color: #F14666;
                background-color: #4a4a4a;
            }
            
            QLabel {
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QStatusBar {
                background-color: #3a3a3a;
                color: #FFCDAA;
                border-top: 2px solid #EE8980;
                font-weight: 600;
                padding: 4px;
            }
            
            QMenuBar {
                background-color: #3a3a3a;
                color: #FFCDAA;
                border-bottom: 2px solid #EE8980;
                font-weight: 600;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            
            QMenuBar::item:selected {
                background-color: #4a4a4a;
                color: #ffffff;
            }
            
            QMenu {
                background-color: #3a3a3a;
                color: #FFCDAA;
                border: 2px solid #F14666;
                border: 2px solid #F14666;
                border-radius: 6px;
                font-weight: 600;
                padding: 4px;
            }
            
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
                margin: 2px;
            }
            
            QMenu::item:selected {
                background-color: #EE8980;
                color: #ffffff;
            }
            
            #headerFrame {
                background-color: #F14666;
                color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                border: 2px solid #F14666;
            }
            
            #appTitle {
                color: white;
                font-size: 22px;
                font-weight: 700;
            }
            
            #pathLabel {
                font-weight: 600;
                padding: 8px 12px;
                background-color: #4a4a4a;
                border-radius: 6px;
                color: #FFCDAA;
                border: 1px solid #EE8980;
            }
            
            #actionButton {
                background-color: #F14666;
                color: white;
                border: 4px solid #F14666;
                border-radius: 6px;
                font-weight: 700;
                padding: 6px 12px;
                min-width: 120px;
                min-height: 32px;
                text-align: center;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #actionButton:hover {
                background-color: #FF5676;
                border: 4px solid #EE8980;
                color: #ffffff;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #actionButton:pressed {
                background-color: #E03256;
                border: 4px solid #FFCDAA;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #lastUpdateLabel {
                color: white;
                font-size: 12px;
                margin: 3px;
                font-weight: 600;
                background-color: rgba(255, 205, 170, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid rgba(255, 205, 170, 0.3);
            }
            
            #lastCheckedLabel {
                color: white;
                font-size: 11px;
                margin: 2px;
                font-style: italic;
                font-weight: 500;
                background-color: rgba(255, 205, 170, 0.1);
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid rgba(255, 205, 170, 0.2);
            }
            
            /* Scan report sections - enhanced readability */
            #resultsText {
                font-weight: 500;
                color: #FFCDAA;
                line-height: 1.4;
            }
            
            #reportViewer {
                font-weight: 500;
                color: #FFCDAA;
                line-height: 1.4;
            }
            
            /* Real-time protection status styles */
            #protectionStatus {
                font-size: 16px;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
            }
            
            /* Dashboard Status Cards with improved visual hierarchy */
            QFrame#statusCard {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
            }
            
            QFrame#statusCard:hover {
                border-color: #F14666;
                background-color: #4a4a4a;
            }
            
            QLabel#cardTitle {
                color: #FFCDAA;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }
            
            QLabel#cardValue {
                font-size: 28px;
                font-weight: 700;
                margin: 8px 0px;
            }
            
            QLabel#cardDescription {
                color: #EE8980;
                font-size: 11px;
                font-weight: 500;
                line-height: 1.4;
            }
            
            /* Dashboard Action Buttons with solid colors */
            QPushButton#dashboardPrimaryButton {
                background-color: #9CB898;
                border: 2px solid #9CB898;
                border-radius: 8px;
                color: #1a1a1a;
                font-weight: 700;
                font-size: 14px;
                min-height: 40px;
                padding: 0px 20px;
            }
            
            QPushButton#dashboardPrimaryButton:hover {
                background-color: #ACC8A8;
                border-color: #ACC8A8;
            }
            
            QPushButton#dashboardSecondaryButton {
                background-color: #4a4a4a;
                border: 2px solid #EE8980;
                border-radius: 8px;
                color: #FFCDAA;
                font-weight: 600;
                font-size: 13px;
                min-height: 40px;
                padding: 0px 16px;
            }
            
            QPushButton#dashboardSecondaryButton:hover {
                background-color: #5a5a5a;
                border-color: #F14666;
                color: #ffffff;
            }
            
            /* Preset Scan Buttons with enhanced styling */
            QPushButton#presetButton {
                background: #4a4a4a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 12px;
                min-height: 35px;
            }
            
            QPushButton#presetButton:hover {
                background: #5a5a5a;
                border-color: #F14666;
                color: #ffffff;
            }
            
            QLabel#presetLabel {
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 5px;
            }
            
            /* Scrollbar styling for consistency */
            QScrollBar:vertical {
                background-color: #3a3a3a;
                width: 12px;
                border-radius: 6px;
                border: 1px solid #EE8980;
            }
            
            QScrollBar::handle:vertical {
                background-color: #F14666;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #FF5676;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Settings Tab Controls */
            QCheckBox {
                color: #FFCDAA;
                font-weight: 500;
                font-size: 12px;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #EE8980;
                border-radius: 4px;
                background-color: #3a3a3a;
            }
            
            QCheckBox::indicator:checked {
                background-color: #9CB898;
                border-color: #9CB898;
            }
            
            QCheckBox::indicator:hover {
                border-color: #F14666;
            }
            
            QSpinBox {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                padding: 8px 12px;
                color: #FFCDAA;
                font-weight: 500;
                font-size: 12px;
            }
            
            QSpinBox:focus {
                border-color: #F14666;
                background-color: #2a2a2a;
            }
            
            QComboBox {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                padding: 8px 12px;
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
                border: 2px solid #EE8980;
                border-radius: 6px;
                color: #FFCDAA;
                selection-background-color: #F14666;
                selection-color: #ffffff;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 20px;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #EE8980;
                color: #ffffff;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #EE8980;
                border: none;
                border-radius: 3px;
                width: 16px;
                color: #1a1a1a;
                font-weight: 600;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #F14666;
            }
            
            QFormLayout QLabel {
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                padding: 5px;
            }
            
            QScrollArea {
                background-color: #1a1a1a;
                border: none;
            }
            
            /* Settings Tab Specific Widgets */
            QWidget#settingsTabWidget {
                background-color: #1a1a1a;
            }
            
            QScrollArea#settingsScrollArea {
                background-color: #1a1a1a;
                border: none;
            }
            
            QWidget#settingsScrollContent {
                background-color: #1a1a1a;
            }
        """)
        
        # Apply activity list styling after theme
        self.setup_activity_list_styling()
    
    def apply_light_theme(self):
        """Apply light theme styling using Sunrise color palette for optimal readability."""
        # Based on Color Theory principles:
        # - 75BDE0 (Sky Blue): Primary accent, trust and stability
        # - F8D49B (Golden Yellow): Secondary accent, warm energy  
        # - F8BC9B (Peach Orange): Interactive elements, friendly warmth
        # - F89B9B (Coral Pink): Danger/attention states, warm warnings
        # Light neutrals (#fefefe, #ffffff, #f5f5f5) for clean hierarchy
        
        self.setStyleSheet("""
            QMainWindow {
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
            
            QPushButton#primaryButton {
                background-color: #75BDE0;
                border: 2px solid #75BDE0;
                color: #ffffff;
                font-weight: 700;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #5AADD4;
                border-color: #5AADD4;
            }
            
            QPushButton#dangerButton {
                background-color: #F89B9B;
                border: 2px solid #F89B9B;
                color: #2c2c2c;
                font-weight: 700;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #F67B7B;
                border-color: #F67B7B;
            }
            
            QProgressBar {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                text-align: center;
                height: 24px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 600;
            }
            
            QProgressBar::chunk {
                background-color: #75BDE0;
                border-radius: 4px;
                margin: 2px;
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
            
            QHeaderView::section {
                background-color: #F8D49B;
                padding: 6px;
                border: 1px solid #F8BC9B;
                border-left: none;
                border-top: none;
                color: #2c2c2c;
                font-weight: 600;
            }
            
            QTextEdit, QListWidget {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 400;
                selection-background-color: #75BDE0;
                selection-color: #ffffff;
                padding: 5px;
            }
            
            QTextEdit:focus, QListWidget:focus {
                border-color: #75BDE0;
            }
            
            QLabel {
                color: #2c2c2c;
                font-weight: 600;
            }
            
            QStatusBar {
                background-color: #F8D49B;
                color: #2c2c2c;
                border-top: 2px solid #F8BC9B;
                font-weight: 600;
            }
            
            QMenuBar {
                background-color: #F8D49B;
                color: #2c2c2c;
                border-bottom: 2px solid #F8BC9B;
                font-weight: 600;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            
            QMenuBar::item:selected {
                background-color: #F8BC9B;
                color: #1a1a1a;
            }
            
            QMenu {
                background-color: #ffffff;
                color: #2c2c2c;
                border: 2px solid #75BDE0;
                border-radius: 6px;
                font-weight: 600;
            }
            
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
                margin: 2px;
            }
            
            QMenu::item:selected {
                background-color: #F8D49B;
                color: #2c2c2c;
            }
            
            #headerFrame {
                background-color: #75BDE0;
                color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                border: 2px solid #75BDE0;
            }
            
            #appTitle {
                color: white;
                font-size: 22px;
                font-weight: 700;
            }
            
            #pathLabel {
                font-weight: 600;
                padding: 8px;
                background-color: #F8D49B;
                border-radius: 6px;
                color: #2c2c2c;
                border: 1px solid #F8BC9B;
            }
            
            #actionButton {
                background-color: #75BDE0;
                color: white;
                border: 4px solid #75BDE0;
                border-radius: 6px;
                font-weight: 700;
                padding: 6px 12px;
                min-width: 120px;
                min-height: 32px;
                text-align: center;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #actionButton:hover {
                background-color: #5AADD4;
                border: 4px solid #F8BC9B;
                color: #ffffff;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #actionButton:pressed {
                background-color: #4A9DC4;
                border: 4px solid #F89B9B;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #lastUpdateLabel {
                color: #2c2c2c;
                font-size: 12px;
                margin: 3px;
                font-weight: 600;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid #F8D49B;
                text-align: center;
            }
            
            #lastCheckedLabel {
                color: #2c2c2c;
                font-size: 11px;
                margin: 2px;
                font-style: italic;
                font-weight: 500;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid #F8BC9B;
                text-align: center;
            }
            
            /* Scan report sections - enhanced readability with sunrise palette */
            #resultsText {
                font-weight: 400;
                line-height: 1.5;
                color: #2c2c2c;
                background-color: #ffffff;
                border: 2px solid #F8D49B;
                border-radius: 6px;
            }
            
            #reportViewer {
                font-weight: 400;
                line-height: 1.5;
                color: #2c2c2c;
            }
            
            /* Real-time protection status styles */
            #protectionStatus {
                font-size: 16px;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                background-color: #ffffff;
                border: 2px solid #F8D49B;
            }
            
            /* Dashboard Status Cards with solid colors */
            QFrame#statusCard {
                background-color: #ffffff;
                border: 2px solid #F8D49B;
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
            }
            
            QFrame#statusCard:hover {
                border-color: #75BDE0;
                background-color: #f8f8f8;
            }
            
            QLabel#cardTitle {
                color: #2c2c2c;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
            }
            
            QLabel#cardValue {
                font-size: 28px;
                font-weight: 700;
                margin: 8px 0px;
            }
            
            QLabel#cardDescription {
                color: #75BDE0;
                font-size: 11px;
                font-weight: 500;
                line-height: 1.4;
            }
            
            /* Dashboard Action Buttons with solid colors */
            QPushButton#dashboardPrimaryButton {
                background-color: #75BDE0;
                border: 2px solid #75BDE0;
                border-radius: 8px;
                color: #ffffff;
                font-weight: 700;
                font-size: 14px;
                min-height: 40px;
                padding: 0px 20px;
            }
            
            QPushButton#dashboardPrimaryButton:hover {
                background-color: #5AADD4;
                border-color: #5AADD4;
            }
            
            QPushButton#dashboardSecondaryButton {
                background-color: #F8D49B;
                border: 2px solid #F8BC9B;
                border-radius: 8px;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 13px;
                min-height: 40px;
                padding: 0px 16px;
            }
            
            QPushButton#dashboardSecondaryButton:hover {
                background-color: #F8BC9B;
                border-color: #F89B9B;
                color: #1a1a1a;
            }
            
            /* Preset Scan Buttons with sunrise styling */
            QPushButton#presetButton {
                background: #F8D49B;
                border: 2px solid #F8BC9B;
                border-radius: 6px;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 12px;
                min-height: 35px;
            }
            
            QPushButton#presetButton:hover {
                background: #F8BC9B;
                border-color: #75BDE0;
                color: #1a1a1a;
            }
            
            QLabel#presetLabel {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 5px;
            }
            
            /* Scrollbar styling for consistency */
            QScrollBar:vertical {
                background-color: #f8f8f8;
                width: 12px;
                border-radius: 6px;
                border: 1px solid #F8D49B;
            }
            
            QScrollBar::handle:vertical {
                background-color: #75BDE0;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #5AADD4;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Settings Tab Controls */
            QCheckBox {
                color: #333333;
                font-weight: 500;
                font-size: 12px;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #75BDE0;
                border-radius: 4px;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background-color: #75BDE0;
                border-color: #75BDE0;
            }
            
            QCheckBox::indicator:hover {
                border-color: #F8BC9B;
            }
            
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #75BDE0;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-weight: 500;
                font-size: 12px;
            }
            
            QSpinBox:focus {
                border-color: #F8BC9B;
                background-color: #f8f8f8;
            }
            
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #75BDE0;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-weight: 500;
                font-size: 12px;
                min-width: 120px;
            }
            
            QComboBox:focus {
                border-color: #F8BC9B;
                background-color: #f8f8f8;
            }
            
            QComboBox:hover {
                border-color: #F8BC9B;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #75BDE0;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #f0f0f0;
            }
            
            QComboBox::drop-down:hover {
                background-color: #F8BC9B;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #333333;
                width: 0px;
                height: 0px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #75BDE0;
                border-radius: 6px;
                color: #333333;
                selection-background-color: #F8BC9B;
                selection-color: #2c2c2c;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 20px;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #75BDE0;
                color: #ffffff;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #75BDE0;
                border: none;
                border-radius: 3px;
                width: 16px;
                color: #ffffff;
                font-weight: 600;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #F8BC9B;
            }
            
            QFormLayout QLabel {
                color: #333333;
                font-weight: 600;
                font-size: 12px;
                padding: 5px;
            }
            
            QScrollArea {
                background-color: #f8f8f8;
                border: none;
            }
            
            /* Settings Tab Specific Widgets */
            QWidget#settingsTabWidget {
                background-color: #f8f8f8;
            }
            
            QScrollArea#settingsScrollArea {
                background-color: #f8f8f8;
                border: none;
            }
            
            QWidget#settingsScrollContent {
                background-color: #f8f8f8;
            }
        """)
        
        # Apply activity list styling after theme
        self.setup_activity_list_styling()
    
    def apply_system_theme(self):
        """Apply system theme (falls back to light theme for now)."""
        # For now, system theme defaults to light theme
        # In a full implementation, you could detect system theme preference
        self.apply_light_theme()
        
    def set_scan_path(self, path):
        """Set the scan path and update the UI."""
        if os.path.exists(path):
            self.scan_path = path
            # Show a shortened version of the path for better readability
            if len(path) > 50:
                display_path = "..." + path[-47:]
            else:
                display_path = path
            self.path_label.setText(display_path)
            self.path_label.setToolTip(path)  # Full path in tooltip
        else:
            self.show_themed_message_box("warning", "Warning", f"Path does not exist: {path}")
        
    def select_scan_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if path:
            self.scan_path = path
            self.path_label.setText(path)
            
    def start_scan(self, quick_scan=False):
        if not hasattr(self, 'scan_path'):
            self.show_themed_message_box("warning", "Warning", "Please select a path to scan first.")
            return
            
        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        
        # Check if this is a full system scan and RKHunter integration is enabled
        is_full_system_scan = (hasattr(self, 'scan_path') and 
                               (self.scan_path == '/' or self.scan_path == str(Path.home())))
        
        rkhunter_settings = self.config.get('rkhunter_settings', {})
        should_run_rkhunter = (is_full_system_scan and 
                               rkhunter_settings.get('enabled', False) and
                               rkhunter_settings.get('run_with_full_scan', False) and
                               self.rkhunter.is_available())
        
        if should_run_rkhunter:
            # Show confirmation for combined scan
            reply = QMessageBox.question(
                self,
                "Combined Security Scan",
                "This appears to be a full system scan with RKHunter integration enabled.\n\n"
                "Would you like to run both ClamAV and RKHunter scans together?\n\n"
                "• ClamAV will scan for viruses, malware, and trojans\n"
                "• RKHunter will scan for rootkits and system integrity issues\n\n"
                "This will provide the most comprehensive security analysis.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.results_text.append("🔒 Starting comprehensive security scan...")
                self.results_text.append("📊 Running ClamAV scan first, followed by RKHunter...")
                # Start combined scan
                self.start_combined_security_scan(quick_scan)
                return
        
        # Start regular scan in separate thread with quick scan option
        self.current_scan_thread = ScanThread(self.scanner, self.scan_path, quick_scan=quick_scan)
        self.current_scan_thread.progress_updated.connect(self.progress_bar.setValue)
        self.current_scan_thread.status_updated.connect(self.status_label.setText)
        self.current_scan_thread.scan_completed.connect(self.scan_completed)
        self.current_scan_thread.start()
    
    def start_combined_security_scan(self, quick_scan=False):
        """Start a combined ClamAV + RKHunter security scan."""
        # Start ClamAV scan first
        self.current_scan_thread = ScanThread(self.scanner, self.scan_path, quick_scan=quick_scan)
        self.current_scan_thread.progress_updated.connect(self.progress_bar.setValue)
        self.current_scan_thread.status_updated.connect(self.status_label.setText)
        self.current_scan_thread.scan_completed.connect(self.clamav_scan_completed_start_rkhunter)
        self.current_scan_thread.start()
    
    def clamav_scan_completed_start_rkhunter(self, clamav_result):
        """Handle ClamAV scan completion and start RKHunter scan."""
        # Display ClamAV results first
        self.display_scan_results(clamav_result)
        
        # Add separator
        self.results_text.append("\n" + "="*60 + "\n")
        
        # Check if RKHunter should still run
        if not self.rkhunter.is_available():
            self.results_text.append("❌ RKHunter not available, skipping rootkit scan")
            self.scan_completed(clamav_result)
            return
        
        # Start RKHunter scan automatically
        self.results_text.append("🔍 Starting RKHunter rootkit scan...\n")
        self.status_label.setText("Running RKHunter rootkit scan...")
        
        # Get test categories from settings
        test_categories = self.get_selected_rkhunter_categories()
        
        self.current_rkhunter_thread = RKHunterScanThread(self.rkhunter, test_categories)
        self.current_rkhunter_thread.progress_updated.connect(self.update_rkhunter_progress)
        self.current_rkhunter_thread.scan_completed.connect(
            lambda rk_result: self.combined_scan_completed(clamav_result, rk_result)
        )
        self.current_rkhunter_thread.start()
    
    def combined_scan_completed(self, clamav_result, rkhunter_result: RKHunterScanResult):
        """Handle completion of combined ClamAV + RKHunter scan."""
        # Display RKHunter results
        self.display_rkhunter_results(rkhunter_result)
        
        # Save both reports
        self.save_rkhunter_report(rkhunter_result)
        
        # Create combined summary
        self.results_text.append("\n" + "="*60)
        self.results_text.append("\n🔒 COMPREHENSIVE SECURITY SCAN SUMMARY")
        self.results_text.append("="*60)
        
        # ClamAV summary
        clamav_threats = 0
        if isinstance(clamav_result, dict):
            clamav_threats = clamav_result.get('threats_found', len(clamav_result.get('threats', [])))
        else:
            clamav_threats = getattr(clamav_result, 'threats_found', 0)
        
        self.results_text.append(f"\n📊 ClamAV Results:")
        self.results_text.append(f"   • Threats Found: {clamav_threats}")
        
        # RKHunter summary
        self.results_text.append(f"\n🔍 RKHunter Results:")
        self.results_text.append(f"   • Warnings: {rkhunter_result.warnings_found}")
        self.results_text.append(f"   • Infections: {rkhunter_result.infections_found}")
        
        # Overall assessment
        total_issues = clamav_threats + rkhunter_result.warnings_found + rkhunter_result.infections_found
        
        if total_issues == 0:
            self.results_text.append(f"\n✅ **SYSTEM CLEAN**")
            self.results_text.append("   No threats or suspicious activity detected.")
        elif rkhunter_result.infections_found > 0:
            self.results_text.append(f"\n🚨 **CRITICAL SECURITY ISSUES DETECTED**")
            self.results_text.append("   Potential rootkits found - immediate action required!")
        elif clamav_threats > 0 or rkhunter_result.warnings_found > 0:
            self.results_text.append(f"\n⚠️  **SECURITY ISSUES DETECTED**")
            self.results_text.append("   Review findings and take appropriate action.")
        
        self.results_text.append("\n" + "="*60)
        
        # Complete the scan
        self.scan_completed(clamav_result)
    
    def install_rkhunter(self):
        """Install or configure RKHunter."""
        self.rkhunter_scan_btn.setEnabled(False)
        self.rkhunter_scan_btn.setText("Checking...")
        
        # First check if RKHunter is actually installed but has permission issues
        if self.rkhunter.rkhunter_path and Path(self.rkhunter.rkhunter_path).exists():
            # RKHunter is installed but may need configuration
            reply = QMessageBox.question(
                self, 
                "RKHunter Configuration",
                "RKHunter is installed but requires elevated privileges to run.\n\n"
                "This is normal for rootkit scanners as they need system-level access.\n"
                "You will be prompted for your password when running scans.\n\n"
                "Continue to enable RKHunter scanning?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Test if it works with sudo
                try:
                    result = subprocess.run(
                        ['sudo', '-v'],  # Validate sudo access
                        capture_output=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        self.show_themed_message_box("information", "RKHunter Ready", 
                                                   "RKHunter is now configured and ready to use!\n\n"
                                                   "You can run rootkit scans from the scan tab.")
                        
                        # Update button to scan mode
                        self.rkhunter_scan_btn.setText("🔍 RKHunter Scan")
                        self.rkhunter_scan_btn.setToolTip("Run RKHunter rootkit detection scan\n(Configure scan categories in Settings → Scanning)")
                        self.rkhunter_scan_btn.clicked.disconnect()
                        self.rkhunter_scan_btn.clicked.connect(self.start_rkhunter_scan)
                        self.rkhunter_scan_btn.setEnabled(True)
                        return
                    
                except subprocess.SubprocessError:
                    pass
            
            self.rkhunter_scan_btn.setText("📦 Install RKHunter")
            self.rkhunter_scan_btn.setEnabled(True)
            return
        
        # Show installation confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Install RKHunter",
            "RKHunter will be installed to provide rootkit detection capabilities.\n\n"
            "This requires administrator privileges. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            self.rkhunter_scan_btn.setEnabled(True)
            self.rkhunter_scan_btn.setText("📦 Install RKHunter")
            return
        
        self.rkhunter_scan_btn.setText("Installing...")
        
        try:
            success, message = self.rkhunter.install_rkhunter()
            
            if success:
                self.show_themed_message_box("information", "Success", 
                                           f"RKHunter installed successfully!\n{message}")
                
                # Update button to scan mode
                self.rkhunter_scan_btn.setText("🔍 RKHunter Scan")
                self.rkhunter_scan_btn.setToolTip("Run RKHunter rootkit detection scan")
                self.rkhunter_scan_btn.clicked.disconnect()
                self.rkhunter_scan_btn.clicked.connect(self.start_rkhunter_scan)
                self.rkhunter_scan_btn.setEnabled(True)
                
            else:
                self.show_themed_message_box("critical", "Installation Failed", 
                                           f"Failed to install RKHunter:\n{message}")
                self.rkhunter_scan_btn.setText("📦 Install RKHunter")
                self.rkhunter_scan_btn.setEnabled(True)
                
        except Exception as e:
            self.show_themed_message_box("critical", "Installation Error", 
                                       f"Error during installation:\n{str(e)}")
            self.rkhunter_scan_btn.setText("📦 Install RKHunter")
            self.rkhunter_scan_btn.setEnabled(True)
    
    def start_rkhunter_scan(self):
        """Start an RKHunter rootkit scan."""
        # Check if already running
        if self.current_rkhunter_thread and self.current_rkhunter_thread.isRunning():
            self.show_themed_message_box("warning", "Scan in Progress", 
                                       "RKHunter scan is already running.")
            return
        
        # Check if RKHunter is functional (this may prompt for permissions)
        if not self.rkhunter.is_functional():
            # Check authentication method available
            pkexec_available = self.rkhunter._find_executable('pkexec')
            
            if pkexec_available:
                auth_method_text = (
                    "RKHunter requires elevated privileges to perform rootkit scans.\n\n"
                    "This is normal security behavior for rootkit detection tools.\n"
                    "A secure GUI password dialog will appear during the scan (same as Update Definitions).\n\n"
                    "Would you like to:\n\n"
                    "• Continue and start the scan (GUI password dialog will appear)\n"
                    "• Configure RKHunter setup first"
                )
            else:
                auth_method_text = (
                    "RKHunter requires elevated privileges to perform rootkit scans.\n\n"
                    "This is normal security behavior for rootkit detection tools.\n"
                    "You will be prompted for your administrator password in the terminal.\n\n"
                    "Would you like to:\n\n"
                    "• Continue and start the scan (terminal password prompt will appear)\n"
                    "• Configure RKHunter setup first"
                )
            
            reply = QMessageBox.question(
                self,
                "RKHunter Setup Required",
                auth_method_text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                self.install_rkhunter()  # Show configuration dialog
                return
        
        # Check if regular scan is running
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Scan in Progress",
                "A regular antivirus scan is currently running.\n\n"
                "Do you want to continue with RKHunter scan in parallel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Get test categories from settings
        test_categories = self.get_selected_rkhunter_categories()
        
        # Show final confirmation with password warning
        auth_dialog = QMessageBox(self)
        auth_dialog.setIcon(QMessageBox.Icon.Information)
        auth_dialog.setWindowTitle("Authentication Required")
        auth_dialog.setText("Ready to Start RKHunter Scan")
        
        # Check if GUI authentication is available
        pkexec_available = self.rkhunter._find_executable('pkexec')
        
        # Build scan categories description for user
        category_names = {
            'system_commands': 'System Commands',
            'rootkits': 'Rootkits & Trojans',
            'network': 'Network Security',
            'system_integrity': 'System Integrity',
            'applications': 'Applications'
        }
        
        selected_category_names = [category_names.get(cat, cat) for cat in test_categories if cat in category_names and category_names.get(cat)]
        categories_text = ", ".join(selected_category_names) if selected_category_names else "Default categories"
        
        if pkexec_available:
            auth_dialog.setInformativeText(
                f"RKHunter will now scan your system for rootkits and malware.\n\n"
                f"Scan categories: {categories_text}\n\n"
                "🔐 A secure password dialog will appear to authorize the scan. "
                "This uses the same authentication method as 'Update Definitions'.\n\n"
                "The scan may take several minutes to complete."
            )
        else:
            auth_dialog.setInformativeText(
                f"RKHunter will now scan your system for rootkits and malware.\n\n"
                f"Scan categories: {categories_text}\n\n"
                "🔐 You may be prompted for your administrator password in the terminal "
                "to authorize the scan.\n\n"
                "The scan may take several minutes to complete."
            )
        
        auth_dialog.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        auth_dialog.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        if auth_dialog.exec() != QMessageBox.StandardButton.Ok:
            return
        
        # Start RKHunter scan in thread
        self.rkhunter_scan_btn.setEnabled(False)
        self.rkhunter_scan_btn.setText("🔄 Scanning...")
        
        self.current_rkhunter_thread = RKHunterScanThread(self.rkhunter, test_categories)
        self.current_rkhunter_thread.progress_updated.connect(self.update_rkhunter_progress)
        self.current_rkhunter_thread.scan_completed.connect(self.rkhunter_scan_completed)
        self.current_rkhunter_thread.start()
        
        # Update status
        self.status_label.setText("Running RKHunter rootkit scan...")
        self.results_text.append("\n🔍 RKHunter rootkit scan started...\n")
    
    def update_rkhunter_progress(self, message):
        """Update progress display for RKHunter scan."""
        self.status_label.setText(f"RKHunter: {message}")
    
    def rkhunter_scan_completed(self, result: RKHunterScanResult):
        """Handle completion of RKHunter scan."""
        self.rkhunter_scan_btn.setEnabled(True)
        self.rkhunter_scan_btn.setText("🔍 RKHunter Scan")
        
        if not result.success:
            self.results_text.append(f"❌ RKHunter scan failed: {result.error_message}")
            self.status_label.setText("RKHunter scan failed")
            return
        
        # Display results
        self.display_rkhunter_results(result)
        
        # Save results to report
        self.save_rkhunter_report(result)
        
        self.status_label.setText("RKHunter scan completed")
    
    def display_rkhunter_results(self, result: RKHunterScanResult):
        """Display RKHunter scan results in the results text area."""
        output = "\n🔍 RKHunter Rootkit Scan Results\n"
        output += "=" * 50 + "\n"
        
        # Scan summary
        duration = (result.end_time - result.start_time).total_seconds() if result.end_time else 0
        output += f"Scan Duration: {duration:.1f} seconds\n"
        output += f"Tests Run: {result.tests_run}\n"
        output += f"Warnings: {result.warnings_found}\n"
        output += f"Infections: {result.infections_found}\n"
        output += f"Skipped: {result.skipped_tests}\n\n"
        
        # Overall status
        if result.infections_found > 0:
            output += "🚨 **CRITICAL**: Potential rootkits detected!\n\n"
        elif result.warnings_found > 0:
            output += "⚠️  Warnings found - review carefully\n\n"
        else:
            output += "✅ No rootkits detected\n\n"
        
        # Detailed findings
        if result.findings:
            output += "Detailed Findings:\n"
            for finding in result.findings:
                status_icon = "🚨" if finding.result.value == "infected" else "⚠️"
                output += f"\n{status_icon} {finding.test_name}\n"
                output += f"   Result: {finding.result.value.upper()}\n"
                output += f"   Severity: {finding.severity.value.upper()}\n"
                output += f"   Description: {finding.description}\n"
                if finding.details:
                    output += f"   Details: {finding.details}\n"
        
        # Recommendations
        recommendations = self.rkhunter.get_scan_recommendations(result)
        if recommendations:
            output += "\n\nRecommendations:\n"
            for rec in recommendations:
                output += f"{rec}\n"
        
        self.results_text.append(output)
    
    def save_rkhunter_report(self, result: RKHunterScanResult):
        """Save RKHunter scan results to a report file."""
        try:
            reports_dir = Path.home() / ".local/share/search-and-destroy/rkhunter_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"rkhunter_scan_{result.scan_id}.json"
            
            # Convert result to dictionary for JSON serialization
            report_data = {
                "scan_id": result.scan_id,
                "scan_type": "rkhunter_rootkit_scan",
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "duration": (result.end_time - result.start_time).total_seconds() if result.end_time else 0,
                "success": result.success,
                "summary": result.scan_summary,
                "statistics": {
                    "total_tests": result.total_tests,
                    "tests_run": result.tests_run,
                    "warnings_found": result.warnings_found,
                    "infections_found": result.infections_found,
                    "skipped_tests": result.skipped_tests
                },
                "findings": [
                    {
                        "test_name": finding.test_name,
                        "result": finding.result.value,
                        "severity": finding.severity.value,
                        "description": finding.description,
                        "details": finding.details,
                        "file_path": finding.file_path,
                        "recommendation": finding.recommendation,
                        "timestamp": finding.timestamp.isoformat() if finding.timestamp else None
                    }
                    for finding in (result.findings or [])
                ],
                "recommendations": self.rkhunter.get_scan_recommendations(result),
                "error_message": result.error_message
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"RKHunter report saved to {report_file}")
            
        except Exception as e:
            print(f"Error saving RKHunter report: {e}")
    
    def get_selected_rkhunter_categories(self):
        """Get list of selected RKHunter test categories from settings."""
        if not hasattr(self, 'settings_rkhunter_category_checkboxes'):
            # Return default categories if settings aren't loaded yet
            return ['system_commands', 'rootkits', 'network', 'system_integrity']
        
        selected = []
        for category_id, checkbox in self.settings_rkhunter_category_checkboxes.items():
            if checkbox.isChecked():
                selected.append(category_id)
        
        # Return default categories if nothing selected
        return selected if selected else ['system_commands', 'rootkits', 'network', 'system_integrity']
    
    def select_all_rkhunter_categories(self):
        """Select all RKHunter test categories."""
        if hasattr(self, 'settings_rkhunter_category_checkboxes'):
            for checkbox in self.settings_rkhunter_category_checkboxes.values():
                checkbox.setChecked(True)
    
    def select_recommended_rkhunter_categories(self):
        """Select recommended RKHunter test categories."""
        if hasattr(self, 'settings_rkhunter_category_checkboxes'):
            recommended = {'system_commands', 'rootkits', 'network', 'system_integrity'}
            for category_id, checkbox in self.settings_rkhunter_category_checkboxes.items():
                checkbox.setChecked(category_id in recommended)
    
    def select_no_rkhunter_categories(self):
        """Deselect all RKHunter test categories."""
        if hasattr(self, 'settings_rkhunter_category_checkboxes'):
            for checkbox in self.settings_rkhunter_category_checkboxes.values():
                checkbox.setChecked(False)
    
    def stop_scan(self):
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            self.current_scan_thread.terminate()
            self.scan_completed({'status': 'cancelled'})
    
    def update_dashboard_cards(self):
        """Update all dashboard status cards with current information."""
        # Update Last Scan card
        if hasattr(self, 'last_scan_card'):
            try:
                # Get the most recent scan report from the reports directory
                reports_dir = Path.home() / ".local/share/search-and-destroy/scan_reports/daily"
                if reports_dir.exists():
                    report_files = list(reports_dir.glob("scan_*.json"))
                    if report_files:
                        # Get the most recent file
                        latest_file = max(report_files, key=lambda p: p.stat().st_mtime)
                        try:
                            with open(latest_file, 'r', encoding='utf-8') as f:
                                report_data = json.load(f)
                            
                            scan_time = report_data.get('scan_metadata', {}).get('timestamp', '')
                            if scan_time:
                                try:
                                    scan_date = datetime.fromisoformat(scan_time.replace('Z', '+00:00'))
                                    formatted_date = scan_date.strftime("%m/%d %H:%M")
                                except (ValueError, AttributeError):
                                    formatted_date = "Recently"
                            else:
                                formatted_date = "Recently"
                                
                            threats_count = len(report_data.get('threats', []))
                            
                            # Update the card
                            for child in self.last_scan_card.findChildren(QLabel):
                                if child.objectName() == "cardValue":
                                    child.setText(formatted_date)
                                    child.setStyleSheet("color: #17a2b8; font-size: 20px; font-weight: bold;")
                                elif child.objectName() == "cardDescription":
                                    child.setText(f"Found {threats_count} threats" if threats_count > 0 else "No threats found")
                                    
                            # Update Threats Found card
                            if hasattr(self, 'threats_card'):
                                for child in self.threats_card.findChildren(QLabel):
                                    if child.objectName() == "cardValue":
                                        child.setText(str(threats_count))
                                        color = "#dc3545" if threats_count > 0 else "#28a745"
                                        child.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
                                    elif child.objectName() == "cardDescription":
                                        child.setText("Threats detected - review quarantine" if threats_count > 0 else "No threats detected in recent scans")
                        except (OSError, ValueError, KeyError) as file_error:
                            print(f"Error reading report file: {file_error}")
                            
            except (OSError, ImportError) as e:
                print(f"Error updating dashboard cards: {e}")
                
    def scan_completed(self, result):
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        
        # Reset quick scan button if it was a quick scan
        if hasattr(self, 'is_quick_scan_running') and self.is_quick_scan_running:
            self.reset_quick_scan_button()
        
        if 'error' in result:
            error_msg = result['error']
            self.results_text.setText(f"Scan error: {error_msg}")
            self.status_bar.showMessage(f"Scan failed: {error_msg}")
            return
            
        # Handle cancelled scans
        if result.get('status') == 'cancelled':
            cancel_msg = result.get('message', 'Scan was cancelled')
            self.results_text.setText(cancel_msg)
            self.status_bar.showMessage(cancel_msg)
            return
            
        # Save the scan result to a report file
        try:
            # Create a proper ScanResult object from the dictionary
            scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Handle both dictionary and dataclass result formats
            if isinstance(result, dict):
                total_files = result.get('total_files', 0)
                scanned_files = result.get('scanned_files', result.get('files_scanned', 0))
                threats_found = result.get('threats_found', len(result.get('threats', [])))
                duration = result.get('duration', result.get('scan_time', 0))
                threats_data = result.get('threats', [])
            else:
                # Assume it's already a proper result object
                total_files = getattr(result, 'total_files', 0)
                scanned_files = getattr(result, 'scanned_files', 0)
                threats_found = getattr(result, 'threats_found', 0)
                duration = getattr(result, 'duration', 0)
                threats_data = getattr(result, 'threats', [])
            
            # Convert threat dictionaries to ThreatInfo objects if any
            threats = []
            for threat_data in threats_data:
                if isinstance(threat_data, dict):
                    # Create ThreatInfo object from the dictionary
                    threat = ThreatInfo(
                        file_path=threat_data.get('file_path', threat_data.get('file', '')),
                        threat_name=threat_data.get('threat_name', threat_data.get('threat', '')),
                        threat_type=threat_data.get('threat_type', threat_data.get('type', 'virus')),
                        threat_level=ThreatLevel.INFECTED,
                        action_taken=threat_data.get('action_taken', threat_data.get('action', 'none')),
                        timestamp=datetime.now().isoformat(),
                        file_size=threat_data.get('file_size', threat_data.get('size', 0)),
                        file_hash=threat_data.get('file_hash', threat_data.get('hash', ''))
                    )
                else:
                    # Already a ThreatInfo object
                    threat = threat_data
                threats.append(threat)
            
            # Create the ScanResult object
            scan_result = ScanResult(
                scan_id=scan_id,
                scan_type=ScanType.CUSTOM,
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration=duration,
                scanned_paths=[self.scan_path],
                total_files=total_files,
                scanned_files=scanned_files,
                threats_found=threats_found,
                threats=threats,
                errors=[],
                scan_settings={},
                engine_version="1.0",
                signature_version="1.0",
                success=True
            )
            
            # Save the scan result
            self.report_manager.save_scan_result(scan_result)
            
            # Refresh the reports list if we're on the reports tab
            if self.tab_widget.currentIndex() == 1:  # Reports tab
                self.refresh_reports()
                
        except (OSError, IOError, json.JSONDecodeError) as e:
            print(f"Error saving scan report: {e}")
        
        # Display the results in the UI
        self.display_scan_results(result)
        
        # Update dashboard cards with new scan information
        self.update_dashboard_cards()
    
    def display_scan_results(self, result):
        output = "Scan completed successfully!\n\n"
        
        # Handle both dictionary and dataclass result formats
        if isinstance(result, dict):
            files_scanned = result.get('scanned_files', result.get('files_scanned', 0))
            threats_found = result.get('threats_found', len(result.get('threats', [])))
            scan_time = result.get('duration', result.get('scan_time', 'Unknown'))
            threats = result.get('threats', [])
        else:
            # Assume it's a dataclass-like object
            files_scanned = getattr(result, 'scanned_files', 0)
            threats_found = getattr(result, 'threats_found', 0)
            scan_time = getattr(result, 'duration', 'Unknown')
            threats = getattr(result, 'threats', [])
        
        # Format scan time nicely
        if isinstance(scan_time, (int, float)) and scan_time != 'Unknown':
            if scan_time < 60:
                formatted_time = f"{scan_time:.1f} seconds"
            else:
                minutes = int(scan_time // 60)
                seconds = scan_time % 60
                formatted_time = f"{minutes}m {seconds:.1f}s"
        else:
            formatted_time = str(scan_time)
        
        output += f"Files scanned: {files_scanned}\n"
        output += f"Threats found: {threats_found}\n"
        output += f"Scan time: {formatted_time}\n\n"
        
        if threats:
            output += "Threats detected:\n"
            for threat in threats:
                if isinstance(threat, dict):
                    file_path = threat.get('file_path', threat.get('file', 'Unknown'))
                    threat_name = threat.get('threat_name', threat.get('threat', 'Unknown'))
                else:
                    file_path = getattr(threat, 'file_path', 'Unknown')
                    threat_name = getattr(threat, 'threat_name', 'Unknown')
                output += f"  - {file_path}: {threat_name}\n"
        
        self.results_text.setText(output)
    
    def quick_scan(self):
        # Toggle quick scan based on current state
        if self.is_quick_scan_running:
            # Stop the quick scan
            self.stop_quick_scan()
        else:
            # Start a quick scan
            self.start_quick_scan()
    
    def start_quick_scan(self):
        """Start a quick scan and update button state."""
        # Quick scan targets common infection vectors, not entire home directory
        # This prevents crashes from scanning millions of files
        import tempfile
        
        quick_scan_paths = [
            os.path.expanduser("~/Downloads"),      # Most common infection vector
            os.path.expanduser("~/Desktop"),        # User accessible files
            os.path.expanduser("~/Documents"),      # User documents
            tempfile.gettempdir(),                  # Temporary files
            "/tmp" if os.path.exists("/tmp") else None,  # System temp (Linux)
        ]
        
        # Filter out non-existent paths
        valid_paths = [path for path in quick_scan_paths if path and os.path.exists(path)]
        
        if not valid_paths:
            self.show_themed_message_box("warning", "Warning", "No valid directories found for quick scan.")
            self.reset_quick_scan_button()
            return
        
        # Use the first valid path (Downloads is most important)
        self.scan_path = valid_paths[0]
        self.path_label.setText(f"Quick Scan ({os.path.basename(self.scan_path)})")
        
        # Update button state
        self.is_quick_scan_running = True
        self.quick_scan_btn.setText("Stop Quick Scan")
        
        # Start the scan with file limit for quick scans
        self.start_scan(quick_scan=True)
    
    def stop_quick_scan(self):
        """Stop the quick scan and reset button state."""
        try:
            if hasattr(self, 'current_scan_thread') and self.current_scan_thread and self.current_scan_thread.isRunning():
                # Gracefully stop the thread
                self.current_scan_thread.terminate()
                # Give the thread time to clean up
                self.current_scan_thread.wait(3000)  # Wait up to 3 seconds
                
                # Force completion if thread hasn't terminated
                if self.current_scan_thread.isRunning():
                    print("Warning: Scan thread did not terminate gracefully")
                
                self.scan_completed({'status': 'cancelled', 'message': 'Quick scan cancelled by user'})
        except (RuntimeError, AttributeError) as e:
            print(f"Error stopping quick scan: {e}")
        finally:
            # Always reset button state
            self.reset_quick_scan_button()
    
    def reset_quick_scan_button(self):
        """Reset the quick scan button to its initial state."""
        self.is_quick_scan_running = False
        self.quick_scan_btn.setText("Quick Scan")
    
    def update_definitions(self):
        """Update virus definitions with progress dialog and user feedback."""
        try:
            # First check if definitions need updating
            freshness = self.scanner.clamav_wrapper.check_definition_freshness()
            
            # Create and show progress dialog
            progress_dialog = QProgressDialog("Checking virus definitions...", "Cancel", 0, 100, self)
            progress_dialog.setWindowTitle("Updating Virus Definitions")
            progress_dialog.setModal(True)
            progress_dialog.setValue(0)
            progress_dialog.show()
            
            # Start update in background thread with progress callbacks
            from threading import Thread
            import time
            
            self.update_result = None
            self.update_progress = 0
            self.update_status = "Initializing..."
            
            def run_update():
                try:
                    # Update progress
                    self.update_status = "Checking current definitions..."
                    self.update_progress = 10
                    
                    # Check if update is needed
                    if not freshness.get('needs_update', True):
                        self.update_status = "Definitions are already up to date"
                        self.update_progress = 100
                        self.update_result = True
                        return
                    
                    self.update_status = "Starting virus definition update..."
                    self.update_progress = 20
                    time.sleep(0.5)
                    
                    # Check if we need sudo by testing write permissions first
                    clamav_db_dir = "/var/lib/clamav"
                    needs_sudo = not os.access(clamav_db_dir, os.W_OK) if os.path.exists(clamav_db_dir) else True
                    
                    if needs_sudo:
                        self.update_status = "Administrator permissions required - please check your terminal"
                        self.update_progress = 30
                        # Give user time to see the message
                        time.sleep(2)
                    else:
                        self.update_status = "Attempting direct update..."
                        self.update_progress = 30
                    
                    # Call the actual update method
                    success = self.scanner.update_virus_definitions()
                    
                    if success:
                        self.update_status = "Virus definitions updated successfully!"
                        self.update_progress = 100
                        self.update_result = True
                    else:
                        self.update_status = "Failed to update virus definitions"
                        self.update_progress = 100
                        self.update_result = False
                        
                except (subprocess.CalledProcessError, OSError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                    self.update_status = f"Error updating definitions: {e}"
                    self.update_progress = 100
                    self.update_result = False
            
            # Start update thread
            update_thread = Thread(target=run_update)
            update_thread.daemon = True
            update_thread.start()
            
            # Create timer to update progress dialog
            timer = QTimer()
            dialog_closed = False
            
            def update_progress():
                nonlocal dialog_closed
                
                if dialog_closed:
                    return
                
                # Handle cancel button first (before processing updates)
                if progress_dialog.wasCanceled():
                    timer.stop()
                    dialog_closed = True
                    progress_dialog.close()
                    self.status_bar.showMessage("Virus definition update cancelled", 3000)
                    return
                    
                if hasattr(self, 'update_progress'):
                    progress_dialog.setValue(self.update_progress)
                    progress_dialog.setLabelText(self.update_status)
                    
                    # Check if completed
                    if self.update_progress >= 100:
                        timer.stop()
                        dialog_closed = True
                        progress_dialog.close()
                        
                        # Show result message
                        if hasattr(self, 'update_result'):
                            if self.update_result:
                                self.show_themed_message_box("information", "Update Complete", 
                                                      "Virus definitions updated successfully!")
                                self.status_bar.showMessage("Virus definitions updated successfully", 5000)
                                # Refresh the definition status display with a small delay
                                QTimer.singleShot(500, self.update_definition_status)
                            else:
                                self.show_themed_message_box("warning", "Update Failed", 
                                                  f"Failed to update virus definitions.\n\n"
                                                  f"Status: {self.update_status}\n\n"
                                                  f"You may need to:\n"
                                                  f"• Run the application as administrator\n"
                                                  f"• Check your internet connection\n"
                                                  f"• Verify ClamAV is properly installed")
                                self.status_bar.showMessage("Failed to update virus definitions", 5000)
                        return
            
            timer.timeout.connect(update_progress)
            timer.start(250)  # Update every 250ms
            
        except (OSError, IOError, RuntimeError) as e:
            self.show_themed_message_box("critical", "Update Error", f"Could not start update: {e}")
    
    def refresh_quarantine(self):
        """Load and display quarantined files."""
        try:
            # Clear the current list
            self.quarantine_list.clear()
            
            # Get quarantine directory from config
            from utils.config import QUARANTINE_DIR
            
            # Verify the directory exists
            if not QUARANTINE_DIR.exists():
                return
                
            # Find all quarantined files
            quarantine_files = list(QUARANTINE_DIR.glob("*.quarantine"))
            
            if not quarantine_files:
                return
                
            # Add to list widget
            for qfile in quarantine_files:
                # Extract original filename from quarantine file
                original_name = qfile.stem
                item = QListWidgetItem(original_name)
                item.setData(Qt.ItemDataRole.UserRole, str(qfile))
                self.quarantine_list.addItem(item)
                
        except (OSError, IOError, PermissionError) as e:
            self.status_bar.showMessage(f"Error loading quarantine: {e}", 5000)
    
    def show_about(self):
        self.show_themed_message_box("information", "About S&D", 
                         """<h1>S&D - Search & Destroy</h1>
                         <p>A modern GUI for ClamAV virus scanning.</p>
                         <p>Version 1.0.0</p>
                         <p>© 2025 xanadOS</p>""")
    
    def update_definition_status(self):
        """Update the last virus definition update time display."""
        # Set the "Last Checked" timestamp to now
        current_time = datetime.now()
        formatted_checked = current_time.strftime("%Y-%m-%d %H:%M")
        self.last_checked_label.setText(f"Last checked: {formatted_checked}")
        
        try:
            freshness = self.scanner.clamav_wrapper.check_definition_freshness()
            
            # Handle error cases gracefully
            if freshness.get('error'):
                print(f"Warning: Error checking definitions: {freshness['error']}")
                self.last_update_label.setText("Status: Check failed")
                return
            
            if freshness.get('last_update'):
                # Handle different types of last_update values
                last_update_value = freshness['last_update']
                
                if last_update_value == "No definitions found":
                    self.last_update_label.setText("Status: No definitions")
                elif last_update_value.startswith("Error:"):
                    self.last_update_label.setText("Status: Check failed")
                else:
                    # Parse the date string and format it nicely
                    try:
                        last_update = datetime.fromisoformat(last_update_value.replace('Z', '+00:00'))
                        # Format as readable date
                        formatted_date = last_update.strftime("%Y-%m-%d %H:%M")
                        label_text = f"Last updated: {formatted_date}"
                        self.last_update_label.setText(label_text)
                    except (ValueError, AttributeError):
                        # If parsing fails, show the raw date
                        label_text = f"Last updated: {last_update_value}"
                        self.last_update_label.setText(label_text)
            else:
                # Check if definitions exist at all
                if freshness.get('definitions_exist', False):
                    self.last_update_label.setText("Last updated: Unknown")
                else:
                    self.last_update_label.setText("Status: No definitions")
                    
        except Exception as e:
            print(f"Error checking definition status: {e}")
            self.last_update_label.setText("Status: Error checking")
            self.last_checked_label.setText(f"Last checked: {formatted_checked} (error)")
            
            # Try a fallback method using clamscan --version (doesn't require sudo)
            try:
                result = subprocess.run(['clamscan', '--version'], 
                                      capture_output=True, text=True, timeout=10, check=False)
                if result.returncode == 0:
                    # If clamscan works, definitions are probably there, just couldn't access them
                    self.last_update_label.setText("Status: Permissions issue")
                else:
                    self.last_update_label.setText("Status: ClamAV not found")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                self.last_update_label.setText("Status: ClamAV not available")
    
    def tray_icon_activated(self, reason):
        # ActivationReason.Trigger is a single click, DoubleClick is double click
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def quit_application(self):
        # Check if real-time protection is active
        if self.monitoring_enabled and self.real_time_monitor and hasattr(self.real_time_monitor, 'state') and self.real_time_monitor.state.name == 'RUNNING':
            reply = self.show_themed_message_box("question", "Exit Application", 
                                       "Real-time protection is currently active and will be stopped if you exit the application.\n\n"
                                       "Are you sure you want to exit and stop real-time protection?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return  # User chose not to exit
            
            # User confirmed exit - stop real-time protection
            try:
                print("🛑 Stopping real-time protection due to application exit...")
                self.stop_real_time_protection()
                print("✅ Real-time protection stopped successfully")
            except Exception as e:
                print(f"⚠️ Error stopping real-time protection: {e}")
        
        # Check for running scans
        if self.current_scan_thread and self.current_scan_thread.isRunning():
            reply = self.show_themed_message_box("question", "Quit", 
                                       "A scan is in progress. Do you want to quit anyway?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
            self.current_scan_thread.terminate()
        
        # Force application to quit instead of just closing the window
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
    
    def closeEvent(self, event):
        # Check if real-time protection is active before closing
        if self.monitoring_enabled and self.real_time_monitor and hasattr(self.real_time_monitor, 'state') and self.real_time_monitor.state.name == 'RUNNING':
            reply = self.show_themed_message_box("question", "Close Application", 
                                       "Real-time protection is currently active and will be stopped if you close the application.\n\n"
                                       "Would you like to:\n"
                                       "• Close and stop protection (Yes)\n"
                                       "• Minimize to system tray and keep protection running (No)",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.No:
                # User chose to minimize to tray instead of closing
                if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
                    self.hide()
                    self.tray_icon.showMessage(
                        "S&D - Search & Destroy",
                        "Application minimized to system tray. Real-time protection is still active.",
                        QSystemTrayIcon.MessageIcon.Information,
                        3000
                    )
                event.ignore()
                return
            
            # User chose to close - stop real-time protection
            try:
                print("🛑 Stopping real-time protection due to application close...")
                self.stop_real_time_protection()
                print("✅ Real-time protection stopped successfully")
            except Exception as e:
                print(f"⚠️ Error stopping real-time protection: {e}")
        
        # Stop real-time monitoring before closing
        if hasattr(self, 'real_time_monitor') and self.real_time_monitor:
            try:
                self.real_time_monitor.stop()
            except Exception:
                pass  # Ignore errors during shutdown
        
        # Save activity logs before closing
        try:
            self.save_activity_logs()
        except Exception as e:
            print(f"Warning: Failed to save activity logs on close: {e}")
        
        # Accept the close event (actually close the application)
        event.accept()
        
        # Force application to quit
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def refresh_reports(self):
        """Load and display scan reports in the reports list."""
        try:
            # Clear the current list
            self.reports_list.clear()
            
            # Get reports directory from the report manager
            reports_dir = self.report_manager.daily_reports
            
            # Verify the directory exists
            if not reports_dir.exists():
                self.report_viewer.setText("No reports directory found.")
                return
                
            # Find all JSON report files
            report_files = list(reports_dir.glob("scan_*.json"))
            
            if not report_files:
                if self.current_theme == 'dark':
                    no_reports_html = """
                    <style>
                        body { 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            color: #FFCDAA; 
                            background-color: #2b2b2b; 
                            margin: 20px; 
                            text-align: center;
                            line-height: 1.6;
                        }
                        h3 { 
                            color: #EE8980; 
                            font-weight: 600; 
                            margin-bottom: 10px;
                        }
                        p { 
                            color: #FFCDAA; 
                            font-weight: 500; 
                        }
                    </style>
                    <h3>No Scan Reports Found</h3>
                    <p>Run a scan to generate your first report.</p>
                    """
                else:
                    no_reports_html = """
                    <style>
                        body { 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            color: #2c2c2c; 
                            background-color: #fefefe; 
                            margin: 20px; 
                            text-align: center;
                            line-height: 1.5;
                        }
                        h3 { 
                            color: #75BDE0; 
                            font-weight: 600; 
                            margin-bottom: 10px;
                        }
                        p { 
                            color: #2c2c2c; 
                            font-weight: 500; 
                        }
                    </style>
                    <h3>No Scan Reports Found</h3>
                    <p>Run a scan to generate your first report.</p>
                    """
                self.report_viewer.setHtml(no_reports_html)
                return
                
            # Sort reports by date (newest first)
            report_files.sort(reverse=True)
            
            # Add to list widget
            for report_file in report_files:
                try:
                    # Extract scan ID from filename
                    scan_id = report_file.stem.replace("scan_", "")
                    
                    # Try to load basic report info
                    with open(report_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Create item with timestamp and scan type
                    item_text = f"{data.get('start_time', 'Unknown')} - {data.get('scan_type', 'Unknown')}"
                    
                    # Add threat count if available
                    threats = data.get('threats_found', 0)
                    item_text += f" - {threats} threats found" if threats else " - Clean"
                    
                    # Create and add the item
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, scan_id)
                    self.reports_list.addItem(item)
                    
                except (OSError, IOError, PermissionError) as e:
                    print(f"Error loading report {report_file}: {e}")
                    
            if self.current_theme == 'dark':
                select_report_html = """
                <style>
                    body { 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #FFCDAA; 
                        background-color: #2b2b2b; 
                        margin: 20px; 
                        text-align: center;
                        line-height: 1.6;
                    }
                    h3 { 
                        color: #EE8980; 
                        font-weight: 600; 
                        margin-bottom: 10px;
                    }
                    p { 
                        color: #FFCDAA; 
                        font-weight: 500; 
                    }
                </style>
                <h3>Select a Report</h3>
                <p>Choose a scan report from the list to view detailed results.</p>
                """
            else:
                select_report_html = """
                <style>
                    body { 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #2c2c2c; 
                        background-color: #fefefe; 
                        margin: 20px; 
                        text-align: center;
                        line-height: 1.5;
                    }
                    h3 { 
                        color: #75BDE0; 
                        font-weight: 600; 
                        margin-bottom: 10px;
                    }
                    p { 
                        color: #2c2c2c; 
                        font-weight: 500; 
                    }
                </style>
                <h3>Select a Report</h3>
                <p>Choose a scan report from the list to view detailed results.</p>
                """
            self.report_viewer.setHtml(select_report_html)
            
        except Exception as e:
            if self.current_theme == 'dark':
                error_html = f"""
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #FFCDAA; 
                        background-color: #2b2b2b; 
                        margin: 20px; 
                        line-height: 1.6;
                    }}
                    h3 {{ 
                        color: #F14666; 
                        font-weight: 600; 
                        margin-bottom: 10px;
                    }}
                    p {{ 
                        color: #FFCDAA; 
                        font-weight: 500; 
                    }}
                </style>
                <h3>Error Loading Reports</h3>
                <p>{e}</p>
                """
            else:
                error_html = f"""
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #2c2c2c; 
                        background-color: #fefefe; 
                        margin: 20px; 
                        line-height: 1.5;
                    }}
                    h3 {{ 
                        color: #F89B9B; 
                        font-weight: 600; 
                        margin-bottom: 10px;
                    }}
                    p {{ 
                        color: #2c2c2c; 
                        font-weight: 500; 
                    }}
                </style>
                <h3>Error Loading Reports</h3>
                <p>{e}</p>
                """
            self.report_viewer.setHtml(error_html)
            
    def load_report(self, item):
        """Load and display the selected scan report."""
        try:
            # Get scan ID from item data
            scan_id = item.data(Qt.ItemDataRole.UserRole)
            if not scan_id:
                if self.current_theme == 'dark':
                    no_id_html = """
                    <style>
                        body { 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            color: #FFCDAA; 
                            background-color: #2b2b2b; 
                            margin: 20px; 
                            text-align: center;
                            line-height: 1.6;
                        }
                        h3 { 
                            color: #F14666; 
                            font-weight: 600; 
                            margin-bottom: 10px;
                        }
                        p { 
                            color: #FFCDAA; 
                            font-weight: 500; 
                        }
                    </style>
                    <h3>Report Error</h3>
                    <p>No scan ID available for this report.</p>
                    """
                else:
                    no_id_html = """
                    <style>
                        body { 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            color: #2c2c2c; 
                            background-color: #fefefe; 
                            margin: 20px; 
                            text-align: center;
                            line-height: 1.5;
                        }
                        h3 { 
                            color: #F89B9B; 
                            font-weight: 600; 
                            margin-bottom: 10px;
                        }
                        p { 
                            color: #2c2c2c; 
                            font-weight: 500; 
                        }
                    </style>
                    <h3>Report Error</h3>
                    <p>No scan ID available for this report.</p>
                    """
                self.report_viewer.setHtml(no_id_html)
                return
                
            # Load the report using the report manager
            scan_result = self.report_manager.load_scan_result(scan_id)
            
            if not scan_result:
                if self.current_theme == 'dark':
                    load_error_html = f"""
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            color: #FFCDAA; 
                            background-color: #2b2b2b; 
                            margin: 20px; 
                            text-align: center;
                            line-height: 1.6;
                        }}
                        h3 {{ 
                            color: #F14666; 
                            font-weight: 600; 
                            margin-bottom: 10px;
                        }}
                        p {{ 
                            color: #FFCDAA; 
                            font-weight: 500; 
                        }}
                    </style>
                    <h3>Report Load Error</h3>
                    <p>Could not load report with ID: {scan_id}</p>
                    """
                else:
                    load_error_html = f"""
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            color: #2c2c2c; 
                            background-color: #fefefe; 
                            margin: 20px; 
                            text-align: center;
                            line-height: 1.5;
                        }}
                        h3 {{ 
                            color: #F89B9B; 
                            font-weight: 600; 
                            margin-bottom: 10px;
                        }}
                        p {{ 
                            color: #2c2c2c; 
                            font-weight: 500; 
                        }}
                    </style>
                    <h3>Report Load Error</h3>
                    <p>Could not load report with ID: {scan_id}</p>
                    """
                self.report_viewer.setHtml(load_error_html)
                return
                
            # Format the report for display
            # Create a formatted text output
            output = f"<h2>Scan Report: {scan_id}</h2>"
            output += f"<p><b>Date:</b> {scan_result.start_time}</p>"
            output += f"<p><b>Scan Type:</b> {scan_result.scan_type.value}</p>"
            output += f"<p><b>Duration:</b> {scan_result.duration:.2f} seconds</p>"
            output += f"<p><b>Files Scanned:</b> {scan_result.scanned_files}/{scan_result.total_files}</p>"
            output += f"<p><b>Threats Found:</b> {scan_result.threats_found}</p>"
            
            # Add paths that were scanned
            output += "<h3>Scanned Paths:</h3><ul>"
            for path in scan_result.scanned_paths:
                output += f"<li>{path}</li>"
            output += "</ul>"
            
            # Add threats if any were found
            if scan_result.threats_found > 0:
                output += "<h3>Detected Threats:</h3><table border='1' cellpadding='3'>"
                output += "<tr><th>File</th><th>Threat</th><th>Level</th><th>Action</th></tr>"
                
                for threat in scan_result.threats:
                    threat_level_class = "error" if threat.threat_level.value == "error" else \
                                        "infected" if threat.threat_level.value == "infected" else \
                                        "suspicious" if threat.threat_level.value == "suspicious" else "clean"
                                        
                    output += f"<tr class='{threat_level_class}'>"
                    output += f"<td>{threat.file_path}</td>"
                    output += f"<td>{threat.threat_name}</td>"
                    output += f"<td>{threat.threat_level.value}</td>"
                    output += f"<td>{threat.action_taken}</td>"
                    output += "</tr>"
                
                output += "</table>"
            else:
                output += "<h3>No threats detected!</h3>"
                
            # Add any errors
            if scan_result.errors:
                output += "<h3>Errors:</h3><ul>"
                for error in scan_result.errors:
                    output += f"<li>{error}</li>"
                output += "</ul>"
                
            # Add CSS styling based on current theme
            if self.current_theme == 'dark':
                # Dark mode styling with Strawberry color palette
                output = f"""
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #FFCDAA;
                        background-color: #2b2b2b;
                        margin: 8px;
                        line-height: 1.6;
                    }}
                    h2 {{ 
                        color: #F14666; 
                        font-weight: 700;
                        margin-top: 16px;
                        margin-bottom: 12px;
                        border-bottom: 2px solid #EE8980;
                        padding-bottom: 8px;
                        font-size: 20px;
                    }}
                    h3 {{ 
                        color: #F14666; 
                        font-weight: 600;
                        margin-top: 16px; 
                        margin-bottom: 10px;
                        font-size: 16px;
                    }}
                    p {{
                        margin: 8px 0;
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                    table {{ 
                        border-collapse: collapse; 
                        width: 100%; 
                        margin: 10px 0;
                        border: 2px solid #EE8980;
                        border-radius: 6px;
                        overflow: hidden;
                        background-color: #353535;
                    }}
                    th {{ 
                        background-color: #EE8980; 
                        color: #ffffff;
                        font-weight: 700;
                        padding: 10px;
                        text-align: left;
                        font-size: 13px;
                    }}
                    td {{
                        padding: 8px 10px;
                        border-bottom: 1px solid #404040;
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                    tr:nth-child(even) {{
                        background-color: #404040;
                    }}
                    tr:nth-child(odd) {{
                        background-color: #353535;
                    }}
                    tr.infected {{ 
                        background-color: #4A2B2B; 
                        border-left: 4px solid #F14666;
                        color: #ffffff;
                    }}
                    tr.suspicious {{ 
                        background-color: #4A3B2B; 
                        border-left: 4px solid #EE8980;
                        color: #ffffff;
                    }}
                    tr.error {{ 
                        background-color: #4A2B2B; 
                        border-left: 4px solid #F14666;
                        color: #ffffff;
                    }}
                    tr.clean {{ 
                        background-color: #2B4A3B; 
                        border-left: 4px solid #9CB898;
                        color: #ffffff;
                    }}
                    ul {{
                        margin: 10px 0;
                        padding-left: 22px;
                    }}
                    li {{
                        margin: 6px 0;
                        color: #FFCDAA;
                        font-weight: 500;
                    }}
                    b {{
                        color: #EE8980;
                        font-weight: 700;
                    }}
                </style>
                {output}
                """
            else:
                # Light mode styling with Sunrise color palette
                output = f"""
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #2c2c2c;
                        background-color: #fefefe;
                        margin: 8px;
                        line-height: 1.5;
                    }}
                    h2 {{ 
                        color: #75BDE0; 
                        font-weight: 700;
                        margin-top: 16px;
                        margin-bottom: 12px;
                        border-bottom: 2px solid #F8D49B;
                        padding-bottom: 6px;
                    }}
                    h3 {{ 
                        color: #75BDE0; 
                        font-weight: 600;
                        margin-top: 16px; 
                        margin-bottom: 8px;
                    }}
                    p {{
                        margin: 6px 0;
                        color: #2c2c2c;
                    }}
                    table {{ 
                        border-collapse: collapse; 
                        width: 100%; 
                        margin: 8px 0;
                        border: 2px solid #F8D49B;
                        border-radius: 6px;
                        overflow: hidden;
                    }}
                    th {{ 
                        background-color: #F8D49B; 
                        color: #2c2c2c;
                        font-weight: 600;
                        padding: 8px;
                        text-align: left;
                    }}
                    td {{
                        padding: 6px 8px;
                        border-bottom: 1px solid #F8F8F8;
                    }}
                    tr:nth-child(even) {{
                        background-color: #FAFAFA;
                    }}
                    tr.infected {{ 
                        background-color: #FEF5F5; 
                        border-left: 4px solid #F89B9B;
                    }}
                    tr.suspicious {{ 
                        background-color: #FEF9F5; 
                        border-left: 4px solid #F8BC9B;
                    }}
                    tr.error {{ 
                        background-color: #FEF5F5; 
                        border-left: 4px solid #F89B9B;
                    }}
                    tr.clean {{ 
                        background-color: #F5FAFF; 
                        border-left: 4px solid #75BDE0;
                    }}
                    ul {{
                        margin: 8px 0;
                        padding-left: 20px;
                    }}
                    li {{
                        margin: 4px 0;
                        color: #2c2c2c;
                    }}
                    b {{
                        color: #75BDE0;
                        font-weight: 600;
                    }}
                </style>
                {output}
                """
            
            self.report_viewer.setHtml(output)
            
        except Exception as e:
            if self.current_theme == 'dark':
                final_error_html = f"""
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #FFCDAA; 
                        background-color: #2b2b2b; 
                        margin: 20px; 
                        text-align: center;
                        line-height: 1.6;
                    }}
                    h3 {{ 
                        color: #F14666; 
                        font-weight: 600; 
                        margin-bottom: 10px;
                    }}
                    p {{ 
                        color: #FFCDAA; 
                        font-weight: 500; 
                    }}
                </style>
                <h3>Report Display Error</h3>
                <p>Error loading report: {e}</p>
                """
            else:
                final_error_html = f"""
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        color: #2c2c2c; 
                        background-color: #fefefe; 
                        margin: 20px; 
                        text-align: center;
                        line-height: 1.5;
                    }}
                    h3 {{ 
                        color: #F89B9B; 
                        font-weight: 600; 
                        margin-bottom: 10px;
                    }}
                    p {{ 
                        color: #2c2c2c; 
                        font-weight: 500; 
                    }}
                </style>
                <h3>Report Display Error</h3>
                <p>Error loading report: {e}</p>
                """
            self.report_viewer.setHtml(final_error_html)
    
    def export_reports(self):
        """Export scan reports to file."""
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit, QPushButton
            from PyQt6.QtCore import QDate
            
            # Create a dialog for export options
            dialog = QDialog(self)
            dialog.setWindowTitle("Export Reports")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # Format selection
            format_layout = QHBoxLayout()
            format_label = QLabel("Export Format:")
            format_combo = QComboBox()
            format_combo.addItems(["JSON", "CSV", "HTML"])
            format_layout.addWidget(format_label)
            format_layout.addWidget(format_combo)
            layout.addLayout(format_layout)
            
            # Date range
            date_layout = QVBoxLayout()
            date_label = QLabel("Date Range (Optional):")
            date_layout.addWidget(date_label)
            
            start_date_layout = QHBoxLayout()
            start_date_label = QLabel("Start Date:")
            start_date = QDateEdit()
            start_date.setCalendarPopup(True)
            start_date.setDate(QDate.currentDate().addDays(-30))  # Last 30 days
            start_date_layout.addWidget(start_date_label)
            start_date_layout.addWidget(start_date)
            date_layout.addLayout(start_date_layout)
            
            end_date_layout = QHBoxLayout()
            end_date_label = QLabel("End Date:")
            end_date = QDateEdit()
            end_date.setCalendarPopup(True)
            end_date.setDate(QDate.currentDate())
            end_date_layout.addWidget(end_date_label)
            end_date_layout.addWidget(end_date)
            date_layout.addLayout(end_date_layout)
            
            layout.addLayout(date_layout)
            
            # Buttons
            button_layout = QHBoxLayout()
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(dialog.reject)
            export_button = QPushButton("Export")
            export_button.clicked.connect(dialog.accept)
            export_button.setDefault(True)
            button_layout.addWidget(cancel_button)
            button_layout.addWidget(export_button)
            layout.addLayout(button_layout)
            
            # Show dialog
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # Get export format
            format_type = format_combo.currentText().lower()
            
            # Get date range
            start_date_str = start_date.date().toString("yyyy-MM-dd")
            end_date_str = end_date.date().toString("yyyy-MM-dd")
            
            # Get output file path
            file_extensions = {
                "json": "JSON Files (*.json)",
                "csv": "CSV Files (*.csv)",
                "html": "HTML Files (*.html)"
            }
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Export File", "", 
                file_extensions.get(format_type, "All Files (*)")
            )
            
            if not file_path:
                return
                
            # Add extension if missing
            if not file_path.lower().endswith(f".{format_type}"):
                file_path += f".{format_type}"
                
            # Export the reports
            success = self.report_manager.export_reports(
                file_path, 
                format_type=format_type,
                start_date=f"{start_date_str}T00:00:00",
                end_date=f"{end_date_str}T23:59:59"
            )
            
            if success:
                self.show_themed_message_box(
                    "information",
                    "Export Complete", 
                    f"Reports successfully exported to:\n{file_path}"
                )
            else:
                self.show_themed_message_box(
                    "warning",
                    "Export Failed", 
                    "Failed to export reports. See log for details."
                )
                
        except Exception as e:
            self.show_themed_message_box("warning", "Export Error", f"Error exporting reports: {e}")

    def delete_all_reports(self):
        """Delete all scan reports after confirmation."""
        try:
            from PyQt6.QtWidgets import QMessageBox
            from pathlib import Path
            
            # Show confirmation dialog
            reply = self.show_themed_message_box(
                "question",
                "Delete All Reports",
                "Are you sure you want to delete ALL scan reports?\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Delete all reports by cleaning up the reports directory
                try:
                    # Use the report manager's reports directory
                    reports_dir = self.report_manager.reports_dir
                    deleted_count = 0
                    
                    if reports_dir.exists():
                        # Delete all .json report files
                        for report_file in reports_dir.glob("*.json"):
                            report_file.unlink()
                            deleted_count += 1
                        
                        # Also clean up any subdirectories like daily summaries, threats, etc.
                        for subdir in reports_dir.iterdir():
                            if subdir.is_dir():
                                for file in subdir.rglob("*"):
                                    if file.is_file():
                                        file.unlink()
                                        deleted_count += 1
                                # Remove empty directories
                                try:
                                    if not any(subdir.iterdir()):
                                        subdir.rmdir()
                                except OSError:
                                    pass  # Directory not empty or other issue
                    
                    self.show_themed_message_box(
                        "information",
                        "Reports Deleted",
                        f"Successfully deleted {deleted_count} report files."
                    )
                    # Refresh the reports list to show it's empty
                    self.refresh_reports()
                    
                except Exception as delete_error:
                    self.show_themed_message_box(
                        "warning",
                        "Delete Failed",
                        f"Failed to delete reports: {delete_error}"
                    )
                    
        except Exception as e:
            self.show_themed_message_box("warning", "Delete Error", f"Error deleting reports: {e}")

    def load_current_settings(self):
        """Load current settings from config into the settings UI controls."""
        try:
            # Scan settings
            scan_settings = self.config.get('scan_settings', {})
            self.settings_max_threads_spin.setValue(scan_settings.get('max_threads', 4))
            self.settings_timeout_spin.setValue(scan_settings.get('timeout_seconds', 300))
            
            # UI settings
            ui_settings = self.config.get('ui_settings', {})
            self.settings_minimize_to_tray_cb.setChecked(ui_settings.get('minimize_to_tray', True))
            self.settings_show_notifications_cb.setChecked(ui_settings.get('show_notifications', True))
            
            # Activity log retention setting
            retention = str(ui_settings.get('activity_log_retention', 100))
            self.settings_activity_retention_combo.setCurrentText(retention)
            
            # Security settings
            security_settings = self.config.get('security_settings', {})
            self.settings_auto_update_cb.setChecked(security_settings.get('auto_update_definitions', True))
            
            # Advanced settings
            advanced_settings = self.config.get('advanced_settings', {})
            self.settings_scan_archives_cb.setChecked(advanced_settings.get('scan_archives', True))
            self.settings_follow_symlinks_cb.setChecked(advanced_settings.get('follow_symlinks', False))
            
            # Real-time protection settings
            protection_settings = self.config.get('realtime_protection', {})
            self.settings_monitor_modifications_cb.setChecked(protection_settings.get('monitor_modifications', True))
            self.settings_monitor_new_files_cb.setChecked(protection_settings.get('monitor_new_files', True))
            self.settings_scan_modified_cb.setChecked(protection_settings.get('scan_modified_files', False))
            
        except (OSError, IOError, PermissionError) as e:
            print(f"Error loading settings: {e}")
            
    def load_default_settings(self):
        """Reset all settings to their default values."""
        try:
            # Reset scan settings to defaults
            self.settings_max_threads_spin.setValue(4)
            self.settings_timeout_spin.setValue(300)
            
            # Reset UI settings to defaults
            self.settings_minimize_to_tray_cb.setChecked(True)
            self.settings_show_notifications_cb.setChecked(True)
            
            # Reset security settings to defaults
            self.settings_auto_update_cb.setChecked(True)
            
            # Reset advanced settings to defaults
            self.settings_scan_archives_cb.setChecked(True)
            self.settings_follow_symlinks_cb.setChecked(False)
            
            # Reset real-time protection settings to defaults
            self.settings_monitor_modifications_cb.setChecked(True)
            self.settings_monitor_new_files_cb.setChecked(True)
            self.settings_scan_modified_cb.setChecked(False)
            
            self.show_themed_message_box("information", "Settings", "Settings have been reset to defaults.")
            
        except Exception as e:
            self.show_themed_message_box("warning", "Error", f"Could not reset settings: {str(e)}")
            
    def save_settings(self):
        """Save all settings from the UI controls to the config file."""
        try:
            # Ensure config sections exist
            if 'scan_settings' not in self.config:
                self.config['scan_settings'] = {}
            if 'ui_settings' not in self.config:
                self.config['ui_settings'] = {}
            if 'security_settings' not in self.config:
                self.config['security_settings'] = {}
            if 'advanced_settings' not in self.config:
                self.config['advanced_settings'] = {}
            if 'realtime_protection' not in self.config:
                self.config['realtime_protection'] = {}
            
            # Update config with new values from UI
            self.config['scan_settings']['max_threads'] = self.settings_max_threads_spin.value()
            self.config['scan_settings']['timeout_seconds'] = self.settings_timeout_spin.value()
            
            self.config['ui_settings']['minimize_to_tray'] = self.settings_minimize_to_tray_cb.isChecked()
            self.config['ui_settings']['show_notifications'] = self.settings_show_notifications_cb.isChecked()
            self.config['ui_settings']['activity_log_retention'] = int(self.settings_activity_retention_combo.currentText())
            
            self.config['security_settings']['auto_update_definitions'] = self.settings_auto_update_cb.isChecked()
            
            self.config['advanced_settings']['scan_archives'] = self.settings_scan_archives_cb.isChecked()
            self.config['advanced_settings']['follow_symlinks'] = self.settings_follow_symlinks_cb.isChecked()
            
            self.config['realtime_protection']['monitor_modifications'] = self.settings_monitor_modifications_cb.isChecked()
            self.config['realtime_protection']['monitor_new_files'] = self.settings_monitor_new_files_cb.isChecked()
            self.config['realtime_protection']['scan_modified_files'] = self.settings_scan_modified_cb.isChecked()
            
            # Save config to file
            from utils.config import save_config
            save_config(self.config)
            
            self.show_themed_message_box("information", "Settings", "Settings saved successfully!")
            
            # If real-time protection is active, update its settings
            if hasattr(self, 'real_time_monitor') and self.real_time_monitor:
                try:
                    # Update real-time monitor settings if it's running
                    pass  # We could add real-time settings update here if needed
                except Exception as monitor_error:
                    print(f"⚠️ Could not update real-time monitor settings: {monitor_error}")
            
        except (OSError, IOError, PermissionError) as e:
            print(f"Error saving settings: {e}")
