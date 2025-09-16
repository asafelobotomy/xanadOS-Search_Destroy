#!/usr/bin/env python3
"""
Unified Resource Coordinator for xanadOS Search & Destroy
Manages system resources, semaphores, and async operations coordination.
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from weakref import WeakSet

import psutil


class ResourceType(Enum):
    """Types of resources managed by the coordinator."""
    FILE_IO = "file_io"
    NETWORK = "network"
    ML_COMPUTATION = "ml_computation"
    THREAT_ANALYSIS = "threat_analysis"
    DATABASE = "database"
    CACHE = "cache"
    GPU = "gpu"
    CPU_INTENSIVE = "cpu_intensive"


@dataclass
class ResourceLimits:
    """Resource limits configuration."""
    max_file_operations: int = 50
    max_network_connections: int = 20
    max_ml_operations: int = 5
    max_threat_analyses: int = 30
    max_database_connections: int = 10
    max_cache_operations: int = 100
    max_gpu_operations: int = 2
    max_cpu_intensive: int = 4


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    active_operations: dict[ResourceType, int] = field(default_factory=dict)
    peak_usage: dict[ResourceType, int] = field(default_factory=dict)
    total_operations: dict[ResourceType, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class AsyncResourceCoordinator:
    """
    Unified coordinator for managing async resources across xanadOS components.

    Features:
    - Centralized semaphore management
    - Resource usage tracking and monitoring
    - Adaptive limits based on system resources
    - Deadlock prevention
    - Performance optimization
    """

    _instance: 'AsyncResourceCoordinator | None' = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> 'AsyncResourceCoordinator':
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        """Initialize the resource coordinator."""
        if hasattr(self, '_initialized'):
            return

        self.logger = logging.getLogger(__name__)

        # Configuration
        self.limits = limits or self._get_adaptive_limits()

        # Semaphores for different resource types
        self.semaphores: dict[ResourceType, asyncio.Semaphore] = {}
        self._initialize_semaphores()

        # Resource tracking
        self.usage = ResourceUsage()
        self._active_operations: WeakSet = WeakSet()

        # Performance monitoring
        self.start_time = time.time()
        self.monitoring_enabled = True

        # Lock for thread-safe operations
        self._stats_lock = asyncio.Lock()

        self._initialized = True
        self.logger.info("Unified resource coordinator initialized with limits: %s", self.limits)

    def _get_adaptive_limits(self) -> ResourceLimits:
        """Calculate adaptive resource limits based on system capabilities."""
        try:
            # Get system information
            cpu_count = psutil.cpu_count() or 4  # Default to 4 if None
            memory_gb = psutil.virtual_memory().total / (1024**3)

            # Adaptive calculation based on system resources
            base_multiplier = min(cpu_count / 4, memory_gb / 8)
            multiplier = max(1.0, base_multiplier)

            return ResourceLimits(
                max_file_operations=int(50 * multiplier),
                max_network_connections=int(20 * multiplier),
                max_ml_operations=min(int(5 * multiplier), cpu_count),
                max_threat_analyses=int(30 * multiplier),
                max_database_connections=int(10 * multiplier),
                max_cache_operations=int(100 * multiplier),
                max_gpu_operations=2,  # Conservative for GPU
                max_cpu_intensive=min(int(4 * multiplier), cpu_count)
            )
        except Exception as e:
            self.logger.warning("Error calculating adaptive limits: %s, using defaults", e)
            return ResourceLimits()

    def _initialize_semaphores(self) -> None:
        """Initialize semaphores for each resource type."""
        self.semaphores = {
            ResourceType.FILE_IO: asyncio.Semaphore(self.limits.max_file_operations),
            ResourceType.NETWORK: asyncio.Semaphore(self.limits.max_network_connections),
            ResourceType.ML_COMPUTATION: asyncio.Semaphore(self.limits.max_ml_operations),
            ResourceType.THREAT_ANALYSIS: asyncio.Semaphore(self.limits.max_threat_analyses),
            ResourceType.DATABASE: asyncio.Semaphore(self.limits.max_database_connections),
            ResourceType.CACHE: asyncio.Semaphore(self.limits.max_cache_operations),
            ResourceType.GPU: asyncio.Semaphore(self.limits.max_gpu_operations),
            ResourceType.CPU_INTENSIVE: asyncio.Semaphore(self.limits.max_cpu_intensive),
        }

    def acquire_resource(self, resource_type: ResourceType, operation_id: str | None = None) -> 'ResourceContext':
        """Acquire a resource with automatic tracking and cleanup."""
        return ResourceContext(self, resource_type, operation_id)

    async def _acquire_semaphore(self, resource_type: ResourceType) -> None:
        """Internal method to acquire semaphore and update stats."""
        await self.semaphores[resource_type].acquire()

        async with self._stats_lock:
            # Update usage statistics
            current = self.usage.active_operations.get(resource_type, 0)
            self.usage.active_operations[resource_type] = current + 1

            # Track peak usage
            peak = self.usage.peak_usage.get(resource_type, 0)
            if current + 1 > peak:
                self.usage.peak_usage[resource_type] = current + 1

            # Update total operations
            total = self.usage.total_operations.get(resource_type, 0)
            self.usage.total_operations[resource_type] = total + 1

            self.usage.last_updated = datetime.utcnow()

    async def _release_semaphore(self, resource_type: ResourceType) -> None:
        """Internal method to release semaphore and update stats."""
        self.semaphores[resource_type].release()

        async with self._stats_lock:
            current = self.usage.active_operations.get(resource_type, 0)
            self.usage.active_operations[resource_type] = max(0, current - 1)
            self.usage.last_updated = datetime.utcnow()

    async def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage statistics."""
        async with self._stats_lock:
            return ResourceUsage(
                active_operations=self.usage.active_operations.copy(),
                peak_usage=self.usage.peak_usage.copy(),
                total_operations=self.usage.total_operations.copy(),
                last_updated=self.usage.last_updated
            )

    async def get_system_health(self) -> dict[str, Any]:
        """Get comprehensive system health information."""
        usage = await self.get_resource_usage()

        # Calculate utilization percentages
        utilization = {}
        for resource_type, limit in [
            (ResourceType.FILE_IO, self.limits.max_file_operations),
            (ResourceType.NETWORK, self.limits.max_network_connections),
            (ResourceType.ML_COMPUTATION, self.limits.max_ml_operations),
            (ResourceType.THREAT_ANALYSIS, self.limits.max_threat_analyses),
            (ResourceType.DATABASE, self.limits.max_database_connections),
            (ResourceType.CACHE, self.limits.max_cache_operations),
            (ResourceType.GPU, self.limits.max_gpu_operations),
            (ResourceType.CPU_INTENSIVE, self.limits.max_cpu_intensive),
        ]:
            active = usage.active_operations.get(resource_type, 0)
            utilization[resource_type.value] = {
                'active': active,
                'limit': limit,
                'utilization_percent': (active / limit) * 100 if limit > 0 else 0,
                'peak': usage.peak_usage.get(resource_type, 0),
                'total': usage.total_operations.get(resource_type, 0)
            }

        return {
            'resource_utilization': utilization,
            'uptime_seconds': time.time() - self.start_time,
            'monitoring_enabled': self.monitoring_enabled,
            'last_updated': usage.last_updated.isoformat()
        }

    def get_file_semaphore(self) -> asyncio.Semaphore:
        """Get file I/O semaphore (for backward compatibility)."""
        return self.semaphores[ResourceType.FILE_IO]

    def get_ml_semaphore(self) -> asyncio.Semaphore:
        """Get ML computation semaphore (for backward compatibility)."""
        return self.semaphores[ResourceType.ML_COMPUTATION]

    def get_threat_semaphore(self) -> asyncio.Semaphore:
        """Get threat analysis semaphore (for backward compatibility)."""
        return self.semaphores[ResourceType.THREAT_ANALYSIS]


class ResourceContext:
    """Context manager for resource acquisition and release."""

    def __init__(self, coordinator: AsyncResourceCoordinator, resource_type: ResourceType, operation_id: str | None = None):
        self.coordinator = coordinator
        self.resource_type = resource_type
        self.operation_id = operation_id or f"{resource_type.value}_{id(self)}"
        self.acquired = False

    async def __aenter__(self) -> 'ResourceContext':
        """Acquire the resource."""
        await self.coordinator._acquire_semaphore(self.resource_type)
        self.acquired = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Release the resource."""
        if self.acquired:
            await self.coordinator._release_semaphore(self.resource_type)
            self.acquired = False


# Global instance
_global_coordinator: AsyncResourceCoordinator | None = None


def get_resource_coordinator() -> AsyncResourceCoordinator:
    """Get the global resource coordinator instance."""
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = AsyncResourceCoordinator()
    return _global_coordinator


# Convenience functions for common operations
def with_file_resource(operation_id: str | None = None) -> ResourceContext:
    """Context manager for file I/O operations."""
    coordinator = get_resource_coordinator()
    return coordinator.acquire_resource(ResourceType.FILE_IO, operation_id)


def with_ml_resource(operation_id: str | None = None) -> ResourceContext:
    """Context manager for ML operations."""
    coordinator = get_resource_coordinator()
    return coordinator.acquire_resource(ResourceType.ML_COMPUTATION, operation_id)


def with_threat_resource(operation_id: str | None = None) -> ResourceContext:
    """Context manager for threat analysis operations."""
    coordinator = get_resource_coordinator()
    return coordinator.acquire_resource(ResourceType.THREAT_ANALYSIS, operation_id)
