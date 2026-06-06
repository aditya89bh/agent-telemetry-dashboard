"""Preview helpers for imported telemetry before analysis."""

from __future__ import annotations

import pandas as pd

PREVIEW_COLUMNS = [
    "run_id",
    "agent_name",
    "task_name",
    "timestamp",
    "status",
    "confidence",
    "latency_ms",
]


def import_preview(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Return a compact preview dataframe for imported telemetry."""
    if df.empty:
        return pd.DataFrame(columns=PREVIEW_COLUMNS)
    visible_columns = [column for column in PREVIEW_COLUMNS if column in df.columns]
    return df.sort_values("timestamp").loc[:, visible_columns].head(limit).reset_index(drop=True)


def import_preview_summary(df: pd.DataFrame) -> dict[str, object]:
    """Return high-level facts used by the import preview page."""
    if df.empty:
        return {"records": 0, "date_start": None, "date_end": None, "statuses": []}
    sorted_df = df.sort_values("timestamp")
    return {
        "records": len(sorted_df),
        "date_start": sorted_df["timestamp"].iloc[0],
        "date_end": sorted_df["timestamp"].iloc[-1],
        "statuses": sorted(sorted_df["status"].unique().tolist()),
    }
