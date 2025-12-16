#!/usr/bin/env python3
"""
Security Event Stream Widget - Task 2.1.4

Provides a live feed of security events with advanced filtering,
full-text search, and export capabilities.

Features:
- Live feed of security events (scans, threats, remediations)
- Event filtering by type, severity, source
- Full-text search across event logs (<200ms)
- Event export (CSV, JSON)
- Event details modal with context
- Pagination for 100K+ events without lag
- Auto-scroll with pause option
- SQLite backend for persistence

Performance Targets:
- Display 100K+ events without lag
- Search completes in <200ms
- Filter updates in <50ms
- Event auto-scroll with pause

Integration:
- Works with ThreatVisualizationWidget (Task 2.1.1)
- Works with PerformanceMetricsWidget (Task 2.1.2)
- Works with CustomizableLayoutManager (Task 2.1.3)

Author: xanadOS Security Team
Date: December 16, 2025
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import json
import csv

try:
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLineEdit,
        QComboBox,
        QTableWidget,
        QTableWidgetItem,
        QLabel,
        QCheckBox,
        QHeaderView,
        QFileDialog,
        QMessageBox,
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PyQt6.QtGui import QColor

    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    # Dummy classes for type checking
    QWidget = object
    QThread = object
    pyqtSignal = lambda *args: None


from app.utils.config import DATA_DIR


# Event database location
EVENTS_DIR = DATA_DIR / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_DB = EVENTS_DIR / "security_events.db"


class EventType(Enum):
    """Security event types."""

    SCAN_START = "scan_start"
    SCAN_COMPLETE = "scan_complete"
    THREAT_DETECTED = "threat_detected"
    THREAT_QUARANTINED = "threat_quarantined"
    THREAT_REMOVED = "threat_removed"
    SYSTEM_ERROR = "system_error"
    UPDATE_START = "update_start"
    UPDATE_COMPLETE = "update_complete"
    CONFIG_CHANGED = "config_changed"
    USER_ACTION = "user_action"


class EventSeverity(Enum):
    """Event severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event record."""

    event_id: int | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str = EventType.USER_ACTION.value
    severity: str = EventSeverity.INFO.value
    source: str = "system"
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecurityEvent:
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_db_row(cls, row: tuple) -> SecurityEvent:
        """Create from database row."""
        return cls(
            event_id=row[0],
            timestamp=row[1],
            event_type=row[2],
            severity=row[3],
            source=row[4],
            message=row[5],
            details=json.loads(row[6]) if row[6] else {},
        )


class SecurityEventLog:
    """
    SQLite-based security event log with indexing and search.

    Features:
    - Fast insertion of events
    - Indexed search by type, severity, source
    - Full-text search on message field
    - Pagination for large datasets
    - Event filtering and querying
    """

    def __init__(self, db_path: Path = EVENTS_DB):
        """Initialize the event log database."""
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for fast querying
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_severity ON events(severity)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_source ON events(source)
            """
            )

            # Full-text search index on message
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
                    message,
                    content=events,
                    content_rowid=event_id
                )
            """
            )

            # Triggers to keep FTS index synchronized
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS events_ai AFTER INSERT ON events BEGIN
                    INSERT INTO events_fts(rowid, message) VALUES (new.event_id, new.message);
                END
            """
            )
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS events_ad AFTER DELETE ON events BEGIN
                    DELETE FROM events_fts WHERE rowid = old.event_id;
                END
            """
            )
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS events_au AFTER UPDATE ON events BEGIN
                    DELETE FROM events_fts WHERE rowid = old.event_id;
                    INSERT INTO events_fts(rowid, message) VALUES (new.event_id, new.message);
                END
            """
            )

            conn.commit()

    def add_event(self, event: SecurityEvent) -> int:
        """Add an event to the log. Returns event_id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO events (timestamp, event_type, severity, source, message, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    event.timestamp,
                    event.event_type,
                    event.severity,
                    event.source,
                    event.message,
                    json.dumps(event.details) if event.details else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        search_query: str | None = None,
    ) -> list[SecurityEvent]:
        """
        Get events with optional filtering and pagination.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            event_type: Filter by event type
            severity: Filter by severity level
            source: Filter by source
            search_query: Full-text search on message field

        Returns:
            List of SecurityEvent objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query with filters
            query = "SELECT event_id, timestamp, event_type, severity, source, message, details FROM events"
            conditions = []
            params = []

            if search_query:
                # Use FTS for search
                query = """
                    SELECT e.event_id, e.timestamp, e.event_type, e.severity, e.source, e.message, e.details
                    FROM events e
                    JOIN events_fts fts ON e.event_id = fts.rowid
                    WHERE fts.message MATCH ?
                """
                params.append(search_query)

            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)

            if severity:
                conditions.append("severity = ?")
                params.append(severity)

            if source:
                conditions.append("source = ?")
                params.append(source)

            if conditions:
                if search_query:
                    query += " AND " + " AND ".join(conditions)
                else:
                    query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [SecurityEvent.from_db_row(row) for row in rows]

    def count_events(
        self,
        event_type: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        search_query: str | None = None,
    ) -> int:
        """Count events matching the given filters."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT COUNT(*) FROM events"
            conditions = []
            params = []

            if search_query:
                query = """
                    SELECT COUNT(*)
                    FROM events e
                    JOIN events_fts fts ON e.event_id = fts.rowid
                    WHERE fts.message MATCH ?
                """
                params.append(search_query)

            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)

            if severity:
                conditions.append("severity = ?")
                params.append(severity)

            if source:
                conditions.append("source = ?")
                params.append(source)

            if conditions:
                if search_query:
                    query += " AND " + " AND ".join(conditions)
                else:
                    query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def clear_events(self, older_than_days: int | None = None) -> int:
        """Clear events, optionally keeping recent ones. Returns count deleted."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if older_than_days:
                cutoff = datetime.utcnow().timestamp() - (older_than_days * 86400)
                cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()
                cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_iso,))
            else:
                cursor.execute("DELETE FROM events")

            deleted = cursor.rowcount
            conn.commit()
            return deleted


class SecurityEventStreamWidget(QWidget):
    """
    Widget for displaying and managing security event stream.

    Features:
    - Live event feed with auto-scroll
    - Filtering by type, severity, source
    - Full-text search (<200ms)
    - Event export (CSV, JSON)
    - Pagination for 100K+ events
    - Event details display

    Signals:
    - event_selected: Emitted when an event is selected
    - events_filtered: Emitted when filter changes
    """

    event_selected = pyqtSignal(dict)  # Event data
    events_filtered = pyqtSignal(int)  # Event count

    def __init__(
        self,
        event_log: SecurityEventLog | None = None,
        auto_refresh_ms: int = 5000,
        page_size: int = 100,
        parent: QWidget | None = None,
    ):
        """
        Initialize the event stream widget.

        Args:
            event_log: SecurityEventLog instance (creates new if None)
            auto_refresh_ms: Auto-refresh interval in milliseconds
            page_size: Number of events per page
            parent: Parent widget
        """
        if not PYQT6_AVAILABLE:
            raise ImportError("PyQt6 is required for SecurityEventStreamWidget")

        super().__init__(parent)

        self.event_log = event_log or SecurityEventLog()
        self.page_size = page_size
        self.current_page = 0
        self.auto_scroll_enabled = True

        # Current filters
        self._event_type_filter: str | None = None
        self._severity_filter: str | None = None
        self._source_filter: str | None = None
        self._search_query: str | None = None

        # Setup UI
        self._setup_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_events)
        self.refresh_timer.start(auto_refresh_ms)

        # Initial load
        self._refresh_events()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title = QLabel("Security Event Stream")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)

        # Filters and search
        filter_layout = QHBoxLayout()

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search events...")
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_input)

        # Event type filter
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", None)
        for event_type in EventType:
            self.type_combo.addItem(
                event_type.value.replace("_", " ").title(), event_type.value
            )
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.type_combo)

        # Severity filter
        self.severity_combo = QComboBox()
        self.severity_combo.addItem("All Severities", None)
        for severity in EventSeverity:
            self.severity_combo.addItem(severity.value.upper(), severity.value)
        self.severity_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.severity_combo)

        layout.addLayout(filter_layout)

        # Event table
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(6)
        self.event_table.setHorizontalHeaderLabels(
            ["Time", "Type", "Severity", "Source", "Message", "Details"]
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.event_table.horizontalHeader().setStretchLastSection(True)
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.event_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.event_table.itemSelectionChanged.connect(self._on_event_selected)
        layout.addWidget(self.event_table)

        # Controls
        controls_layout = QHBoxLayout()

        # Auto-scroll checkbox
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.stateChanged.connect(self._on_auto_scroll_changed)
        controls_layout.addWidget(self.auto_scroll_checkbox)

        # Pagination
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.clicked.connect(self._previous_page)
        controls_layout.addWidget(self.prev_button)

        self.page_label = QLabel("Page 1")
        controls_layout.addWidget(self.page_label)

        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self._next_page)
        controls_layout.addWidget(self.next_button)

        controls_layout.addStretch()

        # Export buttons
        export_csv_button = QPushButton("📄 Export CSV")
        export_csv_button.clicked.connect(self._export_csv)
        controls_layout.addWidget(export_csv_button)

        export_json_button = QPushButton("📋 Export JSON")
        export_json_button.clicked.connect(self._export_json)
        controls_layout.addWidget(export_json_button)

        # Clear button
        clear_button = QPushButton("🗑️ Clear Events")
        clear_button.clicked.connect(self._clear_events)
        controls_layout.addWidget(clear_button)

        layout.addLayout(controls_layout)

        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(
            "padding: 5px; background-color: #e8f5e9; border-radius: 3px;"
        )
        layout.addWidget(self.status_label)

    def _on_search_changed(self, text: str) -> None:
        """Handle search query changes."""
        self._search_query = text if text.strip() else None
        self.current_page = 0
        self._refresh_events()

    def _on_filter_changed(self) -> None:
        """Handle filter changes."""
        self._event_type_filter = self.type_combo.currentData()
        self._severity_filter = self.severity_combo.currentData()
        self.current_page = 0
        self._refresh_events()

    def _on_auto_scroll_changed(self, state: int) -> None:
        """Handle auto-scroll checkbox changes."""
        self.auto_scroll_enabled = bool(state)

    def _refresh_events(self) -> None:
        """Refresh the event list from database."""
        # Get events
        events = self.event_log.get_events(
            limit=self.page_size,
            offset=self.current_page * self.page_size,
            event_type=self._event_type_filter,
            severity=self._severity_filter,
            search_query=self._search_query,
        )

        # Get total count
        total_count = self.event_log.count_events(
            event_type=self._event_type_filter,
            severity=self._severity_filter,
            search_query=self._search_query,
        )

        # Update table
        self.event_table.setRowCount(len(events))

        for row, event in enumerate(events):
            # Format timestamp
            try:
                dt = datetime.fromisoformat(event.timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = event.timestamp

            # Create table items
            items = [
                QTableWidgetItem(time_str),
                QTableWidgetItem(event.event_type.replace("_", " ").title()),
                QTableWidgetItem(event.severity.upper()),
                QTableWidgetItem(event.source),
                QTableWidgetItem(event.message),
                QTableWidgetItem(json.dumps(event.details) if event.details else ""),
            ]

            # Set severity color
            severity_colors = {
                "debug": QColor(200, 200, 200),
                "info": QColor(200, 230, 255),
                "warning": QColor(255, 243, 205),
                "error": QColor(255, 220, 220),
                "critical": QColor(255, 180, 180),
            }
            color = severity_colors.get(event.severity, QColor(255, 255, 255))

            for col, item in enumerate(items):
                item.setBackground(color)
                self.event_table.setItem(row, col, item)

        # Update pagination
        total_pages = (total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

        # Update status
        self.status_label.setText(f"Showing {len(events)} of {total_count} events")

        # Emit signal
        self.events_filtered.emit(total_count)

        # Auto-scroll to latest
        if self.auto_scroll_enabled and self.current_page == 0:
            self.event_table.scrollToTop()

    def _previous_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_events()

    def _next_page(self) -> None:
        """Go to next page."""
        self.current_page += 1
        self._refresh_events()

    def _on_event_selected(self) -> None:
        """Handle event selection."""
        selected_rows = self.event_table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()

        # Get event data
        event_data = {
            "timestamp": self.event_table.item(row, 0).text(),
            "event_type": self.event_table.item(row, 1).text(),
            "severity": self.event_table.item(row, 2).text(),
            "source": self.event_table.item(row, 3).text(),
            "message": self.event_table.item(row, 4).text(),
            "details": self.event_table.item(row, 5).text(),
        }

        self.event_selected.emit(event_data)

    def _export_csv(self) -> None:
        """Export events to CSV file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Events to CSV",
            str(DATA_DIR / "events_export.csv"),
            "CSV Files (*.csv)",
        )

        if not filepath:
            return

        try:
            # Get all events (no pagination)
            events = self.event_log.get_events(
                limit=1000000,  # Large limit
                event_type=self._event_type_filter,
                severity=self._severity_filter,
                search_query=self._search_query,
            )

            with open(filepath, "w", newline="") as f:
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

            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(events)} events to {filepath}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export events: {e}",
            )

    def _export_json(self) -> None:
        """Export events to JSON file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Events to JSON",
            str(DATA_DIR / "events_export.json"),
            "JSON Files (*.json)",
        )

        if not filepath:
            return

        try:
            # Get all events (no pagination)
            events = self.event_log.get_events(
                limit=1000000,
                event_type=self._event_type_filter,
                severity=self._severity_filter,
                search_query=self._search_query,
            )

            with open(filepath, "w") as f:
                json.dump(
                    [event.to_dict() for event in events],
                    f,
                    indent=2,
                )

            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(events)} events to {filepath}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export events: {e}",
            )

    def _clear_events(self) -> None:
        """Clear all events after confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear Events",
            "Are you sure you want to clear all events? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted = self.event_log.clear_events()
            self.current_page = 0
            self._refresh_events()
            QMessageBox.information(
                self,
                "Events Cleared",
                f"Deleted {deleted} events.",
            )

    def add_event(self, event: SecurityEvent) -> None:
        """Add a new event to the stream."""
        self.event_log.add_event(event)

        # Refresh if on first page
        if self.current_page == 0:
            self._refresh_events()

    def pause_auto_refresh(self) -> None:
        """Pause auto-refresh timer."""
        self.refresh_timer.stop()

    def resume_auto_refresh(self) -> None:
        """Resume auto-refresh timer."""
        self.refresh_timer.start()
