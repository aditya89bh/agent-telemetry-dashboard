"""Telemetry ingestion helpers for uploaded external datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO

import pandas as pd

from agent_telemetry_dashboard.loader import _records_from_json_payload, records_to_dataframe
from agent_telemetry_dashboard.models import TelemetryRecord


@dataclass(frozen=True)
class IngestionResult:
    """Validated telemetry parsed from an uploaded file."""

    source_name: str
    format: str
    records: int
    dataframe: pd.DataFrame


def ingest_json_upload(content: bytes, source_name: str = "upload.json") -> IngestionResult:
    """Parse a JSON upload into the dashboard telemetry dataframe format."""
    payload = json.loads(content.decode("utf-8"))
    raw_records = _records_from_json_payload(payload)
    records = [TelemetryRecord.model_validate(item) for item in raw_records]
    dataframe = records_to_dataframe(records)
    return IngestionResult(
        source_name=source_name,
        format="json",
        records=len(records),
        dataframe=dataframe,
    )


def ingest_csv_upload(content: bytes, source_name: str = "upload.csv") -> IngestionResult:
    """Parse a CSV upload into the dashboard telemetry dataframe format."""
    raw_records = pd.read_csv(BytesIO(content), dtype={"schema_version": "string"}).to_dict(
        orient="records"
    )
    records = [TelemetryRecord.model_validate(item) for item in raw_records]
    dataframe = records_to_dataframe(records)
    return IngestionResult(
        source_name=source_name,
        format="csv",
        records=len(records),
        dataframe=dataframe,
    )
