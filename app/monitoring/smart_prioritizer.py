#!/usr/bin/env python3
"""Smart file prioritization for real-time protection.

Assigns scan priorities based on file type risk levels.
"""

import logging
from pathlib import Path

from .scan_priority import ScanPriority


class SmartPrioritizer:
    """Risk-based file prioritization for scanning.

    Assigns priorities based on file type risk:
    - IMMEDIATE: Executables and system libraries
    - HIGH: Scripts and interpreted code
    - NORMAL: Documents and archives
    - LOW: Media files and low-risk formats
    """

    # File extension to priority mapping
    PRIORITY_WEIGHTS = {
        # Executables - highest risk (can run code directly)
        ".exe": ScanPriority.IMMEDIATE,
        ".dll": ScanPriority.IMMEDIATE,
        ".so": ScanPriority.IMMEDIATE,
        ".dylib": ScanPriority.IMMEDIATE,
        ".com": ScanPriority.IMMEDIATE,
        ".bat": ScanPriority.IMMEDIATE,
        ".cmd": ScanPriority.IMMEDIATE,
        ".scr": ScanPriority.IMMEDIATE,
        ".msi": ScanPriority.IMMEDIATE,
        ".app": ScanPriority.IMMEDIATE,
        # Scripts - high risk (interpreted code execution)
        ".sh": ScanPriority.HIGH,
        ".bash": ScanPriority.HIGH,
        ".py": ScanPriority.HIGH,
        ".pyw": ScanPriority.HIGH,
        ".js": ScanPriority.HIGH,
        ".vbs": ScanPriority.HIGH,
        ".ps1": ScanPriority.HIGH,
        ".psm1": ScanPriority.HIGH,
        ".pl": ScanPriority.HIGH,
        ".rb": ScanPriority.HIGH,
        ".php": ScanPriority.HIGH,
        ".jar": ScanPriority.HIGH,
        # Documents - medium risk (macros, exploits)
        ".pdf": ScanPriority.NORMAL,
        ".doc": ScanPriority.NORMAL,
        ".docx": ScanPriority.NORMAL,
        ".xls": ScanPriority.NORMAL,
        ".xlsx": ScanPriority.NORMAL,
        ".ppt": ScanPriority.NORMAL,
        ".pptx": ScanPriority.NORMAL,
        ".odt": ScanPriority.NORMAL,
        ".ods": ScanPriority.NORMAL,
        ".rtf": ScanPriority.NORMAL,
        # Archives - medium risk (may contain malware)
        ".zip": ScanPriority.NORMAL,
        ".tar": ScanPriority.NORMAL,
        ".gz": ScanPriority.NORMAL,
        ".bz2": ScanPriority.NORMAL,
        ".7z": ScanPriority.NORMAL,
        ".rar": ScanPriority.NORMAL,
        ".iso": ScanPriority.NORMAL,
        # Text files - low risk
        ".txt": ScanPriority.LOW,
        ".md": ScanPriority.LOW,
        ".log": ScanPriority.LOW,
        ".json": ScanPriority.LOW,
        ".xml": ScanPriority.LOW,
        ".yaml": ScanPriority.LOW,
        ".yml": ScanPriority.LOW,
        ".toml": ScanPriority.LOW,
        ".ini": ScanPriority.LOW,
        ".cfg": ScanPriority.LOW,
        # Media - low risk (rarely contain executable code)
        ".jpg": ScanPriority.LOW,
        ".jpeg": ScanPriority.LOW,
        ".png": ScanPriority.LOW,
        ".gif": ScanPriority.LOW,
        ".bmp": ScanPriority.LOW,
        ".svg": ScanPriority.LOW,
        ".mp3": ScanPriority.LOW,
        ".mp4": ScanPriority.LOW,
        ".avi": ScanPriority.LOW,
        ".mkv": ScanPriority.LOW,
        ".mov": ScanPriority.LOW,
        ".wav": ScanPriority.LOW,
        ".flac": ScanPriority.LOW,
    }

    def __init__(self):
        """Initialize smart prioritizer."""
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            "Smart prioritizer initialized with %d file type mappings",
            len(self.PRIORITY_WEIGHTS),
        )

    def get_priority(
        self, file_path: str | Path, default: ScanPriority = ScanPriority.NORMAL
    ) -> ScanPriority:
        """Determine scan priority based on file type.

        Args:
            file_path: Path to file
            default: Default priority if file type not recognized

        Returns:
            ScanPriority based on file extension
        """
        try:
            path = Path(file_path)
            ext = path.suffix.lower()

            priority = self.PRIORITY_WEIGHTS.get(ext, default)

            self.logger.debug(
                "File %s assigned priority %s (extension: %s)",
                path.name,
                priority.name,
                ext or "none",
            )

            return priority

        except Exception as e:
            self.logger.debug(
                "Error determining priority for %s: %s, using default", file_path, e
            )
            return default

    def is_high_risk(self, file_path: str | Path) -> bool:
        """Check if file is high risk (executable or script).

        Args:
            file_path: Path to file

        Returns:
            True if file is executable or script, False otherwise
        """
        priority = self.get_priority(file_path)
        return priority in (ScanPriority.IMMEDIATE, ScanPriority.HIGH)

    def is_low_risk(self, file_path: str | Path) -> bool:
        """Check if file is low risk (media or text).

        Args:
            file_path: Path to file

        Returns:
            True if file is media or text, False otherwise
        """
        priority = self.get_priority(file_path)
        return priority == ScanPriority.LOW

    def add_custom_mapping(self, extension: str, priority: ScanPriority):
        """Add custom file extension to priority mapping.

        Args:
            extension: File extension (e.g., ".custom")
            priority: Priority level to assign
        """
        if not extension.startswith("."):
            extension = f".{extension}"

        extension = extension.lower()
        self.PRIORITY_WEIGHTS[extension] = priority

        self.logger.info("Added custom mapping: %s -> %s", extension, priority.name)

    def get_statistics(self) -> dict[str, int]:
        """Get statistics about priority mappings.

        Returns:
            Dictionary with count of each priority level
        """
        stats = {
            "IMMEDIATE": 0,
            "HIGH": 0,
            "NORMAL": 0,
            "LOW": 0,
        }

        for priority in self.PRIORITY_WEIGHTS.values():
            stats[priority.name] += 1

        return stats
