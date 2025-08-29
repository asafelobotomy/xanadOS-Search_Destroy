#!/usr/bin/env python3
"""Unified Authentication Session Manager
xanadOS Search & Destroy - Global Authentication Caching
This module provides a singleton authentication session manager that all
components can use to reduce password prompts throughout the application.
Key Features:
- Global authentication session tracking
- Automatic session timeout (5 minutes)
- Integration with elevated_run for GUI sudo
- Smart passwordless sudo attempts
- Automatic cleanup and fallback mechanisms
- Thread-safe session management
"""

import logging
import os
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class AuthenticationSessionManager:
    """Global authentication session manager for reducing password prompts"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self._session_lock = threading.RLock()
        self._active_sessions: dict[str, datetime] = {}
        self._session_timeout = 300  # 5 minutes in seconds
        self._global_session_active = False
        self._global_session_start: datetime | None = None
        self._initialized = True

        logger.debug("Authentication session manager initialized")

    def is_session_valid(self, session_type: str = "global") -> bool:
        """Check if an authentication session is still valid"""
        with self._session_lock:
            if session_type == "global":
                if not self._global_session_active or not self._global_session_start:
                    return False
                session_age = (
                    datetime.now() - self._global_session_start
                ).total_seconds()
                return session_age < self._session_timeout
            else:
                session_start = self._active_sessions.get(session_type)
                if not session_start:
                    return False
                session_age = (datetime.now() - session_start).total_seconds()
                return session_age < self._session_timeout

    def start_session(
        self, session_type: str = "global", operation: str = "general"
    ) -> None:
        """Start an authentication session"""
        with self._session_lock:
            current_time = datetime.now()

            if session_type == "global":
                self._global_session_active = True
                self._global_session_start = current_time
                logger.debug(
                    f"🔐 Global authentication session started for: {operation}"
                )
            else:
                self._active_sessions[session_type] = current_time
                logger.debug(
                    f"🔐 Authentication session '{session_type}' started for: {operation}"
                )

    def end_session(self, session_type: str = "global") -> None:
        """End an authentication session"""
        with self._session_lock:
            if session_type == "global":
                if self._global_session_active and self._global_session_start:
                    duration = (
                        datetime.now() - self._global_session_start
                    ).total_seconds()
                    logger.debug(
                        f"🔒 Global authentication session ended (lasted {duration:.1f} seconds)"
                    )
                self._global_session_active = False
                self._global_session_start = None
            else:
                session_start = self._active_sessions.pop(session_type, None)
                if session_start:
                    duration = (datetime.now() - session_start).total_seconds()
                    logger.debug(
                        f"🔒 Authentication session '{session_type}' ended (lasted {
                            duration:.1f} seconds)"
                    )

    def cleanup_expired_sessions(self) -> None:
        """Clean up expired authentication sessions"""
        with self._session_lock:
            current_time = datetime.now()

            # Check global session
            if (
                self._global_session_active
                and self._global_session_start
                and (current_time - self._global_session_start).total_seconds()
                >= self._session_timeout
            ):
                logger.debug("Global authentication session expired, cleaning up")
                self._global_session_active = False
                self._global_session_start = None

            # Check named sessions
            expired_sessions = []
            for session_type, start_time in self._active_sessions.items():
                if (current_time - start_time).total_seconds() >= self._session_timeout:
                    expired_sessions.append(session_type)

            for session_type in expired_sessions:
                self.end_session(session_type)
                logger.debug(
                    f"Authentication session '{session_type}' expired and cleaned up"
                )

    def try_passwordless_sudo(
        self, cmd: list[str], timeout: int = 30
    ) -> subprocess.CompletedProcess | None:
        """Attempt to run a command with passwordless sudo if we have an active session

        Returns:
            CompletedProcess if successful, None if authentication required
        """
        # First clean up any expired sessions
        self.cleanup_expired_sessions()

        # Only try passwordless if we have a valid session
        if not self.is_session_valid():
            logger.debug("No valid authentication session, skipping passwordless sudo")
            return None

        try:
            result = subprocess.run(
                ["sudo", "-n"] + cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                logger.debug(
                    f"✅ Passwordless sudo successful for: {' '.join(cmd[:3])}..."
                )
                return result
            else:
                logger.debug(
                    f"❌ Passwordless sudo failed (rc={result.returncode}), session may have expired"
                )
                # Mark session as invalid if passwordless sudo fails
                self.end_session()
                return None

        except subprocess.TimeoutExpired:
            logger.debug(f"⏰ Passwordless sudo timed out for: {' '.join(cmd[:3])}...")
            return None
        except Exception as e:
            logger.debug(f"💥 Passwordless sudo error: {e}")
            return None

    def execute_elevated_command(
        self,
        cmd: list[str],
        timeout: int = 300,
        capture_output: bool = True,
        text: bool = True,
        session_type: str = "global",
        operation: str = "command",
    ) -> subprocess.CompletedProcess:
        """Execute a command with elevated privileges using session management

        This is the main method that components should use for elevated commands.
        It handles session management automatically and reduces password prompts.
        """
        from .elevated_runner import elevated_run

        # Clean up expired sessions first
        self.cleanup_expired_sessions()

        # Try passwordless sudo first if we have a valid session
        if self.is_session_valid(session_type):
            passwordless_result = self.try_passwordless_sudo(
                cmd, timeout=min(timeout, 30)
            )
            if passwordless_result is not None:
                return passwordless_result

        # If no valid session or passwordless failed, use elevated_run for GUI authentication
        try:
            logger.debug(f"Requesting GUI authentication for: {operation}")
            result = elevated_run(
                cmd, timeout=timeout, capture_output=capture_output, text=text, gui=True
            )

            # If successful, start/refresh the session
            if result.returncode == 0:
                self.start_session(session_type, operation)
                logger.debug("✅ Authentication successful, session established")

            return result

        except Exception as e:
            logger.error(f"Elevated command execution failed: {e}")
            # Create a failed result
            return subprocess.CompletedProcess(
                cmd, 1, stdout="", stderr=f"Authentication failed: {e}"
            )

    def execute_elevated_file_operation(
        self,
        operation: str,
        file_path: str,
        content: str = None,
        session_type: str = "global",
    ) -> Any:
        """Execute file operations (read/write) with elevated privileges using session management

        Args:
            operation: "read" or "write"
            file_path: Path to the file
            content: Content to write (for write operations)
            session_type: Type of session to use

        Returns:
            String content for read operations, True for successful write operations
        """
        if operation == "read":
            result = self.execute_elevated_command(
                ["cat", file_path],
                session_type=session_type,
                operation=f"file_read_{os.path.basename(file_path)}",
            )
            if result.returncode == 0:
                return result.stdout
            else:
                raise RuntimeError(f"Failed to read file {file_path}: {result.stderr}")

        elif operation == "write":
            if content is None:
                raise ValueError("Content is required for write operations")

            # Use temporary file approach for writes
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".tmp"
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                result = self.execute_elevated_command(
                    ["cp", tmp_path, file_path],
                    session_type=session_type,
                    operation=f"file_write_{os.path.basename(file_path)}",
                )

                if result.returncode == 0:
                    return True
                else:
                    raise RuntimeError(
                        f"Failed to write file {file_path}: {result.stderr}"
                    )
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except BaseException:
                    pass
        else:
            raise ValueError(f"Unknown operation: {operation}")

    @contextmanager
    def session_context(
        self, session_type: str = "global", operation: str = "batch_operation"
    ):
        """Context manager for batch operations that should share authentication

        Usage:
            with auth_manager.session_context("rkhunter_optimization", "RKHunter setup"):
                # Multiple operations here will share authentication
                result1 = auth_manager.execute_elevated_command(['rkhunter', '--version'])
                result2 = auth_manager.execute_elevated_file_operation('read', '/etc/rkhunter.conf')
                # ... more operations
            # Session automatically cleaned up
        """
        self.start_session(session_type, operation)
        try:
            yield self
        finally:
            self.end_session(session_type)

    def get_session_status(self) -> dict[str, Any]:
        """Get current session status for debugging"""
        with self._session_lock:
            status = {
                "global_session_active": self._global_session_active,
                "global_session_start": (
                    self._global_session_start.isoformat()
                    if self._global_session_start
                    else None
                ),
                "active_sessions": {
                    session_type: start_time.isoformat()
                    for session_type, start_time in self._active_sessions.items()
                },
                "session_timeout": self._session_timeout,
            }

            # Add validity information
            if self._global_session_active and self._global_session_start:
                age = (datetime.now() - self._global_session_start).total_seconds()
                status["global_session_age_seconds"] = age
                status["global_session_valid"] = age < self._session_timeout

            return status


# Global singleton instance
auth_manager = AuthenticationSessionManager()


# Convenience functions for easier usage
def is_session_valid(session_type: str = "global") -> bool:
    """Check if authentication session is valid"""
    return auth_manager.is_session_valid(session_type)


def execute_elevated_command(
    cmd: list[str],
    timeout: int = 300,
    session_type: str = "global",
    operation: str = "command",
) -> subprocess.CompletedProcess:
    """Execute elevated command with session management"""
    return auth_manager.execute_elevated_command(
        cmd, timeout, session_type=session_type, operation=operation
    )


def execute_elevated_file_operation(
    operation: str, file_path: str, content: str = None, session_type: str = "global"
) -> Any:
    """Execute elevated file operation with session management"""
    return auth_manager.execute_elevated_file_operation(
        operation, file_path, content, session_type
    )


def session_context(session_type: str = "global", operation: str = "batch_operation"):
    """Context manager for batch operations"""
    return auth_manager.session_context(session_type, operation)
