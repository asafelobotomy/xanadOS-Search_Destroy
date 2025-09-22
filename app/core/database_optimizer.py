#!/usr/bin/env python3
"""Database optimization module for xanadOS Search & Destroy
Provides efficient database operations and connection management
"""

import logging
import queue
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils.config import load_config


@dataclass
class QueryStats:
    """Database query performance statistics."""

    query_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    slowest_query: str = ""
    slowest_time: float = 0.0


class DatabaseConnectionPool:
    """Thread-safe database connection pool with automatic management."""

    def __init__(
        self,
        database_path: str,
        max_connections: int = 5,
        timeout: float = 30.0,
    ):
        """Initialize connection pool.

        Args:
            database_path: Path to SQLite database file
            max_connections: Maximum number of connections in pool
            timeout: Connection timeout in seconds

        """
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout

        self.pool = queue.Queue(maxsize=max_connections)
        self.created_connections = 0
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

        # Initialize pool with connections
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            # Ensure database directory exists
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

            # Create initial connections
            for _ in range(min(2, self.max_connections)):  # Start with 2 connections
                conn = self._create_connection()
                if conn:
                    self.pool.put(conn)

        except Exception:
            # Log full stack for easier diagnostics
            self.logger.exception("Failed to initialize connection pool")

    def _create_connection(self) -> sqlite3.Connection | None:
        """Create a new database connection."""
        try:
            conn = sqlite3.connect(
                self.database_path,
                timeout=self.timeout,
                check_same_thread=False,
            )

            # Configure connection for performance
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL
            conn.execute("PRAGMA cache_size=10000")  # 10MB cache
            conn.execute("PRAGMA temp_store=MEMORY")  # Temp tables in memory
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory map

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")

            conn.row_factory = sqlite3.Row  # Dict-like row access

            with self.lock:
                self.created_connections += 1

            self.logger.debug(
                "Created database connection #%d",
                self.created_connections,
            )
            return conn

        except Exception:
            self.logger.exception("Failed to create database connection")
            return None

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool.

        Yields:
            Database connection

        """
        conn = None
        try:
            # Try to get connection from pool
            try:
                conn = self.pool.get(timeout=5.0)
            except queue.Empty:
                # Pool is empty, create new connection if under limit
                with self.lock:
                    if self.created_connections < self.max_connections:
                        conn = self._create_connection()
                    else:
                        # Wait longer for connection
                        conn = self.pool.get(timeout=self.timeout)

            if conn is None:
                raise RuntimeError("Failed to get database connection")

            yield conn

        except Exception:
            self.logger.exception("Database connection error")
            # Close broken connection
            if conn:
                try:
                    conn.close()
                except BaseException:
                    pass
                conn = None
            raise
        finally:
            # Return connection to pool
            if conn:
                try:
                    # Check if connection is still valid
                    conn.execute("SELECT 1")
                    self.pool.put(conn, timeout=1.0)
                except BaseException:
                    # Connection is broken, close it
                    try:
                        conn.close()
                    except BaseException:
                        pass

    def close_all(self):
        """Close all connections in the pool."""
        self.logger.info("Closing all database connections")

        # Close connections in pool
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except (queue.Empty, Exception):
                break

        with self.lock:
            self.created_connections = 0


class QueryOptimizer:
    """Database query optimizer with caching and performance monitoring."""

    def __init__(self, connection_pool: DatabaseConnectionPool):
        """Initialize query optimizer.

        Args:
            connection_pool: Database connection pool

        """
        self.connection_pool = connection_pool
        self.logger = logging.getLogger(__name__)

        # Query caching
        self.query_cache: dict[str, Any] = {}
        self.cache_lock = threading.RLock()
        self.cache_max_size = 1000

        # Performance monitoring
        self.query_stats: dict[str, QueryStats] = {}
        self.stats_lock = threading.Lock()

        # Prepared statements
        self.prepared_statements: dict[str, str] = {}

    def _get_cache_key(self, query: str, params: tuple) -> str:
        """Generate cache key for query and parameters."""
        return f"{hash(query)}:{hash(params)}"

    def _should_cache_query(self, query: str) -> bool:
        """Determine if query results should be cached."""
        # Cache SELECT queries that don't contain volatile functions
        query_lower = query.lower().strip()
        if not query_lower.startswith("select"):
            return False

        # Don't cache queries with time-sensitive functions
        volatile_functions = ["datetime", "now", "random"]
        return not any(func in query_lower for func in volatile_functions)

    def execute_query(
        self,
        query: str,
        params: tuple = (),
        cache_results: bool = True,
    ) -> list[sqlite3.Row]:
        """Execute optimized database query.

        Args:
            query: SQL query string
            params: Query parameters
            cache_results: Whether to cache query results

        Returns:
            Query results

        """
        start_time = time.time()
        cache_key = self._get_cache_key(query, params) if cache_results else None

        # Check cache first
        if cache_key and self._should_cache_query(query):
            with self.cache_lock:
                if cache_key in self.query_cache:
                    self.logdebug(
                        "Cache hit for query: %s...".replace("%s", "{query[:50]}").replace(
                            "%d", "{query[:50]}"
                        )
                    )
                    return self.query_cache[cache_key]

        # Execute query
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.execute(query, params)
                results = cursor.fetchall()

                # Cache results if appropriate
                if (
                    cache_key and self._should_cache_query(query) and len(results) < 1000
                ):  # Don't cache large result sets
                    with self.cache_lock:
                        # Implement LRU eviction
                        if len(self.query_cache) >= self.cache_max_size:
                            # Remove oldest 25% of entries
                            items_to_remove = len(self.query_cache) // 4
                            for _ in range(items_to_remove):
                                self.query_cache.pop(next(iter(self.query_cache)))

                        self.query_cache[cache_key] = results

                # Update statistics
                execution_time = time.time() - start_time
                self._update_query_stats(query, execution_time)

                return results

        except Exception:
            self.logger.exception("Query execution failed")
            self.logdebug("Failed query: %s".replace("%s", "{query}").replace("%d", "{query}"))
            raise

    def execute_transaction(self, queries: list[tuple]) -> bool:
        """Execute multiple queries in a transaction.

        Args:
            queries: List of (query, params) tuples

        Returns:
            True if transaction succeeded, False otherwise

        """
        conn = None
        try:
            with self.connection_pool.get_connection() as conn:
                conn.execute("BEGIN TRANSACTION")

                for query, params in queries:
                    conn.execute(query, params)

                conn.execute("COMMIT")
                return True

        except Exception:
            self.logger.exception("Transaction failed")
            try:
                if conn is not None:
                    conn.execute("ROLLBACK")
            except BaseException:
                pass
            return False

    def _update_query_stats(self, query: str, execution_time: float):
        """Update query performance statistics."""
        # Normalize query for statistics (remove specific values)
        normalized_query = self._normalize_query(query)

        with self.stats_lock:
            if normalized_query not in self.query_stats:
                self.query_stats[normalized_query] = QueryStats()

            stats = self.query_stats[normalized_query]
            stats.query_count += 1
            stats.total_time += execution_time
            stats.avg_time = stats.total_time / stats.query_count

            if execution_time > stats.slowest_time:
                stats.slowest_time = execution_time
                stats.slowest_query = query

    def _normalize_query(self, query: str) -> str:
        """Normalize query for statistics grouping."""
        # Simple normalization - replace literal values with placeholders

        normalized = query.lower()
        # Replace string literals
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        # Replace numeric literals
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        # Replace parameter placeholders
        normalized = re.sub(r"\?+", "?", normalized)

        return normalized.strip()

    def get_query_stats(self) -> dict[str, QueryStats]:
        """Get query performance statistics."""
        with self.stats_lock:
            return dict(self.query_stats)

    def clear_cache(self):
        """Clear query result cache."""
        with self.cache_lock:
            self.query_cache.clear()
        self.logger.info("Query cache cleared")

    def optimize_database(self):
        """Perform database optimization operations."""
        self.logger.info("Performing database optimization")

        try:
            with self.connection_pool.get_connection() as conn:
                # Analyze database for query optimizer
                conn.execute("ANALYZE")

                # Vacuum database to reclaim space and reorganize
                conn.execute("VACUUM")

                # Reindex to optimize index performance
                conn.execute("REINDEX")

            self.logger.info("Database optimization completed")

        except Exception:
            self.logger.exception("Database optimization failed")


class ScanResultsDB:
    """Optimized database manager for scan results."""

    def __init__(self, database_path: str):
        """Initialize scan results database.

        Args:
            database_path: Path to database file

        """
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)

        # Initialize connection pool and optimizer
        self.connection_pool = DatabaseConnectionPool(database_path)
        self.query_optimizer = QueryOptimizer(self.connection_pool)

        # Initialize database schema
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize database schema."""
        schema_queries = [
            """
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                scan_type TEXT NOT NULL,
                total_files INTEGER DEFAULT 0,
                infected_files INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                scan_result TEXT NOT NULL,
                threat_name TEXT,
                scan_time DATETIME NOT NULL,
                FOREIGN KEY (session_id) REFERENCES scan_sessions (id)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scan_results_session
            ON scan_results (session_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scan_results_path
            ON scan_results (file_path)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scan_results_result
            ON scan_results (scan_result)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scan_sessions_time
            ON scan_sessions (start_time)
            """,
        ]

        try:
            with self.connection_pool.get_connection() as conn:
                for query in schema_queries:
                    conn.execute(query)
                conn.commit()

            self.logger.info("Database schema initialized")

        except Exception:
            self.logger.exception("Failed to initialize database schema")
            raise

    def create_scan_session(self, scan_type: str) -> int:
        """Create a new scan session.

        Args:
            scan_type: Type of scan

        Returns:
            Session ID

        """
        query = """
        INSERT INTO scan_sessions (start_time, scan_type, status)
        VALUES (datetime('now'), ?, 'running')
        """

        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.execute(query, (scan_type,))
                conn.commit()
                session_id = cursor.lastrowid

                if session_id is None:
                    raise RuntimeError("Failed to get session ID")

            self.logger.info(
                "Created scan session %d for type '%s'",
                session_id,
                scan_type,
            )
            return session_id

        except Exception:
            self.logger.exception("Failed to create scan session")
            raise

    def add_scan_result(
        self,
        session_id: int,
        file_path: str,
        file_size: int,
        scan_result: str,
        threat_name: str | None = None,
    ):
        """Add scan result to database.

        Args:
            session_id: Scan session ID
            file_path: Path to scanned file
            file_size: Size of file in bytes
            scan_result: Scan result (CLEAN, INFECTED, ERROR)
            threat_name: Name of threat if infected

        """
        query = """
        INSERT INTO scan_results
        (session_id, file_path, file_size, scan_result, threat_name, scan_time)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """

        try:
            with self.connection_pool.get_connection() as conn:
                conn.execute(
                    query,
                    (session_id, file_path, file_size, scan_result, threat_name),
                )
                conn.commit()

        except Exception:
            self.logger.exception("Failed to add scan result")

    def finish_scan_session(
        self,
        session_id: int,
        total_files: int,
        infected_files: int,
        errors: int,
    ):
        """Mark scan session as completed.

        Args:
            session_id: Scan session ID
            total_files: Total number of files scanned
            infected_files: Number of infected files found
            errors: Number of errors encountered

        """
        query = """
        UPDATE scan_sessions
        SET end_time = datetime('now'), total_files = ?,
            infected_files = ?, errors = ?, status = 'completed'
        WHERE id = ?
        """

        try:
            with self.connection_pool.get_connection() as conn:
                conn.execute(query, (total_files, infected_files, errors, session_id))
                conn.commit()

            self.loginfo(
                "Completed scan session %d".replace("%s", "{session_id}").replace(
                    "%d", "{session_id}"
                )
            )

        except Exception:
            self.logger.exception("Failed to finish scan session")

    def get_recent_sessions(self, limit: int = 10) -> list[sqlite3.Row]:
        """Get recent scan sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of scan session records

        """
        query = """
        SELECT * FROM scan_sessions
        ORDER BY start_time DESC
        LIMIT ?
        """

        return self.query_optimizer.execute_query(query, (limit,))

    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """Clean up old scan sessions and results.

        Args:
            days_to_keep: Number of days of data to keep

        """
        cleanup_queries = [
            (
                """
            DELETE FROM scan_results
            WHERE session_id IN (
                SELECT id FROM scan_sessions
                WHERE start_time < datetime('now', '-? days')
            )
            """,
                (days_to_keep,),
            ),
            (
                """
            DELETE FROM scan_sessions
            WHERE start_time < datetime('now', '-? days')
            """,
                (days_to_keep,),
            ),
        ]

        if self.query_optimizer.execute_transaction(cleanup_queries):
            self.loginfo(
                "Cleaned up scan data older than %d days".replace("%s", "{days_to_keep}").replace(
                    "%d", "{days_to_keep}"
                )
            )
        else:
            self.logger.error("Failed to clean up old scan data")

    def close(self):
        """Close database connections."""
        self.connection_pool.close_all()


# Global database instance
scan_db: ScanResultsDB | None = None


def get_scan_db() -> ScanResultsDB:
    """Get global scan results database instance."""
    global scan_db
    if scan_db is None:
        config = load_config()
        db_path = config.get("database", {}).get("path", "scan_results.db")
        scan_db = ScanResultsDB(db_path)
    return scan_db
