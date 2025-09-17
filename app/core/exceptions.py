"""
Standardized Exception Handling Framework for xanadOS Search & Destroy

This module provides a comprehensive exception hierarchy and handling patterns
to ensure consistent error handling across all 83 components.

Phase 3 Priority 9 Task: std_002 - Standardize Exception Handling
"""

import logging
import traceback
import uuid
from datetime import datetime
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Error severity levels for categorizing exceptions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for organizing exception types."""

    SYSTEM = "system"
    SECURITY = "security"
    NETWORK = "network"
    FILE_IO = "file_io"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    ML_MODEL = "ml_model"
    DATABASE = "database"


class BaseXanadOSError(Exception):
    """
    Base exception class for all xanadOS Search & Destroy errors.

    Provides consistent error handling with:
    - Unique error IDs for tracking
    - Severity classification
    - Category classification
    - Structured error data
    - Automatic logging
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)

        self.error_id = str(uuid.uuid4())
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()

        # Automatically log the exception
        self._log_exception()

    def _log_exception(self) -> None:
        """Log the exception with appropriate severity level."""
        logger = logging.getLogger(f"xanados.{self.category.value}")

        log_data = {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.cause:
            log_data["cause"] = str(self.cause)
            log_data["cause_type"] = type(self.cause).__name__

        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", extra=log_data)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error("High severity error occurred", extra=log_data)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", extra=log_data)
        else:
            logger.info("Low severity error occurred", extra=log_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
            "timestamp": self.timestamp.isoformat(),
        }


# System Errors
class SystemError(BaseXanadOSError):
    """General system-level errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.SYSTEM, **kwargs)


class ConfigurationError(BaseXanadOSError):
    """Configuration and setup related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)


class PerformanceError(BaseXanadOSError):
    """Performance and resource-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.PERFORMANCE, **kwargs)


# Security Errors
class SecurityError(BaseXanadOSError):
    """Security-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        super().__init__(message, category=ErrorCategory.SECURITY, **kwargs)


class AuthenticationError(BaseXanadOSError):
    """Authentication and authorization errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        super().__init__(message, category=ErrorCategory.AUTHENTICATION, **kwargs)


class ValidationError(BaseXanadOSError):
    """Input validation and sanitization errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)


# Network Errors
class NetworkError(BaseXanadOSError):
    """Network connectivity and communication errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)


class NetworkTimeoutError(NetworkError):
    """Network operation timeout errors."""

    def __init__(self, message: str, timeout_seconds: float, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.context["timeout_seconds"] = timeout_seconds


# File I/O Errors
class FileIOError(BaseXanadOSError):
    """File input/output operation errors."""

    def __init__(
        self, message: str, file_path: str | None = None, **kwargs: Any
    ) -> None:
        super().__init__(message, category=ErrorCategory.FILE_IO, **kwargs)
        if file_path:
            self.context["file_path"] = file_path


class FilePermissionError(FileIOError):
    """File permission related errors."""

    def __init__(self, message: str, file_path: str, **kwargs: Any) -> None:
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        super().__init__(message, file_path=file_path, **kwargs)


# Database Errors
class DatabaseError(BaseXanadOSError):
    """Database operation errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.DATABASE, **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Database connection errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        super().__init__(message, **kwargs)


# Machine Learning Errors
class MLModelError(BaseXanadOSError):
    """Machine learning model related errors."""

    def __init__(
        self, message: str, model_name: str | None = None, **kwargs: Any
    ) -> None:
        super().__init__(message, category=ErrorCategory.ML_MODEL, **kwargs)
        if model_name:
            self.context["model_name"] = model_name


class MLTrainingError(MLModelError):
    """Machine learning model training errors."""

    def __init__(self, message: str, model_name: str, **kwargs: Any) -> None:
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        super().__init__(message, model_name=model_name, **kwargs)


class MLPredictionError(MLModelError):
    """Machine learning prediction errors."""

    def __init__(self, message: str, model_name: str, **kwargs: Any) -> None:
        super().__init__(message, model_name=model_name, **kwargs)


# Exception Handling Decorators and Utilities
def handle_exceptions(
    reraise: bool = True, fallback_return: Any = None, log_traceback: bool = True
):
    """
    Decorator for standardized exception handling.

    Args:
        reraise: Whether to reraise the exception after handling
        fallback_return: Value to return if exception occurs and reraise=False
        log_traceback: Whether to log the full traceback
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseXanadOSError:
                # Our custom exceptions are already logged
                if reraise:
                    raise
                return fallback_return
            except Exception as e:
                # Convert standard exceptions to our format
                logger = logging.getLogger(f"xanados.{func.__module__}")

                error_data = {
                    "function": f"{func.__module__}.{func.__name__}",
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                }

                if log_traceback:
                    error_data["traceback"] = traceback.format_exc()

                logger.error("Unhandled exception in function", extra=error_data)

                if reraise:
                    # Wrap in our exception type
                    raise SystemError(
                        f"Unhandled {type(e).__name__} in {func.__name__}: {e!s}",
                        cause=e,
                        context=error_data,
                    )
                return fallback_return

        return wrapper

    return decorator


def safe_operation(
    operation_name: str,
    error_category: ErrorCategory = ErrorCategory.SYSTEM,
    error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
):
    """
    Context manager for safe operations with standardized error handling.

    Usage:
        with safe_operation("database_connection", ErrorCategory.DATABASE, ErrorSeverity.HIGH):
            # risky operation
            pass
    """

    class SafeOperationContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type and not issubclass(exc_type, BaseXanadOSError):
                # Convert to our exception format
                raise SystemError(
                    f"Error in {operation_name}: {exc_val!s}",
                    cause=exc_val,
                    category=error_category,
                    severity=error_severity,
                )
            return False  # Don't suppress exceptions

    return SafeOperationContext()


def log_and_reraise(
    message: str, exception_class: type = SystemError, **exception_kwargs
):
    """
    Decorator to log and reraise exceptions with additional context.

    Usage:
        @log_and_reraise("Failed to process file")
        def process_file(filename):
            # operation that might fail
            pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise exception_class(
                    f"{message}: {e!s}",
                    cause=e,
                    context={
                        "function": f"{func.__module__}.{func.__name__}",
                        "args": str(args)[:200],  # Limit size
                        "kwargs": str(kwargs)[:200],
                    },
                    **exception_kwargs,
                )

        return wrapper

    return decorator


# Error Recovery Strategies
class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""

    def __init__(self, max_retries: int = 3, delay_seconds: float = 1.0):
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds

    def execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with retry logic."""
        import time

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    logging.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}): {e!s}"
                    )
                    time.sleep(
                        self.delay_seconds * (attempt + 1)
                    )  # Exponential backoff
                else:
                    break

        # All retries exhausted
        raise SystemError(
            f"Operation failed after {self.max_retries + 1} attempts",
            cause=last_exception,
            severity=ErrorSeverity.HIGH,
        )


# Global exception handler setup
def setup_global_exception_handling():
    """Setup global exception handling for the application."""
    import sys

    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """Global exception handler for unhandled exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger = logging.getLogger("xanados.global")

        error_data = {
            "exception_type": exc_type.__name__,
            "exception_message": str(exc_value),
            "traceback": "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            ),
        }

        logger.critical("Unhandled global exception", extra=error_data)

        # Convert to our exception format for consistency
        wrapped_exception = SystemError(
            f"Unhandled global {exc_type.__name__}: {exc_value!s}",
            severity=ErrorSeverity.CRITICAL,
            context=error_data,
        )

        print(
            f"CRITICAL ERROR [{wrapped_exception.error_id}]: {wrapped_exception.message}"
        )
        sys.exit(1)

    sys.excepthook = global_exception_handler


# Exception Statistics and Monitoring
class ExceptionMonitor:
    """Monitor and track exception statistics."""

    def __init__(self):
        self.exception_counts = {}
        self.severity_counts = dict.fromkeys(ErrorSeverity, 0)
        self.category_counts = dict.fromkeys(ErrorCategory, 0)

    def record_exception(self, exception: BaseXanadOSError):
        """Record exception for monitoring."""
        exc_type = type(exception).__name__
        self.exception_counts[exc_type] = self.exception_counts.get(exc_type, 0) + 1
        self.severity_counts[exception.severity] += 1
        self.category_counts[exception.category] += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get exception statistics."""
        return {
            "exception_counts": self.exception_counts,
            "severity_counts": {k.value: v for k, v in self.severity_counts.items()},
            "category_counts": {k.value: v for k, v in self.category_counts.items()},
            "total_exceptions": sum(self.exception_counts.values()),
        }


# Global exception monitor instance
exception_monitor = ExceptionMonitor()

# Store original __init__ method
_original_init = BaseXanadOSError.__init__


def _monitored_init(self, message: str = "", **kwargs):
    """Initialize exception with monitoring."""
    # Call original __init__
    _original_init(self, message, **kwargs)
    # Record the exception
    exception_monitor.record_exception(self)


# Replace __init__ with monitored version
BaseXanadOSError.__init__ = _monitored_init
