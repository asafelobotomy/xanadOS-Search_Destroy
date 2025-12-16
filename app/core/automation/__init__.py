"""
Intelligent Automation Subsystem for xanadOS Search & Destroy.

This package provides AI-driven automation capabilities including:
- Self-optimizing performance tuning
- Automated response orchestration
- Intelligent rule generation
- Context-aware decision making

Phase 2, Task 2.2: Intelligent Automation Enhancements
"""

from app.core.automation.auto_tuner import (
    AutoTuner,
    AutoTuneMetrics,
    PerformanceState,
    TuningAction,
)

from app.core.automation.workflow_engine import (
    WorkflowEngine,
    Workflow,
    WorkflowStep,
    WorkflowResult,
    StepType,
    StepStatus,
    WorkflowStatus,
)

__all__ = [
    # Auto-tuning
    "AutoTuner",
    "AutoTuneMetrics",
    "PerformanceState",
    "TuningAction",
    # Workflow orchestration
    "WorkflowEngine",
    "Workflow",
    "WorkflowStep",
    "WorkflowResult",
    "StepType",
    "StepStatus",
    "WorkflowStatus",
]
