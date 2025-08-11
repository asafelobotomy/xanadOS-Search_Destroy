"""Modular settings page builders separated from main_window for clarity."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QTextEdit)
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
    from PyQt6.QtWidgets import QLabel
    placeholder = QLabel('Additional interface customization options will appear here.')
    placeholder.setWordWrap(True); layout.addWidget(placeholder); layout.addStretch(); return page
