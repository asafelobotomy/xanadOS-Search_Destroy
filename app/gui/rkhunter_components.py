#!/usr/bin/env python3
"""RKHunter scan dialog and thread components for S&D - Search & Destroy"""

import logging
import threading
import time
from typing import Any, List, Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.elevated_runner import validate_auth_session
from app.core.rkhunter_wrapper import RKHunterWrapper

from .thread_cancellation import CooperativeCancellationMixin


class RKHunterScanDialog(QDialog):
    """Dialog for configuring RKHunter scan options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RKHunter Scan Configuration")
        self.setModal(True)
        self.resize(500, 600)
        self.parent_window = parent

        # Test category checkboxes
        self.category_checkboxes = {}

        self.init_ui()

        # Apply parent theme if available
        if parent and hasattr(parent, "current_theme"):
            self.apply_theme(parent.current_theme)
        else:
            self.apply_theme("dark")

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Configure RKHunter Rootkit Scan")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px;"
        )
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Select test categories to run. RKHunter will check your system for "
            "rootkits, trojans, and other malicious software.\n\n"
            "⚠️ This scan may take several minutes to complete."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(desc_label)

        # Test categories group
        categories_group = QGroupBox("Test Categories")
        categories_layout = QVBoxLayout(categories_group)

        # Create scrollable area for checkboxes
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Define test categories with descriptions
        test_categories = {
            "system_commands": {
                "name": "System Commands",
                "description": "Check system command integrity and known rootkit modifications",
            },
            "rootkits": {
                "name": "Rootkits & Trojans",
                "description": "Scan for known rootkits, trojans, and malware signatures",
            },
            "network": {
                "name": "Network Security",
                "description": "Check network interfaces, ports, and packet capture tools",
            },
            "system_integrity": {
                "name": "System Integrity",
                "description": "Verify filesystem integrity, system configs, and startup files",
            },
            "applications": {
                "name": "Applications",
                "description": "Check for hidden processes, files, and suspicious applications",
            },
        }

        # Create checkboxes for each category
        for category_id, category_info in test_categories.items():
            checkbox = QCheckBox(category_info["name"])
            checkbox.setChecked(True)  # Default to all selected
            checkbox.setToolTip(category_info["description"])
            checkbox.setStyleSheet("margin: 5px 0px;")

            # Add description label
            desc_label = QLabel(f"  {category_info['description']}")
            desc_label.setStyleSheet(
                f"color: {
                    self.get_theme_color('secondary_text')
                    if hasattr(self, 'get_theme_color')
                    else '#666'
                }; font-size: 11px; margin-left: 20px; margin-bottom: 10px;"
            )
            desc_label.setWordWrap(True)

            scroll_layout.addWidget(checkbox)
            scroll_layout.addWidget(desc_label)

            self.category_checkboxes[category_id] = checkbox

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setMaximumHeight(300)
        categories_layout.addWidget(scroll_area)

        layout.addWidget(categories_group)

        # Quick select buttons
        quick_select_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_categories)

        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_categories)

        recommended_btn = QPushButton("Recommended")
        recommended_btn.clicked.connect(self.select_recommended_categories)
        recommended_btn.setToolTip("Select recommended test categories for most users")

        quick_select_layout.addWidget(select_all_btn)
        quick_select_layout.addWidget(select_none_btn)
        quick_select_layout.addWidget(recommended_btn)
        quick_select_layout.addStretch()

        layout.addLayout(quick_select_layout)

        # Warning and authentication notice
        warning_label = QLabel(
            "⚠️ <b>Administrator Authentication Required:</b><br/><br/>"
            "RKHunter requires elevated privileges to scan system areas for rootkits. "
            "You will be prompted for your password when the scan starts.<br/><br/>"
            "<b>This is normal and required for:</b><br/>"
            "• Accessing protected system files and directories<br/>"
            "• Checking kernel modules and system processes<br/>"
            "• Verifying system integrity and detecting rootkits<br/><br/>"
            "The scan may be resource-intensive and can trigger security software alerts.<br/><br/>"
            "<b>📋 Note:</b> Scan preferences have been moved to Settings → Scanning → RKHunter Integration. "
            "You can configure which test categories to run by default there."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            f"background-color: {self.get_theme_color('warning') if hasattr(self, 'get_theme_color') else '#fff3cd'}; "
            f"border: 1px solid {self.get_theme_color('border') if hasattr(self, 'get_theme_color') else '#ffeaa7'}; "
            "padding: 15px; border-radius: 5px; margin: 15px 0px; "
            "font-size: 13px; line-height: 1.4;"
        )
        layout.addWidget(warning_label)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        start_btn = QPushButton("Start Scan")
        start_btn.clicked.connect(self.accept)
        start_btn.setDefault(True)
        start_btn.setStyleSheet(
            f"QPushButton {{ background-color: {
                self.get_theme_color('success')
                if hasattr(self, 'get_theme_color')
                else '#007bff'
            }; "
            f"color: {
                self.get_theme_color('primary_text')
                if hasattr(self, 'get_theme_color')
                else 'white'
            }; "
            "font-weight: bold; padding: 8px 20px; border-radius: 4px; }"
            f"QPushButton:hover {{ background-color: {
                self.get_theme_color('hover_bg')
                if hasattr(self, 'get_theme_color')
                else '#0056b3'
            }; }}"
        )

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(start_btn)

        layout.addLayout(buttons_layout)

    def select_all_categories(self):
        """Select all test categories."""
        for checkbox in self.category_checkboxes.values():
            checkbox.setChecked(True)

    def select_no_categories(self):
        """Deselect all test categories."""
        for checkbox in self.category_checkboxes.values():
            checkbox.setChecked(False)

    def select_recommended_categories(self):
        """Select recommended test categories."""
        recommended = ["rootkits", "system_commands", "system_integrity"]

        for category_id, checkbox in self.category_checkboxes.items():
            checkbox.setChecked(category_id in recommended)

    def get_selected_categories(self) -> list[str]:
        """Get list of selected test categories."""
        selected = []
        for category_id, checkbox in self.category_checkboxes.items():
            if checkbox.isChecked():
                selected.append(category_id)
        return selected

    def get_theme_color(self, color_type: str) -> str:
        """Get theme color from parent window if available."""
        if self.parent_window and hasattr(self.parent_window, "get_theme_color"):
            return self.parent_window.get_theme_color(color_type)

        # Fallback colors if parent doesn't have theme system
        fallback_colors = {
            "background": "#1a1a1a",
            "secondary_bg": "#2a2a2a",
            "tertiary_bg": "#3a3a3a",
            "primary_text": "#FFCDAA",
            "success": "#9CB898",
            "error": "#F14666",
            "warning": "#EE8980",
            "accent": "#F14666",
            "border": "#EE8980",
            "hover_bg": "#4a4a4a",
            "pressed_bg": "#2a2a2a",
        }
        return fallback_colors.get(color_type, "#FFCDAA")

    def apply_theme(self, theme_name: str):
        """Apply theme styling to the dialog (supports light & dark)."""
        is_light = theme_name == "light"
        if is_light and not (
            self.parent_window and hasattr(self.parent_window, "get_theme_color")
        ):
            # Provide light palette fallback
            palette = {
                "background": "#ffffff",
                "secondary_bg": "#f8f9fa",
                "tertiary_bg": "#eceef1",
                "primary_text": "#222222",
                "success": "#198754",
                "border": "#d0d5da",
                "hover_bg": "#e6f2fb",
                "pressed_bg": "#d0e8f7",
                "accent": "#0078d4",
            }

            def p(k):
                return palette[k]

        else:

            def p(k):
                return self.get_theme_color(k)

        bg = p("background")
        secondary_bg = p("secondary_bg")
        tertiary_bg = p("tertiary_bg")
        text = p("primary_text")
        success = p("success")
        border = p("border")
        hover_bg = p("hover_bg")
        pressed_bg = p("pressed_bg")
        accent = p("accent")

        style = f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QLabel {{
                color: {text};
            }}
            QGroupBox {{
                color: {text};
                border: 2px solid {tertiary_bg};
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QCheckBox {{
                color: {text};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {tertiary_bg};
                background-color: {bg};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {success};
                background-color: {success};
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {tertiary_bg};
                border: 2px solid {border};
                border-radius: 5px;
                padding: 8px 16px;
                color: {text};
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
            QScrollArea {{
                border: 1px solid {tertiary_bg};
                border-radius: 5px;
                background-color: {bg};
            }}
            QScrollBar:vertical {{
                background-color: {secondary_bg};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {hover_bg};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {accent};
            }}
        """
        self.setStyleSheet(style)


class RKHunterScanThread(QThread, CooperativeCancellationMixin):
    """Thread for running RKHunter scans without blocking the UI."""

    progress_updated = pyqtSignal(str)
    progress_value_updated = pyqtSignal(int)  # Numeric progress for progress bar
    output_updated = pyqtSignal(str)  # Real-time command output
    scan_completed = pyqtSignal(object)  # RKHunterScanResult

    def __init__(
        self, rkhunter: RKHunterWrapper, test_categories: list[str] | None = None
    ):
        super().__init__()
        self.rkhunter = rkhunter
        self.test_categories = test_categories
        self.logger = logging.getLogger(__name__)
        self._scan_cancelled = False
        self._current_process = None  # Track the current RKHunter process

    def stop_scan(self):
        """Request to stop the current scan safely."""
        self.cooperative_cancel()
        self._scan_cancelled = True
        self.logger.info("Stop scan requested for RKHunter")

        # Use the wrapper's terminate method for safe process termination
        success = self.rkhunter.terminate_current_scan()

        if success:
            self.progress_updated.emit("🛑 RKHunter scan cancellation requested")
        else:
            self.progress_updated.emit(
                "⚠️ RKHunter scan termination failed - scan may continue briefly"
            )

        # Force the thread to exit quickly by setting cancellation flag
        # The run() method will check this flag and exit early

    def run(self):
        """Run the RKHunter scan in a separate thread."""
        try:
            # Only emit initial status, no progress bar updates until scan actually starts
            self.progress_updated.emit("Preparing RKHunter scan...")

            # Check if GUI sudo authentication is available
            sudo_available = self.rkhunter._find_executable("sudo")

            if not self.rkhunter.is_functional():
                if sudo_available:
                    self.progress_updated.emit(
                        "🔐 Waiting for GUI authentication... Please enter your password."
                    )
                else:
                    self.progress_updated.emit(
                        "⚠️ Waiting for authentication... Please enter your password in the terminal."
                    )
                # Don't update progress bar during authentication wait

                time.sleep(1)

            # Don't emit progress updates until we know authentication succeeded
            # and the scan is actually running
            # Don't emit progress updates until we know authentication succeeded
            # and the scan is actually running

            # Start the scan - this will handle authentication internally
            # Only start emitting progress once we know scan started successfully

            # Import here to avoid import delays

            scan_completed = threading.Event()
            scan_result: list[Any] = [
                None
            ]  # Use list to allow modification from inner function
            scan_error: list[Any] = [None]
            scan_started = threading.Event()  # Track when scan actually starts

            # Define output callback to emit real-time output and detect scan start
            def output_callback(line: str):
                """Handle real-time output from RKHunter."""
                # Check for cancellation immediately
                if self._scan_cancelled:
                    self.logger.info("Cancellation detected in output callback")
                    return

                if line.strip():  # Only emit non-empty lines
                    self.output_updated.emit(line)

                    # Look for indicators that the scan has actually started
                    # (not just authentication or initialization)
                    # Use very specific indicators that won't conflict with stage detection
                    scan_start_indicators = [
                        "Rootkit Hunter version",
                        "Starting to create file hashes",
                        "Please wait while the file hash values are",
                    ]

                    if any(indicator in line for indicator in scan_start_indicators):
                        if not scan_started.is_set():
                            scan_started.set()
                            # Don't emit progress value here - let main window handle all progress
                            self.progress_updated.emit(
                                "RKHunter scan is now running..."
                            )

            def run_scan():
                try:
                    # Check for cancellation before starting
                    if self._scan_cancelled:
                        self.logger.info("Scan cancelled before starting")
                        return

                    # Simple authentication check
                    self.logger.info("Checking authentication for scan thread...")
                    try:
                        session_valid = validate_auth_session()
                        if session_valid:
                            self.logger.info("Authentication validated for scan thread")
                        else:
                            self.logger.warning(
                                "Authentication validation failed in scan thread"
                            )
                            self.signals.message.emit("Authentication failed")
                            return
                    except Exception as e:
                        self.logger.warning(
                            "Could not check auth session in scan thread: %s", str(e)
                        )

                    result = self.rkhunter.scan_system_with_output_callback(
                        test_categories=self.test_categories,
                        update_database=True,  # Include database update to avoid double authentication
                        output_callback=output_callback,
                    )

                    # Check for cancellation after scan completes
                    if self._scan_cancelled:
                        self.logger.info("Scan cancelled after completion")
                        return

                    scan_result[0] = result
                except Exception as e:
                    self.logger.error("Error in RKHunter scan execution: %s", str(e))
                    scan_error[0] = e
                finally:
                    scan_completed.set()

            # Check for early cancellation
            if self._scan_cancelled:
                self.progress_updated.emit("🛑 RKHunter scan cancelled before start")
                return

            # Start scan in background thread
            scan_thread = threading.Thread(target=run_scan)
            scan_thread.start()

            # Wait for scan to actually start before emitting progress
            scan_started.wait(timeout=120)  # Wait up to 2 minutes for scan to start

            if not scan_started.is_set():
                # If scan hasn't started after timeout, something went wrong
                self.progress_updated.emit(
                    "❌ Scan failed to start - authentication may have been cancelled"
                )
                scan_thread.join(timeout=5)
                return

            # Now we rely on real-time output parsing for progress updates
            # The main window will handle progress based on actual scan output
            # No need for simulated progress steps here since we have real output

            # Just wait for scan to complete while real-time output handles progress
            # Check for cancellation periodically while waiting
            while scan_thread.is_alive():
                if self._scan_cancelled:
                    self.logger.info("Cancellation detected, breaking wait loop")
                    break
                scan_thread.join(timeout=1)  # Check every second

            # If cancelled, don't wait for thread - force cleanup
            if self._scan_cancelled:
                self.logger.info("Scan cancelled, forcing thread cleanup")
                if scan_thread.is_alive():
                    # Give the thread a few seconds to clean up
                    scan_thread.join(timeout=3)

                # Create cancelled result immediately
                self.progress_updated.emit("🛑 RKHunter scan cancelled")
                from datetime import datetime

                from app.core.rkhunter_wrapper import RKHunterScanResult

                cancelled_result = RKHunterScanResult(
                    scan_id=f"rkhunter_cancelled_{int(time.time())}",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    success=False,
                    error_message="Scan cancelled by user",
                )
                self.scan_completed.emit(cancelled_result)
                return

            # Wait for final completion if not cancelled
            if scan_thread.is_alive():
                scan_thread.join()

            if scan_error[0]:
                raise scan_error[0]

            result = scan_result[0]

            self.progress_updated.emit("Rootkit scan completed successfully")
            self.progress_value_updated.emit(100)
            self.scan_completed.emit(result)

        except Exception as e:
            self.logger.error("Error in RKHunter scan thread: %s", str(e))
            self.progress_value_updated.emit(0)  # Reset progress on error

            # Create error result
            from datetime import datetime

            from app.core.rkhunter_wrapper import RKHunterScanResult

            error_result = RKHunterScanResult(
                scan_id=f"error_{int(datetime.now().timestamp())}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                success=False,
                error_message=f"Scan thread error: {e!s}",
            )

            self.scan_completed.emit(error_result)
        finally:
            self.mark_cancellation_complete()
