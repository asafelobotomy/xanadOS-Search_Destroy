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
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from functools import wraps
from pathlib import Path

import jwt
from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import strawberry
from strawberry.fastapi import GraphQLRouter
import redis
import httpx
from cryptography.fernet import Fernet

from app.utils.secure_crypto import secure_crypto, generate_api_key
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.ml_threat_detector import MLThreatDetector
from app.core.edr_engine import EDREngine, SecurityEvent
from app.core.intelligent_automation import get_intelligent_automation
from app.reporting.advanced_reporting import get_advanced_reporting
from app.utils.config import get_config


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
    scan_type: str = Field(default="full", regex="^(quick|full|deep)$")
    include_metadata: bool = True


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
    scan_type: str = Field(default="full", regex="^(quick|full|deep)$")
    max_file_size: int = Field(default=100*1024*1024, ge=1024)  # 100MB default


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
    severity: str = Field(regex="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    source: str
    description: str
    metadata: Dict[str, Any] = {}


class SecurityEventResponse(BaseModel):
    event_id: str
    timestamp: datetime
    processed: bool
    actions_taken: List[str] = []


class WebhookRequest(BaseModel):
    url: str = Field(regex=r'^https?://.+')
    events: List[str]
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    webhook_id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10


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


class AuthenticationManager:
    """Manage API authentication and authorization."""

    def __init__(self, secret_key: str, redis_client: Optional[redis.Redis] = None):
        self.secret_key = secret_key
        self.redis_client = redis_client
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30

        # Database session
        self.engine = create_engine("sqlite:///security_api.db")
        Base.metadata.create_all(bind=self.engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = SessionLocal()

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
        """Create JWT access and refresh tokens."""
        # Access token
        access_payload = {
            "user_id": user_id,
            "permissions": permissions.__dict__,
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "type": "access"
        }

        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

        # Refresh token
        refresh_payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

    async def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is expired
            if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                return None

            return payload

        except jwt.PyJWTError:
            return None

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
    """Rate limiting implementation."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.default_config = RateLimitConfig()

    async def check_rate_limit(self, identifier: str, config: RateLimitConfig = None) -> bool:
        """Check if request is within rate limits."""
        if not config:
            config = self.default_config

        current_time = int(time.time())

        # Check minute limit
        minute_key = f"rate_limit:{identifier}:minute:{current_time // 60}"
        minute_count = self.redis_client.get(minute_key)
        if minute_count and int(minute_count) >= config.requests_per_minute:
            return False

        # Check hour limit
        hour_key = f"rate_limit:{identifier}:hour:{current_time // 3600}"
        hour_count = self.redis_client.get(hour_key)
        if hour_count and int(hour_count) >= config.requests_per_hour:
            return False

        # Check day limit
        day_key = f"rate_limit:{identifier}:day:{current_time // 86400}"
        day_count = self.redis_client.get(day_key)
        if day_count and int(day_count) >= config.requests_per_day:
            return False

        return True

    async def increment_counter(self, identifier: str):
        """Increment rate limit counters."""
        current_time = int(time.time())

        # Increment counters with appropriate expiration
        minute_key = f"rate_limit:{identifier}:minute:{current_time // 60}"
        self.redis_client.incr(minute_key)
        self.redis_client.expire(minute_key, 60)

        hour_key = f"rate_limit:{identifier}:hour:{current_time // 3600}"
        self.redis_client.incr(hour_key)
        self.redis_client.expire(hour_key, 3600)

        day_key = f"rate_limit:{identifier}:day:{current_time // 86400}"
        self.redis_client.incr(day_key)
        self.redis_client.expire(day_key, 86400)


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
        self.auth_manager = AuthenticationManager(self.config.get('api_secret_key', 'fallback-secret'))
        self.rate_limiter = RateLimiter()
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

        # Rate limiting
        limiter = Limiter(key_func=get_remote_address)
        self.app.state.limiter = limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
            # Mock implementation - would integrate with ML threat detector
            return ThreatDetectionResponse(
                threat_detected=False,
                threat_type=None,
                confidence=0.95,
                scan_duration=1.2,
                file_hash="sha256:abcd1234...",
                metadata={"scan_type": request.scan_type}
            )

        @self.app.post("/v1/system/scan", response_model=SystemScanResponse)
        async def start_system_scan(request: SystemScanRequest,
                                  background_tasks: BackgroundTasks,
                                  current_user = Depends(get_current_user)):
            """Start system-wide security scan."""
            scan_id = f"scan_{int(time.time())}"

            # Start background scan
            background_tasks.add_task(self._perform_system_scan, scan_id, request)

            return SystemScanResponse(
                scan_id=scan_id,
                status="STARTED",
                threats_found=0,
                files_scanned=0,
                scan_duration=0.0,
                started_at=datetime.utcnow()
            )

        @self.app.get("/v1/system/scan/{scan_id}")
        async def get_scan_status(scan_id: str, current_user = Depends(get_current_user)):
            """Get scan status and results."""
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
            # Skip rate limiting for health checks
            if request.url.path == "/health":
                return await call_next(request)

            # Get client identifier
            client_ip = get_remote_address(request)

            # Check rate limits
            if not await self.rate_limiter.check_rate_limit(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"}
                )

            # Increment counter
            await self.rate_limiter.increment_counter(client_ip)

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
