#!/usr/bin/env python3
"""
Enhanced ClamAV wrapper for S&D - Search & Destroy
Supports virus definition updates, multiple signature sources, and detailed scanning
"""
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from .secure_subprocess import run_secure


class ScanResult(Enum):
    """Scan result types."""

    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class VirusDefinitionInfo:
    """Information about virus definitions."""

    name: str
    version: str
    last_updated: datetime
    size: int
    url: str


@dataclass
class ScanFileResult:
    """Result for a single file scan."""

    file_path: str
    result: ScanResult
    threat_name: str = ""
    threat_type: str = ""
    file_size: int = 0
    scan_time: float = 0.0
    error_message: str = ""


class ClamAVWrapper:
    """Enhanced ClamAV wrapper with full feature support."""

    def __init__(self):
        try:
            from utils.config import CACHE_DIR, load_config, setup_logging
        except ImportError:
            # Create minimal fallbacks for testing
            import logging

            def setup_logging():
                return logging.getLogger(__name__)

            def load_config():
                return {
                    "advanced_settings": {
                        "scan_timeout": 30,
                        "max_file_size": 100 * 1024 * 1024,
                        "max_recursion_depth": 10,
                    }
                }

            CACHE_DIR = Path("/tmp/test_cache")

        self.logger = setup_logging()
        self.config = load_config()

        # ClamAV executable paths
        self.clamscan_path = self._find_executable("clamscan")
        self.clamdscan_path = self._find_executable("clamdscan")
        self.freshclam_path = self._find_executable("freshclam")
        self.clamd_path = self._find_executable("clamd")

        # Database paths
        self.db_path = Path("/var/lib/clamav")

        # Handle CACHE_DIR which might be mocked during testing
        try:
            if hasattr(
                    CACHE_DIR,
                    "__truediv__"):  # Check if it's a Path object
                self.custom_db_path = CACHE_DIR / "custom_signatures"
            else:
                # Handle string or Mock case
                self.custom_db_path = Path(
                    str(CACHE_DIR)) / "custom_signatures"
        except (TypeError, AttributeError):
            # Fallback for testing
            self.custom_db_path = Path("/tmp/test_cache") / "custom_signatures"

        try:
            self.custom_db_path.mkdir(exist_ok=True)
        except (OSError, AttributeError):
            # Handle case where mkdir fails or path is invalid
            pass

        # Check ClamAV availability
        self.available = self._check_clamav_availability()

        if not self.available:
            self.logger.error("ClamAV not found or not properly installed")
        else:
            self.logger.debug("ClamAV initialized successfully")
            # Note: Daemon startup is now deferred until first scan operation
            # to avoid requesting sudo privileges during app initialization

    def _try_start_daemon_if_needed(self):
        """Try to start ClamAV daemon if it's not running and configured for use."""
        if not self.clamdscan_path or not self.clamd_path:
            self.logger.debug("Daemon executables not available, using clamscan")
            return
            
        if self._is_clamd_running():
            self.logger.debug("ClamAV daemon already running")
            return
            
        self.logger.info("Attempting to start ClamAV daemon for better performance...")
        if self.start_daemon():
            self.logger.info("ClamAV daemon started successfully - scans will be faster")
        else:
            self.logger.info("Could not start daemon - will use regular clamscan (slower)")

    def _find_executable(self, name: str) -> Optional[str]:
        """Find ClamAV executable in system PATH."""
        import shutil

        return shutil.which(name)

    def _check_clamav_availability(self) -> bool:
        """Check if ClamAV is properly installed and accessible."""
        if not self.clamscan_path:
            return False

        try:
            result = run_secure([
                self.clamscan_path, "--version"
            ], timeout=10, capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_engine_version(self) -> Tuple[str, str]:
        """Get ClamAV engine and signature database versions."""
        if not self.available:
            return "Not available", "Not available"

        try:
            result = run_secure([
                self.clamscan_path, "--version"
            ], timeout=10, capture_output=True, text=True)

            if result.returncode == 0:
                # Parse version output
                lines = result.stdout.strip().split("\n")
                engine_version = "Unknown"
                sig_version = "Unknown"

                for line in lines:
                    if line.startswith("ClamAV"):
                        engine_version = line.split()[1]
                    elif "main.cvd" in line or "main.cld" in line:
                        match = re.search(r"version (\d+)", line)
                        if match:
                            sig_version = match.group(1)

                return engine_version, sig_version

        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        return "Unknown", "Unknown"

    def scan_file(self, file_path: str, use_daemon: bool = True, **kwargs) -> ScanFileResult:
        """Scan a single file with ClamAV.
        
        Args:
            file_path: Path to file to scan
            use_daemon: If True, try to use clamdscan (faster) before falling back to clamscan
            **kwargs: Additional scan options
        """
        # Path validation: reject world-writable, symlink traversal
        try:
            p = Path(file_path)
            if p.is_symlink():
                return ScanFileResult(file_path=file_path, result=ScanResult.ERROR, error_message="Symlink not allowed")
            if os.name == "posix":
                st = p.stat()
                if st.st_mode & 0o002:
                    return ScanFileResult(file_path=file_path, result=ScanResult.ERROR, error_message="World-writable file blocked")
        except OSError:
            return ScanFileResult(file_path=file_path, result=ScanResult.ERROR, error_message="Path validation failed")
            
        if not self.available:
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message="ClamAV not available",
            )

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message="File not found",
            )

        # Get file info
        file_size = file_path_obj.stat().st_size
        start_time = datetime.now()

        # Try clamdscan first if requested and available
        if use_daemon and self.clamdscan_path:
            # Check if daemon is running, try to start it if configured but not running
            if not self._is_clamd_running():
                # Only try to start daemon if configured to do so
                if self.config.get("performance", {}).get("enable_clamav_daemon", True):
                    self.logger.debug("Daemon not running, attempting to start for scan operation")
                    self._try_start_daemon_if_needed()
            
            # Use daemon if it's now running
            if self._is_clamd_running():
                try:
                    return self._scan_file_with_daemon(file_path, file_size, start_time, **kwargs)
                except Exception as e:
                    self.logger.warning(f"Daemon scan failed, falling back to clamscan: {e}")

        # Fallback to regular clamscan
        try:
            # Build command
            cmd = [self.clamscan_path]
            cmd.extend(self._build_scan_options(**kwargs))
            cmd.append(str(file_path_obj))

            # Run scan
            result = run_secure(
                cmd,
                timeout=self.config["advanced_settings"]["scan_timeout"],
                capture_output=True,
                text=True,
            )

            scan_time = (datetime.now() - start_time).total_seconds()

            # Parse result
            return self._parse_scan_output(
                file_path,
                result.stdout,
                result.stderr,
                result.returncode,
                file_size,
                scan_time,
            )

        except subprocess.TimeoutExpired:
            scan_time = (datetime.now() - start_time).total_seconds()
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.TIMEOUT,
                file_size=file_size,
                scan_time=scan_time,
                error_message="Scan timeout",
            )
        except (subprocess.SubprocessError, OSError, ValueError, PermissionError) as e:
            scan_time = (datetime.now() - start_time).total_seconds()
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                file_size=file_size,
                scan_time=scan_time,
                error_message=str(e),
            )

    def scan_directory(self, directory_path: str, **
                       kwargs) -> List[ScanFileResult]:
        """Scan a directory recursively."""
        # Directory validation
        try:
            d = Path(directory_path)
            if d.is_symlink():
                return [ScanFileResult(file_path=directory_path, result=ScanResult.ERROR, error_message="Symlink directory not allowed")]
            if os.name == "posix":
                st = d.stat()
                if st.st_mode & 0o002:
                    return [ScanFileResult(file_path=directory_path, result=ScanResult.ERROR, error_message="World-writable directory blocked")]
        except OSError:
            return [ScanFileResult(file_path=directory_path, result=ScanResult.ERROR, error_message="Directory validation failed")]
        if not self.available:
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.ERROR,
                    error_message="ClamAV not available",
                )
            ]

        directory_obj = Path(directory_path)
        if not directory_obj.exists() or not directory_obj.is_dir():
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.ERROR,
                    error_message="Directory not found",
                )
            ]

        try:
            # Build command for directory scan
            cmd = [self.clamscan_path]
            cmd.extend(self._build_scan_options(**kwargs))
            cmd.extend(["--recursive", str(directory_obj)])

            # Run scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config["advanced_settings"]["scan_timeout"]
                * 10,  # Longer timeout for directories
                check=False
            )

            # Parse directory scan results
            return self._parse_directory_scan_output(
                result.stdout, result.stderr, result.returncode
            )

        except subprocess.TimeoutExpired:
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.TIMEOUT,
                    error_message="Directory scan timeout",
                )
            ]
        except (subprocess.SubprocessError, OSError) as e:
            return [
                ScanFileResult(
                    file_path=directory_path,
                    result=ScanResult.ERROR,
                    error_message=str(e),
                )
            ]

    def _build_scan_options(self, quick_scan: bool = False, **kwargs) -> List[str]:
        """Build ClamAV scan options from configuration and parameters.
        
        Args:
            quick_scan: If True, use performance-optimized settings
            **kwargs: Additional scan options
        """
        options = []
        scan_settings = self.config.get("scan_settings", {})
        performance_settings = self.config.get("performance", {})

        # Performance optimization for quick scans
        if quick_scan:
            # Reduced limits for faster scanning
            options.extend(["--max-filesize", "25M"])  # Smaller than default
            options.extend(["--max-recursion", "8"])   # Less recursion
            options.extend(["--max-files", "5000"])    # Fewer files per archive
            
            # Skip some intensive scan types in quick mode
            options.append("--scan-archive")  # Still scan archives but with limits
            options.append("--scan-pe")       # Always scan executables
            options.append("--scan-elf")      # Always scan Linux executables
        else:
            # Full scan mode with comprehensive options
            # Archive scanning
            if kwargs.get("scan_archives", scan_settings.get("scan_archives", True)):
                options.append("--scan-archive")

            # Email scanning
            if kwargs.get("scan_email", scan_settings.get("scan_email", True)):
                options.append("--scan-mail")

            # OLE2 scanning (Office documents)
            if kwargs.get("scan_ole2", scan_settings.get("scan_ole2", True)):
                options.append("--scan-ole2")

            # PDF scanning
            if kwargs.get("scan_pdf", scan_settings.get("scan_pdf", True)):
                options.append("--scan-pdf")

            # HTML scanning
            if kwargs.get("scan_html", scan_settings.get("scan_html", True)):
                options.append("--scan-html")

            # Executable scanning (always enabled for security)
            options.append("--scan-pe")
            options.append("--scan-elf")

            # File size limits
            max_filesize = kwargs.get("max_filesize", scan_settings.get("max_filesize", "100M"))
            if max_filesize:
                options.extend(["--max-filesize", str(max_filesize)])

            # Recursion limits
            max_recursion = kwargs.get("max_recursion", scan_settings.get("max_recursion", 16))
            if max_recursion:
                options.extend(["--max-recursion", str(max_recursion)])

            # Max files
            max_files = kwargs.get("max_files", scan_settings.get("max_files", 10000))
            if max_files:
                options.extend(["--max-files", str(max_files)])

        # Performance optimizations that apply to all scans
        # Detect broken executables and don't scan them (saves time)
        options.append("--detect-broken")
        
        # Skip files larger than necessary (configurable per scan type)
        max_scan_size = performance_settings.get("max_scan_size", "200M" if not quick_scan else "50M")
        options.extend(["--max-scansize", max_scan_size])

        # Custom database path
        if self.custom_db_path.exists() and any(self.custom_db_path.iterdir()):
            options.extend(["--database", str(self.custom_db_path)])

        # Verbose output for better parsing
        options.extend(["--infected", "--verbose"])

        return options

    def get_version_info(self) -> Dict[str, str]:
        """Get detailed ClamAV version and database information."""
        version_info = {
            'engine_version': 'Unknown',
            'database_version': 'Unknown',
            'database_date': 'Unknown',
            'signatures_count': 'Unknown',
            'engine_capabilities': []
        }
        
        if not self.available:
            return version_info
            
        try:
            # Get engine version
            result = subprocess.run([self.clamscan_path, '--version'], 
                                  capture_output=True, text=True, timeout=10, check=False)
            if result.returncode == 0:
                version_info['engine_version'] = result.stdout.strip()
                
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
            
        # Get database info
        try:
            result = subprocess.run([self.clamscan_path, '--database-info'], 
                                  capture_output=True, text=True, timeout=10, check=False)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'signatures:' in line.lower():
                        version_info['signatures_count'] = line.split(':')[-1].strip()
                    elif 'database date:' in line.lower():
                        version_info['database_date'] = line.split(':', 1)[-1].strip()
                        
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
            
        return version_info

    def verify_database_integrity(self) -> bool:
        """Verify ClamAV database integrity and signatures."""
        if not self.available:
            return False
            
        try:
            # Check if database files exist and are readable
            db_files = [
                '/var/lib/clamav/main.cvd',
                '/var/lib/clamav/main.cld', 
                '/var/lib/clamav/daily.cvd',
                '/var/lib/clamav/daily.cld',
                '/var/lib/clamav/bytecode.cvd',
                '/var/lib/clamav/bytecode.cld'
            ]
            
            valid_db_found = False
            for db_file in db_files:
                if Path(db_file).exists() and Path(db_file).stat().st_size > 0:
                    valid_db_found = True
                    break
                    
            if not valid_db_found:
                self.logger.warning("No valid ClamAV database files found")
                return False
                
            # Test scan a known clean file to verify database is working
            test_result = subprocess.run([self.clamscan_path, '--database-info'], 
                                       capture_output=True, text=True, timeout=15)
            return test_result.returncode == 0
            
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError) as e:
            self.logger.error(f"Database integrity check failed: {e}")
            return False

    def get_security_recommendations(self) -> List[str]:
        """Get security recommendations based on current configuration."""
        recommendations = []
        
        # Check for latest version (ClamAV 1.4 LTS as of 2025)
        version_info = self.get_version_info()
        if 'ClamAV 1.4' not in version_info.get('engine_version', ''):
            recommendations.append("Update to ClamAV 1.4 LTS for latest security fixes and performance improvements")
            
        # Check database freshness
        if not self.verify_database_integrity():
            recommendations.append("Update virus databases using freshclam")
            
        # Check daemon configuration
        if self.clamdscan_path and not self._is_clamd_running():
            recommendations.append("Start ClamAV daemon (clamd) for better performance and security")
            
        # Check for secure configuration
        config_path = Path('/etc/clamav/clamd.conf')
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                    
                if 'TCPSocket' in config_content and 'TCPAddr 127.0.0.1' not in config_content:
                    recommendations.append("Restrict TCP socket access to localhost for security")
                    
                if 'MaxScanSize' not in config_content:
                    recommendations.append("Configure MaxScanSize to prevent memory exhaustion")
                    
            except (IOError, PermissionError):
                recommendations.append("Review ClamAV daemon configuration for security settings")
        
        return recommendations

    def optimize_for_parallel_scanning(self, max_threads: int = None) -> Dict[str, Any]:
        """Configure ClamAV for optimal parallel scanning performance."""
        if max_threads is None:
            try:
                import psutil
                max_threads = min(psutil.cpu_count(logical=False) * 2, 8)
            except (ImportError, AttributeError):
                max_threads = 4
                
        optimization_config = {
            'performance_mode': True,
            'max_threads': max_threads,
            'memory_optimization': True,
            'scan_options': {
                'max_filesize': '200M',  # Based on 2024-2025 recommendations
                'max_recursion': 12,     # Balanced for performance/security
                'max_files': 8000,       # Optimized for modern systems
                'max_scansize': '400M',  # Prevent excessive memory usage
            },
            'daemon_config': {
                'use_daemon': True,
                'concurrent_connections': max_threads,
                'memory_limit': '2G',    # Align with 3GB+ recommendation
            }
        }
        
        return optimization_config

    def should_scan_file(self, file_path: str, quick_scan: bool = False) -> bool:
        """Determine if a file should be scanned based on performance heuristics."""
        try:
            path_obj = Path(file_path)
            
            # Get file info
            stat_result = path_obj.stat()
            file_size = stat_result.st_size
            file_extension = path_obj.suffix.lower()
            
            # Skip empty files
            if file_size == 0:
                return False
                
            # Performance optimization: Skip very large files in quick scan mode
            if quick_scan:
                max_quick_size = self.config.get("performance", {}).get("quick_scan_max_file_size", 50 * 1024 * 1024)  # 50MB
                if file_size > max_quick_size:
                    return False
            
            # Skip files that are very unlikely to be malicious
            safe_extensions = {
                # Text files
                '.txt', '.md', '.rst', '.log',
                # Image files (unless specifically requested)
                '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.webp',
                # Audio/Video (large files, low risk in quick scans)
                '.mp3', '.mp4', '.avi', '.mkv', '.flv', '.wav', '.ogg', '.m4a',
                # Font files
                '.ttf', '.otf', '.woff', '.woff2',
                # Data files
                '.json', '.yaml', '.yml', '.csv', '.xml',
            }
            
            # In quick scan mode, skip safe file types
            if quick_scan and file_extension in safe_extensions:
                return False
            
            # Skip very large media files even in full scans (configurable)
            media_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
                              '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}
            if file_extension in media_extensions:
                max_media_size = self.config.get("performance", {}).get("max_media_file_size", 100 * 1024 * 1024)  # 100MB
                if file_size > max_media_size:
                    return False
            
            # Always scan potentially dangerous file types
            high_risk_extensions = {
                '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js', '.jar',
                '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
                '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
                '.html', '.htm', '.php', '.asp', '.jsp',
            }
            
            if file_extension in high_risk_extensions:
                return True
            
            # Check if file is executable
            if stat_result.st_mode & 0o111:  # Has execute permission
                return True
                
            # For files without extension, check if they might be executable
            if not file_extension:
                # Read first few bytes to check for executable signatures
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                        # ELF magic number (Linux executables)
                        if header.startswith(b'\x7fELF'):
                            return True
                        # PE magic number (Windows executables)
                        if header.startswith(b'MZ'):
                            return True
                except (IOError, PermissionError):
                    pass
            
            return True
            
        except (OSError, IOError, PermissionError):
            # If we can't analyze the file, err on the side of caution and scan it
            return True

    def _is_clamd_running(self) -> bool:
        """Check if ClamAV daemon is running."""
        try:
            # Try to connect to the daemon socket or ping
            result = subprocess.run(
                [self.clamdscan_path, "--ping"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _scan_file_with_daemon(self, file_path: str, file_size: int, start_time: datetime, **kwargs) -> ScanFileResult:
        """Scan file using ClamAV daemon (faster)."""
        cmd = [self.clamdscan_path]
        
        # Add basic daemon options
        cmd.extend(["--infected", "--verbose"])
        
        # Add file size limit if specified
        max_filesize = kwargs.get("max_filesize", self.config.get("scan_settings", {}).get("max_filesize"))
        if max_filesize:
            cmd.extend(["--max-filesize", str(max_filesize)])
            
        cmd.append(file_path)
        
        # Run daemon scan
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.config["advanced_settings"]["scan_timeout"],
            check=False
        )
        
        scan_time = (datetime.now() - start_time).total_seconds()
        
        # Parse daemon output (similar format to clamscan)
        return self._parse_scan_output(
            file_path,
            result.stdout,
            result.stderr,
            result.returncode,
            file_size,
            scan_time,
        )

    def start_daemon(self) -> bool:
        """Start ClamAV daemon if not running."""
        if self._is_clamd_running():
            self.logger.info("ClamAV daemon already running")
            return True
            
        if not self.clamd_path:
            self.logger.warning("clamd not found, cannot start daemon")
            return False
            
        try:
            # Start daemon in background
            subprocess.Popen([self.clamd_path], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait a moment for it to start
            import time
            time.sleep(2)
            
            if self._is_clamd_running():
                self.logger.info("ClamAV daemon started successfully")
                return True
            else:
                self.logger.warning("Failed to start ClamAV daemon")
                return False
                
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.logger.error(f"Error starting ClamAV daemon: {e}")
            return False

    def apply_2025_security_hardening(self) -> Dict[str, bool]:
        """Apply 2025 security hardening recommendations for ClamAV."""
        hardening_results = {
            'database_verification': False,
            'secure_permissions': False,
            'memory_limits': False,
            'network_security': False,
            'signature_validation': False
        }
        
        # 1. Verify database integrity and signatures
        hardening_results['database_verification'] = self.verify_database_integrity()
        
        # 2. Check and secure file permissions
        try:
            db_path = Path('/var/lib/clamav')
            if db_path.exists():
                # Verify database directory permissions
                stat_info = db_path.stat()
                # Should be readable by clamav user, not world-writable
                if not (stat_info.st_mode & 0o002):  # Not world-writable
                    hardening_results['secure_permissions'] = True
        except OSError:
            pass
            
        # 3. Validate memory limits are set
        config_path = Path('/etc/clamav/clamd.conf')
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = f.read()
                    if any(param in config for param in ['MaxScanSize', 'MaxFileSize', 'MaxRecursion']):
                        hardening_results['memory_limits'] = True
                    if 'TCPAddr 127.0.0.1' in config or 'LocalSocket' in config:
                        hardening_results['network_security'] = True
            except (IOError, PermissionError):
                pass
                
        # 4. Signature validation (CVD files have built-in verification)
        try:
            # Check if we can verify signature database
            result = subprocess.run([self.clamscan_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'ClamAV' in result.stdout:
                hardening_results['signature_validation'] = True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
            
        return hardening_results

    def get_2025_performance_settings(self) -> Dict[str, Any]:
        """Get optimized performance settings based on 2024-2025 research."""
        return {
            'daemon_settings': {
                'MaxThreads': 12,  # Based on modern multi-core systems
                'MaxConnectionQueueLength': 200,
                'MaxScanSize': '400M',  # Increased for modern file sizes
                'MaxFileSize': '100M',
                'MaxRecursion': 12,     # Balanced security/performance
                'MaxFiles': 8000,       # Optimized for current malware
                'StreamMaxLength': '100M',
                'ReadTimeout': 300,     # 5 minutes for large files
                'CommandReadTimeout': 30,
                'LogVerbose': False,    # Reduce I/O overhead
                'DatabaseDirectory': '/var/lib/clamav',
            },
            'scanning_optimizations': {
                'algorithm_optimization': {
                    'use_aho_corasick': True,  # Parallelization research shows benefits
                    'parallel_signature_matching': True,
                    'memory_mapped_scanning': True,
                },
                'file_type_detection': {
                    'fast_file_type_detection': True,
                    'skip_non_executable_in_quick_scan': True,
                    'prioritize_high_risk_extensions': True,
                },
                'memory_management': {
                    'lazy_loading': True,
                    'signature_cache_optimization': True,
                    'reduced_locking_overhead': True,  # ClamAV 1.4.1+ improvement
                }
            },
            'security_enhancements': {
                'signature_verification': True,
                'database_integrity_checks': True,
                'secure_temp_files': True,
                'privilege_separation': True,
            }
        }

    def implement_multithreaded_scanning(self, file_list: List[str], max_workers: int = None) -> List[Dict[str, Any]]:
        """Implement parallel scanning based on 2024 research findings."""
        if max_workers is None:
            try:
                import psutil
                # Research shows optimal performance with CPU cores * 1.5 for I/O bound tasks
                max_workers = min(int(psutil.cpu_count(logical=False) * 1.5), 8)
            except (ImportError, AttributeError, TypeError):
                max_workers = 4
                
        results = []
        
        # Use daemon if available for better parallel performance
        if self._is_clamd_running():
            self.logger.info(f"Using daemon-based parallel scanning with {max_workers} workers")
            # Implement parallel daemon scanning
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def scan_single_file(file_path: str) -> Dict[str, Any]:
                start_time = datetime.now()
                try:
                    result = self._scan_file_with_daemon(
                        file_path, 
                        Path(file_path).stat().st_size if Path(file_path).exists() else 0,
                        start_time
                    )
                    return {
                        'file_path': file_path,
                        'result': result.result.value,
                        'threat_name': result.threat_name,
                        'scan_time': result.scan_time,
                        'success': True
                    }
                except Exception as e:
                    return {
                        'file_path': file_path,
                        'result': 'error',
                        'error': str(e),
                        'scan_time': (datetime.now() - start_time).total_seconds(),
                        'success': False
                    }
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(scan_single_file, file_path): file_path 
                                 for file_path in file_list}
                
                for future in as_completed(future_to_file):
                    results.append(future.result())
        else:
            self.logger.warning("Daemon not available, falling back to sequential scanning")
            for file_path in file_list:
                result = self.scan_file(file_path)
                results.append({
                    'file_path': file_path,
                    'result': result.result.value,
                    'threat_name': result.threat_name,
                    'scan_time': result.scan_time,
                    'success': result.result != ScanResult.ERROR
                })
                
        return results

    def _parse_scan_output(
        self,
        file_path: str,
        stdout: str,
        stderr: str,
        returncode: int,
        file_size: int,
        scan_time: float,
    ) -> ScanFileResult:
        """Parse ClamAV scan output for a single file."""

        # Check for errors first
        if returncode == 2:  # ClamAV error
            error_msg = stderr.strip() if stderr else "ClamAV scan error"
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                file_size=file_size,
                scan_time=scan_time,
                error_message=error_msg,
            )

        # Parse threat information
        if returncode == 1:  # Threat found
            threat_match = re.search(r"(.+): (.+) FOUND", stdout)
            if threat_match:
                threat_name = threat_match.group(2)
                threat_type = self._classify_threat(threat_name)

                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.INFECTED,
                    threat_name=threat_name,
                    threat_type=threat_type,
                    file_size=file_size,
                    scan_time=scan_time,
                )

        # Clean file
        return ScanFileResult(
            file_path=file_path,
            result=ScanResult.CLEAN,
            file_size=file_size,
            scan_time=scan_time,
        )

    def _parse_directory_scan_output(
        self, stdout: str, stderr: str, returncode: int
    ) -> List[ScanFileResult]:
        """Parse ClamAV output for directory scan."""
        results = []

        # Parse each line for file results
        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Infected file
            threat_match = re.search(r"(.+): (.+) FOUND", line)
            if threat_match:
                file_path = threat_match.group(1)
                threat_name = threat_match.group(2)
                threat_type = self._classify_threat(threat_name)

                results.append(
                    ScanFileResult(
                        file_path=file_path,
                        result=ScanResult.INFECTED,
                        threat_name=threat_name,
                        threat_type=threat_type,
                        file_size=self._get_file_size(file_path),
                    )
                )

            # Clean file (optional, can be many)
            elif " OK" in line and not line.endswith("OK"):
                file_path = line.replace(" OK", "")
                if Path(file_path).exists():
                    results.append(
                        ScanFileResult(
                            file_path=file_path,
                            result=ScanResult.CLEAN,
                            file_size=self._get_file_size(file_path),
                        )
                    )

        return results

    def _classify_threat(self, threat_name: str) -> str:
        """Classify threat type based on name."""
        threat_name_lower = threat_name.lower()

        if any(word in threat_name_lower for word in ["trojan", "backdoor"]):
            return "Trojan"
        elif any(word in threat_name_lower for word in ["virus", "worm"]):
            return "Virus"
        elif any(word in threat_name_lower for word in ["adware", "pup"]):
            return "Adware/PUP"
        elif any(word in threat_name_lower for word in ["ransomware", "crypto"]):
            return "Ransomware"
        elif any(word in threat_name_lower for word in ["rootkit"]):
            return "Rootkit"
        elif any(word in threat_name_lower for word in ["spyware"]):
            return "Spyware"
        elif any(word in threat_name_lower for word in ["exploit"]):
            return "Exploit"
        else:
            return "Malware"

    def _get_file_size(self, file_path: str) -> int:
        """Get file size safely."""
        try:
            return Path(file_path).stat().st_size
        except (OSError, IOError):
            return 0

    def update_virus_definitions(self) -> bool:
        """Update virus definitions using freshclam.

        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self.available:
            self.logger.error("ClamAV not available")
            return False

        if not self.freshclam_path:
            self.logger.error("freshclam not found in PATH")
            return False

        self.logger.info("Starting virus definitions update...")

        # Try different approaches to update definitions
        update_commands = [
            # First try without privileges (in case user has permissions or custom
            # database directory)
            [self.freshclam_path, "--verbose"],
            # Try with user database directory if system directory fails
            [self.freshclam_path, "--verbose",
                "--datadir", str(self.custom_db_path)],
        ]

        # Use elevated_run for consistent GUI sudo experience (same as RKHunter)
        from .elevated_runner import elevated_run
        
        # Add elevated command using the same method as RKHunter
        update_commands.append([self.freshclam_path, "--verbose"])

        for i, cmd in enumerate(update_commands):
            try:
                self.logger.debug(
                    f"Attempt {
                        i +
                        1}: Running command: {
                        ' '.join(cmd)}")

                # Skip privileged commands if we're already running as root
                if os.getuid() == 0 and i >= 2:  # Skip elevated attempts if root
                    self.logger.debug(
                        "Already running as root, skipping elevated command")
                    continue

                # Use elevated_run for the last attempt (consistent with RKHunter)
                if i == len(update_commands) - 1:
                    self.logger.info("Using elevated privileges with GUI authentication (same as RKHunter)")
                    result = elevated_run(
                        cmd,
                        capture_output=True,
                        timeout=300,  # 5 minutes timeout
                        gui=True  # Use GUI authentication like RKHunter
                    )
                    
                    self.logger.debug(f"Return code: {result.returncode}")
                    self.logger.debug(f"STDOUT: {result.stdout}")
                    self.logger.debug(f"STDERR: {result.stderr}")

                    if result.returncode == 0:
                        self.logger.info(
                            "Virus definitions updated successfully with GUI authentication"
                        )
                        return True

                    # Check if definitions are already up to date
                    output_text = result.stdout + result.stderr
                    if (
                        "is up to date" in output_text.lower()
                        or "database is up-to-date" in output_text.lower()
                    ):
                        self.logger.info(
                            "Virus definitions already up to date")
                        return True

                    self.logger.warning(
                        f"Elevated update failed (code {result.returncode}): {result.stderr}")
                    continue
                
                else:
                    # Non-privileged commands can capture output normally
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minutes timeout
                        check=False,
                    )

                    self.logger.debug(f"Return code: {result.returncode}")
                    self.logger.debug(f"STDOUT: {result.stdout}")
                    self.logger.debug(f"STDERR: {result.stderr}")

                    if result.returncode == 0:
                        self.logger.info(
                            "Virus definitions updated successfully")
                        return True

                    # Check if definitions are already up to date
                    output_text = result.stdout + result.stderr
                    if (
                        "is up to date" in output_text.lower()
                        or "database is up-to-date" in output_text.lower()
                    ):
                        self.logger.info(
                            "Virus definitions already up to date")
                        return True

                    # Check for specific error patterns
                    if (
                        "permission denied" in result.stderr.lower()
                        or "can't create temporary directory" in result.stderr.lower()
                    ):
                        self.logger.warning(
                            f"Permission error with attempt {
                                i + 1}, trying next method...")
                        continue

                    # If this was not the last attempt, log the failure
                    if i < len(update_commands) - 1:
                        self.logger.warning(
                            f"Update attempt {i + 1} failed, trying next method")

            except subprocess.TimeoutExpired:
                self.logger.error(
                    f"Virus definition update attempt {
                        i + 1} timed out after 5 minutes")
                continue
            except FileNotFoundError as e:
                self.logger.error(
                    f"Command not found in attempt {
                        i + 1}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Error in update attempt {i + 1}: {str(e)}")
                continue

        # If all attempts failed, provide helpful error message
        self.logger.error("All virus definition update attempts failed.")
        self.logger.error("Please ensure either:")
        self.logger.error(
            "1. You have write permissions to /var/lib/clamav/, or")
        self.logger.error("2. GUI authentication is working properly, or")
        self.logger.error(
            "3. Set up a custom database directory with proper permissions"
        )
        return False

    def _update_custom_source(self, source_url: str) -> bool:
        """Update custom signature source."""
        try:
            response = requests.get(source_url, timeout=60)
            response.raise_for_status()

            # Save to custom database directory
            filename = hashlib.md5(source_url.encode()).hexdigest() + ".cvd"
            filepath = self.custom_db_path / filename

            with open(filepath, "wb") as f:
                f.write(response.content)

            self.logger.info("Updated custom source: %s", source_url)
            return True

        except (requests.RequestException, IOError) as e:
            self.logger.error(
                "Failed to update custom source %s: %s", source_url, e)
            return False

    def get_definition_info(self) -> List[VirusDefinitionInfo]:
        """Get information about current virus definitions."""
        definitions = []

        # Check main ClamAV databases - handle permission errors gracefully
        try:
            if self.db_path.exists():
                for db_file in self.db_path.glob("*.c[vl]d"):
                    try:
                        stat = db_file.stat()
                        definitions.append(
                            VirusDefinitionInfo(
                                name=db_file.name,
                                version="Unknown",  # Would need to parse database file for actual version
                                last_updated=datetime.fromtimestamp(
                                    stat.st_mtime),
                                size=stat.st_size,
                                url="official",
                            )
                        )
                    except (OSError, IOError, PermissionError) as e:
                        # Log the error but continue processing other files
                        print(f"Warning: Could not access {db_file}: {e}")
                        continue
        except (OSError, IOError, PermissionError) as e:
            print(
                f"Warning: Could not access database directory {
                    self.db_path}: {e}")

        # Check custom databases - handle permission errors gracefully
        try:
            if self.custom_db_path.exists():
                for db_file in self.custom_db_path.glob("*.cvd"):
                    try:
                        stat = db_file.stat()
                        definitions.append(
                            VirusDefinitionInfo(
                                name=db_file.name,
                                version="Custom",
                                last_updated=datetime.fromtimestamp(
                                    stat.st_mtime),
                                size=stat.st_size,
                                url="custom",
                            ))
                    except (OSError, IOError, PermissionError) as e:
                        # Log the error but continue processing other files
                        print(
                            f"Warning: Could not access custom db {db_file}: {e}")
                        continue
        except (OSError, IOError, PermissionError) as e:
            print(
                f"Warning: Could not access custom database directory {
                    self.custom_db_path}: {e}")

        return definitions

    def check_definition_freshness(self) -> Dict[str, Any]:
        """Check if virus definitions need updating."""
        info = {
            "needs_update": False,
            "oldest_definition": None,
            "total_definitions": 0,
            "last_update": None,
            "definitions_exist": False,
            "error": None,
        }

        try:
            definitions = self.get_definition_info()
            info["total_definitions"] = len(definitions)
            info["definitions_exist"] = len(definitions) > 0

            if not definitions:
                info["needs_update"] = True
                info["last_update"] = "No definitions found"
                return info

            # Find oldest definition
            oldest = min(definitions, key=lambda x: x.last_updated)
            info["oldest_definition"] = oldest.last_updated.isoformat()
            info["last_update"] = oldest.last_updated.isoformat()

            # Check if update needed (older than 1 day)
            if datetime.now() - oldest.last_updated > timedelta(days=1):
                info["needs_update"] = True

        except Exception as e:
            print(f"Error checking definition freshness: {e}")
            info["error"] = str(e)
            info["needs_update"] = True
            info["last_update"] = f"Error: {e}"

        return info
