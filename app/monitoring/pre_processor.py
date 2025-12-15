#!/usr/bin/env python3
"""Pre-processor for scan requests.

Fast pre-filtering before expensive ClamAV scans to improve throughput.
"""

import logging
import os
from pathlib import Path
from typing import Any

from .scan_cache import ScanResultCache


class PreProcessor:
    """Fast pre-processing before expensive ClamAV scans.

    Performs quick checks to determine if a file needs scanning:
    - File extension filtering (safe extensions skip scan)
    - Scan cache lookup (recently scanned files)
    - File size limits (too large files)
    - Duplicate detection (already being scanned)
    """

    # Extensions considered safe (very low risk)
    SAFE_EXTENSIONS = {
        ".txt",
        ".md",
        ".log",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".css",
        ".html",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".ico",
        ".mp3",
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wav",
        ".flac",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".otf",
    }

    def __init__(
        self,
        scan_cache: ScanResultCache | None = None,
        max_file_size: int = 100 * 1024 * 1024,  # 100 MB
        active_scans: set[str] | None = None,
    ):
        """Initialize pre-processor.

        Args:
            scan_cache: Scan result cache instance
            max_file_size: Maximum file size to scan in bytes
            active_scans: Set of files currently being scanned
        """
        self.logger = logging.getLogger(__name__)
        self.scan_cache = scan_cache
        self.max_file_size = max_file_size
        self.active_scans = active_scans or set()

        # Statistics
        self.checks_performed = 0
        self.scans_skipped = 0
        self.skip_reasons: dict[str, int] = {
            "safe_extension": 0,
            "cached_clean": 0,
            "too_large": 0,
            "duplicate": 0,
            "file_missing": 0,
        }

        self.logger.info(
            "Pre-processor initialized: max_size=%d MB, safe_extensions=%d",
            max_file_size / (1024 * 1024),
            len(self.SAFE_EXTENSIONS),
        )

    def should_scan(self, file_path: str | Path) -> tuple[bool, str]:
        """Quick checks - return (should_scan, reason).

        Args:
            file_path: Path to file to check

        Returns:
            Tuple of (should_scan: bool, reason: str)
            - True with "scan_required" if file needs scanning
            - False with skip reason if scan can be skipped
        """
        self.checks_performed += 1

        try:
            file_path = Path(file_path)

            # Check 1: File exists (instant)
            if not file_path.exists():
                self.scans_skipped += 1
                self.skip_reasons["file_missing"] += 1
                return False, "file_missing"

            # Check 2: File extension (microseconds)
            if self._is_safe_extension(file_path):
                self.scans_skipped += 1
                self.skip_reasons["safe_extension"] += 1
                self.logger.debug("Skipping safe extension: %s", file_path)
                return False, "safe_extension"

            # Check 3: Already scanning (instant)
            if str(file_path) in self.active_scans:
                self.scans_skipped += 1
                self.skip_reasons["duplicate"] += 1
                self.logger.debug("Already scanning: %s", file_path)
                return False, "duplicate"

            # Check 4: File size (instant)
            try:
                file_size = file_path.stat().st_size
                if file_size > self.max_file_size:
                    self.scans_skipped += 1
                    self.skip_reasons["too_large"] += 1
                    self.logger.debug(
                        "File too large: %s (%d MB)",
                        file_path,
                        file_size / (1024 * 1024),
                    )
                    return False, "too_large"
            except OSError:
                # File might have been deleted
                self.scans_skipped += 1
                self.skip_reasons["file_missing"] += 1
                return False, "file_missing"

            # Check 5: Scan cache (milliseconds)
            if self.scan_cache:
                cached_result = self.scan_cache.get_cached_result(file_path)
                if cached_result and cached_result.scan_result == "clean":
                    self.scans_skipped += 1
                    self.skip_reasons["cached_clean"] += 1
                    self.logger.debug("Cached clean result: %s", file_path)
                    return False, "cached_clean"

            # All checks passed - needs scanning
            return True, "scan_required"

        except Exception as e:
            self.logger.error("Error in pre-processor check for %s: %s", file_path, e)
            # On error, err on the side of caution and scan
            return True, "scan_required"

    def _is_safe_extension(self, file_path: Path) -> bool:
        """Check if file has a safe extension.

        Args:
            file_path: Path to file

        Returns:
            True if extension is considered safe
        """
        ext = file_path.suffix.lower()
        return ext in self.SAFE_EXTENSIONS

    def add_safe_extension(self, extension: str):
        """Add a custom safe extension.

        Args:
            extension: File extension (e.g., ".custom")
        """
        if not extension.startswith("."):
            extension = f".{extension}"

        extension = extension.lower()
        self.SAFE_EXTENSIONS.add(extension)
        self.logger.info("Added safe extension: %s", extension)

    def remove_safe_extension(self, extension: str) -> bool:
        """Remove an extension from safe list.

        Args:
            extension: File extension to remove

        Returns:
            True if removed, False if not found
        """
        if not extension.startswith("."):
            extension = f".{extension}"

        extension = extension.lower()
        if extension in self.SAFE_EXTENSIONS:
            self.SAFE_EXTENSIONS.remove(extension)
            self.logger.info("Removed safe extension: %s", extension)
            return True

        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get pre-processor statistics.

        Returns:
            Dictionary with pre-processor statistics
        """
        skip_rate = (
            (self.scans_skipped / self.checks_performed * 100)
            if self.checks_performed > 0
            else 0.0
        )

        return {
            "checks_performed": self.checks_performed,
            "scans_skipped": self.scans_skipped,
            "skip_rate_percent": round(skip_rate, 2),
            "skip_reasons": self.skip_reasons.copy(),
            "safe_extensions": len(self.SAFE_EXTENSIONS),
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.checks_performed = 0
        self.scans_skipped = 0
        self.skip_reasons = {
            "safe_extension": 0,
            "cached_clean": 0,
            "too_large": 0,
            "duplicate": 0,
            "file_missing": 0,
        }
        self.logger.info("Pre-processor statistics reset")
