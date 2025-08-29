"""Safe process termination helpers.
Provides validated, optionally elevated termination of processes with
minimal, auditable logic. Falls back to escalation only when required.
"""

from __future__ import annotations

import logging
import os
import signal
import time
from collections.abc import Sequence
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KillResult:
    success: bool
    escalated: bool
    attempts: list[str]
    error: str | None = None


_ALLOWED_SIGNALS = {
    signal.SIGTERM: "TERM",
    signal.SIGKILL: "KILL",
    signal.SIGINT: "INT",
    signal.SIGHUP: "HUP",
}


def _validate_pid(pid: int) -> None:
    if not isinstance(pid, int) or pid <= 0:
        raise ValueError("Invalid pid")
    # Upper bound heuristic to avoid absurd numbers (defense-in-depth)
    if pid > 1_000_000:
        raise ValueError("PID out of expected range")


def _signal_name(sig: int) -> str:
    return _ALLOWED_SIGNALS.get(sig, str(sig))


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but we lack permission
        return True


def safe_kill(
    pid: int, sig: int = signal.SIGTERM, *, escalate: bool = False, timeout: float = 2.0
) -> KillResult:
    """Send a single signal to a process, optionally escalating.

    escalate: if True, attempt privileged kill via elevated_run when PermissionError.
    timeout: wait this long for process to exit after non-KILL signals before returning.
    """
    attempts: list[str] = []
    try:
        _validate_pid(pid)
    except Exception as e:
        return KillResult(False, False, attempts, str(e))

    if not _process_exists(pid):
        return KillResult(True, False, attempts, None)

    sig_name = _signal_name(sig)
    try:
        os.kill(pid, sig)
        attempts.append(f"os.kill:{sig_name}")
    except PermissionError as e:
        attempts.append(f"os.kill-denied:{sig_name}")
        if not escalate:
            return KillResult(False, False, attempts, str(e))
        # escalate using elevated_run
        try:
            from .elevated_runner import elevated_run

            cp = elevated_run(
                ["kill", f"-{sig_name}", str(pid)],
                timeout=15,
                capture_output=True,
                gui=True,
            )
            attempts.append(f"elevated_run:{sig_name}:rc={cp.returncode}")
            if (
                cp.returncode == 0 or cp.returncode == 126
            ):  # 126=user cancelled auth; treat as soft-success
                return KillResult(
                    cp.returncode == 0,
                    True,
                    attempts,
                    None if cp.returncode == 0 else "auth_cancelled",
                )
            return KillResult(False, True, attempts, cp.stderr or "kill failed")
        except Exception as ee:  # pragma: no cover
            return KillResult(False, True, attempts, f"elevated error:{ee}")
    except ProcessLookupError:
        attempts.append(f"os.kill:notfound:{sig_name}")
        return KillResult(True, False, attempts, None)
    except Exception as e:  # pragma: no cover
        attempts.append(f"os.kill-error:{sig_name}")
        return KillResult(False, False, attempts, str(e))

    # Wait for exit if not SIGKILL
    if sig != signal.SIGKILL:
        end = time.time() + timeout
        while time.time() < end:
            if not _process_exists(pid):
                return KillResult(True, False, attempts, None)
            time.sleep(0.1)
        # still exists
        return KillResult(False, False, attempts, "timeout")
    return KillResult(True, False, attempts, None)


def kill_sequence(
    pid: int,
    signals: Sequence[int] | None = None,
    *,
    escalate: bool = False,
    per_signal_timeout: float = 2.0,
) -> KillResult:
    """Attempt a sequence of signals (default TERM then KILL). Returns first definitive result.

    If TERM fails or times out, escalates to KILL. Escalation to privileged only triggered
    when PermissionError on TERM and escalate=True.
    """
    if signals is None:
        signals = (signal.SIGTERM, signal.SIGKILL)
    all_attempts: list[str] = []
    last_err: str | None = None
    escalated = False
    for sig in signals:
        r = safe_kill(pid, sig, escalate=escalate, timeout=per_signal_timeout)
        all_attempts.extend(r.attempts)
        escalated = escalated or r.escalated
        # If validation failed (no attempts) capture error context for transparency
        if not r.attempts and r.error and not all_attempts:
            all_attempts.append(f"precheck-error:{r.error}")
        if r.success:
            return KillResult(True, escalated, all_attempts, None)
        last_err = r.error
        # If TERM timed out, continue to next (KILL)
        # If permission denied handled inside safe_kill with escalation decision.
    return KillResult(False, escalated, all_attempts, last_err)


__all__ = ["KillResult", "kill_sequence", "safe_kill"]
