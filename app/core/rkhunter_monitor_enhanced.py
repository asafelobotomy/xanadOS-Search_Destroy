#!/usr/bin/env python3
"""Enhanced RKHunter Status Checker - Non-Invasive Implementation
Optimized for security, usability, and compatibility across Linux distributions
Based on comprehensive permissions research and best practices
"""

import json
import os
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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
class RKHunterStatusEnhanced:
    """Enhanced RKHunter status with comprehensive detection info"""

    timestamp: datetime
    available: bool
    version: str
    config_exists: bool
    config_readable: bool
    config_path: Optional[str]
    database_exists: bool
    database_readable: bool
    log_exists: bool
    last_scan_attempt: Optional[datetime]

    # Enhanced fields based on research
    binary_path: Optional[str]
    binary_permissions: Optional[str]
    install_method: str
    distribution_type: str
    permission_issues: List[str]
    user_solutions: List[str]
    confidence_level: str
    status_message: str


class RKHunterMonitorEnhanced:
    """Enhanced RKHunter monitor with optimized detection and user experience"""

    def __init__(self, cache_duration: int = 300):  # 5 minutes default
        self.cache_duration = cache_duration
        self._status_cache: RKHunterStatusEnhanced | None = None
        self._cache_time: float | None = None
        self._lock = threading.Lock()

        # Cache file for persistent status
        self.cache_file = Path.home() / ".xanados_rkhunter_status_cache.json"

        # Enhanced configuration cascade based on research
        self.config_paths = [
            # User-specific configs (highest priority for accessibility)
            str(Path.home() / ".config" / "search-and-destroy" / "rkhunter.conf"),
            str(Path.home() / ".rkhunter.conf"),
            # System configs (standard locations)
            "/etc/rkhunter.conf",
            "/usr/local/etc/rkhunter.conf",
            "/etc/rkhunter/rkhunter.conf",
        ]

        # Binary search paths
        self.binary_paths = [
            "/usr/bin/rkhunter",
            "/usr/local/bin/rkhunter",
            "/usr/sbin/rkhunter",
            "/opt/rkhunter/bin/rkhunter"
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

        # Detect distribution for optimized handling
        self.distribution_type = self._detect_distribution()

        # Load persistent cache
        self._load_persistent_cache()

    def _detect_distribution(self) -> str:
        """Detect Linux distribution for distribution-specific handling"""
        try:
            # Check for distribution-specific files
            if os.path.exists('/etc/arch-release'):
                return 'arch'
            elif os.path.exists('/etc/debian_version'):
                return 'debian'
            elif os.path.exists('/etc/redhat-release'):
                return 'redhat'
            elif os.path.exists('/etc/fedora-release'):
                return 'fedora'

            # Fallback: check /etc/os-release
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'arch' in content:
                        return 'arch'
                    elif 'ubuntu' in content or 'debian' in content:
                        return 'debian'
                    elif 'centos' in content or 'rhel' in content:
                        return 'redhat'
                    elif 'fedora' in content:
                        return 'fedora'

            return 'unknown'
        except Exception:
            return 'unknown'

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

                    self._status_cache = RKHunterStatusEnhanced(**status_data)
                    self._cache_time = cache_time
                    print("✅ Loaded valid enhanced RKHunter status cache")
                    return

        except Exception as e:
            print(f"⚠️ Error loading RKHunter status cache: {e}")

        # If cache loading fails, invalidate
        self._status_cache = None
        self._cache_time = None

    def _save_persistent_cache(self, status: RKHunterStatusEnhanced) -> None:
        """Save status to persistent cache"""
        try:
            # Ensure cache directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            cache_data = {
                "cache_time": time.time(),
                "status": asdict(status),
            }

            # Convert datetime objects to ISO format
            cache_data["status"]["timestamp"] = status.timestamp.isoformat()
            if status.last_scan_attempt:
                cache_data["status"]["last_scan_attempt"] = status.last_scan_attempt.isoformat()

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Error saving RKHunter status cache: {e}")

    def get_status_enhanced(self, force_refresh: bool = False) -> RKHunterStatusEnhanced:
        """Get enhanced RKHunter status with optimized detection"""
        with self._lock:
            # Return cached status if valid
            if (not force_refresh and
                self._status_cache is not None and
                self._cache_time is not None and
                time.time() - self._cache_time < self.cache_duration):

                age = int(time.time() - self._cache_time)
                print(f"📋 Using cached enhanced RKHunter status (age: {age}s)")
                return self._status_cache

            # Perform fresh detection
            print("🔄 Performing enhanced RKHunter status check...")
            status = self._perform_enhanced_detection()

            # Update cache
            self._status_cache = status
            self._cache_time = time.time()
            self._save_persistent_cache(status)

            return status

    def _perform_enhanced_detection(self) -> RKHunterStatusEnhanced:
        """Perform comprehensive RKHunter detection"""
        timestamp = datetime.now()

        # Initialize status with defaults
        status = RKHunterStatusEnhanced(
            timestamp=timestamp,
            available=False,
            version="Unknown",
            config_exists=False,
            config_readable=False,
            config_path=None,
            database_exists=False,
            database_readable=False,
            log_exists=False,
            last_scan_attempt=None,
            binary_path=None,
            binary_permissions=None,
            install_method="unknown",
            distribution_type=self.distribution_type,
            permission_issues=[],
            user_solutions=[],
            confidence_level="low",
            status_message=""
        )

        # Enhanced binary detection
        binary_info = self._detect_binary_enhanced()
        status.binary_path = binary_info["path"]
        status.binary_permissions = binary_info["permissions"]

        # Multi-method availability check
        availability = self._check_availability_enhanced()
        status.available = availability["available"]
        status.version = availability["version"]
        status.install_method = availability["install_method"]

        # Enhanced configuration detection
        config_info = self._detect_configuration_enhanced()
        status.config_exists = config_info["exists"]
        status.config_readable = config_info["readable"]
        status.config_path = config_info["path"]

        # Database and log detection
        status.database_exists, status.database_readable = self._check_database_enhanced()
        status.log_exists = self._check_logs_enhanced()

        # Issue analysis and user solutions
        issues_analysis = self._analyze_issues_enhanced(status)
        status.permission_issues = issues_analysis["issues"]
        status.user_solutions = issues_analysis["solutions"]

        # Generate user-friendly status message
        status_info = self._generate_status_message_enhanced(status)
        status.status_message = status_info["message"]
        status.confidence_level = status_info["confidence"]

        return status

    def _detect_binary_enhanced(self) -> Dict[str, Optional[str]]:
        """Enhanced binary detection with permission analysis"""
        for binary_path in self.binary_paths:
            if os.path.exists(binary_path):
                try:
                    stat_info = os.stat(binary_path)
                    permissions = oct(stat_info.st_mode)[-3:]

                    return {
                        "path": binary_path,
                        "permissions": permissions,
                        "exists": True,
                        "executable": os.access(binary_path, os.X_OK)
                    }
                except OSError:
                    continue

        return {"path": None, "permissions": None, "exists": False, "executable": False}

    def _check_availability_enhanced(self) -> Dict[str, Union[bool, str]]:
        """Enhanced availability checking using multiple methods"""
        methods = {
            "which_command": self._check_via_which(),
            "direct_execution": self._check_via_execution(),
            "package_manager": self._check_via_package_manager(),
            "file_existence": self._check_via_file_existence()
        }

        # Determine overall availability
        available = any(method["available"] for method in methods.values())

        # Get best version and install method
        version = "Unknown"
        install_method = "unknown"

        # Prioritize direct execution for version info
        for method_name in ["direct_execution", "package_manager", "which_command", "file_existence"]:
            method_result = methods[method_name]
            if method_result["available"] and method_result.get("version"):
                version = method_result["version"]
                install_method = method_result.get("install_method", method_name)
                break

        return {
            "available": available,
            "version": version,
            "install_method": install_method
        }

    def _check_via_which(self) -> Dict[str, Union[bool, str]]:
        """Check availability via 'which' command"""
        try:
            result = run_secure(["which", "rkhunter"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return {
                    "available": True,
                    "path": result.stdout.strip(),
                    "install_method": "package"
                }
        except Exception:
            pass

        return {"available": False}

    def _check_via_execution(self) -> Dict[str, Union[bool, str]]:
        """Check availability via direct execution"""
        try:
            result = run_secure(["rkhunter", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "Rootkit Hunter" in result.stdout:
                # Parse version from output
                version = "Rootkit Hunter"
                for line in result.stdout.split("\n"):
                    if "version" in line.lower() and ("1." in line or "2." in line):
                        version = line.strip()
                        break
                    elif "Rootkit Hunter version" in line:
                        version = line.strip()
                        break

                return {
                    "available": True,
                    "version": version,
                    "install_method": "accessible"
                }
        except Exception:
            pass

        return {"available": False}

    def _check_via_package_manager(self) -> Dict[str, Union[bool, str]]:
        """Check installation via package managers"""
        package_managers = [
            (["pacman", "-Q", "rkhunter"], "pacman"),
            (["dpkg", "-l", "rkhunter"], "dpkg"),
            (["rpm", "-q", "rkhunter"], "rpm")
        ]

        for cmd, manager in package_managers:
            try:
                result = run_secure(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and "rkhunter" in result.stdout:
                    return {
                        "available": True,
                        "version": f"Installed via {manager}",
                        "install_method": manager
                    }
            except Exception:
                continue

        return {"available": False}

    def _check_via_file_existence(self) -> Dict[str, Union[bool, str]]:
        """Check via direct file existence"""
        binary_info = self._detect_binary_enhanced()
        if binary_info["exists"]:
            return {
                "available": True,
                "path": binary_info["path"],
                "permissions": binary_info["permissions"],
                "executable": binary_info["executable"],
                "install_method": "file_system"
            }

        return {"available": False}

    def _detect_configuration_enhanced(self) -> Dict[str, Union[bool, str, None]]:
        """Enhanced configuration detection with user accessibility priority"""
        for config_path in self.config_paths:
            expanded_path = os.path.expanduser(config_path)
            if os.path.exists(expanded_path):
                readable = os.access(expanded_path, os.R_OK)
                return {
                    "path": expanded_path,
                    "readable": readable,
                    "exists": True
                }

        return {"path": None, "readable": False, "exists": False}

    def _check_database_enhanced(self) -> Tuple[bool, bool]:
        """Enhanced database checking"""
        for db_path in self.database_paths:
            if os.path.exists(db_path):
                readable = os.access(db_path, os.R_OK)
                return True, readable

        return False, False

    def _check_logs_enhanced(self) -> bool:
        """Enhanced log checking"""
        for log_path in self.log_paths:
            if os.path.exists(log_path):
                return True
        return False

    def _analyze_issues_enhanced(self, status: RKHunterStatusEnhanced) -> Dict[str, List[str]]:
        """Analyze issues and provide actionable solutions"""
        issues = []
        solutions = []

        # Check for Arch Linux permission anomaly
        if (status.distribution_type == "arch" and
            status.binary_permissions == "700"):
            issues.append("RKHunter has restrictive permissions (Arch Linux anomaly)")
            solutions.append("Fix with: sudo chmod 755 /usr/bin/rkhunter")

        # Check for inaccessible configuration
        if status.config_exists and not status.config_readable:
            issues.append("Configuration file exists but is not readable")
            solutions.append("Create user config with: mkdir -p ~/.config/search-and-destroy && cp /etc/rkhunter.conf ~/.config/search-and-destroy/")

        # Check for missing configuration
        if not status.config_exists:
            issues.append("No accessible configuration file found")
            solutions.append("Create user-specific configuration file")

        # Check for binary not executable
        if status.binary_path and not os.access(status.binary_path, os.X_OK):
            issues.append("RKHunter binary is not executable by current user")
            if status.binary_permissions == "700":
                solutions.append(f"Fix permissions: sudo chmod 755 {status.binary_path}")
            else:
                solutions.append("Run with sudo for elevated privileges")

        # Check for not installed
        if not status.available:
            issues.append("RKHunter is not installed")
            install_cmd = self._get_install_command()
            solutions.append(f"Install with: {install_cmd}")

        return {"issues": issues, "solutions": solutions}

    def _get_install_command(self) -> str:
        """Get distribution-specific install command"""
        commands = {
            "arch": "sudo pacman -S rkhunter",
            "debian": "sudo apt update && sudo apt install rkhunter",
            "redhat": "sudo yum install epel-release && sudo yum install rkhunter",
            "fedora": "sudo dnf install rkhunter"
        }

        return commands.get(self.distribution_type, "Use your package manager to install rkhunter")

    def _generate_status_message_enhanced(self, status: RKHunterStatusEnhanced) -> Dict[str, str]:
        """Generate enhanced user-friendly status message"""
        if not status.available:
            return {
                "message": "❌ RKHunter is not installed on this system",
                "confidence": "high"
            }

        if status.permission_issues:
            severity = "high" if any("not executable" in issue for issue in status.permission_issues) else "medium"
            if severity == "high":
                return {
                    "message": "⚠️ RKHunter is installed but has access issues",
                    "confidence": "high"
                }
            else:
                return {
                    "message": "⚡ RKHunter is available with minor configuration issues",
                    "confidence": "medium"
                }

        return {
            "message": "✅ RKHunter is properly installed and accessible",
            "confidence": "high"
        }

    def create_user_configuration(self) -> Optional[str]:
        """Create user-accessible configuration file"""
        user_config_dir = Path.home() / ".config" / "search-and-destroy"
        user_config_path = user_config_dir / "rkhunter.conf"

        if user_config_path.exists():
            return str(user_config_path)

        # Create directory
        user_config_dir.mkdir(parents=True, exist_ok=True)

        # Try to copy system config
        system_configs = ["/etc/rkhunter.conf", "/usr/local/etc/rkhunter.conf"]
        for system_config in system_configs:
            if os.path.exists(system_config):
                try:
                    shutil.copy2(system_config, user_config_path)
                    print(f"✅ Created user configuration: {user_config_path}")
                    return str(user_config_path)
                except (PermissionError, IOError):
                    continue

        # Create minimal config if copy fails
        minimal_config = """# User-specific RKHunter configuration
# Generated by xanadOS Search & Destroy

# Update settings
UPDATE_MIRRORS=1
MIRRORS_MODE=0
WEB_CMD=""

# Security settings
ALLOW_SSH_ROOT_USER=no

# Whitelist common false positives
ALLOWHIDDENDIR="/dev/.udev"
ALLOWHIDDENDIR="/dev/.static"
ALLOWHIDDENDIR="/dev/.initramfs"

# Package manager integration (Debian-based systems)
PKGMGR=DPKG

# Disable problematic checks that often cause false positives
DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps apps"
"""

        try:
            with open(user_config_path, "w") as f:
                f.write(minimal_config)
            print(f"✅ Created minimal user configuration: {user_config_path}")
            return str(user_config_path)
        except IOError:
            return None

    def get_installation_suggestions(self) -> Dict[str, Union[str, List[str]]]:
        """Get distribution-specific installation suggestions"""
        suggestions = {
            "command": self._get_install_command(),
            "distribution": self.distribution_type,
            "notes": self._get_installation_notes()
        }

        return suggestions

    def _get_installation_notes(self) -> List[str]:
        """Get distribution-specific installation notes"""
        notes = []

        if self.distribution_type == "arch":
            notes.append("After installation, fix permissions: sudo chmod 755 /usr/bin/rkhunter")
        elif self.distribution_type in ["redhat", "centos"]:
            notes.append("EPEL repository required for RKHunter")
        elif self.distribution_type in ["debian", "ubuntu"]:
            notes.append("Run 'sudo rkhunter --propupd' after installation")

        return notes


# Legacy compatibility function
def get_rkhunter_status_enhanced() -> RKHunterStatusEnhanced:
    """Legacy compatibility function for enhanced status"""
    monitor = RKHunterMonitorEnhanced()
    return monitor.get_status_enhanced()


# Backward compatibility - provide original interface
class RKHunterMonitorNonInvasive(RKHunterMonitorEnhanced):
    """Backward compatibility wrapper"""

    def get_status_non_invasive(self, force_refresh: bool = False) -> RKHunterStatusEnhanced:
        """Backward compatibility method"""
        return self.get_status_enhanced(force_refresh)


if __name__ == "__main__":
    # Demo the enhanced monitor
    monitor = RKHunterMonitorEnhanced()
    status = monitor.get_status_enhanced()

    print("🔍 Enhanced RKHunter Monitor Results")
    print("=" * 50)
    print(f"Status: {status.status_message}")
    print(f"Available: {status.available}")
    print(f"Binary Path: {status.binary_path}")
    print(f"Binary Permissions: {status.binary_permissions}")
    print(f"Config Path: {status.config_path}")
    print(f"Config Readable: {status.config_readable}")
    print(f"Version: {status.version}")
    print(f"Install Method: {status.install_method}")
    print(f"Distribution: {status.distribution_type}")
    print(f"Confidence: {status.confidence_level}")

    if status.permission_issues:
        print(f"\n⚠️ Issues Found:")
        for issue in status.permission_issues:
            print(f"  - {issue}")

    if status.user_solutions:
        print(f"\n💡 Solutions:")
        for solution in status.user_solutions:
            print(f"  - {solution}")
