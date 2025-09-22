#!/usr/bin/env python3
"""
DEPRECATED: Async Threat Detector Compatibility Shim
=====================================================

This module provides backward compatibility for the legacy async_threat_detector.py.
All functionality has been consolidated into unified_threading_manager.py.

⚠️  DEPRECATION WARNING ⚠️
This shim module is deprecated and will be removed in a future version.
Please update your imports to use:
    from app.core.unified_threading_manager import AsyncThreatDetector

Migration Guide:
- Replace: from app.core.async_threat_detector import AsyncThreatDetector
- With:    from app.core.unified_threading_manager import AsyncThreatDetector

- Replace: from app.core.async_threat_detector import ThreatDetection
- With:    from app.core.unified_threading_manager import ThreatDetection

- Replace: from app.core.async_threat_detector import ThreatLevel
- With:    from app.core.unified_threading_manager import ThreatLevel
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "app.core.async_threat_detector is deprecated. "
    "Use app.core.unified_threading_manager.AsyncThreatDetector instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Import everything from the unified module for backward compatibility
try:
    from app.core.unified_threading_manager import (
        AsyncThreatDetector,
        ThreatDetection,
        ThreatLevel,
    )

except ImportError as e:
    # Fallback if unified module is not available
    warnings.warn(
        f"Failed to import from unified_threading_manager: {e}. "
        "Using minimal fallback implementation.",
        ImportWarning,
        stacklevel=2,
    )

    # Minimal fallback implementation
    import asyncio
    from collections.abc import AsyncIterator
    from dataclasses import dataclass
    from datetime import datetime
    from enum import Enum
    from pathlib import Path

    class ThreatLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    @dataclass
    class ThreatDetection:
        threat_type: str
        file_path: str
        severity: ThreatLevel
        description: str
        timestamp: datetime
        confidence: float = 0.0

    class AsyncThreatDetector:
        def __init__(self, max_workers: int = 4):
            self.max_workers = max_workers

        async def scan_file(self, file_path: Path) -> list[ThreatDetection]:
            """Minimal fallback threat scanner."""
            await asyncio.sleep(0.001)  # Minimal delay
            return []

        async def scan_directory(
            self, directory: Path
        ) -> AsyncIterator[ThreatDetection]:
            """Minimal fallback directory scanner."""
            files = list(directory.rglob("*"))
            for file_path in files:
                if file_path.is_file():
                    threats = await self.scan_file(file_path)
                    for threat in threats:
                        yield threat


# Export the same symbols as the original module
__all__ = [
    "AsyncThreatDetector",
    "ThreatDetection",
    "ThreatLevel",
]
