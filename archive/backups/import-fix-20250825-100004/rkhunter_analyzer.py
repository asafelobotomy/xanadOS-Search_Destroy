#!/usr/bin/env python3
"""
RKHunter Warning Analysis and Explanation System
Provides intelligent categorization and explanations for RKHunter warnings
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class WarningCategory(Enum):
    """Categories of RKHunter warnings."""
    SCRIPT_REPLACEMENT = "script_replacement"
    FILE_MODIFICATION = "file_modification"
    HIDDEN_FILE = "hidden_file"
    NETWORK_CONFIG = "network_config"
    PERMISSION_CHANGE = "permission_change"
    MISSING_FILE = "missing_file"
    SUSPICIOUS_PROCESS = "suspicious_process"
    ROOTKIT_SIGNATURE = "rootkit_signature"
    CONFIG_CHANGE = "config_change"
    UNKNOWN = "unknown"


class SeverityLevel(Enum):
    """Severity levels for warnings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WarningExplanation:
    """Detailed explanation of a warning."""
    category: WarningCategory
    severity: SeverityLevel
    title: str
    description: str
    likely_cause: str
    recommended_action: str
    is_common: bool
    technical_details: str = ""
    remediation_steps: Optional[List[str]] = None

    def __post_init__(self):
        if self.remediation_steps is None:
            self.remediation_steps = []


class RKHunterWarningAnalyzer:
    """Analyzes and explains RKHunter warnings."""

    def __init__(self):
        self.warning_patterns = self._initialize_warning_patterns()

    def _initialize_warning_patterns(self) -> List[Tuple[re.Pattern, WarningExplanation]]:
        """Initialize warning pattern matching rules."""
        patterns = []

        # Script replacement warnings
        patterns.append((
            re.compile(r"The command '([^']+)' has been replaced by a script", re.IGNORECASE),
            WarningExplanation(
                category=WarningCategory.SCRIPT_REPLACEMENT,
                severity=SeverityLevel.LOW,
                title="System Command Replaced by Script",
                description="A system command has been replaced with a script version",
                likely_cause="Package manager update (pacman, apt, yum) replaced binary with script wrapper",
                recommended_action="Usually safe if you recently updated your system. Check if replacement is legitimate.",
                is_common=True,
                technical_details="Modern package managers often replace commands with script wrappers for compatibility",
                remediation_steps=[
                    "Check recent system updates",
                    "Verify script contents if concerned",
                    "Use 'rkhunter --propupd' to update database after confirming legitimacy"
                ]
            )
        ))

        # Hidden file warnings
        patterns.append((
            re.compile(r"Hidden file found: ([^:]+):", re.IGNORECASE),
            WarningExplanation(
                category=WarningCategory.HIDDEN_FILE,
                severity=SeverityLevel.MEDIUM,
                title="Hidden File Detected",
                description="A hidden file (starting with '.') was found in a system directory",
                likely_cause="System configuration files, package installation artifacts, or potentially malicious files",
                recommended_action="Investigate the file contents and purpose. Check if it belongs to a legitimate application.",
                is_common=True,
                technical_details="Hidden files in system directories can be legitimate config files or signs of tampering",
                remediation_steps=[
                    "Examine file contents with 'cat' or 'less'",
                    "Check file ownership and permissions",
                    "Research online if file is known legitimate component",
                    "Remove if confirmed malicious"
                ]
            )
        ))

        # File property changes
        patterns.append((
            re.compile(r"The file properties have changed:", re.IGNORECASE),
            WarningExplanation(
                category=WarningCategory.FILE_MODIFICATION,
                severity=SeverityLevel.MEDIUM,
                title="File Properties Modified",
                description="System file permissions, size, or other properties have changed",
                likely_cause="System updates, security patches, or manual configuration changes",
                recommended_action="Review the specific changes. Update RKHunter database if changes are legitimate.",
                is_common=True,
                technical_details="File property changes often occur during system updates or maintenance",
                remediation_steps=[
                    "Check what specific properties changed",
                    "Verify if changes coincide with recent updates",
                    "Run 'rkhunter --propupd' if changes are legitimate",
                    "Investigate further if no recent system changes"
                ]
            )
        ))

        # SSH configuration warnings
        patterns.append((
            re.compile(r"SSH configuration option '([^']+)' has not been set", re.IGNORECASE),
            WarningExplanation(
                category=WarningCategory.CONFIG_CHANGE,
                severity=SeverityLevel.MEDIUM,
                title="SSH Security Configuration Missing",
                description="Important SSH security settings are not explicitly configured",
                likely_cause="Default SSH configuration may allow insecure settings",
                recommended_action="Review and harden SSH configuration for better security.",
                is_common=True,
                technical_details="SSH defaults may allow less secure protocols or authentication methods",
                remediation_steps=[
                    "Edit /etc/ssh/sshd_config",
                    "Set explicit values for security options",
                    "Restart SSH service after changes",
                    "Test SSH access after configuration changes"
                ]
            )
        ))

        # Passwd/group file warnings
        patterns.append((
            re.compile(r"Unable to check for (passwd|group) file differences", re.IGNORECASE),
            WarningExplanation(
                category=WarningCategory.MISSING_FILE,
                severity=SeverityLevel.LOW,
                title="Baseline File Missing",
                description="RKHunter cannot find its baseline copy of system authentication files",
                likely_cause="First run of RKHunter or missing baseline database",
                recommended_action="Run RKHunter database initialization to create baseline files.",
                is_common=True,
                technical_details="RKHunter needs baseline copies to detect changes in critical system files",
                remediation_steps=[
                    "Run 'sudo rkhunter --propupd' to update database",
                    "Run 'sudo rkhunter --check' again to verify",
                    "This warning should not appear on subsequent scans"
                ]
            )
        ))

        # Network listening warnings
        patterns.append((
            re.compile(r"listening on the network", re.IGNORECASE),
            WarningExplanation(
                category=WarningCategory.NETWORK_CONFIG,
                severity=SeverityLevel.HIGH,
                title="Unexpected Network Service",
                description="A process is listening for network connections",
                likely_cause="New service installation, malware, or configuration change",
                recommended_action="Identify the process and verify its legitimacy. Disable if unnecessary.",
                is_common=False,
                technical_details="Unexpected network listeners can indicate malware or misconfiguration",
                remediation_steps=[
                    "Use 'netstat -tulnp' to identify the process",
                    "Research the process name and purpose",
                    "Disable service if not needed",
                    "Check for malware if process is suspicious"
                ]
            )
        ))

        # Rootkit signature detection
        patterns.append((
            re.compile(r"(rootkit|backdoor|trojan)", re.IGNORECASE),
            WarningExplanation(
                category=WarningCategory.ROOTKIT_SIGNATURE,
                severity=SeverityLevel.CRITICAL,
                title="Potential Rootkit Detected",
                description="RKHunter found signatures or behaviors associated with known rootkits",
                likely_cause="System compromise, malware infection, or false positive",
                recommended_action="IMMEDIATE ACTION REQUIRED: Isolate system and perform thorough investigation.",
                is_common=False,
                technical_details="Rootkit detection requires immediate attention and professional analysis",
                remediation_steps=[
                    "Disconnect system from network immediately",
                    "Boot from rescue media for analysis",
                    "Run multiple antimalware tools",
                    "Consider full system rebuild if confirmed",
                    "Consult security professionals"
                ]
            )
        ))

        return patterns

    def analyze_warning(self, warning_text: str) -> WarningExplanation:
        """Analyze a warning and return detailed explanation."""
        warning_text = warning_text.strip()

        # Try to match against known patterns
        for pattern, explanation in self.warning_patterns:
            if pattern.search(warning_text):
                return explanation

        # Default explanation for unknown warnings
        return WarningExplanation(
            category=WarningCategory.UNKNOWN,
            severity=SeverityLevel.MEDIUM,
            title="Unknown Warning",
            description="RKHunter detected an issue that doesn't match common patterns",
            likely_cause="System change, configuration modification, or potential security issue",
            recommended_action="Research the specific warning message and investigate the underlying cause.",
            is_common=False,
            technical_details="Unknown warnings require manual investigation to determine significance",
            remediation_steps=[
                "Research the warning message online",
                "Check RKHunter documentation",
                "Review recent system changes",
                "Consult security forums or professionals if concerned"
            ]
        )

    def get_severity_color(self, severity: SeverityLevel) -> str:
        """Get color code for severity level."""
        colors = {
            SeverityLevel.LOW: "#28a745",      # Green
            SeverityLevel.MEDIUM: "#ffc107",   # Yellow
            SeverityLevel.HIGH: "#fd7e14",     # Orange
            SeverityLevel.CRITICAL: "#dc3545"  # Red
        }
        return colors.get(severity, "#6c757d")  # Gray default

    def get_severity_icon(self, severity: SeverityLevel) -> str:
        """Get icon for severity level."""
        icons = {
            SeverityLevel.LOW: "ℹ️",
            SeverityLevel.MEDIUM: "⚠️",
            SeverityLevel.HIGH: "🚨",
            SeverityLevel.CRITICAL: "🔴"
        }
        return icons.get(severity, "❓")

    def format_explanation(self, explanation: WarningExplanation, warning_text: str) -> str:
        """Format explanation as readable text."""
        icon = self.get_severity_icon(explanation.severity)

        formatted = f"""
{icon} {explanation.title}

📋 Category: {explanation.category.value.replace('_', ' ').title()}
🔍 Severity: {explanation.severity.value.upper()}
{'🔄 Common Issue' if explanation.is_common else '⚠️ Uncommon Issue'}

💡 What this means:
{explanation.description}

🤔 Likely cause:
{explanation.likely_cause}

✅ Recommended action:
{explanation.recommended_action}
"""

        if explanation.remediation_steps:
            formatted += "\n🛠️ Step-by-step remediation:\n"
            for i, step in enumerate(explanation.remediation_steps, 1):
                formatted += f"   {i}. {step}\n"

        if explanation.technical_details:
            formatted += f"\n🔧 Technical details:\n{explanation.technical_details}\n"

        return formatted
