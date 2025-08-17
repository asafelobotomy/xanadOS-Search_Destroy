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
    
    # Try methods in order of preference
    methods = []
    
    if gui and pkexec:
        # GUI method: pkexec
        env_wrap = [pkexec, "env"] + [f"{k}={v}" for k, v in env.items()]
        methods.append(("pkexec", env_wrap + list(argv)))
    
    if sudo:
        # Command line methods: sudo
        methods.append(("sudo", [sudo] + list(argv)))
    
    # Try each method
    for method_name, cmd in methods:
        try:
            logger.info(f"Trying {method_name}: {' '.join(cmd[:3])}...")
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=capture_output,
                text=text,
                env=env
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
