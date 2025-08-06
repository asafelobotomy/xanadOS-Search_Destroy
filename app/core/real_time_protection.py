#!/usr/bin/env python3
"""
Enhanced Real-time Protection Engine for S&D
Provides comprehensive real-time threat detection and response capabilities.
"""
import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import json
from datetime import datetime, timedelta

# Protection engine states
class ProtectionState(Enum):
    """Real-time protection states."""
    DISABLED = "disabled"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"

class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ProtectionAction(Enum):
    """Actions taken by protection engine."""
    ALLOW = "allow"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    DELETE = "delete"
    SCAN = "scan"
    ALERT = "alert"

@dataclass
class ThreatDetection:
    """Represents a detected threat."""
    file_path: str
    threat_name: str
    threat_type: str
    threat_level: ThreatLevel
    detection_time: datetime
    action_taken: ProtectionAction
    quarantine_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: int = 0
    additional_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProtectionRule:
    """Real-time protection rule."""
    name: str
    description: str
    enabled: bool = True
    file_extensions: List[str] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)
    action: ProtectionAction = ProtectionAction.SCAN
    priority: int = 50
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProtectionStats:
    """Real-time protection statistics."""
    files_scanned: int = 0
    threats_detected: int = 0
    files_quarantined: int = 0
    files_blocked: int = 0
    uptime_seconds: float = 0.0
    scan_rate_fps: float = 0.0
    false_positives: int = 0
    last_update: datetime = field(default_factory=datetime.now)

class RealTimeProtectionEngine:
    """
    Advanced real-time protection engine with behavioral analysis,
    heuristic detection, and intelligent threat response.
    """
    
    def __init__(self, clamav_wrapper=None, quarantine_dir: str = None):
        self.logger = logging.getLogger(__name__)
        self.clamav = clamav_wrapper
        
        # State management
        self.state = ProtectionState.DISABLED
        self.state_lock = threading.RLock()
        
        # Protection configuration
        self.quarantine_dir = Path(quarantine_dir or "/tmp/s&d_quarantine")
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        # Protection rules
        self.protection_rules: List[ProtectionRule] = []
        self._load_default_rules()
        
        # File monitoring
        self.monitored_files: Dict[str, Dict[str, Any]] = {}
        self.file_hashes: Dict[str, str] = {}
        self.suspicious_files: Set[str] = set()
        
        # Statistics and metrics
        self.stats = ProtectionStats()
        self.start_time: Optional[datetime] = None
        self.threat_history: List[ThreatDetection] = []
        
        # Callbacks
        self.threat_detected_callback: Optional[Callable[[ThreatDetection], None]] = None
        self.file_blocked_callback: Optional[Callable[[str, str], None]] = None
        self.protection_status_callback: Optional[Callable[[ProtectionState, str], None]] = None
        
        # Performance settings
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.scan_timeout = 30.0  # seconds
        self.heuristic_enabled = True
        self.behavioral_analysis_enabled = True
        
        # Async components
        self.protection_loop_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        self.logger.info("Real-time protection engine initialized")

    def _load_default_rules(self):
        """Load default protection rules."""
        # Executable files - high priority scanning
        self.protection_rules.append(ProtectionRule(
            name="Executable Files",
            description="Scan executable files immediately",
            file_extensions=[".exe", ".dll", ".bat", ".cmd", ".sh", ".py", ".jar", ".msi"],
            action=ProtectionAction.SCAN,
            priority=90
        ))
        
        # Compressed files - medium priority
        self.protection_rules.append(ProtectionRule(
            name="Compressed Files",
            description="Scan compressed files for embedded threats",
            file_extensions=[".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            action=ProtectionAction.SCAN,
            priority=70
        ))
        
        # Downloads directory - high priority
        self.protection_rules.append(ProtectionRule(
            name="Downloads Folder",
            description="Monitor downloads for threats",
            file_paths=["/home/*/Downloads", "/tmp", "/var/tmp"],
            action=ProtectionAction.SCAN,
            priority=85
        ))
        
        # System files - block modification
        self.protection_rules.append(ProtectionRule(
            name="System Protection",
            description="Protect critical system files",
            file_paths=["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/etc"],
            action=ProtectionAction.ALERT,
            priority=95
        ))
        
        # Known malware patterns
        self.protection_rules.append(ProtectionRule(
            name="Suspicious Patterns",
            description="Block files with suspicious characteristics",
            action=ProtectionAction.QUARANTINE,
            priority=100,
            conditions={
                "max_size": 1024 * 1024,  # 1MB
                "suspicious_names": ["virus", "malware", "trojan", "keylog"]
            }
        ))

    async def start_protection(self) -> bool:
        """Start real-time protection."""
        with self.state_lock:
            if self.state in [ProtectionState.ACTIVE, ProtectionState.STARTING]:
                self.logger.warning("Protection already active or starting")
                return True
            
            self.state = ProtectionState.STARTING
        
        try:
            # Verify ClamAV availability
            if self.clamav and not self.clamav.available:
                raise RuntimeError("ClamAV not available for real-time protection")
            
            # Reset statistics
            self.stats = ProtectionStats()
            self.start_time = datetime.now()
            
            # Start protection loop
            self.protection_loop_task = asyncio.create_task(self._protection_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            with self.state_lock:
                self.state = ProtectionState.ACTIVE
            
            self.logger.info("Real-time protection started successfully")
            self._notify_status_change(ProtectionState.ACTIVE, "Protection active")
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to start real-time protection: %s", e)
            with self.state_lock:
                self.state = ProtectionState.ERROR
            self._notify_status_change(ProtectionState.ERROR, str(e))
            return False

    async def stop_protection(self):
        """Stop real-time protection."""
        with self.state_lock:
            if self.state == ProtectionState.DISABLED:
                return
            self.state = ProtectionState.DISABLED
        
        # Cancel async tasks
        if self.protection_loop_task:
            self.protection_loop_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Wait for tasks to complete
        try:
            if self.protection_loop_task:
                await self.protection_loop_task
        except asyncio.CancelledError:
            pass
        
        try:
            if self.cleanup_task:
                await self.cleanup_task
        except asyncio.CancelledError:
            pass
        
        self.logger.info("Real-time protection stopped")
        self._notify_status_change(ProtectionState.DISABLED, "Protection disabled")

    async def scan_file_realtime(self, file_path: str) -> Optional[ThreatDetection]:
        """
        Perform real-time scan of a file with heuristic and behavioral analysis.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            ThreatDetection if threat found, None if clean
        """
        try:
            file_path_obj = Path(file_path)
            
            # Check if file exists and is accessible
            if not file_path_obj.exists() or not file_path_obj.is_file():
                return None
            
            # Check file size limits
            file_size = file_path_obj.stat().st_size
            if file_size > self.max_file_size:
                self.logger.debug("File too large for real-time scan: %s (%d bytes)", 
                                file_path, file_size)
                return None
            
            # Apply protection rules
            applicable_rules = self._get_applicable_rules(file_path)
            if not applicable_rules:
                return None
            
            # Calculate file hash for tracking
            file_hash = await self._calculate_file_hash(file_path)
            
            # Check for known threats by hash
            if await self._is_known_threat(file_hash):
                return ThreatDetection(
                    file_path=file_path,
                    threat_name="Known Malware Hash",
                    threat_type="Hash Match",
                    threat_level=ThreatLevel.HIGH,
                    detection_time=datetime.now(),
                    action_taken=ProtectionAction.QUARANTINE,
                    file_hash=file_hash,
                    file_size=file_size
                )
            
            # Heuristic analysis
            if self.heuristic_enabled:
                heuristic_result = await self._heuristic_analysis(file_path, file_hash)
                if heuristic_result:
                    return heuristic_result
            
            # ClamAV signature scan
            if self.clamav and self.clamav.available:
                scan_result = await self._perform_clamav_scan(file_path)
                if scan_result:
                    return scan_result
            
            # Behavioral analysis (for executables)
            if self.behavioral_analysis_enabled and self._is_executable(file_path):
                behavioral_result = await self._behavioral_analysis(file_path, file_hash)
                if behavioral_result:
                    return behavioral_result
            
            # Update statistics
            self.stats.files_scanned += 1
            self.stats.last_update = datetime.now()
            
            return None
            
        except Exception as e:
            self.logger.error("Error during real-time scan of %s: %s", file_path, e)
            return None

    async def _protection_loop(self):
        """Main protection monitoring loop."""
        while self.state == ProtectionState.ACTIVE:
            try:
                # Update statistics
                if self.start_time:
                    self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
                    if self.stats.uptime_seconds > 0:
                        self.stats.scan_rate_fps = self.stats.files_scanned / self.stats.uptime_seconds
                
                # Perform periodic health checks
                await self._health_check()
                
                # Sleep before next iteration
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in protection loop: %s", e)
                await asyncio.sleep(5.0)

    async def _cleanup_loop(self):
        """Periodic cleanup of old data and temporary files."""
        while self.state == ProtectionState.ACTIVE:
            try:
                # Clean old threat history (keep last 1000 entries)
                if len(self.threat_history) > 1000:
                    self.threat_history = self.threat_history[-1000:]
                
                # Clean old file monitoring data
                cutoff_time = datetime.now() - timedelta(hours=24)
                old_files = [
                    path for path, data in self.monitored_files.items()
                    if data.get('last_seen', datetime.min) < cutoff_time
                ]
                for file_path in old_files:
                    del self.monitored_files[file_path]
                    self.file_hashes.pop(file_path, None)
                
                # Clean quarantine directory of old files (older than 30 days)
                await self._cleanup_quarantine()
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in cleanup loop: %s", e)
                await asyncio.sleep(3600)

    async def _heuristic_analysis(self, file_path: str, file_hash: str) -> Optional[ThreatDetection]:
        """Perform heuristic analysis on file."""
        try:
            file_path_obj = Path(file_path)
            
            # Check suspicious file names
            suspicious_patterns = ["virus", "malware", "trojan", "keylog", "backdoor", "rootkit"]
            filename_lower = file_path_obj.name.lower()
            
            for pattern in suspicious_patterns:
                if pattern in filename_lower:
                    return ThreatDetection(
                        file_path=file_path,
                        threat_name=f"Suspicious Filename: {pattern}",
                        threat_type="Heuristic",
                        threat_level=ThreatLevel.MEDIUM,
                        detection_time=datetime.now(),
                        action_taken=ProtectionAction.ALERT,
                        file_hash=file_hash,
                        file_size=file_path_obj.stat().st_size
                    )
            
            # Check file entropy (high entropy may indicate packed/encrypted malware)
            if self._is_executable(file_path):
                entropy = await self._calculate_entropy(file_path)
                if entropy > 7.5:  # High entropy threshold
                    return ThreatDetection(
                        file_path=file_path,
                        threat_name="High Entropy Executable",
                        threat_type="Heuristic",
                        threat_level=ThreatLevel.MEDIUM,
                        detection_time=datetime.now(),
                        action_taken=ProtectionAction.SCAN,
                        file_hash=file_hash,
                        file_size=file_path_obj.stat().st_size,
                        additional_info={"entropy": entropy}
                    )
            
            return None
            
        except Exception as e:
            self.logger.error("Error in heuristic analysis: %s", e)
            return None

    async def _behavioral_analysis(self, file_path: str, file_hash: str) -> Optional[ThreatDetection]:
        """Perform basic behavioral analysis."""
        try:
            # Check for rapid file creation patterns (potential malware spreading)
            file_dir = Path(file_path).parent
            recent_files = []
            
            # Count files created in same directory in last 5 minutes
            cutoff_time = datetime.now() - timedelta(minutes=5)
            
            for monitored_path, data in self.monitored_files.items():
                if (Path(monitored_path).parent == file_dir and 
                    data.get('creation_time', datetime.min) > cutoff_time):
                    recent_files.append(monitored_path)
            
            # If many files created rapidly, flag as suspicious
            if len(recent_files) > 20:
                return ThreatDetection(
                    file_path=file_path,
                    threat_name="Rapid File Creation Pattern",
                    threat_type="Behavioral",
                    threat_level=ThreatLevel.MEDIUM,
                    detection_time=datetime.now(),
                    action_taken=ProtectionAction.ALERT,
                    file_hash=file_hash,
                    additional_info={"rapid_files_count": len(recent_files)}
                )
            
            return None
            
        except Exception as e:
            self.logger.error("Error in behavioral analysis: %s", e)
            return None

    async def _perform_clamav_scan(self, file_path: str) -> Optional[ThreatDetection]:
        """Perform ClamAV scan and convert result."""
        try:
            # Use asyncio to run ClamAV scan without blocking
            loop = asyncio.get_event_loop()
            scan_result = await loop.run_in_executor(
                None, 
                self.clamav.scan_file, 
                file_path
            )
            
            if scan_result.result.value == "infected":
                return ThreatDetection(
                    file_path=file_path,
                    threat_name=scan_result.threat_name or "Unknown Threat",
                    threat_type=scan_result.threat_type or "Virus",
                    threat_level=ThreatLevel.HIGH,
                    detection_time=datetime.now(),
                    action_taken=ProtectionAction.QUARANTINE,
                    file_size=scan_result.file_size
                )
            
            return None
            
        except Exception as e:
            self.logger.error("Error in ClamAV scan: %s", e)
            return None

    async def quarantine_file(self, file_path: str, threat_detection: ThreatDetection) -> bool:
        """Quarantine a detected threat."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False
            
            # Create quarantine filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_name = f"{timestamp}_{source_path.name}"
            quarantine_path = self.quarantine_dir / quarantine_name
            
            # Create quarantine metadata
            metadata = {
                "original_path": str(source_path),
                "quarantine_time": datetime.now().isoformat(),
                "threat_name": threat_detection.threat_name,
                "threat_type": threat_detection.threat_type,
                "threat_level": threat_detection.threat_level.name,
                "file_hash": threat_detection.file_hash,
                "file_size": threat_detection.file_size
            }
            
            # Move file to quarantine
            source_path.rename(quarantine_path)
            
            # Save metadata
            metadata_path = quarantine_path.with_suffix(quarantine_path.suffix + ".metadata")
            with metadata_path.open('w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update threat detection with quarantine path
            threat_detection.quarantine_path = str(quarantine_path)
            
            # Update statistics
            self.stats.files_quarantined += 1
            
            self.logger.info("File quarantined: %s -> %s", file_path, quarantine_path)
            return True
            
        except Exception as e:
            self.logger.error("Failed to quarantine file %s: %s", file_path, e)
            return False

    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    async def _calculate_entropy(self, file_path: str) -> float:
        """Calculate file entropy for packed/encrypted malware detection."""
        try:
            import math
            from collections import Counter
            
            with open(file_path, "rb") as f:
                data = f.read(8192)  # Read first 8KB for analysis
            
            if not data:
                return 0.0
            
            # Calculate byte frequency
            byte_counts = Counter(data)
            entropy = 0.0
            
            for count in byte_counts.values():
                probability = count / len(data)
                entropy -= probability * math.log2(probability)
            
            return entropy
            
        except Exception:
            return 0.0

    async def _is_known_threat(self, file_hash: str) -> bool:
        """Check if file hash is in known threat database."""
        # This would integrate with threat intelligence feeds
        # For now, maintain a simple local cache
        # TODO: Implement threat intelligence integration
        return False

    def _is_executable(self, file_path: str) -> bool:
        """Check if file is executable."""
        executable_extensions = {".exe", ".dll", ".bat", ".cmd", ".sh", ".py", ".jar", ".msi", ".deb", ".rpm"}
        return Path(file_path).suffix.lower() in executable_extensions

    def _get_applicable_rules(self, file_path: str) -> List[ProtectionRule]:
        """Get protection rules applicable to file."""
        applicable_rules = []
        file_path_obj = Path(file_path)
        
        for rule in self.protection_rules:
            if not rule.enabled:
                continue
            
            # Check file extensions
            if rule.file_extensions:
                if file_path_obj.suffix.lower() not in rule.file_extensions:
                    continue
            
            # Check file paths
            if rule.file_paths:
                path_match = False
                for path_pattern in rule.file_paths:
                    if file_path.startswith(path_pattern.replace("*", "")):
                        path_match = True
                        break
                if not path_match:
                    continue
            
            # Check exclude paths
            if rule.exclude_paths:
                excluded = False
                for exclude_pattern in rule.exclude_paths:
                    if file_path.startswith(exclude_pattern):
                        excluded = True
                        break
                if excluded:
                    continue
            
            applicable_rules.append(rule)
        
        return sorted(applicable_rules, key=lambda r: r.priority, reverse=True)

    async def _health_check(self):
        """Perform health check of protection components."""
        try:
            # Check ClamAV availability
            if self.clamav and not self.clamav.available:
                self.logger.warning("ClamAV became unavailable during protection")
            
            # Check quarantine directory
            if not self.quarantine_dir.exists():
                self.quarantine_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info("Recreated quarantine directory")
            
        except Exception as e:
            self.logger.error("Health check failed: %s", e)

    async def _cleanup_quarantine(self):
        """Clean up old quarantined files."""
        try:
            cutoff_time = datetime.now() - timedelta(days=30)
            
            for file_path in self.quarantine_dir.iterdir():
                if file_path.is_file():
                    # Check file age
                    if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_time:
                        try:
                            file_path.unlink()
                            # Also remove metadata file if exists
                            metadata_path = file_path.with_suffix(file_path.suffix + ".metadata")
                            if metadata_path.exists():
                                metadata_path.unlink()
                            self.logger.debug("Removed old quarantine file: %s", file_path)
                        except Exception as e:
                            self.logger.error("Failed to remove old quarantine file %s: %s", file_path, e)
            
        except Exception as e:
            self.logger.error("Error cleaning quarantine: %s", e)

    def _notify_status_change(self, new_state: ProtectionState, message: str):
        """Notify about protection status changes."""
        if self.protection_status_callback:
            try:
                self.protection_status_callback(new_state, message)
            except Exception as e:
                self.logger.error("Error in status callback: %s", e)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive protection statistics."""
        return {
            "state": self.state.value,
            "uptime_seconds": self.stats.uptime_seconds,
            "files_scanned": self.stats.files_scanned,
            "threats_detected": self.stats.threats_detected,
            "files_quarantined": self.stats.files_quarantined,
            "files_blocked": self.stats.files_blocked,
            "scan_rate_fps": self.stats.scan_rate_fps,
            "false_positives": self.stats.false_positives,
            "threat_history_count": len(self.threat_history),
            "monitored_files_count": len(self.monitored_files),
            "protection_rules_count": len([r for r in self.protection_rules if r.enabled]),
            "quarantine_files_count": len(list(self.quarantine_dir.iterdir())) if self.quarantine_dir.exists() else 0
        }

    def get_recent_threats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent threat detections."""
        recent_threats = sorted(
            self.threat_history, 
            key=lambda t: t.detection_time, 
            reverse=True
        )[:limit]
        
        return [
            {
                "file_path": threat.file_path,
                "threat_name": threat.threat_name,
                "threat_type": threat.threat_type,
                "threat_level": threat.threat_level.name,
                "detection_time": threat.detection_time.isoformat(),
                "action_taken": threat.action_taken.value,
                "quarantine_path": threat.quarantine_path,
                "file_size": threat.file_size
            }
            for threat in recent_threats
        ]

    # Callback setters
    def set_threat_detected_callback(self, callback: Callable[[ThreatDetection], None]):
        """Set callback for threat detection."""
        self.threat_detected_callback = callback

    def set_file_blocked_callback(self, callback: Callable[[str, str], None]):
        """Set callback for file blocking."""
        self.file_blocked_callback = callback

    def set_protection_status_callback(self, callback: Callable[[ProtectionState, str], None]):
        """Set callback for protection status changes."""
        self.protection_status_callback = callback

    async def handle_file_event(self, file_path: str, event_type: str):
        """
        Handle file system event and perform real-time protection.
        
        Args:
            file_path: Path to file that triggered event
            event_type: Type of file system event
        """
        try:
            # Track file monitoring
            self.monitored_files[file_path] = {
                "last_seen": datetime.now(),
                "event_type": event_type,
                "creation_time": datetime.now() if event_type == "created" else 
                               self.monitored_files.get(file_path, {}).get("creation_time", datetime.now())
            }
            
            # Perform real-time scan
            threat_detection = await self.scan_file_realtime(file_path)
            
            if threat_detection:
                # Add to threat history
                self.threat_history.append(threat_detection)
                self.stats.threats_detected += 1
                
                # Execute protection action
                if threat_detection.action_taken == ProtectionAction.QUARANTINE:
                    await self.quarantine_file(file_path, threat_detection)
                elif threat_detection.action_taken == ProtectionAction.BLOCK:
                    self.stats.files_blocked += 1
                    if self.file_blocked_callback:
                        self.file_blocked_callback(file_path, threat_detection.threat_name)
                
                # Notify about threat detection
                if self.threat_detected_callback:
                    self.threat_detected_callback(threat_detection)
                
                self.logger.warning("THREAT DETECTED: %s - %s (%s)", 
                                  file_path, threat_detection.threat_name, threat_detection.threat_type)
            
        except Exception as e:
            self.logger.error("Error handling file event for %s: %s", file_path, e)
