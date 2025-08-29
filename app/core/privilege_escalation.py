#!/usr/bin/env python3
"""Secure privilege escalation module for xanadOS Search & Destroy
Handles elevation requests through polkit for secure operations
"""

import logging
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .auth_session_manager import auth_manager
from .elevated_runner import elevated_run
from .secure_subprocess import run_secure


class PrivilegeOperation(Enum):
    """Types of operations requiring privilege escalation."""

    SCAN_SYSTEM = "io.github.asafelobotomy.searchanddestroy.scan-system"
    QUARANTINE_MANAGE = "io.github.asafelobotomy.searchanddestroy.quarantine-manage"
    UPDATE_DATABASE = "io.github.asafelobotomy.searchanddestroy.update-database"
    ACCESS_LOGS = "io.github.asafelobotomy.searchanddestroy.access-logs"


@dataclass
class ElevationRequest:
    """Represents a privilege escalation request."""

    operation: PrivilegeOperation
    command: list[str]
    working_directory: str | None = None
    environment: dict[str, str] | None = None
    timeout: int = 300  # 5 minutes default timeout


class SecureElevationError(Exception):
    """Custom exception for privilege escalation errors."""

    pass


class PrivilegeEscalationManager:
    """Manages secure privilege escalation using polkit.

    This class provides a secure way to request elevated privileges
    for specific operations without compromising security.
    """

    def __init__(self):
        """Initialize the privilege escalation manager."""
        self.logger = logging.getLogger(__name__)
        self._polkit_available = self._check_polkit_availability()
        self._policy_file = (
            Path(__file__).parent.parent
            / "config"
            / "io.github.asafelobotomy.searchanddestroy.policy"
        )

    def _check_polkit_availability(self) -> bool:
        """Check if polkit is available on the system."""
        try:
            result = run_secure(["pkcheck", "--version"], timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.warning("Polkit not available on this system")
            return False

    def _check_authorization(self, operation: PrivilegeOperation) -> bool:
        """Check if current user is authorized for the specified operation.

        Args:
            operation: The operation to check authorization for

        Returns:
            True if authorized, False otherwise
        """
        if not self._polkit_available:
            self.logger.warning("Polkit not available, falling back to basic checks")
            return os.geteuid() == 0  # Fallback to root check

        try:
            result = run_secure(
                [
                    "pkcheck",
                    "--action-id",
                    operation.value,
                    "--process",
                    str(os.getpid()),
                    "--allow-user-interaction",
                ],
                timeout=30,
            )
            return result.returncode == 0

        except subprocess.TimeoutExpired:
            self.logger.error("Authorization check timed out")
            return False
        except Exception as e:
            self._safe_log_error("authorization check", e)
            return False

    def _validate_command_security(self, command: list[str]) -> bool:
        """Validate command arguments for security issues.

        Args:
            command: List of command arguments to validate

        Returns:
            True if command is safe, False otherwise
        """
        # Check for dangerous shell metacharacters that could enable injection
        dangerous_patterns = [";", "&&", "||", "`", "$", "|", ">", "<", "&", "\n", "\r"]

        for arg in command:
            # Check for dangerous patterns in arguments
            for pattern in dangerous_patterns:
                if pattern in arg:
                    self.logger.warning(
                        "Potentially dangerous pattern '%s' found in command argument: %s",
                        pattern,
                        arg[:50],  # Limit log output
                    )
                    return False

        return True

    def _safe_log_error(
        self, operation: str, error: Exception, include_type: bool = True
    ) -> None:
        """Log errors safely without exposing sensitive information.

        Args:
            operation: Description of the operation that failed
            error: The exception that occurred
            include_type: Whether to include the exception type
        """
        error_info = f"{type(error).__name__}" if include_type else "Error occurred"
        self.logger.error("Operation '%s' failed: %s", operation, error_info)

    def _create_secure_wrapper_script(self, request: ElevationRequest) -> str:
        """Create a secure wrapper script for the elevated operation.

        Args:
            request: The elevation request

        Returns:
            Path to the wrapper script
        """
        # Create temporary script with secure permissions
        fd, script_path = tempfile.mkstemp(suffix=".sh", prefix="xanados_secure_")

        try:
            with os.fdopen(fd, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("# Secure wrapper script for xanadOS Search & Destroy\n")
                f.write("# Auto-generated - do not modify\n\n")

                # Set secure environment
                f.write("set -euo pipefail\n")
                f.write("umask 0077\n\n")

                # Change to working directory if specified
                if request.working_directory:
                    f.write(f"cd '{request.working_directory}'\n")

                # Set environment variables if specified
                if request.environment:
                    for key, value in request.environment.items():
                        # Sanitize environment variables
                        safe_key = "".join(c for c in key if c.isalnum() or c == "_")
                        safe_value = value.replace("'", "'\"'\"'")
                        f.write(f"export {safe_key}='{safe_value}'\n")

                # Execute the command with timeout
                # Use shlex.quote for proper shell escaping to prevent injection

                escaped_args = [shlex.quote(arg) for arg in request.command]
                cmd_str = " ".join(escaped_args)
                f.write(f"\ntimeout {request.timeout} {cmd_str}\n")

            # Set script permissions (read/execute for owner only)
            os.chmod(script_path, 0o700)
            return script_path

        except Exception:
            # Clean up on error
            os.unlink(script_path)
            raise

    def request_elevation(self, request: ElevationRequest) -> tuple[bool, str, str]:
        """Request privilege escalation for a specific operation.

        Args:
            request: The elevation request containing operation details

        Returns:
            Tuple of (success, stdout, stderr)

        Raises:
            SecureElevationError: If elevation fails or is denied
        """
        self.loginfo(
            "Requesting elevation for operation: %s".replace(
                "%s", "{request.operation.value}"
            ).replace("%d", "{request.operation.value}")
        )

        # Check authorization first
        if not self._check_authorization(request.operation):
            raise SecureElevationError(
                f"Authorization denied for operation: {request.operation.value}"
            )

        # Validate command arguments
        if not request.command or not all(
            isinstance(arg, str) for arg in request.command
        ):
            raise SecureElevationError("Invalid command arguments")

        # Additional security validation for command arguments
        if not self._validate_command_security(request.command):
            raise SecureElevationError(
                "Command contains potentially dangerous patterns"
            )

        script_path = None
        try:
            script_path = self._create_secure_wrapper_script(request)

            result = elevated_run([script_path], timeout=request.timeout + 30, gui=True)

            success = result.returncode == 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            if success:
                self.loginfo(
                    "Elevation successful for operation: %s".replace(
                        "%s", "{request.operation.value}"
                    ).replace("%d", "{request.operation.value}")
                )
            else:
                self.logger.error(
                    "Elevation failed for operation: %s, return code: %d",
                    request.operation.value,
                    result.returncode,
                )

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            error_msg = f"Elevation timed out for operation: {request.operation.value}"
            self.logger.error(error_msg)
            raise SecureElevationError(error_msg)

        except Exception as e:
            self._safe_log_error(
                f"elevation for operation {request.operation.value}", e
            )
            raise SecureElevationError(
                f"Elevation failed for operation: {request.operation.value}"
            )

        finally:
            if (
                "script_path" in locals()
                and script_path
                and os.path.exists(script_path)
            ):
                try:
                    os.unlink(script_path)
                except OSError:
                    self.logwarning(
                        "Failed to clean up wrapper script: %s".replace(
                            "%s", "{e}"
                        ).replace("%d", "{e}")
                    )

    def scan_system_directories(
        self, scan_paths: list[str], scan_options: dict[str, str] | None = None
    ) -> tuple[bool, str, str]:
        """Request elevation to scan system directories.

        Args:
            scan_paths: List of paths to scan
            scan_options: Optional scan configuration

        Returns:
            Tuple of (success, stdout, stderr)
        """
        # Validate scan paths
        validated_paths = []
        for path in scan_paths:
            path_obj = Path(path).resolve()
            if path_obj.exists():
                validated_paths.append(str(path_obj))
            else:
                self.logwarning(
                    "Skipping non-existent path: %s".replace("%s", "{path}").replace(
                        "%d", "{path}"
                    )
                )

        if not validated_paths:
            raise SecureElevationError("No valid scan paths provided")

        # Build scan command
        scan_command = [
            sys.executable,
            "-m",
            "app.core.file_scanner",
            "--scan-paths",
            *validated_paths,
        ]

        if scan_options:
            for key, value in scan_options.items():
                scan_command.extend([f"--{key}", value])

        request = ElevationRequest(
            operation=PrivilegeOperation.SCAN_SYSTEM,
            command=scan_command,
            working_directory=str(Path(__file__).parent.parent),
            timeout=3600,  # 1 hour for system scans
        )

        return self.request_elevation(request)

    def update_virus_database(self) -> tuple[bool, str, str]:
        """Request elevation to update the virus database.

        Returns:
            Tuple of (success, stdout, stderr)
        """
        request = ElevationRequest(
            operation=PrivilegeOperation.UPDATE_DATABASE,
            command=["freshclam", "--verbose"],
            timeout=600,  # 10 minutes for database updates
        )

        return self.request_elevation(request)

    def manage_quarantine(self, action: str, file_path: str) -> tuple[bool, str, str]:
        """Request elevation to manage quarantined files.

        Args:
            action: The quarantine action (restore, delete, etc.)
            file_path: Path to the quarantined file

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if action not in ["restore", "delete", "list"]:
            raise SecureElevationError(f"Invalid quarantine action: {action}")

        request = ElevationRequest(
            operation=PrivilegeOperation.QUARANTINE_MANAGE,
            command=[
                sys.executable,
                "-m",
                "app.core.quarantine_manager",
                f"--{action}",
                file_path,
            ],
            working_directory=str(Path(__file__).parent.parent),
            timeout=300,  # 5 minutes for quarantine operations
        )

        return self.request_elevation(request)

    def install_policy_file(self) -> bool:
        """Install the polkit policy file to the system.

        Returns:
            True if successful, False otherwise
        """
        if not self._policy_file.exists():
            self.logerror(
                "Policy file not found: %s".replace(
                    "%s", "{self._policy_file}"
                ).replace("%d", "{self._policy_file}")
            )
            return False

        policy_dest = Path(
            "/usr/share/polkit-1/actions/io.github.asafelobotomy.searchanddestroy.policy"
        )

        try:
            # Use unified authentication session manager for policy installation
            try:
                # Copy policy file with proper permissions using session management
                result1 = auth_manager.execute_elevated_command(
                    ["cp", str(self._policy_file), str(policy_dest)],
                    timeout=30,
                    session_type="policy_install",
                    operation="install_policy_file",
                )

                if result1.returncode != 0:
                    raise subprocess.CalledProcessError(result1.returncode, ["cp"])

                result2 = auth_manager.execute_elevated_command(
                    ["chmod", "644", str(policy_dest)],
                    timeout=10,
                    session_type="policy_install",
                    operation="set_policy_permissions",
                )

                if result2.returncode != 0:
                    raise subprocess.CalledProcessError(result2.returncode, ["chmod"])

            except ImportError:
                # Fallback to elevated_run if auth_manager not available (same method as RKHunter)

                result1 = elevated_run(
                    ["cp", str(self._policy_file), str(policy_dest)],
                    timeout=30,
                    gui=True,
                )
                if result1.returncode != 0:
                    raise subprocess.CalledProcessError(result1.returncode, ["cp"])

                result2 = elevated_run(
                    ["chmod", "644", str(policy_dest)], timeout=10, gui=True
                )
                if result2.returncode != 0:
                    raise subprocess.CalledProcessError(result2.returncode, ["chmod"])

            self.logger.info("Policy file installed successfully")
            return True

        except subprocess.CalledProcessError:
            self.logerror(
                "Failed to install policy file: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return False
        except Exception:
            self.logerror(
                "Unexpected error installing policy file: %s".replace(
                    "%s", "{e}"
                ).replace("%d", "{e}")
            )
            return False


# Global instance for easy access
privilege_manager = PrivilegeEscalationManager()


def require_elevation(operation: PrivilegeOperation):
    """Decorator to require privilege escalation for a function.

    Args:
        operation: The privilege operation required
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not privilege_manager._check_authorization(operation):
                raise SecureElevationError(
                    f"Insufficient privileges for operation: {operation.value}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
