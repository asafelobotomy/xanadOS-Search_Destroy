#!/usr/bin/env python3
"""
System Hardening Detection and Validation Module
xanadOS Search & Destroy - Enhanced Security Checks
This module implements comprehensive system hardening detection including:
- Kernel security features (KASLR, SMEP/SMAP)
- Lockdown mode status
- Mandatory Access Control (AppArmor - easier than SELinux)
- Critical sysctl security parameters
- Security compliance scoring
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SecurityFeature:
    """Represents a security feature with its status and details"""

    name: str
    enabled: bool
    status: str
    description: str
    recommendation: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    score_impact: int  # Points impact on security score


@dataclass
class HardeningReport:
    """Comprehensive system hardening report"""

    security_features: List[SecurityFeature]
    overall_score: int
    max_score: int
    compliance_level: str
    recommendations: List[str]
    critical_issues: List[str]
    timestamp: str


class SystemHardeningChecker:
    """Advanced system hardening detection and validation"""

    def __init__(self):
        self.proc_path = Path("/proc")
        self.sys_path = Path("/sys")
        self.security_features = {}
        self.sysctl_cache = {}

    def check_all_hardening_features(self) -> HardeningReport:
        """Perform comprehensive system hardening assessment"""
        logger.info("Starting comprehensive system hardening assessment")

        features = []

        # Kernel security features
        features.extend(self._check_kernel_security_features())

        # Lockdown mode
        features.extend(self._check_kernel_lockdown())

        # Mandatory Access Control
        features.extend(self._check_mandatory_access_control())

        # Critical sysctl parameters
        features.extend(self._check_critical_sysctl_params())

        # Additional security features
        features.extend(self._check_additional_security_features())

        # Calculate overall security score
        total_score = sum(f.score_impact for f in features if f.enabled)
        max_possible = sum(f.score_impact for f in features)

        # Determine compliance level
        score_percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
        if score_percentage >= 90:
            compliance_level = "Excellent"
        elif score_percentage >= 75:
            compliance_level = "Good"
        elif score_percentage >= 50:
            compliance_level = "Moderate"
        else:
            compliance_level = "Poor"

        # Generate recommendations - include medium, high, and critical severity features
        recommendations_raw = [
            f.recommendation
            for f in features
            if not f.enabled and f.severity in ["medium", "high", "critical"]
        ]
        # Remove duplicates while preserving order
        recommendations = []
        for rec in recommendations_raw:
            if rec not in recommendations:
                recommendations.append(rec)

        critical_issues = [
            f.name for f in features if not f.enabled and f.severity == "critical"
        ]

        from datetime import datetime

        report = HardeningReport(
            security_features=features,
            overall_score=total_score,
            max_score=max_possible,
            compliance_level=compliance_level,
            recommendations=recommendations[:10],  # Top 10 recommendations
            critical_issues=critical_issues,
            timestamp=datetime.now().isoformat(),
        )

        logger.info(
            f"System hardening assessment complete. Score: {total_score}/{max_possible} ({compliance_level})"
        )
        return report

    def _check_kernel_security_features(self) -> List[SecurityFeature]:
        """Check kernel-level security features (KASLR, SMEP/SMAP, etc.)"""
        features = []

        # Check KASLR (Kernel Address Space Layout Randomization)
        kaslr_status = self._check_kaslr()
        features.append(
            SecurityFeature(
                name="KASLR (Kernel Address Space Layout Randomization)",
                enabled=kaslr_status["enabled"],
                status=kaslr_status["status"],
                description="Randomizes kernel memory layout to prevent exploitation",
                recommendation=(
                    "Enable KASLR in kernel configuration"
                    if not kaslr_status["enabled"]
                    else "KASLR is properly configured"
                ),
                severity="high",
                score_impact=15,
            )
        )

        # Check SMEP/SMAP
        smep_smap = self._check_smep_smap()
        features.append(
            SecurityFeature(
                name="SMEP/SMAP (Supervisor Mode Execution/Access Prevention)",
                enabled=smep_smap["enabled"],
                status=smep_smap["status"],
                description="Prevents kernel from executing/accessing user-mode code",
                recommendation=(
                    "Ensure hardware supports and enables SMEP/SMAP"
                    if not smep_smap["enabled"]
                    else "SMEP/SMAP properly configured"
                ),
                severity="high",
                score_impact=20,
            )
        )

        # Check Stack Guard Pages
        stack_guard = self._check_stack_guard_pages()
        features.append(
            SecurityFeature(
                name="Kernel Stack Guard Pages",
                enabled=stack_guard["enabled"],
                status=stack_guard["status"],
                description="Prevents kernel stack overflow attacks",
                recommendation=(
                    "Enable CONFIG_VMAP_STACK in kernel"
                    if not stack_guard["enabled"]
                    else "Stack guard pages active"
                ),
                severity="medium",
                score_impact=10,
            )
        )

        # Check KASAN (Kernel Address Sanitizer)
        kasan = self._check_kasan()
        features.append(
            SecurityFeature(
                name="KASAN (Kernel Address Sanitizer)",
                enabled=kasan["enabled"],
                status=kasan["status"],
                description="Detects memory corruption in kernel code",
                recommendation=(
                    "Enable KASAN for development/testing environments"
                    if not kasan["enabled"]
                    else "KASAN is active"
                ),
                severity="low",
                score_impact=5,
            )
        )

        return features

    def _check_kernel_lockdown(self) -> List[SecurityFeature]:
        """Check kernel lockdown mode status"""
        features = []

        lockdown_status = self._get_lockdown_status()

        enabled = lockdown_status != "none"
        status_text = f"Lockdown mode: {lockdown_status}"

        if lockdown_status == "confidentiality":
            severity = "low"  # Best setting
            recommendation = "Kernel lockdown at maximum security level"
        elif lockdown_status == "integrity":
            severity = "medium"
            recommendation = (
                "Consider upgrading to 'confidentiality' mode for maximum security"
            )
        else:
            severity = "high"
            recommendation = "Enable kernel lockdown mode for enhanced security"

        features.append(
            SecurityFeature(
                name="Kernel Lockdown Mode",
                enabled=enabled,
                status=status_text,
                description="Restricts kernel modifications and debugging interfaces",
                recommendation=recommendation,
                severity=severity,
                score_impact=25,
            )
        )

        return features

    def _check_mandatory_access_control(self) -> List[SecurityFeature]:
        """Check AppArmor status - SELinux removed for simplicity"""
        features = []

        # Check AppArmor (SELinux removed - AppArmor is easier and more suitable)
        apparmor_status = self._check_apparmor()
        features.append(
            SecurityFeature(
                name="AppArmor (Application Armor)",
                enabled=apparmor_status["enabled"],
                status=apparmor_status["status"],
                description="Mandatory access control security architecture providing application security profiles",
                recommendation=apparmor_status["recommendation"],
                severity="medium",
                score_impact=15,
            )
        )

        return features

    def _check_critical_sysctl_params(self) -> List[SecurityFeature]:
        """Check critical sysctl security parameters"""
        features = []

        critical_sysctls = {
            "kernel.dmesg_restrict": {
                "expected": "1",
                "description": "Restricts dmesg access to privileged users",
                "severity": "medium",
                "score": 5,
            },
            "kernel.kptr_restrict": {
                "expected": "2",
                "description": "Restricts kernel pointer exposure",
                "severity": "high",
                "score": 10,
            },
            "kernel.yama.ptrace_scope": {
                "expected": "1",
                "description": "Restricts ptrace debugging capabilities",
                "severity": "medium",
                "score": 8,
            },
            "net.ipv4.conf.all.send_redirects": {
                "expected": "0",
                "description": "Prevents ICMP redirect sending",
                "severity": "medium",
                "score": 5,
            },
            "net.ipv4.conf.all.accept_redirects": {
                "expected": "0",
                "description": "Prevents ICMP redirect acceptance",
                "severity": "medium",
                "score": 5,
            },
            "net.ipv4.ip_forward": {
                "expected": "0",
                "description": "Disables IP forwarding unless needed",
                "severity": "low",
                "score": 3,
            },
        }

        for param, config in critical_sysctls.items():
            current_value = self._get_sysctl_value(param)
            enabled = current_value == config["expected"]

            status = (
                f"{param} = {current_value}" if current_value else f"{param} not found"
            )
            recommendation = (
                f"Set {param} = {config['expected']}"
                if not enabled
                else f"{param} properly configured"
            )

            features.append(
                SecurityFeature(
                    name=f"Sysctl: {param}",
                    enabled=enabled,
                    status=status,
                    description=config["description"],
                    recommendation=recommendation,
                    severity=config["severity"],
                    score_impact=config["score"],
                )
            )

        return features

    def _check_additional_security_features(self) -> List[SecurityFeature]:
        """Check additional security features"""
        features = []

        # Check ASLR
        aslr_status = self._check_aslr()
        features.append(
            SecurityFeature(
                name="ASLR (Address Space Layout Randomization)",
                enabled=aslr_status["enabled"],
                status=aslr_status["status"],
                description="Randomizes process memory layout",
                recommendation=(
                    "Enable full ASLR randomization"
                    if not aslr_status["enabled"]
                    else "ASLR properly configured"
                ),
                severity="high",
                score_impact=10,
            )
        )

        # Check Exec Shield / NX bit
        nx_status = self._check_nx_bit()
        features.append(
            SecurityFeature(
                name="NX Bit / DEP (Data Execution Prevention)",
                enabled=nx_status["enabled"],
                status=nx_status["status"],
                description="Prevents execution of data pages",
                recommendation=(
                    "Enable NX bit support in BIOS/UEFI"
                    if not nx_status["enabled"]
                    else "NX bit properly enabled"
                ),
                severity="high",
                score_impact=12,
            )
        )

        return features

    def _check_kaslr(self) -> Dict[str, Any]:
        """Check KASLR status"""
        try:
            # Check if KASLR is enabled via kernel command line
            with open("/proc/cmdline", "r") as f:
                cmdline = f.read().strip()

            # Check for KASLR in various ways
            kaslr_enabled = True

            if "nokaslr" in cmdline:
                kaslr_enabled = False
                status = "Disabled via kernel command line (nokaslr)"
            elif "kaslr" in cmdline:
                status = "Explicitly enabled via kernel command line"
            else:
                # Check kernel config if available
                if os.path.exists("/proc/config.gz"):
                    try:
                        result = subprocess.run(
                            ["zcat", "/proc/config.gz"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if "CONFIG_RANDOMIZE_BASE=y" in result.stdout:
                            status = "Enabled in kernel configuration"
                        else:
                            kaslr_enabled = False
                            status = "Not enabled in kernel configuration"
                    except BaseException:
                        status = "Status unknown - unable to check kernel config"
                else:
                    # Assume enabled on modern kernels unless explicitly disabled
                    status = "Likely enabled (modern kernel default)"

            return {"enabled": kaslr_enabled, "status": status}
        except Exception as e:
            logger.warning(f"Error checking KASLR: {e}")
            return {"enabled": False, "status": f"Error checking KASLR: {e}"}

    def _check_smep_smap(self) -> Dict[str, Any]:
        """Check SMEP/SMAP status"""
        try:
            # Check CPU flags for SMEP/SMAP support
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()

            flags = []
            for line in cpuinfo.split("\n"):
                if line.startswith("flags") or line.startswith("Features"):
                    flags.extend(line.split()[2:])  # Skip 'flags' and ':'

            smep_supported = "smep" in flags
            smap_supported = "smap" in flags

            if smep_supported and smap_supported:
                status = "SMEP and SMAP supported and likely enabled"
                enabled = True
            elif smep_supported:
                status = "SMEP supported, SMAP not available"
                enabled = True
            else:
                status = "SMEP/SMAP not supported by hardware"
                enabled = False

            return {"enabled": enabled, "status": status}
        except Exception as e:
            logger.warning(f"Error checking SMEP/SMAP: {e}")
            return {"enabled": False, "status": f"Error checking SMEP/SMAP: {e}"}

    def _check_stack_guard_pages(self) -> Dict[str, Any]:
        """Check kernel stack guard pages"""
        try:
            # Check if VMAP_STACK is enabled
            if os.path.exists("/proc/config.gz"):
                result = subprocess.run(
                    ["zcat", "/proc/config.gz"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if "CONFIG_VMAP_STACK=y" in result.stdout:
                    return {"enabled": True, "status": "VMAP_STACK enabled in kernel"}
                else:
                    return {"enabled": False, "status": "VMAP_STACK not enabled"}
            else:
                # Assume enabled on modern kernels
                return {"enabled": True, "status": "Likely enabled (modern kernel)"}
        except Exception as e:
            return {"enabled": False, "status": f"Error checking: {e}"}

    def _check_kasan(self) -> Dict[str, Any]:
        """Check KASAN status"""
        try:
            # KASAN is typically not enabled in production kernels
            if os.path.exists("/proc/config.gz"):
                result = subprocess.run(
                    ["zcat", "/proc/config.gz"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if "CONFIG_KASAN=y" in result.stdout:
                    return {"enabled": True, "status": "KASAN enabled in kernel"}
                else:
                    return {
                        "enabled": False,
                        "status": "KASAN not enabled (normal for production)",
                    }
            else:
                return {
                    "enabled": False,
                    "status": "KASAN typically disabled in production kernels",
                }
        except Exception as e:
            return {"enabled": False, "status": f"Error checking: {e}"}

    def _get_lockdown_status(self) -> str:
        """Get kernel lockdown mode status"""
        try:
            lockdown_files = [
                "/sys/kernel/security/lockdown",
                "/proc/sys/kernel/lockdown",
            ]

            for lockdown_file in lockdown_files:
                if os.path.exists(lockdown_file):
                    with open(lockdown_file, "r") as f:
                        content = f.read().strip()

                    # Parse lockdown status
                    if "[none]" in content:
                        return "none"
                    elif "[integrity]" in content:
                        return "integrity"
                    elif "[confidentiality]" in content:
                        return "confidentiality"
                    else:
                        return content

            return "none"
        except Exception as e:
            logger.warning(f"Error checking lockdown status: {e}")
            return "unknown"

    def _check_apparmor(self) -> Dict[str, Any]:
        """Check AppArmor status"""
        try:
            result = subprocess.run(
                ["aa-status"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                output = result.stdout
                if "profiles are loaded" in output:
                    # Parse the number of loaded profiles
                    match = re.search(r"(\d+) profiles are loaded", output)
                    if match:
                        profile_count = int(match.group(1))
                        enabled = profile_count > 0
                        status = f"AppArmor active with {profile_count} profiles loaded"
                        recommendation = (
                            "AppArmor is properly configured"
                            if enabled
                            else "Load AppArmor profiles"
                        )
                    else:
                        enabled = True
                        status = "AppArmor active"
                        recommendation = "AppArmor is running"
                else:
                    enabled = False
                    status = "AppArmor installed but no profiles loaded"
                    recommendation = "Load and configure AppArmor profiles"

                return {
                    "enabled": enabled,
                    "status": status,
                    "recommendation": recommendation,
                }
            else:
                return {
                    "enabled": False,
                    "status": "AppArmor not running",
                    "recommendation": "Start and configure AppArmor service",
                }
        except FileNotFoundError:
            return {
                "enabled": False,
                "status": "AppArmor not installed",
                "recommendation": "Install AppArmor if supported by distribution",
            }
        except Exception as e:
            return {
                "enabled": False,
                "status": f"Error checking AppArmor: {e}",
                "recommendation": "Investigate AppArmor configuration",
            }

    def _get_sysctl_value(self, param: str) -> Optional[str]:
        """Get sysctl parameter value"""
        if param in self.sysctl_cache:
            return self.sysctl_cache[param]

        try:
            result = subprocess.run(
                ["sysctl", "-n", param], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                value = result.stdout.strip()
                self.sysctl_cache[param] = value
                return value
            else:
                return None
        except Exception as e:
            logger.debug(f"Error getting sysctl {param}: {e}")
            return None

    def _check_aslr(self) -> Dict[str, Any]:
        """Check ASLR status"""
        aslr_value = self._get_sysctl_value("kernel.randomize_va_space")

        if aslr_value == "2":
            return {
                "enabled": True,
                "status": "ASLR fully enabled (randomize_va_space = 2)",
            }
        elif aslr_value == "1":
            return {
                "enabled": True,
                "status": "ASLR partially enabled (randomize_va_space = 1)",
            }
        elif aslr_value == "0":
            return {
                "enabled": False,
                "status": "ASLR disabled (randomize_va_space = 0)",
            }
        else:
            return {
                "enabled": False,
                "status": f"ASLR status unknown (randomize_va_space = {aslr_value})",
            }

    def _check_nx_bit(self) -> Dict[str, Any]:
        """Check NX bit / DEP status"""
        try:
            # Check CPU flags for NX support
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()

            # Look for NX-related flags
            nx_flags = ["nx", "xd"]  # nx for AMD, xd for Intel
            cpu_flags = []
            for line in cpuinfo.split("\n"):
                if line.startswith("flags"):
                    cpu_flags.extend(line.split()[2:])

            nx_supported = any(flag in cpu_flags for flag in nx_flags)

            if nx_supported:
                return {"enabled": True, "status": "NX bit supported and enabled"}
            else:
                return {"enabled": False, "status": "NX bit not supported or disabled"}
        except Exception as e:
            return {"enabled": False, "status": f"Error checking NX bit: {e}"}

    def get_hardening_recommendations(self, report: HardeningReport) -> List[str]:
        """Generate specific hardening recommendations based on report"""
        recommendations = []

        # Add specific recommendations based on missing features
        for feature in report.security_features:
            if not feature.enabled and feature.severity in ["high", "critical"]:
                recommendations.append(f"⚠️ {feature.name}: {feature.recommendation}")

        # Add general recommendations
        if report.overall_score < report.max_score * 0.5:
            recommendations.append(
                "🔐 Consider implementing a comprehensive security hardening plan"
            )
            recommendations.append(
                "📚 Review CIS benchmarks for your Linux distribution"
            )

        if report.overall_score < report.max_score * 0.75:
            recommendations.append("🛡️ Enable additional kernel security features")
            recommendations.append("🔍 Regular security auditing is recommended")

        return recommendations[:15]  # Limit to top 15 recommendations
