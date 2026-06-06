import pytest
from pydantic import ValidationError

from agent_telemetry_dashboard.models import AgentRegistryEntry, MultiAgentTelemetryRecord


def test_agent_registry_entry_validates_agent_metadata() -> None:
    entry = AgentRegistryEntry(
        agent_name="MemoryScout",
        display_name="Memory Scout",
        role="memory",
        description="Indexes and retrieves memory context.",
    )

    assert entry.agent_name == "MemoryScout"
    assert entry.role == "memory"
    assert entry.enabled is True


def test_agent_registry_entry_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AgentRegistryEntry(agent_name="Agent", display_name="Agent", unexpected="field")


def test_multi_agent_telemetry_extends_base_record() -> None:
    record = MultiAgentTelemetryRecord(
        run_id="run-ma-001",
        agent_name="Planner",
        task_name="Plan workflow",
        timestamp="2026-05-20T09:00:00",
        status="success",
        memory_reads=1,
        memory_writes=1,
        tool_calls=2,
        failures=0,
        retries=0,
        confidence=0.9,
        drift_score=0.1,
        latency_ms=500,
        session_id="session-001",
        workflow_id="workflow-001",
        agent_role="planner",
        shared_memory_keys=["customer_context"],
    )

    assert record.workflow_id == "workflow-001"
    assert record.agent_role == "planner"
    assert record.shared_memory_keys == ["customer_context"]
