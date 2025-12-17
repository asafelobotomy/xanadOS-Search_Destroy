"""
Reporting module for xanadOS Search & Destroy.

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

from app.reporting.web_reports import (
    WebReportGenerator,
    ReportData,
    ChartConfig,
    ExportOptions,
)
from app.reporting.trend_analysis import (
    TrendAnalysisEngine,
    TimeSeriesData,
    TrendAnalysis,
    Anomaly,
    Prediction,
    ForecastResult,
)
from app.reporting.compliance_frameworks import (
    ComplianceFrameworkEngine,
    FrameworkType,
    ControlStatus,
    ComplianceLevel,
    RiskLevel,
    ComplianceControl,
    ControlAssessment,
    ComplianceGap,
    RemediationRoadmap,
    FrameworkAssessment,
    NISTCSFFramework,
    CISControlsFramework,
    HIPAAFramework,
    SOC2Framework,
    FedRAMPFramework,
    CustomFrameworkBuilder,
)
from app.reporting.scheduler import (
    ReportScheduler,
    ReportSchedule,
    ScheduleFrequency,
    ReportType,
    ReportFormat,
    TriggerCondition,
    TriggerRule,
    RetentionPolicy,
    EmailConfig,
    EmailDistributor,
    ReportArchiver,
    DeliveryStatus,
    ReportDelivery,
)

__all__ = [
    # Phase 2, Task 2.3.1: Web Reports
    "WebReportGenerator",
    "ReportData",
    "ChartConfig",
    "ExportOptions",
    # Phase 2, Task 2.3.2: Trend Analysis
    "TrendAnalysisEngine",
    "TimeSeriesData",
    "TrendAnalysis",
    "Anomaly",
    "Prediction",
    "ForecastResult",
    # Phase 2, Task 2.3.3: Compliance Frameworks
    "ComplianceFrameworkEngine",
    "FrameworkType",
    "ControlStatus",
    "ComplianceLevel",
    "RiskLevel",
    "ComplianceControl",
    "ControlAssessment",
    "ComplianceGap",
    "RemediationRoadmap",
    "FrameworkAssessment",
    "NISTCSFFramework",
    "CISControlsFramework",
    "HIPAAFramework",
    "SOC2Framework",
    "FedRAMPFramework",
    "CustomFrameworkBuilder",
    # Phase 2, Task 2.3.4: Automated Scheduling
    "ReportScheduler",
    "ReportSchedule",
    "ScheduleFrequency",
    "ReportType",
    "ReportFormat",
    "TriggerCondition",
    "TriggerRule",
    "RetentionPolicy",
    "EmailConfig",
    "EmailDistributor",
    "ReportArchiver",
    "DeliveryStatus",
    "ReportDelivery",
]
