#!/usr/bin/env python3
"""
Core functionality for S&D application.
Includes scanning engine, security, quarantine management, and performance optimization.
"""

# Performance optimization components
# from .async_scanner import AsyncFileScanner, ScanBatch, ScanProgress, async_scanner  # Temporarily disabled due to import issues
from .clamav_wrapper import ClamAVWrapper, ScanFileResult, ScanResult
from .database_optimizer import (
    DatabaseConnectionPool,
    QueryOptimizer,
    ScanResultsDB,
    get_scan_db,
)

# Scanner and ClamAV integration
from .file_scanner import FileScanner
from .memory_optimizer import MemoryOptimizer
from .rate_limiting import AdaptiveRateLimiter, GlobalRateLimitManager, RateLimiter
from .rkhunter_wrapper import RKHunterResult, RKHunterScanResult, RKHunterWrapper
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
    from .real_time_protection import (
        ProtectionState,
        RealTimeProtectionEngine,
        ThreatLevel,
    )
    from .system_service import ServiceConfig, ServiceState, SystemServiceManager
    from .web_protection import ThreatCategory, URLReputation, WebProtectionSystem
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
    # Performance optimization
    "AsyncFileScanner",
    "ScanProgress",
    "ScanBatch",
    "async_scanner",
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
    "RealTimeProtectionEngine",
    "ProtectionState",
    "ThreatLevel",
    "MultiLanguageSupport",
    "SupportedLanguage",
    "HeuristicAnalysisEngine",
    "HeuristicType",
    "RiskLevel",
    "CloudIntegrationSystem",
    "CloudProvider",
    "ThreatIntelSource",
]
