#!/usr/bin/env python3
"""
Tests for Security Event Stream - Task 2.1.4

Tests cover:
- SecurityEvent dataclass
- SecurityEventLog (SQLite backend)
- Event filtering and search
- Pagination
- Export functionality
- GUI widget (non-GUI tests only for headless CI)

Author: xanadOS Security Team
Date: December 16, 2025
"""

import pytest
import json
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from app.gui.dashboard.event_stream import (
    EventType,
    EventSeverity,
    SecurityEvent,
    SecurityEventLog,
)


# ============================================================================
# SecurityEvent Dataclass Tests
# ============================================================================


def test_security_event_creation():
    """Test SecurityEvent dataclass creation."""
    event = SecurityEvent(
        event_id=1,
        timestamp="2025-12-16T10:30:00",
        event_type=EventType.THREAT_DETECTED.value,
        severity=EventSeverity.CRITICAL.value,
        source="clamav",
        message="Malware detected: Eicar-Test-Signature",
        details={"file_path": "/tmp/eicar.com", "signature": "Eicar-Test-Signature"},
    )

    assert event.event_id == 1
    assert event.timestamp == "2025-12-16T10:30:00"
    assert event.event_type == EventType.THREAT_DETECTED.value
    assert event.severity == EventSeverity.CRITICAL.value
    assert event.source == "clamav"
    assert event.message == "Malware detected: Eicar-Test-Signature"
    assert event.details == {
        "file_path": "/tmp/eicar.com",
        "signature": "Eicar-Test-Signature",
    }


def test_security_event_defaults():
    """Test SecurityEvent default values."""
    event = SecurityEvent()

    assert event.event_id is None
    assert event.event_type == EventType.USER_ACTION.value
    assert event.severity == EventSeverity.INFO.value
    assert event.source == "system"
    assert event.message == ""
    assert event.details == {}

    # Timestamp should be auto-generated
    assert event.timestamp is not None
    assert len(event.timestamp) > 0


def test_security_event_to_dict():
    """Test SecurityEvent.to_dict() serialization."""
    event = SecurityEvent(
        event_id=42,
        timestamp="2025-12-16T10:30:00",
        event_type=EventType.SCAN_COMPLETE.value,
        severity=EventSeverity.INFO.value,
        source="scanner",
        message="Scan completed successfully",
        details={"files_scanned": 1000, "threats_found": 0},
    )

    event_dict = event.to_dict()

    assert event_dict["event_id"] == 42
    assert event_dict["timestamp"] == "2025-12-16T10:30:00"
    assert event_dict["event_type"] == EventType.SCAN_COMPLETE.value
    assert event_dict["severity"] == EventSeverity.INFO.value
    assert event_dict["source"] == "scanner"
    assert event_dict["message"] == "Scan completed successfully"
    assert event_dict["details"] == {"files_scanned": 1000, "threats_found": 0}


def test_security_event_from_dict():
    """Test SecurityEvent.from_dict() deserialization."""
    event_dict = {
        "event_id": 99,
        "timestamp": "2025-12-16T11:00:00",
        "event_type": EventType.UPDATE_COMPLETE.value,
        "severity": EventSeverity.INFO.value,
        "source": "updater",
        "message": "Virus definitions updated",
        "details": {"new_signatures": 500},
    }

    event = SecurityEvent.from_dict(event_dict)

    assert event.event_id == 99
    assert event.timestamp == "2025-12-16T11:00:00"
    assert event.event_type == EventType.UPDATE_COMPLETE.value
    assert event.severity == EventSeverity.INFO.value
    assert event.source == "updater"
    assert event.message == "Virus definitions updated"
    assert event.details == {"new_signatures": 500}


# ============================================================================
# SecurityEventLog Database Tests
# ============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_events.db"
        yield db_path


def test_event_log_initialization(temp_db):
    """Test SecurityEventLog database initialization."""
    log = SecurityEventLog(db_path=temp_db)

    # Check that database file was created
    assert temp_db.exists()

    # Check that tables were created
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()

        # Check events table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        )
        assert cursor.fetchone() is not None

        # Check FTS table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events_fts'"
        )
        assert cursor.fetchone() is not None


def test_event_log_add_event(temp_db):
    """Test adding events to the log."""
    log = SecurityEventLog(db_path=temp_db)

    event = SecurityEvent(
        timestamp="2025-12-16T12:00:00",
        event_type=EventType.SCAN_START.value,
        severity=EventSeverity.INFO.value,
        source="scanner",
        message="Starting system scan",
        details={"scan_type": "full"},
    )

    event_id = log.add_event(event)

    assert event_id > 0

    # Verify event was inserted
    events = log.get_events(limit=10)
    assert len(events) == 1
    assert events[0].event_type == EventType.SCAN_START.value
    assert events[0].message == "Starting system scan"
    assert events[0].details == {"scan_type": "full"}


def test_event_log_get_events_pagination(temp_db):
    """Test event retrieval with pagination."""
    log = SecurityEventLog(db_path=temp_db)

    # Add multiple events
    for i in range(25):
        event = SecurityEvent(
            timestamp=f"2025-12-16T12:{i:02d}:00",
            event_type=EventType.USER_ACTION.value,
            severity=EventSeverity.INFO.value,
            source="test",
            message=f"Test event {i}",
        )
        log.add_event(event)

    # Test pagination
    page1 = log.get_events(limit=10, offset=0)
    assert len(page1) == 10

    page2 = log.get_events(limit=10, offset=10)
    assert len(page2) == 10

    page3 = log.get_events(limit=10, offset=20)
    assert len(page3) == 5

    # Verify ordering (most recent first)
    assert "Test event 24" in page1[0].message
    assert "Test event 4" in page3[0].message


def test_event_log_filter_by_type(temp_db):
    """Test filtering events by type."""
    log = SecurityEventLog(db_path=temp_db)

    # Add different event types
    log.add_event(
        SecurityEvent(
            event_type=EventType.SCAN_START.value,
            message="Scan started",
        )
    )
    log.add_event(
        SecurityEvent(
            event_type=EventType.THREAT_DETECTED.value,
            message="Threat detected",
        )
    )
    log.add_event(
        SecurityEvent(
            event_type=EventType.SCAN_COMPLETE.value,
            message="Scan completed",
        )
    )
    log.add_event(
        SecurityEvent(
            event_type=EventType.THREAT_DETECTED.value,
            message="Another threat detected",
        )
    )

    # Filter by THREAT_DETECTED
    threats = log.get_events(event_type=EventType.THREAT_DETECTED.value)
    assert len(threats) == 2
    assert all(e.event_type == EventType.THREAT_DETECTED.value for e in threats)

    # Filter by SCAN_START
    scans = log.get_events(event_type=EventType.SCAN_START.value)
    assert len(scans) == 1


def test_event_log_filter_by_severity(temp_db):
    """Test filtering events by severity."""
    log = SecurityEventLog(db_path=temp_db)

    # Add events with different severities
    log.add_event(SecurityEvent(severity=EventSeverity.INFO.value, message="Info"))
    log.add_event(
        SecurityEvent(severity=EventSeverity.WARNING.value, message="Warning")
    )
    log.add_event(SecurityEvent(severity=EventSeverity.ERROR.value, message="Error"))
    log.add_event(
        SecurityEvent(severity=EventSeverity.CRITICAL.value, message="Critical")
    )

    # Filter by severity
    criticals = log.get_events(severity=EventSeverity.CRITICAL.value)
    assert len(criticals) == 1
    assert criticals[0].severity == EventSeverity.CRITICAL.value

    warnings = log.get_events(severity=EventSeverity.WARNING.value)
    assert len(warnings) == 1


def test_event_log_filter_by_source(temp_db):
    """Test filtering events by source."""
    log = SecurityEventLog(db_path=temp_db)

    # Add events from different sources
    log.add_event(SecurityEvent(source="clamav", message="ClamAV event"))
    log.add_event(SecurityEvent(source="yara", message="YARA event"))
    log.add_event(SecurityEvent(source="clamav", message="Another ClamAV event"))

    # Filter by source
    clamav_events = log.get_events(source="clamav")
    assert len(clamav_events) == 2
    assert all(e.source == "clamav" for e in clamav_events)


def test_event_log_full_text_search(temp_db):
    """Test full-text search functionality."""
    log = SecurityEventLog(db_path=temp_db)

    # Add events with different messages
    log.add_event(SecurityEvent(message="Malware detected in file.exe"))
    log.add_event(SecurityEvent(message="System scan completed successfully"))
    log.add_event(SecurityEvent(message="Virus definition update failed"))
    log.add_event(SecurityEvent(message="Malware quarantined successfully"))

    # Search for "malware"
    malware_events = log.get_events(search_query="malware")
    assert len(malware_events) == 2

    # Search for "failed"
    failed_events = log.get_events(search_query="failed")
    assert len(failed_events) == 1


def test_event_log_count_events(temp_db):
    """Test counting events with filters."""
    log = SecurityEventLog(db_path=temp_db)

    # Add events
    for i in range(15):
        log.add_event(
            SecurityEvent(
                event_type=(
                    EventType.SCAN_COMPLETE.value
                    if i % 2 == 0
                    else EventType.USER_ACTION.value
                ),
                severity=EventSeverity.INFO.value,
                message=f"Event {i}",
            )
        )

    # Count all events
    total = log.count_events()
    assert total == 15

    # Count by type
    scan_count = log.count_events(event_type=EventType.SCAN_COMPLETE.value)
    assert scan_count == 8  # 0, 2, 4, 6, 8, 10, 12, 14

    user_count = log.count_events(event_type=EventType.USER_ACTION.value)
    assert user_count == 7


def test_event_log_clear_events(temp_db):
    """Test clearing events from the log."""
    log = SecurityEventLog(db_path=temp_db)

    # Add events
    for i in range(10):
        log.add_event(SecurityEvent(message=f"Event {i}"))

    assert log.count_events() == 10

    # Clear all events
    deleted = log.clear_events()
    assert deleted == 10
    assert log.count_events() == 0


def test_event_log_combined_filters(temp_db):
    """Test combining multiple filters."""
    log = SecurityEventLog(db_path=temp_db)

    # Add diverse events
    log.add_event(
        SecurityEvent(
            event_type=EventType.THREAT_DETECTED.value,
            severity=EventSeverity.CRITICAL.value,
            source="clamav",
            message="Malware detected",
        )
    )
    log.add_event(
        SecurityEvent(
            event_type=EventType.THREAT_DETECTED.value,
            severity=EventSeverity.WARNING.value,
            source="yara",
            message="Suspicious file detected",
        )
    )
    log.add_event(
        SecurityEvent(
            event_type=EventType.SCAN_COMPLETE.value,
            severity=EventSeverity.INFO.value,
            source="scanner",
            message="Scan completed",
        )
    )

    # Combined filter: THREAT_DETECTED + CRITICAL
    results = log.get_events(
        event_type=EventType.THREAT_DETECTED.value,
        severity=EventSeverity.CRITICAL.value,
    )
    assert len(results) == 1
    assert results[0].message == "Malware detected"


# ============================================================================
# Import Test (No PyQt6 Required)
# ============================================================================


def test_import_without_pyqt6():
    """Test that dataclasses can be imported without PyQt6."""
    # This should not raise an ImportError
    from app.gui.dashboard.event_stream import (
        EventType,
        EventSeverity,
        SecurityEvent,
        SecurityEventLog,
    )

    # Create instances
    event = SecurityEvent(message="Test")
    assert event.message == "Test"

    # EventType and EventSeverity should be accessible
    assert EventType.SCAN_START.value == "scan_start"
    assert EventSeverity.INFO.value == "info"


# ============================================================================
# Performance Tests
# ============================================================================


def test_event_log_performance_large_dataset(temp_db):
    """Test performance with 1000+ events (targets: <200ms search, <50ms filter)."""
    log = SecurityEventLog(db_path=temp_db)

    # Add 1000 events
    import time

    start = time.time()

    for i in range(1000):
        log.add_event(
            SecurityEvent(
                event_type=(
                    EventType.SCAN_COMPLETE.value
                    if i % 3 == 0
                    else EventType.USER_ACTION.value
                ),
                severity=EventSeverity.INFO.value,
                source=f"source_{i % 5}",
                message=f"Performance test event {i} with searchable content",
            )
        )

    insert_time = time.time() - start
    print(f"Inserted 1000 events in {insert_time:.3f}s")

    # Test filter performance (<50ms target)
    start = time.time()
    filtered = log.get_events(event_type=EventType.SCAN_COMPLETE.value, limit=100)
    filter_time = time.time() - start
    print(f"Filtered events in {filter_time * 1000:.1f}ms")
    assert (
        filter_time < 0.050
    ), f"Filter took {filter_time * 1000:.1f}ms (target: <50ms)"

    # Test search performance (<200ms target)
    start = time.time()
    searched = log.get_events(search_query="searchable", limit=100)
    search_time = time.time() - start
    print(f"Searched events in {search_time * 1000:.1f}ms")
    assert (
        search_time < 0.200
    ), f"Search took {search_time * 1000:.1f}ms (target: <200ms)"

    # Test count performance
    start = time.time()
    count = log.count_events(event_type=EventType.SCAN_COMPLETE.value)
    count_time = time.time() - start
    print(f"Counted {count} events in {count_time * 1000:.1f}ms")

    assert len(filtered) > 0
    assert len(searched) > 0


# ============================================================================
# Export Tests
# ============================================================================


def test_security_event_json_export(temp_db, tmp_path):
    """Test exporting events to JSON format."""
    log = SecurityEventLog(db_path=temp_db)

    # Add events
    for i in range(5):
        log.add_event(
            SecurityEvent(
                event_type=EventType.SCAN_COMPLETE.value,
                severity=EventSeverity.INFO.value,
                message=f"Export test event {i}",
                details={"event_num": i},
            )
        )

    # Export to JSON (simulating widget export logic)
    events = log.get_events(limit=1000)
    export_path = tmp_path / "events_export.json"

    with open(export_path, "w") as f:
        json.dump([event.to_dict() for event in events], f, indent=2)

    # Verify export
    assert export_path.exists()

    with open(export_path, "r") as f:
        exported_data = json.load(f)

    assert len(exported_data) == 5
    assert exported_data[0]["message"] == "Export test event 4"  # Most recent first


def test_security_event_csv_export(temp_db, tmp_path):
    """Test exporting events to CSV format."""
    log = SecurityEventLog(db_path=temp_db)

    # Add events
    for i in range(3):
        log.add_event(
            SecurityEvent(
                timestamp=f"2025-12-16T12:{i:02d}:00",
                event_type=EventType.USER_ACTION.value,
                severity=EventSeverity.INFO.value,
                source="test",
                message=f"CSV export event {i}",
                details={"index": i},
            )
        )

    # Export to CSV (simulating widget export logic)
    events = log.get_events(limit=1000)
    export_path = tmp_path / "events_export.csv"

    with open(export_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "event_type",
                "severity",
                "source",
                "message",
                "details",
            ],
        )
        writer.writeheader()
        for event in events:
            row = event.to_dict()
            row["details"] = json.dumps(row["details"])
            del row["event_id"]
            writer.writerow(row)

    # Verify export
    assert export_path.exists()

    with open(export_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]["message"] == "CSV export event 2"  # Most recent first
    assert json.loads(rows[0]["details"]) == {"index": 2}
