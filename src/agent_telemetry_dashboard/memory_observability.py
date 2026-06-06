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
