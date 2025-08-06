"""
Enhanced Scan Interface with Progressive Disclosure
Reduces cognitive load by showing basic options first, with advanced options expandable
"""

def create_improved_scan_tab(self):
    """Create an improved scan tab with progressive disclosure."""
    scan_widget = QWidget()
    layout = QVBoxLayout(scan_widget)
    layout.setSpacing(15)
    
    # Simple Scan Section (Always Visible)
    simple_group = QGroupBox("Quick Scan")
    simple_layout = QVBoxLayout(simple_group)
    
    # Path selection with smart defaults
    path_layout = QHBoxLayout()
    path_label = QLabel("Scan Location:")
    
    # Preset scan options
    preset_layout = QHBoxLayout()
    home_scan_btn = QPushButton("Scan Home Folder")
    downloads_scan_btn = QPushButton("Scan Downloads")
    custom_scan_btn = QPushButton("Choose Folder...")
    
    preset_layout.addWidget(home_scan_btn)
    preset_layout.addWidget(downloads_scan_btn) 
    preset_layout.addWidget(custom_scan_btn)
    
    simple_layout.addWidget(path_label)
    simple_layout.addLayout(preset_layout)
    
    # Large, prominent scan button
    start_scan_btn = QPushButton("Start Scan")
    start_scan_btn.setObjectName("primaryScanButton")
    start_scan_btn.setMinimumHeight(50)
    simple_layout.addWidget(start_scan_btn)
    
    layout.addWidget(simple_group)
    
    # Advanced Options (Collapsible)
    self.advanced_group = QGroupBox("Advanced Options")
    self.advanced_group.setCheckable(True)
    self.advanced_group.setChecked(False)  # Collapsed by default
    
    advanced_layout = QVBoxLayout(self.advanced_group)
    
    # Scan type options
    scan_type_layout = QHBoxLayout()
    
    quick_radio = QRadioButton("Quick Scan")
    quick_radio.setChecked(True)
    deep_radio = QRadioButton("Deep Scan")
    custom_radio = QRadioButton("Custom Scan")
    
    scan_type_layout.addWidget(quick_radio)
    scan_type_layout.addWidget(deep_radio)
    scan_type_layout.addWidget(custom_radio)
    scan_type_layout.addStretch()
    
    advanced_layout.addLayout(scan_type_layout)
    
    # Additional options
    options_layout = QGridLayout()
    
    scan_archives_cb = QCheckBox("Scan inside archives")
    scan_email_cb = QCheckBox("Scan email files")
    scan_removable_cb = QCheckBox("Include removable drives")
    max_file_size_cb = QCheckBox("Limit file size scanning")
    
    options_layout.addWidget(scan_archives_cb, 0, 0)
    options_layout.addWidget(scan_email_cb, 0, 1)
    options_layout.addWidget(scan_removable_cb, 1, 0)
    options_layout.addWidget(max_file_size_cb, 1, 1)
    
    advanced_layout.addLayout(options_layout)
    
    layout.addWidget(self.advanced_group)
    
    # Progress Section (Enhanced)
    progress_group = QGroupBox("Scan Progress")
    progress_layout = QVBoxLayout(progress_group)
    
    # Status with better formatting
    self.scan_status_label = QLabel("Ready to scan")
    self.scan_status_label.setObjectName("scanStatusLabel")
    
    # Progress bar with percentage
    progress_container = QHBoxLayout()
    self.progress_bar = QProgressBar()
    self.progress_percentage = QLabel("0%")
    self.progress_percentage.setMinimumWidth(40)
    
    progress_container.addWidget(self.progress_bar)
    progress_container.addWidget(self.progress_percentage)
    
    # Real-time scan stats
    stats_layout = QHBoxLayout()
    self.files_scanned_label = QLabel("Files scanned: 0")
    self.scan_speed_label = QLabel("Speed: 0 files/sec")
    self.threats_found_label = QLabel("Threats: 0")
    
    stats_layout.addWidget(self.files_scanned_label)
    stats_layout.addWidget(self.scan_speed_label)
    stats_layout.addWidget(self.threats_found_label)
    stats_layout.addStretch()
    
    progress_layout.addWidget(self.scan_status_label)
    progress_layout.addLayout(progress_container)
    progress_layout.addLayout(stats_layout)
    
    layout.addWidget(progress_group)
    
    # Results section with better organization
    results_group = QGroupBox("Scan Results")
    results_layout = QVBoxLayout(results_group)
    
    # Results summary
    self.results_summary = QLabel("No scan results yet")
    self.results_summary.setObjectName("resultsSummary")
    results_layout.addWidget(self.results_summary)
    
    # Detailed results (collapsible)
    self.results_text = QTextEdit()
    self.results_text.setMaximumHeight(200)  # Limit height
    results_layout.addWidget(self.results_text)
    
    # Action buttons for results
    results_actions = QHBoxLayout()
    export_btn = QPushButton("Export Report")
    quarantine_btn = QPushButton("Quarantine Selected")
    
    results_actions.addWidget(export_btn)
    results_actions.addWidget(quarantine_btn)
    results_actions.addStretch()
    
    results_layout.addLayout(results_actions)
    
    layout.addWidget(results_group)
    
    return scan_widget
