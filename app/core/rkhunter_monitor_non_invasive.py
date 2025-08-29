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

    def run_secure(cmd, **kwargs):
        return subprocess.run(cmd, **kwargs)


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

    def _load_persistent_cache(self):
        """Load cached status from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    data = json.load(f)

                cache_time = data.get("cache_time", 0)
                if time.time() - cache_time < self.cache_duration:
                    status_data = data["status"]
                    status_data["timestamp"] = datetime.fromisoformat(
                        status_data["timestamp"]
                    )
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

    def _save_persistent_cache(self):
        """Save current cache to disk"""
        try:
            if self._status_cache and self._cache_time:
                status_dict = asdict(self._status_cache)
                status_dict["timestamp"] = status_dict["timestamp"].isoformat()
                if status_dict.get("last_scan_attempt"):
                    status_dict["last_scan_attempt"] = status_dict[
                        "last_scan_attempt"
                    ].isoformat()

                cache_data = {"cache_time": self._cache_time, "status": status_dict}

                with open(self.cache_file, "w") as f:
                    json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving RKHunter cache: {e}")

    def get_status_non_invasive(
        self, force_refresh: bool = False
    ) -> RKHunterStatusNonInvasive:
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
        try:
            # Method 1: Check if binary exists in PATH
            result = run_secure(
                ["which", "rkhunter"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return False, "Not installed", "not_installed"

            binary_path = result.stdout.strip()

            # Method 2: Try to get version (usually doesn't require sudo for --version)
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

            except Exception as e:
                print(f"⚠️ Could not get RKHunter version: {e}")
                return True, "Available (version check failed)", "unknown"

            return True, "Available", "unknown"

        except Exception as e:
            print(f"⚠️ Error checking RKHunter availability: {e}")
            return False, f"Error: {e!s}", "error"

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
                                if (
                                    "Starting system scan" in line
                                    or "System check" in line
                                ):
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

    def record_user_activity(self, activity_type: str, details: str = ""):
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


def record_rkhunter_activity(activity_type: str, details: str = ""):
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
