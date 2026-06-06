"""Tests for persistent trace store components."""

from __future__ import annotations

from agent_telemetry_dashboard.datasets import DatasetRegistry
from agent_telemetry_dashboard.trace_store import (
    SQLiteTraceStore,
    StoredTrace,
    TraceQuery,
    TraceRepository,
    filter_stored_traces,
    query_traces_dataframe,
)


def sample_trace(trace_id: str = "trace-1") -> StoredTrace:
    return StoredTrace(
        trace_id=trace_id,
        dataset_id="dataset-1",
        trace_type="event",
        run_id="run-1",
        timestamp="2026-01-01T00:00:00",
        payload={"event_name": "started"},
    )


def test_sqlite_trace_store_round_trip(tmp_path) -> None:  # noqa: ANN001
    repository = TraceRepository(SQLiteTraceStore(tmp_path / "traces.sqlite"))
    repository.save(sample_trace())

    traces = repository.list_traces("dataset-1")

    assert len(traces) == 1
    assert traces[0].trace_id == "trace-1"
    assert traces[0].payload["event_name"] == "started"


def test_trace_query_dataframe_and_filtering(tmp_path) -> None:  # noqa: ANN001
    repository = TraceRepository(SQLiteTraceStore(tmp_path / "traces.sqlite"))
    repository.save(sample_trace("trace-1"))
    repository.save(
        StoredTrace(
            trace_id="trace-2",
            dataset_id="dataset-1",
            trace_type="tool_call",
            run_id="run-2",
            timestamp="2026-01-01T00:01:00",
            payload={"tool_name": "search"},
        )
    )

    df = query_traces_dataframe(repository, TraceQuery(dataset_id="dataset-1"))
    filtered = filter_stored_traces(repository.list_traces("dataset-1"), trace_type="tool_call")

    assert df["trace_id"].tolist() == ["trace-1", "trace-2"]
    assert len(filtered) == 1
    assert filtered[0].trace_id == "trace-2"


def test_dataset_registry_management(tmp_path) -> None:  # noqa: ANN001
    registry = DatasetRegistry(tmp_path / "datasets.json")
    entry = registry.register("dataset-1", "Dataset One", "Example")

    assert entry.dataset_id == "dataset-1"
    assert registry.get("dataset-1") is not None
    assert registry.remove("dataset-1")
    assert registry.get("dataset-1") is None
