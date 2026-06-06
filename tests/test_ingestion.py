"""Tests for uploaded telemetry ingestion."""

from __future__ import annotations

import json
import zipfile
from io import BytesIO

from agent_telemetry_dashboard.ingestion import (
    ingest_csv_upload,
    ingest_json_upload,
    ingest_zip_upload,
    validate_ingestion_records,
)


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


def test_ingest_zip_upload_combines_supported_files() -> None:
    archive_bytes = BytesIO()
    with zipfile.ZipFile(archive_bytes, "w") as archive:
        archive.writestr("runs.json", json.dumps([valid_record()]))
        archive.writestr("notes.txt", "ignored")

    result = ingest_zip_upload(archive_bytes.getvalue(), source_name="bundle.zip")

    assert result.source_name == "bundle.zip"
    assert result.format == "zip"
    assert result.records == 1
    assert result.dataframe.loc[0, "run_id"] == "run-json-1"


def test_validate_ingestion_records_reports_row_errors() -> None:
    invalid = valid_record() | {"status": "failed", "failures": 0}

    report = validate_ingestion_records([valid_record(), invalid])

    assert report.total_records == 2
    assert report.valid_records == 1
    assert not report.is_valid
    assert "record 2" in report.errors[0]
