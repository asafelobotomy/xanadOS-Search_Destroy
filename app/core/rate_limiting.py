#!/usr/bin/env python3
"""Rate limiting module for xanadOS Search & Destroy
Prevents resource exhaustion through intelligent throttling
"""

import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

import psutil


@dataclass
class RateLimit:
    """Rate limit configuration."""

    calls: int
    period: float  # seconds
    burst: int | None = None  # burst allowance


@dataclass
class RateLimitState:
    """Current state of rate limiting."""

    calls_made: int = 0
    window_start: float = 0.0
    last_call: float = 0.0
    burst_used: int = 0


class RateLimiter:
    """Token bucket rate limiter with burst support.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self, rate_limit: RateLimit):
        self.rate_limit = rate_limit
        self.lock = threading.RLock()
        self.tokens = float(rate_limit.calls)
        self.last_update = time.time()
        self.logger = logging.getLogger(__name__)

        # Calculate token refill rate (tokens per second)
        self.refill_rate = rate_limit.calls / rate_limit.period

    def acquire(self, tokens: int = 1) -> bool:
        """Attempt to acquire tokens.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        """
        with self.lock:
            now = time.time()

            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(
                self.rate_limit.calls, self.tokens + (elapsed * self.refill_rate)
            )
            self.last_update = now

            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def wait_time(self) -> float:
        """Calculate time to wait before next token is available."""
        with self.lock:
            if self.tokens >= 1:
                return 0.0

            tokens_needed = 1 - self.tokens
            return tokens_needed / self.refill_rate


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts limits based on system load."""

    def __init__(
        self, base_limit: RateLimit, load_monitor: Callable[[], float] | None = None
    ):
        self.base_limit = base_limit
        self.load_monitor = load_monitor or self._default_load_monitor
        self.limiter = RateLimiter(base_limit)
        self.logger = logging.getLogger(__name__)

        # Adaptation parameters
        self.high_load_threshold = 0.8
        self.critical_load_threshold = 0.95
        self.adaptation_factor = 0.5

    def _default_load_monitor(self) -> float:
        """Default system load monitor using CPU percentage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return float(cpu_percent) / 100.0
        except ImportError:
            return 0.5  # Default moderate load

    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens with adaptive rate limiting."""
        current_load = self.load_monitor()

        # Adjust rate limit based on system load
        if current_load > self.critical_load_threshold:
            # Critical load: severely limit operations
            effective_limit = RateLimit(
                calls=max(1, int(self.base_limit.calls * 0.1)),
                period=self.base_limit.period * 2,
            )
        elif current_load > self.high_load_threshold:
            # High load: reduce rate limit
            effective_limit = RateLimit(
                calls=max(1, int(self.base_limit.calls * self.adaptation_factor)),
                period=self.base_limit.period * 1.5,
            )
        else:
            # Normal load: use base limit
            effective_limit = self.base_limit

        # Update limiter if needed
        if (
            effective_limit.calls != self.limiter.rate_limit.calls
            or effective_limit.period != self.limiter.rate_limit.period
        ):
            self.limiter = RateLimiter(effective_limit)
            self.logger.debug(
                f"Adapted rate limit: {effective_limit.calls} calls per {effective_limit.period}s "
                f"(load: {current_load:.2f})"
            )

        return self.limiter.acquire(tokens)


class GlobalRateLimitManager:
    """Global rate limit manager for different operation types."""

    def __init__(self) -> None:
        self.limiters: dict[str, RateLimiter] = {}
        self.adaptive_limiters: dict[str, AdaptiveRateLimiter] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Default rate limits for different operations
        self._setup_default_limits()

    def _setup_default_limits(self) -> None:
        """Setup default rate limits for common operations."""
        # Load custom rate limits from configuration if available
        try:
            from app.utils.config import load_config

            config = load_config()
            custom_limits = config.get("rate_limiting", {})
        except Exception:
            custom_limits = {}

        # User-friendly rate limits with context-aware thresholds
        default_limits = {
            # USER-INITIATED OPERATIONS (High limits to allow user freedom)
            "user_file_scan": RateLimit(
                calls=5000, period=60.0, burst=1000
            ),  # Very high limits for user-initiated file scans
            "user_directory_scan": RateLimit(
                calls=100, period=60.0, burst=50
            ),  # Allow users to scan many directories without restriction
            "quick_scan": RateLimit(
                calls=1000, period=60.0, burst=200
            ),  # User-initiated quick scans - very high limits
            "full_scan": RateLimit(
                calls=500, period=60.0, burst=100
            ),  # User-initiated full scans - high limits
            "interactive_scan": RateLimit(
                calls=10000, period=60.0, burst=2000
            ),  # Essentially unlimited for interactive use
            # BACKGROUND/AUTOMATED OPERATIONS (Moderate limits for system protection)
            "background_scan": RateLimit(
                calls=50, period=60.0, burst=10
            ),  # Background monitoring - controlled
            "scheduled_scan": RateLimit(
                calls=10, period=60.0, burst=3
            ),  # Scheduled automatic scans
            "real_time_scan": RateLimit(
                calls=2000, period=60.0, burst=500
            ),  # Real-time protection - high but controlled
            # LEGACY/FALLBACK OPERATIONS (Moderate limits)
            "file_scan": RateLimit(
                calls=1000, period=60.0, burst=200
            ),  # General file scanning - increased from 100
            "directory_scan": RateLimit(
                calls=50, period=60.0, burst=20
            ),  # General directory scanning - increased from 10
            # SYSTEM OPERATIONS (Lower limits for protection)
            "virus_db_update": RateLimit(calls=1, period=3600.0),  # 1 update per hour
            "network_request": RateLimit(
                calls=100, period=60.0, burst=20
            ),  # Network requests - increased from 50
            "quarantine_action": RateLimit(
                calls=50, period=60.0, burst=10
            ),  # Quarantine actions - increased from 20
            "system_command": RateLimit(
                calls=10, period=60.0, burst=3
            ),  # System commands - increased from 5
            # API OPERATIONS (Strict limits for security)
            "api_scan_request": RateLimit(
                calls=20, period=60.0, burst=5
            ),  # API-initiated scans need limits
            "api_file_upload": RateLimit(
                calls=10, period=60.0, burst=3
            ),  # File uploads via API
        }

        # Apply configuration overrides
        for operation, default_limit in default_limits.items():
            if operation in custom_limits:
                custom_config = custom_limits[operation]
                try:
                    # Create custom rate limit from configuration
                    custom_limit = RateLimit(
                        calls=custom_config.get("calls", default_limit.calls),
                        period=custom_config.get("period", default_limit.period),
                        burst=custom_config.get("burst", default_limit.burst),
                    )
                    self.set_rate_limit(operation, custom_limit)
                    self.logger.info(
                        f"Applied custom rate limit for {operation}: {custom_limit}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Invalid rate limit configuration for {operation}: {e}, using default"
                    )
                    self.set_rate_limit(operation, default_limit)
            else:
                self.set_rate_limit(operation, default_limit)

    def set_rate_limit(
        self, operation: str, rate_limit: RateLimit, adaptive: bool = False
    ) -> None:
        """Set rate limit for an operation type."""
        with self.lock:
            if adaptive:
                self.adaptive_limiters[operation] = AdaptiveRateLimiter(rate_limit)
            else:
                self.limiters[operation] = RateLimiter(rate_limit)

    def acquire(self, operation: str, tokens: int = 1) -> bool:
        """Acquire tokens for an operation."""
        with self.lock:
            if operation in self.adaptive_limiters:
                return self.adaptive_limiters[operation].acquire(tokens)
            elif operation in self.limiters:
                return self.limiters[operation].acquire(tokens)
            else:
                self.logger.warning(
                    f"No rate limit configured for operation: {operation}"
                )
                return True  # Allow if no limit configured

    def smart_acquire(
        self, operation: str, context: str = "auto", tokens: int = 1
    ) -> tuple[bool, str]:
        """Intelligent rate limiting with context awareness and user-friendly responses.

        Args:
            operation: Base operation type (e.g., 'scan', 'file_scan', 'directory_scan')
            context: Context of the operation ('user', 'background', 'api', 'auto')
            tokens: Number of tokens to acquire

        Returns:
            Tuple of (success, message) where message explains result
        """
        # Auto-detect context if not specified
        if context == "auto":
            context = self._detect_context()

        # Map operation and context to specific rate limit category
        rate_limit_key = self._get_smart_rate_limit_key(operation, context)

        # Try to acquire with the mapped key
        success = self.acquire(rate_limit_key, tokens)

        if success:
            return True, f"Operation '{operation}' approved (context: {context})"

        # If rate limited, provide helpful message
        wait_time = self.wait_time(rate_limit_key)

        if context == "user":
            # For user operations, be more permissive and suggest alternatives
            message = (
                f"System is busy with {operation}. "
                f"You can continue in {wait_time:.1f} seconds, or try a quick scan instead."
            )
        elif context == "background":
            message = f"Background {operation} deferred for {wait_time:.1f} seconds to prioritize user operations."
        else:
            message = f"Rate limit reached for {operation}. Please wait {wait_time:.1f} seconds."

        return False, message

    def _detect_context(self) -> str:
        """Automatically detect the context of the current operation."""
        import threading

        thread_name = threading.current_thread().name.lower()

        # Detect GUI/user operations
        if any(
            keyword in thread_name
            for keyword in ["gui", "main", "qt", "user", "interactive"]
        ):
            return "user"
        # Detect background operations
        elif any(
            keyword in thread_name
            for keyword in ["background", "scheduler", "monitor", "auto"]
        ):
            return "background"
        # Detect API operations
        elif any(keyword in thread_name for keyword in ["api", "http", "rest", "web"]):
            return "api"
        else:
            # Default to user context for unknown threads (be permissive)
            return "user"

    def _get_smart_rate_limit_key(self, operation: str, context: str) -> str:
        """Map operation and context to appropriate rate limit key."""

        # Context-aware mapping
        if context == "user":
            # User operations get high-limit categories
            operation_map = {
                "file_scan": "user_file_scan",
                "directory_scan": "user_directory_scan",
                "scan": "interactive_scan",
                "quick_scan": "quick_scan",
                "full_scan": "full_scan",
            }
        elif context == "background":
            # Background operations get controlled limits
            operation_map = {
                "file_scan": "background_scan",
                "directory_scan": "scheduled_scan",
                "scan": "background_scan",
                "quick_scan": "scheduled_scan",
                "full_scan": "scheduled_scan",
            }
        elif context == "api":
            # API operations get security-focused limits
            operation_map = {
                "file_scan": "api_scan_request",
                "directory_scan": "api_scan_request",
                "scan": "api_scan_request",
                "upload": "api_file_upload",
            }
        else:
            operation_map = {}

        # Return mapped operation or fall back to original
        return operation_map.get(operation, operation)

    def bypass_for_user_operation(
        self, operation: str, user_confirmed: bool = False
    ) -> bool:
        """Allow users to bypass rate limiting for important operations.

        Args:
            operation: The operation that needs to bypass rate limiting
            user_confirmed: Whether the user has confirmed they want to proceed despite system load

        Returns:
            True if bypass is allowed, False otherwise
        """
        # Users can always bypass rate limiting if they really want to
        if user_confirmed:
            self.logger.info(f"User confirmed bypass of rate limiting for {operation}")
            return True

        # Automatic bypass for user operations under normal system conditions
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent

            # Allow bypass if system isn't under severe stress
            if cpu_percent < 80 and memory_percent < 80:
                self.logger.debug(
                    f"Automatic bypass allowed for {operation} (CPU: {cpu_percent}%, RAM: {memory_percent}%)"
                )
                return True
            else:
                self.logger.warning(
                    f"System under stress, rate limiting maintained for {operation} (CPU: {cpu_percent}%, RAM: {memory_percent}%)"
                )
                return False

        except ImportError:
            # If psutil isn't available, be conservative but still allow bypass
            self.logger.debug(f"psutil not available, allowing bypass for {operation}")
            return True
        except Exception as e:
            self.logger.error(f"Error checking system load for bypass: {e}")
            return True  # Default to allowing bypass if we can't check

    def wait_time(self, operation: str) -> float:
        """Get wait time for next token availability."""
        with self.lock:
            if operation in self.limiters:
                return self.limiters[operation].wait_time()
            elif operation in self.adaptive_limiters:
                return self.adaptive_limiters[operation].limiter.wait_time()
            return 0.0

    def is_rate_limited(self, operation: str) -> bool:
        """Check if operation is currently rate limited."""
        return not self.acquire(operation, tokens=0)  # Check without consuming tokens

    def reload_configuration(self) -> None:
        """Reload rate limits from configuration file."""
        self.logger.info("Reloading rate limiting configuration...")
        with self.lock:
            self.limiters.clear()
            self.adaptive_limiters.clear()
            self._setup_default_limits()

    def get_current_limits(self) -> dict[str, dict]:
        """Get current rate limit configuration."""
        with self.lock:
            limits: dict[str, dict[str, Any]] = {}
            for operation, limiter in self.limiters.items():
                limits[operation] = {
                    "calls": limiter.rate_limit.calls,
                    "period": limiter.rate_limit.period,
                    "burst": limiter.rate_limit.burst,
                    "type": "standard",
                }
            for operation, limiter in self.adaptive_limiters.items():
                limits[operation] = {  # type: ignore[assignment]
                    "calls": limiter.base_limit.calls,
                    "period": limiter.base_limit.period,
                    "burst": limiter.base_limit.burst,
                    "type": "adaptive",
                }
            return limits

    def update_rate_limit(
        self, operation: str, calls: int, period: float, burst: int | None = None
    ) -> None:
        """Update rate limit for a specific operation."""
        new_limit = RateLimit(calls=calls, period=period, burst=burst)
        self.set_rate_limit(operation, new_limit)
        self.logger.info(f"Updated rate limit for {operation}: {new_limit}")

    def disable_rate_limiting(self, operation: str) -> None:
        """Disable rate limiting for a specific operation."""
        with self.lock:
            if operation in self.limiters:
                del self.limiters[operation]
            if operation in self.adaptive_limiters:
                del self.adaptive_limiters[operation]
            self.logger.info(f"Disabled rate limiting for {operation}")

    def get_operation_status(self, operation: str) -> dict:
        """Get detailed status for a specific operation."""
        with self.lock:
            if operation in self.limiters:
                limiter = self.limiters[operation]
                return {
                    "operation": operation,
                    "enabled": True,
                    "type": "standard",
                    "current_tokens": limiter.tokens,
                    "max_tokens": limiter.rate_limit.calls,
                    "refill_rate": limiter.refill_rate,
                    "is_limited": limiter.tokens < 1,
                    "wait_time": limiter.wait_time(),
                }
            elif operation in self.adaptive_limiters:
                limiter = self.adaptive_limiters[operation].limiter
                return {
                    "operation": operation,
                    "enabled": True,
                    "type": "adaptive",
                    "current_tokens": limiter.tokens,
                    "max_tokens": limiter.rate_limit.calls,
                    "refill_rate": limiter.refill_rate,
                    "is_limited": limiter.tokens < 1,
                    "wait_time": limiter.wait_time(),
                }
            else:
                return {
                    "operation": operation,
                    "enabled": False,
                    "type": "none",
                    "message": "No rate limiting configured",
                }


# Global rate limit manager instance
rate_limit_manager = GlobalRateLimitManager()


def rate_limit(
    operation: str, tokens: int = 1, wait_on_limit: bool = False
) -> Callable:
    """Decorator for rate limiting function calls.

    Args:
        operation: Operation type for rate limiting
        tokens: Number of tokens to consume
        wait_on_limit: Whether to wait when rate limited (default: raise exception)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not rate_limit_manager.acquire(operation, tokens):
                if wait_on_limit:
                    wait_time = rate_limit_manager.wait_time(operation)
                    if wait_time > 0:
                        time.sleep(wait_time)
                        # Try again after waiting
                        if not rate_limit_manager.acquire(operation, tokens):
                            raise RuntimeError(
                                f"Rate limit exceeded for operation: {operation}"
                            )
                else:
                    raise RuntimeError(
                        f"Rate limit exceeded for operation: {operation}"
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator


class RequestTracker:
    """Track request patterns and detect potential abuse."""

    def __init__(self, window_size: int = 1000) -> None:
        self.window_size = window_size
        self.requests: deque[dict[str, Any]] = deque(maxlen=window_size)
        self.request_counts: defaultdict[str, int] = defaultdict(int)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

    def record_request(self, client_id: str, operation: str) -> None:
        """Record a request for tracking."""
        with self.lock:
            now = time.time()
            request = {"timestamp": now, "client_id": client_id, "operation": operation}

            self.requests.append(request)
            self.request_counts[f"{client_id}:{operation}"] += 1

            # Clean old requests (older than 1 hour)
            cutoff_time = now - 3600
            while self.requests and self.requests[0]["timestamp"] < cutoff_time:
                old_request = self.requests.popleft()
                key = f"{old_request['client_id']}:{old_request['operation']}"
                self.request_counts[key] = max(0, self.request_counts[key] - 1)

    def detect_abuse(
        self, client_id: str, operation: str, threshold: int = 100
    ) -> bool:
        """Detect if client is making too many requests."""
        key = f"{client_id}:{operation}"
        return self.request_counts[key] > threshold

    def get_request_stats(self) -> dict[str, Any]:
        """Get request statistics."""
        with self.lock:
            now = time.time()
            recent_requests = [
                r for r in self.requests if now - r["timestamp"] < 300
            ]  # Last 5 minutes

            return {
                "total_requests": len(self.requests),
                "recent_requests": len(recent_requests),
                "unique_clients": len(set(r["client_id"] for r in recent_requests)),
                "top_operations": self._get_top_operations(recent_requests),
            }

    def _get_top_operations(self, requests: list[dict[str, Any]]) -> dict[str, int]:
        """Get top operations from request list."""
        operation_counts: defaultdict[str, int] = defaultdict(int)
        for request in requests:
            operation_counts[request["operation"]] += 1

        return dict(
            sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )


# Global request tracker
request_tracker = RequestTracker()


def configure_rate_limits(config: dict[str, Any]) -> None:
    """Configure rate limits from configuration dictionary."""
    for operation, limit_config in config.get("rate_limits", {}).items():
        rate_limit = RateLimit(
            calls=limit_config["calls"],
            period=limit_config["period"],
            burst=limit_config.get("burst"),
        )
        adaptive = limit_config.get("adaptive", False)
        rate_limit_manager.set_rate_limit(operation, rate_limit, adaptive)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Test basic rate limiting
    @rate_limit("test_operation", tokens=1)
    def test_function() -> str:
        print("Function called")
        return "success"

    # Configure test rate limit
    rate_limit_manager.set_rate_limit("test_operation", RateLimit(calls=3, period=10.0))

    # Test function calls
    for i in range(5):
        try:
            result = test_function()
            print(f"Call {i + 1}: {result}")
        except RuntimeError as e:
            print(f"Call {i + 1}: Rate limited - {e}")
        time.sleep(1)
