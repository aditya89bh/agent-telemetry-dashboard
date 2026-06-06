from pathlib import Path

from agent_telemetry_dashboard.explorer import (
    RUN_LIST_COLUMNS,
    filter_runs_by_status,
    run_listing,
    search_runs,
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
