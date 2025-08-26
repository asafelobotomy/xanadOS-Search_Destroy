#!/usr/bin/env python3
"""
Setup Wizard for xanadOS Search & Destroy
First-time setup experience for installing and configuring required packages.

Notes
-----
- This module is large due to UI/widget definitions and styling consolidated in one place.
    A future refactor can split it, but for now we prefer stability over risky changes.
"""

# pylint: disable=too-many-lines  # UI-heavy module; tracked for later decomposition

import subprocess
import sys
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtGui import QFont  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
    QCheckBox,
    QProgressBar,
)
from app.utils.config import load_config, save_config

# Import theming support
try:
    from app.gui.theme_manager import get_theme_manager
    from app.gui.themed_widgets import ThemedDialog
    from app.core.elevated_runner import (
        elevated_run,
    )  # pylint: disable=import-outside-toplevel
    from app.core.rkhunter_monitor_non_invasive import (
        rkhunter_monitor,
    )  # pylint: disable=import-outside-toplevel

    THEMING_AVAILABLE = True
except ImportError:
    THEMING_AVAILABLE = False
    ThemedDialog = QDialog

    def get_theme_manager():
        """Fallback theme manager getter when theming is unavailable."""
        return None


@dataclass
class PackageInfo:  # pylint: disable=too-many-instance-attributes
    """Information about a required package"""

    name: str
    display_name: str
    description: str
    purpose: str
    install_commands: Dict[str, str]  # distro -> command
    check_command: str
    service_name: Optional[str] = None
    post_install_commands: Optional[List[str]] = None
    is_critical: bool = True


class InstallationWorker(QThread):  # pylint: disable=too-many-instance-attributes
    """Worker thread for package installation.

    Handles elevated installs, post-install steps, and service start.
    Many attributes are inherent to the worker lifecycle (progress, outputs, etc.).
    """

    progress_updated = pyqtSignal(str, int)  # message, progress
    installation_finished = pyqtSignal(str, bool)  # package_name, success
    output_updated = pyqtSignal(str)

    def __init__(self, package_info: PackageInfo, distro: str):
        """Initialize the worker with package metadata and target distro."""
        super().__init__()
        self.package_info = package_info
        self.distro = distro
        self.should_stop = False

    def run(self):  # pylint: disable=too-many-branches,too-many-statements,R1702
        """Run the installation process."""
        # pylint: disable=too-many-nested-blocks
        # Justification: This method orchestrates a multi-step install with
        # guarded flows (auth/UI/process/service). Splitting further risks user-visible
        # regressions; nesting is acceptable at this UI boundary.
        try:
            # Get installation command for this distribution
            if self.distro not in self.package_info.install_commands:
                self.output_updated.emit(
                    f"ERROR: No installation command available for {self.distro}"
                )
                self.installation_finished.emit(self.package_info.name, False)
                return

            install_cmd = self.package_info.install_commands[self.distro]

            # Update progress
            self.progress_updated.emit(f"Installing {self.package_info.display_name}...", 25)
            self.output_updated.emit(f"Running: {install_cmd}")

            success = False

            try:
                # Use elevated_run for package installation with GUI authentication

                # Parse the command properly for elevated execution
                if install_cmd.startswith("pkexec sh -c"):
                    # Extract shell command from pkexec wrapper
                    shell_cmd = install_cmd.split('"')[1]  # Extract the command between quotes
                    # Execute using shell with elevated_run
                    install_result = elevated_run(
                        ["sh", "-c", shell_cmd],
                        timeout=600,  # 10 minute timeout for package installation
                        capture_output=True,
                        text=True,
                        gui=True,
                    )
                else:
                    # Handle simple commands - remove any pkexec prefix
                    cmd_parts = install_cmd.split()
                    if cmd_parts[0] == "pkexec":
                        cmd_parts = cmd_parts[1:]  # Remove pkexec prefix

                    install_result = elevated_run(
                        cmd_parts, timeout=600, capture_output=True, text=True, gui=True
                    )

                # Output both stdout and stderr
                if install_result.stdout:
                    for line in install_result.stdout.split("\n"):
                        if line.strip():
                            self.output_updated.emit(line.strip())

                if install_result.stderr:
                    for line in install_result.stderr.split("\n"):
                        if line.strip():
                            self.output_updated.emit(f"ERROR: {line.strip()}")

                success = install_result.returncode == 0
                if not success:
                    self.output_updated.emit(
                        f"Command failed with exit code: {install_result.returncode}"
                    )

            except subprocess.TimeoutExpired:
                self.output_updated.emit("Command timed out after 10 minutes")
                success = False
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.output_updated.emit(f"Error running command: {e}")
                success = False

            if success:
                self.progress_updated.emit(f"Configuring {self.package_info.display_name}...", 75)

                # Run post-installation commands if any
                if self.package_info.post_install_commands:
                    for cmd in self.package_info.post_install_commands:
                        self.output_updated.emit(f"Running: {cmd}")
                        try:
                            post_result = subprocess.run(
                                cmd.split(), capture_output=True, text=True, check=False
                            )
                            if post_result.returncode != 0 and post_result.stderr:
                                self.output_updated.emit(
                                    f"Post-install warning: {post_result.stderr}"
                                )
                        except (OSError, subprocess.SubprocessError, ValueError) as e:
                            self.output_updated.emit(f"Post-install error: {e}")

                # Start service if specified
                if self.package_info.service_name:
                    try:
                        self.output_updated.emit(
                            f"Starting service: {self.package_info.service_name}"
                        )
                        service_result = elevated_run(
                            [
                                "systemctl",
                                "enable",
                                "--now",
                                self.package_info.service_name,
                            ],
                            timeout=60,
                            capture_output=True,
                            text=True,
                            gui=True,
                        )
                        if service_result.returncode == 0:
                            self.output_updated.emit(
                                f"Started {self.package_info.service_name} service"
                            )
                        else:
                            # Ensure clean formatting of stderr output
                            self.output_updated.emit(
                                f"Note: Could not start service: {service_result.stderr}"
                            )
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        # elevated_run can surface diverse OS/auth/Qt errors; keep UX stable
                        self.output_updated.emit(f"Note: Could not start service: {e}")

                self.progress_updated.emit(
                    f"{self.package_info.display_name} installed successfully!", 100
                )
            else:
                self.output_updated.emit("Installation failed!")

            self.installation_finished.emit(self.package_info.name, success)

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.output_updated.emit(f"Error during installation: {str(e)}")
            self.installation_finished.emit(self.package_info.name, False)

    def stop(self):
        """Stop the installation process"""
        self.should_stop = True


class PackageCard(QFrame):
    """Widget representing a single package with install option"""

    def __init__(self, package_info: PackageInfo, is_installed: bool):
        super().__init__()
        self.package_info = package_info
        self.is_installed = is_installed
        self.install_requested = False

        self.setFrameStyle(QFrame.Shape.Box)
        self.setObjectName("package_card")  # For CSS styling

        self.setup_ui()

    def setup_ui(self):
        """Setup the card UI"""
        layout = QVBoxLayout()

        # Header with name and status
        header_layout = QHBoxLayout()

        # Package name
        name_label = QLabel(self.package_info.display_name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(14)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)

        # Status indicator
        status_label = QLabel()
        if self.is_installed:
            status_label.setText("✅ Installed")
            status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            status_label.setText("❌ Not Available")
            status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

        header_layout.addStretch()
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)

        # Description
        desc_label = QLabel(self.package_info.description)
        desc_label.setObjectName("description_label")  # For CSS styling
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Purpose
        purpose_label = QLabel(f"Purpose: {self.package_info.purpose}")
        purpose_label.setObjectName("purpose_label")  # For CSS styling
        purpose_label.setWordWrap(True)
        layout.addWidget(purpose_label)

        # Install checkbox (only if not installed)
        if not self.is_installed:
            self.install_checkbox = QCheckBox(f"Install {self.package_info.display_name}")
            if self.package_info.is_critical:
                self.install_checkbox.setChecked(True)
                self.install_checkbox.setText(
                    f"Install {self.package_info.display_name} (Recommended)"
                )
            self.install_checkbox.stateChanged.connect(self.on_install_toggled)
            layout.addWidget(self.install_checkbox)

        self.setLayout(layout)

    def on_install_toggled(self, state):
        """Handle install checkbox toggle"""
        self.install_requested = state == Qt.CheckState.Checked.value

    def should_install(self) -> bool:
        """Check if this package should be installed"""
        return (
            not self.is_installed
            and hasattr(self, "install_checkbox")
            and self.install_checkbox.isChecked()
        )


class SetupWizard(ThemedDialog):  # pylint: disable=too-many-instance-attributes
    """Main setup wizard dialog."""

    def __init__(self, parent=None):
        """Build the wizard UI, detect distro, and prepare package catalog."""
        super().__init__(parent)
        self.setWindowTitle("S&D - First Time Setup")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)

        # Apply proper theming using theme manager
        self.apply_theme_manager_styling()

        # Package definitions
        self.packages = {
            "clamav": PackageInfo(
                name="clamav",
                display_name="ClamAV Antivirus",
                description=(
                    "Open-source antivirus engine for detecting trojans, viruses, "
                    "malware & other malicious threats."
                ),
                purpose=("Core virus scanning and real-time protection capabilities"),
                install_commands={
                    "arch": (
                        'sh -c "rm -f /var/lib/pacman/db.lck && pacman -S --noconfirm clamav"'
                    ),
                    "ubuntu": ('sh -c "apt update && apt install -y clamav clamav-daemon"'),
                    "debian": ('sh -c "apt update && apt install -y clamav clamav-daemon"'),
                    "fedora": "dnf install -y clamav clamav-update",
                    "opensuse": "zypper install -y clamav",
                },
                check_command="clamscan --version",
                service_name="clamav-daemon",
                post_install_commands=["freshclam"],
                is_critical=True,
            ),
            "ufw": PackageInfo(
                name="ufw",
                display_name="UFW Firewall",
                description=(
                    "Uncomplicated Firewall (UFW) provides a user-friendly interface "
                    "for managing iptables firewall rules."
                ),
                purpose="Network security and firewall management",
                install_commands={
                    "arch": ('sh -c "rm -f /var/lib/pacman/db.lck && pacman -S --noconfirm ufw"'),
                    "ubuntu": 'sh -c "apt update && apt install -y ufw"',
                    "debian": 'sh -c "apt update && apt install -y ufw"',
                    "fedora": "dnf install -y ufw",
                    "opensuse": "zypper install -y ufw",
                },
                check_command="ufw --version",
                service_name="ufw",
                post_install_commands=["ufw --force enable"],
                is_critical=False,
            ),
            "rkhunter": PackageInfo(
                name="rkhunter",
                display_name="RKHunter",
                description=(
                    "Rootkit Hunter scans for rootkits, backdoors, and possible "
                    "local exploits on your system."
                ),
                purpose=("Advanced rootkit detection and system integrity checking"),
                install_commands={
                    "arch": (
                        'sh -c "rm -f /var/lib/pacman/db.lck && pacman -S --noconfirm rkhunter"'
                    ),
                    "ubuntu": 'sh -c "apt update && apt install -y rkhunter"',
                    "debian": 'sh -c "apt update && apt install -y rkhunter"',
                    "fedora": "dnf install -y rkhunter",
                    "opensuse": "zypper install -y rkhunter",
                },
                check_command="rkhunter --version",
                post_install_commands=[
                    'sh -c "chmod 755 /usr/bin/rkhunter"',
                    "/usr/bin/rkhunter --update",
                    "/usr/bin/rkhunter --propupd",
                ],
                is_critical=False,
            ),
        }

        self.distro = self.detect_distribution()
        self.package_status = self.check_package_availability()
        self.installation_workers = {}

        # Predefine attributes created later to satisfy Pylint
        self.package_cards = {}
        self.skip_button = None
        self.install_button = None
        self.installation_dialog = None

        self.setup_ui()
        self.check_if_setup_needed()

    def apply_theme_manager_styling(self):
        """Apply theming using the application's theme manager."""
        if not THEMING_AVAILABLE:
            return

        try:
            theme_manager = get_theme_manager()
            if theme_manager:
                # Get theme colors
                bg_color = theme_manager.get_color("elevated_bg")
                primary_text = theme_manager.get_color("primary_text")
                secondary_text = theme_manager.get_color("secondary_text")
                muted_text = theme_manager.get_color("muted_text")
                theme_manager.get_color("accent_text")

                secondary_bg = theme_manager.get_color("secondary_bg")
                card_bg = theme_manager.get_color("card_bg")
                header_bg = theme_manager.get_color("header_bg")
                header_text = theme_manager.get_color("header_text")
                accent_color = theme_manager.get_color("strawberry_primary")
                success_color = theme_manager.get_color("strawberry_sage")
                border_color = theme_manager.get_color("border")
                border_light = theme_manager.get_color("border_light")

                # Apply comprehensive styling with proper text hierarchy
                self.setStyleSheet(
                    f"""
                    QDialog {{
                        background-color: {bg_color};
                        color: {primary_text};
                    }}

                    QLabel {{
                        color: {primary_text};
                        background: transparent;
                    }}

                    /* Secondary text for descriptions */
                    QLabel[objectName="description_label"] {{
                        color: {secondary_text};
                        background: transparent;
                    }}

                    /* Muted text for purpose/hints */
                    QLabel[objectName="purpose_label"] {{
                        color: {muted_text};
                        background: transparent;
                        font-style: italic;
                    }}

                    /* Distribution info */
                    QLabel[objectName="distro_info"] {{
                        color: {secondary_text};
                        background: transparent;
                        font-weight: bold;
                    }}

                    /* Instructions text */
                    QLabel[objectName="instructions"] {{
                        color: {secondary_text};
                        background: transparent;
                    }}

                    QPushButton {{
                        background-color: {secondary_bg};
                        border: 1px solid {border_color};
                        color: {primary_text};
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                        min-height: 20px;
                    }}

                    QPushButton:hover {{
                        background-color: {accent_color};
                        color: {header_text};
                    }}

                    QPushButton:pressed {{
                        background-color: {accent_color};
                        border: 2px solid {accent_color};
                    }}

                    QPushButton#install_button {{
                        background-color: {success_color};
                        border: 1px solid {success_color};
                        color: {header_text};
                    }}

                    QPushButton#install_button:hover {{
                        background-color: {success_color};
                        border: 2px solid {success_color};
                    }}

                    QTextEdit {{
                        background-color: {card_bg};
                        color: {primary_text};
                        border: 1px solid {border_light};
                        selection-background-color: {accent_color};
                    }}

                    QTabWidget::pane {{
                        border: 1px solid {border_light};
                        background-color: {bg_color};
                        border-radius: 4px;
                    }}

                    QTabBar::tab {{
                        background-color: {card_bg};
                        color: {primary_text};
                        padding: 8px 16px;
                        margin: 2px;
                        border-radius: 4px;
                        border: 1px solid {border_light};
                    }}

                    QTabBar::tab:selected {{
                        background-color: {header_bg};
                        color: {header_text};
                        border: 1px solid {header_bg};
                    }}

                    QTabBar::tab:hover {{
                        background-color: {secondary_bg};
                    }}

                    /* Remove general QFrame border - only package cards should have borders */
                    QFrame {{
                        background-color: {card_bg};
                        border: none;
                        border-radius: 8px;
                    }}

                    QScrollArea {{
                        background-color: {bg_color};
                        border: none;
                    }}

                    QScrollArea > QWidget > QWidget {{
                        background-color: {bg_color};
                    }}

                    QCheckBox {{
                        color: {primary_text};
                        spacing: 8px;
                    }}

                    QCheckBox::indicator {{
                        width: 18px;
                        height: 18px;
                        border: 2px solid {border_light};
                        border-radius: 3px;
                        background-color: {card_bg};
                    }}

                    QCheckBox::indicator:checked {{
                        background-color: {success_color};
                        border-color: {success_color};
                        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAxNCAxNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTExLjY2NjcgMy41TDUuMjUgOS45MTY2N0wyLjMzMzMzIDciIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                    }}

                    QProgressBar {{
                        border: 1px solid {border_light};
                        border-radius: 4px;
                        text-align: center;
                        background-color: {card_bg};
                        color: {primary_text};
                    }}

                    QProgressBar::chunk {{
                        background-color: {success_color};
                        border-radius: 3px;
                    }}

                    QFrame#welcome_header {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 {header_bg}, stop:1 {accent_color});
                        border-radius: 10px;
                        margin: 5px;
                        border: none;
                    }}

                    QLabel#welcome_title, QLabel#welcome_subtitle {{
                        color: {header_text};
                        background: transparent;
                        border: none;
                    }}

                    QFrame#package_card {{
                        border: 2px solid {border_color};
                        border-radius: 8px;
                        background-color: {card_bg};
                        margin: 5px;
                        padding: 10px;
                    }}

                    QFrame#package_card:hover {{
                        border-color: {header_bg};
                        background-color: {secondary_bg};
                    }}
                """
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Warning: Could not apply theme manager styling: {e}")
            # Fallback to basic dark theme
            self.apply_fallback_styling()

    def apply_fallback_styling(self):
        """Apply fallback styling if theme manager is not available."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
            }
            QFrame {
                background-color: #353535;
                border: none;
                border-radius: 8px;
            }
            QFrame#package_card {
                border: 2px solid #555555;
                border-radius: 8px;
                background-color: #353535;
                margin: 5px;
                padding: 10px;
            }
        """
        )

    def detect_distribution(self) -> str:
        """Detect the Linux distribution."""
        try:
            # Try to read os-release file
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                content = f.read().lower()

            detected = "unknown"
            if "arch" in content:
                detected = "arch"
            elif "ubuntu" in content:
                detected = "ubuntu"
            elif "debian" in content:
                detected = "debian"
            elif "fedora" in content:
                detected = "fedora"
            elif "opensuse" in content or "suse" in content:
                detected = "opensuse"
            return detected
        except OSError:
            return "unknown"

    def check_package_availability(self) -> Dict[str, bool]:
        """Check which packages are already installed"""
        status = {}

        for package_name, package_info in self.packages.items():
            try:
                check_result = subprocess.run(
                    package_info.check_command.split(), capture_output=True, timeout=5, check=False
                )
                status[package_name] = check_result.returncode == 0
            except (OSError, subprocess.SubprocessError, ValueError):
                status[package_name] = False

        return status

    def check_if_setup_needed(self) -> bool:
        """Check if setup is needed (any critical packages missing)"""
        critical_missing = any(
            not self.package_status.get(name, False)
            for name, info in self.packages.items()
            if info.is_critical
        )

        if not critical_missing:
            # All critical packages available, offer to skip setup
            reply = QMessageBox.question(
                self,
                "Setup Complete",
                "All critical components are already installed!\n\n"
                "Would you like to review the setup anyway or continue to the application?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                self.accept()
                return False

        return True

    def setup_ui(self):
        """Setup the wizard UI."""
        layout = QVBoxLayout()

        # Welcome header
        self.create_welcome_header(layout)

        # Tab widget for different setup sections
        tab_widget = QTabWidget()

        # Package installation tab
        self.create_package_tab(tab_widget)

        # Python dependencies tab (optional features)
        self.create_python_deps_tab(tab_widget)

        # Information tab
        self.create_info_tab(tab_widget)

        layout.addWidget(tab_widget)

        # Action buttons
        self.create_action_buttons(layout)

        self.setLayout(layout)

    def _detect_python_dep(self, module_name: str) -> bool:
        """Return True if importable in current environment."""
        try:
            __import__(module_name)
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _pip_install_user(self, package: str) -> tuple[bool, str]:
        """Attempt pip --user install for a package; return (success, output)."""
        try:
            # Prefer running pip as a module of current interpreter
            cmd = [sys.executable, "-m", "pip", "install", "--user", package]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=900)
            output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
            return result.returncode == 0, output.strip()
        except Exception as e:  # pylint: disable=broad-exception-caught
            return False, str(e)

    def create_python_deps_tab(self, tab_widget):  # pylint: disable=too-many-locals
        """Create an optional Python dependencies installer tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Optional Python Features")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        title.setFont(font)
        layout.addWidget(title)

        desc = QLabel(
            "Install optional Python packages to enable scheduling and enhanced file watching.\n"
            "These install to your user site (no root). For system-wide installs, use your distro packages."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Catalog of optional Python deps
        py_deps = [
            ("schedule", "Task scheduling for background scans"),
            ("inotify", "Linux inotify helpers (alt: watchdog)"),
            ("watchdog", "Cross-platform file system watching"),
        ]

        # Status area
        status_box = QTextEdit()
        status_box.setReadOnly(True)
        status_box.setMinimumHeight(140)

        cards = []
        for name, purpose in py_deps:
            row = QHBoxLayout()
            chk = QCheckBox(f"Install {name}")
            installed = self._detect_python_dep(name)
            lbl = QLabel("✅ Installed" if installed else "❌ Not Installed")
            lbl.setStyleSheet("color: #27ae60;" if installed else "color: #e74c3c;")
            row.addWidget(QLabel(f"{name}: {purpose}"))
            row.addStretch(1)
            row.addWidget(lbl)
            if not installed:
                row.addWidget(chk)
            layout.addLayout(row)
            cards.append((name, chk if not installed else None, lbl))

        def do_install():  # noqa: D401 - small inline handler
            installed_any = False
            for name, chk, lbl in cards:
                if chk is None or not chk.isChecked():
                    continue
                ok, out = self._pip_install_user(name)
                status_box.append(f"$ pip install --user {name}\n{out}\n")
                if ok:
                    lbl.setText("✅ Installed")
                    lbl.setStyleSheet("color: #27ae60;")
                    installed_any = True
            if installed_any:
                QMessageBox.information(
                    self,
                    "Python packages installed",
                    "Optional Python dependencies installed. Some features may require app restart.",
                )

        btn_install = QPushButton("Install Selected (pip --user)")
        btn_install.clicked.connect(do_install)
        layout.addWidget(btn_install)
        layout.addWidget(status_box)

        # Distro help
        help_lbl = QLabel(
            "Prefer system packages? Example commands:\n"
            "Ubuntu/Debian: sudo apt install python3-schedule python3-watchdog\n"
            "Fedora: sudo dnf install python3-schedule python3-watchdog\n"
            "Arch: sudo pacman -S python-schedule python-watchdog"
        )
        help_lbl.setWordWrap(True)
        layout.addWidget(help_lbl)

        widget.setLayout(layout)
        tab_widget.addTab(widget, "🐍 Python Dependencies")

    def create_welcome_header(self, layout):
        """Create welcome header section."""
        header_frame = QFrame()
        header_frame.setObjectName("welcome_header")  # For CSS styling

        header_layout = QVBoxLayout()

        # Title
        title = QLabel("Welcome to S&D - Search & Destroy")
        title.setObjectName("welcome_title")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Let's set up your system security components")
        subtitle.setObjectName("welcome_subtitle")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def create_package_tab(self, tab_widget):
        """Create the package installation tab."""
        package_widget = QWidget()
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "The following security components will enhance your system protection. "
            "Critical components are pre-selected, while optional components can "
            "improve security further."
        )
        instructions.setObjectName("instructions")  # For CSS styling
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Distribution info
        distro_info = QLabel(f"Detected distribution: {self.distro.title()}")
        distro_info.setObjectName("distro_info")  # For CSS styling
        layout.addWidget(distro_info)

        # Scroll area for package cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        cards_widget = QWidget()
        cards_layout = QVBoxLayout()

        # Create package cards
        self.package_cards = {}
        for package_name, package_info in self.packages.items():
            is_installed = self.package_status.get(package_name, False)
            card = PackageCard(package_info, is_installed)
            self.package_cards[package_name] = card
            cards_layout.addWidget(card)

        cards_layout.addStretch()
        cards_widget.setLayout(cards_layout)
        scroll.setWidget(cards_widget)
        layout.addWidget(scroll)

        package_widget.setLayout(layout)
        tab_widget.addTab(package_widget, "📦 Package Installation")

    def create_info_tab(self, tab_widget):
        """Create the information/education tab."""
        info_widget = QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("About S&D Components")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        layout.addWidget(title)

        # Information text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        # Long HTML content; wrapping would hurt readability. Safe to suppress line length here.
        # pylint: disable=line-too-long
        info_text.setHtml(
            """
        <h3>🛡️ Security Layer Overview</h3>
        <p>S&D - Search & Destroy creates a comprehensive security ecosystem using multiple specialized tools:</p>

        <h4>🦠 ClamAV Antivirus (Critical)</h4>
        <ul>
            <li><b>Real-time Protection:</b> Monitors file access and prevents malicious files from executing</li>
            <li><b>Signature-based Detection:</b> Uses regularly updated virus definitions to identify known threats</li>
            <li><b>Heuristic Analysis:</b> Detects unknown threats based on suspicious behavior patterns</li>
            <li><b>Email & Web Scanning:</b> Protects against threats in downloads and email attachments</li>
        </ul>

        <h4>🔥 UFW Firewall (Recommended)</h4>
        <ul>
            <li><b>Network Filtering:</b> Controls incoming and outgoing network connections</li>
            <li><b>Application Rules:</b> Allows granular control over which programs can access the network</li>
            <li><b>Intrusion Prevention:</b> Blocks common attack patterns and suspicious connections</li>
            <li><b>Port Management:</b> Secures unused network ports from potential exploitation</li>
        </ul>

        <h4>🕵️ RKHunter (Advanced)</h4>
        <ul>
            <li><b>Rootkit Detection:</b> Finds deeply embedded malware that hides from other tools</li>
            <li><b>System Integrity:</b> Monitors critical system files for unauthorized changes</li>
            <li><b>Backdoor Scanning:</b> Detects hidden network listeners and suspicious processes</li>
            <li><b>Local Exploit Detection:</b> Identifies tools commonly used by attackers</li>
        </ul>

        <h3>🎯 Why This Combination?</h3>
        <p>Each tool covers different attack vectors:</p>
        <ul>
            <li><b>ClamAV</b> stops viruses and malware before they can execute</li>
            <li><b>UFW</b> prevents network-based attacks and data exfiltration</li>
            <li><b>RKHunter</b> detects sophisticated attacks that bypass other defenses</li>
        </ul>

        <p><b>Together, they provide defense-in-depth security that's greater than the sum of its parts.</b></p>
        """
        )
        # pylint: enable=line-too-long
        layout.addWidget(info_text)

        info_widget.setLayout(layout)
        tab_widget.addTab(info_widget, "📚 Learn More")

    def create_action_buttons(self, layout):
        """Create action buttons at the bottom."""
        button_layout = QHBoxLayout()

        # Skip setup button
        self.skip_button = QPushButton("Skip Setup")
        self.skip_button.clicked.connect(self.skip_setup)
        button_layout.addWidget(self.skip_button)

        button_layout.addStretch()

        # Install button
        self.install_button = QPushButton("Install Selected Packages")
        self.install_button.setObjectName("install_button")  # For CSS styling
        self.install_button.clicked.connect(self.start_installation)
        button_layout.addWidget(self.install_button)

        layout.addLayout(button_layout)

    def skip_setup(self):
        """Skip the setup process."""
        reply = QMessageBox.question(
            self,
            "Skip Setup",
            "Are you sure you want to skip the setup?\n\n"
            "You can run the setup again later from the application menu.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Mark setup as completed even if skipped
            try:
                config = load_config()

                if "setup" not in config:
                    config["setup"] = {}

                config["setup"]["first_time_setup_completed"] = True
                config["setup"]["last_setup_check"] = datetime.now().isoformat()

                save_config(config)
            except OSError as e:
                print(f"Warning: Could not save setup skip status: {e}")

            self.reject()

    def start_installation(self):
        """Start the installation process."""
        # Get list of packages to install
        packages_to_install = [
            name for name, card in self.package_cards.items() if card.should_install()
        ]

        if not packages_to_install:
            QMessageBox.information(
                self,
                "No Packages Selected",
                "Please select at least one package to install.",
            )
            return

        # Confirm installation
        package_names = [self.packages[name].display_name for name in packages_to_install]
        reply = QMessageBox.question(
            self,
            "Confirm Installation",
            "Install the following packages?\n\n"
            + "\n".join(f"• {name}" for name in package_names)
            + "\n\nThis will require administrator privileges.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.show_installation_dialog(packages_to_install)

    def show_installation_dialog(self, packages_to_install: List[str]):
        """Show installation progress dialog."""
        self.installation_dialog = InstallationDialog(
            packages_to_install, self.packages, self.distro, self
        )
        self.installation_dialog.installation_complete.connect(self.on_installation_complete)
        self.installation_dialog.exec()

    def on_installation_complete(self, results: Dict[str, bool]):
        """Handle installation completion."""
        successful = [name for name, success in results.items() if success]
        failed = [name for name, success in results.items() if not success]

        # Update configuration with setup completion
        try:
            config = load_config()

            # Mark setup as completed
            if "setup" not in config:
                config["setup"] = {}

            config["setup"]["first_time_setup_completed"] = True
            config["setup"]["last_setup_check"] = datetime.now().isoformat()

            # Update package installation status
            if "packages_installed" not in config["setup"]:
                config["setup"]["packages_installed"] = {}

            for package_name in self.packages:
                config["setup"]["packages_installed"][package_name] = results.get(
                    package_name, False
                )

            save_config(config)
        except OSError as e:
            print(f"Warning: Could not save setup completion status: {e}")

        # Force refresh of system status in main application
        try:
            # Clear RKHunter cache to force fresh detection

            rkhunter_monitor.get_status_non_invasive(force_refresh=True)
            print("✅ Forced RKHunter status refresh")

            # Also clear any other system status caches
            cache_files = [
                Path.home() / ".xanados_rkhunter_status_cache.json",
                Path.home() / ".xanados_system_status_cache.json",
            ]

            for cache_file in cache_files:
                if cache_file.exists():
                    cache_file.unlink()
                    print(f"✅ Cleared cache file: {cache_file.name}")

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Warning: Could not refresh system status: {e}")

        message = []
        if successful:
            message.append(f"✅ Successfully installed: {', '.join(successful)}")
        if failed:
            message.append(f"❌ Failed to install: {', '.join(failed)}")

        message.append("\nYou can now start using S&D - Search & Destroy!")

        QMessageBox.information(self, "Installation Complete", "\n".join(message))

        # Signal parent to refresh system status if available
        try:
            parent_window = self.parent()
            if hasattr(parent_window, "refresh_system_status"):
                print("🔄 Requesting main window system status refresh...")
                parent_window.refresh_system_status()
            elif hasattr(parent_window, "force_refresh_status"):
                print("🔄 Requesting main window force refresh...")
                parent_window.force_refresh_status()
        except Exception as e:  # pylint: disable=broad-exception-caught
            # UI boundary: parent may not implement these or can raise unexpectedly;
            # keep user flow stable and log the issue instead of crashing the wizard.
            print(f"Warning: Could not refresh parent window status: {e}")

        self.accept()


class InstallationDialog(QDialog):  # pylint: disable=too-many-instance-attributes
    """Dialog showing installation progress."""

    installation_complete = pyqtSignal(dict)  # {package_name: success}

    def __init__(
        self,
        packages_to_install: List[str],
        package_info: Dict[str, PackageInfo],
        distro: str,
        parent=None,
    ):
        """Initialize dialog with package queue and theming from parent."""
        super().__init__(parent)
        self.packages_to_install = packages_to_install
        self.package_info = package_info
        self.distro = distro
        self.results = {}
        self.current_package_index = 0

        self.setWindowTitle("Installing Packages")
        self.setModal(True)
        self.resize(600, 400)

        # Apply same theming as parent setup wizard
        if parent and hasattr(parent, "styleSheet") and parent.styleSheet():
            self.setStyleSheet(parent.styleSheet())
        elif THEMING_AVAILABLE:
            self.apply_installation_dialog_theming()

        self.setup_ui()
        self.start_next_installation()

    def apply_installation_dialog_theming(self):
        """Apply theming to installation dialog."""
        try:
            theme_manager = get_theme_manager()
            if theme_manager:
                bg_color = theme_manager.get_color("elevated_bg")
                primary_text = theme_manager.get_color("primary_text")
                card_bg = theme_manager.get_color("card_bg")
                accent_color = theme_manager.get_color("strawberry_primary")
                border_light = theme_manager.get_color("border_light")

                self.setStyleSheet(
                    f"""
                    QDialog {{
                        background-color: {bg_color};
                        color: {primary_text};
                    }}
                    QLabel {{
                        color: {primary_text};
                    }}
                    QTextEdit {{
                        background-color: {card_bg};
                        color: {primary_text};
                        border: 1px solid {border_light};
                        font-family: monospace;
                    }}
                    QProgressBar {{
                        border: 1px solid {border_light};
                        border-radius: 4px;
                        text-align: center;
                        background-color: {card_bg};
                        color: {primary_text};
                    }}
                    QProgressBar::chunk {{
                        background-color: {accent_color};
                        border-radius: 3px;
                    }}
                    QPushButton {{
                        background-color: {card_bg};
                        border: 1px solid {border_light};
                        color: {primary_text};
                        padding: 8px 16px;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        background-color: {accent_color};
                        color: white;
                    }}
                """
                )
        except Exception:  # pylint: disable=broad-exception-caught
            # Non-critical theming application failure; continue with defaults
            pass

    def setup_ui(self):
        """Setup the installation dialog UI."""
        layout = QVBoxLayout()

        # Current package label
        self.current_package_label = QLabel()
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.current_package_label.setFont(font)
        layout.addWidget(self.current_package_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("monospace", 9))
        layout.addWidget(self.output_text)

        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_installation)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def start_next_installation(self):
        """Start installing the next package."""
        if self.current_package_index >= len(self.packages_to_install):
            # All installations complete
            self.installation_complete.emit(self.results)
            self.accept()
            return

        package_name = self.packages_to_install[self.current_package_index]
        package_info = self.package_info[package_name]

        self.current_package_label.setText(f"Installing {package_info.display_name}...")
        self.progress_bar.setValue(0)

        # Start installation worker
        self.worker = InstallationWorker(package_info, self.distro)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.installation_finished.connect(self.on_package_finished)
        self.worker.output_updated.connect(self.update_output)
        self.worker.start()

    def update_progress(self, message: str, progress: int):
        """Update progress bar and message."""
        self.current_package_label.setText(message)
        self.progress_bar.setValue(progress)

    def update_output(self, text: str):
        """Update output text."""
        self.output_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_package_finished(self, package_name: str, success: bool):
        """Handle package installation completion."""
        self.results[package_name] = success

        if success:
            self.update_output(f"✅ {package_name} installation completed successfully!")
        else:
            self.update_output(f"❌ {package_name} installation failed!")

        self.current_package_index += 1

        # Wait a moment then start next installation
        QTimer.singleShot(1000, self.start_next_installation)

    def cancel_installation(self):
        """Cancel the installation process."""
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)  # Wait up to 3 seconds

        self.reject()


def needs_setup() -> bool:
    """Check if first-time setup is needed."""
    try:
        config = load_config()

        # Check if setup was already completed
        setup_info = config.get("setup", {})
        if setup_info.get("first_time_setup_completed", False):
            return False

    except (OSError, ValueError, TypeError):
        # If config loading fails, assume setup is needed (non-critical path)
        pass

    # Check if critical packages are available
    critical_packages = ["clamscan"]  # ClamAV is the most critical

    for package in critical_packages:
        try:
            ver_result = subprocess.run(
                [package, "--version"], capture_output=True, timeout=5, check=False
            )
            if ver_result.returncode == 0:
                return False  # At least one critical package is available
        except (
            FileNotFoundError,
            PermissionError,
            subprocess.SubprocessError,
            OSError,
            ValueError,
        ):
            continue

    return True  # No critical packages found


def show_setup_wizard(parent=None) -> bool:
    """Show setup wizard and return True if setup was completed."""
    if not needs_setup():
        return True

    wizard = SetupWizard(parent)
    _dlg_result = wizard.exec()
    return _dlg_result == QDialog.DialogCode.Accepted


if __name__ == "__main__":
    # Test the setup wizard standalone
    app = QApplication(sys.argv)

    _wizard = SetupWizard()
    _exec_result = _wizard.exec()

    sys.exit(_exec_result)
