"""
Enhanced Visual Feedback System
Provides clear status communication and better user feedback
"""

# Enhanced theme styles for better visual feedback
enhanced_dark_theme_styles = """
/* Status Card Styles */
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

/* Enhanced Button Styles */
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
    transform: translateY(-2px);
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

/* Enhanced Progress Bar */
QProgressBar#enhancedProgress {
    border: 2px solid #EE8980;
    border-radius: 8px;
    text-align: center;
    height: 24px;
    background-color: #404040;
    color: #FFCDAA;
    font-weight: 600;
    font-size: 12px;
}

QProgressBar#enhancedProgress::chunk {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #9CB898, stop: 0.5 #B2CEB0, stop: 1 #9CB898);
    border-radius: 6px;
    margin: 2px;
}

/* Status Labels with Color Coding */
QLabel#scanStatusLabel {
    font-size: 14px;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 6px;
    background-color: #404040;
    border: 2px solid #EE8980;
}

QLabel#scanStatusLabel[status="scanning"] {
    background-color: #4a90e2;
    border-color: #4a90e2;
    color: #ffffff;
}

QLabel#scanStatusLabel[status="complete"] {
    background-color: #9CB898;
    border-color: #9CB898;
    color: #2b2b2b;
}

QLabel#scanStatusLabel[status="error"] {
    background-color: #F14666;
    border-color: #F14666;
    color: #ffffff;
}

/* Results Summary Styling */
QLabel#resultsSummary {
    font-size: 16px;
    font-weight: 700;
    padding: 12px;
    border-radius: 8px;
    background-color: #404040;
    border: 2px solid #EE8980;
    color: #FFCDAA;
}

QLabel#resultsSummary[result="clean"] {
    background-color: #28a745;
    border-color: #28a745;
    color: #ffffff;
}

QLabel#resultsSummary[result="threats"] {
    background-color: #dc3545;
    border-color: #dc3545;
    color: #ffffff;
}

/* Enhanced Notification Styles */
QFrame#notificationFrame {
    background-color: #F14666;
    border: none;
    border-radius: 8px;
    padding: 12px;
    margin: 5px 0px;
}

QFrame#notificationFrame[type="success"] {
    background-color: #28a745;
}

QFrame#notificationFrame[type="warning"] {
    background-color: #ffc107;
    color: #212529;
}

QFrame#notificationFrame[type="info"] {
    background-color: #17a2b8;
}

/* Activity List Enhancements */
QListWidget#activityList {
    border: 2px solid #EE8980;
    border-radius: 8px;
    background-color: #404040;
    alternate-background-color: #454545;
    color: #FFCDAA;
    font-weight: 500;
    selection-background-color: #F14666;
    selection-color: #ffffff;
}

QListWidget#activityList::item {
    padding: 8px 12px;
    border-bottom: 1px solid #505050;
}

QListWidget#activityList::item:hover {
    background-color: #505050;
}

/* Microinteractions for buttons */
QPushButton {
    transition: all 0.2s ease-in-out;
}

QPushButton:pressed {
    transform: scale(0.98);
}

/* Improved spacing and typography */
QGroupBox {
    margin-top: 20px;
    padding-top: 15px;
}

QGroupBox::title {
    padding: 0px 12px;
    margin-top: -8px;
}
"""

def apply_enhanced_visual_feedback():
    """Apply enhanced visual feedback styles."""
    return enhanced_dark_theme_styles

def create_notification_widget(message, notification_type="info", duration=5000):
    """Create a non-intrusive notification widget."""
    notification = QFrame()
    notification.setObjectName("notificationFrame")
    notification.setProperty("type", notification_type)
    
    layout = QHBoxLayout(notification)
    layout.setContentsMargins(12, 8, 12, 8)
    
    # Icon based on type
    icons = {
        "success": "✅",
        "warning": "⚠️", 
        "error": "❌",
        "info": "ℹ️"
    }
    
    icon_label = QLabel(icons.get(notification_type, "ℹ️"))
    icon_label.setFixedSize(20, 20)
    
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    
    close_btn = QPushButton("×")
    close_btn.setFixedSize(20, 20)
    close_btn.setStyleSheet("border: none; font-weight: bold; color: inherit;")
    
    layout.addWidget(icon_label)
    layout.addWidget(message_label, 1)
    layout.addWidget(close_btn)
    
    # Auto-hide after duration
    if duration > 0:
        QTimer.singleShot(duration, notification.hide)
    
    return notification

def update_scan_status(status_label, status, details=""):
    """Update scan status with appropriate visual styling."""
    status_messages = {
        "ready": ("Ready to scan", ""),
        "scanning": ("Scanning in progress...", "scanning"),
        "complete": ("Scan completed", "complete"), 
        "error": ("Scan failed", "error"),
        "cancelled": ("Scan cancelled", "")
    }
    
    message, status_type = status_messages.get(status, ("Unknown status", ""))
    
    if details:
        message += f" - {details}"
    
    status_label.setText(message)
    if status_type:
        status_label.setProperty("status", status_type)
        status_label.style().polish(status_label)  # Refresh style
