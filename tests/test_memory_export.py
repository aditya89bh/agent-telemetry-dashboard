"""Tests for memory observability exports."""

from __future__ import annotations

import json

import pandas as pd

from agent_telemetry_dashboard.export import memory_report_json, memory_report_payload


def test_memory_report_payload_exports_memory_metrics_and_operations() -> None:
    df = pd.DataFrame(
        [
            {
                "run_id": "run-1",
                "agent_name": "agent",
                "task_name": "task",
                "memory_reads": 1,
                "memory_writes": 2,
                "status": "success",
            }
        ]
    )

    payload = memory_report_payload(df)
    exported = json.loads(memory_report_json(df))

    assert payload["memory_analytics"]["memory_active_runs"] == 1
    assert payload["memory_operations"][0]["run_id"] == "run-1"
    assert exported["memory_analytics"]["avg_memory_ops_per_run"] == 3.0
