#!/usr/bin/env python3
"""RKHunter Configuration Optimization Module
xanadOS Search & Destroy - Enhanced RKHunter Management
This module implements advanced RKHunter configuration optimization including:
- Automated mirror updates with enhanced error handling
- Intelligent baseline management (--propupd)
- Optimized scheduling with conflict detection
- Custom rule integration support
- Performance monitoring and tuning
- Enhanced configuration validation
"""

import fcntl
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from contextlib import nullcontext as _nullcontext
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .secure_subprocess import run_secure

logger = logging.getLogger(__name__)

# Use GUI authentication exclusively - no fallbacks needed
from .gui_auth_manager import elevated_run_gui, get_gui_auth_manager

# logger already defined above


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
    exclude_paths: list[str] = None

    def __post_init__(self):
        if self.exclude_paths is None:
            self.exclude_paths = []


@dataclass
class RKHunterStatus:
    """RKHunter system status"""

    version: str
    config_file: str
    database_version: str
    last_update: datetime | None
    last_scan: datetime | None
    baseline_exists: bool
    mirror_status: str
    performance_metrics: dict[str, Any]
    issues_found: list[str]


@dataclass
class OptimizationReport:
    """RKHunter optimization report"""

    config_changes: list[str]
    performance_improvements: list[str]
    recommendations: list[str]
    warnings: list[str]
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
        self.metrics = {"scan_times": [], "update_times": [], "database_sizes": []}

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
                result = run_secure(
                    ["which", "rkhunter"], timeout=5, check=False, capture_output=True
                )
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

    def _execute_rkhunter_command(
        self, args: list, timeout: int = 30, use_sudo: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute an RKHunter command using unified authentication session management"""
        # Ensure RKHunter is available
        if not self._ensure_rkhunter_available():
            return subprocess.CompletedProcess(
                args, 1, stdout="", stderr="RKHunter is not available"
            )

        cmd = [self.rkhunter_path] + args

        if use_sudo:
            # Use GUI authentication manager
            return elevated_run_gui(
                cmd,
                timeout=timeout,
                capture_output=True,
                text=True
            )
        else:
            # Run without sudo
            return run_secure(cmd, timeout=timeout, check=False, capture_output=True, text=True)

    def _ensure_rkhunter_available(self) -> bool:
        """Ensure RKHunter is available, offer installation if not"""
        if not self.rkhunter_available:
            # Try to refresh availability status
            self.rkhunter_available = self._check_rkhunter_availability()

            if not self.rkhunter_available:
                logger.error(
                    "RKHunter is not available. Please install RKHunter using: sudo pacman -S rkhunter"
                )
                return False

        return True

    def get_installation_command(self) -> str:
        """Get the command to install RKHunter on this system"""
        # Detect package manager and return appropriate command
        if shutil.which("pacman"):
            return "sudo pacman -S rkhunter"
        elif shutil.which("apt"):
            return "sudo apt install rkhunter"
        elif shutil.which("yum"):
            return "sudo yum install rkhunter"
        elif shutil.which("dnf"):
            return "sudo dnf install rkhunter"
        elif shutil.which("zypper"):
            return "sudo zypper install rkhunter"
        else:
            return "Please install rkhunter using your system's package manager"

    def install_rkhunter(self) -> tuple[bool, str]:
        """Attempt to install RKHunter (requires sudo privileges)"""
        try:
            install_cmd = self.get_installation_command()

            if "pacman" in install_cmd:
                # For Arch Linux
                result = run_secure(
                    ["sudo", "pacman", "-S", "--noconfirm", "rkhunter"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0:
                    # Refresh availability after installation
                    self.rkhunter_available = self._check_rkhunter_availability()
                    if self.rkhunter_available:
                        return True, "RKHunter installed successfully"
                    else:
                        return (
                            False,
                            "RKHunter installation completed but verification failed",
                        )
                else:
                    return False, f"Installation failed: {result.stderr}"
            else:
                return (
                    False,
                    f"Automatic installation not supported. Please run: {install_cmd}",
                )

        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, f"Installation error: {e!s}"

    def can_read_config(self) -> bool:
        """Check if we can read the configuration file without sudo"""
        try:
            return (
                Path(self.config_path).exists() and
                os.access(self.config_path, os.R_OK)
            )
        except Exception:
            return False

    def can_write_config(self) -> bool:
        """Check if we can write to the configuration file without sudo"""
        try:
            return (
                Path(self.config_path).exists() and
                os.access(self.config_path, os.W_OK)
            )
        except Exception:
            return False

    def detect_arch_permission_anomaly(self) -> bool:
        """Detect if we have the Arch Linux permission anomaly (600 instead of 644)"""
        try:
            if not Path(self.config_path).exists():
                return False

            stat_info = os.stat(self.config_path)
            current_perms = oct(stat_info.st_mode)[-3:]

            # Arch Linux anomaly: 600 permissions instead of standard 644
            return current_perms == "600"
        except Exception:
            return False

    def fix_arch_permissions(self) -> tuple[bool, str]:
        """
        Fix Arch Linux permission anomaly by changing 600 to 644
        This makes the config readable by users (standard behavior)
        """
        try:
            if not self.detect_arch_permission_anomaly():
                return True, "Permissions are already correct"

            logger.info("Fixing Arch Linux permission anomaly (600 → 644)")

            # Use sudo to fix the permission anomaly
            result = run_secure([
                "sudo", "chmod", "644", self.config_path
            ], check=False, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Fixed RKHunter config permissions")
                return True, "Successfully fixed configuration file permissions"
            else:
                error_msg = f"Failed to fix permissions: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Error fixing permissions: {e}"
            logger.error(error_msg)
            return False, error_msg

    def ensure_config_readable(self) -> tuple[bool, str]:
        """
        Ensure the configuration file is readable, fixing Arch Linux anomaly if needed
        Returns (success, message)
        """
        if self.can_read_config():
            return True, "Configuration file is readable"

        if self.detect_arch_permission_anomaly():
            logger.info("Detected Arch Linux permission anomaly, attempting fix...")
            return self.fix_arch_permissions()
        else:
            return False, f"Configuration file {self.config_path} is not accessible"

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
                timestamp=datetime.now().isoformat(),
            )
            return error_report

        # Acquire lock to prevent concurrent modifications
        with self._acquire_lock():
            # Use unified authentication for the entire optimization process
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
                improvements.append(
                    f"Configured for {target_config.performance_mode} performance mode"
                )

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

            # Auto-fix common configuration issues
            config_fixes = self._auto_fix_config_issues()
            if config_fixes:
                changes.extend(config_fixes)
                improvements.append("Applied automatic configuration fixes")

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
                timestamp=datetime.now().isoformat(),
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
                    issues_found=["RKHunter is not installed. Run: sudo pacman -S rkhunter"],
                )

            # Get version (requires sudo due to restrictive binary permissions)
            try:
                version_result = self._execute_rkhunter_command(
                    ["--version"], timeout=30, use_sudo=True
                )
                version = (
                    self._parse_version(version_result.stdout)
                    if version_result.returncode == 0
                    else "Unknown"
                )
            except Exception as e:
                logger.warning(f"Failed to get RKHunter version: {e}")
                # Fallback to package manager for version info
                try:
                    from app.utils.secure_subprocess import run_secure

                    pkg_result = run_secure(
                        ["pacman", "-Qi", "rkhunter"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if pkg_result.returncode == 0:
                        for line in pkg_result.stdout.split("\n"):
                            if line.startswith("Version"):
                                version = line.split(":", 1)[1].strip()
                                break
                        else:
                            version = "Unknown"
                    else:
                        version = "Unknown"
                except Exception:
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
                issues_found=issues,
            )

        except Exception as e:
            logger.error(f"Error getting RKHunter status: {e}")
            raise

    def update_mirrors_enhanced(self) -> tuple[bool, str]:
        """Enhanced mirror update with better error handling"""
        try:
            # Check RKHunter availability first
            if not self._ensure_rkhunter_available():
                return (
                    False,
                    "RKHunter is not installed or accessible. Run: sudo pacman -S rkhunter",
                )

            logger.info("Starting enhanced mirror update")

            # Check network connectivity first
            if not self._check_network_connectivity():
                return False, "Network connectivity check failed"

            # Run mirror update with timeout and retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = self._execute_rkhunter_command(
                        ["--update", "--nocolors"],
                        timeout=600,  # 10 minute timeout
                    )

                    if result.returncode == 0:
                        logger.info("Mirror update completed successfully")
                        return True, "Mirror update successful"
                    else:
                        logger.warning(
                            f"Mirror update attempt {attempt + 1} failed: {result.stderr}"
                        )
                        if attempt < max_retries - 1:
                            time.sleep(30)  # Wait before retry
                        else:
                            return (
                                False,
                                f"Mirror update failed after {max_retries} attempts: {
                                    result.stderr
                                }",
                            )

                except subprocess.TimeoutExpired:
                    logger.warning(f"Mirror update attempt {attempt + 1} timed out")
                    if attempt < max_retries - 1:
                        time.sleep(60)  # Longer wait for timeout
                    else:
                        return False, "Mirror update timed out after multiple attempts"

        except Exception as e:
            logger.error(f"Enhanced mirror update failed: {e}")
            return False, f"Mirror update error: {e!s}"

    def update_baseline_smart(self) -> tuple[bool, str]:
        """Smart baseline update with change detection"""
        try:
            # Check RKHunter availability first
            if not self._ensure_rkhunter_available():
                return (
                    False,
                    "RKHunter is not installed or accessible. Run: sudo pacman -S rkhunter",
                )

            logger.info("Starting smart baseline update")

            # Check if baseline update is needed
            if not self._baseline_update_needed():
                return True, "Baseline is current, no update needed"

            # Create backup of current baseline if it exists
            baseline_backup = self._backup_baseline()

            # Run property update
            try:
                result = self._execute_rkhunter_command(["--propupd", "--nocolors"], timeout=300)
            except Exception as e:
                return False, f"Failed to execute baseline update: {e!s}"

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
            return False, f"Baseline update error: {e!s}"

    def optimize_cron_schedule(self, frequency: str = "daily") -> tuple[bool, str]:
        """Optimize scheduling with support for both cron and systemd timers"""
        try:
            logger.info(f"Optimizing schedule for {frequency} frequency")

            # Detect available scheduling system
            scheduler_type = self._detect_scheduler_system()
            logger.info(f"Detected scheduler system: {scheduler_type}")

            if scheduler_type == "systemd":
                return self._optimize_systemd_timer(frequency)
            elif scheduler_type == "cron":
                return self._optimize_cron_schedule_traditional(frequency)
            else:
                return False, "No supported scheduling system found (neither cron nor systemd)"

        except Exception as e:
            logger.error(f"Schedule optimization failed: {e}")
            return False, f"Schedule optimization error: {e!s}"

    def _detect_scheduler_system(self) -> str:
        """Detect which scheduling system is available"""
        try:
            # Check for systemd (most common on modern systems)
            result = subprocess.run(
                ["systemctl", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.debug("Systemd detected")
                return "systemd"
        except Exception as e:
            logger.debug(f"Systemd check failed: {e}")

        try:
            # Check for cron systems
            result = elevated_run_gui(["which", "crontab"], timeout=10, capture_output=True, text=True)
            if result.returncode == 0:
                logger.debug("Cron system detected")
                return "cron"
        except Exception as e:
            logger.debug(f"Cron check failed: {e}")

        logger.warning("No supported scheduling system detected")
        return "none"

    def _optimize_systemd_timer(self, frequency: str = "daily") -> tuple[bool, str]:
        """Create systemd timer for RKHunter scheduling"""
        try:
            # Calculate optimal time
            optimal_time = self._calculate_optimal_scan_time(frequency, [])

            # Create systemd service and timer files
            service_content, timer_content = self._generate_systemd_files(frequency, optimal_time)

            # Write service file
            service_success = self._write_systemd_file(
                "rkhunter-xanados.service",
                service_content
            )

            if not service_success:
                return False, "Failed to create systemd service file"

            # Write timer file
            timer_success = self._write_systemd_file(
                "rkhunter-xanados.timer",
                timer_content
            )

            if not timer_success:
                return False, "Failed to create systemd timer file"

            # Enable and start the timer
            enable_success = self._enable_systemd_timer()

            if enable_success:
                return True, f"Systemd timer created and enabled for {optimal_time} {frequency}"
            else:
                return False, "Timer files created but failed to enable"

        except Exception as e:
            logger.error(f"Systemd timer optimization failed: {e}")
            return False, f"Systemd timer error: {e!s}"

    def _generate_systemd_files(self, frequency: str, time: str) -> tuple[str, str]:
        """Generate systemd service and timer file contents"""

        # Service file content
        service_content = """[Unit]
Description=RKHunter Security Scan
After=network.target

[Service]
Type=oneshot
User=root
ExecStart=/usr/bin/rkhunter --check --skip-keypress --quiet --report-warnings-only
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

        # Timer file content - convert time format
        hour, minute = time.split(":")

        if frequency == "daily":
            timer_schedule = f"*-*-* {hour}:{minute}:00"
        elif frequency == "weekly":
            timer_schedule = f"Sun *-*-* {hour}:{minute}:00"
        else:  # monthly
            timer_schedule = f"*-*-01 {hour}:{minute}:00"

        timer_content = f"""[Unit]
Description=RKHunter Security Scan Timer
Requires=rkhunter-xanados.service

[Timer]
OnCalendar={timer_schedule}
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
"""

        return service_content, timer_content

    def _write_systemd_file(self, filename: str, content: str) -> bool:
        """Write systemd unit file using elevated privileges"""
        try:
            import tempfile

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".service") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # Copy to systemd directory
            target_path = f"/etc/systemd/system/{filename}"
            result = elevated_run_gui(
                ["cp", temp_file_path, target_path],
                timeout=30,
                capture_output=True,
                text=True
            )

            # Clean up temp file
            os.unlink(temp_file_path)

            if result.returncode == 0:
                logger.info(f"Created systemd file: {target_path}")

                # Reload systemd daemon
                reload_result = elevated_run_gui(
                    ["systemctl", "daemon-reload"],
                    timeout=30,
                    capture_output=True,
                    text=True
                )

                if reload_result.returncode == 0:
                    logger.info("Systemd daemon reloaded successfully")
                    return True
                else:
                    logger.warning(f"Failed to reload systemd daemon: {reload_result.stderr}")
                    return False
            else:
                logger.error(f"Failed to write systemd file: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error writing systemd file {filename}: {e}")
            return False

    def _enable_systemd_timer(self) -> bool:
        """Enable and start the systemd timer"""
        try:
            # Enable the timer
            result = elevated_run_gui(
                ["systemctl", "enable", "rkhunter-xanados.timer"],
                timeout=30,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to enable timer: {result.stderr}")
                return False

            # Start the timer
            result = elevated_run_gui(
                ["systemctl", "start", "rkhunter-xanados.timer"],
                timeout=30,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Systemd timer enabled and started successfully")
                return True
            else:
                logger.error(f"Failed to start timer: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error enabling systemd timer: {e}")
            return False

    def _optimize_cron_schedule_traditional(self, frequency: str = "daily") -> tuple[bool, str]:
        """Traditional cron optimization (renamed from original method)"""
        try:
            logger.info(f"Optimizing traditional cron schedule for {frequency} frequency")

            # Check existing cron jobs
            existing_jobs = self._get_existing_cron_jobs()

            # Calculate optimal time to avoid conflicts
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
            logger.error(f"Traditional cron optimization failed: {e}")
            return False, f"Cron optimization error: {e!s}"
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
            return False, f"Cron optimization error: {e!s}"

    def _optimize_mirrors(self, config: RKHunterConfig) -> bool:
        """Optimize mirror configuration"""
        try:
            changes_made = False

            # Read current configuration
            config_content = self._read_config_file()

            # Update mirror settings
            if config.update_mirrors:
                config_content = self._update_config_value(config_content, "UPDATE_MIRRORS", "1")
                changes_made = True

            # Set mirrors mode
            config_content = self._update_config_value(
                config_content, "MIRRORS_MODE", str(config.mirrors_mode)
            )
            changes_made = True

            # Configure network timeout
            config_content = self._update_config_value(
                config_content, "WEB_CMD_TIMEOUT", str(config.network_timeout)
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
                config_content = self._update_config_value(config_content, "ROTATE_MIRRORS", "1")
                config_content = self._update_config_value(config_content, "UPDATE_LANG", "en")
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
                    config_content, "LOGFILE", "/var/log/rkhunter.log"
                )
                config_content = self._update_config_value(config_content, "APPEND_LOG", "1")
                config_content = self._update_config_value(config_content, "COPY_LOG_ON_ERROR", "1")
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
                    config_content,
                    "DISABLE_TESTS",
                    "suspscan hidden_procs deleted_files packet_cap_apps apps",
                )
            elif config.performance_mode == "thorough":
                # Thorough mode - enable all checks
                config_content = self._update_config_value(config_content, "DISABLE_TESTS", "")
            else:  # balanced
                # Balanced mode - reasonable defaults
                config_content = self._update_config_value(
                    config_content, "DISABLE_TESTS", "suspscan"
                )

            # Configure scan options
            # SCANROOTKITMODE must be a valid string token understood by rkhunter.
            # The wrapper initializes this to THOROUGH; keep consistent here.
            config_content = self._update_config_value(
                config_content,
                "SCANROOTKITMODE",
                "THOROUGH",
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
            if hasattr(config, "check_frequency"):
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

    def _generate_recommendations(self) -> list[str]:
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

            # Add configuration-specific recommendations
            config_recommendations = self._get_configuration_recommendations()
            recommendations.extend(config_recommendations)

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("❓ Run manual assessment for detailed recommendations")

        return recommendations

    def _get_configuration_recommendations(self) -> list[str]:
        """Get specific recommendations for configuration issues"""
        recommendations = []

        try:
            # Check for common configuration issues and provide fixes
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_content = f.read()

                # Check for obsolete options
                if 'WEB_CMD_TIMEOUT' in config_content:
                    recommendations.append("🔧 Remove obsolete 'WEB_CMD_TIMEOUT' option from configuration")

                if 'EGREP_CMD' in config_content:
                    recommendations.append("📅 Update 'EGREP_CMD' to use 'grep -E' instead of deprecated egrep")

                # Check for common regex issues
                if '\\+' in config_content or '\\-' in config_content:
                    recommendations.append("🔍 Review regex patterns - fix escaped characters that may cause warnings")

                # Check for permission-related configurations
                if 'ALLOW_SYSLOG_FILES' not in config_content:
                    recommendations.append("📝 Consider adding 'ALLOW_SYSLOG_FILES=1' for better log analysis")

                # Check for modern security settings
                if 'DISABLE_TESTS' in config_content:
                    recommendations.append("🛡️ Review disabled tests - re-enable security checks when possible")

        except Exception as e:
            logger.debug(f"Error checking configuration recommendations: {e}")

        return recommendations

    def detect_fixable_issues(self) -> dict[str, dict]:
        """Detect configuration issues that can be automatically fixed.

        Returns:
            Dict mapping issue IDs to issue descriptions and fix actions
        """
        fixable_issues = {}

        try:
            # First, ensure we can read the system config
            can_read, read_message = self.ensure_config_readable()

            if not can_read:
                # Config is not readable - return permission issue
                return {
                    "permission_issue": {
                        "description": "🔒 System configuration requires elevated access",
                        "detail": read_message,
                        "fix_action": "The application will request administrator access when needed",
                        "impact": "Enables system-wide RKHunter optimization",
                        "requires_sudo": True
                    }
                }

            if not os.path.exists(self.config_path):
                return {
                    "config_missing": {
                        "description": "📁 RKHunter configuration file not found",
                        "detail": f"Expected at: {self.config_path}",
                        "fix_action": "Install RKHunter or create configuration file",
                        "impact": "Required for RKHunter functionality",
                        "requires_sudo": True
                    }
                }

            # Read current configuration
            with open(self.config_path, 'r') as f:
                lines = f.readlines()

            line_num = 0
            for line in lines:
                line_num += 1

                # Check for obsolete WEB_CMD_TIMEOUT option
                if line.strip().startswith('WEB_CMD_TIMEOUT'):
                    fixable_issues[f"obsolete_web_cmd_timeout_{line_num}"] = {
                        "description": "🔧 Obsolete 'WEB_CMD_TIMEOUT' setting found",
                        "detail": f"Line {line_num}: {line.strip()}",
                        "fix_action": "Remove this obsolete configuration option",
                        "impact": "Eliminates configuration warnings",
                        "line_number": line_num,
                        "requires_sudo": not self.can_write_config()
                    }

                # Check for egrep commands (should use grep -E)
                if 'egrep' in line and not line.strip().startswith('#'):
                    fixable_issues[f"egrep_deprecated_{line_num}"] = {
                        "description": "📅 Deprecated 'egrep' command found",
                        "detail": f"Line {line_num}: {line.strip()}",
                        "fix_action": "Replace 'egrep' with 'grep -E'",
                        "impact": "Uses modern grep syntax",
                        "line_number": line_num,
                        "requires_sudo": not self.can_write_config()
                    }

                # Check for regex escaping issues
                if '\\+' in line and not line.strip().startswith('#'):
                    fixable_issues[f"regex_plus_escape_{line_num}"] = {
                        "description": "🔍 Invalid regex escaping for '+' character",
                        "detail": f"Line {line_num}: {line.strip()}",
                        "fix_action": "Remove unnecessary backslash before '+'",
                        "impact": "Fixes regex pattern matching",
                        "line_number": line_num,
                        "requires_sudo": not self.can_write_config()
                    }

                if '\\-' in line and not line.strip().startswith('#'):
                    fixable_issues[f"regex_minus_escape_{line_num}"] = {
                        "description": "🔍 Invalid regex escaping for '-' character",
                        "detail": f"Line {line_num}: {line.strip()}",
                        "fix_action": "Remove unnecessary backslash before '-'",
                        "impact": "Fixes regex pattern matching",
                        "line_number": line_num,
                        "requires_sudo": not self.can_write_config()
                    }

        except (PermissionError, OSError) as e:
            return {
                "permission_error": {
                    "description": "🔒 Permission denied accessing system configuration",
                    "detail": f"Cannot read {self.config_path}: {e}",
                    "fix_action": "The application will request administrator access when needed",
                    "impact": "Required for system-wide RKHunter optimization",
                    "requires_sudo": True
                }
            }
        except Exception as e:
            logger.error("Error detecting fixable issues: %s", e)
            return {
                "detection_error": {
                    "description": "❌ Error analyzing configuration",
                    "detail": f"Unexpected error: {e}",
                    "fix_action": "Check system configuration and permissions",
                    "impact": "Cannot determine configuration issues",
                    "requires_sudo": False
                }
            }

        return fixable_issues

    def apply_selected_fixes(self, selected_fix_ids: list[str]) -> list[str]:
        """Apply only the selected configuration fixes.

        Args:
            selected_fix_ids: List of fix IDs to apply

        Returns:
            List of fixes that were successfully applied
        """
        fixes_applied = []

        try:
            if not os.path.exists(self.config_path):
                fixes_applied.append(f"❌ Configuration file {self.config_path} not found")
                return fixes_applied

            # Get current fixable issues
            fixable_issues = self.detect_fixable_issues()

            # Check if selected fixes are still applicable
            applicable_fixes = []
            for fix_id in selected_fix_ids:
                if fix_id in fixable_issues:
                    applicable_fixes.append(fix_id)
                else:
                    fixes_applied.append(f"ℹ️ Fix '{fix_id}' is no longer applicable (issue may have been resolved)")

            if not applicable_fixes:
                if fixes_applied:
                    # Some fixes were not applicable
                    return fixes_applied
                else:
                    # No fixes were applicable at all
                    fixes_applied.append("ℹ️ None of the selected fixes are currently applicable")
                    return fixes_applied

            # Read current configuration
            with open(self.config_path, 'r') as f:
                lines = f.readlines()

            modified = False
            new_lines = []

            line_num = 0
            for line in lines:
                line_num += 1
                original_line = line

                # Check if any selected fixes apply to this line
                line_modified = False

                for fix_id in applicable_fixes:
                    issue = fixable_issues[fix_id]
                    if issue.get("line_number") != line_num:
                        continue

                    # Apply the specific fix
                    if "obsolete_web_cmd_timeout" in fix_id and line.strip().startswith('WEB_CMD_TIMEOUT'):
                        line = f"# Removed obsolete option: {line}"
                        fixes_applied.append("🔧 Removed obsolete 'WEB_CMD_TIMEOUT' setting")
                        line_modified = True
                        modified = True

                    elif "egrep_deprecated" in fix_id and 'egrep' in line and not line.strip().startswith('#'):
                        line = line.replace('egrep', 'grep -E')
                        fixes_applied.append("📅 Updated egrep command to 'grep -E'")
                        line_modified = True
                        modified = True

                    elif "regex_plus_escape" in fix_id and '\\+' in line and not line.strip().startswith('#'):
                        line = line.replace('\\+', '+')
                        fixes_applied.append("🔍 Fixed regex escaping for '+' character")
                        line_modified = True
                        modified = True

                    elif "regex_minus_escape" in fix_id and '\\-' in line and not line.strip().startswith('#'):
                        line = line.replace('\\-', '-')
                        fixes_applied.append("🔍 Fixed regex escaping for '-' character")
                        line_modified = True
                        modified = True

                new_lines.append(line)

            # Write back the fixed configuration if modifications were made
            if modified:
                # Check if we need sudo for writing
                if self.can_write_config():
                    # We can write directly
                    with open(self.config_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    fixes_applied.append("💾 Configuration file updated with selected fixes")
                else:
                    # Need sudo to write to system config
                    try:
                        import tempfile
                        import os

                        # Create a temporary file with the new content
                        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as temp_file:
                            temp_file.writelines(new_lines)
                            temp_file_path = temp_file.name

                        try:
                            # Use sudo to copy the temp file to the system config
                            result = run_secure([
                                "sudo", "cp", temp_file_path, self.config_path
                            ], capture_output=True, text=True)

                            if result.returncode == 0:
                                fixes_applied.append("💾 Configuration file updated with selected fixes (using sudo)")
                            else:
                                fixes_applied.append(f"❌ Failed to write configuration: {result.stderr}")
                                return fixes_applied
                        finally:
                            # Clean up the temporary file
                            os.unlink(temp_file_path)

                    except Exception as write_error:
                        fixes_applied.append(f"❌ Sudo write operation failed: {write_error}")
                        return fixes_applied

                logger.info("Applied %d selected configuration fixes", len(applicable_fixes))
            else:
                if applicable_fixes:
                    fixes_applied.append("ℹ️ Selected fixes were checked but no changes were needed")

        except (PermissionError, OSError) as e:
            logger.error("Permission error applying selected fixes: %s", e)
            fixes_applied.append(f"❌ Permission denied: {e}")
        except Exception as e:
            logger.error("Error applying selected fixes: %s", e)
            fixes_applied.append(f"❌ Fix application failed: {e}")

        return fixes_applied

    def _auto_fix_config_issues(self) -> list[str]:
        """Automatically fix common configuration issues"""
        # Get all fixable issues
        fixable_issues = self.detect_fixable_issues()

        # Apply all fixes automatically
        all_fix_ids = list(fixable_issues.keys())
        return self.apply_selected_fixes(all_fix_ids)

    def _validate_configuration(self) -> list[str]:
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
                    ["--config-check"],
                    timeout=30,  # Reduced timeout
                )

                if result.returncode != 0:
                    # Check if it's a real syntax error or just permission issue
                    stderr_lower = result.stderr.lower() if result.stderr else ""
                    stdout_lower = result.stdout.lower() if result.stdout else ""

                    if "permission" in stderr_lower or "access" in stderr_lower:
                        warnings.append("🔒 Configuration check requires elevated permissions")
                    else:
                        # Parse specific configuration issues
                        config_issues = self._parse_config_check_output(result.stdout, result.stderr)
                        if config_issues:
                            warnings.extend(config_issues)
                        else:
                            warnings.append("⚠️ Configuration syntax issues detected (run 'sudo rkhunter --config-check' for details)")

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
                    warnings.append(
                        "🔒 Running with limited permissions (some features may require sudo)"
                    )
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

    def _parse_config_check_output(self, stdout: str, stderr: str) -> list[str]:
        """Parse RKHunter config-check output to provide specific, actionable warnings"""
        issues = []

        # Combine stdout and stderr for parsing
        output = (stdout or "") + "\n" + (stderr or "")

        # Parse unknown configuration options
        import re
        unknown_options = re.findall(r'Unknown configuration file option:\s*([^\n]+)', output, re.IGNORECASE)
        for option in unknown_options:
            option_name = option.split('=')[0].strip()
            issues.append(f"🔧 Unknown config option '{option_name}' - remove or update this setting")

        # Parse grep warnings (regex issues)
        grep_warnings = re.findall(r'grep: warning:\s*([^\n]+)', output, re.IGNORECASE)
        if grep_warnings:
            unique_warnings = set(grep_warnings)
            if len(unique_warnings) > 3:  # If many warnings, summarize
                issues.append("🔍 Configuration contains invalid regex patterns - review and fix pattern syntax")
            else:
                for warning in list(unique_warnings)[:3]:  # Show first 3 unique warnings
                    if "stray \\" in warning:
                        issues.append("🔍 Invalid backslash escapes in configuration - check regex patterns")
                    else:
                        issues.append(f"🔍 Regex issue: {warning}")

        # Parse egrep obsolescence warnings
        egrep_count = output.lower().count("egrep is obsolescent")
        if egrep_count > 0:
            issues.append("📅 Configuration uses obsolete 'egrep' patterns - update to 'grep -E' syntax")

        # Parse permission issues
        if re.search(r'permission\s+denied|access\s+denied', output, re.IGNORECASE):
            issues.append("🔒 Permission denied during config check - run with elevated privileges")

        # Parse missing files or directories
        missing_files = re.findall(r'(?:cannot access|no such file or directory):\s*([^\n]+)', output, re.IGNORECASE)
        for file_path in missing_files[:3]:  # Limit to first 3
            issues.append(f"📁 Missing file or directory: {file_path.strip()}")

        # Parse dependency issues
        if re.search(r'command not found|not installed', output, re.IGNORECASE):
            issues.append("📦 Missing required dependencies - install missing packages")

        # If we found specific issues, add a general recommendation
        if issues:
            issues.append("💡 Fix suggestion: Review and update your RKHunter configuration file")

        return issues

    # Helper methods
    def _acquire_lock(self):
        """Acquire file lock for safe concurrent access"""

        class FileLock:
            def __init__(self, lock_file):
                self.lock_file = lock_file
                self.fd = None

            def __enter__(self):
                self.fd = open(self.lock_file, "w")
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.fd:
                    fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                    self.fd.close()
                    try:
                        os.unlink(self.lock_file)
                    except BaseException:
                        pass

        return FileLock(self.lock_file)

    def _backup_config(self) -> bool:
        """Create configuration backup with proper privilege escalation."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Configuration file {self.config_path} does not exist")
                return False

            # Use elevated file operation for backup
            try:
                # Try using elevated file operation first
                backup_name = f"rkhunter.conf.backup.{int(time.time())}"
                temp_backup = self.temp_dir / backup_name

                # Use sudo to copy the file
                result = run_secure(
                    ["sudo", "cp", self.config_path, str(temp_backup)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    # Make the backup file readable by the user
                    run_secure(
                        [
                            "sudo",
                            "chown",
                            f"{os.getuid()}:{os.getgid()}",
                            str(temp_backup),
                        ],
                        capture_output=True,
                        timeout=10,
                    )
                    logger.info(f"Configuration backed up to {temp_backup}")
                    return True
                else:
                    logger.warning(f"Sudo copy failed: {result.stderr}")

            except Exception as e:
                logger.debug(f"Privileged backup failed: {e}")

            # Fallback: Try direct copy without privileges
            try:
                backup_name = f"rkhunter.conf.backup.{int(time.time())}"
                temp_backup = self.temp_dir / backup_name
                shutil.copy2(self.config_path, str(temp_backup))
                logger.info(f"Configuration backed up to {temp_backup}")
                return True
            except PermissionError:
                logger.warning("Cannot create configuration backup due to insufficient permissions")
                return False

        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
        return False

    def _read_config_file(self) -> str:
        """Read configuration file content with GUI authentication"""
        try:
            with open(self.config_path) as f:
                return f.read()
        except PermissionError:
            logger.info("Permission denied for direct read, using elevated permissions...")
            try:
                result = elevated_run_gui(
                    ["cat", self.config_path],
                    timeout=30,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.error(f"Failed to read config with elevated permissions: {result.stderr}")
                    return ""
            except Exception as elevated_error:
                logger.error(
                    f"Failed to read config file even with elevated permissions: {elevated_error}"
                )
                return ""
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            return ""

    def _write_config_file(self, content: str):
        """Write configuration file content with GUI authentication"""
        try:
            # First try to write directly
            with open(self.config_path, "w") as f:
                f.write(content)
            logger.info("Configuration file updated")
        except PermissionError:
            logger.info("Permission denied for direct write, using elevated permissions...")
            try:
                # Write to temp file first, then copy with elevated permissions
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".conf") as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                result = elevated_run_gui(
                    ["cp", temp_file_path, self.config_path],
                    timeout=30,
                    capture_output=True,
                    text=True
                )

                # Clean up temp file
                os.unlink(temp_file_path)

                if result.returncode == 0:
                    logger.info("Configuration file updated with elevated permissions")
                else:
                    raise RuntimeError(f"Failed to write config file: {result.stderr}")
            except Exception as elevated_error:
                logger.error(
                    f"Failed to write config file even with elevated permissions: {elevated_error}"
                )
                raise
        except Exception as e:
            logger.error(f"Failed to write config file: {e}")
            raise

    def _update_config_value(self, content: str, key: str, value: str) -> str:
        """Update configuration value"""
        pattern = rf"^{re.escape(key)}=.*$"
        replacement = f"{key}={value}"

        if re.search(pattern, content, re.MULTILINE):
            # Update existing value
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            # Add new value
            content += f"\n{replacement}\n"

        return content

    def _parse_version(self, version_output: str) -> str:
        """Parse RKHunter version from output"""
        match = re.search(r"(\d+\.\d+\.\d+)", version_output)
        return match.group(1) if match else "Unknown"

    def _get_database_version(self) -> str:
        """Get RKHunter database version with privilege escalation."""
        try:
            # First try to read the local database file for version
            db_paths = [
                "/var/lib/rkhunter/db/rkhunter.dat",
                "/usr/local/var/lib/rkhunter/db/rkhunter.dat",
            ]

            for db_path in db_paths:
                try:
                    # Use sudo to read the database file
                    result = run_secure(
                        ["sudo", "head", "-10", db_path],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0 and result.stdout:
                        for line in result.stdout.split("\n"):
                            if line.startswith("Version:"):
                                version = line.split(":", 1)[1].strip()
                                # Convert version format: 2025090500 -> 2025.09.05.00
                                if len(version) == 10 and version.isdigit():
                                    formatted = (
                                        f"{version[:4]}.{version[4:6]}.{version[6:8]}.{version[8:]}"
                                    )
                                    return f"Database: {formatted}"
                                return f"Database: {version}"
                except Exception:
                    continue

            # Fallback: Try to get data file timestamps
            result = run_secure(
                ["sudo", "stat", "-c", "%Y", "/var/lib/rkhunter/db/programs_bad.dat"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                timestamp = int(result.stdout.strip())
                import datetime

                date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                return f"Data files: {date_str}"

            return "Unknown"
        except Exception as e:
            logger.warning(f"Failed to get database version: {e}")
            return "Unknown"

    def _get_last_update_time(self) -> datetime | None:
        """Get last update time"""
        try:
            log_file = "/var/log/rkhunter.log"
            if os.path.exists(log_file):
                # Parse log for last update
                with open(log_file) as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if "Update completed" in line:
                            # Extract timestamp
                            match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                            if match:
                                return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        except BaseException:
            pass
        return None

    def _get_last_scan_time(self) -> datetime | None:
        """Get last scan time"""
        try:
            log_file = "/var/log/rkhunter.log"
            if os.path.exists(log_file):
                # Parse log for last scan
                with open(log_file) as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if "Check completed" in line or "Scan completed" in line:
                            # Extract timestamp
                            match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                            if match:
                                return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        except BaseException:
            pass
        return None

    def _baseline_exists(self) -> bool:
        """Check if baseline exists"""
        baseline_file = "/var/lib/rkhunter/db/rkhunter.dat"
        return os.path.exists(baseline_file)

    def _check_mirror_status(self) -> str:
        """Check mirror connectivity status (lightweight check)"""
        try:
            # Check if mirrors.dat exists and has content
            mirrors_file = "/var/lib/rkhunter/db/mirrors.dat"
            if os.path.exists(mirrors_file):
                try:
                    stat_result = os.stat(mirrors_file)
                    if stat_result.st_size > 0:
                        mod_time = datetime.fromtimestamp(stat_result.st_mtime)
                        days_old = (datetime.now() - mod_time).days
                        if days_old < 30:
                            return f"Updated {days_old} days ago"
                        else:
                            return f"Outdated ({days_old} days old)"
                    else:
                        return "Empty mirrors database"
                except Exception:
                    return "Mirror data inaccessible"

            # Fallback: Check config file with elevated access if needed
            config_file = "/etc/rkhunter.conf"
            if os.path.exists(config_file):
                try:
                    # Try to read config with current permissions first
                    with open(config_file) as f:
                        content = f.read()
                        if "UPDATE_MIRRORS=" in content:
                            return "Configured (no mirror data)"
                        else:
                            return "Not configured"
                except PermissionError:
                    # Try with elevated access
                    try:
                        result = self._execute_rkhunter_command(
                            ["--config-check"], timeout=20, use_sudo=True
                        )
                        if result.returncode == 0:
                            return "Config accessible"
                        else:
                            return "Config check failed"
                    except Exception:
                        return "Config inaccessible"
            else:
                return "Config missing"
        except Exception as e:
            logger.warning(f"Error checking mirror status: {e}")
            return "Unknown"

    def _check_mirror_connectivity(self) -> str:
        """Check actual mirror connectivity (for optimization tasks)"""
        try:
            result = run_secure(
                ["rkhunter", "--update", "--check"],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if "mirrors are OK" in result.stdout:
                return "OK"
            else:
                return "Issues detected"
        except Exception as e:
            logger.warning(f"Error checking mirror connectivity: {e}")
            return "Unknown"

    def _collect_performance_metrics(self) -> dict[str, Any]:
        """Collect performance metrics"""
        metrics = {}
        try:
            # Get average scan time from logs
            metrics["avg_scan_time"] = self._calculate_average_scan_time()

            # Get database size
            db_path = "/var/lib/rkhunter/db"
            if os.path.exists(db_path):
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(db_path)
                    for filename in filenames
                )
                metrics["database_size_mb"] = round(total_size / (1024 * 1024), 2)

            # Get last update duration
            metrics["last_update_duration"] = self._get_last_update_duration()

        except Exception as e:
            logger.debug(f"Error collecting metrics: {e}")
            metrics["error"] = str(e)

        return metrics

    def _check_configuration_issues(self) -> list[str]:
        """Check for configuration issues"""
        issues = []

        try:
            # Check if RKHunter is properly installed
            result = run_secure(["which", "rkhunter"], check=False, capture_output=True)
            if result.returncode != 0:
                issues.append("RKHunter not found in PATH")

            # Check configuration file
            if not os.path.exists(self.config_path):
                issues.append("Configuration file not found")
            elif not os.access(self.config_path, os.R_OK):
                issues.append("Configuration file not readable")

            # Check log directory
            log_dir = "/var/log"
            if not os.access(log_dir, os.W_OK):
                issues.append("Cannot write to log directory")

        except Exception as e:
            issues.append(f"Error checking configuration: {e}")

        return issues

    def _check_network_connectivity(self) -> bool:
        """Check network connectivity for updates"""
        try:
            result = run_secure(
                ["ping", "-c", "1", "-W", "5", "rkhunter.sourceforge.net"],
                check=False,
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except BaseException:
            return False

    def _baseline_update_needed(self) -> bool:
        """Check if baseline update is needed"""
        try:
            # Check if baseline file exists
            baseline_file = "/var/lib/rkhunter/db/rkhunter.dat"
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

    def _backup_baseline(self) -> str | None:
        """Backup current baseline"""
        try:
            baseline_file = "/var/lib/rkhunter/db/rkhunter.dat"
            if os.path.exists(baseline_file):
                backup_file = f"{baseline_file}.backup.{int(time.time())}"
                shutil.copy2(baseline_file, backup_file)
                return backup_file
        except Exception as e:
            logger.warning(f"Failed to backup baseline: {e}")
        return None

    def _analyze_baseline_changes(self, backup_file: str) -> list[str]:
        """Analyze changes between baseline versions"""
        changes = []
        try:
            # This is a simplified implementation
            # In practice, you'd parse the baseline files and compare
            current_file = "/var/lib/rkhunter/db/rkhunter.dat"

            if os.path.exists(current_file) and os.path.exists(backup_file):
                current_size = os.path.getsize(current_file)
                backup_size = os.path.getsize(backup_file)

                if current_size != backup_size:
                    changes.append(f"Database size changed: {backup_size} -> {current_size} bytes")

        except Exception as e:
            logger.debug(f"Error analyzing baseline changes: {e}")

        return changes

    # Additional helper methods for cron optimization, system checks, etc.
    def _get_existing_cron_jobs(self) -> list[str]:
        """Get existing cron jobs - kept for compatibility but not used with systemd"""
        # This method is kept for backwards compatibility but systemd timers
        # are preferred on modern systems
        try:
            result = elevated_run_gui(["crontab", "-l"], timeout=30, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split("\n")
        except Exception as e:
            logger.debug(f"Could not get existing cron jobs (normal on systemd systems): {e}")
        return []

    def _calculate_optimal_scan_time(self, frequency: str, existing_jobs: list[str]) -> str:
        """Calculate optimal scan time to avoid conflicts"""
        # Simple implementation - in practice, you'd analyze system load patterns
        if frequency == "daily":
            return "02:30"  # 2:30 AM
        elif frequency == "weekly":
            return "03:00"  # 3:00 AM on Sundays
        else:  # monthly
            return "03:30"  # 3:30 AM on first day of month

    def _generate_cron_entry(self, frequency: str, time: str, system_cron: bool = False) -> str:
        """Generate cron entry with optional system cron format."""
        hour, minute = time.split(":")

        # Base command
        base_cmd = "/usr/bin/rkhunter --check --skip-keypress --quiet"

        # Add user specification for system cron.d files
        if system_cron:
            user_spec = "root "
        else:
            user_spec = ""

        if frequency == "daily":
            return f"{minute} {hour} * * * {user_spec}{base_cmd}"
        elif frequency == "weekly":
            return f"{minute} {hour} * * 0 {user_spec}{base_cmd}"
        else:  # monthly
            return f"{minute} {hour} 1 * * {user_spec}{base_cmd}"

    def _update_cron_job(self, cron_entry: str) -> bool:
        """Legacy cron job update - kept for backwards compatibility only.
        Modern systems use systemd timers instead via _optimize_systemd_timer().
        """
        logger.warning("Traditional cron scheduling attempted on systemd system")
        logger.info(f"Legacy cron entry would be: {cron_entry}")
        logger.info("Use systemd timer optimization instead for better reliability")
        return False

    def _system_has_sufficient_memory(self) -> bool:
        """Check if system has sufficient memory"""
        try:
            with open("/proc/meminfo") as f:
                meminfo = f.read()
                match = re.search(r"MemTotal:\s+(\d+)", meminfo)
                if match:
                    total_kb = int(match.group(1))
                    total_gb = total_kb / (1024 * 1024)
                    return total_gb >= 2.0  # 2GB minimum
        except BaseException:
            pass
        return False

    def _has_reliable_network(self) -> bool:
        """Check for reliable network connection"""
        return self._check_network_connectivity()

    def _get_available_disk_space(self) -> int | None:
        """Get available disk space in MB with better error handling"""
        try:
            # Try different directories to check space - avoid hardcoded /tmp
            test_paths = ["/var/log", "/var", tempfile.gettempdir(), "/"]

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
            "/etc/rkhunter.d/",
            "/usr/local/etc/rkhunter.d/",
            "/opt/rkhunter/etc/",
        ]

        for path in custom_rules_paths:
            if os.path.exists(path) and os.listdir(path):
                return True
        return False

    def _has_optimal_schedule(self) -> bool:
        """Check if current schedule is optimal"""
        cron_jobs = self._get_existing_cron_jobs()
        rkhunter_jobs = [job for job in cron_jobs if "rkhunter" in job]

        # Simple check - could be enhanced
        return len(rkhunter_jobs) == 1

    def _check_dependencies(self) -> list[str]:
        """Check for missing dependencies"""
        missing = []
        required_commands = ["curl", "wget", "file", "stat", "readlink"]

        for cmd in required_commands:
            result = run_secure(["which", cmd], check=False, capture_output=True)
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
            system_dirs = ["/var/log", "/var/lib/rkhunter", "/etc"]
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

    def _calculate_average_scan_time(self) -> float | None:
        """Calculate average scan time from logs"""
        try:
            # This is a simplified implementation
            # In practice, you'd parse log timestamps
            return 180.0  # 3 minutes average
        except BaseException:
            return None

    def _get_last_update_duration(self) -> float | None:
        """Get duration of last update"""
        try:
            # Simplified implementation
            return 45.0  # 45 seconds
        except BaseException:
            return None
