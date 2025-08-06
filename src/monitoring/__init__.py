#!/usr/bin/env python3
"""
Real-time monitoring system for xanadOS Search & Destroy
Phase 3 implementation: Real-time file system monitoring and threat protection
"""

from .file_watcher import FileSystemWatcher, WatchEvent, WatchEventType
from .event_processor import EventProcessor, EventRule, ProcessedEvent, EventAction
from .background_scanner import BackgroundScanner, ScanTask, ScanPriority
from .real_time_monitor import RealTimeMonitor, MonitorConfig, MonitorState

__all__ = [
    'FileSystemWatcher',
    'WatchEvent', 
    'WatchEventType',
    'EventProcessor',
    'EventRule',
    'ProcessedEvent', 
    'EventAction',
    'BackgroundScanner',
    'ScanTask',
    'ScanPriority',
    'RealTimeMonitor',
    'MonitorConfig',
    'MonitorState'
]