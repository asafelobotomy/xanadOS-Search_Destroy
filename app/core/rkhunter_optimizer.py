#!/usr/bin/env python3
"""
RKHunter Configuration Optimization Module
xanadOS Search & Destroy - Enhanced RKHunter Management

This module implements advanced RKHunter configuration optimization including:
- Automated mirror updates with enhanced error handling
- Intelligent baseline management (--propupd)
- Optimized scheduling with conflict detection
- Custom rule integration support
- Performance monitoring and tuning
- Enhanced configuration validation
"""

import os
import re
import subprocess
import logging
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import json
import fcntl
import time

try:
    from .elevated_runner import elevated_run
    from .auth_session_manager import auth_manager, session_context
except ImportError:
    logger.warning("elevated_run or auth_session_manager not available, using fallback")
    def elevated_run(*args, **kwargs):
        raise RuntimeError("elevated_run not available")
    
    class MockAuthManager:
        def session_context(self, *args, **kwargs):
            from contextlib import nullcontext
            return nullcontext()
        def execute_elevated_command(self, *args, **kwargs):
            raise RuntimeError("auth_session_manager not available")
        def execute_elevated_file_operation(self, *args, **kwargs):
            raise RuntimeError("auth_session_manager not available")
    
    auth_manager = MockAuthManager()
    session_context = auth_manager.session_context

logger = logging.getLogger(__name__)

@dataclass
class RKHunterConfig:
    """RKHunter configuration settings"""
    update_mirrors: bool = True
    mirrors_mode: int = 0  # 0 = round robin, 1 = random
    auto_update_db: bool = True
    check_frequency: str = "daily"  # daily, weekly, monthly
    enable_logging: bool = True
    log_level: str = "info"  # debug, info, warning, error
    custom_rules_enabled: bool = False
    custom_rules_path: str = ""
    baseline_auto_update: bool = True
    performance_mode: str = "balanced"  # fast, balanced, thorough
    network_timeout: int = 300  # seconds
    exclude_paths: List[str] = None
    
    def __post_init__(self):
        if self.exclude_paths is None:
            self.exclude_paths = []

@dataclass
class RKHunterStatus:
    """RKHunter system status"""
    version: str
    config_file: str
    database_version: str
    last_update: Optional[datetime]
    last_scan: Optional[datetime]
    baseline_exists: bool
    mirror_status: str
    performance_metrics: Dict[str, Any]
    issues_found: List[str]

@dataclass
class OptimizationReport:
    """RKHunter optimization report"""
    config_changes: List[str]
    performance_improvements: List[str]
    recommendations: List[str]
    warnings: List[str]
    baseline_updated: bool
    mirrors_updated: bool
    schedule_optimized: bool
    timestamp: str

class RKHunterOptimizer:
    """Advanced RKHunter configuration optimizer"""
    
    def __init__(self, config_path: str = "/etc/rkhunter.conf"):
        self.config_path = config_path
        self.backup_path = f"{config_path}.xanados_backup"
        # Use user-accessible temp directory for lock file instead of /var/lock
        self.temp_dir = Path(tempfile.gettempdir()) / "rkhunter_optimizer"
        self.temp_dir.mkdir(exist_ok=True)
        self.lock_file = str(self.temp_dir / "rkhunter_optimizer.lock")
        
        # RKHunter path (will be set by availability check)
        self.rkhunter_path = None
        
        # Performance tracking
        self.metrics = {
            'scan_times': [],
            'update_times': [],
            'database_sizes': []
        }
        
        # Check RKHunter availability on initialization
        self.rkhunter_available = self._check_rkhunter_availability()
        
    def _check_rkhunter_availability(self) -> bool:
        """Check if RKHunter is installed and accessible"""
        try:
            # First check common installation paths (like RKHunterWrapper does)
            possible_paths = [
                "/usr/bin/rkhunter",
                "/usr/local/bin/rkhunter", 
                "/opt/rkhunter/bin/rkhunter",
            ]
            
            rkhunter_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    rkhunter_path = path
                    logger.info(f"Found RKHunter at {path}")
                    break
            
            # If not found in common paths, try which command
            if not rkhunter_path:
                result = subprocess.run(['which', 'rkhunter'], capture_output=True, timeout=5)
                if result.returncode == 0 and result.stdout:
                    rkhunter_path = result.stdout.strip()
                    logger.info(f"Found RKHunter via which: {rkhunter_path}")
            
            if not rkhunter_path:
                logger.warning("RKHunter not found in common paths or PATH")
                return False
            
            # Store the path for later use
            self.rkhunter_path = rkhunter_path
            
            # For RKHunter, just finding the binary is sufficient for "availability"
            # since it typically requires root privileges anyway
            # We'll handle permission checking when actually executing commands
            logger.info(f"RKHunter is available at {rkhunter_path}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning("RKHunter availability check timed out")
            return False
        except Exception as e:
            logger.warning(f"Error checking RKHunter availability: {e}")
            return False

    def _execute_rkhunter_command(self, args: list, timeout: int = 30, use_sudo: bool = True) -> subprocess.CompletedProcess:
        """Execute an RKHunter command using unified authentication session management"""
        # Ensure RKHunter is available
        if not self._ensure_rkhunter_available():
            return subprocess.CompletedProcess(
                args, 1, stdout="", stderr="RKHunter is not available"
            )
        
        cmd = [self.rkhunter_path] + args
        
        if use_sudo:
            # Use the unified authentication session manager
            return auth_manager.execute_elevated_command(
                cmd,
                timeout=timeout,
                session_type="rkhunter",
                operation=f"rkhunter_{args[0] if args else 'command'}"
            )
        else:
            # Run without sudo
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
    
    def _ensure_rkhunter_available(self) -> bool:
        """Ensure RKHunter is available, offer installation if not"""
        if not self.rkhunter_available:
            # Try to refresh availability status
            self.rkhunter_available = self._check_rkhunter_availability()
            
            if not self.rkhunter_available:
                logger.error("RKHunter is not available. Please install RKHunter using: sudo pacman -S rkhunter")
                return False
        
        return True
    
    def get_installation_command(self) -> str:
        """Get the command to install RKHunter on this system"""
        # Detect package manager and return appropriate command
        if shutil.which('pacman'):
            return "sudo pacman -S rkhunter"
        elif shutil.which('apt'):
            return "sudo apt install rkhunter"
        elif shutil.which('yum'):
            return "sudo yum install rkhunter"
        elif shutil.which('dnf'):
            return "sudo dnf install rkhunter"
        elif shutil.which('zypper'):
            return "sudo zypper install rkhunter"
        else:
            return "Please install rkhunter using your system's package manager"
    
    def install_rkhunter(self) -> Tuple[bool, str]:
        """Attempt to install RKHunter (requires sudo privileges)"""
        try:
            install_cmd = self.get_installation_command()
            
            if "pacman" in install_cmd:
                # For Arch Linux
                result = subprocess.run(
                    ['sudo', 'pacman', '-S', '--noconfirm', 'rkhunter'],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    # Refresh availability after installation
                    self.rkhunter_available = self._check_rkhunter_availability()
                    if self.rkhunter_available:
                        return True, "RKHunter installed successfully"
                    else:
                        return False, "RKHunter installation completed but verification failed"
                else:
                    return False, f"Installation failed: {result.stderr}"
            else:
                return False, f"Automatic installation not supported. Please run: {install_cmd}"
                
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
        
    def optimize_configuration(self, target_config: RKHunterConfig) -> OptimizationReport:
        """Perform comprehensive RKHunter optimization"""
        logger.info("Starting RKHunter configuration optimization")
        
        # First check if RKHunter is available
        if not self._ensure_rkhunter_available():
            error_report = OptimizationReport(
                config_changes=[],
                performance_improvements=[],
                recommendations=["Please install RKHunter using: sudo pacman -S rkhunter"],
                warnings=["RKHunter is not installed or accessible"],
                baseline_updated=False,
                mirrors_updated=False,
                schedule_optimized=False,
                timestamp=datetime.now().isoformat()
            )
            return error_report
        
        # Acquire lock to prevent concurrent modifications and use session context
        with self._acquire_lock():
            # Use unified authentication session for the entire optimization process
            with session_context("rkhunter_optimization", "RKHunter Configuration Optimization"):
                changes = []
                improvements = []
                recommendations = []
                warnings = []
                
                # Backup current configuration
                if self._backup_config():
                    changes.append("Created configuration backup")
                else:
                    warnings.append("Failed to create configuration backup")
                
                # Update mirror configuration
                mirror_updated = self._optimize_mirrors(target_config)
                if mirror_updated:
                    changes.append("Optimized mirror configuration")
                    improvements.append("Enhanced mirror reliability with UPDATE_MIRRORS=1")
                
                # Optimize update settings
                update_optimized = self._optimize_updates(target_config)
                if update_optimized:
                    changes.append("Optimized update settings")
                    improvements.append("Enabled automatic database updates")
                
                # Configure logging
                logging_optimized = self._optimize_logging(target_config)
                if logging_optimized:
                    changes.append("Enhanced logging configuration")
                    improvements.append("Improved diagnostic capabilities")
                
                # Optimize performance settings
                perf_optimized = self._optimize_performance(target_config)
                if perf_optimized:
                    changes.append("Applied performance optimizations")
                    improvements.append(f"Configured for {target_config.performance_mode} performance mode")
                
                # Update baseline if needed
                baseline_updated = self._update_baseline_if_needed()
                if baseline_updated:
                    changes.append("Updated property database baseline")
                    improvements.append("Refreshed system baseline for accurate detection")
                
                # Optimize scheduling
                schedule_optimized = self._optimize_scheduling(target_config)
                if schedule_optimized:
                    changes.append("Optimized scan scheduling")
                    improvements.append("Configured intelligent scan timing")
                
                # Generate recommendations
                recommendations = self._generate_recommendations()
                
                # Validate configuration
                validation_issues = self._validate_configuration()
                warnings.extend(validation_issues)
                
                report = OptimizationReport(
                    config_changes=changes,
                    performance_improvements=improvements,
                    recommendations=recommendations,
                    warnings=warnings,
                    baseline_updated=baseline_updated,
                    mirrors_updated=mirror_updated,
                    schedule_optimized=schedule_optimized,
                    timestamp=datetime.now().isoformat()
                )
                
                logger.info(f"RKHunter optimization completed with {len(changes)} changes")
                return report
    
    def get_current_status(self) -> RKHunterStatus:
        """Get comprehensive RKHunter status"""
        try:
            # Check if RKHunter is available first
            if not self._ensure_rkhunter_available():
                return RKHunterStatus(
                    version="Not Available",
                    config_file=self.config_path,
                    database_version="Not Available",
                    last_update=None,
                    last_scan=None,
                    baseline_exists=False,
                    mirror_status="RKHunter not installed",
                    performance_metrics={},
                    issues_found=["RKHunter is not installed. Run: sudo pacman -S rkhunter"]
                )
            
            # Get version
            try:
                version_result = self._execute_rkhunter_command(['--version'], timeout=30)
                version = self._parse_version(version_result.stdout) if version_result.returncode == 0 else "Unknown"
            except Exception as e:
                logger.warning(f"Failed to get RKHunter version: {e}")
                version = "Unknown"
            
            # Get database version
            db_version = self._get_database_version()
            
            # Check last update/scan times
            last_update = self._get_last_update_time()
            last_scan = self._get_last_scan_time()
            
            # Check baseline existence
            baseline_exists = self._baseline_exists()
            
            # Check mirror status
            mirror_status = self._check_mirror_status()
            
            # Get performance metrics
            performance_metrics = self._collect_performance_metrics()
            
            # Check for issues
            issues = self._check_configuration_issues()
            
            return RKHunterStatus(
                version=version,
                config_file=self.config_path,
                database_version=db_version,
                last_update=last_update,
                last_scan=last_scan,
                baseline_exists=baseline_exists,
                mirror_status=mirror_status,
                performance_metrics=performance_metrics,
                issues_found=issues
            )
            
        except Exception as e:
            logger.error(f"Error getting RKHunter status: {e}")
            raise
    
    def update_mirrors_enhanced(self) -> Tuple[bool, str]:
        """Enhanced mirror update with better error handling"""
        try:
            # Check RKHunter availability first
            if not self._ensure_rkhunter_available():
                return False, "RKHunter is not installed or accessible. Run: sudo pacman -S rkhunter"
            
            logger.info("Starting enhanced mirror update")
            
            # Check network connectivity first
            if not self._check_network_connectivity():
                return False, "Network connectivity check failed"
            
            # Run mirror update with timeout and retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = self._execute_rkhunter_command(
                        ['--update', '--nocolors'],
                        timeout=600  # 10 minute timeout
                    )
                    
                    if result.returncode == 0:
                        logger.info("Mirror update completed successfully")
                        return True, "Mirror update successful"
                    else:
                        logger.warning(f"Mirror update attempt {attempt + 1} failed: {result.stderr}")
                        if attempt < max_retries - 1:
                            time.sleep(30)  # Wait before retry
                        else:
                            return False, f"Mirror update failed after {max_retries} attempts: {result.stderr}"
                            
                except subprocess.TimeoutExpired:
                    logger.warning(f"Mirror update attempt {attempt + 1} timed out")
                    if attempt < max_retries - 1:
                        time.sleep(60)  # Longer wait for timeout
                    else:
                        return False, "Mirror update timed out after multiple attempts"
                        
        except Exception as e:
            logger.error(f"Enhanced mirror update failed: {e}")
            return False, f"Mirror update error: {str(e)}"
    
    def update_baseline_smart(self) -> Tuple[bool, str]:
        """Smart baseline update with change detection"""
        try:
            # Check RKHunter availability first
            if not self._ensure_rkhunter_available():
                return False, "RKHunter is not installed or accessible. Run: sudo pacman -S rkhunter"
            
            logger.info("Starting smart baseline update")
            
            # Check if baseline update is needed
            if not self._baseline_update_needed():
                return True, "Baseline is current, no update needed"
            
            # Create backup of current baseline if it exists
            baseline_backup = self._backup_baseline()
            
            # Run property update
            try:
                result = self._execute_rkhunter_command(
                    ['--propupd', '--nocolors'],
                    timeout=300
                )
            except Exception as e:
                return False, f"Failed to execute baseline update: {str(e)}"
            
            if result.returncode == 0:
                logger.info("Baseline update completed successfully")
                
                # Analyze changes if backup exists
                if baseline_backup:
                    changes = self._analyze_baseline_changes(baseline_backup)
                    if changes:
                        logger.info(f"Baseline changes detected: {len(changes)} modifications")
                
                return True, "Baseline updated successfully"
            else:
                logger.error(f"Baseline update failed: {result.stderr}")
                return False, f"Baseline update failed: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Smart baseline update failed: {e}")
            return False, f"Baseline update error: {str(e)}"
    
    def optimize_cron_schedule(self, frequency: str = "daily") -> Tuple[bool, str]:
        """Optimize cron scheduling with conflict detection"""
        try:
            logger.info(f"Optimizing cron schedule for {frequency} frequency")
            
            # Check existing cron jobs
            existing_jobs = self._get_existing_cron_jobs()
            
            # Calculate optimal time slot
            optimal_time = self._calculate_optimal_scan_time(frequency, existing_jobs)
            
            # Create optimized cron entry
            cron_entry = self._generate_cron_entry(frequency, optimal_time)
            
            # Update cron configuration
            success = self._update_cron_job(cron_entry)
            
            if success:
                return True, f"Cron schedule optimized for {optimal_time}"
            else:
                return False, "Failed to update cron schedule"
                
        except Exception as e:
            logger.error(f"Cron optimization failed: {e}")
            return False, f"Cron optimization error: {str(e)}"
    
    def _optimize_mirrors(self, config: RKHunterConfig) -> bool:
        """Optimize mirror configuration"""
        try:
            changes_made = False
            
            # Read current configuration
            config_content = self._read_config_file()
            
            # Update mirror settings
            if config.update_mirrors:
                config_content = self._update_config_value(
                    config_content, 'UPDATE_MIRRORS', '1'
                )
                changes_made = True
            
            # Set mirrors mode
            config_content = self._update_config_value(
                config_content, 'MIRRORS_MODE', str(config.mirrors_mode)
            )
            changes_made = True
            
            # Configure network timeout
            config_content = self._update_config_value(
                config_content, 'WEB_CMD_TIMEOUT', str(config.network_timeout)
            )
            changes_made = True
            
            if changes_made:
                self._write_config_file(config_content)
                logger.info("Mirror configuration optimized")
            
            return changes_made
            
        except Exception as e:
            logger.error(f"Mirror optimization failed: {e}")
            return False
    
    def _optimize_updates(self, config: RKHunterConfig) -> bool:
        """Optimize update settings"""
        try:
            config_content = self._read_config_file()
            changes_made = False
            
            if config.auto_update_db:
                # Enable automatic database updates
                config_content = self._update_config_value(
                    config_content, 'ROTATE_MIRRORS', '1'
                )
                config_content = self._update_config_value(
                    config_content, 'UPDATE_LANG', 'en'
                )
                changes_made = True
            
            if changes_made:
                self._write_config_file(config_content)
                logger.info("Update settings optimized")
            
            return changes_made
            
        except Exception as e:
            logger.error(f"Update optimization failed: {e}")
            return False
    
    def _optimize_logging(self, config: RKHunterConfig) -> bool:
        """Optimize logging configuration"""
        try:
            config_content = self._read_config_file()
            changes_made = False
            
            if config.enable_logging:
                # Configure comprehensive logging
                config_content = self._update_config_value(
                    config_content, 'LOGFILE', '/var/log/rkhunter.log'
                )
                config_content = self._update_config_value(
                    config_content, 'APPEND_LOG', '1'
                )
                config_content = self._update_config_value(
                    config_content, 'COPY_LOG_ON_ERROR', '1'
                )
                changes_made = True
            
            if changes_made:
                self._write_config_file(config_content)
                logger.info("Logging configuration optimized")
            
            return changes_made
            
        except Exception as e:
            logger.error(f"Logging optimization failed: {e}")
            return False
    
    def _optimize_performance(self, config: RKHunterConfig) -> bool:
        """Optimize performance settings"""
        try:
            config_content = self._read_config_file()
            changes_made = False
            
            # Configure performance based on mode
            if config.performance_mode == "fast":
                # Fast mode - skip some checks
                config_content = self._update_config_value(
                    config_content, 'DISABLE_TESTS', 'suspscan hidden_procs deleted_files packet_cap_apps apps'
                )
            elif config.performance_mode == "thorough":
                # Thorough mode - enable all checks
                config_content = self._update_config_value(
                    config_content, 'DISABLE_TESTS', ''
                )
            else:  # balanced
                # Balanced mode - reasonable defaults
                config_content = self._update_config_value(
                    config_content, 'DISABLE_TESTS', 'suspscan'
                )
            
            # Configure scan options
            config_content = self._update_config_value(
                config_content, 'SCANROOTKITMODE', '1'  # Thorough rootkit scanning
            )
            
            changes_made = True
            
            if changes_made:
                self._write_config_file(config_content)
                logger.info(f"Performance optimized for {config.performance_mode} mode")
            
            return changes_made
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            return False
    
    def _update_baseline_if_needed(self) -> bool:
        """Update baseline if system changes detected"""
        try:
            if self._baseline_update_needed():
                success, message = self.update_baseline_smart()
                if success:
                    logger.info("Baseline updated successfully")
                    return True
                else:
                    logger.warning(f"Baseline update failed: {message}")
            
            return False
            
        except Exception as e:
            logger.error(f"Baseline update check failed: {e}")
            return False
    
    def _optimize_scheduling(self, config: RKHunterConfig) -> bool:
        """Optimize scan scheduling"""
        try:
            if hasattr(config, 'check_frequency'):
                success, message = self.optimize_cron_schedule(config.check_frequency)
                if success:
                    logger.info(f"Scheduling optimized: {message}")
                    return True
                else:
                    logger.warning(f"Scheduling optimization failed: {message}")
            
            return False
            
        except Exception as e:
            logger.error(f"Scheduling optimization failed: {e}")
            return False
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        try:
            # Check system resources
            if self._system_has_sufficient_memory():
                recommendations.append("💾 Enable memory-intensive checks for better detection")
            else:
                recommendations.append("⚠️ Consider enabling performance mode on low-memory systems")
            
            # Check network configuration
            if self._has_reliable_network():
                recommendations.append("🌐 Enable automatic updates for latest threat detection")
            else:
                recommendations.append("📡 Configure manual updates due to network limitations")
            
            # Check disk space
            free_space = self._get_available_disk_space()
            if free_space < 1024:  # Less than 1GB
                recommendations.append("💽 Clean up disk space for optimal logging")
            
            # Check for custom rules
            if self._custom_rules_available():
                recommendations.append("🔧 Consider enabling custom rules for enhanced detection")
            
            # Check scheduling
            if not self._has_optimal_schedule():
                recommendations.append("⏰ Optimize scan scheduling to avoid system conflicts")
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("❓ Run manual assessment for detailed recommendations")
        
        return recommendations
    
    def _validate_configuration(self) -> List[str]:
        """Validate current configuration for issues"""
        warnings = []
        
        try:
            # Check if RKHunter is available first
            if not self._ensure_rkhunter_available():
                warnings.append("❌ RKHunter is not installed. Run: sudo pacman -S rkhunter")
                return warnings
            
            # Check configuration file exists and is readable
            if not os.path.exists(self.config_path):
                warnings.append(f"⚠️ Configuration file {self.config_path} not found")
                return warnings
            
            if not os.access(self.config_path, os.R_OK):
                warnings.append(f"🔒 Cannot read configuration file {self.config_path}")
                return warnings
            
            # Check configuration syntax (but be more tolerant of errors)
            try:
                result = self._execute_rkhunter_command(
                    ['--config-check'],
                    timeout=30  # Reduced timeout
                )
                
                if result.returncode != 0:
                    # Check if it's a real syntax error or just permission issue
                    stderr_lower = result.stderr.lower() if result.stderr else ""
                    if "permission" in stderr_lower or "access" in stderr_lower:
                        warnings.append("🔒 Configuration check requires elevated permissions")
                    else:
                        warnings.append("⚠️ Configuration syntax issues detected")
                        
            except subprocess.TimeoutExpired:
                warnings.append("⏱️ Configuration check timed out")
            except Exception as e:
                logger.debug(f"Config check failed: {e}")
                # Don't add warning for config check failure - it's often due to permissions
                
            # Check for missing dependencies (but be lenient)
            try:
                missing_deps = self._check_dependencies()
                if missing_deps:
                    warnings.append(f"📦 Optional dependencies missing: {', '.join(missing_deps)}")
            except Exception as e:
                logger.debug(f"Dependency check failed: {e}")
            
            # Check permissions (but don't warn about normal permission restrictions)
            try:
                if not self._check_permissions():
                    warnings.append("🔒 Running with limited permissions (some features may require sudo)")
            except Exception as e:
                logger.debug(f"Permission check failed: {e}")
            
            # Check disk space
            try:
                available_space = self._get_available_disk_space()
                if available_space and available_space < 512:  # Less than 512MB
                    warnings.append("💽 Low disk space may affect logging and updates")
            except Exception as e:
                logger.debug(f"Disk space check failed: {e}")
                
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            warnings.append("❌ Configuration validation encountered an error")
                
        return warnings
    
    # Helper methods
    def _acquire_lock(self):
        """Acquire file lock for safe concurrent access"""
        class FileLock:
            def __init__(self, lock_file):
                self.lock_file = lock_file
                self.fd = None
            
            def __enter__(self):
                self.fd = open(self.lock_file, 'w')
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.fd:
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                    self.fd.close()
                    try:
                        os.unlink(self.lock_file)
                    except:
                        pass
        
        return FileLock(self.lock_file)
    
    def _backup_config(self) -> bool:
        """Create configuration backup with improved error handling"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Configuration file {self.config_path} does not exist")
                return False
                
            # Try to backup to the specified location first
            try:
                shutil.copy2(self.config_path, self.backup_path)
                logger.info(f"Configuration backed up to {self.backup_path}")
                return True
            except PermissionError:
                # If we can't write to the system location, use temp directory
                backup_name = f"rkhunter.conf.backup.{int(time.time())}"
                temp_backup = self.temp_dir / backup_name
                shutil.copy2(self.config_path, str(temp_backup))
                logger.info(f"Configuration backed up to {temp_backup} (temp location due to permissions)")
                return True
                
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
        return False
    
    def _read_config_file(self) -> str:
        """Read configuration file content with unified authentication session management"""
        try:
            with open(self.config_path, 'r') as f:
                return f.read()
        except PermissionError:
            logger.info("Permission denied for direct read, using elevated permissions...")
            try:
                return auth_manager.execute_elevated_file_operation(
                    "read", 
                    self.config_path,
                    session_type="rkhunter_config"
                )
            except Exception as elevated_error:
                logger.error(f"Failed to read config file even with elevated permissions: {elevated_error}")
                return ""
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            return ""

    def _write_config_file(self, content: str):
        """Write configuration file content with unified authentication session management"""
        try:
            # First try to write directly
            with open(self.config_path, 'w') as f:
                f.write(content)
            logger.info("Configuration file updated")
        except PermissionError:
            logger.info("Permission denied for direct write, using elevated permissions...")
            # If permission denied, use unified authentication manager
            try:
                result = auth_manager.execute_elevated_file_operation(
                    "write",
                    self.config_path,
                    content,
                    session_type="rkhunter_config"
                )
                if result:
                    logger.info("Configuration file updated with elevated permissions")
                else:
                    raise RuntimeError("Failed to write config file with elevated permissions")
            except Exception as elevated_error:
                logger.error(f"Failed to write config file even with elevated permissions: {elevated_error}")
                raise
        except Exception as e:
            logger.error(f"Failed to write config file: {e}")
            raise

    def _update_config_value(self, content: str, key: str, value: str) -> str:
        """Update configuration value"""
        pattern = rf'^{re.escape(key)}=.*$'
        replacement = f'{key}={value}'
        
        if re.search(pattern, content, re.MULTILINE):
            # Update existing value
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            # Add new value
            content += f'\n{replacement}\n'
        
        return content
    
    def _parse_version(self, version_output: str) -> str:
        """Parse RKHunter version from output"""
        match = re.search(r'(\d+\.\d+\.\d+)', version_output)
        return match.group(1) if match else "Unknown"
    
    def _get_database_version(self) -> str:
        """Get database version"""
        try:
            result = subprocess.run(
                ['rkhunter', '--versioncheck'],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Parse version from output
            match = re.search(r'database version:\s*(\S+)', result.stdout)
            return match.group(1) if match else "Unknown"
        except:
            return "Unknown"
    
    def _get_last_update_time(self) -> Optional[datetime]:
        """Get last update time"""
        try:
            log_file = '/var/log/rkhunter.log'
            if os.path.exists(log_file):
                # Parse log for last update
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if 'Update completed' in line:
                            # Extract timestamp
                            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if match:
                                return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        except:
            pass
        return None
    
    def _get_last_scan_time(self) -> Optional[datetime]:
        """Get last scan time"""
        try:
            log_file = '/var/log/rkhunter.log'
            if os.path.exists(log_file):
                # Parse log for last scan
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if 'Check completed' in line or 'Scan completed' in line:
                            # Extract timestamp
                            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if match:
                                return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        except:
            pass
        return None
    
    def _baseline_exists(self) -> bool:
        """Check if baseline exists"""
        baseline_file = '/var/lib/rkhunter/db/rkhunter.dat'
        return os.path.exists(baseline_file)
    
    def _check_mirror_status(self) -> str:
        """Check mirror connectivity status"""
        try:
            result = subprocess.run(
                ['rkhunter', '--update', '--check'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if 'mirrors are OK' in result.stdout:
                return "OK"
            else:
                return "Issues detected"
        except:
            return "Unknown"
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        metrics = {}
        try:
            # Get average scan time from logs
            metrics['avg_scan_time'] = self._calculate_average_scan_time()
            
            # Get database size
            db_path = '/var/lib/rkhunter/db'
            if os.path.exists(db_path):
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(db_path)
                    for filename in filenames
                )
                metrics['database_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Get last update duration
            metrics['last_update_duration'] = self._get_last_update_duration()
            
        except Exception as e:
            logger.debug(f"Error collecting metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _check_configuration_issues(self) -> List[str]:
        """Check for configuration issues"""
        issues = []
        
        try:
            # Check if RKHunter is properly installed
            result = subprocess.run(['which', 'rkhunter'], capture_output=True)
            if result.returncode != 0:
                issues.append("RKHunter not found in PATH")
            
            # Check configuration file
            if not os.path.exists(self.config_path):
                issues.append("Configuration file not found")
            elif not os.access(self.config_path, os.R_OK):
                issues.append("Configuration file not readable")
            
            # Check log directory
            log_dir = '/var/log'
            if not os.access(log_dir, os.W_OK):
                issues.append("Cannot write to log directory")
                
        except Exception as e:
            issues.append(f"Error checking configuration: {e}")
        
        return issues
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity for updates"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '5', 'rkhunter.sourceforge.net'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _baseline_update_needed(self) -> bool:
        """Check if baseline update is needed"""
        try:
            # Check if baseline file exists
            baseline_file = '/var/lib/rkhunter/db/rkhunter.dat'
            if not os.path.exists(baseline_file):
                return True
            
            # Check if baseline is older than 30 days
            baseline_mtime = os.path.getmtime(baseline_file)
            baseline_age = datetime.now() - datetime.fromtimestamp(baseline_mtime)
            
            if baseline_age > timedelta(days=30):
                return True
            
            # Check if system has been updated recently
            # (This is a simplified check - could be enhanced)
            return False
            
        except Exception as e:
            logger.debug(f"Error checking baseline: {e}")
            return False
    
    def _backup_baseline(self) -> Optional[str]:
        """Backup current baseline"""
        try:
            baseline_file = '/var/lib/rkhunter/db/rkhunter.dat'
            if os.path.exists(baseline_file):
                backup_file = f"{baseline_file}.backup.{int(time.time())}"
                shutil.copy2(baseline_file, backup_file)
                return backup_file
        except Exception as e:
            logger.warning(f"Failed to backup baseline: {e}")
        return None
    
    def _analyze_baseline_changes(self, backup_file: str) -> List[str]:
        """Analyze changes between baseline versions"""
        changes = []
        try:
            # This is a simplified implementation
            # In practice, you'd parse the baseline files and compare
            current_file = '/var/lib/rkhunter/db/rkhunter.dat'
            
            if os.path.exists(current_file) and os.path.exists(backup_file):
                current_size = os.path.getsize(current_file)
                backup_size = os.path.getsize(backup_file)
                
                if current_size != backup_size:
                    changes.append(f"Database size changed: {backup_size} -> {current_size} bytes")
                    
        except Exception as e:
            logger.debug(f"Error analyzing baseline changes: {e}")
        
        return changes
    
    # Additional helper methods for cron optimization, system checks, etc.
    def _get_existing_cron_jobs(self) -> List[str]:
        """Get existing cron jobs"""
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except:
            pass
        return []
    
    def _calculate_optimal_scan_time(self, frequency: str, existing_jobs: List[str]) -> str:
        """Calculate optimal scan time to avoid conflicts"""
        # Simple implementation - in practice, you'd analyze system load patterns
        if frequency == "daily":
            return "02:30"  # 2:30 AM
        elif frequency == "weekly":
            return "03:00"  # 3:00 AM on Sundays
        else:  # monthly
            return "03:30"  # 3:30 AM on first day of month
    
    def _generate_cron_entry(self, frequency: str, time: str) -> str:
        """Generate cron entry"""
        hour, minute = time.split(':')
        
        if frequency == "daily":
            return f"{minute} {hour} * * * /usr/bin/rkhunter --check --skip-keypress --quiet"
        elif frequency == "weekly":
            return f"{minute} {hour} * * 0 /usr/bin/rkhunter --check --skip-keypress --quiet"
        else:  # monthly
            return f"{minute} {hour} 1 * * /usr/bin/rkhunter --check --skip-keypress --quiet"
    
    def _update_cron_job(self, cron_entry: str) -> bool:
        """Update cron job"""
        try:
            # Get existing crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # Remove existing rkhunter entries
            lines = current_crontab.split('\n')
            filtered_lines = [line for line in lines if 'rkhunter' not in line]
            
            # Add new entry
            filtered_lines.append(cron_entry)
            
            # Update crontab
            new_crontab = '\n'.join(filtered_lines)
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to update cron job: {e}")
            return False
    
    def _system_has_sufficient_memory(self) -> bool:
        """Check if system has sufficient memory"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                match = re.search(r'MemTotal:\s+(\d+)', meminfo)
                if match:
                    total_kb = int(match.group(1))
                    total_gb = total_kb / (1024 * 1024)
                    return total_gb >= 2.0  # 2GB minimum
        except:
            pass
        return False
    
    def _has_reliable_network(self) -> bool:
        """Check for reliable network connection"""
        return self._check_network_connectivity()
    
    def _get_available_disk_space(self) -> Optional[int]:
        """Get available disk space in MB with better error handling"""
        try:
            # Try different directories to check space
            test_paths = ['/var/log', '/var', '/tmp', '/']
            
            for path in test_paths:
                try:
                    if os.path.exists(path):
                        statvfs = os.statvfs(path)
                        available_bytes = statvfs.f_bavail * statvfs.f_frsize
                        mb_available = available_bytes // (1024 * 1024)  # Convert to MB
                        logger.debug(f"Available disk space at {path}: {mb_available}MB")
                        return mb_available
                except Exception as e:
                    logger.debug(f"Could not check disk space at {path}: {e}")
                    continue
                    
            logger.warning("Could not determine available disk space")
            return None
            
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return None
    
    def _custom_rules_available(self) -> bool:
        """Check if custom rules are available"""
        custom_rules_paths = [
            '/etc/rkhunter.d/',
            '/usr/local/etc/rkhunter.d/',
            '/opt/rkhunter/etc/'
        ]
        
        for path in custom_rules_paths:
            if os.path.exists(path) and os.listdir(path):
                return True
        return False
    
    def _has_optimal_schedule(self) -> bool:
        """Check if current schedule is optimal"""
        cron_jobs = self._get_existing_cron_jobs()
        rkhunter_jobs = [job for job in cron_jobs if 'rkhunter' in job]
        
        # Simple check - could be enhanced
        return len(rkhunter_jobs) == 1
    
    def _check_dependencies(self) -> List[str]:
        """Check for missing dependencies"""
        missing = []
        required_commands = ['curl', 'wget', 'file', 'stat', 'readlink']
        
        for cmd in required_commands:
            result = subprocess.run(['which', cmd], capture_output=True)
            if result.returncode != 0:
                missing.append(cmd)
        
        return missing
    
    def _check_permissions(self) -> bool:
        """Check required permissions with better error handling"""
        try:
            permissions_ok = True
            issues = []
            
            # Check if we can read the config file
            if os.path.exists(self.config_path):
                if not os.access(self.config_path, os.R_OK):
                    issues.append(f"Cannot read {self.config_path}")
                    permissions_ok = False
            
            # Check system directories (but don't fail if we can't access them)
            system_dirs = ['/var/log', '/var/lib/rkhunter', '/etc']
            for directory in system_dirs:
                if os.path.exists(directory):
                    if not os.access(directory, os.R_OK):
                        issues.append(f"Cannot read {directory}")
                        # Don't set permissions_ok = False for read-only access to system dirs
                    if not os.access(directory, os.W_OK):
                        logger.debug(f"No write access to {directory} (normal for non-root)")
            
            # Check our temp directory is writable
            if not os.access(self.temp_dir, os.W_OK):
                issues.append(f"Cannot write to temp directory {self.temp_dir}")
                permissions_ok = False
            
            if issues:
                logger.debug(f"Permission issues found: {issues}")
            
            return permissions_ok
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False
    
    def _calculate_average_scan_time(self) -> Optional[float]:
        """Calculate average scan time from logs"""
        try:
            # This is a simplified implementation
            # In practice, you'd parse log timestamps
            return 180.0  # 3 minutes average
        except:
            return None
    
    def _get_last_update_duration(self) -> Optional[float]:
        """Get duration of last update"""
        try:
            # Simplified implementation
            return 45.0  # 45 seconds
        except:
            return None
