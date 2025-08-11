"""Unified privileged command execution helper.

Provides a single abstraction for running commands with elevated privileges
preferring pkexec (GUI-friendly) and falling back to sudo variants.

Goals:
 - Centralize environment sanitization & allowlist style validation
 - Enforce timeouts
 - Provide consistent logging & optional JSON output compatibility
 - Minimize authentication prompts (reuse pkexec when available)

NOTE: This does NOT replace run_secure (non-privileged). Use run_secure for
regular commands. Use elevated_run only when privilege escalation is required.
"""
from __future__ import annotations
import os
import shlex
import subprocess
import logging
from pathlib import Path
from typing import Sequence, Mapping, Optional

logger = logging.getLogger(__name__)

SAFE_ENV_KEYS = {"LANG", "LC_ALL", "PATH", "DISPLAY", "XAUTHORITY"}
SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

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
                 env: Optional[Mapping[str, str]] = None) -> subprocess.CompletedProcess:
    """Execute a command with privileges.

    argv: base command (without pkexec/sudo). First element may be a script if allow_script True.
    gui: attempt GUI auth (pkexec) else fallback to sudo passwordless / terminal.
    allow_script: permit executing an absolute owner-only 0700 script outside allowlist.
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
            logger.debug("elevated_run attempting %s: %s", name, _format_cmd(full_cmd[:3] + ['...'] if len(full_cmd)>6 else full_cmd))
            cp = subprocess.run(full_cmd, timeout=timeout, capture_output=capture_output, text=text, env=env_used, check=False)
            attempted.append(name)
            last_cp = cp
            if cp.returncode == 0:
                logger.info("elevated_run success via %s", name)
                return cp
            if name.startswith("pkexec") and cp.returncode in (126,):
                logger.info("pkexec cancelled by user")
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

__all__ = ["elevated_run"]

def elevated_popen(argv: Sequence[str], *, gui: bool = True, allow_script: bool = False,
                   text: bool = True, env: Optional[Mapping[str, str]] = None,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize: int = 1) -> subprocess.Popen:
    """Start a privileged process returning Popen for streaming.

    Attempts pkexec first (GUI), then sudo -n, then sudo -A (if DISPLAY) then sudo.
    Caller handles reading output and waiting.
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
