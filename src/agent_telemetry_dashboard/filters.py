"""Reusable dataframe filters for dashboard telemetry views."""

from __future__ import annotations

from datetime import date

import pandas as pd


def filter_telemetry(
    df: pd.DataFrame,
    *,
    agents: list[str] | None = None,
    statuses: list[str] | None = None,
    tasks: list[str] | None = None,
    date_range: tuple[date, date] | None = None,
    min_confidence: float | None = None,
) -> pd.DataFrame:
    """Apply dashboard filters without mutating the source dataframe."""
    filtered = df.copy()
    if agents:
        filtered = filtered[filtered["agent_name"].isin(agents)]
    if statuses:
        filtered = filtered[filtered["status"].isin(statuses)]
    if tasks:
        filtered = filtered[filtered["task_name"].isin(tasks)]
    if date_range:
        start, end = date_range
        filtered = filtered[
            (filtered["timestamp"].dt.date >= start) & (filtered["timestamp"].dt.date <= end)
        ]
    if min_confidence is not None:
        filtered = filtered[filtered["confidence"] >= min_confidence]
    return filtered.reset_index(drop=True)
