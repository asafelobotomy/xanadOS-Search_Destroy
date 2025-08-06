#!/usr/bin/env python3
"""
Performance module for S&D - Search & Destroy
Provides high-performance scanning and optimization features
"""

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

__all__ = [
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
