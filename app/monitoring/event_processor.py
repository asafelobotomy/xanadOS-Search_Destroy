#!/usr/bin/env python3
"""Event processor for intelligent handling of file system events
Filters, prioritizes, and processes file events for real-time monitoring
"""

import fnmatch
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .file_watcher import WatchEvent, WatchEventType


class EventAction(Enum):
    """Actions that can be taken on events."""

    SCAN = "scan"
    QUARANTINE = "quarantine"
    BLOCK = "block"
    IGNORE = "ignore"
    ALERT = "alert"


@dataclass
class EventRule:
    """Rule for processing file events."""

    name: str
    pattern: str  # File pattern to match
    event_types: list[WatchEventType]
    action: EventAction
    priority: int = 0
    enabled: bool = True
    conditions: dict[str, Any] | None = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}


@dataclass
class ProcessedEvent:
    """Event after processing with actions."""

    original_event: WatchEvent
    action: EventAction
    rule_name: str
    priority: int
    timestamp: float
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EventProcessor:
    """Intelligent event processor that applies rules and filters to file system events."""

    def __init__(self):
        """Initialize event processor."""
        self.logger = logging.getLogger(__name__)

        # Event processing
        self.rules: list[EventRule] = []
        self.processed_events: deque = deque(maxlen=10000)
        self.event_stats: dict[str, int] = defaultdict(int)

        # Event filtering
        self.ignored_extensions = {".tmp", ".swp", ".log", ".cache", ".lock"}
        self.ignored_directories = {"__pycache__", ".git", ".svn", "node_modules"}
        self.max_event_rate = 100  # events per second
        self.event_rate_window = {}  # path -> list of timestamps

        # Event callbacks
        self.event_callback: Callable[[ProcessedEvent], None] | None = None
        self.alert_callback: Callable[[str, str], None] | None = None

        # Threading
        self.lock = threading.RLock()

        # Load default rules
        self._load_default_rules()

    # --- Logger helper methods (avoid attribute errors in tests and unify usage) ---
    def _log(self, fn: Callable[[str], None], msg: str, *args, **kwargs) -> None:
        """Internal safe logger call that tolerates odd format strings.

        - If args/kwargs provided, pass them through to the logger.
        - Otherwise, log the message as-is (stringified), without extra formatting.
        """
        try:
            if args or kwargs:
                fn(msg, *args, **kwargs)
            else:
                fn(str(msg))
        except Exception:
            # Last-resort fallback to avoid raising from logging
            try:
                fn(str(msg))
            except Exception:
                pass

    def loginfo(self, msg: str, *args, **kwargs) -> None:
        self._log(self.logger.info, msg, *args, **kwargs)

    def logdebug(self, msg: str, *args, **kwargs) -> None:
        self._log(self.logger.debug, msg, *args, **kwargs)

    def logwarning(self, msg: str, *args, **kwargs) -> None:
        self._log(self.logger.warning, msg, *args, **kwargs)

    def logerror(self, msg: str, *args, **kwargs) -> None:
        self._log(self.logger.error, msg, *args, **kwargs)

    def add_rule(self, rule: EventRule):
        """Add an event processing rule."""
        with self.lock:
            self.rules.append(rule)
            self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.loginfo(
            "Added event rule: %s".replace("%s", "{rule.name}").replace("%d", "{rule.name}")
        )

    def remove_rule(self, rule_name: str) -> bool:
        """Remove an event processing rule."""
        with self.lock:
            for i, rule in enumerate(self.rules):
                if rule.name == rule_name:
                    del self.rules[i]
                    self.loginfo(
                        "Removed event rule: %s".replace("%s", "{rule_name}").replace(
                            "%d", "{rule_name}"
                        )
                    )
                    return True
        return False

    def process_event(self, event: WatchEvent) -> ProcessedEvent | None:
        """Process a file system event through rules and filters.

        Args:
            event: File system event to process

        Returns:
            ProcessedEvent if the event should be acted upon, None if filtered out
        """
        try:
            # Apply basic filters first
            if not self._should_process_event(event):
                return None

            # Check event rate limiting
            if not self._check_event_rate(event):
                self.logdebug(
                    "Event rate limit exceeded for %s".replace("%s", "{event.file_path}").replace(
                        "%d", "{event.file_path}"
                    )
                )
                return None

            # Find matching rule
            rule = self._find_matching_rule(event)
            if not rule:
                # No rule matched, use default action
                rule = EventRule(
                    name="default",
                    pattern="*",
                    event_types=[event.event_type],
                    action=EventAction.SCAN,
                    priority=0,
                )

            # Create processed event
            processed = ProcessedEvent(
                original_event=event,
                action=rule.action,
                rule_name=rule.name,
                priority=rule.priority,
                timestamp=time.time(),
                metadata=self._extract_metadata(event),
            )

            # Store processed event
            with self.lock:
                self.processed_events.append(processed)
                self.event_stats[rule.action.value] += 1
                self.event_stats["total"] += 1

            # Execute callbacks
            if self.event_callback:
                try:
                    self.event_callback(processed)
                except Exception:
                    self.logerror(
                        "Error in event callback: %s".replace("%s", "{e}").replace("%d", "{e}")
                    )

            if rule.action == EventAction.ALERT and self.alert_callback:
                try:
                    self.alert_callback(
                        event.file_path,
                        f"Alert triggered by rule: {rule.name}",
                    )
                except Exception:
                    self.logerror(
                        "Error in alert callback: %s".replace("%s", "{e}").replace("%d", "{e}")
                    )

            self.logger.debug(
                "Processed event: %s -> %s (%s)",
                event.file_path,
                rule.action.value,
                rule.name,
            )

            return processed

        except Exception:
            self.logerror(
                "Error processing event for %s: %s".replace("%s", "{event.file_path, e}").replace(
                    "%d", "{event.file_path, e}"
                )
            )
            return None

    def _should_process_event(self, event: WatchEvent) -> bool:
        """Check if event should be processed based on basic filters."""
        file_path = Path(event.file_path)

        # Skip if file doesn't exist (except for delete events)
        if event.event_type != WatchEventType.FILE_DELETED and not file_path.exists():
            return False

        # Skip directories for certain event types
        if event.is_directory and event.event_type in [WatchEventType.FILE_MODIFIED]:
            return False

        # Skip ignored file extensions
        if file_path.suffix.lower() in self.ignored_extensions:
            return False

        # Skip ignored directories
        for parent in file_path.parents:
            if parent.name in self.ignored_directories:
                return False

        # Skip hidden files and directories (starting with .)
        if any(part.startswith(".") for part in file_path.parts):
            return False

        return True

    def _check_event_rate(self, event: WatchEvent) -> bool:
        """Check if event rate is within acceptable limits."""
        current_time = time.time()
        path = event.file_path

        # Initialize rate tracking for this path
        if path not in self.event_rate_window:
            self.event_rate_window[path] = deque()

        # Remove old timestamps (older than 1 second)
        window = self.event_rate_window[path]
        while window and current_time - window[0] > 1.0:
            window.popleft()

        # Check if we're over the rate limit
        if len(window) >= self.max_event_rate:
            return False

        # Add current timestamp
        window.append(current_time)
        return True

    def _find_matching_rule(self, event: WatchEvent) -> EventRule | None:
        """Find the highest priority rule that matches the event."""
        with self.lock:
            for rule in self.rules:
                if not rule.enabled:
                    continue

                # Check event type
                if event.event_type not in rule.event_types:
                    continue

                # Check file pattern
                if not fnmatch.fnmatch(event.file_path.lower(), rule.pattern.lower()):
                    continue

                # Check additional conditions
                if not self._check_rule_conditions(event, rule):
                    continue

                return rule

        return None

    def _check_rule_conditions(self, event: WatchEvent, rule: EventRule) -> bool:
        """Check if event meets rule conditions."""
        if not rule.conditions:
            return True

        file_path = Path(event.file_path)

        # Check file size condition
        if "max_file_size" in rule.conditions:
            try:
                if (
                    file_path.exists()
                    and file_path.stat().st_size > rule.conditions["max_file_size"]
                ):
                    return False
            except OSError:
                pass

        # Check file age condition
        if "max_file_age" in rule.conditions:
            try:
                if file_path.exists():
                    file_age = time.time() - file_path.stat().st_mtime
                    if file_age > rule.conditions["max_file_age"]:
                        return False
            except OSError:
                pass

        # Check directory depth condition
        if "max_depth" in rule.conditions:
            depth = len(file_path.parts)
            if depth > rule.conditions["max_depth"]:
                return False

        return True

    def _extract_metadata(self, event: WatchEvent) -> dict[str, Any]:
        """Extract metadata from file event."""
        metadata: dict[str, Any] = {}

        try:
            file_path = Path(event.file_path)

            if file_path.exists():
                stat = file_path.stat()
                metadata.update(
                    {
                        "file_size": stat.st_size,
                        "file_mode": stat.st_mode,
                        "modified_time": stat.st_mtime,
                        "access_time": stat.st_atime,
                        "creation_time": stat.st_ctime,
                    }
                )

            metadata.update(
                {
                    "file_extension": file_path.suffix.lower(),
                    "file_name": file_path.name,
                    "parent_directory": str(file_path.parent),
                    "is_executable": file_path.suffix.lower()
                    in {".exe", ".bat", ".sh", ".py", ".jar"},
                    "is_archive": file_path.suffix.lower()
                    in {".zip", ".rar", ".tar", ".gz", ".7z"},
                    "is_document": file_path.suffix.lower()
                    in {".pdf", ".doc", ".docx", ".xls", ".xlsx"},
                }
            )

        except Exception:
            self.logwarning(
                "Error extracting metadata for %s: %s".replace(
                    "%s", "{event.file_path, e}"
                ).replace("%d", "{event.file_path, e}")
            )

        return metadata

    def _load_default_rules(self):
        """Load default event processing rules."""
        default_rules = [
            # High priority: Block suspicious executables
            EventRule(
                name="block_suspicious_executables",
                pattern="*.exe",
                event_types=[WatchEventType.FILE_CREATED],
                action=EventAction.QUARANTINE,
                priority=100,
                conditions={"max_file_size": 100 * 1024 * 1024},  # 100MB
            ),
            # High priority: Scan new executables
            EventRule(
                name="scan_new_executables",
                pattern="*.exe",
                event_types=[WatchEventType.FILE_CREATED, WatchEventType.FILE_MODIFIED],
                action=EventAction.SCAN,
                priority=90,
            ),
            # High priority: Scan scripts
            EventRule(
                name="scan_scripts",
                pattern="*.{py,sh,bat,ps1,vbs}",
                event_types=[WatchEventType.FILE_CREATED, WatchEventType.FILE_MODIFIED],
                action=EventAction.SCAN,
                priority=80,
            ),
            # Medium priority: Scan downloads
            EventRule(
                name="scan_downloads",
                pattern="*/downloads/*",
                event_types=[WatchEventType.FILE_CREATED],
                action=EventAction.SCAN,
                priority=70,
            ),
            # Medium priority: Scan archives
            EventRule(
                name="scan_archives",
                pattern="*.{zip,rar,tar,gz,7z}",
                event_types=[WatchEventType.FILE_CREATED, WatchEventType.FILE_MODIFIED],
                action=EventAction.SCAN,
                priority=60,
            ),
            # Low priority: Alert on system file changes
            EventRule(
                name="alert_system_changes",
                pattern="/etc/*",
                event_types=[WatchEventType.FILE_MODIFIED, WatchEventType.FILE_DELETED],
                action=EventAction.ALERT,
                priority=50,
            ),
            # Ignore: Temporary files
            EventRule(
                name="ignore_temp_files",
                pattern="*.{tmp,swp,log,cache}",
                event_types=[WatchEventType.FILE_CREATED, WatchEventType.FILE_MODIFIED],
                action=EventAction.IGNORE,
                priority=10,
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def get_statistics(self) -> dict[str, Any]:
        """Get event processing statistics."""
        with self.lock:
            return {
                "total_rules": len(self.rules),
                "enabled_rules": len([r for r in self.rules if r.enabled]),
                "processed_events": len(self.processed_events),
                "event_stats": dict(self.event_stats),
                "rate_limited_paths": len(self.event_rate_window),
            }

    def get_recent_events(self, limit: int = 100) -> list[ProcessedEvent]:
        """Get recent processed events."""
        with self.lock:
            return list(self.processed_events)[-limit:]

    def get_rules(self) -> list[EventRule]:
        """Get all event processing rules."""
        with self.lock:
            return self.rules.copy()

    def clear_statistics(self):
        """Clear event statistics."""
        with self.lock:
            self.event_stats.clear()
            self.processed_events.clear()
            self.event_rate_window.clear()
        self.logger.info("Event statistics cleared")

    def set_event_callback(self, callback: Callable[[ProcessedEvent], None]):
        """Set callback for processed events."""
        self.event_callback = callback

    def set_alert_callback(self, callback: Callable[[str, str], None]):
        """Set callback for alerts."""
        self.alert_callback = callback
