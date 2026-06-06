from pathlib import Path

from agent_telemetry_dashboard.analytics import agent_performance_scores, aggregate_metrics
from agent_telemetry_dashboard.loader import load_telemetry

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_telemetry.json"


def test_aggregate_metrics_counts_core_totals() -> None:
    df = load_telemetry(DATA)
    metrics = aggregate_metrics(df)

    assert metrics["runs"] == len(df)
    assert metrics["agents"] == df["agent_name"].nunique()
    assert metrics["tasks"] == df["task_name"].nunique()
    assert metrics["total_tool_calls"] == int(df["tool_calls"].sum())
    assert metrics["total_memory_reads"] == int(df["memory_reads"].sum())
    assert metrics["total_memory_writes"] == int(df["memory_writes"].sum())


def test_agent_performance_scores_rank_agents() -> None:
    df = load_telemetry(DATA)
    scores = agent_performance_scores(df)

    assert set(scores["agent_name"]) == set(df["agent_name"].unique())
    assert scores["score"].between(0, 100).all()
    assert scores["score"].is_monotonic_decreasing
