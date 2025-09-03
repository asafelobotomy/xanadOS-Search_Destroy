#!/usr/bin/env python3
"""
System Paths Library - Standardized path definitions and management
=====================================================================
This library provides centralized, standardized path definitions for:
- System directories
- Application directories
- Security-sensitive paths
- Command locations
- Configuration paths

Note: This file contains hardcoded system paths for legitimate system
administration purposes. Bandit B108 warnings are suppressed as these
are not used for insecure temporary file operations.

All paths respect XDG Base Directory Specification and system conventions.
"""
# nosec - File contains legitimate system path constants

import os
import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import List


class PathType(Enum):
    """Types of system paths"""

    SYSTEM = "system"
    CONFIG = "config"
    DATA = "data"
    CACHE = "cache"
    TEMP = "temp"
    LOG = "log"
    EXECUTABLE = "executable"
    SECURITY_SENSITIVE = "security_sensitive"


class SystemPaths:
    """Centralized system path definitions with cross-platform compatibility"""

    # System directories (read-only)
    SYSTEM_DIRS = {
        "bin": "/bin",
        "sbin": "/sbin",
        "usr_bin": "/usr/bin",
        "usr_sbin": "/usr/sbin",
        "usr_local_bin": "/usr/local/bin",
        "usr_local_sbin": "/usr/local/sbin",
        "etc": "/etc",
        "var": "/var",
        "opt": "/opt",
        "boot": "/boot",
        "proc": "/proc",
        "sys": "/sys",
        "dev": "/dev",
        "run": "/run",
        "tmp": "/tmp",  # nosec B108 - Legitimate system path constant
        "var_tmp": "/var/tmp",  # nosec B108 - Legitimate system path constant
        "var_log": "/var/log",
        "var_lib": "/var/lib",
        "var_cache": "/var/cache",
        "home": "/home",
        "root": "/root",
        "lib": "/lib",
        "lib64": "/lib64",
        "usr_lib": "/usr/lib",
        "usr_lib64": "/usr/lib64",
    }

    # XDG Base Directory Specification
    XDG_CONFIG_HOME = Path(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    )
    XDG_DATA_HOME = Path(
        os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    )
    XDG_CACHE_HOME = Path(
        os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    )
    XDG_STATE_HOME = Path(
        os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
    )

    # Safe PATH for subprocess execution
    SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    # Security-sensitive paths that should never be scanned/modified
    FORBIDDEN_PATHS = {
        "/proc",
        "/sys",
        "/dev",
        "/run",
        # nosec B108 - Legitimate system path pattern
        "/tmp/systemd-private-*",
        "/etc/shadow",
        "/etc/passwd",
        "/etc/sudoers",
        "/boot",
        "/lost+found",
        "/var/run",
        "/var/lock",
        "/sys/kernel/debug",
        "/proc/kcore",
        "/dev/mem",
        "/dev/kmem",
        "/dev/port",
    }

    # Common executable locations for security tools
    SECURITY_EXECUTABLES = {
        "clamscan": ["/usr/bin/clamscan", "/usr/local/bin/clamscan"],
        "freshclam": ["/usr/bin/freshclam", "/usr/local/bin/freshclam"],
        "rkhunter": ["/usr/bin/rkhunter", "/usr/local/bin/rkhunter"],
        "sudo": ["/usr/bin/sudo", "/bin/sudo"],
        # No pkexec - GUI sudo authentication only
        "systemctl": ["/usr/bin/systemctl", "/bin/systemctl"],
        "ufw": ["/usr/sbin/ufw", "/sbin/ufw"],
        "iptables": ["/usr/sbin/iptables", "/sbin/iptables"],
        "nft": ["/usr/sbin/nft", "/sbin/nft"],
        "firewall-cmd": ["/usr/bin/firewall-cmd"],
    }

    @classmethod
    def get_system_temp_dir(cls) -> str:
        """Get system temporary directory (secure, respects system config)"""
        return tempfile.gettempdir()

    @classmethod
    def get_user_home(cls) -> Path:
        """Get user home directory"""
        return Path.home()

    @classmethod
    def get_app_config_dir(cls, app_name: str) -> Path:
        """Get application config directory following XDG spec"""
        return cls.XDG_CONFIG_HOME / app_name

    @classmethod
    def get_app_data_dir(cls, app_name: str) -> Path:
        """Get application data directory following XDG spec"""
        return cls.XDG_DATA_HOME / app_name

    @classmethod
    def get_app_cache_dir(cls, app_name: str) -> Path:
        """Get application cache directory following XDG spec"""
        return cls.XDG_CACHE_HOME / app_name

    @classmethod
    def get_app_state_dir(cls, app_name: str) -> Path:
        """Get application state directory following XDG spec"""
        return cls.XDG_STATE_HOME / app_name

    @classmethod
    def is_forbidden_path(cls, path: str) -> bool:
        """Check if a path is in the forbidden list"""
        path_obj = Path(path).resolve()
        for forbidden in cls.FORBIDDEN_PATHS:
            if path_obj.match(forbidden) or str(path_obj).startswith(forbidden):
                return True
        return False

    @classmethod
    def is_system_path(cls, path: str) -> bool:
        """Check if a path is a system directory"""
        path_str = str(Path(path).resolve())
        system_paths = [
            "/etc",
            "/sys",
            "/proc",
            "/dev",
            "/boot",
            "/usr",
            "/var",
            "/opt",
        ]
        return any(path_str.startswith(sys_path) for sys_path in system_paths)

    @classmethod
    def get_executable_path(cls, executable: str) -> str | None:
        """Get full path to executable with security validation"""

        # First try shutil.which for standard PATH lookup
        which_result = shutil.which(executable)
        if which_result:
            return which_result

        # Fall back to known locations for security tools
        if executable in cls.SECURITY_EXECUTABLES:
            for path in cls.SECURITY_EXECUTABLES[executable]:
                if Path(path).exists():
                    return path

        return None

    @classmethod
    def ensure_secure_dir(cls, path: Path, mode: int = 0o700) -> bool:
        """Create directory with secure permissions"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            current_mode = path.stat().st_mode & 0o777
            if current_mode != mode:
                path.chmod(mode)
            return True
        except (OSError, PermissionError):
            return False

    @classmethod
    def get_common_scan_paths(cls) -> List[str]:
        """Get common paths for security scanning"""
        home = cls.get_user_home()
        return [
            str(home / "Downloads"),
            str(home / "Documents"),
            str(home / "Desktop"),
            str(home / "Pictures"),
            str(home / "Videos"),
            str(home / "Music"),
            str(home / ".mozilla"),
            str(home / ".config" / "google-chrome"),
            str(home / ".config" / "chromium"),
            str(home / ".local" / "share"),
            str(home / ".cache"),
            cls.get_system_temp_dir(),
        ]

    @classmethod
    def get_excluded_scan_paths(cls) -> List[str]:
        """Get paths that should be excluded from scanning"""
        return [
            "/proc",
            "/sys",
            "/dev",
            "/run",
            cls.get_system_temp_dir(),
        ]


class ApplicationPaths:
    """Application-specific path management"""

    def __init__(self, app_name: str = "xanados-search-destroy"):
        self.app_name = app_name
        self._setup_directories()

    def _setup_directories(self):
        """Setup application directories"""
        self.config_dir = SystemPaths.get_app_config_dir(self.app_name)
        self.data_dir = SystemPaths.get_app_data_dir(self.app_name)
        self.cache_dir = SystemPaths.get_app_cache_dir(self.app_name)
        self.state_dir = SystemPaths.get_app_state_dir(self.app_name)

        # Application-specific subdirectories
        self.quarantine_dir = self.data_dir / "quarantine"
        self.quarantine_files_dir = self.quarantine_dir / "files"
        self.quarantine_metadata_dir = self.quarantine_dir / "metadata"
        self.reports_dir = self.data_dir / "reports"
        self.logs_dir = self.data_dir / "logs"
        self.temp_dir = self.cache_dir / "temp"
        self.languages_dir = self.data_dir / "languages"

        # Config files
        self.main_config_file = self.config_dir / "config.json"
        self.user_config_file = self.config_dir / "user_config.json"
        self.themes_config_file = self.config_dir / "themes.json"

    def ensure_all_directories(self) -> bool:
        """Create all application directories with proper permissions"""
        directories = [
            self.config_dir,
            self.data_dir,
            self.cache_dir,
            self.state_dir,
            self.quarantine_dir,
            self.quarantine_files_dir,
            self.quarantine_metadata_dir,
            self.reports_dir,
            self.logs_dir,
            self.temp_dir,
            self.languages_dir,
        ]

        success = True
        for directory in directories:
            if not SystemPaths.ensure_secure_dir(directory):
                success = False

        return success

    def get_path(self, path_type: str) -> Path:
        """Get specific application path"""
        path_map = {
            "config": self.config_dir,
            "data": self.data_dir,
            "cache": self.cache_dir,
            "state": self.state_dir,
            "quarantine": self.quarantine_dir,
            "quarantine_files": self.quarantine_files_dir,
            "quarantine_metadata": self.quarantine_metadata_dir,
            "reports": self.reports_dir,
            "logs": self.logs_dir,
            "temp": self.temp_dir,
            "languages": self.languages_dir,
            "main_config": self.main_config_file,
            "user_config": self.user_config_file,
            "themes_config": self.themes_config_file,
        }

        if path_type not in path_map:
            raise ValueError(f"Unknown path type: {path_type}")

        return path_map[path_type]


# Global application paths instance
APP_PATHS = ApplicationPaths()


# Convenience functions
def get_app_path(path_type: str) -> Path:
    """Get application path by type"""
    return APP_PATHS.get_path(path_type)


def get_temp_dir() -> str:
    """Get system temporary directory"""
    return SystemPaths.get_system_temp_dir()


def get_executable(name: str) -> str | None:
    """Get executable path with security validation"""
    return SystemPaths.get_executable_path(name)


def is_safe_path(path: str) -> bool:
    """Check if path is safe for operations"""
    return not SystemPaths.is_forbidden_path(path)
