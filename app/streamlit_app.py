"""Streamlit dashboard for local AI agent telemetry."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from agent_telemetry_dashboard.loader import load_telemetry
from agent_telemetry_dashboard.metrics import (
    drift_over_time,
    failure_rate_by_agent,
    latency_distribution,
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
        selected_agents = st.multiselect("Agent name", agents, default=agents)
        selected_statuses = st.multiselect("Run status", statuses, default=statuses)

        min_date = df["timestamp"].dt.date.min()
        max_date = df["timestamp"].dt.date.max()
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    filtered = df[df["agent_name"].isin(selected_agents) & df["status"].isin(selected_statuses)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["timestamp"].dt.date >= start) & (filtered["timestamp"].dt.date <= end)
        ]
    return filtered


def main() -> None:
    st.title("📡 Agent Telemetry Dashboard")
    st.caption(
        "Local, deterministic telemetry inspection for memory-enabled and tool-using AI agents."
    )

    data_path = st.sidebar.text_input("Telemetry file", value=str(DEFAULT_DATA))
    df = cached_load(data_path)
    filtered = filter_data(df)

    metrics = overview_metrics(filtered)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Runs", metrics["runs"])
    c2.metric("Failed runs", metrics["failed_runs"], f"{metrics['failure_rate']:.1%}")
    c3.metric("Avg confidence", f"{metrics['avg_confidence']:.2f}")
    c4.metric("Avg drift", f"{metrics['avg_drift']:.2f}")
    c5.metric("Avg latency", f"{metrics['avg_latency_ms']:.0f} ms")
    c6.metric("Memory ops", metrics["total_memory_ops"])

    if filtered.empty:
        st.warning("No telemetry records match the selected filters.")
        return

    left, right = st.columns(2)
    with left:
        st.subheader("Run status breakdown")
        st.plotly_chart(
            px.pie(
                status_breakdown(filtered),
                names="status",
                values="runs",
                hole=0.45,
                color="status",
            ),
            use_container_width=True,
        )

        st.subheader("Tool calls per run")
        st.plotly_chart(
            px.bar(tool_calls_per_run(filtered), x="run_id", y="tool_calls", color="agent_name"),
            use_container_width=True,
        )

        st.subheader("Failure rate by agent")
        st.plotly_chart(
            px.bar(
                failure_rate_by_agent(filtered),
                x="agent_name",
                y="failure_rate",
                text_auto=".1%",
            ),
            use_container_width=True,
        )

        st.subheader("Drift score over time")
        st.plotly_chart(
            px.line(
                drift_over_time(filtered),
                x="timestamp",
                y="drift_score",
                color="agent_name",
                markers=True,
            ),
            use_container_width=True,
        )

    with right:
        st.subheader("Memory reads/writes over time")
        memory_df = memory_ops_over_time(filtered)
        st.plotly_chart(
            px.line(memory_df, x="date", y=["memory_reads", "memory_writes"], markers=True),
            use_container_width=True,
        )

        st.subheader("Latency distribution")
        st.plotly_chart(
            px.histogram(
                latency_distribution(filtered),
                x="latency_ms",
                color="status",
                nbins=14,
                marginal="box",
            ),
            use_container_width=True,
        )

        st.subheader("Confidence distribution")
        st.plotly_chart(
            px.histogram(filtered, x="confidence", color="status", nbins=12, marginal="box"),
            use_container_width=True,
        )

        st.subheader("Retry count per task")
        st.plotly_chart(
            px.bar(retry_count_per_task(filtered), x="task_name", y="retries"),
            use_container_width=True,
        )

    st.subheader("Run timeline")
    timeline = filtered.sort_values("timestamp").copy()
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

    st.subheader("Raw telemetry")
    st.dataframe(filtered.sort_values("timestamp", ascending=False), use_container_width=True)


if __name__ == "__main__":
    main()
