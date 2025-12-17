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

from app.core.automation.rule_generator import (
    RuleGenerator,
    MalwareSample,
    GeneratedRule,
    RuleGenerationResult,
    RuleType,
    RuleStatus,
    ThreatCategory,
)

from app.core.automation.context_manager import (
    ContextManager,
    SecurityContext,
    PolicyRule,
    ContextChangeEvent,
    PolicyApplication,
    Environment,
    UserRole,
    TimeOfDay,
    NetworkType,
    BatteryStatus,
    Priority,
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
    # Rule generation
    "RuleGenerator",
    "MalwareSample",
    "GeneratedRule",
    "RuleGenerationResult",
    "RuleType",
    "RuleStatus",
    "ThreatCategory",
    # Context-aware automation
    "ContextManager",
    "SecurityContext",
    "PolicyRule",
    "ContextChangeEvent",
    "PolicyApplication",
    "Environment",
    "UserRole",
    "TimeOfDay",
    "NetworkType",
    "BatteryStatus",
    "Priority",
]
