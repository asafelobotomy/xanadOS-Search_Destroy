#!/usr/bin/env python3
"""
Process Management Library - Standardized process definitions and utilities
============================================================================
This library provides standardized process management for:
- Subprocess execution with security controls
- Process monitoring and lifecycle management
- Resource management and optimization
- Cross-platform process utilities
"""

import os
import subprocess
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any

import psutil

from .security_standards import validate_command_safety
from .system_paths import SystemPaths, get_executable


class ProcessPriority(Enum):
    """Process execution priority levels"""

    LOWEST = "lowest"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    HIGHEST = "highest"


class ProcessState(Enum):
    """Process execution states"""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    TIMEOUT = "timeout"


@dataclass
class ProcessConfig:
    """Configuration for process execution"""

    timeout: int = 300
    priority: ProcessPriority = ProcessPriority.NORMAL
    capture_output: bool = True
    text: bool = True
    shell: bool = False
    env: dict[str, str] | None = None
    cwd: str | None = None
    max_memory_mb: int = 1024
    cpu_limit_percent: float | None = None


@dataclass
class ProcessResult:
    """Result of process execution"""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    state: ProcessState
    pid: int | None = None
    memory_peak: int = 0
    cpu_percent: float = 0.0


class SecureProcessManager:
    """Secure process execution with monitoring and resource control"""

    def __init__(self):
        self.active_processes: dict[int, psutil.Process] = {}
        self.process_history: list[ProcessResult] = []
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()

    def execute_command(
        self, command: str | list[str], config: ProcessConfig | None = None
    ) -> ProcessResult:
        """Execute command with security validation and monitoring"""
        if config is None:
            config = ProcessConfig()

        # Normalize command to list
        if isinstance(command, str):
            command = [command]

        # Security validation
        binary = command[0]
        args = command[1:] if len(command) > 1 else []

        # Get absolute path for binary
        binary_path = get_executable(binary)
        if not binary_path:
            return ProcessResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Executable '{binary}' not found",
                execution_time=0.0,
                state=ProcessState.FAILED,
            )

        # Validate command safety
        validation = validate_command_safety(binary, args)
        if not validation.is_valid:
            return ProcessResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Security validation failed: {validation.message}",
                execution_time=0.0,
                state=ProcessState.FAILED,
            )

        # Update command with absolute path
        full_command = [binary_path] + args

        # Prepare environment
        env = self._prepare_environment(config.env)

        # Execute with monitoring
        start_time = time.time()

        try:
            # Create subprocess
            popen_kwargs = {
                "capture_output": config.capture_output,
                "text": config.text,
                "shell": config.shell,
                "env": env,
                "cwd": config.cwd,
                "timeout": config.timeout,
            }

            # Explicitly set check to False to avoid exceptions on non-zero exit
            result = subprocess.run(full_command, check=False, **popen_kwargs)

            execution_time = time.time() - start_time

            process_result = ProcessResult(
                command=command,
                returncode=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                execution_time=execution_time,
                state=(
                    ProcessState.COMPLETED
                    if result.returncode == 0
                    else ProcessState.FAILED
                ),
                pid=None,  # subprocess.run doesn't provide PID after completion
            )

        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            process_result = ProcessResult(
                command=command,
                returncode=-1,
                stdout=e.stdout or "" if hasattr(e, "stdout") else "",
                stderr=e.stderr or "" if hasattr(e, "stderr") else "Process timeout",
                execution_time=execution_time,
                state=ProcessState.TIMEOUT,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            process_result = ProcessResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                state=ProcessState.FAILED,
            )

        # Store in history
        with self._lock:
            self.process_history.append(process_result)
            # Keep only last 100 results
            if len(self.process_history) > 100:
                self.process_history = self.process_history[-100:]

        return process_result

    def execute_async(
        self,
        command: str | list[str],
        config: ProcessConfig | None = None,
        callback: Callable[[ProcessResult], None] | None = None,
    ) -> threading.Thread:
        """Execute command asynchronously"""

        def _async_execute():
            result = self.execute_command(command, config)
            if callback:
                callback(result)

        thread = threading.Thread(target=_async_execute)
        thread.start()
        return thread

    def execute_batch(
        self,
        commands: list[str | list[str]],
        config: ProcessConfig | None = None,
        max_concurrent: int = 4,
    ) -> list[ProcessResult]:
        """Execute multiple commands concurrently"""
        results = []

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [
                executor.submit(self.execute_command, cmd, config) for cmd in commands
            ]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Create error result
                    error_result = ProcessResult(
                        command=["unknown"],
                        returncode=-1,
                        stdout="",
                        stderr=str(e),
                        execution_time=0.0,
                        state=ProcessState.FAILED,
                    )
                    results.append(error_result)

        return results

    def _prepare_environment(
        self, extra_env: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Prepare secure environment for subprocess"""
        env = {
            "PATH": SystemPaths.SAFE_PATH,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }

        # Add display for GUI applications
        if "DISPLAY" in os.environ:
            env["DISPLAY"] = os.environ["DISPLAY"]

        if "XAUTHORITY" in os.environ:
            env["XAUTHORITY"] = os.environ["XAUTHORITY"]

        # Add extra environment variables with validation
        if extra_env:
            for key, value in extra_env.items():
                if (
                    key.isupper()
                    and len(key) < 64
                    and len(value) < 512
                    and ".." not in value
                ):
                    env[key] = value

        return env

    def get_system_info(self) -> dict[str, Any]:
        """Get system resource information"""
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_count": cpu_count,
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_free": disk.free,
                "disk_percent": disk.percent,
            }
        except Exception:
            return {}

    def cleanup_processes(self):
        """Clean up any remaining processes"""
        with self._lock:
            for pid, proc in list(self.active_processes.items()):
                try:
                    if proc.is_running():
                        proc.terminate()
                        time.sleep(1)
                        if proc.is_running():
                            proc.kill()
                    del self.active_processes[pid]
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    def get_process_history(self, limit: int = 10) -> list[ProcessResult]:
        """Get recent process execution history"""
        with self._lock:
            return self.process_history[-limit:]


class ProcessMonitor:
    """Monitor running processes for security and resource usage"""

    def __init__(self):
        self.monitored_processes: dict[int, psutil.Process] = {}
        self.suspicious_processes: list[dict[str, Any]] = []
        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None

    def start_monitoring(self, interval: float = 5.0):
        """Start process monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,)
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop process monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)

    def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                self._check_processes()
                time.sleep(interval)
            except Exception:
                # Continue monitoring even if individual checks fail
                continue

    def _check_processes(self):
        """Check all running processes for suspicious activity"""
        try:
            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_percent"]
            ):
                try:
                    # Check for suspicious patterns
                    if self._is_suspicious_process(proc.info):
                        self.suspicious_processes.append(
                            {
                                "timestamp": time.time(),
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "cmdline": proc.info["cmdline"],
                                "cpu_percent": proc.info["cpu_percent"],
                                "memory_percent": proc.info["memory_percent"],
                            }
                        )

                        # Keep only recent suspicious processes
                        if len(self.suspicious_processes) > 100:
                            self.suspicious_processes = self.suspicious_processes[-50:]

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception:
            pass

    def _is_suspicious_process(self, proc_info: dict[str, Any]) -> bool:
        """Check if process exhibits suspicious behavior"""
        name = proc_info.get("name", "").lower()
        cmdline = " ".join(proc_info.get("cmdline", [])).lower()

        # Suspicious patterns
        suspicious_names = [
            "svchost",
            "winlogon",
            "csrss",
            "lsass",  # Windows-like names on Linux
            "system32",
            "temp",
            "tmp",
        ]

        suspicious_cmdline = [
            "rm -rf /",
            "dd if=",
            "mkfs",
            "format",
            "wget http",
            "curl http",
            "nc -l",
            "netcat",
            "chmod 777",
            "chmod +x /tmp",
        ]

        # Check name patterns
        for pattern in suspicious_names:
            if pattern in name:
                return True

        # Check command line patterns
        for pattern in suspicious_cmdline:
            if pattern in cmdline:
                return True

        return False

    def get_suspicious_processes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent suspicious processes"""
        return self.suspicious_processes[-limit:]


# Global process manager instance
PROCESS_MANAGER = SecureProcessManager()


# Convenience functions
def execute_secure(
    command: str | list[str], timeout: int = 300, capture_output: bool = True
) -> ProcessResult:
    """Execute command securely with default settings"""
    config = ProcessConfig(timeout=timeout, capture_output=capture_output)
    return PROCESS_MANAGER.execute_command(command, config)


def execute_with_privilege(
    command: str | list[str], method: str = "elevated_run", timeout: int = 300
) -> ProcessResult:
    """Execute command with elevated privileges using standardized GUI sudo method"""
    if method == "elevated_run":
        # Use the standardized elevated_run method (same as RKHunter)
        from app.core.elevated_runner import elevated_run

        cmd_list = command if isinstance(command, list) else [command]
        result = elevated_run(cmd_list, timeout=timeout, gui=True)

        # Convert to ProcessResult format
        return ProcessResult(
            command=cmd_list,
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            execution_time=0.0,
            state=(
                ProcessState.COMPLETED
                if result.returncode == 0
                else ProcessState.FAILED
            ),
        )
    else:
        raise ValueError(f"Unknown privilege escalation method: {method}")


@contextmanager
def process_monitoring():
    """Context manager for process monitoring"""
    monitor = ProcessMonitor()
    monitor.start_monitoring()
    try:
        yield monitor
    finally:
        monitor.stop_monitoring()
