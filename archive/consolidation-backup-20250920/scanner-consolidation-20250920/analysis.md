# Scanner Engine Consolidation Analysis

## Overview
4 scanner files identified for consolidation:
- file_scanner.py (1648 lines) - Traditional synchronous scanner with quarantine
- async_scanner.py (479 lines) - Basic async scanner with progress tracking
- async_scanner_engine.py (828 lines) - Comprehensive async engine with config
- advanced_async_scanner.py (700 lines) - High-performance optimizer scanner

## Functional Analysis

### file_scanner.py
**Core Classes:**
- MemoryMonitor - Memory usage tracking
- QuarantineAction, QuarantinedFile, QuarantineManager - Quarantine system
- FileScanner - Main synchronous scanner

**Key Features:**
- ClamAV integration
- Quarantine management
- Scheduling support
- Memory monitoring
- Report generation

### async_scanner.py
**Core Classes:**
- ScanProgress - Progress tracking
- ScanBatch - Batch processing
- AsyncFileScanner - Basic async scanner

**Key Features:**
- Async file scanning
- Worker threads
- Progress tracking
- Batch processing

### async_scanner_engine.py
**Core Classes:**
- ScanType, ScanStatus - Enum definitions
- ScanConfiguration, ScanStatistics, ScanProgress - Data structures
- AsyncScannerEngine - Main async engine

**Key Features:**
- Complete async architecture
- Configuration management
- Statistics tracking
- Real-time scanning support

### advanced_async_scanner.py
**Core Classes:**
- ScanPriority, ScanType - Priority/type enums
- ScanRequest, ScanResult - Request/response structures
- PerformanceMetrics - Performance tracking
- IOOptimizer - I/O optimization
- ResourceMonitor - Resource management
- ScanCache - Intelligent caching
- AdvancedAsyncScanner - High-performance scanner

**Key Features:**
- Priority-based scheduling
- Resource monitoring
- I/O optimization
- Memory-mapped file processing
- Intelligent caching

## Consolidation Strategy

### Unified Scanner Engine Components:

1. **Core Engine** (from async_scanner_engine.py)
   - AsyncScannerEngine as base
   - Configuration management
   - Status tracking

2. **Enhanced Features** (from advanced_async_scanner.py)
   - Priority scheduling
   - Resource optimization
   - Performance monitoring
   - Caching system

3. **Quarantine System** (from file_scanner.py)
   - QuarantineManager
   - Quarantine actions
   - File management

4. **Progress & Batch Processing** (from async_scanner.py)
   - Progress tracking
   - Batch operations
   - Worker management

### Consolidation Benefits:
- Unified async/await patterns
- Single configuration system
- Comprehensive feature set
- Reduced code duplication (3655 → ~1500 lines estimated)
- Better resource management

### Risk Mitigation:
- Backup all files before consolidation
- Create compatibility shims
- Maintain all public API interfaces
- Comprehensive testing

## Implementation Plan:
1. Create unified_scanner_engine.py
2. Merge core classes with modern async patterns
3. Integrate all features (quarantine, priority, caching, etc.)
4. Create backward compatibility shims
5. Test all functionality
