"""Modular settings page builders separated from main_window for clarity."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QTextEdit, QGroupBox, QSpinBox, QGridLayout, QScrollArea, QComboBox, QTabWidget, QFrame, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QListWidget, QListWidgetItem, QMessageBox, QDialog, QDialogButtonBox, QLineEdit)
from PyQt6.QtCore import Qt, QTime, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

try:
    from core.rkhunter_optimizer import RKHunterOptimizer, RKHunterConfig, RKHunterStatus, OptimizationReport
except ImportError:
    try:
        from app.core.rkhunter_optimizer import RKHunterOptimizer, RKHunterConfig, RKHunterStatus, OptimizationReport
    except ImportError:
        # Graceful fallback if module not available
        RKHunterOptimizer = None
        RKHunterConfig = None
        RKHunterStatus = None
        OptimizationReport = None

logger = logging.getLogger(__name__)

# Expect host MainWindow to provide helper widget classes: NoWheelComboBox, NoWheelSpinBox, NoWheelTimeEdit

class RKHunterOptimizationWorker(QThread):
    """Background worker for RKHunter optimization"""
    
    optimization_complete = pyqtSignal(object)  # OptimizationReport
    status_updated = pyqtSignal(object)  # RKHunterStatus
    progress_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.optimizer = RKHunterOptimizer() if RKHunterOptimizer else None
    
    def run(self):
        """Run RKHunter optimization in background"""
        if not self.optimizer:
            self.error_occurred.emit("RKHunter optimizer not available")
            return
            
        try:
            self.progress_updated.emit("Initializing RKHunter optimizer...")
            
            # Get current status first
            self.progress_updated.emit("Checking current RKHunter status...")
            status = self.optimizer.get_current_status()
            self.status_updated.emit(status)
            
            # Run optimization
            self.progress_updated.emit("Applying configuration optimizations...")
            report = self.optimizer.optimize_configuration(self.config)
            
            self.progress_updated.emit("Optimization complete")
            self.optimization_complete.emit(report)
            
        except Exception as e:
            logger.error(f"Error in RKHunter optimization: {e}")
            self.error_occurred.emit(str(e))

class RKHunterStatusWidget(QWidget):
    """Widget displaying RKHunter status information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_status = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("RKHunter Status")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status grid
        self.status_frame = QFrame()
        self.status_frame.setFrameStyle(QFrame.Shape.Box)
        status_layout = QGridLayout(self.status_frame)
        
        # Status items
        self.version_label = QLabel("Unknown")
        self.db_version_label = QLabel("Unknown")
        self.last_update_label = QLabel("Never")
        self.last_scan_label = QLabel("Never")
        self.baseline_label = QLabel("Unknown")
        self.mirror_label = QLabel("Unknown")
        
        status_layout.addWidget(QLabel("Version:"), 0, 0)
        status_layout.addWidget(self.version_label, 0, 1)
        status_layout.addWidget(QLabel("Database:"), 1, 0)
        status_layout.addWidget(self.db_version_label, 1, 1)
        status_layout.addWidget(QLabel("Last Update:"), 2, 0)
        status_layout.addWidget(self.last_update_label, 2, 1)
        status_layout.addWidget(QLabel("Last Scan:"), 3, 0)
        status_layout.addWidget(self.last_scan_label, 3, 1)
        status_layout.addWidget(QLabel("Baseline:"), 4, 0)
        status_layout.addWidget(self.baseline_label, 4, 1)
        status_layout.addWidget(QLabel("Mirrors:"), 5, 0)
        status_layout.addWidget(self.mirror_label, 5, 1)
        
        layout.addWidget(self.status_frame)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(refresh_btn)
    
    def refresh_status(self):
        """Refresh RKHunter status"""
        if RKHunterOptimizer:
            try:
                optimizer = RKHunterOptimizer()
                status = optimizer.get_current_status()
                self.update_status(status)
            except Exception as e:
                logger.error(f"Failed to refresh RKHunter status: {e}")
    
    def update_status(self, status):
        """Update status display"""
        if not status:
            return
            
        self.current_status = status
        self.version_label.setText(getattr(status, 'version', 'Unknown'))
        self.db_version_label.setText(getattr(status, 'database_version', 'Unknown'))
        self.last_update_label.setText(getattr(status, 'last_update', 'Never'))
        self.last_scan_label.setText(getattr(status, 'last_scan', 'Never'))
        self.baseline_label.setText(getattr(status, 'baseline_status', 'Unknown'))
        self.mirror_label.setText(getattr(status, 'mirror_status', 'Unknown'))

def build_general_page(host):
    page = QWidget(); layout = QVBoxLayout(page)
    if not hasattr(host, 'settings_activity_retention_combo'):
        host.settings_activity_retention_combo = host._make_activity_retention_combo()
    if not hasattr(host, 'settings_minimize_to_tray_cb'):
        host.settings_minimize_to_tray_cb = QCheckBox("Minimize to System Tray"); host.settings_minimize_to_tray_cb.setChecked(True)
    if not hasattr(host, 'settings_show_notifications_cb'):
        host.settings_show_notifications_cb = QCheckBox("Show Notifications"); host.settings_show_notifications_cb.setChecked(True)
    form = QFormLayout(); form.addRow("Activity Log Retention:", host.settings_activity_retention_combo); form.addRow(host.settings_minimize_to_tray_cb); form.addRow(host.settings_show_notifications_cb)
    layout.addLayout(form); layout.addStretch(); return page

def build_scanning_page(host):
    page = QWidget(); layout = QVBoxLayout(page)
    if not hasattr(host, 'settings_max_threads_spin'):
        host.settings_max_threads_spin = host._make_threads_spin()
    if not hasattr(host, 'settings_timeout_spin'):
        host.settings_timeout_spin = host._make_timeout_spin()
    if not hasattr(host, 'settings_scan_archives_cb'):
        host.settings_scan_archives_cb = QCheckBox('Scan Archive Files'); host.settings_scan_archives_cb.setChecked(True)
    if not hasattr(host, 'settings_follow_symlinks_cb'):
        host.settings_follow_symlinks_cb = QCheckBox('Follow Symbolic Links'); host.settings_follow_symlinks_cb.setChecked(False)
    if not hasattr(host, 'scan_depth_combo'):
        host.scan_depth_combo = host._make_depth_combo()
    if not hasattr(host, 'file_filter_combo'):
        host.file_filter_combo = host._make_file_filter_combo()
    if not hasattr(host, 'memory_limit_combo'):
        host.memory_limit_combo = host._make_memory_limit_combo()
    if not hasattr(host, 'exclusion_text'):
        host.exclusion_text = QTextEdit(); host.exclusion_text.setMaximumHeight(60)
    form = QFormLayout(); form.addRow('Max Threads:', host.settings_max_threads_spin); form.addRow('Scan Timeout:', host.settings_timeout_spin); form.addRow(host.settings_scan_archives_cb); form.addRow(host.settings_follow_symlinks_cb); form.addRow('Scan Depth:', host.scan_depth_combo); form.addRow('File Types:', host.file_filter_combo); form.addRow('Memory Limit:', host.memory_limit_combo); form.addRow('Exclusion Patterns:', host.exclusion_text)
    layout.addLayout(form); layout.addStretch(); return page

def build_realtime_page(host):
    page = QWidget(); form = QFormLayout(page)
    for attr,label,default in [
        ('settings_monitor_modifications_cb','Monitor File Modifications',True),
        ('settings_monitor_new_files_cb','Monitor New Files',True),
        ('settings_scan_modified_cb','Scan Modified Files Immediately',False),
    ]:
        if not hasattr(host, attr):
            cb = QCheckBox(label); cb.setChecked(default); setattr(host, attr, cb)
        form.addRow(getattr(host, attr))
    return page

def build_scheduling_page(host):
    page = QWidget(); form = QFormLayout(page)
    if not hasattr(host, 'settings_enable_scheduled_cb'):
        host.settings_enable_scheduled_cb = QCheckBox('Enable Scheduled Scans')
    if not hasattr(host, 'settings_scan_frequency_combo'):
        host.settings_scan_frequency_combo = host._make_frequency_combo()
    if not hasattr(host, 'settings_scan_time_edit'):
        host.settings_scan_time_edit = host._make_time_edit(); host.settings_scan_time_edit.setTime(QTime(2,0))
    if not hasattr(host, 'settings_scan_type_combo'):
        host.settings_scan_type_combo = host._make_scan_type_combo()
    if not hasattr(host, 'settings_custom_dir_widget'):
        host._build_custom_dir_widget()
    if not hasattr(host, 'settings_next_scan_label'):
        from PyQt6.QtWidgets import QLabel
        host.settings_next_scan_label = QLabel('None scheduled')
    form.addRow(host.settings_enable_scheduled_cb); form.addRow('Scan Frequency:', host.settings_scan_frequency_combo); form.addRow('Scan Time:', host.settings_scan_time_edit); form.addRow('Scan Type:', host.settings_scan_type_combo); form.addRow('Custom Directory:', host.settings_custom_dir_widget); form.addRow('Next Scan:', host.settings_next_scan_label)
    return page

def build_security_page(host):
    page = QWidget(); layout = QVBoxLayout(page)
    if not hasattr(host, 'settings_auto_update_cb'):
        host.settings_auto_update_cb = QCheckBox('Auto-update Virus Definitions'); host.settings_auto_update_cb.setChecked(True)
    layout.addWidget(host.settings_auto_update_cb); layout.addStretch(); return page

def build_firewall_page(host):
    """Build comprehensive firewall settings page with scroll area."""
    # Create main page widget
    page = QWidget()
    
    # Create scroll area to handle content overflow
    scroll_area = QScrollArea(page)
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    # Create scrollable content widget
    scroll_content = QWidget()
    layout = QVBoxLayout(scroll_content)
    layout.setSpacing(20)  # Better spacing between sections
    layout.setContentsMargins(15, 15, 15, 15)  # Add margins
    
    # === SECTION 1: FIREWALL STATUS & BASIC CONTROLS ===
    status_group = QGroupBox("Firewall Status & Basic Controls")
    status_layout = QVBoxLayout(status_group)
    status_layout.setSpacing(10)
    
    # Current firewall detection display
    if not hasattr(host, 'firewall_info_layout'):
        host.firewall_info_layout = QHBoxLayout()
        
        # Status labels
        host.firewall_name_display = QLabel("Detecting...")
        host.firewall_name_display.setStyleSheet("font-weight: bold; color: #3498db;")
        host.firewall_status_display = QLabel("Unknown")
        host.firewall_status_display.setStyleSheet("font-weight: bold;")
        
        host.firewall_info_layout.addWidget(QLabel("Detected Firewall:"))
        host.firewall_info_layout.addWidget(host.firewall_name_display)
        host.firewall_info_layout.addStretch()
        host.firewall_info_layout.addWidget(QLabel("Status:"))
        host.firewall_info_layout.addWidget(host.firewall_status_display)
    
    status_layout.addLayout(host.firewall_info_layout)
    
    # Auto-detection checkbox
    if not hasattr(host, 'settings_firewall_auto_detect_cb'):
        host.settings_firewall_auto_detect_cb = QCheckBox("Enable automatic firewall detection and monitoring")
        host.settings_firewall_auto_detect_cb.setChecked(True)
        host.settings_firewall_auto_detect_cb.setToolTip("Automatically detect and monitor your system's firewall status")
    status_layout.addWidget(host.settings_firewall_auto_detect_cb)
    
    # Notification settings
    if not hasattr(host, 'settings_firewall_notify_changes_cb'):
        host.settings_firewall_notify_changes_cb = QCheckBox("Notify when firewall status changes externally")
        host.settings_firewall_notify_changes_cb.setChecked(True)
        host.settings_firewall_notify_changes_cb.setToolTip("Show notifications when firewall is enabled/disabled outside the application")
    status_layout.addWidget(host.settings_firewall_notify_changes_cb)
    
    layout.addWidget(status_group)
    
    # === SECTION 2: FIREWALL BEHAVIOR SETTINGS ===
    behavior_group = QGroupBox("Firewall Behavior Settings")
    behavior_layout = QFormLayout(behavior_group)
    behavior_layout.setSpacing(10)
    
    # Preferred firewall type
    if not hasattr(host, 'settings_preferred_firewall_combo'):
        host.settings_preferred_firewall_combo = host.NoWheelComboBox() if hasattr(host, 'NoWheelComboBox') else QComboBox()
        host.settings_preferred_firewall_combo.addItems([
            "Auto-detect (Recommended)",
            "UFW (Uncomplicated Firewall)",
            "firewalld",
            "iptables (Direct)",
            "nftables"
        ])
        host.settings_preferred_firewall_combo.setCurrentText("Auto-detect (Recommended)")
        host.settings_preferred_firewall_combo.setToolTip("Choose which firewall to prefer when multiple are available")
    behavior_layout.addRow("Preferred Firewall:", host.settings_preferred_firewall_combo)
    
    # Confirmation dialogs
    if not hasattr(host, 'settings_firewall_confirm_enable_cb'):
        host.settings_firewall_confirm_enable_cb = QCheckBox("Confirm before enabling firewall")
        host.settings_firewall_confirm_enable_cb.setChecked(True)
    behavior_layout.addRow(host.settings_firewall_confirm_enable_cb)
    
    if not hasattr(host, 'settings_firewall_confirm_disable_cb'):
        host.settings_firewall_confirm_disable_cb = QCheckBox("Confirm before disabling firewall")
        host.settings_firewall_confirm_disable_cb.setChecked(True)
    behavior_layout.addRow(host.settings_firewall_confirm_disable_cb)
    
    # Authentication timeout
    if not hasattr(host, 'settings_firewall_auth_timeout_spin'):
        host.settings_firewall_auth_timeout_spin = host.NoWheelSpinBox() if hasattr(host, 'NoWheelSpinBox') else QSpinBox()
        host.settings_firewall_auth_timeout_spin.setRange(30, 600)  # 30 seconds to 10 minutes
        host.settings_firewall_auth_timeout_spin.setValue(300)  # Default 5 minutes
        host.settings_firewall_auth_timeout_spin.setSuffix(" seconds")
        host.settings_firewall_auth_timeout_spin.setToolTip("Timeout for authentication dialogs when controlling firewall")
    behavior_layout.addRow("Authentication Timeout:", host.settings_firewall_auth_timeout_spin)
    
    layout.addWidget(behavior_group)
    
    # === SECTION 3: ADVANCED SETTINGS ===
    advanced_group = QGroupBox("Advanced Settings")
    advanced_layout = QFormLayout(advanced_group)
    advanced_layout.setSpacing(10)
    
    # Fallback methods
    if not hasattr(host, 'settings_firewall_enable_fallbacks_cb'):
        host.settings_firewall_enable_fallbacks_cb = QCheckBox("Enable fallback methods")
        host.settings_firewall_enable_fallbacks_cb.setChecked(True)
        host.settings_firewall_enable_fallbacks_cb.setToolTip("Try alternative methods if primary firewall control fails")
    advanced_layout.addRow(host.settings_firewall_enable_fallbacks_cb)
    
    # Kernel module auto-loading
    if not hasattr(host, 'settings_firewall_auto_load_modules_cb'):
        host.settings_firewall_auto_load_modules_cb = QCheckBox("Attempt to load missing kernel modules")
        host.settings_firewall_auto_load_modules_cb.setChecked(True)
        host.settings_firewall_auto_load_modules_cb.setToolTip("Try to load iptables kernel modules if they're missing")
    advanced_layout.addRow(host.settings_firewall_auto_load_modules_cb)
    
    # Status check interval
    if not hasattr(host, 'settings_firewall_check_interval_spin'):
        host.settings_firewall_check_interval_spin = host.NoWheelSpinBox() if hasattr(host, 'NoWheelSpinBox') else QSpinBox()
        host.settings_firewall_check_interval_spin.setRange(5, 300)  # 5 seconds to 5 minutes
        host.settings_firewall_check_interval_spin.setValue(30)  # Default 30 seconds
        host.settings_firewall_check_interval_spin.setSuffix(" seconds")
        host.settings_firewall_check_interval_spin.setToolTip("How often to check firewall status for changes")
    advanced_layout.addRow("Status Check Interval:", host.settings_firewall_check_interval_spin)
    
    # Debug logging
    if not hasattr(host, 'settings_firewall_debug_logging_cb'):
        host.settings_firewall_debug_logging_cb = QCheckBox("Enable debug logging")
        host.settings_firewall_debug_logging_cb.setChecked(False)
        host.settings_firewall_debug_logging_cb.setToolTip("Log detailed firewall operation information for troubleshooting")
    advanced_layout.addRow(host.settings_firewall_debug_logging_cb)
    
    layout.addWidget(advanced_group)
    
    # === SECTION 4: CONTROL BUTTONS ===
    controls_group = QGroupBox("Firewall Controls")
    controls_layout = QHBoxLayout(controls_group)
    controls_layout.setSpacing(10)
    
    # Test connection button
    if not hasattr(host, 'firewall_test_btn'):
        host.firewall_test_btn = QPushButton("Test Firewall Connection")
        host.firewall_test_btn.setMinimumHeight(35)
        host.firewall_test_btn.setToolTip("Test if firewall can be controlled successfully")
        host.firewall_test_btn.clicked.connect(host.test_firewall_connection)
    controls_layout.addWidget(host.firewall_test_btn)
    
    # Refresh status button
    if not hasattr(host, 'firewall_refresh_btn'):
        host.firewall_refresh_btn = QPushButton("Refresh Status")
        host.firewall_refresh_btn.setMinimumHeight(35)
        host.firewall_refresh_btn.setToolTip("Manually refresh firewall status information")
        host.firewall_refresh_btn.clicked.connect(host.refresh_firewall_info)
    controls_layout.addWidget(host.firewall_refresh_btn)
    
    # Reset to defaults button
    if not hasattr(host, 'firewall_reset_defaults_btn'):
        host.firewall_reset_defaults_btn = QPushButton("Reset to Defaults")
        host.firewall_reset_defaults_btn.setMinimumHeight(35)
        host.firewall_reset_defaults_btn.setToolTip("Reset all firewall settings to default values")
        host.firewall_reset_defaults_btn.clicked.connect(host.reset_firewall_settings)
    controls_layout.addWidget(host.firewall_reset_defaults_btn)
    
    layout.addWidget(controls_group)
    
    # Initialize firewall info display
    if hasattr(host, 'refresh_firewall_info'):
        host.refresh_firewall_info()
    
    layout.addStretch()
    
    # Set up scroll area
    scroll_area.setWidget(scroll_content)
    
    # Main page layout
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)  # No margins on main page
    page_layout.addWidget(scroll_area)
    
    return page

def build_rkhunter_page(host):
    """Build a comprehensive RKHunter settings page with optimization features."""
    # Create main page widget
    page = QWidget()
    main_layout = QVBoxLayout(page)
    main_layout.setContentsMargins(5, 5, 5, 5)
    
    # Create tab widget for organization
    tab_widget = QTabWidget()
    tab_widget.setTabPosition(QTabWidget.TabPosition.North)
    
    # === TAB 1: BASIC CONFIGURATION ===
    basic_tab = QWidget()
    basic_scroll = QScrollArea(basic_tab)
    basic_scroll.setWidgetResizable(True)
    basic_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    basic_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    basic_content = QWidget()
    basic_layout = QVBoxLayout(basic_content)
    basic_layout.setSpacing(20)
    basic_layout.setContentsMargins(15, 15, 15, 15)
    
    # Basic Configuration Group
    basic_group = QGroupBox("Basic Configuration")
    basic_group_layout = QVBoxLayout(basic_group)
    basic_group_layout.setSpacing(10)
    
    # Enable RKHunter - Primary setting at the top
    if not hasattr(host, 'settings_enable_rkhunter_cb'):
        host.settings_enable_rkhunter_cb = QCheckBox('Enable RKHunter Integration')
        host.settings_enable_rkhunter_cb.setChecked(False)
        host.settings_enable_rkhunter_cb.setStyleSheet("font-weight: bold; font-size: 14px;")
    basic_group_layout.addWidget(host.settings_enable_rkhunter_cb)
    
    # Auto-update setting
    if not hasattr(host, 'settings_rkhunter_auto_update_cb'):
        host.settings_rkhunter_auto_update_cb = QCheckBox('Auto-update Database')
        host.settings_rkhunter_auto_update_cb.setChecked(True)
    basic_group_layout.addWidget(host.settings_rkhunter_auto_update_cb)
    
    basic_layout.addWidget(basic_group)
    
    # Scan Integration Group
    scan_group = QGroupBox("Scan Integration")
    scan_layout = QVBoxLayout(scan_group)
    scan_layout.setSpacing(8)
    
    # Description
    desc_label = QLabel("Configure when RKHunter should run alongside ClamAV scans:")
    desc_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
    scan_layout.addWidget(desc_label)
    
    # Scan type checkboxes
    scan_options = [
        ('settings_run_rkhunter_with_full_scan_cb', 'Run with Full System Scans', False),
        ('settings_run_rkhunter_with_quick_scan_cb', 'Run with Quick Scans', False),
        ('settings_run_rkhunter_with_custom_scan_cb', 'Run with Custom Scans', False),
    ]
    
    for attr, label, default in scan_options:
        if not hasattr(host, attr):
            cb = QCheckBox(label)
            cb.setChecked(default)
            setattr(host, attr, cb)
        scan_layout.addWidget(getattr(host, attr))
    
    basic_layout.addWidget(scan_group)
    
    # Security Categories Group
    categories_group = QGroupBox("Security Check Categories")
    categories_layout = QVBoxLayout(categories_group)
    categories_layout.setSpacing(15)
    
    # Description
    cat_desc = QLabel("Select which security checks RKHunter should perform:")
    cat_desc.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
    categories_layout.addWidget(cat_desc)
    
    # Initialize categories data
    if not hasattr(host, 'settings_rkhunter_test_categories'):
        host.settings_rkhunter_test_categories = {
            'rootkits': {'name':'Rootkits & Trojans','description':'Known rootkits signatures','default':True,'priority':1},
            'system_commands': {'name':'System Commands','description':'System command integrity','default':True,'priority':1},
            'network': {'name':'Network Security','description':'Interfaces and ports','default':True,'priority':2},
            'system_integrity': {'name':'System Integrity','description':'Filesystem & config verification','default':True,'priority':2},
            'applications': {'name':'Applications','description':'Hidden processes & files','default':False,'priority':3},
        }
    
    if not hasattr(host, 'settings_rkhunter_category_checkboxes'):
        host.settings_rkhunter_category_checkboxes = {}
    
    # Create a grid layout for better organization
    categories_grid = QGridLayout()
    categories_grid.setSpacing(15)
    categories_grid.setColumnStretch(0, 1)
    categories_grid.setColumnStretch(1, 1)
    
    # Sort categories by priority and create cards
    sorted_categories = sorted(host.settings_rkhunter_test_categories.items(), 
                             key=lambda x: (x[1]['priority'], x[1]['name']))
    
    for index, (cid, info) in enumerate(sorted_categories):
        # Create card widget
        card_widget = QWidget()
        card_widget.setMinimumHeight(100)
        card_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        card_layout = QVBoxLayout(card_widget)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        # Checkbox
        cb = host.settings_rkhunter_category_checkboxes.get(cid)
        if cb is None:
            cb = QCheckBox(info['name'])
            cb.setChecked(info['default'])
            cb.setStyleSheet("font-weight: bold;")
            host.settings_rkhunter_category_checkboxes[cid] = cb
        
        # Description
        desc_label = QLabel(info['description'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 11px; color: #888;")
        
        card_layout.addWidget(cb)
        card_layout.addWidget(desc_label)
        card_layout.addStretch()
        
        # Add to grid (2 columns)
        row = index // 2
        col = index % 2
        categories_grid.addWidget(card_widget, row, col)
    
    categories_layout.addLayout(categories_grid)
    
    # Quick Actions
    actions_layout = QHBoxLayout()
    actions_layout.setSpacing(10)
    actions_layout.addStretch()
    
    select_all_btn = QPushButton('Select All')
    select_all_btn.setMinimumWidth(100)
    select_all_btn.clicked.connect(host.select_all_rkhunter_categories)
    
    recommended_btn = QPushButton('Recommended')
    recommended_btn.setMinimumWidth(100)
    recommended_btn.setStyleSheet("font-weight: bold;")
    recommended_btn.clicked.connect(host.select_recommended_rkhunter_categories)
    
    select_none_btn = QPushButton('Select None')
    select_none_btn.setMinimumWidth(100)
    select_none_btn.clicked.connect(host.select_no_rkhunter_categories)
    
    actions_layout.addWidget(select_all_btn)
    actions_layout.addWidget(recommended_btn)
    actions_layout.addWidget(select_none_btn)
    actions_layout.addStretch()
    
    categories_layout.addLayout(actions_layout)
    basic_layout.addWidget(categories_group)
    
    basic_layout.addStretch()
    basic_scroll.setWidget(basic_content)
    basic_tab_layout = QVBoxLayout(basic_tab)
    basic_tab_layout.setContentsMargins(0, 0, 0, 0)
    basic_tab_layout.addWidget(basic_scroll)
    
    # === TAB 2: OPTIMIZATION & STATUS ===
    optimization_tab = QWidget()
    
    # Create scroll area for optimization tab
    opt_scroll = QScrollArea(optimization_tab)
    opt_scroll.setWidgetResizable(True)
    opt_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    opt_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    # Create scrollable content widget
    opt_content = QWidget()
    opt_layout = QVBoxLayout(opt_content)
    opt_layout.setSpacing(15)
    opt_layout.setContentsMargins(15, 15, 15, 15)
    
    # Status Section
    status_group = QGroupBox("Current Status")
    status_layout = QVBoxLayout(status_group)
    
    # Add status widget
    if not hasattr(host, 'rkhunter_status_widget'):
        host.rkhunter_status_widget = RKHunterStatusWidget()
    status_layout.addWidget(host.rkhunter_status_widget)
    opt_layout.addWidget(status_group)
    
    # Optimization Controls
    opt_controls_group = QGroupBox("Optimization Controls")
    opt_controls_layout = QVBoxLayout(opt_controls_group)
    
    # Performance mode selection
    perf_layout = QHBoxLayout()
    perf_layout.addWidget(QLabel("Performance Mode:"))
    
    if not hasattr(host, 'rkhunter_perf_mode_combo'):
        host.rkhunter_perf_mode_combo = QComboBox()
        host.rkhunter_perf_mode_combo.addItems(['Fast', 'Balanced', 'Thorough'])
        host.rkhunter_perf_mode_combo.setCurrentText('Balanced')
    perf_layout.addWidget(host.rkhunter_perf_mode_combo)
    perf_layout.addStretch()
    opt_controls_layout.addLayout(perf_layout)
    
    # Optimization buttons
    opt_buttons_layout = QHBoxLayout()
    
    if not hasattr(host, 'rkhunter_update_mirrors_btn'):
        host.rkhunter_update_mirrors_btn = QPushButton("Update Mirrors")
        host.rkhunter_update_mirrors_btn.clicked.connect(lambda: host.run_rkhunter_optimization('update_mirrors'))
    
    if not hasattr(host, 'rkhunter_update_baseline_btn'):
        host.rkhunter_update_baseline_btn = QPushButton("Update Baseline")
        host.rkhunter_update_baseline_btn.clicked.connect(lambda: host.run_rkhunter_optimization('update_baseline'))
    
    if not hasattr(host, 'rkhunter_optimize_config_btn'):
        host.rkhunter_optimize_config_btn = QPushButton("Optimize Configuration")
        host.rkhunter_optimize_config_btn.clicked.connect(lambda: host.run_rkhunter_optimization('optimize_config'))
        host.rkhunter_optimize_config_btn.setStyleSheet("font-weight: bold;")
    
    opt_buttons_layout.addWidget(host.rkhunter_update_mirrors_btn)
    opt_buttons_layout.addWidget(host.rkhunter_update_baseline_btn)
    opt_buttons_layout.addWidget(host.rkhunter_optimize_config_btn)
    opt_buttons_layout.addStretch()
    
    opt_controls_layout.addLayout(opt_buttons_layout)
    
    # Progress section
    if not hasattr(host, 'rkhunter_progress_bar'):
        host.rkhunter_progress_bar = QProgressBar()
        host.rkhunter_progress_bar.setVisible(False)
    
    if not hasattr(host, 'rkhunter_progress_label'):
        host.rkhunter_progress_label = QLabel("")
        host.rkhunter_progress_label.setVisible(False)
    
    opt_controls_layout.addWidget(host.rkhunter_progress_label)
    opt_controls_layout.addWidget(host.rkhunter_progress_bar)
    
    opt_layout.addWidget(opt_controls_group)
    
    # Results section
    results_group = QGroupBox("Optimization Results")
    results_layout = QVBoxLayout(results_group)
    
    if not hasattr(host, 'rkhunter_results_text'):
        host.rkhunter_results_text = QTextEdit()
        host.rkhunter_results_text.setMaximumHeight(200)
        host.rkhunter_results_text.setPlaceholderText("Optimization results will appear here...")
    
    results_layout.addWidget(host.rkhunter_results_text)
    opt_layout.addWidget(results_group)
    
    # Add extra spacing at the bottom for better scrolling
    opt_layout.addSpacing(30)
    
    # Set up the scroll area
    opt_scroll.setWidget(opt_content)
    
    # Create optimization tab layout and add scroll area
    opt_tab_layout = QVBoxLayout(optimization_tab)
    opt_tab_layout.setContentsMargins(0, 0, 0, 0)
    opt_tab_layout.addWidget(opt_scroll)
    
    # Add tabs
    tab_widget.addTab(basic_tab, "⚙️ Configuration")
    tab_widget.addTab(optimization_tab, "🔧 Optimization")
    
    main_layout.addWidget(tab_widget)
    
    # Initialize optimization worker if not exists
    if not hasattr(host, 'rkhunter_optimization_worker'):
        host.rkhunter_optimization_worker = None
    
    return page
    
    return page

def build_interface_page(host):
    page = QWidget(); layout = QVBoxLayout(page)
    from gui.theme_manager import get_theme_manager
    
    # Text Orientation Group
    orientation_group = QGroupBox("Text Orientation")
    orientation_layout = QFormLayout(orientation_group)
    
    # Create text orientation setting
    if not hasattr(host, 'text_orientation_combo'):
        host.text_orientation_combo = host.NoWheelComboBox() if hasattr(host, 'NoWheelComboBox') else QComboBox()
        host.text_orientation_combo.addItems(['Left Aligned', 'Centered', 'Right Aligned'])
        host.text_orientation_combo.setCurrentText('Centered')  # Default to current behavior
        # Connect to apply changes immediately (this also triggers auto-save)
        host.text_orientation_combo.currentTextChanged.connect(host.apply_text_orientation_setting)
    
    orientation_layout.addRow('Scan Results Text Orientation:', host.text_orientation_combo)
    
    # Font Size Group
    font_group = QGroupBox("Font Sizes")
    font_layout = QFormLayout(font_group)
    
    # Create font size spinboxes for different interface elements
    font_elements = [
        ('base_font_spin', 'Base Font Size (Buttons, Tabs, Cards):', 'base'),
        ('scan_results_font_spin', 'Scan Results Text:', 'scan_results'),
        ('reports_font_spin', 'Scan Reports Text:', 'reports'),
        ('activity_font_spin', 'Activity Report Text:', 'activity')
    ]
    
    for attr_name, label, element_type in font_elements:
        if not hasattr(host, attr_name):
            spin = host.NoWheelSpinBox() if hasattr(host, 'NoWheelSpinBox') else QSpinBox()
            spin.setRange(8, 24)  # Reasonable font size range
            spin.setValue(get_theme_manager().get_font_size(element_type))
            spin.setSuffix(' px')
            
            # Connect to apply changes immediately and save to config
            def make_change_handler(element_type):
                def handle_change(value):
                    get_theme_manager().set_font_size(element_type, value)
                    # Save to config
                    if 'ui_settings' not in host.config:
                        host.config['ui_settings'] = {}
                    if 'font_sizes' not in host.config['ui_settings']:
                        host.config['ui_settings']['font_sizes'] = {}
                    host.config['ui_settings']['font_sizes'][element_type] = value
                    host.save_config()
                    
                    # Special handling for activity font size - refresh activity list styling
                    if element_type == 'activity' and hasattr(host, 'setup_activity_list_styling'):
                        host.setup_activity_list_styling()
                        
                return handle_change
            
            spin.valueChanged.connect(make_change_handler(element_type))
            setattr(host, attr_name, spin)
        
        font_layout.addRow(label, getattr(host, attr_name))
    
    # Reset to defaults button
    if not hasattr(host, 'reset_fonts_btn'):
        host.reset_fonts_btn = QPushButton("Reset to Defaults")
        def reset_fonts():
            # Default font sizes
            defaults = {'base': 14, 'scan_results': 14, 'reports': 14, 'activity': 14}
            for element_type, default_size in defaults.items():
                get_theme_manager().set_font_size(element_type, default_size)
                # Update spinbox values
                for attr_name, _, elem_type in font_elements:
                    if elem_type == element_type and hasattr(host, attr_name):
                        getattr(host, attr_name).setValue(default_size)
            # Clear config
            if 'ui_settings' in host.config and 'font_sizes' in host.config['ui_settings']:
                del host.config['ui_settings']['font_sizes']
                host.save_config()
        
        host.reset_fonts_btn.clicked.connect(reset_fonts)
    
    font_layout.addRow('', host.reset_fonts_btn)
    
    # Add groups to main layout
    layout.addWidget(orientation_group)
    layout.addWidget(font_group)
    layout.addStretch()
    return page

def build_updates_page(host):
    """Build the auto-update settings page."""
    page = QWidget()
    layout = QVBoxLayout(page)
    
    # Auto-update settings group
    update_group = QGroupBox("Auto-Update Settings")
    form = QFormLayout(update_group)
    
    # Auto-check setting
    if not hasattr(host, 'settings_auto_check_updates_cb'):
        host.settings_auto_check_updates_cb = QCheckBox("Automatically check for updates")
        host.settings_auto_check_updates_cb.setChecked(True)
    form.addRow(host.settings_auto_check_updates_cb)
    
    # Check interval
    if not hasattr(host, 'settings_update_check_interval_spin'):
        host.settings_update_check_interval_spin = host.NoWheelSpinBox() if hasattr(host, 'NoWheelSpinBox') else QSpinBox()
        host.settings_update_check_interval_spin.setRange(1, 30)
        host.settings_update_check_interval_spin.setSuffix(" days")
        host.settings_update_check_interval_spin.setValue(1)
    form.addRow("Check interval:", host.settings_update_check_interval_spin)
    
    # Auto-download setting
    if not hasattr(host, 'settings_auto_download_updates_cb'):
        host.settings_auto_download_updates_cb = QCheckBox("Automatically download updates")
        host.settings_auto_download_updates_cb.setChecked(False)
    form.addRow(host.settings_auto_download_updates_cb)
    
    # Auto-install setting (with warning)
    if not hasattr(host, 'settings_auto_install_updates_cb'):
        host.settings_auto_install_updates_cb = QCheckBox("Automatically install updates")
        host.settings_auto_install_updates_cb.setChecked(False)
        host.settings_auto_install_updates_cb.setToolTip("Not recommended for security applications - manual review is safer")
    form.addRow(host.settings_auto_install_updates_cb)
    
    layout.addWidget(update_group)
    
    # Current version info group
    version_group = QGroupBox("Version Information")
    version_form = QFormLayout(version_group)
    
    # Current version display
    if not hasattr(host, 'current_version_label'):
        from gui import APP_VERSION
        host.current_version_label = QLabel(f"v{APP_VERSION}")
        host.current_version_label.setStyleSheet("font-weight: bold;")
    version_form.addRow("Current Version:", host.current_version_label)
    
    # Last update check
    if not hasattr(host, 'last_update_check_label'):
        host.last_update_check_label = QLabel("Never")
        # Try to load initial last check time - use a timer to ensure auto_updater is ready
        def load_initial_check_time():
            try:
                if hasattr(host, 'auto_updater') and host.auto_updater:
                    last_check = host.auto_updater.get_last_check_time()
                    if last_check:
                        host.last_update_check_label.setText(last_check)
            except Exception as e:
                print(f"Warning: Could not load initial last check time: {e}")
        
        # Delay loading to ensure auto_updater is initialized
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, load_initial_check_time)
        
    version_form.addRow("Last Update Check:", host.last_update_check_label)
    
    layout.addWidget(version_group)
    
    # Manual update controls
    manual_group = QGroupBox("Manual Update")
    manual_layout = QVBoxLayout(manual_group)
    
    # Check for updates button
    if not hasattr(host, 'check_updates_button'):
        host.check_updates_button = QPushButton("Check for Updates Now")
        host.check_updates_button.clicked.connect(host.open_update_dialog)
    manual_layout.addWidget(host.check_updates_button)
    
    # Update status label
    if not hasattr(host, 'update_status_label'):
        host.update_status_label = QLabel("Click 'Check for Updates Now' to check for the latest version")
        host.update_status_label.setStyleSheet("color: #666; font-style: italic;")
    manual_layout.addWidget(host.update_status_label)
    
    layout.addWidget(manual_group)
    
    layout.addStretch()
    return page
