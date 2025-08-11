#!/usr/bin/env python3
"""
Update dialog for S&D - Search & Destroy
Handles app update notifications and user interaction
"""

import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon


class UpdateDownloadThread(QThread):
    """Thread for downloading updates in the background."""
    
    progress_updated = pyqtSignal(int)  # Progress percentage
    status_updated = pyqtSignal(str)    # Status message
    download_completed = pyqtSignal(bool, str)  # Success, message
    
    def __init__(self, updater, update_info):
        super().__init__()
        self.updater = updater
        self.update_info = update_info
        
    def run(self):
        """Download and apply the update."""
        try:
            self.status_updated.emit("Downloading update...")
            
            # Download the update
            success = self.updater.download_update(
                self.update_info,
                progress_callback=self.progress_updated.emit,
                status_callback=self.status_updated.emit
            )
            
            if success:
                self.status_updated.emit("Installing update...")
                self.progress_updated.emit(90)
                
                # Apply the update
                install_success = self.updater.apply_update()
                
                if install_success:
                    self.progress_updated.emit(100)
                    self.download_completed.emit(True, "Update installed successfully! Please restart the application.")
                else:
                    self.download_completed.emit(False, "Failed to install update.")
            else:
                self.download_completed.emit(False, "Failed to download update.")
                
        except Exception as e:
            self.download_completed.emit(False, f"Update failed: {str(e)}")


class UpdateDialog(QDialog):
    """Dialog for displaying update information and managing updates."""
    
    def __init__(self, parent=None, update_info=None, updater=None):
        super().__init__(parent)
        self.update_info = update_info
        self.updater = updater
        self.download_thread = None
        
        self.setWindowTitle("S&D - Application Update Available")
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        # Apply theme if parent has one
        if parent and hasattr(parent, 'current_theme'):
            self.apply_theme(parent.current_theme)
        else:
            # Default to dark theme if no parent theme attribute
            self.apply_theme('dark')
            
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🔄 Application Update Available")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Version info
        if self.update_info:
            current_version = self.update_info.get('current_version', 'Unknown')
            new_version = self.update_info.get('version', 'Unknown')
            
            version_label = QLabel(f"Current version: {current_version} → New version: {new_version}")
            version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(version_label)
            
        layout.addWidget(header_frame)
        
        # Release notes section
        if self.update_info and self.update_info.get('body'):
            notes_label = QLabel("📋 Release Notes:")
            notes_font = QFont()
            notes_font.setBold(True)
            notes_label.setFont(notes_font)
            layout.addWidget(notes_label)
            
            # Scrollable release notes
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setMaximumHeight(200)
            
            notes_text = QTextEdit()
            notes_text.setPlainText(self.update_info['body'])
            notes_text.setReadOnly(True)
            scroll_area.setWidget(notes_text)
            layout.addWidget(scroll_area)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label (initially hidden)
        self.status_label = QLabel()
        self.status_label.setVisible(False)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # View on GitHub button
        self.github_button = QPushButton("🌐 View on GitHub")
        self.github_button.clicked.connect(self.open_github_release)
        button_layout.addWidget(self.github_button)
        
        # Download and install button
        self.install_button = QPushButton("⬇️ Download & Install")
        self.install_button.clicked.connect(self.start_download)
        self.install_button.setDefault(True)
        button_layout.addWidget(self.install_button)
        
        # Remind later button
        self.later_button = QPushButton("⏰ Remind Later")
        self.later_button.clicked.connect(self.remind_later)
        button_layout.addWidget(self.later_button)
        
        # Skip version button
        self.skip_button = QPushButton("⏭️ Skip Version")
        self.skip_button.clicked.connect(self.skip_version)
        button_layout.addWidget(self.skip_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def apply_theme(self, theme):
        """Apply the application theme to the dialog."""
        if theme == "dark":
            self.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
                QTextEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QProgressBar {
                    border: 1px solid #555555;
                    background-color: #3c3c3c;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                }
                QScrollArea {
                    border: 1px solid #555555;
                }
            """)
        elif theme == "light":
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #000000;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    background-color: #f0f0f0;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                }
                QScrollArea {
                    border: 1px solid #cccccc;
                }
            """)
            
    def open_github_release(self):
        """Open the GitHub release page in the default browser."""
        if self.update_info and self.update_info.get('html_url'):
            webbrowser.open(self.update_info['html_url'])
            
    def start_download(self):
        """Start downloading and installing the update."""
        if not self.updater or not self.update_info:
            return
            
        # Show progress UI
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Disable buttons during download
        self.install_button.setEnabled(False)
        self.later_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        
        # Start download thread
        self.download_thread = UpdateDownloadThread(self.updater, self.update_info)
        self.download_thread.progress_updated.connect(self.progress_bar.setValue)
        self.download_thread.status_updated.connect(self.status_label.setText)
        self.download_thread.download_completed.connect(self.download_finished)
        self.download_thread.start()
        
    def download_finished(self, success, message):
        """Handle download completion."""
        self.status_label.setText(message)
        
        # Re-enable buttons
        self.install_button.setEnabled(True)
        self.later_button.setEnabled(True)
        self.skip_button.setEnabled(True)
        
        if success:
            # Change install button to restart button
            self.install_button.setText("🔄 Restart Application")
            self.install_button.clicked.disconnect()
            self.install_button.clicked.connect(self.restart_application)
        else:
            # Reset progress bar on failure
            self.progress_bar.setValue(0)
            
    def restart_application(self):
        """Restart the application to apply updates."""
        try:
            import sys
            import subprocess
            import os
            
            # Get the current script path
            script_path = sys.argv[0]
            
            # Close the dialog and main application
            self.accept()
            
            # Restart the application
            if hasattr(sys, 'frozen'):
                # Running as executable
                subprocess.Popen([sys.executable] + sys.argv)
            else:
                # Running as script
                subprocess.Popen([sys.executable, script_path])
                
            # Exit current instance
            sys.exit(0)
            
        except Exception as e:
            self.status_label.setText(f"Failed to restart application: {str(e)}")
            
    def remind_later(self):
        """Remind about the update later."""
        # Save reminder preference
        if self.updater:
            self.updater.set_reminder_later(self.update_info.get('version'))
        self.reject()
        
    def skip_version(self):
        """Skip this version permanently."""
        # Save skip preference
        if self.updater:
            self.updater.skip_version(self.update_info.get('version'))
        self.reject()
        
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop download thread if running
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait(3000)  # Wait up to 3 seconds
        event.accept()
