# API Compatibility Mapping for Core Consolidation

## Risk Mitigation: API Backward Compatibility

This document maps existing public APIs to ensure no breaking changes during consolidation.

## Memory Management Consolidation

### Source Files to Consolidate:
- `memory_manager.py` (650 lines)
- `memory_optimizer.py` (342 lines)
- `memory_cache.py` (249 lines)
- `memory_forensics.py` (forensics components)

### Target: `unified_memory_management.py`

## Public API Mapping

### memory_manager.py APIs to Preserve:
```python
# Classes
class MemoryPressureLevel(Enum)
class MemoryPool
class MemoryStats
class CacheManager
class AdvancedMemoryManager

# Functions
def get_memory_manager() -> AdvancedMemoryManager
```

### memory_optimizer.py APIs to Preserve:
```python
# Classes
class MemoryStats
class MemoryPool
class StreamProcessor
class MemoryOptimizer
class CacheManager

# Module-level instances
memory_optimizer: MemoryOptimizer
cache_manager: CacheManager
```

### memory_cache.py APIs to Preserve:
```python
# Classes
class CacheEntry
class ModernMemoryCache
class SystemStatusCache

# Functions
def get_system_cache() -> SystemStatusCache
```

## Backward Compatibility Strategy

### Import Shims (Temporary)
Create import compatibility shims in original file locations:

**memory_manager.py (shim)**:
```python
# Backward compatibility shim
from .unified_memory_management import (
    MemoryPressureLevel,
    MemoryPool,
    MemoryStats,
    CacheManager,
    AdvancedMemoryManager,
    get_memory_manager
)

# Deprecation warnings
import warnings
warnings.warn(
    "memory_manager.py is deprecated. Use unified_memory_management.py",
    DeprecationWarning,
    stacklevel=2
)
```

**memory_optimizer.py (shim)**:
```python
# Backward compatibility shim
from .unified_memory_management import (
    MemoryStats,
    MemoryPool,
    StreamProcessor,
    MemoryOptimizer,
    CacheManager,
    get_memory_optimizer,
    get_cache_manager
)

# Maintain module-level instances
memory_optimizer = get_memory_optimizer()
cache_manager = get_cache_manager()
```

**memory_cache.py (shim)**:
```python
# Backward compatibility shim
from .unified_memory_management import (
    CacheEntry,
    ModernMemoryCache,
    SystemStatusCache,
    get_system_cache
)
```

## Scanner Engine Consolidation

### Source Files to Consolidate:
- `async_scanner.py` (480 lines)
- `async_scanner_engine.py` (780 lines)
- `advanced_async_scanner.py` (650 lines)
- Scanner components from `file_scanner.py`

### Target: `unified_scanner_engine.py`

### Public API Mapping

#### async_scanner.py APIs to Preserve:
```python
# Classes
class AsyncFileScanner
class ScanProgress

# Functions
def get_async_scanner() -> AsyncFileScanner
```

#### async_scanner_engine.py APIs to Preserve:
```python
# Classes
class AsyncScannerEngine
class ScanConfiguration
class ScanStatistics
class ScanProgress
class ScanResult
```

#### advanced_async_scanner.py APIs to Preserve:
```python
# Classes
class AdvancedAsyncScanner
class ScanPriority
class ScanRequest
class ScanResult
class PerformanceMetrics
```

## RKHunter Consolidation

### Source Files to Consolidate:
- `rkhunter_monitor_enhanced.py` (600+ lines)
- `rkhunter_monitor_non_invasive.py` (400+ lines)
- `rkhunter_optimizer.py` (1100+ lines)
- `rkhunter_wrapper.py`
- `rkhunter_analyzer.py`

### Target: `unified_rkhunter_engine.py`

### Critical Issue: Duplicate Classes
**CONFLICT**: `RKHunterMonitorNonInvasive` exists in both:
- `rkhunter_monitor_enhanced.py` (line 598)
- `rkhunter_monitor_non_invasive.py` (line 60)

**Resolution**: Merge implementations, prefer the more comprehensive version.

## Validation Checkpoints

### Pre-Consolidation Validation:
1. All existing imports documented ✓
2. Public API surface mapped ✓
3. Backward compatibility shims designed ✓
4. Conflict resolution strategy defined ✓

### Post-Consolidation Validation:
1. All original imports still work
2. Module-level instances preserved
3. Function signatures unchanged
4. Class hierarchies maintained
5. Deprecation warnings active

## Testing Strategy

### Import Testing:
```python
# Test all original imports still work
import app.core.memory_manager
import app.core.memory_optimizer
import app.core.memory_cache

# Test consolidated imports work
import app.core.unified_memory_management

# Test backward compatibility
manager = app.core.memory_manager.get_memory_manager()
optimizer = app.core.memory_optimizer.memory_optimizer
cache = app.core.memory_cache.get_system_cache()
```

### Functional Testing:
```python
# Test all major operations still work
def test_memory_consolidation():
    # Original API paths
    old_manager = memory_manager.AdvancedMemoryManager()
    old_cache = memory_cache.ModernMemoryCache()

    # New unified API
    new_manager = unified_memory_management.UnifiedMemoryManager()

    # Verify equivalent functionality
    assert old_manager.get_memory_usage() == new_manager.get_memory_usage()
```

## Risk Assessment

### LOW RISK:
- Memory management consolidation (well-defined APIs)
- Cache management unification (clear boundaries)

### MEDIUM RISK:
- Scanner engine consolidation (multiple async patterns)
- File watcher consolidation (event handling complexity)

### HIGH RISK:
- RKHunter consolidation (duplicate class conflicts)
- Protection framework consolidation (security implications)

## Rollback Plan

If consolidation causes issues:
1. Restore from `consolidation-backup/20250920-131606/core-original/`
2. Remove consolidated files
3. Restore original shim files
4. Run validation tests
5. Report issues and plan fixes

## Next Steps

1. ✓ API mapping complete
2. → Begin Memory Management consolidation
3. → Implement backward compatibility shims
4. → Test consolidated functionality
5. → Validate performance improvements
