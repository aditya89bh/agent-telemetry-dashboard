import pandas as pd
import pytest
from pydantic import ValidationError

from agent_telemetry_dashboard.models import (
    AgentCommunicationEvent,
    AgentRegistryEntry,
    MultiAgentTelemetryRecord,
)
from agent_telemetry_dashboard.multi_agent import (
    agent_hierarchy,
    agent_relationship_graph,
    agent_utilization_metrics,
    communication_events_to_dataframe,
    handoff_tracking,
    multi_agent_comparison,
    shared_memory_tracking,
)


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


def test_agent_hierarchy_computes_parent_child_depth() -> None:
    df = pd.DataFrame(
        [
            {"run_id": "root", "parent_run_id": None, "agent_name": "Planner", "task_name": "Plan"},
            {"run_id": "child", "parent_run_id": "root", "agent_name": "Worker", "task_name": "Do"},
        ]
    )

    hierarchy = agent_hierarchy(df)

    assert hierarchy.loc[hierarchy["run_id"] == "root", "depth"].iloc[0] == 0
    assert hierarchy.loc[hierarchy["run_id"] == "child", "depth"].iloc[0] == 1


def test_agent_relationship_graph_returns_nodes_and_edges() -> None:
    df = pd.DataFrame(
        [
            {
                "run_id": "root",
                "parent_run_id": None,
                "agent_name": "Planner",
                "task_name": "Plan",
                "status": "success",
            },
            {
                "run_id": "child",
                "parent_run_id": "root",
                "agent_name": "Worker",
                "task_name": "Do",
                "status": "warning",
            },
        ]
    )

    nodes, edges = agent_relationship_graph(df)

    assert set(nodes["agent_name"]) == {"Planner", "Worker"}
    assert edges.iloc[0].to_dict() == {
        "source": "Planner",
        "target": "Worker",
        "relationship": "parent",
        "weight": 1,
    }


def test_communication_events_convert_to_dataframe() -> None:
    event = AgentCommunicationEvent(
        event_id="evt-001",
        timestamp="2026-05-20T09:00:00",
        source_agent="Planner",
        target_agent="Worker",
        communication_type="message",
        run_id="run-001",
        payload_summary="Assign task",
    )

    frame = communication_events_to_dataframe([event])

    assert frame.loc[0, "source_agent"] == "Planner"
    assert frame.loc[0, "target_agent"] == "Worker"


def test_handoff_tracking_extracts_handoff_rows() -> None:
    df = pd.DataFrame(
        [
            {
                "run_id": "run-002",
                "timestamp": pd.Timestamp("2026-05-20T09:10:00"),
                "handoff_from": "Planner",
                "handoff_to": "Worker",
                "task_name": "Execute",
                "status": "success",
            }
        ]
    )

    handoffs = handoff_tracking(df)

    assert len(handoffs) == 1
    assert handoffs.loc[0, "handoff_from"] == "Planner"


def test_shared_memory_tracking_explodes_memory_keys() -> None:
    df = pd.DataFrame(
        [
            {
                "run_id": "run-003",
                "agent_name": "MemoryScout",
                "shared_memory_keys": ["customer_context", "tool_trace"],
                "memory_reads": 3,
                "memory_writes": 1,
            }
        ]
    )

    shared = shared_memory_tracking(df)

    assert len(shared) == 2
    assert set(shared["shared_memory_key"]) == {"customer_context", "tool_trace"}


def test_agent_utilization_metrics_sum_usage() -> None:
    df = pd.DataFrame(
        [
            {
                "run_id": "run-004",
                "agent_name": "Worker",
                "latency_ms": 100,
                "tool_calls": 2,
                "memory_reads": 3,
                "memory_writes": 1,
            },
            {
                "run_id": "run-005",
                "agent_name": "Worker",
                "latency_ms": 200,
                "tool_calls": 1,
                "memory_reads": 1,
                "memory_writes": 1,
            },
        ]
    )

    metrics = agent_utilization_metrics(df)

    assert metrics.loc[0, "runs"] == 2
    assert metrics.loc[0, "memory_ops"] == 6


def test_multi_agent_comparison_returns_agent_rates() -> None:
    df = pd.DataFrame(
        [
            {
                "run_id": "run-006",
                "agent_name": "Planner",
                "status": "success",
                "confidence": 0.9,
                "drift_score": 0.1,
                "latency_ms": 100,
            },
            {
                "run_id": "run-007",
                "agent_name": "Worker",
                "status": "failed",
                "confidence": 0.5,
                "drift_score": 0.5,
                "latency_ms": 300,
            },
        ]
    )

    comparison = multi_agent_comparison(df)

    assert set(comparison["agent_name"]) == {"Planner", "Worker"}
    assert comparison["success_rate"].between(0, 1).all()
