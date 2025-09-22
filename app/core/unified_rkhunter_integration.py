#!/usr/bin/env python3
"""Unified RKHunter Integration for xanadOS Search & Destroy

This module consolidates all RKHunter functionality into a unified, comprehensive
integration system with:

- Complete RKHunter wrapper with secure process management
- Unified monitoring system (enhanced and non-invasive modes)
- Performance optimization and configuration management
- Advanced warning analysis and categorization
- Intelligent caching and resource management

Consolidates functionality from:
- rkhunter_wrapper.py (core wrapper, scanning functionality)
- rkhunter_optimizer.py (performance optimization, configuration)
- rkhunter_monitor_enhanced.py (enhanced monitoring, detailed status)
- rkhunter_monitor_non_invasive.py (non-invasive monitoring approach)
- rkhunter_analyzer.py (warning analysis, classification)
"""

import asyncio
import configparser
import json
import logging
import os
import subprocess
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import psutil

# Configure logging
logger = logging.getLogger(__name__)

# Import dependencies with fallbacks
try:
    from .safe_kill import kill_sequence

    _SAFE_KILL_AVAILABLE = True
except ImportError:
    _SAFE_KILL_AVAILABLE = False

try:
    from .secure_subprocess import run_secure

    _SECURE_SUBPROCESS_AVAILABLE = True
except ImportError:
    _SECURE_SUBPROCESS_AVAILABLE = False

try:
    from .security_validator import SecureRKHunterValidator

    _SECURITY_VALIDATOR_AVAILABLE = True
except ImportError:
    _SECURITY_VALIDATOR_AVAILABLE = False

try:
    from .elevated_runner import elevated_run as _elevated_run

    _ELEVATED_RUNNER_AVAILABLE = True
except ImportError:
    _elevated_run = None
    _ELEVATED_RUNNER_AVAILABLE = False


# ================== ENUMS AND DATA STRUCTURES ==================


class RKHunterResult(Enum):
    """RKHunter scan result types."""

    CLEAN = "clean"
    WARNING = "warning"
    INFECTED = "infected"
    ERROR = "error"
    SKIPPED = "skipped"


class RKHunterSeverity(Enum):
    """Severity levels for RKHunter findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WarningCategory(Enum):
    """Categories for RKHunter warnings."""

    SYSTEM_FILES = "system_files"
    NETWORK = "network"
    PROCESSES = "processes"
    PACKAGES = "packages"
    ROOTKITS = "rootkits"
    CONFIGURATION = "configuration"
    PERMISSIONS = "permissions"
    CHECKSUMS = "checksums"
    UNKNOWN = "unknown"


class SeverityLevel(Enum):
    """Severity levels for warning analysis."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MonitoringMode(Enum):
    """RKHunter monitoring modes."""

    ENHANCED = "enhanced"  # Full monitoring with elevated privileges
    NON_INVASIVE = "non_invasive"  # Limited monitoring without elevation
    AUTO = "auto"  # Automatically choose based on capabilities


class RKHunterStatus(Enum):
    """RKHunter status values."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    CONFIGURATION_ERROR = "configuration_error"
    PERMISSION_DENIED = "permission_denied"
    NOT_INSTALLED = "not_installed"
    CORRUPTED = "corrupted"


@dataclass
class WarningExplanation:
    """Explanation for a RKHunter warning."""

    category: WarningCategory
    severity: SeverityLevel
    title: str
    description: str
    recommendations: list[str]
    false_positive_likelihood: float = (
        0.0  # 0.0 = definitely real, 1.0 = definitely false positive
    )
    requires_attention: bool = True
    related_files: list[str] = field(default_factory=list)
    mitigation_steps: list[str] = field(default_factory=list)


@dataclass
class RKHunterFinding:
    """Represents a single RKHunter finding."""

    test_name: str
    result: RKHunterResult
    severity: RKHunterSeverity
    description: str
    details: str = ""
    file_path: str | None = None
    recommendation: str = ""
    timestamp: datetime | None = None
    explanation: WarningExplanation | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RKHunterScanResult:
    """Complete RKHunter scan result."""

    scan_id: str
    start_time: datetime
    end_time: datetime | None
    overall_result: RKHunterResult
    findings: list[RKHunterFinding]
    warnings_count: int = 0
    errors_count: int = 0
    total_tests: int = 0
    scan_duration: float = 0.0
    rkhunter_version: str = ""
    config_used: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.end_time and self.scan_duration == 0.0:
            self.scan_duration = (self.end_time - self.start_time).total_seconds()


@dataclass
class RKHunterStatusEnhanced:
    """Enhanced RKHunter status information."""

    available: bool
    status_message: str
    binary_path: str = ""
    version: str = ""
    config_path: str = ""
    config_readable: bool = False
    binary_permissions: str = ""
    install_method: str = ""
    last_scan_time: datetime | None = None
    database_version: str = ""
    database_last_updated: datetime | None = None
    scan_logs_available: bool = False
    log_path: str = ""
    issues_found: list[str] = field(default_factory=list)
    cache_valid: bool = True
    error_message: str = ""


@dataclass
class RKHunterStatusNonInvasive:
    """Non-invasive RKHunter status information."""

    available: bool
    status_message: str
    binary_path: str = ""
    version: str = ""
    config_path: str = ""
    config_readable: bool = False
    last_activity_detected: datetime | None = None
    process_running: bool = False
    log_activity_detected: bool = False
    issues_found: list[str] = field(default_factory=list)
    cache_valid: bool = True
    error_message: str = ""


@dataclass
class OptimizationReport:
    """Report from RKHunter optimization."""

    timestamp: datetime
    optimizations_applied: list[str]
    performance_improvement: float = 0.0
    config_changes: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RKHunterConfig:
    """RKHunter configuration management."""

    config_path: str
    user_config_path: str = ""
    enable_optimization: bool = True
    scan_interval: int = 86400  # 24 hours
    monitoring_mode: MonitoringMode = MonitoringMode.AUTO
    cache_duration: int = 300  # 5 minutes
    max_scan_time: int = 3600  # 1 hour
    enable_analysis: bool = True
    auto_explain_warnings: bool = True


# ================== WARNING ANALYSIS ENGINE ==================


class RKHunterWarningAnalyzer:
    """Advanced warning analysis and explanation system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._warning_patterns = self._build_warning_patterns()

    def _build_warning_patterns(self) -> dict[str, WarningExplanation]:
        """Build database of known warning patterns and explanations."""
        return {
            # System file warnings
            "system_file_changed": WarningExplanation(
                category=WarningCategory.SYSTEM_FILES,
                severity=SeverityLevel.HIGH,
                title="System File Modification Detected",
                description="A critical system file has been modified from its expected state.",
                recommendations=[
                    "Verify if the change was from a legitimate system update",
                    "Check package manager logs for recent updates",
                    "Compare file with known good backup if available",
                    "Run additional malware scans if change is unexplained",
                ],
                false_positive_likelihood=0.3,
                requires_attention=True,
            ),
            # Package warnings
            "package_warning": WarningExplanation(
                category=WarningCategory.PACKAGES,
                severity=SeverityLevel.MEDIUM,
                title="Package Verification Warning",
                description="A package file differs from the expected package database state.",
                recommendations=[
                    "Update package database to latest version",
                    "Reinstall the affected package",
                    "Check for partial updates or interrupted installations",
                ],
                false_positive_likelihood=0.6,
                requires_attention=False,
            ),
            # Network warnings
            "network_warning": WarningExplanation(
                category=WarningCategory.NETWORK,
                severity=SeverityLevel.MEDIUM,
                title="Network Configuration Warning",
                description="Suspicious network configuration or activity detected.",
                recommendations=[
                    "Review network interfaces and routing tables",
                    "Check for unauthorized network services",
                    "Verify firewall configuration",
                ],
                false_positive_likelihood=0.4,
                requires_attention=True,
            ),
            # Default fallback
            "unknown_warning": WarningExplanation(
                category=WarningCategory.UNKNOWN,
                severity=SeverityLevel.MEDIUM,
                title="Unknown Warning",
                description="RKHunter detected an issue that requires manual review.",
                recommendations=[
                    "Review the full RKHunter log for details",
                    "Search RKHunter documentation for this specific warning",
                    "Consider updating RKHunter to the latest version",
                ],
                false_positive_likelihood=0.5,
                requires_attention=True,
            ),
        }

    def analyze_warning(
        self, test_name: str, description: str, details: str = ""
    ) -> WarningExplanation:
        """Analyze a warning and provide explanation."""
        # Pattern matching logic
        if "system" in test_name.lower() or "file" in test_name.lower():
            pattern_key = "system_file_changed"
        elif "package" in test_name.lower() or "rpm" in test_name.lower():
            pattern_key = "package_warning"
        elif "network" in test_name.lower() or "interface" in test_name.lower():
            pattern_key = "network_warning"
        else:
            pattern_key = "unknown_warning"

        explanation = self._warning_patterns.get(
            pattern_key, self._warning_patterns["unknown_warning"]
        )

        # Customize explanation based on specific details
        customized = WarningExplanation(
            category=explanation.category,
            severity=explanation.severity,
            title=explanation.title,
            description=explanation.description,
            recommendations=explanation.recommendations.copy(),
            false_positive_likelihood=explanation.false_positive_likelihood,
            requires_attention=explanation.requires_attention,
        )

        # Add specific details if available
        if details:
            customized.description += f" Details: {details}"

        return customized

    def categorize_findings(
        self, findings: list[RKHunterFinding]
    ) -> dict[WarningCategory, list[RKHunterFinding]]:
        """Categorize findings by warning category."""
        categorized = {}
        for finding in findings:
            if finding.explanation:
                category = finding.explanation.category
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(finding)
        return categorized

    def get_priority_findings(
        self, findings: list[RKHunterFinding]
    ) -> list[RKHunterFinding]:
        """Get findings that require immediate attention."""
        return [
            finding
            for finding in findings
            if finding.explanation and finding.explanation.requires_attention
        ]


# ================== MONITORING SYSTEM ==================


class UnifiedRKHunterMonitor:
    """Unified monitoring system supporting both enhanced and non-invasive modes."""

    def __init__(
        self, mode: MonitoringMode = MonitoringMode.AUTO, cache_duration: int = 300
    ):
        self.mode = mode
        self.cache_duration = cache_duration
        self.logger = logging.getLogger(__name__)

        # Caching
        self._enhanced_cache: RKHunterStatusEnhanced | None = None
        self._non_invasive_cache: RKHunterStatusNonInvasive | None = None
        self._cache_time: float | None = None
        self._lock = threading.Lock()

        # Cache file for persistent status
        self.cache_file = Path.home() / ".xanados_rkhunter_unified_cache.json"

        # Configuration paths
        self.config_paths = [
            str(Path.home() / ".config" / "search-and-destroy" / "rkhunter.conf"),
            "/etc/rkhunter.conf",
            "/usr/local/etc/rkhunter.conf",
        ]

        # Binary paths
        self.binary_paths = [
            "/usr/bin/rkhunter",
            "/usr/local/bin/rkhunter",
            "/opt/rkhunter/bin/rkhunter",
        ]

    def get_status(
        self, force_refresh: bool = False
    ) -> RKHunterStatusEnhanced | RKHunterStatusNonInvasive:
        """Get RKHunter status using appropriate mode."""
        if self.mode == MonitoringMode.ENHANCED or (
            self.mode == MonitoringMode.AUTO and self._can_use_enhanced_mode()
        ):
            return self.get_status_enhanced(force_refresh)
        else:
            return self.get_status_non_invasive(force_refresh)

    def get_status_enhanced(
        self, force_refresh: bool = False
    ) -> RKHunterStatusEnhanced:
        """Get enhanced RKHunter status with detailed information."""
        with self._lock:
            # Check cache
            if not force_refresh and self._is_cache_valid() and self._enhanced_cache:
                return self._enhanced_cache

            try:
                status = self._collect_enhanced_status()
                self._enhanced_cache = status
                self._cache_time = time.time()
                self._save_cache()
                return status
            except Exception as e:
                self.logger.error(f"Enhanced status collection failed: {e}")
                return RKHunterStatusEnhanced(
                    available=False,
                    status_message=f"Status collection failed: {e}",
                    error_message=str(e),
                )

    def get_status_non_invasive(
        self, force_refresh: bool = False
    ) -> RKHunterStatusNonInvasive:
        """Get non-invasive RKHunter status."""
        with self._lock:
            # Check cache
            if (
                not force_refresh
                and self._is_cache_valid()
                and self._non_invasive_cache
            ):
                return self._non_invasive_cache

            try:
                status = self._collect_non_invasive_status()
                self._non_invasive_cache = status
                self._cache_time = time.time()
                self._save_cache()
                return status
            except Exception as e:
                self.logger.error(f"Non-invasive status collection failed: {e}")
                return RKHunterStatusNonInvasive(
                    available=False,
                    status_message=f"Status collection failed: {e}",
                    error_message=str(e),
                )

    def _can_use_enhanced_mode(self) -> bool:
        """Check if enhanced mode is available."""
        # Check if we have elevated privileges or can get them
        if os.geteuid() == 0:
            return True

        # Check if elevated runner is available
        if _ELEVATED_RUNNER_AVAILABLE and _elevated_run:
            return True

        return False

    def _collect_enhanced_status(self) -> RKHunterStatusEnhanced:
        """Collect enhanced status information."""
        status = RKHunterStatusEnhanced(
            available=False, status_message="Collecting enhanced status..."
        )

        # Find RKHunter binary
        binary_path = self._find_rkhunter_binary()
        if not binary_path:
            status.status_message = "RKHunter binary not found"
            return status

        status.binary_path = binary_path
        status.available = True

        # Get version
        try:
            result = subprocess.run(
                [binary_path, "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                status.version = result.stdout.strip()
        except Exception as e:
            self.logger.warning(f"Could not get RKHunter version: {e}")

        # Get binary permissions
        try:
            stat_info = os.stat(binary_path)
            status.binary_permissions = oct(stat_info.st_mode)[-3:]
        except Exception as e:
            self.logger.warning(f"Could not get binary permissions: {e}")

        # Find and check config
        config_path = self._find_config_file()
        if config_path:
            status.config_path = config_path
            status.config_readable = os.access(config_path, os.R_OK)

        # Check for recent scans
        log_paths = ["/var/log/rkhunter.log", "/tmp/rkhunter.log"]
        for log_path in log_paths:
            if os.path.exists(log_path) and os.access(log_path, os.R_OK):
                status.scan_logs_available = True
                status.log_path = log_path
                try:
                    stat_info = os.stat(log_path)
                    status.last_scan_time = datetime.fromtimestamp(stat_info.st_mtime)
                except Exception:
                    pass
                break

        status.status_message = "Enhanced status collected successfully"
        return status

    def _collect_non_invasive_status(self) -> RKHunterStatusNonInvasive:
        """Collect non-invasive status information."""
        status = RKHunterStatusNonInvasive(
            available=False, status_message="Collecting non-invasive status..."
        )

        # Find RKHunter binary (no elevation needed for existence check)
        binary_path = self._find_rkhunter_binary()
        if not binary_path:
            status.status_message = "RKHunter binary not found"
            return status

        status.binary_path = binary_path
        status.available = True

        # Try to get version without elevation
        try:
            result = subprocess.run(
                [binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                user=os.getenv("USER"),  # Run as current user
            )
            if result.returncode == 0:
                status.version = result.stdout.strip()
        except Exception as e:
            self.logger.debug(f"Could not get version non-invasively: {e}")

        # Check for config accessibility
        config_path = self._find_config_file()
        if config_path:
            status.config_path = config_path
            status.config_readable = os.access(config_path, os.R_OK)

        # Check for running processes
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if "rkhunter" in proc.info["name"].lower():
                    status.process_running = True
                    status.last_activity_detected = datetime.now()
                    break
        except Exception as e:
            self.logger.debug(f"Process check failed: {e}")

        # Check for recent log activity
        log_paths = ["/var/log/rkhunter.log", "/tmp/rkhunter.log"]
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    stat_info = os.stat(log_path)
                    # Consider activity within last hour as recent
                    if time.time() - stat_info.st_mtime < 3600:
                        status.log_activity_detected = True
                        status.last_activity_detected = datetime.fromtimestamp(
                            stat_info.st_mtime
                        )
                except Exception:
                    pass

        status.status_message = "Non-invasive status collected successfully"
        return status

    def _find_rkhunter_binary(self) -> str:
        """Find RKHunter binary path."""
        for path in self.binary_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path

        # Try which command
        try:
            result = subprocess.run(
                ["which", "rkhunter"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return ""

    def _find_config_file(self) -> str:
        """Find RKHunter configuration file."""
        for path in self.config_paths:
            if os.path.exists(path):
                return path
        return ""

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache_time is None:
            return False
        return time.time() - self._cache_time < self.cache_duration

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            cache_data = {
                "enhanced": (
                    asdict(self._enhanced_cache) if self._enhanced_cache else None
                ),
                "non_invasive": (
                    asdict(self._non_invasive_cache)
                    if self._non_invasive_cache
                    else None
                ),
                "cache_time": self._cache_time,
            }
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, default=str, indent=2)
        except Exception as e:
            self.logger.debug(f"Cache save failed: {e}")

    def _load_cache(self) -> None:
        """Load cache from disk."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    cache_data = json.load(f)

                self._cache_time = cache_data.get("cache_time")

                if cache_data.get("enhanced"):
                    self._enhanced_cache = RKHunterStatusEnhanced(
                        **cache_data["enhanced"]
                    )

                if cache_data.get("non_invasive"):
                    self._non_invasive_cache = RKHunterStatusNonInvasive(
                        **cache_data["non_invasive"]
                    )
        except Exception as e:
            self.logger.debug(f"Cache load failed: {e}")


# ================== OPTIMIZATION ENGINE ==================


class RKHunterOptimizer:
    """Performance optimization and configuration management for RKHunter."""

    def __init__(self, config: RKHunterConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def optimize_configuration(self) -> OptimizationReport:
        """Optimize RKHunter configuration for performance."""
        report = OptimizationReport(
            timestamp=datetime.now(), optimizations_applied=[], config_changes={}
        )

        try:
            # Load current configuration
            current_config = self._load_current_config()

            # Apply optimizations
            optimizations = [
                self._optimize_scan_frequency,
                self._optimize_file_checks,
                self._optimize_network_checks,
                self._optimize_logging,
            ]

            for optimization in optimizations:
                try:
                    result = optimization(current_config)
                    if result:
                        report.optimizations_applied.append(result["name"])
                        report.config_changes.update(result["changes"])
                except Exception as e:
                    self.logger.error(f"Optimization failed: {e}")
                    report.warnings.append(f"Optimization failed: {e}")

            # Save optimized configuration
            if report.config_changes:
                self._save_optimized_config(current_config, report.config_changes)
                report.recommendations.append(
                    "Configuration updated with optimizations"
                )
            else:
                report.recommendations.append(
                    "No optimizations needed - configuration already optimal"
                )

        except Exception as e:
            self.logger.error(f"Configuration optimization failed: {e}")
            report.warnings.append(f"Optimization failed: {e}")

        return report

    def _load_current_config(self) -> configparser.ConfigParser:
        """Load current RKHunter configuration."""
        config = configparser.ConfigParser()

        if os.path.exists(self.config.config_path):
            config.read(self.config.config_path)

        return config

    def _optimize_scan_frequency(
        self, config: configparser.ConfigParser
    ) -> dict[str, Any] | None:
        """Optimize scan frequency settings."""
        changes = {}

        # Adjust update frequency based on system usage
        if not config.has_option("DEFAULT", "UPDATE_MIRRORS"):
            changes["UPDATE_MIRRORS"] = "1"

        if not config.has_option("DEFAULT", "MIRRORS_MODE"):
            changes["MIRRORS_MODE"] = "0"  # Faster mode

        if changes:
            return {"name": "Scan Frequency Optimization", "changes": changes}
        return None

    def _optimize_file_checks(
        self, config: configparser.ConfigParser
    ) -> dict[str, Any] | None:
        """Optimize file checking settings."""
        changes = {}

        # Skip time-consuming checks that are less critical
        optimizations = {
            "DISABLE_TESTS": "suspscan hidden_procs deleted_files packet_cap_apps apps",
            "PKGMGR": "NONE",  # Disable package manager checks if not needed
            "SCAN_MODE_DEV": "THOROUGH",  # But keep device scanning thorough
        }

        for key, value in optimizations.items():
            if not config.has_option("DEFAULT", key):
                changes[key] = value

        if changes:
            return {"name": "File Check Optimization", "changes": changes}
        return None

    def _optimize_network_checks(
        self, config: configparser.ConfigParser
    ) -> dict[str, Any] | None:
        """Optimize network checking settings."""
        changes = {}

        # Optimize network-related checks
        if not config.has_option("DEFAULT", "ALLOW_SSH_ROOT_USER"):
            changes["ALLOW_SSH_ROOT_USER"] = "no"

        if not config.has_option("DEFAULT", "ALLOW_SSH_PROT_V1"):
            changes["ALLOW_SSH_PROT_V1"] = "2"

        if changes:
            return {"name": "Network Check Optimization", "changes": changes}
        return None

    def _optimize_logging(
        self, config: configparser.ConfigParser
    ) -> dict[str, Any] | None:
        """Optimize logging settings."""
        changes = {}

        # Set appropriate logging levels
        if not config.has_option("DEFAULT", "LOGFILE"):
            changes["LOGFILE"] = "/var/log/rkhunter.log"

        if not config.has_option("DEFAULT", "APPEND_LOG"):
            changes["APPEND_LOG"] = "1"

        if changes:
            return {"name": "Logging Optimization", "changes": changes}
        return None

    def _save_optimized_config(
        self, config: configparser.ConfigParser, changes: dict[str, str]
    ) -> None:
        """Save optimized configuration."""
        # Apply changes to config
        if not config.has_section("DEFAULT"):
            config.add_section("DEFAULT")

        for key, value in changes.items():
            config.set("DEFAULT", key, value)

        # Save to user config path if we can't write to system config
        target_path = self.config.user_config_path or self.config.config_path

        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w") as f:
                config.write(f)
            self.logger.info(f"Optimized configuration saved to {target_path}")
        except Exception as e:
            self.logger.error(f"Failed to save optimized configuration: {e}")


# ================== MAIN UNIFIED WRAPPER ==================


class UnifiedRKHunterIntegration:
    """Unified RKHunter integration with comprehensive functionality."""

    def __init__(self, config: RKHunterConfig | None = None):
        self.config = config or RKHunterConfig(config_path="/etc/rkhunter.conf")
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.monitor = UnifiedRKHunterMonitor(
            mode=self.config.monitoring_mode, cache_duration=self.config.cache_duration
        )
        self.analyzer = RKHunterWarningAnalyzer()
        self.optimizer = RKHunterOptimizer(self.config)

        # State tracking
        self._current_scan: subprocess.Popen | None = None
        self._scan_lock = threading.Lock()

    async def scan_system(self, scan_type: str = "quick") -> RKHunterScanResult:
        """Perform system scan with RKHunter."""
        scan_id = f"rkhunter_{int(time.time())}"
        start_time = datetime.now()

        with self._scan_lock:
            try:
                # Determine scan parameters
                scan_args = self._build_scan_args(scan_type)

                # Execute scan
                result = await self._execute_scan(scan_args)

                # Parse results
                findings = self._parse_scan_output(result.stdout, result.stderr)

                # Analyze findings
                for finding in findings:
                    if finding.result == RKHunterResult.WARNING:
                        finding.explanation = self.analyzer.analyze_warning(
                            finding.test_name, finding.description, finding.details
                        )

                # Create scan result
                scan_result = RKHunterScanResult(
                    scan_id=scan_id,
                    start_time=start_time,
                    end_time=datetime.now(),
                    overall_result=self._determine_overall_result(findings),
                    findings=findings,
                    warnings_count=len(
                        [f for f in findings if f.result == RKHunterResult.WARNING]
                    ),
                    errors_count=len(
                        [f for f in findings if f.result == RKHunterResult.ERROR]
                    ),
                    total_tests=len(findings),
                    rkhunter_version=await self._get_rkhunter_version(),
                )

                return scan_result

            except Exception as e:
                self.logger.error(f"RKHunter scan failed: {e}")
                return RKHunterScanResult(
                    scan_id=scan_id,
                    start_time=start_time,
                    end_time=datetime.now(),
                    overall_result=RKHunterResult.ERROR,
                    findings=[
                        RKHunterFinding(
                            test_name="scan_execution",
                            result=RKHunterResult.ERROR,
                            severity=RKHunterSeverity.CRITICAL,
                            description=f"Scan execution failed: {e}",
                        )
                    ],
                )

    def _build_scan_args(self, scan_type: str) -> list[str]:
        """Build RKHunter scan arguments."""
        binary_path = self.monitor._find_rkhunter_binary()
        if not binary_path:
            raise RuntimeError("RKHunter binary not found")

        base_args = [binary_path, "--check"]

        if scan_type == "quick":
            base_args.extend(["--skip-keypress", "--report-warnings-only"])
        elif scan_type == "full":
            base_args.extend(["--skip-keypress"])
        elif scan_type == "update":
            base_args = [binary_path, "--update"]

        return base_args

    async def _execute_scan(self, args: list[str]) -> subprocess.CompletedProcess:
        """Execute RKHunter scan asynchronously."""
        loop = asyncio.get_event_loop()

        def _run_scan():
            if _SECURE_SUBPROCESS_AVAILABLE:
                return run_secure(args, timeout=self.config.max_scan_time)
            else:
                return subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=self.config.max_scan_time,
                )

        return await loop.run_in_executor(None, _run_scan)

    def _parse_scan_output(self, stdout: str, stderr: str) -> list[RKHunterFinding]:
        """Parse RKHunter scan output into findings."""
        findings = []

        # Parse stdout for test results
        lines = stdout.split("\n")
        current_test = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for test results
            if "[ " in line and " ]" in line:
                parts = line.split("[ ")
                if len(parts) >= 2:
                    test_name = parts[0].strip()
                    result_part = parts[1].split(" ]")[0].strip()

                    # Map result strings to enums
                    result = self._map_result_string(result_part)
                    severity = self._determine_severity(result, result_part)

                    finding = RKHunterFinding(
                        test_name=test_name,
                        result=result,
                        severity=severity,
                        description=line,
                    )
                    findings.append(finding)

        # Parse stderr for errors
        if stderr:
            error_finding = RKHunterFinding(
                test_name="scan_errors",
                result=RKHunterResult.ERROR,
                severity=RKHunterSeverity.HIGH,
                description="Scan generated errors",
                details=stderr,
            )
            findings.append(error_finding)

        return findings

    def _map_result_string(self, result_str: str) -> RKHunterResult:
        """Map RKHunter result string to enum."""
        result_lower = result_str.lower()

        if "ok" in result_lower or "clean" in result_lower:
            return RKHunterResult.CLEAN
        elif "warning" in result_lower:
            return RKHunterResult.WARNING
        elif "infected" in result_lower or "malware" in result_lower:
            return RKHunterResult.INFECTED
        elif "error" in result_lower:
            return RKHunterResult.ERROR
        elif "skip" in result_lower:
            return RKHunterResult.SKIPPED
        else:
            return RKHunterResult.WARNING  # Default to warning for unknown

    def _determine_severity(
        self, result: RKHunterResult, result_str: str
    ) -> RKHunterSeverity:
        """Determine severity based on result."""
        if result == RKHunterResult.INFECTED:
            return RKHunterSeverity.CRITICAL
        elif result == RKHunterResult.WARNING:
            return RKHunterSeverity.MEDIUM
        elif result == RKHunterResult.ERROR:
            return RKHunterSeverity.HIGH
        else:
            return RKHunterSeverity.LOW

    def _determine_overall_result(
        self, findings: list[RKHunterFinding]
    ) -> RKHunterResult:
        """Determine overall scan result."""
        if any(f.result == RKHunterResult.INFECTED for f in findings):
            return RKHunterResult.INFECTED
        elif any(f.result == RKHunterResult.ERROR for f in findings):
            return RKHunterResult.ERROR
        elif any(f.result == RKHunterResult.WARNING for f in findings):
            return RKHunterResult.WARNING
        else:
            return RKHunterResult.CLEAN

    async def _get_rkhunter_version(self) -> str:
        """Get RKHunter version."""
        try:
            binary_path = self.monitor._find_rkhunter_binary()
            if binary_path:
                result = subprocess.run(
                    [binary_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

    # Convenience methods
    def get_status(
        self, force_refresh: bool = False
    ) -> RKHunterStatusEnhanced | RKHunterStatusNonInvasive:
        """Get current RKHunter status."""
        return self.monitor.get_status(force_refresh)

    def optimize_configuration(self) -> OptimizationReport:
        """Optimize RKHunter configuration."""
        return self.optimizer.optimize_configuration()

    def analyze_findings(self, findings: list[RKHunterFinding]) -> dict[str, Any]:
        """Analyze scan findings."""
        return {
            "categorized": self.analyzer.categorize_findings(findings),
            "priority": self.analyzer.get_priority_findings(findings),
            "total_warnings": len(
                [f for f in findings if f.result == RKHunterResult.WARNING]
            ),
            "critical_issues": len(
                [f for f in findings if f.severity == RKHunterSeverity.CRITICAL]
            ),
        }


# ================== CONVENIENCE FUNCTIONS ==================


def create_default_config() -> RKHunterConfig:
    """Create default RKHunter configuration."""
    return RKHunterConfig(
        config_path="/etc/rkhunter.conf",
        user_config_path=str(
            Path.home() / ".config" / "search-and-destroy" / "rkhunter.conf"
        ),
        monitoring_mode=MonitoringMode.AUTO,
    )


def create_non_invasive_config() -> RKHunterConfig:
    """Create configuration for non-invasive operation."""
    config = create_default_config()
    config.monitoring_mode = MonitoringMode.NON_INVASIVE
    return config


def create_enhanced_config() -> RKHunterConfig:
    """Create configuration for enhanced operation."""
    config = create_default_config()
    config.monitoring_mode = MonitoringMode.ENHANCED
    return config


# Module-level instance
_rkhunter_instance: UnifiedRKHunterIntegration | None = None


def get_rkhunter_integration(
    config: RKHunterConfig | None = None,
) -> UnifiedRKHunterIntegration:
    """Get unified RKHunter integration instance (singleton pattern)."""
    global _rkhunter_instance
    if _rkhunter_instance is None:
        _rkhunter_instance = UnifiedRKHunterIntegration(config)
    return _rkhunter_instance


# Legacy compatibility aliases (will be used in shims)
RKHunterWrapper = UnifiedRKHunterIntegration
# RKHunterOptimizer class already exists, use integration for compatibility
RKHunterMonitorEnhanced = UnifiedRKHunterMonitor
RKHunterMonitorNonInvasive = UnifiedRKHunterMonitor  # Resolved conflict


# Legacy function aliases
def get_rkhunter_status_enhanced(force_refresh: bool = False) -> RKHunterStatusEnhanced:
    """Legacy function for enhanced status."""
    integration = get_rkhunter_integration()
    return integration.monitor.get_status_enhanced(force_refresh)


def get_rkhunter_status_non_invasive(
    force_refresh: bool = False,
) -> RKHunterStatusNonInvasive:
    """Legacy function for non-invasive status."""
    integration = get_rkhunter_integration()
    return integration.monitor.get_status_non_invasive(force_refresh)


def record_rkhunter_activity(activity_type: str, details: str = "") -> None:
    """Legacy function for activity recording."""
    logger.info(f"RKHunter activity: {activity_type} - {details}")
