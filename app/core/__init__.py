#!/usr/bin/env python3
"""
Core functionality for S&D application.
Includes scanning engine, security, quarantine management, and performance optimization.

2025 Optimizations:
- Unified Security Engine with eBPF integration
- Advanced Performance Optimizer with ML-based resource management
- Enhanced real-time protection with adaptive scaling
- Optimized component architecture for better maintainability
"""

# Core scanning and security components
from .clamav_wrapper import ClamAVWrapper, ScanFileResult, ScanResult
from .file_scanner import FileScanner
from .rkhunter_wrapper import RKHunterResult, RKHunterScanResult, RKHunterWrapper

# Unified systems (2025 optimizations)
try:
    from .unified_security_engine import (
        UnifiedSecurityEngine,
        ThreatLevel,
        ProtectionMode,
        EventType,
        SecurityEvent,
        SystemHealth
    )
    UNIFIED_SECURITY_AVAILABLE = True
except ImportError as e:
    UNIFIED_SECURITY_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Unified Security Engine unavailable: {e}")

try:
    from .unified_performance_optimizer import (
        UnifiedPerformanceOptimizer,
        PerformanceMode,
        PerformanceMetrics,
        OptimizationResult
    )
    UNIFIED_PERFORMANCE_AVAILABLE = True
except ImportError as e:
    UNIFIED_PERFORMANCE_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Unified Performance Optimizer unavailable: {e}")

# Legacy components (maintained for compatibility)
try:
    from .async_scanner import AsyncFileScanner, ScanBatch, ScanProgress
except ImportError:
    # Async scanner may have import issues, skip for now
    pass
from .rate_limiting import AdaptiveRateLimiter, GlobalRateLimitManager, RateLimiter
from .telemetry import PrivacyManager, TelemetryCollector, TelemetryManager
from .ui_responsiveness import (
    LoadingIndicator,
    ResponsiveUI,
    ScanProgressManager,
    get_loading_indicator,
    get_responsive_ui,
    get_scan_progress,
    initialize_responsive_ui,
)

# Performance optimization components (legacy fallback)
try:
    from .memory_optimizer import MemoryOptimizer
    from .database_optimizer import (
        DatabaseConnectionPool,
        QueryOptimizer,
        ScanResultsDB,
        get_scan_db,
    )
except ImportError:
    pass

# Security modules
try:
    from .input_validation import *
    from .network_security import *
    from .privilege_escalation import *
except ImportError:
    # Security modules may not be available in all environments
    pass

# Advanced feature modules (optional dependencies)
try:
    from .advanced_reporting import AdvancedReportingSystem, ReportFormat, ReportType
    from .automatic_updates import AutoUpdateSystem, UpdateStatus, UpdateType
    from .cloud_integration import (
        CloudIntegrationSystem,
        CloudProvider,
        ThreatIntelSource,
    )
    from .heuristic_analysis import HeuristicAnalysisEngine, HeuristicType, RiskLevel
    from .multi_language_support import MultiLanguageSupport, SupportedLanguage
    # Note: real_time_protection.py has been deprecated and moved to archive/
    # Its functionality has been integrated into enhanced_real_time_protection.py
    from .system_service import ServiceConfig, ServiceState, SystemServiceManager
    from .web_protection import ThreatCategory, URLReputation, WebProtectionSystem
    
    # Non-invasive monitoring system - eliminates sudo requirements for status checks
    from .non_invasive_monitor import (
        NonInvasiveSystemMonitor,
        SystemStatus,
        get_system_status,
        record_activity,
        system_monitor
    )
    from .rkhunter_monitor_non_invasive import (
        RKHunterMonitorNonInvasive,
        RKHunterStatusNonInvasive,
        get_rkhunter_status_non_invasive,
        record_rkhunter_activity,
        rkhunter_monitor
    )
except ImportError as e:
    # Advanced modules may not be available due to missing dependencies
    import logging

    logging.getLogger(__name__).warning(
        f"Some advanced features unavailable: {e}")

__all__ = [
    # Core scanning
    "FileScanner",
    "ClamAVWrapper",
    "RKHunterWrapper",
    # Rate limiting and telemetry
    "RateLimiter",
    "AdaptiveRateLimiter", 
    "GlobalRateLimitManager",
    "TelemetryCollector",
    "PrivacyManager",
    "TelemetryManager",
    # Performance optimization (legacy fallback components)
    "MemoryOptimizer",
    "DatabaseConnectionPool",
    "QueryOptimizer",
    "ScanResultsDB",
    "get_scan_db",
    "ResponsiveUI",
    "ScanProgressManager",
    "LoadingIndicator",
    "initialize_responsive_ui",
    "get_responsive_ui",
    "get_scan_progress",
    "get_loading_indicator",
    # Unified Components (2025 optimizations)
    "UnifiedSecurityEngine",
    "UnifiedPerformanceOptimizer",
    "UNIFIED_SECURITY_AVAILABLE",
    "UNIFIED_PERFORMANCE_AVAILABLE",
    "ThreatLevel",
    "ProtectionMode",
    "PerformanceMode",
    # Advanced features (if available)
    "AutoUpdateSystem",
    "UpdateType",
    "UpdateStatus",
    "AdvancedReportingSystem",
    "ReportType",
    "ReportFormat",
    "WebProtectionSystem",
    "ThreatCategory",
    "URLReputation",
    "SystemServiceManager",
    "ServiceState",
    "ServiceConfig",
    # Note: RealTimeProtectionEngine, ProtectionState, ThreatLevel deprecated
    # Functionality moved to enhanced_real_time_protection.py
    "MultiLanguageSupport",
    "SupportedLanguage",
    "HeuristicAnalysisEngine",
    "HeuristicType",
    "RiskLevel",
    "CloudIntegrationSystem",
    "CloudProvider",
    "ThreatIntelSource",
    # Non-invasive monitoring system
    "NonInvasiveSystemMonitor",
    "SystemStatus", 
    "get_system_status",
    "record_activity",
    "system_monitor",
    "RKHunterMonitorNonInvasive",
    "RKHunterStatusNonInvasive",
    "get_rkhunter_status_non_invasive",
    "record_rkhunter_activity",
    "rkhunter_monitor",
]
