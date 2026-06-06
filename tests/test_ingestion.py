"""Tests for uploaded telemetry ingestion."""

from __future__ import annotations

import json

from agent_telemetry_dashboard.ingestion import ingest_csv_upload, ingest_json_upload


def valid_record() -> dict[str, object]:
    return {
        "run_id": "run-json-1",
        "agent_name": "planner",
        "task_name": "Plan task",
        "timestamp": "2026-01-01T00:00:00",
        "status": "success",
        "memory_reads": 1,
        "memory_writes": 2,
        "tool_calls": 3,
        "failures": 0,
        "retries": 0,
        "confidence": 0.9,
        "drift_score": 0.1,
        "latency_ms": 120,
        "notes": "uploaded",
    }


def test_ingest_json_upload_from_envelope() -> None:
    payload = {"schema_version": "1.0", "records": [valid_record()]}

    result = ingest_json_upload(json.dumps(payload).encode("utf-8"), source_name="runs.json")

    assert result.source_name == "runs.json"
    assert result.format == "json"
    assert result.records == 1
    assert result.dataframe.loc[0, "run_id"] == "run-json-1"


def test_ingest_csv_upload() -> None:
    csv_content = "\n".join(
        [
            "run_id,agent_name,task_name,timestamp,status,memory_reads,memory_writes,"
            "tool_calls,failures,retries,confidence,drift_score,latency_ms,notes",
            "run-csv-1,executor,Execute task,2026-01-01T00:00:00,success,"
            "1,1,2,0,0,0.8,0.2,90,uploaded",
        ]
    )

    result = ingest_csv_upload(csv_content.encode("utf-8"), source_name="runs.csv")

    assert result.source_name == "runs.csv"
    assert result.format == "csv"
    assert result.records == 1
    assert result.dataframe.loc[0, "run_id"] == "run-csv-1"
