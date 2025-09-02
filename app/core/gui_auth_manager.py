#!/usr/bin/env python3
"""Enhanced GUI authentication manager for xanadOS Search & Destroy.
Provides persistent GUI sudo sessions to avoid multiple password prompts.
"""

import logging
import os
import stat
import subprocess
import tempfile
import time
from collections.abc import Sequence

from .secure_subprocess import popen_secure, run_secure

logger = logging.getLogger(__name__)


class GUIAuthManager:
    """Manages GUI-based authentication with persistent sessions.
    Uses only GUI sudo authentication for consistency and security.
    """

    def __init__(self):
        self._sudo_session_active = False
        self._session_start_time = 0
        self._session_timeout = 900  # 15 minutes default sudo timeout
        self._gui_helper = None
        self._discover_gui_helper()

    def _discover_gui_helper(self) -> None:
        """Discover available GUI authentication helpers."""
        # Priority order for GUI authentication helpers
        helpers = [
            "/usr/bin/ksshaskpass",  # KDE SSH askpass (best for KDE)
            "/usr/bin/ssh-askpass",  # Generic SSH askpass
            "/usr/bin/x11-ssh-askpass",  # X11 SSH askpass
            "/usr/bin/lxqt-openssh-askpass",  # LXQt SSH askpass
            "/usr/bin/zenity",  # GNOME zenity (can be used for passwords)
            "/usr/bin/kdialog",  # KDE dialog (can be used for passwords)
        ]

        for helper in helpers:
            if os.path.isfile(helper) and os.access(helper, os.X_OK):
                self._gui_helper = helper
                logger.info(f"Found GUI authentication helper: {helper}")
                break

        if not self._gui_helper:
            logger.warning("No GUI authentication helper found")

    def is_gui_available(self) -> bool:
        """Check if GUI authentication is available."""
        return self._gui_helper is not None and bool(os.environ.get("DISPLAY"))

    def get_gui_helper(self) -> str | None:
        """Get the discovered GUI helper path."""
        return self._gui_helper

    def _which(self, name: str) -> str | None:
        """Find executable in PATH - GUI sudo only version."""
        try:
            # Directly check for sudo at standard locations
            if name == "sudo":
                sudo_paths = ["/usr/bin/sudo", "/bin/sudo", "/usr/local/bin/sudo"]
                for path in sudo_paths:
                    if os.path.isfile(path) and os.access(path, os.X_OK):
                        return path
                return None

            # For other commands, use standard which
            result = run_secure(
                ["which", name], check=False, capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _is_sudo_session_active(self) -> bool:
        """Check if a sudo session is currently active."""
        try:
            # Quick test with sudo -n (non-interactive)
            result = run_secure(
                ["sudo", "-n", "true"],
                check=False,
                capture_output=True,
                timeout=5,
                allow_root=True,
            )

            current_time = time.time()

            if result.returncode == 0:
                # Update session tracking
                if not self._sudo_session_active:
                    self._session_start_time = current_time
                    self._sudo_session_active = True
                    logger.info("Sudo session detected as active")
                return True
            else:
                # Check if our tracked session has expired
                if self._sudo_session_active:
                    elapsed = current_time - self._session_start_time
                    if elapsed > self._session_timeout:
                        self._sudo_session_active = False
                        logger.info("Sudo session expired")

                return False

        except Exception as e:
            logger.debug(f"Error checking sudo session: {e}")
            self._sudo_session_active = False
            return False

    def _create_zenity_password_helper(self) -> str:
        """Create a temporary script to use zenity for password prompts."""
        # Create a temporary script that uses zenity for password input
        script_content = """#!/bin/bash
zenity --password --title="Authentication Required" --text="Enter your password for administrative access:"
"""

        # Create temporary file
        fd, script_path = tempfile.mkstemp(suffix=".sh", prefix="sudo_helper_")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(script_content)

            # Make executable
            os.chmod(script_path, stat.S_IRWXU)

            return script_path
        except Exception:
            os.unlink(script_path)
            raise

    def _create_kdialog_password_helper(self) -> str:
        """Create a temporary script to use kdialog for password prompts."""
        # Create a temporary script that uses kdialog for password input
        script_content = """#!/bin/bash
kdialog --password "Enter your password for administrative access:"
"""

        # Create temporary file
        fd, script_path = tempfile.mkstemp(suffix=".sh", prefix="sudo_helper_")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(script_content)

            # Make executable
            os.chmod(script_path, stat.S_IRWXU)

            return script_path
        except Exception:
            os.unlink(script_path)
            raise

    def _establish_gui_sudo_session(self) -> bool:
        """Establish a GUI sudo session with password caching."""
        if self._is_sudo_session_active():
            logger.info("Sudo session already active")
            return True

        if not self._gui_helper:
            logger.error("No GUI helper available for sudo authentication")
            return False

        # Prepare environment for GUI sudo
        env = os.environ.copy()
        temp_script = None

        try:
            # Set up the appropriate SUDO_ASKPASS helper
            if "ksshaskpass" in self._gui_helper or "ssh-askpass" in self._gui_helper:
                env["SUDO_ASKPASS"] = self._gui_helper
            elif "zenity" in self._gui_helper:
                temp_script = self._create_zenity_password_helper()
                env["SUDO_ASKPASS"] = temp_script
            elif "kdialog" in self._gui_helper:
                temp_script = self._create_kdialog_password_helper()
                env["SUDO_ASKPASS"] = temp_script
            else:
                logger.error(f"Unsupported GUI helper: {self._gui_helper}")
                return False

            # Establish sudo session with GUI password prompt
            logger.info(f"Establishing GUI sudo session using {self._gui_helper}")
            result = run_secure(
                ["sudo", "-A", "true"],
                check=False,
                env=env,
                timeout=60,  # Give user time to enter password
                capture_output=True,
                allow_root=True,
            )

            if result.returncode == 0:
                self._sudo_session_active = True
                self._session_start_time = time.time()
                logger.info("✅ GUI sudo session established successfully")
                return True
            else:
                logger.error(
                    f"Failed to establish sudo session: {result.stderr.decode()}"
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout waiting for password input")
            return False
        except Exception as e:
            logger.error(f"Error establishing GUI sudo session: {e}")
            return False
        finally:
            # Clean up temporary script
            if temp_script and os.path.exists(temp_script):
                try:
                    os.unlink(temp_script)
                except Exception:
                    pass

    def run_with_gui_auth(
        self,
        argv: Sequence[str],
        *,
        timeout: int = 300,
        capture_output: bool = True,
        text: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run command with GUI authentication, using persistent sudo session.

        Args:
            argv: Command to run (without sudo prefix)
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
            text: Whether to use text mode

        Returns:
            subprocess.CompletedProcess result
        """
        if not argv:
            return subprocess.CompletedProcess([], 1, "", "No command provided")

        # Check if sudo is available
        sudo_path = self._which("sudo")
        if not sudo_path:
            logger.error("sudo not found on system")
            return subprocess.CompletedProcess(argv, 1, "", "sudo not available")

        # Try to use existing session first
        if self._is_sudo_session_active():
            logger.info("Using existing sudo session")
            try:
                result = run_secure(
                    [sudo_path] + list(argv),
                    check=False,
                    timeout=timeout,
                    capture_output=capture_output,
                    text=text,
                    allow_root=True,
                )

                if result.returncode == 0:
                    return result
                else:
                    logger.warning(
                        f"Command failed with existing session: {result.returncode}"
                    )
            except Exception as e:
                logger.warning(f"Error using existing session: {e}")

        # Establish new GUI session if needed
        if not self._establish_gui_sudo_session():
            logger.error("Failed to establish GUI sudo session")
            return subprocess.CompletedProcess(argv, 1, "", "Authentication failed")

        # Run the command with the established session
        try:
            logger.info(
                f"Running command with GUI sudo session: {' '.join(argv[:3])}..."
            )
            result = run_secure(
                [sudo_path] + list(argv),
                check=False,
                timeout=timeout,
                capture_output=capture_output,
                text=text,
                allow_root=True,
            )

            if result.returncode == 0:
                logger.info("✅ Command completed successfully")
            else:
                logger.warning(f"⚠️ Command failed with return code {result.returncode}")

            return result

        except subprocess.TimeoutExpired:
            logger.error("Command timed out")
            return subprocess.CompletedProcess(argv, 124, "", "Command timed out")
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return subprocess.CompletedProcess(argv, 1, "", str(e))

    def start_gui_auth_process(
        self,
        argv: Sequence[str],
        *,
        text: bool = True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) -> subprocess.Popen:
        """Start a privileged process with GUI authentication, returning Popen for streaming.

        Args:
            argv: Command to run (without sudo prefix)
            text: Whether to use text mode
            stdout, stderr: Pipe configuration

        Returns:
            subprocess.Popen object
        """
        if not argv:
            raise ValueError("No command provided")

        sudo_path = self._which("sudo")
        if not sudo_path:
            raise RuntimeError("sudo not available")

        # Ensure we have an active session
        if not self._is_sudo_session_active():
            if not self._establish_gui_sudo_session():
                raise RuntimeError("Failed to establish GUI sudo session")

        # Start the process with the established session
        try:
            logger.info(f"Starting GUI sudo process: {' '.join(argv[:3])}...")
            process = popen_secure(
                [sudo_path] + list(argv),
                stdout=stdout,
                stderr=stderr,
                text=text,
                allow_root=True,
            )
            logger.info(f"Process started with GUI sudo, PID: {process.pid}")
            return process

        except Exception as e:
            logger.error(f"Error starting GUI sudo process: {e}")
            raise RuntimeError(f"Failed to start privileged process: {e}")

    def refresh_session(self) -> bool:
        """Refresh the sudo session to extend its lifetime."""
        if not self._is_sudo_session_active():
            return self._establish_gui_sudo_session()

        try:
            # Refresh with a simple command
            result = run_secure(
                ["sudo", "-v"],
                check=False,
                timeout=5,
                capture_output=True,  # Refresh timestamp
                allow_root=True,
            )

            if result.returncode == 0:
                self._session_start_time = time.time()
                logger.debug("Sudo session refreshed")
                return True
            else:
                # Session might have expired, try to re-establish
                self._sudo_session_active = False
                return self._establish_gui_sudo_session()

        except Exception as e:
            logger.error(f"Error refreshing sudo session: {e}")
            return False

    def cleanup_session(self) -> None:
        """Clean up the authentication session."""
        try:
            if self._sudo_session_active:
                # Invalidate sudo timestamp
                run_secure(
                    ["sudo", "-k"],
                    check=False,
                    timeout=5,
                    capture_output=True,
                    allow_root=True,
                )
                logger.info("Sudo session cleaned up")
        except Exception as e:
            logger.debug(f"Error cleaning up session: {e}")
        finally:
            self._sudo_session_active = False
            self._session_start_time = 0

    def get_session_info(self) -> dict[str, any]:
        """Get information about the current authentication session."""
        current_time = time.time()
        elapsed = (
            current_time - self._session_start_time if self._session_start_time else 0
        )
        remaining = (
            max(0, self._session_timeout - elapsed) if self._sudo_session_active else 0
        )

        return {
            "active": self._sudo_session_active,
            "gui_helper": self._gui_helper,
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
            "session_timeout": self._session_timeout,
        }


# Global instance for use throughout the application
_gui_auth_manager = None


def get_gui_auth_manager() -> GUIAuthManager:
    """Get the global GUI authentication manager instance."""
    global _gui_auth_manager
    if _gui_auth_manager is None:
        _gui_auth_manager = GUIAuthManager()
    return _gui_auth_manager


def elevated_run_gui(
    argv: Sequence[str],
    *,
    timeout: int = 300,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Convenience function for running commands with GUI authentication.
    Uses the global GUI authentication manager.
    """
    return get_gui_auth_manager().run_with_gui_auth(
        argv, timeout=timeout, capture_output=capture_output, text=text
    )


def elevated_popen_gui(
    argv: Sequence[str],
    *,
    stdin=None,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text: bool = True,
    env: dict | None = None,
    **kwargs,
) -> subprocess.Popen:
    """Convenience function for starting privileged processes with GUI authentication.
    Uses the global GUI authentication manager.
    """
    # Get the manager instance
    manager = get_gui_auth_manager()

    # Start the process directly with the manager's method
    if not argv:
        raise ValueError("No command provided")

    sudo_path = manager._which("sudo")
    if not sudo_path:
        raise RuntimeError("sudo not available")

    # Ensure we have an active session
    if not manager._is_sudo_session_active():
        if not manager._establish_gui_sudo_session():
            raise RuntimeError("Failed to establish GUI sudo session")

    # Build the sudo command
    sudo_cmd = [sudo_path, "-n"] + list(argv)

    # Create environment if needed
    proc_env = None
    if env:
        proc_env = os.environ.copy()
        proc_env.update(env)

    # Filter out timeout from kwargs since Popen doesn't accept it
    popen_kwargs = {k: v for k, v in kwargs.items() if k != "timeout"}

    # Start the process
    try:
        return subprocess.Popen(
            sudo_cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            text=text,
            env=proc_env,
            **popen_kwargs,
        )
    except Exception as e:
        logger.error(f"Failed to start elevated process: {e}")
        raise RuntimeError(f"Failed to start elevated process: {e}")
