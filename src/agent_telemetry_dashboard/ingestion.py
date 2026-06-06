"""Telemetry ingestion helpers for uploaded external datasets."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import Any

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


@dataclass(frozen=True)
class IngestionValidationReport:
    """Validation summary for raw records before dataframe conversion."""

    total_records: int
    valid_records: int
    errors: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors and self.total_records == self.valid_records


def validate_ingestion_records(raw_records: list[Any]) -> IngestionValidationReport:
    """Validate raw telemetry records and collect row-level validation errors."""
    errors: list[str] = []
    valid_records = 0
    for index, item in enumerate(raw_records, start=1):
        try:
            TelemetryRecord.model_validate(item)
        except Exception as exc:  # noqa: BLE001 - collect validation errors for users.
            errors.append(f"record {index}: {exc}")
        else:
            valid_records += 1
    return IngestionValidationReport(
        total_records=len(raw_records),
        valid_records=valid_records,
        errors=tuple(errors),
    )


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


def ingest_zip_upload(content: bytes, source_name: str = "upload.zip") -> IngestionResult:
    """Parse all supported telemetry files from a ZIP upload."""
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(BytesIO(content)) as archive:
        for member in sorted(archive.namelist()):
            if member.endswith("/"):
                continue
            suffix = member.rsplit(".", maxsplit=1)[-1].lower()
            member_content = archive.read(member)
            if suffix == "json":
                frames.append(ingest_json_upload(member_content, source_name=member).dataframe)
            elif suffix == "csv":
                frames.append(ingest_csv_upload(member_content, source_name=member).dataframe)

    dataframe = pd.concat(frames, ignore_index=True) if frames else records_to_dataframe([])
    if not dataframe.empty:
        dataframe = dataframe.sort_values("timestamp").reset_index(drop=True)
    return IngestionResult(
        source_name=source_name,
        format="zip",
        records=len(dataframe),
        dataframe=dataframe,
    )
