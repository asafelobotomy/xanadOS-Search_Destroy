#!/usr/bin/env python3
"""
Rate limiting module for xanadOS Search & Destroy
Prevents resource exhaustion through intelligent throttling
"""
import time
import threading
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from collections import defaultdict, deque
from functools import wraps


@dataclass
class RateLimit:
    """Rate limit configuration."""
    calls: int
    period: float  # seconds
    burst: Optional[int] = None  # burst allowance


@dataclass
class RateLimitState:
    """Current state of rate limiting."""
    calls_made: int = 0
    window_start: float = 0.0
    last_call: float = 0.0
    burst_used: int = 0


class RateLimiter:
    """
    Token bucket rate limiter with burst support.
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
        """
        Attempt to acquire tokens.

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
                self.rate_limit.calls,
                self.tokens + (elapsed * self.refill_rate)
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
    """
    Adaptive rate limiter that adjusts limits based on system load.
    """

    def __init__(self, base_limit: RateLimit, load_monitor: Optional[Callable[[], float]] = None):
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
            import psutil
            return psutil.cpu_percent(interval=0.1) / 100.0
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
                period=self.base_limit.period * 2
            )
        elif current_load > self.high_load_threshold:
            # High load: reduce rate limit
            effective_limit = RateLimit(
                calls=max(1, int(self.base_limit.calls * self.adaptation_factor)),
                period=self.base_limit.period * 1.5
            )
        else:
            # Normal load: use base limit
            effective_limit = self.base_limit

        # Update limiter if needed
        if (effective_limit.calls != self.limiter.rate_limit.calls or
            effective_limit.period != self.limiter.rate_limit.period):
            self.limiter = RateLimiter(effective_limit)
            self.logger.debug(
                f"Adapted rate limit: {effective_limit.calls} calls per {effective_limit.period}s "
                f"(load: {current_load:.2f})"
            )

        return self.limiter.acquire(tokens)


class GlobalRateLimitManager:
    """
    Global rate limit manager for different operation types.
    """

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.adaptive_limiters: Dict[str, AdaptiveRateLimiter] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Default rate limits for different operations
        self._setup_default_limits()

    def _setup_default_limits(self):
        """Setup default rate limits for common operations."""
        default_limits = {
            'file_scan': RateLimit(calls=100, period=60.0, burst=20),  # 100 scans per minute
            'directory_scan': RateLimit(calls=10, period=60.0, burst=5),  # 10 directory scans per minute
            'virus_db_update': RateLimit(calls=1, period=3600.0),  # 1 update per hour
            'network_request': RateLimit(calls=50, period=60.0, burst=10),  # 50 requests per minute
            'quarantine_action': RateLimit(calls=20, period=60.0),  # 20 quarantine actions per minute
            'system_command': RateLimit(calls=5, period=60.0),  # 5 system commands per minute
        }

        for operation, limit in default_limits.items():
            self.set_rate_limit(operation, limit)

    def set_rate_limit(self, operation: str, rate_limit: RateLimit, adaptive: bool = False):
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
                self.logger.warning(f"No rate limit configured for operation: {operation}")
                return True  # Allow if no limit configured

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


# Global rate limit manager instance
rate_limit_manager = GlobalRateLimitManager()


def rate_limit(operation: str, tokens: int = 1, wait_on_limit: bool = False):
    """
    Decorator for rate limiting function calls.

    Args:
        operation: Operation type for rate limiting
        tokens: Number of tokens to consume
        wait_on_limit: Whether to wait when rate limited (default: raise exception)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not rate_limit_manager.acquire(operation, tokens):
                if wait_on_limit:
                    wait_time = rate_limit_manager.wait_time(operation)
                    if wait_time > 0:
                        time.sleep(wait_time)
                        # Try again after waiting
                        if not rate_limit_manager.acquire(operation, tokens):
                            raise RuntimeError(f"Rate limit exceeded for operation: {operation}")
                else:
                    raise RuntimeError(f"Rate limit exceeded for operation: {operation}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


class RequestTracker:
    """
    Track request patterns and detect potential abuse.
    """

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.requests = deque(maxlen=window_size)
        self.request_counts = defaultdict(int)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

    def record_request(self, client_id: str, operation: str):
        """Record a request for tracking."""
        with self.lock:
            now = time.time()
            request = {
                'timestamp': now,
                'client_id': client_id,
                'operation': operation
            }

            self.requests.append(request)
            self.request_counts[f"{client_id}:{operation}"] += 1

            # Clean old requests (older than 1 hour)
            cutoff_time = now - 3600
            while self.requests and self.requests[0]['timestamp'] < cutoff_time:
                old_request = self.requests.popleft()
                key = f"{old_request['client_id']}:{old_request['operation']}"
                self.request_counts[key] = max(0, self.request_counts[key] - 1)

    def detect_abuse(self, client_id: str, operation: str, threshold: int = 100) -> bool:
        """Detect if client is making too many requests."""
        key = f"{client_id}:{operation}"
        return self.request_counts[key] > threshold

    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics."""
        with self.lock:
            now = time.time()
            recent_requests = [r for r in self.requests if now - r['timestamp'] < 300]  # Last 5 minutes

            return {
                'total_requests': len(self.requests),
                'recent_requests': len(recent_requests),
                'unique_clients': len(set(r['client_id'] for r in recent_requests)),
                'top_operations': self._get_top_operations(recent_requests)
            }

    def _get_top_operations(self, requests) -> Dict[str, int]:
        """Get top operations from request list."""
        operation_counts = defaultdict(int)
        for request in requests:
            operation_counts[request['operation']] += 1

        return dict(sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)[:10])


# Global request tracker
request_tracker = RequestTracker()


def configure_rate_limits(config: Dict[str, Any]):
    """Configure rate limits from configuration dictionary."""
    for operation, limit_config in config.get('rate_limits', {}).items():
        rate_limit = RateLimit(
            calls=limit_config['calls'],
            period=limit_config['period'],
            burst=limit_config.get('burst')
        )
        adaptive = limit_config.get('adaptive', False)
        rate_limit_manager.set_rate_limit(operation, rate_limit, adaptive)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Test basic rate limiting
    @rate_limit('test_operation', tokens=1)
    def test_function():
        print("Function called")
        return "success"

    # Configure test rate limit
    rate_limit_manager.set_rate_limit('test_operation', RateLimit(calls=3, period=10.0))

    # Test function calls
    for i in range(5):
        try:
            result = test_function()
            print(f"Call {i+1}: {result}")
        except RuntimeError as e:
            print(f"Call {i+1}: Rate limited - {e}")
        time.sleep(1)
