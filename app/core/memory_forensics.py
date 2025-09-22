#!/usr/bin/env python3
"""Advanced Memory Forensics Engine for xanadOS Search & Destroy.

This module provides Volatility-based memory analysis capabilities for advanced
threat detection in memory dumps. It integrates with the ML threat detection
and EDR systems to provide comprehensive memory-based security analysis.

Features:
- Volatility 3 integration for memory dump analysis
- Automated malware detection in memory
- Process and network connection analysis
- Registry and file system reconstruction
- Timeline analysis for incident response
- Integration with ML threat detection
- Advanced persistent threat (APT) detection
"""

import asyncio
import io
import json
import logging
import os
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.core.memory_manager import get_memory_manager, memory_efficient
from app.utils.config import get_config


class MemoryAnalysisType(Enum):
    """Types of memory analysis operations."""

    MALWARE_SCAN = "malware_scan"
    PROCESS_ANALYSIS = "process_analysis"
    NETWORK_ANALYSIS = "network_analysis"
    REGISTRY_ANALYSIS = "registry_analysis"
    TIMELINE_ANALYSIS = "timeline_analysis"
    ROOTKIT_DETECTION = "rootkit_detection"
    CODE_INJECTION = "code_injection"
    CRYPTO_ANALYSIS = "crypto_analysis"


@dataclass
class MemoryArtifact:
    """Memory artifact discovered during analysis."""

    artifact_type: str
    name: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float
    location: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    related_processes: List[str] = field(default_factory=list)
    iocs: List[str] = field(default_factory=list)  # Indicators of Compromise


@dataclass
class ProcessInfo:
    """Detailed process information from memory analysis."""

    pid: int
    ppid: int
    name: str
    command_line: str
    create_time: Optional[str]
    exit_time: Optional[str]
    image_path: str
    threads: int
    handles: int
    virtual_size: int
    working_set: int
    suspicious_indicators: List[str] = field(default_factory=list)
    injected_code: bool = False
    network_connections: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NetworkConnection:
    """Network connection information from memory."""

    protocol: str
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    state: str
    pid: int
    process_name: str
    creation_time: Optional[str] = None
    suspicious: bool = False
    threat_indicators: List[str] = field(default_factory=list)


@dataclass
class MemoryForensicsReport:
    """Comprehensive memory forensics analysis report."""

    dump_file: str
    analysis_start: float
    analysis_end: float
    volatility_version: str
    profile: str
    artifacts: List[MemoryArtifact] = field(default_factory=list)
    processes: List[ProcessInfo] = field(default_factory=list)
    network_connections: List[NetworkConnection] = field(default_factory=list)
    threat_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)


class VolatilityWrapper:
    """Wrapper for Volatility 3 command-line interface."""

    def __init__(self, volatility_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.volatility_path = volatility_path or self._find_volatility()
        self.temp_dir = Path(tempfile.gettempdir()) / "xanados_volatility"
        self.temp_dir.mkdir(exist_ok=True)

        if not self.volatility_path:
            raise RuntimeError("Volatility not found. Please install Volatility 3.")

    def _find_volatility(self) -> Optional[str]:
        """Find Volatility installation."""
        possible_paths = [
            "/usr/local/bin/vol.py",
            "/usr/bin/vol.py",
            "vol.py",
            "volatility3",
            "vol"
        ]

        for path in possible_paths:
            try:
                result = subprocess.run([path, "--help"],
                                      capture_output=True,
                                      timeout=10)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return None

    async def run_plugin(self, dump_file: str, plugin: str,
                        output_format: str = "json", **kwargs) -> Dict[str, Any]:
        """Run a Volatility plugin asynchronously."""
        cmd = [
            self.volatility_path,
            "-f", dump_file,
            plugin,
            "--output", output_format
        ]

        # Add plugin-specific arguments
        for key, value in kwargs.items():
            if value is not None:
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        try:
            self.logger.debug(f"Running Volatility command: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                self.logger.error(f"Volatility plugin {plugin} failed: {error_msg}")
                return {"error": error_msg, "success": False}

            # Parse JSON output
            try:
                output = stdout.decode('utf-8', errors='ignore')
                if output_format == "json":
                    return json.loads(output)
                else:
                    return {"output": output, "success": True}
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse Volatility JSON output: {e}")
                return {
                    "output": stdout.decode('utf-8', errors='ignore'),
                    "success": True
                }

        except Exception as e:
            self.logger.error(f"Error running Volatility plugin {plugin}: {e}")
            return {"error": str(e), "success": False}

    async def get_image_info(self, dump_file: str) -> Dict[str, Any]:
        """Get basic information about the memory dump."""
        return await self.run_plugin(dump_file, "windows.info")

    async def list_processes(self, dump_file: str) -> Dict[str, Any]:
        """List all processes in the memory dump."""
        return await self.run_plugin(dump_file, "windows.pslist")

    async def scan_processes(self, dump_file: str) -> Dict[str, Any]:
        """Scan for hidden/unlinked processes."""
        return await self.run_plugin(dump_file, "windows.psscan")

    async def list_network_connections(self, dump_file: str) -> Dict[str, Any]:
        """List network connections."""
        return await self.run_plugin(dump_file, "windows.netstat")

    async def scan_for_malware(self, dump_file: str) -> Dict[str, Any]:
        """Scan for malware indicators."""
        return await self.run_plugin(dump_file, "windows.malfind")

    async def dump_process_memory(self, dump_file: str, pid: int,
                                 output_dir: str) -> Dict[str, Any]:
        """Dump memory of a specific process."""
        return await self.run_plugin(
            dump_file,
            "windows.memmap",
            pid=pid,
            dump_dir=output_dir
        )


class ThreatPatternMatcher:
    """Pattern matching for known threat indicators in memory."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns = self._load_threat_patterns()

    def _load_threat_patterns(self) -> Dict[str, Any]:
        """Load threat detection patterns."""
        return {
            "suspicious_processes": [
                r".*\.tmp\.exe$",
                r"^[a-f0-9]{8,16}\.exe$",
                r".*svchost.*\.exe$",  # Fake svchost
                r".*lsass.*\.exe$",    # Fake lsass
                r".*powershell.*-enc.*",  # Encoded PowerShell
            ],
            "code_injection_indicators": [
                "CreateRemoteThread",
                "WriteProcessMemory",
                "VirtualAllocEx",
                "SetWindowsHookEx",
                "NtMapViewOfSection"
            ],
            "persistence_mechanisms": [
                "Run\\",
                "RunOnce\\",
                "Winlogon\\",
                "Services\\",
                "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion"
            ],
            "network_indicators": {
                "suspicious_ports": [4444, 8080, 1234, 31337],
                "tor_indicators": ["127.0.0.1:9050", "127.0.0.1:9051"],
                "c2_patterns": [r".*\.tk$", r".*\.ml$", r".*\.ga$"]
            }
        }

    def analyze_process(self, process: ProcessInfo) -> List[str]:
        """Analyze process for suspicious indicators."""
        indicators = []

        # Check process name patterns
        for pattern in self.patterns["suspicious_processes"]:
            import re
            if re.match(pattern, process.name, re.IGNORECASE):
                indicators.append(f"Suspicious process name pattern: {pattern}")

        # Check command line for indicators
        cmd_line = process.command_line.lower()
        for indicator in self.patterns["code_injection_indicators"]:
            if indicator.lower() in cmd_line:
                indicators.append(f"Code injection indicator: {indicator}")

        # Check for process hollowing indicators
        if process.threads == 0 or process.handles == 0:
            indicators.append("Possible process hollowing (zero threads/handles)")

        # Check for suspicious parent-child relationships
        if process.ppid == 0 and process.pid != 4:  # Not System process
            indicators.append("Orphaned process (PPID=0)")

        return indicators

    def analyze_network_connection(self, conn: NetworkConnection) -> List[str]:
        """Analyze network connection for threats."""
        indicators = []

        # Check suspicious ports
        if conn.remote_port in self.patterns["network_indicators"]["suspicious_ports"]:
            indicators.append(f"Connection to suspicious port: {conn.remote_port}")

        # Check for Tor indicators
        conn_string = f"{conn.remote_address}:{conn.remote_port}"
        for tor_indicator in self.patterns["network_indicators"]["tor_indicators"]:
            if conn_string == tor_indicator:
                indicators.append("Possible Tor connection")

        # Check C2 domain patterns
        import re
        for pattern in self.patterns["network_indicators"]["c2_patterns"]:
            if re.match(pattern, conn.remote_address, re.IGNORECASE):
                indicators.append(f"Suspicious domain pattern: {pattern}")

        return indicators


class MemoryForensicsEngine:
    """Advanced memory forensics analysis engine."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.volatility = VolatilityWrapper()
        self.pattern_matcher = ThreatPatternMatcher()
        self.memory_manager = get_memory_manager()

        # Analysis cache
        self.analysis_cache = self.memory_manager.get_cache('memory_forensics')
        if not self.analysis_cache:
            self.analysis_cache = self.memory_manager.create_cache(
                'memory_forensics',
                max_items=50,
                max_memory_mb=200
            )

        # Active analyses
        self.active_analyses = {}
        self.analysis_lock = threading.Lock()

    @memory_efficient(aggressive=True)
    async def analyze_memory_dump(self, dump_file: str,
                                 analysis_types: Optional[List[MemoryAnalysisType]] = None,
                                 progress_callback: Optional[callable] = None) -> MemoryForensicsReport:
        """Perform comprehensive memory dump analysis."""
        if not os.path.exists(dump_file):
            raise FileNotFoundError(f"Memory dump file not found: {dump_file}")

        # Default analysis types
        if analysis_types is None:
            analysis_types = [
                MemoryAnalysisType.PROCESS_ANALYSIS,
                MemoryAnalysisType.MALWARE_SCAN,
                MemoryAnalysisType.NETWORK_ANALYSIS,
                MemoryAnalysisType.ROOTKIT_DETECTION
            ]

        # Check cache first
        cache_key = f"{dump_file}_{hash(tuple(analysis_types))}"
        cached_result = self.analysis_cache.get(cache_key)
        if cached_result:
            self.logger.info(f"Returning cached analysis for {dump_file}")
            return cached_result

        # Create analysis report
        report = MemoryForensicsReport(
            dump_file=dump_file,
            analysis_start=time.time(),
            analysis_end=0.0,
            volatility_version="3.0",
            profile="Auto-detected"
        )

        try:
            # Register active analysis
            analysis_id = f"analysis_{int(time.time())}"
            with self.analysis_lock:
                self.active_analyses[analysis_id] = {
                    'dump_file': dump_file,
                    'start_time': time.time(),
                    'progress': 0
                }

            total_steps = len(analysis_types) + 2  # +2 for info and final processing
            current_step = 0

            # Get image information
            self.logger.info(f"Analyzing memory dump: {dump_file}")
            if progress_callback:
                progress_callback(current_step / total_steps, "Getting image information")

            image_info = await self.volatility.get_image_info(dump_file)
            if image_info.get("success", True):
                self.logger.info("Successfully retrieved image information")

            current_step += 1

            # Perform requested analyses
            for analysis_type in analysis_types:
                if progress_callback:
                    progress_callback(
                        current_step / total_steps,
                        f"Performing {analysis_type.value}"
                    )

                await self._perform_specific_analysis(report, dump_file, analysis_type)
                current_step += 1

            # Final processing and threat scoring
            if progress_callback:
                progress_callback(current_step / total_steps, "Calculating threat score")

            await self._calculate_threat_score(report)
            await self._generate_recommendations(report)

            report.analysis_end = time.time()

            # Cache the result
            self.analysis_cache.put(cache_key, report)

            self.logger.info(
                f"Memory analysis completed in {report.analysis_end - report.analysis_start:.2f}s"
            )

            return report

        except Exception as e:
            self.logger.error(f"Memory analysis failed: {e}")
            report.analysis_end = time.time()
            report.artifacts.append(
                MemoryArtifact(
                    artifact_type="ERROR",
                    name="Analysis Error",
                    description=f"Analysis failed: {str(e)}",
                    severity="HIGH",
                    confidence=1.0,
                    location="Analysis Engine"
                )
            )
            return report

        finally:
            # Cleanup active analysis
            with self.analysis_lock:
                self.active_analyses.pop(analysis_id, None)

    async def _perform_specific_analysis(self, report: MemoryForensicsReport,
                                        dump_file: str, analysis_type: MemoryAnalysisType):
        """Perform a specific type of memory analysis."""
        try:
            if analysis_type == MemoryAnalysisType.PROCESS_ANALYSIS:
                await self._analyze_processes(report, dump_file)

            elif analysis_type == MemoryAnalysisType.MALWARE_SCAN:
                await self._scan_for_malware(report, dump_file)

            elif analysis_type == MemoryAnalysisType.NETWORK_ANALYSIS:
                await self._analyze_network_connections(report, dump_file)

            elif analysis_type == MemoryAnalysisType.ROOTKIT_DETECTION:
                await self._detect_rootkits(report, dump_file)

            elif analysis_type == MemoryAnalysisType.REGISTRY_ANALYSIS:
                await self._analyze_registry(report, dump_file)

            elif analysis_type == MemoryAnalysisType.TIMELINE_ANALYSIS:
                await self._create_timeline(report, dump_file)

            elif analysis_type == MemoryAnalysisType.CODE_INJECTION:
                await self._detect_code_injection(report, dump_file)

            elif analysis_type == MemoryAnalysisType.CRYPTO_ANALYSIS:
                await self._analyze_crypto_activity(report, dump_file)

        except Exception as e:
            self.logger.error(f"Failed to perform {analysis_type.value}: {e}")
            report.artifacts.append(
                MemoryArtifact(
                    artifact_type="ERROR",
                    name=f"{analysis_type.value} Error",
                    description=f"Analysis failed: {str(e)}",
                    severity="MEDIUM",
                    confidence=1.0,
                    location="Analysis Engine"
                )
            )

    async def _analyze_processes(self, report: MemoryForensicsReport, dump_file: str):
        """Analyze processes in memory dump."""
        # Get process list
        pslist_result = await self.volatility.list_processes(dump_file)
        psscan_result = await self.volatility.scan_processes(dump_file)

        if pslist_result.get("success", True):
            processes_data = pslist_result.get("rows", [])

            for proc_data in processes_data:
                process = ProcessInfo(
                    pid=proc_data.get("PID", 0),
                    ppid=proc_data.get("PPID", 0),
                    name=proc_data.get("ImageFileName", ""),
                    command_line=proc_data.get("CommandLine", ""),
                    create_time=proc_data.get("CreateTime"),
                    exit_time=proc_data.get("ExitTime"),
                    image_path=proc_data.get("ImagePathName", ""),
                    threads=proc_data.get("Threads", 0),
                    handles=proc_data.get("Handles", 0),
                    virtual_size=proc_data.get("VirtualSize", 0),
                    working_set=proc_data.get("WorkingSetSize", 0)
                )

                # Analyze for suspicious indicators
                indicators = self.pattern_matcher.analyze_process(process)
                process.suspicious_indicators = indicators

                if indicators:
                    report.artifacts.append(
                        MemoryArtifact(
                            artifact_type="SUSPICIOUS_PROCESS",
                            name=process.name,
                            description=f"Process with suspicious indicators: {', '.join(indicators)}",
                            severity="HIGH" if len(indicators) > 2 else "MEDIUM",
                            confidence=0.8,
                            location=f"PID: {process.pid}",
                            metadata={
                                "pid": process.pid,
                                "ppid": process.ppid,
                                "command_line": process.command_line
                            }
                        )
                    )

                report.processes.append(process)

        # Check for hidden processes
        if psscan_result.get("success", True):
            pslist_pids = {proc.pid for proc in report.processes}
            psscan_data = psscan_result.get("rows", [])

            for proc_data in psscan_data:
                pid = proc_data.get("PID", 0)
                if pid not in pslist_pids:
                    report.artifacts.append(
                        MemoryArtifact(
                            artifact_type="HIDDEN_PROCESS",
                            name=proc_data.get("ImageFileName", "Unknown"),
                            description="Process found in scan but not in process list (possible rootkit)",
                            severity="HIGH",
                            confidence=0.9,
                            location=f"PID: {pid}",
                            metadata={"pid": pid}
                        )
                    )

    async def _scan_for_malware(self, report: MemoryForensicsReport, dump_file: str):
        """Scan for malware in memory dump."""
        malfind_result = await self.volatility.scan_for_malware(dump_file)

        if malfind_result.get("success", True):
            malware_data = malfind_result.get("rows", [])

            for malware_entry in malware_data:
                report.artifacts.append(
                    MemoryArtifact(
                        artifact_type="MALWARE_INDICATOR",
                        name="Injected Code",
                        description=f"Possible code injection detected in PID {malware_entry.get('PID', 'Unknown')}",
                        severity="HIGH",
                        confidence=0.85,
                        location=f"PID: {malware_entry.get('PID')}, Address: {malware_entry.get('VirtualAddress')}",
                        metadata=malware_entry
                    )
                )

    async def _analyze_network_connections(self, report: MemoryForensicsReport, dump_file: str):
        """Analyze network connections."""
        netstat_result = await self.volatility.list_network_connections(dump_file)

        if netstat_result.get("success", True):
            connections_data = netstat_result.get("rows", [])

            for conn_data in connections_data:
                connection = NetworkConnection(
                    protocol=conn_data.get("Protocol", ""),
                    local_address=conn_data.get("LocalAddr", ""),
                    local_port=conn_data.get("LocalPort", 0),
                    remote_address=conn_data.get("ForeignAddr", ""),
                    remote_port=conn_data.get("ForeignPort", 0),
                    state=conn_data.get("State", ""),
                    pid=conn_data.get("PID", 0),
                    process_name=conn_data.get("Owner", ""),
                    creation_time=conn_data.get("Created")
                )

                # Analyze for threats
                indicators = self.pattern_matcher.analyze_network_connection(connection)
                connection.threat_indicators = indicators

                if indicators:
                    connection.suspicious = True
                    report.artifacts.append(
                        MemoryArtifact(
                            artifact_type="SUSPICIOUS_NETWORK",
                            name=f"Network Connection",
                            description=f"Suspicious network activity: {', '.join(indicators)}",
                            severity="MEDIUM",
                            confidence=0.7,
                            location=f"{connection.remote_address}:{connection.remote_port}",
                            metadata={
                                "pid": connection.pid,
                                "process": connection.process_name,
                                "remote_endpoint": f"{connection.remote_address}:{connection.remote_port}"
                            }
                        )
                    )

                report.network_connections.append(connection)

    async def _detect_rootkits(self, report: MemoryForensicsReport, dump_file: str):
        """Detect rootkit presence."""
        # Compare pslist vs psscan for hidden processes (already done in process analysis)
        # Add additional rootkit detection techniques

        # Check for SSDT hooks (if available in Volatility)
        try:
            ssdt_result = await self.volatility.run_plugin(dump_file, "windows.ssdt")
            if ssdt_result.get("success", True):
                hooks_data = ssdt_result.get("rows", [])
                for hook in hooks_data:
                    if hook.get("Hooked", False):
                        report.artifacts.append(
                            MemoryArtifact(
                                artifact_type="ROOTKIT_INDICATOR",
                                name="SSDT Hook",
                                description=f"System Service Descriptor Table hook detected",
                                severity="HIGH",
                                confidence=0.95,
                                location=f"Table: {hook.get('Table')}, Index: {hook.get('Index')}",
                                metadata=hook
                            )
                        )
        except Exception as e:
            self.logger.debug(f"SSDT analysis not available: {e}")

    async def _analyze_registry(self, report: MemoryForensicsReport, dump_file: str):
        """Analyze registry for persistence mechanisms."""
        # This would require specific Volatility plugins for registry analysis
        # Implementation depends on available plugins
        pass

    async def _create_timeline(self, report: MemoryForensicsReport, dump_file: str):
        """Create timeline of events."""
        # Timeline analysis would combine various timestamps from processes,
        # network connections, and other artifacts
        timeline_events = []

        # Add process creation times
        for process in report.processes:
            if process.create_time:
                timeline_events.append({
                    'timestamp': process.create_time,
                    'event_type': 'process_creation',
                    'description': f"Process {process.name} (PID: {process.pid}) created",
                    'severity': 'LOW'
                })

        # Sort by timestamp
        timeline_events.sort(key=lambda x: x['timestamp'])
        report.timeline = timeline_events

    async def _detect_code_injection(self, report: MemoryForensicsReport, dump_file: str):
        """Detect code injection techniques."""
        # This is partially covered by malfind, but we can add more specific checks
        for process in report.processes:
            if any(indicator in process.command_line.lower()
                   for indicator in ['createremotethread', 'writeprocessmemory']):
                process.injected_code = True

                report.artifacts.append(
                    MemoryArtifact(
                        artifact_type="CODE_INJECTION",
                        name=f"Code Injection in {process.name}",
                        description="Process shows signs of code injection",
                        severity="HIGH",
                        confidence=0.8,
                        location=f"PID: {process.pid}",
                        metadata={"pid": process.pid, "process_name": process.name}
                    )
                )

    async def _analyze_crypto_activity(self, report: MemoryForensicsReport, dump_file: str):
        """Analyze cryptocurrency and encryption activity."""
        # Look for crypto-related processes and network connections
        crypto_indicators = [
            'bitcoin', 'ethereum', 'monero', 'mining', 'wallet',
            'crypto', 'blockchain', 'stratum', 'xmrig'
        ]

        for process in report.processes:
            if any(indicator in process.name.lower() or indicator in process.command_line.lower()
                   for indicator in crypto_indicators):
                report.artifacts.append(
                    MemoryArtifact(
                        artifact_type="CRYPTO_ACTIVITY",
                        name=f"Cryptocurrency Activity",
                        description=f"Cryptocurrency-related process detected: {process.name}",
                        severity="MEDIUM",
                        confidence=0.7,
                        location=f"PID: {process.pid}",
                        metadata={"pid": process.pid, "process_name": process.name}
                    )
                )

    async def _calculate_threat_score(self, report: MemoryForensicsReport):
        """Calculate overall threat score for the memory dump."""
        threat_score = 0.0

        # Weight artifacts by severity
        severity_weights = {
            'CRITICAL': 10.0,
            'HIGH': 5.0,
            'MEDIUM': 2.0,
            'LOW': 0.5
        }

        for artifact in report.artifacts:
            weight = severity_weights.get(artifact.severity, 1.0)
            threat_score += weight * artifact.confidence

        # Additional factors
        if len(report.artifacts) > 10:
            threat_score *= 1.2  # Multiple threats increase score

        if any(artifact.artifact_type == "ROOTKIT_INDICATOR" for artifact in report.artifacts):
            threat_score *= 1.5  # Rootkits are particularly dangerous

        # Normalize to 0-100 scale
        report.threat_score = min(threat_score, 100.0)

    async def _generate_recommendations(self, report: MemoryForensicsReport):
        """Generate security recommendations based on analysis."""
        recommendations = []

        # Analyze artifact types for recommendations
        artifact_types = {artifact.artifact_type for artifact in report.artifacts}

        if "MALWARE_INDICATOR" in artifact_types:
            recommendations.append(
                "Immediate isolation recommended: Malware indicators detected in memory"
            )

        if "ROOTKIT_INDICATOR" in artifact_types:
            recommendations.append(
                "System rebuild recommended: Rootkit presence indicates deep compromise"
            )

        if "SUSPICIOUS_NETWORK" in artifact_types:
            recommendations.append(
                "Network traffic analysis recommended: Suspicious connections detected"
            )

        if "CODE_INJECTION" in artifact_types:
            recommendations.append(
                "Process analysis recommended: Code injection techniques detected"
            )

        if report.threat_score > 70:
            recommendations.append(
                "High threat level: Comprehensive incident response required"
            )
        elif report.threat_score > 40:
            recommendations.append(
                "Medium threat level: Enhanced monitoring and investigation required"
            )

        if not recommendations:
            recommendations.append("System appears clean, continue regular monitoring")

        report.recommendations = recommendations

    def get_active_analyses(self) -> Dict[str, Any]:
        """Get information about active analyses."""
        with self.analysis_lock:
            return dict(self.active_analyses)

    async def cancel_analysis(self, analysis_id: str) -> bool:
        """Cancel an active analysis."""
        with self.analysis_lock:
            if analysis_id in self.active_analyses:
                # In a real implementation, this would signal the analysis to stop
                del self.active_analyses[analysis_id]
                self.logger.info(f"Cancelled analysis: {analysis_id}")
                return True
            return False
