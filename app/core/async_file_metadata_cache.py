#!/usr/bin/env python3
"""
File Metadata Cache for xanadOS Search & Destroy
Reduces redundant file system operations by caching file metadata.
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiofiles.os


@dataclass
class FileMetadata:
    """Cached file metadata."""
    file_path: str
    size: int
    mtime: float
    mode: int
    exists: bool
    is_file: bool
    is_dir: bool
    hash_sha256: str | None = None
    cached_at: datetime | None = None
    cache_hits: int = 0


class AsyncFileMetadataCache:
    """
    Async file metadata cache with TTL and intelligent invalidation.

    Features:
    - Automatic cache invalidation based on mtime
    - TTL-based expiration
    - Memory-efficient LRU eviction
    - Async file operations
    - Hash caching for threat detection
    """

    def __init__(
        self,
        max_entries: int = 10000,
        default_ttl: timedelta = timedelta(minutes=5),
        hash_cache_ttl: timedelta = timedelta(hours=1),
    ) -> None:
        """Initialize the file metadata cache."""
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.hash_cache_ttl = hash_cache_ttl

        # Cache storage
        self._cache: dict[str, FileMetadata] = {}
        self._access_times: dict[str, float] = {}

        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_invalidations = 0

        # Async lock for thread safety
        self._lock = asyncio.Lock()

        self.logger.info("File metadata cache initialized (max_entries=%d)", max_entries)

    async def get_file_metadata(self, file_path: str, include_hash: bool = False) -> FileMetadata | None:
        """Get file metadata from cache or filesystem."""
        async with self._lock:
            # Check cache first
            if file_path in self._cache:
                cached_metadata = self._cache[file_path]

                # Check if cache entry is still valid
                if await self._is_cache_valid(cached_metadata):
                    # Update access time and hit count
                    self._access_times[file_path] = time.time()
                    cached_metadata.cache_hits += 1
                    self.cache_hits += 1

                    # If hash is requested but not cached, compute it
                    if include_hash and not cached_metadata.hash_sha256:
                        cached_metadata.hash_sha256 = await self._compute_file_hash(file_path)

                    return cached_metadata
                else:
                    # Cache entry is invalid, remove it
                    await self._remove_from_cache(file_path)
                    self.cache_invalidations += 1

            # Cache miss - fetch from filesystem
            self.cache_misses += 1
            metadata = await self._fetch_file_metadata(file_path, include_hash)

            if metadata:
                await self._add_to_cache(file_path, metadata)

            return metadata

    async def _is_cache_valid(self, metadata: FileMetadata) -> bool:
        """Check if cached metadata is still valid."""
        try:
            # Check TTL
            if metadata.cached_at:
                age = datetime.utcnow() - metadata.cached_at
                if age > self.default_ttl:
                    return False

            # Check if file still exists
            exists = await aiofiles.os.path.exists(metadata.file_path)
            if not exists and metadata.exists:
                return False

            if exists:
                # Check mtime for changes
                try:
                    stat_result = await aiofiles.os.stat(metadata.file_path)
                    if stat_result.st_mtime != metadata.mtime:
                        return False
                except (OSError, IOError):
                    return False

            return True

        except Exception as e:
            self.logger.debug("Error validating cache entry for %s: %s", metadata.file_path, e)
            return False

    async def _fetch_file_metadata(self, file_path: str, include_hash: bool = False) -> FileMetadata | None:
        """Fetch file metadata from filesystem."""
        try:
            # Check if file exists
            exists = await aiofiles.os.path.exists(file_path)

            if not exists:
                return FileMetadata(
                    file_path=file_path,
                    size=0,
                    mtime=0.0,
                    mode=0,
                    exists=False,
                    is_file=False,
                    is_dir=False,
                    cached_at=datetime.utcnow()
                )

            # Get file stats
            stat_result = await aiofiles.os.stat(file_path)
            is_file = await aiofiles.os.path.isfile(file_path)
            is_dir = await aiofiles.os.path.isdir(file_path)

            # Compute hash if requested and it's a file
            file_hash = None
            if include_hash and is_file:
                file_hash = await self._compute_file_hash(file_path)

            return FileMetadata(
                file_path=file_path,
                size=stat_result.st_size,
                mtime=stat_result.st_mtime,
                mode=stat_result.st_mode,
                exists=True,
                is_file=is_file,
                is_dir=is_dir,
                hash_sha256=file_hash,
                cached_at=datetime.utcnow()
            )

        except (OSError, IOError, PermissionError) as e:
            self.logger.debug("Error fetching metadata for %s: %s", file_path, e)
            return None

    async def _compute_file_hash(self, file_path: str) -> str | None:
        """Compute SHA256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()

            async with aiofiles.open(file_path, 'rb') as f:
                # Read in chunks to avoid memory issues with large files
                chunk_size = 64 * 1024  # 64KB chunks
                while chunk := await f.read(chunk_size):
                    hash_sha256.update(chunk)

            return hash_sha256.hexdigest()

        except (OSError, IOError, PermissionError) as e:
            self.logger.debug("Error computing hash for %s: %s", file_path, e)
            return None

    async def _add_to_cache(self, file_path: str, metadata: FileMetadata) -> None:
        """Add metadata to cache with LRU eviction."""
        # Check if we need to evict entries
        if len(self._cache) >= self.max_entries:
            await self._evict_lru_entries(self.max_entries // 4)  # Evict 25% of cache

        # Add to cache
        self._cache[file_path] = metadata
        self._access_times[file_path] = time.time()

    async def _remove_from_cache(self, file_path: str) -> None:
        """Remove entry from cache."""
        self._cache.pop(file_path, None)
        self._access_times.pop(file_path, None)

    async def _evict_lru_entries(self, count: int) -> None:
        """Evict least recently used entries."""
        if not self._access_times:
            return

        # Sort by access time and remove oldest entries
        sorted_entries = sorted(self._access_times.items(), key=lambda x: x[1])

        for file_path, _ in sorted_entries[:count]:
            await self._remove_from_cache(file_path)

    async def invalidate_file(self, file_path: str) -> None:
        """Manually invalidate a specific file's cache entry."""
        async with self._lock:
            if file_path in self._cache:
                await self._remove_from_cache(file_path)
                self.cache_invalidations += 1

    async def invalidate_directory(self, directory_path: str) -> None:
        """Invalidate all cached entries under a directory."""
        async with self._lock:
            dir_path = Path(directory_path).resolve()
            files_to_remove = []

            for file_path in self._cache:
                try:
                    file_path_obj = Path(file_path).resolve()
                    if dir_path in file_path_obj.parents or file_path_obj == dir_path:
                        files_to_remove.append(file_path)
                except Exception:
                    continue

            for file_path in files_to_remove:
                await self._remove_from_cache(file_path)
                self.cache_invalidations += 1

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            hit_rate = (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0.0
            )

            return {
                'cache_size': len(self._cache),
                'max_entries': self.max_entries,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_invalidations': self.cache_invalidations,
                'hit_rate': hit_rate,
                'utilization': len(self._cache) / self.max_entries
            }

    async def clear_cache(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self.logger.info("File metadata cache cleared")

    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries and return count removed."""
        async with self._lock:
            expired_files = []

            for file_path, metadata in self._cache.items():
                if not await self._is_cache_valid(metadata):
                    expired_files.append(file_path)

            for file_path in expired_files:
                await self._remove_from_cache(file_path)

            self.cache_invalidations += len(expired_files)
            return len(expired_files)


# Global cache instance
_global_cache: AsyncFileMetadataCache | None = None


def get_file_metadata_cache() -> AsyncFileMetadataCache:
    """Get the global file metadata cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = AsyncFileMetadataCache()
    return _global_cache


# Convenience functions
async def get_cached_file_stats(file_path: str) -> FileMetadata | None:
    """Get cached file statistics."""
    cache = get_file_metadata_cache()
    return await cache.get_file_metadata(file_path, include_hash=False)


async def get_cached_file_hash(file_path: str) -> str | None:
    """Get cached file hash."""
    cache = get_file_metadata_cache()
    metadata = await cache.get_file_metadata(file_path, include_hash=True)
    return metadata.hash_sha256 if metadata else None


async def invalidate_cached_file(file_path: str) -> None:
    """Invalidate cached file metadata."""
    cache = get_file_metadata_cache()
    await cache.invalidate_file(file_path)
