#!/usr/bin/env python3
"""Scan result cache for real-time protection.

Caches scan results based on file hash to avoid rescanning unchanged files.
Implements TTL-based expiration and signature version tracking.
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    """Represents a cached scan result."""

    file_hash: str
    scan_result: str  # "clean", "infected", "error"
    threat_name: str | None
    timestamp: float
    signature_version: str
    file_size: int

    def is_expired(self, ttl_seconds: int, current_sig_version: str) -> bool:
        """Check if cache entry has expired.

        Args:
            ttl_seconds: Time-to-live in seconds
            current_sig_version: Current ClamAV signature version

        Returns:
            True if expired, False otherwise
        """
        # Expired if too old
        if time.time() - self.timestamp > ttl_seconds:
            return True

        # Expired if signature version changed
        if self.signature_version != current_sig_version:
            return True

        return False


class ScanResultCache:
    """Cache for scan results to avoid rescanning unchanged files.

    Features:
    - SHA256-based file identification
    - TTL-based expiration (default 24 hours)
    - Signature version tracking
    - Thread-safe operations
    - Size-based cache management
    """

    def __init__(
        self,
        ttl_hours: int = 24,
        max_entries: int = 10000,
        signature_version: str | None = None,
    ):
        """Initialize scan result cache.

        Args:
            ttl_hours: Time-to-live for cache entries in hours
            max_entries: Maximum number of cache entries
            signature_version: ClamAV signature version (auto-detected if None)
        """
        self.logger = logging.getLogger(__name__)
        self.ttl_seconds = ttl_hours * 3600
        self.max_entries = max_entries

        # Cache storage: file_hash -> CacheEntry
        self.cache: dict[str, CacheEntry] = {}

        # Signature version for cache invalidation
        self.signature_version = signature_version or self._get_signature_version()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        self.logger.info(
            "Scan cache initialized: TTL=%d hours, max_entries=%d, sig_version=%s",
            ttl_hours,
            max_entries,
            self.signature_version,
        )

    def _get_signature_version(self) -> str:
        """Get current ClamAV signature version.

        Returns:
            Signature version string, or "unknown" if unavailable
        """
        try:
            from app.core.clamav_wrapper import ClamAVWrapper

            clamav = ClamAVWrapper()
            if hasattr(clamav, "get_version"):
                return clamav.get_version()
        except Exception:
            pass

        return "unknown"

    def _compute_hash(self, file_path: str | Path) -> str | None:
        """Compute SHA256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash as hex string, or None on error
        """
        try:
            file_path = Path(file_path)
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

    def should_scan(self, file_path: str | Path) -> bool:
        """Check if file needs scanning based on cache.

        Args:
            file_path: Path to file

        Returns:
            True if file should be scanned, False if cached result is valid
        """
        file_hash = self._compute_hash(file_path)
        if not file_hash:
            # Can't hash, must scan
            self.misses += 1
            return True

        # Check cache
        if file_hash in self.cache:
            entry = self.cache[file_hash]

            # Check if expired
            if entry.is_expired(self.ttl_seconds, self.signature_version):
                # Expired - remove and rescan
                del self.cache[file_hash]
                self.misses += 1
                self.logger.debug("Cache expired for %s", file_path)
                return True

            # Valid cache hit
            self.hits += 1
            self.logger.debug("Cache hit for %s: %s", file_path, entry.scan_result)
            return False

        # Not in cache
        self.misses += 1
        return True

    def add_result(
        self,
        file_path: str | Path,
        scan_result: str,
        threat_name: str | None = None,
    ) -> bool:
        """Add scan result to cache.

        Args:
            file_path: Path to scanned file
            scan_result: Scan result ("clean", "infected", "error")
            threat_name: Name of detected threat (if infected)

        Returns:
            True if added successfully, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False

            file_hash = self._compute_hash(file_path)
            if not file_hash:
                return False

            file_size = file_path.stat().st_size

            # Create cache entry
            entry = CacheEntry(
                file_hash=file_hash,
                scan_result=scan_result,
                threat_name=threat_name,
                timestamp=time.time(),
                signature_version=self.signature_version,
                file_size=file_size,
            )

            # Evict old entries if cache is full
            if len(self.cache) >= self.max_entries:
                self._evict_oldest()

            # Add to cache
            self.cache[file_hash] = entry
            self.logger.debug("Cached result for %s: %s", file_path, scan_result)
            return True

        except Exception as e:
            self.logger.error("Failed to cache result for %s: %s", file_path, e)
            return False

    def _evict_oldest(self):
        """Evict oldest cache entry."""
        if not self.cache:
            return

        # Find oldest entry
        oldest_hash = min(self.cache, key=lambda k: self.cache[k].timestamp)
        del self.cache[oldest_hash]
        self.evictions += 1

        self.logger.debug("Evicted oldest cache entry")

    def get_cached_result(self, file_path: str | Path) -> CacheEntry | None:
        """Get cached result for file.

        Args:
            file_path: Path to file

        Returns:
            CacheEntry if valid cached result exists, None otherwise
        """
        file_hash = self._compute_hash(file_path)
        if not file_hash:
            return None

        if file_hash in self.cache:
            entry = self.cache[file_hash]
            if not entry.is_expired(self.ttl_seconds, self.signature_version):
                return entry

        return None

    def invalidate(self, file_path: str | Path) -> bool:
        """Invalidate cache entry for file.

        Args:
            file_path: Path to file

        Returns:
            True if entry was invalidated, False if not found
        """
        file_hash = self._compute_hash(file_path)
        if not file_hash:
            return False

        if file_hash in self.cache:
            del self.cache[file_hash]
            self.logger.debug("Invalidated cache for %s", file_path)
            return True

        return False

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.logger.info("Cache cleared")

    def update_signature_version(self, new_version: str):
        """Update signature version and invalidate cache.

        Args:
            new_version: New signature version
        """
        if new_version != self.signature_version:
            self.logger.info(
                "Signature version updated: %s -> %s",
                self.signature_version,
                new_version,
            )
            self.signature_version = new_version
            # Clear cache as all entries are now invalid
            self.clear()

    def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "entries": len(self.cache),
            "max_entries": self.max_entries,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_hours": self.ttl_seconds / 3600,
            "signature_version": self.signature_version,
        }

    def __len__(self) -> int:
        """Return number of cache entries."""
        return len(self.cache)
