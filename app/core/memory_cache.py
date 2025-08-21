#!/usr/bin/env python3
"""
Modern Memory Cache Manager for xanadOS Search & Destroy
Implements 2025 best practices for application caching with TTL and intelligent invalidation.
"""

import time
import json
import threading
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    value: Any
    timestamp: float
    ttl: float  # Time to live in seconds
    access_count: int = 0
    last_access: float = 0.0
    
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() - self.timestamp > self.ttl
        
    def is_stale(self, stale_threshold: float = 0.8) -> bool:
        """Check if entry is getting stale (80% of TTL by default)."""
        elapsed = time.time() - self.timestamp
        return elapsed > (self.ttl * stale_threshold)
        
    def access(self):
        """Mark this entry as accessed."""
        self.access_count += 1
        self.last_access = time.time()


class ModernMemoryCache:
    """
    Modern memory cache implementation with intelligent eviction and TTL.
    
    Features:
    - TTL-based expiration
    - LRU eviction
    - Stale-while-revalidate pattern
    - Thread-safe operations
    - Access statistics
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'refreshes': 0
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with automatic cleanup."""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return default
                
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._stats['misses'] += 1
                return default
                
            # Update access statistics
            entry.access()
            self._stats['hits'] += 1
            return entry.value
            
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache with TTL."""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
                
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
                
            self._cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                last_access=time.time()
            )
            
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[float] = None) -> Any:
        """Get value or set it using a factory function."""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
        
    def is_stale(self, key: str, threshold: float = 0.8) -> bool:
        """Check if a key is stale and needs background refresh."""
        with self._lock:
            if key not in self._cache:
                return True
            return self._cache[key].is_stale(threshold)
            
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
            
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._cache:
            return
            
        # Find LRU item
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].last_access)
        del self._cache[lru_key]
        self._stats['evictions'] += 1
        
    def cleanup_expired(self) -> int:
        """Clean up expired entries and return count removed."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            return len(expired_keys)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'refreshes': self._stats['refreshes']
            }


class SystemStatusCache:
    """
    Specialized cache for system status with intelligent refresh patterns.
    Implements stale-while-revalidate for optimal user experience.
    """
    
    def __init__(self):
        self.cache = ModernMemoryCache(max_size=100, default_ttl=30)  # 30 second TTL
        self.refresh_callbacks: Dict[str, Callable] = {}
        self._background_refresh_active = set()
        
    def register_refresh_callback(self, key: str, callback: Callable):
        """Register a callback to refresh stale data."""
        self.refresh_callbacks[key] = callback
        
    def get_system_status(self, component: str, factory: Optional[Callable] = None) -> Any:
        """
        Get system status with stale-while-revalidate pattern.
        Returns cached data immediately, triggers background refresh if stale.
        """
        # Try to get cached value first
        cached_value = self.cache.get(f"status_{component}")
        
        # If we have a cached value but it's stale, trigger background refresh
        if cached_value is not None and self.cache.is_stale(f"status_{component}"):
            self._trigger_background_refresh(component)
            
        # If no cached value and we have a factory, get fresh data
        if cached_value is None and factory:
            cached_value = self._get_fresh_status(component, factory)
            
        return cached_value
        
    def set_system_status(self, component: str, status: Any, ttl: float = 30):
        """Set system status in cache."""
        self.cache.set(f"status_{component}", status, ttl)
        
    def _get_fresh_status(self, component: str, factory: Callable) -> Any:
        """Get fresh status data and cache it."""
        try:
            status = factory()
            self.set_system_status(component, status)
            return status
        except Exception as e:
            print(f"Failed to refresh {component} status: {e}")
            return None
            
    def _trigger_background_refresh(self, component: str):
        """Trigger background refresh for a component."""
        if component in self._background_refresh_active:
            return  # Already refreshing
            
        if component not in self.refresh_callbacks:
            return  # No refresh callback registered
            
        self._background_refresh_active.add(component)
        
        # Use QTimer for background refresh in Qt application
        from PyQt6.QtCore import QTimer
        
        def refresh_and_cleanup():
            try:
                callback = self.refresh_callbacks[component]
                fresh_status = callback()
                self.set_system_status(component, fresh_status)
                self.cache._stats['refreshes'] += 1
            except Exception as e:
                print(f"Background refresh failed for {component}: {e}")
            finally:
                self._background_refresh_active.discard(component)
                
        QTimer.singleShot(0, refresh_and_cleanup)
        
    def invalidate_component(self, component: str):
        """Invalidate cache for a specific component."""
        self.cache.delete(f"status_{component}")
        
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get cache performance summary."""
        stats = self.cache.get_stats()
        stats['active_refreshes'] = len(self._background_refresh_active)
        stats['registered_callbacks'] = len(self.refresh_callbacks)
        return stats


# Global cache instance
_system_cache = None

def get_system_cache() -> SystemStatusCache:
    """Get global system status cache instance."""
    global _system_cache
    if _system_cache is None:
        _system_cache = SystemStatusCache()
    return _system_cache
