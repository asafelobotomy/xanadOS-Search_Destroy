#!/usr/bin/env python3
"""
Permission Controller for Unified Security Framework

This module provides comprehensive file system permission management and
privilege escalation for the xanadOS Search & Destroy security framework.

Consolidates functionality from:
- app/utils/permission_manager.py (385 lines) - Permission checking and sudo management
- app/core/elevated_runner.py (150 lines) - Privilege escalation and command execution

Features:
- File system permission checking and caching
- Privilege escalation with GUI authentication
- Secure command execution with elevated privileges
- Permission context management and auditing
- Integration with unified security framework
- Cross-platform permission handling
"""

import logging
import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .unified_security_framework import SecurityConfig, UnifiedSecurityManager


# ================== PERMISSION ENUMERATIONS AND DATA STRUCTURES ==================


class PermissionLevel(Enum):
    """File system permission levels."""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    OWNER = "owner"
    ROOT = "root"


class ElevationMethod(Enum):
    """Methods for privilege escalation."""

    NONE = "none"
    SUDO_GUI = "sudo_gui"
    SUDO_TERMINAL = "sudo_terminal"
    PKEXEC = "pkexec"
    RUNAS = "runas"  # Windows


@dataclass
class PermissionContext:
    """Context for permission operations."""

    path: str
    required_level: PermissionLevel
    operation: str  # read, write, execute, delete, etc.
    user_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    justification: str = ""


@dataclass
class ElevationResult:
    """Result of privilege escalation attempt."""

    success: bool
    method_used: ElevationMethod
    duration_seconds: float = 0.0
    error_message: str = ""
    command_output: str = ""
    return_code: int = 0


@dataclass
class PrivilegedPath:
    """Configuration for privileged paths."""

    path: str
    required_level: PermissionLevel
    description: str
    allow_user_override: bool = False
    requires_justification: bool = False


# ================== PERMISSION CHECKER ==================


class PermissionChecker:
    """
    Enhanced permission checking with caching and security integration.
    """

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PermissionChecker")

        # Permission state and caching
        self._checked_paths: dict[str, tuple[PermissionLevel, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache permission checks for 5 minutes

        # Known privileged paths with enhanced configuration
        self._privileged_paths = [
            PrivilegedPath(
                "/proc", PermissionLevel.ROOT, "Process information", False, True
            ),
            PrivilegedPath(
                "/sys", PermissionLevel.ROOT, "System information", False, True
            ),
            PrivilegedPath("/dev", PermissionLevel.ROOT, "Device files", False, True),
            PrivilegedPath(
                "/root", PermissionLevel.ROOT, "Root home directory", False, True
            ),
            PrivilegedPath("/boot", PermissionLevel.ROOT, "Boot files", False, True),
            PrivilegedPath(
                "/etc", PermissionLevel.ROOT, "System configuration", True, True
            ),
            PrivilegedPath(
                "/var/log", PermissionLevel.ROOT, "System logs", True, False
            ),
            PrivilegedPath(
                "/var/cache", PermissionLevel.ROOT, "System cache", True, False
            ),
            PrivilegedPath(
                "/var/lib", PermissionLevel.ROOT, "System libraries", True, True
            ),
            PrivilegedPath(
                "/var/spool", PermissionLevel.ROOT, "System spool", True, False
            ),
            PrivilegedPath(
                "/usr/local/etc",
                PermissionLevel.ROOT,
                "Local configuration",
                True,
                False,
            ),
            PrivilegedPath(
                "/opt", PermissionLevel.ROOT, "Optional software", True, False
            ),
            PrivilegedPath(
                "/tmp", PermissionLevel.WRITE, "Temporary files", True, False
            ),
            PrivilegedPath(
                "/home", PermissionLevel.READ, "User directories", True, False
            ),
        ]

        # Create path lookup for performance
        self._path_lookup = {p.path: p for p in self._privileged_paths}

        self.logger.info("Permission checker initialized with enhanced security")

    async def check_permission(
        self, path: str, required_level: PermissionLevel
    ) -> tuple[bool, PermissionLevel]:
        """Check if current user has required permission level for path."""
        try:
            # Normalize path
            normalized_path = os.path.normpath(os.path.abspath(path))

            # Check cache first
            cache_key = f"{normalized_path}:{required_level.value}"
            cached_result = self._get_cached_permission(cache_key)
            if cached_result is not None:
                return cached_result

            # Determine actual permission level
            actual_level = await self._determine_permission_level(normalized_path)

            # Check if actual level meets requirement
            has_permission = self._level_meets_requirement(actual_level, required_level)

            # Cache result
            self._cache_permission(cache_key, (has_permission, actual_level))

            return has_permission, actual_level

        except Exception as e:
            self.logger.error(f"Permission check failed for {path}: {e}")
            return False, PermissionLevel.NONE

    async def requires_elevation(self, path: str) -> tuple[bool, PrivilegedPath | None]:
        """Check if path requires privilege elevation."""
        try:
            normalized_path = os.path.normpath(os.path.abspath(path))

            # Check against known privileged paths
            for privileged_path in self._privileged_paths:
                if normalized_path.startswith(privileged_path.path):
                    # Check if current user has sufficient permissions
                    has_permission, _ = await self.check_permission(
                        normalized_path, privileged_path.required_level
                    )
                    if not has_permission:
                        return True, privileged_path

            # Check if path is owned by root or has restrictive permissions
            try:
                stat_info = os.stat(normalized_path)
                if stat_info.st_uid == 0:  # Owned by root
                    # Check if we can actually access it
                    if not os.access(normalized_path, os.R_OK):
                        return True, PrivilegedPath(
                            normalized_path,
                            PermissionLevel.ROOT,
                            "Root-owned file",
                            True,
                            False,
                        )
            except (OSError, PermissionError):
                # If we can't even stat the file, we likely need elevation
                return True, PrivilegedPath(
                    normalized_path, PermissionLevel.ROOT, "Access denied", True, True
                )

            return False, None

        except Exception as e:
            self.logger.error(f"Elevation check failed for {path}: {e}")
            return False, None

    async def _determine_permission_level(self, path: str) -> PermissionLevel:
        """Determine actual permission level for path."""
        try:
            # Check if path exists
            if not os.path.exists(path):
                return PermissionLevel.NONE

            # Check ownership
            stat_info = os.stat(path)
            current_uid = os.getuid()

            if stat_info.st_uid == current_uid:
                return PermissionLevel.OWNER
            elif current_uid == 0:
                return PermissionLevel.ROOT
            elif os.access(path, os.W_OK):
                return PermissionLevel.WRITE
            elif os.access(path, os.X_OK):
                return PermissionLevel.EXECUTE
            elif os.access(path, os.R_OK):
                return PermissionLevel.READ
            else:
                return PermissionLevel.NONE

        except Exception as e:
            self.logger.error(f"Permission level determination failed for {path}: {e}")
            return PermissionLevel.NONE

    def _level_meets_requirement(
        self, actual: PermissionLevel, required: PermissionLevel
    ) -> bool:
        """Check if actual permission level meets requirement."""
        level_hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.EXECUTE: 2,
            PermissionLevel.WRITE: 3,
            PermissionLevel.OWNER: 4,
            PermissionLevel.ROOT: 5,
        }

        return level_hierarchy.get(actual, 0) >= level_hierarchy.get(required, 0)

    def _get_cached_permission(
        self, cache_key: str
    ) -> tuple[bool, PermissionLevel] | None:
        """Get cached permission result if still valid."""
        if cache_key not in self._checked_paths:
            return None

        cached_level, cached_time = self._checked_paths[cache_key]
        if datetime.now() - cached_time > self._cache_ttl:
            del self._checked_paths[cache_key]
            return None

        # Extract required level from cache key
        required_level_str = cache_key.split(":")[1]
        required_level = PermissionLevel(required_level_str)

        has_permission = self._level_meets_requirement(cached_level, required_level)
        return has_permission, cached_level

    def _cache_permission(self, cache_key: str, result: tuple[bool, PermissionLevel]):
        """Cache permission result."""
        _, actual_level = result
        self._checked_paths[cache_key] = (actual_level, datetime.now())

    def clear_cache(self):
        """Clear permission cache."""
        self._checked_paths.clear()
        self.logger.info("Permission cache cleared")


# ================== PRIVILEGE ESCALATION MANAGER ==================


class PrivilegeEscalationManager:
    """
    Secure privilege escalation with multiple authentication methods.
    """

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PrivilegeEscalationManager")

        # Escalation state
        self._active_sessions: dict[str, datetime] = {}
        self._session_timeout = timedelta(seconds=self.config.sudo_timeout_seconds)
        self._failed_attempts: dict[str, int] = {}
        self._max_failed_attempts = 3

        # Available escalation methods (in order of preference)
        self._available_methods = self._detect_available_methods()

        self.logger.info(
            f"Privilege escalation manager initialized with methods: {[m.value for m in self._available_methods]}"
        )

    def _detect_available_methods(self) -> list[ElevationMethod]:
        """Detect available privilege escalation methods."""
        methods = []

        # Check for GUI sudo (preferred)
        if os.environ.get("DISPLAY") and shutil.which("sudo"):
            methods.append(ElevationMethod.SUDO_GUI)

        # Check for terminal sudo
        if shutil.which("sudo"):
            methods.append(ElevationMethod.SUDO_TERMINAL)

        # Check for pkexec (PolicyKit)
        if shutil.which("pkexec"):
            methods.append(ElevationMethod.PKEXEC)

        # Check for Windows runas
        if os.name == "nt" and shutil.which("runas"):
            methods.append(ElevationMethod.RUNAS)

        return methods

    async def elevate_command(
        self,
        command: Sequence[str],
        context: PermissionContext | None = None,
        preferred_method: ElevationMethod | None = None,
        timeout: int = 300,
    ) -> ElevationResult:
        """Execute command with elevated privileges."""
        try:
            if not command:
                return ElevationResult(
                    success=False,
                    method_used=ElevationMethod.NONE,
                    error_message="No command provided",
                )

            # Check if elevation is actually needed
            if not self.config.require_sudo_for_privileged:
                return await self._execute_without_elevation(command, timeout)

            # Determine best escalation method
            method = (
                preferred_method
                if preferred_method in self._available_methods
                else self._available_methods[0]
            )

            # Check rate limiting and failed attempts
            session_key = f"{context.user_id if context else 'unknown'}:{method.value}"
            if not self._can_attempt_escalation(session_key):
                return ElevationResult(
                    success=False,
                    method_used=method,
                    error_message="Too many failed attempts or rate limited",
                )

            # Execute with chosen method
            start_time = datetime.now()

            if method == ElevationMethod.SUDO_GUI:
                result = await self._execute_sudo_gui(command, timeout)
            elif method == ElevationMethod.SUDO_TERMINAL:
                result = await self._execute_sudo_terminal(command, timeout)
            elif method == ElevationMethod.PKEXEC:
                result = await self._execute_pkexec(command, timeout)
            else:
                result = ElevationResult(
                    success=False,
                    method_used=method,
                    error_message=f"Escalation method {method.value} not implemented",
                )

            # Update timing
            result.duration_seconds = (datetime.now() - start_time).total_seconds()

            # Handle result
            if result.success:
                self._record_successful_escalation(session_key)
            else:
                self._record_failed_escalation(session_key)

            return result

        except Exception as e:
            self.logger.error(f"Command elevation failed: {e}")
            return ElevationResult(
                success=False,
                method_used=preferred_method or ElevationMethod.NONE,
                error_message=f"Elevation failed: {e!s}",
            )

    async def _execute_without_elevation(
        self, command: Sequence[str], timeout: int
    ) -> ElevationResult:
        """Execute command without elevation."""
        try:
            result = subprocess.run(
                command, timeout=timeout, capture_output=True, text=True, check=False
            )

            return ElevationResult(
                success=result.returncode == 0,
                method_used=ElevationMethod.NONE,
                command_output=result.stdout,
                error_message=result.stderr if result.returncode != 0 else "",
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.NONE,
                error_message="Command timed out",
            )
        except Exception as e:
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.NONE,
                error_message=f"Execution failed: {e!s}",
            )

    async def _execute_sudo_gui(
        self, command: Sequence[str], timeout: int
    ) -> ElevationResult:
        """Execute command using GUI sudo authentication."""
        try:
            # Use unified security framework for GUI elevation
            try:
                from .security_integration import elevate_privileges

                result = elevate_privileges(
                    user_id="permission_controller",
                    operation=f"Execute command: {' '.join(command)}",
                    command=list(command),
                    use_gui=True,
                    timeout=timeout,
                )

                return ElevationResult(
                    success=result.success,
                    method_used=ElevationMethod.SUDO_GUI,
                    command_output=result.stdout,
                    error_message=result.error_output if not result.success else "",
                    return_code=result.return_code,
                )

            except ImportError:
                self.logger.warning("GUI authentication manager not available")
                return ElevationResult(
                    success=False,
                    method_used=ElevationMethod.SUDO_GUI,
                    error_message="GUI authentication not available",
                )

        except Exception as e:
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.SUDO_GUI,
                error_message=f"GUI sudo failed: {e!s}",
            )

    async def _execute_sudo_terminal(
        self, command: Sequence[str], timeout: int
    ) -> ElevationResult:
        """Execute command using terminal sudo."""
        try:
            sudo_command = ["sudo", "-S"] + list(command)

            result = subprocess.run(
                sudo_command,
                timeout=timeout,
                capture_output=True,
                text=True,
                input="",  # No password input for non-interactive
                check=False,
            )

            return ElevationResult(
                success=result.returncode == 0,
                method_used=ElevationMethod.SUDO_TERMINAL,
                command_output=result.stdout,
                error_message=result.stderr if result.returncode != 0 else "",
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.SUDO_TERMINAL,
                error_message="Sudo command timed out",
            )
        except Exception as e:
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.SUDO_TERMINAL,
                error_message=f"Terminal sudo failed: {e!s}",
            )

    async def _execute_pkexec(
        self, command: Sequence[str], timeout: int
    ) -> ElevationResult:
        """Execute command using pkexec (PolicyKit)."""
        try:
            pkexec_command = ["pkexec"] + list(command)

            result = subprocess.run(
                pkexec_command,
                timeout=timeout,
                capture_output=True,
                text=True,
                check=False,
            )

            return ElevationResult(
                success=result.returncode == 0,
                method_used=ElevationMethod.PKEXEC,
                command_output=result.stdout,
                error_message=result.stderr if result.returncode != 0 else "",
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.PKEXEC,
                error_message="Pkexec command timed out",
            )
        except Exception as e:
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.PKEXEC,
                error_message=f"Pkexec failed: {e!s}",
            )

    def _can_attempt_escalation(self, session_key: str) -> bool:
        """Check if escalation attempt is allowed."""
        # Check failed attempts
        if self._failed_attempts.get(session_key, 0) >= self._max_failed_attempts:
            return False

        # Check active session timeout
        if session_key in self._active_sessions:
            last_attempt = self._active_sessions[session_key]
            if datetime.now() - last_attempt < self._session_timeout:
                return True  # Within session timeout
            else:
                del self._active_sessions[session_key]

        return True

    def _record_successful_escalation(self, session_key: str):
        """Record successful escalation attempt."""
        self._active_sessions[session_key] = datetime.now()
        if session_key in self._failed_attempts:
            del self._failed_attempts[session_key]

    def _record_failed_escalation(self, session_key: str):
        """Record failed escalation attempt."""
        self._failed_attempts[session_key] = (
            self._failed_attempts.get(session_key, 0) + 1
        )
        self.logger.warning(
            f"Failed escalation attempt for {session_key}: {self._failed_attempts[session_key]}"
        )


# ================== PERMISSION CONTROLLER ==================


class PermissionController:
    """
    Central permission management controller integrating all permission operations.
    """

    def __init__(
        self,
        config: SecurityConfig | None = None,
        security_manager: UnifiedSecurityManager | None = None,
    ):
        self.config = config or SecurityConfig()
        self.security_manager = security_manager
        self.logger = logging.getLogger(f"{__name__}.PermissionController")

        # Initialize components
        self.permission_checker = PermissionChecker(self.config)
        self.escalation_manager = PrivilegeEscalationManager(self.config)

        # Permission operation tracking
        self._operation_history: list[tuple[PermissionContext, ElevationResult]] = []
        self._max_history = 1000

        self.logger.info("Permission controller initialized")

    async def request_access(
        self,
        path: str,
        operation: str,
        required_level: PermissionLevel = PermissionLevel.READ,
        user_id: str | None = None,
        justification: str = "",
    ) -> tuple[bool, ElevationResult | None]:
        """Request access to path with specified permission level."""
        try:
            # Create permission context
            context = PermissionContext(
                path=path,
                required_level=required_level,
                operation=operation,
                user_id=user_id,
                justification=justification,
            )

            # Check current permissions
            has_permission, actual_level = (
                await self.permission_checker.check_permission(path, required_level)
            )

            if has_permission:
                # Permission already available
                self.logger.info(
                    f"Access granted to {path} for {operation} (current level: {actual_level.value})"
                )
                return True, None

            # Check if elevation is required and possible
            needs_elevation, _ = await self.permission_checker.requires_elevation(path)

            if not needs_elevation:
                # Permission denied but elevation not required - likely a bug
                self.logger.warning(
                    f"Access denied to {path} but elevation not required"
                )
                return False, None

            # Request privilege escalation
            self.logger.info(
                f"Requesting elevation for {path} ({operation}): {justification}"
            )

            # Create command to check access (dummy command for permission testing)
            test_command = [
                "test",
                "-r" if required_level == PermissionLevel.READ else "-w",
                path,
            ]

            elevation_result = await self.escalation_manager.elevate_command(
                test_command, context=context
            )

            # Record operation
            self._record_operation(context, elevation_result)

            # Audit the permission request
            if self.security_manager:
                await self.security_manager._audit_event(
                    event_type="permission_request",
                    action=operation,
                    result="success" if elevation_result.success else "failure",
                    user_id=user_id,
                    resource=path,
                    additional_data={
                        "required_level": required_level.value,
                        "elevation_method": elevation_result.method_used.value,
                        "justification": justification,
                    },
                )

            return elevation_result.success, elevation_result

        except Exception as e:
            self.logger.error(f"Access request failed for {path}: {e}")
            return False, None

    async def execute_privileged_command(
        self,
        command: Sequence[str],
        user_id: str | None = None,
        justification: str = "",
        timeout: int = 300,
    ) -> ElevationResult:
        """Execute command with elevated privileges."""
        try:
            context = PermissionContext(
                path="command_execution",
                required_level=PermissionLevel.ROOT,
                operation="execute",
                user_id=user_id,
                justification=justification,
            )

            self.logger.info(f"Executing privileged command: {' '.join(command)}")

            result = await self.escalation_manager.elevate_command(
                command, context=context, timeout=timeout
            )

            # Record operation
            self._record_operation(context, result)

            # Audit the command execution
            if self.security_manager:
                await self.security_manager._audit_event(
                    event_type="privileged_execution",
                    action="execute_command",
                    result="success" if result.success else "failure",
                    user_id=user_id,
                    resource=" ".join(command),
                    additional_data={
                        "elevation_method": result.method_used.value,
                        "return_code": result.return_code,
                        "duration": result.duration_seconds,
                        "justification": justification,
                    },
                )

            return result

        except Exception as e:
            self.logger.error(f"Privileged command execution failed: {e}")
            return ElevationResult(
                success=False,
                method_used=ElevationMethod.NONE,
                error_message=f"Command execution failed: {e!s}",
            )

    async def check_path_permissions(
        self, paths: list[str]
    ) -> dict[str, tuple[bool, PermissionLevel]]:
        """Check permissions for multiple paths."""
        results = {}

        for path in paths:
            try:
                has_read, level = await self.permission_checker.check_permission(
                    path, PermissionLevel.READ
                )
                results[path] = (has_read, level)
            except Exception as e:
                self.logger.error(f"Permission check failed for {path}: {e}")
                results[path] = (False, PermissionLevel.NONE)

        return results

    def _record_operation(self, context: PermissionContext, result: ElevationResult):
        """Record permission operation for auditing."""
        self._operation_history.append((context, result))

        # Trim history if needed
        if len(self._operation_history) > self._max_history:
            self._operation_history = self._operation_history[-self._max_history :]

    def get_operation_history(
        self, limit: int = 100
    ) -> list[tuple[PermissionContext, ElevationResult]]:
        """Get recent permission operations."""
        return self._operation_history[-limit:]

    def clear_caches(self):
        """Clear all permission caches."""
        self.permission_checker.clear_cache()
        self.logger.info("Permission caches cleared")


# ================== LEGACY COMPATIBILITY FUNCTIONS ==================


async def elevated_run(
    argv: Sequence[str],
    *,
    timeout: int = 300,
    capture_output: bool = True,
    text: bool = True,
    gui: bool = True,
) -> subprocess.CompletedProcess:
    """Legacy compatibility function for elevated_run."""
    # Create a temporary permission controller
    config = SecurityConfig()
    controller = PermissionController(config)

    # Execute the command
    result = await controller.execute_privileged_command(
        argv, timeout=timeout, justification="Legacy elevated_run call"
    )

    # Convert to subprocess.CompletedProcess format
    return subprocess.CompletedProcess(
        argv, result.return_code, result.command_output, result.error_message
    )


def requires_root_access(path: str) -> bool:
    """Legacy compatibility function for permission checking."""
    import asyncio

    # Create a temporary permission controller
    config = SecurityConfig()
    controller = PermissionController(config)

    # Check if elevation is required
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        needs_elevation, _ = loop.run_until_complete(
            controller.permission_checker.requires_elevation(path)
        )
        return needs_elevation
    finally:
        loop.close()


# Export public API
__all__ = [
    "ElevationMethod",
    "ElevationResult",
    "PermissionChecker",
    "PermissionContext",
    "PermissionController",
    "PermissionLevel",
    "PrivilegeEscalationManager",
    "PrivilegedPath",
    "elevated_run",
    "requires_root_access",
]
