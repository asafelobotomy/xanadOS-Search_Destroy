#!/usr/bin/env python3
"""xanadOS Security API Client SDK.

This module provides a comprehensive Python SDK for integrating with the
xanadOS Security API, offering both synchronous and asynchronous clients
with full feature coverage.

Features:
- Comprehensive API client with all endpoints
- Automatic authentication and token management
- Rate limiting and retry logic
- WebSocket support for real-time updates
- Webhook integration helpers
- Response caching and optimization
- Error handling and logging
- Type hints and documentation
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from pathlib import Path

import httpx
import websockets
from cryptography.fernet import Fernet

from app.utils.secure_crypto import secure_crypto
from app.core.exceptions import (
    NetworkError,
    AuthenticationError,
    ValidationError,
    FileIOError,
    SystemError
)


@dataclass
class APIConfig:
    """API client configuration."""
    base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    timeout: int = 30
    retries: int = 3
    retry_delay: float = 1.0
    cache_ttl: int = 300  # 5 minutes


@dataclass
class ThreatDetectionResult:
    """Threat detection result."""
    threat_detected: bool
    threat_type: Optional[str]
    confidence: float
    scan_duration: float
    file_hash: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class SystemScanResult:
    """System scan result."""
    scan_id: str
    status: str
    threats_found: int
    files_scanned: int
    scan_duration: float
    started_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class SecurityEvent:
    """Security event data."""
    event_id: str
    event_type: str
    severity: str
    source: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class WebhookSubscription:
    """Webhook subscription data."""
    webhook_id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime


class SecurityAPIClient:
    """Comprehensive API client for xanadOS Security API."""

    def __init__(self, config: APIConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._session: Optional[httpx.AsyncClient] = None
        self._token_expires: Optional[datetime] = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def __aenter__(self) -> "SecurityAPIClient":
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """Async context manager exit."""
        if self._session:
            await self._session.aclose()

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is available."""
        if not self._session:
            self._session = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )

    async def _ensure_token(self) -> None:
        """Ensure valid access token is available."""
        if not self.config.access_token or self._token_expired():
            if self.config.api_key:
                await self._refresh_token()
            else:
                raise ValueError("No API key or access token provided")

    def _token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self._token_expires:
            return True
        return datetime.utcnow() >= self._token_expires

    async def _refresh_token(self) -> None:
        """Refresh access token using API key."""
        await self._ensure_session()  # Ensure session exists
        if self._session is None:
            raise ValueError("Failed to initialize HTTP session")

        try:
            response = await self._session.post(
                "/auth/token",
                json={"api_key": self.config.api_key}
            )
            response.raise_for_status()

            token_data = response.json()
            self.config.access_token = token_data["access_token"]

            # Set expiration time
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)

            self.logger.info("Access token refreshed successfully")

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            self.logger.error(f"HTTP error refreshing token: {e}")
            raise NetworkError(f"Failed to refresh token due to network error: {e}", cause=e)
        except KeyError as e:
            self.logger.error(f"Missing required field in token response: {e}")
            raise AuthenticationError(f"Invalid token response format: missing {e}", cause=e)
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid token data format: {e}")
            raise AuthenticationError(f"Invalid token data received: {e}", cause=e)

    async def _make_request(self, method: str, endpoint: str,
                          **kwargs: Any) -> httpx.Response:
        """Make authenticated API request with retry logic."""
        await self._ensure_session()
        await self._ensure_token()

        if self._session is None:
            raise ValueError("Failed to initialize HTTP session")

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.config.access_token}"

        for attempt in range(self.config.retries + 1):
            try:
                response = await self._session.request(
                    method, endpoint, headers=headers, **kwargs
                )

                if response.status_code == 401:
                    # Token might be expired, refresh and retry
                    await self._refresh_token()
                    headers["Authorization"] = f"Bearer {self.config.access_token}"
                    continue

                response.raise_for_status()
                return response

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == self.config.retries:
                    raise NetworkError(
                        f"Request failed after {self.config.retries + 1} attempts: {e}",
                        cause=e,
                        context={
                            "method": method,
                            "endpoint": endpoint,
                            "attempts": attempt + 1
                        }
                    )

                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        # This should never be reached due to the raise in the except block above
        raise NetworkError("Max retries exceeded - this should not happen")

    def _get_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for request."""
        key_data = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        return f"cache:{hash(key_data)}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False

        cached_time = self._cache[cache_key]["timestamp"]
        return time.time() - cached_time < self.config.cache_ttl

    # Authentication methods
    async def create_api_key(self, name: str, permissions: Dict[str, bool]) -> Dict[str, str]:
        """Create new API key."""
        response = await self._make_request(
            "POST", "/auth/api-key",
            json={"name": name, "permissions": permissions}
        )
        return response.json()

    # Threat detection methods
    async def detect_threat(self, file_path: Optional[str] = None,
                          file_content: Optional[str] = None,
                          scan_type: str = "full",
                          include_metadata: bool = True) -> ThreatDetectionResult:
        """Detect threats in file or content."""
        request_data = {
            "scan_type": scan_type,
            "include_metadata": include_metadata
        }

        if file_path:
            request_data["file_path"] = file_path
        if file_content:
            request_data["file_content"] = file_content

        response = await self._make_request(
            "POST", "/v1/threats/detect",
            json=request_data
        )

        data = response.json()
        return ThreatDetectionResult(
            threat_detected=data["threat_detected"],
            threat_type=data.get("threat_type"),
            confidence=data["confidence"],
            scan_duration=data["scan_duration"],
            file_hash=data.get("file_hash"),
            metadata=data.get("metadata", {})
        )

    async def scan_file(self, file_path: str, scan_type: str = "full") -> ThreatDetectionResult:
        """Scan specific file for threats."""
        return await self.detect_threat(file_path=file_path, scan_type=scan_type)

    async def scan_content(self, content: str, scan_type: str = "full") -> ThreatDetectionResult:
        """Scan content for threats."""
        return await self.detect_threat(file_content=content, scan_type=scan_type)

    # System scanning methods
    async def start_system_scan(self, paths: Optional[List[str]] = None,
                              exclude_patterns: Optional[List[str]] = None,
                              scan_type: str = "full",
                              max_file_size: int = 100*1024*1024) -> SystemScanResult:
        """Start system-wide security scan."""
        request_data = {
            "paths": paths or [],
            "exclude_patterns": exclude_patterns or [],
            "scan_type": scan_type,
            "max_file_size": max_file_size
        }

        response = await self._make_request(
            "POST", "/v1/system/scan",
            json=request_data
        )

        data = response.json()
        return SystemScanResult(
            scan_id=data["scan_id"],
            status=data["status"],
            threats_found=data["threats_found"],
            files_scanned=data["files_scanned"],
            scan_duration=data["scan_duration"],
            started_at=datetime.fromisoformat(data["started_at"].replace("Z", "+00:00"))
        )

    async def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get scan status and results."""
        cache_key = self._get_cache_key(f"/v1/system/scan/{scan_id}")

        # Check cache for completed scans
        if self._is_cache_valid(cache_key):
            cached_data = self._cache[cache_key]["data"]
            if cached_data.get("status") == "COMPLETED":
                return cached_data

        response = await self._make_request("GET", f"/v1/system/scan/{scan_id}")
        data = response.json()

        # Cache completed scans
        if data.get("status") == "COMPLETED":
            self._cache[cache_key] = {
                "data": data,
                "timestamp": time.time()
            }

        return data

    async def wait_for_scan_completion(self, scan_id: str,
                                     poll_interval: int = 5,
                                     timeout: int = 3600) -> Dict[str, Any]:
        """Wait for scan to complete with polling."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self.get_scan_status(scan_id)

            if status["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
                return status

            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Scan {scan_id} did not complete within {timeout} seconds")

    # Security events methods
    async def create_security_event(self, event_type: str, severity: str,
                                  source: str, description: str,
                                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create new security event."""
        request_data = {
            "event_type": event_type,
            "severity": severity,
            "source": source,
            "description": description,
            "metadata": metadata or {}
        }

        response = await self._make_request(
            "POST", "/v1/events",
            json=request_data
        )

        data = response.json()
        return data["event_id"]

    async def get_security_events(self, limit: int = 100, offset: int = 0,
                                event_type: Optional[str] = None,
                                severity: Optional[str] = None) -> List[SecurityEvent]:
        """Get security events with filtering."""
        params = {"limit": limit, "offset": offset}
        if event_type:
            params["event_type"] = event_type
        if severity:
            params["severity"] = severity

        response = await self._make_request(
            "GET", "/v1/events",
            params=params
        )

        data = response.json()
        events = []

        for event_data in data["events"]:
            events.append(SecurityEvent(
                event_id=event_data["event_id"],
                event_type=event_data["event_type"],
                severity=event_data["severity"],
                source=event_data["source"],
                description=event_data["description"],
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                metadata=event_data.get("metadata", {})
            ))

        return events

    # Reports methods
    async def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary report."""
        cache_key = self._get_cache_key("/v1/reports/summary")

        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]

        response = await self._make_request("GET", "/v1/reports/summary")
        data = response.json()

        # Cache summary data
        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }

        return data

    async def generate_report(self, report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate security report."""
        response = await self._make_request(
            "POST", "/v1/reports/generate",
            json={"report_type": report_type}
        )
        return response.json()

    # Webhook methods
    async def create_webhook(self, url: str, events: List[str],
                           secret: Optional[str] = None) -> WebhookSubscription:
        """Create webhook subscription."""
        request_data = {
            "url": url,
            "events": events
        }
        if secret:
            request_data["secret"] = secret

        response = await self._make_request(
            "POST", "/v1/webhooks",
            json=request_data
        )

        data = response.json()
        return WebhookSubscription(
            webhook_id=data["webhook_id"],
            url=data["url"],
            events=data["events"],
            is_active=data["is_active"],
            created_at=datetime.fromisoformat(data["created_at"])
        )

    async def list_webhooks(self) -> List[WebhookSubscription]:
        """List webhook subscriptions."""
        response = await self._make_request("GET", "/v1/webhooks")
        data = response.json()

        webhooks = []
        for webhook_data in data["webhooks"]:
            webhooks.append(WebhookSubscription(
                webhook_id=webhook_data["id"],
                url=webhook_data["url"],
                events=webhook_data["events"],
                is_active=True,
                created_at=datetime.fromisoformat(webhook_data["created_at"])
            ))

        return webhooks

    # System configuration methods
    async def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration."""
        response = await self._make_request("GET", "/v1/system/config")
        return response.json()

    async def update_system_config(self, config: Dict[str, Any]) -> bool:
        """Update system configuration."""
        response = await self._make_request(
            "PUT", "/v1/system/config",
            json=config
        )
        data = response.json()
        return data.get("updated", False)

    # Real-time methods
    async def subscribe_to_events(self, event_types: Optional[List[str]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to real-time security events via WebSocket."""
        ws_url = self.config.base_url.replace("http", "ws") + "/ws/events"

        # Add authentication
        headers = {
            "Authorization": f"Bearer {self.config.access_token}"
        }

        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            # Send subscription message
            subscription = {
                "action": "subscribe",
                "event_types": event_types or ["*"]
            }
            await websocket.send(json.dumps(subscription))

            # Listen for events
            async for message in websocket:
                try:
                    event_data = json.loads(message)
                    yield event_data
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON received: {message}")

    # Batch operations
    async def batch_scan_files(self, file_paths: List[str],
                             scan_type: str = "full",
                             max_concurrent: int = 5) -> List[ThreatDetectionResult]:
        """Scan multiple files concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scan_single_file(file_path: str) -> ThreatDetectionResult:
            async with semaphore:
                return await self.scan_file(file_path, scan_type)

        tasks = [scan_single_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error scanning {file_paths[i]}: {result}")
            else:
                successful_results.append(result)

        return successful_results

    # Health and status methods
    async def health_check(self) -> bool:
        """Check API health status."""
        try:
            await self._ensure_session()
            if self._session is None:
                return False
            response = await self._session.get("/health")
            return response.status_code == 200
        except (httpx.RequestError, httpx.HTTPStatusError, ConnectionError) as e:
            self.logger.warning(f"Health check failed due to network error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during health check: {e}")
            return False

    async def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        # This would require additional endpoint on the server
        # For now, return basic client stats
        return {
            "cache_entries": len(self._cache),
            "last_token_refresh": self._token_expires.isoformat() if self._token_expires else None,
            "session_active": self._session is not None
        }


class WebhookHandler:
    """Helper class for handling incoming webhooks."""

    def __init__(self, secret: str):
        self.secret = secret
        self.logger = logging.getLogger(__name__)

    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature using secure cryptography."""
        expected_signature = secure_crypto.secure_hmac(
            self.secret.encode(),
            payload,
            'sha256'
        )

        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]

        return secure_crypto.constant_time_compare(expected_signature, signature)

    def parse_webhook(self, payload: str, signature: str) -> Optional[Dict[str, Any]]:
        """Parse and verify webhook payload."""
        if not self.verify_signature(payload, signature):
            self.logger.warning("Invalid webhook signature")
            return None

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in webhook payload")
            return None


class SecurityAPIClientSync:
    """Synchronous wrapper for SecurityAPIClient."""

    def __init__(self, config: APIConfig):
        self.client = SecurityAPIClient(config)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _run_async(self, coro: Any) -> Any:
        """Run async coroutine in sync context."""
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        return self._loop.run_until_complete(coro)

    def __enter__(self) -> "SecurityAPIClientSync":
        self._run_async(self.client.__aenter__())
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        self._run_async(self.client.__aexit__(exc_type, exc_val, exc_tb))

    # Synchronous wrapper methods
    def detect_threat(self, **kwargs) -> ThreatDetectionResult:
        return self._run_async(self.client.detect_threat(**kwargs))

    def scan_file(self, file_path: str, scan_type: str = "full") -> ThreatDetectionResult:
        return self._run_async(self.client.scan_file(file_path, scan_type))

    def start_system_scan(self, **kwargs) -> SystemScanResult:
        return self._run_async(self.client.start_system_scan(**kwargs))

    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        return self._run_async(self.client.get_scan_status(scan_id))

    def create_security_event(self, **kwargs) -> str:
        return self._run_async(self.client.create_security_event(**kwargs))

    def get_security_events(self, **kwargs) -> List[SecurityEvent]:
        return self._run_async(self.client.get_security_events(**kwargs))

    def get_security_summary(self) -> Dict[str, Any]:
        return self._run_async(self.client.get_security_summary())

    def generate_report(self, report_type: str = "comprehensive") -> Dict[str, Any]:
        return self._run_async(self.client.generate_report(report_type))

    def create_webhook(self, **kwargs) -> WebhookSubscription:
        return self._run_async(self.client.create_webhook(**kwargs))

    def list_webhooks(self) -> List[WebhookSubscription]:
        return self._run_async(self.client.list_webhooks())

    def health_check(self) -> bool:
        return self._run_async(self.client.health_check())


# Example usage and testing
async def example_usage():
    """Example usage of the SecurityAPIClient."""
    config = APIConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )

    async with SecurityAPIClient(config) as client:
        # Check API health
        is_healthy = await client.health_check()
        print(f"API Health: {is_healthy}")

        # Scan a file
        result = await client.scan_file("/path/to/suspicious/file.exe")
        print(f"Threat detected: {result.threat_detected}")
        print(f"Confidence: {result.confidence}")

        # Start system scan
        scan = await client.start_system_scan(
            paths=["/home/user"],
            scan_type="quick"
        )
        print(f"Scan started: {scan.scan_id}")

        # Wait for completion
        final_status = await client.wait_for_scan_completion(scan.scan_id)
        print(f"Scan completed: {final_status}")

        # Create security event
        event_id = await client.create_security_event(
            event_type="MALWARE_DETECTED",
            severity="HIGH",
            source="File Scanner",
            description="Malicious file detected in downloads folder"
        )
        print(f"Event created: {event_id}")

        # Get security summary
        summary = await client.get_security_summary()
        print(f"Security summary: {summary}")

        # Create webhook
        webhook = await client.create_webhook(
            url="https://your-server.com/webhook",
            events=["THREAT_DETECTED", "SCAN_COMPLETED"]
        )
        print(f"Webhook created: {webhook.webhook_id}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
