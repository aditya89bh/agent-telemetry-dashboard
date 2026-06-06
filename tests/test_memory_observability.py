"""Tests for memory-aware observability primitives."""

from __future__ import annotations

from agent_telemetry_dashboard.memory_observability import memory_influence_dataframe
from agent_telemetry_dashboard.models import (
    MemoryInfluenceTrace,
    MemoryRetrievalTrace,
    MemoryWriteTrace,
)


def test_memory_retrieval_trace_schema_accepts_valid_trace() -> None:
    trace = MemoryRetrievalTrace.model_validate(
        {
            "trace_id": "retrieval-1",
            "run_id": "run-1",
            "memory_id": "mem-1",
            "timestamp": "2026-01-01T00:00:00",
            "query": "user preference",
            "source": "semantic",
            "relevance_score": 0.92,
            "rank": 1,
            "content_summary": "User prefers concise updates.",
        }
    )

    assert trace.trace_id == "retrieval-1"
    assert trace.source == "semantic"
    assert trace.relevance_score == 0.92


def test_memory_write_trace_schema_accepts_valid_trace() -> None:
    trace = MemoryWriteTrace.model_validate(
        {
            "trace_id": "write-1",
            "run_id": "run-1",
            "memory_id": "mem-1",
            "timestamp": "2026-01-01T00:01:00",
            "operation": "update",
            "source": "episodic",
            "importance_score": 0.84,
            "previous_summary": "Old preference",
            "new_summary": "Updated preference",
        }
    )

    assert trace.operation == "update"
    assert trace.source == "episodic"
    assert trace.importance_score == 0.84


def test_memory_influence_tracking_dataframe_orders_traces() -> None:
    traces = [
        MemoryInfluenceTrace.model_validate(
            {
                "trace_id": "influence-2",
                "run_id": "run-1",
                "memory_id": "mem-2",
                "timestamp": "2026-01-01T00:02:00",
                "influence_kind": "tool_selection",
                "target": "search",
                "evidence": "Prior preference selected search first.",
                "influence_strength": 0.7,
            }
        ),
        MemoryInfluenceTrace.model_validate(
            {
                "trace_id": "influence-1",
                "run_id": "run-1",
                "memory_id": "mem-1",
                "timestamp": "2026-01-01T00:01:00",
                "influence_kind": "decision",
                "target": "choose concise answer",
                "evidence": "Remembered concise preference.",
                "influence_strength": 0.9,
            }
        ),
    ]

    df = memory_influence_dataframe(traces)

    assert df["trace_id"].tolist() == ["influence-1", "influence-2"]
    assert df.loc[0, "influence_kind"] == "decision"
