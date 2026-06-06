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

FIELD_ALIASES = {
    "agent": "agent_name",
    "task": "task_name",
    "duration_ms": "latency_ms",
    "error_count": "failures",
    "retry_count": "retries",
}
STATUS_ALIASES = {
    "ok": "success",
    "succeeded": "success",
    "error": "failed",
    "failure": "failed",
    "warn": "warning",
}


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


class IngestionError(ValueError):
    """User-facing ingestion failure with safe remediation context."""

    def __init__(self, message: str, *, source_name: str, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.source_name = source_name
        self.errors = errors


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


def normalize_telemetry_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize common external telemetry field names into the dashboard schema."""
    normalized = dict(record)
    for source_field, target_field in FIELD_ALIASES.items():
        if source_field in normalized and target_field not in normalized:
            normalized[target_field] = normalized.pop(source_field)

    status = normalized.get("status")
    if isinstance(status, str):
        normalized["status"] = STATUS_ALIASES.get(status.lower(), status.lower())

    normalized.setdefault("schema_version", "1.0")
    normalized.setdefault("memory_reads", 0)
    normalized.setdefault("memory_writes", 0)
    normalized.setdefault("tool_calls", 0)
    normalized.setdefault("failures", 0)
    normalized.setdefault("retries", 0)
    normalized.setdefault("confidence", 0.0)
    normalized.setdefault("drift_score", 0.0)
    normalized.setdefault("latency_ms", 0)
    normalized.setdefault("notes", "")
    return normalized


def normalize_telemetry_records(raw_records: list[Any]) -> list[Any]:
    """Normalize a collection of raw telemetry records where possible."""
    return [
        normalize_telemetry_record(item) if isinstance(item, dict) else item
        for item in raw_records
    ]


def ingest_json_upload(content: bytes, source_name: str = "upload.json") -> IngestionResult:
    """Parse a JSON upload into the dashboard telemetry dataframe format."""
    try:
        payload = json.loads(content.decode("utf-8"))
        raw_records = _records_from_json_payload(payload)
    except Exception as exc:  # noqa: BLE001 - convert parser failures to user-facing errors.
        raise IngestionError(
            "Could not parse JSON telemetry upload", source_name=source_name
        ) from exc
    raw_records = normalize_telemetry_records(raw_records)
    report = validate_ingestion_records(raw_records)
    if not report.is_valid:
        raise IngestionError(
            "JSON telemetry upload failed validation",
            source_name=source_name,
            errors=report.errors,
        )
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
    try:
        raw_records = pd.read_csv(BytesIO(content), dtype={"schema_version": "string"}).to_dict(
            orient="records"
        )
    except Exception as exc:  # noqa: BLE001 - convert parser failures to user-facing errors.
        raise IngestionError(
            "Could not parse CSV telemetry upload", source_name=source_name
        ) from exc
    raw_records = normalize_telemetry_records(raw_records)
    report = validate_ingestion_records(raw_records)
    if not report.is_valid:
        raise IngestionError(
            "CSV telemetry upload failed validation",
            source_name=source_name,
            errors=report.errors,
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
    try:
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
    except IngestionError:
        raise
    except Exception as exc:  # noqa: BLE001 - convert parser failures to user-facing errors.
        raise IngestionError(
            "Could not parse ZIP telemetry upload", source_name=source_name
        ) from exc

    if not frames:
        raise IngestionError(
            "ZIP telemetry upload did not contain supported JSON or CSV files",
            source_name=source_name,
        )

    dataframe = pd.concat(frames, ignore_index=True) if frames else records_to_dataframe([])
    if not dataframe.empty:
        dataframe = dataframe.sort_values("timestamp").reset_index(drop=True)
    return IngestionResult(
        source_name=source_name,
        format="zip",
        records=len(dataframe),
        dataframe=dataframe,
    )


def ingest_upload(content: bytes, source_name: str) -> IngestionResult:
    """Dispatch an uploaded file to the correct format-specific ingestion helper."""
    lower_name = source_name.lower()
    if lower_name.endswith(".json"):
        return ingest_json_upload(content, source_name=source_name)
    if lower_name.endswith(".csv"):
        return ingest_csv_upload(content, source_name=source_name)
    if lower_name.endswith(".zip"):
        return ingest_zip_upload(content, source_name=source_name)
    raise IngestionError("Unsupported telemetry upload format", source_name=source_name)


def ingest_bulk_uploads(uploads: list[tuple[str, bytes]]) -> IngestionResult:
    """Import multiple uploaded telemetry files into one combined result."""
    results = [ingest_upload(content, source_name=name) for name, content in uploads]
    frames = [result.dataframe for result in results]
    dataframe = pd.concat(frames, ignore_index=True) if frames else records_to_dataframe([])
    if not dataframe.empty:
        dataframe = dataframe.sort_values("timestamp").reset_index(drop=True)
    formats = "+".join(sorted({result.format for result in results})) if results else "bulk"
    return IngestionResult(
        source_name=f"bulk:{len(results)} files",
        format=formats,
        records=len(dataframe),
        dataframe=dataframe,
    )
