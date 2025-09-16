#!/usr/bin/env python3
"""
Interactive Configuration Fix Dialog for RKHunter

This dialog allows users to review and selectively apply configuration fixes.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .theme_manager import get_theme_manager

logger = logging.getLogger(__name__)


class ConfigFixDialog(QDialog):
    """Dialog for interactive configuration fix selection and application"""

    fixes_applied = pyqtSignal(list)  # Signal emitted when fixes are applied

    def __init__(self, fixable_issues: dict, parent=None):
        super().__init__(parent)
        self.fixable_issues = fixable_issues
        self.selected_fixes = set()
        self.theme_manager = get_theme_manager()

        self.setWindowTitle("🔧 RKHunter Configuration Optimizer")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self._setup_ui()
        self._populate_issues()
        self._apply_theme()

    def _setup_ui(self):
        """Setup the dialog UI with improved spacing and layout"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with improved styling
        header_label = QLabel("🔧 RKHunter Configuration Optimizer")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Theme-based styling will be applied in _apply_theme()
        layout.addWidget(header_label)
        self.header_label = header_label  # Store reference for theming

        # Description with better formatting
        desc_label = QLabel(
            "The following system configuration issues can be automatically fixed. "
            "Review the details and select which optimizations you'd like to apply to /etc/rkhunter.conf:"
        )
        desc_label.setWordWrap(True)
        # Theme-based styling will be applied in _apply_theme()
        layout.addWidget(desc_label)
        self.desc_label = desc_label  # Store reference for theming

        # Create splitter for main content with better proportions
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter)

        # Left side: Issue list with checkboxes
        self._setup_issues_panel(splitter)

        # Right side: Fix details
        self._setup_details_panel(splitter)

        # Set better splitter proportions for wider display
        splitter.setSizes([450, 650])

        # Bottom buttons with improved spacing
        self._setup_buttons(layout)

        # Count label with better styling
        self.count_label = QLabel()
        # Theme-based styling will be applied in _apply_theme()
        layout.addWidget(self.count_label)

    def _setup_issues_panel(self, splitter):
        """Setup the issues selection panel with improved layout"""
        issues_widget = QWidget()
        issues_layout = QVBoxLayout(issues_widget)
        issues_layout.setSpacing(12)
        issues_layout.setContentsMargins(15, 15, 15, 15)

        # Panel title with better styling
        title_label = QLabel("� Available Optimizations")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2d5aa0;
                padding: 8px;
                margin-bottom: 8px;
                border-bottom: 2px solid #2d5aa0;
            }
        """)
        issues_layout.addWidget(title_label)
        self.issues_title_label = title_label  # Store reference for theming

        # Scroll area for issues with improved sizing
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(400)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QScrollArea QWidget {
                background-color: white;
            }
        """)
        self.issues_scroll_area = scroll_area  # Store reference for theming

        self.issues_widget = QWidget()
        self.issues_layout = QVBoxLayout(self.issues_widget)
        self.issues_layout.setSpacing(10)
        self.issues_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area.setWidget(self.issues_widget)
        issues_layout.addWidget(scroll_area)

        # Select all/none buttons with improved styling
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        select_all_btn = QPushButton("✓ Select All")
        # Theme-based styling will be applied in _apply_theme()
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)
        self.select_all_btn = select_all_btn  # Store reference for theming

        select_none_btn = QPushButton("✗ Select None")
        # Theme-based styling will be applied in _apply_theme()
        select_none_btn.clicked.connect(self._select_none)
        button_layout.addWidget(select_none_btn)
        self.select_none_btn = select_none_btn  # Store reference for theming

        issues_layout.addLayout(button_layout)

        splitter.addWidget(issues_widget)

    def _setup_details_panel(self, splitter):
        """Setup the fix details panel with improved layout"""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(12)
        details_layout.setContentsMargins(15, 15, 15, 15)

        # Panel title with better styling
        title_label = QLabel("� Optimization Details")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2d5aa0;
                padding: 8px;
                margin-bottom: 8px;
                border-bottom: 2px solid #2d5aa0;
            }
        """)
        details_layout.addWidget(title_label)
        self.details_title_label = title_label  # Store reference for theming

        # Details text area with improved styling and sizing
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMinimumWidth(500)
        # Theme-based styling will be applied in _apply_theme()

        # Set a default message with theme-aware styling
        self._set_default_message()

        details_layout.addWidget(self.details_text)

        splitter.addWidget(details_widget)

    def _setup_buttons(self, layout):
        """Setup dialog buttons with improved styling and spacing"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(10, 15, 10, 10)

        # Apply fixes button with enhanced styling
        self.apply_button = QPushButton("⚡ Apply Selected Optimizations")
        # Theme-based styling will be applied in _apply_theme()
        self.apply_button.clicked.connect(self._apply_fixes)
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.apply_button)

        button_layout.addStretch()

        # Cancel button with improved styling
        cancel_button = QPushButton("✖ Cancel")
        # Theme-based styling will be applied in _apply_theme()
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        self.cancel_button = cancel_button  # Store reference for theming

        layout.addLayout(button_layout)

    def _populate_issues(self):
        """Populate the issues list"""
        if not self.fixable_issues:
            # No issues found - create a more attractive display
            no_issues_widget = QWidget()
            no_issues_layout = QVBoxLayout(no_issues_widget)
            no_issues_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_issues_layout.setSpacing(15)

            # Success icon and message
            success_label = QLabel("🎉")
            success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            success_label.setStyleSheet("font-size: 48px;")
            no_issues_layout.addWidget(success_label)

            # Main message
            message_label = QLabel("Excellent! No Configuration Issues Found")
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme_manager.get_color('success')};
                    font-weight: bold;
                    font-size: 16px;
                    padding: 10px;
                }}
            """)
            no_issues_layout.addWidget(message_label)

            # Subtitle
            subtitle_label = QLabel("Your RKHunter configuration is already optimized")
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.theme_manager.get_color('secondary_text')};
                    font-size: 13px;
                    padding: 5px;
                }}
            """)
            no_issues_layout.addWidget(subtitle_label)

            self.issues_layout.addWidget(no_issues_widget)
            self._update_details_text("✅ <b>No fixable issues detected.</b><br><br>Your RKHunter configuration appears to be up-to-date and optimized.")
            return

        # Group issues by type for better organization
        issue_groups = {}
        for fix_id, issue in self.fixable_issues.items():
            issue_type = self._get_issue_type(fix_id)
            if issue_type not in issue_groups:
                issue_groups[issue_type] = []
            issue_groups[issue_type].append((fix_id, issue))

        # Create checkboxes for each group
        for group_name, group_issues in issue_groups.items():
            # Group header with theme-based styling
            group_box = QGroupBox(group_name)
            group_box.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 2px solid {self.theme_manager.get_color('border_muted')};
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background-color: {self.theme_manager.get_color('background')};
                    color: {self.theme_manager.get_color('primary_text')};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: {self.theme_manager.get_color('accent')};
                    background-color: {self.theme_manager.get_color('background')};
                }}
            """)
            group_layout = QVBoxLayout(group_box)
            group_layout.setSpacing(8)

            for fix_id, issue in group_issues:
                # Create description with sudo indicator if needed
                description = issue["description"]
                if issue.get("requires_sudo", False):
                    description += " 🔒"  # Add lock icon for sudo-required fixes

                checkbox = QCheckBox(description)
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        font-size: 12px;
                        padding: 6px;
                        spacing: 8px;
                        color: {self.theme_manager.get_color('primary_text')};
                    }}
                    QCheckBox::indicator {{
                        width: 18px;
                        height: 18px;
                        border-radius: 3px;
                        border: 2px solid {self.theme_manager.get_color('border_muted')};
                        background-color: {self.theme_manager.get_color('background')};
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: {self.theme_manager.get_color('accent')};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {self.theme_manager.get_color('accent')};
                        border-color: {self.theme_manager.get_color('accent')};
                        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik04LjMzMzMzIDAuNUwzLjMzMzMzIDUuNUwxLjY2NjY3IDMuODMzMzMiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                    }}
                    QCheckBox::indicator:checked:hover {{
                        background-color: {self.theme_manager.get_color('accent_hover')};
                    }}
                """)

                # Enhanced tooltip with sudo information
                tooltip_text = f"<b>Fix Action:</b> {issue['fix_action']}<br><b>Impact:</b> {issue['impact']}"
                if issue.get("requires_sudo", False):
                    tooltip_text += "<br><br><b>⚠️ Administrator Access Required:</b><br>This fix requires sudo privileges to modify the system configuration file."
                checkbox.setToolTip(tooltip_text)

                checkbox.stateChanged.connect(lambda state, fid=fix_id: self._on_checkbox_changed(fid, state))
                group_layout.addWidget(checkbox)

            self.issues_layout.addWidget(group_box)

        # Add stretch to push everything to the top
        self.issues_layout.addStretch()

        # Update details with summary
        self._update_details_with_summary()

    def _get_issue_type(self, fix_id: str) -> str:
        """Get a human-readable group name for an issue type"""
        if "obsolete" in fix_id:
            return "📦 Obsolete Settings"
        elif "egrep" in fix_id:
            return "📅 Deprecated Commands"
        elif "regex" in fix_id:
            return "🔍 Regex Pattern Issues"
        else:
            return "🔧 Other Configuration Issues"

    def _on_checkbox_changed(self, fix_id: str, state: int):
        """Handle checkbox state changes"""
        if state == Qt.CheckState.Checked.value:
            self.selected_fixes.add(fix_id)
        else:
            self.selected_fixes.discard(fix_id)

        self._update_count_label()
        self._update_apply_button()
        self._update_details_for_selection()

    def _select_all(self):
        """Select all fixable issues"""
        for i in range(self.issues_layout.count() - 1):  # -1 for stretch
            item = self.issues_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QGroupBox):
                group_box = item.widget()
                group_layout = group_box.layout()
                for j in range(group_layout.count()):
                    group_item = group_layout.itemAt(j)
                    if group_item and group_item.widget() and isinstance(group_item.widget(), QCheckBox):
                        group_item.widget().setChecked(True)

    def _select_none(self):
        """Deselect all fixable issues"""
        for i in range(self.issues_layout.count() - 1):  # -1 for stretch
            item = self.issues_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QGroupBox):
                group_box = item.widget()
                group_layout = group_box.layout()
                for j in range(group_layout.count()):
                    group_item = group_layout.itemAt(j)
                    if group_item and group_item.widget() and isinstance(group_item.widget(), QCheckBox):
                        group_item.widget().setChecked(False)

    def _update_count_label(self):
        """Update the count label with improved styling"""
        total = len(self.fixable_issues)
        selected = len(self.selected_fixes)

        if selected == 0:
            status_text = "No optimizations selected"
            status_color = self.theme_manager.get_color('muted_text')
        elif selected == total:
            status_text = f"All {total} optimizations selected"
            status_color = self.theme_manager.get_color('success')
        else:
            status_text = f"{selected} of {total} optimizations selected"
            status_color = self.theme_manager.get_color('accent')

        self.count_label.setText(f"📊 {status_text}")
        self.count_label.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                background-color: {self.theme_manager.get_color('secondary_bg')};
                border-radius: 4px;
                border-left: 3px solid {status_color};
            }}
        """)

    def _update_apply_button(self):
        """Update the apply button state"""
        self.apply_button.setEnabled(len(self.selected_fixes) > 0)

    def _update_details_with_summary(self):
        """Update details panel with summary of all issues"""
        if not self.fixable_issues:
            return

        html = "<h3>🔍 Configuration Issues Summary</h3>"
        html += f"<p>Found <strong>{len(self.fixable_issues)}</strong> issues that can be automatically fixed:</p>"
        html += "<ul>"

        for fix_id, issue in self.fixable_issues.items():
            html += f"<li><strong>{issue['description']}</strong><br/>"
            html += f"   📍 {issue['detail']}<br/>"
            html += f"   🔧 Fix: {issue['fix_action']}<br/>"
            html += f"   💡 Impact: {issue['impact']}</li><br/>"

        html += "</ul>"
        html += "<p><em>Select the issues you want to fix and click 'Apply Selected Fixes'.</em></p>"

        self.details_text.setHtml(html)

    def _update_details_for_selection(self):
        """Update details panel for current selection"""
        if not self.selected_fixes:
            self._update_details_with_summary()
            return

        html = "<h3>🎯 Selected Fixes</h3>"
        html += f"<p>The following <strong>{len(self.selected_fixes)}</strong> fixes will be applied:</p>"

        # Check if any fixes require sudo
        sudo_required = any(
            self.fixable_issues[fix_id].get("requires_sudo", False)
            for fix_id in self.selected_fixes
            if fix_id in self.fixable_issues
        )

        if sudo_required:
            html += '<p style="color: #ff9500; font-weight: bold;">🔒 Administrator access will be requested for system configuration changes.</p>'

        html += "<ul>"

        for fix_id in self.selected_fixes:
            if fix_id in self.fixable_issues:
                issue = self.fixable_issues[fix_id]
                sudo_indicator = " 🔒" if issue.get("requires_sudo", False) else ""
                html += f"<li><strong>{issue['description']}{sudo_indicator}</strong><br/>"
                html += f"   📍 {issue['detail']}<br/>"
                html += f"   🔧 Action: {issue['fix_action']}<br/>"
                html += f"   💡 Result: {issue['impact']}"
                if issue.get("requires_sudo", False):
                    html += "<br/>   🔒 <em>Requires administrator privileges</em>"
                html += "</li><br/>"

        html += "</ul>"
        html += "<p><strong>⚠️ These changes will be applied to the system RKHunter configuration file.</strong></p>"

        self.details_text.setHtml(html)

    def _apply_fixes(self):
        """Apply the selected fixes"""
        if not self.selected_fixes:
            return

        # Emit signal with selected fix IDs
        self.fixes_applied.emit(list(self.selected_fixes))
        self.accept()

    def get_selected_fixes(self) -> list[str]:
        """Get the list of selected fix IDs"""
        return list(self.selected_fixes)

    def _apply_theme(self):
        """Apply theme-based styling to all dialog components"""
        theme = self.theme_manager

        # Main dialog background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.get_color('background')};
                color: {theme.get_color('primary_text')};
            }}
        """)

        # Header styling
        self.header_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.get_color('accent')};
                padding: 10px;
                margin-bottom: 5px;
            }}
        """)

        # Description styling
        self.desc_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.get_color('secondary_text')};
                font-size: 12px;
                padding: 10px;
                margin-bottom: 10px;
                background-color: {theme.get_color('secondary_bg')};
                border-radius: 6px;
                border-left: 3px solid {theme.get_color('accent')};
            }}
        """)

        # Count label styling
        if hasattr(self, 'count_label'):
            self.count_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme.get_color('muted_text')};
                    font-size: 12px;
                    font-weight: bold;
                    padding: 8px;
                    background-color: {theme.get_color('secondary_bg')};
                    border-radius: 4px;
                    border-left: 3px solid {theme.get_color('muted_text')};
                }}
            """)

        # Issues panel styling
        if hasattr(self, 'issues_title_label'):
            self.issues_title_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme.get_color('accent')};
                    padding: 8px;
                    margin-bottom: 8px;
                    border-bottom: 2px solid {theme.get_color('accent')};
                }}
            """)

        if hasattr(self, 'issues_scroll_area'):
            self.issues_scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    border: 1px solid {theme.get_color('border_muted')};
                    border-radius: 6px;
                    background-color: {theme.get_color('background')};
                }}
                QScrollArea QWidget {{
                    background-color: {theme.get_color('background')};
                }}
            """)

        # Details panel styling
        if hasattr(self, 'details_title_label'):
            self.details_title_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme.get_color('accent')};
                    padding: 8px;
                    margin-bottom: 8px;
                    border-bottom: 2px solid {theme.get_color('accent')};
                }}
            """)

        if hasattr(self, 'details_text'):
            self.details_text.setStyleSheet(f"""
                QTextEdit {{
                    border: 1px solid {theme.get_color('border_muted')};
                    border-radius: 6px;
                    background-color: {theme.get_color('secondary_bg')};
                    color: {theme.get_color('primary_text')};
                    padding: 12px;
                    font-family: {theme.get_font_property('monospace_family')};
                    font-size: 11px;
                    line-height: 1.4;
                }}
            """)

        # Button styling
        if hasattr(self, 'apply_button'):
            self.apply_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.get_color('accent')};
                    color: {theme.get_color('contrast_text')};
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 200px;
                }}
                QPushButton:hover {{
                    background-color: {theme.get_color('accent_hover')};
                }}
                QPushButton:pressed {{
                    background-color: {theme.get_color('accent_pressed')};
                }}
                QPushButton:disabled {{
                    background-color: {theme.get_color('disabled_bg')};
                    color: {theme.get_color('disabled_text')};
                }}
            """)

        if hasattr(self, 'select_all_btn'):
            self.select_all_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.get_color('success')};
                    color: {theme.get_color('contrast_text')};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {theme.get_color('success_border')};
                }}
            """)

        if hasattr(self, 'select_none_btn'):
            self.select_none_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.get_color('error')};
                    color: {theme.get_color('contrast_text')};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {theme.get_color('error_border')};
                }}
            """)

        if hasattr(self, 'cancel_button'):
            self.cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.get_color('muted_text')};
                    color: {theme.get_color('contrast_text')};
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {theme.get_color('hover_bg')};
                }}
                QPushButton:pressed {{
                    background-color: {theme.get_color('pressed_bg')};
                }}
            """)

    def _set_default_message(self):
        """Set the default message in the details panel"""
        color = self.theme_manager.get_color('secondary_text')
        self.details_text.setHtml(f"""
        <div style="text-align: center; color: {color}; padding: 20px;">
            <h3>💡 Select an optimization to view details</h3>
            <p>Click on any optimization item in the left panel to see detailed information about what changes will be made to your RKHunter configuration.</p>
        </div>
        """)
