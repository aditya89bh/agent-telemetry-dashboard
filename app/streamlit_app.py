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
from agent_telemetry_dashboard.datasets import DatasetRegistry
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
from agent_telemetry_dashboard.export import (
    analytics_export_json,
    analytics_quality_csv,
    memory_report_json,
)
from agent_telemetry_dashboard.filters import filter_telemetry
from agent_telemetry_dashboard.import_history import (
    append_import_history,
    create_import_history_entry,
    load_import_history,
)
from agent_telemetry_dashboard.import_preview import import_preview, import_preview_summary
from agent_telemetry_dashboard.ingestion import (
    IngestionError,
    ingest_bulk_uploads,
)
from agent_telemetry_dashboard.ingestion_stats import ingestion_statistics
from agent_telemetry_dashboard.loader import load_telemetry
from agent_telemetry_dashboard.memory_observability import (
    memory_analytics_summary,
    memory_health_score,
)
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
from agent_telemetry_dashboard.models import (
    MemoryInfluenceTrace,
    MemoryRetrievalTrace,
    MemoryWriteTrace,
)
from agent_telemetry_dashboard.multi_agent import (
    agent_utilization_metrics,
    multi_agent_comparison,
    orchestration_metrics,
    workflow_visualization_edges,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "sample_telemetry.json"
IMPORT_HISTORY_PATH = ROOT / "data" / "import_history.jsonl"
DATASET_REGISTRY_PATH = ROOT / "data" / "datasets.json"

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
        registry = DatasetRegistry(DATASET_REGISTRY_PATH)
        datasets = registry.list_datasets()
        if datasets:
            selected_dataset = st.selectbox(
                "Saved dataset",
                datasets,
                format_func=lambda dataset: dataset.name,
                help="Select a persisted trace dataset for trace-store workflows.",
            )
            st.caption(f"Dataset ID: `{selected_dataset.dataset_id}`")
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


def render_upload_tab() -> None:
    st.subheader("Telemetry upload")
    st.caption(
        "Import external agent telemetry into the dashboard. "
        "Format-specific ingestion support is added incrementally in Phase 5."
    )
    uploaded_files = st.file_uploader(
        "Upload telemetry file(s)",
        type=["json", "csv", "zip"],
        accept_multiple_files=True,
        help="Use this page to stage telemetry exported by external agent systems.",
    )
    if not uploaded_files:
        st.info("Choose one or more telemetry files to begin an import.")
        return
    st.success(f"Selected {len(uploaded_files)} file(s) for import preview.")
    st.dataframe(
        [
            {
                "filename": uploaded_file.name,
                "size_bytes": uploaded_file.size,
                "content_type": uploaded_file.type or "unknown",
            }
            for uploaded_file in uploaded_files
        ],
        use_container_width=True,
        hide_index=True,
    )
    try:
        result = ingest_bulk_uploads(
            [(uploaded_file.name, uploaded_file.getvalue()) for uploaded_file in uploaded_files]
        )
    except IngestionError as exc:
        st.error(str(exc))
        for error in exc.errors[:10]:
            st.code(error)
        return

    st.metric(f"Imported {result.format.upper()} records", result.records)
    preview_summary = import_preview_summary(result.dataframe)
    st.subheader("Import preview")
    st.write(preview_summary)
    st.dataframe(import_preview(result.dataframe), use_container_width=True, hide_index=True)
    stats = ingestion_statistics(result.dataframe)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Imported agents", stats["agents"])
    s2.metric("Imported tasks", stats["tasks"])
    s3.metric("Success rate", f"{stats['success_rate']:.1%}")
    s4.metric("Avg latency", f"{stats['avg_latency_ms']:.0f} ms")
    with st.expander("Full imported dataframe"):
        st.dataframe(result.dataframe, use_container_width=True, hide_index=True)
    entry = create_import_history_entry(result.source_name, result.format, result.records)
    append_import_history(IMPORT_HISTORY_PATH, entry)

    history = load_import_history(IMPORT_HISTORY_PATH)
    if history:
        st.subheader("Import history")
        st.dataframe([item.__dict__ for item in history[-10:]], use_container_width=True)


def render_analytics_tab(df: pd.DataFrame) -> None:
    st.subheader("Telemetry analytics")
    export_left, export_right = st.columns(2)
    export_left.download_button(
        "Download analytics JSON",
        analytics_export_json(df),
        file_name="agent_telemetry_analytics.json",
        mime="application/json",
    )
    export_right.download_button(
        "Download run quality CSV",
        analytics_quality_csv(df),
        file_name="run_quality_scores.csv",
        mime="text/csv",
    )
    metrics = aggregate_metrics(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agents", metrics["agents"])
    c2.metric("Tasks", metrics["tasks"])
    c3.metric("Success runs", metrics["success_runs"])
    c4.metric("Total retries", metrics["total_retries"])
    memory_metrics = memory_analytics_summary(df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Memory-active runs", memory_metrics["memory_active_runs"])
    m2.metric("Memory-active rate", f"{memory_metrics['memory_active_rate']:.1%}")
    m3.metric("Avg memory ops/run", f"{memory_metrics['avg_memory_ops_per_run']:.1f}")
    m4.metric("Memory failure rate", f"{memory_metrics['memory_failure_rate']:.1%}")

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


def render_agents_tab(df: pd.DataFrame) -> None:
    st.subheader("Per-agent observability")
    orchestration = orchestration_metrics(df)
    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Workflows", orchestration["workflows"])
    o2.metric("Agents", orchestration["agents"])
    o3.metric("Handoffs", orchestration["handoffs"])
    o4.metric("Workflow edges", orchestration["workflow_edges"])

    agents = sorted(df["agent_name"].unique())
    selected_agent = st.selectbox("Agent", agents)
    agent_df = df[df["agent_name"] == selected_agent]
    render_summary_cards(agent_df)

    left, right = st.columns(2)
    with left:
        st.subheader("Agent utilization")
        st.dataframe(agent_utilization_metrics(agent_df), use_container_width=True, hide_index=True)
        st.subheader("Agent run quality")
        st.dataframe(run_quality_scores(agent_df), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Agent latency")
        st.plotly_chart(
            px.line(agent_df.sort_values("timestamp"), x="timestamp", y="latency_ms", markers=True),
            use_container_width=True,
        )
        st.subheader("Agent confidence and drift")
        st.plotly_chart(
            px.line(
                agent_df.sort_values("timestamp"),
                x="timestamp",
                y=["confidence", "drift_score"],
                markers=True,
            ),
            use_container_width=True,
        )

    st.subheader("Multi-agent comparison")
    comparison = multi_agent_comparison(df)
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    st.plotly_chart(
        px.bar(
            comparison,
            x="agent_name",
            y=["success_rate", "failure_rate"],
            barmode="group",
        ),
        use_container_width=True,
    )

    st.subheader("Workflow visualization")
    workflow_edges = workflow_visualization_edges(df)
    if workflow_edges.empty:
        st.info("No cross-agent workflow transitions detected in the selected telemetry.")
    else:
        st.dataframe(workflow_edges, use_container_width=True, hide_index=True)
        st.plotly_chart(
            px.bar(
                workflow_edges.groupby(["source_agent", "target_agent"], as_index=False).size(),
                x="source_agent",
                y="size",
                color="target_agent",
            ),
            use_container_width=True,
        )


def render_memory_tab(df: pd.DataFrame) -> None:
    st.subheader("Memory-aware observability")
    st.caption("Inspect memory activity, health signals, and memory-related risk indicators.")
    st.download_button(
        "Download memory report JSON",
        memory_report_json(df),
        file_name="memory_observability_report.json",
        mime="application/json",
    )
    retrievals = [
        MemoryRetrievalTrace(
            trace_id=f"retrieval-{row.run_id}",
            run_id=row.run_id,
            memory_id=f"{row.agent_name}-retrieval",
            timestamp=row.timestamp,
            relevance_score=float(row.confidence),
            content_summary=f"{row.memory_reads} memory read(s)",
        )
        for row in df.itertuples()
        if row.memory_reads > 0
    ]
    writes = [
        MemoryWriteTrace(
            trace_id=f"write-{row.run_id}",
            run_id=row.run_id,
            memory_id=f"{row.agent_name}-write",
            timestamp=row.timestamp,
            operation="update",
            importance_score=float(row.confidence),
            new_summary=f"{row.memory_writes} memory write(s)",
        )
        for row in df.itertuples()
        if row.memory_writes > 0
    ]
    influences = [
        MemoryInfluenceTrace(
            trace_id=f"influence-{row.run_id}",
            run_id=row.run_id,
            memory_id=f"{row.agent_name}-retrieval",
            timestamp=row.timestamp,
            influence_kind="decision",
            target=row.task_name,
            influence_strength=float(row.confidence),
        )
        for row in df.itertuples()
        if row.memory_reads > 0 and row.status == "success"
    ]
    health = memory_health_score(retrievals, writes, influences)
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Memory health", f"{health['memory_health_score']:.2f}")
    h2.metric("Useful retrievals", f"{health['useful_retrieval_rate']:.1%}")
    h3.metric("Avg relevance", f"{health['avg_relevance_score']:.2f}")
    h4.metric("Conflicts", health["conflict_count"])

    st.subheader("Memory operations by agent")
    st.plotly_chart(
        px.bar(
            memory_activity_by_agent(df),
            x="agent_name",
            y=["memory_reads", "memory_writes"],
            barmode="group",
        ),
        use_container_width=True,
    )
    st.subheader("Memory operations over time")
    st.plotly_chart(
        px.line(memory_ops_over_time(df), x="date", y=["memory_reads", "memory_writes"]),
        use_container_width=True,
    )


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

    overview, reliability, runs, analytics, agents, memory, upload, timeline, data = st.tabs(
        [
            "Overview",
            "Reliability",
            "Runs",
            "Analytics",
            "Agents",
            "Memory",
            "Upload",
            "Run timeline",
            "Raw data",
        ]
    )
    with overview:
        render_overview_tab(filtered)
    with reliability:
        render_reliability_tab(filtered)
    with runs:
        render_runs_tab(filtered)
    with analytics:
        render_analytics_tab(filtered)
    with agents:
        render_agents_tab(filtered)
    with memory:
        render_memory_tab(filtered)
    with upload:
        render_upload_tab()
    with timeline:
        render_timeline_tab(filtered)
    with data:
        render_data_tab(filtered)


if __name__ == "__main__":
    main()
