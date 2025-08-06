"""
Practical GUI Improvements for S&D Main Window
This file contains ready-to-implement code snippets that can be directly integrated
into your existing main_window.py file.
"""

# 1. QUICK WIN: Reduce header icon size and improve layout
def improve_header_section(self, layout):
    """Replace the existing create_header_section with this improved version."""
    header_frame = QFrame()
    header_frame.setObjectName("headerFrame")
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(20, 15, 20, 15)
    
    # Improved title section with smaller icon
    title_layout = QHBoxLayout()
    
    # Smaller, more proportional icon
    self.icon_label = QLabel()
    self.icon_label.setFixedSize(64, 64)  # Reduced from 128x128
    self.update_icon_for_theme()
    title_layout.addWidget(self.icon_label)
    
    # Better typography for title
    title_label = QLabel("S&D - Search & Destroy")
    title_label.setObjectName("appTitle")
    title_font = QFont()
    title_font.setPointSize(16)  # Reduced from 18
    title_font.setBold(True)
    title_label.setFont(title_font)
    
    # Add subtitle for better context
    subtitle_label = QLabel("Advanced Threat Detection & Removal")
    subtitle_label.setObjectName("appSubtitle")
    subtitle_font = QFont()
    subtitle_font.setPointSize(11)
    subtitle_font.setWeight(QFont.Weight.Normal)
    subtitle_label.setFont(subtitle_font)
    
    title_text_layout = QVBoxLayout()
    title_text_layout.addWidget(title_label)
    title_text_layout.addWidget(subtitle_label)
    
    title_layout.addLayout(title_text_layout)
    title_layout.addStretch()
    
    header_layout.addLayout(title_layout)
    
    # Improved quick actions with better spacing
    actions_layout = QHBoxLayout()
    actions_layout.setSpacing(15)
    
    # More descriptive button labels
    quick_scan_btn = QPushButton("Quick Scan")
    quick_scan_btn.setObjectName("headerActionButton")
    quick_scan_btn.setToolTip("Scan commonly infected areas (5-10 minutes)")
    quick_scan_btn.clicked.connect(self.quick_scan)
    
    update_btn = QPushButton("Update Virus Definitions")  # More descriptive
    update_btn.setObjectName("headerActionButton")
    update_btn.setToolTip("Download latest threat definitions")
    update_btn.clicked.connect(self.update_definitions)
    
    # Status indicator for updates (less intrusive than separate labels)
    self.update_status_icon = QLabel("●")
    self.update_status_icon.setObjectName("updateStatusIcon")
    self.update_status_icon.setToolTip("Definitions status")
    
    settings_btn = QPushButton("Settings")
    settings_btn.setObjectName("headerActionButton")
    settings_btn.setToolTip("Configure scan options and preferences")
    settings_btn.clicked.connect(self.open_settings_dialog)
    
    actions_layout.addWidget(quick_scan_btn)
    actions_layout.addWidget(update_btn)
    actions_layout.addWidget(self.update_status_icon)
    actions_layout.addWidget(settings_btn)
    
    header_layout.addLayout(actions_layout)
    layout.addWidget(header_frame)

# 2. DASHBOARD TAB: Add as first tab for better overview
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
    protection_card = self.create_status_card(
        "Real-Time Protection",
        "Active" if self.monitoring_enabled else "Inactive",
        "#28a745" if self.monitoring_enabled else "#dc3545",
        "Your system is being monitored" if self.monitoring_enabled else "Click to enable protection"
    )
    protection_card.mousePressEvent = lambda e: self.tab_widget.setCurrentIndex(2)  # Go to protection tab
    
    # Last Scan Card
    last_scan_card = self.create_status_card(
        "Last Scan",
        "2 hours ago",  # TODO: Get from scan history
        "#17a2b8",
        "Full system scan completed successfully"
    )
    last_scan_card.mousePressEvent = lambda e: self.tab_widget.setCurrentIndex(3)  # Go to reports tab
    
    # Threats Card
    threats_card = self.create_status_card(
        "Threats Found",
        "0",  # TODO: Get from scan results
        "#28a745",
        "No threats detected in recent scans"
    )
    threats_card.mousePressEvent = lambda e: self.tab_widget.setCurrentIndex(4)  # Go to quarantine tab
    
    status_row.addWidget(protection_card)
    status_row.addWidget(last_scan_card)
    status_row.addWidget(threats_card)
    
    layout.addLayout(status_row)
    
    # Quick Actions Section
    actions_group = QGroupBox("Quick Actions")
    actions_layout = QGridLayout(actions_group)
    actions_layout.setSpacing(15)
    
    # Large, prominent action buttons
    quick_scan_btn = QPushButton("Quick Scan")
    quick_scan_btn.setObjectName("dashboardPrimaryButton")
    quick_scan_btn.setMinimumHeight(60)
    quick_scan_btn.setToolTip("Scan Downloads, Desktop, and Documents folders")
    quick_scan_btn.clicked.connect(self.quick_scan)
    
    full_scan_btn = QPushButton("Full System Scan")
    full_scan_btn.setObjectName("dashboardSecondaryButton")
    full_scan_btn.setMinimumHeight(60)
    full_scan_btn.setToolTip("Comprehensive scan of entire system")
    full_scan_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
    
    custom_scan_btn = QPushButton("Custom Scan")
    custom_scan_btn.setObjectName("dashboardSecondaryButton")
    custom_scan_btn.setMinimumHeight(60)
    custom_scan_btn.setToolTip("Choose specific folders to scan")
    custom_scan_btn.clicked.connect(self.select_scan_path)
    
    update_btn = QPushButton("Update Definitions")
    update_btn.setObjectName("dashboardSecondaryButton") 
    update_btn.setMinimumHeight(60)
    update_btn.setToolTip("Download latest virus definitions")
    update_btn.clicked.connect(self.update_definitions)
    
    actions_layout.addWidget(quick_scan_btn, 0, 0, 1, 2)
    actions_layout.addWidget(full_scan_btn, 1, 0)
    actions_layout.addWidget(custom_scan_btn, 1, 1)
    actions_layout.addWidget(update_btn, 2, 0, 1, 2)
    
    layout.addWidget(actions_group)
    
    # Recent Activity Summary
    activity_group = QGroupBox("Recent Activity")
    activity_layout = QVBoxLayout(activity_group)
    
    self.dashboard_activity = QListWidget()
    self.dashboard_activity.setMaximumHeight(120)
    self.dashboard_activity.setAlternatingRowColors(True)
    activity_layout.addWidget(self.dashboard_activity)
    
    # Show more link
    show_more_btn = QPushButton("View All Activity →")
    show_more_btn.setFlat(True)
    show_more_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
    activity_layout.addWidget(show_more_btn)
    
    layout.addWidget(activity_group)
    
    layout.addStretch()
    
    # Insert as first tab
    self.tab_widget.insertTab(0, dashboard_widget, "Dashboard")
    self.tab_widget.setCurrentIndex(0)

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

# 3. IMPROVED TAB LABELS: Remove emojis for better consistency
def update_tab_labels(self):
    """Update tab labels to remove emojis and use clear text."""
    # This should be called after creating all tabs
    tab_labels = [
        "Dashboard",
        "Scan", 
        "Protection",
        "Reports",
        "Quarantine", 
        "Settings"
    ]
    
    for i, label in enumerate(tab_labels):
        if i < self.tab_widget.count():
            self.tab_widget.setTabText(i, label)

# 4. ENHANCED VISUAL STYLES: Add to your existing stylesheet
def get_dashboard_styles(self):
    """Additional styles for dashboard components."""
    return """
    /* Status Cards */
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
    
    /* Dashboard Buttons */
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
    
    /* Header Action Buttons */
    QPushButton#headerActionButton {
        background-color: rgba(255, 255, 255, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 6px;
        color: white;
        font-weight: 600;
        padding: 8px 16px;
        min-width: 100px;
    }
    
    QPushButton#headerActionButton:hover {
        background-color: rgba(255, 255, 255, 0.3);
        border-color: rgba(255, 255, 255, 0.5);
    }
    
    /* App Subtitle */
    QLabel#appSubtitle {
        color: rgba(255, 255, 255, 0.8);
        font-style: italic;
    }
    
    /* Update Status Icon */
    QLabel#updateStatusIcon {
        font-size: 12px;
        padding: 2px;
    }
    
    /* Card Text */
    QLabel#cardTitle {
        color: #495057;
        font-weight: 600;
    }
    
    QLabel#cardDescription {
        color: #6c757d;
        line-height: 1.4;
    }
    """

# 5. ACCESSIBILITY QUICK WINS: Add these to your __init__
def add_accessibility_features(self):
    """Add basic accessibility features."""
    # Keyboard shortcuts
    self.quick_scan_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
    self.quick_scan_shortcut.activated.connect(self.quick_scan)
    
    self.settings_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
    self.settings_shortcut.activated.connect(self.open_settings_dialog)
    
    # Accessible names and descriptions
    self.tab_widget.setAccessibleName("Main application tabs")
    
    if hasattr(self, 'start_scan_btn'):
        self.start_scan_btn.setAccessibleName("Start virus scan")
        self.start_scan_btn.setAccessibleDescription("Begin scanning selected directory for threats")
    
    if hasattr(self, 'progress_bar'):
        self.progress_bar.setAccessibleName("Scan progress indicator")

# 6. INTEGRATION INSTRUCTIONS
"""
To integrate these improvements into your existing main_window.py:

1. Replace your create_header_section method with improve_header_section
2. Add create_dashboard_tab call in your init_ui method BEFORE creating other tabs
3. Add create_status_card method to your MainWindow class
4. Call update_tab_labels() after creating all tabs
5. Add the dashboard styles to your existing stylesheet methods
6. Call add_accessibility_features() in your __init__ method

Example integration in init_ui():
    def init_ui(self):
        # ... existing code ...
        
        # Create dashboard tab first
        self.create_dashboard_tab()
        
        # Create other tabs
        self.create_scan_tab()
        self.create_real_time_tab()
        # ... etc ...
        
        # Update tab labels
        self.update_tab_labels()
        
        # Add accessibility
        self.add_accessibility_features()
"""
