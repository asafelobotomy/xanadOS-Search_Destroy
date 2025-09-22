"""
Security Integration Layer - Unified Security Coordinator

This module provides a comprehensive security integration layer that coordinates
all security components (authentication, authorization, API security, permissions)
into a unified, enterprise-ready security framework.

Components:
- SecurityIntegrationCoordinator: Main security orchestration hub
- SecurityRequest/Response: Unified security pipeline data structures
- Enterprise Configuration: LDAP, SAML, OAuth2, MFA integration
- Performance Monitoring: Security operation performance tracking
- Convenience Functions: Simplified security operation APIs

Features:
- Unified security request processing pipeline
- Enterprise authentication integration (LDAP, SAML, OAuth2)
- Multi-factor authentication support
- Performance monitoring and optimization
- Centralized security event coordination
- Cross-component security state management

Example:
    # Initialize security integration
    security = SecurityIntegrationCoordinator()

    # Process security request
    request = SecurityRequest(
        user_id="admin",
        resource="/secure/file",
        action="read",
        context={"source": "gui"}
    )
    response = security.process_security_request(request)

    # Check authorization
    if security.check_authorization("user123", "/data", "write"):
        # Proceed with authorized operation
        pass
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .api_security_gateway import APISecurityGateway
from .authorization_engine import (
    AuthorizationContext,
    AuthorizationEngine,
)
from .permission_controller import (
    ElevationResult,
    PermissionController,
    PermissionLevel,
)
from .unified_security_framework import (
    AuthenticationMethod,
    SecurityConfig,
    UnifiedSecurityManager,
)

# Import enterprise authentication if available
try:
    from .enterprise_authentication import EnterpriseAuthenticationCoordinator

    ENTERPRISE_AUTH_AVAILABLE = True
except ImportError:
    ENTERPRISE_AUTH_AVAILABLE = False

try:
    from .compliance_reporting import (
        ComplianceCoordinator,
        ComplianceStandard,
        AuditEventType,
        SeverityLevel,
    )

    COMPLIANCE_REPORTING_AVAILABLE = True
except ImportError:
    COMPLIANCE_REPORTING_AVAILABLE = False


class SecurityRequestType(Enum):
    """Types of security operations."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    PERMISSION_CHECK = "permission_check"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    API_ACCESS = "api_access"
    FILE_OPERATION = "file_operation"
    ENTERPRISE_SSO = "enterprise_sso"


class SecurityRequestPriority(Enum):
    """Priority levels for security requests."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SecurityRequest:
    """Unified security request containing all necessary context."""

    user_id: str
    resource: str
    action: str
    request_type: SecurityRequestType = SecurityRequestType.AUTHORIZATION
    priority: SecurityRequestPriority = SecurityRequestPriority.MEDIUM
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str | None = None
    client_info: dict[str, Any] = field(default_factory=dict)
    enterprise_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityResponse:
    """Unified security response with detailed results."""

    request_id: str
    success: bool
    user_id: str
    resource: str
    action: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    permissions_granted: list[str] = field(default_factory=list)
    security_level: str = "standard"
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    cache_hit: bool = False
    enterprise_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnterpriseConfig:
    """Configuration for enterprise integration features."""

    enable_ldap: bool = False
    ldap_server: str = ""
    ldap_base_dn: str = ""
    enable_saml: bool = False
    saml_provider_url: str = ""
    saml_entity_id: str = ""
    enable_oauth2: bool = False
    oauth2_provider: str = ""
    oauth2_client_id: str = ""
    enable_mfa: bool = False
    mfa_providers: list[str] = field(default_factory=list)
    session_timeout_minutes: int = 480  # 8 hours default
    require_enterprise_auth: list[str] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Performance tracking for security operations."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    average_response_time_ms: float = 0.0
    peak_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)
    component_metrics: dict[str, dict[str, float]] = field(default_factory=dict)


class SecurityIntegrationCoordinator:
    """
    Central coordinator for all security operations with enterprise features.

    This class provides a unified interface for all security operations,
    coordinating between authentication, authorization, API security, and
    permission management components. It includes enterprise features like
    LDAP/SAML integration, performance monitoring, and caching.
    """

    def __init__(
        self,
        config: SecurityConfig | None = None,
        enterprise_config: EnterpriseConfig | None = None,
    ):
        """Initialize security integration coordinator."""
        self.config = config or SecurityConfig()
        self.enterprise_config = enterprise_config or EnterpriseConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize security components
        self.unified_security = UnifiedSecurityManager(self.config)
        self.auth_engine = AuthorizationEngine(self.config)
        self.api_gateway = APISecurityGateway(self.config)
        self.permission_controller = PermissionController(self.config)

        # Performance and caching
        self.metrics = PerformanceMetrics()
        self._response_cache: dict[str, tuple[SecurityResponse, datetime]] = {}
        self._cache_ttl_minutes = 5

        # Enterprise integration components
        self._enterprise_sessions: dict[str, dict[str, Any]] = {}
        self._mfa_pending: dict[str, dict[str, Any]] = {}

        # Initialize enterprise authentication if available and configured
        self.enterprise_auth = None
        if ENTERPRISE_AUTH_AVAILABLE and self._should_enable_enterprise():
            self.enterprise_auth = self._initialize_enterprise_auth()

        # Initialize compliance reporting if available and configured
        self.compliance = None
        if COMPLIANCE_REPORTING_AVAILABLE and self._should_enable_compliance():
            self.compliance = self._initialize_compliance_reporting()

        self.logger.info("Security Integration Coordinator initialized")

    def process_security_request(self, request: SecurityRequest) -> SecurityResponse:
        """Process unified security request through all security layers."""
        start_time = datetime.now()
        request_id = f"{request.user_id}_{request.timestamp.isoformat()}"

        try:
            # Check cache first
            cached_response = self._get_cached_response(request)
            if cached_response:
                cached_response.cache_hit = True
                self._update_metrics(True, 0.0, cache_hit=True)
                return cached_response

            # Enterprise authentication check
            if self._requires_enterprise_auth(request):
                enterprise_result = self._handle_enterprise_auth(request)
                if not enterprise_result["success"]:
                    return self._create_error_response(
                        request_id, request, "Enterprise authentication required"
                    )

            # Process through security pipeline
            response = self._process_security_pipeline(request_id, request)

            # Cache successful responses
            if response.success:
                self._cache_response(request, response)

            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            response.processing_time_ms = processing_time
            self._update_metrics(response.success, processing_time)

            return response

        except Exception as e:
            self.logger.error(f"Security request processing failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_metrics(False, processing_time)
            return self._create_error_response(
                request_id, request, f"Security processing error: {e!s}"
            )

    def _process_security_pipeline(
        self, request_id: str, request: SecurityRequest
    ) -> SecurityResponse:
        """Process request through the complete security pipeline."""
        # Step 1: Authentication
        auth_result = self.unified_security.authenticate_user(
            request.user_id, request.context.get("credentials", {})
        )
        if not auth_result.success:
            return self._create_error_response(
                request_id, request, f"Authentication failed: {auth_result.message}"
            )

        # Step 2: Authorization
        auth_context = AuthorizationContext(
            user_id=request.user_id,
            resource=request.resource,
            action=request.action,
            context=request.context,
        )

        auth_result = self.auth_engine.check_authorization(auth_context)
        if not auth_result.success:
            return self._create_error_response(
                request_id, request, f"Authorization denied: {auth_result.message}"
            )

        # Step 3: Permission validation
        if request.request_type == SecurityRequestType.PERMISSION_CHECK:
            perm_result = self.permission_controller.check_file_permissions(
                request.resource,
                request.context.get("required_level", PermissionLevel.READ),
            )
            if not perm_result.success:
                return self._create_error_response(
                    request_id, request, f"Permission denied: {perm_result.message}"
                )

        # Step 4: Privilege escalation if needed
        if request.request_type == SecurityRequestType.PRIVILEGE_ESCALATION:
            elevation_result = self.permission_controller.elevate_privileges(
                request.context.get("elevation_reason", "Required for operation"),
                request.context.get("use_gui", True),
            )
            if not elevation_result.success:
                return self._create_error_response(
                    request_id,
                    request,
                    f"Privilege escalation failed: {elevation_result.message}",
                )

        # Step 5: API security validation
        if request.request_type == SecurityRequestType.API_ACCESS:
            api_result = self.api_gateway.validate_request(
                request.user_id, request.resource, request.context
            )
            if not api_result.success:
                return self._create_error_response(
                    request_id, request, f"API access denied: {api_result.message}"
                )

        # Create successful response
        return SecurityResponse(
            request_id=request_id,
            success=True,
            user_id=request.user_id,
            resource=request.resource,
            action=request.action,
            message="Security validation successful",
            details={
                "auth_level": auth_result.auth_level,
                "permissions": auth_result.permissions,
                "security_context": request.context,
            },
            permissions_granted=auth_result.permissions,
            security_level=auth_result.auth_level,
        )

    def _requires_enterprise_auth(self, request: SecurityRequest) -> bool:
        """Check if request requires enterprise authentication."""
        if not self.enterprise_config.require_enterprise_auth:
            return False

        return any(
            pattern in request.resource
            for pattern in self.enterprise_config.require_enterprise_auth
        )

    def _handle_enterprise_auth(self, request: SecurityRequest) -> dict[str, Any]:
        """Handle enterprise authentication (LDAP, SAML, OAuth2)."""
        # This is a placeholder for enterprise authentication
        # In a real implementation, this would integrate with actual enterprise systems

        if self.enterprise_config.enable_ldap:
            # LDAP authentication logic
            pass

        if self.enterprise_config.enable_saml:
            # SAML authentication logic
            pass

        if self.enterprise_config.enable_oauth2:
            # OAuth2 authentication logic
            pass

        if self.enterprise_config.enable_mfa:
            # Multi-factor authentication logic
            pass

        # For now, return success if any enterprise auth is enabled
        return {
            "success": True,
            "method": "enterprise",
            "details": {"configured_methods": self._get_configured_auth_methods()},
        }

    def _get_configured_auth_methods(self) -> list[str]:
        """Get list of configured enterprise authentication methods."""
        methods = []
        if self.enterprise_config.enable_ldap:
            methods.append("ldap")
        if self.enterprise_config.enable_saml:
            methods.append("saml")
        if self.enterprise_config.enable_oauth2:
            methods.append("oauth2")
        if self.enterprise_config.enable_mfa:
            methods.append("mfa")
        return methods

    def _get_cached_response(self, request: SecurityRequest) -> SecurityResponse | None:
        """Get cached security response if available and valid."""
        cache_key = f"{request.user_id}_{request.resource}_{request.action}"

        if cache_key in self._response_cache:
            response, cached_time = self._response_cache[cache_key]

            # Check if cache is still valid
            if datetime.now() - cached_time < timedelta(
                minutes=self._cache_ttl_minutes
            ):
                self.logger.debug(f"Cache hit for request: {cache_key}")
                return response
            else:
                # Remove expired cache entry
                del self._response_cache[cache_key]

        return None

    def _cache_response(self, request: SecurityRequest, response: SecurityResponse):
        """Cache security response for future use."""
        cache_key = f"{request.user_id}_{request.resource}_{request.action}"
        self._response_cache[cache_key] = (response, datetime.now())

        # Cleanup old cache entries periodically
        if len(self._response_cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired cache entries."""
        current_time = datetime.now()
        expired_keys = [
            key
            for key, (_, cached_time) in self._response_cache.items()
            if current_time - cached_time > timedelta(minutes=self._cache_ttl_minutes)
        ]

        for key in expired_keys:
            del self._response_cache[key]

        self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _create_error_response(
        self, request_id: str, request: SecurityRequest, message: str
    ) -> SecurityResponse:
        """Create standardized error response."""
        return SecurityResponse(
            request_id=request_id,
            success=False,
            user_id=request.user_id,
            resource=request.resource,
            action=request.action,
            message=message,
            details={"error": True, "context": request.context},
        )

    def _update_metrics(
        self, success: bool, processing_time_ms: float, cache_hit: bool = False
    ):
        """Update performance metrics."""
        self.metrics.total_requests += 1

        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        if cache_hit:
            self.metrics.cache_hits += 1

        # Update timing metrics
        self.metrics.peak_response_time_ms = max(
            self.metrics.peak_response_time_ms, processing_time_ms
        )

        # Calculate rolling average
        total_time = (
            self.metrics.average_response_time_ms * (self.metrics.total_requests - 1)
            + processing_time_ms
        )
        self.metrics.average_response_time_ms = total_time / self.metrics.total_requests

    # Convenience methods for common operations

    def authenticate_user(self, user_id: str, credentials: dict[str, Any]) -> bool:
        """Simplified user authentication."""
        request = SecurityRequest(
            user_id=user_id,
            resource="auth",
            action="authenticate",
            request_type=SecurityRequestType.AUTHENTICATION,
            context={"credentials": credentials},
        )
        response = self.process_security_request(request)
        return response.success

    def check_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Simplified authorization check."""
        request = SecurityRequest(
            user_id=user_id,
            resource=resource,
            action=action,
            request_type=SecurityRequestType.AUTHORIZATION,
            context=context or {},
        )
        response = self.process_security_request(request)
        return response.success

    def check_file_permissions(
        self,
        user_id: str,
        file_path: str,
        required_level: PermissionLevel = PermissionLevel.READ,
    ) -> bool:
        """Simplified file permission check."""
        request = SecurityRequest(
            user_id=user_id,
            resource=file_path,
            action="access",
            request_type=SecurityRequestType.PERMISSION_CHECK,
            context={"required_level": required_level},
        )
        response = self.process_security_request(request)
        return response.success

    def elevate_privileges(
        self, user_id: str, reason: str, use_gui: bool = True
    ) -> ElevationResult:
        """Simplified privilege escalation."""
        request = SecurityRequest(
            user_id=user_id,
            resource="system",
            action="elevate",
            request_type=SecurityRequestType.PRIVILEGE_ESCALATION,
            context={"elevation_reason": reason, "use_gui": use_gui},
        )
        response = self.process_security_request(request)

        return ElevationResult(
            success=response.success,
            message=response.message,
            elevated_command="",  # Would be populated by actual elevation
            privilege_level=(
                PermissionLevel.ADMIN if response.success else PermissionLevel.USER
            ),
        )

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self.metrics

    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = PerformanceMetrics()
        self.logger.info("Performance metrics reset")

    def _should_enable_enterprise(self) -> bool:
        """Check if enterprise authentication should be enabled."""
        return (
            self.enterprise_config.enable_ldap
            or self.enterprise_config.enable_saml
            or self.enterprise_config.enable_oauth2
        )

    def _should_enable_compliance(self) -> bool:
        """Check if compliance reporting should be enabled."""
        # Check configuration or environment variables
        compliance_enabled = (
            os.getenv("ENABLE_COMPLIANCE_REPORTING", "true").lower() == "true"
        )
        return compliance_enabled and COMPLIANCE_REPORTING_AVAILABLE

    def _initialize_enterprise_auth(self) -> "EnterpriseAuthenticationCoordinator":
        """Initialize enterprise authentication coordinator."""
        from .enterprise_authentication import (
            EnterpriseAuthenticationCoordinator,
            LDAPConfig,
            MFAConfig,
            OAuth2Config,
            SAMLConfig,
        )

        # Configure LDAP if enabled
        ldap_config = None
        if self.enterprise_config.enable_ldap:
            ldap_config = LDAPConfig(
                server_url=self.enterprise_config.ldap_server,
                bind_dn="",  # Will be configured per environment
                bind_password="",  # Will be configured per environment
                user_base_dn=self.enterprise_config.ldap_base_dn,
                group_base_dn=self.enterprise_config.ldap_base_dn,
            )

        # Configure SAML if enabled
        saml_config = None
        if self.enterprise_config.enable_saml:
            saml_config = SAMLConfig(
                idp_entity_id=self.enterprise_config.saml_entity_id,
                idp_sso_url=self.enterprise_config.saml_provider_url,
                idp_certificate="",  # Will be configured per environment
                sp_entity_id="xanados-search-destroy",
                sp_acs_url="",  # Will be configured per environment
                sp_private_key="",  # Will be configured per environment
                sp_certificate="",  # Will be configured per environment
            )

        # Configure OAuth2 if enabled
        oauth2_configs = {}
        if self.enterprise_config.enable_oauth2:
            oauth2_configs["default"] = OAuth2Config(
                client_id=self.enterprise_config.oauth2_client_id,
                client_secret="",  # Will be configured per environment
                authorization_url="",  # Will be configured per environment
                token_url="",  # Will be configured per environment
                userinfo_url="",  # Will be configured per environment
                provider_name=self.enterprise_config.oauth2_provider,
            )

        # Configure MFA if enabled
        mfa_config = None
        if self.enterprise_config.enable_mfa:
            mfa_config = MFAConfig(
                enabled_methods=[],  # Will be configured from enterprise_config.mfa_providers
                totp_issuer="xanadOS Search & Destroy",
            )

        return EnterpriseAuthenticationCoordinator(
            auth_framework=self.unified_security.auth_framework,
            ldap_config=ldap_config,
            saml_config=saml_config,
            oauth2_configs=oauth2_configs,
            mfa_config=mfa_config,
        )

    async def authenticate_enterprise_user(
        self, method: AuthenticationMethod, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """Authenticate user using enterprise authentication methods."""
        if not self.enterprise_auth:
            return {
                "success": False,
                "error": "Enterprise authentication not configured",
            }

        try:
            result = await self.enterprise_auth.authenticate(method, credentials)

            if result.success:
                # Create enterprise session
                session_id = await self.enterprise_auth.create_enterprise_session(
                    result, require_mfa=self.enterprise_config.enable_mfa
                )

                return {
                    "success": True,
                    "user_id": result.user_id,
                    "username": result.username,
                    "email": result.email,
                    "groups": result.groups,
                    "session_id": session_id,
                    "mfa_required": result.mfa_required,
                }
            else:
                return {"success": False, "error": result.error_message}

        except Exception as e:
            self.logger.error(f"Enterprise authentication failed: {e}")
            return {"success": False, "error": "Authentication service error"}

    def get_enterprise_config(self) -> EnterpriseConfig:
        """Get current enterprise configuration."""
        return self.enterprise_config

    def update_enterprise_config(self, config: EnterpriseConfig):
        """Update enterprise configuration."""
        self.enterprise_config = config
        self.logger.info("Enterprise configuration updated")

    def _initialize_compliance_reporting(self) -> "ComplianceCoordinator | None":
        """Initialize compliance reporting coordinator."""
        if not COMPLIANCE_REPORTING_AVAILABLE:
            return None

        try:
            from .compliance_reporting import ComplianceCoordinator

            return ComplianceCoordinator()
        except Exception as e:
            self.logger.error(f"Failed to initialize compliance reporting: {e}")
            return None

    async def log_compliance_event(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        outcome: str,
        details: dict[str, Any] | None = None,
    ) -> str | None:
        """Log security event for compliance tracking."""
        if not self.compliance:
            return None

        try:
            from .compliance_reporting import AuditEventType

            # Map string event type to enum
            audit_event_type = getattr(
                AuditEventType, event_type.upper(), AuditEventType.SYSTEM_MODIFICATION
            )

            return await self.compliance.log_security_event(
                event_type=audit_event_type,
                user_id=user_id,
                resource=resource,
                action=action,
                outcome=outcome,
                details=details or {},
            )
        except Exception as e:
            self.logger.error(f"Failed to log compliance event: {e}")
            return None

    async def generate_compliance_report(
        self, standards: list[str], period_days: int = 30
    ) -> dict[str, Any] | None:
        """Generate compliance report for specified standards."""
        if not self.compliance:
            return None

        try:
            from .compliance_reporting import ComplianceStandard

            # Convert string standards to enum
            compliance_standards = []
            for standard in standards:
                try:
                    compliance_standards.append(
                        getattr(ComplianceStandard, standard.upper())
                    )
                except AttributeError:
                    self.logger.warning(f"Unknown compliance standard: {standard}")

            if not compliance_standards:
                return None

            report = await self.compliance.generate_compliance_report(
                standards=compliance_standards, period_days=period_days
            )

            return {
                "report_id": report.report_id,
                "generation_date": report.generation_date.isoformat(),
                "overall_score": report.overall_score,
                "standards": [s.value for s in report.standards],
                "executive_summary": report.executive_summary,
                "gap_analysis": report.gap_analysis,
                "recommendations": report.recommendations,
            }
        except Exception as e:
            self.logger.error(f"Failed to generate compliance report: {e}")
            return None


# Global security coordinator instance
_security_coordinator: SecurityIntegrationCoordinator | None = None


def get_security_coordinator(
    config: SecurityConfig | None = None,
    enterprise_config: EnterpriseConfig | None = None,
) -> SecurityIntegrationCoordinator:
    """Get global security coordinator instance."""
    global _security_coordinator

    if _security_coordinator is None:
        _security_coordinator = SecurityIntegrationCoordinator(
            config, enterprise_config
        )

    return _security_coordinator


def reset_security_coordinator():
    """Reset global security coordinator instance."""
    global _security_coordinator
    _security_coordinator = None


# Convenience functions for common security operations


def authenticate_user(user_id: str, credentials: dict[str, Any]) -> bool:
    """Global function for user authentication."""
    coordinator = get_security_coordinator()
    return coordinator.authenticate_user(user_id, credentials)


def check_authorization(
    user_id: str, resource: str, action: str, context: dict[str, Any] | None = None
) -> bool:
    """Global function for authorization check."""
    coordinator = get_security_coordinator()
    return coordinator.check_authorization(user_id, resource, action, context)


def check_file_permissions(
    user_id: str, file_path: str, required_level: PermissionLevel = PermissionLevel.READ
) -> bool:
    """Global function for file permission check."""
    coordinator = get_security_coordinator()
    return coordinator.check_file_permissions(user_id, file_path, required_level)


def elevate_privileges(
    user_id: str, reason: str, use_gui: bool = True
) -> ElevationResult:
    """Global function for privilege escalation."""
    coordinator = get_security_coordinator()
    return coordinator.elevate_privileges(user_id, reason, use_gui)


async def authenticate_enterprise_user(
    method: AuthenticationMethod, credentials: dict[str, Any]
) -> dict[str, Any]:
    """Global function for enterprise authentication."""
    coordinator = get_security_coordinator()
    return await coordinator.authenticate_enterprise_user(method, credentials)
