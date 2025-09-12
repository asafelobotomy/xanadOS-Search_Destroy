#!/usr/bin/env python3
"""GUI components for the auto-update system"""

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

# Import compatible update system
try:
    from app.core.automatic_updates import AutoUpdateSystem

    UPDATES_AVAILABLE = True
except ImportError:
    UPDATES_AVAILABLE = False
    AutoUpdateSystem = None
from pathlib import Path

from app.gui.theme_manager import get_theme_manager


class UpdateCheckThread(QThread):
    """Thread for checking updates without blocking the UI."""

    update_available = pyqtSignal(dict)  # Emitted when update is available
    no_update = pyqtSignal()  # Emitted when no update is available
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs

    def __init__(self, current_version: str, force_check: bool = False):
        super().__init__()
        self.current_version = current_version
        self.force_check = force_check

    def run(self):
        try:
            updater = AutoUpdateSystem(self.current_version)
            update_info = updater.check_for_updates(self.force_check)

            if update_info and update_info.get("available"):
                self.update_available.emit(update_info)
            else:
                self.no_update.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))


class UpdateDownloadThread(QThread):
    """Thread for downloading updates."""

    progress_updated = pyqtSignal(int)  # Progress percentage
    download_completed = pyqtSignal(str)  # Path to downloaded file
    download_failed = pyqtSignal(str)  # Error message

    def __init__(self, current_version: str, download_url: str):
        super().__init__()
        self.current_version = current_version
        self.download_url = download_url

    def run(self):
        try:
            updater = AutoUpdateSystem(self.current_version)

            def progress_callback(percent):
                self.progress_updated.emit(percent)

            download_path = updater.download_update(self.download_url, progress_callback)

            if download_path:
                self.download_completed.emit(str(download_path))
            else:
                self.download_failed.emit("Download failed")
        except Exception as e:
            self.download_failed.emit(str(e))


class UpdateDialog(QDialog):
    """Dialog for displaying update information and managing updates."""

    def __init__(self, parent=None, current_version: str = "0.0.0"):
        super().__init__(parent)
        self.current_version = current_version
        self.update_info = None
        self.download_path = None

        self.setWindowTitle("S&D - Application Updates")
        self.setModal(True)
        self.resize(600, 500)

        self.setup_ui()
        self.setup_connections()
        self.load_last_check_time()
        # Theme is now handled by global theme manager automatically

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        # Icon (if available)
        try:
            icon_label = QLabel()
            pixmap = QPixmap(":/icons/update.png")
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio))
                header_layout.addWidget(icon_label)
            else:
                # Use text icon as fallback
                icon_label.setText("🔄")
                icon_label.setFont(QFont("Arial", 24))
                header_layout.addWidget(icon_label)
        except Exception:
            # Fallback to text icon
            icon_label = QLabel("🔄")
            icon_label.setFont(QFont("Arial", 24))
            header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel("Application Updates")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Current version info
        version_group = QGroupBox("Current Version")
        version_layout = QFormLayout(version_group)

        self.current_version_label = QLabel(self.current_version)
        version_layout.addRow("Installed Version:", self.current_version_label)

        self.last_check_label = QLabel("Never")
        version_layout.addRow("Last Check:", self.last_check_label)

        layout.addWidget(version_group)

        # Update information
        self.update_group = QGroupBox("Update Information")
        self.update_group.setVisible(False)
        update_layout = QVBoxLayout(self.update_group)

        # Version comparison
        version_compare_layout = QHBoxLayout()
        self.available_version_label = QLabel()
        available_font = QFont()
        available_font.setBold(True)
        self.available_version_label.setFont(available_font)
        version_compare_layout.addWidget(QLabel("Available Version:"))
        version_compare_layout.addWidget(self.available_version_label)
        version_compare_layout.addStretch()
        update_layout.addLayout(version_compare_layout)

        # Release notes
        update_layout.addWidget(QLabel("Release Notes:"))
        self.release_notes = QTextEdit()
        self.release_notes.setMaximumHeight(150)
        self.release_notes.setReadOnly(True)
        update_layout.addWidget(self.release_notes)

        layout.addWidget(self.update_group)

        # Progress
        self.progress_group = QGroupBox("Download Progress")
        self.progress_group.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Ready to download...")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(self.progress_group)

        # Status
        self.status_label = QLabel("Click 'Check for Updates' to begin")
        self.status_label.setStyleSheet(
            f"color: {get_theme_manager().get_color('muted_text')}; font-style: italic;"
        )
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.check_button = QPushButton("Check for Updates")
        self.download_button = QPushButton("Download Update")
        self.install_button = QPushButton("Install Update")
        self.close_button = QPushButton("Close")

        self.download_button.setVisible(False)
        self.install_button.setVisible(False)

        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.install_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def setup_connections(self):
        """Set up signal connections."""
        self.check_button.clicked.connect(self.check_for_updates)
        self.download_button.clicked.connect(self.download_update)
        self.install_button.clicked.connect(self.install_update)
        self.close_button.clicked.connect(self.close)

    def load_last_check_time(self):
        """Load and display the last update check time."""
        try:
            updater = AutoUpdateSystem(self.current_version)
            last_check = updater.get_last_check_time()
            if last_check:
                # Format the datetime as a readable string
                formatted_time = last_check.strftime("%Y-%m-%d %H:%M:%S")
                self.last_check_label.setText(formatted_time)
            else:
                self.last_check_label.setText("Never")
        except Exception as e:
            print(f"Warning: Could not load last check time: {e}")
            self.last_check_label.setText("Never")

    def check_for_updates(self):
        """Start checking for updates."""
        self.status_label.setText("Checking for updates...")
        self.check_button.setEnabled(False)

        # Start update check thread
        self.check_thread = UpdateCheckThread(self.current_version, force_check=True)
        self.check_thread.update_available.connect(self.on_update_available)
        self.check_thread.no_update.connect(self.on_no_update)
        self.check_thread.error_occurred.connect(self.on_check_error)
        self.check_thread.start()

    def on_update_available(self, update_info):
        """Handle when an update is available."""
        self.update_info = update_info

        # Update UI
        self.available_version_label.setText(f"v{update_info['latest_version']}")
        self.release_notes.setPlainText(
            update_info.get("release_notes", "No release notes available")
        )

        self.update_group.setVisible(True)
        self.download_button.setVisible(True)

        self.status_label.setText(f"Update available: v{update_info['latest_version']}")
        self.status_label.setStyleSheet(
            f"color: {get_theme_manager().get_color('success')}; font-weight: bold;"
        )

        self.check_button.setEnabled(True)
        self.check_button.setText("Check Again")

        # Update last check time
        self.load_last_check_time()

    def on_no_update(self):
        """Handle when no update is available."""
        self.status_label.setText("Your application is up to date!")
        self.status_label.setStyleSheet(f"color: {get_theme_manager().get_color('success')};")
        self.check_button.setEnabled(True)
        self.check_button.setText("Check Again")

        # Update last check time
        self.load_last_check_time()

    def on_check_error(self, error_message):
        """Handle errors during update check."""
        self.status_label.setText(f"Error checking for updates: {error_message}")
        self.status_label.setStyleSheet(f"color: {get_theme_manager().get_color('error')};")
        self.check_button.setEnabled(True)

        # Update last check time even on error (since we did attempt to check)
        self.load_last_check_time()

    def download_update(self):
        """Start downloading the update."""
        if not self.update_info:
            return

        download_url = self.update_info.get("download_url")
        if not download_url:
            QMessageBox.warning(self, "Error", "No download URL available")
            return

        # Show progress
        self.progress_group.setVisible(True)
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting download...")

        # Start download thread
        self.download_thread = UpdateDownloadThread(self.current_version, download_url)
        self.download_thread.progress_updated.connect(self.on_download_progress)
        self.download_thread.download_completed.connect(self.on_download_completed)
        self.download_thread.download_failed.connect(self.on_download_failed)
        self.download_thread.start()

    def on_download_progress(self, percent):
        """Update download progress."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"Downloading... {percent}%")

    def on_download_completed(self, download_path):
        """Handle successful download completion."""
        self.download_path = download_path
        self.progress_label.setText("Download completed!")
        self.install_button.setVisible(True)
        self.status_label.setText("Update downloaded. Ready to install.")
        self.status_label.setStyleSheet(f"color: {get_theme_manager().get_color('success')};")

    def on_download_failed(self, error_message):
        """Handle download failure."""
        self.progress_label.setText(f"Download failed: {error_message}")
        self.download_button.setEnabled(True)
        self.status_label.setText("Download failed. Please try again.")
        self.status_label.setStyleSheet(f"color: {get_theme_manager().get_color('error')};")

    def install_update(self):
        """Install the downloaded update."""
        if not self.download_path:
            return

        # Confirm installation
        reply = QMessageBox.question(
            self,
            "Install Update",
            "This will install the update and restart the application. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                updater = AutoUpdateSystem(self.current_version)

                self.status_label.setText("Installing update...")
                self.install_button.setEnabled(False)

                # Apply update
                success = updater.apply_update(Path(self.download_path))

                if success:
                    # Use themed message box if parent has it
                    if hasattr(self.parent(), "show_themed_message_box"):
                        self.parent().show_themed_message_box(
                            "information",
                            "Update Installed",
                            "Update installed successfully! The application will restart now.",
                        )
                    else:
                        QMessageBox.information(
                            self,
                            "Update Installed",
                            "Update installed successfully! The application will restart now.",
                        )
                    updater.restart_application()
                else:
                    if hasattr(self.parent(), "show_themed_message_box"):
                        self.parent().show_themed_message_box(
                            "critical",
                            "Installation Failed",
                            "Failed to install the update. Please try again or install manually.",
                        )
                    else:
                        QMessageBox.critical(
                            self,
                            "Installation Failed",
                            "Failed to install the update. Please try again or install manually.",
                        )
                    self.install_button.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Installation Error",
                    f"An error occurred during installation: {e!s}",
                )
                self.install_button.setEnabled(True)


class UpdateSettingsWidget:
    """Widget for auto-update settings (to be integrated into main settings)."""

    def __init__(self, parent_widget, current_version: str):
        self.parent = parent_widget
        self.current_version = current_version
        self.updater = AutoUpdateSystem(current_version)

    def create_settings_widgets(self):
        """Create and return auto-update settings widgets."""
        # Auto-update group
        update_group = QGroupBox("Auto-Update Settings")
        layout = QFormLayout(update_group)

        # Enable auto-check
        self.auto_check_cb = QCheckBox("Automatically check for updates")
        layout.addRow(self.auto_check_cb)

        # Check interval
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 30)
        self.check_interval_spin.setSuffix(" days")
        layout.addRow("Check interval:", self.check_interval_spin)

        # Auto-download
        self.auto_download_cb = QCheckBox("Automatically download updates")
        layout.addRow(self.auto_download_cb)

        # Auto-install (not recommended for security apps)
        self.auto_install_cb = QCheckBox("Automatically install updates")
        self.auto_install_cb.setToolTip("Not recommended for security applications")
        layout.addRow(self.auto_install_cb)

        # Manual check button
        check_now_btn = QPushButton("Check for Updates Now")
        check_now_btn.clicked.connect(self.open_update_dialog)
        layout.addRow(check_now_btn)

        # Load current settings
        self.load_settings()

        return update_group

    def load_settings(self):
        """Load current auto-update settings."""
        settings = self.updater.get_update_settings()

        self.auto_check_cb.setChecked(settings.get("auto_check", True))
        self.check_interval_spin.setValue(settings.get("check_interval_days", 1))
        self.auto_download_cb.setChecked(settings.get("auto_download", False))
        self.auto_install_cb.setChecked(settings.get("auto_install", False))

    def save_settings(self):
        """Save auto-update settings."""
        settings = {
            "auto_check": self.auto_check_cb.isChecked(),
            "check_interval_days": self.check_interval_spin.value(),
            "auto_download": self.auto_download_cb.isChecked(),
            "auto_install": self.auto_install_cb.isChecked(),
        }

        self.updater.save_update_settings(settings)

    def open_update_dialog(self):
        """Open the update dialog."""
        dialog = UpdateDialog(self.parent, self.current_version)
        dialog.exec()


# Notification system for background update checks
class UpdateNotifier:
    """Handles background update notifications."""

    def __init__(self, main_window, current_version: str):
        self.main_window = main_window
        self.current_version = current_version
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_updates_background)

        # Check every 6 hours for updates
        self.timer.start(6 * 60 * 60 * 1000)  # 6 hours in milliseconds

    def check_for_updates_background(self):
        """Check for updates in the background using QThread."""
        try:
            # Create background worker thread

            class BackgroundUpdateChecker(QThread):
                update_found = pyqtSignal(dict)
                error_occurred = pyqtSignal(str)

                def __init__(self, main_window):
                    super().__init__()
                    self.main_window = main_window

                def run(self):
                    try:
                        # Check for updates using the auto-updater
                        if (
                            hasattr(self.main_window, "auto_updater")
                            and self.main_window.auto_updater
                        ):
                            update_info = self.main_window.auto_updater.check_for_updates_sync()
                            if update_info and update_info.get("available", False):
                                self.update_found.emit(update_info)
                    except Exception as e:
                        self.error_occurred.emit(str(e))

            # Create and start the worker thread
            self.background_checker = BackgroundUpdateChecker(self.main_window)
            self.background_checker.update_found.connect(self.notify_update_available)
            self.background_checker.error_occurred.connect(
                lambda err: self.logger.error(f"Background update check failed: {err}")
            )
            self.background_checker.start()

        except Exception as e:
            self.logger.error(f"Failed to start background update check: {e}")
            # Fallback to no-op if threading fails
            return

    def notify_update_available(self, update_info):
        """Notify user that an update is available."""
        if hasattr(self.main_window, "tray_icon") and self.main_window.tray_icon:
            # Show system tray notification
            self.main_window.tray_icon.showMessage(
                "Update Available",
                f"S&D v{update_info['latest_version']} is available. Click to update.",
                2,  # Information icon
                5000,  # 5 seconds
            )

            # You could also add the update option to the tray menu
            # or show a non-modal notification in the main window
