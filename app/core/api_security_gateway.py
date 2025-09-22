#!/usr/bin/env python3
"""
API Security Gateway for Unified Security Framework

This module provides comprehensive API security including rate limiting,
input validation, security headers, attack prevention, and request processing
for the xanadOS Search & Destroy security framework.

Consolidates functionality from:
- app/api/security_api.py - Rate limiting, input validation, security headers
- API security patterns and best practices
- Attack prevention and monitoring

Features:
- Advanced rate limiting with sliding windows
- Comprehensive input validation and sanitization
- Security headers injection and CORS handling
- Attack detection and prevention (SQLi, XSS, etc.)
- Request/response monitoring and logging
- Integration with unified security framework
"""

import html
import logging
import re
import time
import urllib.parse
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from .unified_security_framework import SecurityConfig, UnifiedSecurityManager


# ================== SECURITY ENUMERATIONS AND DATA STRUCTURES ==================


class ThreatLevel(Enum):
    """Threat levels for security events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(Enum):
    """Types of attacks detected by the security gateway."""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BRUTE_FORCE = "brute_force"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALFORMED_REQUEST = "malformed_request"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    INVALID_INPUT = "invalid_input"


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    name: str
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_size_seconds: int = 60
    enabled: bool = True


@dataclass
class SecurityHeader:
    """Security header configuration."""

    name: str
    value: str
    always_include: bool = True
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationRule:
    """Input validation rule."""

    field_name: str
    required: bool = False
    data_type: str = "string"  # string, int, float, email, url, etc.
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None  # Regex pattern
    allowed_values: list[str] | None = None
    sanitize: bool = True


@dataclass
class SecurityEvent:
    """Security event detected by the gateway."""

    event_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    threat_level: ThreatLevel = ThreatLevel.LOW
    attack_type: AttackType = AttackType.SUSPICIOUS_PATTERN
    client_ip: str = ""
    user_agent: str = ""
    request_path: str = ""
    request_method: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    blocked: bool = False


# ================== RATE LIMITING SYSTEM ==================


class RateLimiter:
    """
    Advanced rate limiter with sliding window and burst protection.
    """

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RateLimiter")

        # Rate limiting state
        self._request_windows: defaultdict[str, deque] = defaultdict(deque)
        self._burst_counters: defaultdict[str, int] = defaultdict(int)
        self._lockout_times: dict[str, datetime] = {}

        # Default rate limiting rules
        self._rules = {
            "default": RateLimitRule(
                name="default",
                requests_per_minute=self.config.api_rate_limit_per_minute,
                requests_per_hour=self.config.api_rate_limit_per_hour,
                burst_limit=10,
            ),
            "authentication": RateLimitRule(
                name="authentication",
                requests_per_minute=10,
                requests_per_hour=100,
                burst_limit=3,
            ),
            "file_operations": RateLimitRule(
                name="file_operations",
                requests_per_minute=30,
                requests_per_hour=500,
                burst_limit=5,
            ),
        }

        self.logger.info("Rate limiter initialized")

    async def check_rate_limit(
        self, identifier: str, rule_name: str = "default"
    ) -> tuple[bool, dict[str, Any]]:
        """Check if request is within rate limits."""
        try:
            rule = self._rules.get(rule_name, self._rules["default"])
            if not rule.enabled:
                return True, {"rule": rule_name, "allowed": True}

            current_time = datetime.utcnow()

            # Check if in lockout period
            if identifier in self._lockout_times:
                lockout_time = self._lockout_times[identifier]
                if current_time - lockout_time < timedelta(minutes=15):
                    return False, {
                        "rule": rule_name,
                        "allowed": False,
                        "reason": "rate_limit_lockout",
                        "lockout_remaining": 15
                        - (current_time - lockout_time).total_seconds() / 60,
                    }
                else:
                    # Lockout expired
                    del self._lockout_times[identifier]

            # Get request window for identifier
            window_key = f"{identifier}:{rule_name}"
            window = self._request_windows[window_key]

            # Clean old requests from window
            cutoff_time = current_time - timedelta(seconds=rule.window_size_seconds)
            while window and window[0] < cutoff_time:
                window.popleft()

            # Check minute limit
            minute_cutoff = current_time - timedelta(minutes=1)
            recent_requests = sum(1 for req_time in window if req_time > minute_cutoff)

            if recent_requests >= rule.requests_per_minute:
                self._handle_rate_limit_exceeded(identifier, rule_name)
                return False, {
                    "rule": rule_name,
                    "allowed": False,
                    "reason": "rate_limit_exceeded",
                    "limit": rule.requests_per_minute,
                    "window": "1 minute",
                }

            # Check hour limit
            hour_cutoff = current_time - timedelta(hours=1)
            hourly_requests = sum(1 for req_time in window if req_time > hour_cutoff)

            if hourly_requests >= rule.requests_per_hour:
                self._handle_rate_limit_exceeded(identifier, rule_name)
                return False, {
                    "rule": rule_name,
                    "allowed": False,
                    "reason": "rate_limit_exceeded",
                    "limit": rule.requests_per_hour,
                    "window": "1 hour",
                }

            # Check burst limit
            burst_window = current_time - timedelta(
                seconds=10
            )  # 10-second burst window
            burst_requests = sum(1 for req_time in window if req_time > burst_window)

            if burst_requests >= rule.burst_limit:
                return False, {
                    "rule": rule_name,
                    "allowed": False,
                    "reason": "burst_limit_exceeded",
                    "limit": rule.burst_limit,
                    "window": "10 seconds",
                }

            # Add current request to window
            window.append(current_time)

            return True, {
                "rule": rule_name,
                "allowed": True,
                "requests_in_minute": recent_requests + 1,
                "requests_in_hour": hourly_requests + 1,
            }

        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            # Fail open for availability
            return True, {"rule": rule_name, "allowed": True, "error": str(e)}

    def _handle_rate_limit_exceeded(self, identifier: str, rule_name: str):
        """Handle rate limit exceeded event."""
        self._lockout_times[identifier] = datetime.utcnow()
        self.logger.warning(f"Rate limit exceeded for {identifier} on rule {rule_name}")


# ================== INPUT VALIDATION AND SANITIZATION ==================


class InputValidator:
    """
    Comprehensive input validation and sanitization system.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.InputValidator")

        # Common validation patterns
        self._patterns = {
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "url": re.compile(r"^https?://[^\s/$.?#].[^\s]*$"),
            "uuid": re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            ),
            "filename": re.compile(r"^[a-zA-Z0-9._-]+$"),
            "path": re.compile(r"^[a-zA-Z0-9./_-]+$"),
            "alphanumeric": re.compile(r"^[a-zA-Z0-9]+$"),
        }

        # SQL injection patterns
        self._sql_patterns = [
            re.compile(r"(\bUNION\b.*\bSELECT\b)", re.IGNORECASE),
            re.compile(r"(\bSELECT\b.*\bFROM\b)", re.IGNORECASE),
            re.compile(r"(\bINSERT\b.*\bINTO\b)", re.IGNORECASE),
            re.compile(r"(\bDELETE\b.*\bFROM\b)", re.IGNORECASE),
            re.compile(r"(\bDROP\b.*\bTABLE\b)", re.IGNORECASE),
            re.compile(r"(\'\s*OR\s*\')", re.IGNORECASE),
            re.compile(r"(\'\s*AND\s*\')", re.IGNORECASE),
            re.compile(r"(--\s*$)", re.MULTILINE),
        ]

        # XSS patterns
        self._xss_patterns = [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>", re.IGNORECASE),
            re.compile(r"<object[^>]*>", re.IGNORECASE),
            re.compile(r"<embed[^>]*>", re.IGNORECASE),
        ]

        self.logger.info("Input validator initialized")

    async def validate_input(
        self, data: dict[str, Any], rules: list[ValidationRule]
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """Validate input data against rules."""
        try:
            validated_data = {}
            errors = []
            security_warnings = []

            # Create rules lookup
            rules_by_field = {rule.field_name: rule for rule in rules}

            # Check required fields
            for rule in rules:
                if rule.required and rule.field_name not in data:
                    errors.append(f"Required field '{rule.field_name}' is missing")

            # Validate each field in data
            for field_name, value in data.items():
                rule = rules_by_field.get(field_name)
                if not rule:
                    # Unknown field - could be suspicious
                    security_warnings.append(f"Unknown field '{field_name}' in request")
                    continue

                # Validate field
                is_valid, validated_value, field_errors = await self._validate_field(
                    field_name, value, rule
                )

                if is_valid:
                    validated_data[field_name] = validated_value
                else:
                    errors.extend(field_errors)

                # Check for attack patterns
                if isinstance(value, str):
                    attack_detected = await self._check_attack_patterns(
                        field_name, value
                    )
                    if attack_detected:
                        security_warnings.extend(attack_detected)

            is_valid = len(errors) == 0

            return is_valid, validated_data, errors + security_warnings

        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            return False, {}, [f"Validation error: {e!s}"]

    async def _validate_field(
        self, field_name: str, value: Any, rule: ValidationRule
    ) -> tuple[bool, Any, list[str]]:
        """Validate individual field."""
        errors = []

        try:
            # Type validation
            if rule.data_type == "string":
                if not isinstance(value, str):
                    errors.append(f"{field_name} must be a string")
                    return False, value, errors

                # Length validation
                if rule.min_length is not None and len(value) < rule.min_length:
                    errors.append(
                        f"{field_name} must be at least {rule.min_length} characters"
                    )

                if rule.max_length is not None and len(value) > rule.max_length:
                    errors.append(
                        f"{field_name} must be at most {rule.max_length} characters"
                    )

                # Pattern validation
                if rule.pattern:
                    pattern = self._patterns.get(rule.pattern, re.compile(rule.pattern))
                    if not pattern.match(value):
                        errors.append(f"{field_name} format is invalid")

                # Allowed values validation
                if rule.allowed_values and value not in rule.allowed_values:
                    errors.append(
                        f"{field_name} must be one of: {', '.join(rule.allowed_values)}"
                    )

                # Sanitization
                if rule.sanitize and not errors:
                    value = await self._sanitize_string(value)

            elif rule.data_type == "int":
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    errors.append(f"{field_name} must be an integer")

            elif rule.data_type == "float":
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    errors.append(f"{field_name} must be a number")

            elif rule.data_type == "email":
                if not isinstance(value, str) or not self._patterns["email"].match(
                    value
                ):
                    errors.append(f"{field_name} must be a valid email address")

            elif rule.data_type == "url":
                if not isinstance(value, str) or not self._patterns["url"].match(value):
                    errors.append(f"{field_name} must be a valid URL")

            return len(errors) == 0, value, errors

        except Exception as e:
            self.logger.error(f"Field validation failed for {field_name}: {e}")
            return False, value, [f"Validation error for {field_name}"]

    async def _sanitize_string(self, value: str) -> str:
        """Sanitize string input."""
        try:
            # HTML escape
            value = html.escape(value)

            # URL decode (to prevent double encoding attacks)
            value = urllib.parse.unquote(value)

            # Remove null bytes and control characters
            value = "".join(
                char for char in value if ord(char) >= 32 or char in "\t\n\r"
            )

            # Limit length to prevent DoS
            if len(value) > 10000:
                value = value[:10000]

            return value
        except Exception as e:
            self.logger.error(f"String sanitization failed: {e}")
            return value

    async def _check_attack_patterns(self, field_name: str, value: str) -> list[str]:
        """Check for attack patterns in input."""
        warnings = []

        try:
            # SQL injection detection
            for pattern in self._sql_patterns:
                if pattern.search(value):
                    warnings.append(f"Potential SQL injection detected in {field_name}")
                    break

            # XSS detection
            for pattern in self._xss_patterns:
                if pattern.search(value):
                    warnings.append(f"Potential XSS attack detected in {field_name}")
                    break

            # Path traversal detection
            if "../" in value or "..\\" in value:
                warnings.append(
                    f"Potential path traversal attack detected in {field_name}"
                )

            # Command injection detection
            if any(
                cmd in value.lower()
                for cmd in ["rm ", "del ", "format ", "sudo ", "chmod "]
            ):
                warnings.append(f"Potential command injection detected in {field_name}")

            return warnings

        except Exception as e:
            self.logger.error(f"Attack pattern check failed: {e}")
            return warnings


# ================== SECURITY HEADERS MANAGER ==================


class SecurityHeadersManager:
    """
    Security headers injection and CORS handling.
    """

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SecurityHeadersManager")

        # Default security headers
        self._default_headers = [
            SecurityHeader("X-Content-Type-Options", "nosniff"),
            SecurityHeader("X-Frame-Options", "DENY"),
            SecurityHeader("X-XSS-Protection", "1; mode=block"),
            SecurityHeader("Referrer-Policy", "strict-origin-when-cross-origin"),
            SecurityHeader(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';",
            ),
            SecurityHeader(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            ),
            SecurityHeader(
                "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
            ),
        ]

        self.logger.info("Security headers manager initialized")

    def get_security_headers(
        self, request_context: dict[str, Any] | None = None
    ) -> dict[str, str]:
        """Get security headers for response."""
        headers = {}

        try:
            for header in self._default_headers:
                if header.always_include:
                    headers[header.name] = header.value
                elif request_context and self._check_header_conditions(
                    header, request_context
                ):
                    headers[header.name] = header.value

            return headers

        except Exception as e:
            self.logger.error(f"Security headers generation failed: {e}")
            return {}

    def _check_header_conditions(
        self, header: SecurityHeader, context: dict[str, Any]
    ) -> bool:
        """Check if header conditions are met."""
        # Simplified condition checking - in production would be more sophisticated
        return True

    def handle_cors(self, origin: str | None, method: str) -> dict[str, str]:
        """Handle CORS headers."""
        cors_headers = {}

        try:
            if not self.config.enable_cors:
                return cors_headers

            # Check if origin is allowed
            if origin and self._is_origin_allowed(origin):
                cors_headers["Access-Control-Allow-Origin"] = origin
                cors_headers["Access-Control-Allow-Credentials"] = "true"

            # Handle preflight requests
            if method.upper() == "OPTIONS":
                cors_headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, DELETE, OPTIONS"
                )
                cors_headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-API-Key"
                )
                cors_headers["Access-Control-Max-Age"] = "86400"

            return cors_headers

        except Exception as e:
            self.logger.error(f"CORS handling failed: {e}")
            return {}

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed list."""
        try:
            parsed_origin = urlparse(origin)
            hostname = parsed_origin.hostname

            if hostname in self.config.allowed_origins:
                return True

            # Check for localhost variations
            if hostname in ["localhost", "127.0.0.1", "::1"]:
                return "localhost" in self.config.allowed_origins

            return False

        except Exception as e:
            self.logger.error(f"Origin validation failed: {e}")
            return False


# ================== API SECURITY GATEWAY ==================


class APISecurityGateway:
    """
    Comprehensive API security gateway combining all security components.
    """

    def __init__(
        self,
        config: SecurityConfig | None = None,
        security_manager: UnifiedSecurityManager | None = None,
    ):
        self.config = config or SecurityConfig()
        self.security_manager = security_manager
        self.logger = logging.getLogger(f"{__name__}.APISecurityGateway")

        # Initialize security components
        self.rate_limiter = RateLimiter(self.config)
        self.input_validator = InputValidator()
        self.headers_manager = SecurityHeadersManager(self.config)

        # Security monitoring
        self._security_events: deque[SecurityEvent] = deque(maxlen=10000)
        self._blocked_ips: set[str] = set()
        self._suspicious_patterns: dict[str, int] = defaultdict(int)

        self.logger.info("API Security Gateway initialized")

    async def process_request(
        self, request_data: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        """Process incoming request through security gateway."""
        try:
            client_ip = request_data.get("client_ip", "unknown")
            user_agent = request_data.get("user_agent", "")
            request_path = request_data.get("path", "")
            request_method = request_data.get("method", "GET")

            # Check if IP is blocked
            if client_ip in self._blocked_ips:
                await self._log_security_event(
                    ThreatLevel.HIGH,
                    AttackType.BRUTE_FORCE,
                    client_ip,
                    user_agent,
                    request_path,
                    request_method,
                    {"reason": "blocked_ip"},
                    blocked=True,
                )
                return False, {"error": "Access denied", "reason": "blocked_ip"}

            # Rate limiting check
            rate_limit_passed, rate_limit_info = (
                await self.rate_limiter.check_rate_limit(
                    client_ip, self._get_rate_limit_rule(request_path)
                )
            )

            if not rate_limit_passed:
                await self._log_security_event(
                    ThreatLevel.MEDIUM,
                    AttackType.RATE_LIMIT_EXCEEDED,
                    client_ip,
                    user_agent,
                    request_path,
                    request_method,
                    rate_limit_info,
                    blocked=True,
                )
                return False, {
                    "error": "Rate limit exceeded",
                    "details": rate_limit_info,
                }

            # Input validation
            if "data" in request_data:
                validation_rules = self._get_validation_rules(
                    request_path, request_method
                )
                is_valid, validated_data, validation_errors = (
                    await self.input_validator.validate_input(
                        request_data["data"], validation_rules
                    )
                )

                if not is_valid:
                    await self._log_security_event(
                        ThreatLevel.MEDIUM,
                        AttackType.INVALID_INPUT,
                        client_ip,
                        user_agent,
                        request_path,
                        request_method,
                        {"validation_errors": validation_errors},
                        blocked=True,
                    )
                    return False, {
                        "error": "Invalid input",
                        "details": validation_errors,
                    }

                request_data["data"] = validated_data

            # Additional security checks
            security_check_passed = await self._perform_security_checks(request_data)
            if not security_check_passed:
                return False, {"error": "Security check failed"}

            return True, {"status": "allowed", "rate_limit": rate_limit_info}

        except Exception as e:
            self.logger.error(f"Request processing failed: {e}")
            return False, {"error": "Internal security error"}

    def get_response_headers(
        self, request_data: dict[str, Any] | None = None
    ) -> dict[str, str]:
        """Get security headers for response."""
        try:
            headers = self.headers_manager.get_security_headers(request_data)

            # Add CORS headers if needed
            if request_data:
                origin = request_data.get("origin")
                method = request_data.get("method", "GET")
                cors_headers = self.headers_manager.handle_cors(origin, method)
                headers.update(cors_headers)

            return headers

        except Exception as e:
            self.logger.error(f"Response headers generation failed: {e}")
            return {}

    def _get_rate_limit_rule(self, path: str) -> str:
        """Get appropriate rate limit rule for path."""
        if "/auth" in path or "/login" in path:
            return "authentication"
        elif "/files" in path or "/quarantine" in path:
            return "file_operations"
        else:
            return "default"

    def _get_validation_rules(self, path: str, method: str) -> list[ValidationRule]:
        """Get validation rules for endpoint."""
        rules = []

        # Common rules
        if method in ["POST", "PUT", "PATCH"]:
            if "/auth" in path:
                rules.extend(
                    [
                        ValidationRule(
                            "username",
                            required=True,
                            min_length=3,
                            max_length=50,
                            pattern="alphanumeric",
                        ),
                        ValidationRule(
                            "password", required=True, min_length=8, max_length=128
                        ),
                    ]
                )
            elif "/files" in path:
                rules.extend(
                    [
                        ValidationRule("filename", required=True, pattern="filename"),
                        ValidationRule("path", required=False, pattern="path"),
                    ]
                )

        return rules

    async def _perform_security_checks(self, request_data: dict[str, Any]) -> bool:
        """Perform additional security checks."""
        try:
            # Check for suspicious patterns
            user_agent = request_data.get("user_agent", "")
            if self._is_suspicious_user_agent(user_agent):
                return False

            # Check request size
            if "data" in request_data:
                data_size = len(str(request_data["data"]))
                if data_size > self.config.api_max_request_size_mb * 1024 * 1024:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Security checks failed: {e}")
            return True  # Fail open

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        suspicious_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "scanner",
            "exploit",
            "attack",
            "hack",
        ]

        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)

    async def _log_security_event(
        self,
        threat_level: ThreatLevel,
        attack_type: AttackType,
        client_ip: str,
        user_agent: str,
        request_path: str,
        request_method: str,
        details: dict[str, Any],
        blocked: bool = False,
    ):
        """Log security event."""
        try:
            event = SecurityEvent(
                event_id=f"sec_{int(time.time())}_{len(self._security_events)}",
                threat_level=threat_level,
                attack_type=attack_type,
                client_ip=client_ip,
                user_agent=user_agent,
                request_path=request_path,
                request_method=request_method,
                details=details,
                blocked=blocked,
            )

            self._security_events.append(event)

            # Log critical events
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self.logger.warning(
                    f"Security event: {attack_type.value} from {client_ip}"
                )

            # Auto-block on repeated high-threat events
            if threat_level == ThreatLevel.HIGH and blocked:
                self._suspicious_patterns[client_ip] += 1
                if self._suspicious_patterns[client_ip] >= 5:
                    self._blocked_ips.add(client_ip)
                    self.logger.warning(
                        f"Auto-blocked IP {client_ip} due to repeated security violations"
                    )

        except Exception as e:
            self.logger.error(f"Security event logging failed: {e}")

    def get_security_events(self, limit: int = 100) -> list[SecurityEvent]:
        """Get recent security events."""
        return list(self._security_events)[-limit:]

    def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock IP address."""
        try:
            if ip_address in self._blocked_ips:
                self._blocked_ips.remove(ip_address)
                self._suspicious_patterns[ip_address] = 0
                self.logger.info(f"Unblocked IP {ip_address}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"IP unblocking failed: {e}")
            return False


# Export public API
__all__ = [
    "APISecurityGateway",
    "AttackType",
    "InputValidator",
    "RateLimitRule",
    "RateLimiter",
    "SecurityEvent",
    "SecurityHeader",
    "SecurityHeadersManager",
    "ThreatLevel",
    "ValidationRule",
]
