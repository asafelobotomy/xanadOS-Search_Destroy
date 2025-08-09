# Database Schema and Design Architecture

## Overview

The xanadOS Search & Destroy application uses a SQLite database for persistent storage of scan results, system configuration, and performance metrics. This document outlines the database schema, optimization strategies, and data management policies.

## Database Architecture

### Technology Stack
- **Database Engine**: SQLite 3.x
- **ORM Layer**: Custom lightweight ORM
- **Connection Management**: Connection pooling for multi-threaded access
- **Migration System**: Version-controlled schema updates

### Design Principles
1. **ACID Compliance**: Ensure data integrity and consistency
2. **Performance Optimization**: Indexed queries and efficient storage
3. **Scalability**: Handle large datasets efficiently
4. **Thread Safety**: Concurrent access from multiple threads
5. **Data Integrity**: Constraints and validation rules

## Core Schema Design

### 1. Scan Results Table

```sql
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT UNIQUE NOT NULL,
    scan_type TEXT NOT NULL CHECK(scan_type IN ('quick', 'full', 'custom')),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'stopped', 'error')),
    total_files INTEGER DEFAULT 0,
    scanned_files INTEGER DEFAULT 0,
    threats_found INTEGER DEFAULT 0,
    scan_duration INTEGER, -- in seconds
    scan_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Threat Detection Table

```sql
CREATE TABLE threat_detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    threat_type TEXT NOT NULL,
    severity INTEGER CHECK(severity BETWEEN 1 AND 10),
    signature_name TEXT,
    detection_time TIMESTAMP NOT NULL,
    action_taken TEXT CHECK(action_taken IN ('quarantine', 'delete', 'ignore', 'pending')),
    false_positive BOOLEAN DEFAULT FALSE,
    notes TEXT,
    FOREIGN KEY (scan_id) REFERENCES scan_results(scan_id)
);
```

### 3. System Configuration Table

```sql
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    config_type TEXT CHECK(config_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    is_user_configurable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Performance Metrics Table

```sql
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    scan_id TEXT,
    measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scan_results(scan_id)
);
```

### 5. File Quarantine Table

```sql
CREATE TABLE quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT NOT NULL,
    quarantine_path TEXT NOT NULL,
    file_hash TEXT,
    file_size INTEGER,
    quarantine_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    threat_type TEXT,
    scan_id TEXT,
    restore_requested BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (scan_id) REFERENCES scan_results(scan_id)
);
```

### 6. Update History Table

```sql
CREATE TABLE update_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    update_type TEXT NOT NULL CHECK(update_type IN ('signatures', 'application', 'database')),
    version_from TEXT,
    version_to TEXT NOT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    download_size INTEGER,
    install_duration INTEGER -- in seconds
);
```

## Indexes and Optimization

### Primary Indexes

```sql
-- Performance optimization indexes
CREATE INDEX idx_scan_results_type_time ON scan_results(scan_type, start_time);
CREATE INDEX idx_threat_detections_scan_id ON threat_detections(scan_id);
CREATE INDEX idx_threat_detections_severity ON threat_detections(severity DESC);
CREATE INDEX idx_performance_metrics_scan_id ON performance_metrics(scan_id);
CREATE INDEX idx_performance_metrics_time ON performance_metrics(measurement_time);
CREATE INDEX idx_quarantine_time ON quarantine(quarantine_time);
CREATE INDEX idx_update_history_type_time ON update_history(update_type, update_time);

-- Composite indexes for common queries
CREATE INDEX idx_scan_results_status_type ON scan_results(status, scan_type);
CREATE INDEX idx_threats_scan_severity ON threat_detections(scan_id, severity);
```

### Query Optimization Strategies

#### 1. Prepared Statements
```python
class DatabaseManager:
    def __init__(self):
        self.prepared_statements = {
            'insert_scan_result': """
                INSERT INTO scan_results 
                (scan_id, scan_type, start_time, status, scan_path)
                VALUES (?, ?, ?, ?, ?)
            """,
            'get_recent_scans': """
                SELECT * FROM scan_results 
                WHERE start_time >= ? 
                ORDER BY start_time DESC 
                LIMIT ?
            """
        }
```

#### 2. Batch Operations
```python
def insert_multiple_threats(self, threats_data):
    """Insert multiple threat detections in a single transaction"""
    with self.get_connection() as conn:
        conn.executemany("""
            INSERT INTO threat_detections 
            (scan_id, file_path, threat_type, severity, detection_time)
            VALUES (?, ?, ?, ?, ?)
        """, threats_data)
```

#### 3. Connection Pooling
```python
class ConnectionPool:
    def __init__(self, database_path, pool_size=5):
        self.database_path = database_path
        self.pool = queue.Queue(maxsize=pool_size)
        self.create_connections()
        
    def get_connection(self):
        return self.pool.get(timeout=30)
        
    def return_connection(self, conn):
        self.pool.put(conn)
```

## Data Management Policies

### Retention Policies

#### Scan Results Retention
```sql
-- Keep detailed scan results for 90 days
DELETE FROM scan_results 
WHERE start_time < date('now', '-90 days')
AND status = 'completed';

-- Keep summary statistics indefinitely
INSERT INTO scan_statistics_monthly 
SELECT 
    strftime('%Y-%m', start_time) as month,
    scan_type,
    COUNT(*) as total_scans,
    AVG(scan_duration) as avg_duration,
    SUM(threats_found) as total_threats
FROM scan_results 
WHERE start_time < date('now', '-90 days')
GROUP BY month, scan_type;
```

#### Performance Metrics Cleanup
```sql
-- Keep performance metrics for 30 days
DELETE FROM performance_metrics 
WHERE measurement_time < date('now', '-30 days');
```

### Data Archival Strategy

#### 1. Monthly Archives
- Export old scan results to compressed files
- Maintain monthly summary statistics
- Remove detailed records older than retention period

#### 2. Backup Procedures
```python
def create_database_backup():
    """Create timestamped database backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"backups/xanados_db_{timestamp}.sqlite"
    
    with sqlite3.connect(DATABASE_PATH) as source:
        with sqlite3.connect(backup_path) as backup:
            source.backup(backup)
```

## Thread Safety and Concurrency

### Connection Management

#### Thread-Safe Access
```python
import threading
from contextlib import contextmanager

class ThreadSafeDatabaseManager:
    def __init__(self):
        self.local_storage = threading.local()
        self.lock = threading.RLock()
        
    @contextmanager
    def get_connection(self):
        if not hasattr(self.local_storage, 'connection'):
            with self.lock:
                self.local_storage.connection = sqlite3.connect(
                    DATABASE_PATH,
                    check_same_thread=False
                )
        
        try:
            yield self.local_storage.connection
        finally:
            # Connection cleanup handled by context manager
            pass
```

#### Transaction Management
```python
@contextmanager
def transaction():
    """Ensure atomic database operations"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

### Locking Strategies

#### 1. WAL Mode Configuration
```sql
-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
```

#### 2. Timeout Handling
```python
def execute_with_retry(query, params=None, max_retries=3):
    """Execute query with automatic retry on database lock"""
    for attempt in range(max_retries):
        try:
            with get_connection() as conn:
                return conn.execute(query, params or [])
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            raise
```

## Data Validation and Integrity

### Constraint Enforcement

#### Foreign Key Constraints
```sql
-- Enable foreign key constraint checking
PRAGMA foreign_keys = ON;

-- Cascading deletes for related data
ALTER TABLE threat_detections 
ADD CONSTRAINT fk_threat_scan 
FOREIGN KEY (scan_id) REFERENCES scan_results(scan_id) 
ON DELETE CASCADE;
```

#### Check Constraints
```sql
-- Ensure data validity
ALTER TABLE scan_results 
ADD CONSTRAINT chk_scan_duration 
CHECK (scan_duration IS NULL OR scan_duration >= 0);

ALTER TABLE threat_detections 
ADD CONSTRAINT chk_severity_range 
CHECK (severity BETWEEN 1 AND 10);
```

### Data Validation Layer

#### Input Sanitization
```python
class DataValidator:
    @staticmethod
    def validate_scan_result(data):
        """Validate scan result data before database insertion"""
        required_fields = ['scan_id', 'scan_type', 'start_time', 'status']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing")
        
        if data['scan_type'] not in ['quick', 'full', 'custom']:
            raise ValueError(f"Invalid scan type: {data['scan_type']}")
        
        return True
```

#### Data Sanitization
```python
def sanitize_file_path(file_path):
    """Sanitize file paths for database storage"""
    # Remove null bytes and normalize path
    clean_path = file_path.replace('\x00', '').strip()
    return os.path.normpath(clean_path)
```

## Migration System

### Schema Versioning

#### Version Tracking
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial schema creation');
```

#### Migration Scripts
```python
class DatabaseMigrator:
    def __init__(self):
        self.migrations = {
            2: self.migrate_to_v2,
            3: self.migrate_to_v3,
            # Add new migrations here
        }
    
    def migrate_to_v2(self, conn):
        """Add performance metrics table"""
        conn.execute("""
            CREATE TABLE performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
    def apply_migrations(self):
        """Apply all pending migrations"""
        current_version = self.get_current_version()
        
        for version in sorted(self.migrations.keys()):
            if version > current_version:
                self.apply_migration(version)
```

## Performance Monitoring

### Query Performance Tracking

#### Slow Query Logging
```python
import time
import logging

def log_slow_queries(func):
    """Decorator to log slow database queries"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log queries taking > 1 second
            logging.warning(f"Slow query detected: {func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper
```

#### Database Statistics
```sql
-- Monitor database size and performance
SELECT 
    name,
    page_count * page_size as size_bytes,
    page_count
FROM pragma_database_list()
JOIN pragma_page_count() ON name = 'main';

-- Analyze query plans
EXPLAIN QUERY PLAN 
SELECT * FROM scan_results 
WHERE scan_type = 'full' 
AND start_time >= date('now', '-7 days');
```

## Backup and Recovery

### Automated Backup Strategy

#### Daily Backups
```python
def schedule_daily_backup():
    """Schedule automated daily database backups"""
    import schedule
    
    schedule.every().day.at("02:00").do(create_database_backup)
    schedule.every().week.do(cleanup_old_backups)
```

#### Point-in-Time Recovery
```python
def restore_from_backup(backup_path, target_time=None):
    """Restore database from backup with optional point-in-time recovery"""
    if target_time:
        # Restore to specific timestamp using transaction logs
        restore_to_timestamp(backup_path, target_time)
    else:
        # Full restore from backup file
        shutil.copy2(backup_path, DATABASE_PATH)
```

---

This database architecture provides a robust, scalable, and efficient foundation for data storage and retrieval in the xanadOS Search & Destroy application, ensuring data integrity while maintaining optimal performance across all operations.
