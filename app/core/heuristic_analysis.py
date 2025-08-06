#!/usr/bin/env python3
"""
Heuristic Analysis Engine for S&D
Provides behavioral analysis, pattern detection, and machine learning-based threat detection.
"""
import os
import hashlib
import math
import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import json
import re
import struct
from collections import Counter, defaultdict
import sqlite3

class HeuristicType(Enum):
    """Types of heuristic analysis."""
    ENTROPY_ANALYSIS = "entropy_analysis"
    PATTERN_MATCHING = "pattern_matching"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    STRUCTURAL_ANALYSIS = "structural_analysis"
    METADATA_ANALYSIS = "metadata_analysis"
    NETWORK_BEHAVIOR = "network_behavior"

class ThreatIndicator(Enum):
    """Threat indicator types."""
    PACKED_EXECUTABLE = "packed_executable"
    SUSPICIOUS_STRINGS = "suspicious_strings"
    RAPID_FILE_CREATION = "rapid_file_creation"
    REGISTRY_MODIFICATION = "registry_modification"
    NETWORK_COMMUNICATION = "network_communication"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    FILE_ENCRYPTION = "file_encryption"
    ANTI_ANALYSIS = "anti_analysis"
    CODE_INJECTION = "code_injection"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"

class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class HeuristicResult:
    """Result of heuristic analysis."""
    file_path: str
    heuristic_type: HeuristicType
    threat_indicators: List[ThreatIndicator]
    risk_level: RiskLevel
    confidence_score: float  # 0.0 to 1.0
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    scan_time: float = 0.0

@dataclass
class BehavioralPattern:
    """Behavioral pattern for analysis."""
    pattern_id: str
    name: str
    description: str
    indicators: List[str]
    weight: float
    risk_level: RiskLevel
    enabled: bool = True

@dataclass
class FileSignature:
    """File signature for pattern matching."""
    signature_id: str
    name: str
    pattern: bytes
    offset: int
    threat_type: str
    confidence: float

class HeuristicAnalysisEngine:
    """
    Advanced heuristic analysis engine for detecting unknown threats
    using behavioral analysis, entropy calculation, and pattern matching.
    """
    
    def __init__(self, database_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Database for storing patterns and results
        self.db_path = database_path or "heuristic_analysis.db"
        self._init_database()
        
        # Analysis components
        self.behavioral_patterns: Dict[str, BehavioralPattern] = {}
        self.file_signatures: Dict[str, FileSignature] = {}
        self.suspicious_strings: Set[str] = set()
        
        # File tracking for behavioral analysis
        self.file_activities: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.process_activities: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        
        # Analysis cache
        self.analysis_cache: Dict[str, HeuristicResult] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        
        # Performance settings
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.cache_ttl_hours = 24
        self.analysis_timeout = 30.0  # seconds
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Load default patterns and signatures
        self._load_default_patterns()
        self._load_default_signatures()
        self._load_suspicious_strings()
        
        self.logger.info("Heuristic analysis engine initialized")

    def _init_database(self):
        """Initialize analysis database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    heuristic_type TEXT,
                    threat_indicators TEXT,
                    risk_level TEXT,
                    confidence_score REAL,
                    description TEXT,
                    details TEXT,
                    scan_time REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Behavioral patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS behavioral_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    indicators TEXT,
                    weight REAL,
                    risk_level TEXT,
                    enabled BOOLEAN
                )
            """)
            
            # File signatures table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_signatures (
                    signature_id TEXT PRIMARY KEY,
                    name TEXT,
                    pattern BLOB,
                    offset INTEGER,
                    threat_type TEXT,
                    confidence REAL
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error("Failed to initialize database: %s", e)

    def _load_default_patterns(self):
        """Load default behavioral patterns."""
        default_patterns = [
            BehavioralPattern(
                pattern_id="rapid_file_creation",
                name="Rapid File Creation",
                description="Detects rapid creation of many files (potential ransomware)",
                indicators=["file_create", "high_frequency"],
                weight=0.8,
                risk_level=RiskLevel.HIGH
            ),
            BehavioralPattern(
                pattern_id="file_encryption_pattern",
                name="File Encryption Pattern",
                description="Detects patterns consistent with file encryption malware",
                indicators=["file_modify", "extension_change", "size_increase"],
                weight=0.9,
                risk_level=RiskLevel.CRITICAL
            ),
            BehavioralPattern(
                pattern_id="suspicious_network_activity",
                name="Suspicious Network Activity",
                description="Detects suspicious network communication patterns",
                indicators=["network_connect", "unknown_domain", "data_exfiltration"],
                weight=0.7,
                risk_level=RiskLevel.MEDIUM
            ),
            BehavioralPattern(
                pattern_id="privilege_escalation",
                name="Privilege Escalation",
                description="Detects attempts to escalate privileges",
                indicators=["process_create", "elevated_privileges", "system_access"],
                weight=0.85,
                risk_level=RiskLevel.HIGH
            ),
            BehavioralPattern(
                pattern_id="anti_analysis_behavior",
                name="Anti-Analysis Behavior",
                description="Detects evasion and anti-analysis techniques",
                indicators=["debugger_detection", "vm_detection", "time_delay"],
                weight=0.75,
                risk_level=RiskLevel.MEDIUM
            )
        ]
        
        for pattern in default_patterns:
            self.behavioral_patterns[pattern.pattern_id] = pattern

    def _load_default_signatures(self):
        """Load default file signatures."""
        default_signatures = [
            FileSignature(
                signature_id="pe_packer_upx",
                name="UPX Packed Executable",
                pattern=b"UPX!",
                offset=0,
                threat_type="packed_executable",
                confidence=0.8
            ),
            FileSignature(
                signature_id="pe_overlay_suspicious",
                name="Suspicious PE Overlay",
                pattern=b"\x4D\x5A",  # MZ header in overlay
                offset=-1,  # Variable offset
                threat_type="suspicious_overlay",
                confidence=0.6
            ),
            FileSignature(
                signature_id="elf_suspicious",
                name="Suspicious ELF Binary",
                pattern=b"\x7FELF",
                offset=0,
                threat_type="suspicious_elf",
                confidence=0.5
            )
        ]
        
        for signature in default_signatures:
            self.file_signatures[signature.signature_id] = signature

    def _load_suspicious_strings(self):
        """Load suspicious string patterns."""
        suspicious_patterns = {
            # Malware-related strings
            "virus", "malware", "trojan", "backdoor", "keylogger", "rootkit",
            "botnet", "ransomware", "cryptolocker", "wannacry",
            
            # Suspicious API calls
            "CreateRemoteThread", "WriteProcessMemory", "VirtualAllocEx",
            "SetWindowsHookEx", "GetProcAddress", "LoadLibrary",
            
            # Network-related
            "connect", "send", "recv", "socket", "bind", "listen",
            "HttpSendRequest", "InternetOpen", "URLDownloadToFile",
            
            # File operations
            "CreateFile", "WriteFile", "DeleteFile", "MoveFile",
            "FindFirstFile", "CopyFile",
            
            # Registry operations
            "RegOpenKey", "RegSetValue", "RegDeleteKey", "RegCreateKey",
            
            # Encryption/Obfuscation
            "CryptEncrypt", "CryptDecrypt", "encode", "decode",
            "base64", "xor", "encrypt", "decrypt"
        }
        
        self.suspicious_strings.update(suspicious_patterns)

    async def analyze_file(self, file_path: str) -> List[HeuristicResult]:
        """
        Perform comprehensive heuristic analysis on a file.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            List of heuristic analysis results
        """
        try:
            start_time = time.time()
            results = []
            
            # Check cache first
            file_hash = await self._calculate_file_hash(file_path)
            cached_result = self._get_cached_result(file_hash)
            if cached_result:
                return [cached_result]
            
            # Check file size limit
            file_size = Path(file_path).stat().st_size
            if file_size > self.max_file_size:
                self.logger.debug("File too large for heuristic analysis: %s", file_path)
                return []
            
            # Perform different types of analysis
            analysis_tasks = [
                self._entropy_analysis(file_path),
                self._pattern_analysis(file_path),
                self._structural_analysis(file_path),
                self._metadata_analysis(file_path),
                self._string_analysis(file_path)
            ]
            
            # Run analyses with timeout
            try:
                analysis_results = await asyncio.wait_for(
                    asyncio.gather(*analysis_tasks, return_exceptions=True),
                    timeout=self.analysis_timeout
                )
                
                # Process results
                for result in analysis_results:
                    if isinstance(result, HeuristicResult):
                        result.scan_time = time.time() - start_time
                        results.append(result)
                        
                        # Cache significant results
                        if result.risk_level.value >= RiskLevel.MEDIUM.value:
                            self._cache_result(file_hash, result)
                
            except asyncio.TimeoutError:
                self.logger.warning("Heuristic analysis timeout for %s", file_path)
            
            # Store results in database
            for result in results:
                self._store_analysis_result(result, file_hash)
            
            return results
            
        except Exception as e:
            self.logger.error("Error in heuristic analysis of %s: %s", file_path, e)
            return []

    async def _entropy_analysis(self, file_path: str) -> Optional[HeuristicResult]:
        """Analyze file entropy to detect packed/encrypted content."""
        try:
            file_path_obj = Path(file_path)
            
            # Calculate entropy for different sections of the file
            with file_path_obj.open('rb') as f:
                # Read first 64KB for analysis
                data = f.read(65536)
                
                if not data:
                    return None
                
                # Calculate overall entropy
                overall_entropy = self._calculate_entropy(data)
                
                # Calculate entropy for sections
                section_size = len(data) // 4 if len(data) >= 4 else len(data)
                section_entropies = []
                
                for i in range(0, len(data), section_size):
                    section_data = data[i:i + section_size]
                    if section_data:
                        section_entropy = self._calculate_entropy(section_data)
                        section_entropies.append(section_entropy)
                
                # Analyze entropy patterns
                threat_indicators = []
                risk_level = RiskLevel.LOW
                confidence = 0.0
                
                # High overall entropy (>7.5) suggests packing/encryption
                if overall_entropy > 7.5:
                    threat_indicators.append(ThreatIndicator.PACKED_EXECUTABLE)
                    risk_level = RiskLevel.MEDIUM
                    confidence = min((overall_entropy - 7.0) / 1.0, 1.0)
                
                # Very high entropy (>7.8) is highly suspicious
                if overall_entropy > 7.8:
                    risk_level = RiskLevel.HIGH
                    confidence = min((overall_entropy - 7.5) / 0.5, 1.0)
                
                # Check for entropy variance (encrypted sections)
                if section_entropies:
                    entropy_variance = self._calculate_variance(section_entropies)
                    if entropy_variance > 1.0:  # High variance
                        threat_indicators.append(ThreatIndicator.ANTI_ANALYSIS)
                        if risk_level == RiskLevel.LOW:
                            risk_level = RiskLevel.MEDIUM
                        confidence = max(confidence, 0.6)
                
                if threat_indicators:
                    return HeuristicResult(
                        file_path=file_path,
                        heuristic_type=HeuristicType.ENTROPY_ANALYSIS,
                        threat_indicators=threat_indicators,
                        risk_level=risk_level,
                        confidence_score=confidence,
                        description=f"High entropy content detected (entropy: {overall_entropy:.2f})",
                        details={
                            "overall_entropy": overall_entropy,
                            "section_entropies": section_entropies,
                            "entropy_variance": entropy_variance if section_entropies else 0.0
                        }
                    )
                
                return None
                
        except Exception as e:
            self.logger.error("Error in entropy analysis: %s", e)
            return None

    async def _pattern_analysis(self, file_path: str) -> Optional[HeuristicResult]:
        """Analyze file for known malicious patterns."""
        try:
            file_path_obj = Path(file_path)
            threat_indicators = []
            confidence_scores = []
            details = {}
            
            with file_path_obj.open('rb') as f:
                # Read file in chunks for pattern matching
                chunk_size = 1024 * 1024  # 1MB chunks
                data_chunks = []
                
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    data_chunks.append(chunk)
                    
                    # Limit total data for analysis
                    if len(data_chunks) * chunk_size > 10 * 1024 * 1024:  # 10MB limit
                        break
                
                # Combine chunks for analysis
                file_data = b''.join(data_chunks)
                
                # Check file signatures
                for sig_id, signature in self.file_signatures.items():
                    if self._check_signature_match(file_data, signature):
                        if signature.threat_type == "packed_executable":
                            threat_indicators.append(ThreatIndicator.PACKED_EXECUTABLE)
                        elif signature.threat_type == "suspicious_overlay":
                            threat_indicators.append(ThreatIndicator.ANTI_ANALYSIS)
                        
                        confidence_scores.append(signature.confidence)
                        details[f"signature_{sig_id}"] = signature.name
                
                # Check for suspicious byte patterns
                suspicious_patterns = self._detect_suspicious_patterns(file_data)
                if suspicious_patterns:
                    threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                    confidence_scores.append(0.7)
                    details["suspicious_patterns"] = suspicious_patterns
                
                if threat_indicators:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    risk_level = self._calculate_risk_level(threat_indicators, avg_confidence)
                    
                    return HeuristicResult(
                        file_path=file_path,
                        heuristic_type=HeuristicType.PATTERN_MATCHING,
                        threat_indicators=threat_indicators,
                        risk_level=risk_level,
                        confidence_score=avg_confidence,
                        description="Suspicious patterns detected in file",
                        details=details
                    )
                
                return None
                
        except Exception as e:
            self.logger.error("Error in pattern analysis: %s", e)
            return None

    async def _structural_analysis(self, file_path: str) -> Optional[HeuristicResult]:
        """Analyze file structure for anomalies."""
        try:
            file_path_obj = Path(file_path)
            threat_indicators = []
            details = {}
            confidence = 0.0
            
            # Check file extension vs content type
            extension = file_path_obj.suffix.lower()
            
            with file_path_obj.open('rb') as f:
                header = f.read(512)  # Read first 512 bytes
                
                # Check for PE file structure
                if header.startswith(b'MZ'):
                    details["file_type"] = "PE"
                    
                    # Check for PE anomalies
                    pe_anomalies = self._check_pe_anomalies(header, f)
                    if pe_anomalies:
                        threat_indicators.append(ThreatIndicator.ANTI_ANALYSIS)
                        details["pe_anomalies"] = pe_anomalies
                        confidence = 0.6
                
                # Check for ELF file structure
                elif header.startswith(b'\x7FELF'):
                    details["file_type"] = "ELF"
                    
                    # Check for ELF anomalies
                    elf_anomalies = self._check_elf_anomalies(header)
                    if elf_anomalies:
                        threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                        details["elf_anomalies"] = elf_anomalies
                        confidence = 0.5
                
                # Check for script files
                elif any(header.startswith(script) for script in [b'#!/', b'<script', b'<?php']):
                    details["file_type"] = "script"
                    
                    # Check for suspicious script content
                    script_threats = self._check_script_threats(header)
                    if script_threats:
                        threat_indicators.append(ThreatIndicator.CODE_INJECTION)
                        details["script_threats"] = script_threats
                        confidence = 0.7
                
                # Extension mismatch detection
                if extension and not self._extension_matches_content(extension, header):
                    threat_indicators.append(ThreatIndicator.ANTI_ANALYSIS)
                    details["extension_mismatch"] = True
                    confidence = max(confidence, 0.4)
                
                if threat_indicators:
                    risk_level = self._calculate_risk_level(threat_indicators, confidence)
                    
                    return HeuristicResult(
                        file_path=file_path,
                        heuristic_type=HeuristicType.STRUCTURAL_ANALYSIS,
                        threat_indicators=threat_indicators,
                        risk_level=risk_level,
                        confidence_score=confidence,
                        description="Structural anomalies detected",
                        details=details
                    )
                
                return None
                
        except Exception as e:
            self.logger.error("Error in structural analysis: %s", e)
            return None

    async def _metadata_analysis(self, file_path: str) -> Optional[HeuristicResult]:
        """Analyze file metadata for suspicious characteristics."""
        try:
            file_path_obj = Path(file_path)
            stat = file_path_obj.stat()
            threat_indicators = []
            details = {}
            confidence = 0.0
            
            # Check file timestamps
            current_time = time.time()
            creation_time = stat.st_ctime
            modification_time = stat.st_mtime
            
            # Future timestamps are suspicious
            if creation_time > current_time + 86400:  # More than 1 day in future
                threat_indicators.append(ThreatIndicator.ANTI_ANALYSIS)
                details["future_timestamp"] = True
                confidence = 0.3
            
            # Very old files with recent activity might be suspicious
            if (current_time - creation_time > 365 * 24 * 3600 and  # Older than 1 year
                current_time - modification_time < 3600):  # Modified in last hour
                threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                details["timestamp_anomaly"] = True
                confidence = max(confidence, 0.4)
            
            # Check file size anomalies
            file_size = stat.st_size
            
            # Extremely small executables
            if (file_path_obj.suffix.lower() in ['.exe', '.dll'] and 
                file_size < 1024):  # Less than 1KB
                threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                details["tiny_executable"] = True
                confidence = max(confidence, 0.5)
            
            # Check file name patterns
            filename = file_path_obj.name.lower()
            
            # Suspicious filename patterns
            suspicious_name_patterns = [
                r'temp\d+\.exe', r'tmp\d+\.exe', r'[a-f0-9]{8,}\.exe',
                r'svchost\d*\.exe', r'winlogon\d*\.exe', r'explorer\d*\.exe'
            ]
            
            for pattern in suspicious_name_patterns:
                if re.match(pattern, filename):
                    threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                    details["suspicious_filename"] = pattern
                    confidence = max(confidence, 0.6)
                    break
            
            # Hidden files in suspicious locations
            if (filename.startswith('.') and 
                any(path_part in str(file_path_obj.parent).lower() 
                    for path_part in ['temp', 'tmp', 'downloads', 'desktop'])):
                threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                details["hidden_file_suspicious_location"] = True
                confidence = max(confidence, 0.3)
            
            if threat_indicators:
                risk_level = self._calculate_risk_level(threat_indicators, confidence)
                
                return HeuristicResult(
                    file_path=file_path,
                    heuristic_type=HeuristicType.METADATA_ANALYSIS,
                    threat_indicators=threat_indicators,
                    risk_level=risk_level,
                    confidence_score=confidence,
                    description="Suspicious metadata characteristics",
                    details=details
                )
            
            return None
            
        except Exception as e:
            self.logger.error("Error in metadata analysis: %s", e)
            return None

    async def _string_analysis(self, file_path: str) -> Optional[HeuristicResult]:
        """Analyze strings in file for suspicious content."""
        try:
            threat_indicators = []
            details = {}
            suspicious_strings_found = []
            confidence = 0.0
            
            with open(file_path, 'rb') as f:
                # Read file in chunks
                data = f.read(1024 * 1024)  # 1MB limit for string analysis
                
                if not data:
                    return None
                
                # Extract ASCII strings
                strings = self._extract_strings(data)
                
                # Check for suspicious strings
                for string in strings:
                    string_lower = string.lower()
                    
                    # Check against suspicious string database
                    for suspicious_string in self.suspicious_strings:
                        if suspicious_string in string_lower:
                            suspicious_strings_found.append(string)
                            break
                
                # Analyze string patterns
                if suspicious_strings_found:
                    # Count different categories
                    api_calls = sum(1 for s in suspicious_strings_found 
                                  if any(api in s.lower() for api in 
                                        ['create', 'write', 'read', 'delete', 'reg']))
                    
                    network_strings = sum(1 for s in suspicious_strings_found 
                                        if any(net in s.lower() for net in 
                                              ['http', 'connect', 'socket', 'send']))
                    
                    crypto_strings = sum(1 for s in suspicious_strings_found 
                                       if any(crypto in s.lower() for crypto in 
                                             ['encrypt', 'decrypt', 'crypt', 'hash']))
                    
                    # Calculate threat indicators based on string categories
                    if api_calls > 5:
                        threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                        confidence = max(confidence, 0.4)
                    
                    if network_strings > 3:
                        threat_indicators.append(ThreatIndicator.NETWORK_COMMUNICATION)
                        confidence = max(confidence, 0.5)
                    
                    if crypto_strings > 2:
                        threat_indicators.append(ThreatIndicator.FILE_ENCRYPTION)
                        confidence = max(confidence, 0.6)
                    
                    # High concentration of suspicious strings
                    if len(suspicious_strings_found) > 10:
                        threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
                        confidence = max(confidence, 0.7)
                    
                    details = {
                        "suspicious_strings_count": len(suspicious_strings_found),
                        "api_calls": api_calls,
                        "network_strings": network_strings,
                        "crypto_strings": crypto_strings,
                        "sample_strings": suspicious_strings_found[:10]  # First 10 for review
                    }
                
                if threat_indicators:
                    risk_level = self._calculate_risk_level(threat_indicators, confidence)
                    
                    return HeuristicResult(
                        file_path=file_path,
                        heuristic_type=HeuristicType.METADATA_ANALYSIS,
                        threat_indicators=threat_indicators,
                        risk_level=risk_level,
                        confidence_score=confidence,
                        description=f"Suspicious strings detected ({len(suspicious_strings_found)} found)",
                        details=details
                    )
                
                return None
                
        except Exception as e:
            self.logger.error("Error in string analysis: %s", e)
            return None

    def analyze_behavioral_pattern(self, activities: List[Dict[str, Any]]) -> List[HeuristicResult]:
        """Analyze behavioral patterns from system activities."""
        try:
            results = []
            
            # Group activities by time windows
            time_windows = self._group_activities_by_time(activities)
            
            for window_start, window_activities in time_windows.items():
                # Check each behavioral pattern
                for pattern_id, pattern in self.behavioral_patterns.items():
                    if not pattern.enabled:
                        continue
                    
                    match_score = self._evaluate_behavioral_pattern(pattern, window_activities)
                    
                    if match_score > 0.5:  # Threshold for pattern match
                        threat_indicators = self._pattern_to_threat_indicators(pattern)
                        confidence = match_score * pattern.weight
                        
                        result = HeuristicResult(
                            file_path="<behavioral_analysis>",
                            heuristic_type=HeuristicType.BEHAVIORAL_ANALYSIS,
                            threat_indicators=threat_indicators,
                            risk_level=pattern.risk_level,
                            confidence_score=confidence,
                            description=f"Behavioral pattern detected: {pattern.name}",
                            details={
                                "pattern_id": pattern_id,
                                "match_score": match_score,
                                "activity_count": len(window_activities),
                                "time_window": window_start.isoformat()
                            }
                        )
                        
                        results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error("Error in behavioral pattern analysis: %s", e)
            return []

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0.0
        
        # Count byte frequencies
        byte_counts = Counter(data)
        data_len = len(data)
        
        # Calculate entropy
        entropy = 0.0
        for count in byte_counts.values():
            probability = count / data_len
            entropy -= probability * math.log2(probability)
        
        return entropy

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def _check_signature_match(self, data: bytes, signature: FileSignature) -> bool:
        """Check if data matches a file signature."""
        try:
            if signature.offset == -1:  # Variable offset
                return signature.pattern in data
            elif signature.offset + len(signature.pattern) <= len(data):
                return data[signature.offset:signature.offset + len(signature.pattern)] == signature.pattern
            return False
        except Exception:
            return False

    def _detect_suspicious_patterns(self, data: bytes) -> List[str]:
        """Detect suspicious byte patterns in data."""
        patterns = []
        
        # Check for repeated patterns (potential obfuscation)
        if len(data) > 100:
            for pattern_len in [4, 8, 16]:
                if len(data) >= pattern_len * 10:  # At least 10 repetitions
                    pattern = data[:pattern_len]
                    if data.count(pattern) > len(data) // (pattern_len * 5):
                        patterns.append(f"repeated_pattern_{pattern_len}")
        
        # Check for null bytes (potential padding/obfuscation)
        null_count = data.count(b'\x00')
        if null_count > len(data) * 0.3:  # More than 30% null bytes
            patterns.append("excessive_null_bytes")
        
        # Check for high frequency of specific bytes
        byte_counts = Counter(data)
        if byte_counts:
            max_count = max(byte_counts.values())
            if max_count > len(data) * 0.4:  # Single byte appears >40% of time
                patterns.append("single_byte_dominance")
        
        return patterns

    def _check_pe_anomalies(self, header: bytes, file_obj) -> List[str]:
        """Check for PE file anomalies."""
        anomalies = []
        
        try:
            # Check PE header structure
            if len(header) >= 64:
                # Check for unusual entry point
                pe_offset = struct.unpack('<I', header[60:64])[0]
                
                if pe_offset > 1024:  # Unusual PE offset
                    anomalies.append("unusual_pe_offset")
                
                # Read PE header if within bounds
                file_obj.seek(0)
                full_header = file_obj.read(pe_offset + 256)
                
                if len(full_header) > pe_offset + 24:
                    # Check number of sections
                    num_sections = struct.unpack('<H', full_header[pe_offset + 6:pe_offset + 8])[0]
                    
                    if num_sections > 20:  # Unusual number of sections
                        anomalies.append("excessive_sections")
                    elif num_sections == 0:
                        anomalies.append("no_sections")
        
        except Exception:
            anomalies.append("pe_parsing_error")
        
        return anomalies

    def _check_elf_anomalies(self, header: bytes) -> List[str]:
        """Check for ELF file anomalies."""
        anomalies = []
        
        try:
            if len(header) >= 20:
                # Check ELF class (32/64 bit)
                elf_class = header[4]
                if elf_class not in [1, 2]:  # Invalid class
                    anomalies.append("invalid_elf_class")
                
                # Check endianness
                endian = header[5]
                if endian not in [1, 2]:  # Invalid endianness
                    anomalies.append("invalid_endianness")
        
        except Exception:
            anomalies.append("elf_parsing_error")
        
        return anomalies

    def _check_script_threats(self, header: bytes) -> List[str]:
        """Check for threats in script files."""
        threats = []
        
        try:
            script_content = header.decode('utf-8', errors='ignore').lower()
            
            # Check for suspicious script patterns
            suspicious_patterns = [
                'eval', 'exec', 'shell_exec', 'system',
                'base64_decode', 'gzinflate', 'str_rot13',
                'document.write', 'unescape', 'fromcharcode'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in script_content:
                    threats.append(f"suspicious_function_{pattern}")
        
        except Exception:
            pass
        
        return threats

    def _extension_matches_content(self, extension: str, header: bytes) -> bool:
        """Check if file extension matches content type."""
        extension = extension.lower()
        
        # Common file type mappings
        type_mappings = {
            '.exe': [b'MZ'],
            '.dll': [b'MZ'],
            '.pdf': [b'%PDF'],
            '.zip': [b'PK\x03\x04', b'PK\x05\x06'],
            '.jpg': [b'\xff\xd8\xff'],
            '.png': [b'\x89PNG'],
            '.gif': [b'GIF87a', b'GIF89a'],
            '.mp3': [b'ID3', b'\xff\xfb'],
            '.mp4': [b'ftyp'],
            '.doc': [b'\xd0\xcf\x11\xe0'],
            '.xls': [b'\xd0\xcf\x11\xe0']
        }
        
        if extension in type_mappings:
            expected_headers = type_mappings[extension]
            return any(header.startswith(expected) for expected in expected_headers)
        
        return True  # Unknown extension, assume valid

    def _extract_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Extract ASCII strings from binary data."""
        strings = []
        current_string = ""
        
        for byte in data:
            if 32 <= byte <= 126:  # Printable ASCII
                current_string += chr(byte)
            else:
                if len(current_string) >= min_length:
                    strings.append(current_string)
                current_string = ""
        
        # Don't forget the last string
        if len(current_string) >= min_length:
            strings.append(current_string)
        
        return strings

    def _group_activities_by_time(self, activities: List[Dict[str, Any]], 
                                window_minutes: int = 5) -> Dict[datetime, List[Dict[str, Any]]]:
        """Group activities into time windows."""
        windows = defaultdict(list)
        window_size = timedelta(minutes=window_minutes)
        
        for activity in activities:
            timestamp = activity.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Round timestamp to window boundary
            window_start = timestamp.replace(
                minute=(timestamp.minute // window_minutes) * window_minutes,
                second=0,
                microsecond=0
            )
            
            windows[window_start].append(activity)
        
        return windows

    def _evaluate_behavioral_pattern(self, pattern: BehavioralPattern, 
                                   activities: List[Dict[str, Any]]) -> float:
        """Evaluate how well activities match a behavioral pattern."""
        if not activities:
            return 0.0
        
        # Count matching indicators
        matched_indicators = 0
        total_indicators = len(pattern.indicators)
        
        for indicator in pattern.indicators:
            # Check if any activity matches this indicator
            for activity in activities:
                if self._activity_matches_indicator(activity, indicator):
                    matched_indicators += 1
                    break
        
        # Calculate match score
        if total_indicators == 0:
            return 0.0
        
        return matched_indicators / total_indicators

    def _activity_matches_indicator(self, activity: Dict[str, Any], indicator: str) -> bool:
        """Check if an activity matches a behavioral indicator."""
        activity_type = activity.get('type', '').lower()
        activity_details = str(activity.get('details', '')).lower()
        
        # Simple pattern matching - could be enhanced with regex
        return (indicator in activity_type or 
                indicator in activity_details or
                any(indicator in str(v).lower() for v in activity.values()))

    def _pattern_to_threat_indicators(self, pattern: BehavioralPattern) -> List[ThreatIndicator]:
        """Convert behavioral pattern to threat indicators."""
        # Mapping from pattern indicators to threat indicators
        indicator_mapping = {
            'file_create': ThreatIndicator.RAPID_FILE_CREATION,
            'file_modify': ThreatIndicator.FILE_ENCRYPTION,
            'network_connect': ThreatIndicator.NETWORK_COMMUNICATION,
            'process_create': ThreatIndicator.PRIVILEGE_ESCALATION,
            'registry_modify': ThreatIndicator.REGISTRY_MODIFICATION,
            'debugger_detection': ThreatIndicator.ANTI_ANALYSIS,
            'code_injection': ThreatIndicator.CODE_INJECTION
        }
        
        threat_indicators = []
        for indicator in pattern.indicators:
            if indicator in indicator_mapping:
                threat_indicators.append(indicator_mapping[indicator])
            else:
                threat_indicators.append(ThreatIndicator.SUSPICIOUS_BEHAVIOR)
        
        return list(set(threat_indicators))  # Remove duplicates

    def _calculate_risk_level(self, threat_indicators: List[ThreatIndicator], 
                            confidence: float) -> RiskLevel:
        """Calculate overall risk level based on threat indicators and confidence."""
        if not threat_indicators:
            return RiskLevel.LOW
        
        # Assign risk scores to different indicators
        indicator_risks = {
            ThreatIndicator.PACKED_EXECUTABLE: 2,
            ThreatIndicator.SUSPICIOUS_STRINGS: 1,
            ThreatIndicator.RAPID_FILE_CREATION: 3,
            ThreatIndicator.REGISTRY_MODIFICATION: 2,
            ThreatIndicator.NETWORK_COMMUNICATION: 2,
            ThreatIndicator.PRIVILEGE_ESCALATION: 3,
            ThreatIndicator.FILE_ENCRYPTION: 4,
            ThreatIndicator.ANTI_ANALYSIS: 2,
            ThreatIndicator.CODE_INJECTION: 3,
            ThreatIndicator.SUSPICIOUS_BEHAVIOR: 1
        }
        
        # Calculate total risk score
        total_risk = sum(indicator_risks.get(indicator, 1) for indicator in threat_indicators)
        
        # Adjust by confidence
        adjusted_risk = total_risk * confidence
        
        # Map to risk levels
        if adjusted_risk >= 3.0:
            return RiskLevel.CRITICAL
        elif adjusted_risk >= 2.0:
            return RiskLevel.HIGH
        elif adjusted_risk >= 1.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

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

    def _get_cached_result(self, file_hash: str) -> Optional[HeuristicResult]:
        """Get cached analysis result."""
        with self.lock:
            if file_hash in self.analysis_cache:
                # Check if cache entry is still valid
                if (file_hash in self.cache_expiry and 
                    datetime.now() < self.cache_expiry[file_hash]):
                    return self.analysis_cache[file_hash]
                else:
                    # Remove expired entry
                    del self.analysis_cache[file_hash]
                    self.cache_expiry.pop(file_hash, None)
        
        return None

    def _cache_result(self, file_hash: str, result: HeuristicResult):
        """Cache analysis result."""
        with self.lock:
            self.analysis_cache[file_hash] = result
            self.cache_expiry[file_hash] = datetime.now() + timedelta(hours=self.cache_ttl_hours)
            
            # Limit cache size
            if len(self.analysis_cache) > 1000:
                # Remove oldest entries
                oldest_hashes = sorted(
                    self.cache_expiry.keys(),
                    key=lambda h: self.cache_expiry[h]
                )[:100]
                
                for hash_to_remove in oldest_hashes:
                    self.analysis_cache.pop(hash_to_remove, None)
                    self.cache_expiry.pop(hash_to_remove, None)

    def _store_analysis_result(self, result: HeuristicResult, file_hash: str):
        """Store analysis result in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO analysis_results 
                (file_path, file_hash, heuristic_type, threat_indicators, risk_level, 
                 confidence_score, description, details, scan_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.file_path,
                file_hash,
                result.heuristic_type.value,
                json.dumps([ti.value for ti in result.threat_indicators]),
                result.risk_level.value,
                result.confidence_score,
                result.description,
                json.dumps(result.details),
                result.scan_time
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error("Error storing analysis result: %s", e)

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis engine statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count total analyses
            cursor.execute("SELECT COUNT(*) FROM analysis_results")
            total_analyses = cursor.fetchone()[0]
            
            # Count by risk level
            cursor.execute("""
                SELECT risk_level, COUNT(*) 
                FROM analysis_results 
                GROUP BY risk_level
            """)
            risk_level_counts = dict(cursor.fetchall())
            
            # Count by heuristic type
            cursor.execute("""
                SELECT heuristic_type, COUNT(*) 
                FROM analysis_results 
                GROUP BY heuristic_type
            """)
            heuristic_type_counts = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "total_analyses": total_analyses,
                "risk_level_distribution": risk_level_counts,
                "heuristic_type_distribution": heuristic_type_counts,
                "cache_size": len(self.analysis_cache),
                "behavioral_patterns_count": len(self.behavioral_patterns),
                "file_signatures_count": len(self.file_signatures),
                "suspicious_strings_count": len(self.suspicious_strings)
            }
            
        except Exception as e:
            self.logger.error("Error getting statistics: %s", e)
            return {}

    def add_behavioral_pattern(self, pattern: BehavioralPattern):
        """Add a new behavioral pattern."""
        self.behavioral_patterns[pattern.pattern_id] = pattern
        
        # Store in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO behavioral_patterns 
                (pattern_id, name, description, indicators, weight, risk_level, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.pattern_id,
                pattern.name,
                pattern.description,
                json.dumps(pattern.indicators),
                pattern.weight,
                pattern.risk_level.value,
                pattern.enabled
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error("Error storing behavioral pattern: %s", e)

    def add_file_signature(self, signature: FileSignature):
        """Add a new file signature."""
        self.file_signatures[signature.signature_id] = signature
        
        # Store in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO file_signatures 
                (signature_id, name, pattern, offset, threat_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                signature.signature_id,
                signature.name,
                signature.pattern,
                signature.offset,
                signature.threat_type,
                signature.confidence
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error("Error storing file signature: %s", e)
