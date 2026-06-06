"""Tests for external framework telemetry adapters."""

from __future__ import annotations

from agent_telemetry_dashboard.adapters import langchain_event_to_record
from agent_telemetry_dashboard.models import TelemetryRecord


def test_langchain_event_to_record_outputs_valid_telemetry() -> None:
    record = langchain_event_to_record(
        {
            "id": "lc-1",
            "name": "ResearchChain",
            "run_type": "chain",
            "start_time": "2026-01-01T00:00:00",
            "status": "success",
            "child_runs": [{"id": "tool-1"}],
            "duration_ms": 150,
            "confidence": 0.81,
        }
    )

    telemetry = TelemetryRecord.model_validate(record)
    assert telemetry.run_id == "lc-1"
    assert telemetry.agent_name == "ResearchChain"
    assert telemetry.task_name == "chain"
    assert telemetry.tool_calls == 1
    assert telemetry.latency_ms == 150
