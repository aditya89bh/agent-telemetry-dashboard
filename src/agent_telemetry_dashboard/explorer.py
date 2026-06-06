"""Session exploration helpers for run-level dashboard views."""

from __future__ import annotations

import pandas as pd

RUN_LIST_COLUMNS = [
    "run_id",
    "agent_name",
    "task_name",
    "timestamp",
    "status",
    "confidence",
    "drift_score",
    "latency_ms",
]


def run_listing(df: pd.DataFrame) -> pd.DataFrame:
    """Return a compact, newest-first listing of agent runs."""
    if df.empty:
        return pd.DataFrame(columns=RUN_LIST_COLUMNS)
    return df[RUN_LIST_COLUMNS].sort_values("timestamp", ascending=False).reset_index(drop=True)


def search_runs(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Search runs by run id, agent name, task name, status, or notes."""
    if df.empty or not query.strip():
        return run_listing(df)
    normalized = query.strip().casefold()
    searchable_columns = ["run_id", "agent_name", "task_name", "status", "notes"]
    mask = df[searchable_columns].astype(str).apply(
        lambda column: column.str.casefold().str.contains(normalized, regex=False)
    )
    return run_listing(df[mask.any(axis=1)])
