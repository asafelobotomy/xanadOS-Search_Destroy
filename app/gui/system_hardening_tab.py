#!/usr/bin/env python3
"""System Hardening GUI Components
xanadOS Search & Destroy - Enhanced Security Interface
This module provides GUI components for displaying system hardening
status, security compliance scores, and hardening recommendations.
"""

import logging
import os
import shutil
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.elevated_runner import elevated_run
from app.core.system_hardening import (
    HardeningReport,
    SecurityFeature,
    SystemHardeningChecker,
)

from .theme_manager import create_themed_message_box, get_theme_manager
from .themed_widgets import ThemedWidgetMixin

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
        self.compliance_label.setObjectName(
            "cardTitle"
        )  # Use global card title styling
        self.compliance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.score_frame)

        # Last updated
        self.updated_label = QLabel("Last Updated: Never")
        self.updated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.updated_label.setObjectName(
            "secondary"
        )  # Use global secondary text styling
        layout.addWidget(self.updated_label)

    def update_score(
        self, score: int, max_score: int, compliance_level: str, timestamp: str
    ):
        """Update the security score display"""
        self.score = score
        self.max_score = max_score

        # Calculate percentage for standardized 0-100 display
        percentage = int((score / max_score) * 100) if max_score > 0 else 0

        # Update labels with standardized 0-100 scale
        self.score_label.setText(f"{percentage}/100")
        self.compliance_label.setText(compliance_level)

        # Update progress bar with animation
        self.progress_bar.setValue(percentage)

        # Use theme colors for compliance level styling
        theme = get_theme_manager()
        if percentage >= 90:
            color = theme.get_color("success")
        elif percentage >= 75:
            color = theme.get_color("strawberry_sage")
        elif percentage >= 50:
            color = theme.get_color("warning")
        else:
            color = theme.get_color("error")

        # Apply theme-aware styling to compliance label
        self.compliance_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Update timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.updated_label.setText(f"Last Updated: {formatted_time}")
        except BaseException:
            self.updated_label.setText(f"Last Updated: {timestamp}")


class SecurityFeatureTable(QTableWidget):
    """Table widget for displaying security features"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()

    def setup_table(self):
        # Set up optimized columns for maximum space efficiency
        headers = [
            "Security Feature",
            "Status",
            "Impact",
            "Description & Recommendation",
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Configure table appearance - let global theming handle most styling
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)

        # Optimal column widths for space efficiency and readability
        header = self.horizontalHeader()
        # Security Feature - flexible
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        # Status - compact fixed width
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        # Impact - compact fixed width
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        # Description & Recommendation - use remaining space
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # Set optimal fixed widths for compact columns (based on content analysis)
        header.resizeSection(1, 90)  # Status: compact for ✅❌⚠️ + text
        header.resizeSection(2, 75)  # Impact: compact for emoji + level text
        header.resizeSection(0, 250)  # Feature: reasonable width for names

        # Enable word wrapping for better text utilization
        self.setWordWrap(True)

        # Set minimum section sizes to prevent over-compression
        header.setMinimumSectionSize(60)

        # Remove custom styling - let global theme handle it

    def populate_features(self, features: list[SecurityFeature]):
        """Populate table with security features using optimized space-efficient presentation"""
        self.setRowCount(len(features))
        theme = get_theme_manager()

        for row, feature in enumerate(features):
            # Security Feature name (simplified and user-friendly)
            name_item = QTableWidgetItem(self._get_friendly_feature_name(feature.name))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, name_item)

            # Status - compact with clear visual indicators
            status_text, status_color, status_bg = self._get_compact_status(feature)
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Apply clear visual styling
            status_item.setForeground(QColor(status_color))
            status_item.setBackground(QColor(status_bg))

            # Make status text bold for better visibility
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)

            self.setItem(row, 1, status_item)

            # Impact - compact display
            impact_text, impact_color = self._get_compact_impact(feature.severity)
            impact_item = QTableWidgetItem(impact_text)
            impact_item.setFlags(impact_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            impact_item.setForeground(QColor(impact_color))

            # Make impact text bold
            font = impact_item.font()
            font.setBold(True)
            impact_item.setFont(font)

            self.setItem(row, 2, impact_item)

            # Combined Description & Recommendation - maximum information density
            combined_text = self._get_combined_description_recommendation(feature)
            combined_item = QTableWidgetItem(combined_text)
            combined_item.setFlags(combined_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Color-code based on urgency for quick scanning
            if not feature.enabled and feature.severity in ["high", "critical"]:
                # High priority items get error coloring
                font = combined_item.font()
                font.setBold(True)
                combined_item.setFont(font)
                combined_item.setForeground(QColor(theme.get_color("error")))
            elif not feature.enabled and feature.severity == "medium":
                combined_item.setForeground(QColor(theme.get_color("warning")))

            self.setItem(row, 3, combined_item)

        # Set optimal row height for density while maintaining readability
        self.verticalHeader().setDefaultSectionSize(45)  # Slightly more compact

        # Enable text wrapping and auto-resize rows to fit content efficiently
        self.resizeRowsToContents()

        # Set maximum row height to prevent excessive expansion
        for row in range(self.rowCount()):
            current_height = self.rowHeight(row)
            if current_height > 80:  # Limit maximum row height
                self.setRowHeight(row, 80)

    def _get_friendly_feature_name(self, technical_name: str) -> str:
        """Convert technical feature names to compact, user-friendly versions"""
        name_mapping = {
            "KASLR (Kernel Address Space Layout Randomization)": "Memory Protection",
            "SMEP/SMAP (Supervisor Mode Execution/Access Prevention)": "Kernel Protection",
            "Kernel Stack Guard Pages": "Stack Protection",
            "KASAN (Kernel Address Sanitizer)": "Memory Sanitizer",
            "Kernel Lockdown Mode": "Kernel Lockdown",
            "AppArmor (Application Armor)": "App Security",
            "Sysctl: kernel.dmesg_restrict": "Log Access Control",
            "Sysctl: kernel.kptr_restrict": "Pointer Protection",
            "Sysctl: kernel.yama.ptrace_scope": "Debug Control",
            "Sysctl: net.ipv4.conf.all.send_redirects": "Redirect Prevention",
            "Sysctl: net.ipv4.conf.all.accept_redirects": "Redirect Blocking",
            "Sysctl: net.ipv4.ip_forward": "IP Forwarding",
            "ASLR (Address Space Layout Randomization)": "Address Randomization",
            "NX Bit / DEP (Data Execution Prevention)": "Code Protection",
        }
        return name_mapping.get(technical_name, technical_name)

    def _get_compact_status(self, feature: SecurityFeature) -> tuple[str, str, str]:
        """Get compact status display with visual indicators"""
        if feature.enabled:
            return "✅ Protected", "#2d5016", "#e8f5e8"  # Green text, light green bg
        # Use severity to determine urgency level
        elif feature.severity in ["critical", "high"]:
            return "❌ Vulnerable", "#721c24", "#f8d7da"  # Red text, light red bg
        else:
            return "⚠️ At Risk", "#8b4513", "#fff3cd"  # Brown text, light yellow bg

    def _get_compact_impact(self, severity: str) -> tuple[str, str]:
        """Get compact impact level display"""
        severity_colors = {
            "critical": ("#721c24", "🔴 Critical"),  # Dark red
            "high": ("#8b4513", "🟠 High"),  # Brown/orange
            "medium": ("#856404", "🟡 Medium"),  # Dark yellow
            "low": ("#155724", "🟢 Low"),  # Dark green
        }

        color, display = severity_colors.get(
            severity.lower(), ("#6c757d", "❓ Unknown")
        )
        return display, color

    def _get_combined_description_recommendation(self, feature: SecurityFeature) -> str:
        """Combine description and recommendation for maximum space efficiency with subtext styling"""
        # Get the explanation
        explanation = self._get_plain_language_explanation(feature)

        # Get the recommendation
        recommendation = self._get_actionable_recommendation(feature)

        # Use dense formatting with visual hierarchy
        if feature.enabled:
            return f"✅ {explanation}"
        else:
            # Use compact formatting with clear action indication
            return f"{explanation}\n\n🔧 {recommendation}"

    def _get_user_friendly_status(self, feature: SecurityFeature) -> tuple:
        """Get user-friendly status with visual indicators"""
        if feature.enabled:
            return "✅ Protected", "#2e7d32", "#e8f5e8"  # Green
        elif feature.severity == "critical":
            return "❌ Vulnerable", "#d32f2f", "#ffebee"  # Red
        elif feature.severity == "high":
            return "⚠️ At Risk", "#f57c00", "#fff3e0"  # Orange
        elif feature.severity == "medium":
            return "⚠️ Needs Attention", "#f9a825", "#fffde7"  # Yellow
        else:
            return "ℹ️ Optional", "#1976d2", "#e3f2fd"  # Blue

    def _get_impact_level_display(self, severity: str) -> tuple:
        """Convert technical severity to user-friendly impact level"""
        impact_mapping = {
            "critical": ("🔴 Critical", "#d32f2f"),
            "high": ("🟠 High", "#f57c00"),
            "medium": ("🟡 Medium", "#f9a825"),
            "low": ("🟢 Low", "#2e7d32"),
        }
        return impact_mapping.get(severity, ("Unknown", "#666666"))

    def _get_plain_language_explanation(self, feature: SecurityFeature) -> str:
        """Provide clear explanation of what the feature status means"""
        explanations = {
            "KASLR (Kernel Address Space Layout Randomization)": "Your system memory layout is randomized, making it much harder for attackers to exploit vulnerabilities.",
            "SMEP/SMAP (Supervisor Mode Execution/Access Prevention)": "Your kernel is protected from executing malicious user code, preventing privilege escalation attacks.",
            "Kernel Stack Guard Pages": "Stack overflow attacks are blocked by guard pages that detect and prevent buffer overruns.",
            "KASAN (Kernel Address Sanitizer)": "Memory corruption detection is available for development environments (not needed in production).",
            "Kernel Lockdown Mode": "Your kernel is protected from unauthorized modifications and debugging access.",
            "AppArmor (Application Armor)": (
                "Application security profiles control what programs can access on your system."
                if feature.enabled
                else "Applications are running without security profiles, allowing broader system access."
            ),
            "Sysctl: kernel.dmesg_restrict": "System diagnostic messages are protected from unauthorized access.",
            "Sysctl: kernel.kptr_restrict": "Kernel memory addresses are hidden from potential attackers.",
            "Sysctl: kernel.yama.ptrace_scope": "Debug access to running processes is restricted to authorized users only.",
            "Sysctl: net.ipv4.conf.all.send_redirects": "Your system won't send network redirects that could be used for attacks.",
            "Sysctl: net.ipv4.conf.all.accept_redirects": "Your system ignores network redirects that could redirect traffic maliciously.",
            "Sysctl: net.ipv4.ip_forward": "IP forwarding is configured appropriately for your system's role.",
            "ASLR (Address Space Layout Randomization)": "Program memory layouts are randomized, making exploitation much more difficult.",
            "NX Bit / DEP (Data Execution Prevention)": "Data areas in memory cannot be executed as code, preventing many types of attacks.",
        }

        base_explanation = explanations.get(feature.name, feature.description)

        if feature.enabled:
            return f"✅ {base_explanation}"
        else:
            return f"⚠️ This protection is not active. {
                base_explanation.replace('Your system', 'Your system would')
            }"

    def _get_actionable_recommendation(self, feature: SecurityFeature) -> str:
        """Provide clear, actionable recommendations"""
        if feature.enabled:
            if "properly configured" in feature.recommendation:
                return (
                    "✅ No action needed - this security feature is working correctly."
                )
            else:
                return f"✅ Active and protecting your system. {feature.recommendation}"

        # For disabled features, provide clear actions
        action_recommendations = {
            "AppArmor (Application Armor)": "🔧 Install and enable AppArmor service to add application security profiles.",
            "KASAN (Kernel Address Sanitizer)": "ℹ️ This is primarily for developers. Production systems typically don't need KASAN.",
            "Kernel Lockdown Mode": "🔧 Consider upgrading to 'confidentiality' mode for maximum security in the kernel configuration.",
        }

        specific_action = action_recommendations.get(feature.name)
        if specific_action:
            return specific_action

        # Generic recommendations based on severity
        if feature.severity == "critical":
            return f"🚨 HIGH PRIORITY: {feature.recommendation}"
        elif feature.severity == "high":
            return f"⚠️ RECOMMENDED: {feature.recommendation}"
        elif feature.severity == "medium":
            return f"💡 SUGGESTED: {feature.recommendation}"
        else:
            return f"ℹ️ OPTIONAL: {feature.recommendation}"


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

    def update_recommendations(self, recommendations: list[str]):
        """Update the recommendations display"""
        if not recommendations:
            self.recommendations_text.setHtml(
                "<i>No specific recommendations at this time.</i>"
            )
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

        # Button container for proper spacing
        button_layout = QHBoxLayout()
        button_layout.setSpacing(
            15
        )  # Increased spacing between buttons to prevent overlap
        button_layout.setContentsMargins(0, 0, 10, 0)  # Add right margin for safety

        self.refresh_button = QPushButton("Run Assessment")
        self.refresh_button.setFixedWidth(150)  # Fixed width prevents overlap
        self.refresh_button.setFixedHeight(32)  # Set consistent button height
        self.refresh_button.setObjectName(
            "primaryButton"
        )  # Use global primary button styling
        button_layout.addWidget(self.refresh_button)

        # Add Fix Issues button
        self.fix_button = QPushButton("Fix Issues")
        self.fix_button.setFixedWidth(120)  # Fixed width prevents overlap
        self.fix_button.setFixedHeight(32)  # Set consistent button height
        self.fix_button.setObjectName(
            "warningButton"
        )  # Use warning styling for fix actions
        self.fix_button.setEnabled(False)  # Disabled until assessment is run
        button_layout.addWidget(self.fix_button)

        header_layout.addLayout(button_layout)

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
        # Limit width to prevent excessive space usage
        self.recommendations_widget.setMaximumWidth(400)
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
        self.progress_label.setText(
            "Click 'Run Assessment' to start system hardening evaluation"
        )

    def setup_connections(self):
        """Set up signal connections"""
        self.refresh_button.clicked.connect(self.run_assessment)
        self.fix_button.clicked.connect(self.fix_issues)

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
            report.timestamp,
        )

        # Update features table
        self.features_table.populate_features(report.security_features)

        # Update recommendations
        all_recommendations = report.recommendations.copy()
        if hasattr(report, "critical_issues") and report.critical_issues:
            all_recommendations.insert(
                0, f"🚨 Critical Issues Found: {len(report.critical_issues)}"
            )

        self.recommendations_widget.update_recommendations(all_recommendations)

        # Enable fix button if there are fixable issues
        fixable_issues = self._get_fixable_issues(report)
        self.fix_button.setEnabled(len(fixable_issues) > 0)
        if len(fixable_issues) > 0:
            self.fix_button.setText(f"Fix {len(fixable_issues)} Issues")
        else:
            self.fix_button.setText("No Fixes Available")

        self.progress_label.setText(
            f"Assessment complete - {report.compliance_level} security level"
        )

    def on_error(self, error_message: str):
        """Handle assessment error"""
        self.progress_label.setText(f"Error: {error_message}")
        QMessageBox.warning(
            self,
            "Assessment Error",
            f"An error occurred during assessment:\n\n{error_message}",
        )

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

    def _get_fixable_issues(self, report: HardeningReport) -> list[SecurityFeature]:
        """Get list of security features that can be automatically fixed"""
        fixable_issues = []

        # Detect distribution for platform-specific fixes
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "id=arch" in content:
                    pass
        except BaseException:
            pass

        for feature in report.security_features:
            if not feature.enabled:
                # Check if this is a fixable issue
                feature_name = feature.name.lower()

                # Always fixable: sysctl parameters, lockdown, apparmor
                if any(
                    fixable in feature_name
                    for fixable in [
                        "sysctl",
                        "kernel.kptr_restrict",
                        "kernel.dmesg_restrict",
                        "kernel.yama.ptrace_scope",
                        "net.ipv4",
                        "lockdown",
                        "apparmor",
                    ]
                ):
                    fixable_issues.append(feature)

        return fixable_issues

    def fix_issues(self):
        """Apply automatic fixes for detected security issues"""
        if not hasattr(self, "current_report") or not self.current_report:
            msg_box = create_themed_message_box(
                self, "warning", "No Assessment", "Please run an assessment first."
            )
            msg_box.exec()
            return

        fixable_issues = self._get_fixable_issues(self.current_report)
        if not fixable_issues:
            msg_box = create_themed_message_box(
                self,
                "information",
                "No Fixes Available",
                "No automatically fixable issues were found.",
            )
            msg_box.exec()
            return

        # Show fix selection dialog
        fix_dialog = FixSelectionDialog(fixable_issues, self)

        if fix_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_fixes = fix_dialog.get_selected_fixes()

            if not selected_fixes:
                msg_box = create_themed_message_box(
                    self,
                    "information",
                    "No Fixes Selected",
                    "No fixes were selected to apply.",
                )
                msg_box.exec()
                return

            # Show final confirmation with selected fixes
            fix_count = len(selected_fixes)
            fix_names = [self._get_clean_fix_name(fix) for fix in selected_fixes]
            fix_list = "\n".join([f"• {name}" for name in fix_names])

            confirmation_msg = f"""You have selected {fix_count} security fix{
                "es" if fix_count != 1 else ""
            } to apply:

{fix_list}

These changes will:
• Require administrator privileges
• Be applied immediately
• Persist after reboot

Do you want to proceed?"""

            confirm_box = create_themed_message_box(
                self,
                "question",
                f"Apply {fix_count} Fix{'es' if fix_count != 1 else ''}?",
                confirmation_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            confirm_box.setDefaultButton(QMessageBox.StandardButton.No)

            if confirm_box.exec() == QMessageBox.StandardButton.Yes:
                # Apply selected fixes
                self._apply_security_fixes(selected_fixes)

    def _get_clean_fix_name(self, issue: SecurityFeature) -> str:
        """Get a clean display name for confirmation"""
        name = issue.name
        if "sysctl:" in name.lower():
            name = name.replace("Sysctl: ", "")
        elif "Kernel Lockdown Mode" in name:
            name = "Kernel Lockdown"
        return name

    def _apply_security_fixes(self, fixable_issues: list[SecurityFeature]):
        """Apply security fixes using elevated privileges"""
        self.fix_button.setEnabled(False)
        self.fix_button.setText("Applying Fixes...")
        self.progress_label.setText("Applying security fixes...")

        success_count = 0
        failed_fixes = []

        for issue in fixable_issues:
            try:
                if self._apply_single_fix(issue):
                    success_count += 1
                else:
                    failed_fixes.append(issue.name)
            except Exception as e:
                logger.error(f"Failed to apply fix for {issue.name}: {e}")
                failed_fixes.append(f"{issue.name} ({e!s})")

        # Show results with themed dialogs
        if success_count > 0:
            result_message = f"Successfully applied {success_count} security fixes."
            if failed_fixes:
                result_message += (
                    f"\\n\\nFailed to apply {len(failed_fixes)} fixes:\\n"
                    + "\\n".join(failed_fixes)
                )
                msg_box = create_themed_message_box(
                    self, "warning", "Fixes Partially Applied", result_message
                )
                msg_box.exec()
            else:
                msg_box = create_themed_message_box(
                    self, "information", "Fixes Applied", result_message
                )
                msg_box.exec()
        else:
            result_message = "Failed to apply any fixes:\\n" + "\\n".join(failed_fixes)
            msg_box = create_themed_message_box(
                self, "critical", "Fixes Failed", result_message
            )
            msg_box.exec()

        # Reset button state
        self.fix_button.setText("Fix Issues")
        self.fix_button.setEnabled(
            len(self._get_fixable_issues(self.current_report)) > 0
        )
        self.progress_label.setText(
            "Fixes completed. Run assessment again to verify changes."
        )

    def _apply_single_fix(self, issue: SecurityFeature) -> bool:
        """Apply a single security fix"""
        try:
            # Sysctl parameter fixes
            if "sysctl:" in issue.name.lower():
                return self._fix_sysctl_parameter(issue)

            # Kernel lockdown fix
            elif "lockdown" in issue.name.lower():
                return self._fix_kernel_lockdown(issue)

            # AppArmor fix
            elif "apparmor" in issue.name.lower():
                return self._fix_apparmor(issue)

            # Other fixes can be added here
            else:
                logger.warning(f"No fix implementation for: {issue.name}")
                return False

        except Exception as e:
            logger.error(f"Error applying fix for {issue.name}: {e}")
            return False

    def _fix_sysctl_parameter(self, issue: SecurityFeature) -> bool:
        """Fix sysctl parameter issues with enhanced security validation"""
        try:
            # Extract parameter name and expected value from recommendation
            recommendation = issue.recommendation
            if "Set " in recommendation and " = " in recommendation:
                # Extract "kernel.kptr_restrict = 2" from "Set kernel.kptr_restrict = 2"
                param_setting = recommendation.replace("Set ", "").strip()
                if " = " not in param_setting:
                    logger.error(f"Invalid parameter setting format: {param_setting}")
                    return False

                param_name, expected_value = param_setting.split(" = ", 1)

                # Validate parameter name against known safe parameters
                safe_params = {
                    "kernel.kptr_restrict": ["0", "1", "2"],
                    "kernel.dmesg_restrict": ["0", "1"],
                    "kernel.yama.ptrace_scope": ["0", "1", "2", "3"],
                    "net.ipv4.conf.all.send_redirects": ["0", "1"],
                    "net.ipv4.conf.all.accept_redirects": ["0", "1"],
                    "net.ipv4.ip_forward": ["0", "1"],
                }

                if param_name not in safe_params:
                    logger.error(f"Parameter {param_name} not in safe parameters list")
                    return False

                if expected_value not in safe_params[param_name]:
                    logger.error(
                        f"Invalid value {expected_value} for parameter {param_name}"
                    )
                    return False

                # Apply sysctl setting with validation
                sysctl_cmd = ["sysctl", "-w", f"{param_name}={expected_value}"]
                result = elevated_run(sysctl_cmd, gui=True)

                if result.returncode == 0:
                    # Make it persistent by adding to sysctl.conf
                    sysctl_line = f"# xanadOS Search & Destroy hardening\n{param_name} = {expected_value}"

                    # Check if config directory exists, create if needed
                    config_dir_result = elevated_run(
                        ["mkdir", "-p", "/etc/sysctl.d"], gui=True
                    )
                    if config_dir_result.returncode != 0:
                        logger.error("Failed to create sysctl.d directory")
                        return False

                    # Use a more secure method to write the config
                    config_file = "/etc/sysctl.d/99-xanados-hardening.conf"

                    # Check if parameter already exists in config
                    check_result = elevated_run(
                        ["grep", "-q", f"^{param_name}", config_file], gui=True
                    )

                    if check_result.returncode == 0:
                        # Parameter exists, update it
                        sed_cmd = [
                            "sed",
                            "-i",
                            f"s|^{param_name}.*|{param_name} = {expected_value}|",
                            config_file,
                        ]
                        echo_result = elevated_run(sed_cmd, gui=True)
                    else:
                        # Parameter doesn't exist, append it
                        echo_result = elevated_run(
                            ["sh", "-c", f"echo '{sysctl_line}' >> {config_file}"],
                            gui=True,
                        )

                    return echo_result.returncode == 0

                return False

            logger.error(f"Unable to parse recommendation: {recommendation}")
            return False

        except Exception as e:
            logger.error(f"Error fixing sysctl parameter {issue.name}: {e}")
            return False

    def _fix_kernel_lockdown(self, issue: SecurityFeature) -> bool:
        """Fix kernel lockdown mode with enhanced implementation"""
        try:
            # Check current lockdown status
            current_status = "none"
            lockdown_files = [
                "/sys/kernel/security/lockdown",
                "/proc/sys/kernel/lockdown",
            ]

            for lockdown_file in lockdown_files:
                try:
                    with open(lockdown_file) as f:
                        content = f.read().strip()
                        if "[integrity]" in content:
                            current_status = "integrity"
                        elif "[confidentiality]" in content:
                            current_status = "confidentiality"
                        break
                except BaseException:
                    continue

            # Offer automatic GRUB configuration for supported systems
            grub_config_msg = f"""Kernel Lockdown Mode Configuration

Current Status: {current_status}

Kernel lockdown mode enhances security by restricting kernel debugging interfaces and preventing unauthorized kernel modifications.

Choose your lockdown level:

• integrity: Basic protection (recommended for most users)
  - Restricts kernel memory access
  - Allows most functionality to work normally

• confidentiality: Maximum protection (for high-security environments)
  - Strongest protection available
  - May break some debugging tools

Would you like to automatically configure GRUB to enable kernel lockdown?"""

            from ..utils.theme import create_themed_message_box

            choice_box = create_themed_message_box(
                self,
                "question",
                "Kernel Lockdown Configuration",
                grub_config_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if choice_box.exec() == QMessageBox.StandardButton.Yes:
                # Ask for lockdown level
                level_msg = """Choose Lockdown Level:

Click 'Yes' for integrity mode (recommended)
Click 'No' for confidentiality mode (maximum security)"""

                level_box = create_themed_message_box(
                    self,
                    "question",
                    "Choose Lockdown Level",
                    level_msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                level_box.button(QMessageBox.StandardButton.Yes).setText("Integrity")
                level_box.button(QMessageBox.StandardButton.No).setText(
                    "Confidentiality"
                )

                lockdown_mode = (
                    "integrity"
                    if level_box.exec() == QMessageBox.StandardButton.Yes
                    else "confidentiality"
                )

                return self._configure_grub_lockdown(lockdown_mode)
            else:
                # Provide manual instructions
                manual_msg = f"""Manual Kernel Lockdown Configuration

To enable kernel lockdown mode manually:

1. Edit /etc/default/grub as root
2. Find the line starting with GRUB_CMDLINE_LINUX=
3. Add lockdown=integrity or lockdown=confidentiality to the parameters
4. Run: sudo update-grub (Debian/Ubuntu) or sudo grub-mkconfig -o /boot/grub/grub.cfg
5. Reboot the system

Example:
GRUB_CMDLINE_LINUX="quiet splash lockdown=integrity"

Current status: {current_status}"""

                manual_box = create_themed_message_box(
                    self, "information", "Manual Configuration", manual_msg
                )
                manual_box.exec()
                return False  # Manual intervention required

        except Exception as e:
            logger.error(f"Error configuring kernel lockdown: {e}")
            return False

    def _configure_grub_lockdown(self, lockdown_mode: str) -> bool:
        """Automatically configure GRUB for kernel lockdown"""
        try:
            grub_file = "/etc/default/grub"
            backup_file = f"{grub_file}.backup.xanados"

            # Create backup
            backup_result = elevated_run(["cp", grub_file, backup_file], gui=True)
            if backup_result.returncode != 0:
                logger.error("Failed to create GRUB backup")
                return False

            # Check if lockdown parameter already exists
            check_result = elevated_run(
                ["grep", "-q", "lockdown=", grub_file], gui=True
            )

            if check_result.returncode == 0:
                # Update existing lockdown parameter
                sed_cmd = [
                    "sed",
                    "-i",
                    f"s/lockdown=[a-z]*/lockdown={lockdown_mode}/g",
                    grub_file,
                ]
                update_result = elevated_run(sed_cmd, gui=True)
            else:
                # Add lockdown parameter to GRUB_CMDLINE_LINUX
                sed_cmd = [
                    "sed",
                    "-i",
                    f'/^GRUB_CMDLINE_LINUX=/s/"$/ lockdown={lockdown_mode}"/',
                    grub_file,
                ]
                update_result = elevated_run(sed_cmd, gui=True)

            if update_result.returncode != 0:
                logger.error("Failed to update GRUB configuration")
                return False

            # Update GRUB
            update_grub_cmds = [
                ["update-grub"],  # Debian/Ubuntu
                ["grub-mkconfig", "-o", "/boot/grub/grub.cfg"],  # Arch/others
                ["grub2-mkconfig", "-o", "/boot/grub2/grub.cfg"],  # RHEL/Fedora
            ]

            grub_updated = False
            for cmd in update_grub_cmds:
                result = elevated_run(cmd, gui=True)
                if result.returncode == 0:
                    grub_updated = True
                    break

            if grub_updated:
                success_msg = f"""✅ Kernel Lockdown Configured Successfully

Lockdown mode '{lockdown_mode}' has been added to your GRUB configuration.

⚠️ REBOOT REQUIRED: You must reboot for the changes to take effect.

The system will boot with enhanced kernel security protection."""

                from ..utils.theme import create_themed_message_box

                success_box = create_themed_message_box(
                    self, "information", "Configuration Complete", success_msg
                )
                success_box.exec()
                return True
            else:
                logger.error("Failed to update GRUB bootloader")
                return False

        except Exception as e:
            logger.error(f"Error configuring GRUB lockdown: {e}")
            return False
        return False  # Manual intervention required

    def _install_fail2ban_redhat(self) -> bool:
        """Install fail2ban on Red Hat/Fedora systems"""
        try:
            # Use dnf/yum based on availability
            if shutil.which("dnf"):
                cmd = ["dnf", "install", "-y", "fail2ban"]
            else:
                cmd = ["yum", "install", "-y", "fail2ban"]

            result = elevated_run(cmd, gui=True)
            if result.returncode != 0:
                return False

            return self._start_and_enable_fail2ban()
        except Exception as e:
            logger.error(f"Error installing fail2ban on Red Hat/Fedora: {e}")
            return False

    def _install_fail2ban_suse(self) -> bool:
        """Install fail2ban on openSUSE systems"""
        try:
            cmd = ["zypper", "install", "-y", "fail2ban"]
            result = elevated_run(cmd, gui=True)
            if result.returncode != 0:
                return False

            return self._start_and_enable_fail2ban()
        except Exception as e:
            logger.error(f"Error installing fail2ban on openSUSE: {e}")
            return False

    def _install_fail2ban_arch(self) -> bool:
        """Install fail2ban on Arch Linux"""
        try:
            cmd = ["pacman", "-S", "--noconfirm", "fail2ban"]
            result = elevated_run(cmd, gui=True)
            if result.returncode != 0:
                return False

            return self._start_and_enable_fail2ban()
        except Exception as e:
            logger.error(f"Error installing fail2ban on Arch: {e}")
            return False

    def _start_and_enable_fail2ban(self) -> bool:
        """Start and enable fail2ban service"""
        try:
            # Start the service
            start_cmd = ["systemctl", "start", "fail2ban"]
            result = elevated_run(start_cmd, gui=True)
            if result.returncode != 0:
                logger.error("Failed to start fail2ban service")
                return False

            # Enable the service
            enable_cmd = ["systemctl", "enable", "fail2ban"]
            result = elevated_run(enable_cmd, gui=True)
            if result.returncode != 0:
                logger.error("Failed to enable fail2ban service")
                return False

            return True
        except Exception as e:
            logger.error(f"Error starting/enabling fail2ban: {e}")
            return False

    def _fix_apparmor(self, issue: SecurityFeature) -> bool:
        """Fix AppArmor service configuration with enhanced profile management"""
        try:
            # First, check if AppArmor is installed
            check_result = elevated_run(["which", "apparmor_status"], gui=True)

            if check_result.returncode != 0:
                # AppArmor not installed, try to install it
                return self._install_apparmor()

            # AppArmor is installed, configure it
            return self._configure_apparmor()

        except Exception as e:
            logger.error(f"Error configuring AppArmor: {e}")
            return False

    def _install_apparmor(self) -> bool:
        """Install AppArmor with distribution-specific handling"""
        try:
            distro_info = self._get_distribution_info()

            install_success = False

            if "ubuntu" in distro_info or "debian" in distro_info:
                # Update package list first
                update_result = elevated_run(["apt", "update"], gui=True)
                if update_result.returncode != 0:
                    logger.warning("Failed to update package list")

                # Install AppArmor packages
                packages = ["apparmor", "apparmor-utils", "apparmor-profiles"]
                install_result = elevated_run(
                    ["apt", "install", "-y"] + packages, gui=True
                )
                install_success = install_result.returncode == 0

            elif (
                "fedora" in distro_info
                or "rhel" in distro_info
                or "centos" in distro_info
            ):
                # Install AppArmor packages for Red Hat family
                packages = ["apparmor", "apparmor-utils"]
                install_result = elevated_run(
                    ["dnf", "install", "-y"] + packages, gui=True
                )
                install_success = install_result.returncode == 0

            elif "arch" in distro_info:
                # AppArmor installation on Arch
                install_result = elevated_run(
                    ["pacman", "-S", "--noconfirm", "apparmor"], gui=True
                )
                install_success = install_result.returncode == 0

            elif "opensuse" in distro_info or "suse" in distro_info:
                # AppArmor on openSUSE
                install_result = elevated_run(
                    ["zypper", "install", "-y", "apparmor-utils"], gui=True
                )
                install_success = install_result.returncode == 0

            else:
                # Unknown distribution
                guidance_msg = """AppArmor Installation Required

AppArmor installation varies by distribution. Please install manually:

• Ubuntu/Debian: sudo apt install apparmor apparmor-utils apparmor-profiles
• Fedora/RHEL: sudo dnf install apparmor apparmor-utils
• Arch Linux: sudo pacman -S apparmor
• openSUSE: sudo zypper install apparmor-utils

After installation, enable AppArmor and reboot, then run this assessment again."""

                from ..utils.theme import create_themed_message_box

                msg_box = create_themed_message_box(
                    self, "information", "Manual Installation Required", guidance_msg
                )
                msg_box.exec()
                return False

            if install_success:
                return self._configure_apparmor()
            else:
                logger.error("Failed to install AppArmor packages")
                return False

        except Exception as e:
            logger.error(f"Error installing AppArmor: {e}")
            return False

    def _configure_apparmor(self) -> bool:
        """Configure AppArmor service and load basic profiles"""
        try:
            # Enable AppArmor service
            enable_result = elevated_run(["systemctl", "enable", "apparmor"], gui=True)
            if enable_result.returncode != 0:
                logger.error("Failed to enable AppArmor service")
                return False

            # Start AppArmor service
            start_result = elevated_run(["systemctl", "start", "apparmor"], gui=True)
            if start_result.returncode != 0:
                logger.warning("Failed to start AppArmor service (may need reboot)")

            # Load basic profiles if available
            self._load_apparmor_profiles()

            # Check if AppArmor kernel support is available
            if not self._check_apparmor_kernel_support():
                kernel_msg = """⚠️ AppArmor Kernel Support

AppArmor has been installed but your kernel may not have AppArmor support enabled.

You may need to:
1. Add 'apparmor=1 security=apparmor' to kernel boot parameters
2. Reboot the system
3. Run this assessment again to verify

AppArmor service has been enabled and will start after reboot if kernel support is available."""

                from ..utils.theme import create_themed_message_box

                warn_box = create_themed_message_box(
                    self, "warning", "Kernel Support Check", kernel_msg
                )
                warn_box.exec()

            success_msg = """✅ AppArmor Configuration Complete

AppArmor has been successfully installed and configured:

• Service enabled for automatic startup
• Basic security profiles loaded
• Ready to enforce application security policies

Some applications may require reboot to fully activate AppArmor protection."""

            from ..utils.theme import create_themed_message_box

            success_box = create_themed_message_box(
                self, "information", "AppArmor Configured", success_msg
            )
            success_box.exec()

            return True

        except Exception as e:
            logger.error(f"Error configuring AppArmor: {e}")
            return False

    def _load_apparmor_profiles(self):
        """Load available AppArmor profiles"""
        try:
            # Common profile locations
            profile_dirs = ["/etc/apparmor.d", "/usr/share/apparmor/extra-profiles"]

            for profile_dir in profile_dirs:
                if os.path.exists(profile_dir):
                    # Load profiles from directory
                    load_result = elevated_run(
                        ["aa-enforce", f"{profile_dir}/*"], gui=True
                    )
                    if load_result.returncode == 0:
                        logger.info(f"Loaded AppArmor profiles from {profile_dir}")

        except Exception as e:
            logger.debug(f"Error loading AppArmor profiles: {e}")

    def _check_apparmor_kernel_support(self) -> bool:
        """Check if kernel has AppArmor support"""
        try:
            # Check for AppArmor filesystem
            if os.path.exists("/sys/kernel/security/apparmor"):
                return True

            # Check kernel boot parameters
            with open("/proc/cmdline") as f:
                cmdline = f.read()
                if "apparmor=1" in cmdline or "security=apparmor" in cmdline:
                    return True

            # Check if kernel was compiled with AppArmor
            if os.path.exists("/proc/config.gz"):
                result = elevated_run(["zcat", "/proc/config.gz"], gui=True)
                if "CONFIG_SECURITY_APPARMOR=y" in result.stdout:
                    return True

            return False

        except Exception as e:
            logger.debug(f"Error checking AppArmor kernel support: {e}")
            return False

    def _get_distribution_info(self) -> str:
        """Get distribution information for package management"""
        try:
            distro_info = []
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID=") or line.startswith("ID_LIKE="):
                        distro_info.append(line.strip().lower())
            return " ".join(distro_info)
        except BaseException:
            return ""


class FixSelectionDialog(ThemedWidgetMixin, QDialog):
    """Dialog for selecting which security fixes to apply"""

    def __init__(self, fixable_issues: list[SecurityFeature], parent=None):
        super().__init__(parent)
        self.fixable_issues = fixable_issues
        self.selected_fixes = []
        self.checkboxes = []

        self.setWindowTitle("Select Security Fixes")
        self.setModal(True)
        self.resize(600, 500)
        self._apply_theme()
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title and description
        title_label = QLabel("Select Security Fixes to Apply")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; padding: 10px 0;"
        )
        layout.addWidget(title_label)

        description_label = QLabel(
            "Choose which security fixes you want to apply. "
            "Each fix will require administrator privileges and will be applied immediately."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description_label)

        # Scroll area for fixes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        # Create checkbox for each fixable issue
        for i, issue in enumerate(self.fixable_issues):
            fix_frame = QFrame()
            fix_frame.setFrameStyle(QFrame.Shape.Box)
            fix_frame.setStyleSheet(
                """
                QFrame {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 10px;
                    background-color: rgba(0, 0, 0, 0.02);
                }
                QFrame:hover {
                    background-color: rgba(0, 120, 204, 0.05);
                    border-color: #007acc;
                }
            """
            )

            fix_layout = QVBoxLayout(fix_frame)
            fix_layout.setSpacing(8)

            # Checkbox with issue name
            checkbox = QCheckBox(self._get_clean_name(issue))
            checkbox.setChecked(True)  # Default to checked
            checkbox.setStyleSheet("font-weight: bold; font-size: 13px;")
            self.checkboxes.append(checkbox)
            fix_layout.addWidget(checkbox)

            # Issue description
            desc_label = QLabel(issue.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #555; margin-left: 20px; font-size: 11px;")
            fix_layout.addWidget(desc_label)

            # Severity indicator
            severity_label = QLabel(f"Severity: {issue.severity.upper()}")
            severity_color = {
                "low": "#28a745",
                "medium": "#ffc107",
                "high": "#fd7e14",
                "critical": "#dc3545",
            }.get(issue.severity, "#6c757d")

            severity_label.setStyleSheet(
                f"""
                color: {severity_color};
                font-weight: bold;
                margin-left: 20px;
                font-size: 10px;
            """
            )
            fix_layout.addWidget(severity_label)

            scroll_layout.addWidget(fix_frame)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Select All / Deselect All buttons
        selection_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        selection_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        selection_layout.addWidget(deselect_all_btn)

        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Update OK button text based on selection
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.update_ok_button()

        # Connect checkboxes to update OK button
        for checkbox in self.checkboxes:
            checkbox.stateChanged.connect(self.update_ok_button)

        layout.addWidget(button_box)

    def _get_clean_name(self, issue: SecurityFeature) -> str:
        """Get a clean display name for the issue"""
        name = issue.name
        if "sysctl:" in name.lower():
            name = name.replace("Sysctl: ", "")
        elif "Kernel Lockdown Mode" in name:
            name = "Kernel Lockdown"
        return name

    def select_all(self):
        """Select all checkboxes"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all(self):
        """Deselect all checkboxes"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def update_ok_button(self):
        """Update OK button text based on selection count"""
        selected_count = sum(1 for checkbox in self.checkboxes if checkbox.isChecked())
        if selected_count == 0:
            self.ok_button.setText("Apply 0 Fixes")
            self.ok_button.setEnabled(False)
        else:
            self.ok_button.setText(
                f"Apply {selected_count} Fix{'es' if selected_count != 1 else ''}"
            )
            self.ok_button.setEnabled(True)

    def get_selected_fixes(self) -> list[SecurityFeature]:
        """Get the list of selected fixes"""
        selected = []
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                selected.append(self.fixable_issues[i])
        return selected


class HardeningDetailsDialog(ThemedWidgetMixin, QDialog):
    """Dialog for showing detailed hardening information"""

    def __init__(self, report: HardeningReport, parent=None):
        super().__init__(parent)
        self.report = report
        self.setWindowTitle("Detailed Hardening Report")
        self.setModal(True)
        self.resize(800, 600)
        # Apply themed styling
        self.apply_theme()
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
           ({int((self.report.overall_score / self.report.max_score) * 100) if self.report.max_score > 0 else 0}%)</p>
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
        error_color = theme.get_color("error")

        html_content = "<h3>Security Recommendations</h3>"

        if self.report.critical_issues:
            html_content += (
                f"<h4 style='color: {error_color};'>Critical Issues</h4><ul>"
            )
            for issue in self.report.critical_issues:
                html_content += (
                    f"<li style='color: {error_color};'><strong>{issue}</strong></li>"
                )
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
