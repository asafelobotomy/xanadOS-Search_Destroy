#!/usr/bin/env python3
"""
Core functionality for S&D application.
Includes scanning engine, security, quarantine management, and performance optimization.
"""

# Scanner and ClamAV integration
from .file_scanner import FileScanner
from .clamav_wrapper import ClamAVWrapper

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

__all__ = [
    # Core scanning
    'FileScanner',
    'ClamAVWrapper',
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
    'get_loading_indicator'
]
