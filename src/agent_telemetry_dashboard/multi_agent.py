"""Multi-agent observability helpers."""

from __future__ import annotations

import pandas as pd

from agent_telemetry_dashboard.models import AgentCommunicationEvent


def _column_or_default(df: pd.DataFrame, column: str, default: object) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series([default] * len(df), index=df.index)


def agent_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """Return parent-child run relationships with backward-compatible defaults."""
    columns = ["run_id", "parent_run_id", "agent_name", "task_name", "depth"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    hierarchy = pd.DataFrame(
        {
            "run_id": df["run_id"],
            "parent_run_id": _column_or_default(df, "parent_run_id", None),
            "agent_name": df["agent_name"],
            "task_name": df["task_name"],
        }
    )
    parent_lookup = dict(zip(hierarchy["run_id"], hierarchy["parent_run_id"], strict=False))
    hierarchy["depth"] = [
        _hierarchy_depth(run_id=row.run_id, parent_lookup=parent_lookup)
        for row in hierarchy.itertuples()
    ]
    return hierarchy[columns]


def _hierarchy_depth(run_id: str, parent_lookup: dict[str, object]) -> int:
    depth = 0
    seen = {run_id}
    parent = parent_lookup.get(run_id)
    while parent and parent in parent_lookup and parent not in seen:
        seen.add(parent)
        depth += 1
        parent = parent_lookup.get(parent)
    return depth


def agent_relationship_graph(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build graph node and edge tables for agent relationships."""
    if df.empty:
        return (
            pd.DataFrame(columns=["agent_name", "runs", "status"]),
            pd.DataFrame(columns=["source", "target", "relationship", "weight"]),
        )

    nodes = (
        df.groupby("agent_name", as_index=False)
        .agg(runs=("run_id", "count"), status=("status", _dominant_status))
        .sort_values("agent_name")
        .reset_index(drop=True)
    )
    hierarchy = agent_hierarchy(df)
    run_to_agent = dict(zip(hierarchy["run_id"], hierarchy["agent_name"], strict=False))
    edge_rows = []
    for row in hierarchy.dropna(subset=["parent_run_id"]).itertuples(index=False):
        source = run_to_agent.get(row.parent_run_id)
        target = row.agent_name
        if source and source != target:
            edge_rows.append(
                {"source": source, "target": target, "relationship": "parent", "weight": 1}
            )
    edges = pd.DataFrame(edge_rows, columns=["source", "target", "relationship", "weight"])
    if not edges.empty:
        edges = edges.groupby(["source", "target", "relationship"], as_index=False)["weight"].sum()
    return nodes, edges


def _dominant_status(status: pd.Series) -> str:
    if status.eq("failed").any():
        return "failed"
    if status.eq("warning").any():
        return "warning"
    return "success"


def communication_events_to_dataframe(
    events: list[AgentCommunicationEvent],
) -> pd.DataFrame:
    """Convert typed communication events into a dataframe."""
    columns = [
        "event_id",
        "timestamp",
        "source_agent",
        "target_agent",
        "communication_type",
        "run_id",
        "payload_summary",
    ]
    if not events:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame([event.model_dump() for event in events], columns=columns).sort_values(
        "timestamp"
    )


def handoff_tracking(df: pd.DataFrame) -> pd.DataFrame:
    """Return handoff transitions from optional multi-agent telemetry columns."""
    columns = ["run_id", "timestamp", "handoff_from", "handoff_to", "task_name", "status"]
    if df.empty or "handoff_from" not in df.columns or "handoff_to" not in df.columns:
        return pd.DataFrame(columns=columns)
    handoffs = df[df["handoff_from"].notna() & df["handoff_to"].notna()]
    if handoffs.empty:
        return pd.DataFrame(columns=columns)
    return handoffs[columns].sort_values("timestamp").reset_index(drop=True)


def shared_memory_tracking(df: pd.DataFrame) -> pd.DataFrame:
    """Return shared memory key usage by agent and run."""
    columns = ["run_id", "agent_name", "shared_memory_key", "memory_reads", "memory_writes"]
    if df.empty or "shared_memory_keys" not in df.columns:
        return pd.DataFrame(columns=columns)
    rows = []
    for row in df.itertuples(index=False):
        keys = getattr(row, "shared_memory_keys", None) or []
        for key in keys:
            rows.append(
                {
                    "run_id": row.run_id,
                    "agent_name": row.agent_name,
                    "shared_memory_key": key,
                    "memory_reads": row.memory_reads,
                    "memory_writes": row.memory_writes,
                }
            )
    return pd.DataFrame(rows, columns=columns)


def agent_utilization_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-agent utilization from run counts, latency, tools, and memory ops."""
    columns = [
        "agent_name",
        "runs",
        "total_latency_ms",
        "avg_latency_ms",
        "tool_calls",
        "memory_ops",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)
    grouped = df.groupby("agent_name", as_index=False).agg(
        runs=("run_id", "count"),
        total_latency_ms=("latency_ms", "sum"),
        avg_latency_ms=("latency_ms", "mean"),
        tool_calls=("tool_calls", "sum"),
        memory_reads=("memory_reads", "sum"),
        memory_writes=("memory_writes", "sum"),
    )
    grouped["memory_ops"] = grouped["memory_reads"] + grouped["memory_writes"]
    return grouped[columns].sort_values("runs", ascending=False).reset_index(drop=True)
