"""Deterministic metrics for agent telemetry dashboards."""

from __future__ import annotations

import pandas as pd


def overview_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    """Return headline metrics for a telemetry dataframe."""
    if df.empty:
        return {
            "runs": 0,
            "failure_rate": 0.0,
            "avg_confidence": 0.0,
            "avg_drift": 0.0,
            "avg_latency_ms": 0.0,
            "failed_runs": 0,
            "warning_runs": 0,
            "total_tool_calls": 0,
            "total_memory_ops": 0,
        }
    return {
        "runs": int(len(df)),
        "failure_rate": float((df["status"] == "failed").mean()),
        "avg_confidence": float(df["confidence"].mean()),
        "avg_drift": float(df["drift_score"].mean()),
        "avg_latency_ms": float(df["latency_ms"].mean()),
        "failed_runs": int(df["status"].eq("failed").sum()),
        "warning_runs": int(df["status"].eq("warning").sum()),
        "total_tool_calls": int(df["tool_calls"].sum()),
        "total_memory_ops": int(df["memory_reads"].sum() + df["memory_writes"].sum()),
    }


def tool_calls_per_run(df: pd.DataFrame) -> pd.DataFrame:
    return df[["run_id", "agent_name", "tool_calls"]].sort_values("tool_calls", ascending=False)


def memory_ops_over_time(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "memory_reads", "memory_writes"])
    daily = df.assign(date=df["timestamp"].dt.date)
    return daily.groupby("date", as_index=False)[["memory_reads", "memory_writes"]].sum()


def failure_rate_by_agent(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["agent_name", "failure_rate"])
    return (
        df.assign(is_failed=df["status"].eq("failed"))
        .groupby("agent_name", as_index=False)["is_failed"]
        .mean()
        .rename(columns={"is_failed": "failure_rate"})
    )


def status_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Return run counts and percentages by status."""
    if df.empty:
        return pd.DataFrame(columns=["status", "runs", "percentage"])
    counts = df.groupby("status", as_index=False).size().rename(columns={"size": "runs"})
    counts["percentage"] = counts["runs"] / counts["runs"].sum()
    return counts.sort_values("runs", ascending=False).reset_index(drop=True)


def retry_count_per_task(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["task_name", "retries"])
    return (
        df.groupby("task_name", as_index=False)["retries"]
        .sum()
        .sort_values("retries", ascending=False)
    )


def drift_over_time(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "agent_name", "drift_score"])
    return df[["timestamp", "agent_name", "drift_score"]].sort_values("timestamp")


def latency_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return latency values with agent and status context for distribution charts."""
    if df.empty:
        return pd.DataFrame(columns=["run_id", "agent_name", "status", "latency_ms"])
    return df[["run_id", "agent_name", "status", "latency_ms"]].sort_values("latency_ms")


def confidence_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return confidence values with context for histogram and box plots."""
    if df.empty:
        return pd.DataFrame(columns=["run_id", "agent_name", "status", "confidence"])
    return df[["run_id", "agent_name", "status", "confidence"]].sort_values("confidence")
