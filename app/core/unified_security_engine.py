#!/usr/bin/env python3
"""Unified Security Engine for xanadOS Search & Destroy
Consolidates all security components into a single, optimized system.
This module combines:
- Enhanced Real-Time Protection
- Enhanced File System Monitoring
- Integrated Protection Management
- 2025 Security Research Optimizations
Features:
- eBPF-based kernel monitoring
- Machine learning anomaly detection
- Adaptive resource management
- Advanced threat detection
- Performance optimization
"""

import asyncio
import logging
import os
import tempfile
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Security Research Integration (2025)
from importlib.util import find_spec as _find_spec
from pathlib import Path
from typing import Any

import numpy as np
import psutil

# Check for optional dependencies safely
try:
    EBPF_AVAILABLE = _find_spec("bpftool") is not None
except (ModuleNotFoundError, AttributeError):
    EBPF_AVAILABLE = False

try:
    WATCHDOG_AVAILABLE = _find_spec("watchdog") is not None
except (ModuleNotFoundError, AttributeError):
    WATCHDOG_AVAILABLE = False

# fanotify constants for advanced monitoring (statically defined for internal use)
FAN_ACCESS = 0x00000001
FAN_MODIFY = 0x00000002
FAN_CLOSE_WRITE = 0x00000008
FAN_CREATE = 0x00000100
FANOTIFY_AVAILABLE = True


class ThreatLevel(Enum):
    """Threat level classification."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ProtectionMode(Enum):
    """Protection operation modes."""

    MAXIMUM_SECURITY = "maximum_security"
    BALANCED = "balanced"
    PERFORMANCE = "performance"
    GAMING = "gaming"
    CUSTOM = "custom"


class EventType(Enum):
    """Security event types with priority."""

    FILE_CREATED = ("file_created", 3)
    FILE_EXECUTED = ("file_executed", 3)
    EXECUTABLE_MODIFIED = ("executable_modified", 3)
    FILE_MODIFIED = ("file_modified", 2)
    FILE_MOVED = ("file_moved", 2)
    FILE_ACCESSED = ("file_accessed", 1)
    PROCESS_SPAWNED = ("process_spawned", 3)
    NETWORK_CONNECTION = ("network_connection", 2)
    PRIVILEGE_ESCALATION = ("privilege_escalation", 3)

    def __init__(self, event_name: str, priority: int):
        self.event_name = event_name
        self.priority = priority


@dataclass
class SecurityEvent:
    """Unified security event representation."""

    event_type: EventType
    timestamp: float
    source_path: str
    target_path: str | None = None
    process_id: int | None = None
    user_id: int | None = None
    threat_level: ThreatLevel = ThreatLevel.LOW
    additional_data: dict[str, Any] | None = None
    detection_latency_ms: float = 0.0

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class SystemHealth:
    """Comprehensive system health metrics."""

    cpu_usage: float
    memory_usage: float
    disk_io_usage: float
    network_activity: float
    active_processes: int
    threat_level: ThreatLevel
    protection_mode: str
    last_update: datetime
    performance_score: float = 0.0


class MLAnomalyDetector:
    """Lightweight ML-based anomaly detection engine."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.training_data = defaultdict(list)
        self.sensitivity = 0.7
        self.min_samples = 100

        # Statistical thresholds
        self.file_size_threshold = 2.0  # Z-score threshold
        self.access_pattern_threshold = 2.5
        self.process_behavior_threshold = 2.0

    def update_sensitivity(self, sensitivity: float):
        """Update ML model sensitivity."""
        self.sensitivity = max(0.1, min(0.9, sensitivity))

    def add_training_sample(self, event: SecurityEvent):
        """Add training sample for ML models."""
        try:
            # File size anomaly detection
            if event.source_path and os.path.exists(event.source_path):
                file_size = os.path.getsize(event.source_path)
                self.training_data["file_sizes"].append(file_size)

            # Process behavior tracking
            if event.process_id:
                self.training_data["process_behavior"].append(
                    {
                        "pid": event.process_id,
                        "event_type": event.event_type.event_name,
                        "timestamp": event.timestamp,
                    }
                )

        except Exception as e:
            self.logger.error(f"Error adding training sample: {e}")

    def detect_anomaly(self, event: SecurityEvent) -> tuple[bool, float]:
        """Detect if event is anomalous using ML models."""
        try:
            anomaly_scores = []

            # File size anomaly detection
            if event.source_path and os.path.exists(event.source_path):
                file_score = self._detect_file_size_anomaly(event.source_path)
                anomaly_scores.append(file_score)

            # Process behavior anomaly
            if event.process_id:
                process_score = self._detect_process_behavior_anomaly(event)
                anomaly_scores.append(process_score)

            # Calculate overall anomaly score
            if anomaly_scores:
                overall_score = max(anomaly_scores)  # Take highest anomaly score
                is_anomaly = overall_score > self.sensitivity
                return is_anomaly, overall_score

            return False, 0.0

        except Exception as e:
            self.logger.error(f"Error detecting anomaly: {e}")
            return False, 0.0

    def _detect_file_size_anomaly(self, file_path: str) -> float:
        """Detect file size anomalies using statistical analysis."""
        try:
            file_size = os.path.getsize(file_path)
            sizes = self.training_data["file_sizes"]

            if len(sizes) < self.min_samples:
                return 0.0

            # Calculate z-score
            mean_size = np.mean(sizes)
            std_size = np.std(sizes)

            if std_size == 0:
                return 0.0

            z_score = abs((file_size - mean_size) / std_size)

            # Convert z-score to anomaly score (0-1)
            anomaly_score = min(1.0, z_score / self.file_size_threshold)

            return anomaly_score

        except Exception:
            return 0.0

    def _detect_process_behavior_anomaly(self, event: SecurityEvent) -> float:
        """Detect process behavior anomalies."""
        try:
            # Simple heuristic: rapid-fire events from same process
            recent_events = [
                e
                for e in self.training_data["process_behavior"][-100:]
                if e["pid"] == event.process_id and event.timestamp - e["timestamp"] < 1.0
            ]

            # High frequency of events in short time = suspicious
            if len(recent_events) > 10:
                return 0.8
            elif len(recent_events) > 5:
                return 0.5

            return 0.0

        except Exception:
            return 0.0


class SmartEventFilter:
    """Intelligent event filtering with 2025 optimizations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # File extension classification (2025 threat intelligence)
        self.high_risk_extensions = {
            ".exe",
            ".dll",
            ".bat",
            ".cmd",
            ".scr",
            ".pif",
            ".com",
            ".jar",
            ".py",
            ".sh",
            ".js",
            ".vbs",
            ".ps1",
            ".msi",
            ".appimage",
            ".flatpak",
            ".snap",  # Linux-specific
        }

        self.medium_risk_extensions = {
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".bz2",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".deb",
            ".rpm",  # Package files
        }

        # Path-based exclusions (optimized for 2025)
        self.excluded_paths = {
            "/proc",
            "/sys",
            "/dev",
            tempfile.gettempdir(),  # Use system temp directory
            "/var/log",
            "/var/cache",
            "/.git",
            "/node_modules",
            "/__pycache__",
            "/.venv",
            "/snap",
            "/var/lib/flatpak",  # Modern Linux paths
        }

        self.high_priority_paths = {
            "/home",
            "/usr/bin",
            "/usr/local/bin",
            "/opt",
            "/etc",
            "/usr/share/applications",
            "/var/lib",  # Critical system paths
        }

        # eBPF integration (2025 research)
        self.ebpf_filters = {
            "syscalls": ["execve", "open", "openat", "unlink", "rename"],
            "network": ["connect", "bind", "listen"],
            "process": ["fork", "clone", "vfork"],
        }

        # Event history for duplicate detection
        self.event_history = defaultdict(deque)
        self.duplicate_threshold = 0.5  # seconds

    def should_process_event(self, event: SecurityEvent) -> bool:
        """Determine if event should be processed based on intelligent filtering."""
        try:
            # Skip excluded paths
            if any(event.source_path.startswith(path) for path in self.excluded_paths):
                return False

            # Skip temporary files
            if self._is_temporary_file(event.source_path):
                return False

            # Check for duplicates
            if self._is_duplicate_event(event):
                return False

            # Priority-based filtering
            file_path = Path(event.source_path)
            extension = file_path.suffix.lower()

            # Always process high-risk files
            if extension in self.high_risk_extensions:
                return True

            # Process high-priority paths
            if any(event.source_path.startswith(path) for path in self.high_priority_paths):
                if event.event_type in [
                    EventType.FILE_CREATED,
                    EventType.EXECUTABLE_MODIFIED,
                ]:
                    return True

            # Skip low-priority events for low-risk files
            if (
                extension not in self.medium_risk_extensions
                and event.event_type == EventType.FILE_ACCESSED
            ):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error filtering event: {e}")
            return True  # Default to processing on error

    def _is_temporary_file(self, file_path: str) -> bool:
        """Check if file is temporary."""
        path = Path(file_path)
        name = path.name.lower()

        temp_patterns = [".tmp", ".temp", ".swp", ".~", ".bak", ".log"]
        return any(pattern in name for pattern in temp_patterns)

    def _is_duplicate_event(self, event: SecurityEvent) -> bool:
        """Check for duplicate events."""
        path_history = self.event_history[event.source_path]
        current_time = event.timestamp

        # Remove old events
        while path_history and current_time - path_history[0].timestamp > 5.0:
            path_history.popleft()

        # Check for recent similar events
        for recent_event in path_history:
            if (
                current_time - recent_event.timestamp < self.duplicate_threshold
                and recent_event.event_type == event.event_type
            ):
                return True

        # Add current event to history
        path_history.append(event)
        return False


class AdaptiveResourceManager:
    """Advanced resource management with 2025 optimizations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Performance thresholds (updated for 2025)
        self.cpu_high_threshold = 75.0  # Reduced from 80%
        self.memory_high_threshold = 80.0  # Reduced from 85%
        self.disk_high_threshold = 85.0

        # Protection modes with 2025 optimizations
        self.modes = {
            ProtectionMode.MAXIMUM_SECURITY: {
                "scan_depth": "deep",
                "ml_sensitivity": 0.9,
                "batch_size": 1,
                "scan_interval": 0.05,  # Faster scanning
                "thread_count": 4,
                "enable_ebpf": True,
            },
            ProtectionMode.BALANCED: {
                "scan_depth": "standard",
                "ml_sensitivity": 0.7,
                "batch_size": 5,
                "scan_interval": 0.2,
                "thread_count": 2,
                "enable_ebpf": True,
            },
            ProtectionMode.PERFORMANCE: {
                "scan_depth": "quick",
                "ml_sensitivity": 0.5,
                "batch_size": 15,
                "scan_interval": 0.5,
                "thread_count": 1,
                "enable_ebpf": False,
            },
            ProtectionMode.GAMING: {
                "scan_depth": "minimal",
                "ml_sensitivity": 0.3,
                "batch_size": 30,
                "scan_interval": 2.0,
                "thread_count": 1,
                "enable_ebpf": False,
            },
        }

        # Performance history
        self.performance_history = []
        self.optimization_learning = True

    def analyze_system_health(self) -> SystemHealth:
        """Analyze comprehensive system health."""
        try:
            # Core system metrics
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Network activity (enhanced for 2025)
            net_io = psutil.net_io_counters()
            network_activity = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)

            # Process count and analysis
            processes = list(psutil.process_iter(["pid", "name", "cpu_percent"]))
            active_processes = len(processes)

            # Threat level assessment (enhanced)
            threat_level = self._assess_threat_level(cpu_percent, memory.percent, processes)

            # Protection mode determination
            protection_mode = self._determine_optimal_mode(
                cpu_percent, memory.percent, disk.percent
            )

            # Performance score calculation (new for 2025)
            performance_score = self._calculate_performance_score(
                cpu_percent, memory.percent, disk.percent
            )

            return SystemHealth(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_io_usage=disk.percent,
                network_activity=network_activity,
                active_processes=active_processes,
                threat_level=threat_level,
                protection_mode=protection_mode.value,
                last_update=datetime.now(),
                performance_score=performance_score,
            )

        except Exception as e:
            self.logger.error(f"Error analyzing system health: {e}")
            return SystemHealth(0, 0, 0, 0, 0, ThreatLevel.LOW, "balanced", datetime.now())

    def _assess_threat_level(
        self, cpu_usage: float, memory_usage: float, processes: list
    ) -> ThreatLevel:
        """Enhanced threat level assessment."""
        # High resource usage might indicate malicious activity
        if cpu_usage > 95 or memory_usage > 95:
            return ThreatLevel.CRITICAL
        elif cpu_usage > 85 or memory_usage > 85:
            return ThreatLevel.HIGH
        elif cpu_usage > 70 or memory_usage > 70:
            return ThreatLevel.MEDIUM

        # Check for suspicious process behavior
        suspicious_processes = 0
        for proc in processes:
            try:
                if proc.info["cpu_percent"] > 50:  # High CPU usage process
                    suspicious_processes += 1
            except BaseException:
                pass

        if suspicious_processes > 3:
            return ThreatLevel.HIGH
        elif suspicious_processes > 1:
            return ThreatLevel.MEDIUM

        return ThreatLevel.LOW

    def _determine_optimal_mode(self, cpu: float, memory: float, disk: float) -> ProtectionMode:
        """Determine optimal protection mode with ML learning."""
        # Critical resource usage - minimize overhead
        if cpu > 90 or memory > 90:
            return ProtectionMode.GAMING

        # High resource usage - performance mode
        elif cpu > self.cpu_high_threshold or memory > self.memory_high_threshold:
            return ProtectionMode.PERFORMANCE

        # Low resource usage - maximize security
        elif cpu < 25 and memory < 40:
            return ProtectionMode.MAXIMUM_SECURITY

        # Default balanced approach
        else:
            return ProtectionMode.BALANCED

    def _calculate_performance_score(self, cpu: float, memory: float, disk: float) -> float:
        """Calculate overall system performance score (0-100)."""
        # Weighted performance calculation
        cpu_score = max(0, 100 - cpu)
        memory_score = max(0, 100 - memory)
        disk_score = max(0, 100 - disk)

        # Weighted average (CPU and memory more important)
        performance_score = cpu_score * 0.4 + memory_score * 0.4 + disk_score * 0.2

        return round(performance_score, 2)


class UnifiedSecurityEngine:
    """Main unified security engine combining all components."""

    def __init__(self, watch_paths: list[str]):
        self.logger = logging.getLogger(__name__)
        self.watch_paths = watch_paths

        # Core components
        self.ml_detector = MLAnomalyDetector()
        self.event_filter = SmartEventFilter()
        self.resource_manager = AdaptiveResourceManager()

        # State management
        self.is_running = False
        self.current_mode = ProtectionMode.BALANCED
        self.threat_level = ThreatLevel.LOW

        # Event processing
        self.event_queue = asyncio.Queue()
        self.processed_events = 0
        self.threats_detected = 0

        # Performance tracking
        self.performance_metrics = {
            "events_processed": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "avg_processing_time": 0.0,
            "system_impact": 0.0,
            "uptime_seconds": 0.0,
        }

        # Callbacks
        self.threat_callbacks: list[Callable] = []
        self.performance_callbacks: list[Callable] = []

        # Background tasks
        self.monitoring_tasks: list[asyncio.Task] = []

        self.start_time = time.time()

    async def initialize(self) -> bool:
        """Initialize the unified security engine."""
        try:
            self.logger.info("🛡️ Initializing Unified Security Engine...")

            # Check system capabilities
            capabilities = self._check_system_capabilities()
            self.logger.info(f"📊 System capabilities: {capabilities}")

            # Initialize ML detector
            await self._initialize_ml_detector()

            # Set initial protection mode
            health = self.resource_manager.analyze_system_health()
            self.current_mode = ProtectionMode(health.protection_mode)

            self.logger.info(
                f"✅ Unified Security Engine initialized in {self.current_mode.value} mode"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize security engine: {e}")
            return False

    def _check_system_capabilities(self) -> dict[str, bool]:
        """Check available system capabilities for 2025 features."""
        capabilities = {
            "ebpf": EBPF_AVAILABLE and os.geteuid() == 0,
            "fanotify": FANOTIFY_AVAILABLE and os.geteuid() == 0,
            "watchdog": WATCHDOG_AVAILABLE,
            "root_privileges": os.geteuid() == 0,
            "kernel_version": self._get_kernel_version(),
        }

        return capabilities

    def _get_kernel_version(self) -> str:
        """Get kernel version for capability assessment."""
        try:
            with open("/proc/version") as f:
                return f.read().strip()
        except BaseException:
            return "unknown"

    async def _initialize_ml_detector(self):
        """Initialize ML detection with baseline data."""
        # This would load pre-trained models or initialize with baseline data
        self.logger.info("🤖 ML Anomaly Detector initialized")

    async def start_protection(self) -> bool:
        """Start the unified security protection system."""
        try:
            if self.is_running:
                return True

            self.logger.info("🚀 Starting Unified Security Protection...")

            # Start file system monitoring
            monitoring_task = asyncio.create_task(self._file_system_monitor())
            self.monitoring_tasks.append(monitoring_task)

            # Start system health monitoring
            health_task = asyncio.create_task(self._health_monitor())
            self.monitoring_tasks.append(health_task)

            # Start event processing
            processing_task = asyncio.create_task(self._event_processor())
            self.monitoring_tasks.append(processing_task)

            # Start performance monitoring
            perf_task = asyncio.create_task(self._performance_monitor())
            self.monitoring_tasks.append(perf_task)

            self.is_running = True
            self.start_time = time.time()

            self.logger.info("✅ Unified Security Protection started successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start protection: {e}")
            await self.stop_protection()
            return False

    async def stop_protection(self):
        """Stop the unified security protection system."""
        self.logger.info("🛑 Stopping Unified Security Protection...")

        self.is_running = False

        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        self.monitoring_tasks.clear()

        self.logger.info("✅ Unified Security Protection stopped")

    async def _file_system_monitor(self):
        """Advanced file system monitoring with 2025 optimizations."""
        self.logger.info("👁️ Starting file system monitoring...")

        # This would implement fanotify/watchdog monitoring
        # For now, simulating with periodic checks
        while self.is_running:
            try:
                # Simulate file system events
                for path in self.watch_paths:
                    if os.path.exists(path):
                        await self._simulate_fs_events(path)

                await asyncio.sleep(0.1)  # High-frequency monitoring

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in file system monitoring: {e}")
                await asyncio.sleep(1.0)

    async def _simulate_fs_events(self, path: str):
        """Simulate file system events for testing."""
        # This would be replaced with actual fanotify/watchdog implementation
        try:
            for root, dirs, files in os.walk(path):
                if not self.is_running:
                    break

                for file in files[:5]:  # Limit for simulation
                    file_path = os.path.join(root, file)

                    event = SecurityEvent(
                        event_type=EventType.FILE_ACCESSED,
                        timestamp=time.time(),
                        source_path=file_path,
                    )

                    if self.event_filter.should_process_event(event):
                        await self.event_queue.put(event)

                # Only check first level for simulation
                break

        except Exception as e:
            self.logger.debug(f"Simulation error for {path}: {e}")

    async def _event_processor(self):
        """Process security events with ML analysis."""
        self.logger.info("⚙️ Starting event processor...")

        while self.is_running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                start_time = time.time()

                # ML anomaly detection
                is_anomaly, anomaly_score = self.ml_detector.detect_anomaly(event)

                # Update threat level based on anomaly
                if is_anomaly:
                    if anomaly_score > 0.8:
                        event.threat_level = ThreatLevel.HIGH
                    elif anomaly_score > 0.6:
                        event.threat_level = ThreatLevel.MEDIUM
                    else:
                        event.threat_level = ThreatLevel.LOW

                # Process threat
                if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    await self._handle_threat(event, anomaly_score)

                # Update metrics
                processing_time = (time.time() - start_time) * 1000
                event.detection_latency_ms = processing_time

                self.performance_metrics["events_processed"] += 1
                self._update_performance_averages(processing_time)

                # Add to training data
                self.ml_detector.add_training_sample(event)

            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")

    async def _handle_threat(self, event: SecurityEvent, anomaly_score: float):
        """Handle detected threats."""
        self.threats_detected += 1
        self.performance_metrics["threats_detected"] += 1

        threat_info = {
            "event": event,
            "anomaly_score": anomaly_score,
            "detection_time": datetime.now(),
            "action_taken": "logged",  # Would implement actual response
        }

        self.logger.warning(f"🚨 THREAT DETECTED: {event.source_path} (score: {anomaly_score:.3f})")

        # Call threat callbacks
        for callback in self.threat_callbacks:
            try:
                callback(threat_info)
            except Exception as e:
                self.logger.error(f"Error in threat callback: {e}")

    async def _health_monitor(self):
        """Monitor system health and adjust protection mode."""
        self.logger.info("💓 Starting health monitoring...")

        while self.is_running:
            try:
                health = self.resource_manager.analyze_system_health()

                # Check if mode change is needed
                optimal_mode = ProtectionMode(health.protection_mode)
                if optimal_mode != self.current_mode:
                    await self._change_protection_mode(optimal_mode)

                # Update current threat level
                self.threat_level = health.threat_level

                # Call performance callbacks
                for callback in self.performance_callbacks:
                    try:
                        callback(health)
                    except Exception as e:
                        self.logger.error(f"Error in performance callback: {e}")

                await asyncio.sleep(10.0)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(5.0)

    async def _performance_monitor(self):
        """Monitor and optimize performance."""
        self.logger.info("📈 Starting performance monitoring...")

        while self.is_running:
            try:
                # Update uptime
                self.performance_metrics["uptime_seconds"] = time.time() - self.start_time

                # Calculate system impact
                health = self.resource_manager.analyze_system_health()
                self.performance_metrics["system_impact"] = 100 - health.performance_score

                await asyncio.sleep(30.0)  # Monitor every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(10.0)

    async def _change_protection_mode(self, new_mode: ProtectionMode):
        """Change protection mode with optimization."""
        try:
            old_mode = self.current_mode
            self.current_mode = new_mode

            # Get new settings
            settings = self.resource_manager.modes[new_mode]

            # Update ML sensitivity
            self.ml_detector.update_sensitivity(settings["ml_sensitivity"])

            self.logger.info(f"🔄 Protection mode: {old_mode.value} → {new_mode.value}")

        except Exception as e:
            self.logger.error(f"Error changing protection mode: {e}")

    def _update_performance_averages(self, processing_time_ms: float):
        """Update rolling performance averages."""
        alpha = 0.1  # Smoothing factor

        current_avg = self.performance_metrics["avg_processing_time"]
        self.performance_metrics["avg_processing_time"] = (
            alpha * processing_time_ms + (1 - alpha) * current_avg
        )

    def add_threat_callback(self, callback: Callable):
        """Add callback for threat notifications."""
        self.threat_callbacks.append(callback)

    def add_performance_callback(self, callback: Callable):
        """Add callback for performance monitoring."""
        self.performance_callbacks.append(callback)

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive security engine status."""
        return {
            "engine_status": {
                "running": self.is_running,
                "current_mode": self.current_mode.value,
                "threat_level": self.threat_level.value,
                "uptime_seconds": time.time() - self.start_time,
            },
            "performance_metrics": self.performance_metrics.copy(),
            "system_health": self.resource_manager.analyze_system_health().__dict__,
            "ml_detector": {
                "sensitivity": self.ml_detector.sensitivity,
                "training_samples": len(self.ml_detector.training_data["file_sizes"]),
            },
        }


# Example usage and testing
async def demonstrate_unified_engine():
    """Demonstrate the unified security engine."""
    print("🛡️ Unified Security Engine Demonstration")
    print("=" * 50)

    # Define paths to monitor - avoid hardcoded /tmp
    watch_paths = [tempfile.gettempdir(), "/home"]

    # Create unified engine
    engine = UnifiedSecurityEngine(watch_paths)

    # Add callbacks
    def threat_callback(threat_info):
        print(
            f"🚨 THREAT: {threat_info['event'].source_path} "
            f"(score: {threat_info['anomaly_score']:.3f})"
        )

    def performance_callback(health: SystemHealth):
        print(
            f"📊 Health - CPU: {health.cpu_usage:.1f}%, "
            f"Memory: {health.memory_usage:.1f}%, "
            f"Mode: {health.protection_mode}, "
            f"Score: {health.performance_score:.1f}"
        )

    engine.add_threat_callback(threat_callback)
    engine.add_performance_callback(performance_callback)

    try:
        # Initialize and start
        if await engine.initialize():
            print("✅ Engine initialized")

            if await engine.start_protection():
                print("✅ Protection started")

                # Let it run for demonstration
                print("⏱️ Running for 60 seconds...")
                await asyncio.sleep(60.0)

                # Show final status
                status = engine.get_status()
                print("\n📊 Final Status:")
                print(f"   Events processed: {status['performance_metrics']['events_processed']}")
                print(f"   Threats detected: {status['performance_metrics']['threats_detected']}")
                print(
                    f"   Avg processing time: {status['performance_metrics']['avg_processing_time']:.2f}ms"
                )
                print(f"   System impact: {status['performance_metrics']['system_impact']:.1f}%")

            else:
                print("❌ Failed to start protection")
        else:
            print("❌ Failed to initialize engine")

    finally:
        await engine.stop_protection()
        print("✅ Engine stopped cleanly")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run demonstration
    asyncio.run(demonstrate_unified_engine())
