"""Reporting module for xanadOS Search & Destroy.

This module provides comprehensive reporting capabilities including:
- Scan result reports
- Security compliance reports
- Performance metrics
- Threat analysis
- Interactive web-based reports (Phase 2, Task 2.3.1)
- Trend analysis & predictions (Phase 2, Task 2.3.2)
- Compliance framework expansion (Phase 2, Task 2.3.3)
- Automated report scheduling (Phase 2, Task 2.3.4)
"""

from app.reporting.compliance_frameworks import (
    CISControlsFramework,
    ComplianceControl,
    ComplianceFrameworkEngine,
    ComplianceGap,
    ComplianceLevel,
    ControlAssessment,
    ControlStatus,
    CustomFrameworkBuilder,
    FedRAMPFramework,
    FrameworkAssessment,
    FrameworkType,
    HIPAAFramework,
    NISTCSFFramework,
    RemediationRoadmap,
    RiskLevel,
    SOC2Framework,
)
from app.reporting.scheduler import (
    DeliveryStatus,
    EmailConfig,
    EmailDistributor,
    ReportArchiver,
    ReportDelivery,
    ReportFormat,
    ReportSchedule,
    ReportScheduler,
    ReportType,
    RetentionPolicy,
    ScheduleFrequency,
    TriggerCondition,
    TriggerRule,
)
from app.reporting.trend_analysis import (
    Anomaly,
    ForecastResult,
    Prediction,
    TimeSeriesData,
    TrendAnalysis,
    TrendAnalysisEngine,
)
from app.reporting.web_reports import (
    ChartConfig,
    ExportOptions,
    ReportData,
    WebReportGenerator,
)

__all__ = [
    "Anomaly",
    "CISControlsFramework",
    "ChartConfig",
    "ComplianceControl",
    # Phase 2, Task 2.3.3: Compliance Frameworks
    "ComplianceFrameworkEngine",
    "ComplianceGap",
    "ComplianceLevel",
    "ControlAssessment",
    "ControlStatus",
    "CustomFrameworkBuilder",
    "DeliveryStatus",
    "EmailConfig",
    "EmailDistributor",
    "ExportOptions",
    "FedRAMPFramework",
    "ForecastResult",
    "FrameworkAssessment",
    "FrameworkType",
    "HIPAAFramework",
    "NISTCSFFramework",
    "Prediction",
    "RemediationRoadmap",
    "ReportArchiver",
    "ReportData",
    "ReportDelivery",
    "ReportFormat",
    "ReportSchedule",
    # Phase 2, Task 2.3.4: Automated Scheduling
    "ReportScheduler",
    "ReportType",
    "RetentionPolicy",
    "RiskLevel",
    "SOC2Framework",
    "ScheduleFrequency",
    "TimeSeriesData",
    "TrendAnalysis",
    # Phase 2, Task 2.3.2: Trend Analysis
    "TrendAnalysisEngine",
    "TriggerCondition",
    "TriggerRule",
    # Phase 2, Task 2.3.1: Web Reports
    "WebReportGenerator",
]
