#!/usr/bin/env python3
"""
Simple validation script for unified security framework components.
This script validates the core functionality of our new security system
without importing the full application dependencies.
"""

import sys
import tempfile
from pathlib import Path

# Add the app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def validate_unified_security_framework():
    """Validate the unified security framework core."""
    try:
        from app.core.unified_security_framework import (
            SecurityConfig,
            APIPermissions,
            UnifiedSecurityManager,
        )

        print("✅ UnifiedSecurityFramework imports successfully")

        # Test basic functionality
        config = SecurityConfig()
        manager = UnifiedSecurityManager(config)

        # Test API permissions
        permissions = APIPermissions(read=True, write=True)
        api_key = manager.generate_api_key("test_user", permissions)

        # Test API key validation
        result = manager.validate_api_key(api_key)
        assert result.success
        assert result.user_id == "test_user"

        # Test authentication
        auth_result = manager.authenticate_user("test_user", {"password": "test"})
        assert auth_result.success

        print("✅ UnifiedSecurityFramework core functionality validated")
        return True

    except Exception as e:
        print(f"❌ UnifiedSecurityFramework validation failed: {e}")
        return False


def validate_authorization_engine():
    """Validate the authorization engine."""
    try:
        from app.core.authorization_engine import (
            AuthorizationEngine,
            AuthorizationContext,
        )

        print("✅ AuthorizationEngine imports successfully")

        # Test basic functionality
        from app.core.unified_security_framework import SecurityConfig

        config = SecurityConfig()
        engine = AuthorizationEngine(config)

        # Test authorization context
        context = AuthorizationContext(
            user_id="test_user", resource="/test/resource", action="read"
        )

        # Test authorization check
        result = engine.check_authorization(context)
        assert result.success

        print("✅ AuthorizationEngine functionality validated")
        return True

    except Exception as e:
        print(f"❌ AuthorizationEngine validation failed: {e}")
        return False


def validate_api_security_gateway():
    """Validate the API security gateway."""
    try:
        from app.core.api_security_gateway import (
            APISecurityGateway,
            SecurityEvent,
            ThreatLevel,
        )

        print("✅ APISecurityGateway imports successfully")

        # Test basic functionality
        from app.core.unified_security_framework import SecurityConfig

        config = SecurityConfig()
        gateway = APISecurityGateway(config)

        # Test request validation
        request_data = {
            "user_id": "test_user",
            "endpoint": "/api/test",
            "method": "GET",
        }

        result = gateway.validate_request("test_user", "/api/test", request_data)
        assert result.success

        # Test security event logging
        event = SecurityEvent(
            event_type="test_event",
            user_id="test_user",
            resource="/api/test",
            description="Test security event",
            threat_level=ThreatLevel.LOW,
        )

        gateway.log_security_event(event)

        print("✅ APISecurityGateway functionality validated")
        return True

    except Exception as e:
        print(f"❌ APISecurityGateway validation failed: {e}")
        return False


def validate_permission_controller():
    """Validate the permission controller."""
    try:
        from app.core.permission_controller import (
            PermissionController,
            PermissionLevel,
            ElevationResult,
        )

        print("✅ PermissionController imports successfully")

        # Test basic functionality
        from app.core.unified_security_framework import SecurityConfig

        config = SecurityConfig()
        controller = PermissionController(config)

        # Test file permission checking with a temporary file
        with tempfile.NamedTemporaryFile() as temp_file:
            result = controller.check_file_permissions(
                temp_file.name, PermissionLevel.READ
            )
            assert result.success

        # Test privilege escalation (without GUI)
        elevation_result = controller.elevate_privileges(
            "Test privilege escalation", use_gui=False
        )
        assert isinstance(elevation_result, ElevationResult)

        print("✅ PermissionController functionality validated")
        return True

    except Exception as e:
        print(f"❌ PermissionController validation failed: {e}")
        return False


def validate_security_integration():
    """Validate the security integration coordinator."""
    try:
        from app.core.security_integration import (
            SecurityIntegrationCoordinator,
            SecurityRequest,
            SecurityRequestType,
            EnterpriseConfig,
            authenticate_user,
            check_authorization,
            check_file_permissions,
            elevate_privileges,
            get_security_coordinator,
        )

        print("✅ SecurityIntegration imports successfully")

        # Test basic functionality
        from app.core.unified_security_framework import SecurityConfig

        config = SecurityConfig()
        enterprise_config = EnterpriseConfig()
        coordinator = SecurityIntegrationCoordinator(config, enterprise_config)

        # Test security request processing
        request = SecurityRequest(
            user_id="test_user",
            resource="/test/resource",
            action="read",
            request_type=SecurityRequestType.AUTHORIZATION,
        )

        response = coordinator.process_security_request(request)
        assert response.user_id == "test_user"
        assert response.resource == "/test/resource"

        # Test global convenience functions
        auth_result = authenticate_user("test_user", {"password": "test"})
        assert isinstance(auth_result, bool)

        authz_result = check_authorization("test_user", "/resource", "read")
        assert isinstance(authz_result, bool)

        with tempfile.NamedTemporaryFile() as temp_file:
            perm_result = check_file_permissions("test_user", temp_file.name)
            assert isinstance(perm_result, bool)

        elev_result = elevate_privileges("test_user", "test operation", use_gui=False)
        assert hasattr(elev_result, "success")

        # Test singleton coordinator
        coordinator1 = get_security_coordinator()
        coordinator2 = get_security_coordinator()
        assert coordinator1 is coordinator2

        print("✅ SecurityIntegration functionality validated")
        return True

    except Exception as e:
        print(f"❌ SecurityIntegration validation failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🔒 Validating Unified Security Framework Components")
    print("=" * 60)

    tests = [
        ("Unified Security Framework", validate_unified_security_framework),
        ("Authorization Engine", validate_authorization_engine),
        ("API Security Gateway", validate_api_security_gateway),
        ("Permission Controller", validate_permission_controller),
        ("Security Integration", validate_security_integration),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"🏁 Validation Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All security framework components validated successfully!")
        print("✅ Security consolidation Phase 2D.8 completed")
        return True
    else:
        print("⚠️  Some security components need attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
