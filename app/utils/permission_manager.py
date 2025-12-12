"""
Permission management utilities for handling privileged directory access during scanning.

This module provides utilities to:
- Detect directories that require elevated permissions
- Present user choices for handling permission errors
- Manage sudo authentication for elevated scanning
"""

import os
import shutil
import subprocess
import tempfile

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox


class PermissionChecker:
    """Utility class for checking and managing file system permissions."""

    def __init__(self):
        self._known_privileged_paths = {
            "/proc",
            "/sys",
            "/dev",
            "/root",
            "/boot",
            "/etc",
            "/var/log",
            "/var/cache",
            "/var/lib",
            "/var/spool",
            "/usr/local/etc",
            "/opt",
        }
        self._checked_paths = {}  # Cache for permission checks

    def requires_root_access(self, path: str) -> bool:
        """
        Check if a directory path requires root access.

        Args:
            path: Directory path to check

        Returns:
            True if path requires root access, False otherwise
        """
        # Normalize path
        abs_path = os.path.abspath(path)

        # Check cache first
        if abs_path in self._checked_paths:
            return self._checked_paths[abs_path]

        # Check if path starts with known privileged directories
        for priv_path in self._known_privileged_paths:
            if abs_path.startswith(priv_path):
                self._checked_paths[abs_path] = True
                return True

        # Test actual access
        try:
            # Try to list directory contents
            os.listdir(abs_path)
            self._checked_paths[abs_path] = False
            return False
        except PermissionError:
            self._checked_paths[abs_path] = True
            return True
        except (OSError, FileNotFoundError):
            # Path doesn't exist or other error - not a permission issue
            self._checked_paths[abs_path] = False
            return False

    def test_directory_access(self, path: str) -> tuple[bool, str | None]:
        """
        Test if a directory can be accessed and return detailed error info.

        Args:
            path: Directory path to test

        Returns:
            Tuple of (can_access, error_message)
        """
        try:
            # Test if directory exists
            if not os.path.exists(path):
                return False, f"Directory does not exist: {path}"

            if not os.path.isdir(path):
                return False, f"Path is not a directory: {path}"

            # Test read access
            os.listdir(path)
            return True, None

        except PermissionError as e:
            return False, f"Permission denied: {e}"
        except OSError as e:
            return False, f"OS error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def find_privileged_subdirectories(
        self, root_path: str, max_depth: int = 2
    ) -> list[str]:
        """
        Find subdirectories that require root access within a given path.

        Args:
            root_path: Root directory to scan
            max_depth: Maximum depth to check (default: 2)

        Returns:
            List of paths that require root access
        """
        privileged_dirs = []

        def _check_recursive(current_path: str, current_depth: int):
            if current_depth > max_depth:
                return

            try:
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)

                    if os.path.isdir(item_path):
                        if self.requires_root_access(item_path):
                            privileged_dirs.append(item_path)
                        else:
                            _check_recursive(item_path, current_depth + 1)

            except (PermissionError, OSError):
                # Can't access this directory
                pass

        try:
            _check_recursive(root_path, 0)
        except Exception:
            pass

        return privileged_dirs

    def can_use_sudo(self) -> bool:
        """
        Check if sudo is available and can be used.

        Returns:
            True if sudo is available, False otherwise
        """
        try:
            # Check if sudo command exists
            sudo_path = shutil.which("sudo")
            if not sudo_path:
                return False

            result = subprocess.run(
                [sudo_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


class PermissionDialog:
    """GUI dialog for handling permission-related user choices."""

    @staticmethod
    def ask_for_sudo_permission(parent=None, privileged_paths: list[str] | None = None) -> str:
        """
        Ask user how to handle privileged directory access.

        Args:
            parent: Parent widget for the dialog
            privileged_paths: List of paths requiring root access

        Returns:
            'skip' - Skip privileged directories
            'cancel' - Cancel the entire scan
        """
        if not privileged_paths:
            privileged_paths = []

        # Format the paths for display
        path_display = "\n".join(f"• {path}" for path in privileged_paths[:10])
        if len(privileged_paths) > 10:
            path_display += f"\n... and {len(privileged_paths) - 10} more directories"

        message = (
            "Permission Required for System Directories\n\n"
            "The scan has encountered directories that require administrator privileges:\n\n"
            f"{path_display}\n\n"
            "How would you like to proceed?\n\n"
            "• Skip Protected: Continue scanning but skip directories requiring root access\n"
            "• Cancel: Stop the entire scanning operation"
        )

        # Create custom message box with two options
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Administrator Access Required")
        msg_box.setText(message)

        # Add custom buttons
        skip_btn = msg_box.addButton(
            "Skip Protected", QMessageBox.ButtonRole.AcceptRole
        )
        msg_box.addButton("Cancel Scan", QMessageBox.ButtonRole.RejectRole)

        msg_box.setDefaultButton(skip_btn)  # Default to skip for safety
        msg_box.exec()

        clicked_button = msg_box.clickedButton()

        if clicked_button == skip_btn:
            return "skip"
        else:  # cancel_btn or closed
            return "cancel"


class SudoAuthenticator(QThread):
    """Thread for handling sudo authentication without blocking the GUI."""

    authentication_result = pyqtSignal(bool, str)  # success, message

    def __init__(self, command: list[str]):
        super().__init__()
        self.command = command
        self._process = None

    def run(self):
        """Run sudo authentication in background thread."""
        try:
            # Use pkexec for GUI sudo authentication if available
            if self._has_pkexec():
                auth_command = ["pkexec"] + self.command
                env = None
            else:
                # Fallback to terminal sudo (will require terminal)
                auth_command = ["sudo", "-A"] + self.command
                # Set environment for GUI password prompt
                env = os.environ.copy()
                env["SUDO_ASKPASS"] = self._get_askpass_program()

            self._process = subprocess.run(
                auth_command,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                env=env,
                check=False,
            )

            if self._process.returncode == 0:
                self.authentication_result.emit(True, "Authentication successful")
            else:
                error_msg = self._process.stderr.strip() or "Authentication failed"
                self.authentication_result.emit(False, error_msg)

        except subprocess.TimeoutExpired:
            self.authentication_result.emit(False, "Authentication timeout")
        except Exception as e:
            self.authentication_result.emit(False, f"Authentication error: {e}")

    def _has_pkexec(self) -> bool:
        """Check if pkexec is available for GUI authentication."""
        try:
            pkexec_path = shutil.which("pkexec")
            if not pkexec_path:
                return False
            subprocess.run(
                [pkexec_path, "--version"], capture_output=True, timeout=5, check=False
            )
            return True
        except Exception:
            return False

    def _get_askpass_program(self) -> str:
        """Get available GUI askpass program for sudo."""
        askpass_programs = [
            "/usr/bin/ssh-askpass",
            "/usr/bin/x11-ssh-askpass",
            "/usr/bin/qt4-ssh-askpass",
            "/usr/bin/ksshaskpass",
        ]

        for program in askpass_programs:
            if os.path.exists(program):
                return program

        # Create a simple zenity-based askpass if available
        zenity_path = shutil.which("zenity")
        if zenity_path:
            return self._create_zenity_askpass()

        # Fallback - will require terminal
        return "/bin/false"

    def _create_zenity_askpass(self) -> str:
        """Create a temporary zenity-based askpass script."""
        askpass_script = """#!/bin/bash
zenity --password --title="Sudo Password Required" --text="Please enter your password for administrator access:"
"""

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
                f.write(askpass_script)
                f.flush()
                os.chmod(f.name, 0o700)  # Secure permissions
                return f.name
        except Exception:
            return "/bin/false"


class PrivilegedScanner:
    """Manager for scanning with elevated privileges when necessary."""

    def __init__(self):
        self.permission_checker = PermissionChecker()
        self._sudo_available = None

    def is_sudo_available(self) -> bool:
        """Check if sudo is available for use."""
        if self._sudo_available is None:
            self._sudo_available = self.permission_checker.can_use_sudo()
        return self._sudo_available

    def scan_with_elevation(self, scanner_instance, path: str, **kwargs) -> dict:
        """
        Scan a directory with elevated privileges if needed.

        Args:
            scanner_instance: FileScanner instance to use
            path: Directory path to scan
            **kwargs: Additional scan parameters

        Returns:
            Scan results dictionary
        """
        # This would need to be implemented based on how the scanner
        # can be run with elevated privileges. For now, return standard scan.
        return scanner_instance.scan_directory(path, **kwargs)

    def prepare_scan_with_permissions(
        self, path: str, parent_widget=None
    ) -> tuple[bool, str, list[str]]:
        """
        Prepare scanning by checking permissions and getting user consent.

        Args:
            path: Path to scan
            parent_widget: Parent widget for dialogs

        Returns:
            Tuple of (should_proceed, permission_mode, privileged_paths)
            permission_mode: 'normal', 'skip_privileged'
        """
        # Check if scanning root or system directories
        privileged_dirs = []

        if path == "/" or self.permission_checker.requires_root_access(path):
            # Find specific privileged subdirectories
            privileged_dirs = self.permission_checker.find_privileged_subdirectories(
                path
            )

            if privileged_dirs and parent_widget:
                # Ask user for permission handling choice
                choice = PermissionDialog.ask_for_sudo_permission(
                    parent_widget, privileged_dirs
                )

                if choice == "cancel":
                    return False, "cancelled", privileged_dirs
                else:  # skip - only remaining option
                    return True, "skip_privileged", privileged_dirs

        # No special permissions needed
        return True, "normal", []
