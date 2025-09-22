#!/usr/bin/env python3
"""
Centralized Component Manager for xanadOS Search & Destroy
Manages initialization, resource allocation, and coordination of all Phase 1/2 components.
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum

from app.utils.config import get_config


class ComponentState(Enum):
    """Component lifecycle states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


@dataclass
class ComponentInfo:
    """Component metadata and state information."""
    name: str
    state: ComponentState
    instance: object | None
    dependencies: list[str]
    resource_usage: dict[str, float]
    last_error: str | None
    initialization_time: float | None


class ComponentManager:
    """Centralized manager for all security components."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()

        # Component registry
        self.components: dict[str, ComponentInfo] = {}
        self.initialization_order = [
            "memory_manager",
            "config_manager",
            "ml_threat_detector",
            "edr_engine",
            "memory_forensics",
            "intelligent_automation",
            "security_dashboard",
            "web_dashboard",
            "advanced_reporting",
            "security_api",
            "deep_learning",
            "gpu_acceleration"
        ]

        # Resource management
        self.max_concurrent_initializations = 3
        self.initialization_lock = threading.Lock()
        self.component_instances = {}

        # Callbacks
        self.state_change_callbacks = []

        self.logger.info("Component Manager initialized")

    def register_component(self, name: str, dependencies: list[str] = None):
        """Register a component for management."""
        if dependencies is None:
            dependencies = []

        self.components[name] = ComponentInfo(
            name=name,
            state=ComponentState.UNINITIALIZED,
            instance=None,
            dependencies=dependencies,
            resource_usage={},
            last_error=None,
            initialization_time=None
        )

        self.logger.debug(f"Registered component: {name}")

    def get_component(self, name: str) -> object | None:
        """Get a component instance, initializing if necessary."""
        if name not in self.components:
            self.logger.error(f"Component not registered: {name}")
            return None

        component_info = self.components[name]

        # Return existing instance if available
        if component_info.instance is not None and component_info.state == ComponentState.READY:
            return component_info.instance

        # Initialize if needed
        if component_info.state == ComponentState.UNINITIALIZED:
            self._initialize_component(name)

        return component_info.instance

    def _initialize_component(self, name: str) -> bool:
        """Initialize a specific component with dependency resolution."""
        if name not in self.components:
            self.logger.error(f"Cannot initialize unregistered component: {name}")
            return False

        component_info = self.components[name]

        if component_info.state in [ComponentState.READY, ComponentState.RUNNING]:
            return True

        with self.initialization_lock:
            # Double-check after acquiring lock
            if component_info.state in [ComponentState.READY, ComponentState.RUNNING]:
                return True

            self._set_component_state(name, ComponentState.INITIALIZING)

            try:
                start_time = time.time()

                # Initialize dependencies first
                for dep_name in component_info.dependencies:
                    if not self._initialize_component(dep_name):
                        raise RuntimeError(f"Failed to initialize dependency: {dep_name}")

                # Initialize the component
                instance = self._create_component_instance(name)
                if instance is None:
                    raise RuntimeError(f"Failed to create instance for {name}")

                component_info.instance = instance
                component_info.initialization_time = time.time() - start_time

                self._set_component_state(name, ComponentState.READY)
                self.logger.info(f"Initialized component: {name} ({component_info.initialization_time:.2f}s)")

                return True

            except Exception as e:
                error_msg = f"Failed to initialize {name}: {e}"
                self.logger.error(error_msg)
                component_info.last_error = str(e)
                self._set_component_state(name, ComponentState.ERROR)
                return False

    def _create_component_instance(self, name: str) -> object | None:
        """Create an instance of the specified component."""
        try:
            if name == "memory_manager":
                from app.core.memory_manager import get_memory_manager
                return get_memory_manager()

            elif name == "ml_threat_detector":
                from app.core.ml_threat_detector import get_threat_detector
                return get_threat_detector()

            elif name == "edr_engine":
                from app.core.edr_engine import get_edr_engine
                return get_edr_engine()

            elif name == "memory_forensics":
                from app.core.memory_forensics import get_memory_forensics
                return get_memory_forensics()

            elif name == "intelligent_automation":
                from app.core.intelligent_automation import get_intelligent_automation
                return get_intelligent_automation()

            elif name == "security_dashboard":
                # Note: GUI components are handled differently
                self.logger.info("Security dashboard initialization deferred to GUI")
                return None

            elif name == "web_dashboard":
                from app.api.web_dashboard import WebDashboard
                return WebDashboard()

            elif name == "advanced_reporting":
                from app.reporting.advanced_reporting import get_reporting_system
                return get_reporting_system()

            elif name == "security_api":
                from app.api.security_api import SecurityAPI
                return SecurityAPI()

            elif name == "deep_learning":
                from app.ml.deep_learning import get_deep_learning_detector
                return get_deep_learning_detector()

            elif name == "gpu_acceleration":
                from app.gpu.acceleration import get_gpu_accelerator
                return get_gpu_accelerator()

            else:
                self.logger.warning(f"Unknown component type: {name}")
                return None

        except ImportError as e:
            self.logger.error(f"Import error for {name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Creation error for {name}: {e}")
            return None

    def _set_component_state(self, name: str, state: ComponentState):
        """Update component state and notify callbacks."""
        if name in self.components:
            old_state = self.components[name].state
            self.components[name].state = state

            # Notify callbacks
            for callback in self.state_change_callbacks:
                try:
                    callback(name, old_state, state)
                except Exception as e:
                    self.logger.error(f"State change callback error: {e}")

    def initialize_all_components(self) -> bool:
        """Initialize all components in dependency order."""
        self.logger.info("Starting full component initialization")

        # Register all components with their dependencies
        self._register_all_components()

        success_count = 0
        total_count = len(self.components)

        for component_name in self.initialization_order:
            if component_name in self.components:
                if self._initialize_component(component_name):
                    success_count += 1
                else:
                    self.logger.error(f"Failed to initialize critical component: {component_name}")

        success_rate = success_count / total_count if total_count > 0 else 0
        self.logger.info(f"Component initialization complete: {success_count}/{total_count} ({success_rate:.1%})")

        return success_rate >= 0.8  # At least 80% success rate required

    def _register_all_components(self):
        """Register all components with their dependencies."""
        # Memory manager (no dependencies)
        self.register_component("memory_manager", [])

        # Core ML and detection (depends on memory manager)
        self.register_component("ml_threat_detector", ["memory_manager"])
        self.register_component("edr_engine", ["memory_manager"])
        self.register_component("memory_forensics", ["memory_manager"])

        # Intelligence and automation (depends on ML/EDR)
        self.register_component("intelligent_automation", ["ml_threat_detector", "edr_engine"])

        # Dashboard and UI (depends on core components)
        self.register_component("security_dashboard", ["ml_threat_detector", "edr_engine", "intelligent_automation"])
        self.register_component("web_dashboard", ["ml_threat_detector", "edr_engine", "intelligent_automation"])

        # Reporting (depends on all detection components)
        self.register_component("advanced_reporting", ["ml_threat_detector", "edr_engine", "memory_forensics"])

        # API (depends on core components)
        self.register_component("security_api", ["ml_threat_detector", "edr_engine", "intelligent_automation"])

        # Advanced ML (depends on basic ML)
        self.register_component("deep_learning", ["ml_threat_detector"])
        self.register_component("gpu_acceleration", ["deep_learning"])

    def get_component_status(self) -> dict[str, dict]:
        """Get status of all components."""
        status = {}
        for name, info in self.components.items():
            status[name] = {
                "state": info.state.value,
                "has_instance": info.instance is not None,
                "dependencies": info.dependencies,
                "last_error": info.last_error,
                "initialization_time": info.initialization_time,
                "resource_usage": info.resource_usage
            }
        return status

    def shutdown_all_components(self):
        """Shutdown all components in reverse order."""
        self.logger.info("Shutting down all components")

        # Shutdown in reverse order of initialization
        shutdown_order = list(reversed(self.initialization_order))

        for component_name in shutdown_order:
            if component_name in self.components:
                self._shutdown_component(component_name)

        self.logger.info("All components shutdown complete")

    def _shutdown_component(self, name: str):
        """Shutdown a specific component."""
        if name not in self.components:
            return

        component_info = self.components[name]

        if component_info.state in [ComponentState.SHUTDOWN, ComponentState.UNINITIALIZED]:
            return

        self._set_component_state(name, ComponentState.SHUTTING_DOWN)

        try:
            if component_info.instance and hasattr(component_info.instance, 'shutdown'):
                # Use getattr to safely call shutdown if available
                shutdown_method = getattr(component_info.instance, 'shutdown', None)
                if shutdown_method and callable(shutdown_method):
                    shutdown_method()

            component_info.instance = None
            self._set_component_state(name, ComponentState.SHUTDOWN)
            self.logger.debug(f"Shutdown component: {name}")

        except Exception as e:
            self.logger.error(f"Error shutting down {name}: {e}")


# Global instance
_component_manager = None


def get_component_manager() -> ComponentManager:
    """Get the global component manager instance."""
    global _component_manager
    if _component_manager is None:
        _component_manager = ComponentManager()
    return _component_manager


def get_component(name: str) -> object | None:
    """Convenience function to get a component instance."""
    return get_component_manager().get_component(name)
