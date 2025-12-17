#!/usr/bin/env python3
"""
Compliance Frameworks Module

Provides comprehensive compliance assessment, gap analysis, and remediation tracking
for 6 major security frameworks:
- NIST Cybersecurity Framework (CSF)
- CIS Critical Security Controls v8
- HIPAA (Healthcare)
- SOC 2 Type II
- FedRAMP (Federal Risk and Authorization Management Program)
- Custom Framework Builder

Features:
- Automated control assessments
- Gap analysis with prioritization
- Remediation roadmap generation
- Evidence collection tracking
- Control mapping across frameworks
- Executive dashboards and audit reports

Integration:
- app/reporting/web_reports.py - HTML/PDF report generation
- app/reporting/trend_analysis.py - Compliance trend tracking
- app/core/compliance_reporting.py - Base compliance infrastructure
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ================== FRAMEWORK DEFINITIONS ==================


class FrameworkType(Enum):
    """Supported compliance frameworks."""

    NIST_CSF = "nist_csf"
    CIS_CONTROLS = "cis_controls"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    FEDRAMP = "fedramp"
    CUSTOM = "custom"


class ControlStatus(Enum):
    """Control implementation status."""

    IMPLEMENTED = "implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"
    IN_PROGRESS = "in_progress"
    NOT_ASSESSED = "not_assessed"


class ComplianceLevel(Enum):
    """Compliance assessment levels."""

    COMPLIANT = "compliant"  # 90-100%
    MOSTLY_COMPLIANT = "mostly_compliant"  # 70-89%
    PARTIALLY_COMPLIANT = "partially_compliant"  # 50-69%
    NON_COMPLIANT = "non_compliant"  # <50%
    NOT_ASSESSED = "not_assessed"


class RiskLevel(Enum):
    """Risk levels for compliance gaps."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


# ================== DATA MODELS ==================


@dataclass
class ComplianceControl:
    """Individual control within a framework."""

    control_id: str
    framework: FrameworkType
    title: str
    description: str
    category: str
    subcategory: str = ""
    implementation_guidance: str = ""
    required_evidence: list[str] = field(default_factory=list)
    automated_check: bool = False
    priority: RiskLevel = RiskLevel.MEDIUM
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "control_id": self.control_id,
            "framework": self.framework.value,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "implementation_guidance": self.implementation_guidance,
            "required_evidence": self.required_evidence,
            "automated_check": self.automated_check,
            "priority": self.priority.value,
            "metadata": self.metadata,
        }


@dataclass
class ControlAssessment:
    """Assessment result for a control."""

    control_id: str
    status: ControlStatus
    compliance_score: float  # 0.0-1.0
    assessment_date: datetime
    evidence_provided: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    assessor: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "control_id": self.control_id,
            "status": self.status.value,
            "compliance_score": self.compliance_score,
            "assessment_date": self.assessment_date.isoformat(),
            "evidence_provided": self.evidence_provided,
            "findings": self.findings,
            "assessor": self.assessor,
            "notes": self.notes,
        }


@dataclass
class ComplianceGap:
    """Identified compliance gap requiring remediation."""

    gap_id: str
    control_id: str
    framework: FrameworkType
    title: str
    description: str
    risk_level: RiskLevel
    current_state: str
    desired_state: str
    remediation_steps: list[str] = field(default_factory=list)
    estimated_effort_hours: int = 0
    target_completion_date: datetime | None = None
    assigned_to: str = ""
    status: str = "open"  # open, in_progress, resolved, accepted_risk

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gap_id": self.gap_id,
            "control_id": self.control_id,
            "framework": self.framework.value,
            "title": self.title,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "current_state": self.current_state,
            "desired_state": self.desired_state,
            "remediation_steps": self.remediation_steps,
            "estimated_effort_hours": self.estimated_effort_hours,
            "target_completion_date": (
                self.target_completion_date.isoformat()
                if self.target_completion_date
                else None
            ),
            "assigned_to": self.assigned_to,
            "status": self.status,
        }


@dataclass
class RemediationRoadmap:
    """Prioritized plan for addressing compliance gaps."""

    framework: FrameworkType
    gaps: list[ComplianceGap]
    total_effort_hours: int
    estimated_completion_date: datetime
    phases: list[dict[str, Any]] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework": self.framework.value,
            "gaps": [gap.to_dict() for gap in self.gaps],
            "total_effort_hours": self.total_effort_hours,
            "estimated_completion_date": self.estimated_completion_date.isoformat(),
            "phases": self.phases,
            "dependencies": self.dependencies,
        }


@dataclass
class FrameworkAssessment:
    """Complete assessment of a compliance framework."""

    framework: FrameworkType
    assessment_date: datetime
    overall_score: float  # 0.0-1.0
    compliance_level: ComplianceLevel
    total_controls: int
    implemented_controls: int
    partially_implemented_controls: int
    not_implemented_controls: int
    control_assessments: list[ControlAssessment] = field(default_factory=list)
    gaps: list[ComplianceGap] = field(default_factory=list)
    remediation_roadmap: RemediationRoadmap | None = None
    recommendations: list[str] = field(default_factory=list)
    next_assessment_date: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework": self.framework.value,
            "assessment_date": self.assessment_date.isoformat(),
            "overall_score": self.overall_score,
            "compliance_level": self.compliance_level.value,
            "total_controls": self.total_controls,
            "implemented_controls": self.implemented_controls,
            "partially_implemented_controls": self.partially_implemented_controls,
            "not_implemented_controls": self.not_implemented_controls,
            "control_assessments": [
                assessment.to_dict() for assessment in self.control_assessments
            ],
            "gaps": [gap.to_dict() for gap in self.gaps],
            "remediation_roadmap": (
                self.remediation_roadmap.to_dict() if self.remediation_roadmap else None
            ),
            "recommendations": self.recommendations,
            "next_assessment_date": (
                self.next_assessment_date.isoformat()
                if self.next_assessment_date
                else None
            ),
        }


# ================== NIST CSF FRAMEWORK ==================


class NISTCSFFramework:
    """NIST Cybersecurity Framework v1.1 implementation."""

    FUNCTIONS = ["identify", "protect", "detect", "respond", "recover"]

    def __init__(self):
        self.controls = self._initialize_controls()

    def _initialize_controls(self) -> list[ComplianceControl]:
        """Initialize NIST CSF controls."""
        controls = []

        # IDENTIFY Function
        controls.extend(
            [
                ComplianceControl(
                    control_id="ID.AM-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Physical devices and systems inventory",
                    description="Physical devices and systems within the organization are inventoried",
                    category="Asset Management",
                    subcategory="Identify",
                    implementation_guidance="Maintain comprehensive asset inventory with hardware, software, and network devices",
                    required_evidence=[
                        "Asset inventory database",
                        "Network topology diagram",
                        "Hardware asset list",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="ID.AM-2",
                    framework=FrameworkType.NIST_CSF,
                    title="Software platforms and applications inventory",
                    description="Software platforms and applications within the organization are inventoried",
                    category="Asset Management",
                    subcategory="Identify",
                    implementation_guidance="Track all software installations, versions, and licenses",
                    required_evidence=[
                        "Software inventory list",
                        "License management records",
                        "Version control logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="ID.RA-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Asset vulnerabilities are identified and documented",
                    description="Asset vulnerabilities are identified and documented",
                    category="Risk Assessment",
                    subcategory="Identify",
                    implementation_guidance="Conduct regular vulnerability scans and document findings",
                    required_evidence=[
                        "Vulnerability scan reports",
                        "Risk assessment documentation",
                        "Remediation tracking",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
            ]
        )

        # PROTECT Function
        controls.extend(
            [
                ComplianceControl(
                    control_id="PR.AC-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Identities and credentials management",
                    description="Identities and credentials are issued, managed, verified, revoked, and audited for authorized devices, users and processes",
                    category="Access Control",
                    subcategory="Protect",
                    implementation_guidance="Implement identity and access management (IAM) solution",
                    required_evidence=[
                        "IAM policies and procedures",
                        "User provisioning logs",
                        "Access review records",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="PR.DS-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Data-at-rest is protected",
                    description="Data-at-rest is protected",
                    category="Data Security",
                    subcategory="Protect",
                    implementation_guidance="Encrypt sensitive data at rest using industry-standard encryption",
                    required_evidence=[
                        "Encryption configuration",
                        "Key management procedures",
                        "Data classification policy",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
            ]
        )

        # DETECT Function
        controls.extend(
            [
                ComplianceControl(
                    control_id="DE.CM-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Network monitoring",
                    description="The network is monitored to detect potential cybersecurity events",
                    category="Continuous Monitoring",
                    subcategory="Detect",
                    implementation_guidance="Deploy network monitoring and anomaly detection systems",
                    required_evidence=[
                        "Network monitoring logs",
                        "IDS/IPS configuration",
                        "Anomaly detection reports",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="DE.AE-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Baseline network operations and expected data flows",
                    description="A baseline of network operations and expected data flows for users and systems is established and managed",
                    category="Anomalies and Events",
                    subcategory="Detect",
                    implementation_guidance="Establish normal behavior baselines and monitor for deviations",
                    required_evidence=[
                        "Baseline documentation",
                        "Monitoring policies",
                        "Anomaly detection rules",
                    ],
                    automated_check=True,
                    priority=RiskLevel.MEDIUM,
                ),
            ]
        )

        # RESPOND Function
        controls.extend(
            [
                ComplianceControl(
                    control_id="RS.RP-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Response plan execution",
                    description="Response plan is executed during or after an incident",
                    category="Response Planning",
                    subcategory="Respond",
                    implementation_guidance="Develop and regularly test incident response plans",
                    required_evidence=[
                        "Incident response plan",
                        "Tabletop exercise records",
                        "Incident response logs",
                    ],
                    automated_check=False,
                    priority=RiskLevel.CRITICAL,
                ),
            ]
        )

        # RECOVER Function
        controls.extend(
            [
                ComplianceControl(
                    control_id="RC.RP-1",
                    framework=FrameworkType.NIST_CSF,
                    title="Recovery plan execution",
                    description="Recovery plan is executed during or after a cybersecurity incident",
                    category="Recovery Planning",
                    subcategory="Recover",
                    implementation_guidance="Maintain business continuity and disaster recovery plans",
                    required_evidence=[
                        "Recovery plan documentation",
                        "Backup verification logs",
                        "Recovery test results",
                    ],
                    automated_check=False,
                    priority=RiskLevel.HIGH,
                ),
            ]
        )

        return controls

    def get_controls_by_function(self, function: str) -> list[ComplianceControl]:
        """Get controls for a specific CSF function (case-insensitive)."""
        return [c for c in self.controls if c.subcategory.lower() == function.lower()]


# ================== CIS CONTROLS FRAMEWORK ==================


class CISControlsFramework:
    """CIS Critical Security Controls v8 implementation."""

    IMPLEMENTATION_GROUPS = ["IG1", "IG2", "IG3"]  # Small, Medium, Large orgs

    def __init__(self):
        self.controls = self._initialize_controls()

    def _initialize_controls(self) -> list[ComplianceControl]:
        """Initialize CIS Controls v8."""
        controls = []

        controls.extend(
            [
                ComplianceControl(
                    control_id="CIS-1.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish and Maintain Detailed Enterprise Asset Inventory",
                    description="Establish and maintain an accurate, detailed, and up-to-date inventory of all enterprise assets",
                    category="Inventory and Control of Enterprise Assets",
                    subcategory="IG1",
                    implementation_guidance="Use automated asset discovery tools to maintain real-time inventory",
                    required_evidence=[
                        "Asset inventory database",
                        "Automated discovery tool logs",
                        "Asset reconciliation reports",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="CIS-2.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish and Maintain a Software Inventory",
                    description="Establish and maintain a detailed inventory of all licensed software installed on enterprise assets",
                    category="Inventory and Control of Software Assets",
                    subcategory="IG1",
                    implementation_guidance="Track all authorized and unauthorized software",
                    required_evidence=[
                        "Software inventory list",
                        "License compliance report",
                        "Unauthorized software alerts",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="CIS-3.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish and Maintain a Data Management Process",
                    description="Establish and maintain a data management process",
                    category="Data Protection",
                    subcategory="IG1",
                    implementation_guidance="Document data flows, classification, and retention policies",
                    required_evidence=[
                        "Data flow diagrams",
                        "Data classification policy",
                        "Retention schedule",
                    ],
                    automated_check=False,
                    priority=RiskLevel.MEDIUM,
                ),
                ComplianceControl(
                    control_id="CIS-4.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish and Maintain a Secure Configuration Process",
                    description="Establish and maintain a secure configuration process for enterprise assets",
                    category="Secure Configuration of Enterprise Assets and Software",
                    subcategory="IG1",
                    implementation_guidance="Deploy hardened configuration baselines",
                    required_evidence=[
                        "Configuration baselines",
                        "Hardening checklists",
                        "Configuration audit reports",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="CIS-5.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish and Maintain an Inventory of Accounts",
                    description="Establish and maintain an inventory of all accounts managed in the enterprise",
                    category="Account Management",
                    subcategory="IG1",
                    implementation_guidance="Track all user, service, and system accounts",
                    required_evidence=[
                        "Account inventory",
                        "Privileged account list",
                        "Account lifecycle logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="CIS-6.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish an Access Granting Process",
                    description="Establish and follow a process for granting access to enterprise assets",
                    category="Access Control Management",
                    subcategory="IG1",
                    implementation_guidance="Implement least privilege access controls",
                    required_evidence=[
                        "Access request procedures",
                        "Approval workflows",
                        "Access audit logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="CIS-7.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish and Maintain a Vulnerability Management Process",
                    description="Establish and maintain a vulnerability management process",
                    category="Continuous Vulnerability Management",
                    subcategory="IG1",
                    implementation_guidance="Scan for vulnerabilities and remediate based on risk",
                    required_evidence=[
                        "Vulnerability scan reports",
                        "Remediation SLAs",
                        "Patch management logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="CIS-8.1",
                    framework=FrameworkType.CIS_CONTROLS,
                    title="Establish and Maintain Audit Log Management",
                    description="Establish and maintain an audit log management process",
                    category="Audit Log Management",
                    subcategory="IG1",
                    implementation_guidance="Collect, protect, and review security logs",
                    required_evidence=[
                        "Log collection configuration",
                        "Log retention policy",
                        "Log review procedures",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
            ]
        )

        return controls


# ================== HIPAA FRAMEWORK ==================


class HIPAAFramework:
    """HIPAA (Health Insurance Portability and Accountability Act) compliance."""

    SAFEGUARD_CATEGORIES = [
        "Administrative Safeguards",
        "Physical Safeguards",
        "Technical Safeguards",
    ]

    def __init__(self):
        self.controls = self._initialize_controls()

    def _initialize_controls(self) -> list[ComplianceControl]:
        """Initialize HIPAA controls."""
        controls = []

        # Administrative Safeguards
        controls.extend(
            [
                ComplianceControl(
                    control_id="HIPAA-164.308(a)(1)(i)",
                    framework=FrameworkType.HIPAA,
                    title="Security Management Process",
                    description="Implement policies and procedures to prevent, detect, contain, and correct security violations",
                    category="Administrative Safeguards",
                    implementation_guidance="Establish comprehensive security management program",
                    required_evidence=[
                        "Security policies and procedures",
                        "Risk assessment documentation",
                        "Security incident logs",
                    ],
                    automated_check=False,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="HIPAA-164.308(a)(3)",
                    framework=FrameworkType.HIPAA,
                    title="Workforce Security",
                    description="Implement policies and procedures to ensure workforce members have appropriate access to ePHI",
                    category="Administrative Safeguards",
                    implementation_guidance="Establish workforce authorization and supervision procedures",
                    required_evidence=[
                        "Access authorization policies",
                        "Workforce training records",
                        "Access review logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="HIPAA-164.308(a)(4)",
                    framework=FrameworkType.HIPAA,
                    title="Information Access Management",
                    description="Implement policies and procedures for authorizing access to ePHI",
                    category="Administrative Safeguards",
                    implementation_guidance="Implement role-based access control (RBAC)",
                    required_evidence=[
                        "Access control policies",
                        "Role definitions",
                        "Access grant/revoke logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="HIPAA-164.308(a)(5)",
                    framework=FrameworkType.HIPAA,
                    title="Security Awareness and Training",
                    description="Implement security awareness and training program for all workforce members",
                    category="Administrative Safeguards",
                    implementation_guidance="Conduct annual security awareness training",
                    required_evidence=[
                        "Training curriculum",
                        "Training completion records",
                        "Phishing simulation results",
                    ],
                    automated_check=False,
                    priority=RiskLevel.HIGH,
                ),
            ]
        )

        # Physical Safeguards
        controls.extend(
            [
                ComplianceControl(
                    control_id="HIPAA-164.310(a)(1)",
                    framework=FrameworkType.HIPAA,
                    title="Facility Access Controls",
                    description="Implement policies and procedures to limit physical access to electronic information systems",
                    category="Physical Safeguards",
                    implementation_guidance="Control physical access to facilities and equipment",
                    required_evidence=[
                        "Physical access control procedures",
                        "Visitor logs",
                        "Badge access records",
                    ],
                    automated_check=False,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="HIPAA-164.310(d)(1)",
                    framework=FrameworkType.HIPAA,
                    title="Device and Media Controls",
                    description="Implement policies and procedures for disposal of ePHI and hardware/electronic media",
                    category="Physical Safeguards",
                    implementation_guidance="Securely dispose of media containing ePHI",
                    required_evidence=[
                        "Media disposal procedures",
                        "Certificate of destruction",
                        "Disposal tracking logs",
                    ],
                    automated_check=False,
                    priority=RiskLevel.MEDIUM,
                ),
            ]
        )

        # Technical Safeguards
        controls.extend(
            [
                ComplianceControl(
                    control_id="HIPAA-164.312(a)(1)",
                    framework=FrameworkType.HIPAA,
                    title="Access Control",
                    description="Implement technical policies and procedures for electronic information systems that maintain ePHI",
                    category="Technical Safeguards",
                    implementation_guidance="Use unique user identification and emergency access procedures",
                    required_evidence=[
                        "User authentication system",
                        "Emergency access procedures",
                        "Access audit logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="HIPAA-164.312(a)(2)(iv)",
                    framework=FrameworkType.HIPAA,
                    title="Encryption and Decryption",
                    description="Implement mechanism to encrypt and decrypt ePHI",
                    category="Technical Safeguards",
                    implementation_guidance="Encrypt ePHI at rest and in transit",
                    required_evidence=[
                        "Encryption implementation",
                        "Key management procedures",
                        "Encryption audit logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="HIPAA-164.312(b)",
                    framework=FrameworkType.HIPAA,
                    title="Audit Controls",
                    description="Implement hardware, software, and/or procedural mechanisms to record and examine activity",
                    category="Technical Safeguards",
                    implementation_guidance="Enable comprehensive audit logging",
                    required_evidence=[
                        "Audit log configuration",
                        "Log review procedures",
                        "Audit trail reports",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="HIPAA-164.312(e)(1)",
                    framework=FrameworkType.HIPAA,
                    title="Transmission Security",
                    description="Implement technical security measures to guard against unauthorized access to ePHI during transmission",
                    category="Technical Safeguards",
                    implementation_guidance="Use TLS/SSL for data transmission",
                    required_evidence=[
                        "Transmission encryption configuration",
                        "Network security architecture",
                        "VPN/TLS implementation",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
            ]
        )

        return controls


# ================== SOC 2 FRAMEWORK ==================


class SOC2Framework:
    """SOC 2 Type II compliance framework."""

    TRUST_SERVICE_CRITERIA = [
        "Security",
        "Availability",
        "Processing Integrity",
        "Confidentiality",
        "Privacy",
    ]

    def __init__(self):
        self.controls = self._initialize_controls()

    def _initialize_controls(self) -> list[ComplianceControl]:
        """Initialize SOC 2 controls."""
        controls = []

        # Common Criteria (CC) - Security
        controls.extend(
            [
                ComplianceControl(
                    control_id="SOC2-CC6.1",
                    framework=FrameworkType.SOC2,
                    title="Logical and Physical Access Controls",
                    description="Implement logical and physical access controls to protect system boundaries",
                    category="Security",
                    implementation_guidance="Deploy multi-factor authentication and physical access controls",
                    required_evidence=[
                        "Access control policies",
                        "MFA configuration",
                        "Physical security documentation",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="SOC2-CC6.2",
                    framework=FrameworkType.SOC2,
                    title="Prior Authorization of Changes",
                    description="Changes to system components require prior authorization",
                    category="Security",
                    implementation_guidance="Implement change management process with approvals",
                    required_evidence=[
                        "Change management policy",
                        "Change approval records",
                        "Change logs",
                    ],
                    automated_check=False,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="SOC2-CC6.3",
                    framework=FrameworkType.SOC2,
                    title="System Authorization and Access Restrictions",
                    description="Restrict access to system components based on job responsibilities",
                    category="Security",
                    implementation_guidance="Implement least privilege access controls",
                    required_evidence=[
                        "Role-based access control matrix",
                        "Quarterly access reviews",
                        "Privileged access logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="SOC2-CC6.6",
                    framework=FrameworkType.SOC2,
                    title="Logical Access Controls - Encryption",
                    description="Encrypt data at rest and in transit",
                    category="Security",
                    implementation_guidance="Implement encryption using industry-standard algorithms",
                    required_evidence=[
                        "Encryption policy",
                        "Key management procedures",
                        "Encryption verification tests",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
            ]
        )

        # Availability
        controls.extend(
            [
                ComplianceControl(
                    control_id="SOC2-CC7.1",
                    framework=FrameworkType.SOC2,
                    title="System Capacity Monitoring",
                    description="Monitor system capacity to meet availability commitments",
                    category="Availability",
                    implementation_guidance="Implement capacity monitoring and alerting",
                    required_evidence=[
                        "Capacity monitoring dashboards",
                        "Performance metrics",
                        "Capacity planning reports",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="SOC2-CC7.2",
                    framework=FrameworkType.SOC2,
                    title="System Monitoring and Incident Response",
                    description="Monitor systems and respond to incidents affecting availability",
                    category="Availability",
                    implementation_guidance="Deploy 24/7 monitoring and incident response capabilities",
                    required_evidence=[
                        "Monitoring tool configuration",
                        "Incident response procedures",
                        "Incident response logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
            ]
        )

        # Processing Integrity
        controls.extend(
            [
                ComplianceControl(
                    control_id="SOC2-CC8.1",
                    framework=FrameworkType.SOC2,
                    title="System Processing Accuracy and Completeness",
                    description="Ensure system processing is complete, valid, accurate, and authorized",
                    category="Processing Integrity",
                    implementation_guidance="Implement data validation and processing controls",
                    required_evidence=[
                        "Data validation rules",
                        "Processing error logs",
                        "Data integrity checks",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
            ]
        )

        return controls


# ================== FEDRAMP FRAMEWORK ==================


class FedRAMPFramework:
    """FedRAMP (Federal Risk and Authorization Management Program) framework."""

    IMPACT_LEVELS = ["Low", "Moderate", "High"]

    def __init__(self):
        self.controls = self._initialize_controls()

    def _initialize_controls(self) -> list[ComplianceControl]:
        """Initialize FedRAMP controls (based on NIST 800-53)."""
        controls = []

        controls.extend(
            [
                ComplianceControl(
                    control_id="FedRAMP-AC-1",
                    framework=FrameworkType.FEDRAMP,
                    title="Access Control Policy and Procedures",
                    description="Develop, document, and disseminate access control policy and procedures",
                    category="Access Control",
                    implementation_guidance="Document and maintain access control policies",
                    required_evidence=[
                        "Access control policy document",
                        "Procedures documentation",
                        "Policy review records",
                    ],
                    automated_check=False,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="FedRAMP-AC-2",
                    framework=FrameworkType.FEDRAMP,
                    title="Account Management",
                    description="Manage system accounts including creation, modification, and removal",
                    category="Access Control",
                    implementation_guidance="Implement automated account management processes",
                    required_evidence=[
                        "Account provisioning procedures",
                        "Account review logs",
                        "Termination procedures",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="FedRAMP-AU-2",
                    framework=FrameworkType.FEDRAMP,
                    title="Audit Events",
                    description="Define auditable events and coordinate with other entities",
                    category="Audit and Accountability",
                    implementation_guidance="Document and implement comprehensive audit logging",
                    required_evidence=[
                        "Audit event definitions",
                        "Logging configuration",
                        "Audit log samples",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="FedRAMP-CA-2",
                    framework=FrameworkType.FEDRAMP,
                    title="Security Assessments",
                    description="Develop and implement security assessment plan",
                    category="Security Assessment and Authorization",
                    implementation_guidance="Conduct annual security assessments",
                    required_evidence=[
                        "Security assessment plan",
                        "Assessment reports",
                        "POA&M documentation",
                    ],
                    automated_check=False,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="FedRAMP-CM-2",
                    framework=FrameworkType.FEDRAMP,
                    title="Baseline Configuration",
                    description="Develop, document, and maintain baseline configurations",
                    category="Configuration Management",
                    implementation_guidance="Maintain hardened configuration baselines",
                    required_evidence=[
                        "Configuration baseline documentation",
                        "Configuration management database",
                        "Configuration audit reports",
                    ],
                    automated_check=True,
                    priority=RiskLevel.HIGH,
                ),
                ComplianceControl(
                    control_id="FedRAMP-IA-2",
                    framework=FrameworkType.FEDRAMP,
                    title="Identification and Authentication",
                    description="Uniquely identify and authenticate users",
                    category="Identification and Authentication",
                    implementation_guidance="Implement multi-factor authentication for all users",
                    required_evidence=[
                        "MFA implementation documentation",
                        "Authentication configuration",
                        "Authentication logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="FedRAMP-SC-7",
                    framework=FrameworkType.FEDRAMP,
                    title="Boundary Protection",
                    description="Monitor and control communications at external boundaries",
                    category="System and Communications Protection",
                    implementation_guidance="Deploy firewalls and boundary protection devices",
                    required_evidence=[
                        "Network architecture diagram",
                        "Firewall configurations",
                        "Boundary device logs",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
                ComplianceControl(
                    control_id="FedRAMP-SC-13",
                    framework=FrameworkType.FEDRAMP,
                    title="Cryptographic Protection",
                    description="Implement FIPS-validated cryptography",
                    category="System and Communications Protection",
                    implementation_guidance="Use FIPS 140-2 validated cryptographic modules",
                    required_evidence=[
                        "Cryptographic implementation details",
                        "FIPS validation certificates",
                        "Key management documentation",
                    ],
                    automated_check=True,
                    priority=RiskLevel.CRITICAL,
                ),
            ]
        )

        return controls


# ================== CUSTOM FRAMEWORK BUILDER ==================


class CustomFrameworkBuilder:
    """Builder for custom compliance frameworks."""

    def __init__(self, framework_name: str):
        self.framework_name = framework_name
        self.controls: list[ComplianceControl] = []

    def add_control(
        self,
        control_id: str,
        title: str,
        description: str,
        category: str,
        priority: RiskLevel = RiskLevel.MEDIUM,
        **kwargs,
    ) -> "CustomFrameworkBuilder":
        """Add a custom control to the framework."""
        control = ComplianceControl(
            control_id=control_id,
            framework=FrameworkType.CUSTOM,
            title=title,
            description=description,
            category=category,
            priority=priority,
            **kwargs,
        )
        self.controls.append(control)
        return self

    def build(self) -> list[ComplianceControl]:
        """Build and return the custom framework controls."""
        return self.controls


# ================== COMPLIANCE ENGINE ==================


class ComplianceFrameworkEngine:
    """Main engine for compliance framework assessment and management."""

    def __init__(self):
        self.frameworks = {
            FrameworkType.NIST_CSF: NISTCSFFramework(),
            FrameworkType.CIS_CONTROLS: CISControlsFramework(),
            FrameworkType.HIPAA: HIPAAFramework(),
            FrameworkType.SOC2: SOC2Framework(),
            FrameworkType.FEDRAMP: FedRAMPFramework(),
        }
        self.custom_frameworks: dict[str, list[ComplianceControl]] = {}

    def add_custom_framework(
        self, framework_name: str, controls: list[ComplianceControl]
    ):
        """Add a custom framework."""
        self.custom_frameworks[framework_name] = controls

    def get_framework_controls(
        self, framework: FrameworkType
    ) -> list[ComplianceControl]:
        """Get all controls for a framework."""
        if framework == FrameworkType.CUSTOM:
            # Return all custom framework controls
            all_custom = []
            for controls in self.custom_frameworks.values():
                all_custom.extend(controls)
            return all_custom
        return self.frameworks[framework].controls

    def assess_framework(
        self,
        framework: FrameworkType,
        current_implementation: dict[str, ControlStatus] | None = None,
    ) -> FrameworkAssessment:
        """
        Assess compliance with a framework.

        Args:
            framework: Framework to assess
            current_implementation: Dict mapping control_id -> ControlStatus
                                  If None, simulates assessment

        Returns:
            FrameworkAssessment with complete results
        """
        controls = self.get_framework_controls(framework)

        if current_implementation is None:
            # Simulate assessment for demonstration
            current_implementation = self._simulate_assessment(controls)

        # Perform control assessments
        control_assessments = []
        implemented_count = 0
        partial_count = 0
        not_implemented_count = 0

        for control in controls:
            status = current_implementation.get(
                control.control_id, ControlStatus.NOT_ASSESSED
            )

            # Calculate compliance score
            if status == ControlStatus.IMPLEMENTED:
                score = 1.0
                implemented_count += 1
            elif status == ControlStatus.PARTIALLY_IMPLEMENTED:
                score = 0.5
                partial_count += 1
            elif status == ControlStatus.NOT_APPLICABLE:
                score = 1.0  # N/A counts as compliant
            else:
                score = 0.0
                not_implemented_count += 1

            assessment = ControlAssessment(
                control_id=control.control_id,
                status=status,
                compliance_score=score,
                assessment_date=datetime.utcnow(),
                assessor="ComplianceFrameworkEngine",
            )
            control_assessments.append(assessment)

        # Calculate overall score
        total_controls = len(controls)
        overall_score = (
            sum(a.compliance_score for a in control_assessments) / total_controls
            if total_controls > 0
            else 0.0
        )

        # Determine compliance level
        if overall_score >= 0.9:
            compliance_level = ComplianceLevel.COMPLIANT
        elif overall_score >= 0.7:
            compliance_level = ComplianceLevel.MOSTLY_COMPLIANT
        elif overall_score >= 0.5:
            compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance_level = ComplianceLevel.NON_COMPLIANT

        # Identify gaps
        gaps = self._identify_gaps(controls, control_assessments)

        # Generate remediation roadmap
        roadmap = self._generate_roadmap(framework, gaps) if gaps else None

        # Generate recommendations
        recommendations = self._generate_recommendations(framework, control_assessments)

        return FrameworkAssessment(
            framework=framework,
            assessment_date=datetime.utcnow(),
            overall_score=overall_score,
            compliance_level=compliance_level,
            total_controls=total_controls,
            implemented_controls=implemented_count,
            partially_implemented_controls=partial_count,
            not_implemented_controls=not_implemented_count,
            control_assessments=control_assessments,
            gaps=gaps,
            remediation_roadmap=roadmap,
            recommendations=recommendations,
            next_assessment_date=datetime.utcnow() + timedelta(days=90),
        )

    def _simulate_assessment(
        self, controls: list[ComplianceControl]
    ) -> dict[str, ControlStatus]:
        """Simulate assessment results for demonstration."""
        import random

        implementation = {}
        for control in controls:
            # Weighted random: 50% implemented, 30% partial, 20% not implemented
            rand = random.random()
            if rand < 0.5:
                status = ControlStatus.IMPLEMENTED
            elif rand < 0.8:
                status = ControlStatus.PARTIALLY_IMPLEMENTED
            else:
                status = ControlStatus.NOT_IMPLEMENTED

            implementation[control.control_id] = status

        return implementation

    def _identify_gaps(
        self,
        controls: list[ComplianceControl],
        assessments: list[ControlAssessment],
    ) -> list[ComplianceGap]:
        """Identify compliance gaps from assessments."""
        gaps = []
        assessment_map = {a.control_id: a for a in assessments}

        for control in controls:
            assessment = assessment_map.get(control.control_id)
            if not assessment:
                continue

            if assessment.status in [
                ControlStatus.NOT_IMPLEMENTED,
                ControlStatus.PARTIALLY_IMPLEMENTED,
            ]:
                gap = ComplianceGap(
                    gap_id=f"GAP-{control.control_id}",
                    control_id=control.control_id,
                    framework=control.framework,
                    title=control.title,
                    description=f"Control {control.control_id} is {assessment.status.value}",
                    risk_level=control.priority,
                    current_state=assessment.status.value,
                    desired_state="implemented",
                    remediation_steps=self._get_remediation_steps(control),
                    estimated_effort_hours=self._estimate_effort(control, assessment),
                )
                gaps.append(gap)

        # Sort by priority (critical first)
        priority_order = {
            RiskLevel.CRITICAL: 0,
            RiskLevel.HIGH: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 3,
            RiskLevel.INFORMATIONAL: 4,
        }
        gaps.sort(key=lambda g: priority_order[g.risk_level])

        return gaps

    def _get_remediation_steps(self, control: ComplianceControl) -> list[str]:
        """Generate remediation steps for a control."""
        steps = []

        if control.implementation_guidance:
            steps.append(control.implementation_guidance)

        if control.required_evidence:
            steps.append(
                f"Collect evidence: {', '.join(control.required_evidence[:3])}"
            )

        if control.automated_check:
            steps.append("Configure automated compliance checks")

        steps.append("Document implementation and test")
        steps.append("Obtain approval from security team")

        return steps

    def _estimate_effort(
        self, control: ComplianceControl, assessment: ControlAssessment
    ) -> int:
        """Estimate effort hours for remediation."""
        base_effort = {
            RiskLevel.CRITICAL: 40,
            RiskLevel.HIGH: 24,
            RiskLevel.MEDIUM: 16,
            RiskLevel.LOW: 8,
            RiskLevel.INFORMATIONAL: 4,
        }

        effort = base_effort.get(control.priority, 16)

        # Reduce effort for partially implemented controls
        if assessment.status == ControlStatus.PARTIALLY_IMPLEMENTED:
            effort = effort // 2

        return effort

    def _generate_roadmap(
        self, framework: FrameworkType, gaps: list[ComplianceGap]
    ) -> RemediationRoadmap:
        """Generate remediation roadmap from gaps."""
        total_effort = sum(gap.estimated_effort_hours for gap in gaps)

        # Assign target dates (critical first, then staggered)
        base_date = datetime.utcnow()
        for i, gap in enumerate(gaps):
            # Critical: 2 weeks, High: 4 weeks, Medium: 8 weeks, Low: 12 weeks
            weeks = {
                RiskLevel.CRITICAL: 2,
                RiskLevel.HIGH: 4,
                RiskLevel.MEDIUM: 8,
                RiskLevel.LOW: 12,
                RiskLevel.INFORMATIONAL: 16,
            }
            offset_weeks = weeks.get(gap.risk_level, 8)
            gap.target_completion_date = base_date + timedelta(weeks=offset_weeks)

        # Calculate overall completion date (latest gap)
        completion_date = max(
            (gap.target_completion_date for gap in gaps if gap.target_completion_date),
            default=base_date + timedelta(weeks=12),
        )

        # Create phases
        phases = self._create_remediation_phases(gaps)

        return RemediationRoadmap(
            framework=framework,
            gaps=gaps,
            total_effort_hours=total_effort,
            estimated_completion_date=completion_date,
            phases=phases,
        )

    def _create_remediation_phases(
        self, gaps: list[ComplianceGap]
    ) -> list[dict[str, Any]]:
        """Create remediation phases based on priority."""
        phases = []

        # Phase 1: Critical gaps
        critical_gaps = [g for g in gaps if g.risk_level == RiskLevel.CRITICAL]
        if critical_gaps:
            phases.append(
                {
                    "phase": 1,
                    "name": "Critical Remediation",
                    "duration_weeks": 2,
                    "gap_ids": [g.gap_id for g in critical_gaps],
                    "start_date": datetime.utcnow().isoformat(),
                }
            )

        # Phase 2: High priority gaps
        high_gaps = [g for g in gaps if g.risk_level == RiskLevel.HIGH]
        if high_gaps:
            start = datetime.utcnow() + timedelta(weeks=2)
            phases.append(
                {
                    "phase": 2,
                    "name": "High Priority Remediation",
                    "duration_weeks": 4,
                    "gap_ids": [g.gap_id for g in high_gaps],
                    "start_date": start.isoformat(),
                }
            )

        # Phase 3: Medium/Low gaps
        remaining_gaps = [
            g
            for g in gaps
            if g.risk_level
            in [RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.INFORMATIONAL]
        ]
        if remaining_gaps:
            start = datetime.utcnow() + timedelta(weeks=6)
            phases.append(
                {
                    "phase": 3,
                    "name": "Continuous Improvement",
                    "duration_weeks": 8,
                    "gap_ids": [g.gap_id for g in remaining_gaps],
                    "start_date": start.isoformat(),
                }
            )

        return phases

    def _generate_recommendations(
        self, framework: FrameworkType, assessments: list[ControlAssessment]
    ) -> list[str]:
        """Generate recommendations based on assessment."""
        recommendations = []

        # Calculate implementation rate
        total = len(assessments)
        implemented = sum(
            1 for a in assessments if a.status == ControlStatus.IMPLEMENTED
        )
        rate = implemented / total if total > 0 else 0

        if rate < 0.5:
            recommendations.append(
                "Prioritize immediate remediation of critical control gaps"
            )
            recommendations.append("Consider engaging external compliance consultants")

        if rate < 0.7:
            recommendations.append(
                "Develop comprehensive compliance program with quarterly reviews"
            )

        recommendations.append(f"Schedule next {framework.value} assessment in 90 days")
        recommendations.append(
            "Implement continuous compliance monitoring for automated controls"
        )

        # Framework-specific recommendations
        if framework == FrameworkType.HIPAA:
            recommendations.append(
                "Ensure Business Associate Agreements (BAAs) are current"
            )
        elif framework == FrameworkType.SOC2:
            recommendations.append(
                "Engage external auditor for SOC 2 Type II audit preparation"
            )
        elif framework == FrameworkType.FEDRAMP:
            recommendations.append(
                "Prepare for continuous monitoring with monthly POA&M updates"
            )

        return recommendations
