#!/usr/bin/env python3
"""
Enhanced ClamAV wrapper for S&D - Search & Destroy
Supports virus definition updates, multiple signature sources, and detailed scanning
"""
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


class ScanResult(Enum):
    """Scan result types."""

    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class VirusDefinitionInfo:
    """Information about virus definitions."""

    name: str
    version: str
    last_updated: datetime
    size: int
    url: str


@dataclass
class ScanFileResult:
    """Result for a single file scan."""

    file_path: str
    result: ScanResult
    threat_name: str = ""
    threat_type: str = ""
    file_size: int = 0
    scan_time: float = 0.0
    error_message: str = ""


class ClamAVWrapper:
    """Enhanced ClamAV wrapper with full feature support."""

    def __init__(self):
        try:
            from utils.config import CACHE_DIR, load_config, setup_logging
        except ImportError:
            # Create minimal fallbacks for testing
            import logging
            import os

            def setup_logging():
                return logging.getLogger(__name__)

            def load_config():
                return {
                    "advanced_settings": {
                        "scan_timeout": 30,
                        "max_file_size": 100 * 1024 * 1024,
                        "max_recursion_depth": 10,
                    }
                }

            CACHE_DIR = Path("/tmp/test_cache")

        self.logger = setup_logging()
        self.config = load_config()

        # ClamAV executable paths
        self.clamscan_path = self._find_executable("clamscan")
        self.clamdscan_path = self._find_executable("clamdscan")
        self.freshclam_path = self._find_executable("freshclam")
        self.clamd_path = self._find_executable("clamd")

        # Database paths
        self.db_path = Path("/var/lib/clamav")

        # Handle CACHE_DIR which might be mocked during testing
        try:
            if hasattr(
                    CACHE_DIR,
                    "__truediv__"):  # Check if it's a Path object
                self.custom_db_path = CACHE_DIR / "custom_signatures"
            else:
                # Handle string or Mock case
                self.custom_db_path = Path(
                    str(CACHE_DIR)) / "custom_signatures"
        except (TypeError, AttributeError):
            # Fallback for testing
            self.custom_db_path = Path("/tmp/test_cache") / "custom_signatures"

        try:
            self.custom_db_path.mkdir(exist_ok=True)
        except (OSError, AttributeError):
            # Handle case where mkdir fails or path is invalid
            pass

        # Check ClamAV availability
        self.available = self._check_clamav_availability()

        if not self.available:
            self.logger.error("ClamAV not found or not properly installed")

    def _find_executable(self, name: str) -> Optional[str]:
        """Find ClamAV executable in system PATH."""
        import shutil

        return shutil.which(name)

    def _check_clamav_availability(self) -> bool:
        """Check if ClamAV is properly installed and accessible."""
        if not self.clamscan_path:
            return False

        try:
            result = subprocess.run(
                [self.clamscan_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_engine_version(self) -> Tuple[str, str]:
        """Get ClamAV engine and signature database versions."""
        if not self.available:
            return "Not available", "Not available"

        try:
            result = subprocess.run(
                [self.clamscan_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse version output
                lines = result.stdout.strip().split("\n")
                engine_version = "Unknown"
                sig_version = "Unknown"

                for line in lines:
                    if line.startswith("ClamAV"):
                        engine_version = line.split()[1]
                    elif "main.cvd" in line or "main.cld" in line:
                        match = re.search(r"version (\d+)", line)
                        if match:
                            sig_version = match.group(1)

                return engine_version, sig_version

        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        return "Unknown", "Unknown"

    def scan_file(self, file_path: str, **kwargs) -> ScanFileResult:
        """Scan a single file with ClamAV."""
        if not self.available:
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message="ClamAV not available",
            )

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message="File not found",
            )

        # Get file info
        file_size = file_path_obj.stat().st_size
        start_time = datetime.now()

        try:
            # Build command
            cmd = [self.clamscan_path]
            cmd.extend(self._build_scan_options(**kwargs))
            cmd.append(str(file_path_obj))

            # Run scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config["advanced_settings"]["scan_timeout"],
            )

            scan_time = (datetime.now() - start_time).total_seconds()

            # Parse result
            return self._parse_scan_output(
                file_path,
                result.stdout,
                result.stderr,
                result.returncode,
                file_size,
                scan_time,
            )

        except subprocess.TimeoutExpired:
            scan_time = (datetime.now() - start_time).total_seconds()
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.TIMEOUT,
                file_size=file_size,
                scan_time=scan_time,
                error_message="Scan timeout",
            )
        except (subprocess.SubprocessError, OSError) as e:
            scan_time = (datetime.now() - start_time).total_seconds()
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                file_size=file_size,
                scan_time=scan_time,
                error_message=str(e),
            )

    def scan_directory(self, directory_path: str, **
                       kwargs) -> List[ScanFileResult]:
        """Scan a directory recursively."""
        if not self.available:
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.ERROR,
                    error_message="ClamAV not available",
                )
            ]

        directory_obj = Path(directory_path)
        if not directory_obj.exists() or not directory_obj.is_dir():
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.ERROR,
                    error_message="Directory not found",
                )
            ]

        try:
            # Build command for directory scan
            cmd = [self.clamscan_path]
            cmd.extend(self._build_scan_options(**kwargs))
            cmd.extend(["--recursive", str(directory_obj)])

            # Run scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config["advanced_settings"]["scan_timeout"]
                * 10,  # Longer timeout for directories
            )

            # Parse directory scan results
            return self._parse_directory_scan_output(
                result.stdout, result.stderr, result.returncode
            )

        except subprocess.TimeoutExpired:
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.TIMEOUT,
                    error_message="Directory scan timeout",
                )
            ]
        except (subprocess.SubprocessError, OSError) as e:
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.ERROR,
                    error_message=str(e),
                )
            ]

    def _build_scan_options(self, **kwargs) -> List[str]:
        """Build ClamAV scan options from configuration and parameters."""
        options = []
        scan_settings = self.config.get("scan_settings", {})

        # Archive scanning
        if kwargs.get(
            "scan_archives",
            scan_settings.get(
                "scan_archives",
                True)):
            options.append("--scan-archive")

        # Email scanning
        if kwargs.get("scan_email", scan_settings.get("scan_email", True)):
            options.append("--scan-mail")

        # OLE2 scanning (Office documents)
        if kwargs.get("scan_ole2", scan_settings.get("scan_ole2", True)):
            options.append("--scan-ole2")

        # PDF scanning
        if kwargs.get("scan_pd", scan_settings.get("scan_pd", True)):
            options.append("--scan-pd")

        # HTML scanning
        if kwargs.get("scan_html", scan_settings.get("scan_html", True)):
            options.append("--scan-html")

        # Executable scanning
        if kwargs.get(
            "scan_executable",
            scan_settings.get(
                "scan_executable",
                True)):
            options.append("--scan-pe")
            options.append("--scan-el")

        # File size limits
        max_filesize = kwargs.get(
            "max_filesize", scan_settings.get("max_filesize", "100M")
        )
        if max_filesize:
            options.extend(["--max-filesize", str(max_filesize)])

        # Recursion limits
        max_recursion = kwargs.get(
            "max_recursion", scan_settings.get("max_recursion", 16)
        )
        if max_recursion:
            options.extend(["--max-recursion", str(max_recursion)])

        # Max files
        max_files = kwargs.get(
            "max_files", scan_settings.get(
                "max_files", 10000))
        if max_files:
            options.extend(["--max-files", str(max_files)])

        # Custom database path
        if self.custom_db_path.exists() and any(self.custom_db_path.iterdir()):
            options.extend(["--database", str(self.custom_db_path)])

        # Verbose output for better parsing
        options.extend(["--infected", "--verbose"])

        return options

    def _parse_scan_output(
        self,
        file_path: str,
        stdout: str,
        stderr: str,
        returncode: int,
        file_size: int,
        scan_time: float,
    ) -> ScanFileResult:
        """Parse ClamAV scan output for a single file."""

        # Check for errors first
        if returncode == 2:  # ClamAV error
            error_msg = stderr.strip() if stderr else "ClamAV scan error"
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                file_size=file_size,
                scan_time=scan_time,
                error_message=error_msg,
            )

        # Parse threat information
        if returncode == 1:  # Threat found
            threat_match = re.search(r"(.+): (.+) FOUND", stdout)
            if threat_match:
                threat_name = threat_match.group(2)
                threat_type = self._classify_threat(threat_name)

                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.INFECTED,
                    threat_name=threat_name,
                    threat_type=threat_type,
                    file_size=file_size,
                    scan_time=scan_time,
                )

        # Clean file
        return ScanFileResult(
            file_path=file_path,
            result=ScanResult.CLEAN,
            file_size=file_size,
            scan_time=scan_time,
        )

    def _parse_directory_scan_output(
        self, stdout: str, stderr: str, returncode: int
    ) -> List[ScanFileResult]:
        """Parse ClamAV output for directory scan."""
        results = []

        # Parse each line for file results
        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Infected file
            threat_match = re.search(r"(.+): (.+) FOUND", line)
            if threat_match:
                file_path = threat_match.group(1)
                threat_name = threat_match.group(2)
                threat_type = self._classify_threat(threat_name)

                results.append(
                    ScanFileResult(
                        file_path=file_path,
                        result=ScanResult.INFECTED,
                        threat_name=threat_name,
                        threat_type=threat_type,
                        file_size=self._get_file_size(file_path),
                    )
                )

            # Clean file (optional, can be many)
            elif " OK" in line and not line.endswith("OK"):
                file_path = line.replace(" OK", "")
                if Path(file_path).exists():
                    results.append(
                        ScanFileResult(
                            file_path=file_path,
                            result=ScanResult.CLEAN,
                            file_size=self._get_file_size(file_path),
                        )
                    )

        return results

    def _classify_threat(self, threat_name: str) -> str:
        """Classify threat type based on name."""
        threat_name_lower = threat_name.lower()

        if any(word in threat_name_lower for word in ["trojan", "backdoor"]):
            return "Trojan"
        elif any(word in threat_name_lower for word in ["virus", "worm"]):
            return "Virus"
        elif any(word in threat_name_lower for word in ["adware", "pup"]):
            return "Adware/PUP"
        elif any(word in threat_name_lower for word in ["ransomware", "crypto"]):
            return "Ransomware"
        elif any(word in threat_name_lower for word in ["rootkit"]):
            return "Rootkit"
        elif any(word in threat_name_lower for word in ["spyware"]):
            return "Spyware"
        elif any(word in threat_name_lower for word in ["exploit"]):
            return "Exploit"
        else:
            return "Malware"

    def _get_file_size(self, file_path: str) -> int:
        """Get file size safely."""
        try:
            return Path(file_path).stat().st_size
        except (OSError, IOError):
            return 0

    def update_virus_definitions(self) -> bool:
        """Update virus definitions using freshclam.

        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self.available:
            self.logger.error("ClamAV not available")
            return False

        if not self.freshclam_path:
            self.logger.error("freshclam not found in PATH")
            return False

        self.logger.info("Starting virus definitions update...")

        # Try different approaches to update definitions
        update_commands = [
            # First try without sudo (in case user has permissions or custom
            # database directory)
            [self.freshclam_path, "--verbose"],
            # Try with user database directory if system directory fails
            [self.freshclam_path, "--verbose",
                "--datadir", str(self.custom_db_path)],
        ]

        # Add GUI-friendly privilege escalation methods
        pkexec_path = self._find_executable("pkexec")
        if pkexec_path:
            # pkexec provides GUI password prompts
            update_commands.append(
                ["pkexec", self.freshclam_path, "--verbose"])

        # Fallback to sudo (terminal-based)
        sudo_path = self._find_executable("sudo")
        if sudo_path:
            update_commands.append(["sudo", self.freshclam_path, "--verbose"])

        for i, cmd in enumerate(update_commands):
            try:
                self.logger.debug(
                    f"Attempt {
                        i +
                        1}: Running command: {
                        ' '.join(cmd)}")

                # Skip sudo command if we're already running as root
                if cmd[0] == "sudo" and os.getuid() == 0:
                    self.logger.debug(
                        "Already running as root, skipping sudo command")
                    continue

                # Special handling for privilege escalation commands
                if cmd[0] in ["sudo", "pkexec"]:
                    if cmd[0] == "pkexec":
                        self.logger.info(
                            "Using pkexec for GUI password prompt")
                        # pkexec shows GUI password dialog, can capture output
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=300,
                            check=False,
                        )

                        self.logger.debug(f"Return code: {result.returncode}")
                        self.logger.debug(f"STDOUT: {result.stdout}")
                        self.logger.debug(f"STDERR: {result.stderr}")

                        if result.returncode == 0:
                            self.logger.info(
                                "Virus definitions updated successfully with pkexec"
                            )
                            return True

                        # Check if definitions are already up to date
                        output_text = result.stdout + result.stderr
                        if (
                            "is up to date" in output_text.lower()
                            or "database is up-to-date" in output_text.lower()
                        ):
                            self.logger.info(
                                "Virus definitions already up to date")
                            return True

                        self.logger.warning(
                            f"pkexec update attempt {
                                i +
                                1} failed (code {
                                result.returncode}): {
                                result.stderr}")
                        continue

                    else:  # sudo
                        self.logger.info(
                            "Running with sudo - you may be prompted for your password"
                        )
                        # Run sudo command without capturing output so user can
                        # interact
                        result = subprocess.run(
                            cmd, text=True, timeout=300, check=False
                        )

                        # Since we can't capture output with interactive sudo,
                        # check return code and log appropriately
                        if result.returncode == 0:
                            self.logger.info(
                                "Virus definitions updated successfully with sudo"
                            )
                            return True
                        else:
                            self.logger.warning(
                                f"Sudo update attempt {
                                    i +
                                    1} failed (code {
                                    result.returncode})")
                            continue
                else:
                    # Non-sudo commands can capture output normally
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minutes timeout
                        check=False,
                    )

                    self.logger.debug(f"Return code: {result.returncode}")
                    self.logger.debug(f"STDOUT: {result.stdout}")
                    self.logger.debug(f"STDERR: {result.stderr}")

                    if result.returncode == 0:
                        self.logger.info(
                            "Virus definitions updated successfully")
                        return True

                    # Check if definitions are already up to date
                    output_text = result.stdout + result.stderr
                    if (
                        "is up to date" in output_text.lower()
                        or "database is up-to-date" in output_text.lower()
                    ):
                        self.logger.info(
                            "Virus definitions already up to date")
                        return True

                    # Check for specific error patterns
                    if (
                        "permission denied" in result.stderr.lower()
                        or "can't create temporary directory" in result.stderr.lower()
                    ):
                        self.logger.warning(
                            f"Permission error with attempt {
                                i + 1}, trying next method...")
                        continue

                    # If this was the last attempt, log the failure
                    if i == len(update_commands) - 1:
                        self.logger.error(
                            f"Failed to update virus definitions (code {
                                result.returncode}): {
                                result.stderr}")

            except subprocess.TimeoutExpired:
                self.logger.error(
                    f"Virus definition update attempt {
                        i + 1} timed out after 5 minutes")
                continue
            except FileNotFoundError as e:
                if "sudo" in str(e) and cmd[0] == "sudo":
                    self.logger.warning(
                        "sudo not available, skipping sudo method")
                    continue
                else:
                    self.logger.error(
                        f"Command not found in attempt {
                            i + 1}: {e}")
                    continue
            except Exception as e:
                self.logger.error(f"Error in update attempt {i + 1}: {str(e)}")
                continue

        # If all attempts failed, provide helpful error message
        self.logger.error("All virus definition update attempts failed.")
        self.logger.error("Please ensure either:")
        self.logger.error(
            "1. You have write permissions to /var/lib/clamav/, or")
        self.logger.error("2. sudo is available and configured, or")
        self.logger.error(
            "3. Set up a custom database directory with proper permissions"
        )
        return False

    def _update_custom_source(self, source_url: str) -> bool:
        """Update custom signature source."""
        try:
            response = requests.get(source_url, timeout=60)
            response.raise_for_status()

            # Save to custom database directory
            filename = hashlib.md5(source_url.encode()).hexdigest() + ".cvd"
            filepath = self.custom_db_path / filename

            with open(filepath, "wb") as f:
                f.write(response.content)

            self.logger.info("Updated custom source: %s", source_url)
            return True

        except (requests.RequestException, IOError) as e:
            self.logger.error(
                "Failed to update custom source %s: %s", source_url, e)
            return False

    def get_definition_info(self) -> List[VirusDefinitionInfo]:
        """Get information about current virus definitions."""
        definitions = []

        # Check main ClamAV databases - handle permission errors gracefully
        try:
            if self.db_path.exists():
                for db_file in self.db_path.glob("*.c[vl]d"):
                    try:
                        stat = db_file.stat()
                        definitions.append(
                            VirusDefinitionInfo(
                                name=db_file.name,
                                version="Unknown",  # Would need to parse database file for actual version
                                last_updated=datetime.fromtimestamp(
                                    stat.st_mtime),
                                size=stat.st_size,
                                url="official",
                            )
                        )
                    except (OSError, IOError, PermissionError) as e:
                        # Log the error but continue processing other files
                        print(f"Warning: Could not access {db_file}: {e}")
                        continue
        except (OSError, IOError, PermissionError) as e:
            print(
                f"Warning: Could not access database directory {
                    self.db_path}: {e}")

        # Check custom databases - handle permission errors gracefully
        try:
            if self.custom_db_path.exists():
                for db_file in self.custom_db_path.glob("*.cvd"):
                    try:
                        stat = db_file.stat()
                        definitions.append(
                            VirusDefinitionInfo(
                                name=db_file.name,
                                version="Custom",
                                last_updated=datetime.fromtimestamp(
                                    stat.st_mtime),
                                size=stat.st_size,
                                url="custom",
                            ))
                    except (OSError, IOError, PermissionError) as e:
                        # Log the error but continue processing other files
                        print(
                            f"Warning: Could not access custom db {db_file}: {e}")
                        continue
        except (OSError, IOError, PermissionError) as e:
            print(
                f"Warning: Could not access custom database directory {
                    self.custom_db_path}: {e}")

        return definitions

    def check_definition_freshness(self) -> Dict[str, Any]:
        """Check if virus definitions need updating."""
        info = {
            "needs_update": False,
            "oldest_definition": None,
            "total_definitions": 0,
            "last_update": None,
            "definitions_exist": False,
            "error": None,
        }

        try:
            definitions = self.get_definition_info()
            info["total_definitions"] = len(definitions)
            info["definitions_exist"] = len(definitions) > 0

            if not definitions:
                info["needs_update"] = True
                info["last_update"] = "No definitions found"
                return info

            # Find oldest definition
            oldest = min(definitions, key=lambda x: x.last_updated)
            info["oldest_definition"] = oldest.last_updated.isoformat()
            info["last_update"] = oldest.last_updated.isoformat()

            # Check if update needed (older than 1 day)
            if datetime.now() - oldest.last_updated > timedelta(days=1):
                info["needs_update"] = True

        except Exception as e:
            print(f"Error checking definition freshness: {e}")
            info["error"] = str(e)
            info["needs_update"] = True
            info["last_update"] = f"Error: {e}"

        return info
