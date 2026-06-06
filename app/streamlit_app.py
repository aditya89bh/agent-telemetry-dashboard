"""Streamlit dashboard for local AI agent telemetry."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from agent_telemetry_dashboard.analytics import (
    agent_performance_scores,
    aggregate_metrics,
    confidence_trend,
    detect_anomalies,
    drift_trend,
    failure_rates,
    latency_trend,
    memory_usage_trend,
    retry_effectiveness_metrics,
    run_quality_scores,
    success_rates,
    tool_reliability_metrics,
)
from agent_telemetry_dashboard.explorer import (
    compare_runs,
    confidence_evolution,
    drift_evolution,
    failure_inspection,
    filter_runs_by_status,
    memory_event_timeline,
    retry_inspection,
    run_detail,
    run_event_timeline,
    run_metadata,
    search_runs,
    tool_call_timeline,
)
from agent_telemetry_dashboard.filters import filter_telemetry
from agent_telemetry_dashboard.loader import load_telemetry
from agent_telemetry_dashboard.metrics import (
    confidence_distribution,
    drift_over_time,
    failure_rate_by_agent,
    failure_retry_by_task,
    latency_distribution,
    memory_activity_by_agent,
    memory_ops_over_time,
    overview_metrics,
    retry_count_per_task,
    status_breakdown,
    tool_calls_per_run,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "sample_telemetry.json"

st.set_page_config(
    page_title="Agent Telemetry Dashboard",
    page_icon="📡",
    layout="wide",
)


@st.cache_data
def cached_load(path: str) -> pd.DataFrame:
    return load_telemetry(path)


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filters")
        agents = sorted(df["agent_name"].unique())
        statuses = sorted(df["status"].unique())
        tasks = sorted(df["task_name"].unique())
        selected_agents = st.multiselect("Agent name", agents, default=agents)
        selected_statuses = st.multiselect("Run status", statuses, default=statuses)
        selected_tasks = st.multiselect("Task name", tasks, default=tasks)
        min_confidence = st.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.05)

        min_date = df["timestamp"].dt.date.min()
        max_date = df["timestamp"].dt.date.max()
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    selected_range = None
    if isinstance(date_range, tuple) and len(date_range) == 2:
        selected_range = date_range
    return filter_telemetry(
        df,
        agents=selected_agents,
        statuses=selected_statuses,
        tasks=selected_tasks,
        date_range=selected_range,
        min_confidence=min_confidence,
    )


def render_summary_cards(df: pd.DataFrame) -> None:
    metrics = overview_metrics(df)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Runs", metrics["runs"])
    c2.metric("Failed runs", metrics["failed_runs"], f"{metrics['failure_rate']:.1%}")
    c3.metric("Avg confidence", f"{metrics['avg_confidence']:.2f}")
    c4.metric("Avg drift", f"{metrics['avg_drift']:.2f}")
    c5.metric("Avg latency", f"{metrics['avg_latency_ms']:.0f} ms")
    c6.metric("Memory ops", metrics["total_memory_ops"])


def render_overview_tab(df: pd.DataFrame) -> None:
    left, right = st.columns(2)
    with left:
        st.subheader("Run status breakdown")
        st.plotly_chart(
            px.pie(
                status_breakdown(df),
                names="status",
                values="runs",
                hole=0.45,
                color="status",
            ),
            use_container_width=True,
        )

        st.subheader("Tool calls per run")
        st.plotly_chart(
            px.bar(tool_calls_per_run(df), x="run_id", y="tool_calls", color="agent_name"),
            use_container_width=True,
        )

        st.subheader("Drift score over time")
        st.plotly_chart(
            px.line(
                drift_over_time(df),
                x="timestamp",
                y="drift_score",
                color="agent_name",
                markers=True,
            ),
            use_container_width=True,
        )

    with right:
        st.subheader("Memory reads/writes over time")
        st.plotly_chart(
            px.line(
                memory_ops_over_time(df),
                x="date",
                y=["memory_reads", "memory_writes"],
                markers=True,
            ),
            use_container_width=True,
        )

        st.subheader("Memory activity by agent")
        st.plotly_chart(
            px.bar(
                memory_activity_by_agent(df),
                x="agent_name",
                y=["memory_reads", "memory_writes"],
                barmode="group",
            ),
            use_container_width=True,
        )


def render_reliability_tab(df: pd.DataFrame) -> None:
    left, right = st.columns(2)
    with left:
        st.subheader("Failure rate by agent")
        st.plotly_chart(
            px.bar(
                failure_rate_by_agent(df),
                x="agent_name",
                y="failure_rate",
                text_auto=".1%",
            ),
            use_container_width=True,
        )

        st.subheader("Failures and retries by task")
        st.plotly_chart(
            px.bar(
                failure_retry_by_task(df),
                x="task_name",
                y=["failures", "retries"],
                barmode="group",
                hover_data=["failed_runs"],
            ),
            use_container_width=True,
        )

    with right:
        st.subheader("Retry count per task")
        st.plotly_chart(
            px.bar(retry_count_per_task(df), x="task_name", y="retries"),
            use_container_width=True,
        )

        st.subheader("Latency distribution")
        st.plotly_chart(
            px.histogram(
                latency_distribution(df),
                x="latency_ms",
                color="status",
                nbins=14,
                marginal="box",
            ),
            use_container_width=True,
        )

        st.subheader("Confidence distribution")
        st.plotly_chart(
            px.histogram(
                confidence_distribution(df),
                x="confidence",
                color="status",
                nbins=12,
                marginal="box",
            ),
            use_container_width=True,
        )


def render_timeline_tab(df: pd.DataFrame) -> None:
    st.subheader("Run timeline")
    timeline = df.sort_values("timestamp").copy()
    timeline["end"] = timeline["timestamp"] + pd.to_timedelta(timeline["latency_ms"], unit="ms")
    st.plotly_chart(
        px.timeline(
            timeline,
            x_start="timestamp",
            x_end="end",
            y="task_name",
            color="status",
            hover_data=["run_id", "agent_name", "confidence", "drift_score", "failures", "retries"],
        ),
        use_container_width=True,
    )


def render_runs_tab(df: pd.DataFrame) -> None:
    st.subheader("Run listing")
    st.caption("Browse individual agent runs before opening deeper session exploration views.")
    query = st.text_input("Search runs", placeholder="Search by run, agent, task, status, or notes")
    statuses = sorted(df["status"].unique())
    selected_statuses = st.multiselect("Run listing status", statuses, default=statuses)
    searched = search_runs(df, query)
    visible_runs = filter_runs_by_status(searched, selected_statuses)
    st.dataframe(
        visible_runs,
        use_container_width=True,
        hide_index=True,
    )
    if visible_runs.empty:
        return

    st.subheader("Run detail")
    selected_run = st.selectbox("Select run", visible_runs["run_id"].tolist())
    detail = run_detail(df, selected_run)
    comparison_run = st.selectbox("Compare against", visible_runs["run_id"].tolist(), index=0)
    if comparison_run != selected_run:
        st.subheader("Run comparison")
        comparison = compare_runs(detail, run_detail(df, comparison_run))
        st.dataframe(comparison, use_container_width=True, hide_index=True)
        st.plotly_chart(
            px.bar(comparison, x="metric", y="delta", title="Comparison delta"),
            use_container_width=True,
        )

    st.subheader("Run metadata")
    metadata = run_metadata(detail)
    meta_cols = st.columns(4)
    for index, (label, value) in enumerate(metadata.items()):
        meta_cols[index % 4].metric(label, value)

    left, right = st.columns(2)
    with left:
        st.write(
            {
                "run_id": detail["run_id"],
                "agent_name": detail["agent_name"],
                "task_name": detail["task_name"],
                "timestamp": detail["timestamp"],
                "status": detail["status"],
            }
        )
    with right:
        st.write(
            {
                "confidence": detail["confidence"],
                "drift_score": detail["drift_score"],
                "latency_ms": detail["latency_ms"],
                "notes": detail["notes"],
            }
        )
    st.subheader("Event timeline")
    events = run_event_timeline(detail)
    st.plotly_chart(
        px.scatter(
            events,
            x="event_time",
            y="event_type",
            color="event_type",
            hover_data=["description"],
        ),
        use_container_width=True,
    )
    st.dataframe(events, use_container_width=True, hide_index=True)

    st.subheader("Memory event timeline")
    memory_events = memory_event_timeline(detail)
    st.plotly_chart(
        px.bar(
            memory_events,
            x="event_time",
            y="count",
            color="event_type",
            hover_data=["description"],
        ),
        use_container_width=True,
    )

    st.subheader("Tool call timeline")
    tool_events = tool_call_timeline(detail)
    st.plotly_chart(
        px.scatter(
            tool_events,
            x="event_time",
            y="tool_call_index",
            color="tool_call_index",
            hover_data=["description"],
        ),
        use_container_width=True,
    )

    st.subheader("Confidence evolution")
    st.plotly_chart(
        px.line(
            confidence_evolution(df, detail),
            x="timestamp",
            y="confidence",
            color="agent_name",
            markers=True,
            hover_data=["run_id"],
        ),
        use_container_width=True,
    )

    st.subheader("Drift evolution")
    st.plotly_chart(
        px.line(
            drift_evolution(df, detail),
            x="timestamp",
            y="drift_score",
            color="agent_name",
            markers=True,
            hover_data=["run_id"],
        ),
        use_container_width=True,
    )

    st.subheader("Failure inspection")
    failure_info = failure_inspection(detail)
    if failure_info["has_failures"]:
        st.error(f"{failure_info['failures']} failure(s), severity: {failure_info['severity']}")
    else:
        st.success("No failures recorded for this run.")
    st.json(failure_info)

    st.subheader("Retry inspection")
    retry_info = retry_inspection(detail)
    if retry_info["has_retries"]:
        st.warning(
            f"{retry_info['retries']} retry attempt(s); "
            f"ratio: {retry_info['retry_to_failure_ratio']}"
        )
    else:
        st.success("No retries recorded for this run.")
    st.json(retry_info)


def render_data_tab(df: pd.DataFrame) -> None:
    st.subheader("Raw telemetry")
    st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)


def render_analytics_tab(df: pd.DataFrame) -> None:
    st.subheader("Telemetry analytics")
    metrics = aggregate_metrics(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agents", metrics["agents"])
    c2.metric("Tasks", metrics["tasks"])
    c3.metric("Success runs", metrics["success_runs"])
    c4.metric("Total retries", metrics["total_retries"])

    left, right = st.columns(2)
    with left:
        st.subheader("Agent performance scores")
        st.plotly_chart(
            px.bar(agent_performance_scores(df), x="agent_name", y="score"),
            use_container_width=True,
        )
        st.subheader("Success and failure rates")
        rate_df = success_rates(df).merge(failure_rates(df), on=["agent_name", "runs"])
        st.plotly_chart(
            px.bar(rate_df, x="agent_name", y=["success_rate", "failure_rate"], barmode="group"),
            use_container_width=True,
        )
        st.subheader("Latency trend")
        st.plotly_chart(
            px.line(latency_trend(df), x="period", y=["avg_latency_ms", "p95_latency_ms"]),
            use_container_width=True,
        )
        st.subheader("Memory usage trend")
        st.plotly_chart(
            px.line(memory_usage_trend(df), x="period", y=["memory_reads", "memory_writes"]),
            use_container_width=True,
        )

    with right:
        st.subheader("Confidence and drift trends")
        st.plotly_chart(
            px.line(confidence_trend(df), x="period", y="avg_confidence"),
            use_container_width=True,
        )
        st.plotly_chart(
            px.line(drift_trend(df), x="period", y="avg_drift_score"),
            use_container_width=True,
        )
        st.subheader("Tool reliability and retries")
        st.dataframe(tool_reliability_metrics(df), use_container_width=True, hide_index=True)
        st.dataframe(retry_effectiveness_metrics(df), use_container_width=True, hide_index=True)

    st.subheader("Run quality and anomalies")
    quality, anomalies = st.columns(2)
    with quality:
        st.dataframe(run_quality_scores(df).head(10), use_container_width=True, hide_index=True)
    with anomalies:
        st.dataframe(detect_anomalies(df), use_container_width=True, hide_index=True)


def main() -> None:
    st.title("📡 Agent Telemetry Dashboard")
    st.caption(
        "Local, deterministic telemetry inspection for memory-enabled and tool-using AI agents."
    )

    data_path = st.sidebar.text_input("Telemetry file", value=str(DEFAULT_DATA))
    df = cached_load(data_path)
    filtered = filter_data(df)

    render_summary_cards(filtered)

    if filtered.empty:
        st.warning("No telemetry records match the selected filters.")
        return

    overview, reliability, runs, analytics, timeline, data = st.tabs(
        ["Overview", "Reliability", "Runs", "Analytics", "Run timeline", "Raw data"]
    )
    with overview:
        render_overview_tab(filtered)
    with reliability:
        render_reliability_tab(filtered)
    with runs:
        render_runs_tab(filtered)
    with analytics:
        render_analytics_tab(filtered)
    with timeline:
        render_timeline_tab(filtered)
    with data:
        render_data_tab(filtered)


if __name__ == "__main__":
    main()
