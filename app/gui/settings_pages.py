"""Modular settings page builders separated from main_window for clarity."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QTextEdit, QGroupBox, QSpinBox)
from PyQt6.QtCore import QTime

# Expect host MainWindow to provide helper widget classes: NoWheelComboBox, NoWheelSpinBox, NoWheelTimeEdit

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

def build_rkhunter_page(host):
    page = QWidget(); v = QVBoxLayout(page); row = QHBoxLayout()
    for attr,label,default in [
        ('settings_enable_rkhunter_cb','Enable RKHunter Integration',False),
        ('settings_run_rkhunter_with_full_scan_cb','Full System',False),
        ('settings_run_rkhunter_with_quick_scan_cb','Quick Scans',False),
        ('settings_run_rkhunter_with_custom_scan_cb','Custom Scans',False),
        ('settings_rkhunter_auto_update_cb','Auto-update DB',True),
    ]:
        if not hasattr(host, attr):
            cb = QCheckBox(label); cb.setChecked(default); setattr(host, attr, cb)
        row.addWidget(getattr(host, attr))
    row.addStretch(); v.addLayout(row)
    if not hasattr(host, 'settings_rkhunter_test_categories'):
        host.settings_rkhunter_test_categories = {
            'system_commands': {'name':'System Commands','description':'System command integrity','default':True,'priority':1},
            'rootkits': {'name':'Rootkits & Trojans','description':'Known rootkits signatures','default':True,'priority':1},
            'system_integrity': {'name':'System Integrity','description':'Filesystem & config verification','default':True,'priority':2},
            'network': {'name':'Network Security','description':'Interfaces and ports','default':True,'priority':2},
            'applications': {'name':'Applications','description':'Hidden processes & files','default':False,'priority':3},
        }
    if not hasattr(host, 'settings_rkhunter_category_checkboxes'):
        host.settings_rkhunter_category_checkboxes = {}
    cat_row = QHBoxLayout(); cat_row.addStretch(1)
    for cid,info in sorted(host.settings_rkhunter_test_categories.items(), key=lambda x:(x[1]['priority'], x[1]['name'])):
        card = QVBoxLayout(); cb = host.settings_rkhunter_category_checkboxes.get(cid)
        if cb is None:
            cb = QCheckBox(info['name']); cb.setChecked(info['default']); cb.setToolTip(info['description']); host.settings_rkhunter_category_checkboxes[cid] = cb
        card.addWidget(cb); from PyQt6.QtWidgets import QLabel; desc = QLabel(info['description']); desc.setWordWrap(True); desc.setStyleSheet('font-size:11px;'); card.addWidget(desc); w = QWidget(); w.setLayout(card); w.setFixedWidth(160); w.setFixedHeight(120); cat_row.addWidget(w)
    cat_row.addStretch(1); v.addLayout(cat_row)
    btns = QHBoxLayout(); btns.addStretch(); b1 = QPushButton('Select All'); b1.clicked.connect(host.select_all_rkhunter_categories); btns.addWidget(b1); b2 = QPushButton('Recommended'); b2.clicked.connect(host.select_recommended_rkhunter_categories); btns.addWidget(b2); b3 = QPushButton('Select None'); b3.clicked.connect(host.select_no_rkhunter_categories); btns.addWidget(b3); btns.addStretch(); v.addLayout(btns); v.addStretch(); return page

def build_interface_page(host):
    page = QWidget(); layout = QVBoxLayout(page)
    from PyQt6.QtWidgets import QLabel, QComboBox, QFormLayout, QGroupBox
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
        ('reports_font_spin', 'Reports Text:', 'reports'),
        ('headers_font_spin', 'Headers & Titles:', 'headers'),
        ('small_font_spin', 'Small Text & Labels:', 'small')
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
                return handle_change
            
            spin.valueChanged.connect(make_change_handler(element_type))
            setattr(host, attr_name, spin)
        
        font_layout.addRow(label, getattr(host, attr_name))
    
    # Reset to defaults button
    if not hasattr(host, 'reset_fonts_btn'):
        host.reset_fonts_btn = QPushButton("Reset to Defaults")
        def reset_fonts():
            # Default font sizes
            defaults = {'base': 14, 'scan_results': 14, 'reports': 14, 'headers': 18, 'small': 12}
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
