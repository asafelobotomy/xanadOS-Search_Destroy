#!/usr/bin/env python3
"""
RKHunter (Rootkit Hunter) integration wrapper for S&D - Search & Destroy
Provides rootkit detection capabilities complementing ClamAV
"""

import logging
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os


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

    def _run_with_privilege_escalation(
            self,
            cmd_args: List[str],
            capture_output: bool = True,
            timeout: int = 300) -> subprocess.CompletedProcess:
        """
        Run a command with privilege escalation, preferring GUI methods.

        Args:
            cmd_args: Command arguments (without sudo/pkexec prefix)
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds

        Returns:
            subprocess.CompletedProcess: The result of the command
        """
        # Try different privilege escalation methods in order of preference
        escalation_methods = []

        # First preference: pkexec (GUI password dialog)
        pkexec_path = self._find_executable("pkexec")
        if pkexec_path:
            escalation_methods.append(("pkexec", [pkexec_path] + cmd_args))

        # Fallback: sudo (terminal password prompt)
        sudo_path = self._find_executable("sudo")
        if sudo_path:
            escalation_methods.append(("sudo", [sudo_path] + cmd_args))

        # If already root, run directly
        if os.getuid() == 0:
            escalation_methods.insert(0, ("direct", cmd_args))

        last_error = None

        for method_name, full_cmd in escalation_methods:
            try:
                self.logger.debug(
                    f"Trying {method_name}: {
                        ' '.join(full_cmd)}")

                if method_name == "pkexec":
                    # pkexec shows GUI password dialog
                    self.logger.info("Using GUI password dialog (pkexec)")
                    result = subprocess.run(
                        full_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                elif method_name == "sudo":
                    # sudo uses terminal password prompt
                    self.logger.info("Using terminal password prompt (sudo)")
                    if capture_output:
                        # For sudo, we might need to handle interactive input
                        # differently
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
                else:  # direct
                    result = subprocess.run(
                        full_cmd,
                        capture_output=capture_output,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )

                # Check if command succeeded
                if result.returncode == 0:
                    self.logger.info(f"Command succeeded using {method_name}")
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

# Database locations
DBDIR=/var/lib/rkhunter/db
SCRIPTDIR=/usr/share/rkhunter/scripts
BINDIR=/usr/bin

# Disable GUI prompts (for automated scanning)
AUTO_X_DETECT=1
WHITELISTED_IS_WHITE=1
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
            return False

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

            cmd_args.extend(["--nocolors", "--report-warnings-only"])

            # Add specific test categories if specified
            if test_categories:
                for category in test_categories:
                    if category in self.test_categories:
                        for test in self.test_categories[category]:
                            cmd_args.extend(["--enable", test])

            # Add configuration file
            if self.config_path.exists():
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
            output_lines = scan_process.stdout.split("\n")

            current_test = ""

            for line in output_lines:
                line = line.strip()

                if not line:
                    continue

                # Parse test results
                if "Checking" in line:
                    current_test = line.replace("Checking", "").strip()

                elif "[ Warning ]" in line:
                    result.warnings_found += 1
                    finding = RKHunterFinding(
                        test_name=current_test or "Unknown Test",
                        result=RKHunterResult.WARNING,
                        severity=RKHunterSeverity.MEDIUM,
                        description=line,
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

                elif "[ OK ]" in line:
                    result.tests_run += 1

            # Parse summary information from stderr if available
            if scan_process.stderr:
                self._parse_scan_summary(scan_process.stderr, result)

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
                (["dn", "install", "-y", "rkhunter"], "dn"),
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
                                True,
                                    f"RKHunter installed successfully using {pm_name}",
                                    )
                        else:
                            return (
                                False,
                                    "Installation appeared successful but RKHunter not found",
                                    )
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
