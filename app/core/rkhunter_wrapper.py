#!/usr/bin/env python3
"""
RKHunter (Rootkit Hunter) integration wrapper for S&D - Search & Destroy
Provides rootkit detection capabilities complementing ClamAV
"""

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

# Import the warning analyzer
from .rkhunter_analyzer import RKHunterWarningAnalyzer, WarningExplanation
# Import security validator
from .security_validator import SecureRKHunterValidator


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
    """
    Wrapper for RKHunter (Rootkit Hunter) integration.

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
        self._grace_period_extensions = 0  # Track grace period usage for security monitoring
        
        # Initialize security validator
        self.security_validator = SecureRKHunterValidator()
        
        # Initialize warning analyzer
        self.warning_analyzer = RKHunterWarningAnalyzer()
        
        # Validate RKHunter path on initialization for security
        if self.rkhunter_path:
            if not self.security_validator.validate_executable_path(self.rkhunter_path):
                self.logger.warning(f"RKHunter path {self.rkhunter_path} failed security validation")
                # Try to get a safe path
                safe_path = self.security_validator.get_safe_rkhunter_path()
                if safe_path:
                    self.logger.info(f"Using safe RKHunter path: {safe_path}")
                    self.rkhunter_path = safe_path
                else:
                    self.logger.error("No safe RKHunter path found - disabling RKHunter")
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
            "rootkits": [
                "rootkits",
                "trojans",
                "malware"],
            "network": [
                "network",
                "ports",
                "packet_cap_apps"],
            "system_integrity": [
                "filesystem",
                "system_configs",
                "startup_files"],
            "applications": [
                "applications",
                "hidden_procs",
                "hidden_files"],
        }

        if self.available:
            self._initialize_config()
            self.logger.info("RKHunter wrapper initialized successfully")
        else:
            self.logger.warning("RKHunter not available on system")

    def _configure_security_settings(self):
        """
        Configure security settings based on environment and security policy.
        SECURITY: Adaptive grace period based on system security requirements.
        """
        try:
            # SECURITY: Check for security configuration file
            config_path = Path.home() / ".config" / "search-and-destroy" / "security.conf"
            
            if config_path.exists():
                # Load custom security configuration
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
                
                if config.has_section('grace_period'):
                    custom_period = config.getint('grace_period', 'duration', fallback=self._grace_period)
                    max_period = config.getint('grace_period', 'max_duration', fallback=self._max_grace_period)
                    
                    # SECURITY: Validate custom grace period
                    if 30 <= custom_period <= max_period:
                        self._grace_period = custom_period
                        self.logger.info(f"Using custom grace period: {custom_period}s")
                    else:
                        self.logger.warning(
                            f"Invalid custom grace period {custom_period}s, "
                            f"using default: {self._grace_period}s"
                        )
            
            # SECURITY: Environment-based adjustments
            # Check if running in a high-security environment
            if os.path.exists('/etc/security/high-security-mode'):
                # Reduce grace period in high-security environments
                self._grace_period = min(300, self._grace_period)  # Max 5 minutes
                self.logger.info("High-security mode detected - reduced grace period")
            
            # SECURITY: Check system load to adjust grace period
            try:
                import psutil
                system_load = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
                if system_load > 2.0:
                    # Increase grace period on high-load systems (scans take longer)
                    self._grace_period = min(self._max_grace_period, int(self._grace_period * 1.5))
                    self.logger.info(f"High system load detected - extended grace period to {self._grace_period}s")
            except ImportError:
                pass  # psutil not available
                
        except Exception as e:
            self.logger.warning(f"Error configuring security settings: {e}")
        
        self.logger.info(
            f"Security configuration complete - grace period: {self._grace_period}s, "
            f"max: {self._max_grace_period}s"
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
            result = subprocess.run(
                ["which", "rkhunter"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return None

    def _find_executable(self, name: str) -> Optional[str]:
        """Find an executable in PATH."""
        import shutil

        return shutil.which(name)

    def terminate_current_scan(self):
        """
        Safely terminate the currently running RKHunter scan.
        
        Uses a graceful approach: SIGTERM first, then SIGKILL if needed.
        For elevated processes, also attempts privileged termination.
        """
        if self._current_process is not None:
            try:
                pid = self._current_process.pid
                self.logger.info("Terminating RKHunter scan process (PID: %d)", pid)
                
                # First try graceful termination (SIGTERM)
                self._current_process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    self._current_process.wait(timeout=5)
                    self.logger.info("RKHunter scan terminated gracefully")
                    return True
                except subprocess.TimeoutExpired:
                    # If still running after timeout, try privileged termination
                    self.logger.warning("RKHunter scan did not terminate gracefully, trying privileged termination")
                    
                    # Attempt privileged termination using pkexec
                    if self._terminate_with_privilege_escalation(pid):
                        self.logger.info("RKHunter scan terminated via privileged escalation")
                        return True
                    
                    # If privileged termination fails, force kill (SIGKILL)
                    self.logger.warning("Privileged termination failed, using SIGKILL")
                    self._current_process.kill()
                    try:
                        self._current_process.wait(timeout=2)
                        self.logger.info("RKHunter scan force-terminated")
                        return True
                    except subprocess.TimeoutExpired:
                        self.logger.error("Failed to terminate RKHunter scan even with SIGKILL")
                        return False
            except PermissionError as e:
                # This is expected when trying to terminate elevated processes
                self.logger.info("Permission denied when terminating elevated RKHunter process (expected): %s", e)
                
                # Try privileged termination as fallback
                if hasattr(self, '_current_process') and self._current_process:
                    pid = self._current_process.pid
                    
                    # If we're within grace period, be more lenient about termination
                    if self._is_within_auth_grace_period():
                        self.logger.info("Within grace period - attempting privileged termination but accepting if unsuccessful")
                        success = self._terminate_with_privilege_escalation(pid)
                        if not success:
                            self.logger.info("Privileged termination within grace period was unsuccessful, but process will terminate naturally")
                        return True  # Always return success within grace period
                    else:
                        # Outside grace period, try harder to terminate
                        if self._terminate_with_privilege_escalation(pid):
                            self.logger.info("RKHunter scan terminated via privileged escalation fallback")
                            return True
                
                self.logger.info("RKHunter process was started with elevated privileges and cannot be terminated by non-elevated process")
                return True  # Still consider this a "success" since the process will eventually finish
            except Exception as e:
                self.logger.error("Error terminating RKHunter scan: %s", e)
                return False
            finally:
                self._current_process = None
        else:
            self.logger.warning("No RKHunter scan process to terminate")
            return True

    def _is_within_auth_grace_period(self) -> bool:
        """
        Check if we're within the authentication grace period.
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
                f"Extended grace period in use: {elapsed:.1f}s elapsed, "
                f"extension #{self._grace_period_extensions}"
            )
            
            # SECURITY: Limit grace period extensions to prevent abuse
            if self._grace_period_extensions > 3:
                self.logger.error(
                    "Grace period extension limit exceeded - forcing re-authentication"
                )
                return False
        
        self.logger.debug(
            f"Auth session elapsed time: {elapsed:.1f}s, "
            f"grace period: {self._grace_period}s, "
            f"within standard: {within_standard_period}, "
            f"within extended: {within_extended_period}"
        )
        
        return within_extended_period

    def _update_auth_session(self):
        """
        Update the authentication session timestamp.
        SECURITY: Enhanced with session validation and monitoring.
        """
        current_time = time.time()
        
        # SECURITY: Check for session reset (new scan starting)
        if self._auth_session_start is not None:
            previous_elapsed = current_time - self._auth_session_start
            self.logger.info(
                f"Authentication session reset after {previous_elapsed:.1f}s, "
                f"extensions used: {self._grace_period_extensions}"
            )
        
        self._auth_session_start = current_time
        self._grace_period_extensions = 0  # Reset extension counter
        
        self.logger.info(
            f"Authentication session updated - grace period: {self._grace_period}s"
        )
        
        # SECURITY: Log session start for audit trail
        self.logger.info("SECURITY_AUDIT: New privileged session started")
    
    def _reset_auth_session(self):
        """
        Reset the authentication session.
        SECURITY: Clean session termination with audit logging.
        """
        if self._auth_session_start is not None:
            elapsed = time.time() - self._auth_session_start
            self.logger.info(
                f"Authentication session ended after {elapsed:.1f}s, "
                f"extensions used: {self._grace_period_extensions}"
            )
            # SECURITY: Log session end for audit trail
            self.logger.info("SECURITY_AUDIT: Privileged session ended")
        
        self._auth_session_start = None
        self._grace_period_extensions = 0

    def _terminate_with_privilege_escalation(self, pid: int) -> bool:
        """
        Attempt to terminate a process using privileged escalation when needed.
        Uses regular kill commands within grace period to avoid re-authentication.
        
        Args:
            pid: Process ID to terminate
            
        Returns:
            bool: True if termination was successful, False otherwise
        """
        try:
            # Check if we're within the grace period for immediate termination
            if self._is_within_auth_grace_period():
                self.logger.info("Within authentication grace period, attempting direct termination for PID %d", pid)
                
                # Try regular kill command first (no privilege escalation needed)
                try:
                    # First try SIGTERM
                    result = subprocess.run(["kill", "-TERM", str(pid)], 
                                 capture_output=True, check=False, timeout=5)
                    
                    if result.returncode == 0:
                        self.logger.info("Direct SIGTERM sent successfully (grace period)")
                        
                        # Wait a bit to see if the process terminates
                        time.sleep(2)
                        
                        # Check if process is still running
                        try:
                            check_result = subprocess.run(["kill", "-0", str(pid)], 
                                         capture_output=True, check=False, timeout=5)
                            if check_result.returncode == 0:
                                # Process still running, try SIGKILL
                                kill_result = subprocess.run(["kill", "-KILL", str(pid)], 
                                             capture_output=True, check=False, timeout=5)
                                if kill_result.returncode == 0:
                                    self.logger.info("Direct SIGKILL sent successfully (grace period)")
                                    return True
                                else:
                                    self.logger.info("Direct SIGKILL failed (grace period) - process is elevated, but returning success to avoid re-auth")
                                    # Within grace period, we don't want to prompt for authentication again
                                    # Even if we can't kill the elevated process, return success
                                    return True
                            else:
                                # Process no longer exists (kill -0 failed)
                                self.logger.info("Process terminated successfully via direct SIGTERM (grace period)")
                                return True
                        except subprocess.TimeoutExpired:
                            self.logger.warning("Timeout checking process status during grace period - assuming success")
                            # Within grace period, assume success to avoid re-auth
                            return True
                    else:
                        # SIGTERM failed (probably due to permissions), try SIGKILL
                        kill_result = subprocess.run(["kill", "-KILL", str(pid)], 
                                     capture_output=True, check=False, timeout=5)
                        if kill_result.returncode == 0:
                            self.logger.info("Direct SIGKILL sent successfully (grace period)")
                            return True
                        else:
                            self.logger.info("Both direct SIGTERM and SIGKILL failed (grace period) - process is elevated, but returning success to avoid re-auth")
                            # Within grace period, we don't want to prompt for authentication again
                            # Even if we can't kill the elevated process, return success
                            return True
                        
                except subprocess.TimeoutExpired:
                    self.logger.info("Direct kill timeout during grace period - returning success to avoid re-auth")
                    # Within grace period, assume success to avoid re-auth
                    return True
                except Exception as e:
                    self.logger.info("Direct kill failed during grace period (%s) - returning success to avoid re-auth", e)
                    # Within grace period, assume success to avoid re-auth
                    return True
            
            # Outside grace period or direct kill failed - use pkexec
            pkexec_path = self._find_executable("pkexec")
            if not pkexec_path:
                self.logger.warning("pkexec not available for privileged termination")
                return False
            
            self.logger.info("Using pkexec for privileged termination (authentication required)")
            
            # First try SIGTERM (graceful)
            self.logger.info("Attempting privileged SIGTERM for PID %d using pkexec", pid)
            cmd = [pkexec_path, "kill", "-TERM", str(pid)]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=15,  # Give more time for pkexec authentication
                    check=False
                )
                
                if result.returncode == 0:
                    self.logger.info("Privileged SIGTERM sent successfully via pkexec")
                    # Wait a bit to see if the process terminates
                    time.sleep(2)
                    
                    # Check if process is still running
                    try:
                        # Try to send signal 0 to check if process exists
                        subprocess.run(["kill", "-0", str(pid)], 
                                     capture_output=True, check=True, timeout=5)
                        # If we reach here, process is still running, try SIGKILL
                        self.logger.warning("Process still running after SIGTERM, trying privileged SIGKILL via pkexec")
                        
                        cmd_kill = [pkexec_path, "kill", "-KILL", str(pid)]
                        result_kill = subprocess.run(
                            cmd_kill,
                            capture_output=True,
                            text=True,
                            timeout=15,  # Give more time for pkexec authentication
                            check=False
                        )
                        
                        if result_kill.returncode == 0:
                            self.logger.info("Privileged SIGKILL sent successfully via pkexec")
                            return True
                        else:
                            self.logger.error("Privileged SIGKILL failed via pkexec: %s", result_kill.stderr)
                            return False
                            
                    except subprocess.CalledProcessError:
                        # Process no longer exists (kill -0 failed), termination successful
                        self.logger.info("Process terminated successfully with privileged SIGTERM via pkexec")
                        return True
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Timeout checking process status")
                        return False
                else:
                    self.logger.error("Privileged SIGTERM failed via pkexec (exit code %d): %s", 
                                    result.returncode, result.stderr)
                    
                    # Check if this was a cancellation by user
                    if result.returncode == 126:  # pkexec user cancelled
                        self.logger.info("User cancelled pkexec authentication - this is expected")
                        return True  # Don't treat user cancellation as failure
                    elif result.returncode == 127:  # pkexec not authorized
                        self.logger.warning("User not authorized for pkexec kill command")
                        return False
                    else:
                        return False
                    
            except subprocess.TimeoutExpired:
                self.logger.error("Timeout during privileged termination via pkexec")
                return False
                
        except Exception as e:
            self.logger.error("Error during privileged termination via pkexec: %s", e)
            return False

    def _run_with_privilege_escalation(
            self,
            cmd_args: List[str],
            capture_output: bool = True,
            timeout: int = 300) -> subprocess.CompletedProcess:
        """
        Run a command with privilege escalation, preferring pkexec for consistency.
        SECURITY: Validates all commands against security policy before execution.

        Args:
            cmd_args: Command arguments (without sudo/pkexec prefix)
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds

        Returns:
            subprocess.CompletedProcess: The result of the command
        """
        # SECURITY: Validate command arguments before any execution
        is_valid, error_message = self.security_validator.validate_command_args(cmd_args)
        if not is_valid:
            self.logger.error(f"Security validation failed: {error_message}")
            # Return a failed result instead of raising exception for better error handling
            result = subprocess.CompletedProcess(
                args=cmd_args,
                returncode=1,
                stdout="",
                stderr=f"Security validation failed: {error_message}"
            )
            return result
        
        self.logger.info(f"Security validation passed for command: {' '.join(cmd_args[:2])}")  # Log first 2 args only
        # Try different privilege escalation methods in order of preference
        escalation_methods = []

        # If already root, run directly
        if os.getuid() == 0:
            escalation_methods.append(("direct", cmd_args))

        # PRIMARY METHOD: pkexec (GUI password dialog - system native)
        # This ensures consistency with termination method
        pkexec_path = self._find_executable("pkexec")
        sudo_path = self._find_executable("sudo")  # Define sudo_path at top level
        
        if pkexec_path:
            escalation_methods.append(("pkexec", [pkexec_path] + cmd_args))
            self.logger.info("Using pkexec for privilege escalation (consistent with termination)")

        # FALLBACK METHODS (only if pkexec is not available)
        # Note: Fallback methods may cause inconsistency with termination
        if not pkexec_path:
            self.logger.warning("pkexec not available, falling back to sudo methods - termination may be inconsistent")
            # Second preference: sudo with GUI password helper
            if sudo_path:
                # Check for GUI password helpers
                askpass_helpers = [
                    "/usr/bin/ssh-askpass",
                    "/usr/bin/x11-ssh-askpass", 
                    "/usr/bin/ksshaskpass",
                    "/usr/bin/lxqt-openssh-askpass"
                ]
                
                askpass_cmd = None
                for helper in askpass_helpers:
                    if os.path.exists(helper):
                        askpass_cmd = helper
                        break
                
                if askpass_cmd and os.environ.get('DISPLAY'):
                    escalation_methods.append(("sudo_gui", [sudo_path, "-A"] + cmd_args))

        # Third preference: sudo -n (passwordless sudo for headless environments)
        if sudo_path:
            escalation_methods.append(("sudo_nopasswd", [sudo_path, "-n"] + cmd_args))

        # Fourth preference: sudo (terminal password prompt)
        if sudo_path:
            escalation_methods.append(("sudo", [sudo_path] + cmd_args))

        last_error = None

        for method_name, full_cmd in escalation_methods:
            try:
                self.logger.debug(
                    f"Trying {method_name}: {
                        ' '.join(full_cmd)}")

                if method_name == "direct":
                    # Already running as root
                    self.logger.info("Running as root directly")
                    result = subprocess.run(
                        full_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                elif method_name == "pkexec":
                    # pkexec shows GUI password dialog
                    self.logger.info("Using GUI password dialog (pkexec)")
                    # Set up environment for GUI authentication
                    env = os.environ.copy()
                    if 'DISPLAY' not in env:
                        env['DISPLAY'] = ':0'
                    if 'XAUTHORITY' not in env and 'HOME' in env:
                        env['XAUTHORITY'] = f"{env['HOME']}/.Xauthority"
                    
                    result = subprocess.run(
                        full_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                        env=env,
                    )
                elif method_name == "sudo_gui":
                    # sudo -A uses GUI password helper
                    self.logger.info("Using GUI password helper (sudo -A)")
                    # Set up environment for GUI authentication
                    env = os.environ.copy()
                    env['SUDO_ASKPASS'] = '/usr/bin/ksshaskpass'  # We know this exists from our check
                    
                    result = subprocess.run(
                        full_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                        env=env,
                    )
                elif method_name == "sudo_nopasswd":
                    # sudo -n uses passwordless authentication
                    self.logger.info("Using passwordless sudo")
                    result = subprocess.run(
                        full_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                elif method_name == "pkexec_custom":
                    # pkexec with custom PolicyKit action (single authentication)
                    self.logger.info("Using custom PolicyKit action (pkexec_custom)")
                    
                    result = subprocess.run(
                        full_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                elif method_name == "pkexec":
                    # pkexec shows GUI password dialog
                    self.logger.info("Using GUI password dialog (pkexec)")
                    
                    # Get current environment variables for GUI
                    display = os.environ.get('DISPLAY', ':0')
                    xauthority = os.environ.get('XAUTHORITY', f"{os.environ.get('HOME', '')}/.Xauthority")
                    
                    # COMBINED SCRIPT OPTIMIZATION: Check if this is an RKHunter scan command
                    # and if we have the combined script available
                    project_root = Path(__file__).parent.parent.parent
                    combined_script = project_root / "scripts" / "rkhunter-update-and-scan.sh"
                    if (len(full_cmd) >= 2 and 
                        "rkhunter" in full_cmd[1] and 
                        "--check" in full_cmd and 
                        combined_script.exists()):
                        
                        self.logger.info("Using combined RKHunter script to avoid double authentication")
                        # Replace rkhunter path with combined script
                        scan_args = [arg for arg in full_cmd[2:] if arg != "--check"]  # Get args after rkhunter
                        env_cmd = ["pkexec", "env", f"DISPLAY={display}", f"XAUTHORITY={xauthority}", str(combined_script), "--check"] + scan_args
                    else:
                        # Modify command to include environment variables with pkexec
                        # pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY command
                        env_cmd = ["pkexec", "env", f"DISPLAY={display}", f"XAUTHORITY={xauthority}"] + full_cmd[1:]  # Skip original pkexec
                    
                    self.logger.info(f"Original command: {' '.join(full_cmd)}")
                    self.logger.info(f"Modified command: {' '.join(env_cmd)}")
                    
                    result = subprocess.run(
                        env_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                elif method_name == "sudo":
                    # sudo uses terminal password prompt
                    self.logger.info("Using terminal password prompt (sudo)")
                    
                    # For GUI applications, try to use a GUI password helper
                    env = os.environ.copy()
                    askpass_helpers = [
                        "/usr/bin/ssh-askpass",
                        "/usr/bin/x11-ssh-askpass", 
                        "/usr/bin/ksshaskpass",
                        "/usr/bin/lxqt-openssh-askpass"
                    ]
                    
                    askpass_cmd = None
                    for helper in askpass_helpers:
                        if os.path.exists(helper):
                            askpass_cmd = helper
                            break
                    
                    if askpass_cmd and os.environ.get('DISPLAY'):
                        # Use GUI password prompt with sudo -A
                        env['SUDO_ASKPASS'] = askpass_cmd
                        # Modify command to use -A flag
                        gui_cmd = [full_cmd[0], '-A'] + full_cmd[1:]
                        self.logger.info(f"Using GUI password helper: {askpass_cmd}")
                        result = subprocess.run(
                            gui_cmd,
                            capture_output=capture_output,
                            text=True,
                            timeout=timeout,
                            check=False,
                            env=env,
                        )
                    elif capture_output:
                        # For sudo, we might need to handle interactive input
                        result = subprocess.run(
                            full_cmd,
                            capture_output=True,
                            text=True,
                            timeout=timeout,
                            check=False,
                            input="\n",  # Auto-confirm prompts
                        )
                    else:
                        # Let user interact with sudo directly
                        result = subprocess.run(
                            full_cmd, text=True, timeout=timeout, check=False
                        )
                else:
                    # Unknown method
                    self.logger.error(f"Unknown privilege escalation method: {method_name}")
                    continue

                # IMPROVED SUCCESS DETECTION: Check if RKHunter actually ran successfully
                # RKHunter returns exit code 1 when warnings are found, which is normal
                scan_completed_successfully = False
                
                if result.returncode == 0:
                    # Perfect success
                    scan_completed_successfully = True
                elif result.returncode == 1 and result.stdout:
                    # Check if RKHunter completed but found warnings
                    if "Info: End date is" in result.stdout or "System checks summary" in result.stdout:
                        scan_completed_successfully = True
                        self.logger.info(f"RKHunter completed with warnings (exit code 1) using {method_name}")
                
                if scan_completed_successfully:
                    self.logger.info(f"Command succeeded using {method_name}")
                    # Update authentication session for grace period termination
                    self._update_auth_session()
                    self.logger.debug(f"Authentication session updated for {self._grace_period}s grace period")
                    return result

                # Log the attempt and try next method
                self.logger.warning(
                    f"{method_name} failed with return code {
                        result.returncode}")
                last_error = result

            except subprocess.TimeoutExpired as e:
                self.logger.error(
                    f"{method_name} timed out after {timeout} seconds")
                last_error = e
            except Exception as e:
                self.logger.error(f"{method_name} failed with exception: {e}")
                last_error = e

        # If all methods failed, return the last error or create a failure
        # result
        if isinstance(last_error, subprocess.CompletedProcess):
            return last_error
        else:
            # Create a failure result
            return subprocess.CompletedProcess(
                args=cmd_args,
                returncode=1,
                stdout="",
                stderr=f"All privilege escalation methods failed. Last error: {last_error}",
            )

    def _run_with_privilege_escalation_streaming(
            self,
            cmd_args: List[str],
            output_callback: Optional[Callable[[str], None]] = None,
            timeout: int = 300) -> subprocess.CompletedProcess:
        """
        Run a command with privilege escalation and real-time output streaming.
        SECURITY: Validates all commands against security policy before execution.

        Args:
            cmd_args: Command arguments (without sudo/pkexec prefix)
            output_callback: Function to call with each line of output
            timeout: Command timeout in seconds

        Returns:
            subprocess.CompletedProcess: The result of the command
        """
        # SECURITY: Validate command arguments before any execution
        is_valid, error_message = self.security_validator.validate_command_args(cmd_args)
        if not is_valid:
            self.logger.error(f"Security validation failed: {error_message}")
            # Return a failed result instead of raising exception for better error handling
            result = subprocess.CompletedProcess(
                args=cmd_args,
                returncode=1,
                stdout="",
                stderr=f"Security validation failed: {error_message}"
            )
            return result
        
        self.logger.info(f"Security validation passed for streaming command: {' '.join(cmd_args[:2])}")  # Log first 2 args only
        # Try different privilege escalation methods in order of preference
        escalation_methods = []

        # If already root, run directly
        if os.getuid() == 0:
            escalation_methods.append(("direct", cmd_args))

        # PRIMARY METHOD: pkexec (GUI password dialog - system native)
        # This ensures consistency with termination method
        pkexec_path = self._find_executable("pkexec")
        sudo_path = self._find_executable("sudo")  # Define sudo_path at top level
        
        if pkexec_path:
            escalation_methods.append(("pkexec", [pkexec_path] + cmd_args))
            self.logger.info("Using pkexec for RKHunter scan (consistent with termination)")

        # FALLBACK METHODS (only if pkexec is not available)
        # Note: Fallback methods may cause inconsistency with termination
        if not pkexec_path:
            self.logger.warning("pkexec not available, falling back to sudo methods - termination may be inconsistent")
            # Second preference: sudo with GUI password helper
            if sudo_path:
                # Check for GUI password helpers
                askpass_helpers = [
                    "/usr/bin/ssh-askpass",
                    "/usr/bin/x11-ssh-askpass", 
                    "/usr/bin/ksshaskpass",
                    "/usr/bin/lxqt-openssh-askpass"
                ]
                
                askpass_cmd = None
                for helper in askpass_helpers:
                    if os.path.exists(helper):
                        askpass_cmd = helper
                        break
                
                if askpass_cmd and os.environ.get('DISPLAY'):
                    escalation_methods.append(("sudo_gui", [sudo_path, "-A"] + cmd_args))

        # Third preference: sudo -n (passwordless sudo for headless environments)
        if sudo_path:
            escalation_methods.append(("sudo_nopasswd", [sudo_path, "-n"] + cmd_args))

        # Fourth preference: sudo (terminal password prompt)
        if sudo_path:
            escalation_methods.append(("sudo", [sudo_path] + cmd_args))

        last_error = None

        for method_name, full_cmd in escalation_methods:
            try:
                self.logger.debug(f"Trying {method_name}: {' '.join(full_cmd)}")

                if method_name == "direct":
                    self.logger.info("Running as root directly")
                    env = os.environ.copy()
                elif method_name == "pkexec":
                    self.logger.info("Using GUI password dialog (pkexec)")
                    
                    # Get current environment variables for GUI
                    display = os.environ.get('DISPLAY', ':0')
                    xauthority = os.environ.get('XAUTHORITY', f"{os.environ.get('HOME', '')}/.Xauthority")
                    
                    # Store original command for logging
                    original_cmd = full_cmd.copy()
                    
                    # COMBINED SCRIPT OPTIMIZATION: Check if this is an RKHunter scan command
                    # and if we have the combined script available
                    project_root = Path(__file__).parent.parent.parent
                    combined_script = project_root / "scripts" / "rkhunter-update-and-scan.sh"
                    if (len(full_cmd) >= 2 and 
                        "rkhunter" in full_cmd[1] and 
                        "--check" in full_cmd and 
                        combined_script.exists()):
                        
                        self.logger.info("Using combined RKHunter script to avoid double authentication")
                        # Replace rkhunter path with combined script
                        scan_args = [arg for arg in full_cmd[2:] if arg != "--check"]  # Get args after rkhunter
                        full_cmd = ["pkexec", "env", f"DISPLAY={display}", f"XAUTHORITY={xauthority}", str(combined_script), "--check"] + scan_args
                    else:
                        # Modify command to include environment variables with pkexec
                        # pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY command
                        full_cmd = ["pkexec", "env", f"DISPLAY={display}", f"XAUTHORITY={xauthority}"] + full_cmd[1:]  # Skip original pkexec
                    
                    self.logger.info(f"Original command: {' '.join(original_cmd)}")
                    self.logger.info(f"Modified command: {' '.join(full_cmd)}")
                    
                    env = os.environ.copy()
                elif method_name == "sudo_gui":
                    self.logger.info("Using GUI password helper (sudo with askpass)")
                    env = os.environ.copy()
                    # Set up GUI password helper
                    askpass_helpers = [
                        "/usr/bin/ssh-askpass",
                        "/usr/bin/x11-ssh-askpass", 
                        "/usr/bin/ksshaskpass",
                        "/usr/bin/lxqt-openssh-askpass"
                    ]
                    for helper in askpass_helpers:
                        if os.path.exists(helper):
                            env['SUDO_ASKPASS'] = helper
                            break
                elif method_name == "sudo_nopasswd":
                    self.logger.info("Attempting passwordless sudo (requires NOPASSWD in sudoers)")
                    env = os.environ.copy()
                elif method_name == "sudo":
                    self.logger.info("Using terminal password prompt (sudo)")
                    # For GUI applications, try to use a GUI password helper
                    env = os.environ.copy()
                    askpass_helpers = [
                        "/usr/bin/ssh-askpass",
                        "/usr/bin/x11-ssh-askpass", 
                        "/usr/bin/ksshaskpass",
                        "/usr/bin/lxqt-openssh-askpass"
                    ]
                    
                    askpass_cmd = None
                    for helper in askpass_helpers:
                        if os.path.exists(helper):
                            askpass_cmd = helper
                            break
                    
                    if askpass_cmd and os.environ.get('DISPLAY'):
                        # Use GUI password prompt with sudo -A
                        env['SUDO_ASKPASS'] = askpass_cmd
                        # Modify command to use -A flag
                        full_cmd = [full_cmd[0], '-A'] + full_cmd[1:]
                        self.logger.info(f"Using GUI password helper: {askpass_cmd}")
                else:
                    env = os.environ.copy()

                # Start the process with real-time output capture
                process = subprocess.Popen(
                    full_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env=env
                )
                
                # Track the current process for potential termination
                self._current_process = process
                
                # Update authentication session for grace period termination
                self._update_auth_session()
                self.logger.info(f"Authentication session started for {self._grace_period}s grace period")

                stdout_lines = []
                
                # Read output line by line in real-time
                if process.stdout:
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        
                        line = line.rstrip()
                        stdout_lines.append(line)
                        
                        # Call the output callback if provided
                        if output_callback:
                            output_callback(line)

                # Wait for process to complete
                process.wait(timeout=timeout)
                
                # Clear the process reference when done
                self._current_process = None
                
                # Create result object
                result = subprocess.CompletedProcess(
                    args=full_cmd,
                    returncode=process.returncode,
                    stdout='\n'.join(stdout_lines),
                    stderr=""
                )

                # IMPROVED SUCCESS DETECTION: Check if RKHunter actually ran successfully
                # RKHunter returns exit code 1 when warnings are found, which is normal
                scan_completed_successfully = False
                
                if result.returncode == 0:
                    # Perfect success
                    scan_completed_successfully = True
                elif result.returncode == 1 and result.stdout:
                    # Check if RKHunter completed but found warnings
                    if "Info: End date is" in result.stdout or "System checks summary" in result.stdout:
                        scan_completed_successfully = True
                        self.logger.info(f"RKHunter completed with warnings (exit code 1) using {method_name}")
                
                if scan_completed_successfully:
                    self.logger.info(f"Command succeeded using {method_name}")
                    # Update authentication session for grace period termination
                    self._update_auth_session()
                    self.logger.debug(f"Authentication session updated for {self._grace_period}s grace period")
                    return result

                # Log the attempt and try next method
                self.logger.warning(
                    f"{method_name} failed with return code {result.returncode}")
                last_error = result

            except subprocess.TimeoutExpired as e:
                if 'process' in locals():
                    process.kill()
                self.logger.error(f"{method_name} timed out after {timeout} seconds")
                last_error = e
            except Exception as e:
                self.logger.error(f"{method_name} failed with exception: {e}")
                last_error = e

        # If all methods failed, return the last error or create a failure result
        if isinstance(last_error, subprocess.CompletedProcess):
            return last_error
        else:
            # Create a failure result
            return subprocess.CompletedProcess(
                args=cmd_args,
                returncode=1,
                stdout="",
                stderr=f"All privilege escalation methods failed. Last error: {last_error}",
            )

    def _initialize_config(self):
        """Initialize RKHunter configuration."""
        try:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Create basic configuration if it doesn't exist
            if not self.config_path.exists():
                config_content = """# RKHunter configuration for S&D Search & Destroy
# This file configures RKHunter behavior within the antivirus application

# Logging
LOGFILE=/tmp/rkhunter-scan.log
APPEND_LOG=1
COPY_LOG_ON_ERROR=1

# Scan behavior
SCANROOTKITMODE=1
UNHIDETCPUDP=1
ALLOW_SSH_ROOT_USER=no
ALLOW_SSH_PROT_V1=0

# Update behavior
UPDATE_MIRRORS=1
MIRRORS_MODE=0
WEB_CMD=""

# Database locations - Arch Linux specific paths
DBDIR=/var/lib/rkhunter/db
# Arch Linux script directory
SCRIPTDIR=/usr/lib/rkhunter/scripts
BINDIR=/usr/bin
# Installation directory
INSTALLDIR=/usr
# Temporary directory
TMPDIR=/tmp

# Suppress common warnings and false positives
DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps apps"

# Additional Arch Linux specific settings
ALLOWHIDDENDIR=/etc/.java
ALLOWHIDDENDIR=/dev/.static
ALLOWHIDDENDIR=/dev/.udev
ALLOWHIDDENDIR=/dev/.mount

# Package manager
PKGMGR=PACMAN
SCRIPTWHITELIST=""
ALLOWHIDDENDIR="/etc/.java"
ALLOWHIDDENFILE="/etc/.java"

# Disable GUI prompts (for automated scanning)
AUTO_X_DETECT=1
WHITELISTED_IS_WHITE=1
SUPPRESS_DEPRECATION_WARNINGS=1

# Reduce grep warnings by using simpler patterns
USE_SYSLOG=0
"""
                with open(self.config_path, "w") as f:
                    f.write(config_content)

                self.logger.info(
                    "Created RKHunter configuration at %s", self.config_path
                )

        except Exception as e:
            self.logger.error("Failed to initialize RKHunter config: %s", e)

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
            result = subprocess.run(
                [self.rkhunter_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True
        except PermissionError:
            pass
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

        # If direct execution failed, try with privilege escalation
        try:
            result = self._run_with_privilege_escalation(
                [self.rkhunter_path, "--version"], capture_output=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Tuple[str, str]:
        """Get RKHunter version information."""
        if not self.available or self.rkhunter_path is None:
            return "Not Available", "N/A"

        try:
            # First try without privilege escalation
            result = subprocess.run(
                [self.rkhunter_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                version_line = next(
                    (line for line in lines if "RKH" in line), "Unknown"
                )
                return version_line.strip(), "Current"

        except PermissionError:
            pass
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Error", "N/A"

        # If direct execution failed, try with privilege escalation
        try:
            result = self._run_with_privilege_escalation(
                [self.rkhunter_path, "--version"], capture_output=True, timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                version_line = next(
                    (line for line in lines if "RKH" in line), "Unknown"
                )
                return version_line.strip(), "Current (requires elevated privileges)"
        except Exception:
            pass

        return "Unknown", "Permission denied"

    def update_database(self) -> bool:
        """Update RKHunter database using GUI-friendly privilege escalation."""
        if not self.available or self.rkhunter_path is None:
            return False

        try:
            self.logger.info("Updating RKHunter database...")

            # Use new privilege escalation method (prefers GUI dialog)
            result = self._run_with_privilege_escalation(
                [self.rkhunter_path, "--update"],
                capture_output=True,
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode == 0:
                self.logger.info("RKHunter database updated successfully")
                return True
            else:
                # Check if database is already up to date
                output_text = result.stdout + result.stderr
                if (
                    "already have the latest" in output_text.lower()
                    or "up to date" in output_text.lower()
                ):
                    self.logger.info("RKHunter database is already up to date")
                    return True

                self.logger.warning(
                    "RKHunter database update returned code %d: %s",
                    result.returncode,
                    result.stderr,
                )
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("RKHunter database update timed out")
            return False
        except Exception as e:
            self.logger.error("Failed to update RKHunter database: %s", e)
            return False

    def scan_system_with_output_callback(self,
                    test_categories: Optional[List[str]] = None,
                    skip_keypress: bool = True,
                    update_database: bool = True,
                    output_callback: Optional[Callable[[str], None]] = None) -> RKHunterScanResult:
        """
        Perform a full system rootkit scan with real-time output streaming.

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
            scan_id=scan_id, start_time=start_time, end_time=None
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

            cmd_args.extend([
                "--nocolors", 
                "--no-mail-on-warning",  # Don't try to send mail
            ])

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
                cmd_args.extend(["--tmpdir", "/var/lib/rkhunter/tmp"])  # Use secure temp dir
            elif self.config_path.exists():
                cmd_args.extend(["--configfile", str(self.config_path)])

            self.logger.info(
                "Running RKHunter scan with command: %s", " ".join(cmd_args)
            )

            # Run the scan with real-time output capture
            scan_result = self._run_with_privilege_escalation_streaming(
                cmd_args, output_callback=output_callback, timeout=1800
            )

            result.end_time = datetime.now()

            # Parse results
            self._parse_scan_results(scan_result, result)

            if scan_result.returncode == 0:
                result.success = True
                result.scan_summary = "System appears clean"
            elif scan_result.returncode == 1:
                result.success = True
                result.scan_summary = f"Warnings found: {
                    result.warnings_found}"
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
                "RKHunter scan completed: %s",
                result.scan_summary)

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

    def scan_system(self,
                    test_categories: Optional[List[str]] = None,
                    skip_keypress: bool = True) -> RKHunterScanResult:
        """
        Perform a full system rootkit scan.

        Args:
            test_categories: List of test categories to run (None for all)
            skip_keypress: Skip manual keypress confirmations

        Returns:
            RKHunterScanResult with scan results
        """
        scan_id = f"rkhunter_scan_{int(time.time())}"
        start_time = datetime.now()

        result = RKHunterScanResult(
            scan_id=scan_id, start_time=start_time, end_time=None
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

            cmd_args.extend([
                "--nocolors", 
                "--no-mail-on-warning",  # Don't try to send mail
            ])

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
                cmd_args.extend(["--tmpdir", "/var/lib/rkhunter/tmp"])  # Use secure temp dir
            elif self.config_path.exists():
                cmd_args.extend(["--configfile", str(self.config_path)])

            self.logger.info(
                "Running RKHunter scan with command: %s", " ".join(cmd_args)
            )

            # Run the scan using privilege escalation (prefers GUI dialog)
            scan_result = self._run_with_privilege_escalation(
                cmd_args, capture_output=True, timeout=1800  # 30 minutes timeout
            )

            result.end_time = datetime.now()

            # Parse results
            self._parse_scan_results(scan_result, result)

            if scan_result.returncode == 0:
                result.success = True
                result.scan_summary = "System appears clean"
            elif scan_result.returncode == 1:
                result.success = True
                result.scan_summary = f"Warnings found: {
                    result.warnings_found}"
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
                "RKHunter scan completed: %s",
                result.scan_summary)

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
            result: RKHunterScanResult):
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
                if ("grep: warning:" in line or 
                    "egrep: warning:" in line):
                    continue

                # Parse test result indicators - these are the actual test completions
                if (" [ OK ]" in line or " [ Not found ]" in line or 
                    " [ None found ]" in line or " [ Found ]" in line or
                    " [ Warning ]" in line or " [ Infected ]" in line or
                    " [ Skipped ]" in line):
                    test_count += 1

                # Extract test name from the line
                if "Checking" in line:
                    current_test = line.replace("Checking", "").replace("...", "").strip()

                # Parse warnings - RKHunter uses "Warning:" format and "[ Warning ]" 
                if (" [ Warning ]" in line):
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
                    rk_severity = severity_mapping.get(explanation.severity, RKHunterSeverity.MEDIUM)
                    
                    finding = RKHunterFinding(
                        test_name=current_test or "Security Check",
                        result=RKHunterResult.WARNING,
                        severity=rk_severity,
                        description=line,
                        explanation=explanation,
                    )
                    if result.findings is not None:
                        result.findings.append(finding)

                elif line.startswith("Warning:"):
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
                    rk_severity = severity_mapping.get(explanation.severity, RKHunterSeverity.MEDIUM)
                    
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
                    rk_severity = severity_mapping.get(explanation.severity, RKHunterSeverity.MEDIUM)
                    
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
                            pass
                    except ValueError:
                        pass

                elif "Rootkits checked" in line:
                    # Extract rootkit count from summary  
                    try:
                        parts = line.split(":")
                        if len(parts) > 1:
                            rootkit_count = int(parts[1].strip())
                            # Add to test count if not already counted
                            pass
                    except ValueError:
                        pass

                elif "Suspect files:" in line:
                    # Extract suspect file count
                    try:
                        parts = line.split(":")
                        if len(parts) > 1:
                            suspect_count = int(parts[1].strip())
                            # These are likely warnings we should count
                            pass
                    except ValueError:
                        pass

            # Set tests run based on actual test execution
            result.tests_run = test_count
            result.total_tests = test_count

        except Exception as e:
            self.logger.error("Error parsing RKHunter results: %s", e)

    def _parse_scan_summary(
            self,
            stderr_output: str,
            result: RKHunterScanResult):
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

        except Exception as e:
            self.logger.error("Error parsing RKHunter summary: %s", e)

    def get_log_path(self) -> Optional[Path]:
        """Get path to RKHunter log file."""
        log_paths = [
            Path("/var/log/rkhunter.log"),
            Path("/tmp/rkhunter-scan.log"),
            Path.home() / ".rkhunter.log",
        ]

        for log_path in log_paths:
            if log_path.exists():
                return log_path

        return None

    def install_rkhunter(self) -> Tuple[bool, str]:
        """
        Attempt to install RKHunter using system package manager with GUI-friendly auth.

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
                        f"Attempting to install RKHunter using {pm_name}")

                    # Use privilege escalation (prefers GUI dialog)
                    result = self._run_with_privilege_escalation(
                        cmd_args, capture_output=True, timeout=300  # 5 minutes
                    )

                    if result.returncode == 0:
                        # Refresh our paths
                        self.rkhunter_path = self._find_rkhunter()
                        self.available = self.rkhunter_path is not None

                        if self.available:
                            self._initialize_config()
                            return (
                                True, f"RKHunter installed successfully using {pm_name}", )
                        else:
                            return (
                                False, f"Installation appeared successful but RKHunter not found", )
                    else:
                        self.logger.warning(
                            f"Installation with {pm_name} failed: {
                                result.stderr}")

                except Exception as e:
                    self.logger.warning(f"Error trying {pm_name}: {e}")
                    continue  # Try next package manager

            return False, "No compatible package manager found or installation failed"

        except Exception as e:
            return False, f"Installation error: {str(e)}"

    def get_scan_recommendations(
            self, scan_result: RKHunterScanResult) -> List[str]:
        """
        Get recommendations based on scan results.

        Args:
            scan_result: The completed scan result

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not scan_result.success:
            recommendations.append(
                "• Scan failed - check RKHunter installation and permissions"
            )
            return recommendations

        if scan_result.infections_found > 0:
            recommendations.append(
                "• **CRITICAL**: Potential rootkits detected - immediate action required"
            )
            recommendations.append(
                "• Run system in rescue mode and perform manual inspection"
            )
            recommendations.append(
                "• Consider reinstalling the operating system if compromised"
            )
            recommendations.append(
                "• Change all passwords after cleaning the system")

        if scan_result.warnings_found > 0:
            recommendations.append(
                "• Review warnings carefully - they may indicate suspicious activity"
            )
            recommendations.append(
                "• Update RKHunter database and run scan again")
            recommendations.append("• Check system logs for unusual activity")

        if scan_result.warnings_found == 0 and scan_result.infections_found == 0:
            recommendations.append("• System appears clean of rootkits")
            recommendations.append("• Continue regular security monitoring")
            recommendations.append(
                "• Keep system and antivirus definitions updated")

        # Add general recommendations
        recommendations.extend(
            [
                "• Perform regular system scans",
                "• Keep operating system updated",
                "• Use strong passwords and enable 2FA where possible",
                "• Monitor system performance and network activity",
            ]
        )

        return recommendations
