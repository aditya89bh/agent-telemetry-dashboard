"""Statistics for imported telemetry datasets."""

from __future__ import annotations

import pandas as pd

DEFAULT_INGESTION_STATS = {
    "records": 0,
    "agents": 0,
    "tasks": 0,
    "success_rate": 0.0,
    "failure_rate": 0.0,
    "avg_latency_ms": 0.0,
    "avg_confidence": 0.0,
}


def ingestion_statistics(df: pd.DataFrame) -> dict[str, float | int]:
    """Return import-level statistics for a validated telemetry dataframe."""
    if df.empty:
        return dict(DEFAULT_INGESTION_STATS)
    records = len(df)
    success_runs = int((df["status"] == "success").sum())
    failed_runs = int((df["status"] == "failed").sum())
    return {
        "records": records,
        "agents": int(df["agent_name"].nunique()),
        "tasks": int(df["task_name"].nunique()),
        "success_rate": success_runs / records,
        "failure_rate": failed_runs / records,
        "avg_latency_ms": float(df["latency_ms"].mean()),
        "avg_confidence": float(df["confidence"].mean()),
    }
