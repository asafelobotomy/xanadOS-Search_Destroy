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
    AutoTuneMetrics,
    AutoTuner,
    PerformanceState,
    TuningAction,
)
from app.core.automation.context_manager import (
    BatteryStatus,
    ContextChangeEvent,
    ContextManager,
    Environment,
    NetworkType,
    PolicyApplication,
    PolicyRule,
    Priority,
    SecurityContext,
    TimeOfDay,
    UserRole,
)
from app.core.automation.rule_generator import (
    GeneratedRule,
    MalwareSample,
    RuleGenerationResult,
    RuleGenerator,
    RuleStatus,
    RuleType,
    ThreatCategory,
)
from app.core.automation.workflow_engine import (
    StepStatus,
    StepType,
    Workflow,
    WorkflowEngine,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
)

__all__ = [
    "AutoTuneMetrics",
    # Auto-tuning
    "AutoTuner",
    "BatteryStatus",
    "ContextChangeEvent",
    # Context-aware automation
    "ContextManager",
    "Environment",
    "GeneratedRule",
    "MalwareSample",
    "NetworkType",
    "PerformanceState",
    "PolicyApplication",
    "PolicyRule",
    "Priority",
    "RuleGenerationResult",
    # Rule generation
    "RuleGenerator",
    "RuleStatus",
    "RuleType",
    "SecurityContext",
    "StepStatus",
    "StepType",
    "ThreatCategory",
    "TimeOfDay",
    "TuningAction",
    "UserRole",
    "Workflow",
    # Workflow orchestration
    "WorkflowEngine",
    "WorkflowResult",
    "WorkflowStatus",
    "WorkflowStep",
]
