#!/usr/bin/env python3
"""
Resource Coordination and Optimization for xanadOS Search & Destroy
Manages GPU, CPU, memory, and I/O resources across all Phase 1/2 components.
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

import psutil
import torch


class ResourceType(Enum):
    """Types of system resources."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"


class Priority(Enum):
    """Resource allocation priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ResourceRequest:
    """Resource allocation request."""
    component_name: str
    resource_type: ResourceType
    priority: Priority
    amount: float  # Percentage of resource requested (0.0-1.0)
    duration_estimate: float  # Estimated duration in seconds
    callback: Callable | None = None


class ResourceCoordinator:
    """Coordinates resource usage across all security components."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Resource allocation tracking
        self.resource_locks = {
            ResourceType.CPU: threading.Semaphore(4),  # Max 4 concurrent CPU-intensive tasks
            ResourceType.MEMORY: threading.Semaphore(3),  # Max 3 concurrent memory-intensive tasks
            ResourceType.GPU: threading.Semaphore(1),  # Max 1 GPU task at a time
            ResourceType.DISK_IO: threading.Semaphore(2),  # Max 2 concurrent disk operations
            ResourceType.NETWORK_IO: threading.Semaphore(3),  # Max 3 concurrent network operations
        }

        # Active resource usage tracking
        self.active_requests: dict[ResourceType, list[ResourceRequest]] = {
            resource_type: [] for resource_type in ResourceType
        }

        # Resource usage statistics
        self.usage_stats = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "gpu_memory_percent": 0.0,
            "disk_io_percent": 0.0,
            "network_io_percent": 0.0,
        }

        # Component priorities
        self.component_priorities = {
            "edr_engine": Priority.CRITICAL,
            "ml_threat_detector": Priority.HIGH,
            "memory_forensics": Priority.HIGH,
            "deep_learning": Priority.NORMAL,
            "gpu_acceleration": Priority.NORMAL,
            "intelligent_automation": Priority.NORMAL,
            "security_dashboard": Priority.LOW,
            "web_dashboard": Priority.LOW,
            "advanced_reporting": Priority.LOW,
        }

        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()

        self.logger.info("Resource Coordinator initialized")

    def request_resource(self, request: ResourceRequest) -> bool:
        """Request allocation of a system resource."""
        component_priority = self.component_priorities.get(request.component_name, Priority.NORMAL)
        effective_priority = max(request.priority, component_priority)

        # Check if resource is available
        if not self._check_resource_availability(request.resource_type, request.amount):
            self.logger.warning(f"Resource {request.resource_type.value} not available for {request.component_name}")
            return False

        # Acquire resource lock
        resource_lock = self.resource_locks[request.resource_type]
        acquired = resource_lock.acquire(blocking=False)

        if not acquired:
            # Handle priority-based preemption if needed
            if effective_priority in [Priority.CRITICAL, Priority.HIGH]:
                acquired = self._try_preempt_resource(request.resource_type, effective_priority)

        if acquired:
            # Track the allocation
            self.active_requests[request.resource_type].append(request)
            self.logger.debug(f"Allocated {request.resource_type.value} to {request.component_name}")

            # Schedule automatic release
            if request.duration_estimate > 0:
                threading.Timer(
                    request.duration_estimate,
                    self._auto_release_resource,
                    args=[request]
                ).start()

            return True
        else:
            self.logger.warning(f"Failed to acquire {request.resource_type.value} for {request.component_name}")
            return False

    def release_resource(self, request: ResourceRequest):
        """Release a previously allocated resource."""
        try:
            # Remove from active requests
            if request in self.active_requests[request.resource_type]:
                self.active_requests[request.resource_type].remove(request)

            # Release the lock
            self.resource_locks[request.resource_type].release()

            self.logger.debug(f"Released {request.resource_type.value} from {request.component_name}")

            # Execute callback if provided
            if request.callback:
                try:
                    request.callback()
                except Exception as e:
                    self.logger.error(f"Resource release callback error: {e}")

        except Exception as e:
            self.logger.error(f"Error releasing resource: {e}")

    def _check_resource_availability(self, resource_type: ResourceType, amount: float) -> bool:
        """Check if the requested resource is available."""
        if resource_type == ResourceType.CPU:
            return self.usage_stats["cpu_percent"] + (amount * 100) < 85.0
        elif resource_type == ResourceType.MEMORY:
            return self.usage_stats["memory_percent"] + (amount * 100) < 90.0
        elif resource_type == ResourceType.GPU:
            return self.usage_stats["gpu_memory_percent"] + (amount * 100) < 95.0
        elif resource_type == ResourceType.DISK_IO:
            return self.usage_stats["disk_io_percent"] + (amount * 100) < 80.0
        elif resource_type == ResourceType.NETWORK_IO:
            return self.usage_stats["network_io_percent"] + (amount * 100) < 70.0
        return True

    def _try_preempt_resource(self, resource_type: ResourceType, priority: Priority) -> bool:
        """Try to preempt lower priority resource allocations."""
        active = self.active_requests[resource_type]

        # Find lower priority requests that can be preempted
        preemptable = [
            req for req in active
            if self.component_priorities.get(req.component_name, Priority.NORMAL).value < priority.value
        ]

        if preemptable:
            # Preempt the lowest priority request
            victim = min(preemptable, key=lambda r: self.component_priorities.get(r.component_name, Priority.NORMAL).value)

            self.logger.info(f"Preempting {victim.component_name} for higher priority request")
            self.release_resource(victim)

            return self.resource_locks[resource_type].acquire(blocking=False)

        return False

    def _auto_release_resource(self, request: ResourceRequest):
        """Automatically release resource after estimated duration."""
        if request in self.active_requests[request.resource_type]:
            self.logger.debug(f"Auto-releasing {request.resource_type.value} from {request.component_name}")
            self.release_resource(request)

    def _monitor_resources(self):
        """Monitor system resource usage continuously."""
        while self.monitoring_active:
            try:
                # Update CPU usage
                self.usage_stats["cpu_percent"] = psutil.cpu_percent(interval=1)

                # Update memory usage
                memory = psutil.virtual_memory()
                self.usage_stats["memory_percent"] = memory.percent

                # Update GPU usage if available
                if torch.cuda.is_available():
                    try:
                        gpu_memory = torch.cuda.memory_stats()
                        allocated = gpu_memory.get('allocated_bytes.all.current', 0)
                        reserved = gpu_memory.get('reserved_bytes.all.current', 0)
                        total = torch.cuda.get_device_properties(0).total_memory
                        self.usage_stats["gpu_memory_percent"] = (allocated / total) * 100 if total > 0 else 0
                    except Exception:
                        self.usage_stats["gpu_memory_percent"] = 0

                # Update disk I/O (simplified)
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    # This is a simplified metric - could be improved
                    self.usage_stats["disk_io_percent"] = min(50.0, disk_io.read_bytes / 1024 / 1024)  # MB/s approximation

                # Log high resource usage
                for resource, usage in self.usage_stats.items():
                    if usage > 80:
                        self.logger.warning(f"High {resource}: {usage:.1f}%")

                time.sleep(5)  # Monitor every 5 seconds

            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                time.sleep(10)  # Wait longer on error

    def get_resource_stats(self) -> dict[str, Any]:
        """Get current resource usage statistics."""
        return {
            "usage": self.usage_stats.copy(),
            "active_requests": {
                resource_type.value: len(requests)
                for resource_type, requests in self.active_requests.items()
            },
            "available_locks": {
                resource_type.value: self.resource_locks[resource_type]._value
                for resource_type in ResourceType
            }
        }

    def optimize_component_resources(self, component_name: str) -> dict[str, Any]:
        """Provide resource optimization recommendations for a component."""
        recommendations = {
            "priority": self.component_priorities.get(component_name, Priority.NORMAL).name,
            "suggestions": []
        }

        # General optimization suggestions based on component type
        if "ml" in component_name.lower() or "deep_learning" in component_name:
            recommendations["suggestions"].extend([
                "Consider batch processing to reduce GPU memory fragmentation",
                "Use model quantization to reduce memory usage",
                "Implement model caching to avoid repeated loading"
            ])

        if "scanner" in component_name.lower():
            recommendations["suggestions"].extend([
                "Use asynchronous I/O for file operations",
                "Implement file caching for recently scanned items",
                "Consider parallel processing with thread pools"
            ])

        if "dashboard" in component_name.lower():
            recommendations["suggestions"].extend([
                "Use lazy loading for UI components",
                "Implement data pagination for large datasets",
                "Cache frequently accessed data"
            ])

        return recommendations

    def shutdown(self):
        """Shutdown the resource coordinator."""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        # Release all active resources
        for resource_type, requests in self.active_requests.items():
            for request in requests.copy():
                self.release_resource(request)

        self.logger.info("Resource Coordinator shutdown complete")


# Convenience functions for components to use
_resource_coordinator = None


def get_resource_coordinator() -> ResourceCoordinator:
    """Get the global resource coordinator instance."""
    global _resource_coordinator
    if _resource_coordinator is None:
        _resource_coordinator = ResourceCoordinator()
    return _resource_coordinator


def request_cpu_resource(component_name: str, amount: float = 0.25, duration: float = 0) -> bool:
    """Request CPU resource allocation."""
    request = ResourceRequest(
        component_name=component_name,
        resource_type=ResourceType.CPU,
        priority=Priority.NORMAL,
        amount=amount,
        duration_estimate=duration
    )
    return get_resource_coordinator().request_resource(request)


def request_gpu_resource(component_name: str, amount: float = 0.5, duration: float = 0) -> bool:
    """Request GPU resource allocation."""
    request = ResourceRequest(
        component_name=component_name,
        resource_type=ResourceType.GPU,
        priority=Priority.NORMAL,
        amount=amount,
        duration_estimate=duration
    )
    return get_resource_coordinator().request_resource(request)


def request_memory_resource(component_name: str, amount: float = 0.2, duration: float = 0) -> bool:
    """Request memory resource allocation."""
    request = ResourceRequest(
        component_name=component_name,
        resource_type=ResourceType.MEMORY,
        priority=Priority.NORMAL,
        amount=amount,
        duration_estimate=duration
    )
    return get_resource_coordinator().request_resource(request)
