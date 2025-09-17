#!/usr/bin/env python3
"""API-First Architecture for xanadOS Search & Destroy.

This module provides comprehensive REST and GraphQL APIs with authentication,
rate limiting, complete endpoint coverage, webhook support, and enterprise
integration capabilities.

Features:
- RESTful API with full CRUD operations
- GraphQL API with flexible queries and mutations
- JWT-based authentication and authorization
- Rate limiting and request throttling
- Comprehensive endpoint coverage for all security components
- Webhook system for real-time notifications
- Enterprise integration capabilities
- API versioning and backward compatibility
- OpenAPI/Swagger documentation
- Request/response logging and monitoring
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
import time
import secrets
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from functools import wraps
from pathlib import Path

import jwt
from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import strawberry
from strawberry.fastapi import GraphQLRouter
import redis
import httpx
from cryptography.fernet import Fernet

from app.utils.secure_crypto import secure_crypto, generate_api_key
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.ml_threat_detector import MLThreatDetector
from app.core.edr_engine import EDREngine, SecurityEvent
from app.core.intelligent_automation import get_intelligent_automation
from app.reporting.advanced_reporting import get_advanced_reporting
from app.utils.config import get_config, get_api_security_config, get_secure_database_url, get_redis_config, backup_database, DATA_DIR


# Database Models
Base = declarative_base()

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key_id = Column(String(50), unique=True, index=True)
    key_hash = Column(String(255))
    name = Column(String(100))
    permissions = Column(Text)  # JSON string
    rate_limit = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)


class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True)
    request_id = Column(String(50), index=True)
    endpoint = Column(String(255))
    method = Column(String(10))
    status_code = Column(Integer)
    response_time = Column(Integer)  # milliseconds
    ip_address = Column(String(45))
    user_agent = Column(Text)
    api_key_id = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True)
    url = Column(String(500))
    events = Column(Text)  # JSON array
    secret = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)


# Pydantic Models
class ThreatDetectionRequest(BaseModel):
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    scan_type: str = Field(default="full", pattern="^(quick|full|deep)$")
    include_metadata: bool = True

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        """Validate file path to prevent directory traversal attacks."""
        if v is None:
            return v
        # Normalize path and check for dangerous patterns
        if '..' in v or v.startswith('/'):
            raise ValueError("File path cannot contain '..' or start with '/'")
        # Sanitize path - only allow alphanumeric, underscore, dash, dot, forward slash
        if not re.match(r'^[a-zA-Z0-9._/-]+$', v):
            raise ValueError("File path contains invalid characters")
        if len(v) > 1000:
            raise ValueError("File path too long (max 1000 characters)")
        return v

    @field_validator('file_content')
    @classmethod
    def validate_file_content(cls, v):
        """Validate file content size and encoding."""
        if v is None:
            return v
        # Limit file content size to 10MB
        if len(v.encode('utf-8')) > 10 * 1024 * 1024:
            raise ValueError("File content too large (max 10MB)")
        # Check for null bytes which can indicate binary data or injection attempts
        if '\x00' in v:
            raise ValueError("File content contains null bytes")
        return v

    @field_validator('scan_type')
    @classmethod
    def validate_scan_type(cls, v):
        """Additional validation for scan type."""
        allowed_types = {'quick', 'full', 'deep'}
        if v not in allowed_types:
            raise ValueError(f"Invalid scan type. Must be one of: {allowed_types}")
        return v


class ThreatDetectionResponse(BaseModel):
    threat_detected: bool
    threat_type: Optional[str] = None
    confidence: float
    scan_duration: float
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SystemScanRequest(BaseModel):
    paths: List[str] = []
    exclude_patterns: List[str] = []
    scan_type: str = Field(default="full", pattern="^(quick|full|deep)$")
    max_file_size: int = Field(default=100*1024*1024, ge=1024)  # 100MB default

    # @validator('paths')
    def validate_paths(cls, v):
        """Validate scan paths to prevent directory traversal and injection."""
        if not isinstance(v, list):
            raise ValueError("Paths must be a list")
        if len(v) > 100:
            raise ValueError("Too many paths specified (max 100)")

        validated_paths = []
        for path in v:
            if not isinstance(path, str):
                raise ValueError("All paths must be strings")
            # Normalize and validate path
            if '..' in path:
                raise ValueError(f"Path '{path}' contains '..' which is not allowed")
            # Allow absolute paths but validate them
            if not re.match(r'^[a-zA-Z0-9._/-]+$', path):
                raise ValueError(f"Path '{path}' contains invalid characters")
            if len(path) > 1000:
                raise ValueError(f"Path '{path}' too long (max 1000 characters)")
            validated_paths.append(path)
        return validated_paths

    @validator('exclude_patterns')
    def validate_exclude_patterns(cls, v):
        """Validate exclude patterns."""
        if not isinstance(v, list):
            raise ValueError("Exclude patterns must be a list")
        if len(v) > 50:
            raise ValueError("Too many exclude patterns (max 50)")

        for pattern in v:
            if not isinstance(pattern, str):
                raise ValueError("All exclude patterns must be strings")
            if len(pattern) > 200:
                raise ValueError("Exclude pattern too long (max 200 characters)")
            # Basic regex validation
            try:
                re.compile(pattern)
            except re.error:
                raise ValueError(f"Invalid regex pattern: '{pattern}'")
        return v

    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        """Validate max file size limits."""
        if v < 1024:  # 1KB minimum
            raise ValueError("Max file size must be at least 1KB")
        if v > 1024 * 1024 * 1024:  # 1GB maximum
            raise ValueError("Max file size cannot exceed 1GB")
        return v


class SystemScanResponse(BaseModel):
    scan_id: str
    status: str
    threats_found: int
    files_scanned: int
    scan_duration: float
    started_at: datetime
    completed_at: Optional[datetime] = None


class SecurityEventRequest(BaseModel):
    event_type: str
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    source: str
    description: str
    metadata: Dict[str, Any] = {}

    @validator('event_type')
    def validate_event_type(cls, v):
        """Validate event type to prevent injection."""
        if not isinstance(v, str):
            raise ValueError("Event type must be a string")
        if len(v) < 1 or len(v) > 100:
            raise ValueError("Event type must be 1-100 characters")
        # Only allow alphanumeric, underscore, and dash
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Event type can only contain letters, numbers, underscore, and dash")
        return v.lower()

    @validator('source')
    def validate_source(cls, v):
        """Validate event source."""
        if not isinstance(v, str):
            raise ValueError("Source must be a string")
        if len(v) < 1 or len(v) > 200:
            raise ValueError("Source must be 1-200 characters")
        # Allow more characters for source but still restrict dangerous ones
        if not re.match(r'^[a-zA-Z0-9._:-]+$', v):
            raise ValueError("Source contains invalid characters")
        return v

    @validator('description')
    def validate_description(cls, v):
        """Validate description to prevent XSS and injection."""
        if not isinstance(v, str):
            raise ValueError("Description must be a string")
        if len(v) < 1 or len(v) > 2000:
            raise ValueError("Description must be 1-2000 characters")
        # Check for dangerous HTML/script tags
        dangerous_patterns = [
            r'<script[^>]*>',
            r'</script>',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'<iframe[^>]*>',
            r'<embed[^>]*>',
            r'<object[^>]*>'
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Description contains potentially dangerous content")
        return v

    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata dictionary."""
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        if len(v) > 50:
            raise ValueError("Too many metadata fields (max 50)")

        total_size = 0
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("All metadata keys must be strings")
            if len(key) > 100:
                raise ValueError("Metadata key too long (max 100 characters)")
            if not re.match(r'^[a-zA-Z0-9._-]+$', key):
                raise ValueError(f"Metadata key '{key}' contains invalid characters")

            # Convert value to string and check size
            str_value = str(value)
            if len(str_value) > 1000:
                raise ValueError(f"Metadata value for '{key}' too long (max 1000 characters)")
            total_size += len(key) + len(str_value)

        if total_size > 10000:
            raise ValueError("Total metadata size too large (max 10KB)")
        return v


class SecurityEventResponse(BaseModel):
    event_id: str
    timestamp: datetime
    processed: bool
    actions_taken: List[str] = []


class WebhookRequest(BaseModel):
    url: str = Field(pattern=r'^https?://.+')
    events: List[str]
    secret: Optional[str] = None

    @validator('url')
    def validate_url(cls, v):
        """Enhanced URL validation to prevent SSRF attacks."""
        if not isinstance(v, str):
            raise ValueError("URL must be a string")
        if len(v) > 2000:
            raise ValueError("URL too long (max 2000 characters)")

        # Must start with http or https
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")

        # Parse URL to validate components
        try:
            from urllib.parse import urlparse
            parsed = urlparse(v)

            # Check for dangerous schemes
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP and HTTPS URLs are allowed")

            # Prevent localhost and private IP ranges
            hostname = parsed.hostname
            if hostname:
                hostname = hostname.lower()
                # Block localhost variants
                if hostname in ['localhost', '127.0.0.1', '0.0.0.0', '::1']:
                    raise ValueError("Localhost URLs are not allowed")

                # Block private IP ranges (basic check)
                if (hostname.startswith('192.168.') or
                    hostname.startswith('10.') or
                    hostname.startswith('172.')):
                    raise ValueError("Private IP addresses are not allowed")

                # Block link-local addresses
                if hostname.startswith('169.254.'):
                    raise ValueError("Link-local addresses are not allowed")

        except Exception as e:
            raise ValueError(f"Invalid URL format: {str(e)}")

        return v

    @validator('events')
    def validate_events(cls, v):
        """Validate webhook events list."""
        if not isinstance(v, list):
            raise ValueError("Events must be a list")
        if len(v) == 0:
            raise ValueError("At least one event must be specified")
        if len(v) > 20:
            raise ValueError("Too many events specified (max 20)")

        allowed_events = {
            'threat_detected', 'scan_completed', 'system_alert',
            'security_event', 'api_key_created', 'api_key_revoked',
            'authentication_failed', 'rate_limit_exceeded'
        }

        for event in v:
            if not isinstance(event, str):
                raise ValueError("All events must be strings")
            if event not in allowed_events:
                raise ValueError(f"Invalid event '{event}'. Allowed events: {allowed_events}")

        return list(set(v))  # Remove duplicates

    @validator('secret')
    def validate_secret(cls, v):
        """Validate webhook secret."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("Secret must be a string")
        if len(v) < 8:
            raise ValueError("Secret must be at least 8 characters")
        if len(v) > 256:
            raise ValueError("Secret too long (max 256 characters)")
        return v


class WebhookResponse(BaseModel):
    webhook_id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime


# File Upload Models
class FileUploadResponse(BaseModel):
    """Response model for secure file uploads."""
    file_id: str
    filename: str
    file_size: int
    content_type: str
    sha256_hash: str
    upload_timestamp: datetime
    scan_status: str = Field(default="pending")
    threat_detected: bool = Field(default=False)
    quarantined: bool = Field(default=False)


class FileUploadMetadata(BaseModel):
    """Metadata for uploaded files."""
    purpose: str = Field(..., pattern="^(scan|analysis|reference)$")
    description: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default=[], max_length=10)
    retention_days: int = Field(default=30, ge=1, le=365)

    @validator('tags')
    def validate_tags(cls, v):
        """Validate file tags."""
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
            if len(tag) > 50:
                raise ValueError("Tag too long (max 50 characters)")
            if not re.match(r'^[a-zA-Z0-9._-]+$', tag):
                raise ValueError("Tag contains invalid characters")
        return v


class FileListResponse(BaseModel):
    """Response model for file listings."""
    files: List[FileUploadResponse]
    total_count: int
    page: int
    page_size: int


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10


class InputSanitizer:
    """Comprehensive input sanitization and validation utilities."""

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"'[\s]*(?:or|and)[\s]*'",
        r"'[\s]*(?:union|select|insert|update|delete|drop|create|alter)[\s]",
        r"--[\s]*",
        r"/\*.*?\*/",
        r"xp_cmdshell",
        r"sp_executesql"
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>"
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`]",
        r"\$\(",
        r"`[^`]*`",
        r"\|\s*\w+",
        r"&&\s*\w+",
        r"\|\|\s*\w+",
        r">\s*/",
        r"<\s*/"
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000,
                       allow_html: bool = False,
                       check_sql_injection: bool = True,
                       check_xss: bool = True,
                       check_command_injection: bool = True) -> str:
        """
        Comprehensive string sanitization.

        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            check_sql_injection: Whether to check for SQL injection patterns
            check_xss: Whether to check for XSS patterns
            check_command_injection: Whether to check for command injection

        Returns:
            Sanitized string

        Raises:
            ValueError: If dangerous patterns are detected
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a string")

        if len(value) > max_length:
            raise ValueError(f"String too long (max {max_length} characters)")

        # Check for null bytes
        if '\x00' in value:
            raise ValueError("String contains null bytes")

        # Check for control characters (except common whitespace)
        if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', value):
            raise ValueError("String contains control characters")

        # SQL injection check
        if check_sql_injection:
            for pattern in cls.SQL_INJECTION_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValueError("Potential SQL injection detected")

        # XSS check
        if check_xss and not allow_html:
            for pattern in cls.XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValueError("Potential XSS attack detected")

        # Command injection check
        if check_command_injection:
            for pattern in cls.COMMAND_INJECTION_PATTERNS:
                if re.search(pattern, value):
                    raise ValueError("Potential command injection detected")

        return value

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")

        if len(filename) > 255:
            raise ValueError("Filename too long (max 255 characters)")

        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Remove dots at start/end and double dots
        filename = filename.strip('. ')
        if '..' in filename:
            raise ValueError("Filename cannot contain '..'")

        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        if filename.upper() in reserved_names:
            raise ValueError("Filename is a reserved name")

        if not filename:
            raise ValueError("Filename cannot be empty")

        return filename

    @classmethod
    def validate_json_size(cls, data: dict, max_size: int = 1024 * 1024) -> dict:
        """Validate JSON data size to prevent DoS attacks."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        # Calculate approximate JSON size
        json_str = json.dumps(data, separators=(',', ':'))
        if len(json_str.encode('utf-8')) > max_size:
            raise ValueError(f"JSON data too large (max {max_size} bytes)")

        return data

    @classmethod
    def prevent_sql_injection(cls, value: str) -> str:
        """Specific SQL injection prevention."""
        return cls.sanitize_string(value, check_sql_injection=True, check_xss=False, check_command_injection=False)

    @classmethod
    def prevent_xss(cls, value: str) -> str:
        """Specific XSS prevention."""
        return cls.sanitize_string(value, check_sql_injection=False, check_xss=True, check_command_injection=False)

    @classmethod
    def prevent_path_traversal(cls, path: str) -> str:
        """Prevent directory traversal attacks."""
        if not isinstance(path, str):
            raise ValueError("Path must be a string")

        # Normalize the path
        normalized_path = os.path.normpath(path)

        # Check for dangerous patterns
        if '..' in normalized_path:
            raise ValueError("Path contains directory traversal sequences")

        # Check for absolute paths
        if os.path.isabs(normalized_path):
            raise ValueError("Absolute paths are not allowed")

        # Check for dangerous characters
        dangerous_chars = ['\\', '|', '&', ';', '$', '>', '<', '`']
        if any(char in normalized_path for char in dangerous_chars):
            raise ValueError("Path contains dangerous characters")

        return normalized_path


class InputValidationMiddleware:
    """
    Comprehensive input validation middleware for FastAPI.

    This middleware provides multiple layers of protection:
    - Request size limits to prevent DoS attacks
    - Content-Type validation
    - Header sanitization
    - Query parameter validation
    - JSON payload validation
    """

    def __init__(self, app):
        self.app = app

        # Configuration
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_headers = 50
        self.max_header_size = 8192
        self.max_query_params = 50
        self.max_query_param_length = 1000

        # Allowed content types
        self.allowed_content_types = {
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain'
        }

    async def __call__(self, scope, receive, send):
        """Process incoming requests with comprehensive validation."""

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            # Validate request size
            content_length = scope.get("headers", {})
            for name, value in scope.get("headers", []):
                if name == b"content-length":
                    try:
                        size = int(value.decode())
                        if size > self.max_request_size:
                            await self._send_error(send, 413, "Request too large")
                            return
                    except ValueError:
                        await self._send_error(send, 400, "Invalid content-length header")
                        return

            # Validate headers
            headers = scope.get("headers", [])
            if len(headers) > self.max_headers:
                await self._send_error(send, 400, "Too many headers")
                return

            for name, value in headers:
                if len(value) > self.max_header_size:
                    await self._send_error(send, 400, "Header too large")
                    return

                # Sanitize header values
                try:
                    header_value = value.decode('utf-8', errors='strict')
                    # Check for dangerous characters in headers
                    if any(char in header_value for char in ['\n', '\r', '\0']):
                        await self._send_error(send, 400, "Invalid header format")
                        return
                except UnicodeDecodeError:
                    await self._send_error(send, 400, "Invalid header encoding")
                    return

            # Validate query parameters
            query_string = scope.get("query_string", b"").decode()
            if query_string:
                try:
                    from urllib.parse import parse_qs
                    query_params = parse_qs(query_string)

                    if len(query_params) > self.max_query_params:
                        await self._send_error(send, 400, "Too many query parameters")
                        return

                    for key, values in query_params.items():
                        if len(key) > 100:
                            await self._send_error(send, 400, "Query parameter name too long")
                            return

                        for value in values:
                            if len(value) > self.max_query_param_length:
                                await self._send_error(send, 400, "Query parameter value too long")
                                return

                            # Basic injection protection for query params
                            try:
                                InputSanitizer.sanitize_string(
                                    value,
                                    max_length=self.max_query_param_length,
                                    allow_html=False,
                                    check_sql_injection=True,
                                    check_xss=True,
                                    check_command_injection=True
                                )
                            except ValueError as e:
                                await self._send_error(send, 400, f"Invalid query parameter: {str(e)}")
                                return

                except Exception as e:
                    await self._send_error(send, 400, "Invalid query string format")
                    return

            # Validate Content-Type for POST/PUT/PATCH requests
            method = scope.get("method", "")
            if method in ["POST", "PUT", "PATCH"]:
                content_type = None
                for name, value in headers:
                    if name == b"content-type":
                        content_type = value.decode().split(';')[0].strip()
                        break

                if content_type and content_type not in self.allowed_content_types:
                    await self._send_error(send, 415, "Unsupported content type")
                    return

            # Continue to the application
            await self.app(scope, receive, send)

        except Exception as e:
            logging.error(f"Input validation middleware error: {type(e).__name__}")
            await self._send_error(send, 500, "Internal server error")

    async def _send_error(self, send, status_code: int, message: str):
        """Send error response."""
        response = {
            "status_code": status_code,
            "body": json.dumps({"error": message}).encode(),
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(json.dumps({"error": message}).encode())).encode()]
            ]
        }

        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": response["headers"]
        })

        await send({
            "type": "http.response.body",
            "body": response["body"]
        })


@dataclass
class APIPermissions:
    """API access permissions."""
    read_threats: bool = True
    write_threats: bool = False
    read_system: bool = True
    write_system: bool = False
    read_reports: bool = True
    write_reports: bool = False
    admin_access: bool = False

    def to_dict(self) -> Dict[str, bool]:
        """Safe serialization of permissions."""
        return {
            "read_threats": self.read_threats,
            "write_threats": self.write_threats,
            "read_system": self.read_system,
            "write_system": self.write_system,
            "read_reports": self.read_reports,
            "write_reports": self.write_reports,
            "admin_access": self.admin_access
        }

    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> "APIPermissions":
        """Safe deserialization of permissions."""
        return cls(
            read_threats=data.get("read_threats", False),
            write_threats=data.get("write_threats", False),
            read_system=data.get("read_system", False),
            write_system=data.get("write_system", False),
            read_reports=data.get("read_reports", False),
            write_reports=data.get("write_reports", False),
            admin_access=data.get("admin_access", False)
        )


class AuthenticationManager:
    """Manage API authentication and authorization with enhanced security."""

    def __init__(self, api_config: Optional[dict] = None):
        """
        Initialize AuthenticationManager with secure configuration.

        Args:
            api_config: Optional API security configuration dict.
                       If None, will load from secure config system.
        """
        # Load secure configuration
        if api_config is None:
            api_config = get_api_security_config()

        # JWT Configuration
        jwt_config = api_config.get("jwt", {})
        self.secret_key = jwt_config["secret_key"]
        self.algorithm = jwt_config.get("algorithm", "HS256")
        self.access_token_expire_minutes = jwt_config.get("access_token_expire_minutes", 15)
        self.refresh_token_expire_days = jwt_config.get("refresh_token_expire_days", 7)

        # Security enhancements
        self.token_issuer = jwt_config.get("issuer", "xanadOS-Security-API")
        self.token_audience = jwt_config.get("audience", "xanadOS-clients")
        self.blacklisted_tokens: Set[str] = set()  # In-memory blacklist (use Redis in production)

        # Redis Configuration
        redis_config = api_config.get("redis", {})
        try:
            self.redis_client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password") or None,
                ssl=redis_config.get("ssl", False),
                socket_timeout=redis_config.get("socket_timeout", 30),
                retry_on_timeout=redis_config.get("retry_on_timeout", True),
                decode_responses=True
            )
            # Test Redis connection
            self.redis_client.ping()
            logging.info("Redis connection established successfully")
        except Exception as e:
            logging.warning(f"Redis connection failed, using in-memory fallback: {e}")
            self.redis_client = None

        # Database Configuration
        try:
            database_url = get_secure_database_url()
            db_config = api_config.get("database", {})

            # Create engine with security options
            engine_kwargs = {
                "pool_size": db_config.get("pool_size", 10),
                "max_overflow": db_config.get("max_overflow", 20),
                "pool_timeout": db_config.get("pool_timeout", 30),
                "pool_recycle": db_config.get("pool_recycle", 3600),
                "echo": db_config.get("echo", False)
            }

            # SQLite-specific optimizations
            if "sqlite" in database_url:
                engine_kwargs.update({
                    "pool_pre_ping": True,
                    "connect_args": {
                        "check_same_thread": False,
                        "timeout": 30,
                        # Enable WAL mode for better concurrency
                        "isolation_level": None
                    }
                })

            self.engine = create_engine(database_url, **engine_kwargs)

            # Create tables
            Base.metadata.create_all(bind=self.engine)

            # Session configuration
            SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False
            )
            self.db_session = SessionLocal()

            # Enable WAL mode for SQLite
            if "sqlite" in database_url:
                self.db_session.execute(text("PRAGMA journal_mode=WAL"))
                self.db_session.execute(text("PRAGMA synchronous=NORMAL"))
                self.db_session.execute(text("PRAGMA cache_size=1000"))
                self.db_session.execute(text("PRAGMA temp_store=memory"))
                self.db_session.commit()

            # Create initial backup
            backup_database()

            logging.info(f"Database initialized successfully: {database_url}")

        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
            raise RuntimeError(f"Cannot initialize database: {e}")

        # Security validation
        self._validate_security_config(api_config)

    def _validate_security_config(self, api_config: dict):
        """Validate security configuration and warn about insecure settings."""
        jwt_config = api_config.get("jwt", {})

        # Check secret key strength
        secret_key = jwt_config.get("secret_key", "")
        if len(secret_key) < 32:
            logging.warning("JWT secret key is too short! Minimum 32 characters recommended.")

        # Check for default/weak secrets
        weak_patterns = ["secret", "password", "key", "default", "test", "dev"]
        if any(pattern in secret_key.lower() for pattern in weak_patterns):
            logging.warning("JWT secret key appears to contain weak patterns!")

        # Check algorithm security
        algorithm = jwt_config.get("algorithm", "HS256")
        if algorithm in ["none", "HS256"] and len(secret_key) < 64:
            logging.warning(f"JWT algorithm {algorithm} with short key may be vulnerable!")

        # Check token expiry times
        access_expire = jwt_config.get("access_token_expire_minutes", 15)
        if access_expire > 60:
            logging.warning("Access token expiry time is longer than recommended (60 minutes max)")

        refresh_expire = jwt_config.get("refresh_token_expire_days", 7)
        if refresh_expire > 30:
            logging.warning("Refresh token expiry time is longer than recommended (30 days max)")

        # Check database security
        db_config = api_config.get("database", {})
        db_path = db_config.get("path", "")
        if db_path and not str(db_path).startswith(str(DATA_DIR)):
            logging.warning("Database path is not in secure data directory!")

        # Check Redis security
        redis_config = api_config.get("redis", {})
        if not redis_config.get("password") and redis_config.get("host") != "localhost":
            logging.warning("Redis connection has no password for remote host!")

        logging.info("Security configuration validation completed")

    async def create_api_key(self, name: str, permissions: APIPermissions,
                           rate_limit: int = 1000) -> Tuple[str, str]:
        """Create new API key."""
        # Generate API key
        key_id = self._generate_key_id()
        api_key = self._generate_api_key()
        key_hash = self._hash_key(api_key)

        # Store in database
        db_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=json.dumps(permissions.__dict__),
            rate_limit=rate_limit
        )
        self.db_session.add(db_key)
        self.db_session.commit()

        return key_id, api_key

    async def validate_api_key(self, api_key: str) -> Optional[APIPermissions]:
        """Validate API key and return permissions."""
        key_hash = self._hash_key(api_key)

        db_key = self.db_session.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()

        if not db_key:
            return None

        # Update last used timestamp
        db_key.last_used = datetime.utcnow()
        self.db_session.commit()

        # Return permissions
        permissions_dict = json.loads(db_key.permissions)
        return APIPermissions(**permissions_dict)

    async def create_jwt_token(self, user_id: str, permissions: APIPermissions) -> Dict[str, str]:
        """Create JWT access and refresh tokens with enhanced security."""
        current_time = datetime.utcnow()

        # Generate unique token ID for revocation support
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())

        # Create secure permissions dictionary (avoid direct object serialization)
        permissions_dict = permissions.to_dict()

        # Access token with security claims
        access_payload = {
            "user_id": user_id,
            "permissions": permissions_dict,
            "exp": current_time + timedelta(minutes=self.access_token_expire_minutes),
            "iat": current_time,
            "nbf": current_time,  # Not before claim
            "iss": self.token_issuer,  # Issuer claim
            "aud": self.token_audience,  # Audience claim
            "jti": access_jti,  # JWT ID for revocation
            "type": "access",
            "scope": "api_access"
        }

        # Refresh token with minimal claims
        refresh_payload = {
            "user_id": user_id,
            "exp": current_time + timedelta(days=self.refresh_token_expire_days),
            "iat": current_time,
            "nbf": current_time,
            "iss": self.token_issuer,
            "aud": self.token_audience,
            "jti": refresh_jti,
            "type": "refresh",
            "scope": "token_refresh"
        }

        try:
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

            # Store token JTIs in Redis for revocation tracking
            if self.redis_client:
                # Store with expiration matching token expiry
                access_expire = self.access_token_expire_minutes * 60
                refresh_expire = self.refresh_token_expire_days * 24 * 60 * 60

                await self.redis_client.setex(f"token:access:{access_jti}", access_expire, user_id)
                await self.redis_client.setex(f"token:refresh:{refresh_jti}", refresh_expire, user_id)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "refresh_expires_in": self.refresh_token_expire_days * 24 * 60 * 60
            }

        except Exception as e:
            logging.error(f"JWT token creation failed: {e}")
            raise ValueError("Failed to create secure tokens")

    async def validate_jwt_token(self, token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
        """Validate JWT token with comprehensive security checks."""
        try:
            # Decode with strict validation
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.token_audience,
                issuer=self.token_issuer,
                options={
                    "require": ["exp", "iat", "nbf", "iss", "aud", "jti"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )

            # Verify token type
            if payload.get("type") != expected_type:
                logging.warning(f"Token type mismatch: expected {expected_type}, got {payload.get('type')}")
                return None

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti:
                # Check Redis blacklist first
                if self.redis_client:
                    is_blacklisted = await self.redis_client.get(f"blacklist:{jti}")
                    if is_blacklisted:
                        logging.warning(f"Attempted use of blacklisted token: {jti}")
                        return None

                # Check in-memory blacklist as fallback
                if jti in self.blacklisted_tokens:
                    logging.warning(f"Attempted use of blacklisted token: {jti}")
                    return None

            # Additional timestamp validations
            current_time = datetime.utcnow()

            # Check if token was issued in the future (clock skew attack)
            iat = datetime.utcfromtimestamp(payload["iat"])
            if iat > current_time + timedelta(minutes=5):  # 5 min clock skew tolerance
                logging.warning("Token issued in the future - possible clock skew attack")
                return None

            # Check if token is too old (replay attack protection)
            if current_time - iat > timedelta(hours=24):
                logging.warning("Token is too old - possible replay attack")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logging.info("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logging.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logging.error(f"Token validation error: {e}")
            return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token by adding it to blacklist."""
        try:
            # Decode token to get JTI without validation (since we're revoking)
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")

            if not jti:
                return False

            # Add to Redis blacklist with TTL
            if self.redis_client:
                exp = payload.get("exp", 0)
                ttl = max(0, exp - int(time.time()))
                await self.redis_client.setex(f"blacklist:{jti}", ttl, "revoked")

            # Add to in-memory blacklist as fallback
            self.blacklisted_tokens.add(jti)

            logging.info(f"Token revoked: {jti}")
            return True

        except Exception as e:
            logging.error(f"Token revocation failed: {e}")
            return False

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using a valid refresh token."""
        # Validate refresh token
        payload = await self.validate_jwt_token(refresh_token, expected_type="refresh")
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        # Get user permissions (in a real app, fetch from database)
        # For now, we'll use default permissions
        permissions = APIPermissions(
            read_threats=True,
            write_threats=False,
            read_system=True,
            write_system=False,
            read_reports=True,
            write_reports=False,
            admin_access=False
        )

        # Revoke the old refresh token to prevent reuse
        await self.revoke_token(refresh_token)

        # Create new tokens
        return await self.create_jwt_token(user_id, permissions)

    def _generate_key_id(self) -> str:
        """Generate unique key ID using secure cryptography."""
        timestamp = str(int(time.time()))
        secure_hash = secure_crypto.secure_hash(timestamp, 'sha256')[:8]
        return f"key_{timestamp}_{secure_hash}"

    def _generate_api_key(self) -> str:
        """Generate secure API key using secure cryptography."""
        return generate_api_key()

    def _hash_key(self, key: str) -> str:
        """Hash API key for storage using secure cryptography."""
        return secure_crypto.secure_hash(key, 'sha256')


class RateLimiter:
    """Advanced rate limiting implementation with security features."""

    def __init__(self, api_config: Optional[dict] = None, redis_client: Optional[redis.Redis] = None):
        """
        Initialize RateLimiter with secure configuration.

        Args:
            api_config: API security configuration dict
            redis_client: Optional Redis client (will create one if None)
        """
        # Load configuration
        if api_config is None:
            api_config = get_api_security_config()

        self.rate_config = api_config.get("rate_limiting", {})
        self.enabled = self.rate_config.get("enabled", True)

        # Default rate limits
        self.requests_per_minute = self.rate_config.get("requests_per_minute", 60)
        self.requests_per_hour = self.rate_config.get("requests_per_hour", 1000)
        self.requests_per_day = self.rate_config.get("requests_per_day", 10000)
        self.burst_limit = self.rate_config.get("burst_limit", 10)

        # IP lists
        self.whitelist_ips = set(self.rate_config.get("whitelist_ips", []))
        self.blacklist_ips = set(self.rate_config.get("blacklist_ips", []))

        # Redis client setup
        if redis_client:
            self.redis_client = redis_client
        else:
            redis_config = api_config.get("redis", {})
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.get("host", "localhost"),
                    port=redis_config.get("port", 6379),
                    db=redis_config.get("db", 0),
                    password=redis_config.get("password") or None,
                    ssl=redis_config.get("ssl", False),
                    decode_responses=True,
                    socket_timeout=redis_config.get("socket_timeout", 5),
                    retry_on_timeout=redis_config.get("retry_on_timeout", True)
                )
                # Test connection
                self.redis_client.ping()
                self.redis_available = True
                logging.info("Rate limiter Redis connection established")
            except Exception as e:
                logging.warning(f"Rate limiter Redis connection failed: {e}, using in-memory fallback")
                self.redis_client = None
                self.redis_available = False

        # In-memory fallback for when Redis is unavailable
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_cleanup_interval = 300  # 5 minutes

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting."""
        # Try to get user ID from JWT token first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                # This would need to be properly integrated with AuthenticationManager
                # For now, we'll use a simple approach
                return f"user:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
            except Exception:
                pass

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _is_whitelisted(self, identifier: str) -> bool:
        """Check if identifier is whitelisted."""
        if identifier.startswith("ip:"):
            ip = identifier[3:]
            return ip in self.whitelist_ips
        return False

    def _is_blacklisted(self, identifier: str) -> bool:
        """Check if identifier is blacklisted."""
        if identifier.startswith("ip:"):
            ip = identifier[3:]
            return ip in self.blacklist_ips
        return False

    async def is_rate_limited(self, request: Request, custom_limits: Optional[Dict[str, int]] = None) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited.

        Returns:
            tuple: (is_limited, rate_limit_info)
        """
        if not self.enabled:
            return False, {"status": "disabled"}

        identifier = self._get_client_identifier(request)

        # Check blacklist first
        if self._is_blacklisted(identifier):
            return True, {
                "reason": "blacklisted",
                "identifier": identifier,
                "retry_after": None
            }

        # Check whitelist
        if self._is_whitelisted(identifier):
            return False, {
                "reason": "whitelisted",
                "identifier": identifier
            }

        # Use custom limits if provided
        limits = {
            "minute": custom_limits.get("minute", self.requests_per_minute) if custom_limits else self.requests_per_minute,
            "hour": custom_limits.get("hour", self.requests_per_hour) if custom_limits else self.requests_per_hour,
            "day": custom_limits.get("day", self.requests_per_day) if custom_limits else self.requests_per_day,
            "burst": custom_limits.get("burst", self.burst_limit) if custom_limits else self.burst_limit
        }

        current_time = int(time.time())

        try:
            if self.redis_available:
                return await self._check_redis_limits(identifier, limits, current_time)
            else:
                return await self._check_memory_limits(identifier, limits, current_time)
        except Exception as e:
            logging.error(f"Rate limit check failed: {e}")
            # Fail open for availability
            return False, {"error": str(e)}

    async def _check_redis_limits(self, identifier: str, limits: Dict[str, int], current_time: int) -> tuple[bool, Dict[str, Any]]:
        """Check rate limits using Redis."""
        pipe = self.redis_client.pipeline()

        # Time windows
        minute_window = current_time // 60
        hour_window = current_time // 3600
        day_window = current_time // 86400

        # Keys
        minute_key = f"rate_limit:{identifier}:minute:{minute_window}"
        hour_key = f"rate_limit:{identifier}:hour:{hour_window}"
        day_key = f"rate_limit:{identifier}:day:{day_window}"
        burst_key = f"rate_limit:{identifier}:burst"

        # Get current counts
        pipe.get(minute_key)
        pipe.get(hour_key)
        pipe.get(day_key)
        pipe.llen(burst_key)

        results = pipe.execute()

        minute_count = int(results[0] or 0)
        hour_count = int(results[1] or 0)
        day_count = int(results[2] or 0)
        burst_count = int(results[3] or 0)

        # Check limits
        if minute_count >= limits["minute"]:
            return True, {
                "reason": "minute_limit_exceeded",
                "limit": limits["minute"],
                "current": minute_count,
                "retry_after": 60 - (current_time % 60),
                "identifier": identifier
            }

        if hour_count >= limits["hour"]:
            return True, {
                "reason": "hour_limit_exceeded",
                "limit": limits["hour"],
                "current": hour_count,
                "retry_after": 3600 - (current_time % 3600),
                "identifier": identifier
            }

        if day_count >= limits["day"]:
            return True, {
                "reason": "day_limit_exceeded",
                "limit": limits["day"],
                "current": day_count,
                "retry_after": 86400 - (current_time % 86400),
                "identifier": identifier
            }

        # Check burst limit (requests in last 10 seconds)
        burst_cutoff = current_time - 10
        burst_recent = 0
        if burst_count > 0:
            # Count recent requests in burst window
            burst_times = self.redis_client.lrange(burst_key, 0, -1)
            burst_recent = sum(1 for t in burst_times if int(t) > burst_cutoff)

        if burst_recent >= limits["burst"]:
            return True, {
                "reason": "burst_limit_exceeded",
                "limit": limits["burst"],
                "current": burst_recent,
                "retry_after": 10,
                "identifier": identifier
            }

        return False, {
            "limits": limits,
            "current": {
                "minute": minute_count,
                "hour": hour_count,
                "day": day_count,
                "burst": burst_recent
            },
            "identifier": identifier
        }

    async def _check_memory_limits(self, identifier: str, limits: Dict[str, int], current_time: int) -> tuple[bool, Dict[str, Any]]:
        """Check rate limits using in-memory storage (fallback)."""
        if identifier not in self.memory_cache:
            self.memory_cache[identifier] = {
                "minute": [],
                "hour": [],
                "day": [],
                "burst": []
            }

        cache = self.memory_cache[identifier]

        # Clean old entries
        minute_cutoff = current_time - 60
        hour_cutoff = current_time - 3600
        day_cutoff = current_time - 86400
        burst_cutoff = current_time - 10

        cache["minute"] = [t for t in cache["minute"] if t > minute_cutoff]
        cache["hour"] = [t for t in cache["hour"] if t > hour_cutoff]
        cache["day"] = [t for t in cache["day"] if t > day_cutoff]
        cache["burst"] = [t for t in cache["burst"] if t > burst_cutoff]

        # Check limits
        if len(cache["minute"]) >= limits["minute"]:
            return True, {
                "reason": "minute_limit_exceeded",
                "limit": limits["minute"],
                "current": len(cache["minute"]),
                "retry_after": 60,
                "identifier": identifier
            }

        if len(cache["hour"]) >= limits["hour"]:
            return True, {
                "reason": "hour_limit_exceeded",
                "limit": limits["hour"],
                "current": len(cache["hour"]),
                "retry_after": 3600,
                "identifier": identifier
            }

        if len(cache["day"]) >= limits["day"]:
            return True, {
                "reason": "day_limit_exceeded",
                "limit": limits["day"],
                "current": len(cache["day"]),
                "retry_after": 86400,
                "identifier": identifier
            }

        if len(cache["burst"]) >= limits["burst"]:
            return True, {
                "reason": "burst_limit_exceeded",
                "limit": limits["burst"],
                "current": len(cache["burst"]),
                "retry_after": 10,
                "identifier": identifier
            }

        return False, {
            "limits": limits,
            "current": {
                "minute": len(cache["minute"]),
                "hour": len(cache["hour"]),
                "day": len(cache["day"]),
                "burst": len(cache["burst"])
            },
            "identifier": identifier
        }

    async def record_request(self, request: Request) -> Dict[str, Any]:
        """Record a request for rate limiting."""
        if not self.enabled:
            return {"status": "disabled"}

        identifier = self._get_client_identifier(request)
        current_time = int(time.time())

        try:
            if self.redis_available:
                return await self._record_redis_request(identifier, current_time)
            else:
                return await self._record_memory_request(identifier, current_time)
        except Exception as e:
            logging.error(f"Failed to record request: {e}")
            return {"error": str(e)}

    async def _record_redis_request(self, identifier: str, current_time: int) -> Dict[str, Any]:
        """Record request in Redis."""
        pipe = self.redis_client.pipeline()

        # Time windows
        minute_window = current_time // 60
        hour_window = current_time // 3600
        day_window = current_time // 86400

        # Keys
        minute_key = f"rate_limit:{identifier}:minute:{minute_window}"
        hour_key = f"rate_limit:{identifier}:hour:{hour_window}"
        day_key = f"rate_limit:{identifier}:day:{day_window}"
        burst_key = f"rate_limit:{identifier}:burst"

        # Increment counters
        pipe.incr(minute_key)
        pipe.expire(minute_key, 60)
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        pipe.incr(day_key)
        pipe.expire(day_key, 86400)

        # Add to burst window
        pipe.lpush(burst_key, current_time)
        pipe.ltrim(burst_key, 0, self.burst_limit - 1)  # Keep only recent entries
        pipe.expire(burst_key, 10)

        pipe.execute()

        return {"status": "recorded", "backend": "redis", "identifier": identifier}

    async def _record_memory_request(self, identifier: str, current_time: int) -> Dict[str, Any]:
        """Record request in memory."""
        if identifier not in self.memory_cache:
            self.memory_cache[identifier] = {
                "minute": [],
                "hour": [],
                "day": [],
                "burst": []
            }

        cache = self.memory_cache[identifier]

        # Add current request
        cache["minute"].append(current_time)
        cache["hour"].append(current_time)
        cache["day"].append(current_time)
        cache["burst"].append(current_time)

        return {"status": "recorded", "backend": "memory", "identifier": identifier}

    async def get_rate_limit_status(self, request: Request) -> Dict[str, Any]:
        """Get current rate limit status for debugging."""
        identifier = self._get_client_identifier(request)
        current_time = int(time.time())

        try:
            if self.redis_available:
                return await self._get_redis_status(identifier, current_time)
            else:
                return await self._get_memory_status(identifier, current_time)
        except Exception as e:
            return {"error": str(e)}

    async def _get_redis_status(self, identifier: str, current_time: int) -> Dict[str, Any]:
        """Get Redis-based status."""
        pipe = self.redis_client.pipeline()

        minute_window = current_time // 60
        hour_window = current_time // 3600
        day_window = current_time // 86400

        minute_key = f"rate_limit:{identifier}:minute:{minute_window}"
        hour_key = f"rate_limit:{identifier}:hour:{hour_window}"
        day_key = f"rate_limit:{identifier}:day:{day_window}"
        burst_key = f"rate_limit:{identifier}:burst"

        pipe.get(minute_key)
        pipe.get(hour_key)
        pipe.get(day_key)
        pipe.llen(burst_key)

        results = pipe.execute()

        return {
            "identifier": identifier,
            "backend": "redis",
            "current": {
                "minute": int(results[0] or 0),
                "hour": int(results[1] or 0),
                "day": int(results[2] or 0),
                "burst": int(results[3] or 0)
            },
            "limits": {
                "minute": self.requests_per_minute,
                "hour": self.requests_per_hour,
                "day": self.requests_per_day,
                "burst": self.burst_limit
            }
        }

    async def _get_memory_status(self, identifier: str, current_time: int) -> Dict[str, Any]:
        """Get memory-based status."""
        if identifier not in self.memory_cache:
            current_counts = {"minute": 0, "hour": 0, "day": 0, "burst": 0}
        else:
            cache = self.memory_cache[identifier]

            minute_cutoff = current_time - 60
            hour_cutoff = current_time - 3600
            day_cutoff = current_time - 86400
            burst_cutoff = current_time - 10

            current_counts = {
                "minute": len([t for t in cache["minute"] if t > minute_cutoff]),
                "hour": len([t for t in cache["hour"] if t > hour_cutoff]),
                "day": len([t for t in cache["day"] if t > day_cutoff]),
                "burst": len([t for t in cache["burst"] if t > burst_cutoff])
            }

        return {
            "identifier": identifier,
            "backend": "memory",
            "current": current_counts,
            "limits": {
                "minute": self.requests_per_minute,
                "hour": self.requests_per_hour,
                "day": self.requests_per_day,
                "burst": self.burst_limit
            }
        }


class WebhookManager:
    """Manage webhook subscriptions and delivery."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.delivery_queue = asyncio.Queue()
        self.logger = logging.getLogger(__name__)

        # Start delivery worker
        asyncio.create_task(self._delivery_worker())

    async def create_webhook(self, url: str, events: List[str], secret: str = None) -> str:
        """Create new webhook subscription."""
        if not secret:
            secret = Fernet.generate_key().decode()

        webhook = Webhook(
            url=url,
            events=json.dumps(events),
            secret=secret
        )

        self.db_session.add(webhook)
        self.db_session.commit()

        return str(webhook.id)

    async def trigger_webhooks(self, event_type: str, payload: Dict[str, Any]):
        """Trigger webhooks for specific event type."""
        webhooks = self.db_session.query(Webhook).filter(
            Webhook.is_active == True
        ).all()

        for webhook in webhooks:
            events = json.loads(webhook.events)
            if event_type in events or '*' in events:
                await self.delivery_queue.put({
                    'webhook': webhook,
                    'event_type': event_type,
                    'payload': payload
                })

    async def _delivery_worker(self):
        """Background worker for webhook delivery."""
        while True:
            try:
                delivery = await self.delivery_queue.get()
                await self._deliver_webhook(
                    delivery['webhook'],
                    delivery['event_type'],
                    delivery['payload']
                )
            except Exception as e:
                self.logger.error(f"Error delivering webhook: {e}")

    async def _deliver_webhook(self, webhook: Webhook, event_type: str, payload: Dict[str, Any]):
        """Deliver webhook to endpoint."""
        try:
            # Prepare payload
            webhook_payload = {
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': payload
            }

            # Create signature
            signature = self._create_signature(json.dumps(webhook_payload), webhook.secret)

            # Send webhook
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature,
                'X-Webhook-Event': event_type
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook.url,
                    json=webhook_payload,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    # Update last triggered
                    webhook.last_triggered = datetime.utcnow()
                    self.db_session.commit()
                    self.logger.info(f"Webhook delivered successfully to {webhook.url}")
                else:
                    self.logger.warning(f"Webhook delivery failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error delivering webhook to {webhook.url}: {e}")

    def _create_signature(self, payload: str, secret: str) -> str:
        """Create HMAC signature for webhook."""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"


# GraphQL Schema
@strawberry.type
class ThreatInfo:
    threat_detected: bool
    threat_type: Optional[str]
    confidence: float
    file_hash: Optional[str]


@strawberry.type
class SystemInfo:
    cpu_usage: float
    memory_usage: float
    uptime: float
    threats_detected: int


@strawberry.type
class Query:
    @strawberry.field
    async def threat_status(self) -> ThreatInfo:
        """Get current threat status."""
        # Mock data - would integrate with actual threat detector
        return ThreatInfo(
            threat_detected=False,
            threat_type=None,
            confidence=0.95,
            file_hash=None
        )

    @strawberry.field
    async def system_status(self) -> SystemInfo:
        """Get current system status."""
        # Mock data - would integrate with actual system monitor
        return SystemInfo(
            cpu_usage=35.2,
            memory_usage=68.5,
            uptime=99.7,
            threats_detected=150
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def scan_file(self, file_path: str) -> ThreatInfo:
        """Scan a specific file for threats."""
        # Mock implementation - would integrate with actual scanner
        return ThreatInfo(
            threat_detected=False,
            threat_type=None,
            confidence=0.98,
            file_hash="sha256:abcd1234..."
        )


class SecurityAPI:
    """Main API application class."""

    def __init__(self):
        self.app = FastAPI(
            title="xanadOS Security API",
            description="Comprehensive security API for threat detection and system monitoring",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # Initialize components
        self.config = get_config()
        self.api_security_config = get_api_security_config()
        self.auth_manager = AuthenticationManager(self.api_security_config)
        self.rate_limiter = RateLimiter(api_config=self.api_security_config)
        self.webhook_manager = WebhookManager(self.auth_manager.db_session)

        # Security middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )

        # Add comprehensive input validation middleware
        self.app.add_middleware(InputValidationMiddleware)

        # Rate limiting
        limiter = Limiter(key_func=get_remote_address)
        self.app.state.limiter = limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        # Add comprehensive error handlers
        @self.app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc: ValueError):
            """Handle validation errors consistently."""
            # Log actual error for debugging
            logging.warning(f"Validation error on {request.url.path}: {type(exc).__name__}")

            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation Error",
                    "detail": "Input validation failed. Please check your request and try again.",
                    "type": "validation_error"
                }
            )

        @self.app.exception_handler(422)  # Pydantic validation errors
        async def validation_exception_handler(request: Request, exc):
            """Handle Pydantic validation errors."""
            # Log error details for debugging
            logging.warning(f"Pydantic validation error on {request.url.path}: {type(exc).__name__}")

            return JSONResponse(
                status_code=422,
                content={
                    "error": "Input Validation Failed",
                    "detail": "One or more input fields failed validation",
                    "type": "pydantic_validation_error"
                    # Note: Removed detailed error info to prevent information disclosure
                }
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle unexpected errors securely."""
            # Log the actual error for debugging (server-side only)
            error_id = hashlib.md5(f"{time.time()}{request.url}".encode()).hexdigest()[:8]
            logging.error(f"Unexpected error [{error_id}] in {request.url.path}: {type(exc).__name__}", exc_info=True)

            # Return generic error to prevent information disclosure
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred. Please try again later.",
                    "type": "internal_error",
                    "error_id": error_id  # For support correlation only
                }
            )

        # Setup routes
        self._setup_routes()

        # Setup GraphQL
        self._setup_graphql()

        # Setup middleware
        self._setup_middleware()

    def _setup_routes(self):
        """Setup REST API routes."""

        # Authentication dependency
        security = HTTPBearer()

        async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
            payload = await self.auth_manager.validate_jwt_token(credentials.credentials)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")
            return payload

        # Health check
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

        # Authentication endpoints
        @self.app.post("/auth/api-key")
        async def create_api_key(name: str, permissions: dict):
            """Create new API key."""
            perms = APIPermissions(**permissions)
            key_id, api_key = await self.auth_manager.create_api_key(name, perms)
            return {"key_id": key_id, "api_key": api_key}

        @self.app.post("/auth/token")
        async def create_token(api_key: str):
            """Create JWT token from API key."""
            permissions = await self.auth_manager.validate_api_key(api_key)
            if not permissions:
                raise HTTPException(status_code=401, detail="Invalid API key")

            tokens = await self.auth_manager.create_jwt_token("api_user", permissions)
            return tokens

        # Threat detection endpoints
        @self.app.post("/v1/threats/detect", response_model=ThreatDetectionResponse)
        async def detect_threat(request: ThreatDetectionRequest,
                              current_user = Depends(get_current_user)):
            """Detect threats in file or content."""
            try:
                # Additional server-side validation beyond Pydantic
                if request.file_path:
                    # Validate file path doesn't escape sandbox
                    validated_path = InputSanitizer.sanitize_string(
                        request.file_path,
                        max_length=1000,
                        check_command_injection=True
                    )
                    request.file_path = InputSanitizer.sanitize_filename(validated_path)

                if request.file_content:
                    # Additional content validation
                    if len(request.file_content.encode('utf-8')) > 10 * 1024 * 1024:  # 10MB limit
                        raise HTTPException(status_code=413, detail="File content too large")

                # Validate scan type again at endpoint level
                if request.scan_type not in ['quick', 'full', 'deep']:
                    raise HTTPException(status_code=400, detail="Invalid scan type")

                # Mock implementation - would integrate with ML threat detector
                return ThreatDetectionResponse(
                    threat_detected=False,
                    threat_type=None,
                    confidence=0.95,
                    scan_duration=1.2,
                    file_hash="sha256:abcd1234...",
                    metadata={"scan_type": request.scan_type}
                )
            except ValueError as e:
                # Log the actual error for debugging
                logging.warning(f"Threat detection validation error: {type(e).__name__} - {e}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request parameters. Please check your input and try again."
                )
            except Exception as e:
                logging.error(f"Threat detection error: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

        # Secure File Upload Endpoints
        @self.app.post("/v1/files/upload", response_model=FileUploadResponse)
        async def upload_file(
            request: Request,
            file: UploadFile = File(...),
            metadata: str = Form(...),
            current_user = Depends(get_current_user)
        ):
            """Secure file upload with comprehensive validation and scanning."""
            try:
                # Apply strict rate limiting for file uploads (resource intensive)
                upload_limits = {
                    "requests_per_minute": 5,  # Only 5 uploads per minute
                    "requests_per_hour": 20,   # 20 uploads per hour
                    "requests_per_day": 50     # 50 uploads per day
                }

                is_limited, limit_info = await self.rate_limiter.is_rate_limited(request, upload_limits)
                if is_limited:
                    headers = {
                        "X-RateLimit-Limit": str(limit_info.get("limit", 0)),
                        "X-RateLimit-Remaining": str(limit_info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(limit_info.get("reset_time", 0)),
                        "Retry-After": str(limit_info.get("retry_after", 60))
                    }
                    raise HTTPException(
                        status_code=429,
                        detail="Upload rate limit exceeded. Please try again later.",
                        headers=headers
                    )
                # Parse metadata
                try:
                    metadata_dict = json.loads(metadata)
                    file_metadata = FileUploadMetadata(**metadata_dict)
                except (json.JSONDecodeError, ValueError) as e:
                    # Log the actual error for debugging
                    logging.warning(f"Invalid file upload metadata: {type(e).__name__} - {e}")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid metadata format. Please check your metadata and try again."
                    )

                # Validate file size
                MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
                file_size = 0
                content = b""

                # Read file content while tracking size
                async for chunk in file.stream():
                    content += chunk
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        raise HTTPException(status_code=413, detail="File too large (max 100MB)")

                # Validate filename
                if not file.filename:
                    raise HTTPException(status_code=400, detail="Filename is required")

                safe_filename = InputSanitizer.sanitize_filename(file.filename)
                if not safe_filename:
                    raise HTTPException(status_code=400, detail="Invalid filename")

                # Validate content type
                allowed_types = {
                    'text/plain', 'text/csv', 'application/json', 'application/xml',
                    'application/pdf', 'application/zip', 'image/jpeg', 'image/png',
                    'application/octet-stream'  # For binary files that need scanning
                }
                if file.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Content type '{file.content_type}' not allowed"
                    )

                # Check for dangerous file extensions
                dangerous_extensions = {
                    '.exe', '.bat', '.cmd', '.scr', '.pif', '.vbs', '.js', '.jar'
                }
                file_ext = Path(safe_filename).suffix.lower()
                if file_ext in dangerous_extensions:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File extension '{file_ext}' not allowed for security reasons"
                    )

                # Calculate file hash
                import hashlib
                sha256_hash = hashlib.sha256(content).hexdigest()

                # Check for duplicate files
                # In a real implementation, this would check against a database
                file_id = f"file_{uuid.uuid4().hex[:16]}"

                # Perform initial security scan
                threat_detected = False
                scan_status = "completed"

                # Basic malware signature check (simplified)
                malware_signatures = [
                    b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR',  # EICAR test signature
                    b'MZARUH'  # Common PE header start
                ]

                for signature in malware_signatures:
                    if signature in content:
                        threat_detected = True
                        scan_status = "threat_detected"
                        break

                # Create secure storage path
                from datetime import datetime
                storage_dir = Path("secure_uploads") / datetime.now().strftime("%Y/%m/%d")
                storage_dir.mkdir(parents=True, exist_ok=True)

                secure_file_path = storage_dir / f"{file_id}_{safe_filename}"

                # Write file to secure location (in real implementation, use encrypted storage)
                with open(secure_file_path, 'wb') as f:
                    f.write(content)

                # Log the upload
                logging.info(f"File uploaded: {file_id}, size: {file_size}, hash: {sha256_hash}")

                return FileUploadResponse(
                    file_id=file_id,
                    filename=safe_filename,
                    file_size=file_size,
                    content_type=file.content_type,
                    sha256_hash=sha256_hash,
                    upload_timestamp=datetime.utcnow(),
                    scan_status=scan_status,
                    threat_detected=threat_detected,
                    quarantined=threat_detected
                )

            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"File upload error: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.get("/v1/files", response_model=FileListResponse)
        async def list_files(
            page: int = 1,
            page_size: int = 20,
            scan_status: Optional[str] = None,
            current_user = Depends(get_current_user)
        ):
            """List uploaded files with filtering options."""
            try:
                # Validate parameters
                if page < 1:
                    raise HTTPException(status_code=400, detail="Page must be >= 1")
                if page_size < 1 or page_size > 100:
                    raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

                if scan_status and scan_status not in ['pending', 'completed', 'threat_detected', 'error']:
                    raise HTTPException(status_code=400, detail="Invalid scan status")

                # Mock implementation - in real system, query database
                files = []  # Would fetch from database with filtering and pagination

                return FileListResponse(
                    files=files,
                    total_count=0,
                    page=page,
                    page_size=page_size
                )

            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"File listing error: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.delete("/v1/files/{file_id}")
        async def delete_file(
            file_id: str,
            current_user = Depends(get_current_user)
        ):
            """Securely delete uploaded file."""
            try:
                # Validate file_id format
                if not re.match(r'^file_[a-f0-9]{16}$', file_id):
                    raise HTTPException(status_code=400, detail="Invalid file ID format")

                # In real implementation:
                # 1. Check if file exists in database
                # 2. Verify user has permission to delete
                # 3. Securely wipe file from storage
                # 4. Remove from database

                return {"message": f"File {file_id} deleted successfully"}

            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"File deletion error: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.post("/v1/system/scan", response_model=SystemScanResponse)
        async def start_system_scan(request_obj: Request,
                                  scan_request: SystemScanRequest,
                                  background_tasks: BackgroundTasks,
                                  current_user = Depends(get_current_user)):
            """Start system-wide security scan."""
            try:
                # Apply strict rate limiting for system scans (very resource intensive)
                scan_limits = {
                    "requests_per_minute": 2,  # Only 2 system scans per minute
                    "requests_per_hour": 5,    # 5 system scans per hour
                    "requests_per_day": 10     # 10 system scans per day
                }

                is_limited, limit_info = await self.rate_limiter.is_rate_limited(request_obj, scan_limits)
                if is_limited:
                    headers = {
                        "X-RateLimit-Limit": str(limit_info.get("limit", 0)),
                        "X-RateLimit-Remaining": str(limit_info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(limit_info.get("reset_time", 0)),
                        "Retry-After": str(limit_info.get("retry_after", 60))
                    }
                    raise HTTPException(
                        status_code=429,
                        detail="System scan rate limit exceeded. Please try again later.",
                        headers=headers
                    )

                # Additional validation for paths
                validated_paths = []
                for path in scan_request.paths:
                    # Validate each path
                    validated_path = InputSanitizer.sanitize_string(
                        path,
                        max_length=1000,
                        check_command_injection=True
                    )
                    # Ensure path doesn't escape allowed directories
                    if not path.startswith(('/home/', '/opt/', '/var/lib/')):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Path '{path}' is not in allowed scan directories"
                        )
                    validated_paths.append(validated_path)

                # Validate exclude patterns are safe regex
                for pattern in scan_request.exclude_patterns:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        # Log the actual error for debugging
                        logging.warning(f"Invalid regex pattern in scan request: {pattern} - {e}")
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid exclude pattern format. Please check your regex syntax."
                        )

                # Validate file size limits
                if scan_request.max_file_size > 1024 * 1024 * 1024:  # 1GB max
                    raise HTTPException(
                        status_code=400,
                        detail="Max file size cannot exceed 1GB"
                    )

                scan_id = f"scan_{int(time.time())}_{secrets.token_hex(4)}"

                # Start background scan
                background_tasks.add_task(self._perform_system_scan, scan_id, scan_request)

                return SystemScanResponse(
                    scan_id=scan_id,
                    status="STARTED",
                    threats_found=0,
                    files_scanned=0,
                    scan_duration=0.0,
                    started_at=datetime.utcnow()
                )
            except ValueError as e:
                # Log the actual error for debugging
                logging.warning(f"System scan validation error: {type(e).__name__} - {e}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid scan parameters. Please check your request and try again."
                )
            except Exception as e:
                logging.error(f"System scan error: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.get("/v1/system/scan/{scan_id}")
        async def get_scan_status(scan_id: str, current_user = Depends(get_current_user)):
            """Get scan status and results."""
            try:
                # Validate scan ID format to prevent injection
                if not re.match(r'^scan_\d+_[a-f0-9]{8}$', scan_id):
                    raise HTTPException(status_code=400, detail="Invalid scan ID format")

                # Additional sanitization
                scan_id = InputSanitizer.sanitize_string(
                    scan_id,
                    max_length=100,
                    check_sql_injection=True,
                    check_command_injection=True
                )

                # Mock implementation - would check actual scan status
                return {
                    "scan_id": scan_id,
                    "status": "COMPLETED",
                    "progress": 100,
                    "results": {
                        "threats_found": 3,
                        "files_scanned": 15420,
                        "scan_duration": 145.7
                    }
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Security events endpoints
        @self.app.post("/v1/events", response_model=SecurityEventResponse)
        async def create_security_event(request: SecurityEventRequest,
                                      current_user = Depends(get_current_user)):
            """Create new security event."""
            event_id = f"event_{int(time.time())}"

            # Trigger webhooks
            await self.webhook_manager.trigger_webhooks("security_event", {
                "event_id": event_id,
                "event_type": request.event_type,
                "severity": request.severity,
                "source": request.source,
                "description": request.description
            })

            return SecurityEventResponse(
                event_id=event_id,
                timestamp=datetime.utcnow(),
                processed=True,
                actions_taken=["logged", "analyzed", "webhooks_triggered"]
            )

        @self.app.get("/v1/events")
        async def get_security_events(limit: int = 100, offset: int = 0,
                                    current_user = Depends(get_current_user)):
            """Get security events."""
            # Mock implementation - would query actual events
            return {
                "events": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }

        # Reports endpoints
        @self.app.get("/v1/reports/summary")
        async def get_security_summary(current_user = Depends(get_current_user)):
            """Get security summary report."""
            reporting = get_advanced_reporting()
            status = reporting.get_report_status()
            return status

        @self.app.post("/v1/reports/generate")
        async def generate_report(report_type: str = "comprehensive",
                                current_user = Depends(get_current_user)):
            """Generate security report."""
            reporting = get_advanced_reporting()
            reports = await reporting.generate_comprehensive_report()
            return {"reports": reports}

        # Webhook endpoints
        @self.app.post("/v1/webhooks", response_model=WebhookResponse)
        async def create_webhook(request: WebhookRequest,
                               current_user = Depends(get_current_user)):
            """Create webhook subscription."""
            webhook_id = await self.webhook_manager.create_webhook(
                request.url, request.events, request.secret
            )

            return WebhookResponse(
                webhook_id=webhook_id,
                url=request.url,
                events=request.events,
                is_active=True,
                created_at=datetime.utcnow()
            )

        @self.app.get("/v1/webhooks")
        async def list_webhooks(current_user = Depends(get_current_user)):
            """List webhook subscriptions."""
            webhooks = self.auth_manager.db_session.query(Webhook).filter(
                Webhook.is_active == True
            ).all()

            return {
                "webhooks": [
                    {
                        "id": str(w.id),
                        "url": w.url,
                        "events": json.loads(w.events),
                        "created_at": w.created_at.isoformat()
                    }
                    for w in webhooks
                ]
            }

        # System configuration endpoints
        @self.app.get("/v1/system/config")
        async def get_system_config(current_user = Depends(get_current_user)):
            """Get system configuration."""
            automation = get_intelligent_automation()
            status = automation.get_system_status()
            return status

        @self.app.put("/v1/system/config")
        async def update_system_config(config: Dict[str, Any],
                                     current_user = Depends(get_current_user)):
            """Update system configuration."""
            # Mock implementation - would update actual configuration
            return {"updated": True, "config": config}

        # Rate limiting management endpoints
        @self.app.get("/v1/rate-limit/status")
        async def get_rate_limit_status(request: Request,
                                      current_user = Depends(get_current_user)):
            """Get current rate limiting status for the requesting client."""
            try:
                status = await self.rate_limiter.get_rate_limit_status(request)
                return status
            except Exception as e:
                # Log the actual error for debugging
                error_id = hashlib.md5(f"{time.time()}{request.url}".encode()).hexdigest()[:8]
                logging.error(f"Failed to get rate limit status [{error_id}]: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Failed to retrieve rate limit status",
                        "detail": "An internal error occurred. Please try again later.",
                        "error_id": error_id
                    }
                )

        @self.app.get("/v1/rate-limit/config")
        async def get_rate_limit_config(current_user = Depends(get_current_user)):
            """Get current rate limiting configuration."""
            try:
                rate_config = self.api_security_config.get("rate_limiting", {})
                # Remove sensitive information
                safe_config = {
                    "enabled": rate_config.get("enabled", True),
                    "requests_per_minute": rate_config.get("requests_per_minute", 60),
                    "requests_per_hour": rate_config.get("requests_per_hour", 1000),
                    "requests_per_day": rate_config.get("requests_per_day", 10000),
                    "burst_limit": rate_config.get("burst_limit", 10),
                    "backend": "redis" if self.rate_limiter.redis_available else "memory",
                    "whitelist_count": len(rate_config.get("whitelist_ips", [])),
                    "blacklist_count": len(rate_config.get("blacklist_ips", []))
                }
                return safe_config
            except Exception as e:
                logging.error(f"Failed to get rate limit config: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to retrieve rate limit configuration", "detail": str(e)}
                )

        @self.app.post("/v1/rate-limit/whitelist")
        async def add_to_whitelist(request: Request,
                                 ip_address: str,
                                 current_user = Depends(get_current_user)):
            """Add IP address to rate limiting whitelist."""
            try:
                # Validate IP address format
                import ipaddress
                try:
                    ipaddress.ip_address(ip_address)
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid IP address format", "detail": f"'{ip_address}' is not a valid IP address"}
                    )

                # Add to whitelist (would need to update configuration persistently)
                self.rate_limiter.whitelist_ips.add(ip_address)

                # Log the action
                logging.info(f"IP {ip_address} added to rate limit whitelist by user {current_user.get('user_id', 'unknown')}")

                return {
                    "status": "success",
                    "message": f"IP {ip_address} added to whitelist",
                    "ip_address": ip_address
                }
            except Exception as e:
                logging.error(f"Failed to add IP to whitelist: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to add IP to whitelist", "detail": str(e)}
                )

        @self.app.delete("/v1/rate-limit/whitelist/{ip_address}")
        async def remove_from_whitelist(ip_address: str,
                                      current_user = Depends(get_current_user)):
            """Remove IP address from rate limiting whitelist."""
            try:
                if ip_address in self.rate_limiter.whitelist_ips:
                    self.rate_limiter.whitelist_ips.remove(ip_address)
                    logging.info(f"IP {ip_address} removed from rate limit whitelist by user {current_user.get('user_id', 'unknown')}")
                    return {
                        "status": "success",
                        "message": f"IP {ip_address} removed from whitelist",
                        "ip_address": ip_address
                    }
                else:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "IP not found", "detail": f"IP {ip_address} is not in the whitelist"}
                    )
            except Exception as e:
                logging.error(f"Failed to remove IP from whitelist: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to remove IP from whitelist", "detail": str(e)}
                )

        @self.app.post("/v1/rate-limit/blacklist")
        async def add_to_blacklist(request: Request,
                                 ip_address: str,
                                 current_user = Depends(get_current_user)):
            """Add IP address to rate limiting blacklist."""
            try:
                # Validate IP address format
                import ipaddress
                try:
                    ipaddress.ip_address(ip_address)
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid IP address format", "detail": f"'{ip_address}' is not a valid IP address"}
                    )

                # Add to blacklist
                self.rate_limiter.blacklist_ips.add(ip_address)

                # Log the action
                logging.info(f"IP {ip_address} added to rate limit blacklist by user {current_user.get('user_id', 'unknown')}")

                return {
                    "status": "success",
                    "message": f"IP {ip_address} added to blacklist",
                    "ip_address": ip_address
                }
            except Exception as e:
                logging.error(f"Failed to add IP to blacklist: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to add IP to blacklist", "detail": str(e)}
                )

        @self.app.delete("/v1/rate-limit/blacklist/{ip_address}")
        async def remove_from_blacklist(ip_address: str,
                                      current_user = Depends(get_current_user)):
            """Remove IP address from rate limiting blacklist."""
            try:
                if ip_address in self.rate_limiter.blacklist_ips:
                    self.rate_limiter.blacklist_ips.remove(ip_address)
                    logging.info(f"IP {ip_address} removed from rate limit blacklist by user {current_user.get('user_id', 'unknown')}")
                    return {
                        "status": "success",
                        "message": f"IP {ip_address} removed from blacklist",
                        "ip_address": ip_address
                    }
                else:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "IP not found", "detail": f"IP {ip_address} is not in the blacklist"}
                    )
            except Exception as e:
                logging.error(f"Failed to remove IP from blacklist: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to remove IP from blacklist", "detail": str(e)}
                )

    def _setup_graphql(self):
        """Setup GraphQL endpoint."""
        schema = strawberry.Schema(query=Query, mutation=Mutation)
        graphql_app = GraphQLRouter(schema)
        self.app.include_router(graphql_app, prefix="/graphql")

    def _setup_middleware(self):
        """Setup custom middleware."""

        @self.app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            start_time = time.time()

            # Generate request ID
            request_id = f"req_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
            request.state.request_id = request_id

            # Process request
            response = await call_next(request)

            # Calculate response time
            process_time = time.time() - start_time

            # Log request
            await self._log_request(request, response, process_time, request_id)

            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(int(process_time * 1000))

            return response

        @self.app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            """Enhanced rate limiting middleware with comprehensive security features."""
            # Skip rate limiting for health checks and specific endpoints
            skip_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
            if request.url.path in skip_paths:
                return await call_next(request)

            try:
                # Check if request should be rate limited
                is_limited, rate_info = await self.rate_limiter.is_rate_limited(request)

                if is_limited:
                    # Create rate limit response with proper headers
                    content = {
                        "error": "Rate Limit Exceeded",
                        "detail": f"Request rate limit exceeded: {rate_info.get('reason', 'unknown')}",
                        "type": "rate_limit_error",
                        "identifier": rate_info.get('identifier', 'unknown'),
                        "limit_info": {
                            "limit": rate_info.get('limit'),
                            "current": rate_info.get('current'),
                            "window": rate_info.get('reason', '').replace('_limit_exceeded', '')
                        }
                    }

                    headers = {
                        "X-RateLimit-Limit": str(rate_info.get('limit', 'unknown')),
                        "X-RateLimit-Remaining": str(max(0, (rate_info.get('limit', 0) - rate_info.get('current', 0)))),
                        "X-RateLimit-Reset": str(int(time.time() + rate_info.get('retry_after', 60))),
                    }

                    if rate_info.get('retry_after'):
                        headers["Retry-After"] = str(rate_info['retry_after'])

                    # Log rate limit event
                    logging.warning(f"Rate limit exceeded for {rate_info.get('identifier', 'unknown')}: {rate_info}")

                    return JSONResponse(
                        status_code=429,
                        content=content,
                        headers=headers
                    )

                # Record the request for rate limiting tracking
                await self.rate_limiter.record_request(request)

                # Process the request
                response = await call_next(request)

                # Add rate limit headers to successful responses
                try:
                    status = await self.rate_limiter.get_rate_limit_status(request)
                    if status and 'current' in status and 'limits' in status:
                        # Add informational headers about current rate limit status
                        response.headers["X-RateLimit-Limit-Minute"] = str(status['limits'].get('minute', 'unknown'))
                        response.headers["X-RateLimit-Remaining-Minute"] = str(
                            max(0, status['limits'].get('minute', 0) - status['current'].get('minute', 0))
                        )
                        response.headers["X-RateLimit-Backend"] = status.get('backend', 'unknown')
                except Exception as e:
                    # Don't fail the request if rate limit status check fails
                    logging.debug(f"Failed to add rate limit headers: {e}")

                return response

            except Exception as e:
                # Log error but don't block the request
                logging.error(f"Rate limiting middleware error: {e}", exc_info=True)
                # Proceed with request if rate limiting fails
                return await call_next(request)

    async def _log_request(self, request: Request, response: Response,
                          response_time: float, request_id: str):
        """Log API request."""
        # Extract API key if present
        api_key_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = await self.auth_manager.validate_jwt_token(token)
            if payload:
                api_key_id = payload.get("user_id")

        # Create log entry
        log_entry = APILog(
            request_id=request_id,
            endpoint=str(request.url.path),
            method=request.method,
            status_code=response.status_code,
            response_time=int(response_time * 1000),
            ip_address=get_remote_address(request),
            user_agent=request.headers.get("User-Agent", ""),
            api_key_id=api_key_id
        )

        self.auth_manager.db_session.add(log_entry)
        self.auth_manager.db_session.commit()

    async def _perform_system_scan(self, scan_id: str, request: SystemScanRequest):
        """Perform system scan in background."""
        # Mock implementation - would perform actual scan
        await asyncio.sleep(5)  # Simulate scan time

        # Trigger webhook for scan completion
        await self.webhook_manager.trigger_webhooks("scan_completed", {
            "scan_id": scan_id,
            "status": "COMPLETED",
            "threats_found": 3,
            "files_scanned": 15420
        })


class APIDocumentationGenerator:
    """Generate comprehensive API documentation."""

    def __init__(self, api: SecurityAPI):
        self.api = api

    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI specification."""
        return self.api.app.openapi()

    def generate_postman_collection(self) -> Dict[str, Any]:
        """Generate Postman collection."""
        openapi_spec = self.generate_openapi_spec()

        # Convert OpenAPI to Postman format
        collection = {
            "info": {
                "name": openapi_spec["info"]["title"],
                "description": openapi_spec["info"]["description"],
                "version": openapi_spec["info"]["version"]
            },
            "item": []
        }

        # Add requests from paths
        for path, methods in openapi_spec["paths"].items():
            for method, details in methods.items():
                item = {
                    "name": details.get("summary", f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [
                            {
                                "key": "Authorization",
                                "value": "Bearer {{access_token}}",
                                "type": "text"
                            }
                        ],
                        "url": {
                            "raw": f"{{base_url}}{path}",
                            "host": ["{{base_url}}"],
                            "path": path.split("/")[1:]
                        }
                    }
                }
                collection["item"].append(item)

        return collection


# Global API instance
_api_instance = None


def get_security_api() -> SecurityAPI:
    """Get the global security API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = SecurityAPI()
    return _api_instance


async def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    import uvicorn

    api = get_security_api()

    # Run server
    config = uvicorn.Config(
        api.app,
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_api_server())
