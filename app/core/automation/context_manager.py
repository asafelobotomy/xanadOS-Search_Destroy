"""
Context-Aware Decision Making for xanadOS Search & Destroy.

This module provides intelligent, context-aware automation that adapts
security policies and scanner behavior based on:
- Environment (production, development, testing)
- User role (admin, user, guest)
- Time of day (business hours, off-hours)
- Network type (LAN, VPN, remote)
- System resources (CPU load, battery status)

Phase 2, Task 2.2.4: Context-Aware Decision Making
"""

import logging
import platform
import psutil
from dataclasses import dataclass, field, asdict
from datetime import datetime, time as datetime_time
from enum import Enum
from pathlib import Path
from typing import Callable, Any
import json
import subprocess
import os

logger = logging.getLogger(__name__)


# ========================================
# Enumerations
# ========================================


class Environment(Enum):
    """Operating environment."""

    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"
    UNKNOWN = "unknown"


class UserRole(Enum):
    """User role/permission level."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    UNKNOWN = "unknown"


class TimeOfDay(Enum):
    """Time-based categories."""

    BUSINESS_HOURS = "business_hours"  # 9 AM - 6 PM
    OFF_HOURS = "off_hours"  # 6 PM - 9 AM
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


class NetworkType(Enum):
    """Network connection type."""

    LAN = "lan"  # Local area network
    VPN = "vpn"  # VPN connection
    REMOTE = "remote"  # Internet connection
    OFFLINE = "offline"  # No network
    UNKNOWN = "unknown"


class BatteryStatus(Enum):
    """Battery/power status."""

    AC_POWER = "ac"  # Plugged in
    BATTERY = "battery"  # On battery
    LOW_BATTERY = "low_battery"  # <20% battery
    UNKNOWN = "unknown"


class Priority(Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ========================================
# Data Models
# ========================================


@dataclass
class SecurityContext:
    """
    Current security context based on system state.

    This represents the complete context in which security
    operations are running, used to make intelligent decisions
    about scan intensity, resource usage, and automation behavior.
    """

    environment: str = Environment.UNKNOWN.value
    user_role: str = UserRole.UNKNOWN.value
    time_of_day: str = TimeOfDay.BUSINESS_HOURS.value
    network_type: str = NetworkType.UNKNOWN.value
    system_load: float = 0.0  # 0.0-1.0 (CPU utilization)
    battery_status: str = BatteryStatus.UNKNOWN.value
    available_memory_gb: float = 0.0
    is_interactive: bool = True  # User is actively using system
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SecurityContext":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PolicyRule:
    """
    Context-based policy rule for automation.

    Defines how the system should behave under specific
    context conditions.
    """

    rule_id: str
    name: str
    description: str
    condition: Callable[[SecurityContext], bool]
    actions: dict[str, Any]  # Configuration changes to apply
    priority: int = 0  # Higher priority rules applied first
    enabled: bool = True
    metadata: dict = field(default_factory=dict)

    def matches(self, context: SecurityContext) -> bool:
        """Check if this rule matches the given context."""
        if not self.enabled:
            return False

        try:
            return self.condition(context)
        except Exception as e:
            logger.error(f"Error evaluating rule {self.rule_id}: {e}")
            return False

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding non-serializable condition)."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }


@dataclass
class ContextChangeEvent:
    """Event representing a context change."""

    old_context: SecurityContext
    new_context: SecurityContext
    changed_fields: list[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "old_context": self.old_context.to_dict(),
            "new_context": self.new_context.to_dict(),
            "changed_fields": self.changed_fields,
            "timestamp": self.timestamp,
        }


@dataclass
class PolicyApplication:
    """Record of a policy being applied."""

    rule_id: str
    rule_name: str
    context: SecurityContext
    actions_applied: dict[str, Any]
    applied_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    user_override: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "context": self.context.to_dict(),
            "actions_applied": self.actions_applied,
            "applied_at": self.applied_at,
            "user_override": self.user_override,
        }


# ========================================
# Context Manager
# ========================================


class ContextManager:
    """
    Manages security context detection and policy application.

    Continuously monitors system state and applies context-aware
    policies to optimize security operations.
    """

    def __init__(
        self,
        audit_log_path: Path | None = None,
        enable_auto_policy: bool = True,
    ):
        """
        Initialize context manager.

        Args:
            audit_log_path: Path to audit log file (default: XDG data dir)
            enable_auto_policy: Automatically apply policies when context changes
        """
        self.current_context = SecurityContext()
        self.policy_rules: list[PolicyRule] = []
        self.enable_auto_policy = enable_auto_policy
        self.user_overrides: dict[str, Any] = {}
        self.context_history: list[ContextChangeEvent] = []
        self.policy_history: list[PolicyApplication] = []

        # Set up audit logging
        if audit_log_path is None:
            data_dir = Path.home() / ".local/share/search-and-destroy/context"
            data_dir.mkdir(parents=True, exist_ok=True)
            audit_log_path = data_dir / "audit.log"

        self.audit_log_path = audit_log_path

        # Initialize with default policies
        self._register_default_policies()

        # Detect initial context
        self.update_context()

        logger.info("ContextManager initialized")

    def _register_default_policies(self) -> None:
        """Register default context-aware policies."""

        # Policy 1: Aggressive scanning during off-hours on AC power
        self.register_policy(
            rule_id="aggressive_off_hours",
            name="Aggressive Off-Hours Scanning",
            description="Use maximum resources during off-hours on AC power",
            condition=lambda ctx: (
                ctx.time_of_day == TimeOfDay.OFF_HOURS.value
                and ctx.battery_status == BatteryStatus.AC_POWER.value
                and ctx.system_load < 0.7
            ),
            actions={
                "max_workers": 32,
                "scan_priority": Priority.HIGH.value,
                "enable_deep_scan": True,
                "cache_size_mb": 512,
            },
            priority=10,
        )

        # Policy 2: Conservative scanning on battery
        self.register_policy(
            rule_id="battery_saver",
            name="Battery Saver Mode",
            description="Reduce resource usage when on battery power",
            condition=lambda ctx: ctx.battery_status
            in (BatteryStatus.BATTERY.value, BatteryStatus.LOW_BATTERY.value),
            actions={
                "max_workers": 2,
                "scan_priority": Priority.LOW.value,
                "enable_deep_scan": False,
                "cache_size_mb": 64,
            },
            priority=20,  # Higher priority than aggressive scanning
        )

        # Policy 3: Reduced scanning during business hours
        self.register_policy(
            rule_id="business_hours",
            name="Business Hours Mode",
            description="Reduce scan intensity during active work hours",
            condition=lambda ctx: (
                ctx.time_of_day == TimeOfDay.BUSINESS_HOURS.value and ctx.is_interactive
            ),
            actions={
                "max_workers": 4,
                "scan_priority": Priority.NORMAL.value,
                "enable_deep_scan": False,
                "cache_size_mb": 128,
            },
            priority=5,
        )

        # Policy 4: High system load - throttle scanning
        self.register_policy(
            rule_id="high_system_load",
            name="High Load Throttling",
            description="Throttle scanning when system is under heavy load",
            condition=lambda ctx: ctx.system_load > 0.8,
            actions={
                "max_workers": 1,
                "scan_priority": Priority.LOW.value,
                "enable_deep_scan": False,
                "scan_delay_ms": 500,
            },
            priority=30,  # Highest priority
        )

        # Policy 5: Development environment - fast iteration
        self.register_policy(
            rule_id="dev_environment",
            name="Development Mode",
            description="Optimize for fast iteration in dev environment",
            condition=lambda ctx: ctx.environment == Environment.DEVELOPMENT.value,
            actions={
                "max_workers": 8,
                "scan_priority": Priority.NORMAL.value,
                "enable_deep_scan": False,
                "cache_size_mb": 256,
                "skip_safe_paths": True,
            },
            priority=15,
        )

        # Policy 6: Testing environment - thorough scanning
        self.register_policy(
            rule_id="test_environment",
            name="Testing Mode",
            description="Thorough scanning for testing/validation",
            condition=lambda ctx: ctx.environment == Environment.TESTING.value,
            actions={
                "max_workers": 16,
                "scan_priority": Priority.HIGH.value,
                "enable_deep_scan": True,
                "cache_size_mb": 512,
                "skip_safe_paths": False,
            },
            priority=15,
        )

        logger.info(f"Registered {len(self.policy_rules)} default policies")

    def register_policy(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition: Callable[[SecurityContext], bool],
        actions: dict[str, Any],
        priority: int = 0,
        enabled: bool = True,
    ) -> None:
        """
        Register a new context-aware policy.

        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name
            description: Description of what the rule does
            condition: Function that takes SecurityContext and returns bool
            actions: Dictionary of configuration changes to apply
            priority: Priority (higher = applied first when multiple match)
            enabled: Whether the rule is active
        """
        rule = PolicyRule(
            rule_id=rule_id,
            name=name,
            description=description,
            condition=condition,
            actions=actions,
            priority=priority,
            enabled=enabled,
        )

        # Remove existing rule with same ID
        self.policy_rules = [r for r in self.policy_rules if r.rule_id != rule_id]

        # Add new rule and sort by priority (descending)
        self.policy_rules.append(rule)
        self.policy_rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info(f"Registered policy: {name} (priority={priority})")

    def update_context(self) -> SecurityContext:
        """
        Detect current system context.

        Returns:
            Updated SecurityContext
        """
        old_context = self.current_context

        # Detect all context factors
        new_context = SecurityContext(
            environment=self._detect_environment(),
            user_role=self._detect_user_role(),
            time_of_day=self._detect_time_of_day(),
            network_type=self._detect_network_type(),
            system_load=self._detect_system_load(),
            battery_status=self._detect_battery_status(),
            available_memory_gb=self._detect_available_memory(),
            is_interactive=self._detect_interactive_session(),
        )

        # Check for changes
        changed_fields = self._get_changed_fields(old_context, new_context)

        if changed_fields:
            # Record context change event
            event = ContextChangeEvent(
                old_context=old_context,
                new_context=new_context,
                changed_fields=changed_fields,
            )
            self.context_history.append(event)

            # Log change
            logger.info(f"Context changed: {', '.join(changed_fields)}")
            self._audit_log("context_change", event.to_dict())

            # Update current context
            self.current_context = new_context

            # Apply policies if enabled
            if self.enable_auto_policy:
                self.apply_policies()

        return new_context

    def _detect_environment(self) -> str:
        """Detect operating environment."""
        # Check environment variable
        env = os.getenv("SEARCH_DESTROY_ENV", "").lower()
        if env in ("production", "prod"):
            return Environment.PRODUCTION.value
        elif env in ("development", "dev"):
            return Environment.DEVELOPMENT.value
        elif env in ("testing", "test"):
            return Environment.TESTING.value

        # Check for development indicators
        dev_indicators = [
            Path.cwd() / ".git",
            Path.cwd() / "pyproject.toml",
            Path.cwd() / "setup.py",
        ]

        if any(indicator.exists() for indicator in dev_indicators):
            return Environment.DEVELOPMENT.value

        # Default to production for safety
        return Environment.PRODUCTION.value

    def _detect_user_role(self) -> str:
        """Detect user role/permission level."""
        try:
            # Check if running as root
            if os.geteuid() == 0:
                return UserRole.ADMIN.value

            # Check if user is in sudo/admin groups
            groups_output = subprocess.run(
                ["groups"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if groups_output.returncode == 0:
                groups = groups_output.stdout.lower()
                if "sudo" in groups or "wheel" in groups or "admin" in groups:
                    return UserRole.ADMIN.value

            return UserRole.USER.value

        except Exception as e:
            logger.warning(f"Could not detect user role: {e}")
            return UserRole.UNKNOWN.value

    def _detect_time_of_day(self) -> str:
        """Detect time-based category."""
        now = datetime.now()

        # Check if weekend
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return TimeOfDay.WEEKEND.value

        # Check business hours (9 AM - 6 PM)
        business_start = datetime_time(9, 0)
        business_end = datetime_time(18, 0)
        current_time = now.time()

        if business_start <= current_time < business_end:
            return TimeOfDay.BUSINESS_HOURS.value
        else:
            return TimeOfDay.OFF_HOURS.value

    def _detect_network_type(self) -> str:
        """Detect network connection type."""
        try:
            # Check for network connectivity
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()

            # No active interfaces
            if not any(stat.isup for stat in stats.values()):
                return NetworkType.OFFLINE.value

            # Check for VPN indicators
            vpn_indicators = ["tun", "tap", "ppp", "wg"]
            for interface in stats.keys():
                if any(ind in interface.lower() for ind in vpn_indicators):
                    if stats[interface].isup:
                        return NetworkType.VPN.value

            # Check for local network
            for interface, addr_list in addrs.items():
                if not stats.get(interface, None) or not stats[interface].isup:
                    continue

                for addr in addr_list:
                    if addr.family == 2:  # AF_INET (IPv4)
                        ip = addr.address
                        # Check for private IP ranges
                        if (
                            ip.startswith("192.168.")
                            or ip.startswith("10.")
                            or ip.startswith("172.")
                        ):
                            return NetworkType.LAN.value

            # Default to remote
            return NetworkType.REMOTE.value

        except Exception as e:
            logger.warning(f"Could not detect network type: {e}")
            return NetworkType.UNKNOWN.value

    def _detect_system_load(self) -> float:
        """Detect CPU load (0.0-1.0)."""
        try:
            # Get CPU usage percentage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return cpu_percent / 100.0
        except Exception as e:
            logger.warning(f"Could not detect system load: {e}")
            return 0.0

    def _detect_battery_status(self) -> str:
        """Detect battery/power status."""
        try:
            battery = psutil.sensors_battery()

            if battery is None:
                # Desktop system with no battery
                return BatteryStatus.AC_POWER.value

            if battery.power_plugged:
                return BatteryStatus.AC_POWER.value

            # On battery - check level
            if battery.percent < 20:
                return BatteryStatus.LOW_BATTERY.value
            else:
                return BatteryStatus.BATTERY.value

        except Exception as e:
            logger.warning(f"Could not detect battery status: {e}")
            return BatteryStatus.UNKNOWN.value

    def _detect_available_memory(self) -> float:
        """Detect available memory in GB."""
        try:
            mem = psutil.virtual_memory()
            return mem.available / (1024**3)  # Convert to GB
        except Exception as e:
            logger.warning(f"Could not detect available memory: {e}")
            return 0.0

    def _detect_interactive_session(self) -> bool:
        """Detect if user is actively using the system."""
        try:
            # Check if there are active user sessions
            users = psutil.users()
            return len(users) > 0
        except Exception as e:
            logger.warning(f"Could not detect interactive session: {e}")
            return True  # Assume interactive by default

    def _get_changed_fields(
        self,
        old_context: SecurityContext,
        new_context: SecurityContext,
    ) -> list[str]:
        """Get list of fields that changed between contexts."""
        changed = []

        for field_name in [
            "environment",
            "user_role",
            "time_of_day",
            "network_type",
            "battery_status",
        ]:
            old_val = getattr(old_context, field_name)
            new_val = getattr(new_context, field_name)
            if old_val != new_val:
                changed.append(field_name)

        # Check numeric fields with threshold
        if abs(old_context.system_load - new_context.system_load) > 0.1:
            changed.append("system_load")

        if abs(old_context.available_memory_gb - new_context.available_memory_gb) > 0.5:
            changed.append("available_memory_gb")

        if old_context.is_interactive != new_context.is_interactive:
            changed.append("is_interactive")

        return changed

    def apply_policies(self, context: SecurityContext | None = None) -> dict[str, Any]:
        """
        Apply context-aware policies.

        Args:
            context: Context to apply policies for (default: current context)

        Returns:
            Dictionary of configuration changes to apply
        """
        if context is None:
            context = self.current_context

        # Find matching policies
        matching_policies = [
            rule for rule in self.policy_rules if rule.matches(context)
        ]

        if not matching_policies:
            logger.debug("No matching policies for current context")
            return {}

        # Apply highest priority policy
        policy = matching_policies[0]

        # Check for user overrides
        final_actions = policy.actions.copy()
        for key, override_value in self.user_overrides.items():
            if key in final_actions:
                final_actions[key] = override_value
                logger.info(f"User override applied: {key}={override_value}")

        # Record policy application
        application = PolicyApplication(
            rule_id=policy.rule_id,
            rule_name=policy.name,
            context=context,
            actions_applied=final_actions,
            user_override=bool(self.user_overrides),
        )

        self.policy_history.append(application)

        # Audit log
        self._audit_log("policy_applied", application.to_dict())

        logger.info(f"Applied policy: {policy.name}")

        return final_actions

    def set_user_override(self, key: str, value: Any) -> None:
        """
        Set user override for a configuration value.

        User overrides take precedence over policy-based values.

        Args:
            key: Configuration key
            value: Override value
        """
        self.user_overrides[key] = value
        logger.info(f"User override set: {key}={value}")
        self._audit_log("user_override", {"key": key, "value": value})

    def clear_user_override(self, key: str | None = None) -> None:
        """
        Clear user override(s).

        Args:
            key: Specific key to clear, or None to clear all
        """
        if key is None:
            self.user_overrides.clear()
            logger.info("Cleared all user overrides")
        elif key in self.user_overrides:
            del self.user_overrides[key]
            logger.info(f"Cleared user override: {key}")

        self._audit_log("user_override_cleared", {"key": key})

    def get_policy_by_id(self, rule_id: str) -> PolicyRule | None:
        """Get policy by ID."""
        for rule in self.policy_rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def enable_policy(self, rule_id: str) -> bool:
        """Enable a policy."""
        policy = self.get_policy_by_id(rule_id)
        if policy:
            policy.enabled = True
            logger.info(f"Enabled policy: {policy.name}")
            self._audit_log("policy_enabled", {"rule_id": rule_id})
            return True
        return False

    def disable_policy(self, rule_id: str) -> bool:
        """Disable a policy."""
        policy = self.get_policy_by_id(rule_id)
        if policy:
            policy.enabled = False
            logger.info(f"Disabled policy: {policy.name}")
            self._audit_log("policy_disabled", {"rule_id": rule_id})
            return True
        return False

    def get_active_policies(self) -> list[PolicyRule]:
        """Get all enabled policies."""
        return [rule for rule in self.policy_rules if rule.enabled]

    def get_matching_policies(
        self,
        context: SecurityContext | None = None,
    ) -> list[PolicyRule]:
        """Get policies that match the given context."""
        if context is None:
            context = self.current_context

        return [rule for rule in self.policy_rules if rule.matches(context)]

    def get_context_history(self, limit: int = 100) -> list[ContextChangeEvent]:
        """Get recent context change history."""
        return self.context_history[-limit:]

    def get_policy_history(self, limit: int = 100) -> list[PolicyApplication]:
        """Get recent policy application history."""
        return self.policy_history[-limit:]

    def _audit_log(self, event_type: str, data: dict) -> None:
        """Write event to audit log."""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "data": data,
            }

            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_statistics(self) -> dict:
        """Get statistics about context management."""
        return {
            "current_context": self.current_context.to_dict(),
            "total_policies": len(self.policy_rules),
            "enabled_policies": len(self.get_active_policies()),
            "user_overrides": len(self.user_overrides),
            "context_changes": len(self.context_history),
            "policies_applied": len(self.policy_history),
            "matching_policies": len(self.get_matching_policies()),
        }
