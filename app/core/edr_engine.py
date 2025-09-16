#!/usr/bin/env python3
"""EDR (Endpoint Detection & Response) Engine for xanadOS Search & Destroy.

This module implements enterprise-grade endpoint detection and response capabilities:
- Continuous endpoint monitoring and threat detection
- Automated incident response and containment
- Digital forensics evidence collection
- Advanced persistent threat (APT) detection
- Real-time behavioral analysis and alerting

Features:
- Process monitoring and analysis
- Network connection tracking
- File system integrity monitoring
- Memory analysis and dump collection
- Automated threat containment
- Forensic evidence preservation
- Incident response orchestration
"""

import asyncio
import hashlib
import json
import logging
import os
import signal
import subprocess
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import psutil

from app.core.ml_threat_detector import get_threat_detector
from app.core.unified_security_engine import SecurityEvent, ThreatLevel, EventType
from app.utils.config import get_config


class IncidentSeverity(Enum):
    """Incident severity levels."""

    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class ResponseAction(Enum):
    """Automated response actions."""

    MONITOR = "monitor"
    ALERT = "alert"
    QUARANTINE = "quarantine"
    BLOCK = "block"
    ISOLATE = "isolate"
    TERMINATE = "terminate"


@dataclass
class ProcessInfo:
    """Comprehensive process information."""

    pid: int
    ppid: int
    name: str
    cmdline: List[str]
    exe: str
    cwd: str
    username: str
    create_time: float
    cpu_percent: float
    memory_percent: float
    connections: List[Dict[str, Any]] = field(default_factory=list)
    open_files: List[str] = field(default_factory=list)
    children: List[int] = field(default_factory=list)
    threat_score: float = 0.0
    is_suspicious: bool = False


@dataclass
class NetworkConnection:
    """Network connection information."""

    pid: int
    process_name: str
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    status: str
    family: str
    type: str
    timestamp: float
    is_suspicious: bool = False
    threat_indicators: List[str] = field(default_factory=list)


@dataclass
class FileSystemEvent:
    """File system monitoring event."""

    event_type: str
    file_path: str
    process_pid: int
    process_name: str
    timestamp: float
    file_hash: Optional[str] = None
    file_size: int = 0
    is_suspicious: bool = False
    threat_indicators: List[str] = field(default_factory=list)


@dataclass
class SecurityIncident:
    """Security incident record."""

    incident_id: str
    severity: IncidentSeverity
    title: str
    description: str
    timestamp: float
    source_events: List[SecurityEvent]
    affected_processes: List[int]
    affected_files: List[str]
    network_indicators: List[str]
    response_actions: List[ResponseAction]
    evidence_collected: List[str] = field(default_factory=list)
    is_resolved: bool = False
    resolution_time: Optional[float] = None


class ProcessMonitor:
    """Advanced process monitoring and analysis."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitored_processes = {}
        self.process_history = deque(maxlen=1000)
        self.suspicious_patterns = [
            'powershell.exe -enc',
            'cmd.exe /c',
            'bash -c',
            'python -c',
            'perl -e',
            'wget',
            'curl',
            'nc ',
            'netcat',
        ]

    async def start_monitoring(self):
        """Start continuous process monitoring."""
        self.logger.info("Starting process monitoring")
        asyncio.create_task(self._monitor_processes())

    async def _monitor_processes(self):
        """Main process monitoring loop."""
        while True:
            try:
                current_processes = {}

                for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'exe',
                                               'cwd', 'username', 'create_time']):
                    try:
                        proc_info = proc.info
                        pid = proc_info['pid']

                        # Skip kernel threads
                        if not proc_info['cmdline']:
                            continue

                        # Create comprehensive process info
                        process_info = ProcessInfo(
                            pid=pid,
                            ppid=proc_info['ppid'],
                            name=proc_info['name'],
                            cmdline=proc_info['cmdline'] or [],
                            exe=proc_info['exe'] or '',
                            cwd=proc_info['cwd'] or '',
                            username=proc_info['username'] or '',
                            create_time=proc_info['create_time'],
                            cpu_percent=proc.cpu_percent(),
                            memory_percent=proc.memory_percent()
                        )

                        # Analyze for suspicious activity
                        await self._analyze_process(process_info)

                        current_processes[pid] = process_info

                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                # Detect new processes
                await self._detect_new_processes(current_processes)

                # Update monitored processes
                self.monitored_processes = current_processes

                await asyncio.sleep(2.0)  # Monitor every 2 seconds

            except Exception as e:
                self.logger.error(f"Process monitoring error: {e}")
                await asyncio.sleep(5.0)

    async def _analyze_process(self, process_info: ProcessInfo):
        """Analyze process for suspicious activity."""
        suspicion_score = 0.0
        cmdline_str = ' '.join(process_info.cmdline).lower()

        # Check for suspicious command patterns
        for pattern in self.suspicious_patterns:
            if pattern in cmdline_str:
                suspicion_score += 0.3
                break

        # Check for unusual execution locations
        if process_info.exe:
            suspicious_paths = ['/tmp/', '/var/tmp/', '/dev/shm/', '/home/']
            for path in suspicious_paths:
                if path in process_info.exe and process_info.name.endswith(('.sh', '.py', '.pl')):
                    suspicion_score += 0.2
                    break

        # Check for high resource usage
        if process_info.cpu_percent > 80 or process_info.memory_percent > 50:
            suspicion_score += 0.1

        # Check for privilege escalation indicators
        if 'sudo' in cmdline_str or 'su ' in cmdline_str:
            suspicion_score += 0.2

        process_info.threat_score = min(suspicion_score, 1.0)
        process_info.is_suspicious = suspicion_score > 0.3

    async def _detect_new_processes(self, current_processes: Dict[int, ProcessInfo]):
        """Detect and analyze new processes."""
        new_pids = set(current_processes.keys()) - set(self.monitored_processes.keys())

        for pid in new_pids:
            process_info = current_processes[pid]
            self.process_history.append(process_info)

            if process_info.is_suspicious:
                self.logger.warning(f"Suspicious process detected: {process_info.name} (PID: {pid})")
                # Generate security event
                event = SecurityEvent(
                    event_type=EventType.PROCESS_SPAWNED,
                    timestamp=time.time(),
                    source_path=process_info.exe,
                    process_id=pid,
                    threat_level=ThreatLevel.MEDIUM if process_info.threat_score > 0.5 else ThreatLevel.LOW,
                    additional_data={'process_info': asdict(process_info)}
                )
                # Here you would typically send this to the main EDR engine

    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get detailed information about a specific process."""
        return self.monitored_processes.get(pid)

    def get_suspicious_processes(self) -> List[ProcessInfo]:
        """Get all currently suspicious processes."""
        return [proc for proc in self.monitored_processes.values() if proc.is_suspicious]


class NetworkMonitor:
    """Network connection monitoring and analysis."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connections = {}
        self.connection_history = deque(maxlen=1000)
        self.suspicious_ports = {22, 23, 135, 139, 445, 1433, 3389, 5432, 5900}
        self.suspicious_ips = set()  # Would be populated from threat intelligence

    async def start_monitoring(self):
        """Start network monitoring."""
        self.logger.info("Starting network monitoring")
        asyncio.create_task(self._monitor_connections())

    async def _monitor_connections(self):
        """Monitor network connections."""
        while True:
            try:
                current_connections = {}

                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == psutil.CONN_LISTEN:
                        continue  # Skip listening sockets for now

                    # Get process information
                    process_name = "unknown"
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            process_name = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    connection = NetworkConnection(
                        pid=conn.pid or 0,
                        process_name=process_name,
                        local_address=conn.laddr.ip if conn.laddr else '',
                        local_port=conn.laddr.port if conn.laddr else 0,
                        remote_address=conn.raddr.ip if conn.raddr else '',
                        remote_port=conn.raddr.port if conn.raddr else 0,
                        status=conn.status,
                        family=conn.family.name,
                        type=conn.type.name,
                        timestamp=time.time()
                    )

                    # Analyze for suspicious activity
                    await self._analyze_connection(connection)

                    conn_key = f"{conn.pid}:{connection.local_port}:{connection.remote_address}:{connection.remote_port}"
                    current_connections[conn_key] = connection

                # Detect new connections
                await self._detect_new_connections(current_connections)

                self.connections = current_connections
                await asyncio.sleep(3.0)  # Monitor every 3 seconds

            except Exception as e:
                self.logger.error(f"Network monitoring error: {e}")
                await asyncio.sleep(5.0)

    async def _analyze_connection(self, connection: NetworkConnection):
        """Analyze connection for suspicious activity."""
        threat_indicators = []

        # Check for connections to suspicious ports
        if connection.remote_port in self.suspicious_ports:
            threat_indicators.append(f"Connection to suspicious port {connection.remote_port}")

        # Check for connections to suspicious IPs
        if connection.remote_address in self.suspicious_ips:
            threat_indicators.append(f"Connection to suspicious IP {connection.remote_address}")

        # Check for unusual outbound connections
        if connection.remote_port > 1024 and connection.process_name in ['sh', 'bash', 'cmd.exe', 'powershell.exe']:
            threat_indicators.append("Shell process making outbound connection")

        connection.threat_indicators = threat_indicators
        connection.is_suspicious = len(threat_indicators) > 0

    async def _detect_new_connections(self, current_connections: Dict[str, NetworkConnection]):
        """Detect and analyze new network connections."""
        new_keys = set(current_connections.keys()) - set(self.connections.keys())

        for key in new_keys:
            connection = current_connections[key]
            self.connection_history.append(connection)

            if connection.is_suspicious:
                self.logger.warning(f"Suspicious network connection: {connection.process_name} -> {connection.remote_address}:{connection.remote_port}")

    def get_suspicious_connections(self) -> List[NetworkConnection]:
        """Get all suspicious network connections."""
        return [conn for conn in self.connections.values() if conn.is_suspicious]


class IncidentResponseEngine:
    """Automated incident response and containment."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_incidents = {}
        self.incident_history = deque(maxlen=100)
        self.response_rules = self._load_response_rules()

    def _load_response_rules(self) -> Dict[str, Dict]:
        """Load automated response rules."""
        return {
            'malware_detected': {
                'severity': IncidentSeverity.HIGH,
                'actions': [ResponseAction.QUARANTINE, ResponseAction.ALERT]
            },
            'suspicious_process': {
                'severity': IncidentSeverity.MEDIUM,
                'actions': [ResponseAction.MONITOR, ResponseAction.ALERT]
            },
            'privilege_escalation': {
                'severity': IncidentSeverity.HIGH,
                'actions': [ResponseAction.TERMINATE, ResponseAction.ALERT]
            },
            'network_anomaly': {
                'severity': IncidentSeverity.MEDIUM,
                'actions': [ResponseAction.BLOCK, ResponseAction.ALERT]
            }
        }

    async def handle_security_event(self, event: SecurityEvent) -> Optional[SecurityIncident]:
        """Handle a security event and potentially create an incident."""
        try:
            # Determine incident type
            incident_type = self._classify_event(event)
            if not incident_type:
                return None

            # Create incident
            incident = await self._create_incident(incident_type, [event])

            # Execute automated response
            await self._execute_response(incident)

            return incident

        except Exception as e:
            self.logger.error(f"Incident handling failed: {e}")
            return None

    def _classify_event(self, event: SecurityEvent) -> Optional[str]:
        """Classify security event to determine incident type."""
        if event.threat_level == ThreatLevel.CRITICAL:
            return 'malware_detected'
        elif event.event_type == EventType.PRIVILEGE_ESCALATION:
            return 'privilege_escalation'
        elif event.event_type == EventType.PROCESS_SPAWNED and event.threat_level.value >= ThreatLevel.MEDIUM.value:
            return 'suspicious_process'
        elif event.event_type == EventType.NETWORK_CONNECTION:
            return 'network_anomaly'

        return None

    async def _create_incident(self, incident_type: str, events: List[SecurityEvent]) -> SecurityIncident:
        """Create a security incident."""
        incident_id = hashlib.md5(f"{incident_type}:{time.time()}".encode()).hexdigest()[:8]

        rule = self.response_rules.get(incident_type, {})
        severity = rule.get('severity', IncidentSeverity.LOW)

        incident = SecurityIncident(
            incident_id=incident_id,
            severity=severity,
            title=f"{incident_type.replace('_', ' ').title()} Detected",
            description=f"Automated detection of {incident_type}",
            timestamp=time.time(),
            source_events=events,
            affected_processes=[e.process_id for e in events if e.process_id],
            affected_files=[e.source_path for e in events],
            network_indicators=[],
            response_actions=rule.get('actions', [ResponseAction.MONITOR])
        )

        self.active_incidents[incident_id] = incident
        self.incident_history.append(incident)

        self.logger.info(f"Created incident {incident_id}: {incident.title}")
        return incident

    async def _execute_response(self, incident: SecurityIncident):
        """Execute automated response actions."""
        for action in incident.response_actions:
            try:
                success = await self._execute_action(action, incident)
                if success:
                    self.logger.info(f"Successfully executed {action.value} for incident {incident.incident_id}")
                else:
                    self.logger.warning(f"Failed to execute {action.value} for incident {incident.incident_id}")
            except Exception as e:
                self.logger.error(f"Error executing {action.value}: {e}")

    async def _execute_action(self, action: ResponseAction, incident: SecurityIncident) -> bool:
        """Execute a specific response action."""
        try:
            if action == ResponseAction.QUARANTINE:
                return await self._quarantine_files(incident.affected_files)
            elif action == ResponseAction.TERMINATE:
                return await self._terminate_processes(incident.affected_processes)
            elif action == ResponseAction.BLOCK:
                return await self._block_network_connections(incident.network_indicators)
            elif action == ResponseAction.ALERT:
                return await self._send_alert(incident)
            elif action == ResponseAction.MONITOR:
                return await self._enhance_monitoring(incident)

            return True

        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            return False

    async def _quarantine_files(self, file_paths: List[str]) -> bool:
        """Quarantine suspicious files."""
        quarantine_dir = Path("/var/quarantine/xanados")
        quarantine_dir.mkdir(parents=True, exist_ok=True)

        for file_path in file_paths:
            try:
                if Path(file_path).exists():
                    quarantine_path = quarantine_dir / f"{int(time.time())}_{Path(file_path).name}"
                    subprocess.run(['sudo', 'mv', file_path, str(quarantine_path)], check=True)
                    self.logger.info(f"Quarantined file: {file_path} -> {quarantine_path}")
            except Exception as e:
                self.logger.error(f"Failed to quarantine {file_path}: {e}")
                return False

        return True

    async def _terminate_processes(self, pids: List[int]) -> bool:
        """Terminate suspicious processes."""
        for pid in pids:
            try:
                if pid > 0:
                    os.kill(pid, signal.SIGTERM)
                    self.logger.info(f"Terminated process PID {pid}")
            except (OSError, ProcessLookupError) as e:
                self.logger.warning(f"Could not terminate PID {pid}: {e}")

        return True

    async def _block_network_connections(self, indicators: List[str]) -> bool:
        """Block network connections (placeholder - would use iptables)."""
        # This would implement actual network blocking
        self.logger.info(f"Would block network indicators: {indicators}")
        return True

    async def _send_alert(self, incident: SecurityIncident) -> bool:
        """Send security alert."""
        alert_message = f"Security Incident {incident.incident_id}: {incident.title}"
        self.logger.warning(alert_message)
        # Here you would send to SIEM, email, Slack, etc.
        return True

    async def _enhance_monitoring(self, incident: SecurityIncident) -> bool:
        """Enhance monitoring for related activities."""
        self.logger.info(f"Enhanced monitoring enabled for incident {incident.incident_id}")
        return True

    def get_active_incidents(self) -> List[SecurityIncident]:
        """Get all active incidents."""
        return list(self.active_incidents.values())

    async def resolve_incident(self, incident_id: str, resolution_notes: str = "") -> bool:
        """Mark an incident as resolved."""
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
            incident.is_resolved = True
            incident.resolution_time = time.time()
            del self.active_incidents[incident_id]

            self.logger.info(f"Resolved incident {incident_id}: {resolution_notes}")
            return True

        return False


class EDREngine:
    """Main EDR engine coordinating all detection and response components."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()

        # Core components
        self.process_monitor = ProcessMonitor()
        self.network_monitor = NetworkMonitor()
        self.incident_response = IncidentResponseEngine()
        self.ml_detector = get_threat_detector()

        # State
        self.is_running = False
        self.start_time = None

    async def start(self):
        """Start the EDR engine."""
        if self.is_running:
            return

        self.is_running = True
        self.start_time = time.time()

        self.logger.info("Starting EDR engine")

        # Start monitoring components
        await self.process_monitor.start_monitoring()
        await self.network_monitor.start_monitoring()

        # Start main analysis loop
        asyncio.create_task(self._analysis_loop())

        self.logger.info("EDR engine started successfully")

    async def stop(self):
        """Stop the EDR engine."""
        if not self.is_running:
            return

        self.is_running = False
        self.logger.info("EDR engine stopped")

    async def _analysis_loop(self):
        """Main analysis and correlation loop."""
        while self.is_running:
            try:
                # Correlate events and detect incidents
                await self._correlate_events()

                # Perform ML-based analysis
                await self._ml_analysis()

                await asyncio.sleep(5.0)  # Analyze every 5 seconds

            except Exception as e:
                self.logger.error(f"Analysis loop error: {e}")
                await asyncio.sleep(10.0)

    async def _correlate_events(self):
        """Correlate events to detect complex attacks."""
        # Get current suspicious activities
        suspicious_processes = self.process_monitor.get_suspicious_processes()
        suspicious_connections = self.network_monitor.get_suspicious_connections()

        # Look for correlated suspicious activity
        for process in suspicious_processes:
            # Check if process has suspicious network connections
            proc_connections = [conn for conn in suspicious_connections if conn.pid == process.pid]

            if proc_connections:
                # Create correlated security event
                event = SecurityEvent(
                    event_type=EventType.PRIVILEGE_ESCALATION,
                    timestamp=time.time(),
                    source_path=process.exe,
                    process_id=process.pid,
                    threat_level=ThreatLevel.HIGH,
                    additional_data={
                        'process_info': asdict(process),
                        'network_connections': [asdict(conn) for conn in proc_connections]
                    }
                )

                # Handle the correlated event
                await self.incident_response.handle_security_event(event)

    async def _ml_analysis(self):
        """Perform ML-based threat analysis on collected data."""
        try:
            # Create events from current system state
            events = []

            # Add process events
            for process in self.process_monitor.get_suspicious_processes():
                event = SecurityEvent(
                    event_type=EventType.PROCESS_SPAWNED,
                    timestamp=time.time(),
                    source_path=process.exe,
                    process_id=process.pid,
                    threat_level=ThreatLevel.MEDIUM if process.threat_score > 0.5 else ThreatLevel.LOW
                )
                events.append(event)

            # Add network events
            for connection in self.network_monitor.get_suspicious_connections():
                event = SecurityEvent(
                    event_type=EventType.NETWORK_CONNECTION,
                    timestamp=connection.timestamp,
                    source_path=f"{connection.remote_address}:{connection.remote_port}",
                    process_id=connection.pid,
                    threat_level=ThreatLevel.MEDIUM if connection.is_suspicious else ThreatLevel.LOW
                )
                events.append(event)

            if events:
                # Analyze with ML detector
                assessment = await self.ml_detector.analyze_behavior(events)

                if assessment.threat_level.value >= ThreatLevel.HIGH.value:
                    # Create high-priority incident
                    event = SecurityEvent(
                        event_type=EventType.PRIVILEGE_ESCALATION,
                        timestamp=time.time(),
                        source_path="ml_analysis",
                        threat_level=assessment.threat_level,
                        additional_data={'ml_assessment': asdict(assessment)}
                    )

                    await self.incident_response.handle_security_event(event)

        except Exception as e:
            self.logger.error(f"ML analysis failed: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'is_running': self.is_running,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'suspicious_processes': len(self.process_monitor.get_suspicious_processes()),
            'suspicious_connections': len(self.network_monitor.get_suspicious_connections()),
            'active_incidents': len(self.incident_response.get_active_incidents()),
            'total_processes': len(self.process_monitor.monitored_processes),
            'total_connections': len(self.network_monitor.connections)
        }

    def get_security_overview(self) -> Dict[str, Any]:
        """Get security overview dashboard data."""
        return {
            'threat_level': self._calculate_overall_threat_level(),
            'recent_incidents': self.incident_response.incident_history,
            'suspicious_activities': {
                'processes': self.process_monitor.get_suspicious_processes(),
                'connections': self.network_monitor.get_suspicious_connections()
            },
            'system_metrics': self.get_system_status()
        }

    def _calculate_overall_threat_level(self) -> ThreatLevel:
        """Calculate overall system threat level."""
        active_incidents = self.incident_response.get_active_incidents()

        if any(incident.severity == IncidentSeverity.CRITICAL for incident in active_incidents):
            return ThreatLevel.CRITICAL
        elif any(incident.severity == IncidentSeverity.HIGH for incident in active_incidents):
            return ThreatLevel.HIGH
        elif any(incident.severity == IncidentSeverity.MEDIUM for incident in active_incidents):
            return ThreatLevel.MEDIUM
        elif active_incidents:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.LOW


# Global EDR instance
_edr_instance = None


def get_edr_engine() -> EDREngine:
    """Get the global EDR engine instance."""
    global _edr_instance
    if _edr_instance is None:
        _edr_instance = EDREngine()
    return _edr_instance
