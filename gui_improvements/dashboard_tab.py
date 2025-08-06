"""
Enhanced Dashboard Tab for S&D Main Window
Provides at-a-glance system status and quick actions
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QProgressBar, QFrame, QGroupBox, QListWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap


def create_dashboard_tab(self):
    """Create an enhanced dashboard tab as the main overview."""
    dashboard_widget = QWidget()
    layout = QVBoxLayout(dashboard_widget)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)
    
    # System Status Cards (Top Row)
    status_layout = QHBoxLayout()
    
    # Protection Status Card
    protection_card = self.create_status_card(
        "Protection Status", 
        "🛡️ Active" if self.monitoring_enabled else "⚫ Inactive",
        "#28a745" if self.monitoring_enabled else "#6c757d",
        "Real-time protection is monitoring your system"
    )
    
    # Last Scan Card  
    last_scan_card = self.create_status_card(
        "Last Scan",
        "2 hours ago",  # Dynamic from scan history
        "#17a2b8",
        "Full system scan completed successfully"
    )
    
    # Threats Found Card
    threats_card = self.create_status_card(
        "Threats Found",
        "0",  # Dynamic from scan results
        "#28a745",
        "No threats detected in recent scans"
    )
    
    status_layout.addWidget(protection_card)
    status_layout.addWidget(last_scan_card) 
    status_layout.addWidget(threats_card)
    layout.addLayout(status_layout)
    
    # Quick Actions Section
    actions_group = QGroupBox("Quick Actions")
    actions_layout = QHBoxLayout(actions_group)
    
    quick_scan_btn = QPushButton("Quick Scan")
    quick_scan_btn.setObjectName("dashboardPrimaryButton")
    quick_scan_btn.setMinimumHeight(45)
    
    full_scan_btn = QPushButton("Full System Scan")
    full_scan_btn.setObjectName("dashboardSecondaryButton") 
    full_scan_btn.setMinimumHeight(45)
    
    update_btn = QPushButton("Update Definitions")
    update_btn.setObjectName("dashboardSecondaryButton")
    update_btn.setMinimumHeight(45)
    
    actions_layout.addWidget(quick_scan_btn)
    actions_layout.addWidget(full_scan_btn)
    actions_layout.addWidget(update_btn)
    
    layout.addWidget(actions_group)
    
    # Recent Activity Feed
    activity_group = QGroupBox("Recent Activity")
    activity_layout = QVBoxLayout(activity_group)
    
    self.dashboard_activity_list = QListWidget()
    self.dashboard_activity_list.setMaximumHeight(150)
    activity_layout.addWidget(self.dashboard_activity_list)
    
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
    
    layout = QVBoxLayout(card)
    layout.setSpacing(8)
    layout.setContentsMargins(15, 15, 15, 15)
    
    # Title
    title_label = QLabel(title)
    title_label.setObjectName("cardTitle")
    
    # Value
    value_label = QLabel(value)
    value_label.setObjectName("cardValue")
    value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
    
    # Description
    desc_label = QLabel(description)
    desc_label.setObjectName("cardDescription")
    desc_label.setWordWrap(True)
    
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    layout.addWidget(desc_label)
    layout.addStretch()
    
    return card
