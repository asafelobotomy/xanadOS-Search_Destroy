"""
Security audit logging for xanadOS Search & Destroy.

Comprehensive logging of all security-relevant events for forensics
and compliance. Follows NIST 800-53 logging requirements.

Author: xanadOS Security Team
Date: 2025-12-17
Phase: 2 (HIGH severity - CWE-778 mitigation)
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import os
import getpass

# Security event log location
SECURITY_LOG_DIR = (
    Path.home() / ".local" / "share" / "search-and-destroy" / "security-logs"
)
SECURITY_LOG_FILE = SECURITY_LOG_DIR / "security_events.log"


class SecurityAuditLogger:
    """
    Centralized security audit logging.

    Logs all security-relevant events with structured data for analysis.

    Event Categories:
    - Authentication (login, logout, failed auth)
    - Authorization (privilege escalation, access denied)
    - Data Access (quarantine, scan results)
    - System Changes (configuration, policy updates)
    - Security Events (threats detected, malware quarantined)
    """

    def __init__(self, log_file: Path | None = None):
        """Initialize security audit logger."""
        self.log_file = log_file or SECURITY_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Configure logger
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)

        # File handler with secure permissions
        handler = logging.FileHandler(self.log_file, mode="a")
        handler.setLevel(logging.INFO)

        # Structured JSON format
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

        # Set secure file permissions
        try:
            os.chmod(self.log_file, 0o600)
        except Exception:
            pass

    def _log_event(
        self,
        event_type: str,
        action: str,
        result: str,
        details: dict[str, Any] | None = None,
        severity: str = "INFO",
    ) -> None:
        """
        Log a security event.

        Args:
            event_type: Category (AUTH, AUTHZ, DATA_ACCESS, SYSTEM_CHANGE, THREAT)
            action: Specific action taken
            result: SUCCESS, FAILURE, DENIED
            details: Additional event details
            severity: INFO, WARNING, ERROR, CRITICAL
        """
        event = {
            "event_type": event_type,
            "action": action,
            "result": result,
            "user": getpass.getuser(),
            "pid": os.getpid(),
            "details": details or {},
        }

        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(json.dumps(event))

    # ============ Authentication Events ============

    def log_authentication(
        self, user: str, method: str, success: bool, details: dict | None = None
    ):
        """Log authentication attempt."""
        self._log_event(
            event_type="AUTH",
            action=f"authentication_{method}",
            result="SUCCESS" if success else "FAILURE",
            details={"user": user, **(details or {})},
            severity="INFO" if success else "WARNING",
        )

    # ============ Authorization Events ============

    def log_privilege_escalation(
        self, command: str, method: str, success: bool, reason: str | None = None
    ):
        """Log privilege escalation attempt."""
        self._log_event(
            event_type="AUTHZ",
            action="privilege_escalation",
            result="SUCCESS" if success else "DENIED",
            details={"command": command, "method": method, "reason": reason},
            severity="WARNING" if success else "ERROR",
        )

    def log_access_denied(self, resource: str, action: str, reason: str):
        """Log access denial."""
        self._log_event(
            event_type="AUTHZ",
            action=f"access_denied_{action}",
            result="DENIED",
            details={"resource": resource, "reason": reason},
            severity="WARNING",
        )

    # ============ Data Access Events ============

    def log_quarantine_access(
        self,
        action: str,
        file_path: str,
        quarantine_id: str | None = None,
        success: bool = True,
    ):
        """Log quarantine file access."""
        self._log_event(
            event_type="DATA_ACCESS",
            action=f"quarantine_{action}",
            result="SUCCESS" if success else "FAILURE",
            details={"file_path": file_path, "quarantine_id": quarantine_id},
            severity="INFO",
        )

    def log_scan_result_access(self, scan_id: str, files_accessed: int):
        """Log scan result data access."""
        self._log_event(
            event_type="DATA_ACCESS",
            action="scan_results_viewed",
            result="SUCCESS",
            details={"scan_id": scan_id, "files_accessed": files_accessed},
        )

    # ============ System Change Events ============

    def log_configuration_change(
        self,
        setting: str,
        old_value: Any,
        new_value: Any,
        changed_by: str | None = None,
    ):
        """Log configuration change."""
        self._log_event(
            event_type="SYSTEM_CHANGE",
            action="configuration_modified",
            result="SUCCESS",
            details={
                "setting": setting,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "changed_by": changed_by or getpass.getuser(),
            },
            severity="WARNING",
        )

    def log_policy_update(self, policy_file: str, action: str):
        """Log security policy update."""
        self._log_event(
            event_type="SYSTEM_CHANGE",
            action=f"policy_{action}",
            result="SUCCESS",
            details={"policy_file": policy_file},
            severity="WARNING",
        )

    # ============ Security Events ============

    def log_threat_detected(
        self,
        file_path: str,
        threat_name: str,
        threat_level: str,
        scanner: str,
        quarantined: bool = False,
    ):
        """Log threat detection."""
        self._log_event(
            event_type="THREAT",
            action="threat_detected",
            result="QUARANTINED" if quarantined else "DETECTED",
            details={
                "file_path": file_path,
                "threat_name": threat_name,
                "threat_level": threat_level,
                "scanner": scanner,
                "quarantined": quarantined,
            },
            severity="CRITICAL" if threat_level == "HIGH" else "WARNING",
        )

    def log_malware_quarantined(
        self, original_path: str, quarantine_id: str, threat_name: str, file_size: int
    ):
        """Log malware quarantine action."""
        self._log_event(
            event_type="THREAT",
            action="malware_quarantined",
            result="SUCCESS",
            details={
                "original_path": original_path,
                "quarantine_id": quarantine_id,
                "threat_name": threat_name,
                "file_size": file_size,
            },
            severity="WARNING",
        )

    def log_security_scan(
        self,
        scan_type: str,
        target: str,
        files_scanned: int,
        threats_found: int,
        duration_seconds: float,
    ):
        """Log security scan completion."""
        self._log_event(
            event_type="THREAT",
            action=f"scan_{scan_type}_completed",
            result="SUCCESS",
            details={
                "target": target,
                "files_scanned": files_scanned,
                "threats_found": threats_found,
                "duration_seconds": duration_seconds,
            },
            severity="WARNING" if threats_found > 0 else "INFO",
        )

    # ============ Anomaly Detection ============

    def log_anomaly(
        self,
        anomaly_type: str,
        description: str,
        severity: str = "WARNING",
        details: dict | None = None,
    ):
        """Log detected anomaly."""
        self._log_event(
            event_type="ANOMALY",
            action=f"anomaly_{anomaly_type}",
            result="DETECTED",
            details={"description": description, **(details or {})},
            severity=severity,
        )


# Global audit logger instance
_audit_logger: Optional[SecurityAuditLogger] = None


def get_audit_logger() -> SecurityAuditLogger:
    """Get global security audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SecurityAuditLogger()
    return _audit_logger


# Convenience functions
def log_threat_detected(file_path: str, threat_name: str, **kwargs):
    """Convenience function for logging threats."""
    get_audit_logger().log_threat_detected(file_path, threat_name, **kwargs)


def log_quarantine(
    original_path: str, quarantine_id: str, threat_name: str, file_size: int
):
    """Convenience function for logging quarantine."""
    get_audit_logger().log_malware_quarantined(
        original_path, quarantine_id, threat_name, file_size
    )


def log_privilege_escalation(command: str, method: str, success: bool):
    """Convenience function for logging privilege escalation."""
    get_audit_logger().log_privilege_escalation(command, method, success)


# Example usage
if __name__ == "__main__":
    logger = SecurityAuditLogger()

    # Example events
    logger.log_threat_detected(
        file_path="/tmp/malware.exe",
        threat_name="Trojan.Generic",
        threat_level="HIGH",
        scanner="ClamAV",
        quarantined=True,
    )

    logger.log_privilege_escalation(
        command="systemctl restart clamav-daemon", method="pkexec", success=True
    )

    logger.log_configuration_change(setting="scan_depth", old_value=10, new_value=15)

    print(f"✅ Security events logged to: {SECURITY_LOG_FILE}")
