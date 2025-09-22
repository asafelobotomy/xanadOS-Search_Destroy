"""Test suite for unified security framework components."""

import tempfile
import unittest
from unittest.mock import patch

from app.core.unified_security_framework import (
    APIPermissions,
    SecurityConfig,
    UnifiedSecurityManager,
)
from app.core.authorization_engine import AuthorizationContext, AuthorizationEngine
from app.core.api_security_gateway import APISecurityGateway, SecurityEvent, ThreatLevel
from app.core.permission_controller import (
    ElevationResult,
    PermissionController,
    PermissionLevel,
)
from app.core.security_integration import (
    EnterpriseConfig,
    SecurityIntegrationCoordinator,
    SecurityRequest,
    SecurityRequestType,
    authenticate_user,
    check_authorization,
    check_file_permissions,
    elevate_privileges,
    get_security_coordinator,
)


class TestUnifiedSecurityFramework(unittest.TestCase):
    """Test suite for the core unified security framework."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SecurityConfig()
        self.security_manager = UnifiedSecurityManager(self.config)

    def test_security_config_creation(self):
        """Test SecurityConfig creation and defaults."""
        config = SecurityConfig()
        self.assertIsInstance(config.api_key_length, int)
        self.assertGreater(config.api_key_length, 0)
        self.assertIsInstance(config.session_timeout_hours, int)
        self.assertGreater(config.session_timeout_hours, 0)

    def test_api_permissions_creation(self):
        """Test APIPermissions creation and serialization."""
        permissions = APIPermissions()
        self.assertFalse(permissions.read)
        self.assertFalse(permissions.write)
        self.assertFalse(permissions.delete)
        self.assertFalse(permissions.admin)

        # Test from_dict method
        perm_dict = {"read": True, "write": True, "delete": False, "admin": False}
        permissions = APIPermissions.from_dict(perm_dict)
        self.assertTrue(permissions.read)
        self.assertTrue(permissions.write)
        self.assertFalse(permissions.delete)
        self.assertFalse(permissions.admin)

    def test_security_manager_initialization(self):
        """Test UnifiedSecurityManager initialization."""
        self.assertIsNotNone(self.security_manager.config)
        self.assertIsInstance(self.security_manager.config, SecurityConfig)

    def test_api_key_generation(self):
        """Test API key generation functionality."""
        api_key = self.security_manager.generate_api_key(
            "test_user", APIPermissions(read=True, write=True)
        )
        self.assertIsInstance(api_key, str)
        self.assertGreater(len(api_key), 0)

        # Test API key validation
        result = self.security_manager.validate_api_key(api_key)
        self.assertTrue(result.success)
        self.assertEqual(result.user_id, "test_user")

    def test_user_authentication(self):
        """Test user authentication functionality."""
        result = self.security_manager.authenticate_user(
            "test_user", {"password": "test_pass"}
        )
        self.assertTrue(result.success)
        self.assertEqual(result.user_id, "test_user")


class TestAuthorizationEngine(unittest.TestCase):
    """Test suite for the authorization engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SecurityConfig()
        self.auth_engine = AuthorizationEngine(self.config)

    def test_authorization_engine_initialization(self):
        """Test AuthorizationEngine initialization."""
        self.assertIsNotNone(self.auth_engine.config)
        self.assertIsInstance(self.auth_engine.config, SecurityConfig)

    def test_authorization_context_creation(self):
        """Test AuthorizationContext creation."""
        context = AuthorizationContext(
            user_id="test_user",
            resource="/test/resource",
            action="read",
            context={"source": "test"},
        )
        self.assertEqual(context.user_id, "test_user")
        self.assertEqual(context.resource, "/test/resource")
        self.assertEqual(context.action, "read")

    def test_basic_authorization_check(self):
        """Test basic authorization checking."""
        context = AuthorizationContext(
            user_id="admin", resource="/admin/resource", action="read"
        )

        result = self.auth_engine.check_authorization(context)
        self.assertTrue(result.success)
        self.assertEqual(result.user_id, "admin")


class TestAPISecurityGateway(unittest.TestCase):
    """Test suite for the API security gateway."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SecurityConfig()
        self.gateway = APISecurityGateway(self.config)

    def test_api_gateway_initialization(self):
        """Test APISecurityGateway initialization."""
        self.assertIsNotNone(self.gateway.config)
        self.assertIsInstance(self.gateway.config, SecurityConfig)

    def test_request_validation(self):
        """Test API request validation."""
        request_data = {
            "user_id": "test_user",
            "endpoint": "/api/test",
            "method": "GET",
        }

        result = self.gateway.validate_request("test_user", "/api/test", request_data)
        self.assertTrue(result.success)

    def test_security_event_logging(self):
        """Test security event logging."""
        event = SecurityEvent(
            event_type="suspicious_activity",
            user_id="test_user",
            resource="/api/admin",
            description="Multiple failed authentication attempts",
            threat_level=ThreatLevel.MEDIUM,
        )

        # Test that event can be logged without errors
        try:
            self.gateway.log_security_event(event)
            success = True
        except Exception:
            success = False

        self.assertTrue(success)


class TestPermissionController(unittest.TestCase):
    """Test suite for the permission controller."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SecurityConfig()
        self.controller = PermissionController(self.config)

    def test_permission_controller_initialization(self):
        """Test PermissionController initialization."""
        self.assertIsNotNone(self.controller.config)
        self.assertIsInstance(self.controller.config, SecurityConfig)

    @patch("os.access")
    def test_file_permission_checking(self, mock_access):
        """Test file permission checking."""
        mock_access.return_value = True

        with tempfile.NamedTemporaryFile() as temp_file:
            result = self.controller.check_file_permissions(
                temp_file.name, PermissionLevel.READ
            )
            self.assertTrue(result.success)

    def test_privilege_escalation(self):
        """Test privilege escalation functionality."""
        result = self.controller.elevate_privileges(
            "Test operation requires elevated privileges",
            use_gui=False,  # Don't try to show GUI in tests
        )

        self.assertIsInstance(result, ElevationResult)
        self.assertIsInstance(result.success, bool)
        self.assertIsInstance(result.message, str)


class TestSecurityIntegration(unittest.TestCase):
    """Test suite for the security integration coordinator."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SecurityConfig()
        self.enterprise_config = EnterpriseConfig()
        self.coordinator = SecurityIntegrationCoordinator(
            self.config, self.enterprise_config
        )

    def test_security_coordinator_initialization(self):
        """Test SecurityIntegrationCoordinator initialization."""
        self.assertIsNotNone(self.coordinator.config)
        self.assertIsNotNone(self.coordinator.enterprise_config)
        self.assertIsNotNone(self.coordinator.unified_security)
        self.assertIsNotNone(self.coordinator.auth_engine)
        self.assertIsNotNone(self.coordinator.api_gateway)
        self.assertIsNotNone(self.coordinator.permission_controller)

    def test_security_request_processing(self):
        """Test unified security request processing."""
        request = SecurityRequest(
            user_id="test_user",
            resource="/test/resource",
            action="read",
            request_type=SecurityRequestType.AUTHORIZATION,
        )

        response = self.coordinator.process_security_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.user_id, "test_user")
        self.assertEqual(response.resource, "/test/resource")
        self.assertEqual(response.action, "read")

    def test_performance_metrics(self):
        """Test performance monitoring."""
        metrics = self.coordinator.get_performance_metrics()
        self.assertIsNotNone(metrics)
        self.assertGreaterEqual(metrics.total_requests, 0)
        self.assertGreaterEqual(metrics.successful_requests, 0)
        self.assertGreaterEqual(metrics.failed_requests, 0)


class TestGlobalSecurityFunctions(unittest.TestCase):
    """Test suite for global security convenience functions."""

    def test_global_authenticate_user(self):
        """Test global authenticate_user function."""
        result = authenticate_user("test_user", {"password": "test"})
        self.assertIsInstance(result, bool)

    def test_global_check_authorization(self):
        """Test global check_authorization function."""
        result = check_authorization("test_user", "/resource", "read")
        self.assertIsInstance(result, bool)

    def test_global_check_file_permissions(self):
        """Test global check_file_permissions function."""
        with tempfile.NamedTemporaryFile() as temp_file:
            result = check_file_permissions("test_user", temp_file.name)
            self.assertIsInstance(result, bool)

    def test_global_elevate_privileges(self):
        """Test global elevate_privileges function."""
        result = elevate_privileges("test_user", "test operation", use_gui=False)
        self.assertIsInstance(result, ElevationResult)

    def test_get_security_coordinator(self):
        """Test get_security_coordinator function."""
        coordinator = get_security_coordinator()
        self.assertIsInstance(coordinator, SecurityIntegrationCoordinator)

        # Test singleton behavior
        coordinator2 = get_security_coordinator()
        self.assertIs(coordinator, coordinator2)


if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=True)
