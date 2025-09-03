#!/usr/bin/env python3
"""Core functionality for S&D application.
Includes scanning engine, security, quarantine management, and performance optimization.
2025 Optimizations:
- Unified Security Engine with eBPF integration
- Advanced Performance Optimizer with ML-based resource management
- Enhanced real-time protection with adaptive scaling
- Optimized component architecture for better maintainability
"""

# Core scanning and security components
from .clamav_wrapper import ClamAVWrapper
from .file_scanner import FileScanner
from .rkhunter_wrapper import RKHunterWrapper

# Unified systems (2025 optimizations)
try:
    from .unified_security_engine import UnifiedSecurityEngine

    UNIFIED_SECURITY_AVAILABLE = True
except ImportError as e:
    UNIFIED_SECURITY_AVAILABLE = False
    import logging

    logging.getLogger(__name__).warning(f"Unified Security Engine unavailable: {e}")

try:
    from .unified_performance_optimizer import UnifiedPerformanceOptimizer

    UNIFIED_PERFORMANCE_AVAILABLE = True
except ImportError as e:
    UNIFIED_PERFORMANCE_AVAILABLE = False
    import logging

    logging.getLogger(__name__).warning(
        f"Unified Performance Optimizer unavailable: {e}"
    )

# Core components
try:
    from .async_scanner import AsyncFileScanner
except ImportError:
    # Async scanner may have import issues, skip for now
    pass
from .rate_limiting import AdaptiveRateLimiter
from .telemetry import TelemetryManager
from .ui_responsiveness import initialize_responsive_ui

# Performance optimization components
try:
    from .memory_optimizer import MemoryOptimizer
except ImportError:
    pass

# Security modules
try:
    # Optional security modules; leave imports for availability or side effects
    from .input_validation import InputValidator
    from .network_security import NetworkPolicy
    from .privilege_escalation import PrivilegeManager
except ImportError:
    # Security modules may not be available in all environments
    pass

# Advanced feature modules (optional dependencies)
try:
    from .advanced_reporting import AdvancedReportingSystem
    from .automatic_updates import AutoUpdateSystem
    from .cloud_integration import CloudIntegrationSystem
    from .heuristic_analysis import HeuristicAnalysisEngine
    from .multi_language_support import MultiLanguageSupport

    # Non-invasive monitor and rkhunter monitor kept if available
    from .non_invasive_monitor import system_monitor
    from .rkhunter_monitor_non_invasive import rkhunter_monitor
    from .system_service import SystemServiceManager
    from .web_protection import WebProtectionSystem
except ImportError as e:
    # Advanced modules may not be available due to missing dependencies
    import logging

    logging.getLogger(__name__).warning(f"Some advanced features unavailable: {e}")

__all__ = [
    "UNIFIED_PERFORMANCE_AVAILABLE",
    "UNIFIED_SECURITY_AVAILABLE",
    "AdaptiveRateLimiter",
    "AdvancedReportingSystem",
    "AutoUpdateSystem",
    "ClamAVWrapper",
    "FileScanner",
    "MemoryOptimizer",
    "RKHunterWrapper",
    "SystemServiceManager",
    "TelemetryManager",
    "UnifiedPerformanceOptimizer",
    "UnifiedSecurityEngine",
    "WebProtectionSystem",
    "initialize_responsive_ui",
    "rkhunter_monitor",
    "system_monitor",
]
