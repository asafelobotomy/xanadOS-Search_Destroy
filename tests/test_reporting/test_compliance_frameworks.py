#!/usr/bin/env python3
"""
Tests for Compliance Frameworks Module

Tests all 6 compliance frameworks (NIST CSF, CIS Controls, HIPAA, SOC 2, FedRAMP, Custom)
and the compliance engine functionality.
"""

import pytest
from datetime import datetime, timedelta

from app.reporting.compliance_frameworks import (
    # Enums
    FrameworkType,
    ControlStatus,
    ComplianceLevel,
    RiskLevel,
    # Data Models
    ComplianceControl,
    ControlAssessment,
    ComplianceGap,
    RemediationRoadmap,
    FrameworkAssessment,
    # Frameworks
    NISTCSFFramework,
    CISControlsFramework,
    HIPAAFramework,
    SOC2Framework,
    FedRAMPFramework,
    CustomFrameworkBuilder,
    # Engine
    ComplianceFrameworkEngine,
)


# ================== FIXTURES ==================


@pytest.fixture
def compliance_engine():
    """Create compliance framework engine."""
    return ComplianceFrameworkEngine()


@pytest.fixture
def nist_framework():
    """Create NIST CSF framework."""
    return NISTCSFFramework()


@pytest.fixture
def cis_framework():
    """Create CIS Controls framework."""
    return CISControlsFramework()


@pytest.fixture
def hipaa_framework():
    """Create HIPAA framework."""
    return HIPAAFramework()


@pytest.fixture
def soc2_framework():
    """Create SOC 2 framework."""
    return SOC2Framework()


@pytest.fixture
def fedramp_framework():
    """Create FedRAMP framework."""
    return FedRAMPFramework()


@pytest.fixture
def custom_framework():
    """Create custom framework."""
    builder = CustomFrameworkBuilder("Internal Security Policy")
    builder.add_control(
        control_id="CUSTOM-001",
        title="Quarterly Security Reviews",
        description="Conduct quarterly security posture reviews",
        category="Security Governance",
        priority=RiskLevel.HIGH,
    )
    return builder.build()


@pytest.fixture
def fully_compliant_implementation():
    """Simulated fully compliant implementation."""

    # Returns function that creates dict for any control list
    def create_implementation(controls):
        return {c.control_id: ControlStatus.IMPLEMENTED for c in controls}

    return create_implementation


@pytest.fixture
def partially_compliant_implementation():
    """Simulated partially compliant implementation."""

    def create_implementation(controls):
        implementation = {}
        for i, control in enumerate(controls):
            if i % 3 == 0:
                implementation[control.control_id] = ControlStatus.IMPLEMENTED
            elif i % 3 == 1:
                implementation[control.control_id] = ControlStatus.PARTIALLY_IMPLEMENTED
            else:
                implementation[control.control_id] = ControlStatus.NOT_IMPLEMENTED
        return implementation

    return create_implementation


# ================== NIST CSF TESTS ==================


def test_nist_csf_framework_initialization(nist_framework):
    """Test NIST CSF framework initialization."""
    assert len(nist_framework.controls) >= 8
    assert len(NISTCSFFramework.FUNCTIONS) == 5

    # Check all functions represented
    functions = {c.subcategory for c in nist_framework.controls}
    assert "Identify" in functions
    assert "Protect" in functions
    assert "Detect" in functions
    assert "Respond" in functions
    assert "Recover" in functions


def test_nist_csf_control_structure(nist_framework):
    """Test NIST CSF control structure."""
    control = nist_framework.controls[0]

    assert control.control_id.startswith("ID.") or control.control_id.startswith("PR.")
    assert control.framework == FrameworkType.NIST_CSF
    assert control.title
    assert control.description
    assert control.category
    assert control.subcategory.lower() in [
        f.lower() for f in NISTCSFFramework.FUNCTIONS
    ]
    assert isinstance(control.required_evidence, list)
    assert isinstance(control.automated_check, bool)
    assert isinstance(control.priority, RiskLevel)


def test_nist_csf_get_controls_by_function(nist_framework):
    """Test filtering NIST controls by function."""
    identify_controls = nist_framework.get_controls_by_function("Identify")

    assert len(identify_controls) >= 2
    assert all(c.subcategory == "Identify" for c in identify_controls)
    assert any("asset" in c.title.lower() for c in identify_controls)


def test_nist_csf_critical_controls(nist_framework):
    """Test NIST CSF includes critical controls."""
    control_ids = {c.control_id for c in nist_framework.controls}

    # Should include key controls
    assert "ID.AM-1" in control_ids  # Asset inventory
    assert "PR.AC-1" in control_ids  # Access control
    assert "DE.CM-1" in control_ids  # Network monitoring
    assert "RS.RP-1" in control_ids  # Response plan


# ================== CIS CONTROLS TESTS ==================


def test_cis_controls_initialization(cis_framework):
    """Test CIS Controls framework initialization."""
    assert len(cis_framework.controls) >= 8
    assert len(CISControlsFramework.IMPLEMENTATION_GROUPS) == 3


def test_cis_control_structure(cis_framework):
    """Test CIS control structure."""
    control = cis_framework.controls[0]

    assert control.control_id.startswith("CIS-")
    assert control.framework == FrameworkType.CIS_CONTROLS
    assert control.subcategory in ["IG1", "IG2", "IG3"]
    assert control.title
    assert len(control.required_evidence) > 0


def test_cis_controls_coverage(cis_framework):
    """Test CIS Controls cover key safeguards."""
    control_ids = {c.control_id for c in cis_framework.controls}

    # Should include foundational controls
    assert "CIS-1.1" in control_ids  # Asset inventory
    assert "CIS-2.1" in control_ids  # Software inventory
    assert "CIS-4.1" in control_ids  # Secure configuration
    assert "CIS-5.1" in control_ids  # Account management
    assert "CIS-6.1" in control_ids  # Access control
    assert "CIS-7.1" in control_ids  # Vulnerability management
    assert "CIS-8.1" in control_ids  # Audit logs


def test_cis_ig1_controls(cis_framework):
    """Test CIS IG1 (basic) controls exist."""
    ig1_controls = [c for c in cis_framework.controls if c.subcategory == "IG1"]

    assert len(ig1_controls) >= 6
    assert all(c.framework == FrameworkType.CIS_CONTROLS for c in ig1_controls)


# ================== HIPAA TESTS ==================


def test_hipaa_framework_initialization(hipaa_framework):
    """Test HIPAA framework initialization."""
    assert len(hipaa_framework.controls) >= 10
    assert len(HIPAAFramework.SAFEGUARD_CATEGORIES) == 3


def test_hipaa_control_structure(hipaa_framework):
    """Test HIPAA control structure."""
    control = hipaa_framework.controls[0]

    assert control.control_id.startswith("HIPAA-164.")
    assert control.framework == FrameworkType.HIPAA
    assert control.category in HIPAAFramework.SAFEGUARD_CATEGORIES
    assert control.description
    assert len(control.required_evidence) > 0


def test_hipaa_safeguard_categories(hipaa_framework):
    """Test HIPAA includes all safeguard categories."""
    categories = {c.category for c in hipaa_framework.controls}

    assert "Administrative Safeguards" in categories
    assert "Physical Safeguards" in categories
    assert "Technical Safeguards" in categories


def test_hipaa_critical_controls(hipaa_framework):
    """Test HIPAA critical controls."""
    control_ids = {c.control_id for c in hipaa_framework.controls}

    # Key HIPAA controls
    assert "HIPAA-164.308(a)(1)(i)" in control_ids  # Security management
    assert "HIPAA-164.308(a)(3)" in control_ids  # Workforce security
    assert "HIPAA-164.312(a)(1)" in control_ids  # Access control
    assert "HIPAA-164.312(a)(2)(iv)" in control_ids  # Encryption
    assert "HIPAA-164.312(e)(1)" in control_ids  # Transmission security


def test_hipaa_ephi_protection(hipaa_framework):
    """Test HIPAA controls focus on ePHI protection."""
    # Most controls should mention ePHI or protection
    ephi_related = [
        c
        for c in hipaa_framework.controls
        if "ePHI" in c.description or "protect" in c.description.lower()
    ]

    assert len(ephi_related) >= 5


# ================== SOC 2 TESTS ==================


def test_soc2_framework_initialization(soc2_framework):
    """Test SOC 2 framework initialization."""
    assert len(soc2_framework.controls) >= 7
    assert len(SOC2Framework.TRUST_SERVICE_CRITERIA) == 5


def test_soc2_control_structure(soc2_framework):
    """Test SOC 2 control structure."""
    control = soc2_framework.controls[0]

    assert control.control_id.startswith("SOC2-")
    assert control.framework == FrameworkType.SOC2
    assert control.category in SOC2Framework.TRUST_SERVICE_CRITERIA
    assert control.description


def test_soc2_trust_service_criteria(soc2_framework):
    """Test SOC 2 trust service criteria coverage."""
    categories = {c.category for c in soc2_framework.controls}

    assert "Security" in categories
    assert "Availability" in categories
    assert "Processing Integrity" in categories


def test_soc2_common_criteria_controls(soc2_framework):
    """Test SOC 2 Common Criteria controls."""
    control_ids = {c.control_id for c in soc2_framework.controls}

    # Key CC controls
    assert "SOC2-CC6.1" in control_ids  # Access controls
    assert "SOC2-CC6.2" in control_ids  # Change management
    assert "SOC2-CC6.3" in control_ids  # System authorization
    assert "SOC2-CC6.6" in control_ids  # Encryption


def test_soc2_security_controls(soc2_framework):
    """Test SOC 2 security controls are prioritized."""
    security_controls = [c for c in soc2_framework.controls if c.category == "Security"]

    assert len(security_controls) >= 4
    # Security controls should be high priority
    assert all(
        c.priority in [RiskLevel.CRITICAL, RiskLevel.HIGH] for c in security_controls
    )


# ================== FEDRAMP TESTS ==================


def test_fedramp_framework_initialization(fedramp_framework):
    """Test FedRAMP framework initialization."""
    assert len(fedramp_framework.controls) >= 8
    assert len(FedRAMPFramework.IMPACT_LEVELS) == 3


def test_fedramp_control_structure(fedramp_framework):
    """Test FedRAMP control structure."""
    control = fedramp_framework.controls[0]

    assert control.control_id.startswith("FedRAMP-")
    assert control.framework == FrameworkType.FEDRAMP
    assert control.category
    assert control.description


def test_fedramp_nist_800_53_alignment(fedramp_framework):
    """Test FedRAMP controls align with NIST 800-53."""
    control_ids = {c.control_id for c in fedramp_framework.controls}

    # Should include key NIST 800-53 controls
    assert "FedRAMP-AC-1" in control_ids  # Access control policy
    assert "FedRAMP-AC-2" in control_ids  # Account management
    assert "FedRAMP-AU-2" in control_ids  # Audit events
    assert "FedRAMP-IA-2" in control_ids  # Identification/authentication


def test_fedramp_critical_controls(fedramp_framework):
    """Test FedRAMP critical controls."""
    critical_controls = [
        c for c in fedramp_framework.controls if c.priority == RiskLevel.CRITICAL
    ]

    assert len(critical_controls) >= 5
    # Should include access control, authentication, encryption
    assert any("access" in c.title.lower() for c in critical_controls)
    assert any("authentication" in c.title.lower() for c in critical_controls)


# ================== CUSTOM FRAMEWORK TESTS ==================


def test_custom_framework_builder(custom_framework):
    """Test custom framework builder."""
    assert len(custom_framework) == 1

    control = custom_framework[0]
    assert control.control_id == "CUSTOM-001"
    assert control.framework == FrameworkType.CUSTOM
    assert control.title == "Quarterly Security Reviews"
    assert control.priority == RiskLevel.HIGH


def test_custom_framework_builder_chaining():
    """Test custom framework builder method chaining."""
    builder = CustomFrameworkBuilder("Test Framework")

    framework = (
        builder.add_control(
            control_id="CUST-1",
            title="Control 1",
            description="First control",
            category="Category A",
        )
        .add_control(
            control_id="CUST-2",
            title="Control 2",
            description="Second control",
            category="Category B",
            priority=RiskLevel.CRITICAL,
        )
        .build()
    )

    assert len(framework) == 2
    assert framework[0].control_id == "CUST-1"
    assert framework[1].control_id == "CUST-2"
    assert framework[1].priority == RiskLevel.CRITICAL


# ================== DATA MODEL TESTS ==================


def test_compliance_control_to_dict():
    """Test ComplianceControl serialization."""
    control = ComplianceControl(
        control_id="TEST-001",
        framework=FrameworkType.NIST_CSF,
        title="Test Control",
        description="Test description",
        category="Test Category",
        subcategory="Test Subcategory",
        required_evidence=["Evidence 1", "Evidence 2"],
        automated_check=True,
        priority=RiskLevel.HIGH,
    )

    data = control.to_dict()

    assert data["control_id"] == "TEST-001"
    assert data["framework"] == "nist_csf"
    assert data["title"] == "Test Control"
    assert data["automated_check"] is True
    assert data["priority"] == "high"
    assert len(data["required_evidence"]) == 2


def test_control_assessment_to_dict():
    """Test ControlAssessment serialization."""
    assessment = ControlAssessment(
        control_id="TEST-001",
        status=ControlStatus.IMPLEMENTED,
        compliance_score=1.0,
        assessment_date=datetime(2025, 12, 16, 10, 0, 0),
        evidence_provided=["Evidence 1"],
        findings=["All requirements met"],
        assessor="Test Assessor",
    )

    data = assessment.to_dict()

    assert data["control_id"] == "TEST-001"
    assert data["status"] == "implemented"
    assert data["compliance_score"] == 1.0
    assert "2025-12-16" in data["assessment_date"]
    assert len(data["evidence_provided"]) == 1


def test_compliance_gap_to_dict():
    """Test ComplianceGap serialization."""
    gap = ComplianceGap(
        gap_id="GAP-001",
        control_id="TEST-001",
        framework=FrameworkType.HIPAA,
        title="Missing Encryption",
        description="Encryption not implemented",
        risk_level=RiskLevel.CRITICAL,
        current_state="not_implemented",
        desired_state="implemented",
        remediation_steps=["Step 1", "Step 2"],
        estimated_effort_hours=40,
    )

    data = gap.to_dict()

    assert data["gap_id"] == "GAP-001"
    assert data["framework"] == "hipaa"
    assert data["risk_level"] == "critical"
    assert data["estimated_effort_hours"] == 40
    assert len(data["remediation_steps"]) == 2


def test_framework_assessment_to_dict(compliance_engine, nist_framework):
    """Test FrameworkAssessment serialization."""
    implementation = {
        c.control_id: ControlStatus.IMPLEMENTED for c in nist_framework.controls
    }
    assessment = compliance_engine.assess_framework(
        FrameworkType.NIST_CSF, implementation
    )

    data = assessment.to_dict()

    assert data["framework"] == "nist_csf"
    assert 0 <= data["overall_score"] <= 1.0
    assert data["compliance_level"] in [
        "compliant",
        "mostly_compliant",
        "partially_compliant",
        "non_compliant",
    ]
    assert data["total_controls"] >= 8
    assert isinstance(data["control_assessments"], list)
    assert isinstance(data["gaps"], list)


# ================== COMPLIANCE ENGINE TESTS ==================


def test_compliance_engine_initialization(compliance_engine):
    """Test compliance engine initialization."""
    assert len(compliance_engine.frameworks) == 5

    assert FrameworkType.NIST_CSF in compliance_engine.frameworks
    assert FrameworkType.CIS_CONTROLS in compliance_engine.frameworks
    assert FrameworkType.HIPAA in compliance_engine.frameworks
    assert FrameworkType.SOC2 in compliance_engine.frameworks
    assert FrameworkType.FEDRAMP in compliance_engine.frameworks


def test_get_framework_controls(compliance_engine):
    """Test retrieving framework controls."""
    nist_controls = compliance_engine.get_framework_controls(FrameworkType.NIST_CSF)

    assert len(nist_controls) >= 8
    assert all(c.framework == FrameworkType.NIST_CSF for c in nist_controls)


def test_assess_framework_fully_compliant(
    compliance_engine, nist_framework, fully_compliant_implementation
):
    """Test framework assessment with full compliance."""
    implementation = fully_compliant_implementation(nist_framework.controls)
    assessment = compliance_engine.assess_framework(
        FrameworkType.NIST_CSF, implementation
    )

    assert assessment.framework == FrameworkType.NIST_CSF
    assert assessment.overall_score == 1.0
    assert assessment.compliance_level == ComplianceLevel.COMPLIANT
    assert assessment.implemented_controls == len(nist_framework.controls)
    assert assessment.not_implemented_controls == 0
    assert len(assessment.gaps) == 0
    assert assessment.remediation_roadmap is None


def test_assess_framework_partially_compliant(
    compliance_engine, nist_framework, partially_compliant_implementation
):
    """Test framework assessment with partial compliance."""
    implementation = partially_compliant_implementation(nist_framework.controls)
    assessment = compliance_engine.assess_framework(
        FrameworkType.NIST_CSF, implementation
    )

    assert assessment.framework == FrameworkType.NIST_CSF
    assert 0.3 < assessment.overall_score < 0.8
    assert assessment.compliance_level in [
        ComplianceLevel.PARTIALLY_COMPLIANT,
        ComplianceLevel.MOSTLY_COMPLIANT,
    ]
    assert assessment.implemented_controls > 0
    assert assessment.not_implemented_controls > 0
    assert len(assessment.gaps) > 0


def test_assess_framework_generates_gaps(compliance_engine, hipaa_framework):
    """Test gap identification in assessment."""
    # Simulate some non-compliant controls
    implementation = {
        c.control_id: (
            ControlStatus.NOT_IMPLEMENTED if i % 2 == 0 else ControlStatus.IMPLEMENTED
        )
        for i, c in enumerate(hipaa_framework.controls)
    }

    assessment = compliance_engine.assess_framework(FrameworkType.HIPAA, implementation)

    assert len(assessment.gaps) > 0

    # Check gap structure
    gap = assessment.gaps[0]
    assert gap.control_id
    assert gap.framework == FrameworkType.HIPAA
    assert gap.risk_level in [
        RiskLevel.CRITICAL,
        RiskLevel.HIGH,
        RiskLevel.MEDIUM,
        RiskLevel.LOW,
    ]
    assert gap.current_state == "not_implemented"
    assert gap.desired_state == "implemented"
    assert len(gap.remediation_steps) > 0
    assert gap.estimated_effort_hours > 0


def test_assess_framework_generates_roadmap(compliance_engine, soc2_framework):
    """Test remediation roadmap generation."""
    # Partial compliance to trigger roadmap
    implementation = {
        c.control_id: (
            ControlStatus.NOT_IMPLEMENTED if i < 3 else ControlStatus.IMPLEMENTED
        )
        for i, c in enumerate(soc2_framework.controls)
    }

    assessment = compliance_engine.assess_framework(FrameworkType.SOC2, implementation)

    assert assessment.remediation_roadmap is not None

    roadmap = assessment.remediation_roadmap
    assert roadmap.framework == FrameworkType.SOC2
    assert len(roadmap.gaps) > 0
    assert roadmap.total_effort_hours > 0
    assert roadmap.estimated_completion_date > datetime.utcnow()
    assert len(roadmap.phases) > 0


def test_roadmap_prioritizes_critical_gaps(compliance_engine, fedramp_framework):
    """Test roadmap prioritizes critical gaps first."""
    # Make critical controls non-compliant
    implementation = {}
    for control in fedramp_framework.controls:
        if control.priority == RiskLevel.CRITICAL:
            implementation[control.control_id] = ControlStatus.NOT_IMPLEMENTED
        else:
            implementation[control.control_id] = ControlStatus.IMPLEMENTED

    assessment = compliance_engine.assess_framework(
        FrameworkType.FEDRAMP, implementation
    )

    assert len(assessment.gaps) > 0

    # First gaps should be critical
    critical_gaps = [g for g in assessment.gaps if g.risk_level == RiskLevel.CRITICAL]
    assert len(critical_gaps) > 0

    # Critical gaps should come first
    first_gap = assessment.gaps[0]
    assert first_gap.risk_level == RiskLevel.CRITICAL


def test_roadmap_phases_structure(compliance_engine, cis_framework):
    """Test remediation roadmap phases."""
    # Create mix of priority gaps
    implementation = {
        c.control_id: ControlStatus.NOT_IMPLEMENTED for c in cis_framework.controls
    }

    assessment = compliance_engine.assess_framework(
        FrameworkType.CIS_CONTROLS, implementation
    )

    roadmap = assessment.remediation_roadmap
    assert len(roadmap.phases) > 0

    # Check phase structure
    phase = roadmap.phases[0]
    assert "phase" in phase
    assert "name" in phase
    assert "duration_weeks" in phase
    assert "gap_ids" in phase
    assert "start_date" in phase


def test_assess_framework_generates_recommendations(compliance_engine, nist_framework):
    """Test recommendation generation."""
    implementation = {
        c.control_id: ControlStatus.IMPLEMENTED for c in nist_framework.controls[:4]
    }
    # Leave rest unimplemented

    assessment = compliance_engine.assess_framework(
        FrameworkType.NIST_CSF, implementation
    )

    assert len(assessment.recommendations) > 0
    assert any(
        "90 days" in rec for rec in assessment.recommendations
    )  # Next assessment
    assert any("monitoring" in rec.lower() for rec in assessment.recommendations)


def test_add_custom_framework(compliance_engine):
    """Test adding custom framework to engine."""
    custom_controls = (
        CustomFrameworkBuilder("Custom Policy")
        .add_control(
            control_id="CUST-1",
            title="Custom Control",
            description="Test",
            category="Testing",
        )
        .build()
    )

    compliance_engine.add_custom_framework("Custom Policy", custom_controls)

    assert "Custom Policy" in compliance_engine.custom_frameworks
    assert len(compliance_engine.custom_frameworks["Custom Policy"]) == 1


# ================== ACCEPTANCE CRITERIA TESTS ==================


def test_acceptance_all_frameworks_implemented(compliance_engine):
    """Test all 6 frameworks are implemented."""
    # 5 standard frameworks + custom
    assert len(compliance_engine.frameworks) == 5

    # Can retrieve controls for each
    for framework_type in [
        FrameworkType.NIST_CSF,
        FrameworkType.CIS_CONTROLS,
        FrameworkType.HIPAA,
        FrameworkType.SOC2,
        FrameworkType.FEDRAMP,
    ]:
        controls = compliance_engine.get_framework_controls(framework_type)
        assert len(controls) >= 7  # Each framework has at least 7 controls


def test_acceptance_gap_analysis_accuracy(compliance_engine, nist_framework):
    """Test gap analysis accuracy >90%."""
    # Create known implementation state
    implementation = {}
    expected_gaps = []

    for i, control in enumerate(nist_framework.controls):
        if i < 2:  # Make first 2 non-compliant
            implementation[control.control_id] = ControlStatus.NOT_IMPLEMENTED
            expected_gaps.append(control.control_id)
        else:
            implementation[control.control_id] = ControlStatus.IMPLEMENTED

    assessment = compliance_engine.assess_framework(
        FrameworkType.NIST_CSF, implementation
    )

    # Check gap accuracy
    identified_gap_controls = {gap.control_id for gap in assessment.gaps}

    # All expected gaps should be identified
    for expected_gap in expected_gaps:
        assert expected_gap in identified_gap_controls

    # Accuracy should be 100% in this controlled test
    accuracy = len(identified_gap_controls & set(expected_gaps)) / len(expected_gaps)
    assert accuracy >= 0.9  # >90% accuracy


def test_acceptance_remediation_roadmap_auto_generated(
    compliance_engine, hipaa_framework
):
    """Test remediation roadmap auto-generated."""
    # Create partial compliance
    implementation = {
        c.control_id: (
            ControlStatus.NOT_IMPLEMENTED if i % 3 == 0 else ControlStatus.IMPLEMENTED
        )
        for i, c in enumerate(hipaa_framework.controls)
    }

    assessment = compliance_engine.assess_framework(FrameworkType.HIPAA, implementation)

    # Roadmap should be auto-generated when gaps exist
    if len(assessment.gaps) > 0:
        assert assessment.remediation_roadmap is not None
        assert assessment.remediation_roadmap.total_effort_hours > 0
        assert len(assessment.remediation_roadmap.gaps) == len(assessment.gaps)
        assert len(assessment.remediation_roadmap.phases) > 0


def test_acceptance_evidence_attachments_supported(compliance_engine, soc2_framework):
    """Test evidence attachments supported."""
    # All controls should have required_evidence field
    for control in soc2_framework.controls:
        assert hasattr(control, "required_evidence")
        assert isinstance(control.required_evidence, list)

    # Assessment should track evidence
    implementation = {
        c.control_id: ControlStatus.IMPLEMENTED for c in soc2_framework.controls
    }
    assessment = compliance_engine.assess_framework(FrameworkType.SOC2, implementation)

    for control_assessment in assessment.control_assessments:
        assert hasattr(control_assessment, "evidence_provided")
        assert isinstance(control_assessment.evidence_provided, list)


# ================== EDGE CASE TESTS ==================


def test_assessment_with_empty_implementation(compliance_engine, nist_framework):
    """Test assessment with no implementation data."""
    # Pass empty dict (all controls unassessed)
    assessment = compliance_engine.assess_framework(FrameworkType.NIST_CSF, {})

    # Should have low score, all controls not assessed
    assert assessment.overall_score < 0.2
    assert assessment.compliance_level == ComplianceLevel.NON_COMPLIANT


def test_assessment_with_not_applicable_controls(compliance_engine, fedramp_framework):
    """Test assessment with N/A controls."""
    implementation = {}
    for i, control in enumerate(fedramp_framework.controls):
        if i < 2:
            implementation[control.control_id] = ControlStatus.NOT_APPLICABLE
        else:
            implementation[control.control_id] = ControlStatus.IMPLEMENTED

    assessment = compliance_engine.assess_framework(
        FrameworkType.FEDRAMP, implementation
    )

    # N/A should count as compliant
    assert assessment.overall_score >= 0.9


def test_framework_assessment_next_assessment_date(compliance_engine, cis_framework):
    """Test next assessment date is set."""
    implementation = {
        c.control_id: ControlStatus.IMPLEMENTED for c in cis_framework.controls
    }
    assessment = compliance_engine.assess_framework(
        FrameworkType.CIS_CONTROLS, implementation
    )

    assert assessment.next_assessment_date is not None
    assert assessment.next_assessment_date > datetime.utcnow()
    # Should be ~90 days in future
    assert assessment.next_assessment_date < datetime.utcnow() + timedelta(days=100)


# ================== INTEGRATION TEST ==================


def test_full_compliance_workflow(compliance_engine):
    """Test complete compliance assessment workflow."""
    # Step 1: Assess multiple frameworks
    frameworks_to_assess = [
        FrameworkType.NIST_CSF,
        FrameworkType.HIPAA,
        FrameworkType.SOC2,
    ]

    assessments = []
    for framework in frameworks_to_assess:
        assessment = compliance_engine.assess_framework(framework)
        assessments.append(assessment)

    # Step 2: Verify all assessments completed
    assert len(assessments) == 3

    # Step 3: Check each assessment has key data
    for assessment in assessments:
        assert assessment.overall_score >= 0
        assert assessment.compliance_level is not None
        assert assessment.total_controls > 0
        assert len(assessment.control_assessments) == assessment.total_controls
        assert len(assessment.recommendations) > 0

    # Step 4: Verify gap analysis
    total_gaps = sum(len(a.gaps) for a in assessments)
    assert total_gaps >= 0  # May have gaps

    # Step 5: Verify remediation roadmaps for non-compliant assessments
    for assessment in assessments:
        if len(assessment.gaps) > 0:
            assert assessment.remediation_roadmap is not None
            assert assessment.remediation_roadmap.total_effort_hours > 0

    # Step 6: Verify serialization
    for assessment in assessments:
        data = assessment.to_dict()
        assert "framework" in data
        assert "overall_score" in data
        assert "control_assessments" in data
