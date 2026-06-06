"""Memory-aware observability helpers."""

from __future__ import annotations

import pandas as pd

from agent_telemetry_dashboard.models import (
    MemoryInfluenceTrace,
    MemoryRetrievalTrace,
    MemoryWriteTrace,
)


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


def memory_effectiveness_metrics(
    retrievals: list[MemoryRetrievalTrace],
    writes: list[MemoryWriteTrace],
    influences: list[MemoryInfluenceTrace],
) -> dict[str, float | int]:
    """Summarize whether memory activity appears useful across runs."""
    retrieval_count = len(retrievals)
    write_count = len(writes)
    influence_count = len(influences)
    avg_relevance = (
        sum(trace.relevance_score for trace in retrievals) / retrieval_count
        if retrieval_count
        else 0.0
    )
    avg_influence = (
        sum(trace.influence_strength for trace in influences) / influence_count
        if influence_count
        else 0.0
    )
    influenced_memory_ids = {trace.memory_id for trace in influences}
    retrieved_memory_ids = {trace.memory_id for trace in retrievals}
    useful_retrieval_rate = (
        len(retrieved_memory_ids & influenced_memory_ids) / len(retrieved_memory_ids)
        if retrieved_memory_ids
        else 0.0
    )
    return {
        "retrievals": retrieval_count,
        "writes": write_count,
        "influences": influence_count,
        "avg_relevance_score": avg_relevance,
        "avg_influence_strength": avg_influence,
        "useful_retrieval_rate": useful_retrieval_rate,
    }


def detect_memory_conflicts(writes: list[MemoryWriteTrace]) -> pd.DataFrame:
    """Detect memory IDs that receive conflicting write summaries."""
    columns = ["memory_id", "write_events", "distinct_summaries", "conflict_score"]
    if not writes:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame([trace.model_dump() for trace in writes])
    df["summary_key"] = df["new_summary"].str.strip().str.lower()
    grouped = (
        df[df["summary_key"] != ""]
        .groupby("memory_id", as_index=False)
        .agg(
            write_events=("trace_id", "count"),
            distinct_summaries=("summary_key", "nunique"),
        )
    )
    conflicts = grouped[grouped["distinct_summaries"] > 1].copy()
    if conflicts.empty:
        return pd.DataFrame(columns=columns)
    conflicts["conflict_score"] = conflicts["distinct_summaries"] / conflicts["write_events"]
    return conflicts.sort_values("conflict_score", ascending=False).reset_index(drop=True)


def memory_drift_metrics(writes: list[MemoryWriteTrace]) -> pd.DataFrame:
    """Estimate per-memory drift from write history and importance changes."""
    columns = ["memory_id", "versions", "summary_changes", "avg_importance", "drift_score"]
    if not writes:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame([trace.model_dump() for trace in writes])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
    df["summary_key"] = df["new_summary"].str.strip().str.lower()
    grouped = (
        df.sort_values("timestamp")
        .groupby("memory_id", as_index=False)
        .agg(
            versions=("trace_id", "count"),
            summary_changes=("summary_key", "nunique"),
            avg_importance=("importance_score", "mean"),
        )
    )
    grouped["drift_score"] = grouped.apply(
        lambda row: 0.0
        if row["versions"] <= 1
        else min(1.0, (row["summary_changes"] - 1) / (row["versions"] - 1)),
        axis=1,
    )
    return grouped.sort_values("drift_score", ascending=False).reset_index(drop=True)
