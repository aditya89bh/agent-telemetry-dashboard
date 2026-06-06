from pathlib import Path

from agent_telemetry_dashboard.explorer import RUN_LIST_COLUMNS, run_listing
from agent_telemetry_dashboard.loader import load_telemetry

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_telemetry.json"


def test_run_listing_returns_newest_first_compact_rows() -> None:
    df = load_telemetry(DATA)
    listing = run_listing(df)

    assert list(listing.columns) == RUN_LIST_COLUMNS
    assert len(listing) == len(df)
    assert listing["timestamp"].is_monotonic_decreasing
