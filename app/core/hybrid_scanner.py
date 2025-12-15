#!/usr/bin/env python3
"""Hybrid multi-engine malware scanner.

Combines multiple detection methods for comprehensive threat detection:
- Layer 1: ClamAV signature-based detection (fast, high accuracy)
- Layer 2: YARA heuristic detection (behavioral patterns)
- Layer 3: Additional engines (future: custom ML, sandboxing)
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.file_scanner import FileScanner, ScanResult
from app.core.yara_scanner import YaraScanner, YaraScanResult


@dataclass
class HybridScanResult:
    """Result from hybrid multi-engine scan."""

    file_path: str
    infected: bool
    virus_name: str | None
    scan_engine: str  # "clamav", "yara", "hybrid"

    # ClamAV results
    clamav_infected: bool
    clamav_virus: str | None

    # YARA results
    yara_matched: bool
    yara_rules: list[str]
    yara_severity: str | None
    yara_metadata: dict[str, Any]

    # Combined information
    threat_level: str  # "none", "low", "medium", "high", "critical"
    detection_layers: list[str]  # Which engines detected threat
    error: str | None = None

    def __str__(self) -> str:
        """String representation."""
        if self.infected:
            engines = "+".join(self.detection_layers)
            return f"INFECTED ({engines}): {self.virus_name or self.yara_rules}"
        return "CLEAN"


class HybridScanner:
    """Multi-layered malware detection system.

    Features:
    - ClamAV signature scanning (primary)
    - YARA heuristic scanning (secondary)
    - Combined threat assessment
    - Adaptive scanning strategy
    """

    def __init__(
        self,
        enable_clamav: bool = True,
        enable_yara: bool = True,
        yara_rules_dir: str | Path | None = None,
    ):
        """Initialize hybrid scanner.

        Args:
            enable_clamav: Enable ClamAV signature scanning
            enable_yara: Enable YARA heuristic scanning
            yara_rules_dir: Directory containing YARA rules
        """
        self.logger = logging.getLogger(__name__)

        # Initialize scanners
        self.clamav_enabled = enable_clamav
        self.yara_enabled = enable_yara

        if enable_clamav:
            try:
                self.clamav = FileScanner()
                self.logger.info("ClamAV scanner initialized")
            except Exception as e:
                self.logger.warning("ClamAV initialization failed: %s", e)
                self.clamav = None
                self.clamav_enabled = False
        else:
            self.clamav = None

        if enable_yara:
            try:
                self.yara = YaraScanner(rules_dir=yara_rules_dir)
                if not self.yara.available:
                    self.logger.warning("YARA scanner not available")
                    self.yara_enabled = False
                self.logger.info("YARA scanner initialized")
            except Exception as e:
                self.logger.warning("YARA initialization failed: %s", e)
                self.yara = None
                self.yara_enabled = False
        else:
            self.yara = None

        # Statistics
        self.scans_performed = 0
        self.clamav_detections = 0
        self.yara_detections = 0
        self.hybrid_detections = 0  # Both engines detected
        self.errors = 0

        self.logger.info(
            "Hybrid scanner initialized - ClamAV: %s, YARA: %s",
            self.clamav_enabled,
            self.yara_enabled,
        )

    def scan_file(self, file_path: str | Path) -> HybridScanResult:
        """Scan file with all enabled engines.

        Strategy:
        1. ClamAV signature scan (fast, definitive)
        2. YARA heuristic scan (if ClamAV clean or for additional context)
        3. Combine results and assess threat level

        Args:
            file_path: Path to file to scan

        Returns:
            HybridScanResult with combined analysis
        """
        file_path = Path(file_path)
        self.scans_performed += 1

        # Initialize results
        clamav_result = None
        yara_result = None
        detection_layers = []

        try:
            # Layer 1: ClamAV signature scan
            if self.clamav_enabled and self.clamav:
                clamav_result = self.clamav.scan_file(str(file_path))

                # Handle both ClamAVWrapper and FileScanner result formats
                if hasattr(clamav_result, "result"):
                    # FileScanner/ScanFileResult format
                    clamav_infected = clamav_result.result.value == "infected"
                elif hasattr(clamav_result, "infected"):
                    # Direct infected attribute
                    clamav_infected = clamav_result.infected
                else:
                    clamav_infected = False

                if clamav_infected:
                    self.clamav_detections += 1
                    detection_layers.append("clamav")

            # Layer 2: YARA heuristic scan
            # Run YARA even if ClamAV found something (for additional context)
            if self.yara_enabled and self.yara:
                yara_result = self.yara.scan_file(file_path)

                if yara_result.matched:
                    self.yara_detections += 1
                    detection_layers.append("yara")

            # Track hybrid detections (both engines)
            if len(detection_layers) > 1:
                self.hybrid_detections += 1

            # Combine results
            return self._combine_results(
                file_path, clamav_result, yara_result, detection_layers
            )

        except Exception as e:
            self.logger.error("Hybrid scan error for %s: %s", file_path, e)
            self.errors += 1
            return HybridScanResult(
                file_path=str(file_path),
                infected=False,
                virus_name=None,
                scan_engine="hybrid",
                clamav_infected=False,
                clamav_virus=None,
                yara_matched=False,
                yara_rules=[],
                yara_severity=None,
                yara_metadata={},
                threat_level="none",
                detection_layers=[],
                error=str(e),
            )

    def _combine_results(
        self,
        file_path: Path,
        clamav_result: ScanResult | None,
        yara_result: YaraScanResult | None,
        detection_layers: list[str],
    ) -> HybridScanResult:
        """Combine results from multiple engines.

        Args:
            file_path: File that was scanned
            clamav_result: ClamAV scan result
            yara_result: YARA scan result
            detection_layers: List of engines that detected threats

        Returns:
            Combined HybridScanResult
        """
        # Extract ClamAV data - handle both result formats
        if clamav_result:
            if hasattr(clamav_result, "result"):
                # FileScanner/ScanFileResult format
                clamav_infected = clamav_result.result.value == "infected"
                clamav_virus = clamav_result.threat_name if clamav_infected else None
            elif hasattr(clamav_result, "infected"):
                # Direct format
                clamav_infected = clamav_result.infected
                clamav_virus = getattr(clamav_result, "virus_name", None)
            else:
                clamav_infected = False
                clamav_virus = None
        else:
            clamav_infected = False
            clamav_virus = None

        # Extract YARA data
        yara_matched = yara_result.matched if yara_result else False
        yara_rules = yara_result.rules_matched if yara_result else []
        yara_severity = yara_result.severity if yara_result else None
        yara_metadata = yara_result.metadata if yara_result else {}

        # Determine if infected
        infected = clamav_infected or yara_matched

        # Determine virus name (prefer ClamAV)
        if clamav_virus:
            virus_name = clamav_virus
        elif yara_rules:
            virus_name = f"Heuristic: {', '.join(yara_rules)}"
        else:
            virus_name = None

        # Determine threat level
        threat_level = self._assess_threat_level(
            clamav_infected, yara_matched, yara_severity
        )

        # Determine primary scan engine
        if clamav_infected and yara_matched:
            scan_engine = "hybrid"
        elif clamav_infected:
            scan_engine = "clamav"
        elif yara_matched:
            scan_engine = "yara"
        else:
            scan_engine = "hybrid"

        return HybridScanResult(
            file_path=str(file_path),
            infected=infected,
            virus_name=virus_name,
            scan_engine=scan_engine,
            clamav_infected=clamav_infected,
            clamav_virus=clamav_virus,
            yara_matched=yara_matched,
            yara_rules=yara_rules,
            yara_severity=yara_severity,
            yara_metadata=yara_metadata,
            threat_level=threat_level,
            detection_layers=detection_layers,
        )

    def _assess_threat_level(
        self,
        clamav_infected: bool,
        yara_matched: bool,
        yara_severity: str | None,
    ) -> str:
        """Assess overall threat level.

        Args:
            clamav_infected: Whether ClamAV detected threat
            yara_matched: Whether YARA matched rules
            yara_severity: YARA severity level

        Returns:
            Threat level: "none", "low", "medium", "high", "critical"
        """
        # ClamAV detection is definitive - high threat
        if clamav_infected:
            # If YARA also matched, escalate based on YARA severity
            if yara_matched and yara_severity == "critical":
                return "critical"
            return "high"

        # YARA-only detection - use YARA severity
        if yara_matched:
            if yara_severity == "critical":
                return "critical"
            elif yara_severity == "high":
                return "high"
            elif yara_severity == "medium":
                return "medium"
            else:
                return "low"

        # No detections
        return "none"

    def get_statistics(self) -> dict[str, Any]:
        """Get scanner statistics.

        Returns:
            Dictionary with statistics from all engines
        """
        stats = {
            "engines_enabled": {
                "clamav": self.clamav_enabled,
                "yara": self.yara_enabled,
            },
            "scans_performed": self.scans_performed,
            "detections": {
                "clamav_only": self.clamav_detections - self.hybrid_detections,
                "yara_only": self.yara_detections - self.hybrid_detections,
                "both_engines": self.hybrid_detections,
                "total": self.clamav_detections + self.yara_detections,
            },
            "errors": self.errors,
        }

        # Add ClamAV stats (if method exists)
        if self.clamav and hasattr(self.clamav, "get_statistics"):
            stats["clamav"] = self.clamav.get_statistics()
        elif self.clamav:
            stats["clamav"] = {"available": getattr(self.clamav, "available", True)}

        # Add YARA stats
        if self.yara:
            stats["yara"] = self.yara.get_statistics()

        return stats

    def reload_yara_rules(self) -> bool:
        """Reload YARA rules.

        Returns:
            True if successful, False otherwise
        """
        if self.yara and self.yara_enabled:
            return self.yara.reload_rules()
        return False
