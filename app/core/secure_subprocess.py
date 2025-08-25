"""Secure subprocess execution helpers.
Centralizes command execution with:
- Allowlist enforcement / pattern validation
- Default timeouts
- Sanitized environment (PATH, no dangerous overrides)
- Optional root elevation prevention
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from typing import Mapping, Optional, Sequence

DEFAULT_TIMEOUT = 60
SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Simple allowlist of binaries we expect to call; expand as needed.
ALLOWED_BINARIES = {
    "clamscan",
    "freshclam",
    "rkhunter",
    "systemctl",
    "kill",
    "pkexec",  # still allow, but can gate
    "sudo",  # consider removing; prefer pkexec GUI
    "ufw",
    "firewall-cmd",
    "iptables",
    "nft",
    "pkcheck",
    "chkconfig",
    "journalctl",
    "gpg",
    "start",  # upstart utilities
    "stop",
    "restart",
    "sigtool",
}

# Simple disallowed pattern for arguments (shell metachars not expected in argv elements)
_ARG_UNSAFE_RE = re.compile(r"[;&|><`$(){}]\s*")


def _is_allowed(argv: Sequence[str]) -> bool:
    if not argv:
        return False
    prog = argv[0]
    # Absolute path -> take basename for allowlist check
    base = os.path.basename(prog)
    return base in ALLOWED_BINARIES


def _sanitized_env(extra: Optional[Mapping[str, str]] = None) -> Mapping[str, str]:
    env = {
        "PATH": SAFE_PATH,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if extra:
        env.update({k: v for k, v in extra.items() if k.isupper() and ".." not in v})
    return env


def run_secure(
    argv: Sequence[str],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    check: bool = False,
    allow_root: bool = False,
    env: Optional[Mapping[str, str]] = None,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess with security constraints.

    Raises ValueError if binary not in allowlist.
    Disallows running as root unless allow_root is True (when current euid == 0).
    """
    if not _is_allowed(argv):
        raise ValueError(f"Attempt to execute non-allowed binary: {argv[0]}")
    if os.name == "posix" and os.geteuid() == 0 and not allow_root:
        raise PermissionError(f"Refusing to execute as root: {argv[0]}")
    # Argument sanitation
    for arg in argv[1:]:  # skip program path
        if _ARG_UNSAFE_RE.search(arg):
            raise ValueError(f"Unsafe characters in argument: {arg}")
    proc = subprocess.run(
        list(argv),
        timeout=timeout,
        check=check,
        env=_sanitized_env(env),
        capture_output=capture_output,
        text=text,
    )
    return proc


def quote_for_logging(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(a) for a in argv)


__all__ = [
    "run_secure",
    "quote_for_logging",
]


def popen_secure(
    argv: Sequence[str],
    *,
    allow_root: bool = False,
    env: Optional[Mapping[str, str]] = None,
    text: bool = True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize: int = 1,
) -> subprocess.Popen:
    """Popen variant with same security constraints as run_secure.

    Returns a subprocess.Popen object. Caller responsible for communicating / waiting.
    """
    if not _is_allowed(argv):
        raise ValueError(f"Attempt to execute non-allowed binary: {argv[0]}")
    if os.name == "posix" and os.geteuid() == 0 and not allow_root:
        raise PermissionError(f"Refusing to execute as root: {argv[0]}")
    for arg in argv[1:]:
        if _ARG_UNSAFE_RE.search(arg):
            raise ValueError(f"Unsafe characters in argument: {arg}")
    return subprocess.Popen(
        list(argv),
        env=_sanitized_env(env),
        text=text,
        stdout=stdout,
        stderr=stderr,
        bufsize=bufsize,
    )


__all__.append("popen_secure")
