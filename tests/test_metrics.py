from pathlib import Path

from agent_telemetry_dashboard.loader import load_telemetry
from agent_telemetry_dashboard.metrics import (
    confidence_distribution,
    drift_over_time,
    failure_rate_by_agent,
    latency_distribution,
    memory_ops_over_time,
    overview_metrics,
    retry_count_per_task,
    status_breakdown,
    tool_calls_per_run,
)

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_telemetry.json"


def test_overview_metrics_are_deterministic() -> None:
    df = load_telemetry(DATA)
    metrics = overview_metrics(df)

    assert metrics["runs"] == 42
    assert metrics["total_tool_calls"] == int(df["tool_calls"].sum())
    assert metrics["total_memory_ops"] == int(df["memory_reads"].sum() + df["memory_writes"].sum())
    assert metrics["failure_rate"] == (df["status"] == "failed").mean()
    assert metrics["failed_runs"] == int(df["status"].eq("failed").sum())
    assert metrics["warning_runs"] == int(df["status"].eq("warning").sum())
    assert metrics["avg_latency_ms"] == float(df["latency_ms"].mean())


def test_memory_ops_over_time_groups_by_day() -> None:
    df = load_telemetry(DATA)
    daily = memory_ops_over_time(df)

    assert {"date", "memory_reads", "memory_writes"} == set(daily.columns)
    assert daily["memory_reads"].sum() == df["memory_reads"].sum()
    assert daily["memory_writes"].sum() == df["memory_writes"].sum()


def test_failure_rate_by_agent() -> None:
    df = load_telemetry(DATA)
    result = failure_rate_by_agent(df)

    assert set(result.columns) == {"agent_name", "failure_rate"}
    assert result["failure_rate"].between(0, 1).all()


def test_status_breakdown_counts_runs() -> None:
    df = load_telemetry(DATA)
    result = status_breakdown(df)

    assert set(result.columns) == {"status", "runs", "percentage"}
    assert result["runs"].sum() == len(df)
    assert round(result["percentage"].sum(), 10) == 1.0


def test_chart_metric_frames_have_expected_columns() -> None:
    df = load_telemetry(DATA)

    assert list(tool_calls_per_run(df).columns) == ["run_id", "agent_name", "tool_calls"]
    assert list(retry_count_per_task(df).columns) == ["task_name", "retries"]
    assert list(drift_over_time(df).columns) == ["timestamp", "agent_name", "drift_score"]
    assert list(latency_distribution(df).columns) == [
        "run_id",
        "agent_name",
        "status",
        "latency_ms",
    ]
    assert list(confidence_distribution(df).columns) == [
        "run_id",
        "agent_name",
        "status",
        "confidence",
    ]
