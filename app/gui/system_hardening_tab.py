#!/usr/bin/env python3
"""
System Hardening GUI Components
xanadOS Search & Destroy - Enhanced Security Interface

This module provides GUI components for displaying system hardening
status, security compliance scores, and hardening recommendations.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QProgressBar, QFrame,
                             QScrollArea, QGroupBox, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
import logging
from typing import List
from datetime import datetime

from core.system_hardening import SystemHardeningChecker, HardeningReport, SecurityFeature
from .themed_widgets import ThemedWidgetMixin
from .theme_manager import get_theme_manager

logger = logging.getLogger(__name__)

class HardeningWorker(QThread):
    """Background worker for system hardening checks"""
    
    report_ready = pyqtSignal(object)  # HardeningReport
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.checker = SystemHardeningChecker()
    
    def run(self):
        """Run hardening assessment in background"""
        try:
            self.progress_updated.emit("Initializing system hardening assessment...")
            
            self.progress_updated.emit("Checking kernel security features...")
            report = self.checker.check_all_hardening_features()
            
            self.progress_updated.emit("Assessment complete")
            self.report_ready.emit(report)
            
        except Exception as e:
            logger.error(f"Error in hardening assessment: {e}")
            self.error_occurred.emit(str(e))

class SecurityScoreWidget(ThemedWidgetMixin, QWidget):
    """Widget displaying security compliance score with visual indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.score = 0
        self.max_score = 100
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Security Compliance Score")
        title.setObjectName("header")  # Use global header styling
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Score display frame - use global card styling
        self.score_frame = QFrame()
        self.score_frame.setObjectName("statusCard")  # Use global status card styling
        score_layout = QVBoxLayout(self.score_frame)
        
        self.score_label = QLabel("0/100")
        self.score_label.setObjectName("cardValue")  # Use global card value styling
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.score_label)
        
        # Progress bar - let global theming handle the styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        score_layout.addWidget(self.progress_bar)
        
        self.compliance_label = QLabel("No Assessment")
        self.compliance_label.setObjectName("cardTitle")  # Use global card title styling
        self.compliance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.score_frame)
        
        # Last updated
        self.updated_label = QLabel("Last Updated: Never")
        self.updated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.updated_label.setObjectName("secondary")  # Use global secondary text styling
        layout.addWidget(self.updated_label)
    
    def update_score(self, score: int, max_score: int, compliance_level: str, timestamp: str):
        """Update the security score display"""
        self.score = score
        self.max_score = max_score
        
        # Update labels
        self.score_label.setText(f"{score}/{max_score}")
        self.compliance_label.setText(compliance_level)
        
        # Update progress bar with animation
        percentage = int((score / max_score) * 100) if max_score > 0 else 0
        self.progress_bar.setValue(percentage)
        
        # Use theme colors for compliance level styling
        theme = get_theme_manager()
        if percentage >= 90:
            color = theme.get_color('success')
        elif percentage >= 75:
            color = theme.get_color('strawberry_sage')
        elif percentage >= 50:
            color = theme.get_color('warning')
        else:
            color = theme.get_color('error')
        
        # Apply theme-aware styling to compliance label
        self.compliance_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        # Update timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.updated_label.setText(f"Last Updated: {formatted_time}")
        except:
            self.updated_label.setText(f"Last Updated: {timestamp}")

class SecurityFeatureTable(QTableWidget):
    """Table widget for displaying security features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        # Set up columns
        headers = ["Feature", "Status", "Severity", "Score Impact", "Description"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table appearance - let global theming handle most styling
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Feature
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Severity
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Score
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Description
        
        # Remove custom styling - let global theme handle it
    
    def populate_features(self, features: List[SecurityFeature]):
        """Populate table with security features"""
        self.setRowCount(len(features))
        theme = get_theme_manager()
        
        for row, feature in enumerate(features):
            # Feature name
            name_item = QTableWidgetItem(feature.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, name_item)
            
            # Status with better theming and contrast
            status_item = QTableWidgetItem("Enabled" if feature.enabled else "Disabled")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Use text color approach instead of background for better readability
            if feature.enabled:
                # Success state - use theme success color with subtle background
                status_item.setForeground(QColor(theme.get_color('success')))
                status_item.setBackground(QColor(theme.get_color('success')).lighter(230))  # Very light background
            else:
                # Error state - use theme error color with subtle background  
                status_item.setForeground(QColor(theme.get_color('error')))
                status_item.setBackground(QColor(theme.get_color('error')).lighter(230))  # Very light background
            
            # Set font weight for better visibility
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            
            self.setItem(row, 1, status_item)
            
            # Severity with enhanced theme-aware styling
            severity_item = QTableWidgetItem(feature.severity.upper())
            severity_item.setFlags(severity_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Use theme colors for severity with consistent styling
            severity_colors = {
                'critical': theme.get_color('error'),
                'high': theme.get_color('warning'), 
                'medium': theme.get_color('accent'),
                'low': theme.get_color('success')
            }
            
            if feature.severity in severity_colors:
                color = QColor(severity_colors[feature.severity])
                severity_item.setForeground(color)
                # Add subtle background tint for better visual distinction
                severity_item.setBackground(color.lighter(240))
                
                # Make severity text bold for better readability
                font = severity_item.font()
                font.setBold(True)
                severity_item.setFont(font)
            
            self.setItem(row, 2, severity_item)
            
            # Score impact
            score_item = QTableWidgetItem(str(feature.score_impact))
            score_item.setFlags(score_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 3, score_item)
            
            # Description
            desc_item = QTableWidgetItem(feature.description)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            desc_item.setToolTip(feature.recommendation)  # Show recommendation on hover
            self.setItem(row, 4, desc_item)

class HardeningRecommendationsWidget(ThemedWidgetMixin, QWidget):
    """Widget for displaying hardening recommendations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title using global styling
        title = QLabel("Security Recommendations")
        title.setObjectName("header")  # Use global header styling
        layout.addWidget(title)
        
        # Recommendations text area - optimized for side-by-side layout
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        # Increase height since we now have more vertical space available
        self.recommendations_text.setMinimumHeight(300)
        self.recommendations_text.setMaximumHeight(400)
        layout.addWidget(self.recommendations_text)
    
    def update_recommendations(self, recommendations: List[str]):
        """Update the recommendations display"""
        if not recommendations:
            self.recommendations_text.setHtml("<i>No specific recommendations at this time.</i>")
            return
        
        html_content = "<ul>"
        for rec in recommendations:
            html_content += f"<li>{rec}</li>"
        html_content += "</ul>"
        
        self.recommendations_text.setHtml(html_content)

class SystemHardeningTab(ThemedWidgetMixin, QWidget):
    """Main system hardening tab widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_report = None
        self.worker = None
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        
        title = QLabel("System Hardening Assessment")
        title.setObjectName("header")  # Use global header styling
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.refresh_button = QPushButton("Run Assessment")
        self.refresh_button.setMinimumWidth(150)
        self.refresh_button.setObjectName("primaryButton")  # Use global primary button styling
        header_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("secondary")  # Use global secondary styling
        main_layout.addWidget(self.progress_label)
        
        # Create scroll area for content - let global theming handle styling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Top section: Security score (centered)
        score_layout = QHBoxLayout()
        score_layout.addStretch()
        
        # Security score widget
        self.score_widget = SecurityScoreWidget()
        self.score_widget.setMaximumWidth(300)
        score_layout.addWidget(self.score_widget)
        
        score_layout.addStretch()
        content_layout.addLayout(score_layout)
        
        # Middle section: Recommendations and Features table side by side
        middle_layout = QHBoxLayout()
        
        # Left side: Recommendations widget
        self.recommendations_widget = HardeningRecommendationsWidget()
        self.recommendations_widget.setMaximumWidth(400)  # Limit width to prevent excessive space usage
        middle_layout.addWidget(self.recommendations_widget)
        
        # Right side: Features table wrapped in GroupBox
        features_group = QGroupBox("Security Features Status")
        features_layout = QVBoxLayout(features_group)
        
        self.features_table = SecurityFeatureTable()
        features_layout.addWidget(self.features_table)
        
        middle_layout.addWidget(features_group)
        
        content_layout.addLayout(middle_layout)
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Initial state
        self.progress_label.setText("Click 'Run Assessment' to start system hardening evaluation")
    
    def setup_connections(self):
        """Set up signal connections"""
        self.refresh_button.clicked.connect(self.run_assessment)
    
    def run_assessment(self):
        """Start hardening assessment"""
        if self.worker and self.worker.isRunning():
            return
        
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Running...")
        self.progress_label.setText("Starting assessment...")
        
        # Clear previous results
        self.score_widget.update_score(0, 100, "Assessing...", "")
        self.features_table.setRowCount(0)
        self.recommendations_widget.update_recommendations([])
        
        # Start worker
        self.worker = HardeningWorker()
        self.worker.report_ready.connect(self.on_report_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_assessment_finished)
        self.worker.start()
    
    def on_report_ready(self, report: HardeningReport):
        """Handle completed hardening report"""
        self.current_report = report
        
        # Update score widget
        self.score_widget.update_score(
            report.overall_score,
            report.max_score,
            report.compliance_level,
            report.timestamp
        )
        
        # Update features table
        self.features_table.populate_features(report.security_features)
        
        # Update recommendations
        all_recommendations = report.recommendations.copy()
        if hasattr(report, 'critical_issues') and report.critical_issues:
            all_recommendations.insert(0, f"🚨 Critical Issues Found: {len(report.critical_issues)}")
        
        self.recommendations_widget.update_recommendations(all_recommendations)
        
        self.progress_label.setText(f"Assessment complete - {report.compliance_level} security level")
    
    def on_error(self, error_message: str):
        """Handle assessment error"""
        self.progress_label.setText(f"Error: {error_message}")
        QMessageBox.warning(self, "Assessment Error", f"An error occurred during assessment:\n\n{error_message}")
    
    def on_progress_updated(self, message: str):
        """Handle progress updates"""
        self.progress_label.setText(message)
    
    def on_assessment_finished(self):
        """Handle assessment completion"""
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Run Assessment")
        
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

class HardeningDetailsDialog(QDialog):
    """Dialog for showing detailed hardening information"""
    
    def __init__(self, report: HardeningReport, parent=None):
        super().__init__(parent)
        self.report = report
        self.setWindowTitle("Detailed Hardening Report")
        self.setModal(True)
        self.resize(800, 600)
        # Remove custom styling - let global theme handle dialog appearance
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget for different sections - let global theming handle styling
        tab_widget = QTabWidget()
        
        # Summary tab
        summary_widget = self.create_summary_tab()
        tab_widget.addTab(summary_widget, "Summary")
        
        # Features tab
        features_widget = self.create_features_tab()
        tab_widget.addTab(features_widget, "All Features")
        
        # Recommendations tab
        recommendations_widget = self.create_recommendations_tab()
        tab_widget.addTab(recommendations_widget, "Recommendations")
        
        layout.addWidget(tab_widget)
        
        # Button box - let global theming handle styling
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_summary_tab(self) -> QWidget:
        """Create summary tab content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Score summary - let global theming handle text styling
        score_text = QTextEdit()
        score_text.setReadOnly(True)
        score_text.setMaximumHeight(150)
        
        summary_html = f"""
        <h3>Security Assessment Summary</h3>
        <p><strong>Overall Score:</strong> {self.report.overall_score}/{self.report.max_score} 
           ({int((self.report.overall_score/self.report.max_score)*100) if self.report.max_score > 0 else 0}%)</p>
        <p><strong>Compliance Level:</strong> {self.report.compliance_level}</p>
        <p><strong>Assessment Time:</strong> {self.report.timestamp}</p>
        <p><strong>Critical Issues:</strong> {len(self.report.critical_issues)}</p>
        <p><strong>Total Features Assessed:</strong> {len(self.report.security_features)}</p>
        <p><strong>Features Enabled:</strong> {sum(1 for f in self.report.security_features if f.enabled)}</p>
        """
        
        score_text.setHtml(summary_html)
        layout.addWidget(score_text)
        
        return widget
    
    def create_features_tab(self) -> QWidget:
        """Create features tab content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = SecurityFeatureTable()
        table.populate_features(self.report.security_features)
        layout.addWidget(table)
        
        return widget
    
    def create_recommendations_tab(self) -> QWidget:
        """Create recommendations tab content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Let global theming handle text area styling
        recommendations_text = QTextEdit()
        recommendations_text.setReadOnly(True)
        
        # Build comprehensive recommendations with theme-aware colors
        theme = get_theme_manager()
        error_color = theme.get_color('error')
        
        html_content = "<h3>Security Recommendations</h3>"
        
        if self.report.critical_issues:
            html_content += f"<h4 style='color: {error_color};'>Critical Issues</h4><ul>"
            for issue in self.report.critical_issues:
                html_content += f"<li style='color: {error_color};'><strong>{issue}</strong></li>"
            html_content += "</ul>"
        
        if self.report.recommendations:
            html_content += "<h4>General Recommendations</h4><ul>"
            for rec in self.report.recommendations:
                html_content += f"<li>{rec}</li>"
            html_content += "</ul>"
        
        # Add feature-specific recommendations
        disabled_features = [f for f in self.report.security_features if not f.enabled]
        if disabled_features:
            html_content += "<h4>Feature-Specific Recommendations</h4><ul>"
            for feature in disabled_features:
                html_content += f"<li><strong>{feature.name}:</strong> {feature.recommendation}</li>"
            html_content += "</ul>"
        
        recommendations_text.setHtml(html_content)
        layout.addWidget(recommendations_text)
        
        return widget
