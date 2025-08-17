"""Unified privileged command execution helper.

Provides a single abstraction for running commands with elevated privileges
preferring pkexec (GUI-friendly) and falling back to sudo variants.

Goals:
 - Centralize environment sanitization & allowlist style validation
 - Enforce timeouts
 - Provide consistent logging & optional JSON output compatibility
 - Minimize authentication prompts (reuse sudo sessions across threads/processes)

NOTE: This does NOT replace run_secure (non-privileged). Use run_secure for
regular commands. Use elevated_run only when privilege escalation is required.
"""
from __future__ import annotations
import os
import shlex
import subprocess
import logging
import time
import tempfile
from pathlib import Path
from typing import Sequence, Mapping, Optional

logger = logging.getLogger(__name__)

SAFE_ENV_KEYS = {"LANG", "LC_ALL", "PATH", "DISPLAY", "XAUTHORITY"}
SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Session tracking file for cross-thread/process communication
_SESSION_FILE = os.path.join(tempfile.gettempdir(), f"xanados_sudo_session_{os.getuid()}")
_SESSION_TIMEOUT = 900  # 15 minutes (typical sudo timeout)

# Track which authentication method was used for the session
_AUTH_METHOD_FILE = os.path.join(tempfile.gettempdir(), f"xanados_auth_method_{os.getuid()}")

def _which(cmd: str) -> Optional[str]:
    from shutil import which
    return which(cmd)

def _sanitize_env(extra: Optional[Mapping[str, str]] = None, gui: bool = True) -> dict:
    env = {
        "PATH": SAFE_PATH,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if gui:
        # Pass through DISPLAY / XAUTHORITY if present and minimal
        d = os.environ.get("DISPLAY")
        if d and len(d) < 16 and d.startswith(":"):
            env["DISPLAY"] = d
        xa = os.environ.get("XAUTHORITY")
        if xa and xa.startswith(str(Path.home())):
            env["XAUTHORITY"] = xa
    if extra:
        for k, v in extra.items():
            if k in SAFE_ENV_KEYS and isinstance(v, str) and len(v) < 512:
                env[k] = v
    return env

def _validate_args(argv: Sequence[str]) -> None:
    if not argv:
        raise ValueError("Empty command")
    for a in argv:
        if any(ch in a for ch in [';','&&','||','`','$','>','<','|']):
            raise ValueError(f"Unsafe token in argument: {a}")

def _format_cmd(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(a) for a in argv)

def elevated_run(argv: Sequence[str], *, timeout: int = 300, capture_output: bool = True,
                 text: bool = True, gui: bool = True, allow_script: bool = False,
                 env: Optional[Mapping[str, str]] = None, prefer_sudo: bool = False) -> subprocess.CompletedProcess:
    """Execute a command with privileges.

    argv: base command (without pkexec/sudo). First element may be a script if allow_script True.
    gui: attempt GUI auth (pkexec) else fallback to sudo passwordless / terminal.
    allow_script: permit executing an absolute owner-only 0700 script outside allowlist.
    prefer_sudo: prefer sudo over pkexec for session reuse (useful for batch operations).
    """
    _validate_args(argv)

    prog = argv[0]
    prog_path = Path(prog)
    if prog_path.is_absolute():
        if not prog_path.exists():
            raise FileNotFoundError(prog)
        if allow_script:
            st = prog_path.stat()
            if st.st_mode & 0o077:
                raise PermissionError("Script has unsafe permissions")
            if st.st_uid != os.getuid():
                # We only allow running user-owned temp scripts through this path
                raise PermissionError("Script not owned by current user")
        else:
            # For absolute paths without allow_script, require binary in safe dirs
            if not any(str(prog_path).startswith(p) for p in ("/usr/bin/","/usr/sbin/","/bin/","/usr/local/bin/")):
                raise PermissionError("Absolute path outside trusted prefixes")

    pkexec = _which("pkexec") if gui else None
    sudo = _which("sudo")

    base_env = _sanitize_env(env, gui=gui)

    attempted = []
    errors = []

    methods: list[tuple[str,list[str],dict]] = []
    
    # Check current session and preferred authentication method
    session_active = _is_sudo_session_active()
    session_auth_method = _get_session_auth_method() if session_active else ""
    
    logger.info("🔍 Session check: active=%s, method='%s', prefer_sudo=%s", 
               session_active, session_auth_method, prefer_sudo)
    
    # Automatically prefer the same method used in the active session
    should_prefer_sudo = prefer_sudo or (session_active and session_auth_method == "sudo")
    should_prefer_pkexec = session_active and session_auth_method == "pkexec"
    
    if should_prefer_sudo:
        logger.info("🔄 Preferring sudo for session reuse (active=%s, method=%s, requested=%s)", 
                    session_active, session_auth_method, prefer_sudo)
    elif should_prefer_pkexec:
        logger.info("🔄 Preferring pkexec for session consistency (active=%s, method=%s)", 
                    session_active, session_auth_method)
    else:
        logger.info("🔄 Using default method priority (no active session or preference)")
    
    # Adjust method priority based on session consistency and preferences
    if should_prefer_pkexec and pkexec:
        # When pkexec session is active, use pkexec consistently
        logger.info("🔐 Using pkexec to maintain session consistency")
        env_wrap = [pkexec, "env"] + [f"{k}={v}" for k,v in base_env.items()]
        methods.append(("pkexec", env_wrap + list(argv), base_env))
        # Add sudo methods as fallback only
        if sudo:
            methods.append(("sudo -n", [sudo, "-n"] + list(argv), base_env))
            if gui and os.environ.get("DISPLAY"):
                askpass_helpers = [
                    "/usr/bin/ssh-askpass","/usr/bin/x11-ssh-askpass","/usr/bin/ksshaskpass","/usr/bin/lxqt-openssh-askpass"
                ]
                for helper in askpass_helpers:
                    if os.path.exists(helper):
                        e = dict(base_env)
                        e["SUDO_ASKPASS"] = helper
                        methods.append(("sudo -A", [sudo, "-A"] + list(argv), e))
                        break
            methods.append(("sudo", [sudo] + list(argv), base_env))
    elif should_prefer_sudo and sudo:
        # When prefer_sudo is True or sudo session is active, try sudo methods first for session reuse
        methods.append(("sudo -n", [sudo, "-n"] + list(argv), base_env))
        # sudo askpass (GUI) if DISPLAY present
        if gui and os.environ.get("DISPLAY"):
            askpass_helpers = [
                "/usr/bin/ssh-askpass","/usr/bin/x11-ssh-askpass","/usr/bin/ksshaskpass","/usr/bin/lxqt-openssh-askpass"
            ]
            for helper in askpass_helpers:
                if os.path.exists(helper):
                    e = dict(base_env)
                    e["SUDO_ASKPASS"] = helper
                    methods.append(("sudo -A", [sudo, "-A"] + list(argv), e))
                    break
        # plain sudo (may prompt in terminal)
        methods.append(("sudo", [sudo] + list(argv), base_env))
        # Add pkexec as fallback only if no sudo session is active
        if pkexec and not session_active:
            env_wrap = [pkexec, "env"] + [f"{k}={v}" for k,v in base_env.items()]
            methods.append(("pkexec", env_wrap + list(argv), base_env))
    else:
        # Default behavior: prefer pkexec for GUI-friendly experience
        if pkexec:
            # Use env wrapper so sanitized env applied
            env_wrap = [pkexec, "env"] + [f"{k}={v}" for k,v in base_env.items()]
            methods.append(("pkexec", env_wrap + list(argv), base_env))
        # passwordless sudo
        if sudo:
            methods.append(("sudo -n", [sudo, "-n"] + list(argv), base_env))
        # sudo askpass (GUI) if DISPLAY present
        if sudo and gui and os.environ.get("DISPLAY"):
            askpass_helpers = [
                "/usr/bin/ssh-askpass","/usr/bin/x11-ssh-askpass","/usr/bin/ksshaskpass","/usr/bin/lxqt-openssh-askpass"
            ]
            for helper in askpass_helpers:
                if os.path.exists(helper):
                    e = dict(base_env)
                    e["SUDO_ASKPASS"] = helper
                    methods.append(("sudo -A", [sudo, "-A"] + list(argv), e))
                    break
        # plain sudo (may prompt in terminal)
        if sudo:
            methods.append(("sudo", [sudo] + list(argv), base_env))

    last_cp: Optional[subprocess.CompletedProcess] = None
    for name, full_cmd, env_used in methods:
        try:
            logger.info("🚀 Attempting %s: %s", name, _format_cmd(full_cmd[:3] + ['...'] if len(full_cmd)>6 else full_cmd))
            cp = subprocess.run(full_cmd, timeout=timeout, capture_output=capture_output, text=text, env=env_used, check=False)
            attempted.append(name)
            last_cp = cp
            if cp.returncode == 0:
                logger.info("✅ elevated_run success via %s", name)
                # Mark session as active for future authentication reuse
                if name.startswith("sudo"):
                    _set_sudo_session_active(True)
                    logger.debug("Sudo session marked as active after successful authentication")
                return cp
            if name.startswith("pkexec") and cp.returncode in (126,):
                logger.info("❌ pkexec cancelled by user")
                return cp
            errors.append(f"{name} rc={cp.returncode}")
        except subprocess.TimeoutExpired:
            errors.append(f"{name} timeout")
        except Exception as e:  # pragma: no cover - defensive
            errors.append(f"{name} error:{e}")

    if last_cp is not None:
        if capture_output:
            combined_err = (last_cp.stderr or "") + f"\nAttempts: {', '.join(attempted)}; errors: {'; '.join(errors)}"
            last_cp.stderr = combined_err  # type: ignore[attr-defined]
        return last_cp
    return subprocess.CompletedProcess(argv, 1, stdout="", stderr="elevated_run failed: " + "; ".join(errors))

def validate_auth_session() -> bool:
    """
    Validate/refresh authentication session to minimize prompts.
    Uses GUI-friendly authentication methods when possible.
    Uses file-based session tracking for cross-thread/process communication.
    
    Returns:
        True if authentication is valid/refreshed, False otherwise
    """
    # First check if session is already active
    if _is_sudo_session_active():
        logger.debug("Authentication session already active")
        return True
        
    # Try GUI-friendly authentication first (pkexec), then sudo
    pkexec = _which("pkexec")
    sudo = _which("sudo")
    
    if not (pkexec or sudo):
        logger.error("No authentication method available (pkexec or sudo)")
        return False
    
    # Method 1: Try pkexec with a simple command (GUI-friendly)
    if pkexec:
        try:
            logger.info("🔐 Attempting GUI authentication with pkexec...")
            result = subprocess.run(
                [pkexec, "true"],  # Simple command to test authentication
                timeout=60,
                capture_output=True,
                text=True,
                env=_sanitize_env(gui=True)
            )
            
            logger.debug("pkexec result: returncode=%d, stdout='%s', stderr='%s'", 
                        result.returncode, result.stdout.strip(), result.stderr.strip())
            
            if result.returncode == 0:
                logger.info("✅ GUI authentication successful with pkexec")
                
                # Also establish a sudo session for subsequent command reuse
                # This prevents multiple pkexec prompts since pkexec doesn't persist sessions
                if sudo:
                    try:
                        logger.debug("Establishing sudo session after pkexec success...")
                        sudo_result = subprocess.run(
                            [sudo, "-v"],  # Validate/refresh sudo credentials
                            timeout=30,
                            capture_output=True,
                            text=True,
                            env=_sanitize_env(gui=True)
                        )
                        if sudo_result.returncode == 0:
                            logger.info("✅ Sudo session established for command reuse")
                            _set_sudo_session_active(True, "sudo")  # Use sudo for subsequent commands
                        else:
                            logger.debug("Sudo session establishment failed, keeping pkexec")
                            _set_sudo_session_active(True, "pkexec")
                    except Exception as e:
                        logger.debug("Error establishing sudo session: %s", e)
                        _set_sudo_session_active(True, "pkexec")
                else:
                    _set_sudo_session_active(True, "pkexec")
                
                return True
            elif result.returncode == 126:
                logger.info("❌ pkexec cancelled by user")
                return False
            else:
                logger.warning("❌ pkexec failed (rc=%d), trying sudo methods", result.returncode)
        except subprocess.TimeoutExpired:
            logger.warning("pkexec authentication timed out")
        except Exception as e:
            logger.debug("pkexec authentication error: %s", e)
    
    # Method 2: Try sudo with askpass helper (GUI-friendly)
    if sudo and os.environ.get("DISPLAY"):
        askpass_helpers = [
            "/usr/bin/ssh-askpass", "/usr/bin/x11-ssh-askpass", 
            "/usr/bin/ksshaskpass", "/usr/bin/lxqt-openssh-askpass"
        ]
        
        for helper in askpass_helpers:
            if os.path.exists(helper):
                try:
                    logger.debug("Attempting GUI authentication with sudo + %s", helper)
                    env = _sanitize_env(gui=True)
                    env["SUDO_ASKPASS"] = helper
                    result = subprocess.run(
                        [sudo, "-A", "-v"],  # -A uses askpass, -v validates credentials
                        timeout=60,
                        capture_output=True,
                        text=True,
                        env=env
                    )
                    
                    if result.returncode == 0:
                        logger.info("GUI authentication successful with sudo + askpass")
                        _set_sudo_session_active(True, "sudo")
                        return True
                    else:
                        logger.debug("sudo + askpass failed (rc=%d)", result.returncode)
                        
                except subprocess.TimeoutExpired:
                    logger.warning("sudo + askpass authentication timed out")
                except Exception as e:
                    logger.debug("sudo + askpass authentication error: %s", e)
                    
                # Only try the first available askpass helper
                break
    
    # Method 3: Fallback to regular sudo -v (may prompt in terminal)
    if sudo:
        try:
            logger.debug("Attempting terminal authentication with sudo -v")
            result = subprocess.run(
                [sudo, "-v"], 
                timeout=60,
                capture_output=True, 
                text=True,
                env=_sanitize_env(gui=True)
            )
            
            if result.returncode == 0:
                logger.info("Terminal authentication successful with sudo")
                _set_sudo_session_active(True, "sudo")
                return True
            else:
                logger.warning("Sudo authentication validation failed (rc=%d)", result.returncode)
                _set_sudo_session_active(False)
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("Sudo authentication validation timed out")
            _set_sudo_session_active(False)
            return False
        except Exception as e:
            logger.warning("Sudo authentication validation error: %s", e)
            _set_sudo_session_active(False)
            return False
    
    logger.error("All authentication methods failed")
    _set_sudo_session_active(False)
    return False

def _set_sudo_session_active(active: bool, auth_method: str = "sudo") -> None:
    """Set authentication session state using file-based tracking for cross-thread communication."""
    try:
        if active:
            # Create session file with current timestamp
            with open(_SESSION_FILE, 'w') as f:
                f.write(str(time.time()))
            # Set restrictive permissions (owner only)
            os.chmod(_SESSION_FILE, 0o600)
            
            # Store the authentication method used
            with open(_AUTH_METHOD_FILE, 'w') as f:
                f.write(auth_method)
            os.chmod(_AUTH_METHOD_FILE, 0o600)
            
            logger.debug("Authentication session file created: %s (method: %s)", _SESSION_FILE, auth_method)
        else:
            # Remove session files
            for filepath in [_SESSION_FILE, _AUTH_METHOD_FILE]:
                if os.path.exists(filepath):
                    os.unlink(filepath)
            logger.debug("Authentication session files removed")
    except Exception as e:
        logger.warning("Failed to update authentication session state: %s", e)

def _is_sudo_session_active() -> bool:
    """Check if sudo session is currently active using file-based tracking."""
    try:
        if not os.path.exists(_SESSION_FILE):
            return False
        
        # Check if session file is recent enough
        stat = os.stat(_SESSION_FILE)
        session_age = time.time() - stat.st_mtime
        
        if session_age > _SESSION_TIMEOUT:
            # Session too old, remove files
            try:
                for filepath in [_SESSION_FILE, _AUTH_METHOD_FILE]:
                    if os.path.exists(filepath):
                        os.unlink(filepath)
            except OSError:
                pass
            logger.debug("Authentication session expired (age: %.1fs)", session_age)
            return False
        
        logger.debug("Authentication session active (age: %.1fs)", session_age)
        return True
        
    except Exception as e:
        logger.warning("Failed to check authentication session state: %s", e)
        return False

def _get_session_auth_method() -> str:
    """Get the authentication method used for the current session."""
    try:
        if not _is_sudo_session_active():
            return ""
        
        if os.path.exists(_AUTH_METHOD_FILE):
            with open(_AUTH_METHOD_FILE, 'r') as f:
                return f.read().strip()
        return "sudo"  # Default fallback
    except Exception as e:
        logger.warning("Failed to get session auth method: %s", e)
        return ""

def cleanup_auth_session() -> None:
    """Clean up authentication session state (called on application exit)."""
    try:
        for filepath in [_SESSION_FILE, _AUTH_METHOD_FILE]:
            if os.path.exists(filepath):
                os.unlink(filepath)
        logger.debug("Authentication session cleaned up")
    except Exception as e:
        logger.warning("Failed to cleanup authentication session: %s", e)

__all__ = ["elevated_run", "validate_auth_session", "cleanup_auth_session", "elevated_popen"]

def elevated_popen(argv: Sequence[str], *, gui: bool = True, allow_script: bool = False,
                   text: bool = True, env: Optional[Mapping[str, str]] = None,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize: int = 1, prefer_sudo: bool = False) -> subprocess.Popen:
    """Start a privileged process returning Popen for streaming.

    Attempts pkexec first (GUI), then sudo -n, then sudo -A (if DISPLAY) then sudo.
    Caller handles reading output and waiting.
    prefer_sudo: prefer sudo over pkexec for session reuse (useful for batch operations).
    """
    _validate_args(argv)
    prog_path = Path(argv[0])
    if prog_path.is_absolute():
        if not prog_path.exists():
            raise FileNotFoundError(argv[0])
        if allow_script:
            st = prog_path.stat()
            if st.st_mode & 0o077:
                raise PermissionError("Script has unsafe permissions")
        else:
            if not any(str(prog_path).startswith(p) for p in ("/usr/bin/","/usr/sbin/","/bin/","/usr/local/bin/")):
                raise PermissionError("Absolute path outside trusted prefixes")

    pkexec = _which("pkexec") if gui else None
    sudo = _which("sudo")
    base_env = _sanitize_env(env, gui=gui)
    attempts: list[tuple[str,list[str],dict]] = []
    
    # Automatically prefer sudo if session is active, or if explicitly requested
    should_prefer_sudo = prefer_sudo or _is_sudo_session_active()
    
    if should_prefer_sudo:
        logger.debug("Preferring sudo for popen session reuse (active=%s, requested=%s)", 
                    _is_sudo_session_active(), prefer_sudo)
    
    # Adjust method priority based on prefer_sudo flag or active session
    if should_prefer_sudo and sudo:
        # When prefer_sudo is True or session is active, try sudo methods first for session reuse
        attempts.append(("sudo -n", [sudo, "-n"] + list(argv), base_env))
        if gui and os.environ.get("DISPLAY"):
            for helper in ["/usr/bin/ssh-askpass","/usr/bin/x11-ssh-askpass","/usr/bin/ksshaskpass","/usr/bin/lxqt-openssh-askpass"]:
                if os.path.exists(helper):
                    e = dict(base_env); e["SUDO_ASKPASS"] = helper
                    attempts.append(("sudo -A", [sudo, "-A"] + list(argv), e))
                    break
        attempts.append(("sudo", [sudo] + list(argv), base_env))
        # Add pkexec as fallback only if no sudo session is active
        if pkexec and not _is_sudo_session_active():
            env_wrap = [pkexec, "env"] + [f"{k}={v}" for k,v in base_env.items()]
            attempts.append(("pkexec", env_wrap + list(argv), base_env))
    else:
        # Default behavior: prefer pkexec for GUI-friendly experience
        if pkexec:
            env_wrap = [pkexec, "env"] + [f"{k}={v}" for k,v in base_env.items()]
            attempts.append(("pkexec", env_wrap + list(argv), base_env))
        if sudo:
            attempts.append(("sudo -n", [sudo, "-n"] + list(argv), base_env))
        if sudo and gui and os.environ.get("DISPLAY"):
            for helper in ["/usr/bin/ssh-askpass","/usr/bin/x11-ssh-askpass","/usr/bin/ksshaskpass","/usr/bin/lxqt-openssh-askpass"]:
                if os.path.exists(helper):
                    e = dict(base_env); e["SUDO_ASKPASS"] = helper
                    attempts.append(("sudo -A", [sudo, "-A"] + list(argv), e))
                    break
        if sudo:
            attempts.append(("sudo", [sudo] + list(argv), base_env))

    last_err: Exception | None = None
    for name, full_cmd, env_used in attempts:
        try:
            logger.debug("elevated_popen attempting %s: %s", name, _format_cmd(full_cmd[:3] + ['...'] if len(full_cmd)>6 else full_cmd))
            return subprocess.Popen(full_cmd, text=text, stdout=stdout, stderr=stderr, bufsize=bufsize, env=env_used)
        except Exception as e:  # pragma: no cover
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("elevated_popen: no execution path available")

__all__.append("elevated_popen")
