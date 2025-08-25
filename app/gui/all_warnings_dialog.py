#!/usr/bin/env python3
"""
All Warnings Dialog - Comprehensive view of all scan warnings
Part of xanadOS Search & Destroy
"""

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QIcon
    from PyQt6.QtWidgets import (
        QDialog,
        QFileDialog,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSplitter,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    PYQT6_AVAILABLE = True
except ImportError:
    # Fallback for environments without PyQt6
    PYQT6_AVAILABLE = False

    # Create dummy classes to prevent import errors
    class QDialog:
        pass

    class QVBoxLayout:
        pass

    class QHBoxLayout:
        pass

    class QLabel:
        pass

    class QPushButton:
        pass

    class QTextEdit:
        pass

    class QSplitter:
        pass

    class QListWidget:
        pass

    class QListWidgetItem:
        pass

    class QGroupBox:
        pass

    class QMessageBox:
        pass

    class QFileDialog:
        pass

    class Qt:
        class Orientation:
            Horizontal = 1


#!/usr/bin/env python3
"""
All Warnings Dialog - Comprehensive view of all scan warnings
Part of xanadOS Search & Destroy
"""


class AllWarningsDialog(QDialog):
    """Dialog showing comprehensive view of all scan warnings."""

    def __init__(self, warnings, parent=None):
        super().__init__(parent)

        # Validate input
        if not warnings:
            warnings = []

        self.warnings = warnings
        self.current_warning_index = 0
        self.parent_window = parent

        self.setWindowTitle("⚠️ Scan Warnings - Detailed Explanations")
        self.setModal(True)
        self.resize(900, 700)

        # Initialize UI components
        self.warning_list = None
        self.warning_title = None
        self.warning_details = None
        self.investigate_btn = None
        self.mark_safe_single_btn = None

        try:
            self._setup_ui()
            self._populate_warnings()

            # Apply parent theme if available
            if parent and hasattr(parent, "current_theme"):
                self._apply_theme(parent.current_theme)
            else:
                self._apply_theme("dark")

            # Select first warning if available
            if self.warnings and self.warning_list:
                self.warning_list.setCurrentRow(0)
                self._show_warning_details(0)
        except Exception as e:
            # If UI setup fails, show simple error dialog
            QMessageBox.critical(
                parent,
                "Error",
                f"Failed to create warnings dialog: {str(e)}\n\nPlease check the application logs.",
            )
            self.accept()  # Close dialog

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header_label = QLabel("⚠️ Security Warnings Found")
        header_label.setObjectName("headerLabel")  # For themed styling
        layout.addWidget(header_label)

        # Summary info
        summary_label = QLabel(
            f"Found {len(self.warnings)} warnings that require attention"
        )
        summary_label.setObjectName("summaryLabel")  # For themed styling
        layout.addWidget(summary_label)

        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - warnings list
        left_panel = self._create_warnings_list_panel()
        splitter.addWidget(left_panel)

        # Right panel - warning details
        right_panel = self._create_warning_details_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions (30% left, 70% right)
        splitter.setSizes([270, 630])

        # Bottom buttons
        button_layout = QHBoxLayout()

        # Mark all as safe button (for advanced users)
        mark_safe_btn = QPushButton("Mark All as Safe")
        mark_safe_btn.clicked.connect(self._mark_all_as_safe)
        button_layout.addWidget(mark_safe_btn)

        button_layout.addStretch()

        # Export warnings button
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self._export_warnings_report)
        button_layout.addWidget(export_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _apply_theme(self, theme_name: str):
        """Apply theme styling (dark + light) consistently."""
        is_light = theme_name == "light"

        # Use parent theme color API if available
        def color(key, default_dark, default_light):
            if (
                self.parent_window
                and hasattr(self.parent_window, "get_theme_color")
                and not is_light
            ):
                return self.parent_window.get_theme_color(key)
            return default_light if is_light else default_dark

        bg = color("background", "#1a1a1a", "#ffffff")
        secondary_bg = color("secondary_bg", "#2a2a2a", "#f7f7f9")
        tertiary_bg = color("tertiary_bg", "#333333", "#ececef")
        text = color("primary_text", "#FFCDAA", "#1f1f23")
        accent = color("accent", "#F14666", "#0078d4")
        border = color("border", "#EE8980", "#d0d0d5")
        color("success", "#28a745", "#218838")
        info = color("hover_bg", "#3a3a3a", "#e6f2fb")
        neutral = color("pressed_bg", "#2a2a2a", "#d9e7f2")

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QLabel#headerLabel {{
                font-size: 18px; font-weight: 700; margin-bottom: 4px; color: {accent};
            }}
            QLabel#summaryLabel {{ color: {text}; font-size: 12px; margin-bottom: 8px; }}
            QGroupBox {{
                border: 2px solid {border};
                border-radius: 8px;
                margin-top: 12px;
                background-color: {secondary_bg};
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 10px; padding: 2px 8px; color: {accent};
            }}
            QListWidget {{
                background-color: {secondary_bg};
                border: 1px solid {border};
                border-radius: 6px; color: {text};
            }}
            QTextEdit {{
                background-color: {tertiary_bg};
                border: 1px solid {border};
                border-radius: 6px; color: {text};
                font-family: monospace; font-size: 11px;
            }}
            QPushButton {{
                background-color: {secondary_bg};
                border: 1px solid {border};
                border-radius: 6px; padding: 8px 16px; color: {text}; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {info}; border-color: {accent}; }}
            QPushButton:pressed {{ background-color: {neutral}; }}
        """
        )

    def _create_warnings_list_panel(self):
        """Create the left panel with warnings list."""
        panel = QGroupBox("Warnings List")
        panel.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )

        layout = QVBoxLayout(panel)

        # Warnings list
        self.warning_list = QListWidget()
        self.warning_list.setStyleSheet(
            """
            QListWidget {
                background-color: #1E1E1E;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                border: 1px solid transparent;
            }
            QListWidget::item:selected {
                background-color: #FF6B35;
                color: white;
                border-color: #FF8C00;
            }
            QListWidget::item:hover {
                background-color: #333333;
                border-color: #555555;
            }
        """
        )
        self.warning_list.currentRowChanged.connect(self._show_warning_details)
        layout.addWidget(self.warning_list)

        return panel

    def _create_warning_details_panel(self):
        """Create the right panel with warning details."""
        panel = QGroupBox("Warning Details")
        panel.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )

        layout = QVBoxLayout(panel)

        # Warning title
        self.warning_title = QLabel("Select a warning to view details")
        self.warning_title.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #FF6B35;
                padding: 8px;
                background: #2D2D2D;
                border-radius: 6px;
                margin-bottom: 10px;
            }
        """
        )
        layout.addWidget(self.warning_title)

        # Warning details text area
        self.warning_details = QTextEdit()
        self.warning_details.setStyleSheet(
            """
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
        """
        )
        self.warning_details.setReadOnly(True)
        layout.addWidget(self.warning_details)

        # Action buttons for current warning
        action_layout = QHBoxLayout()

        self.investigate_btn = QPushButton("🔍 Investigate This Warning")
        self.investigate_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FFC107;
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E0A800; }
        """
        )
        self.investigate_btn.clicked.connect(self._investigate_current_warning)
        action_layout.addWidget(self.investigate_btn)

        self.mark_safe_single_btn = QPushButton("✓ Mark as Safe")
        self.mark_safe_single_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """
        )
        self.mark_safe_single_btn.clicked.connect(self._mark_current_warning_as_safe)
        action_layout.addWidget(self.mark_safe_single_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        return panel

    def _populate_warnings(self):
        """Populate the warnings list."""
        self.warning_list.clear()

        for i, warning in enumerate(self.warnings):
            # Get warning description/title
            title = getattr(warning, "description", f"Warning {i + 1}")
            if hasattr(warning, "check_name"):
                title = f"{warning.check_name}: {title}"

            # Truncate if too long
            if len(title) > 50:
                title = title[:47] + "..."

            # Create list item
            item = QListWidgetItem(f"⚠️ {title}")
            item.setToolTip(
                f"Warning {i + 1}: {getattr(warning, 'description', 'No description available')}"
            )
            self.warning_list.addItem(item)

    def _show_warning_details(self, index):
        """Show details for the selected warning."""
        if index < 0 or index >= len(self.warnings):
            return

        self.current_warning_index = index
        warning = self.warnings[index]

        # Update title
        title = getattr(warning, "description", f"Warning {index + 1}")
        if hasattr(warning, "check_name"):
            title = f"{warning.check_name}"
        self.warning_title.setText(f"⚠️ {title}")

        # Build detailed explanation
        details = []

        # Basic warning info
        details.append("📋 WARNING DETAILS")
        details.append("=" * 50)

        if hasattr(warning, "description"):
            details.append(f"Description: {warning.description}")

        if hasattr(warning, "file_path"):
            details.append(f"File/Path: {warning.file_path}")

        if hasattr(warning, "check_name"):
            details.append(f"Check: {warning.check_name}")

        details.append("")

        # Detailed explanation
        if hasattr(warning, "explanation") and warning.explanation:
            details.append("📖 DETAILED EXPLANATION")
            details.append("=" * 50)

            # Handle WarningExplanation object properly
            try:
                if hasattr(warning.explanation, "description"):
                    # It's a WarningExplanation object
                    explanation_obj = warning.explanation
                    details.append(
                        f"Category: {
                            explanation_obj.category.value
                            if hasattr(explanation_obj.category, 'value')
                            else str(explanation_obj.category)
                        }"
                    )
                    details.append(
                        f"Severity: {
                            explanation_obj.severity.value
                            if hasattr(explanation_obj.severity, 'value')
                            else str(explanation_obj.severity)
                        }"
                    )
                    details.append(f"Title: {explanation_obj.title}")
                    details.append("")
                    details.append(f"Description: {explanation_obj.description}")
                    details.append("")
                    details.append(f"Likely Cause: {explanation_obj.likely_cause}")
                    details.append("")
                    if (
                        hasattr(explanation_obj, "technical_details")
                        and explanation_obj.technical_details
                    ):
                        details.append(
                            f"Technical Details: {explanation_obj.technical_details}"
                        )
                        details.append("")
                    if (
                        hasattr(explanation_obj, "remediation_steps")
                        and explanation_obj.remediation_steps
                    ):
                        details.append("Remediation Steps:")
                        for step in explanation_obj.remediation_steps:
                            details.append(f"  • {str(step)}")
                        details.append("")
                else:
                    # It's a string explanation or other type
                    details.append(str(warning.explanation))
            except Exception as e:
                # Fallback to string conversion if anything goes wrong
                details.append(f"Explanation: {str(warning.explanation)}")
                details.append(f"(Note: Error processing explanation details: {e})")
            details.append("")
        else:
            details.append("📖 GENERAL GUIDANCE")
            details.append("=" * 50)
            details.append(self._get_generic_warning_explanation(warning))
            details.append("")

        # Recommendations
        details.append("💡 RECOMMENDED ACTIONS")
        details.append("=" * 50)
        recommendations = self._get_warning_recommendations(warning)
        for rec in recommendations:
            details.append(f"• {rec}")

        # Set the details text
        self.warning_details.setPlainText("\n".join(details))

    def _get_generic_warning_explanation(self, warning):
        """Get generic explanation for warnings without specific explanations."""
        return (
            "This warning indicates a potential security concern that requires attention.\n\n"
            "Security warnings typically fall into these categories:\n"
            "• System files that have been modified unexpectedly\n"
            "• Suspicious processes or network connections\n"
            "• Configuration changes that may reduce security\n"
            "• Potential indicators of malware or intrusion\n\n"
            "It's important to investigate each warning to determine if it represents\n"
            "a legitimate security threat or a false positive."
        )

    def _get_warning_recommendations(self, warning):
        """Get recommendations for addressing the warning."""
        recommendations = []

        # First, try to get specific recommendations from WarningExplanation
        try:
            if hasattr(warning, "explanation") and warning.explanation:
                if (
                    hasattr(warning.explanation, "recommended_action")
                    and warning.explanation.recommended_action
                ):
                    recommendations.append(str(warning.explanation.recommended_action))
                if (
                    hasattr(warning.explanation, "remediation_steps")
                    and warning.explanation.remediation_steps
                ):
                    for step in warning.explanation.remediation_steps:
                        recommendations.append(str(step))
        except Exception as e:
            # Log error but continue with fallback recommendations
            print(f"Warning: Error extracting specific recommendations: {e}")

        # Add generic recommendations if none were found or to supplement specific ones
        if not recommendations:
            recommendations = [
                "Review the warning details carefully",
                "Check recent system changes and installations",
                "Verify the legitimacy of any flagged files or processes",
                "Consult system logs for related events",
                "Consider running additional security scans",
                "If confirmed safe, mark the warning as a false positive",
                "If suspicious, take appropriate security measures",
            ]

        # Add specific recommendations based on warning type
        try:
            if hasattr(warning, "check_name") and warning.check_name:
                check_name = str(warning.check_name).lower()
                if "file" in check_name:
                    recommendations.insert(-2, "Verify file integrity and source")
                elif "process" in check_name:
                    recommendations.insert(-2, "Check process origin and behavior")
                elif "network" in check_name:
                    recommendations.insert(
                        -2, "Monitor network connections and traffic"
                    )
        except Exception as e:
            # Continue without type-specific recommendations if there's an error
            print(f"Warning: Error adding type-specific recommendations: {e}")

        # Ensure all recommendations are strings
        return [str(rec) for rec in recommendations]

    def _investigate_current_warning(self):
        """Provide investigation guidance for current warning."""
        if self.current_warning_index >= len(self.warnings):
            return

        self.warnings[self.current_warning_index]

        # Create investigation dialog
        if hasattr(self.parent_window, "show_themed_message_box"):
            self.parent_window.show_themed_message_box(
                "information",
                "🔍 Investigation Guidance",
                "To investigate this warning:\n\n"
                "1. Review the warning details above\n"
                "2. Check system logs around the time of detection\n"
                "3. Verify any files or processes mentioned\n"
                "4. Consider the system's recent activity\n"
                "5. Run additional targeted scans if needed\n\n"
                "If you're unsure about the warning's significance,\n"
                "consider consulting with a security professional.",
            )
        else:
            QMessageBox.information(
                self,
                "🔍 Investigation Guidance",
                "To investigate this warning:\n\n"
                "1. Review the warning details above\n"
                "2. Check system logs around the time of detection\n"
                "3. Verify any files or processes mentioned\n"
                "4. Consider the system's recent activity\n"
                "5. Run additional targeted scans if needed\n\n"
                "If you're unsure about the warning's significance,\n"
                "consider consulting with a security professional.",
            )

    def _mark_current_warning_as_safe(self):
        """Mark the current warning as safe."""
        if self.current_warning_index >= len(self.warnings):
            return

        if hasattr(self.parent_window, "show_themed_message_box"):
            reply = self.parent_window.show_themed_message_box(
                "question",
                "Mark Warning as Safe",
                "Are you sure this warning represents a false positive?\n\n"
                "Only mark warnings as safe if you're confident they\n"
                "don't represent actual security threats.",
            )
        else:
            reply = QMessageBox.question(
                self,
                "Mark Warning as Safe",
                "Are you sure this warning represents a false positive?\n\n"
                "Only mark warnings as safe if you're confident they\n"
                "don't represent actual security threats.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.parent_window, "show_themed_message_box"):
                self.parent_window.show_themed_message_box(
                    "information",
                    "Warning Marked as Safe",
                    "This warning has been marked as a false positive.\n"
                    "It will be ignored in future scans.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Warning Marked as Safe",
                    "This warning has been marked as a false positive.\n"
                    "It will be ignored in future scans.",
                )

    def _mark_all_as_safe(self):
        """Mark all warnings as safe (with strong confirmation)."""
        if hasattr(self.parent_window, "show_themed_message_box"):
            reply = self.parent_window.show_themed_message_box(
                "question",
                "Mark All Warnings as Safe",
                f"⚠️ WARNING: You are about to mark ALL {len(self.warnings)} warnings as safe!\n\n"
                f"This action should only be taken if you are absolutely certain\n"
                f"that none of these warnings represent actual security threats.\n\n"
                f"Are you sure you want to continue?",
            )
        else:
            reply = QMessageBox.question(
                self,
                "Mark All Warnings as Safe",
                f"⚠️ WARNING: You are about to mark ALL {len(self.warnings)} warnings as safe!\n\n"
                f"This action should only be taken if you are absolutely certain\n"
                f"that none of these warnings represent actual security threats.\n\n"
                f"Are you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

        if reply == QMessageBox.StandardButton.Yes:
            # Second confirmation
            if hasattr(self.parent_window, "show_themed_message_box"):
                reply2 = self.parent_window.show_themed_message_box(
                    "question",
                    "Final Confirmation",
                    "This is your final confirmation.\n\n"
                    "Mark all warnings as false positives?",
                )
            else:
                reply2 = QMessageBox.question(
                    self,
                    "Final Confirmation",
                    "This is your final confirmation.\n\n"
                    "Mark all warnings as false positives?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

            if reply2 == QMessageBox.StandardButton.Yes:
                if hasattr(self.parent_window, "show_themed_message_box"):
                    self.parent_window.show_themed_message_box(
                        "information",
                        "All Warnings Marked as Safe",
                        f"All {len(self.warnings)} warnings have been marked as false positives.\n"
                        f"They will be ignored in future scans.",
                    )
                else:
                    QMessageBox.information(
                        self,
                        "All Warnings Marked as Safe",
                        f"All {len(self.warnings)} warnings have been marked as false positives.\n"
                        f"They will be ignored in future scans.",
                    )

    def _export_warnings_report(self):
        """Export warnings to a detailed report file."""
        from datetime import datetime

        from PyQt6.QtWidgets import QFileDialog

        # Get save location
        default_name = f"warnings_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Warnings Report",
            default_name,
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            # Generate report content
            report_lines = []
            report_lines.append("SECURITY WARNINGS REPORT")
            report_lines.append("=" * 50)
            report_lines.append(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            report_lines.append(f"Total Warnings: {len(self.warnings)}")
            report_lines.append("")

            for i, warning in enumerate(self.warnings):
                report_lines.append(f"WARNING #{i + 1}")
                report_lines.append("-" * 30)

                if hasattr(warning, "description"):
                    report_lines.append(f"Description: {warning.description}")
                if hasattr(warning, "check_name"):
                    report_lines.append(f"Check: {warning.check_name}")
                if hasattr(warning, "file_path"):
                    report_lines.append(f"File/Path: {warning.file_path}")
                if hasattr(warning, "explanation") and warning.explanation:
                    report_lines.append(f"Explanation: {warning.explanation}")

                report_lines.append("")

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines))

            if hasattr(self.parent_window, "show_themed_message_box"):
                self.parent_window.show_themed_message_box(
                    "information",
                    "Report Exported",
                    f"Warnings report has been exported to:\n{file_path}",
                )
            else:
                QMessageBox.information(
                    self,
                    "Report Exported",
                    f"Warnings report has been exported to:\n{file_path}",
                )

        except Exception as e:
            if hasattr(self.parent_window, "show_themed_message_box"):
                self.parent_window.show_themed_message_box(
                    "critical", "Export Error", f"Failed to export report:\n{str(e)}"
                )
            else:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export report:\n{str(e)}"
                )
