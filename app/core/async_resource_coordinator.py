#!/usr/bin/env python3
"""
DEPRECATED: Async Resource Coordinator Compatibility Shim
========================================================

This module provides backward compatibility for the legacy async_resource_coordinator.py.
All functionality has been consolidated into unified_threading_manager.py.

⚠️  DEPRECATION WARNING ⚠️
This shim module is deprecated and will be removed in a future version.
Please update your imports to use:
    from app.core.unified_threading_manager import get_resource_coordinator

Migration Guide:
- Replace: from app.core.async_resource_coordinator import AsyncResourceCoordinator
- With:    from app.core.unified_threading_manager import AsyncResourceCoordinator

- Replace: from app.core.async_resource_coordinator import get_resource_coordinator
- With:    from app.core.unified_threading_manager import get_resource_coordinator

- Replace: from app.core.async_resource_coordinator import ResourceType
- With:    from app.core.unified_threading_manager import ResourceType
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "app.core.async_resource_coordinator is deprecated. "
    "Use app.core.unified_threading_manager.get_resource_coordinator() instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the unified module for backward compatibility
try:
    from app.core.unified_threading_manager import (
        AsyncResourceCoordinator,
        ResourceContext,
        ResourceLimits,
        ResourceType,
        ResourceUsage,
        get_resource_coordinator,
        with_file_resource,
        with_ml_resource,
        with_resource,
        with_threat_analysis_resource,
    )
    
    # Create module-level instances for legacy compatibility
    _global_coordinator = None
    
    # All functions are available directly from the import above

except ImportError as e:
    # Fallback if unified module is not available
    warnings.warn(
        f"Failed to import from unified_threading_manager: {e}. "
        "Using minimal fallback implementation.",
        ImportWarning,
        stacklevel=2
    )
    
    # Minimal fallback implementation
    import asyncio
    from dataclasses import dataclass
    from enum import Enum
    
    class ResourceType(Enum):
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
        max_file_operations: int = 50
        max_network_connections: int = 20
        max_ml_operations: int = 5
        max_threat_analyses: int = 30
        max_database_connections: int = 10
        max_cache_operations: int = 100
        max_gpu_operations: int = 2
        max_cpu_intensive: int = 4
    
    class AsyncResourceCoordinator:
        def __init__(self):
            self.semaphores = {
                ResourceType.FILE_IO: asyncio.Semaphore(50),
                ResourceType.NETWORK: asyncio.Semaphore(20),
                ResourceType.ML_COMPUTATION: asyncio.Semaphore(5),
                ResourceType.THREAT_ANALYSIS: asyncio.Semaphore(30),
                ResourceType.DATABASE: asyncio.Semaphore(10),
                ResourceType.CACHE: asyncio.Semaphore(100),
                ResourceType.GPU: asyncio.Semaphore(2),
                ResourceType.CPU_INTENSIVE: asyncio.Semaphore(4),
            }
        
        def get_semaphore(self, resource_type: ResourceType):
            return self.semaphores.get(resource_type, asyncio.Semaphore(10))
            
        def get_file_semaphore(self):
            return self.semaphores[ResourceType.FILE_IO]
            
        def get_ml_semaphore(self):
            return self.semaphores[ResourceType.ML_COMPUTATION]
            
        def get_threat_semaphore(self):
            return self.semaphores[ResourceType.THREAT_ANALYSIS]
    
    _global_coordinator = AsyncResourceCoordinator()
    
    def get_resource_coordinator():
        return _global_coordinator

# Export the same symbols as the original module
__all__ = [
    'AsyncResourceCoordinator',
    'ResourceContext',
    'ResourceLimits',
    'ResourceType',
    'ResourceUsage',
    'get_resource_coordinator',
    'with_file_resource',
    'with_ml_resource',
    'with_resource',
    'with_threat_analysis_resource',
]