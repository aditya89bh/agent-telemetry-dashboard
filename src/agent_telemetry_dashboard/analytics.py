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
