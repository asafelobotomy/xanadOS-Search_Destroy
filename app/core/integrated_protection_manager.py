#!/usr/bin/env python3
"""
Enhanced Real-Time Protection Integration
Combines all 2025 optimization techniques into a unified system:
- Enhanced file system monitoring with fanotify/eBPF
- Machine learning anomaly detection
- Adaptive resource management
- Behavioral analysis and heuristic detection
- Performance monitoring and optimization
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import psutil

# Import our enhanced components
try:
    from .enhanced_file_watcher import (
        EnhancedFileSystemWatcher,
        WatchEvent,
        WatchEventType,
    )
    from .unified_security_engine import (
        ProtectionMode,
        SecurityEvent,
        ThreatLevel,
        UnifiedSecurityEngine,
    )
    from .enhanced_real_time_protection import EnhancedRealTimeProtection
except ImportError:
    # For standalone testing, provide light fallbacks
    EnhancedFileSystemWatcher = None  # type: ignore
    WatchEvent = None  # type: ignore
    WatchEventType = None  # type: ignore
    ProtectionMode = None  # type: ignore
    SecurityEvent = None  # type: ignore
    ThreatLevel = None  # type: ignore
    UnifiedSecurityEngine = None  # type: ignore
    EnhancedRealTimeProtection = None  # type: ignore


# Local lightweight event type used to pass events to protection engine when needed
@dataclass
class ProtectionEvent:
    event_type: str
    file_path: str
    threat_level: ThreatLevel
    details: Dict[str, Any]


@dataclass
class SystemHealth:
    """System health metrics for adaptive protection."""

    cpu_usage: float
    memory_usage: float
    disk_io_usage: float
    network_activity: float
    active_processes: int
    threat_level: ThreatLevel
    protection_mode: str
    last_update: datetime


class PerformanceOptimizer:
    """Intelligent performance optimizer based on system conditions."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Performance thresholds
        self.cpu_high_threshold = 80.0
        self.memory_high_threshold = 85.0
        self.disk_high_threshold = 90.0

        # Optimization history
        self.optimization_history = []
        self.last_optimization = None

        # Performance modes
        self.modes = {
            "maximum_security": {
                "scan_depth": "deep",
                "ml_sensitivity": 0.9,
                "heuristic_level": "aggressive",
                "batch_size": 1,
                "scan_interval": 0.1,
            },
            "balanced": {
                "scan_depth": "standard",
                "ml_sensitivity": 0.7,
                "heuristic_level": "moderate",
                "batch_size": 5,
                "scan_interval": 0.5,
            },
            "performance": {
                "scan_depth": "quick",
                "ml_sensitivity": 0.5,
                "heuristic_level": "basic",
                "batch_size": 20,
                "scan_interval": 1.0,
            },
            "gaming": {
                "scan_depth": "minimal",
                "ml_sensitivity": 0.3,
                "heuristic_level": "basic",
                "batch_size": 50,
                "scan_interval": 2.0,
            },
        }

    def analyze_system_health(self) -> SystemHealth:
        """Analyze current system health and performance."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Network activity (simplified)
            net_io = psutil.net_io_counters()
            network_activity = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # MB

            # Process count
            active_processes = len(psutil.pids())

            # Determine threat level based on system state
            threat_level = self._assess_threat_level(cpu_percent, memory.percent)

            # Determine optimal protection mode
            protection_mode = self._determine_protection_mode(
                cpu_percent, memory.percent, disk.percent
            )

            return SystemHealth(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_io_usage=disk.percent,
                network_activity=network_activity,
                active_processes=active_processes,
                threat_level=threat_level,
                protection_mode=protection_mode,
                last_update=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing system health: {e}")
            return SystemHealth(0, 0, 0, 0, 0, ThreatLevel.LOW, "balanced", datetime.now())

    def _assess_threat_level(self, cpu_usage: float, memory_usage: float) -> ThreatLevel:
        """Assess current threat level based on system activity."""
        # High resource usage might indicate malicious activity
        if cpu_usage > 90 or memory_usage > 90:
            return ThreatLevel.HIGH
        elif cpu_usage > 70 or memory_usage > 70:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    def _determine_protection_mode(self, cpu: float, memory: float, disk: float) -> str:
        """Determine optimal protection mode based on system resources."""
        # High resource usage - reduce protection overhead
        if cpu > self.cpu_high_threshold or memory > self.memory_high_threshold:
            return "performance"

        # Very low resource usage - can afford maximum security
        elif cpu < 30 and memory < 50:
            return "maximum_security"

        # Moderate usage - balanced approach
        else:
            return "balanced"

    def get_optimization_settings(self, mode: str) -> Dict[str, Any]:
        """Get optimization settings for a specific mode."""
        return self.modes.get(mode, self.modes["balanced"])

    def record_optimization(self, mode: str, performance_impact: float):
        """Record optimization results for learning."""
        optimization_record = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "performance_impact": performance_impact,
            "system_state": self.analyze_system_health().__dict__,
        }

        self.optimization_history.append(optimization_record)
        self.last_optimization = optimization_record

        # Keep only recent history
        if len(self.optimization_history) > 1000:
            self.optimization_history = self.optimization_history[-500:]


class IntegratedProtectionManager:
    """Main integrated protection manager combining all enhancements."""

    def __init__(self, watch_paths: List[str]):
        self.logger = logging.getLogger(__name__)
        self.watch_paths = watch_paths

        # Core components
        self.file_watcher: Optional[EnhancedFileSystemWatcher] = None
        self.protection_engine: Optional[EnhancedRealTimeProtection] = None
        self.performance_optimizer = PerformanceOptimizer()

        # State management
        self.is_running = False
        self.current_mode = "balanced"
        self.threat_level = ThreatLevel.LOW

        # Performance tracking
        self.performance_metrics = {
            "files_scanned": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "scan_time_avg": 0.0,
            "cpu_usage_avg": 0.0,
            "memory_usage_avg": 0.0,
            "uptime": 0.0,
        }

        # Event callbacks
        self.threat_callbacks: List[Callable] = []
        self.performance_callbacks: List[Callable] = []

        # Background tasks
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.performance_task: Optional[asyncio.Task] = None

        self.start_time = time.time()

    async def initialize(self) -> bool:
        """Initialize all protection components."""
        try:
            self.logger.info("🔒 Initializing Integrated Protection Manager...")

            # Initialize file system watcher
            self.file_watcher = EnhancedFileSystemWatcher(
                self.watch_paths, self._handle_file_events
            )

            # Initialize protection engine
            self.protection_engine = EnhancedRealTimeProtection()
            await self.protection_engine.initialize()

            # Optimize initial settings
            await self._optimize_settings()

            self.logger.info("✅ Integrated Protection Manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize protection manager: {e}")
            return False

    async def start_protection(self) -> bool:
        """Start the integrated protection system."""
        try:
            if self.is_running:
                return True

            self.logger.info("🚀 Starting Integrated Protection System...")

            # Start file system monitoring
            if not self.file_watcher.start_monitoring():
                raise Exception("Failed to start file system monitoring")

            # Start protection engine
            await self.protection_engine.start_protection()

            # Start background monitoring tasks
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            self.performance_task = asyncio.create_task(self._performance_monitor_loop())

            self.is_running = True
            self.start_time = time.time()

            self.logger.info("✅ Integrated Protection System started successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start protection system: {e}")
            await self.stop_protection()
            return False

    async def stop_protection(self):
        """Stop the integrated protection system."""
        self.logger.info("🛑 Stopping Integrated Protection System...")

        self.is_running = False

        # Stop background tasks
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
        if self.performance_task:
            self.performance_task.cancel()

        # Stop components
        if self.file_watcher:
            self.file_watcher.stop_monitoring()

        if self.protection_engine:
            await self.protection_engine.stop_protection()

        self.logger.info("✅ Integrated Protection System stopped")

    def _handle_file_events(self, events: List[WatchEvent]):
        """Handle file system events from the watcher."""
        try:
            # Convert file events to protection events
            protection_events = []

            for event in events:
                # Create protection event
                protection_event = ProtectionEvent(
                    event_type="file_system_activity",
                    file_path=event.file_path,
                    threat_level=self._assess_event_threat_level(event),
                    details={
                        "fs_event_type": event.event_type.event_name,
                        "file_size": event.file_size,
                        "process_id": event.process_id,
                        "timestamp": event.timestamp,
                    },
                )

                protection_events.append(protection_event)

            # Process events through protection engine
            if self.protection_engine:
                asyncio.create_task(self.protection_engine.process_events(protection_events))

            # Update metrics
            self.performance_metrics["files_scanned"] += len(events)

        except Exception as e:
            self.logger.error(f"Error handling file events: {e}")

    def _assess_event_threat_level(self, event: WatchEvent) -> ThreatLevel:
        """Assess threat level of a file system event."""
        # High-risk file creation/modification
        if event.event_type in [
            WatchEventType.FILE_CREATED,
            WatchEventType.EXECUTABLE_MODIFIED,
        ]:
            return ThreatLevel.HIGH

        # Medium-risk modifications
        if event.event_type == WatchEventType.FILE_MODIFIED:
            return ThreatLevel.MEDIUM

        # Low-risk events
        return ThreatLevel.LOW

    async def _health_monitor_loop(self):
        """Background task for monitoring system health."""
        while self.is_running:
            try:
                # Analyze system health
                health = self.performance_optimizer.analyze_system_health()

                # Update current state
                self.threat_level = health.threat_level

                # Check if mode change is needed
                if health.protection_mode != self.current_mode:
                    await self._change_protection_mode(health.protection_mode)

                # Call performance callbacks
                for callback in self.performance_callbacks:
                    try:
                        callback(health)
                    except Exception as e:
                        self.logger.error(f"Error in performance callback: {e}")

                # Wait before next check
                await asyncio.sleep(10.0)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(5.0)

    async def _performance_monitor_loop(self):
        """Background task for performance monitoring and optimization."""
        while self.is_running:
            try:
                # Update performance metrics
                self.performance_metrics["uptime"] = time.time() - self.start_time

                # Get current system usage
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent

                # Update averages
                self._update_performance_averages(cpu_usage, memory_usage)

                # Check for optimization opportunities
                await self._check_optimization_opportunities()

                await asyncio.sleep(30.0)  # Monitor every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in performance monitor loop: {e}")
                await asyncio.sleep(10.0)

    def _update_performance_averages(self, cpu_usage: float, memory_usage: float):
        """Update rolling performance averages."""
        # Simple exponential moving average
        alpha = 0.1  # Smoothing factor

        self.performance_metrics["cpu_usage_avg"] = (
            alpha * cpu_usage + (1 - alpha) * self.performance_metrics["cpu_usage_avg"]
        )

        self.performance_metrics["memory_usage_avg"] = (
            alpha * memory_usage + (1 - alpha) * self.performance_metrics["memory_usage_avg"]
        )

    async def _check_optimization_opportunities(self):
        """Check for performance optimization opportunities."""
        try:
            # Get current health
            health = self.performance_optimizer.analyze_system_health()

            # Check if current mode is still optimal
            optimal_mode = health.protection_mode

            if optimal_mode != self.current_mode:
                self.logger.info(
                    f"🔧 Optimization opportunity: switching from {self.current_mode} to {
                        optimal_mode
                    }"
                )
                await self._change_protection_mode(optimal_mode)

        except Exception as e:
            self.logger.error(f"Error checking optimization opportunities: {e}")

    async def _change_protection_mode(self, new_mode: str):
        """Change protection mode with optimization."""
        try:
            old_mode = self.current_mode
            self.current_mode = new_mode

            # Get new settings
            settings = self.performance_optimizer.get_optimization_settings(new_mode)

            # Apply settings to protection engine
            if self.protection_engine:
                await self.protection_engine.update_settings(settings)

            self.logger.info(f"🔄 Protection mode changed: {old_mode} → {new_mode}")

            # Record optimization
            performance_impact = 0.0  # Would calculate actual impact
            self.performance_optimizer.record_optimization(new_mode, performance_impact)

        except Exception as e:
            self.logger.error(f"Error changing protection mode: {e}")

    async def _optimize_settings(self):
        """Optimize initial settings based on system state."""
        health = self.performance_optimizer.analyze_system_health()
        await self._change_protection_mode(health.protection_mode)

    def add_threat_callback(self, callback: Callable):
        """Add callback for threat notifications."""
        self.threat_callbacks.append(callback)

    def add_performance_callback(self, callback: Callable):
        """Add callback for performance monitoring."""
        self.performance_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive protection system status."""
        file_watcher_stats = {}
        if self.file_watcher:
            file_watcher_stats = self.file_watcher.get_performance_stats()

        protection_stats = {}
        if self.protection_engine:
            protection_stats = self.protection_engine.get_performance_stats()

        health = self.performance_optimizer.analyze_system_health()

        return {
            "system_status": {
                "running": self.is_running,
                "current_mode": self.current_mode,
                "threat_level": self.threat_level.value,
                "uptime_seconds": time.time() - self.start_time,
            },
            "system_health": {
                "cpu_usage": health.cpu_usage,
                "memory_usage": health.memory_usage,
                "disk_usage": health.disk_io_usage,
                "active_processes": health.active_processes,
            },
            "performance_metrics": self.performance_metrics.copy(),
            "file_watcher": file_watcher_stats,
            "protection_engine": protection_stats,
            "optimization_history": self.performance_optimizer.optimization_history[
                -10:
            ],  # Last 10
        }

    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration for backup/sharing."""
        return {
            "version": "1.0",
            "watch_paths": self.watch_paths,
            "current_mode": self.current_mode,
            "performance_settings": self.performance_optimizer.get_optimization_settings(
                self.current_mode
            ),
            "exported_at": datetime.now().isoformat(),
        }

    async def import_configuration(self, config: Dict[str, Any]):
        """Import configuration from backup/sharing."""
        try:
            if config.get("version") != "1.0":
                raise ValueError("Unsupported configuration version")

            # Update watch paths if needed
            if "watch_paths" in config:
                self.watch_paths = config["watch_paths"]

            # Update mode if specified
            if "current_mode" in config:
                await self._change_protection_mode(config["current_mode"])

            self.logger.info("✅ Configuration imported successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to import configuration: {e}")
            raise


# Example usage and integration
async def demonstrate_integrated_protection():
    """Demonstrate the integrated protection system."""
    print("🛡️  Enhanced Real-Time Protection Integration Demo")
    print("=" * 60)

    # Define paths to monitor (adjust for your system)
    watch_paths = ["/tmp", "/home"]  # Example paths

    # Create integrated protection manager
    protection_manager = IntegratedProtectionManager(watch_paths)

    # Add callbacks for monitoring
    def threat_callback(threat_info):
        print(f"🚨 THREAT DETECTED: {threat_info}")

    def performance_callback(health: SystemHealth):
        print(
            f"📊 System Health - CPU: {health.cpu_usage:.1f}%, "
            f"Memory: {health.memory_usage:.1f}%, Mode: {health.protection_mode}"
        )

    protection_manager.add_threat_callback(threat_callback)
    protection_manager.add_performance_callback(performance_callback)

    try:
        # Initialize and start protection
        if await protection_manager.initialize():
            print("✅ Protection system initialized")

            if await protection_manager.start_protection():
                print("✅ Protection system started")

                # Let it run for demonstration
                print("⏱️  Running protection system for 30 seconds...")
                await asyncio.sleep(30.0)

                # Show status
                status = protection_manager.get_status()
                print("\n📊 Final Status:")
                print(f"   Files scanned: {status['performance_metrics']['files_scanned']}")
                print(f"   Uptime: {status['system_status']['uptime_seconds']:.1f}s")
                print(f"   Current mode: {status['system_status']['current_mode']}")
                print(f"   CPU usage: {status['system_health']['cpu_usage']:.1f}%")

                # Export configuration
                config = protection_manager.export_configuration()
                print(f"📄 Configuration exported with {len(config)} settings")

            else:
                print("❌ Failed to start protection system")
        else:
            print("❌ Failed to initialize protection system")

    finally:
        # Clean shutdown
        await protection_manager.stop_protection()
        print("✅ Protection system stopped cleanly")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run demonstration
    asyncio.run(demonstrate_integrated_protection())
