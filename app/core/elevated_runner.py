#!/usr/bin/env python3
"""Enhanced privilege escalation for xanadOS Search & Destroy.
Uses only GUI sudo authentication for better user experience and consistency.
"""

import logging
import os
import subprocess
from collections.abc import Sequence

logger = logging.getLogger(__name__)


def elevated_run(
    argv: Sequence[str],
    *,
    timeout: int = 300,
    capture_output: bool = True,
    text: bool = True,
    gui: bool = True,
) -> subprocess.CompletedProcess:
    """Run command with elevated privileges using GUI authentication.

    Args:
        argv: Command to run (without sudo prefix)
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        text: Whether to use text mode
        gui: Whether to prefer GUI authentication (always True)

    Returns:
        subprocess.CompletedProcess result
    """
    if not argv:
        return subprocess.CompletedProcess([], 1, "", "No command provided")

    # Only use GUI authentication manager
    if os.environ.get("DISPLAY"):
        try:
            from .gui_auth_manager import elevated_run_gui

            logger.info("Using persistent GUI sudo authentication")
            return elevated_run_gui(
                argv, timeout=timeout, capture_output=capture_output, text=text
            )
        except ImportError:
            logger.error(
                "GUI authentication manager not available - GUI environment required"
            )
            return subprocess.CompletedProcess(
                argv, 1, "", "GUI authentication not available"
            )
        except Exception as e:
            logger.error(f"GUI authentication failed: {e}")
            return subprocess.CompletedProcess(
                argv, 1, "", f"GUI authentication failed: {e}"
            )
    else:
        logger.error("No DISPLAY environment - GUI authentication required")
        return subprocess.CompletedProcess(
            argv, 1, "", "GUI environment required for authentication"
        )


def elevated_popen(
    argv: Sequence[str],
    *,
    stdin: str | None = None,
    stdout: int | str = subprocess.PIPE,
    stderr: int | str = subprocess.PIPE,
    text: bool = True,
    env: dict | None = None,
    **kwargs,
) -> subprocess.Popen:
    """Start a privileged process using GUI authentication.

    Args:
        argv: Command to run (without sudo prefix)
        stdin, stdout, stderr: Standard I/O streams
        text: Whether to use text mode
        env: Environment variables
        **kwargs: Additional Popen arguments

    Returns:
        subprocess.Popen object
    """
    if not argv:
        raise ValueError("No command provided")

    if not os.environ.get("DISPLAY"):
        raise OSError("GUI environment required for authentication")

    try:
        from .gui_auth_manager import elevated_popen_gui

        logger.info("Starting privileged process with GUI sudo")
        return elevated_popen_gui(
            argv,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            text=text,
            env=env,
            **kwargs,
        )
    except ImportError:
        raise ImportError("GUI authentication manager not available")
    except Exception as e:
        logger.error(f"Failed to start privileged process: {e}")
        raise RuntimeError(f"GUI authentication failed: {e}")


def cleanup_auth_session() -> None:
    """Clean up authentication session using GUI authentication manager."""
    try:
        # Lazy import to avoid circular imports
        from .gui_auth_manager import get_gui_auth_manager

        manager = get_gui_auth_manager()
        manager.cleanup_session()
        logger.info("GUI authentication session cleaned up")
    except ImportError:
        logger.debug("GUI authentication manager not available for cleanup")
    except Exception as e:
        logger.debug(f"Error cleaning up GUI authentication session: {e}")


def validate_auth_session() -> bool:
    """Validate authentication session using GUI authentication manager.

    Returns:
        True if authentication works, False otherwise
    """
    try:
        # Lazy import to avoid circular imports
        from .gui_auth_manager import get_gui_auth_manager

        manager = get_gui_auth_manager()
        session_info = manager.get_session_info()
        if session_info["active"]:
            logger.debug("GUI authentication session is active")
            return True
    except ImportError:
        logger.debug("GUI authentication manager not available for validation")
    except Exception as e:
        logger.debug(f"Error validating GUI authentication session: {e}")

    # Fallback to simple test
    try:
        result = elevated_run(["true"], timeout=30)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Authentication validation failed: {e}")
        return False


# Legacy aliases for backward compatibility
def _legacy_elevated_run(*args, **kwargs):
    """Legacy function - redirects to GUI sudo only."""
    logger.warning("Legacy function called - using GUI sudo only")
    return elevated_run(*args, **kwargs)


def _legacy_elevated_popen(*args, **kwargs):
    """Legacy function - redirects to GUI sudo only."""
    logger.warning("Legacy function called - using GUI sudo only")
    return elevated_popen(*args, **kwargs)
