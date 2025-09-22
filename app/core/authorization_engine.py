#!/usr/bin/env python3
"""
Authorization Engine for Unified Security Framework

This module provides role-based access control (RBAC) and dynamic permission
management for the xanadOS Search & Destroy security framework.

Features:
- Role-based access control with hierarchical permissions
- Dynamic permission evaluation and caching
- Resource-level access control
- Policy-driven authorization decisions
- Audit trail for all authorization events
- Integration with authentication framework
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .unified_security_framework import APIPermissions, SecurityConfig


# ================== ROLE AND PERMISSION STRUCTURES ==================


class ResourceType(Enum):
    """Types of resources that can be protected."""

    THREATS = "threats"
    SYSTEM = "system"
    REPORTS = "reports"
    ANALYTICS = "analytics"
    USERS = "users"
    PERMISSIONS = "permissions"
    FILES = "files"
    QUARANTINE = "quarantine"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"


class ActionType(Enum):
    """Types of actions that can be performed on resources."""

    READ = "read"
    WRITE = "write"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    CONFIGURE = "configure"


@dataclass
class Role:
    """Role definition with hierarchical permissions."""

    name: str
    description: str
    permissions: set[str] = field(default_factory=set)
    inherits_from: set[str] = field(default_factory=set)  # Role inheritance
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_permission(self, resource: ResourceType, action: ActionType):
        """Add permission to role."""
        permission = f"{resource.value}:{action.value}"
        self.permissions.add(permission)

    def remove_permission(self, resource: ResourceType, action: ActionType):
        """Remove permission from role."""
        permission = f"{resource.value}:{action.value}"
        self.permissions.discard(permission)

    def has_permission(self, resource: ResourceType, action: ActionType) -> bool:
        """Check if role has specific permission."""
        permission = f"{resource.value}:{action.value}"
        return permission in self.permissions


@dataclass
class User:
    """User with role assignments and dynamic permissions."""

    user_id: str
    username: str
    roles: set[str] = field(default_factory=set)
    direct_permissions: set[str] = field(default_factory=set)  # Override permissions
    is_active: bool = True
    is_locked: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: datetime | None = None

    def add_role(self, role_name: str):
        """Add role to user."""
        self.roles.add(role_name)

    def remove_role(self, role_name: str):
        """Remove role from user."""
        self.roles.discard(role_name)

    def add_direct_permission(self, resource: ResourceType, action: ActionType):
        """Add direct permission to user."""
        permission = f"{resource.value}:{action.value}"
        self.direct_permissions.add(permission)


@dataclass
class PermissionPolicy:
    """Policy for dynamic permission evaluation."""

    name: str
    description: str
    resource_pattern: str  # Regex pattern for resources
    action_pattern: str  # Regex pattern for actions
    conditions: dict[str, Any] = field(default_factory=dict)
    effect: str = "allow"  # allow or deny
    priority: int = 0  # Higher priority takes precedence
    is_active: bool = True


@dataclass
class AuthorizationContext:
    """Context for authorization decisions."""

    user_id: str
    resource: str
    action: str
    request_time: datetime = field(default_factory=datetime.utcnow)
    ip_address: str | None = None
    user_agent: str | None = None
    additional_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthorizationResult:
    """Result of authorization check."""

    is_authorized: bool
    reason: str
    permissions_used: list[str] = field(default_factory=list)
    policies_applied: list[str] = field(default_factory=list)
    cached: bool = False
    evaluation_time_ms: float = 0.0


# ================== AUTHORIZATION ENGINE ==================


class AuthorizationEngine:
    """
    Role-based access control and dynamic permission evaluation engine.
    """

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AuthorizationEngine")

        # Authorization state
        self._roles: dict[str, Role] = {}
        self._users: dict[str, User] = {}
        self._policies: dict[str, PermissionPolicy] = {}
        self._permission_cache: dict[str, AuthorizationResult] = {}
        self._cache_ttl = timedelta(minutes=15)  # Cache timeout

        # Initialize system roles
        self._initialize_system_roles()

        self.logger.info("Authorization engine initialized")

    def _initialize_system_roles(self):
        """Initialize default system roles."""
        # Guest role - minimal permissions
        guest_role = Role(
            name="guest",
            description="Guest user with read-only access to basic features",
            is_system_role=True,
        )
        guest_role.add_permission(ResourceType.THREATS, ActionType.READ)
        guest_role.add_permission(ResourceType.REPORTS, ActionType.READ)

        # User role - standard user permissions
        user_role = Role(
            name="user",
            description="Standard user with basic threat management capabilities",
            inherits_from={"guest"},
            is_system_role=True,
        )
        user_role.add_permission(ResourceType.THREATS, ActionType.WRITE)
        user_role.add_permission(ResourceType.ANALYTICS, ActionType.READ)
        user_role.add_permission(ResourceType.FILES, ActionType.READ)

        # Operator role - operational permissions
        operator_role = Role(
            name="operator",
            description="Operator with quarantine and system management capabilities",
            inherits_from={"user"},
            is_system_role=True,
        )
        operator_role.add_permission(ResourceType.QUARANTINE, ActionType.CREATE)
        operator_role.add_permission(ResourceType.QUARANTINE, ActionType.DELETE)
        operator_role.add_permission(ResourceType.SYSTEM, ActionType.READ)
        operator_role.add_permission(ResourceType.FILES, ActionType.DELETE)

        # Admin role - administrative permissions
        admin_role = Role(
            name="admin",
            description="Administrator with full system access except super admin functions",
            inherits_from={"operator"},
            is_system_role=True,
        )
        admin_role.add_permission(ResourceType.USERS, ActionType.CREATE)
        admin_role.add_permission(ResourceType.USERS, ActionType.UPDATE)
        admin_role.add_permission(ResourceType.USERS, ActionType.DELETE)
        admin_role.add_permission(ResourceType.CONFIGURATION, ActionType.UPDATE)
        admin_role.add_permission(ResourceType.MONITORING, ActionType.ADMIN)

        # Super Admin role - highest privileges
        super_admin_role = Role(
            name="super_admin",
            description="Super administrator with unrestricted access",
            inherits_from={"admin"},
            is_system_role=True,
        )
        super_admin_role.add_permission(ResourceType.PERMISSIONS, ActionType.ADMIN)
        super_admin_role.add_permission(ResourceType.SYSTEM, ActionType.ADMIN)
        super_admin_role.add_permission(ResourceType.CONFIGURATION, ActionType.ADMIN)

        # Store system roles
        self._roles.update(
            {
                "guest": guest_role,
                "user": user_role,
                "operator": operator_role,
                "admin": admin_role,
                "super_admin": super_admin_role,
            }
        )

        self.logger.info(
            "Initialized system roles: guest, user, operator, admin, super_admin"
        )

    async def create_user(
        self, user_id: str, username: str, initial_roles: list[str] | None = None
    ) -> User:
        """Create new user with optional initial roles."""
        if user_id in self._users:
            raise ValueError(f"User {user_id} already exists")

        user = User(user_id=user_id, username=username)

        # Add initial roles
        if initial_roles:
            for role_name in initial_roles:
                if role_name in self._roles:
                    user.add_role(role_name)
                else:
                    self.logger.warning(
                        f"Role {role_name} not found when creating user {user_id}"
                    )

        self._users[user_id] = user
        self.logger.info(f"Created user {user_id} with roles: {initial_roles or []}")
        return user

    async def create_role(
        self,
        name: str,
        description: str,
        permissions: list[tuple[ResourceType, ActionType]] | None = None,
        inherits_from: list[str] | None = None,
    ) -> Role:
        """Create new role with specified permissions."""
        if name in self._roles:
            raise ValueError(f"Role {name} already exists")

        role = Role(
            name=name, description=description, inherits_from=set(inherits_from or [])
        )

        # Add permissions
        if permissions:
            for resource, action in permissions:
                role.add_permission(resource, action)

        self._roles[name] = role
        self.logger.info(
            f"Created role {name} with {len(permissions or [])} permissions"
        )
        return role

    async def assign_role_to_user(self, user_id: str, role_name: str):
        """Assign role to user."""
        if user_id not in self._users:
            raise ValueError(f"User {user_id} not found")
        if role_name not in self._roles:
            raise ValueError(f"Role {role_name} not found")

        user = self._users[user_id]
        user.add_role(role_name)

        # Clear permission cache for user
        self._clear_user_cache(user_id)

        self.logger.info(f"Assigned role {role_name} to user {user_id}")

    async def remove_role_from_user(self, user_id: str, role_name: str):
        """Remove role from user."""
        if user_id not in self._users:
            raise ValueError(f"User {user_id} not found")

        user = self._users[user_id]
        user.remove_role(role_name)

        # Clear permission cache for user
        self._clear_user_cache(user_id)

        self.logger.info(f"Removed role {role_name} from user {user_id}")

    async def check_permission(
        self, context: AuthorizationContext
    ) -> AuthorizationResult:
        """Check if user has permission for specific action on resource."""
        start_time = datetime.utcnow()

        # Check cache first
        cache_key = f"{context.user_id}:{context.resource}:{context.action}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            cached_result.cached = True
            return cached_result

        # Get user
        user = self._users.get(context.user_id)
        if not user:
            return AuthorizationResult(
                is_authorized=False,
                reason=f"User {context.user_id} not found",
                evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds()
                * 1000,
            )

        # Check if user is active
        if not user.is_active or user.is_locked:
            return AuthorizationResult(
                is_authorized=False,
                reason=f"User {context.user_id} is inactive or locked",
                evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds()
                * 1000,
            )

        # Collect all permissions for user
        all_permissions = await self._get_user_permissions(user)

        # Check direct permission match
        permission_key = f"{context.resource}:{context.action}"
        if permission_key in all_permissions:
            result = AuthorizationResult(
                is_authorized=True,
                reason="Direct permission match",
                permissions_used=[permission_key],
                evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds()
                * 1000,
            )
        else:
            result = AuthorizationResult(
                is_authorized=False,
                reason="No matching permissions found",
                evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds()
                * 1000,
            )

        # Apply policies for additional context-based checks
        result = await self._apply_policies(context, result)

        # Cache result
        self._cache_result(cache_key, result)

        return result

    async def _get_user_permissions(self, user: User) -> set[str]:
        """Get all permissions for user (roles + direct permissions)."""
        all_permissions = set(user.direct_permissions)

        # Add permissions from roles (with inheritance)
        processed_roles = set()
        roles_to_process = list(user.roles)

        while roles_to_process:
            role_name = roles_to_process.pop(0)
            if role_name in processed_roles:
                continue

            role = self._roles.get(role_name)
            if not role:
                self.logger.warning(
                    f"Role {role_name} not found for user {user.user_id}"
                )
                continue

            # Add role permissions
            all_permissions.update(role.permissions)
            processed_roles.add(role_name)

            # Add inherited roles to processing queue
            for inherited_role in role.inherits_from:
                if inherited_role not in processed_roles:
                    roles_to_process.append(inherited_role)

        return all_permissions

    async def _apply_policies(
        self, context: AuthorizationContext, result: AuthorizationResult
    ) -> AuthorizationResult:
        """Apply permission policies for context-based authorization."""
        # This is a simplified policy engine - in production would be more sophisticated
        # Policies could check time-based access, IP restrictions, device trust, etc.

        applied_policies = []

        # Example: Time-based access policy
        current_hour = context.request_time.hour
        if current_hour < 6 or current_hour > 22:  # Outside business hours
            # Could apply stricter permissions or deny certain actions
            applied_policies.append("after_hours_policy")

        # Example: High-privilege action requires additional validation
        if context.action in ["delete", "admin"] and result.is_authorized:
            # Could require additional authentication or approval
            applied_policies.append("high_privilege_policy")

        result.policies_applied = applied_policies
        return result

    def _get_cached_result(self, cache_key: str) -> AuthorizationResult | None:
        """Get cached authorization result if still valid."""
        if cache_key not in self._permission_cache:
            return None

        cached_result, cached_time = self._permission_cache[cache_key]
        if datetime.utcnow() - cached_time > self._cache_ttl:
            del self._permission_cache[cache_key]
            return None

        return cached_result

    def _cache_result(self, cache_key: str, result: AuthorizationResult):
        """Cache authorization result."""
        self._permission_cache[cache_key] = (result, datetime.utcnow())

    def _clear_user_cache(self, user_id: str):
        """Clear all cached results for user."""
        keys_to_remove = [
            key
            for key in self._permission_cache.keys()
            if key.startswith(f"{user_id}:")
        ]
        for key in keys_to_remove:
            del self._permission_cache[key]

    def get_user_roles(self, user_id: str) -> list[str]:
        """Get roles assigned to user."""
        user = self._users.get(user_id)
        return list(user.roles) if user else []

    def get_role_permissions(self, role_name: str) -> list[str]:
        """Get permissions for role."""
        role = self._roles.get(role_name)
        return list(role.permissions) if role else []

    def list_roles(self) -> list[str]:
        """List all available roles."""
        return list(self._roles.keys())

    def list_users(self) -> list[str]:
        """List all users."""
        return list(self._users.keys())


# ================== UTILITY FUNCTIONS ==================


def convert_api_permissions_to_context(
    user_id: str, permissions: APIPermissions
) -> list[AuthorizationContext]:
    """Convert APIPermissions to authorization contexts for compatibility."""
    contexts = []

    # Map API permissions to resource/action contexts
    permission_mapping = [
        (permissions.read_threats, ResourceType.THREATS, ActionType.READ),
        (permissions.write_threats, ResourceType.THREATS, ActionType.WRITE),
        (permissions.read_system, ResourceType.SYSTEM, ActionType.READ),
        (permissions.write_system, ResourceType.SYSTEM, ActionType.WRITE),
        (permissions.read_reports, ResourceType.REPORTS, ActionType.READ),
        (permissions.write_reports, ResourceType.REPORTS, ActionType.WRITE),
        (permissions.read_analytics, ResourceType.ANALYTICS, ActionType.READ),
        (permissions.manage_users, ResourceType.USERS, ActionType.ADMIN),
        (permissions.manage_permissions, ResourceType.PERMISSIONS, ActionType.ADMIN),
        (permissions.admin_access, ResourceType.SYSTEM, ActionType.ADMIN),
        (permissions.quarantine_files, ResourceType.QUARANTINE, ActionType.CREATE),
        (permissions.delete_files, ResourceType.FILES, ActionType.DELETE),
        (permissions.access_system_files, ResourceType.FILES, ActionType.ADMIN),
    ]

    for has_permission, resource, action in permission_mapping:
        if has_permission:
            contexts.append(
                AuthorizationContext(
                    user_id=user_id, resource=resource.value, action=action.value
                )
            )

    return contexts


# Export public API
__all__ = [
    "ActionType",
    "AuthorizationContext",
    "AuthorizationEngine",
    "AuthorizationResult",
    "PermissionPolicy",
    "ResourceType",
    "Role",
    "User",
    "convert_api_permissions_to_context",
]
