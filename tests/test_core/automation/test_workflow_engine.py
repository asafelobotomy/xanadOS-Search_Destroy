"""
Comprehensive tests for the WorkflowEngine automation system.

Tests cover:
- Basic workflow execution
- Conditional step execution
- Rollback functionality
- Retry logic
- Timeout handling
- YAML template loading
- Execution history
- Action registry
- Error handling
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.automation.workflow_engine import (
    WorkflowEngine,
    Workflow,
    WorkflowStep,
    WorkflowResult,
    StepType,
    StepStatus,
    WorkflowStatus,
)


# ========================================
# Fixtures
# ========================================


@pytest.fixture
def workflow_engine():
    """Create a fresh WorkflowEngine instance."""
    return WorkflowEngine()


@pytest.fixture
def simple_workflow():
    """Create a simple 2-step workflow."""
    return Workflow(
        workflow_id="test_simple",
        name="Simple Test Workflow",
        description="A simple workflow for testing",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Test Step 1",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"key": "value"},
            ),
            WorkflowStep(
                step_id="step2",
                name="Test Step 2",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"key": "value2"},
            ),
        ],
    )


@pytest.fixture
def conditional_workflow():
    """Create a workflow with conditional steps."""
    return Workflow(
        workflow_id="test_conditional",
        name="Conditional Test Workflow",
        description="Workflow with conditional logic",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Unconditional Step",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"output_key": "result1", "value": True},
            ),
            WorkflowStep(
                step_id="step2",
                name="Conditional Step (True)",
                step_type=StepType.CONDITION.value,
                action="test_action",
                params={"value": "executed"},
                condition='context.get("result1") is True',
            ),
            WorkflowStep(
                step_id="step3",
                name="Conditional Step (False)",
                step_type=StepType.CONDITION.value,
                action="test_action",
                params={"value": "skipped"},
                condition='context.get("result1") is False',
            ),
        ],
    )


@pytest.fixture
def rollback_workflow():
    """Create a workflow with rollback capability."""
    return Workflow(
        workflow_id="test_rollback",
        name="Rollback Test Workflow",
        description="Workflow that tests rollback",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Step with Rollback",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"key": "value"},
                rollback_action="rollback_action",
            ),
            WorkflowStep(
                step_id="step2",
                name="Failing Step",
                step_type=StepType.ACTION.value,
                action="failing_action",
                params={},
                on_failure="rollback",
            ),
        ],
        rollback_on_failure=True,
    )


# ========================================
# Test: Basic Workflow Execution
# ========================================


@pytest.mark.asyncio
async def test_simple_workflow_execution(workflow_engine, simple_workflow):
    """Test basic workflow execution with all steps succeeding."""

    # Register test action
    async def test_action(**kwargs):
        return {"success": True, **kwargs}

    workflow_engine.register_action("test_action", test_action)

    # Execute workflow
    result = await workflow_engine.execute_workflow(simple_workflow)

    # Assertions
    assert result.status == WorkflowStatus.COMPLETED.value
    assert result.steps_completed == 2
    assert result.steps_failed == 0
    assert result.steps_skipped == 0
    assert result.error is None
    assert simple_workflow.status == WorkflowStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_workflow_step_execution_order(workflow_engine, simple_workflow):
    """Test that workflow steps execute in order."""
    execution_order = []

    async def make_track_execution(step_id):
        async def track_execution(**kwargs):
            execution_order.append(step_id)
            return {"success": True}

        return track_execution

    # Create workflow with unique action names for each step
    workflow = Workflow(
        workflow_id="test_order",
        name="Order Test Workflow",
        description="Test execution order",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Test Step 1",
                step_type=StepType.ACTION.value,
                action="action1",
                params={"key": "value"},
            ),
            WorkflowStep(
                step_id="step2",
                name="Test Step 2",
                step_type=StepType.ACTION.value,
                action="action2",
                params={"key": "value2"},
            ),
        ],
    )

    # Register unique actions for each step
    workflow_engine.register_action("action1", await make_track_execution("step1"))
    workflow_engine.register_action("action2", await make_track_execution("step2"))

    await workflow_engine.execute_workflow(workflow)

    assert execution_order == ["step1", "step2"]


# ========================================
# Test: Conditional Step Execution
# ========================================


@pytest.mark.asyncio
async def test_conditional_step_true(workflow_engine, conditional_workflow):
    """Test conditional step execution when condition is true."""

    async def test_action(**kwargs):
        return kwargs.get("value", True)

    workflow_engine.register_action("test_action", test_action)

    result = await workflow_engine.execute_workflow(conditional_workflow)

    # Step 2 should execute (condition true), step 3 should be skipped (condition false)
    assert result.status == WorkflowStatus.COMPLETED.value
    assert result.steps_completed == 2  # Step 1 and 2
    assert result.steps_skipped == 1  # Step 3


@pytest.mark.asyncio
async def test_conditional_step_false(workflow_engine):
    """Test conditional step execution when condition is false."""
    workflow = Workflow(
        workflow_id="test_false",
        name="False Condition Test",
        description="Test false condition",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Set False",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"output_key": "flag", "value": False},
            ),
            WorkflowStep(
                step_id="step2",
                name="Should Skip",
                step_type=StepType.CONDITION.value,
                action="test_action",
                params={},
                condition='context.get("flag") is True',
            ),
        ],
    )

    async def test_action(**kwargs):
        return kwargs.get("value", True)

    workflow_engine.register_action("test_action", test_action)

    result = await workflow_engine.execute_workflow(workflow)

    assert result.steps_completed == 1
    assert result.steps_skipped == 1


@pytest.mark.asyncio
async def test_condition_evaluation(workflow_engine):
    """Test various condition expressions."""
    test_cases = [
        ('context.get("value") > 10', {"value": 15}, True),
        ('context.get("value") > 10', {"value": 5}, False),
        ('"test" in context.get("items", [])', {"items": ["test", "other"]}, True),
        ('context.get("count", 0) == 0', {}, True),
        (
            'context.get("flag") and context.get("enabled")',
            {"flag": True, "enabled": True},
            True,
        ),
    ]

    for condition, context, expected in test_cases:
        result = workflow_engine._evaluate_condition(condition, context)
        assert (
            result == expected
        ), f"Condition '{condition}' with context {context} should be {expected}"


# ========================================
# Test: Rollback Functionality
# ========================================


@pytest.mark.asyncio
async def test_workflow_rollback_on_failure(workflow_engine, rollback_workflow):
    """Test that workflow rolls back when a step fails."""
    rollback_called = []

    async def test_action(**kwargs):
        return {"success": True}

    async def failing_action(**kwargs):
        raise ValueError("Simulated failure")

    async def rollback_action(**kwargs):
        rollback_called.append(True)
        return {"rolled_back": True}

    workflow_engine.register_action("test_action", test_action)
    workflow_engine.register_action("failing_action", failing_action)
    workflow_engine.register_action("rollback_action", rollback_action)

    result = await workflow_engine.execute_workflow(rollback_workflow)

    # Check workflow failed and rolled back
    assert result.status == WorkflowStatus.ROLLED_BACK.value
    assert len(rollback_called) == 1  # Rollback was called
    assert rollback_workflow.status == WorkflowStatus.ROLLED_BACK.value


@pytest.mark.asyncio
async def test_rollback_reverse_order(workflow_engine):
    """Test that rollback executes in reverse order."""
    workflow = Workflow(
        workflow_id="test_reverse",
        name="Reverse Rollback Test",
        description="Test rollback order",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Step 1",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"id": 1},
                rollback_action="rollback_action",
            ),
            WorkflowStep(
                step_id="step2",
                name="Step 2",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"id": 2},
                rollback_action="rollback_action",
            ),
            WorkflowStep(
                step_id="step3",
                name="Failing Step",
                step_type=StepType.ACTION.value,
                action="failing_action",
                params={},
            ),
        ],
        rollback_on_failure=True,
    )

    rollback_order = []

    async def test_action(**kwargs):
        return {"success": True}

    async def failing_action(**kwargs):
        raise ValueError("Fail")

    async def rollback_action(**kwargs):
        rollback_order.append(kwargs.get("id"))
        return {"rolled_back": True}

    workflow_engine.register_action("test_action", test_action)
    workflow_engine.register_action("failing_action", failing_action)
    workflow_engine.register_action("rollback_action", rollback_action)

    await workflow_engine.execute_workflow(workflow)

    # Rollback should be in reverse order: step2, step1
    assert rollback_order == [2, 1]


# ========================================
# Test: Retry Logic
# ========================================


@pytest.mark.asyncio
async def test_step_retry_on_failure(workflow_engine):
    """Test that steps retry on failure up to max_retries."""
    attempt_count = 0

    async def flaky_action(**kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Attempt {attempt_count} failed")
        return {"success": True, "attempts": attempt_count}

    workflow = Workflow(
        workflow_id="test_retry",
        name="Retry Test",
        description="Test retry logic",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Flaky Step",
                step_type=StepType.ACTION.value,
                action="flaky_action",
                params={},
                on_failure="retry",
                max_retries=3,
            ),
        ],
    )

    workflow_engine.register_action("flaky_action", flaky_action)

    result = await workflow_engine.execute_workflow(workflow)

    assert result.status == WorkflowStatus.COMPLETED.value
    assert attempt_count == 3  # Should succeed on third attempt
    assert workflow.steps[0].retry_count == 2  # 2 retries before success


@pytest.mark.asyncio
async def test_max_retries_exceeded(workflow_engine):
    """Test that step fails after exceeding max_retries."""

    async def always_fail(**kwargs):
        raise ValueError("Always fails")

    workflow = Workflow(
        workflow_id="test_max_retries",
        name="Max Retries Test",
        description="Test max retry limit",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Always Fails",
                step_type=StepType.ACTION.value,
                action="always_fail",
                params={},
                on_failure="retry",
                max_retries=2,
            ),
        ],
        rollback_on_failure=False,
    )

    workflow_engine.register_action("always_fail", always_fail)

    result = await workflow_engine.execute_workflow(workflow)

    assert result.status == WorkflowStatus.FAILED.value
    assert workflow.steps[0].retry_count == 2  # Hit max retries


# ========================================
# Test: Timeout Handling
# ========================================


@pytest.mark.asyncio
async def test_step_timeout(workflow_engine):
    """Test that steps timeout after configured duration."""

    async def slow_action(**kwargs):
        await asyncio.sleep(10)  # Sleep longer than timeout
        return {"success": True}

    workflow = Workflow(
        workflow_id="test_timeout",
        name="Timeout Test",
        description="Test step timeout",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Slow Step",
                step_type=StepType.ACTION.value,
                action="slow_action",
                params={},
                timeout=0.1,  # Very short timeout
                on_failure="skip",
            ),
        ],
    )

    workflow_engine.register_action("slow_action", slow_action)

    result = await workflow_engine.execute_workflow(workflow)

    # Should fail due to timeout but skip on failure
    assert result.status == WorkflowStatus.COMPLETED.value
    assert workflow.steps[0].status == StepStatus.FAILED.value
    assert "timed out" in workflow.steps[0].error.lower()


# ========================================
# Test: YAML Template Loading
# ========================================


@pytest.mark.asyncio
async def test_load_yaml_template(workflow_engine, tmp_path):
    """Test loading workflow from YAML template."""
    yaml_content = """
id: test_workflow
name: "Test Workflow"
description: "Test workflow from YAML"
rollback_on_failure: true

steps:
  - id: step1
    name: "First Step"
    type: action
    action: test_action
    params:
      key: value
    on_failure: skip
    timeout: 30.0
"""
    yaml_file = tmp_path / "test_workflow.yaml"
    yaml_file.write_text(yaml_content)

    workflow = Workflow.from_yaml(yaml_file)

    assert workflow.workflow_id == "test_workflow"
    assert workflow.name == "Test Workflow"
    assert workflow.rollback_on_failure is True
    assert len(workflow.steps) == 1
    assert workflow.steps[0].step_id == "step1"
    assert workflow.steps[0].action == "test_action"
    assert workflow.steps[0].timeout == 30.0


@pytest.mark.asyncio
async def test_load_template_by_name(workflow_engine):
    """Test loading workflow template by name."""
    # This test assumes templates exist in app/core/automation/templates/
    # We'll test the critical_threat_response template

    workflow = workflow_engine.load_template("critical_threat_response")

    assert workflow is not None
    assert workflow.workflow_id == "critical_threat_response"
    assert len(workflow.steps) > 0


# ========================================
# Test: Execution History
# ========================================


@pytest.mark.asyncio
async def test_execution_history_tracking():
    """Test that workflow executions are tracked in history."""
    # Use fresh workflow engine to avoid pollution from other tests
    fresh_engine = WorkflowEngine()

    # Clear any existing history from disk
    fresh_engine.execution_history = []

    async def test_action(**kwargs):
        return {"success": True}

    fresh_engine.register_action("test_action", test_action)

    # Execute workflow twice with different IDs
    workflow1 = Workflow(
        workflow_id="test_simple_1",
        name="Simple Test Workflow 1",
        description="First test workflow",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Test Step 1",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"key": "value"},
            ),
        ],
    )

    workflow2 = Workflow(
        workflow_id="test_simple_2",
        name="Simple Test Workflow 2",
        description="Second test workflow",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Test Step 1",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={"key": "value"},
            ),
        ],
    )

    await fresh_engine.execute_workflow(workflow1)
    await fresh_engine.execute_workflow(workflow2)

    history = fresh_engine.get_execution_history(limit=10)

    assert len(history) == 2
    assert all(isinstance(entry, WorkflowResult) for entry in history)


@pytest.mark.asyncio
async def test_execution_history_limit(workflow_engine, simple_workflow):
    """Test that execution history respects limit."""

    async def test_action(**kwargs):
        return {"success": True}

    workflow_engine.register_action("test_action", test_action)

    # Execute multiple times
    for i in range(5):
        simple_workflow.workflow_id = f"test_{i}"
        await workflow_engine.execute_workflow(simple_workflow)

    history = workflow_engine.get_execution_history(limit=3)

    assert len(history) == 3


@pytest.mark.asyncio
async def test_workflow_stats():
    """Test workflow statistics generation."""
    # Use fresh workflow engine
    fresh_engine = WorkflowEngine()

    # Clear any existing history
    fresh_engine.execution_history = []

    async def test_action(**kwargs):
        return {"success": True}

    fresh_engine.register_action("test_action", test_action)

    # Create simple workflow
    workflow = Workflow(
        workflow_id="test_stats",
        name="Stats Test Workflow",
        description="Test stats",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Test Step",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={},
            ),
        ],
    )

    await fresh_engine.execute_workflow(workflow)

    stats = fresh_engine.get_workflow_stats()

    assert "total_executions" in stats
    assert "successful_executions" in stats
    assert "failed_executions" in stats
    assert "avg_execution_time" in stats
    assert stats["total_executions"] == 1


# ========================================
# Test: Action Registry
# ========================================


@pytest.mark.asyncio
async def test_register_custom_action(workflow_engine):
    """Test registering custom action handler."""
    custom_called = []

    async def custom_action(**kwargs):
        custom_called.append(kwargs)
        return {"custom": True}

    workflow_engine.register_action("my_custom_action", custom_action)

    workflow = Workflow(
        workflow_id="test_custom",
        name="Custom Action Test",
        description="Test custom action",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Custom Step",
                step_type=StepType.ACTION.value,
                action="my_custom_action",
                params={"test_param": "value"},
            ),
        ],
    )

    result = await workflow_engine.execute_workflow(workflow)

    assert result.status == WorkflowStatus.COMPLETED.value
    assert len(custom_called) == 1
    assert custom_called[0]["test_param"] == "value"


@pytest.mark.asyncio
async def test_action_not_registered(workflow_engine):
    """Test that unknown actions cause workflow failure when not skipped."""
    workflow = Workflow(
        workflow_id="test_unknown",
        name="Unknown Action Test",
        description="Test unknown action",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Unknown Step",
                step_type=StepType.ACTION.value,
                action="nonexistent_action",
                params={},
                on_failure="rollback",  # Default - will cause rollback
            ),
        ],
        rollback_on_failure=False,  # But step-level on_failure takes precedence
    )

    result = await workflow_engine.execute_workflow(workflow)

    assert result.status == WorkflowStatus.ROLLED_BACK.value
    assert result.steps_failed == 1


# ========================================
# Test: Context Sharing
# ========================================


@pytest.mark.asyncio
async def test_context_sharing_between_steps(workflow_engine):
    """Test that steps can share data via context."""
    workflow = Workflow(
        workflow_id="test_context",
        name="Context Sharing Test",
        description="Test context sharing",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Produce Data",
                step_type=StepType.ACTION.value,
                action="producer",
                params={"output_key": "shared_data"},
            ),
            WorkflowStep(
                step_id="step2",
                name="Consume Data",
                step_type=StepType.ACTION.value,
                action="consumer",
                params={},
            ),
        ],
    )

    async def producer(**kwargs):
        return {"value": 42}

    consumer_received = []

    async def consumer(**kwargs):
        # Access shared data from context
        shared = workflow.context.get("shared_data")
        consumer_received.append(shared)
        return {"consumed": True}

    workflow_engine.register_action("producer", producer)
    workflow_engine.register_action("consumer", consumer)

    result = await workflow_engine.execute_workflow(workflow)

    assert result.status == WorkflowStatus.COMPLETED.value
    assert len(consumer_received) == 1
    assert consumer_received[0] == {"value": 42}


# ========================================
# Test: Serialization
# ========================================


def test_workflow_step_serialization():
    """Test WorkflowStep to_dict and from_dict."""
    step = WorkflowStep(
        step_id="test_step",
        name="Test Step",
        step_type=StepType.ACTION.value,
        action="test_action",
        params={"key": "value"},
        condition="context.get('flag')",
        on_failure="retry",
        rollback_action="rollback_test",
        timeout=15.0,
        max_retries=2,
    )

    # Serialize and deserialize
    step_dict = step.to_dict()
    restored_step = WorkflowStep.from_dict(step_dict)

    assert restored_step.step_id == step.step_id
    assert restored_step.name == step.name
    assert restored_step.action == step.action
    assert restored_step.params == step.params
    assert restored_step.condition == step.condition
    assert restored_step.timeout == step.timeout


def test_workflow_serialization():
    """Test Workflow to_dict and from_dict."""
    workflow = Workflow(
        workflow_id="test_wf",
        name="Test Workflow",
        description="Test description",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Step 1",
                step_type=StepType.ACTION.value,
                action="action1",
                params={},
            ),
        ],
        rollback_on_failure=True,
    )

    # Serialize and deserialize
    workflow_dict = workflow.to_dict()
    restored_workflow = Workflow.from_dict(workflow_dict)

    assert restored_workflow.workflow_id == workflow.workflow_id
    assert restored_workflow.name == workflow.name
    assert restored_workflow.rollback_on_failure == workflow.rollback_on_failure
    assert len(restored_workflow.steps) == len(workflow.steps)


def test_workflow_result_serialization():
    """Test WorkflowResult to_dict."""
    result = WorkflowResult(
        workflow_id="test_wf",
        status=WorkflowStatus.COMPLETED.value,
        execution_time=1.5,
        steps_completed=3,
        steps_failed=0,
        steps_skipped=1,
        error=None,
        context={"key": "value"},
        step_results=[{"step": "result"}],
    )

    result_dict = result.to_dict()

    assert result_dict["workflow_id"] == "test_wf"
    assert result_dict["status"] == WorkflowStatus.COMPLETED.value
    assert result_dict["execution_time"] == 1.5
    assert result_dict["steps_completed"] == 3


# ========================================
# Test: Error Handling
# ========================================


@pytest.mark.asyncio
async def test_step_on_failure_skip(workflow_engine):
    """Test that step with on_failure='skip' skips on error."""

    async def failing_action(**kwargs):
        raise ValueError("Expected failure")

    workflow = Workflow(
        workflow_id="test_skip",
        name="Skip On Failure Test",
        description="Test skip behavior",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Failing Step",
                step_type=StepType.ACTION.value,
                action="failing_action",
                params={},
                on_failure="skip",
            ),
            WorkflowStep(
                step_id="step2",
                name="Next Step",
                step_type=StepType.ACTION.value,
                action="test_action",
                params={},
            ),
        ],
        rollback_on_failure=False,
    )

    async def test_action(**kwargs):
        return {"success": True}

    workflow_engine.register_action("failing_action", failing_action)
    workflow_engine.register_action("test_action", test_action)

    result = await workflow_engine.execute_workflow(workflow)

    # Workflow should complete despite step1 failure
    assert result.status == WorkflowStatus.COMPLETED.value
    assert workflow.steps[0].status == StepStatus.FAILED.value
    assert workflow.steps[1].status == StepStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_workflow_failure_without_rollback(workflow_engine):
    """Test workflow failure when rollback_on_failure is False and step doesn't request rollback."""

    async def failing_action(**kwargs):
        raise ValueError("Expected failure")

    workflow = Workflow(
        workflow_id="test_no_rollback",
        name="No Rollback Test",
        description="Test without rollback",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Failing Step",
                step_type=StepType.ACTION.value,
                action="failing_action",
                params={},
                on_failure="skip",  # Skip, not rollback
            ),
        ],
        rollback_on_failure=False,
    )

    workflow_engine.register_action("failing_action", failing_action)

    result = await workflow_engine.execute_workflow(workflow)

    # Should complete (step skipped) without rollback
    assert result.status == WorkflowStatus.COMPLETED.value
    assert workflow.steps[0].status == StepStatus.FAILED.value
    assert result.steps_failed == 1


# ========================================
# Test: Built-in Actions
# ========================================


@pytest.mark.asyncio
async def test_builtin_quarantine_file(workflow_engine, tmp_path):
    """Test built-in quarantine_file action."""
    # Create a test file
    test_file = tmp_path / "malware.txt"
    test_file.write_text("malicious content")

    workflow = Workflow(
        workflow_id="test_quarantine",
        name="Quarantine Test",
        description="Test quarantine action",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Quarantine File",
                step_type=StepType.ACTION.value,
                action="quarantine_file",
                params={"file_path": str(test_file)},
            ),
        ],
    )

    result = await workflow_engine.execute_workflow(workflow)

    assert result.status == WorkflowStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_builtin_send_notification(workflow_engine):
    """Test built-in send_notification action."""
    workflow = Workflow(
        workflow_id="test_notify",
        name="Notification Test",
        description="Test notification action",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="Send Notification",
                step_type=StepType.NOTIFICATION.value,
                action="send_notification",
                params={
                    "recipient": "admin@test.com",
                    "message": "Test notification",
                },
            ),
        ],
    )

    result = await workflow_engine.execute_workflow(workflow)

    assert result.status == WorkflowStatus.COMPLETED.value


# ========================================
# Test: Performance
# ========================================


@pytest.mark.asyncio
async def test_workflow_execution_time(workflow_engine, simple_workflow):
    """Test that simple workflows execute within time limit (<10s)."""

    async def test_action(**kwargs):
        await asyncio.sleep(0.01)  # Small delay to simulate work
        return {"success": True}

    workflow_engine.register_action("test_action", test_action)

    start = datetime.utcnow()
    result = await workflow_engine.execute_workflow(simple_workflow)
    duration = (datetime.utcnow() - start).total_seconds()

    assert result.status == WorkflowStatus.COMPLETED.value
    assert duration < 10.0, f"Workflow took {duration}s, expected <10s"
    assert result.execution_time < 10.0
