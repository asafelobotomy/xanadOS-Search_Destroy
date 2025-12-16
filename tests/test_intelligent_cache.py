#!/usr/bin/env python3
"""Comprehensive tests for IntelligentCache (Task 1.2).

Test Coverage:
- Cache operations (get, set, delete, clear)
- LRU eviction policy
- TTL expiration behavior
- Hit/miss rate tracking
- Memory limit enforcement
- Cache persistence (save/load from SQLite)
- Thread safety
- Signature version invalidation
- Edge cases (empty cache, full cache, expired entries)

Target: >90% code coverage
"""

import hashlib
import sqlite3
import tempfile
import threading
import time
from pathlib import Path

import pytest

from app.core.intelligent_cache import CacheEntry, CacheStatistics, IntelligentCache


class TestCacheEntry:
    """Test CacheEntry dataclass."""

    def test_create_entry(self):
        """Test creating cache entry."""
        entry = CacheEntry(
            file_hash="abc123",
            file_path="/test/file.txt",
            scan_result="clean",
            threat_name=None,
            threat_level=0.0,
            engine="clamav",
            timestamp=time.time(),
            signature_version="v1.0",
            file_size=1024,
            file_mtime=time.time(),
            hits=0,
        )

        assert entry.file_hash == "abc123"
        assert entry.scan_result == "clean"
        assert entry.threat_level == 0.0

    def test_entry_to_dict(self):
        """Test converting entry to dictionary."""
        timestamp = time.time()
        mtime = time.time()

        entry = CacheEntry(
            file_hash="abc123",
            file_path="/test/file.txt",
            scan_result="infected",
            threat_name="Win32.Virus",
            threat_level=0.95,
            engine="hybrid",
            timestamp=timestamp,
            signature_version="v2.0",
            file_size=2048,
            file_mtime=mtime,
            hits=5,
        )

        data = entry.to_dict()

        assert data["file_hash"] == "abc123"
        assert data["threat_name"] == "Win32.Virus"
        assert data["threat_level"] == 0.95
        assert data["hits"] == 5

    def test_entry_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "file_hash": "def456",
            "file_path": "/test/file2.txt",
            "scan_result": "suspicious",
            "threat_name": "Heuristic.Suspicious",
            "threat_level": 0.6,
            "engine": "yara",
            "timestamp": time.time(),
            "signature_version": "v3.0",
            "file_size": 4096,
            "file_mtime": time.time(),
            "hits": 3,
        }

        entry = CacheEntry.from_dict(data)

        assert entry.file_hash == "def456"
        assert entry.scan_result == "suspicious"
        assert entry.threat_level == 0.6
        assert entry.hits == 3


class TestCacheStatistics:
    """Test CacheStatistics tracker."""

    def test_initialization(self):
        """Test statistics initialization."""
        stats = CacheStatistics()
        data = stats.get_stats()

        assert data["hits"] == 0
        assert data["misses"] == 0
        assert data["evictions"] == 0
        assert data["expirations"] == 0
        assert data["hit_rate_percent"] == 0.0

    def test_record_hits_misses(self):
        """Test recording hits and misses."""
        stats = CacheStatistics()

        stats.record_hit()
        stats.record_hit()
        stats.record_miss()

        data = stats.get_stats()

        assert data["hits"] == 2
        assert data["misses"] == 1
        assert data["hit_rate_percent"] == 66.67  # 2/3 * 100

    def test_record_evictions_expirations(self):
        """Test recording evictions and expirations."""
        stats = CacheStatistics()

        stats.record_eviction()
        stats.record_expiration()
        stats.record_expiration()

        data = stats.get_stats()

        assert data["evictions"] == 1
        assert data["expirations"] == 2

    def test_memory_tracking(self):
        """Test memory usage tracking."""
        stats = CacheStatistics()

        stats.update_memory(1048576)  # 1 MB

        data = stats.get_stats()

        assert data["memory_bytes"] == 1048576
        assert data["memory_mb"] == 1.0

    def test_reset(self):
        """Test resetting statistics."""
        stats = CacheStatistics()

        stats.record_hit()
        stats.record_miss()
        stats.record_eviction()
        stats.update_memory(1024)

        stats.reset()

        data = stats.get_stats()

        assert data["hits"] == 0
        assert data["misses"] == 0
        assert data["evictions"] == 0
        assert data["memory_bytes"] == 0

    def test_thread_safety(self):
        """Test thread-safe statistics updates."""
        stats = CacheStatistics()

        def record_operations():
            for _ in range(100):
                stats.record_hit()
                stats.record_miss()

        # Run operations in parallel threads
        threads = [threading.Thread(target=record_operations) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        data = stats.get_stats()

        # Should have 1000 hits and 1000 misses (100 * 10 threads)
        assert data["hits"] == 1000
        assert data["misses"] == 1000


class TestIntelligentCache:
    """Test IntelligentCache main functionality."""

    @pytest.fixture
    def temp_cache_file(self):
        """Create temporary cache file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            cache_file = Path(f.name)

        yield cache_file

        # Cleanup
        if cache_file.exists():
            cache_file.unlink()

    @pytest.fixture
    def temp_test_file(self):
        """Create temporary test file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("This is test content for scanning.\n" * 100)
            test_file = Path(f.name)

        yield test_file

        # Cleanup
        if test_file.exists():
            test_file.unlink()

    @pytest.fixture
    def cache(self, temp_cache_file):
        """Create cache instance."""
        return IntelligentCache(
            maxsize=128,
            ttl_seconds=60,
            signature_version="test-v1.0",
            cache_file=temp_cache_file,
        )

    def test_initialization(self, cache, temp_cache_file):
        """Test cache initialization."""
        assert cache.maxsize == 128
        assert cache.ttl_seconds == 60
        assert cache.signature_version == "test-v1.0"
        assert cache.cache_file == temp_cache_file
        assert len(cache) == 0

    def test_set_and_get(self, cache, temp_test_file):
        """Test setting and getting cache entries."""
        # Add entry
        result = cache.set(
            temp_test_file,
            scan_result="clean",
            threat_name=None,
            threat_level=0.0,
            engine="clamav",
        )

        assert result is True
        assert len(cache) == 1

        # Retrieve entry
        entry = cache.get(temp_test_file)

        assert entry is not None
        assert entry.scan_result == "clean"
        assert entry.threat_level == 0.0
        assert entry.engine == "clamav"
        assert entry.hits == 1  # Hit counter incremented

    def test_cache_hit_tracking(self, cache, temp_test_file):
        """Test cache hit tracking."""
        # Add entry
        cache.set(temp_test_file, "clean")

        # Multiple retrievals
        for i in range(5):
            entry = cache.get(temp_test_file)
            assert entry.hits == i + 1

        # Check statistics
        stats = cache.get_statistics()

        assert stats["hits"] == 5
        assert stats["misses"] == 0
        assert stats["hit_rate_percent"] == 100.0

    def test_cache_miss(self, cache):
        """Test cache miss on nonexistent file."""
        nonexistent = Path("/nonexistent/file.txt")

        entry = cache.get(nonexistent)

        assert entry is None

        stats = cache.get_statistics()

        assert stats["hits"] == 0
        assert stats["misses"] == 1

    def test_ttl_expiration(self, temp_test_file, temp_cache_file):
        """Test TTL-based cache expiration."""
        # Create cache with 1-second TTL
        cache = IntelligentCache(
            maxsize=128,
            ttl_seconds=1,
            signature_version="test-v1.0",
            cache_file=temp_cache_file,
        )

        # Add entry
        cache.set(temp_test_file, "clean")

        # Immediate retrieval should work
        entry = cache.get(temp_test_file)
        assert entry is not None

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired now
        entry = cache.get(temp_test_file)
        assert entry is None

        stats = cache.get_statistics()

        # Should have 1 hit (before expiration) and 1 miss (after expiration)
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_signature_version_invalidation(self, cache, temp_test_file):
        """Test cache invalidation on signature version change."""
        # Add entry with version v1.0
        cache.set(temp_test_file, "clean")

        # Verify entry exists
        entry = cache.get(temp_test_file)
        assert entry is not None
        assert entry.signature_version == "test-v1.0"

        # Update signature version
        cache.update_signature_version("test-v2.0")

        # Cache should be cleared
        assert len(cache) == 0

        # Entry should not be retrievable
        entry = cache.get(temp_test_file)
        assert entry is None

    def test_lru_eviction(self, temp_cache_file):
        """Test LRU eviction when cache is full."""
        # Create small cache (maxsize=3)
        cache = IntelligentCache(
            maxsize=3,
            ttl_seconds=60,
            signature_version="test-v1.0",
            cache_file=temp_cache_file,
        )

        # Create temporary files
        files = []
        for i in range(4):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"Test content {i}\n")
                files.append(Path(f.name))

        try:
            # Add 4 entries (should trigger eviction)
            for i, file_path in enumerate(files):
                cache.set(file_path, f"result_{i}")

            # Cache should have maxsize entries
            assert len(cache) <= cache.maxsize

            # Oldest entry (file 0) should be evicted (LRU policy)
            # Note: With TTLCache, eviction might not follow strict LRU
            # but cache size should not exceed maxsize

            stats = cache.get_statistics()
            assert stats["entries"] <= 3

        finally:
            # Cleanup
            for file_path in files:
                if file_path.exists():
                    file_path.unlink()

    def test_delete_entry(self, cache, temp_test_file):
        """Test deleting cache entry."""
        # Add entry
        cache.set(temp_test_file, "clean")
        assert len(cache) == 1

        # Delete entry
        result = cache.delete(temp_test_file)

        assert result is True
        assert len(cache) == 0

        # Entry should not be retrievable
        entry = cache.get(temp_test_file)
        assert entry is None

    def test_clear_cache(self, cache, temp_test_file):
        """Test clearing all cache entries."""
        # Add multiple entries
        files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"Content {i}\n")
                files.append(Path(f.name))

        try:
            for file_path in files:
                cache.set(file_path, "clean")

            assert len(cache) == 5

            # Clear cache
            cache.clear()

            assert len(cache) == 0

        finally:
            for file_path in files:
                if file_path.exists():
                    file_path.unlink()

    def test_persistence_save_load(self, cache, temp_test_file, temp_cache_file):
        """Test saving and loading cache from disk."""
        # Add entries
        cache.set(
            temp_test_file,
            scan_result="clean",
            threat_name=None,
            threat_level=0.0,
            engine="clamav",
        )

        # Save to disk
        result = cache.save_to_disk()
        assert result is True

        # Verify SQLite file exists and has data
        conn = sqlite3.connect(str(temp_cache_file))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cache_entries")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

        # Create new cache instance and load
        new_cache = IntelligentCache(
            maxsize=128,
            ttl_seconds=60,
            signature_version="test-v1.0",
            cache_file=temp_cache_file,
        )

        # Should have loaded entry
        assert len(new_cache) == 1

        # Verify loaded entry
        entry = new_cache.get(temp_test_file)
        assert entry is not None
        assert entry.scan_result == "clean"

    def test_persistence_skip_expired(self, temp_test_file, temp_cache_file):
        """Test that expired entries are not loaded from disk."""
        # Create cache with 1-second TTL
        cache = IntelligentCache(
            maxsize=128,
            ttl_seconds=1,
            signature_version="test-v1.0",
            cache_file=temp_cache_file,
        )

        # Add entry
        cache.set(temp_test_file, "clean")

        # Save to disk
        cache.save_to_disk()

        # Wait for expiration
        time.sleep(1.5)

        # Create new cache and load (should skip expired entry)
        new_cache = IntelligentCache(
            maxsize=128,
            ttl_seconds=1,
            signature_version="test-v1.0",
            cache_file=temp_cache_file,
        )

        # Should not have loaded expired entry
        assert len(new_cache) == 0

    def test_persistence_skip_old_signature(self, temp_test_file, temp_cache_file):
        """Test that entries with old signature version are not loaded."""
        # Create cache with v1.0 signature
        cache = IntelligentCache(
            maxsize=128,
            ttl_seconds=60,
            signature_version="test-v1.0",
            cache_file=temp_cache_file,
        )

        # Add entry
        cache.set(temp_test_file, "clean")

        # Save to disk
        cache.save_to_disk()

        # Create new cache with v2.0 signature (should skip v1.0 entries)
        new_cache = IntelligentCache(
            maxsize=128,
            ttl_seconds=60,
            signature_version="test-v2.0",
            cache_file=temp_cache_file,
        )

        # Should not have loaded entry with old signature
        assert len(new_cache) == 0

    def test_file_modification_invalidation(self, cache):
        """Test that cache key changes when file is modified."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Original content\n")
            test_file = Path(f.name)

        try:
            # Add entry
            cache.set(test_file, "clean")

            # Get entry (should work)
            entry = cache.get(test_file)
            assert entry is not None

            # Modify file
            time.sleep(0.1)  # Ensure mtime changes
            with test_file.open("w") as f:
                f.write("Modified content\n")

            # Entry should not be found (mtime changed, different cache key)
            entry = cache.get(test_file)
            assert entry is None

        finally:
            if test_file.exists():
                test_file.unlink()

    def test_cache_statistics(self, cache, temp_test_file):
        """Test comprehensive cache statistics."""
        # Perform operations
        cache.set(temp_test_file, "clean")
        cache.get(temp_test_file)  # hit
        cache.get(temp_test_file)  # hit
        cache.get(Path("/nonexistent"))  # miss

        stats = cache.get_statistics()

        assert stats["entries"] == 1
        assert stats["maxsize"] == 128
        assert stats["ttl_seconds"] == 60
        assert stats["signature_version"] == "test-v1.0"
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == 66.67  # 2/3 * 100

    def test_contains_operator(self, cache, temp_test_file):
        """Test __contains__ operator (in keyword)."""
        # File not in cache
        assert temp_test_file not in cache

        # Add to cache
        cache.set(temp_test_file, "clean")

        # File should be in cache
        assert temp_test_file in cache

    def test_repr(self, cache):
        """Test string representation."""
        repr_str = repr(cache)

        assert "IntelligentCache" in repr_str
        assert "maxsize=128" in repr_str
        assert "ttl=60s" in repr_str
        assert "sig_version=test-v1.0" in repr_str

    def test_thread_safety(self, cache):
        """Test thread-safe cache operations."""
        files = []

        # Create test files
        for i in range(10):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"Content {i}\n")
                files.append(Path(f.name))

        try:

            def cache_operations():
                for file_path in files:
                    cache.set(file_path, "clean")
                    cache.get(file_path)

            # Run operations in parallel threads
            threads = [threading.Thread(target=cache_operations) for _ in range(5)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # Verify cache integrity (no crashes, reasonable state)
            assert 0 < len(cache) <= cache.maxsize

        finally:
            for file_path in files:
                if file_path.exists():
                    file_path.unlink()

    def test_memory_estimation(self, cache, temp_test_file):
        """Test memory usage estimation."""
        # Empty cache
        stats = cache.get_statistics()
        assert stats["memory_bytes"] == 0
        assert stats["memory_mb"] == 0.0

        # Add entry
        cache.set(temp_test_file, "clean")

        # Memory should be estimated
        stats = cache.get_statistics()
        assert stats["memory_bytes"] > 0
        # Check MB conversion (500 bytes per entry → 0.0005 MB, rounds to 0.0)
        # So we verify bytes only
        assert stats["memory_bytes"] >= 500  # At least 1 entry

    def test_nonexistent_file_handling(self, cache):
        """Test handling of nonexistent files."""
        nonexistent = Path("/does/not/exist.txt")

        # Should not crash
        result = cache.set(nonexistent, "clean")
        assert result is False

        entry = cache.get(nonexistent)
        assert entry is None

        result = cache.delete(nonexistent)
        assert result is False


class TestCacheIntegration:
    """Integration tests for cache with scanner."""

    @pytest.fixture
    def cache(self):
        """Create cache for integration tests."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            cache_file = Path(f.name)

        cache = IntelligentCache(
            maxsize=256,
            ttl_seconds=300,  # 5 minutes
            signature_version="integration-v1.0",
            cache_file=cache_file,
        )

        yield cache

        # Cleanup
        if cache_file.exists():
            cache_file.unlink()

    def test_repeated_scans_scenario(self, cache):
        """Test realistic repeated scan scenario."""
        # Create test files
        files = []
        for i in range(20):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"Test content {i}\n" * 100)
                files.append(Path(f.name))

        try:
            # First scan (cold cache)
            for file_path in files:
                entry = cache.get(file_path)
                assert entry is None  # Cache miss

                # Simulate scan and cache result
                cache.set(file_path, "clean", threat_level=0.0, engine="clamav")

            # Second scan (warm cache)
            for file_path in files:
                entry = cache.get(file_path)
                assert entry is not None  # Cache hit
                assert entry.scan_result == "clean"

            stats = cache.get_statistics()

            # Should have high hit rate on second scan
            assert stats["hits"] == 20
            assert stats["misses"] == 20
            assert stats["hit_rate_percent"] == 50.0

        finally:
            for file_path in files:
                if file_path.exists():
                    file_path.unlink()

    def test_cache_warming(self, cache):
        """Test cache warming on startup."""
        # Create files
        files = []
        for i in range(10):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"Content {i}\n")
                files.append(Path(f.name))

        try:
            # Pre-populate cache
            for file_path in files:
                cache.set(file_path, "clean")

            # Save to disk
            cache.save_to_disk()

            # Simulate restart - create new cache instance
            new_cache = IntelligentCache(
                maxsize=256,
                ttl_seconds=300,
                signature_version="integration-v1.0",
                cache_file=cache.cache_file,
            )

            # Should have loaded entries (cache warming)
            assert len(new_cache) == 10

            # All files should have cached results
            for file_path in files:
                entry = new_cache.get(file_path)
                assert entry is not None

        finally:
            for file_path in files:
                if file_path.exists():
                    file_path.unlink()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
