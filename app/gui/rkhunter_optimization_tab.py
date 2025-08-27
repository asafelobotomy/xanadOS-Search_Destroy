#!/usr/bin/env python3
"""
RKHunter Optimization GUI Components
xanadOS Search & Destroy - Enhanced RKHunter Management Interface
This module provides GUI components for RKHunter optimization including:
- Configuration optimization interface
- Status monitoring and reporting
- Performance metrics dashboard
- Automated baseline management
- Mirror and update optimization
"""

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QFormLayout, QFrame, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMessageBox, QPushButton,
                             QScrollArea, QSpinBox, QSplitter, QTabWidget,
                             QTextEdit, QVBoxLayout, QWidget)

try:
    from app.core.rkhunter_optimizer import (OptimizationReport,
                                             RKHunterConfig, RKHunterOptimizer,
                                             RKHunterStatus)
except ImportError:
    # Fallbacks if optimizer module not fully available
    OptimizationReport = None  # type: ignore[assignment]
    RKHunterConfig = None  # type: ignore[assignment]
    RKHunterStatus = None  # type: ignore[assignment]
    from app.core.rkhunter_optimizer import RKHunterOptimizer

logger = logging.getLogger(__name__)


class StatusOnlyWorker(QThread):
    """Lightweight worker for status-only checks without sudo requirements"""

    status_updated = pyqtSignal(object)  # RKHunterStatus
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.optimizer = RKHunterOptimizer()

    def run(self):
        """Run lightweight RKHunter status check"""
        try:
            status = self.optimizer.get_current_status()
            self.status_updated.emit(status)
        except Exception as e:
            logger.error(f"Error in status check: {e}")
            self.error_occurred.emit(str(e))


class RKHunterOptimizationWorker(QThread):
    """Background worker for RKHunter optimization"""

    optimization_complete = pyqtSignal(object)  # OptimizationReport
    status_updated = pyqtSignal(object)  # RKHunterStatus
    progress_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, config: RKHunterConfig):
        super().__init__()
        self.config = config
        self.optimizer = RKHunterOptimizer()

    def run(self):
        """Run RKHunter optimization in background"""
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
        self.status_history = []  # Keep history of status checks
        self.max_history = 10  # Keep last 10 status checks
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("RKHunter Status")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
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

        # Performance metrics
        perf_group = QGroupBox("Performance Metrics")
        perf_layout = QVBoxLayout(perf_group)

        self.metrics_text = QTextEdit()
        self.metrics_text.setMaximumHeight(120)
        self.metrics_text.setReadOnly(True)
        perf_layout.addWidget(self.metrics_text)

        layout.addWidget(perf_group)

        # Issues section
        issues_group = QGroupBox("Configuration Issues")
        issues_layout = QVBoxLayout(issues_group)

        self.issues_list = QListWidget()
        self.issues_list.setMaximumHeight(100)
        issues_layout.addWidget(self.issues_list)

        layout.addWidget(issues_group)

    def update_status(self, status: RKHunterStatus):
        """Update the status display and maintain history"""
        self.current_status = status

        # Add to history with timestamp

        history_entry = {"timestamp": datetime.now(), "status": status}
        self.status_history.append(history_entry)

        # Maintain max history size
        if len(self.status_history) > self.max_history:
            self.status_history.pop(0)

        # Update labels
        self.version_label.setText(status.version)
        self.db_version_label.setText(status.database_version)

        # Format timestamps
        if status.last_update:
            update_text = status.last_update.strftime("%Y-%m-%d %H:%M")
            age = datetime.now() - status.last_update
            if age.days > 7:
                update_text += f" ({age.days} days ago)"
                self.last_update_label.setStyleSheet("color: orange;")
            else:
                self.last_update_label.setStyleSheet("color: green;")
        else:
            update_text = "Never"
            self.last_update_label.setStyleSheet("color: red;")
        self.last_update_label.setText(update_text)

        if status.last_scan:
            scan_text = status.last_scan.strftime("%Y-%m-%d %H:%M")
            age = datetime.now() - status.last_scan
            if age.days > 1:
                scan_text += f" ({age.days} days ago)"
        else:
            scan_text = "Never"
        self.last_scan_label.setText(scan_text)

        # Baseline status
        baseline_text = "✅ Exists" if status.baseline_exists else "❌ Missing"
        baseline_color = "green" if status.baseline_exists else "red"
        self.baseline_label.setText(baseline_text)
        self.baseline_label.setStyleSheet(f"color: {baseline_color};")

        # Mirror status
        mirror_color = "green" if status.mirror_status == "OK" else "orange"
        self.mirror_label.setText(status.mirror_status)
        self.mirror_label.setStyleSheet(f"color: {mirror_color};")

        # Performance metrics
        metrics_text = ""
        for key, value in status.performance_metrics.items():
            if key == "avg_scan_time" and value:
                metrics_text += f"Average Scan Time: {value:.1f} seconds\n"
            elif key == "database_size_mb" and value:
                metrics_text += f"Database Size: {value} MB\n"
            elif key == "last_update_duration" and value:
                metrics_text += f"Last Update Duration: {value:.1f} seconds\n"

        if not metrics_text:
            metrics_text = "No performance data available"

        self.metrics_text.setPlainText(metrics_text)

        # Issues
        self.issues_list.clear()
        if status.issues_found:
            for issue in status.issues_found:
                item = QListWidgetItem(f"⚠️ {issue}")
                item.setForeground(QColor("red"))
                self.issues_list.addItem(item)
        else:
            item = QListWidgetItem("✅ No issues detected")
            item.setForeground(QColor("green"))
            self.issues_list.addItem(item)

    def get_status_history(self):
        """Get the status check history"""
        return self.status_history.copy()

    def clear_history(self):
        """Clear the status history"""
        self.status_history.clear()


class RKHunterConfigWidget(QWidget):
    """Widget for configuring RKHunter optimization settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("RKHunter Optimization Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Configuration form
        QFormLayout()

        # Mirror settings
        mirror_group = QGroupBox("Mirror Settings")
        mirror_layout = QFormLayout(mirror_group)

        self.update_mirrors_cb = QCheckBox("Enable automatic mirror updates")
        self.update_mirrors_cb.setChecked(True)
        mirror_layout.addRow(self.update_mirrors_cb)

        self.mirrors_mode_combo = QComboBox()
        self.mirrors_mode_combo.addItems(["Round Robin", "Random"])
        mirror_layout.addRow("Mirror Selection Mode:", self.mirrors_mode_combo)

        self.network_timeout_spin = QSpinBox()
        self.network_timeout_spin.setRange(60, 1800)
        self.network_timeout_spin.setValue(300)
        self.network_timeout_spin.setSuffix(" seconds")
        mirror_layout.addRow("Network Timeout:", self.network_timeout_spin)

        layout.addWidget(mirror_group)

        # Update settings
        update_group = QGroupBox("Update Settings")
        update_layout = QFormLayout(update_group)

        self.auto_update_cb = QCheckBox("Enable automatic database updates")
        self.auto_update_cb.setChecked(True)
        update_layout.addRow(self.auto_update_cb)

        self.check_frequency_combo = QComboBox()
        self.check_frequency_combo.addItems(["Daily", "Weekly", "Monthly"])
        update_layout.addRow("Check Frequency:", self.check_frequency_combo)

        self.baseline_auto_cb = QCheckBox("Auto-update baseline after system changes")
        self.baseline_auto_cb.setChecked(True)
        update_layout.addRow(self.baseline_auto_cb)

        layout.addWidget(update_group)

        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(perf_group)

        self.performance_combo = QComboBox()
        self.performance_combo.addItems(["Fast", "Balanced", "Thorough"])
        self.performance_combo.setCurrentText("Balanced")
        perf_layout.addRow("Performance Mode:", self.performance_combo)

        layout.addWidget(perf_group)

        # Logging settings
        log_group = QGroupBox("Logging Settings")
        log_layout = QFormLayout(log_group)

        self.enable_logging_cb = QCheckBox("Enable comprehensive logging")
        self.enable_logging_cb.setChecked(True)
        log_layout.addRow(self.enable_logging_cb)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        self.log_level_combo.setCurrentText("Info")
        log_layout.addRow("Log Level:", self.log_level_combo)

        layout.addWidget(log_group)

        # Custom rules (placeholder for future implementation)
        custom_group = QGroupBox("Custom Rules (Advanced)")
        custom_layout = QFormLayout(custom_group)

        self.custom_rules_cb = QCheckBox("Enable custom detection rules")
        custom_layout.addRow(self.custom_rules_cb)

        self.custom_rules_path = QLineEdit()
        self.custom_rules_path.setPlaceholderText("/path/to/custom/rules")
        self.custom_rules_path.setEnabled(False)
        custom_layout.addRow("Rules Path:", self.custom_rules_path)

        # Connect custom rules checkbox
        self.custom_rules_cb.toggled.connect(self.custom_rules_path.setEnabled)

        layout.addWidget(custom_group)

        layout.addStretch()

    def get_config(self) -> RKHunterConfig:
        """Get current configuration from UI"""
        return RKHunterConfig(
            update_mirrors=self.update_mirrors_cb.isChecked(),
            mirrors_mode=self.mirrors_mode_combo.currentIndex(),
            auto_update_db=self.auto_update_cb.isChecked(),
            check_frequency=self.check_frequency_combo.currentText().lower(),
            enable_logging=self.enable_logging_cb.isChecked(),
            log_level=self.log_level_combo.currentText().lower(),
            custom_rules_enabled=self.custom_rules_cb.isChecked(),
            custom_rules_path=self.custom_rules_path.text(),
            baseline_auto_update=self.baseline_auto_cb.isChecked(),
            performance_mode=self.performance_combo.currentText().lower(),
            network_timeout=self.network_timeout_spin.value(),
        )


class RKHunterOptimizationResultsWidget(QWidget):
    """Widget displaying optimization results"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Optimization Results")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Results tabs
        self.results_tabs = QTabWidget()

        # Changes tab
        changes_widget = QWidget()
        changes_layout = QVBoxLayout(changes_widget)

        self.changes_list = QListWidget()
        changes_layout.addWidget(QLabel("Configuration Changes:"))
        changes_layout.addWidget(self.changes_list)

        self.results_tabs.addTab(changes_widget, "Changes")

        # Improvements tab
        improvements_widget = QWidget()
        improvements_layout = QVBoxLayout(improvements_widget)

        self.improvements_list = QListWidget()
        improvements_layout.addWidget(QLabel("Performance Improvements:"))
        improvements_layout.addWidget(self.improvements_list)

        self.results_tabs.addTab(improvements_widget, "Improvements")

        # Recommendations tab
        recommendations_widget = QWidget()
        recommendations_layout = QVBoxLayout(recommendations_widget)

        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(QLabel("Additional Recommendations:"))
        recommendations_layout.addWidget(self.recommendations_text)

        self.results_tabs.addTab(recommendations_widget, "Recommendations")

        # Warnings tab
        warnings_widget = QWidget()
        warnings_layout = QVBoxLayout(warnings_widget)

        self.warnings_list = QListWidget()
        warnings_layout.addWidget(QLabel("Warnings and Issues:"))
        warnings_layout.addWidget(self.warnings_list)

        self.results_tabs.addTab(warnings_widget, "Warnings")

        layout.addWidget(self.results_tabs)

    def update_results(self, report: OptimizationReport):
        """Update results display"""
        # Clear previous results
        self.changes_list.clear()
        self.improvements_list.clear()
        self.warnings_list.clear()

        # Populate changes
        for change in report.config_changes:
            item = QListWidgetItem(f"✅ {change}")
            item.setForeground(QColor("green"))
            self.changes_list.addItem(item)

        if not report.config_changes:
            item = QListWidgetItem("ℹ️ No configuration changes were needed")
            self.changes_list.addItem(item)

        # Populate improvements
        for improvement in report.performance_improvements:
            item = QListWidgetItem(f"🚀 {improvement}")
            item.setForeground(QColor("blue"))
            self.improvements_list.addItem(item)

        if not report.performance_improvements:
            item = QListWidgetItem("ℹ️ No performance improvements applied")
            self.improvements_list.addItem(item)

        # Populate recommendations
        if report.recommendations:
            recommendations_html = "<ul>"
            for rec in report.recommendations:
                recommendations_html += f"<li>{rec}</li>"
            recommendations_html += "</ul>"
            self.recommendations_text.setHtml(recommendations_html)
        else:
            self.recommendations_text.setPlainText(
                "No additional recommendations at this time."
            )

        # Populate warnings
        for warning in report.warnings:
            item = QListWidgetItem(f"⚠️ {warning}")
            item.setForeground(QColor("orange"))
            self.warnings_list.addItem(item)

        if not report.warnings:
            item = QListWidgetItem("✅ No warnings or issues detected")
            item.setForeground(QColor("green"))
            self.warnings_list.addItem(item)

        # Set tab badges based on content
        self.results_tabs.setTabText(0, f"Changes ({len(report.config_changes)})")
        self.results_tabs.setTabText(
            1, f"Improvements ({len(report.performance_improvements)})"
        )
        self.results_tabs.setTabText(
            2, f"Recommendations ({len(report.recommendations)})"
        )
        self.results_tabs.setTabText(3, f"Warnings ({len(report.warnings)})")


class RKHunterOptimizationTab(QWidget):
    """Main RKHunter optimization tab widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_report = None
        self.worker = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Header with controls
        header_layout = QHBoxLayout()

        title = QLabel("RKHunter Configuration Optimization")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Control buttons
        self.refresh_status_btn = QPushButton("🔄 Refresh Status")
        self.refresh_status_btn.setMinimumWidth(120)
        header_layout.addWidget(self.refresh_status_btn)

        self.optimize_btn = QPushButton("⚡ Optimize Configuration")
        self.optimize_btn.setMinimumWidth(150)
        self.optimize_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """
        )
        header_layout.addWidget(self.optimize_btn)

        main_layout.addLayout(header_layout)

        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.progress_label)

        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Status and Configuration
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Status widget
        self.status_widget = RKHunterStatusWidget()
        left_layout.addWidget(self.status_widget)

        # Configuration widget in scroll area
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        self.config_widget = RKHunterConfigWidget()
        config_scroll.setWidget(self.config_widget)
        left_layout.addWidget(config_scroll)

        splitter.addWidget(left_panel)

        # Right panel: Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.results_widget = RKHunterOptimizationResultsWidget()
        right_layout.addWidget(self.results_widget)

        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([400, 500])
        main_layout.addWidget(splitter)

        # Initial state
        self.progress_label.setText(
            "Click 'Refresh Status' to check current RKHunter configuration"
        )

    def setup_connections(self):
        """Set up signal connections"""
        self.refresh_status_btn.clicked.connect(self.refresh_status)
        self.optimize_btn.clicked.connect(self.run_optimization)

    def refresh_status(self):
        """Refresh RKHunter status using a lightweight status check"""
        if self.worker and self.worker.isRunning():
            return

        self.refresh_status_btn.setEnabled(False)
        self.progress_label.setText("Checking RKHunter status...")

        # Create a lightweight status-only worker
        self.worker = StatusOnlyWorker()
        self.worker.status_updated.connect(self.on_status_updated)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.finished.connect(self.on_status_check_finished)
        self.worker.start()

    def run_optimization(self):
        """Start RKHunter optimization"""
        if self.worker and self.worker.isRunning():
            return

        # Get configuration from UI
        config = self.config_widget.get_config()

        # Confirm optimization
        reply = QMessageBox.question(
            self,
            "Confirm Optimization",
            "This will modify RKHunter configuration files and may update the baseline.\n\n"
            "Do you want to proceed with the optimization?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.optimize_btn.setEnabled(False)
        self.refresh_status_btn.setEnabled(False)
        self.optimize_btn.setText("⏳ Optimizing...")
        self.progress_label.setText("Starting optimization...")

        # Start optimization worker
        self.worker = RKHunterOptimizationWorker(config)
        self.worker.optimization_complete.connect(self.on_optimization_complete)
        self.worker.status_updated.connect(self.on_status_updated)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_optimization_finished)
        self.worker.start()

    def on_status_updated(self, status: RKHunterStatus):
        """Handle status update"""
        self.status_widget.update_status(status)
        self.progress_label.setText("Status updated successfully")

    def on_optimization_complete(self, report: OptimizationReport):
        """Handle completed optimization"""
        self.current_report = report
        self.results_widget.update_results(report)

        # Show summary
        changes_count = len(report.config_changes)
        improvements_count = len(report.performance_improvements)
        warnings_count = len(report.warnings)

        summary = f"Optimization completed: {changes_count} changes, {improvements_count} improvements"
        if warnings_count > 0:
            summary += f", {warnings_count} warnings"

        self.progress_label.setText(summary)

        # Show completion message
        QMessageBox.information(
            self,
            "Optimization Complete",
            f"RKHunter optimization completed successfully!\n\n"
            f"• Configuration changes: {changes_count}\n"
            f"• Performance improvements: {improvements_count}\n"
            f"• Warnings: {warnings_count}\n\n"
            f"Check the results tabs for detailed information.",
        )

    def on_error(self, error_message: str):
        """Handle optimization error"""
        self.progress_label.setText(f"Error: {error_message}")
        QMessageBox.warning(
            self,
            "Optimization Error",
            f"An error occurred during optimization:\n\n{error_message}\n\n"
            f"Please check your system configuration and try again.",
        )

    def on_progress_updated(self, message: str):
        """Handle progress updates"""
        self.progress_label.setText(message)

    def on_status_check_finished(self):
        """Handle status check completion"""
        self.refresh_status_btn.setEnabled(True)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def on_optimization_finished(self):
        """Handle optimization completion"""
        self.optimize_btn.setEnabled(True)
        self.refresh_status_btn.setEnabled(True)
        self.optimize_btn.setText("⚡ Optimize Configuration")

        if self.worker:
            self.worker.deleteLater()
            self.worker = None

        # Refresh status after optimization
        QTimer.singleShot(1000, self.refresh_status)


class RKHunterManualActionsDialog(QDialog):
    """Dialog for manual RKHunter actions"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual RKHunter Actions")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Actions group
        actions_group = QGroupBox("Available Actions")
        actions_layout = QVBoxLayout(actions_group)

        # Update mirrors button
        self.update_mirrors_btn = QPushButton("🔄 Update Mirrors")
        self.update_mirrors_btn.clicked.connect(self.update_mirrors)
        actions_layout.addWidget(self.update_mirrors_btn)

        # Update baseline button
        self.update_baseline_btn = QPushButton("📋 Update Baseline (--propupd)")
        self.update_baseline_btn.clicked.connect(self.update_baseline)
        actions_layout.addWidget(self.update_baseline_btn)

        # Check configuration button
        self.check_config_btn = QPushButton("🔍 Check Configuration")
        self.check_config_btn.clicked.connect(self.check_configuration)
        actions_layout.addWidget(self.check_config_btn)

        layout.addWidget(actions_group)

        # Output area
        output_group = QGroupBox("Command Output")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier", 10))
        output_layout.addWidget(self.output_text)

        layout.addWidget(output_group)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def update_mirrors(self):
        """Update RKHunter mirrors"""
        self.run_action(
            "Updating mirrors...", lambda: self.optimizer.update_mirrors_enhanced()
        )

    def update_baseline(self):
        """Update RKHunter baseline"""
        self.run_action(
            "Updating baseline...", lambda: self.optimizer.update_baseline_smart()
        )

    def check_configuration(self):
        """Check RKHunter configuration"""

        def check_config():
            result = subprocess.run(
                ["rkhunter", "--config-check"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0, result.stdout + result.stderr

        self.run_action("Checking configuration...", check_config)

    def run_action(self, status_message: str, action_func):
        """Run an action and display results"""
        self.output_text.append(f"\n{'=' * 50}")
        self.output_text.append(f"🔄 {status_message}")
        self.output_text.append(f"{'=' * 50}")

        try:
            if hasattr(self, "optimizer"):
                success, message = action_func()
            else:
                self.optimizer = RKHunterOptimizer()
                success, message = action_func()

            if success:
                self.output_text.append(f"✅ Success: {message}")
            else:
                self.output_text.append(f"❌ Failed: {message}")

        except Exception as e:
            self.output_text.append(f"💥 Error: {str(e)}")

        # Scroll to bottom
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)
