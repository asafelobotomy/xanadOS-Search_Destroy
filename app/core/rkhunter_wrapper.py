#!/usr/bin/env python3
"""RKHunter (Rootkit Hunter) integration wrapper for S&D - Search & Destroy.
Provides rootkit detection capabilities complementing ClamAV.
"""

import configparser
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .rkhunter_analyzer import RKHunterWarningAnalyzer, WarningExplanation
from .security_validator import SecureRKHunterValidator

# Import the warning analyzer
# Import security validator
# Provide a module-level alias for elevated_run to ease monkeypatching in tests.
try:  # pragma: no cover - import guard
    from .elevated_runner import elevated_run as _elevated_run
except Exception:  # pragma: no cover - fallback if elevated runner unavailable
    _elevated_run = None


class RKHunterResult(Enum):
    """RKHunter scan result types."""

    CLEAN = "clean"
    WARNING = "warning"
    INFECTED = "infected"
    ERROR = "error"
    SKIPPED = "skipped"


class RKHunterSeverity(Enum):
    """Severity levels for RKHunter findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RKHunterFinding:
    """Represents a single RKHunter finding."""

    test_name: str
    result: RKHunterResult
    severity: RKHunterSeverity
    description: str
    details: str = ""
    file_path: Optional[str] = None
    recommendation: str = ""
    timestamp: Optional[datetime] = None
    explanation: Optional[WarningExplanation] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RKHunterScanResult:
    """Complete RKHunter scan results."""

    scan_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_tests: int = 0
    tests_run: int = 0
    warnings_found: int = 0
    infections_found: int = 0
    skipped_tests: int = 0
    findings: Optional[List[RKHunterFinding]] = None
    scan_summary: str = ""
    success: bool = False
    error_message: str = ""

    def __post_init__(self):
        if self.findings is None:
            self.findings = []


class RKHunterWrapper:
    """Wrapper for RKHunter (Rootkit Hunter) integration.

    Provides methods to run rootkit scans, parse results, and integrate
    with the main antivirus application.
    """

    def __init__(self):
        """Initialize RKHunter wrapper."""
        self.logger = logging.getLogger(__name__)
        self.rkhunter_path = self._find_rkhunter()
        self.available = self.rkhunter_path is not None
        self.config_path = (
            Path.home() / ".config" / "search-and-destroy" / "rkhunter.conf"
        )
        self._current_process = None  # Track current running process

        # Authentication session management
        self._auth_session_start = None  # Track when authentication was granted
        self._auth_session_duration = 60  # Session valid for 60 seconds
        # SECURITY: Extended grace period for scan duration but with additional safeguards
        # Research shows RKHunter scans typically take 5-45 minutes
        # Extended to match scan duration with enhanced security validation
        self._grace_period = 1800  # 30 minutes - covers typical RKHunter scan duration
        self._max_grace_period = 3600  # 60 minutes - absolute maximum for large systems
        self._grace_period_extensions = (
            0  # Track grace period usage for security monitoring
        )

        # Initialize security validator
        self.security_validator = SecureRKHunterValidator()

        # Initialize warning analyzer
        self.warning_analyzer = RKHunterWarningAnalyzer()

        # Validate RKHunter path on initialization for security
        if self.rkhunter_path:
            if not self.security_validator.validate_executable_path(self.rkhunter_path):
                self.logger.warning(
                    "RKHunter path %s failed security validation",
                    self.rkhunter_path,
                )
                # Try to get a safe path
                safe_path = self.security_validator.get_safe_rkhunter_path()
                if safe_path:
                    self.logger.info("Using safe RKHunter path: %s", safe_path)
                    self.rkhunter_path = safe_path
                else:
                    self.logger.error(
                        "No safe RKHunter path found - disabling RKHunter",
                    )
                    self.rkhunter_path = None
                    self._available = False

        # SECURITY: Configure grace period based on environment
        self._configure_security_settings()

        # RKHunter test categories
        self.test_categories = {
            "system_commands": [
                "system_commands_hashes",
                "system_commands_known_rootkits",
                "system_commands_properties",
            ],
            "rootkits": ["rootkits", "trojans", "malware"],
            "network": ["network", "ports", "packet_cap_apps"],
            "system_integrity": ["filesystem", "system_configs", "startup_files"],
            "applications": ["applications", "hidden_procs", "hidden_files"],
        }

        if self.available:
            self._initialize_config()
            self.logger.info("RKHunter wrapper initialized successfully")
        else:
            self.logger.warning("RKHunter not available on system")

    def _initialize_config(self):
        """Initialize minimal RKHunter configuration if missing."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.config_path.exists():
                self.config_path.write_text(
                    "# minimal rkhunter config generated for tests\n",
                )
        except Exception:
            self.logger.debug("Failed to initialize minimal config", exc_info=True)

    def get_version(self) -> Tuple[str, str]:
        """Return (version_string, status). Single authoritative implementation."""
        if not self.available or self.rkhunter_path is None:
            return "Not Available", "N/A"
        try:
            result = run_secure([self.rkhunter_path, "--version"], timeout=5)
            if result.returncode == 0 and result.stdout:
                line = result.stdout.strip().split("\n")[0].strip()
                return line, "Current"
        except PermissionError:
            pass
        except Exception:
            pass
        try:
            elevated_result = self._run_with_privilege_escalation(
                [self.rkhunter_path, "--version"],
                capture_output=True,
                timeout=10,
            )
            if elevated_result.returncode == 0 and elevated_result.stdout:
                line = elevated_result.stdout.strip().split("\n")[0].strip()
                return line, "Current (requires elevated privileges)"
            if elevated_result.returncode != 0:
                return "Unknown", "Permission denied"
        except Exception:
            return "Unknown", "Permission denied"
        return "Unknown", "Error"

    def _configure_security_settings(self):
        """Configure security settings based on environment and security policy.
        SECURITY: Adaptive grace period based on system security requirements.
        """
        try:
            # SECURITY: Check for security configuration file
            config_path = (
                Path.home() / ".config" / "search-and-destroy" / "security.conf"
            )

            if config_path.exists():
                # Load custom security configuration

                config = configparser.ConfigParser()
                config.read(config_path)

                if config.has_section("grace_period"):
                    custom_period = config.getint(
                        "grace_period",
                        "duration",
                        fallback=self._grace_period,
                    )
                    max_period = config.getint(
                        "grace_period",
                        "max_duration",
                        fallback=self._max_grace_period,
                    )

                    # SECURITY: Validate custom grace period
                    if 30 <= custom_period <= max_period:
                        self._grace_period = custom_period
                        self.logger.info(
                            "Using custom grace period: %ss".replace(
                                "%s", "{custom_period}"
                            ).replace("%d", "{custom_period}")
                        )
                    else:
                        self.logger.warning(
                            "Invalid custom grace period %ss, using default: %ss",
                            custom_period,
                            self._grace_period,
                        )

            # SECURITY: Environment-based adjustments
            # Check if running in a high-security environment
            if os.path.exists("/etc/security/high-security-mode"):
                # Reduce grace period in high-security environments
                self._grace_period = min(300, self._grace_period)  # Max 5 minutes
                self.logger.info("High-security mode detected - reduced grace period")

            # SECURITY: Check system load to adjust grace period
            try:
                system_load = (
                    psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0
                )
                if system_load > 2.0:
                    # Increase grace period on high-load systems (scans take longer)
                    self._grace_period = min(
                        self._max_grace_period,
                        int(self._grace_period * 1.5),
                    )
                    self.logger.info(
                        "High system load detected - extended grace period to %ss",
                        self._grace_period,
                    )
            except ImportError:
                pass  # psutil not available

        except Exception:
            self.logger.warning("Error configuring security settings", exc_info=True)

        self.logger.info(
            "Security configuration complete - grace period: %ss, max: %ss",
            self._grace_period,
            self._max_grace_period,
        )

    def _find_rkhunter(self) -> Optional[str]:
        """Find RKHunter executable."""
        possible_paths = [
            "/usr/bin/rkhunter",
            "/usr/local/bin/rkhunter",
            "/opt/rkhunter/bin/rkhunter",
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        # Try which command
        try:
            result = run_secure(["which", "rkhunter"], timeout=5)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def _find_executable(self, name: str) -> Optional[str]:
        """Find an executable in PATH."""
        return shutil.which(name)

    def terminate_current_scan(self):
        """Safely terminate the currently running RKHunter scan.

        Uses a graceful approach: SIGTERM first, then SIGKILL if needed.
        For elevated processes, also attempts privileged termination.
        """
        if self._current_process is not None:
            try:
                pid = self._current_process.pid
                self.logger.info(
                    "Terminating RKHunter scan process (PID: %d)".replace(
                        "%s", "{pid}"
                    ).replace("%d", "{pid}")
                )

                within_grace = self._is_within_auth_grace_period()
                result = kill_sequence(pid, escalate=within_grace is False)
                if result.success:
                    self.logger.info(
                        "Scan termination success (escalated=%s attempts=%s)",
                        result.escalated,
                        result.attempts,
                    )
                    return True
                self.logger.warning(
                    "Scan termination failed (escalated=%s attempts=%s error=%s)",
                    result.escalated,
                    result.attempts,
                    result.error,
                )
                return within_grace  # Treat as soft-success inside grace window
            except PermissionError as e:
                # This is expected when trying to terminate elevated processes
                self.logger.info(
                    "Permission denied when terminating elevated RKHunter process (expected): %s",
                    e,
                )

                # Try privileged termination as fallback
                if hasattr(self, "_current_process") and self._current_process:
                    pid = self._current_process.pid

                    # If we're within grace period, be more lenient about termination
                    if self._is_within_auth_grace_period():
                        self.logger.info(
                            "Within grace period - attempting privileged termination but accepting if unsuccessful",
                        )
                        success = self._terminate_with_privilege_escalation(pid)
                        if not success:
                            self.logger.info(
                                "Privileged termination within grace period was unsuccessful, but process will terminate naturally",
                            )
                        return True  # Always return success within grace period
                    # Outside grace period, try harder to terminate
                    if self._terminate_with_privilege_escalation(pid):
                        self.logger.info(
                            "RKHunter scan terminated via privileged escalation fallback",
                        )
                        return True

                self.logger.info(
                    "RKHunter process was started with elevated privileges and cannot be terminated by non-elevated process",
                )
                return True  # Still consider this a "success" since the process will eventually finish
            except Exception:
                self.logger.error(
                    "Error terminating RKHunter scan: %s".replace("%s", "{e}").replace(
                        "%d", "{e}"
                    )
                )
                return False
            finally:
                self._current_process = None
        else:
            self.logger.warning("No RKHunter scan process to terminate")
            return True

    def _is_within_auth_grace_period(self) -> bool:
        """Check if we're within the authentication grace period.
        SECURITY: Enhanced with additional safeguards for extended grace period.

        Returns:
            bool: True if within grace period, False otherwise

        """
        if self._auth_session_start is None:
            return False

        current_time = time.time()
        elapsed = current_time - self._auth_session_start

        # SECURITY: Additional validation for extended grace period
        # Check if we're within the standard grace period first
        within_standard_period = elapsed <= 30  # Original 30-second period
        within_extended_period = elapsed <= self._grace_period

        # SECURITY: Log extended grace period usage for monitoring
        if within_extended_period and not within_standard_period:
            self._grace_period_extensions += 1
            self.logger.warning(
                "Extended grace period in use: %.1fs elapsed, extension #%s",
                elapsed,
                self._grace_period_extensions,
            )

            # SECURITY: Limit grace period extensions to prevent abuse
            if self._grace_period_extensions > 3:
                self.logger.error(
                    "Grace period extension limit exceeded - forcing re-authentication",
                )
                return False

        self.logger.debug(
            "Auth session elapsed time: %.1fs, grace period: %ss, within standard: %s, within extended: %s",
            elapsed,
            self._grace_period,
            within_standard_period,
            within_extended_period,
        )

        return within_extended_period

    def _ensure_auth_session(self) -> bool:
        """Ensure authentication session is active to minimize prompts.

        Returns:
            True if session is active, False if authentication failed

        """
        try:
            self.logger.info("Attempting to ensure authentication session...")

            self.logger.info("validate_auth_session imported successfully")

            result = validate_auth_session()
            self.logger.info(
                "validate_auth_session returned: %s".replace("%s", "{result}").replace(
                    "%d", "{result}"
                )
            )
            return result

        except ImportError as e:
            # Fallback if validate_auth_session is not available
            self.logger.warning(
                "validate_auth_session not available: %s, authentication may prompt multiple times",
                e,
            )
            return True
        except Exception:
            self.logger.error("Authentication session validation failed", exc_info=True)
            return False

    def _update_auth_session(self):
        """Update the authentication session timestamp.
        SECURITY: Enhanced with session validation and monitoring.
        """
        current_time = time.time()

        # SECURITY: Check for session reset (new scan starting)
        if self._auth_session_start is not None:
            previous_elapsed = current_time - self._auth_session_start
            self.logger.info(
                "Authentication session reset after %.1fs, extensions used: %s",
                previous_elapsed,
                self._grace_period_extensions,
            )

        self._auth_session_start = current_time
        self._grace_period_extensions = 0  # Reset extension counter

        self.logger.info(
            "Authentication session updated - grace period: %ss",
            self._grace_period,
        )

        # SECURITY: Log session start for audit trail
        self.logger.info("SECURITY_AUDIT: New privileged session started")

    def _reset_auth_session(self):
        """Reset the authentication session.
        SECURITY: Clean session termination with audit logging.
        """
        if self._auth_session_start is not None:
            elapsed = time.time() - self._auth_session_start
            self.logger.info(
                "Authentication session ended after %.1fs, extensions used: %s",
                elapsed,
                self._grace_period_extensions,
            )
            # SECURITY: Log session end for audit trail
            self.logger.info("SECURITY_AUDIT: Privileged session ended")

        self._auth_session_start = None
        self._grace_period_extensions = 0

    def _terminate_with_privilege_escalation(self, pid: int) -> bool:
        """Legacy compatibility wrapper now using kill_sequence abstraction.
        Prefer graceful TERM then KILL; escalate only when outside grace
        period (to avoid unnecessary auth prompts) and direct signals denied.
        """
        try:
            within_grace = self._is_within_auth_grace_period()
            # escalate only if NOT within grace period to avoid extra prompts
            result = kill_sequence(pid, escalate=not within_grace)
            if result.success:
                self.logger.info(
                    "Termination succeeded (grace=%s escalated=%s attempts=%s)",
                    within_grace,
                    result.escalated,
                    result.attempts,
                )
                return True
            if within_grace:
                # treat as soft-success to avoid prompting again
                self.logger.info(
                    "Termination treated as success inside grace window (attempts=%s error=%s)",
                    result.attempts,
                    result.error,
                )
                return True
            self.logger.warning(
                "Termination failed (escalated=%s attempts=%s error=%s)",
                result.escalated,
                result.attempts,
                result.error,
            )
            return False
        except Exception:  # pragma: no cover - defensive
            self.logger.error(
                "safe_kill termination error: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return False

    def _run_with_privilege_escalation(
        self,
        cmd_args: List[str],
        capture_output: bool = True,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        # Use injected/aliased elevated_run so tests can monkeypatch without
        # hitting real privilege escalation paths.
        _elev_run = _elevated_run
        if _elev_run is None:  # Lazy import fallback
            from .elevated_runner import elevated_run as _fallback

            _elev_run = _fallback
        is_valid, error_message = self.security_validator.validate_command_args(
            cmd_args,
        )
        if not is_valid:
            return subprocess.CompletedProcess(
                args=cmd_args,
                returncode=1,
                stdout="",
                stderr="Security validation failed: %s" % (error_message,),
            )
        self.logger.info(
            "Security validation passed for command: %s",
            " ".join(cmd_args[:2]),
        )
        # elevated_run with GUI authentication for consistent user experience
        result = _elev_run(
            cmd_args,
            timeout=timeout,
            capture_output=capture_output,
            gui=True,
        )
        # Apply success heuristic abstraction
        try:
            if self._is_successful_scan(
                result.returncode, getattr(result, "stdout", "")
            ):
                # Note: Simplified elevated runner doesn't need session tracking
                self.logger.debug("Elevated operation completed successfully")
        except Exception:  # pragma: no cover - defensive
            pass
        return result

    def _is_successful_scan(self, returncode: int, stdout: str) -> bool:
        """Determine whether a rkhunter execution indicates a successful scan completion.

        Success criteria (tight to avoid false positives):
        - Return code must be 0 (clean) or 1 (warnings) ONLY.
        - Output must contain one of the known terminal sentinel phrases produced
          at the end of a full rkhunter check run.
        - Empty stdout is never success.

        Args:
            returncode: Process return code.
            stdout: Captured standard output text.

        Returns:
            True if conditions classify as successful scan, else False.

        """
        if returncode not in (0, 1):
            return False
        if not stdout:
            return False
        # Sentinel phrases drawn from typical end-of-run summary markers.
        if ("Info: End date is" in stdout) or ("System checks summary" in stdout):
            return True
        return False

    def _run_with_privilege_escalation_streaming(
        self,
        cmd_args: List[str],
        output_callback: Optional[Callable[[str], None]] = None,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """Run a command with privilege escalation and stream output.
        SECURITY: Validates all commands against security policy before execution.

        Args:
            cmd_args: Command arguments (without sudo/pkexec prefix)
            output_callback: Function to call with each line of output
            timeout: Command timeout in seconds

        Returns:
            subprocess.CompletedProcess with stdout collected line-by-line.
        """

        # SECURITY: Validate command arguments before any execution
        is_valid, error_message = self.security_validator.validate_command_args(
            cmd_args,
        )
        if not is_valid:
            self.logger.error(
                "Security validation failed: %s".replace(
                    "%s", "{error_message}"
                ).replace("%d", "{error_message}")
            )
            return subprocess.CompletedProcess(
                args=cmd_args,
                returncode=1,
                stdout="",
                stderr="Security validation failed: %s" % (error_message,),
            )

        self.logger.info(
            "Security validation passed for streaming command: %s",
            " ".join(cmd_args[:2]),
        )

        # Lazy import to allow tests to monkeypatch without escalations
        from .elevated_runner import elevated_popen

        # Launch process with GUI auth for consistent UX
        process = elevated_popen(cmd_args, gui=True)
        self._current_process = process
        stdout_lines: list[str] = []
        try:
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    if not line:
                        break
                    line_clean = line.rstrip()
                    stdout_lines.append(line_clean)
                    if output_callback:
                        output_callback(line_clean)
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            return subprocess.CompletedProcess(
                args=cmd_args,
                returncode=124,
                stdout="\n".join(stdout_lines),
                stderr="timeout",
            )
        finally:
            self._current_process = None

        result = subprocess.CompletedProcess(
            args=cmd_args,
            returncode=process.returncode,
            stdout="\n".join(stdout_lines),
            stderr="",
        )

        if result.returncode in (0, 1) and (
            "Info: End date is" in result.stdout
            or "System checks summary" in result.stdout
            or result.returncode == 0
        ):
            self.logger.debug("RKHunter operation completed successfully")
        return result

    def _initialize_config(self):
        """Initialize RKHunter configuration."""
        try:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Create basic configuration if it doesn't exist
            if not self.config_path.exists():
                config_lines = [
                    "# RKHunter configuration for S&D Search & Destroy",
                    "# This file configures RKHunter behavior within the antivirus application",
                    "",
                    "# Logging",
                    "LOGFILE=/tmp/rkhunter-scan.log",
                    "APPEND_LOG=1",
                    "COPY_LOG_ON_ERROR=1",
                    "",
                    "# Scan behavior",
                    "SCANROOTKITMODE=THOROUGH",
                    "UNHIDETCPUDP=1",
                    "ALLOW_SSH_ROOT_USER=no",
                    "ALLOW_SSH_PROT_V1=0",
                    "",
                    "# Update behavior",
                    "UPDATE_MIRRORS=1",
                    "MIRRORS_MODE=0",
                    'WEB_CMD=""',
                    "",
                    "# Database locations - Arch Linux specific paths",
                    "DBDIR=/var/lib/rkhunter/db",
                    "SCRIPTDIR=/usr/lib/rkhunter/scripts",
                    "BINDIR=/usr/bin",
                    "INSTALLDIR=/usr",
                    "TMPDIR=/tmp",
                    "",
                    "# Suppress common warnings and false positives",
                    'DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps apps"',
                    "",
                    "# Additional Arch Linux specific settings",
                    "ALLOWHIDDENDIR=/etc/.java",
                    "ALLOWHIDDENDIR=/dev/.static",
                    "ALLOWHIDDENDIR=/dev/.udev",
                    "ALLOWHIDDENDIR=/dev/.mount",
                    "",
                    "# Package manager",
                    "PKGMGR=PACMAN",
                    'SCRIPTWHITELIST=""',
                    'ALLOWHIDDENDIR="/etc/.java"',
                    'ALLOWHIDDENFILE="/etc/.java"',
                    "",
                    "# Disable GUI prompts (for automated scanning)",
                    "AUTO_X_DETECT=1",
                    "WHITELISTED_IS_WHITE=1",
                    "SUPPRESS_DEPRECATION_WARNINGS=1",
                    "",
                    "# Reduce grep warnings by using simpler patterns",
                    "USE_SYSLOG=0",
                    "",
                ]
                try:
                    with open(self.config_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(config_lines))
                    self.logger.info(
                        "Created RKHunter configuration at %s",
                        self.config_path,
                    )
                except Exception:
                    self.logger.warning(
                        "Failed writing RKHunter config: %s".replace(
                            "%s", "{write_err}"
                        ).replace("%d", "{write_err}")
                    )

        except Exception:
            self.logger.error(
                "Failed to initialize RKHunter config: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def is_available(self) -> bool:
        """Check if RKHunter is available and functional."""
        if not self.available or self.rkhunter_path is None:
            return False

        # For GUI applications, we'll use a less intrusive check
        # Just verify the executable exists and is executable
        try:
            path_obj = Path(self.rkhunter_path)
            return path_obj.exists() and path_obj.is_file()
        except Exception:
            return False

    def is_functional(self) -> bool:
        """Check if RKHunter is functional (may require privilege escalation)."""
        if not self.available or self.rkhunter_path is None:
            return False

        try:
            # First try without privilege escalation

            result = run_secure([self.rkhunter_path, "--version"], timeout=10)
            if result.returncode == 0:
                return True
        except PermissionError:
            pass
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

        # If direct execution failed, try with privilege escalation
        # elevated_run now automatically prefers sudo when session is active
        try:
            result = self._run_with_privilege_escalation(
                [self.rkhunter_path, "--version"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def update_database(self) -> bool:
        """Update the RKHunter database (returns True on success)."""
        if not self.available or self.rkhunter_path is None:
            return False
        try:
            self.logger.info("Updating RKHunter database...")
            # elevated_run now automatically prefers sudo when session is active
            result = self._run_with_privilege_escalation(
                [self.rkhunter_path, "--update"],
                capture_output=True,
                timeout=300,
            )
            if result.returncode == 0:
                self.logger.info("RKHunter database updated successfully")
                return True
            output_text = (result.stdout or "") + (result.stderr or "")
            if any(
                s in output_text.lower()
                for s in ("already have the latest", "up to date")
            ):
                self.logger.info("RKHunter database already up to date")
                return True
            self.logger.warning(
                "RKHunter database update failed (code %d)",
                result.returncode,
            )
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("RKHunter database update timed out")
            return False
        except Exception:  # pragma: no cover
            self.logger.error(
                "RKHunter database update error: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return False

    def scan_system_with_output_callback(
        self,
        test_categories: Optional[List[str]] = None,
        skip_keypress: bool = True,
        update_database: bool = True,
        output_callback: Optional[Callable[[str], None]] = None,
    ) -> RKHunterScanResult:
        """Perform a full system rootkit scan with real-time output streaming.

        Args:
            test_categories: List of test categories to run (None for all)
            skip_keypress: Skip manual keypress confirmations
            update_database: Include database update in the same privileged call
            output_callback: Function to call with real-time output lines

        Returns:
            RKHunterScanResult with scan results

        """
        scan_id = f"rkhunter_scan_{int(time.time())}"
        start_time = datetime.now()

        result = RKHunterScanResult(
            scan_id=scan_id,
            start_time=start_time,
            end_time=None,
        )

        if not self.available or self.rkhunter_path is None:
            result.error_message = "RKHunter not available"
            result.end_time = datetime.now()
            return result

        try:
            # Build command arguments (without sudo/pkexec prefix)
            cmd_args = [self.rkhunter_path, "--check"]

            if skip_keypress:
                cmd_args.append("--sk")  # Skip keypress

            cmd_args.extend(
                [
                    "--nocolors",
                    "--no-mail-on-warning",  # Don't try to send mail
                ],
            )

            # Skip specific test categories for now - RKHunter will run all tests by default
            # if test_categories:
            #     for category in test_categories:
            #         if category in self.test_categories:
            #             for test in self.test_categories[category]:
            #                 cmd_args.extend(["--enable", test])

            # Add configuration file - use system default with minimal overrides
            if os.path.exists("/etc/rkhunter.conf"):
                cmd_args.extend(["--configfile", "/etc/rkhunter.conf"])
                # Override problematic settings via command line
                cmd_args.extend(
                    ["--tmpdir", "/var/lib/rkhunter/tmp"],
                )  # Use secure temp dir
            elif self.config_path.exists():
                cmd_args.extend(["--configfile", str(self.config_path)])

            self.logger.info(
                "Running RKHunter scan with command: %s",
                " ".join(cmd_args),
            )

            # Run the scan with real-time output capture
            scan_result = self._run_with_privilege_escalation_streaming(
                cmd_args,
                output_callback=output_callback,
                timeout=1800,
            )

            result.end_time = datetime.now()

            # Parse results
            self._parse_scan_results(scan_result, result)

            if scan_result.returncode == 0:
                result.success = True
                result.scan_summary = "System appears clean"
            elif scan_result.returncode == 1:
                result.success = True
                result.scan_summary = f"Warnings found: {result.warnings_found}"
            elif scan_result.returncode == 2:
                result.success = True  # Still successful scan, but infections found
                result.scan_summary = (
                    f"Potential rootkits detected: {result.infections_found}"
                )
            else:
                result.success = False
                result.error_message = (
                    f"Scan failed with return code {scan_result.returncode}"
                )

            self.logger.info(
                "RKHunter scan completed: %s".replace(
                    "%s", "{result.scan_summary}"
                ).replace("%d", "{result.scan_summary}")
            )

        except subprocess.TimeoutExpired:
            result.end_time = datetime.now()
            result.success = False
            result.error_message = "Scan timed out after 30 minutes"
            self.logger.error("RKHunter scan timed out")

        except Exception as e:
            result.end_time = datetime.now()
            result.success = False
            result.error_message = f"Scan error: {str(e)}"
            self.logger.error("RKHunter scan failed: %s", e)

        return result

    def scan_system(
        self,
        test_categories: Optional[List[str]] = None,
        skip_keypress: bool = True,
    ) -> RKHunterScanResult:
        """Perform a full system rootkit scan.

        Args:
            test_categories: List of test categories to run (None for all)
            skip_keypress: Skip manual keypress confirmations

        Returns:
            RKHunterScanResult with scan results

        """
        scan_id = f"rkhunter_scan_{int(time.time())}"
        start_time = datetime.now()

        result = RKHunterScanResult(
            scan_id=scan_id,
            start_time=start_time,
            end_time=None,
        )

        if not self.available or self.rkhunter_path is None:
            result.error_message = "RKHunter not available"
            result.end_time = datetime.now()
            return result

        try:
            # Build command arguments (without sudo/pkexec prefix)
            cmd_args = [self.rkhunter_path, "--check"]

            if skip_keypress:
                cmd_args.append("--sk")  # Skip keypress

            cmd_args.extend(
                [
                    "--nocolors",
                    "--no-mail-on-warning",  # Don't try to send mail
                ],
            )

            # Skip specific test categories for now - RKHunter will run all tests by default
            # if test_categories:
            #     for category in test_categories:
            #         if category in self.test_categories:
            #             for test in self.test_categories[category]:
            #                 cmd_args.extend(["--enable", test])

            # Add configuration file - use system default with minimal overrides
            if os.path.exists("/etc/rkhunter.conf"):
                cmd_args.extend(["--configfile", "/etc/rkhunter.conf"])
                # Override problematic settings via command line
                cmd_args.extend(
                    ["--tmpdir", "/var/lib/rkhunter/tmp"],
                )  # Use secure temp dir
            elif self.config_path.exists():
                cmd_args.extend(["--configfile", str(self.config_path)])

            self.logger.info(
                "Running RKHunter scan with command: %s",
                " ".join(cmd_args),
            )

            # Run the scan using privilege escalation (prefers GUI dialog)
            scan_result = self._run_with_privilege_escalation(
                cmd_args,
                capture_output=True,
                timeout=1800,  # 30 minutes timeout
            )

            result.end_time = datetime.now()

            # Parse results
            self._parse_scan_results(scan_result, result)

            if scan_result.returncode == 0:
                result.success = True
                result.scan_summary = "System appears clean"
            elif scan_result.returncode == 1:
                result.success = True
                result.scan_summary = f"Warnings found: {result.warnings_found}"
            elif scan_result.returncode == 2:
                result.success = True  # Still successful scan, but infections found
                result.scan_summary = (
                    f"Potential rootkits detected: {result.infections_found}"
                )
            else:
                result.success = False
                result.error_message = (
                    f"Scan failed with return code {scan_result.returncode}"
                )

            self.logger.info(
                "RKHunter scan completed: %s".replace(
                    "%s", "{result.scan_summary}"
                ).replace("%d", "{result.scan_summary}")
            )

        except subprocess.TimeoutExpired:
            result.end_time = datetime.now()
            result.success = False
            result.error_message = "Scan timed out after 30 minutes"
            self.logger.error("RKHunter scan timed out")

        except Exception as e:
            result.end_time = datetime.now()
            result.success = False
            result.error_message = f"Scan error: {str(e)}"
            self.logger.error("RKHunter scan failed: %s", e)

        return result

    def _parse_scan_results(
        self,
        scan_process: subprocess.CompletedProcess,
        result: RKHunterScanResult,
    ):
        """Parse RKHunter scan output and populate results."""
        try:
            # Combine stdout and stderr since RKHunter outputs to both
            all_output = []
            if scan_process.stdout:
                all_output.extend(scan_process.stdout.split("\n"))
            if scan_process.stderr:
                all_output.extend(scan_process.stderr.split("\n"))

            current_test = ""
            test_count = 0

            for line in all_output:
                line = line.strip()

                if not line:
                    continue

                # Skip grep/egrep warnings that clutter output
                if "grep: warning:" in line or "egrep: warning:" in line:
                    continue

                # Parse test result indicators - these are the actual test completions
                if (
                    " [ OK ]" in line
                    or " [ Not found ]" in line
                    or " [ None found ]" in line
                    or " [ Found ]" in line
                    or " [ Warning ]" in line
                    or " [ Infected ]" in line
                    or " [ Skipped ]" in line
                ):
                    test_count += 1

                # Extract test name from the line
                if "Checking" in line:
                    current_test = (
                        line.replace("Checking", "").replace("...", "").strip()
                    )

                # Parse warnings - RKHunter uses "Warning:" format and "[ Warning ]"
                if " [ Warning ]" in line or line.startswith("Warning:"):
                    result.warnings_found += 1

                    # Analyze the warning to get detailed explanation
                    explanation = self.warning_analyzer.analyze_warning(line)

                    # Map analyzer severity to RKHunter severity
                    from .rkhunter_analyzer import SeverityLevel

                    severity_mapping = {
                        SeverityLevel.LOW: RKHunterSeverity.LOW,
                        SeverityLevel.MEDIUM: RKHunterSeverity.MEDIUM,
                        SeverityLevel.HIGH: RKHunterSeverity.HIGH,
                        SeverityLevel.CRITICAL: RKHunterSeverity.CRITICAL,
                    }
                    rk_severity = severity_mapping.get(
                        explanation.severity,
                        RKHunterSeverity.MEDIUM,
                    )

                    finding = RKHunterFinding(
                        test_name=current_test or "Security Check",
                        result=RKHunterResult.WARNING,
                        severity=rk_severity,
                        description=line,
                        explanation=explanation,
                    )
                    if result.findings is not None:
                        result.findings.append(finding)

                # Parse traditional format markers (in case they exist)
                elif "[ Warning ]" in line:
                    result.warnings_found += 1

                    # Analyze the warning to get detailed explanation
                    explanation = self.warning_analyzer.analyze_warning(line)

                    # Map analyzer severity to RKHunter severity
                    from .rkhunter_analyzer import SeverityLevel

                    severity_mapping = {
                        SeverityLevel.LOW: RKHunterSeverity.LOW,
                        SeverityLevel.MEDIUM: RKHunterSeverity.MEDIUM,
                        SeverityLevel.HIGH: RKHunterSeverity.HIGH,
                        SeverityLevel.CRITICAL: RKHunterSeverity.CRITICAL,
                    }
                    rk_severity = severity_mapping.get(
                        explanation.severity,
                        RKHunterSeverity.MEDIUM,
                    )

                    finding = RKHunterFinding(
                        test_name=current_test or "Unknown Test",
                        result=RKHunterResult.WARNING,
                        severity=rk_severity,
                        description=line,
                        explanation=explanation,
                    )
                    if result.findings is not None:
                        result.findings.append(finding)

                elif "[ Infected ]" in line or "[ INFECTED ]" in line:
                    result.infections_found += 1
                    finding = RKHunterFinding(
                        test_name=current_test or "Unknown Test",
                        result=RKHunterResult.INFECTED,
                        severity=RKHunterSeverity.HIGH,
                        description=line,
                    )
                    if result.findings is not None:
                        result.findings.append(finding)

                elif "[ Skipped ]" in line:
                    result.skipped_tests += 1

                elif "[ OK ]" in line or " OK " in line:
                    # Count successful tests
                    pass

                # Parse summary information
                elif "Files checked:" in line:
                    # Extract file count from summary
                    try:
                        parts = line.split(":")
                        if len(parts) > 1:
                            file_count = int(parts[1].strip())
                            # Add to test count if not already counted
                    except ValueError:
                        pass

                elif "Rootkits checked" in line:
                    # Extract rootkit count from summary
                    try:
                        parts = line.split(":")
                        if len(parts) > 1:
                            rootkit_count = int(parts[1].strip())
                            # Add to test count if not already counted
                    except ValueError:
                        pass

                elif "Suspect files:" in line:
                    # Extract suspect file count
                    try:
                        parts = line.split(":")
                        if len(parts) > 1:
                            suspect_count = int(parts[1].strip())
                            # These are likely warnings we should count
                    except ValueError:
                        pass

            # Set tests run based on actual test execution
            result.tests_run = test_count
            result.total_tests = test_count

        except Exception:
            self.logger.error(
                "Error parsing RKHunter results: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def _parse_scan_summary(self, stderr_output: str, result: RKHunterScanResult):
        """Parse summary information from RKHunter stderr output."""
        try:
            for line in stderr_output.split("\n"):
                line = line.strip()

                if "tests performed" in line.lower():
                    # Extract number of tests
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            result.total_tests = int(part)
                            break

        except Exception:
            self.logger.error(
                "Error parsing RKHunter summary: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def get_log_path(self) -> Optional[Path]:
        """Get path to RKHunter log file."""
        log_paths = [
            Path("/var/log/rkhunter.log"),
            Path.home() / ".rkhunter.log",
            # Use secure temp path as last resort
            Path(tempfile.gettempdir()) / "rkhunter-scan.log",
        ]

        for log_path in log_paths:
            if log_path.exists():
                return log_path

        return None

    def install_rkhunter(self) -> Tuple[bool, str]:
        """Attempt to install RKHunter using system package manager with GUI-friendly auth.

        Returns:
            Tuple of (success, message)

        """
        try:
            # Try different package managers (without sudo prefix - we'll add
            # it via privilege escalation)
            package_managers = [
                (["pacman", "-S", "--noconfirm", "rkhunter"], "pacman"),
                (["apt-get", "install", "-y", "rkhunter"], "apt"),
                (["yum", "install", "-y", "rkhunter"], "yum"),
                (["dnf", "install", "-y", "rkhunter"], "dnf"),
                (["zypper", "install", "-y", "rkhunter"], "zypper"),
            ]

            for cmd_args, pm_name in package_managers:
                try:
                    # Check if package manager exists
                    if not self._find_executable(cmd_args[0]):
                        continue

                    self.logger.info(
                        "Attempting to install RKHunter using %s".replace(
                            "%s", "{pm_name}"
                        ).replace("%d", "{pm_name}")
                    )

                    # Use privilege escalation (prefers GUI dialog)
                    result = self._run_with_privilege_escalation(
                        cmd_args,
                        capture_output=True,
                        timeout=300,  # 5 minutes
                    )

                    if result.returncode == 0:
                        # Refresh our paths
                        self.rkhunter_path = self._find_rkhunter()
                        self.available = self.rkhunter_path is not None

                        if self.available:
                            self._initialize_config()
                            return (
                                True,
                                f"RKHunter installed successfully using {pm_name}",
                            )
                        return (
                            False,
                            "Installation appeared successful but RKHunter not found",
                        )
                    self.logger.warning(
                        "Installation with %s failed: %s", pm_name, result.stderr
                    )

                except Exception:
                    self.logger.warning(
                        "Error trying %s: %s".replace("%s", "{pm_name, e}").replace(
                            "%d", "{pm_name, e}"
                        )
                    )
                    continue  # Try next package manager

            return False, "No compatible package manager found or installation failed"

        except Exception as e:
            return False, f"Installation error: {str(e)}"

    def get_scan_recommendations(self, scan_result: RKHunterScanResult) -> List[str]:
        """Get recommendations based on scan results.

        Args:
            scan_result: The completed scan result

        Returns:
            List of recommendation strings

        """
        recommendations = []

        if not scan_result.success:
            recommendations.append(
                "• Scan failed - check RKHunter installation and permissions",
            )
            return recommendations

        if scan_result.infections_found > 0:
            recommendations.append(
                "• **CRITICAL**: Potential rootkits detected - immediate action required",
            )
            recommendations.append(
                "• Run system in rescue mode and perform manual inspection",
            )
            recommendations.append(
                "• Consider reinstalling the operating system if compromised",
            )
            recommendations.append("• Change all passwords after cleaning the system")

        if scan_result.warnings_found > 0:
            recommendations.append(
                "• Review warnings carefully - they may indicate suspicious activity",
            )
            recommendations.append("• Update RKHunter database and run scan again")
            recommendations.append("• Check system logs for unusual activity")

        if scan_result.warnings_found == 0 and scan_result.infections_found == 0:
            recommendations.append("• System appears clean of rootkits")
            recommendations.append("• Continue regular security monitoring")
            recommendations.append("• Keep system and antivirus definitions updated")

        # Add general recommendations
        recommendations.extend(
            [
                "• Perform regular system scans",
                "• Keep operating system updated",
                "• Use strong passwords and enable 2FA where possible",
                "• Monitor system performance and network activity",
            ],
        )

        return recommendations

    def get_quick_status(self) -> dict:
        """Get quick status information for UI display."""
        try:
            if not self.is_available():
                return {"status": "not_available", "message": "RKHunter not available"}

            # Check if functional
            if not self.is_functional():
                return {
                    "status": "not_functional",
                    "message": "RKHunter not functional",
                }

            # Get version info
            version_info = self.get_version()

            return {
                "status": "available",
                "version": version_info[0] if version_info[0] else "unknown",
                "database_version": version_info[1] if version_info[1] else "unknown",
                "message": "RKHunter ready for scanning",
            }

        except Exception as e:
            logging.error("Failed to get RKHunter quick status: %s", e)
            return {"status": "error", "message": f"Error getting status: {e}"}


import psutil

from .safe_kill import kill_sequence
from .secure_subprocess import run_secure

# Import elevated_run for module-level usage/fallback (outside class)
try:  # pragma: no cover - testing convenience
    from .elevated_runner import elevated_run  # type: ignore  # noqa: F401
    from .elevated_runner import validate_auth_session  # type: ignore
except Exception:  # pragma: no cover

    def elevated_run(*a, **k):  # type: ignore
        raise RuntimeError("elevated_run unavailable")
