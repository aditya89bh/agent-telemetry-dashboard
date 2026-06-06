"""Telemetry analytics engine for aggregate agent run analysis."""

from __future__ import annotations

import pandas as pd


def aggregate_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    """Compute aggregate analytics across a telemetry dataframe."""
    if df.empty:
        return {
            "runs": 0,
            "agents": 0,
            "tasks": 0,
            "success_runs": 0,
            "failed_runs": 0,
            "warning_runs": 0,
            "total_failures": 0,
            "total_retries": 0,
            "total_tool_calls": 0,
            "total_memory_reads": 0,
            "total_memory_writes": 0,
            "avg_confidence": 0.0,
            "avg_drift_score": 0.0,
            "avg_latency_ms": 0.0,
        }

    return {
        "runs": int(len(df)),
        "agents": int(df["agent_name"].nunique()),
        "tasks": int(df["task_name"].nunique()),
        "success_runs": int(df["status"].eq("success").sum()),
        "failed_runs": int(df["status"].eq("failed").sum()),
        "warning_runs": int(df["status"].eq("warning").sum()),
        "total_failures": int(df["failures"].sum()),
        "total_retries": int(df["retries"].sum()),
        "total_tool_calls": int(df["tool_calls"].sum()),
        "total_memory_reads": int(df["memory_reads"].sum()),
        "total_memory_writes": int(df["memory_writes"].sum()),
        "avg_confidence": float(df["confidence"].mean()),
        "avg_drift_score": float(df["drift_score"].mean()),
        "avg_latency_ms": float(df["latency_ms"].mean()),
    }


def agent_performance_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Score each agent from 0-100 using success, confidence, drift, and failures."""
    columns = ["agent_name", "runs", "success_rate", "avg_confidence", "avg_drift", "score"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    grouped = df.groupby("agent_name")
    scores = pd.DataFrame(
        {
            "runs": grouped.size(),
            "success_rate": grouped["status"].apply(lambda status: status.eq("success").mean()),
            "avg_confidence": grouped["confidence"].mean(),
            "avg_drift": grouped["drift_score"].mean(),
            "failure_rate": grouped["status"].apply(lambda status: status.eq("failed").mean()),
        }
    ).reset_index()
    raw_score = (
        scores["success_rate"] * 45
        + scores["avg_confidence"] * 35
        + (1 - scores["avg_drift"]) * 15
        + (1 - scores["failure_rate"]) * 5
    )
    scores["score"] = raw_score.round(2).clip(0, 100)
    return scores[columns].sort_values("score", ascending=False).reset_index(drop=True)


def success_rates(df: pd.DataFrame, by: str = "agent_name") -> pd.DataFrame:
    """Calculate success rates overall or grouped by a telemetry column."""
    columns = [by, "runs", "success_runs", "success_rate"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    grouped = df.groupby(by, as_index=False).agg(
        runs=("run_id", "count"),
        success_runs=("status", lambda status: int(status.eq("success").sum())),
    )
    grouped["success_rate"] = grouped["success_runs"] / grouped["runs"]
    return grouped.sort_values("success_rate", ascending=False).reset_index(drop=True)


def failure_rates(df: pd.DataFrame, by: str = "agent_name") -> pd.DataFrame:
    """Calculate failure rates overall or grouped by a telemetry column."""
    columns = [by, "runs", "failed_runs", "failure_rate", "total_failures"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    grouped = df.groupby(by, as_index=False).agg(
        runs=("run_id", "count"),
        failed_runs=("status", lambda status: int(status.eq("failed").sum())),
        total_failures=("failures", "sum"),
    )
    grouped["failure_rate"] = grouped["failed_runs"] / grouped["runs"]
    return grouped.sort_values("failure_rate", ascending=False).reset_index(drop=True)


def latency_trend(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Analyze average and p95 latency over time."""
    columns = ["period", "avg_latency_ms", "p95_latency_ms", "runs"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    trend = (
        df.set_index("timestamp")
        .resample(freq)
        .agg(
            avg_latency_ms=("latency_ms", "mean"),
            p95_latency_ms=("latency_ms", lambda value: value.quantile(0.95)),
            runs=("run_id", "count"),
        )
        .dropna(subset=["avg_latency_ms"])
        .reset_index()
        .rename(columns={"timestamp": "period"})
    )
    return trend[columns]


def confidence_trend(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Analyze average confidence over time."""
    columns = ["period", "avg_confidence", "min_confidence", "max_confidence", "runs"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    trend = (
        df.set_index("timestamp")
        .resample(freq)
        .agg(
            avg_confidence=("confidence", "mean"),
            min_confidence=("confidence", "min"),
            max_confidence=("confidence", "max"),
            runs=("run_id", "count"),
        )
        .dropna(subset=["avg_confidence"])
        .reset_index()
        .rename(columns={"timestamp": "period"})
    )
    return trend[columns]


def drift_trend(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Analyze average and maximum drift over time."""
    columns = ["period", "avg_drift_score", "max_drift_score", "runs"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    trend = (
        df.set_index("timestamp")
        .resample(freq)
        .agg(
            avg_drift_score=("drift_score", "mean"),
            max_drift_score=("drift_score", "max"),
            runs=("run_id", "count"),
        )
        .dropna(subset=["avg_drift_score"])
        .reset_index()
        .rename(columns={"timestamp": "period"})
    )
    return trend[columns]


def memory_usage_trend(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Analyze memory read/write usage over time."""
    columns = ["period", "memory_reads", "memory_writes", "memory_ops", "runs"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    trend = (
        df.set_index("timestamp")
        .resample(freq)
        .agg(
            memory_reads=("memory_reads", "sum"),
            memory_writes=("memory_writes", "sum"),
            runs=("run_id", "count"),
        )
        .query("runs > 0")
        .reset_index()
        .rename(columns={"timestamp": "period"})
    )
    trend["memory_ops"] = trend["memory_reads"] + trend["memory_writes"]
    return trend[columns]
