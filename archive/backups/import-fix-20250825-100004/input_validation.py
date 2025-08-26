#!/usr/bin/env python3
"""
Security input validation module for S&D - Search & Destroy
Provides comprehensive input validation and security checks
"""
import hashlib
import logging
import os
import stat
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Maximum file sizes (in bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_ARCHIVE_SIZE = 500 * 1024 * 1024  # 500MB
MAX_SCAN_DEPTH = 10  # Maximum directory depth
MAX_FILES_PER_SCAN = 10000  # Maximum files in single scan

# Forbidden paths that should never be scanned
FORBIDDEN_PATHS = [
    "/proc",
    "/sys",
    "/dev",
    "/run",
    "/tmp/systemd-private-*",  # nosec B108 - path validation list, not temp file creation
    "/etc/shadow",
    "/etc/passwd",
    "/etc/sudoers",
    "/boot",
    "/lost+found",
    "/var/run",
    "/var/lock",
]

# Dangerous file extensions that need special handling
DANGEROUS_EXTENSIONS = {
    ".exe",
    ".scr",
    ".bat",
    ".cmd",
    ".com",
    ".pif",
    ".vbs",
    ".js",
    ".jar",
    ".app",
    ".deb",
    ".rpm",
    ".pkg",
    ".dmg",
    ".iso",
}

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Raised when security validation fails."""

    pass


class PathValidator:
    """Validates file and directory paths for security."""

    def __init__(self):
        self.forbidden_paths = [Path(p) for p in FORBIDDEN_PATHS]

    def validate_scan_path(self, path: str) -> Tuple[bool, str]:
        """
        Validate a path for scanning.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Convert to Path object and resolve
            path_obj = Path(path).resolve()

            # Check if path exists
            if not path_obj.exists():
                return False, f"Path does not exist: {path}"

            # Check if we have read permission
            if not os.access(path_obj, os.R_OK):
                return False, f"No read permission for path: {path}"

            # Check against forbidden paths
            for forbidden in self.forbidden_paths:
                try:
                    if path_obj.is_relative_to(forbidden):
                        return False, f"Scanning forbidden system path: {forbidden}"
                except ValueError:
                    # is_relative_to can raise ValueError in some cases
                    continue

            # Check for suspicious symbolic links
            if path_obj.is_symlink():
                target = path_obj.readlink()
                if target.is_absolute() and str(target).startswith(
                    ("/proc", "/sys", "/dev")
                ):
                    return False, f"Suspicious symlink to system path: {target}"

            # Additional checks for directories
            if path_obj.is_dir():
                # Check directory permissions
                if not os.access(path_obj, os.X_OK):
                    return False, f"No execute permission for directory: {path}"

                # Estimate directory size (basic check)
                try:
                    file_count = sum(
                        1 for _ in path_obj.rglob("*") if _.is_file())
                    if file_count > MAX_FILES_PER_SCAN:
                        return (
                            False,
                            f"Directory contains too many files: {file_count} > {MAX_FILES_PER_SCAN}",
                        )
                except (OSError, PermissionError):
                    # If we can't count files, it might be too large or
                    # inaccessible
                    logger.warning(
                        f"Could not count files in directory: {path}")

            return True, ""

        except (OSError, ValueError, PermissionError) as e:
            return False, f"Path validation error: {e}"

    def validate_file_for_scan(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate an individual file for scanning.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_obj = Path(file_path).resolve()

            # Check if file exists
            if not file_obj.exists():
                return False, f"File does not exist: {file_path}"

            # Check if it's actually a file
            if not file_obj.is_file():
                return False, f"Not a regular file: {file_path}"

            # Check file permissions
            if not os.access(file_obj, os.R_OK):
                return False, f"No read permission for file: {file_path}"

            # Check file size
            try:
                file_size = file_obj.stat().st_size
                if file_size > MAX_FILE_SIZE:
                    return False, f"File too large: {file_size} bytes > {MAX_FILE_SIZE}"

                # Special handling for archives
                if self._is_archive(file_obj):
                    if file_size > MAX_ARCHIVE_SIZE:
                        return (
                            False, f"Archive too large: {file_size} bytes > {MAX_ARCHIVE_SIZE}", )

            except OSError as e:
                return False, f"Could not check file size: {e}"

            # Check for suspicious file characteristics
            if self._is_suspicious_file(file_obj):
                logger.warning(
                    f"Suspicious file characteristics detected: {file_path}")
                # Don't block, but log for review

            return True, ""

        except (OSError, ValueError) as e:
            return False, f"File validation error: {e}"

    def _is_archive(self, file_path: Path) -> bool:
        """Check if file is an archive format."""
        archive_extensions = {
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".bz2",
            ".xz"}
        return file_path.suffix.lower() in archive_extensions

    def _is_suspicious_file(self, file_path: Path) -> bool:
        """Check for suspicious file characteristics."""
        # Check extension
        if file_path.suffix.lower() in DANGEROUS_EXTENSIONS:
            return True

        # Check for executable bit on non-executable extensions
        try:
            file_stat = file_path.stat()
            if file_stat.st_mode & stat.S_IXUSR:
                if file_path.suffix.lower() not in {
                        ".sh", ".py", ".pl", ".rb"}:
                    return True
        except OSError:
            pass

        # Check for suspicious file names
        suspicious_names = {
            "autorun.inf",
            "desktop.ini",
            "thumbs.db",
            ".htaccess",
            "index.php",
            "config.php",
            "wp-config.php",
        }
        if file_path.name.lower() in suspicious_names:
            return True

        return False


class InputSanitizer:
    """Sanitizes user inputs for security."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path separators and dangerous characters
        dangerous_chars = [
            "/",
            "\\",
            "..",
            "<",
            ">",
            ":",
            '"',
            "|",
            "?",
            "*",
            ";",  # Command separator
            "`",  # Command substitution
            "$",  # Variable expansion
            "&",  # Background process
            "(",  # Subshell
            ")",  # Subshell
            "\n", # Newline
            "\r", # Carriage return
            "\t", # Tab
            "\x00"]  # Null byte

        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "_")

        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[: 255 - len(ext)] + ext

        # Ensure not empty
        if not sanitized or sanitized.isspace():
            sanitized = "unnamed_file"

        return sanitized

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize path for safe operations."""
        # Normalize path
        try:
            sanitized = os.path.normpath(path)

            # Remove any remaining .. components
            parts = sanitized.split(os.sep)
            safe_parts = [part for part in parts if part != ".."]

            return os.sep.join(safe_parts)
        except (ValueError, TypeError):
            raise SecurityValidationError(f"Invalid path format: {path}")


class FileSizeMonitor:
    """Monitors file processing to prevent resource exhaustion."""

    def __init__(self):
        self.processed_size = 0
        self.processed_files = 0
        self.max_total_size = 1024 * 1024 * 1024  # 1GB per scan session

    def check_can_process_file(self, file_path: str) -> bool:
        """Check if file can be processed within limits."""
        try:
            file_size = Path(file_path).stat().st_size

            # Check individual file size
            if file_size > MAX_FILE_SIZE:
                logger.warning(
                    f"File too large to process: {file_path} ({file_size} bytes)")
                return False

            # Check total processed size
            if self.processed_size + file_size > self.max_total_size:
                logger.warning(
                    f"Total scan size limit reached: {
                        self.processed_size + file_size}")
                return False

            # Check file count
            if self.processed_files >= MAX_FILES_PER_SCAN:
                logger.warning(
                    f"Maximum file count reached: {
                        self.processed_files}")
                return False

            return True

        except OSError:
            return False

    def record_processed_file(self, file_path: str):
        """Record that a file has been processed."""
        try:
            file_size = Path(file_path).stat().st_size
            self.processed_size += file_size
            self.processed_files += 1
        except OSError:
            pass

    def reset(self):
        """Reset monitoring counters."""
        self.processed_size = 0
        self.processed_files = 0


def validate_scan_request(
        scan_path: str,
        max_depth: Optional[int] = None,
        additional_options: Optional[Dict[str, str]] = None) -> dict:
    """
    Comprehensive validation of scan requests.

    Args:
        scan_path: Path to scan
        max_depth: Maximum directory depth
        additional_options: Additional scan options to validate

    Returns:
        Dict with validation results
    """
    validator = PathValidator()
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "estimated_files": 0,
        "estimated_size": 0,
    }

    # Basic path validation
    is_valid, error_msg = validator.validate_scan_path(scan_path)
    if not is_valid:
        result["errors"].append(error_msg)
        return result

    # Depth validation
    if max_depth is not None and max_depth > MAX_SCAN_DEPTH:
        result["errors"].append(
            f"Scan depth too deep: {max_depth} > {MAX_SCAN_DEPTH}")
        return result

    # Validate additional options for security
    if additional_options:
        for key, value in additional_options.items():
            # Check for injection patterns in option values
            if not _validate_option_security(key, value):
                result["errors"].append(f"Potentially unsafe option: {key}")
                return result

    # Estimate scan size and complexity
    try:
        path_obj = Path(scan_path)
        if path_obj.is_file():
            result["estimated_files"] = 1
            result["estimated_size"] = path_obj.stat().st_size
        elif path_obj.is_dir():
            files = list(path_obj.rglob("*"))
            result["estimated_files"] = len([f for f in files if f.is_file()])
            result["estimated_size"] = sum(
                f.stat().st_size for f in files if f.is_file()
            )

            # Add warnings for large scans
            if result["estimated_files"] > 1000:
                result["warnings"].append(
                    f"Large scan: {result['estimated_files']} files"
                )
            if result["estimated_size"] > 100 * 1024 * 1024:  # 100MB
                result["warnings"].append(
                    f"Large data size: {result['estimated_size']} bytes"
                )

    except (OSError, PermissionError) as e:
        result["warnings"].append(f"Could not estimate scan size: {e}")

    result["valid"] = len(result["errors"]) == 0
    return result


def _validate_option_security(key: str, value: str) -> bool:
    """
    Validate option key-value pairs for security issues.

    Args:
        key: Option key
        value: Option value

    Returns:
        True if safe, False if potentially dangerous
    """
    # Check for dangerous characters in keys
    if not key.replace('_', '').replace('-', '').isalnum():
        return False

    # Check for injection patterns in values
    dangerous_patterns = [';', '&&', '||', '`', '$', '|', '\n', '\r', '../']
    for pattern in dangerous_patterns:
        if pattern in value:
            return False

    return True
