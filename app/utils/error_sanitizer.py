"""
Error message sanitization for security.

Prevents information disclosure through error messages by sanitizing
sensitive data before displaying to users or logging.

Author: xanadOS Security Team
Date: 2025-12-17
Phase: 2 (HIGH severity - CWE-209 mitigation)
"""

import re
from pathlib import Path
from typing import Any


# Patterns to redact from error messages
SENSITIVE_PATTERNS = [
    # File paths
    (r"/home/[^/\s]+", "/home/[REDACTED]"),
    (r"/root", "/[REDACTED]"),
    (r"C:\\\\Users\\\\[^\\\\]+", "C:\\\\Users\\\\[REDACTED]"),
    # IP addresses
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP_REDACTED]"),
    (r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", "[IPv6_REDACTED]"),
    # Email addresses
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
    # API keys and tokens (common patterns)
    (
        r'[Aa]pi[_-]?[Kk]ey["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})',
        "api_key=[API_KEY_REDACTED]",
    ),
    (
        r'[Tt]oken["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-\.]{20,})',
        "token=[TOKEN_REDACTED]",
    ),
    # Database connection strings
    (r"(postgresql|mysql|mongodb)://[^@]+@", r"\1://[USER_REDACTED]@"),
    # SSH keys
    (
        r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----.*?-----END (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
        "[SSH_KEY_REDACTED]",
    ),
    # Password patterns
    (r'[Pp]assword["\']?\s*[:=]\s*["\']?([^\s"\']+)', "password=[PASSWORD_REDACTED]"),
]


class ErrorSanitizer:
    """
    Sanitizes error messages to prevent information disclosure.

    Removes sensitive data like file paths, IPs, credentials, etc.

    Example:
        >>> sanitizer = ErrorSanitizer()
        >>> error = "Failed to connect to 192.168.1.100"
        >>> sanitizer.sanitize(error)
        'Failed to connect to [IP_REDACTED]'
    """

    def __init__(self, custom_patterns: list[tuple[str, str]] | None = None):
        """
        Initialize error sanitizer.

        Args:
            custom_patterns: Additional (pattern, replacement) tuples to apply
        """
        self.patterns = SENSITIVE_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)

    def sanitize(self, message: str) -> str:
        """
        Sanitize an error message.

        Args:
            message: Original error message

        Returns:
            Sanitized message with sensitive data redacted
        """
        if not message:
            return message

        sanitized = message

        # Apply all sanitization patterns
        for pattern, replacement in self.patterns:
            sanitized = re.sub(
                pattern, replacement, sanitized, flags=re.IGNORECASE | re.DOTALL
            )

        return sanitized

    def sanitize_exception(self, exc: Exception, include_type: bool = True) -> str:
        """
        Sanitize an exception for user display.

        Args:
            exc: Exception to sanitize
            include_type: Include exception type in output

        Returns:
            Sanitized error message
        """
        message = str(exc)
        sanitized = self.sanitize(message)

        if include_type:
            return f"{type(exc).__name__}: {sanitized}"
        return sanitized

    def sanitize_traceback(self, traceback: str) -> str:
        """
        Sanitize a full traceback.

        Args:
            traceback: Full traceback string

        Returns:
            Sanitized traceback
        """
        return self.sanitize(traceback)

    def get_safe_error_message(
        self,
        exc: Exception,
        user_facing: bool = True,
        generic_message: str = "An error occurred during operation",
    ) -> str:
        """
        Get a safe error message for user display.

        Args:
            exc: Exception that occurred
            user_facing: If True, returns generic message. If False, returns sanitized details.
            generic_message: Generic message to return for user-facing errors

        Returns:
            Safe error message
        """
        if user_facing:
            # For user-facing errors, return generic message with error type
            return f"{generic_message}. Error type: {type(exc).__name__}"
        else:
            # For internal/debug use, return sanitized details
            return self.sanitize_exception(exc)


# Global sanitizer instance
_sanitizer = ErrorSanitizer()


def sanitize_error(message: str) -> str:
    """
    Convenience function to sanitize error messages.

    Args:
        message: Error message to sanitize

    Returns:
        Sanitized message
    """
    return _sanitizer.sanitize(message)


def sanitize_exception(exc: Exception, user_facing: bool = False) -> str:
    """
    Convenience function to sanitize exceptions.

    Args:
        exc: Exception to sanitize
        user_facing: If True, returns generic message

    Returns:
        Sanitized exception message
    """
    if user_facing:
        return _sanitizer.get_safe_error_message(exc, user_facing=True)
    return _sanitizer.sanitize_exception(exc)


# Example usage
if __name__ == "__main__":
    sanitizer = ErrorSanitizer()

    # Test cases
    test_cases = [
        "Failed to read file: /home/user/sensitive/data.txt",
        "Connection to 192.168.1.100:3306 failed",
        "Auth failed with api_key='sk-1234567890abcdef1234567890'",
        "User john.doe@example.com not authorized",
        "Password='MySecretPass123' is incorrect",
        "Database connection: postgresql://admin:password123@localhost/db",
    ]

    print("Error Message Sanitization Examples:\\n")
    for msg in test_cases:
        sanitized = sanitizer.sanitize(msg)
        print(f"Original:  {msg}")
        print(f"Sanitized: {sanitized}")
        print()
