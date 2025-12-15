#!/usr/bin/env python3
"""YARA scanner for heuristic malware detection.

Complements ClamAV signature-based detection with behavioral analysis.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yara

    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False


@dataclass
class YaraScanResult:
    """Result from YARA scan."""

    file_path: str
    matched: bool
    rules_matched: list[str]
    metadata: dict[str, Any]
    error: str | None = None

    @property
    def severity(self) -> str:
        """Get highest severity from matched rules."""
        if not self.rules_matched:
            return "none"

        severities = []
        for rule in self.rules_matched:
            if "meta" in self.metadata.get(rule, {}):
                severity = self.metadata[rule]["meta"].get("severity", "low")
                severities.append(severity)

        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"


class YaraScanner:
    """YARA-based heuristic malware scanner.

    Features:
    - Behavioral pattern detection
    - Heuristic analysis
    - Custom rule support
    - Complement to signature-based scanning
    """

    def __init__(self, rules_dir: str | Path | None = None):
        """Initialize YARA scanner.

        Args:
            rules_dir: Directory containing YARA rule files (.yar, .yara)
        """
        self.logger = logging.getLogger(__name__)

        if not YARA_AVAILABLE:
            self.logger.warning(
                "YARA not available - install with: pip install yara-python"
            )
            self.available = False
            self.rules = None
            return

        self.available = True

        # Default rules directory
        if rules_dir is None:
            rules_dir = Path(__file__).parent.parent.parent / "config" / "yara_rules"

        self.rules_dir = Path(rules_dir)

        # Statistics
        self.scans_performed = 0
        self.matches_found = 0
        self.errors = 0

        # Load rules
        self.rules = self._load_rules()

        if self.rules:
            self.logger.info(
                "YARA scanner initialized with rules from: %s", self.rules_dir
            )
        else:
            self.logger.warning("YARA scanner initialized but no rules loaded")

    def _load_rules(self) -> yara.Rules | None:
        """Load YARA rules from directory.

        Returns:
            Compiled YARA rules or None if loading failed
        """
        if not self.available:
            return None

        try:
            if not self.rules_dir.exists():
                self.logger.error("YARA rules directory not found: %s", self.rules_dir)
                return None

            # Find all .yar and .yara files
            rule_files = []
            for ext in ("*.yar", "*.yara"):
                rule_files.extend(self.rules_dir.glob(ext))

            if not rule_files:
                self.logger.warning("No YARA rule files found in: %s", self.rules_dir)
                return None

            # Create file path dictionary for yara.compile
            filepaths = {}
            for i, rule_file in enumerate(rule_files):
                namespace = (
                    rule_file.stem
                )  # Use filename without extension as namespace
                filepaths[namespace] = str(rule_file)

            # Compile all rules
            rules = yara.compile(filepaths=filepaths)

            self.logger.info("Loaded %d YARA rule file(s)", len(rule_files))
            return rules

        except Exception as e:
            self.logger.error("Failed to load YARA rules: %s", e)
            self.errors += 1
            return None

    def scan_file(self, file_path: str | Path) -> YaraScanResult:
        """Scan file with YARA rules.

        Args:
            file_path: Path to file to scan

        Returns:
            YaraScanResult with match information
        """
        file_path = Path(file_path)
        self.scans_performed += 1

        # Check availability
        if not self.available:
            return YaraScanResult(
                file_path=str(file_path),
                matched=False,
                rules_matched=[],
                metadata={},
                error="YARA not available",
            )

        if not self.rules:
            return YaraScanResult(
                file_path=str(file_path),
                matched=False,
                rules_matched=[],
                metadata={},
                error="No YARA rules loaded",
            )

        try:
            # Check file exists
            if not file_path.exists():
                return YaraScanResult(
                    file_path=str(file_path),
                    matched=False,
                    rules_matched=[],
                    metadata={},
                    error="File not found",
                )

            # Perform scan
            matches = self.rules.match(str(file_path))

            if matches:
                self.matches_found += 1

                # Extract matched rule information
                rules_matched = []
                metadata = {}

                for match in matches:
                    rule_name = match.rule
                    rules_matched.append(rule_name)

                    # Extract metadata
                    meta = {}
                    if hasattr(match, "meta"):
                        meta = dict(match.meta)

                    metadata[rule_name] = {
                        "meta": meta,
                        "namespace": match.namespace,
                        "tags": list(match.tags) if hasattr(match, "tags") else [],
                    }

                self.logger.info(
                    "YARA match: %s - %d rule(s) matched",
                    file_path,
                    len(rules_matched),
                )

                return YaraScanResult(
                    file_path=str(file_path),
                    matched=True,
                    rules_matched=rules_matched,
                    metadata=metadata,
                )

            # No matches
            return YaraScanResult(
                file_path=str(file_path),
                matched=False,
                rules_matched=[],
                metadata={},
            )

        except Exception as e:
            self.logger.error("YARA scan error for %s: %s", file_path, e)
            self.errors += 1
            return YaraScanResult(
                file_path=str(file_path),
                matched=False,
                rules_matched=[],
                metadata={},
                error=str(e),
            )

    def reload_rules(self) -> bool:
        """Reload YARA rules from directory.

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Reloading YARA rules...")
        self.rules = self._load_rules()
        return self.rules is not None

    def get_statistics(self) -> dict[str, Any]:
        """Get scanner statistics.

        Returns:
            Dictionary with statistics
        """
        match_rate = (
            (self.matches_found / self.scans_performed * 100)
            if self.scans_performed > 0
            else 0.0
        )

        return {
            "available": self.available,
            "rules_loaded": self.rules is not None,
            "scans_performed": self.scans_performed,
            "matches_found": self.matches_found,
            "match_rate_percent": round(match_rate, 2),
            "errors": self.errors,
            "rules_dir": str(self.rules_dir),
        }
