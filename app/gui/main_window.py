import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QProgressBar, QTextEdit, 
                             QTabWidget, QGroupBox, QListWidget, QListWidgetItem,
                             QSplitter, QFrame, QStatusBar, QMenuBar, QMenu,
                             QFileDialog, QMessageBox, QSystemTrayIcon, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction, QShortcut, QKeySequence, QMouseEvent

from gui.scan_thread import ScanThread
from core.file_scanner import FileScanner
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.scanner = FileScanner()
        self.report_manager = ScanReportManager()
        self.current_scan_thread = None
        
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
        
    def init_ui(self):
        self.setWindowTitle("S&D - Search & Destroy")
        self.setMinimumSize(1000, 750)
        self.resize(1200, 850)
        
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
        
        quick_scan_btn = QPushButton("Quick Scan")
        quick_scan_btn.setObjectName("actionButton")
        quick_scan_btn.setMinimumSize(120, 40)  # Increased size to prevent text cutoff
        quick_scan_btn.clicked.connect(self.quick_scan)
        
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
        
        actions_layout.addWidget(quick_scan_btn)
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
        
        # Protection Status Card
        self.protection_card = self.create_clickable_status_card(
            "Real-Time Protection",
            "Active" if self.monitoring_enabled else "Inactive",
            "#28a745" if self.monitoring_enabled else "#dc3545",
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
        
        # Threats Card
        self.threats_card = self.create_status_card(
            "Threats Found",
            "0",  # Will be updated dynamically
            "#28a745",
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
                self.add_activity_message("⏹️ Real-time protection disabled from dashboard")
    
    def update_protection_status_card(self):
        """Update the protection status card with current state."""
        if hasattr(self, 'protection_card'):
            # Find the card's value label and update it
            for child in self.protection_card.findChildren(QLabel):
                if child.objectName() == "cardValue":
                    child.setText("Active" if self.monitoring_enabled else "Inactive")
                    child.setStyleSheet(f"color: {'#28a745' if self.monitoring_enabled else '#dc3545'}; font-size: 20px; font-weight: bold;")
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
                    self.protection_status_label.setStyleSheet("color: #00FF7F; font-weight: bold; font-size: 12px; padding: 5px;")
                    self.protection_toggle_btn.setText("⏹️ Stop")
                    print("✅ Protection tab UI updated to Active state")
                else:
                    # Monitoring was supposed to be enabled but isn't running - reset
                    print("⚠️ Monitoring was enabled but not running - resetting to inactive")
                    self.monitoring_enabled = False
                    self.protection_status_label.setText("❌ Failed to restore")
                    self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
                    self.protection_toggle_btn.setText("▶️ Start")
                    
                    # Update config to reflect actual state
                    if 'security_settings' not in self.config:
                        self.config['security_settings'] = {}
                    self.config['security_settings']['real_time_protection'] = False
                    save_config(self.config)
            else:
                self.protection_status_label.setText("⚫ Inactive")
                self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("▶️ Start")
                print("✅ Protection tab UI updated to Inactive state")
            
            # Also update the dashboard card
            self.update_protection_status_card()
        else:
            print("⚠️ Protection tab UI elements not found - skipping update")

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
        
        scan_buttons_layout.addWidget(self.start_scan_btn)
        scan_buttons_layout.addWidget(self.stop_scan_btn)
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
        delete_all_btn.setStyleSheet("color: #ff6b6b;")  # Red text to indicate destructive action
        
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
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Open settings dialog button
        settings_btn = QPushButton("Open Settings")
        settings_btn.clicked.connect(self.open_settings_dialog)
        
        layout.addWidget(settings_btn)
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def create_real_time_tab(self):
        """Create the real-time protection tab."""
        real_time_widget = QWidget()
        layout = QVBoxLayout(real_time_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)  # Center horizontally, align to top
        layout.setSpacing(15)  # Add more spacing between sections
        
        # Real-time protection status group
        status_group = QGroupBox("Protection Status")
        status_group.setMaximumWidth(600)  # Limit width for better centering
        status_layout = QVBoxLayout(status_group)
        
        # Protection status display
        self.protection_status_label = QLabel("🔄 Initializing...")
        self.protection_status_label.setObjectName("protectionStatus")
        self.protection_status_label.setWordWrap(True)  # Enable word wrapping
        self.protection_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align
        self.protection_status_label.setMinimumHeight(30)  # Ensure minimum height
        self.protection_status_label.setStyleSheet("font-size: 12px; padding: 5px;")  # Add padding
        status_layout.addWidget(self.protection_status_label)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.protection_toggle_btn = QPushButton("▶️ Start")
        self.protection_toggle_btn.clicked.connect(self.toggle_real_time_protection)
        self.protection_toggle_btn.setMinimumHeight(35)  # Make button taller for better visibility
        
        controls_layout.addStretch()  # Add stretch before button
        controls_layout.addWidget(self.protection_toggle_btn)
        controls_layout.addStretch()  # Add stretch after button
        
        status_layout.addLayout(controls_layout)
        layout.addWidget(status_group)
        
        # Statistics group
        stats_group = QGroupBox("Protection Statistics")
        stats_group.setMaximumWidth(600)  # Limit width for better centering
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the entire layout
        
        # Statistics display
        self.events_processed_label = QLabel("Events Processed: 0")
        self.events_processed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.threats_detected_label = QLabel("Threats Detected: 0")
        self.threats_detected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scans_performed_label = QLabel("Scans Performed: 0")
        self.scans_performed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.uptime_label = QLabel("Uptime: 0 seconds")
        self.uptime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        stats_layout.addWidget(self.events_processed_label)
        stats_layout.addWidget(self.threats_detected_label)
        stats_layout.addWidget(self.scans_performed_label)
        stats_layout.addWidget(self.uptime_label)
        
        layout.addWidget(stats_group)
        
        # Recent activity group
        activity_group = QGroupBox("Recent Activity")
        activity_group.setMaximumWidth(600)  # Limit width for better centering
        activity_layout = QVBoxLayout(activity_group)
        activity_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the layout
        
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(200)
        activity_layout.addWidget(self.activity_list)
        
        layout.addWidget(activity_group)
        
        # Watch paths configuration group
        paths_group = QGroupBox("Monitored Paths")
        paths_group.setMaximumWidth(600)  # Limit width for better centering
        paths_layout = QVBoxLayout(paths_group)
        paths_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the layout
        
        self.paths_list = QListWidget()
        self.paths_list.setMaximumHeight(150)
        
        paths_controls = QHBoxLayout()
        add_path_btn = QPushButton("Add Path")
        add_path_btn.clicked.connect(self.add_watch_path)
        remove_path_btn = QPushButton("Remove Path")
        remove_path_btn.clicked.connect(self.remove_watch_path)
        
        paths_controls.addStretch()  # Add stretch before buttons
        paths_controls.addWidget(add_path_btn)
        paths_controls.addWidget(remove_path_btn)
        paths_controls.addStretch()  # Add stretch after buttons
        
        paths_layout.addWidget(self.paths_list)
        paths_layout.addLayout(paths_controls)
        
        layout.addWidget(paths_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(real_time_widget, "Protection")
        
    def init_real_time_monitoring_safe(self):
        """Safely initialize the real-time monitoring system with better error handling."""
        print("🔧 Initializing real-time monitoring system...")
        try:
            # Create monitor configuration with safer defaults
            watch_paths = self.config.get('watch_paths', [str(Path.home())])  # Just monitor home directory initially
            excluded_paths = self.config.get('excluded_paths', ['/proc', '/sys', '/dev', '/tmp'])
            
            print(f"📁 Watch paths: {watch_paths}")
            print(f"🚫 Excluded paths: {excluded_paths}")
            
            # Ensure paths are properly formatted
            if isinstance(watch_paths, list):
                watch_paths = [str(path) for path in watch_paths]
            else:
                watch_paths = [str(watch_paths)]
                
            if isinstance(excluded_paths, list):
                excluded_paths = [str(path) for path in excluded_paths]
            else:
                excluded_paths = [str(excluded_paths)]
            
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
                        self.protection_status_label.setStyleSheet("color: #00FF7F; font-weight: bold; font-size: 12px; padding: 5px;")
                        if hasattr(self, 'protection_toggle_btn'):
                            self.protection_toggle_btn.setText("⏹️ Stop")
                        print("✅ Real-time protection restored successfully!")
                        self.add_activity_message("✅ Real-time protection restored from previous session")
                    else:
                        # Failed to start, reset to inactive
                        print("❌ Failed to restore real-time protection")
                        self.monitoring_enabled = False
                        self.protection_status_label.setText("❌ Failed to restore")
                        self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
                        if hasattr(self, 'protection_toggle_btn'):
                            self.protection_toggle_btn.setText("▶️ Start")
                        self.add_activity_message("❌ Failed to restore real-time protection from previous session")
                        # Update config to reflect failure
                        if 'security_settings' not in self.config:
                            self.config['security_settings'] = {}
                        self.config['security_settings']['real_time_protection'] = False
                        save_config(self.config)
                else:
                    # Protection is disabled, set inactive status
                    self.protection_status_label.setText("⚫ Inactive")
                    self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
                    if hasattr(self, 'protection_toggle_btn'):
                        self.protection_toggle_btn.setText("▶️ Start")
            
            print("✅ Real-time monitoring initialized successfully!")
            return True
                
        except Exception as e:
            print(f"❌ Failed to initialize monitoring: {e}")
            # Create a dummy monitor for UI purposes
            self.real_time_monitor = None
            self.add_activity_message(f"⚠️ Monitoring system offline: {str(e)}")
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
                self.protection_status_label.setText("⚫ Inactive")
                self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
                
        except Exception as e:
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
                self.protection_status_label.setStyleSheet("color: #00FF7F; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("⏹️ Stop")
                self.add_activity_message("✅ Real-time protection started")
                self.status_bar.showMessage("Real-time protection active")
                
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
            else:
                self.protection_status_label.setText("❌ Failed")
                self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
                # Keep button as "Start" since protection failed to start
                self.protection_toggle_btn.setText("▶️ Start")
                self.add_activity_message("❌ Failed to start real-time protection")
                
                # Make sure dashboard shows failure state
                self.monitoring_enabled = False
                self.update_protection_status_card()
                
        except Exception as e:
            self.add_activity_message(f"❌ Error starting protection: {e}")
            # Ensure button stays as "Start" if there was an error
            self.protection_toggle_btn.setText("▶️ Start")
            # Make sure dashboard shows error state
            self.monitoring_enabled = False
            self.update_protection_status_card()
    
    def stop_real_time_protection(self):
        """Stop real-time protection."""
        try:
            if self.real_time_monitor:
                self.real_time_monitor.stop()
                self.protection_status_label.setText("⚫ Inactive")
                self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
                self.protection_toggle_btn.setText("▶️ Start")
                self.add_activity_message("⏹️ Real-time protection stopped")
                self.status_bar.showMessage("Real-time protection stopped")
                
                # Save user preference
                self.monitoring_enabled = False
                if 'security_settings' not in self.config:
                    self.config['security_settings'] = {}
                self.config['security_settings']['real_time_protection'] = False
                save_config(self.config)
                
                # Update dashboard card to reflect the change
                self.update_protection_status_card()
                
        except Exception as e:
            self.add_activity_message(f"❌ Error stopping protection: {e}")
            # If stopping failed, we can't be sure of the state, so show error and allow retry
            self.protection_status_label.setText("❌ Error")
            self.protection_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12px; padding: 5px;")
    
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
        
        # Add to main activity list if it exists
        if hasattr(self, 'activity_list'):
            # Add to top of list
            item = QListWidgetItem(full_message)
            self.activity_list.insertItem(0, item)
            
            # Keep only last 100 items
            while self.activity_list.count() > 100:
                self.activity_list.takeItem(self.activity_list.count() - 1)
        
        # Also add to dashboard activity list if it exists
        if hasattr(self, 'dashboard_activity'):
            # Add to top of dashboard list
            item = QListWidgetItem(full_message)
            self.dashboard_activity.insertItem(0, item)
            
            # Keep only last 20 items on dashboard for brevity
            while self.dashboard_activity.count() > 20:
                self.dashboard_activity.takeItem(self.dashboard_activity.count() - 1)
    
    def update_monitoring_statistics(self):
        """Update the monitoring statistics display."""
        if self.real_time_monitor:
            try:
                stats = self.real_time_monitor.get_statistics()
                monitor_stats = stats.get('monitor', {})
                
                self.events_processed_label.setText(f"Events Processed: {monitor_stats.get('events_processed', 0)}")
                self.threats_detected_label.setText(f"Threats Detected: {monitor_stats.get('threats_detected', 0)}")
                self.scans_performed_label.setText(f"Scans Performed: {monitor_stats.get('scans_performed', 0)}")
                
                uptime = monitor_stats.get('uptime_seconds', 0)
                if uptime > 0:
                    hours = int(uptime // 3600)
                    minutes = int((uptime % 3600) // 60)
                    seconds = int(uptime % 60)
                    self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
                else:
                    self.uptime_label.setText("Uptime: 00:00:00")
                    
            except Exception as e:
                pass  # Silently handle statistics update errors
    
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
        
        scan_action = QAction("New Scan...", self)
        scan_action.triggered.connect(self.open_scan_dialog)
        file_menu.addAction(scan_action)
        
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
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
        icon_path = Path(__file__).parent.parent.parent / 'icons' / 'org.xanados.SearchAndDestroy.svg'
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
        tray_menu = QMenu()
        
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
        
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.settings_shortcut.activated.connect(self.open_settings_dialog)
        
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
        icon_path = Path(__file__).parent.parent.parent / 'icons' / 'org.xanados.SearchAndDestroy-128.png'
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
        if self.current_theme == 'dark':
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
    
    def apply_dark_theme(self):
        """Apply dark theme styling using Strawberry color palette for optimal readability."""
        self.setStyleSheet("""
            QMainWindow {
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
            
            QPushButton#primaryButton {
                background-color: #9CB898;
                border: 2px solid #9CB898;
                color: #2b2b2b;
                font-weight: 700;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #B2CEB0;
                border-color: #B2CEB0;
            }
            
            QPushButton#dangerButton {
                background-color: #F14666;
                border: 2px solid #F14666;
                color: #ffffff;
                font-weight: 700;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #E6336B;
                border-color: #E6336B;
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
            
            QHeaderView::section {
                background-color: #404040;
                padding: 6px;
                border: 1px solid #EE8980;
                border-left: none;
                border-top: none;
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QTextEdit, QListWidget {
                border: 2px solid #EE8980;
                border-radius: 5px;
                background-color: #404040;
                color: #FFCDAA;
                font-weight: 500;
                selection-background-color: #F14666;
                selection-color: #ffffff;
            }
            
            QTextEdit:focus, QListWidget:focus {
                border-color: #F14666;
                background-color: #454545;
            }
            
            QLabel {
                color: #FFCDAA;
                font-weight: 600;
            }
            
            QStatusBar {
                background-color: #404040;
                color: #FFCDAA;
                border-top: 2px solid #EE8980;
                font-weight: 600;
            }
            
            QMenuBar {
                background-color: #404040;
                color: #FFCDAA;
                border-bottom: 2px solid #EE8980;
                font-weight: 600;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 10px;
            }
            
            QMenuBar::item:selected {
                background-color: #505050;
                color: #ffffff;
            }
            
            QMenu {
                background-color: #404040;
                color: #FFCDAA;
                border: 2px solid #F14666;
                font-weight: 600;
            }
            
            QMenu::item:selected {
                background-color: #EE8980;
                color: #ffffff;
            }
            
            #headerFrame {
                background-color: #F14666;
                color: white;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 12px;
            }
            
            #appTitle {
                color: white;
                font-size: 20px;
                font-weight: 700;
            }
            
            #pathLabel {
                font-weight: 600;
                padding: 6px;
                background-color: #505050;
                border-radius: 4px;
                color: #FFCDAA;
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
                background-color: #E6336B;
                border: 4px solid #EE8980;
                color: #ffffff;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #actionButton:pressed {
                background-color: #D12B5B;
                border: 4px solid #FFCDAA;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
                line-height: 1.2;
                font-size: 13px;
                /* Removed margins that were causing text cutoff */
            }
            
            #lastUpdateLabel {
                color: white;
                font-size: 12px;
                margin: 2px;
                font-weight: 600;
            }
            
            #lastCheckedLabel {
                color: white;
                font-size: 11px;
                margin: 1px;
                font-style: italic;
                font-weight: 500;
            }
            
            /* Scan report sections - maintain readability */
            #resultsText {
                font-weight: 500;
                color: #FFCDAA;
            }
            
            #reportViewer {
                font-weight: 500;
                color: #FFCDAA;
            }
            
            /* Real-time protection status styles */
            #protectionStatus {
                font-size: 16px;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                background-color: #404040;
                border: 2px solid #EE8980;
            }
            
            /* Dashboard Status Cards */
            QFrame#statusCard {
                background-color: #3a3a3a;
                border: 2px solid #EE8980;
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
            }
            
            QFrame#statusCard:hover {
                border-color: #F14666;
                background-color: #404040;
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
            
            /* Dashboard Action Buttons */
            QPushButton#dashboardPrimaryButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #9CB898, stop: 1 #8BA885);
                border: 3px solid #9CB898;
                border-radius: 8px;
                color: #2b2b2b;
                font-weight: 700;
                font-size: 14px;
                min-height: 40px;
                padding: 0px 20px;
            }
            
            QPushButton#dashboardPrimaryButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #B2CEB0, stop: 1 #9CB898);
                border-color: #B2CEB0;
            }
            
            QPushButton#dashboardSecondaryButton {
                background-color: #505050;
                border: 2px solid #EE8980;
                border-radius: 8px;
                color: #FFCDAA;
                font-weight: 600;
                font-size: 13px;
                min-height: 40px;
                padding: 0px 16px;
            }
            
            QPushButton#dashboardSecondaryButton:hover {
                background-color: #606060;
                border-color: #F14666;
                color: #ffffff;
            }
            
            /* Preset Scan Buttons */
            QPushButton#presetButton {
                background-color: #4a4a4a;
                border: 2px solid #EE8980;
                border-radius: 6px;
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 12px;
                min-height: 35px;
            }
            
            QPushButton#presetButton:hover {
                background-color: #5a5a5a;
                border-color: #F14666;
                color: #ffffff;
            }
            
            QLabel#presetLabel {
                color: #FFCDAA;
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 5px;
            }
        """)
    
    def apply_light_theme(self):
        """Apply light theme styling using Sunrise color palette for optimal readability."""
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
                background-color: #F07B7B;
                border-color: #F07B7B;
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
            
            QHeaderView::section {
                background-color: #F8D49B;
                padding: 8px;
                border: 1px solid #F8BC9B;
                border-left: none;
                border-top: none;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QTextEdit, QListWidget {
                border: 2px solid #F8D49B;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c2c2c;
                font-weight: 400;
                font-size: 11px;
                padding: 5px;
            }
            
            QTextEdit:focus, QListWidget:focus {
                border-color: #75BDE0;
            }
            
            QLabel {
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
            }
            
            QStatusBar {
                background-color: #F8D49B;
                color: #2c2c2c;
                border-top: 2px solid #F8BC9B;
                font-weight: 600;
                font-size: 11px;
            }
            
            QMenuBar {
                background-color: #F8D49B;
                color: #2c2c2c;
                border-bottom: 2px solid #F8BC9B;
                font-weight: 600;
                font-size: 11px;
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
                font-size: 11px;
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
                font-size: 11px;
            }
            
            #actionButton {
                background-color: #ffffff;
                color: #75BDE0;
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
                background-color: #F8D49B;
                color: #2c2c2c;
                border: 4px solid #F8BC9B;
                padding: 6px 12px;
                min-height: 32px;
                line-height: 1.3;
                font-size: 13px;
            }
            
            #actionButton:pressed {
                background-color: #F8BC9B;
                color: #1a1a1a;
                border: 4px solid #75BDE0;
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
                background-color: #FEFEFE;
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
                background-color: #FEFEFE;
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid #F8BC9B;
                text-align: center;
            }
            
            /* Scan report sections - maintain readability with Sunrise palette */
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
            
            #reportViewer {
                font-weight: 400;
                line-height: 1.5;
                color: #2c2c2c;
                background-color: #ffffff;
                border: 2px solid #F8D49B;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            
            /* HTML content styling in report viewer */
            #reportViewer h1, #reportViewer h2, #reportViewer h3 {
                color: #75BDE0;
                font-weight: 700;
                margin-top: 12px;
                margin-bottom: 8px;
            }
            
            #reportViewer h1 {
                font-size: 16px;
                border-bottom: 2px solid #F8D49B;
                padding-bottom: 4px;
            }
            
            #reportViewer h2 {
                font-size: 14px;
                color: #75BDE0;
            }
            
            #reportViewer h3 {
                font-size: 12px;
                color: #F8BC9B;
            }
            
            #reportViewer p {
                color: #2c2c2c;
                margin: 4px 0;
            }
            
            #reportViewer .threat-high {
                color: #F89B9B;
                font-weight: 600;
                background-color: #FEF5F5;
                padding: 2px 4px;
                border-radius: 3px;
            }
            
            #reportViewer .threat-medium {
                color: #F8BC9B;
                font-weight: 600;
                background-color: #FEF9F5;
                padding: 2px 4px;
                border-radius: 3px;
            }
            
            #reportViewer .threat-low {
                color: #75BDE0;
                font-weight: 600;
                background-color: #F5FAFF;
                padding: 2px 4px;
                border-radius: 3px;
            }
            
            #reportViewer .file-path {
                color: #2c2c2c;
                font-family: 'monospace', 'Consolas', 'Courier New';
                font-size: 10px;
                background-color: #F8F8F8;
                padding: 2px 4px;
                border-radius: 3px;
                margin: 2px 0;
            }
            
            /* Real-time protection status styles */
            #protectionStatus {
                font-size: 16px;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                background-color: #ffffff;
                border: 2px solid #75BDE0;
            }
            
            /* Dashboard Status Cards */
            QFrame#statusCard {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin: 5px;
            }
            
            QFrame#statusCard:hover {
                border-color: #75BDE0;
                background-color: #ffffff;
            }
            
            QLabel#cardTitle {
                color: #495057;
                font-weight: 600;
            }
            
            QLabel#cardDescription {
                color: #6c757d;
                line-height: 1.4;
            }
            
            /* Dashboard Action Buttons */
            QPushButton#dashboardPrimaryButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #28a745, stop: 1 #1e7e34);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            
            QPushButton#dashboardPrimaryButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #34ce57, stop: 1 #28a745);
            }
            
            QPushButton#dashboardSecondaryButton {
                background-color: #6c757d;
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                font-size: 13px;
            }
            
            QPushButton#dashboardSecondaryButton:hover {
                background-color: #5a6268;
            }
            
            /* Preset Scan Buttons */
            QPushButton#presetButton {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                color: #495057;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 12px;
                min-height: 35px;
            }
            
            QPushButton#presetButton:hover {
                background-color: #e9ecef;
                border-color: #75BDE0;
                color: #495057;
            }
            
            QLabel#presetLabel {
                color: #495057;
                font-weight: 600;
                font-size: 12px;
                margin-bottom: 5px;
            }
        """)
    
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
            
    def start_scan(self):
        if not hasattr(self, 'scan_path'):
            self.show_themed_message_box("warning", "Warning", "Please select a path to scan first.")
            return
            
        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        
        # Start scan in separate thread
        self.current_scan_thread = ScanThread(self.scanner, self.scan_path)
        self.current_scan_thread.progress_updated.connect(self.progress_bar.setValue)
        self.current_scan_thread.status_updated.connect(self.status_label.setText)
        self.current_scan_thread.scan_completed.connect(self.scan_completed)
        self.current_scan_thread.start()
    
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
                from pathlib import Path
                reports_dir = Path.home() / ".local/share/search-and-destroy/scan_reports/daily"
                if reports_dir.exists():
                    report_files = list(reports_dir.glob("scan_*.json"))
                    if report_files:
                        # Get the most recent file
                        latest_file = max(report_files, key=lambda p: p.stat().st_mtime)
                        try:
                            import json
                            with open(latest_file, 'r') as f:
                                report_data = json.load(f)
                            
                            scan_time = report_data.get('scan_metadata', {}).get('timestamp', '')
                            if scan_time:
                                from datetime import datetime
                                try:
                                    scan_date = datetime.fromisoformat(scan_time.replace('Z', '+00:00'))
                                    formatted_date = scan_date.strftime("%m/%d %H:%M")
                                except:
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
                        except Exception as file_error:
                            print(f"Error reading report file: {file_error}")
                            
            except Exception as e:
                print(f"Error updating dashboard cards: {e}")
                
    def scan_completed(self, result):
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        
        if 'error' in result:
            self.results_text.setText(f"Scan error: {result['error']}")
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
        except Exception as e:
            print(f"Unexpected error saving scan report: {e}")
        
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
        # Implement quick scan of common directories
        self.scan_path = os.path.expanduser("~")
        self.path_label.setText("Quick Scan (Home Directory)")
        self.start_scan()
    
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
                        
                except (subprocess.CalledProcessError, OSError, FileNotFoundError) as e:
                    self.update_status = f"Error updating definitions: {e}"
                    self.update_progress = 100
                    self.update_result = False
                except Exception as e:
                    self.update_status = f"Unexpected error updating definitions: {e}"
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
            
        except Exception as e:
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
                
        except Exception as e:
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
            
            if freshness.get('last_update'):
                # Parse the date string and format it nicely
                try:
                    last_update = datetime.fromisoformat(freshness['last_update'].replace('Z', '+00:00'))
                    # Format as readable date
                    formatted_date = last_update.strftime("%Y-%m-%d %H:%M")
                    label_text = f"Last updated: {formatted_date}"
                    self.last_update_label.setText(label_text)
                except (ValueError, AttributeError):
                    # If parsing fails, show the raw date
                    label_text = f"Last updated: {freshness['last_update']}"
                    self.last_update_label.setText(label_text)
            else:
                # Check if definitions exist at all
                if freshness.get('definitions_exist', False):
                    self.last_update_label.setText("Last updated: Unknown")
                else:
                    self.last_update_label.setText("No definitions found")
                    
        except Exception as e:
            print(f"Error checking definition status: {e}")
            self.last_update_label.setText("Status: Error checking")
            self.last_checked_label.setText(f"Last checked: {formatted_checked} (error)")
    
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
        
        # Accept the close event (actually close the application)
        event.accept()
        
        # Force application to quit
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def open_scan_dialog(self):
        from .scan_dialog import ScanDialog
        dialog = ScanDialog(self)
        dialog.exec()

    def open_settings_dialog(self):
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()
        
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
                    
                except Exception as e:
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
