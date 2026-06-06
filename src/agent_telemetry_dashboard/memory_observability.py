"""Memory-aware observability helpers."""

from __future__ import annotations

import pandas as pd

from agent_telemetry_dashboard.models import MemoryInfluenceTrace


def memory_influence_dataframe(traces: list[MemoryInfluenceTrace]) -> pd.DataFrame:
    """Convert memory influence traces into a dashboard-friendly dataframe."""
    columns = [
        "trace_id",
        "run_id",
        "memory_id",
        "timestamp",
        "influence_kind",
        "target",
        "evidence",
        "influence_strength",
    ]
    df = pd.DataFrame([trace.model_dump() for trace in traces], columns=columns)
    if df.empty:
        return pd.DataFrame(columns=columns)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
    return df.sort_values("timestamp").reset_index(drop=True)


def memory_influence_scores(traces: list[MemoryInfluenceTrace]) -> pd.DataFrame:
    """Score memory influence by memory item across observed traces."""
    df = memory_influence_dataframe(traces)
    columns = ["memory_id", "influence_events", "avg_influence_strength", "max_influence_strength"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    return (
        df.groupby("memory_id", as_index=False)
        .agg(
            influence_events=("trace_id", "count"),
            avg_influence_strength=("influence_strength", "mean"),
            max_influence_strength=("influence_strength", "max"),
        )
        .sort_values(["avg_influence_strength", "influence_events"], ascending=False)
        .reset_index(drop=True)
    )
