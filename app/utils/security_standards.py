#!/usr/bin/env python3
"""
Security Standards Library - Centralized security definitions and utilities
===========================================================================
This library provides standardized security definitions for:
- Allowed binaries and commands
- Security validation patterns
- File type classifications
- Risk levels and threat categories
- Security policy enforcement
"""

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import List


class SecurityLevel(Enum):
    """Security risk levels"""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatCategory(Enum):
    """Types of security threats"""

    MALWARE = "malware"
    ROOTKIT = "rootkit"
    TROJAN = "trojan"
    VIRUS = "virus"
    WORM = "worm"
    SPYWARE = "spyware"
    ADWARE = "adware"
    POTENTIALLY_UNWANTED = "pup"
    SUSPICIOUS_BEHAVIOR = "suspicious"
    POLICY_VIOLATION = "policy"


class FileRiskLevel(Enum):
    """File risk classification"""

    SAFE = "safe"
    LOW_RISK = "low_risk"
    MODERATE_RISK = "moderate_risk"
    HIGH_RISK = "high_risk"
    DANGEROUS = "dangerous"


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_scan_depth: int = 10
    max_files_per_scan: int = 10000
    timeout_seconds: int = 300
    allow_archives: bool = True
    allow_executables: bool = True
    quarantine_threats: bool = True
    real_time_protection: bool = False


class SecurityStandards:
    """Centralized security standards and validation"""

    # Allowed system binaries for subprocess execution
    ALLOWED_BINARIES = {
        # Antivirus engines
        "clamscan",
        "freshclam",
        "clamd",
        "clamdscan",
        # Rootkit scanners
        "rkhunter",
        "chkrootkit",
        "lynis",
        # System utilities
        "systemctl",
        "journalctl",
        "ps",
        "top",
        "kill",
        "killall",
        "lsof",
        "netstat",
        "ss",
        "who",
        "w",
        "last",
        "lastlog",
        "uname",
        "uptime",
        "df",
        "du",
        "free",
        "mount",
        "umount",
        # Network security
        "ufw",
        "firewall-cmd",
        "iptables",
        "ip6tables",
        "nft",
        "netfilter",
        "tc",
        "nmap",
        "nslookup",
        "dig",
        # Privilege escalation (use with caution)
        "sudo",
        "pkexec",
        "su",
        # Package management (for updates)
        "apt",
        "apt-get",
        "yum",
        "dnf",
        "zypper",
        "pacman",
        "snap",
        "flatpak",
        "pip",
        "pip3",
        # Archive utilities
        "tar",
        "gzip",
        "gunzip",
        "zip",
        "unzip",
        "7z",
        # File utilities
        "find",
        "locate",
        "which",
        "file",
        "stat",
        "ls",
        "cat",
        "head",
        "tail",
        "grep",
        "awk",
        "sed",
        "sort",
        "uniq",
        # Security tools
        "gpg",
        "gpg2",
        "openssl",
        "ssh-keygen",
        "pkcheck",
        "audit",
        "auditctl",
        "ausearch",
        "aureport",
        # System monitoring
        "dmesg",
        "sysctl",
        "lscpu",
        "lspci",
        "lsusb",
        "lsmod",
    }

    # Dangerous file extensions requiring special handling
    DANGEROUS_EXTENSIONS = {
        # Executables
        ".exe",
        ".com",
        ".bat",
        ".cmd",
        ".scr",
        ".pif",
        ".msi",
        ".dll",
        ".sys",
        ".drv",
        ".vxd",
        ".cpl",
        ".ocx",
        ".ax",
        ".bin",
        # Scripts
        ".sh",
        ".bash",
        ".zsh",
        ".csh",
        ".fish",
        ".ps1",
        ".vbs",
        ".js",
        ".jse",
        ".wsf",
        ".wsh",
        ".hta",
        ".jar",
        ".py",
        ".pl",
        ".rb",
        # Archives (need scanning inside)
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".cab",
        ".arj",
        ".lzh",
        ".ace",
        ".iso",
        ".dmg",
        # Documents with macros
        ".doc",
        ".docm",
        ".xls",
        ".xlsm",
        ".ppt",
        ".pptm",
        ".docx",
        ".xlsx",
        ".pptx",  # Can contain macros too
        # Other potentially dangerous
        ".lnk",
        ".url",
        ".desktop",
        ".app",
        ".deb",
        ".rpm",
    }

    # File extensions that are generally safe
    SAFE_EXTENSIONS = {
        # Images
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".webp",
        ".tiff",
        ".tif",
        ".ico",
        ".psd",
        # Audio/Video (generally safe but scan anyway)
        ".mp3",
        ".wav",
        ".flac",
        ".ogg",
        ".m4a",
        ".wma",
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        # Text files
        ".txt",
        ".md",
        ".rst",
        ".log",
        ".cfg",
        ".conf",
        ".ini",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        # Source code (safe to scan)
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".cs",
        ".go",
        ".rs",
        ".html",
        ".css",
        ".scss",
        ".less",
    }

    # Suspicious filename patterns
    SUSPICIOUS_PATTERNS = [
        # Common malware naming patterns
        re.compile(r".*\.(exe|com|scr|bat|cmd|pif)\..*", re.IGNORECASE),
        re.compile(r".*svchost.*\.exe", re.IGNORECASE),
        re.compile(r".*system32.*\.exe", re.IGNORECASE),
        re.compile(r".*temp.*\.(exe|com|scr)", re.IGNORECASE),
        re.compile(r".*\d{8,}\.exe", re.IGNORECASE),  # Random numbers
        re.compile(r".*[a-z]{8,}\.exe", re.IGNORECASE),  # Random letters
        # Double extensions
        re.compile(r".*\.(jpg|png|pdf|doc|txt)\.(exe|scr|com|bat)", re.IGNORECASE),
        # Obfuscated names
        re.compile(r".*[0O]{3,}.*\.(exe|com)", re.IGNORECASE),
        re.compile(r".*[1lI]{3,}.*\.(exe|com)", re.IGNORECASE),
    ]

    # Argument validation patterns (prevent injection)
    UNSAFE_ARG_PATTERN = re.compile(r"[;&|`$<>{}()\\]|\.\./")

    # Network security settings
    SAFE_PORTS = {80, 443, 21, 22, 25, 53, 110, 143, 993, 995}
    DANGEROUS_PORTS = {135, 139, 445, 1433, 1521, 3389, 5432}

    # File size limits by type
    FILE_SIZE_LIMITS = {
        "executable": 500 * 1024 * 1024,  # 500MB
        "archive": 1024 * 1024 * 1024,  # 1GB
        "document": 100 * 1024 * 1024,  # 100MB
        "media": 2 * 1024 * 1024 * 1024,  # 2GB
        "default": 100 * 1024 * 1024,  # 100MB
    }

    @classmethod
    def is_allowed_binary(cls, binary_name: str) -> bool:
        """Check if a binary is in the allowed list"""

        base_name = os.path.basename(binary_name)
        return base_name in cls.ALLOWED_BINARIES

    @classmethod
    def get_file_risk_level(cls, filename: str, file_size: int = 0) -> FileRiskLevel:
        """Determine risk level of a file based on extension and properties"""
        filename_lower = filename.lower()

        # Check for suspicious patterns first
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if pattern.match(filename):
                return FileRiskLevel.DANGEROUS

        # Get file extension
        ext = None
        for extension in cls.DANGEROUS_EXTENSIONS | cls.SAFE_EXTENSIONS:
            if filename_lower.endswith(extension):
                ext = extension
                break

        if not ext:
            return FileRiskLevel.MODERATE_RISK

        if ext in cls.DANGEROUS_EXTENSIONS:
            # Further classify dangerous files
            if ext in [".exe", ".com", ".scr", ".bat", ".cmd"]:
                return FileRiskLevel.DANGEROUS
            elif ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
                return FileRiskLevel.HIGH_RISK  # Archives need scanning
            else:
                return FileRiskLevel.MODERATE_RISK

        if ext in cls.SAFE_EXTENSIONS:
            # Even "safe" files can be dangerous if oversized
            if file_size > cls.FILE_SIZE_LIMITS.get("default", 100 * 1024 * 1024):
                return FileRiskLevel.MODERATE_RISK
            return FileRiskLevel.SAFE

        return FileRiskLevel.LOW_RISK

    @classmethod
    def validate_command_arguments(cls, args: List[str]) -> bool:
        """Validate command arguments for safety"""
        for arg in args:
            if cls.UNSAFE_ARG_PATTERN.search(arg):
                return False
            # Additional length check
            if len(arg) > 1024:
                return False
        return True

    @classmethod
    def get_security_policy(cls, level: SecurityLevel) -> SecurityPolicy:
        """Get security policy for given security level"""
        policies = {
            SecurityLevel.MINIMAL: SecurityPolicy(
                max_file_size=1024 * 1024 * 1024,  # 1GB
                max_scan_depth=20,
                max_files_per_scan=50000,
                timeout_seconds=600,
                allow_archives=True,
                allow_executables=True,
                quarantine_threats=False,
                real_time_protection=False,
            ),
            SecurityLevel.LOW: SecurityPolicy(
                max_file_size=500 * 1024 * 1024,  # 500MB
                max_scan_depth=15,
                max_files_per_scan=25000,
                timeout_seconds=450,
                allow_archives=True,
                allow_executables=True,
                quarantine_threats=True,
                real_time_protection=False,
            ),
            SecurityLevel.MEDIUM: SecurityPolicy(
                max_file_size=200 * 1024 * 1024,  # 200MB
                max_scan_depth=10,
                max_files_per_scan=15000,
                timeout_seconds=300,
                allow_archives=True,
                allow_executables=True,
                quarantine_threats=True,
                real_time_protection=True,
            ),
            SecurityLevel.HIGH: SecurityPolicy(
                max_file_size=100 * 1024 * 1024,  # 100MB
                max_scan_depth=8,
                max_files_per_scan=10000,
                timeout_seconds=240,
                allow_archives=True,
                allow_executables=False,  # Block executable scanning
                quarantine_threats=True,
                real_time_protection=True,
            ),
            SecurityLevel.CRITICAL: SecurityPolicy(
                max_file_size=50 * 1024 * 1024,  # 50MB
                max_scan_depth=5,
                max_files_per_scan=5000,
                timeout_seconds=180,
                allow_archives=False,  # Skip archives
                allow_executables=False,
                quarantine_threats=True,
                real_time_protection=True,
            ),
        }

        return policies.get(level, policies[SecurityLevel.MEDIUM])

    @classmethod
    def classify_threat(cls, threat_name: str) -> ThreatCategory:
        """Classify threat based on name patterns"""
        threat_lower = threat_name.lower()

        if any(pattern in threat_lower for pattern in ["rootkit", "backdoor"]):
            return ThreatCategory.ROOTKIT
        elif any(pattern in threat_lower for pattern in ["trojan", "horse"]):
            return ThreatCategory.TROJAN
        elif any(pattern in threat_lower for pattern in ["virus", "infect"]):
            return ThreatCategory.VIRUS
        elif any(pattern in threat_lower for pattern in ["worm", "network"]):
            return ThreatCategory.WORM
        elif any(pattern in threat_lower for pattern in ["spy", "keylog", "steal"]):
            return ThreatCategory.SPYWARE
        elif any(pattern in threat_lower for pattern in ["adware", "popup", "banner"]):
            return ThreatCategory.ADWARE
        elif any(
            pattern in threat_lower for pattern in ["pup", "unwanted", "suspicious"]
        ):
            return ThreatCategory.POTENTIALLY_UNWANTED
        else:
            return ThreatCategory.MALWARE

    @classmethod
    def classify_file_risk(cls, filename: str, file_size: int = 0) -> FileRiskLevel:
        """Classify file risk level - alias for get_file_risk_level"""
        return cls.get_file_risk_level(filename, file_size)


class ValidationResult:
    """Result of security validation"""

    def __init__(
        self,
        is_valid: bool,
        message: str = "",
        risk_level: SecurityLevel = SecurityLevel.LOW,
    ):
        self.is_valid = is_valid
        self.message = message
        self.risk_level = risk_level


def validate_file_safety(filename: str, file_size: int = 0) -> ValidationResult:
    """Validate file safety"""
    risk_level = SecurityStandards.get_file_risk_level(filename, file_size)

    if risk_level == FileRiskLevel.DANGEROUS:
        return ValidationResult(
            False, f"File {filename} is classified as dangerous", SecurityLevel.CRITICAL
        )
    elif risk_level == FileRiskLevel.HIGH_RISK:
        return ValidationResult(
            True, f"File {filename} requires careful scanning", SecurityLevel.HIGH
        )
    elif risk_level == FileRiskLevel.MODERATE_RISK:
        return ValidationResult(
            True, f"File {filename} has moderate risk", SecurityLevel.MEDIUM
        )
    else:
        return ValidationResult(
            True, f"File {filename} appears safe", SecurityLevel.LOW
        )


def validate_command_safety(binary: str, args: List[str]) -> ValidationResult:
    """Validate command execution safety"""
    if not SecurityStandards.is_allowed_binary(binary):
        return ValidationResult(
            False, f"Binary {binary} is not in allowed list", SecurityLevel.CRITICAL
        )

    if not SecurityStandards.validate_command_arguments(args):
        return ValidationResult(
            False, "Command arguments contain unsafe patterns", SecurityLevel.HIGH
        )

    return ValidationResult(True, f"Command {binary} appears safe", SecurityLevel.LOW)


# Create global instance for easy access
SECURITY_STANDARDS = SecurityStandards()


# Module-level convenience functions
def is_binary_allowed(binary: str) -> bool:
    """Check if a binary is in the allowed list"""
    return SecurityStandards.is_allowed_binary(binary)


def get_security_policy(level: SecurityLevel) -> SecurityPolicy:
    """Get security policy for a given level"""
    return SecurityStandards.get_security_policy(level)


def classify_file_risk(filename: str, file_size: int = 0) -> "FileRiskLevel":
    """Classify file risk level"""
    return SecurityStandards.classify_file_risk(filename, file_size)
