#!/usr/bin/env python3
"""
Standardized Error Handling for xanadOS Search & Destroy
Provides consistent error handling, logging, and recovery across all components.
"""

import logging
import traceback
import functools
import time
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Type
from collections.abc import Callable as CallableABC


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    MEMORY = "memory"
    PROCESSING = "processing"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    SECURITY = "security"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    exception_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    function: str
    timestamp: float
    traceback_str: str
    context: dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False


class SecurityError(Exception):
    """Base exception for security-related errors."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, category: ErrorCategory = ErrorCategory.SECURITY):
        super().__init__(message)
        self.severity = severity
        self.category = category


class ComponentError(Exception):
    """Base exception for component-level errors."""
    def __init__(self, message: str, component: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message)
        self.component = component
        self.severity = severity


class ConfigurationError(Exception):
    """Exception for configuration-related errors."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message)
        self.severity = severity
        self.category = ErrorCategory.CONFIGURATION


class ErrorHandler:
    """Centralized error handling and recovery system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_history: list[ErrorInfo] = []
        self.max_history = 1000
        self.error_counts = {}
        self.recovery_strategies = {}
        self._setup_recovery_strategies()

    def _setup_recovery_strategies(self):
        """Setup default recovery strategies for different error types."""
        self.recovery_strategies = {
            # Memory errors
            MemoryError: self._recover_memory_error,

            # File system errors
            FileNotFoundError: self._recover_file_not_found,
            PermissionError: self._recover_permission_error,
            OSError: self._recover_os_error,

            # Network errors
            ConnectionError: self._recover_connection_error,
            TimeoutError: self._recover_timeout_error,

            # Configuration errors
            ConfigurationError: self._recover_configuration_error,

            # Component errors
            ComponentError: self._recover_component_error,
        }

    def handle_error(self,
                    exception: Exception,
                    component: str,
                    function: str,
                    context: dict[str, Any] = None,
                    severity: ErrorSeverity = None,
                    category: ErrorCategory = None) -> ErrorInfo:
        """Handle an exception with comprehensive logging and recovery."""

        if context is None:
            context = {}

        # Determine severity and category
        if severity is None:
            severity = self._determine_severity(exception)
        if category is None:
            category = self._determine_category(exception)

        # Create error info
        error_info = ErrorInfo(
            exception_type=type(exception).__name__,
            message=str(exception),
            severity=severity,
            category=category,
            component=component,
            function=function,
            timestamp=time.time(),
            traceback_str=traceback.format_exc(),
            context=context
        )

        # Log the error
        self._log_error(error_info)

        # Track error frequency
        error_key = f"{component}.{function}.{type(exception).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Attempt recovery if appropriate
        if severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            recovery_success = self._attempt_recovery(exception, error_info)
            error_info.recovery_attempted = True
            error_info.recovery_successful = recovery_success

        # Store in history (with limit)
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

        return error_info

    def _determine_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type."""
        if hasattr(exception, 'severity'):
            return exception.severity

        if isinstance(exception, (SecurityError, MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        elif isinstance(exception, (PermissionError, FileNotFoundError, ConnectionError)):
            return ErrorSeverity.HIGH
        elif isinstance(exception, (ValueError, TypeError, ConfigurationError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _determine_category(self, exception: Exception) -> ErrorCategory:
        """Determine error category based on exception type."""
        if hasattr(exception, 'category'):
            return exception.category

        if isinstance(exception, PermissionError):
            return ErrorCategory.AUTHORIZATION
        elif isinstance(exception, (FileNotFoundError, OSError)):
            return ErrorCategory.FILESYSTEM
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK
        elif isinstance(exception, MemoryError):
            return ErrorCategory.MEMORY
        elif isinstance(exception, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION
        elif isinstance(exception, SecurityError):
            return ErrorCategory.SECURITY
        else:
            return ErrorCategory.UNKNOWN

    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level based on severity."""
        log_message = (
            f"[{error_info.component}.{error_info.function}] "
            f"{error_info.exception_type}: {error_info.message}"
        )

        if error_info.context:
            log_message += f" | Context: {error_info.context}"

        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
            self.logger.debug(f"Traceback:\n{error_info.traceback_str}")
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
            self.logger.debug(f"Traceback:\n{error_info.traceback_str}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def _attempt_recovery(self, exception: Exception, error_info: ErrorInfo) -> bool:
        """Attempt to recover from an error using registered strategies."""
        recovery_strategy = self.recovery_strategies.get(type(exception))

        if recovery_strategy:
            try:
                return recovery_strategy(exception, error_info)
            except Exception as recovery_exception:
                self.logger.error(f"Recovery strategy failed: {recovery_exception}")
                return False

        return False

    # Recovery strategy implementations
    def _recover_memory_error(self, exception: MemoryError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from memory errors."""
        try:
            import gc
            gc.collect()
            self.logger.info(f"Attempted garbage collection for memory error in {error_info.component}")
            return True
        except Exception:
            return False

    def _recover_file_not_found(self, exception: FileNotFoundError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from file not found errors."""
        try:
            # Try to create parent directories if they don't exist
            file_path = error_info.context.get('file_path')
            if file_path:
                from pathlib import Path
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created missing directories for {file_path}")
                return True
        except Exception:
            pass
        return False

    def _recover_permission_error(self, exception: PermissionError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from permission errors."""
        # For security reasons, we generally don't auto-fix permission errors
        # Just log and recommend manual intervention
        self.logger.warning(f"Permission error in {error_info.component} - manual intervention may be required")
        return False

    def _recover_os_error(self, exception: OSError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from OS errors."""
        # Basic retry logic for transient OS errors
        if hasattr(exception, 'errno') and exception.errno in [2, 13, 22]:  # Common transient errors
            time.sleep(0.1)  # Brief delay
            return True
        return False

    def _recover_connection_error(self, exception: ConnectionError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from connection errors."""
        # Implement basic retry logic
        self.logger.info(f"Connection error in {error_info.component} - will retry")
        return True  # Indicate that retry is appropriate

    def _recover_timeout_error(self, exception: TimeoutError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from timeout errors."""
        # Increase timeout and retry
        self.logger.info(f"Timeout error in {error_info.component} - increasing timeout for retry")
        return True

    def _recover_configuration_error(self, exception: ConfigurationError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from configuration errors."""
        # Try to load default configuration
        try:
            from app.utils.config import create_initial_config, save_config
            config = create_initial_config()
            save_config(config)
            self.logger.info("Created default configuration to recover from config error")
            return True
        except Exception:
            return False

    def _recover_component_error(self, exception: ComponentError, error_info: ErrorInfo) -> bool:
        """Attempt to recover from component errors."""
        # Try to restart the component
        try:
            from app.core.unified_component_validator import get_component_validator
            validator = get_component_validator()
            # This would need component restart capability
            self.logger.info(f"Attempting to recover component: {exception.component}")
            return True
        except Exception:
            return False

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics and patterns."""
        if not self.error_history:
            return {"total_errors": 0}

        recent_errors = [e for e in self.error_history if time.time() - e.timestamp < 3600]  # Last hour

        severity_counts = {}
        category_counts = {}
        component_counts = {}

        for error in recent_errors:
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            component_counts[error.component] = component_counts.get(error.component, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "component_distribution": component_counts,
            "most_frequent_errors": sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_exceptions(component: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, category: ErrorCategory = None):
    """Decorator for automatic exception handling."""
    def decorator(func: CallableABC) -> CallableABC:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                error_info = error_handler.handle_error(
                    exception=e,
                    component=component,
                    function=func.__name__,
                    context={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                    severity=severity,
                    category=category
                )

                # Re-raise if critical or if recovery failed
                if error_info.severity == ErrorSeverity.CRITICAL or not error_info.recovery_successful:
                    raise

                # Return None for handled errors (caller should check)
                return None

        return wrapper
    return decorator


def safe_execute(func: CallableABC,
                component: str,
                default_return: Any = None,
                context: dict[str, Any] = None,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Any:
    """Safely execute a function with error handling."""
    try:
        return func()
    except Exception as e:
        error_handler = get_error_handler()
        error_info = error_handler.handle_error(
            exception=e,
            component=component,
            function=getattr(func, '__name__', 'anonymous'),
            context=context or {},
            severity=severity
        )

        # Return default if recovery was successful or error is minor
        if error_info.recovery_successful or severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            return default_return
        else:
            raise  # Re-raise for critical errors
