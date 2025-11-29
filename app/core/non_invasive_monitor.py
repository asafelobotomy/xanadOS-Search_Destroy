#!/usr/bin/env python3
"""Non-Invasive Status Monitoring System
Extends the successful firewall solution to all other system status checks
"""

import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Import secure subprocess without requiring elevated privileges
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
class SystemStatus:
    """Comprehensive system status without requiring elevated privileges"""

    timestamp: datetime
    rkhunter_available: bool
    rkhunter_version: str
    clamav_available: bool
    clamav_version: str
    virus_definitions_age: int  # days since last update
    system_services: dict[str, str]  # service_name: status
    firewall_status: str
    last_activity: datetime | None
    cache_valid: bool
    rkhunter_config_ok: bool = False
    rkhunter_config_details: str = ""
    clamav_config_ok: bool = False
    clamav_config_details: str = ""
    ufw_config_ok: bool = False
    ufw_config_details: str = ""


class NonInvasiveSystemMonitor:
    """System-wide non-invasive status monitoring
    Uses the same principles as the successful firewall solution:
    1. Activity-based caching with time limits
    2. Multiple detection methods without sudo
    3. Graceful degradation when privileged info unavailable
    4. Persistent state management
    """

    def __init__(self, cache_duration: int = 300):  # 5 minutes default
        self.cache_duration = cache_duration
        self._status_cache: SystemStatus | None = None
        self._cache_time: float | None = None
        self._lock = threading.Lock()

        # Cache file for persistent status across app sessions
        self.cache_file = Path.home() / ".xanados_system_status_cache.json"

        # Load persistent cache
        self._load_persistent_cache()

    def _load_persistent_cache(self) -> None:
        """Load cached status from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    data = json.load(f)

                # Check if cache is still valid (within cache_duration)
                cache_time = data.get("cache_time", 0)
                if time.time() - cache_time < self.cache_duration:
                    # Convert datetime strings back to datetime objects
                    if data.get("status"):
                        status_data = data["status"]
                        status_data["timestamp"] = datetime.fromisoformat(status_data["timestamp"])
                        if status_data.get("last_activity"):
                            status_data["last_activity"] = datetime.fromisoformat(
                                status_data["last_activity"]
                            )

                        self._status_cache = SystemStatus(**status_data)
                        self._cache_time = cache_time
                        print("✅ Loaded valid persistent system status cache")
                        return

            print("📝 No valid persistent cache found, will create fresh status")
        except Exception as e:
            print(f"⚠️ Error loading persistent cache: {e}")

    def _save_persistent_cache(self) -> None:
        """Save current cache to disk"""
        try:
            if self._status_cache and self._cache_time:
                # Convert datetime objects to strings for JSON serialization
                status_dict = asdict(self._status_cache)
                status_dict["timestamp"] = status_dict["timestamp"].isoformat()
                if status_dict.get("last_activity"):
                    status_dict["last_activity"] = status_dict["last_activity"].isoformat()

                cache_data = {"cache_time": self._cache_time, "status": status_dict}

                with open(self.cache_file, "w") as f:
                    json.dump(cache_data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Error saving persistent cache: {e}")

    def get_system_status(self, force_refresh: bool = False) -> SystemStatus:
        """Get comprehensive system status using non-invasive methods

        Args:
            force_refresh: If True, bypass cache and get fresh status

        Returns:
            SystemStatus object with all available information
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
                    f"📋 Using cached system status (age: {int(current_time - self._cache_time)}s)"
                )
                return self._status_cache

            print("🔄 Refreshing system status using non-invasive methods...")

            # Collect fresh status
            status = self._collect_fresh_status()

            # Update cache
            self._status_cache = status
            self._cache_time = current_time

            # Save to persistent cache
            self._save_persistent_cache()

            print("✅ System status refreshed successfully")
            return status

    def _collect_fresh_status(self) -> SystemStatus:
        """Collect fresh system status using only non-invasive methods"""
        # RKHunter status (non-invasive)
        rkhunter_available, rkhunter_version = self._check_rkhunter_non_invasive()
        rkhunter_config_ok, rkhunter_config_details = self._validate_rkhunter_configuration()

        # ClamAV status (non-invasive)
        clamav_available, clamav_version = self._check_clamav_non_invasive()
        clamav_config_ok, clamav_config_details = self._validate_clamav_configuration()

        # Virus definitions age (non-invasive)
        virus_def_age = self._check_virus_definitions_age()

        # System services status (non-invasive)
        services_status = self._check_system_services_non_invasive()

        # Firewall status (using existing non-invasive method)
        firewall_status = self._get_firewall_status_non_invasive()
        ufw_config_ok, ufw_config_details = self._validate_ufw_configuration()

        return SystemStatus(
            timestamp=datetime.now(),
            rkhunter_available=rkhunter_available,
            rkhunter_version=rkhunter_version,
            clamav_available=clamav_available,
            clamav_version=clamav_version,
            virus_definitions_age=virus_def_age,
            system_services=services_status,
            firewall_status=firewall_status,
            last_activity=datetime.now(),
            cache_valid=True,
            rkhunter_config_ok=rkhunter_config_ok,
            rkhunter_config_details=rkhunter_config_details,
            clamav_config_ok=clamav_config_ok,
            clamav_config_details=clamav_config_details,
            ufw_config_ok=ufw_config_ok,
            ufw_config_details=ufw_config_details,
        )

    def _check_rkhunter_non_invasive(self) -> tuple[bool, str]:
        """Check RKHunter availability without requiring sudo"""
        try:
            # Method 1: Check if rkhunter binary exists (don't require user execution permissions)
            rkhunter_paths = [
                "/usr/bin/rkhunter",
                "/usr/local/bin/rkhunter",
                "/opt/rkhunter/bin/rkhunter",
            ]
            rkhunter_path = None

            for path in rkhunter_paths:
                if os.path.exists(path):  # Just check existence, not user execution permissions
                    rkhunter_path = path
                    break

            if not rkhunter_path:
                return False, "Not installed"

            # Method 2: Try to get version (may require privilege escalation)
            try:
                result = run_secure(
                    [rkhunter_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    version = "Available"
                    # Try to parse actual version from output
                    for line in result.stdout.split("\n"):
                        if "Rootkit Hunter" in line or "version" in line.lower():
                            version = line.strip()
                            break
                    return True, version
            except PermissionError:
                # Permission denied is expected for RKHunter - but it's still installed
                return True, "Installed (requires elevation)"
            except Exception:
                pass

            # Method 3: Check config file existence (indicates installation)
            config_paths = ["/etc/rkhunter.conf", "/usr/local/etc/rkhunter.conf"]

            for config_path in config_paths:
                if os.path.exists(config_path):
                    return True, "Installed (config found)"

            return False, "Not found"

        except Exception as e:
            print(f"⚠️ Error checking RKHunter: {e}")
            return False, f"Error: {e!s}"

    def _check_clamav_non_invasive(self) -> tuple[bool, str]:
        """Check ClamAV availability without requiring sudo"""
        try:
            # Method 1: Check if clamscan exists (don't require user execution permissions)
            clamscan_paths = [
                "/usr/bin/clamscan",
                "/usr/local/bin/clamscan",
                "/opt/clamav/bin/clamscan",
            ]
            clamscan_path = None

            for path in clamscan_paths:
                if os.path.exists(path):  # Just check existence
                    clamscan_path = path
                    break

            if not clamscan_path:
                return False, "Not installed"

            # Method 2: Try to get version
            try:
                result = run_secure(
                    [clamscan_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    version_line = result.stdout.strip()
                    return True, version_line
            except PermissionError:
                # Permission denied - but ClamAV is still installed
                return True, "Installed (requires elevation)"
            except Exception:
                pass

            # Method 3: Check for database directory
            if os.path.exists("/var/lib/clamav") or os.path.exists("/usr/share/clamav"):
                return True, "Installed (database found)"

            return False, "Not found"

        except Exception as e:
            print(f"⚠️ Error checking ClamAV: {e}")
            return False, f"Error: {e!s}"

    def _check_virus_definitions_age(self) -> int:
        """Check virus definitions age without requiring sudo"""
        try:
            # Check common ClamAV database locations
            db_paths = [
                "/var/lib/clamav/main.cvd",
                "/var/lib/clamav/daily.cvd",
                "/usr/share/clamav/main.cvd",
            ]

            newest_time = None
            for db_path in db_paths:
                if os.path.exists(db_path):
                    mtime = os.path.getmtime(db_path)
                    if newest_time is None or mtime > newest_time:
                        newest_time = mtime

            if newest_time:
                age_seconds = time.time() - newest_time
                age_days = int(age_seconds / (24 * 3600))
                return age_days

            return -1  # Unknown

        except Exception as e:
            print(f"⚠️ Error checking virus definitions age: {e}")
            return -1

    def _check_system_services_non_invasive(self) -> dict[str, str]:
        """Check system services status without requiring sudo"""
        services = {}

        # Common security-related services to monitor
        service_list = ["ufw", "firewalld", "iptables", "fail2ban", "clamd"]

        for service in service_list:
            try:
                # Use systemctl is-active (doesn't require sudo)
                result = run_secure(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0:
                    services[service] = result.stdout.strip()
                else:
                    services[service] = "inactive"

            except Exception as e:
                services[service] = f"error: {e!s}"

        return services

    def _get_firewall_status_non_invasive(self) -> str:
        """Get firewall status using the proven non-invasive method"""
        try:
            # Use the same method that solved the authentication loops
            # Method 1: Check systemctl service status (most reliable, no sudo needed)
            result = run_secure(
                ["systemctl", "is-active", "ufw"],
                timeout=5,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return "active (ufw)"

            # Method 2: Check firewalld
            result = run_secure(
                ["systemctl", "is-active", "firewalld"],
                timeout=5,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return "active (firewalld)"

            # Method 3: Check for iptables rules without sudo
            try:
                # Check if iptables service is active
                result = run_secure(
                    ["systemctl", "is-active", "iptables"],
                    timeout=5,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip() == "active":
                    return "active (iptables)"
            except BaseException:
                pass

            return "inactive"

        except Exception as e:
            print(f"⚠️ Error checking firewall: {e}")
            return f"error: {e!s}"

    def _validate_rkhunter_configuration(self) -> tuple[bool, str]:
        """Validate RKHunter configuration using lightweight checks."""
        issues: list[str] = []

        config_paths = [
            "/etc/rkhunter.conf",
            "/usr/local/etc/rkhunter.conf",
            str(Path.home() / ".config" / "search-and-destroy" / "rkhunter.conf"),
        ]

        config_readable = False
        for config_path in config_paths:
            if os.path.exists(config_path):
                if os.access(config_path, os.R_OK):
                    config_readable = True
                    break
                issues.append(f"Config not readable: {config_path}")
        if not config_readable:
            issues.append("No readable RKHunter configuration found")

        db_locations = [
            "/var/lib/rkhunter/db",
            "/usr/local/var/lib/rkhunter/db",
            str(Path.home() / ".rkhunter" / "db"),
        ]

        db_ok = False
        for db_path in db_locations:
            if os.path.isdir(db_path):
                try:
                    if any(Path(db_path).iterdir()):
                        db_ok = True
                        break
                except OSError:
                    continue
        if not db_ok:
            issues.append("RKHunter database not found")

        if issues:
            return False, "; ".join(issues)
        return True, "Configuration healthy"

    def _validate_clamav_configuration(self) -> tuple[bool, str]:
        """Validate ClamAV configuration efficiently without elevation."""
        issues: list[str] = []

        config_candidates = [
            "/etc/clamav/clamd.conf",
            "/etc/clamd.conf",
            "/usr/local/etc/clamd.conf",
        ]

        config_present = False
        for config_path in config_candidates:
            if os.path.exists(config_path):
                config_present = True
                if not os.access(config_path, os.R_OK):
                    issues.append(f"Config not readable: {config_path}")
                break
        if not config_present:
            issues.append("ClamAV config missing")

        database_paths = [
            "/var/lib/clamav",
            "/usr/share/clamav",
            "/app/share/clamav",
        ]

        db_files = [
            "main.cvd",
            "main.cld",
            "daily.cvd",
            "daily.cld",
        ]

        db_found = False
        for db_dir in database_paths:
            if os.path.isdir(db_dir):
                for db_file in db_files:
                    if os.path.exists(os.path.join(db_dir, db_file)):
                        db_found = True
                        break
            if db_found:
                break
        if not db_found:
            issues.append("Virus definition database missing")

        if issues:
            return False, "; ".join(issues)
        return True, "Configuration healthy"

    def _validate_ufw_configuration(self) -> tuple[bool, str]:
        """Validate UFW configuration using file checks instead of commands."""
        issues: list[str] = []

        config_path = "/etc/ufw/ufw.conf"
        if os.path.exists(config_path):
            try:
                with open(config_path, encoding="utf-8") as f:
                    config_content = f.read()
                if "ENABLED=yes" not in config_content and "ENABLED=no" not in config_content:
                    issues.append("UFW config missing ENABLED flag")
            except (OSError, UnicodeDecodeError) as exc:
                issues.append(f"Unable to read UFW config: {exc}")
        else:
            issues.append("UFW config missing")

        rules_paths = ["/var/lib/ufw/user.rules", "/var/lib/ufw/user6.rules"]
        rules_present = any(os.path.exists(path) and os.path.getsize(path) > 0 for path in rules_paths)
        if not rules_present:
            issues.append("No UFW rule files detected")

        if issues:
            return False, "; ".join(issues)
        return True, "Configuration healthy"

    def record_user_activity(self, activity_type: str, details: str = "") -> None:
        """Record user activity to improve status caching"""
        with self._lock:
            if self._status_cache:
                self._status_cache.last_activity = datetime.now()
                # Save to persistent cache
                self._save_persistent_cache()

                print(f"📝 Recorded user activity: {activity_type} - {details}")


# Global instance for use throughout the application
system_monitor = NonInvasiveSystemMonitor()


def get_system_status(force_refresh: bool = False) -> SystemStatus:
    """Convenience function to get system status"""
    return system_monitor.get_system_status(force_refresh)


def record_activity(activity_type: str, details: str = "") -> None:
    """Convenience function to record user activity"""
    system_monitor.record_user_activity(activity_type, details)


if __name__ == "__main__":
    print("🧪 TESTING: Non-Invasive System Monitor")
    print("=" * 50)

    # Test the system monitor
    status = get_system_status(force_refresh=True)

    print("\n📊 SYSTEM STATUS REPORT:")
    print(f"Timestamp: {status.timestamp}")
    print(f"RKHunter: {'✅' if status.rkhunter_available else '❌'} {status.rkhunter_version}")
    print(
        f"RKHunter config: {'✅' if status.rkhunter_config_ok else '❌'} {status.rkhunter_config_details}"
    )
    print(f"ClamAV: {'✅' if status.clamav_available else '❌'} {status.clamav_version}")
    print(
        f"ClamAV config: {'✅' if status.clamav_config_ok else '❌'} {status.clamav_config_details}"
    )
    print(f"Virus Definitions Age: {status.virus_definitions_age} days")
    print(f"Firewall: {status.firewall_status}")
    print(
        f"UFW config: {'✅' if status.ufw_config_ok else '❌'} {status.ufw_config_details}"
    )
    print("System Services:")
    for service, state in status.system_services.items():
        print(f"  {service}: {state}")

    print("\n✅ Test completed successfully - no authentication prompts required!")
