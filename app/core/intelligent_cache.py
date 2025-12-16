#!/usr/bin/env python3
"""Intelligent LRU cache with TTL support for scan results.

This module provides an advanced caching system that combines:
- LRU (Least Recently Used) eviction policy
- TTL (Time-To-Live) automatic expiration
- Memory-bounded cache with size limits
- Hit/miss rate tracking
- Persistence to disk (SQLite)
- Thread-safe operations

Based on research from Task 1.2:
- Uses cachetools library for battle-tested implementation
- Implements TTL + LRU hybrid strategy
- Optimized for file scan result caching
- Target: 70-80% hit rate for repeated scans
"""

import hashlib
import logging
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from cachetools import TTLCache

    CACHETOOLS_AVAILABLE = True
except ImportError:
    # Fallback to basic dict if cachetools not available
    CACHETOOLS_AVAILABLE = False
    logging.warning("cachetools not installed - falling back to basic dict cache")


@dataclass
class CacheEntry:
    """Represents a cached scan result with metadata."""

    file_hash: str
    file_path: str
    scan_result: str  # "clean", "infected", "suspicious", "error"
    threat_name: str | None
    threat_level: float  # 0.0 to 1.0
    engine: str  # "clamav", "yara", "hybrid"
    timestamp: float
    signature_version: str
    file_size: int
    file_mtime: float  # File modification time
    hits: int = 0  # Number of times this entry was accessed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheEntry":
        """Create CacheEntry from dictionary."""
        return cls(**data)


class CacheStatistics:
    """Thread-safe cache statistics tracker."""

    def __init__(self):
        """Initialize statistics with thread safety."""
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
        self._memory_bytes = 0

    def record_hit(self):
        """Record cache hit."""
        with self._lock:
            self._hits += 1

    def record_miss(self):
        """Record cache miss."""
        with self._lock:
            self._misses += 1

    def record_eviction(self):
        """Record cache eviction."""
        with self._lock:
            self._evictions += 1

    def record_expiration(self):
        """Record TTL expiration."""
        with self._lock:
            self._expirations += 1

    def update_memory(self, bytes_used: int):
        """Update memory usage estimate."""
        with self._lock:
            self._memory_bytes = bytes_used

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics snapshot."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (
                (self._hits / total_requests * 100) if total_requests > 0 else 0.0
            )

            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "expirations": self._expirations,
                "hit_rate_percent": round(hit_rate, 2),
                "memory_bytes": self._memory_bytes,
                "memory_mb": round(self._memory_bytes / (1024 * 1024), 2),
            }

    def reset(self):
        """Reset all statistics."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0
            self._memory_bytes = 0


class IntelligentCache:
    """Intelligent LRU cache with TTL, persistence, and performance tracking.

    Features:
    - LRU eviction when cache is full
    - TTL-based automatic expiration
    - File modification time tracking
    - Signature version invalidation
    - Hit/miss rate statistics
    - SQLite persistence
    - Thread-safe operations
    - Memory usage monitoring

    Example:
        >>> cache = IntelligentCache(maxsize=1024, ttl_seconds=3600)
        >>> cache.set("file.txt", scan_result, threat_level=0.0)
        >>> entry = cache.get("file.txt")
        >>> stats = cache.get_statistics()
        >>> cache.save_to_disk()
    """

    def __init__(
        self,
        maxsize: int = 1024,
        ttl_seconds: int = 3600,  # 1 hour default
        signature_version: str | None = None,
        cache_file: Path | None = None,
    ):
        """Initialize intelligent cache.

        Args:
            maxsize: Maximum number of cache entries
            ttl_seconds: Time-to-live for cache entries in seconds
            signature_version: Malware signature version (for invalidation)
            cache_file: Path to SQLite cache persistence file
        """
        self.logger = logging.getLogger(__name__)
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.signature_version = signature_version or self._detect_signature_version()

        # Initialize cache backend
        if CACHETOOLS_AVAILABLE:
            # Use cachetools TTLCache (LRU + TTL hybrid)
            self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
            self.logger.info("Using cachetools.TTLCache backend")
        else:
            # Fallback to basic dict
            self._cache: dict[str, CacheEntry] = {}
            self.logger.warning("Using fallback dict cache (no TTL/LRU)")

        # Thread safety
        self._lock = threading.RLock()

        # Statistics tracking
        self.stats = CacheStatistics()

        # Persistence
        self.cache_file = (
            cache_file
            or Path.home() / ".cache" / "search-and-destroy" / "scan_cache.db"
        )
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            "IntelligentCache initialized: maxsize=%d, ttl=%ds, sig_version=%s, persistence=%s",
            maxsize,
            ttl_seconds,
            self.signature_version,
            self.cache_file,
        )

        # Load from disk if exists
        if self.cache_file.exists():
            self.load_from_disk()

    def _detect_signature_version(self) -> str:
        """Detect current malware signature version.

        Returns:
            Signature version string, or "unknown" if unavailable
        """
        try:
            from app.core.clamav_wrapper import ClamAVWrapper

            clamav = ClamAVWrapper()
            if hasattr(clamav, "get_version"):
                return clamav.get_version()
        except Exception as e:
            self.logger.debug("Could not detect signature version: %s", e)

        return "unknown"

    def _compute_cache_key(self, file_path: str | Path) -> str | None:
        """Compute cache key from file path + mtime.

        Cache key format: SHA256(file_path + mtime)
        This ensures cache is invalidated when file is modified.

        Args:
            file_path: Path to file

        Returns:
            Cache key string, or None if file doesn't exist
        """
        try:
            file_path = Path(file_path).resolve()
            if not file_path.exists():
                return None

            # Combine path and mtime for cache key
            mtime = file_path.stat().st_mtime
            key_data = f"{file_path}:{mtime}".encode()
            return hashlib.sha256(key_data).hexdigest()

        except Exception as e:
            self.logger.debug("Failed to compute cache key for %s: %s", file_path, e)
            return None

    def _compute_file_hash(self, file_path: Path) -> str | None:
        """Compute SHA256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hex digest, or None on error
        """
        try:
            if not file_path.exists():
                return None

            hasher = hashlib.sha256()
            with file_path.open("rb") as f:
                # Read in 64KB chunks for efficiency
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)

            return hasher.hexdigest()

        except Exception as e:
            self.logger.debug("Failed to hash file %s: %s", file_path, e)
            return None

    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage of cache in bytes.

        Returns:
            Estimated bytes used by cache
        """
        if not self._cache:
            return 0

        # Rough estimate: 500 bytes per entry (conservative)
        return len(self._cache) * 500

    def get(self, file_path: str | Path) -> CacheEntry | None:
        """Get cached entry for file.

        Args:
            file_path: Path to file

        Returns:
            CacheEntry if valid cached result exists, None otherwise
        """
        cache_key = self._compute_cache_key(file_path)
        if not cache_key:
            self.stats.record_miss()
            return None

        with self._lock:
            if CACHETOOLS_AVAILABLE:
                # TTLCache automatically handles expiration
                try:
                    entry = self._cache[cache_key]
                    # Check signature version
                    if entry.signature_version != self.signature_version:
                        del self._cache[cache_key]
                        self.stats.record_expiration()
                        self.stats.record_miss()
                        return None

                    entry.hits += 1
                    self.stats.record_hit()
                    self.logger.debug(
                        "Cache hit for %s (key=%s)", file_path, cache_key[:8]
                    )
                    return entry

                except KeyError:
                    # Not in cache or expired
                    self.stats.record_miss()
                    return None

            else:
                # Fallback dict - manual TTL check
                if cache_key in self._cache:
                    entry = self._cache[cache_key]

                    # Check TTL expiration
                    if time.time() - entry.timestamp > self.ttl_seconds:
                        del self._cache[cache_key]
                        self.stats.record_expiration()
                        self.stats.record_miss()
                        return None

                    # Check signature version
                    if entry.signature_version != self.signature_version:
                        del self._cache[cache_key]
                        self.stats.record_expiration()
                        self.stats.record_miss()
                        return None

                    entry.hits += 1
                    self.stats.record_hit()
                    return entry

                self.stats.record_miss()
                return None

    def set(
        self,
        file_path: str | Path,
        scan_result: str,
        threat_name: str | None = None,
        threat_level: float = 0.0,
        engine: str = "unknown",
    ) -> bool:
        """Add scan result to cache.

        Args:
            file_path: Path to scanned file
            scan_result: Scan result ("clean", "infected", "suspicious", "error")
            threat_name: Name of detected threat (if any)
            threat_level: Threat level 0.0 (safe) to 1.0 (dangerous)
            engine: Scanner engine used ("clamav", "yara", "hybrid")

        Returns:
            True if added successfully, False otherwise
        """
        try:
            file_path = Path(file_path).resolve()
            if not file_path.exists():
                return False

            cache_key = self._compute_cache_key(file_path)
            if not cache_key:
                return False

            file_hash = self._compute_file_hash(file_path)
            file_size = file_path.stat().st_size
            file_mtime = file_path.stat().st_mtime

            # Create cache entry
            entry = CacheEntry(
                file_hash=file_hash or "unknown",
                file_path=str(file_path),
                scan_result=scan_result,
                threat_name=threat_name,
                threat_level=threat_level,
                engine=engine,
                timestamp=time.time(),
                signature_version=self.signature_version,
                file_size=file_size,
                file_mtime=file_mtime,
                hits=0,
            )

            with self._lock:
                # Add to cache (eviction handled automatically by TTLCache)
                if not CACHETOOLS_AVAILABLE and len(self._cache) >= self.maxsize:
                    # Manual LRU eviction for fallback dict
                    oldest_key = min(
                        self._cache, key=lambda k: self._cache[k].timestamp
                    )
                    del self._cache[oldest_key]
                    self.stats.record_eviction()

                self._cache[cache_key] = entry
                self.stats.update_memory(self._estimate_memory_usage())

            self.logger.debug(
                "Cached result for %s: %s (key=%s)",
                file_path,
                scan_result,
                cache_key[:8],
            )
            return True

        except Exception as e:
            self.logger.error("Failed to cache result for %s: %s", file_path, e)
            return False

    def delete(self, file_path: str | Path) -> bool:
        """Delete cache entry for file.

        Args:
            file_path: Path to file

        Returns:
            True if entry was deleted, False if not found
        """
        cache_key = self._compute_cache_key(file_path)
        if not cache_key:
            return False

        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                self.stats.update_memory(self._estimate_memory_usage())
                self.logger.debug("Deleted cache entry for %s", file_path)
                return True

        return False

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self.stats.update_memory(0)
            self.logger.info("Cache cleared")

    def update_signature_version(self, new_version: str):
        """Update signature version and invalidate outdated entries.

        Args:
            new_version: New signature version
        """
        if new_version == self.signature_version:
            return

        self.logger.info(
            "Signature version updated: %s -> %s (invalidating cache)",
            self.signature_version,
            new_version,
        )

        self.signature_version = new_version

        # Invalidate all entries (they use old signatures)
        self.clear()

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            stats = self.stats.get_stats()
            stats.update(
                {
                    "entries": len(self._cache),
                    "maxsize": self.maxsize,
                    "ttl_seconds": self.ttl_seconds,
                    "signature_version": self.signature_version,
                    "backend": (
                        "cachetools.TTLCache"
                        if CACHETOOLS_AVAILABLE
                        else "dict (fallback)"
                    ),
                }
            )

        return stats

    def save_to_disk(self) -> bool:
        """Persist cache to SQLite database.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.logger.info("Saving cache to disk: %s", self.cache_file)

            # Create connection
            conn = sqlite3.connect(str(self.cache_file))
            cursor = conn.cursor()

            # Create table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    file_hash TEXT,
                    file_path TEXT,
                    scan_result TEXT,
                    threat_name TEXT,
                    threat_level REAL,
                    engine TEXT,
                    timestamp REAL,
                    signature_version TEXT,
                    file_size INTEGER,
                    file_mtime REAL,
                    hits INTEGER
                )
            """
            )

            # Clear old entries
            cursor.execute("DELETE FROM cache_entries")

            # Insert current entries
            with self._lock:
                for cache_key, entry in self._cache.items():
                    cursor.execute(
                        """
                        INSERT INTO cache_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cache_key,
                            entry.file_hash,
                            entry.file_path,
                            entry.scan_result,
                            entry.threat_name,
                            entry.threat_level,
                            entry.engine,
                            entry.timestamp,
                            entry.signature_version,
                            entry.file_size,
                            entry.file_mtime,
                            entry.hits,
                        ),
                    )

            conn.commit()
            conn.close()

            self.logger.info("Saved %d cache entries to disk", len(self._cache))
            return True

        except Exception as e:
            self.logger.error("Failed to save cache to disk: %s", e)
            return False

    def load_from_disk(self) -> int:
        """Load cache from SQLite database.

        Returns:
            Number of entries loaded
        """
        try:
            self.logger.info("Loading cache from disk: %s", self.cache_file)

            # Create connection
            conn = sqlite3.connect(str(self.cache_file))
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='cache_entries'
            """
            )

            if not cursor.fetchone():
                conn.close()
                self.logger.debug("No cache table found - starting fresh")
                return 0

            # Load entries
            cursor.execute("SELECT * FROM cache_entries")
            rows = cursor.fetchall()

            loaded = 0
            with self._lock:
                for row in rows:
                    (
                        cache_key,
                        file_hash,
                        file_path,
                        scan_result,
                        threat_name,
                        threat_level,
                        engine,
                        timestamp,
                        signature_version,
                        file_size,
                        file_mtime,
                        hits,
                    ) = row

                    # Skip expired entries
                    if time.time() - timestamp > self.ttl_seconds:
                        continue

                    # Skip entries with old signature version
                    if signature_version != self.signature_version:
                        continue

                    # Reconstruct entry
                    entry = CacheEntry(
                        file_hash=file_hash,
                        file_path=file_path,
                        scan_result=scan_result,
                        threat_name=threat_name,
                        threat_level=threat_level,
                        engine=engine,
                        timestamp=timestamp,
                        signature_version=signature_version,
                        file_size=file_size,
                        file_mtime=file_mtime,
                        hits=hits,
                    )

                    self._cache[cache_key] = entry
                    loaded += 1

                self.stats.update_memory(self._estimate_memory_usage())

            conn.close()

            self.logger.info(
                "Loaded %d cache entries from disk (skipped %d expired)",
                loaded,
                len(rows) - loaded,
            )
            return loaded

        except Exception as e:
            self.logger.error("Failed to load cache from disk: %s", e)
            return 0

    def __len__(self) -> int:
        """Return number of cache entries."""
        return len(self._cache)

    def __contains__(self, file_path: str | Path) -> bool:
        """Check if file is in cache.

        Args:
            file_path: Path to file

        Returns:
            True if file has valid cached entry, False otherwise
        """
        return self.get(file_path) is not None

    def __repr__(self) -> str:
        """String representation of cache."""
        return (
            f"IntelligentCache(entries={len(self._cache)}, "
            f"maxsize={self.maxsize}, ttl={self.ttl_seconds}s, "
            f"sig_version={self.signature_version})"
        )
