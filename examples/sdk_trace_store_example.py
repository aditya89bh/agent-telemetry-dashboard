"""Example: emit traces into a local SQLite trace store with the SDK."""

from __future__ import annotations

from pathlib import Path

from agent_telemetry_dashboard.sdk import TelemetryClient, TelemetrySDKConfig
from agent_telemetry_dashboard.trace_store import SQLiteTraceStore, TraceRepository

STORE_PATH = Path("data/example_traces.sqlite")

if __name__ == "__main__":
    repository = TraceRepository(SQLiteTraceStore(STORE_PATH))
    client = TelemetryClient(
        repository,
        TelemetrySDKConfig(dataset_id="example", service_name="example-agent"),
    )

    client.emit_run_start("run-example-1", agent_name="planner", task_name="Plan a task")
    client.emit_event("run-example-1", "planning_started", {"source": "example"})
    client.emit_tool_call("run-example-1", "search", latency_ms=42)
    client.emit_run_end("run-example-1", status="success", latency_ms=120)

    print(f"Wrote example traces to {STORE_PATH}")
