"""Load and validate local telemetry datasets."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from agent_telemetry_dashboard.models import TelemetryRecord

COLUMNS = [
    "run_id",
    "agent_name",
    "task_name",
    "timestamp",
    "status",
    "memory_reads",
    "memory_writes",
    "tool_calls",
    "failures",
    "retries",
    "confidence",
    "drift_score",
    "latency_ms",
    "notes",
]


def records_to_dataframe(records: Iterable[TelemetryRecord]) -> pd.DataFrame:
    """Convert validated telemetry records into a consistently typed dataframe."""
    df = pd.DataFrame([record.model_dump() for record in records], columns=COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
    numeric_columns = [
        "memory_reads",
        "memory_writes",
        "tool_calls",
        "failures",
        "retries",
        "confidence",
        "drift_score",
        "latency_ms",
    ]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
    return df.sort_values("timestamp").reset_index(drop=True)


def load_telemetry(path: str | Path) -> pd.DataFrame:
    """Load telemetry from JSON or CSV and validate it with Pydantic."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("JSON telemetry must be a list of records")
        raw_records = payload
    elif path.suffix.lower() == ".csv":
        raw_records = pd.read_csv(path).to_dict(orient="records")
    else:
        raise ValueError(f"Unsupported telemetry format: {path.suffix}")

    records = [TelemetryRecord.model_validate(item) for item in raw_records]
    return records_to_dataframe(records)
