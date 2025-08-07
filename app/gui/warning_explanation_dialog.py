#!/usr/bin/env python3
"""
RKHunter Warning Explanation Dialog
Provides detailed explanations and guidance for RKHunter warnings
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QWidget, QFrame, QGroupBox,
    QCheckBox, QMessageBox
)

from app.core.rkhunter_analyzer import WarningExplanation, SeverityLevel


class WarningExplanationDialog(QDialog):
    """Dialog to display detailed warning explanations."""
    
    # Signals
    mark_as_safe = pyqtSignal(str)  # Emit warning text when marked as safe
    investigate_requested = pyqtSignal(str)  # Emit warning text for investigation
    
    def __init__(self, warning_text: str, explanation: WarningExplanation, parent=None):
        super().__init__(parent)
        self.warning_text = warning_text
        self.explanation = explanation
        
        self.setWindowTitle("RKHunter Warning Explanation")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header with severity and icon
        header_layout = QHBoxLayout()
        
        # Severity icon
        severity_icon = self._get_severity_icon()
        icon_label = QLabel()
        icon_label.setPixmap(severity_icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Title and category
        title_layout = QVBoxLayout()
        
        title_label = QLabel(self.explanation.title)
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        category_text = self.explanation.category.value.replace('_', ' ').title()
        category_label = QLabel(f"Category: {category_text}")
        category_label.setFont(QFont("", 10))
        category_label.setStyleSheet("color: #666;")
        title_layout.addWidget(category_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Severity badge
        severity_badge = self._create_severity_badge()
        header_layout.addWidget(severity_badge)
        
        layout.addLayout(header_layout)
        
        # Original warning text
        warning_group = QGroupBox("Original Warning")
        warning_layout = QVBoxLayout(warning_group)
        
        warning_text_widget = QTextEdit()
        warning_text_widget.setPlainText(self.warning_text)
        warning_text_widget.setMaximumHeight(80)
        warning_text_widget.setReadOnly(True)
        warning_text_widget.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        warning_layout.addWidget(warning_text_widget)
        layout.addWidget(warning_group)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Description
        desc_group = QGroupBox("What This Means")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(self.explanation.description)
        desc_label.setWordWrap(True)
        desc_layout.addWidget(desc_label)
        scroll_layout.addWidget(desc_group)
        
        # Likely cause
        cause_group = QGroupBox("Likely Cause")
        cause_layout = QVBoxLayout(cause_group)
        cause_label = QLabel(self.explanation.likely_cause)
        cause_label.setWordWrap(True)
        cause_layout.addWidget(cause_label)
        scroll_layout.addWidget(cause_group)
        
        # Recommended action
        action_group = QGroupBox("Recommended Action")
        action_layout = QVBoxLayout(action_group)
        action_label = QLabel(self.explanation.recommended_action)
        action_label.setWordWrap(True)
        action_layout.addWidget(action_label)
        scroll_layout.addWidget(action_group)
        
        # Remediation steps (if available)
        if self.explanation.remediation_steps:
            steps_group = QGroupBox("Step-by-Step Remediation")
            steps_layout = QVBoxLayout(steps_group)
            
            for i, step in enumerate(self.explanation.remediation_steps, 1):
                step_label = QLabel(f"{i}. {step}")
                step_label.setWordWrap(True)
                step_label.setMargin(5)
                steps_layout.addWidget(step_label)
            
            scroll_layout.addWidget(steps_group)
        
        # Technical details (if available)
        if self.explanation.technical_details:
            tech_group = QGroupBox("Technical Details")
            tech_layout = QVBoxLayout(tech_group)
            tech_label = QLabel(self.explanation.technical_details)
            tech_label.setWordWrap(True)
            tech_label.setStyleSheet("font-style: italic; color: #555;")
            tech_layout.addWidget(tech_label)
            scroll_layout.addWidget(tech_group)
        
        # Common issue indicator
        if self.explanation.is_common:
            common_group = QGroupBox("ℹ️ Good to Know")
            common_layout = QVBoxLayout(common_group)
            common_label = QLabel("This is a common warning that often occurs during normal system operation. It's usually not a cause for concern.")
            common_label.setWordWrap(True)
            common_label.setStyleSheet("color: #28a745; font-weight: bold;")
            common_layout.addWidget(common_label)
            scroll_layout.addWidget(common_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Mark as safe checkbox and button
        self.mark_safe_checkbox = QCheckBox("I understand this warning and want to mark it as safe")
        button_layout.addWidget(self.mark_safe_checkbox)
        
        button_layout.addStretch()
        
        # Investigate button
        investigate_btn = QPushButton("🔍 Investigate Further")
        investigate_btn.clicked.connect(self._on_investigate)
        button_layout.addWidget(investigate_btn)
        
        # Mark as safe button
        mark_safe_btn = QPushButton("✅ Mark as Safe")
        mark_safe_btn.clicked.connect(self._on_mark_safe)
        mark_safe_btn.setEnabled(False)
        self.mark_safe_checkbox.toggled.connect(mark_safe_btn.setEnabled)
        button_layout.addWidget(mark_safe_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _get_severity_icon(self) -> QPixmap:
        """Get icon based on severity level."""
        # Create a simple colored circle icon based on severity
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # In a real implementation, you'd use proper icons
        # For now, we'll use the text-based icons from the analyzer
        icon_text = {
            SeverityLevel.LOW: "ℹ️",
            SeverityLevel.MEDIUM: "⚠️",
            SeverityLevel.HIGH: "🚨",
            SeverityLevel.CRITICAL: "🔴"
        }.get(self.explanation.severity, "❓")
        
        # For simplicity, return empty pixmap (icon text will be in badge)
        return pixmap
    
    def _create_severity_badge(self) -> QLabel:
        """Create severity level badge."""
        badge = QLabel(self.explanation.severity.value.upper())
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setMinimumSize(80, 30)
        
        # Color based on severity
        colors = {
            SeverityLevel.LOW: "#28a745",      # Green
            SeverityLevel.MEDIUM: "#ffc107",   # Yellow  
            SeverityLevel.HIGH: "#fd7e14",     # Orange
            SeverityLevel.CRITICAL: "#dc3545"  # Red
        }
        
        color = colors.get(self.explanation.severity, "#6c757d")
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
        return badge
    
    def _apply_styles(self):
        """Apply custom styles to the dialog."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
    
    def _on_investigate(self):
        """Handle investigate button click."""
        self.investigate_requested.emit(self.warning_text)
        # You could also open a web search or documentation
        QMessageBox.information(
            self, 
            "Investigation Tips",
            f"To investigate this warning further:\n\n"
            f"1. Search online for: \"{self.warning_text[:50]}...\"\n"
            f"2. Check RKHunter documentation\n"
            f"3. Review recent system changes\n"
            f"4. Consult security forums if concerned"
        )
    
    def _on_mark_safe(self):
        """Handle mark as safe button click."""
        if not self.mark_safe_checkbox.isChecked():
            return
            
        reply = QMessageBox.question(
            self,
            "Mark Warning as Safe",
            f"Are you sure you want to mark this warning as safe?\n\n"
            f"This will:\n"
            f"• Hide this warning in future scans\n"
            f"• Add it to the safe warnings list\n"
            f"• Reduce the warning count in reports\n\n"
            f"Only do this if you're confident the warning is harmless.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.mark_as_safe.emit(self.warning_text)
            self.accept()
