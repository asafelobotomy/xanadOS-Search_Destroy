#!/usr/bin/env python3
"""
System Service Integration for S&D
Provides system service management, startup integration, and daemon capabilities.
"""
import os
import sys
import logging
import subprocess
import signal
import threading
import time
import socket
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import pwd
import grp
from datetime import datetime

class ServiceState(Enum):
    """System service states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    """Service integration types."""
    SYSTEMD = "systemd"
    SYSV_INIT = "sysv_init"
    UPSTART = "upstart"
    MANUAL = "manual"

@dataclass
class ServiceConfig:
    """Service configuration."""
    service_name: str = "search-and-destroy"
    display_name: str = "S&D - Search & Destroy"
    description: str = "Real-time antivirus protection service"
    user: str = "root"
    group: str = "root"
    working_directory: str = "/opt/search-and-destroy"
    executable_path: str = "/opt/search-and-destroy/app/main.py"
    pid_file: str = "/var/run/search-and-destroy.pid"
    log_file: str = "/var/log/search-and-destroy/service.log"
    config_file: str = "/etc/search-and-destroy/config.json"
    auto_start: bool = True
    restart_on_failure: bool = True
    restart_delay_seconds: int = 10
    max_restart_attempts: int = 5
    environment_vars: Dict[str, str] = None

    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}

@dataclass
class ServiceStatus:
    """Service status information."""
    state: ServiceState
    pid: Optional[int] = None
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    restart_count: int = 0
    last_restart_time: Optional[datetime] = None
    error_message: str = ""

class SystemServiceManager:
    """
    Comprehensive system service integration for S&D.
    Handles service installation, management, and monitoring across different init systems.
    """
    
    def __init__(self, config: ServiceConfig = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or ServiceConfig()
        
        # Detect init system
        self.service_type = self._detect_init_system()
        self.logger.info("Detected init system: %s", self.service_type.value)
        
        # Service state
        self.current_state = ServiceState.UNKNOWN
        self.service_pid: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        
        # Daemon mode support
        self.daemon_mode = False
        self.daemon_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        # Service monitoring
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_running = False
        
        # Callbacks
        self.state_changed_callback: Optional[Callable[[ServiceState, str], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None

    def _detect_init_system(self) -> ServiceType:
        """Detect the system's init system."""
        try:
            # Check for systemd
            if Path("/run/systemd/system").exists():
                return ServiceType.SYSTEMD
            
            # Check for upstart
            if Path("/sbin/initctl").exists() and os.access("/sbin/initctl", os.X_OK):
                return ServiceType.UPSTART
            
            # Check for SysV init
            if Path("/etc/init.d").exists():
                return ServiceType.SYSV_INIT
            
            # Fallback to manual
            return ServiceType.MANUAL
            
        except Exception as e:
            self.logger.error("Error detecting init system: %s", e)
            return ServiceType.MANUAL

    def install_service(self) -> bool:
        """Install the service for automatic startup."""
        try:
            self.logger.info("Installing system service...")
            
            if self.service_type == ServiceType.SYSTEMD:
                return self._install_systemd_service()
            elif self.service_type == ServiceType.SYSV_INIT:
                return self._install_sysv_service()
            elif self.service_type == ServiceType.UPSTART:
                return self._install_upstart_service()
            else:
                self.logger.warning("Manual service management - no automatic installation")
                return True
                
        except Exception as e:
            self.logger.error("Failed to install service: %s", e)
            if self.error_callback:
                self.error_callback(f"Service installation failed: {e}")
            return False

    def uninstall_service(self) -> bool:
        """Uninstall the system service."""
        try:
            self.logger.info("Uninstalling system service...")
            
            # Stop service first
            self.stop_service()
            
            if self.service_type == ServiceType.SYSTEMD:
                return self._uninstall_systemd_service()
            elif self.service_type == ServiceType.SYSV_INIT:
                return self._uninstall_sysv_service()
            elif self.service_type == ServiceType.UPSTART:
                return self._uninstall_upstart_service()
            else:
                return True
                
        except Exception as e:
            self.logger.error("Failed to uninstall service: %s", e)
            return False

    def start_service(self) -> bool:
        """Start the system service."""
        try:
            self.logger.info("Starting system service...")
            
            if self.service_type == ServiceType.SYSTEMD:
                result = self._systemctl_action("start")
            elif self.service_type == ServiceType.SYSV_INIT:
                result = self._sysv_action("start")
            elif self.service_type == ServiceType.UPSTART:
                result = self._upstart_action("start")
            else:
                result = self._manual_start()
            
            if result:
                self._set_state(ServiceState.RUNNING)
                self.start_time = datetime.now()
                self.logger.info("Service started successfully")
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to start service: %s", e)
            self._set_state(ServiceState.FAILED, str(e))
            return False

    def stop_service(self) -> bool:
        """Stop the system service."""
        try:
            self.logger.info("Stopping system service...")
            
            if self.service_type == ServiceType.SYSTEMD:
                result = self._systemctl_action("stop")
            elif self.service_type == ServiceType.SYSV_INIT:
                result = self._sysv_action("stop")
            elif self.service_type == ServiceType.UPSTART:
                result = self._upstart_action("stop")
            else:
                result = self._manual_stop()
            
            if result:
                self._set_state(ServiceState.STOPPED)
                self.logger.info("Service stopped successfully")
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to stop service: %s", e)
            return False

    def restart_service(self) -> bool:
        """Restart the system service."""
        try:
            self.logger.info("Restarting system service...")
            
            if self.service_type == ServiceType.SYSTEMD:
                result = self._systemctl_action("restart")
            elif self.service_type == ServiceType.SYSV_INIT:
                result = self._sysv_action("restart")
            elif self.service_type == ServiceType.UPSTART:
                result = self._upstart_action("restart")
            else:
                result = self._manual_stop() and self._manual_start()
            
            if result:
                self.restart_count += 1
                self.start_time = datetime.now()
                self._set_state(ServiceState.RUNNING)
                self.logger.info("Service restarted successfully")
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to restart service: %s", e)
            return False

    def get_service_status(self) -> ServiceStatus:
        """Get current service status."""
        try:
            # Update current state
            self._update_service_state()
            
            # Get process info if running
            pid = self._get_service_pid()
            uptime = 0.0
            memory_usage = 0.0
            cpu_percent = 0.0
            
            if pid and self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
                memory_usage, cpu_percent = self._get_process_stats(pid)
            
            return ServiceStatus(
                state=self.current_state,
                pid=pid,
                uptime_seconds=uptime,
                memory_usage_mb=memory_usage,
                cpu_percent=cpu_percent,
                restart_count=self.restart_count,
                last_restart_time=self.start_time
            )
            
        except Exception as e:
            self.logger.error("Error getting service status: %s", e)
            return ServiceStatus(
                state=ServiceState.UNKNOWN,
                error_message=str(e)
            )

    def enable_auto_start(self) -> bool:
        """Enable automatic service startup."""
        try:
            if self.service_type == ServiceType.SYSTEMD:
                return self._systemctl_action("enable")
            elif self.service_type == ServiceType.SYSV_INIT:
                return self._chkconfig_enable()
            elif self.service_type == ServiceType.UPSTART:
                # Upstart services are enabled by default
                return True
            else:
                self.logger.warning("Manual mode - auto-start not supported")
                return False
                
        except Exception as e:
            self.logger.error("Failed to enable auto-start: %s", e)
            return False

    def disable_auto_start(self) -> bool:
        """Disable automatic service startup."""
        try:
            if self.service_type == ServiceType.SYSTEMD:
                return self._systemctl_action("disable")
            elif self.service_type == ServiceType.SYSV_INIT:
                return self._chkconfig_disable()
            elif self.service_type == ServiceType.UPSTART:
                # Would need to modify upstart config
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error("Failed to disable auto-start: %s", e)
            return False

    def start_daemon_mode(self, main_function: Callable[[], None]) -> bool:
        """Start the application in daemon mode."""
        try:
            if self.daemon_mode:
                self.logger.warning("Already running in daemon mode")
                return True
            
            self.logger.info("Starting daemon mode...")
            
            # Setup signal handlers
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGHUP, self._signal_handler)
            
            # Create PID file
            self._create_pid_file()
            
            # Start service monitoring
            self.start_service_monitoring()
            
            # Set daemon mode
            self.daemon_mode = True
            self._set_state(ServiceState.RUNNING)
            
            # Run main function in daemon thread
            self.daemon_thread = threading.Thread(
                target=self._daemon_main_loop,
                args=(main_function,),
                daemon=False,
                name="ServiceDaemon"
            )
            self.daemon_thread.start()
            
            self.logger.info("Daemon mode started")
            return True
            
        except Exception as e:
            self.logger.error("Failed to start daemon mode: %s", e)
            return False

    def stop_daemon_mode(self):
        """Stop daemon mode."""
        try:
            if not self.daemon_mode:
                return
            
            self.logger.info("Stopping daemon mode...")
            
            # Signal shutdown
            self.shutdown_event.set()
            self.daemon_mode = False
            
            # Stop monitoring
            self.stop_service_monitoring()
            
            # Wait for daemon thread
            if self.daemon_thread and self.daemon_thread.is_alive():
                self.daemon_thread.join(timeout=10.0)
            
            # Remove PID file
            self._remove_pid_file()
            
            self._set_state(ServiceState.STOPPED)
            self.logger.info("Daemon mode stopped")
            
        except Exception as e:
            self.logger.error("Error stopping daemon mode: %s", e)

    def start_service_monitoring(self):
        """Start service health monitoring."""
        if self.monitor_running:
            return
        
        self.monitor_running = True
        self.monitor_thread = threading.Thread(
            target=self._service_monitor_loop,
            daemon=True,
            name="ServiceMonitor"
        )
        self.monitor_thread.start()
        self.logger.info("Service monitoring started")

    def stop_service_monitoring(self):
        """Stop service health monitoring."""
        self.monitor_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Service monitoring stopped")

    def _install_systemd_service(self) -> bool:
        """Install systemd service unit."""
        try:
            service_content = self._generate_systemd_unit()
            service_file = Path(f"/etc/systemd/system/{self.config.service_name}.service")
            
            # Write service file
            with service_file.open('w') as f:
                f.write(service_content)
            
            # Set permissions
            service_file.chmod(0o644)
            
            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            # Enable if configured
            if self.config.auto_start:
                self.enable_auto_start()
            
            self.logger.info("Systemd service installed: %s", service_file)
            return True
            
        except Exception as e:
            self.logger.error("Failed to install systemd service: %s", e)
            return False

    def _generate_systemd_unit(self) -> str:
        """Generate systemd unit file content."""
        env_vars = ""
        if self.config.environment_vars:
            env_vars = "\n".join([
                f"Environment={key}={value}"
                for key, value in self.config.environment_vars.items()
            ])
        
        return f"""[Unit]
Description={self.config.description}
After=network.target
Wants=network.target

[Service]
Type=simple
User={self.config.user}
Group={self.config.group}
WorkingDirectory={self.config.working_directory}
ExecStart=/usr/bin/python3 {self.config.executable_path} --daemon
ExecReload=/bin/kill -HUP $MAINPID
PIDFile={self.config.pid_file}
Restart={"always" if self.config.restart_on_failure else "no"}
RestartSec={self.config.restart_delay_seconds}
StandardOutput=journal
StandardError=journal
SyslogIdentifier={self.config.service_name}
{env_vars}

[Install]
WantedBy=multi-user.target
"""

    def _install_sysv_service(self) -> bool:
        """Install SysV init script."""
        try:
            script_content = self._generate_sysv_script()
            script_file = Path(f"/etc/init.d/{self.config.service_name}")
            
            # Write script file
            with script_file.open('w') as f:
                f.write(script_content)
            
            # Set permissions
            script_file.chmod(0o755)
            
            # Enable if configured
            if self.config.auto_start:
                self.enable_auto_start()
            
            self.logger.info("SysV init script installed: %s", script_file)
            return True
            
        except Exception as e:
            self.logger.error("Failed to install SysV service: %s", e)
            return False

    def _generate_sysv_script(self) -> str:
        """Generate SysV init script content."""
        return f"""#!/bin/bash
#
# {self.config.service_name}        {self.config.description}
#
# chkconfig: 35 80 20
# description: {self.config.description}
#

. /etc/rc.d/init.d/functions

USER="{self.config.user}"
DAEMON="{self.config.service_name}"
ROOT_DIR="{self.config.working_directory}"

SERVER="$ROOT_DIR/{self.config.executable_path}"
LOCK_FILE="/var/lock/subsys/{self.config.service_name}"

start() {{
    if [ -f $LOCK_FILE ] ; then
        echo "$DAEMON is locked."
        return 1
    fi
    
    echo -n $"Starting $DAEMON: "
    runuser -l "$USER" -c "$SERVER --daemon" && echo_success || echo_failure
    RETVAL=$?
    echo
    [ $RETVAL -eq 0 ] && touch $LOCK_FILE
    return $RETVAL
}}

stop() {{
    echo -n $"Shutting down $DAEMON: "
    pid=`ps -aefw | grep "$DAEMON" | grep -v " grep " | awk '{{print $2}}'`
    kill -9 $pid > /dev/null 2>&1
    [ $? -eq 0 ] && echo_success || echo_failure
    echo
    [ $RETVAL -eq 0 ] && rm -f $LOCK_FILE
    return $RETVAL
}}

restart() {{
    stop
    start
}}

status() {{
    if [ -f $LOCK_FILE ]; then
        echo "$DAEMON is running."
    else
        echo "$DAEMON is stopped."
    fi
}}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: {{start|stop|status|restart}}"
        exit 1
        ;;
esac

exit $?
"""

    def _install_upstart_service(self) -> bool:
        """Install Upstart service configuration."""
        try:
            config_content = self._generate_upstart_config()
            config_file = Path(f"/etc/init/{self.config.service_name}.conf")
            
            # Write config file
            with config_file.open('w') as f:
                f.write(config_content)
            
            # Set permissions
            config_file.chmod(0o644)
            
            self.logger.info("Upstart service installed: %s", config_file)
            return True
            
        except Exception as e:
            self.logger.error("Failed to install Upstart service: %s", e)
            return False

    def _generate_upstart_config(self) -> str:
        """Generate Upstart configuration content."""
        return f"""description "{self.config.description}"

start on runlevel [2345]
stop on runlevel [016]

setuid {self.config.user}
setgid {self.config.group}

chdir {self.config.working_directory}

respawn
respawn limit {self.config.max_restart_attempts} {self.config.restart_delay_seconds}

exec /usr/bin/python3 {self.config.executable_path} --daemon
"""

    def _uninstall_systemd_service(self) -> bool:
        """Uninstall systemd service."""
        try:
            service_file = Path(f"/etc/systemd/system/{self.config.service_name}.service")
            
            # Disable service
            self.disable_auto_start()
            
            # Remove service file
            if service_file.exists():
                service_file.unlink()
            
            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            self.logger.info("Systemd service uninstalled")
            return True
            
        except Exception as e:
            self.logger.error("Failed to uninstall systemd service: %s", e)
            return False

    def _uninstall_sysv_service(self) -> bool:
        """Uninstall SysV service."""
        try:
            script_file = Path(f"/etc/init.d/{self.config.service_name}")
            
            # Disable service
            self.disable_auto_start()
            
            # Remove script file
            if script_file.exists():
                script_file.unlink()
            
            self.logger.info("SysV service uninstalled")
            return True
            
        except Exception as e:
            self.logger.error("Failed to uninstall SysV service: %s", e)
            return False

    def _uninstall_upstart_service(self) -> bool:
        """Uninstall Upstart service."""
        try:
            config_file = Path(f"/etc/init/{self.config.service_name}.conf")
            
            # Remove config file
            if config_file.exists():
                config_file.unlink()
            
            self.logger.info("Upstart service uninstalled")
            return True
            
        except Exception as e:
            self.logger.error("Failed to uninstall Upstart service: %s", e)
            return False

    def _systemctl_action(self, action: str) -> bool:
        """Execute systemctl action."""
        try:
            result = subprocess.run(
                ["systemctl", action, self.config.service_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _sysv_action(self, action: str) -> bool:
        """Execute SysV init action."""
        try:
            result = subprocess.run(
                [f"/etc/init.d/{self.config.service_name}", action],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _upstart_action(self, action: str) -> bool:
        """Execute Upstart action."""
        try:
            if action == "start":
                cmd = ["start", self.config.service_name]
            elif action == "stop":
                cmd = ["stop", self.config.service_name]
            elif action == "restart":
                cmd = ["restart", self.config.service_name]
            else:
                return False
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def _manual_start(self) -> bool:
        """Manual service start."""
        try:
            # This would start the service manually
            # For now, just indicate success if not already running
            if not self._get_service_pid():
                self.logger.info("Manual start - would execute: python3 %s --daemon", 
                               self.config.executable_path)
                return True
            return False
        except Exception:
            return False

    def _manual_stop(self) -> bool:
        """Manual service stop."""
        try:
            pid = self._get_service_pid()
            if pid:
                os.kill(pid, signal.SIGTERM)
                return True
            return False
        except Exception:
            return False

    def _chkconfig_enable(self) -> bool:
        """Enable service with chkconfig."""
        try:
            result = subprocess.run(
                ["chkconfig", self.config.service_name, "on"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _chkconfig_disable(self) -> bool:
        """Disable service with chkconfig."""
        try:
            result = subprocess.run(
                ["chkconfig", self.config.service_name, "off"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _update_service_state(self):
        """Update current service state."""
        try:
            if self.service_type == ServiceType.SYSTEMD:
                result = subprocess.run(
                    ["systemctl", "is-active", self.config.service_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    status = result.stdout.strip()
                    if status == "active":
                        self.current_state = ServiceState.RUNNING
                    elif status == "inactive":
                        self.current_state = ServiceState.STOPPED
                    elif status == "failed":
                        self.current_state = ServiceState.FAILED
                    else:
                        self.current_state = ServiceState.UNKNOWN
                else:
                    self.current_state = ServiceState.STOPPED
            else:
                # For other systems, check if PID exists
                pid = self._get_service_pid()
                if pid and self._is_process_running(pid):
                    self.current_state = ServiceState.RUNNING
                else:
                    self.current_state = ServiceState.STOPPED
                    
        except Exception as e:
            self.logger.error("Error updating service state: %s", e)
            self.current_state = ServiceState.UNKNOWN

    def _get_service_pid(self) -> Optional[int]:
        """Get service process ID."""
        try:
            pid_file = Path(self.config.pid_file)
            if pid_file.exists():
                with pid_file.open('r') as f:
                    pid = int(f.read().strip())
                    if self._is_process_running(pid):
                        return pid
            return None
        except Exception:
            return None

    def _is_process_running(self, pid: int) -> bool:
        """Check if process is running."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _get_process_stats(self, pid: int) -> tuple[float, float]:
        """Get process memory and CPU statistics."""
        try:
            # Read from /proc/pid/stat and /proc/pid/status
            stat_file = Path(f"/proc/{pid}/stat")
            status_file = Path(f"/proc/{pid}/status")
            
            memory_mb = 0.0
            cpu_percent = 0.0
            
            # Get memory usage from status file
            if status_file.exists():
                with status_file.open('r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            memory_kb = int(line.split()[1])
                            memory_mb = memory_kb / 1024.0
                            break
            
            # CPU percentage would require more complex calculation
            # For now, return 0.0 as placeholder
            
            return memory_mb, cpu_percent
            
        except Exception:
            return 0.0, 0.0

    def _create_pid_file(self):
        """Create PID file."""
        try:
            pid_file = Path(self.config.pid_file)
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            
            with pid_file.open('w') as f:
                f.write(str(os.getpid()))
            
            self.logger.debug("PID file created: %s", pid_file)
            
        except Exception as e:
            self.logger.error("Failed to create PID file: %s", e)

    def _remove_pid_file(self):
        """Remove PID file."""
        try:
            pid_file = Path(self.config.pid_file)
            if pid_file.exists():
                pid_file.unlink()
                self.logger.debug("PID file removed: %s", pid_file)
        except Exception as e:
            self.logger.error("Failed to remove PID file: %s", e)

    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        self.logger.info("Received signal %d", signum)
        
        if signum in [signal.SIGTERM, signal.SIGINT]:
            self.stop_daemon_mode()
        elif signum == signal.SIGHUP:
            # Reload configuration
            self.logger.info("Reloading configuration...")

    def _daemon_main_loop(self, main_function: Callable[[], None]):
        """Main daemon loop."""
        try:
            self.logger.info("Daemon main loop started")
            
            # Run the main application function
            main_function()
            
            # Wait for shutdown signal
            while not self.shutdown_event.is_set():
                time.sleep(1.0)
            
            self.logger.info("Daemon main loop finished")
            
        except Exception as e:
            self.logger.error("Error in daemon main loop: %s", e)
            self._set_state(ServiceState.FAILED, str(e))

    def _service_monitor_loop(self):
        """Service health monitoring loop."""
        while self.monitor_running:
            try:
                # Update service state
                self._update_service_state()
                
                # Check for restart conditions
                if (self.current_state == ServiceState.FAILED and 
                    self.config.restart_on_failure and 
                    self.restart_count < self.config.max_restart_attempts):
                    
                    self.logger.warning("Service failed, attempting restart (%d/%d)",
                                      self.restart_count + 1, self.config.max_restart_attempts)
                    
                    time.sleep(self.config.restart_delay_seconds)
                    
                    if self.restart_service():
                        self.logger.info("Service restart successful")
                    else:
                        self.logger.error("Service restart failed")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error("Error in service monitor: %s", e)
                time.sleep(60)

    def _set_state(self, new_state: ServiceState, message: str = ""):
        """Set service state and notify callbacks."""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            
            self.logger.info("Service state changed: %s -> %s", 
                           old_state.value, new_state.value)
            
            if self.state_changed_callback:
                try:
                    self.state_changed_callback(new_state, message)
                except Exception as e:
                    self.logger.error("Error in state change callback: %s", e)

    def get_service_logs(self, lines: int = 100) -> List[str]:
        """Get recent service logs."""
        try:
            if self.service_type == ServiceType.SYSTEMD:
                result = subprocess.run(
                    ["journalctl", "-u", self.config.service_name, "-n", str(lines), "--no-pager"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.split('\n')
            
            # Fallback to log file
            log_file = Path(self.config.log_file)
            if log_file.exists():
                with log_file.open('r') as f:
                    return f.readlines()[-lines:]
            
            return []
            
        except Exception as e:
            self.logger.error("Error getting service logs: %s", e)
            return [f"Error reading logs: {e}"]

    def is_service_installed(self) -> bool:
        """Check if service is installed."""
        try:
            if self.service_type == ServiceType.SYSTEMD:
                service_file = Path(f"/etc/systemd/system/{self.config.service_name}.service")
                return service_file.exists()
            elif self.service_type == ServiceType.SYSV_INIT:
                script_file = Path(f"/etc/init.d/{self.config.service_name}")
                return script_file.exists()
            elif self.service_type == ServiceType.UPSTART:
                config_file = Path(f"/etc/init/{self.config.service_name}.conf")
                return config_file.exists()
            else:
                return False
                
        except Exception:
            return False

    def is_service_enabled(self) -> bool:
        """Check if service is enabled for auto-start."""
        try:
            if self.service_type == ServiceType.SYSTEMD:
                result = subprocess.run(
                    ["systemctl", "is-enabled", self.config.service_name],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0 and result.stdout.strip() == "enabled"
            elif self.service_type == ServiceType.SYSV_INIT:
                result = subprocess.run(
                    ["chkconfig", "--list", self.config.service_name],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0 and ":on" in result.stdout
            elif self.service_type == ServiceType.UPSTART:
                # Upstart services are enabled by default if config exists
                return self.is_service_installed()
            else:
                return False
                
        except Exception:
            return False

    # Callback setters
    def set_state_changed_callback(self, callback: Callable[[ServiceState, str], None]):
        """Set callback for service state changes."""
        self.state_changed_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]):
        """Set callback for service errors."""
        self.error_callback = callback
