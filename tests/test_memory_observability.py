"""Tests for memory-aware observability primitives."""

from __future__ import annotations

from agent_telemetry_dashboard.models import MemoryRetrievalTrace


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
