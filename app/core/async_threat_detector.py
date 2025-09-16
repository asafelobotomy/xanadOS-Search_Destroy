#!/usr/bin/env python3
"""
Async Threat Detector for xanadOS Search & Destroy
Modernized threat detection with async/await patterns and non-blocking operations.
"""

import asyncio
import logging
import time
import types
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import aiofiles
import aiofiles.os

from app.utils.secure_crypto import secure_file_hash
from app.core.async_resource_coordinator import get_resource_coordinator, ResourceType
from app.core.async_file_metadata_cache import get_file_metadata_cache


class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of threats that can be detected."""
    MALWARE = "malware"
    VIRUS = "virus"
    TROJAN = "trojan"
    ROOTKIT = "rootkit"
    SPYWARE = "spyware"
    ADWARE = "adware"
    RANSOMWARE = "ransomware"
    SUSPICIOUS = "suspicious"
    HEURISTIC = "heuristic"
    BEHAVIORAL = "behavioral"


@dataclass
class ThreatDetection:
    """Represents a detected threat."""
    file_path: str
    threat_name: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    detection_time: datetime
    file_hash: str
    file_size: int
    confidence_score: float = 0.0
    additional_info: dict[str, Any] | None = None
    quarantined: bool = False
    quarantine_path: str | None = None


@dataclass
class ScanResult:
    """Results from an async threat scan."""
    file_path: str
    is_threat: bool
    threat_detection: ThreatDetection | None = None
    scan_duration_ms: float = 0.0
    scan_method: str = "async"
    error: str | None = None


class AsyncThreatDetector:
    """
    Async threat detector using modern async/await patterns.

    Features:
    - Non-blocking file I/O and analysis
    - Concurrent threat scanning with configurable limits
    - Async signature matching and heuristic analysis
    - Real-time threat scoring and classification
    - Memory-efficient batch processing
    """

    def __init__(
        self,
        max_workers: int = 20,
        signature_db_path: str | None = None,
        enable_heuristics: bool = True,
        enable_behavioral: bool = True,
    ) -> None:
        """Initialize async threat detector."""
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.max_workers = max_workers
        self.signature_db_path = signature_db_path
        self.enable_heuristics = enable_heuristics
        self.enable_behavioral = enable_behavioral

        # Get resource coordinator for unified resource management
        self.resource_coordinator = get_resource_coordinator()

        # Get file metadata cache for efficient file operations
        self.metadata_cache = get_file_metadata_cache()

        # Async control - use resource coordinator's semaphore instead of creating our own
        self.is_active = False

        # Threat signatures and patterns
        self.malware_signatures: dict[str, str] = {}
        self.suspicious_patterns: list[str] = []
        self.behavioral_rules: dict[str, float] = {}

        # Performance tracking
        self.scans_completed = 0
        self.threats_detected = 0
        self.total_scan_time = 0.0
        self.start_time = time.time()

        # Initialize threat detection data
        asyncio.create_task(self._initialize_async_components())

        self.logger.info(
            "Async threat detector initialized with %d workers",
            max_workers
        )

    async def __aenter__(self) -> 'AsyncThreatDetector':
        """Async context manager entry."""
        if not self.is_active:
            await self._initialize_async_components()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None:
        """Async context manager exit with cleanup."""
        await self.cleanup_async()

    async def cleanup_async(self) -> None:
        """Clean up async threat detector resources."""
        try:
            self.logger.info("Starting async threat detector cleanup...")

            # Clear threat signatures and patterns
            self.malware_signatures.clear()
            self.suspicious_patterns.clear()
            self.behavioral_rules.clear()

            # Reset performance metrics
            self.scans_completed = 0
            self.threats_detected = 0
            self.total_scan_time = 0.0

            # Mark as inactive
            self.is_active = False

            self.logger.info("Async threat detector cleanup completed")

        except Exception as e:
            self.logger.error("Error during threat detector cleanup: %s", e)

    async def _initialize_async_components(self) -> None:
        """Initialize async components and load threat data."""
        try:
            # Resource coordinator is already available, no need to create semaphore

            # Load threat signatures asynchronously
            await self._load_threat_signatures_async()

            # Initialize behavioral analysis patterns
            await self._initialize_behavioral_patterns_async()

            # Initialize heuristic rules
            await self._initialize_heuristic_rules_async()

            self.is_active = True
            self.logger.info("Async threat detector initialization completed")

        except Exception as e:
            self.logger.error("Error initializing async threat detector: %s", e)

    async def _load_threat_signatures_async(self) -> None:
        """Load threat signatures asynchronously."""
        try:
            # Load built-in signatures
            self.malware_signatures = {
                "d41d8cd98f00b204e9800998ecf8427e": "Empty File (Test)",
                "68b329da9893e34099c7d8ad5cb9c940": "Suspicious Pattern A",
                "adc83b19e793491b1c6ea0fd8b46cd9f": "Suspicious Pattern B",
            }

            # Load custom signatures if available
            if self.signature_db_path and await aiofiles.os.path.exists(self.signature_db_path):
                await self._load_custom_signatures_async()

            self.logger.info(
                "Loaded %d threat signatures",
                len(self.malware_signatures)
            )

        except Exception as e:
            self.logger.error("Error loading threat signatures: %s", e)

    async def _load_custom_signatures_async(self) -> None:
        """Load custom threat signatures from file."""
        try:
            async with aiofiles.open(self.signature_db_path) as f:
                async for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(':')
                        if len(parts) >= 2:
                            hash_value = parts[0].strip()
                            threat_name = parts[1].strip()
                            self.malware_signatures[hash_value] = threat_name
        except Exception as e:
            self.logger.error("Error loading custom signatures: %s", e)

    async def _initialize_behavioral_patterns_async(self) -> None:
        """Initialize behavioral analysis patterns."""
        if not self.enable_behavioral:
            return

        try:
            self.behavioral_rules = {
                "rapid_file_creation": 0.7,
                "system_file_modification": 0.9,
                "registry_modification": 0.8,
                "network_suspicious_activity": 0.6,
                "process_injection": 0.9,
                "privilege_escalation": 0.8,
            }

            self.logger.info(
                "Initialized %d behavioral analysis rules",
                len(self.behavioral_rules)
            )

        except Exception as e:
            self.logger.error("Error initializing behavioral patterns: %s", e)

    async def _initialize_heuristic_rules_async(self) -> None:
        """Initialize heuristic analysis rules."""
        if not self.enable_heuristics:
            return

        try:
            self.suspicious_patterns = [
                "virus", "malware", "trojan", "backdoor", "keylog",
                "rootkit", "spyware", "ransomware", "cryptolocker",
                "botnet", "payload", "exploit", "shellcode", "injection"
            ]

            self.logger.info(
                "Initialized %d heuristic patterns",
                len(self.suspicious_patterns)
            )

        except Exception as e:
            self.logger.error("Error initializing heuristic rules: %s", e)

    async def scan_file_async(self, file_path: str) -> ScanResult:
        """Scan a single file for threats asynchronously."""
        scan_start = time.time()

        try:
            # Use metadata cache for efficient file checking
            metadata = await self.metadata_cache.get_file_metadata(file_path, include_hash=False)

            if not metadata or not metadata.exists:
                return ScanResult(
                    file_path=file_path,
                    is_threat=False,
                    error="File does not exist"
                )

            # Check file size limits using cached metadata
            if metadata.size > 500 * 1024 * 1024:  # 500MB limit
                return ScanResult(
                    file_path=file_path,
                    is_threat=False,
                    error="File too large for scanning"
                )

            # Use resource coordinator for controlled concurrency
            async with self.resource_coordinator.acquire_resource(
                ResourceType.THREAT_ANALYSIS,
                f"scan_{file_path}"
            ):
                result = await self._perform_async_scan(file_path, metadata)

            # Update performance metrics
            scan_duration = (time.time() - scan_start) * 1000
            result.scan_duration_ms = scan_duration
            self.scans_completed += 1
            self.total_scan_time += scan_duration

            if result.is_threat:
                self.threats_detected += 1

            return result

        except (FileNotFoundError, PermissionError) as e:
            scan_duration = (time.time() - scan_start) * 1000
            self.logger.warning("File access error for %s: %s", file_path, e)
            return ScanResult(
                file_path=file_path,
                is_threat=False,
                scan_duration_ms=scan_duration,
                error=f"File access error: {e}"
            )
        except OSError as e:
            scan_duration = (time.time() - scan_start) * 1000
            self.logger.warning("File access error for %s: %s", file_path, e)
            return ScanResult(
                file_path=file_path,
                is_threat=False,
                scan_duration_ms=scan_duration,
                error=f"File access error: {e}"
            )
        except Exception as e:
            scan_duration = (time.time() - scan_start) * 1000
            self.logger.error("Unexpected error scanning file %s: %s", file_path, e)
            return ScanResult(
                file_path=file_path,
                is_threat=False,
                scan_duration_ms=scan_duration,
                error=f"Scan error: {e}"
            )

    async def _perform_async_scan(self, file_path: str, metadata: Any) -> ScanResult:
        """Perform the actual async threat scan using cached metadata."""
        try:
            # Get file hash from cache or calculate it
            file_hash = metadata.hash_sha256
            if not file_hash:
                # Hash not in cache, compute and update cache
                file_hash = await self._calculate_file_hash_async(file_path)
                metadata.hash_sha256 = file_hash

            # Check against known threat signatures
            signature_result = await self._check_signature_match_async(
                file_path, file_hash, metadata.size
            )
            if signature_result:
                return ScanResult(
                    file_path=file_path,
                    is_threat=True,
                    threat_detection=signature_result
                )

            # Heuristic analysis
            if self.enable_heuristics:
                heuristic_result = await self._perform_heuristic_analysis_async(
                    file_path, file_hash, metadata.size
                )
                if heuristic_result:
                    return ScanResult(
                        file_path=file_path,
                        is_threat=True,
                        threat_detection=heuristic_result
                    )

            # Behavioral analysis
            if self.enable_behavioral:
                behavioral_result = await self._perform_behavioral_analysis_async(
                    file_path, file_hash, metadata.size
                )
                if behavioral_result:
                    return ScanResult(
                        file_path=file_path,
                        is_threat=True,
                        threat_detection=behavioral_result
                    )

            # No threats detected
            return ScanResult(
                file_path=file_path,
                is_threat=False
            )

        except Exception as e:
            self.logger.error("Error in async scan for %s: %s", file_path, e)
            return ScanResult(
                file_path=file_path,
                is_threat=False,
                error=str(e)
            )

    async def _calculate_file_hash_async(self, file_path: str) -> str:
        """Calculate file hash asynchronously."""
        try:
            # Use secure crypto's async-compatible hash function
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, secure_file_hash, file_path, 'sha256')
        except Exception as e:
            self.logger.error("Error calculating hash for %s: %s", file_path, e)
            return ""

    async def _check_signature_match_async(
        self, file_path: str, file_hash: str, file_size: int
    ) -> ThreatDetection | None:
        """Check for signature matches asynchronously."""
        try:
            if file_hash in self.malware_signatures:
                threat_name = self.malware_signatures[file_hash]
                return ThreatDetection(
                    file_path=file_path,
                    threat_name=threat_name,
                    threat_type=ThreatType.MALWARE,
                    threat_level=ThreatLevel.HIGH,
                    detection_time=datetime.now(),
                    file_hash=file_hash,
                    file_size=file_size,
                    confidence_score=1.0,
                    additional_info={"detection_method": "signature_match"}
                )
            return None
        except Exception as e:
            self.logger.error("Error in signature matching for %s: %s", file_path, e)
            return None

    async def _perform_heuristic_analysis_async(
        self, file_path: str, file_hash: str, file_size: int
    ) -> ThreatDetection | None:
        """Perform heuristic analysis asynchronously."""
        try:
            filename = file_path.lower()
            suspicious_score = 0.0
            detected_patterns = []

            # Check for suspicious filename patterns
            for pattern in self.suspicious_patterns:
                if pattern in filename:
                    suspicious_score += 0.3
                    detected_patterns.append(pattern)

            # Check file size anomalies
            if file_size < 1024 and filename.endswith(('.exe', '.dll', '.scr')):
                suspicious_score += 0.4
                detected_patterns.append("suspicious_small_executable")

            # Check for packed/obfuscated executables
            if filename.endswith(('.exe', '.dll')):
                entropy_score = await self._calculate_entropy_async(file_path)
                if entropy_score > 7.5:
                    suspicious_score += 0.5
                    detected_patterns.append("high_entropy_executable")

            # If score exceeds threshold, report as threat
            if suspicious_score >= 0.6:
                threat_level = ThreatLevel.HIGH if suspicious_score >= 0.8 else ThreatLevel.MEDIUM

                return ThreatDetection(
                    file_path=file_path,
                    threat_name=f"Heuristic Detection: {', '.join(detected_patterns)}",
                    threat_type=ThreatType.HEURISTIC,
                    threat_level=threat_level,
                    detection_time=datetime.now(),
                    file_hash=file_hash,
                    file_size=file_size,
                    confidence_score=suspicious_score,
                    additional_info={
                        "detection_method": "heuristic_analysis",
                        "patterns": detected_patterns,
                        "score": suspicious_score
                    }
                )

            return None

        except Exception as e:
            self.logger.error("Error in heuristic analysis for %s: %s", file_path, e)
            return None

    async def _perform_behavioral_analysis_async(
        self, file_path: str, file_hash: str, file_size: int
    ) -> ThreatDetection | None:
        """Perform behavioral analysis asynchronously."""
        try:
            # Simulate behavioral analysis (would integrate with real-time monitoring)
            behavioral_score = 0.0
            detected_behaviors = []

            # Check for rapid file creation patterns
            # (This would integrate with the file watcher in a real implementation)

            # For now, use simple heuristics based on file location and type
            if any(path_segment in file_path.lower() for path_segment in
                   ['/tmp/', '/var/tmp/', 'temp', 'cache']):
                behavioral_score += 0.3
                detected_behaviors.append("suspicious_location")

            # Check for system file modifications
            if any(path_segment in file_path.lower() for path_segment in
                   ['/bin/', '/sbin/', '/usr/bin/', '/system/']):
                behavioral_score += 0.7
                detected_behaviors.append("system_modification")

            # If score exceeds threshold, report as threat
            if behavioral_score >= 0.5:
                threat_level = ThreatLevel.HIGH if behavioral_score >= 0.8 else ThreatLevel.MEDIUM

                return ThreatDetection(
                    file_path=file_path,
                    threat_name=f"Behavioral Detection: {', '.join(detected_behaviors)}",
                    threat_type=ThreatType.BEHAVIORAL,
                    threat_level=threat_level,
                    detection_time=datetime.now(),
                    file_hash=file_hash,
                    file_size=file_size,
                    confidence_score=behavioral_score,
                    additional_info={
                        "detection_method": "behavioral_analysis",
                        "behaviors": detected_behaviors,
                        "score": behavioral_score
                    }
                )

            return None

        except Exception as e:
            self.logger.error("Error in behavioral analysis for %s: %s", file_path, e)
            return None

    async def _calculate_entropy_async(self, file_path: str) -> float:
        """Calculate file entropy asynchronously."""
        try:
            import math
            from collections import Counter

            # Read file in chunks to avoid memory issues
            byte_counts: Counter[int] = Counter()
            total_bytes = 0

            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    byte_counts.update(chunk)
                    total_bytes += len(chunk)

            if total_bytes == 0:
                return 0.0

            # Calculate Shannon entropy
            entropy = 0.0
            for count in byte_counts.values():
                probability = count / total_bytes
                if probability > 0:
                    entropy -= probability * math.log2(probability)

            return entropy

        except Exception as e:
            self.logger.error("Error calculating entropy for %s: %s", file_path, e)
            return 0.0

    async def scan_files_async(self, file_paths: list[str]) -> list[ScanResult]:
        """Scan multiple files concurrently."""
        if not file_paths:
            return []

        self.logger.info("Starting async scan of %d files", len(file_paths))

        # Create concurrent scan tasks
        tasks = [
            asyncio.create_task(self.scan_file_async(file_path))
            for file_path in file_paths
        ]

        # Wait for all scans to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return results
        scan_results: list[ScanResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "Exception scanning %s: %s",
                    file_paths[i],
                    result
                )
                scan_results.append(ScanResult(
                    file_path=file_paths[i],
                    is_threat=False,
                    error=str(result)
                ))
            elif isinstance(result, ScanResult):
                scan_results.append(result)

        threats_found = sum(1 for result in scan_results if result.is_threat)
        self.logger.info(
            "Async scan completed: %d files scanned, %d threats detected",
            len(scan_results),
            threats_found
        )

        return scan_results

    async def get_statistics_async(self) -> dict[str, Any]:
        """Get detector performance statistics asynchronously."""
        uptime = time.time() - self.start_time
        avg_scan_time = (
            self.total_scan_time / self.scans_completed
            if self.scans_completed > 0 else 0.0
        )

        return {
            "is_active": self.is_active,
            "uptime_seconds": uptime,
            "scans_completed": self.scans_completed,
            "threats_detected": self.threats_detected,
            "threat_detection_rate": (
                self.threats_detected / self.scans_completed
                if self.scans_completed > 0 else 0.0
            ),
            "average_scan_time_ms": avg_scan_time,
            "scans_per_second": self.scans_completed / max(uptime, 1),
            "signatures_loaded": len(self.malware_signatures),
            "heuristics_enabled": self.enable_heuristics,
            "behavioral_enabled": self.enable_behavioral,
            "max_workers": self.max_workers,
        }

    async def update_signatures_async(self, new_signatures: dict[str, str]) -> None:
        """Update threat signatures asynchronously."""
        try:
            self.malware_signatures.update(new_signatures)
            self.logger.info(
                "Updated threat signatures: %d total signatures",
                len(self.malware_signatures)
            )
        except Exception as e:
            self.logger.error("Error updating signatures: %s", e)

    async def shutdown_async(self) -> None:
        """Shutdown the async threat detector."""
        self.is_active = False
        self.logger.info("Async threat detector shutdown completed")


# Async utility functions for threat detection
async def async_scan_directory(
    detector: AsyncThreatDetector,
    directory_path: str,
    recursive: bool = True
) -> list[ScanResult]:
    """Scan a directory for threats asynchronously."""
    try:
        file_paths = []

        if recursive:
            # Use async directory traversal
            async def collect_files() -> list[str]:
                loop = asyncio.get_event_loop()

                def sync_walk() -> list[str]:
                    import os
                    result = []
                    for root, _, files in os.walk(directory_path):
                        for file in files:
                            result.append(os.path.join(root, file))
                    return result

                return await loop.run_in_executor(None, sync_walk)

            file_paths = await collect_files()
        else:
            # Scan only direct files
            try:
                async with aiofiles.os.scandir(directory_path) as entries:
                    async for entry in entries:
                        if await aiofiles.os.path.isfile(entry.path):
                            file_paths.append(entry.path)
            except Exception as e:
                logging.error("Error scanning directory %s: %s", directory_path, e)
                return []

        return await detector.scan_files_async(file_paths)

    except Exception as e:
        logging.error("Error in async directory scan: %s", e)
        return []


async def async_quarantine_file(
    file_path: str,
    quarantine_dir: str,
    threat_detection: ThreatDetection
) -> bool:
    """Quarantine a threat file asynchronously."""
    try:
        import shutil
        from pathlib import Path

        source_path = Path(file_path)
        if not await aiofiles.os.path.exists(file_path):
            return False

        # Create quarantine filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quarantine_name = f"{timestamp}_{source_path.name}"
        quarantine_path = Path(quarantine_dir) / quarantine_name

        # Ensure quarantine directory exists
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file to quarantine asynchronously
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, shutil.move, file_path, str(quarantine_path))

        # Update threat detection record
        threat_detection.quarantined = True
        threat_detection.quarantine_path = str(quarantine_path)

        logging.info("File quarantined: %s -> %s", file_path, quarantine_path)
        return True

    except Exception as e:
        logging.error("Error quarantining file %s: %s", file_path, e)
        return False
