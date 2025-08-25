#!/usr/bin/env python3
"""
Security Hardening for RKHunter Wrapper
Implements strict command validation and privilege restrictions.
"""

import os
import re
from typing import List, Optional, Set


class SecureRKHunterValidator:
    """
    Validates RKHunter commands and arguments for security.
    Implements whitelist-based approach for all privileged operations.
    """

    def __init__(self):
        # Allowed RKHunter executable paths (strict whitelist)
        self.allowed_rkhunter_paths: Set[str] = {
            "/usr/bin/rkhunter",
            "/usr/local/bin/rkhunter",
            "/opt/rkhunter/bin/rkhunter",
        }

        # Allowed RKHunter commands (strict whitelist)
        self.allowed_commands: Set[str] = {
            "--version",
            "--check",
            "--update",
            "--propupd",
            "--versioncheck",
        }

        # Allowed RKHunter options (safe options only)
        self.allowed_options: Set[str] = {
            "--sk",  # Skip keypress
            "--nocolors",  # No colors
            "--no-mail-on-warning",  # No mail
            "--quiet",  # Quiet mode
            "--report-warnings-only",  # Report warnings only
            "--display-logfile",  # Display log
            "--cronjob",  # Cron job mode
            "--enable",  # Enable specific tests (with validation)
            "--disable",  # Disable specific tests (with validation)
            "--rwo",  # Report warnings only
            "--summary",  # Summary only
            "--append-log",  # Append to log
            "--configfile",  # Config file (with path validation)
            "--tmpdir",  # Temporary directory (with path validation)
            "--configcheck",  # Configuration validation check
        }

        # Allowed test categories for --enable/--disable
        self.allowed_test_categories: Set[str] = {
            "filesystem",
            "network",
            "system_commands",
            "rootkits",
            "malware",
            "applications",
            "ssh",
            "group_accounts",
            "system_accounts",
            "filesystem_properties",
            "startup_files",
            "group_changes",
            "passwd_changes",
            "local_host",
        }

        # Allowed config file paths
        self.allowed_config_paths: Set[str] = {
            "/etc/rkhunter.conf",
            "/usr/local/etc/rkhunter.conf",
        }

        # Allowed temporary directory paths
        self.allowed_tmp_paths: Set[str] = {
            "/var/lib/rkhunter/tmp",
            "/tmp/rkhunter",
            "/var/tmp/rkhunter",
        }

    def validate_executable_path(self, rkhunter_path: str) -> bool:
        """
        Validate that the RKHunter executable path is in the allowlist.

        Args:
            rkhunter_path: Path to RKHunter executable

        Returns:
            bool: True if path is allowed, False otherwise
        """
        # Resolve symbolic links and normalize path
        try:
            resolved_path = os.path.realpath(rkhunter_path)
            return resolved_path in self.allowed_rkhunter_paths
        except (OSError, ValueError):
            return False

    def validate_command_args(self, cmd_args: List[str]) -> tuple[bool, str]:
        """
        Validate RKHunter command arguments against security policy.

        Args:
            cmd_args: List of command arguments

        Returns:
            tuple: (is_valid, error_message)
        """
        if not cmd_args:
            return False, "Empty command arguments"

        # First argument must be RKHunter executable
        rkhunter_path = cmd_args[0]
        if not self.validate_executable_path(rkhunter_path):
            return False, f"Unauthorized RKHunter path: {rkhunter_path}"

        # Validate all arguments
        i = 1
        while i < len(cmd_args):
            arg = cmd_args[i]

            # Check for command injection attempts
            if self._contains_injection_patterns(arg):
                return False, f"Potential command injection in argument: {arg}"

            # Validate main commands
            if arg in self.allowed_commands:
                i += 1
                continue

            # Validate options
            if arg in self.allowed_options:
                # Some options require additional validation
                if arg in ["--enable", "--disable"]:
                    if i + 1 >= len(cmd_args):
                        return False, f"Option {arg} requires a test category"

                    test_category = cmd_args[i + 1]
                    if test_category not in self.allowed_test_categories:
                        return False, f"Unauthorized test category: {test_category}"
                    i += 2  # Skip the test category argument
                    continue

                elif arg == "--configfile":
                    if i + 1 >= len(cmd_args):
                        return False, f"Option {arg} requires a config file path"

                    config_path = cmd_args[i + 1]
                    if config_path not in self.allowed_config_paths:
                        return False, f"Unauthorized config file path: {config_path}"
                    i += 2  # Skip the config file argument
                    continue

                elif arg == "--tmpdir":
                    if i + 1 >= len(cmd_args):
                        return (
                            False,
                            f"Option {arg} requires a temporary directory path",
                        )

                    tmp_path = cmd_args[i + 1]
                    if tmp_path not in self.allowed_tmp_paths:
                        return (
                            False,
                            f"Unauthorized temporary directory path: {tmp_path}",
                        )
                    i += 2  # Skip the tmp directory argument
                    continue

                i += 1
                continue

            # Reject any unrecognized arguments
            return False, f"Unauthorized argument: {arg}"

        return True, "Command arguments validated successfully"

    def _contains_injection_patterns(self, arg: str) -> bool:
        """
        Check for common command injection patterns.

        Args:
            arg: Argument to check

        Returns:
            bool: True if injection patterns detected
        """
        # Dangerous characters and patterns
        dangerous_patterns = [
            r"[;&|`$()]",  # Shell metacharacters
            r"\.\./",  # Directory traversal
            r"/proc/",  # Proc filesystem access
            r"/dev/",  # Device access
            r"\\x[0-9a-fA-F]{2}",  # Hex escape sequences
            r"%[0-9a-fA-F]{2}",  # URL encoding
            r"<|>",  # Redirection operators
            r"\*|\?",  # Glob patterns
            r"^\s*$",  # Empty or whitespace only
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, arg):
                return True

        return False

    def get_safe_rkhunter_path(self) -> Optional[str]:
        """
        Get the first available safe RKHunter path.

        Returns:
            str: Safe RKHunter path, or None if none found
        """
        for path in self.allowed_rkhunter_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None


# Example usage and testing
if __name__ == "__main__":
    validator = SecureRKHunterValidator()

    # Test cases
    test_cases = [
        # Valid commands
        (["/usr/bin/rkhunter", "--version"], True, "Valid version check"),
        (
            ["/usr/bin/rkhunter", "--check", "--sk", "--nocolors"],
            True,
            "Valid scan command",
        ),
        (["/usr/bin/rkhunter", "--update"], True, "Valid update command"),
        # Invalid commands
        (["/tmp/evil_script"], False, "Unauthorized executable"),
        (
            ["/usr/bin/rkhunter", "--check", "; rm -rf /"],
            False,
            "Command injection attempt",
        ),
        (["/usr/bin/rkhunter", "--evil-option"], False, "Unauthorized option"),
        (
            ["/usr/bin/rkhunter", "--enable", "../../../../etc/passwd"],
            False,
            "Directory traversal",
        ),
        (
            ["/usr/bin/rkhunter", "--configfile", "/tmp/evil.conf"],
            False,
            "Unauthorized config path",
        ),
    ]

    print("Security Validation Test Results:")
    print("=" * 50)

    for cmd_args, expected_valid, description in test_cases:
        is_valid, message = validator.validate_command_args(cmd_args)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"{status} {description}")
        print(f"      Command: {' '.join(cmd_args)}")
        print(f"      Result: {message}")
        print()
