#!/usr/bin/env python3
"""
Core functionality for S&D application.
Includes scanning engine, security, quarantine management, and performance optimization.
"""

# Scanner and ClamAV integration
from .file_scanner import FileScanner
from .clamav_wrapper import ClamAVWrapper, ScanResult, ScanFileResult
from .rkhunter_wrapper import RKHunterWrapper, RKHunterResult, RKHunterScanResult

# Performance optimization components
from .async_scanner import (
    AsyncFileScanner,
    ScanProgress,
    ScanBatch,
    async_scanner
)
from .memory_optimizer import MemoryOptimizer
from .database_optimizer import (
    DatabaseConnectionPool,
    QueryOptimizer,
    ScanResultsDB,
    get_scan_db
)
from .ui_responsiveness import (
    ResponsiveUI,
    ScanProgressManager,
    LoadingIndicator,
    initialize_responsive_ui,
    get_responsive_ui,
    get_scan_progress,
    get_loading_indicator
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
    from .automatic_updates import AutoUpdateSystem, UpdateType, UpdateStatus
    from .advanced_reporting import AdvancedReportingSystem, ReportType, ReportFormat
    from .web_protection import WebProtectionSystem, ThreatCategory, URLReputation
    from .system_service import SystemServiceManager, ServiceState, ServiceConfig
    from .real_time_protection import RealTimeProtectionEngine, ProtectionState, ThreatLevel
    from .multi_language_support import MultiLanguageSupport, SupportedLanguage
    from .heuristic_analysis import HeuristicAnalysisEngine, HeuristicType, RiskLevel
    from .cloud_integration import CloudIntegrationSystem, CloudProvider, ThreatIntelSource
except ImportError as e:
    # Advanced modules may not be available due to missing dependencies
    import logging
    logging.getLogger(__name__).warning(f"Some advanced features unavailable: {e}")

__all__ = [
    # Core scanning
    'FileScanner',
    'ClamAVWrapper',
    'RKHunterWrapper',
    # Performance optimization
    'AsyncFileScanner',
    'ScanProgress', 
    'ScanBatch',
    'async_scanner',
    'MemoryOptimizer',
    'DatabaseConnectionPool',
    'QueryOptimizer',
    'ScanResultsDB',
    'get_scan_db',
    'ResponsiveUI',
    'ScanProgressManager',
    'LoadingIndicator',
    'initialize_responsive_ui',
    'get_responsive_ui',
    'get_scan_progress',
    'get_loading_indicator',
    # Advanced features (if available)
    'AutoUpdateSystem',
    'UpdateType',
    'UpdateStatus',
    'AdvancedReportingSystem',
    'ReportType',
    'ReportFormat',
    'WebProtectionSystem',
    'ThreatCategory',
    'URLReputation',
    'SystemServiceManager',
    'ServiceState',
    'ServiceConfig',
    'RealTimeProtectionEngine',
    'ProtectionState',
    'ThreatLevel',
    'MultiLanguageSupport',
    'SupportedLanguage',
    'HeuristicAnalysisEngine',
    'HeuristicType',
    'RiskLevel',
    'CloudIntegrationSystem',
    'CloudProvider',
    'ThreatIntelSource'
]
