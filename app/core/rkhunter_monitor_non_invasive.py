#!/usr/bin/env python3
"""Enhanced RKHunter Status Checker - Non-Invasive Implementation
Replaces elevated privilege status checking with activity-based caching
"""

import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

try:
    from app.core.secure_subprocess import run_secure
except ImportError:
    import subprocess
    from collections.abc import Mapping, Sequence
    from typing import Any

    def run_secure(
        argv: Sequence[str],
        *,
        timeout: int = 10,
        check: bool = True,
        allow_root: bool = False,
        env: Mapping[str, str] | None = None,
        capture_output: bool = True,
        text: bool = True,
    ) -> subprocess.CompletedProcess[Any]:
        return subprocess.run(
            argv,
            timeout=timeout,
            check=check,
            env=env,
            capture_output=capture_output,
            text=text,
        )


@dataclass
class RKHunterStatusNonInvasive:
    """Non-invasive RKHunter status information"""

    timestamp: datetime
    available: bool
    version: str
    config_exists: bool
    config_readable: bool
    database_exists: bool
    database_readable: bool
    log_file_exists: bool
    last_scan_attempt: datetime | None
    installation_method: str  # "package", "manual", "not_installed"
    issues_found: list
    cache_valid: bool
    error_message: str = ""


class RKHunterMonitorNonInvasive:
    """Non-invasive RKHunter monitoring using the same principles as firewall solution:
    1. No elevated privilege requirements
    2. Activity-based caching
    3. Multiple detection methods
    4. Graceful degradation
    """

    def __init__(self, cache_duration: int = 300):  # 5 minutes default
        self.cache_duration = cache_duration
        self._status_cache: RKHunterStatusNonInvasive | None = None
        self._cache_time: float | None = None
        self._lock = threading.Lock()

        # Cache file for persistent status
        self.cache_file = Path.home() / ".xanados_rkhunter_status_cache.json"

        # Common RKHunter paths to check
        self.config_paths = [
            str(Path.home() / ".config" / "search-and-destroy" / "rkhunter.conf"),  # User-specific config first
            "/etc/rkhunter.conf",
            "/usr/local/etc/rkhunter.conf",
            "/etc/rkhunter/rkhunter.conf",
        ]

        self.database_paths = [
            "/var/lib/rkhunter/db",
            "/usr/local/lib/rkhunter/db",
            "/var/lib/rkhunter",
        ]

        self.log_paths = [
            "/var/log/rkhunter.log",
            "/var/log/rkhunter/rkhunter.log",
            "/usr/local/var/log/rkhunter.log",
        ]

        # Load persistent cache
        self._load_persistent_cache()

    def _has_arch_permission_issue(self, binary_path: str) -> bool:
        """Check if RKHunter has the Arch Linux permission issue (600 permissions)."""
        try:
            if not os.path.exists(binary_path):
                return False

            stat_info = os.stat(binary_path)
            # Check for 600 permissions (read/write for owner, no execute bit)
            if (stat_info.st_uid == 0 and  # Owned by root
                (stat_info.st_mode & 0o777) == 0o600):  # 600 permissions exactly
                return True

            # Also check if it simply lacks execute permissions
            if not (stat_info.st_mode & 0o111):  # No execute bits at all
                return True

            return False
        except Exception:
            return False

    def _load_persistent_cache(self) -> None:
        """Load cached status from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    data = json.load(f)

                cache_time = data.get("cache_time", 0)
                if time.time() - cache_time < self.cache_duration:
                    status_data = data["status"]
                    status_data["timestamp"] = datetime.fromisoformat(status_data["timestamp"])
                    if status_data.get("last_scan_attempt"):
                        status_data["last_scan_attempt"] = datetime.fromisoformat(
                            status_data["last_scan_attempt"]
                        )

                    self._status_cache = RKHunterStatusNonInvasive(**status_data)
                    self._cache_time = cache_time
                    print("✅ Loaded valid RKHunter status cache")
                    return

            print("📝 No valid RKHunter cache found, will create fresh status")
        except Exception as e:
            print(f"⚠️ Error loading RKHunter cache: {e}")

    def _save_persistent_cache(self) -> None:
        """Save current cache to disk"""
        try:
            if self._status_cache and self._cache_time:
                status_dict = asdict(self._status_cache)
                status_dict["timestamp"] = status_dict["timestamp"].isoformat()
                if status_dict.get("last_scan_attempt"):
                    status_dict["last_scan_attempt"] = status_dict["last_scan_attempt"].isoformat()

                cache_data = {"cache_time": self._cache_time, "status": status_dict}

                with open(self.cache_file, "w") as f:
                    json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving RKHunter cache: {e}")

    def get_status_non_invasive(self, force_refresh: bool = False) -> RKHunterStatusNonInvasive:
        """Get RKHunter status using only non-invasive methods

        This replaces get_current_status() to eliminate sudo requirements
        """
        with self._lock:
            current_time = time.time()

            # Use cached status if available and valid
            if (
                not force_refresh
                and self._status_cache
                and self._cache_time
                and current_time - self._cache_time < self.cache_duration
            ):
                print(
                    f"📋 Using cached RKHunter status (age: {int(current_time - self._cache_time)}s)"
                )
                return self._status_cache

            print("🔄 Checking RKHunter status using non-invasive methods...")

            # Collect fresh status
            status = self._collect_fresh_status()

            # Update cache
            self._status_cache = status
            self._cache_time = current_time

            # Save to persistent cache
            self._save_persistent_cache()

            print("✅ RKHunter status checked successfully (no sudo required)")
            return status

    def _collect_fresh_status(self) -> RKHunterStatusNonInvasive:
        """Collect fresh RKHunter status using only non-invasive methods"""
        issues = []

        # Check if RKHunter is available
        available, version, install_method = self._check_rkhunter_availability()

        if not available:
            return RKHunterStatusNonInvasive(
                timestamp=datetime.now(),
                available=False,
                version=version,
                config_exists=False,
                config_readable=False,
                database_exists=False,
                database_readable=False,
                log_file_exists=False,
                last_scan_attempt=None,
                installation_method=install_method,
                issues_found=["RKHunter is not installed"],
                cache_valid=True,
                error_message="RKHunter not found",
            )

        # Check configuration
        config_exists, config_readable = self._check_configuration()
        if not config_exists:
            issues.append("Configuration file not found")
        elif not config_readable:
            issues.append("Configuration file exists but not readable")

        # Check for Arch Linux permission issue
        rkhunter_paths = ["/usr/bin/rkhunter", "/usr/local/bin/rkhunter"]
        for path in rkhunter_paths:
            if os.path.exists(path) and self._has_arch_permission_issue(path):
                issues.append("RKHunter has incorrect permissions (Arch Linux packaging issue)")
                issues.append("Execute permissions need to be fixed before scanning")
                break

        # Check database
        db_exists, db_readable = self._check_database()
        if not db_exists:
            issues.append("Database directory not found")
        elif not db_readable:
            issues.append("Database directory exists but not readable")

        # Check log files and extract last scan time
        log_exists, last_scan = self._check_logs()
        if not log_exists:
            issues.append("Log file not found - RKHunter may not have been run")

        return RKHunterStatusNonInvasive(
            timestamp=datetime.now(),
            available=True,
            version=version,
            config_exists=config_exists,
            config_readable=config_readable,
            database_exists=db_exists,
            database_readable=db_readable,
            log_file_exists=log_exists,
            last_scan_attempt=last_scan,
            installation_method=install_method,
            issues_found=issues,
            cache_valid=True,
        )

    def _check_rkhunter_availability(self) -> tuple[bool, str, str]:
        """Check if RKHunter is available without elevated privileges"""
        binary_path = None

        try:
            # Method 1: Check if binary exists in PATH
            result = run_secure(["which", "rkhunter"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                binary_path = result.stdout.strip()
        except Exception:
            pass

        # Method 2: If 'which' failed, check common binary locations directly
        if not binary_path:
            common_paths = ["/usr/bin/rkhunter", "/usr/sbin/rkhunter", "/usr/local/bin/rkhunter"]
            for path in common_paths:
                if os.path.exists(path):
                    binary_path = path
                    break

        # If no binary found at all, return not installed
        if not binary_path:
            return False, "Not installed", "not_installed"

        # Method 3: Check if file exists and get basic info
        if os.path.exists(binary_path):
            try:
                stat_info = os.stat(binary_path)
                # Check if the file has restrictive permissions (root only)
                if stat_info.st_uid == 0 and stat_info.st_mode & 0o077 == 0:
                    # Binary exists but has root-only permissions
                    # We can't run --version without sudo, so determine version another way

                    # Try to determine installation method
                    install_method = "manual"
                    if "/usr/bin" in binary_path or "/usr/sbin" in binary_path:
                        install_method = "package"

                    # For package installations, try to get version from package manager
                    if install_method == "package":
                        try:
                            # Try pacman (Arch)
                            result = run_secure(
                                ["pacman", "-Qi", "rkhunter"],
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            if result.returncode == 0:
                                for line in result.stdout.split("\n"):
                                    if line.startswith("Version"):
                                        version = f"Rootkit Hunter {line.split(':')[1].strip()}"
                                        return True, version, install_method
                        except Exception:
                            pass

                        # Try other package managers if needed
                        try:
                            # Try rpm-based systems
                            result = run_secure(
                                ["rpm", "-q", "rkhunter"],
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            if result.returncode == 0:
                                version = f"Rootkit Hunter (via RPM: {result.stdout.strip()})"
                                return True, version, install_method
                        except Exception:
                            pass

                    # If we can't get version, just report as available
                    return (
                        True,
                        "Rootkit Hunter (version requires sudo)",
                        install_method,
                    )

                else:
                    # Binary is readable, try version command
                    try:
                        result = run_secure(
                            ["rkhunter", "--version"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        if result.returncode == 0:
                            version_output = result.stdout.strip()

                            # Parse version from output
                            version = "Available"
                            for line in version_output.split("\n"):
                                if "RKH version" in line or "rkhunter" in line.lower():
                                    version = line.strip()
                                    break

                            # Determine installation method
                            install_method = "manual"
                            if "/usr/bin" in binary_path or "/usr/sbin" in binary_path:
                                install_method = "package"

                            return True, version, install_method
                    except Exception:
                        pass

            except Exception as e:
                print(f"⚠️ Could not check RKHunter binary: {e}")
                return True, "Available (file check failed)", "unknown"

        return True, "Available", "unknown"

    def _check_configuration(self) -> tuple[bool, bool]:
        """Check RKHunter configuration files"""
        for config_path in self.config_paths:
            if os.path.exists(config_path):
                try:
                    # Try to read first few lines to check readability
                    with open(config_path) as f:
                        f.read(100)  # Read first 100 chars
                    return True, True
                except PermissionError:
                    return True, False
                except Exception:
                    continue

        return False, False

    def _check_database(self) -> tuple[bool, bool]:
        """Check RKHunter database directories"""
        for db_path in self.database_paths:
            if os.path.exists(db_path):
                try:
                    # Try to list directory contents
                    os.listdir(db_path)
                    return True, True
                except PermissionError:
                    return True, False
                except Exception:
                    continue

        return False, False

    def _check_logs(self) -> tuple[bool, datetime | None]:
        """Check RKHunter log files and extract last scan time"""
        last_scan = None

        for log_path in self.log_paths:
            if os.path.exists(log_path):
                try:
                    # Try to read last few lines of log file
                    with open(log_path) as f:
                        # Get file modification time as fallback
                        mtime = os.path.getmtime(log_path)
                        last_scan = datetime.fromtimestamp(mtime)

                        # Try to find actual scan timestamps in log
                        try:
                            lines = f.readlines()
                            for line in reversed(lines[-100:]):  # Check last 100 lines
                                if "Starting system scan" in line or "System check" in line:
                                    # Try to parse timestamp from log line
                                    # This is a basic implementation - could be enhanced
                                    break
                        except BaseException:
                            pass  # Use file mtime as fallback

                    return True, last_scan

                except PermissionError:
                    return True, None
                except Exception:
                    continue

        return False, None

    def record_user_activity(self, activity_type: str, details: str = "") -> None:
        """Record user activity related to RKHunter"""
        with self._lock:
            if self._status_cache:
                # Update cache timestamp to keep it fresh during user interaction
                current_time = time.time()
                self._cache_time = current_time
                self._save_persistent_cache()
                print(f"📝 Recorded RKHunter activity: {activity_type} - {details}")


# Global instance
rkhunter_monitor = RKHunterMonitorNonInvasive()


def get_rkhunter_status_non_invasive(
    force_refresh: bool = False,
) -> RKHunterStatusNonInvasive:
    """Convenience function to get RKHunter status without sudo"""
    return rkhunter_monitor.get_status_non_invasive(force_refresh)


def record_rkhunter_activity(activity_type: str, details: str = "") -> None:
    """Convenience function to record RKHunter-related activity"""
    rkhunter_monitor.record_user_activity(activity_type, details)


if __name__ == "__main__":
    print("🧪 TESTING: Non-Invasive RKHunter Monitor")
    print("=" * 50)

    # Test the RKHunter monitor
    status = get_rkhunter_status_non_invasive(force_refresh=True)

    print("\n📊 RKHUNTER STATUS REPORT:")
    print(f"Timestamp: {status.timestamp}")
    print(f"Available: {'✅' if status.available else '❌'}")
    print(f"Version: {status.version}")
    print(f"Installation Method: {status.installation_method}")
    print(f"Config Exists: {'✅' if status.config_exists else '❌'}")
    print(f"Config Readable: {'✅' if status.config_readable else '❌'}")
    print(f"Database Exists: {'✅' if status.database_exists else '❌'}")
    print(f"Database Readable: {'✅' if status.database_readable else '❌'}")
    print(f"Log File Exists: {'✅' if status.log_file_exists else '❌'}")
    print(f"Last Scan Attempt: {status.last_scan_attempt or 'Unknown'}")

    if status.issues_found:
        print("\n⚠️ Issues Found:")
        for issue in status.issues_found:
            print(f"  - {issue}")
    else:
        print("\n✅ No issues found")

    print("\n✅ Test completed successfully - no authentication prompts required!")
