from pathlib import Path

from agent_telemetry_dashboard.explorer import (
    RUN_LIST_COLUMNS,
    confidence_evolution,
    drift_evolution,
    failure_inspection,
    filter_runs_by_status,
    memory_event_timeline,
    retry_inspection,
    run_detail,
    run_event_timeline,
    run_listing,
    run_metadata,
    search_runs,
    tool_call_timeline,
)
from agent_telemetry_dashboard.loader import load_telemetry

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_telemetry.json"


def test_run_listing_returns_newest_first_compact_rows() -> None:
    df = load_telemetry(DATA)
    listing = run_listing(df)

    assert list(listing.columns) == RUN_LIST_COLUMNS
    assert len(listing) == len(df)
    assert listing["timestamp"].is_monotonic_decreasing


def test_search_runs_matches_task_and_agent_text() -> None:
    df = load_telemetry(DATA)

    task_matches = search_runs(df, "support")
    agent_matches = search_runs(df, "memoryscout")

    assert not task_matches.empty
    assert task_matches["task_name"].str.contains("support").any()
    assert set(agent_matches["agent_name"]) == {"MemoryScout"}


def test_filter_runs_by_status_limits_listing_rows() -> None:
    df = load_telemetry(DATA)
    failed = filter_runs_by_status(df, ["failed"])

    assert not failed.empty
    assert set(failed["status"]) == {"failed"}


def test_run_detail_returns_selected_run() -> None:
    df = load_telemetry(DATA)
    detail = run_detail(df, "run-001")

    assert detail["run_id"] == "run-001"
    assert detail["agent_name"] == "MemoryScout"


def test_run_event_timeline_is_ordered() -> None:
    df = load_telemetry(DATA)
    timeline = run_event_timeline(run_detail(df, "run-001"))

    assert timeline["event_time"].is_monotonic_increasing
    assert timeline["event_type"].iloc[0] == "run_started"
    assert timeline["event_type"].iloc[-1] == "run_completed"


def test_memory_event_timeline_contains_read_and_write_counts() -> None:
    df = load_telemetry(DATA)
    detail = run_detail(df, "run-001")
    timeline = memory_event_timeline(detail)

    assert set(timeline["event_type"]) == {"memory_reads", "memory_writes"}
    assert timeline["count"].sum() == detail["memory_reads"] + detail["memory_writes"]


def test_tool_call_timeline_has_one_row_per_tool_call() -> None:
    df = load_telemetry(DATA)
    detail = run_detail(df, "run-001")
    timeline = tool_call_timeline(detail)

    assert len(timeline) == detail["tool_calls"]
    assert timeline["event_time"].is_monotonic_increasing


def test_confidence_evolution_scopes_to_selected_agent() -> None:
    df = load_telemetry(DATA)
    detail = run_detail(df, "run-001")
    evolution = confidence_evolution(df, detail)

    assert set(evolution["agent_name"]) == {detail["agent_name"]}
    assert evolution["timestamp"].is_monotonic_increasing


def test_drift_evolution_scopes_to_selected_agent() -> None:
    df = load_telemetry(DATA)
    detail = run_detail(df, "run-001")
    evolution = drift_evolution(df, detail)

    assert set(evolution["agent_name"]) == {detail["agent_name"]}
    assert evolution["timestamp"].is_monotonic_increasing


def test_run_metadata_contains_display_fields() -> None:
    df = load_telemetry(DATA)
    metadata = run_metadata(run_detail(df, "run-001"))

    assert metadata["Run ID"] == "run-001"
    assert metadata["Agent"] == "MemoryScout"
    assert "Schema version" in metadata


def test_failure_inspection_marks_failed_runs() -> None:
    df = load_telemetry(DATA)
    failed_run_id = df[df["status"] == "failed"].iloc[0]["run_id"]
    inspection = failure_inspection(run_detail(df, failed_run_id))

    assert inspection["has_failures"] is True
    assert inspection["severity"] == "high"


def test_retry_inspection_reports_retry_ratio() -> None:
    df = load_telemetry(DATA)
    retried_run_id = df[df["retries"] > 0].iloc[0]["run_id"]
    inspection = retry_inspection(run_detail(df, retried_run_id))

    assert inspection["has_retries"] is True
    assert inspection["retry_to_failure_ratio"] > 0
