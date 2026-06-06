"""Integration tests across adapters and ingestion."""

from __future__ import annotations

import json

from agent_telemetry_dashboard.adapters import (
    crewai_task_to_record,
    langchain_event_to_record,
    openai_agents_trace_to_record,
)
from agent_telemetry_dashboard.ingestion import ingest_json_upload


def test_adapter_records_can_be_ingested_as_json_upload() -> None:
    records = [
        langchain_event_to_record(
            {
                "id": "lc-integration",
                "name": "Chain",
                "run_type": "chain",
                "start_time": "2026-01-01T00:00:00",
                "status": "success",
            }
        ),
        crewai_task_to_record(
            {
                "task_id": "crew-integration",
                "agent": {"role": "Worker"},
                "description": "Do work",
                "started_at": "2026-01-01T00:01:00",
                "status": "completed",
            }
        ),
        openai_agents_trace_to_record(
            {
                "trace_id": "oa-integration",
                "agent_name": "Agent",
                "task": "Respond",
                "created_at": "2026-01-01T00:02:00",
                "status": "success",
            }
        ),
    ]

    result = ingest_json_upload(
        json.dumps({"schema_version": "1.0", "records": records}).encode("utf-8"),
        source_name="adapter-records.json",
    )

    assert result.records == 3
    assert result.dataframe["run_id"].tolist() == [
        "lc-integration",
        "crew-integration",
        "oa-integration",
    ]
    assert set(result.dataframe["status"]) == {"success"}
