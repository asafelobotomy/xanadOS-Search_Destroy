#!/usr/bin/env python3
"""
Simple privilege escalation for xanadOS Search & Destroy.
Simplified version without complex session management.
"""

import logging
import os
import subprocess
from typing import Sequence, Optional, Mapping

logger = logging.getLogger(__name__)


def _which(name: str) -> Optional[str]:
    """Find executable in PATH."""
    try:
        result = subprocess.run(['which', name], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _sanitize_env(gui: bool = True) -> dict:
    """Create sanitized environment for privilege escalation."""
    env = {
        'PATH': os.environ.get('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
        'USER': os.environ.get('USER', 'root'),
        'HOME': '/root',
        'SHELL': '/bin/bash',
    }
    
    if gui and os.environ.get('DISPLAY'):
        env['DISPLAY'] = os.environ['DISPLAY']
        if os.environ.get('XAUTHORITY'):
            env['XAUTHORITY'] = os.environ['XAUTHORITY']
    
    return env


def elevated_run(argv: Sequence[str], *, timeout: int = 300, capture_output: bool = True,
                text: bool = True, gui: bool = True) -> subprocess.CompletedProcess:
    """
    Run command with elevated privileges using the simplest available method.
    
    Args:
        argv: Command to run (without sudo/pkexec prefix)
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        text: Whether to use text mode
        gui: Whether to prefer GUI authentication
    
    Returns:
        subprocess.CompletedProcess result
    """
    if not argv:
        return subprocess.CompletedProcess([], 1, "", "No command provided")
    
    # Find available privilege escalation tools
    pkexec = _which("pkexec") if gui else None
    sudo = _which("sudo")
    
    if not (pkexec or sudo):
        return subprocess.CompletedProcess(argv, 1, "", "No privilege escalation tool available")
    
    # Prepare environment
    env = _sanitize_env(gui=gui)
    
    # Try methods in order of preference (new priority order)
    methods = []
    
    if sudo:
        # 1. Passwordless sudo (first priority - fastest and most secure)
        methods.append(("sudo-nopass", [sudo, "-n"] + list(argv), env))
    
    if sudo and gui and os.environ.get("DISPLAY"):
        # 2. GUI sudo with askpass helper (second priority - good user experience)
        askpass_helpers = [
            "/usr/bin/ksshaskpass",
            "/usr/bin/ssh-askpass", 
            "/usr/bin/x11-ssh-askpass",
            "/usr/bin/lxqt-openssh-askpass"
        ]
        
        for helper in askpass_helpers:
            if _which(helper.split('/')[-1]):  # Check if helper exists
                logger.info(f"Using GUI sudo with {helper}")
                env_with_askpass = env.copy()
                env_with_askpass["SUDO_ASKPASS"] = helper
                methods.append(("sudo-gui", [sudo, "-A"] + list(argv), env_with_askpass))
                break
    
    if gui and pkexec:
        # 3. pkexec (third priority - alternative GUI method)
        env_wrap = [pkexec, "env"] + [f"{k}={v}" for k, v in env.items()]
        methods.append(("pkexec", env_wrap + list(argv), env))
    
    if sudo:
        # 4. Terminal sudo (last resort)
        methods.append(("sudo-terminal", [sudo] + list(argv), env))
    
    # Try each method
    for method_name, cmd, method_env in methods:
        try:
            logger.info(f"Trying {method_name}: {' '.join(cmd[:3])}...")
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=capture_output,
                text=text,
                env=method_env
            )
            
            if result.returncode == 0:
                logger.info(f"Success with {method_name}")
                return result
            else:
                logger.debug(f"{method_name} failed with return code {result.returncode}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"{method_name} timed out")
        except Exception as e:
            logger.debug(f"{method_name} error: {e}")
    
    # If all methods failed, return the last result or create a failure result
    return subprocess.CompletedProcess(argv, 1, "", "All privilege escalation methods failed")


def validate_auth_session() -> bool:
    """
    Simple authentication validation - just try a basic command.
    
    Returns:
        True if authentication works, False otherwise
    """
    try:
        result = elevated_run(["true"], timeout=30)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Authentication validation failed: {e}")
        return False


def elevated_popen(argv: Sequence[str], *, gui: bool = True, text: bool = True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize: int = 1) -> subprocess.Popen:
    """
    Start a privileged process returning Popen for streaming.
    Simplified version - tries pkexec first, then sudo.
    
    Args:
        argv: Command to run (without sudo/pkexec prefix)
        gui: Whether to prefer GUI authentication
        text: Whether to use text mode
        stdout, stderr: Pipe configuration
        bufsize: Buffer size
    
    Returns:
        subprocess.Popen object
    """
    if not argv:
        raise ValueError("No command provided")
    
    # Find available privilege escalation tools
    pkexec = _which("pkexec") if gui else None
    sudo = _which("sudo")
    
    if not (pkexec or sudo):
        raise RuntimeError("No privilege escalation tool available")
    
    # Prepare environment
    env = _sanitize_env(gui=gui)
    
    # Try methods in order of preference (new priority order)
    methods = []
    
    if sudo:
        # 1. Passwordless sudo (first priority - fastest and most secure)
        methods.append(("sudo-nopass", [sudo, "-n"] + list(argv), env))
    
    if sudo and gui and os.environ.get("DISPLAY"):
        # 2. GUI sudo with askpass helper (second priority - good user experience)
        askpass_helpers = [
            "/usr/bin/ksshaskpass",
            "/usr/bin/ssh-askpass", 
            "/usr/bin/x11-ssh-askpass",
            "/usr/bin/lxqt-openssh-askpass"
        ]
        
        for helper in askpass_helpers:
            if _which(helper.split('/')[-1]):  # Check if helper exists
                logger.info(f"Using GUI sudo with {helper}")
                env_with_askpass = env.copy()
                env_with_askpass["SUDO_ASKPASS"] = helper
                methods.append(("sudo-gui", [sudo, "-A"] + list(argv), env_with_askpass))
                break
    
    if gui and pkexec:
        # 3. pkexec (third priority - alternative GUI method)
        env_wrap = [pkexec, "env"] + [f"{k}={v}" for k, v in env.items()]
        methods.append(("pkexec", env_wrap + list(argv), env))
    
    if sudo:
        # 4. Terminal sudo (last resort)
        methods.append(("sudo-terminal", [sudo] + list(argv), env))
    
    # Try each method until one works
    last_error = None
    for method_name, cmd, method_env in methods:
        try:
            logger.info(f"Starting {method_name} process: {' '.join(cmd[:3])}...")
            process = subprocess.Popen(
                cmd,
                stdout=stdout,
                stderr=stderr,
                text=text,
                bufsize=bufsize,
                env=method_env
            )
            logger.info(f"Process started with {method_name}, PID: {process.pid}")
            return process
            
        except Exception as e:
            logger.debug(f"{method_name} popen error: {e}")
            last_error = e
    
    # If all methods failed, raise the last error
    raise RuntimeError(f"All privilege escalation methods failed. Last error: {last_error}")


def cleanup_auth_session() -> None:
    """
    Clean up authentication session.
    Simplified version - no persistent sessions to clean up.
    """
    logger.debug("Authentication session cleanup (simplified - no persistent sessions)")
    pass
