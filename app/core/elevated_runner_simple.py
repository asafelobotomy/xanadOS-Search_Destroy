#!/usr/bin/env python3
"""
Simple privilege escalation for xanadOS Search & Destroy.
Simplified version without complex session management.
"""

import logging
import os
import subprocess
from typing import Optional, Sequence

logger = logging.getLogger(__name__)


def _which(name: str) -> Optional[str]:
    """Find executable in PATH."""
    try:
        result = subprocess.run(
            ["which", name], capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _sanitize_env(gui: bool = True) -> dict:
    """Create sanitized environment for privilege escalation."""
    env = {
        "PATH": os.environ.get(
            "PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ),
        "USER": os.environ.get("USER", "root"),
        "HOME": "/root",
        "SHELL": "/bin/bash",
    }

    if gui and os.environ.get("DISPLAY"):
        env["DISPLAY"] = os.environ["DISPLAY"]
        if os.environ.get("XAUTHORITY"):
            env["XAUTHORITY"] = os.environ["XAUTHORITY"]

    return env


def elevated_run(
    argv: Sequence[str],
    *,
    timeout: int = 300,
    capture_output: bool = True,
    text: bool = True,
    gui: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run command with elevated privileges using persistent GUI authentication.

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

    # Try the new GUI authentication manager first (highest priority)
    if gui and os.environ.get("DISPLAY"):
        try:
            from .gui_auth_manager import elevated_run_gui

            logger.info("Using persistent GUI authentication manager (simple)")
            return elevated_run_gui(
                argv, timeout=timeout, capture_output=capture_output, text=text
            )
        except ImportError:
            logger.warning(
                "GUI authentication manager not available, falling back to legacy methods"
            )
        except Exception as e:
            logger.warning(
                f"GUI authentication manager failed: {e}, falling back to legacy methods"
            )

    # Fallback to legacy simple methods
    return _simple_legacy_elevated_run(
        argv, timeout=timeout, capture_output=capture_output, text=text, gui=gui
    )


def _simple_legacy_elevated_run(
    argv: Sequence[str],
    *,
    timeout: int = 300,
    capture_output: bool = True,
    text: bool = True,
    gui: bool = True,
) -> subprocess.CompletedProcess:
    """
    Legacy simple privilege escalation fallback method.
    """
    # Find available privilege escalation tools
    sudo = _which("sudo")
    pkexec = _which("pkexec") if gui else None

    if not (sudo or pkexec):
        return subprocess.CompletedProcess(
            argv, 1, "", "No privilege escalation tool available"
        )

    # Prepare environment
    env = _sanitize_env(gui=gui)

    # Try methods in order of preference (GUI sudo prioritized over pkexec)
    methods = []

    if sudo and gui and os.environ.get("DISPLAY"):
        # 1. GUI sudo with askpass helper (highest priority for persistent sessions)
        askpass_helpers = [
            "/usr/bin/ksshaskpass",
            "/usr/bin/ssh-askpass",
            "/usr/bin/x11-ssh-askpass",
            "/usr/bin/lxqt-openssh-askpass",
        ]

        for helper in askpass_helpers:
            if _which(helper.split("/")[-1]):  # Check if helper exists
                logger.info(f"Using GUI sudo with {helper}")
                env_with_askpass = env.copy()
                env_with_askpass["SUDO_ASKPASS"] = helper
                methods.append(("sudo-gui", [sudo, "-A"] + list(argv)))
                break

    # pkexec moved to lower priority (only as fallback)
    if gui and pkexec:
        # 2. pkexec (fallback GUI method - less persistent than sudo)
        env_wrap = [pkexec, "env"] + [f"{k}={v}" for k, v in env.items()]
        methods.append(("pkexec-fallback", env_wrap + list(argv)))

    if sudo:
        # 3. Command line methods: sudo
        methods.append(("sudo", [sudo] + list(argv)))

    # Try each method
    for method_name, cmd in methods:
        try:
            logger.info(f"Trying {method_name}: {' '.join(cmd[:3])}...")
            result = subprocess.run(
                cmd, timeout=timeout, capture_output=capture_output, text=text, env=env
            )

            if result.returncode == 0:
                logger.info(f"Success with {method_name}")
                return result
            else:
                logger.debug(
                    f"{method_name} failed with return code {result.returncode}"
                )

        except subprocess.TimeoutExpired:
            logger.warning(f"{method_name} timed out")
        except Exception as e:
            logger.debug(f"{method_name} error: {e}")

    # If all methods failed, return the last result or create a failure result
    return subprocess.CompletedProcess(
        argv, 1, "", "All privilege escalation methods failed"
    )


def validate_auth_session() -> bool:
    """
    Validate authentication session using GUI authentication manager.

    Returns:
        True if authentication works, False otherwise
    """
    try:
        # Import here to avoid hard dependency if GUI auth is unavailable
        from .gui_auth_manager import get_gui_auth_manager

        manager = get_gui_auth_manager()
        session_info = manager.get_session_info()
        if session_info["active"]:
            logger.debug("GUI authentication session is active (simple)")
            return True
    except ImportError:
        logger.debug("GUI authentication manager not available for validation (simple)")
    except Exception as e:
        logger.debug(f"Error validating GUI authentication session (simple): {e}")

    # Fallback to simple test
    try:
        result = elevated_run(["true"], timeout=30)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Authentication validation failed (simple): {e}")
        return False
