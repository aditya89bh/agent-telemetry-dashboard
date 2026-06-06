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
