from pathlib import Path

from agent_telemetry_dashboard.analytics import (
    agent_performance_scores,
    aggregate_metrics,
    confidence_trend,
    detect_anomalies,
    drift_trend,
    failure_rates,
    latency_trend,
    memory_usage_trend,
    multi_agent_analytics_summary,
    retry_effectiveness_metrics,
    run_quality_scores,
    success_rates,
    tool_reliability_metrics,
)
from agent_telemetry_dashboard.loader import load_telemetry
from agent_telemetry_dashboard.metrics import overview_metrics

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


def test_success_rates_group_by_agent() -> None:
    df = load_telemetry(DATA)
    rates = success_rates(df)

    assert set(rates.columns) == {"agent_name", "runs", "success_runs", "success_rate"}
    assert rates["success_rate"].between(0, 1).all()
    assert rates["success_runs"].sum() == int(df["status"].eq("success").sum())


def test_failure_rates_group_by_agent() -> None:
    df = load_telemetry(DATA)
    rates = failure_rates(df)

    assert set(rates.columns) == {
        "agent_name",
        "runs",
        "failed_runs",
        "failure_rate",
        "total_failures",
    }
    assert rates["failure_rate"].between(0, 1).all()
    assert rates["failed_runs"].sum() == int(df["status"].eq("failed").sum())


def test_latency_trend_returns_period_statistics() -> None:
    df = load_telemetry(DATA)
    trend = latency_trend(df)

    assert set(trend.columns) == {"period", "avg_latency_ms", "p95_latency_ms", "runs"}
    assert trend["runs"].sum() == len(df)
    assert (trend["p95_latency_ms"] >= trend["avg_latency_ms"]).all()


def test_confidence_trend_returns_bounded_scores() -> None:
    df = load_telemetry(DATA)
    trend = confidence_trend(df)

    assert set(trend.columns) == {
        "period",
        "avg_confidence",
        "min_confidence",
        "max_confidence",
        "runs",
    }
    assert trend["avg_confidence"].between(0, 1).all()
    assert trend["runs"].sum() == len(df)


def test_drift_trend_returns_bounded_scores() -> None:
    df = load_telemetry(DATA)
    trend = drift_trend(df)

    assert set(trend.columns) == {"period", "avg_drift_score", "max_drift_score", "runs"}
    assert trend["avg_drift_score"].between(0, 1).all()
    assert trend["runs"].sum() == len(df)


def test_memory_usage_trend_sums_memory_ops() -> None:
    df = load_telemetry(DATA)
    trend = memory_usage_trend(df)

    assert set(trend.columns) == {"period", "memory_reads", "memory_writes", "memory_ops", "runs"}
    assert trend["memory_reads"].sum() == int(df["memory_reads"].sum())
    assert trend["memory_writes"].sum() == int(df["memory_writes"].sum())


def test_detect_anomalies_flags_failed_runs() -> None:
    df = load_telemetry(DATA)
    anomalies = detect_anomalies(df)

    assert set(anomalies.columns) == {
        "run_id",
        "agent_name",
        "timestamp",
        "rule",
        "severity",
        "value",
    }
    assert "failed_run" in set(anomalies["rule"])
    assert set(anomalies["severity"]).issubset({"medium", "high"})


def test_tool_reliability_metrics_are_bounded() -> None:
    df = load_telemetry(DATA)
    reliability = tool_reliability_metrics(df)

    assert set(reliability.columns) == {
        "agent_name",
        "tool_calls",
        "failures",
        "retries",
        "tool_success_rate",
    }
    assert reliability["tool_success_rate"].between(0, 1).all()


def test_retry_effectiveness_metrics_are_bounded() -> None:
    df = load_telemetry(DATA)
    effectiveness = retry_effectiveness_metrics(df)

    assert set(effectiveness.columns) == {
        "agent_name",
        "retried_runs",
        "retries",
        "recovered_runs",
        "retry_effectiveness",
    }
    assert effectiveness["retry_effectiveness"].between(0, 1).all()


def test_run_quality_scores_are_bounded_and_ranked() -> None:
    df = load_telemetry(DATA)
    scores = run_quality_scores(df)

    assert set(scores.columns) == {"run_id", "agent_name", "task_name", "status", "quality_score"}
    assert scores["quality_score"].between(0, 100).all()
    assert scores["quality_score"].is_monotonic_decreasing


def test_aggregate_metrics_stay_consistent_with_overview_metrics() -> None:
    df = load_telemetry(DATA)
    analytics = aggregate_metrics(df)
    overview = overview_metrics(df)

    assert analytics["runs"] == overview["runs"]
    assert analytics["failed_runs"] == overview["failed_runs"]
    assert analytics["total_tool_calls"] == overview["total_tool_calls"]


def test_analytics_functions_handle_empty_dataframes() -> None:
    df = load_telemetry(DATA).iloc[0:0]

    assert aggregate_metrics(df)["runs"] == 0
    assert agent_performance_scores(df).empty
    assert success_rates(df).empty
    assert failure_rates(df).empty
    assert latency_trend(df).empty
    assert confidence_trend(df).empty
    assert drift_trend(df).empty
    assert memory_usage_trend(df).empty
    assert detect_anomalies(df).empty
    assert tool_reliability_metrics(df).empty
    assert retry_effectiveness_metrics(df).empty
    assert run_quality_scores(df).empty


def test_multi_agent_analytics_summary_contains_sections() -> None:
    df = load_telemetry(DATA)
    summary = multi_agent_analytics_summary(df)

    assert set(summary) == {"orchestration", "utilization", "comparison"}
    assert summary["orchestration"]["agents"] == df["agent_name"].nunique()
