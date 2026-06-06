"""Tests for memory-aware observability primitives."""

from __future__ import annotations

from agent_telemetry_dashboard.memory_observability import (
    detect_memory_conflicts,
    memory_drift_metrics,
    memory_effectiveness_metrics,
    memory_influence_dataframe,
    memory_influence_scores,
    memory_lifecycle_events,
    memory_replay_events,
)
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


def test_memory_influence_scores_rank_memory_items() -> None:
    traces = [
        MemoryInfluenceTrace(
            trace_id="i1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:00:00",
            influence_kind="decision",
            influence_strength=0.8,
        ),
        MemoryInfluenceTrace(
            trace_id="i2",
            run_id="run-2",
            memory_id="mem-1",
            timestamp="2026-01-01T00:01:00",
            influence_kind="response",
            influence_strength=0.6,
        ),
        MemoryInfluenceTrace(
            trace_id="i3",
            run_id="run-3",
            memory_id="mem-2",
            timestamp="2026-01-01T00:02:00",
            influence_kind="plan",
            influence_strength=0.2,
        ),
    ]

    scores = memory_influence_scores(traces)

    assert scores.loc[0, "memory_id"] == "mem-1"
    assert scores.loc[0, "influence_events"] == 2
    assert scores.loc[0, "avg_influence_strength"] == 0.7


def test_memory_effectiveness_metrics_connect_retrievals_to_influences() -> None:
    retrievals = [
        MemoryRetrievalTrace(
            trace_id="r1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:00:00",
            relevance_score=0.9,
        ),
        MemoryRetrievalTrace(
            trace_id="r2",
            run_id="run-1",
            memory_id="mem-2",
            timestamp="2026-01-01T00:00:01",
            relevance_score=0.5,
        ),
    ]
    writes = [
        MemoryWriteTrace(
            trace_id="w1",
            run_id="run-1",
            memory_id="mem-3",
            timestamp="2026-01-01T00:00:02",
        )
    ]
    influences = [
        MemoryInfluenceTrace(
            trace_id="i1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:00:03",
            influence_strength=0.8,
        )
    ]

    metrics = memory_effectiveness_metrics(retrievals, writes, influences)

    assert metrics["retrievals"] == 2
    assert metrics["writes"] == 1
    assert metrics["avg_relevance_score"] == 0.7
    assert metrics["useful_retrieval_rate"] == 0.5


def test_detect_memory_conflicts_flags_divergent_summaries() -> None:
    writes = [
        MemoryWriteTrace(
            trace_id="w1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:00:00",
            new_summary="User prefers short replies.",
        ),
        MemoryWriteTrace(
            trace_id="w2",
            run_id="run-2",
            memory_id="mem-1",
            timestamp="2026-01-01T00:01:00",
            new_summary="User prefers detailed replies.",
        ),
    ]

    conflicts = detect_memory_conflicts(writes)

    assert conflicts.loc[0, "memory_id"] == "mem-1"
    assert conflicts.loc[0, "distinct_summaries"] == 2
    assert conflicts.loc[0, "conflict_score"] == 1.0


def test_memory_drift_metrics_score_summary_changes() -> None:
    writes = [
        MemoryWriteTrace(
            trace_id="w1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:00:00",
            new_summary="Prefers concise replies.",
            importance_score=0.8,
        ),
        MemoryWriteTrace(
            trace_id="w2",
            run_id="run-2",
            memory_id="mem-1",
            timestamp="2026-01-01T00:01:00",
            new_summary="Prefers detailed replies.",
            importance_score=0.6,
        ),
    ]

    drift = memory_drift_metrics(writes)

    assert drift.loc[0, "memory_id"] == "mem-1"
    assert drift.loc[0, "versions"] == 2
    assert drift.loc[0, "drift_score"] == 1.0


def test_memory_lifecycle_events_builds_timeline_dataframe() -> None:
    writes = [
        MemoryWriteTrace(
            trace_id="w2",
            run_id="run-2",
            memory_id="mem-1",
            timestamp="2026-01-01T00:02:00",
            operation="update",
            new_summary="Updated",
        ),
        MemoryWriteTrace(
            trace_id="w1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:01:00",
            operation="create",
            new_summary="Created",
        ),
    ]

    lifecycle = memory_lifecycle_events(writes)

    assert lifecycle["operation"].tolist() == ["create", "update"]
    assert lifecycle.loc[0, "summary"] == "Created"


def test_memory_replay_events_combines_memory_activity_for_run() -> None:
    retrievals = [
        MemoryRetrievalTrace(
            trace_id="r1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:00:00",
            relevance_score=0.9,
            content_summary="Retrieved preference",
        )
    ]
    writes = [
        MemoryWriteTrace(
            trace_id="w1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:01:00",
            operation="update",
            new_summary="Updated preference",
        )
    ]
    influences = [
        MemoryInfluenceTrace(
            trace_id="i1",
            run_id="run-1",
            memory_id="mem-1",
            timestamp="2026-01-01T00:02:00",
            influence_kind="decision",
            target="decision",
            influence_strength=0.8,
        )
    ]

    replay = memory_replay_events(retrievals, writes, influences, run_id="run-1")

    assert replay["event_type"].tolist() == ["retrieval", "write:update", "influence:decision"]
    assert replay.loc[0, "detail"] == "Retrieved preference"
