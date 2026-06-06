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


def filter_runs_by_status(df: pd.DataFrame, statuses: list[str]) -> pd.DataFrame:
    """Filter a run dataframe by status while preserving listing order."""
    if df.empty or not statuses:
        return run_listing(df)
    return run_listing(df[df["status"].isin(statuses)])


def run_detail(df: pd.DataFrame, run_id: str) -> pd.Series:
    """Return a single run detail row by id."""
    matches = df[df["run_id"] == run_id]
    if matches.empty:
        raise KeyError(f"Run not found: {run_id}")
    return matches.sort_values("timestamp").iloc[0]


def run_event_timeline(run: pd.Series) -> pd.DataFrame:
    """Build a deterministic event timeline from a run summary record."""
    start = run["timestamp"]
    latency = int(run["latency_ms"])
    events = [
        {
            "event_time": start,
            "event_type": "run_started",
            "description": f"Started {run['task_name']}",
        },
        {
            "event_time": start + pd.to_timedelta(max(latency // 4, 1), unit="ms"),
            "event_type": "memory_activity",
            "description": f"{run['memory_reads']} reads / {run['memory_writes']} writes",
        },
        {
            "event_time": start + pd.to_timedelta(max(latency // 2, 2), unit="ms"),
            "event_type": "tool_activity",
            "description": f"{run['tool_calls']} tool calls",
        },
    ]
    if int(run["failures"]) > 0 or int(run["retries"]) > 0:
        events.append(
            {
                "event_time": start + pd.to_timedelta(max((latency * 3) // 4, 3), unit="ms"),
                "event_type": "reliability_event",
                "description": f"{run['failures']} failures / {run['retries']} retries",
            }
        )
    events.append(
        {
            "event_time": start + pd.to_timedelta(latency, unit="ms"),
            "event_type": "run_completed",
            "description": f"Completed with status {run['status']}",
        }
    )
    return pd.DataFrame(events).sort_values("event_time").reset_index(drop=True)


def memory_event_timeline(run: pd.Series) -> pd.DataFrame:
    """Return memory-specific events for a selected run."""
    start = run["timestamp"]
    latency = int(run["latency_ms"])
    rows = [
        {
            "event_time": start + pd.to_timedelta(max(latency // 5, 1), unit="ms"),
            "event_type": "memory_reads",
            "count": int(run["memory_reads"]),
            "description": "Memory context reads performed during the run",
        },
        {
            "event_time": start + pd.to_timedelta(max((latency * 4) // 5, 2), unit="ms"),
            "event_type": "memory_writes",
            "count": int(run["memory_writes"]),
            "description": "Memory updates written after task execution",
        },
    ]
    return pd.DataFrame(rows).sort_values("event_time").reset_index(drop=True)
