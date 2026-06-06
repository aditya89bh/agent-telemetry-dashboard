"""Tests for telemetry SDK emitters."""

from __future__ import annotations

from agent_telemetry_dashboard.models import MemoryRetrievalTrace
from agent_telemetry_dashboard.sdk import TelemetryClient, TelemetrySDKConfig
from agent_telemetry_dashboard.trace_store import SQLiteTraceStore, TraceRepository


def client(tmp_path) -> TelemetryClient:  # noqa: ANN001
    repository = TraceRepository(SQLiteTraceStore(tmp_path / "sdk.sqlite"))
    return TelemetryClient(repository, TelemetrySDKConfig(dataset_id="sdk-test"))


def test_sdk_emits_generic_event(tmp_path) -> None:  # noqa: ANN001
    sdk = client(tmp_path)

    trace = sdk.emit_event("run-1", "started", {"step": 1})

    assert trace.dataset_id == "sdk-test"
    assert trace.trace_type == "event"
    assert trace.payload["event_name"] == "started"


def test_sdk_emits_memory_trace(tmp_path) -> None:  # noqa: ANN001
    sdk = client(tmp_path)
    memory_trace = MemoryRetrievalTrace(
        trace_id="memory-1",
        run_id="run-1",
        memory_id="mem-1",
        timestamp="2026-01-01T00:00:00",
        relevance_score=0.9,
    )

    trace = sdk.emit_memory_trace(memory_trace)

    assert trace.trace_id == "memory-1"
    assert trace.trace_type == "memory_retrieval"
    assert trace.payload["memory_id"] == "mem-1"


def test_sdk_emits_tool_and_lifecycle_traces(tmp_path) -> None:  # noqa: ANN001
    sdk = client(tmp_path)

    start = sdk.emit_run_start("run-1", "agent", "task")
    tool = sdk.emit_tool_call("run-1", "search", latency_ms=25)
    end = sdk.emit_run_end("run-1", "success", latency_ms=50)

    assert start.trace_type == "run_lifecycle"
    assert tool.trace_type == "tool_call"
    assert tool.payload["tool_name"] == "search"
    assert end.payload["lifecycle_event"] == "end"
