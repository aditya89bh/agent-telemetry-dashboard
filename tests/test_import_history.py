"""Tests for import history tracking."""

from __future__ import annotations

from agent_telemetry_dashboard.import_history import (
    append_import_history,
    create_import_history_entry,
    load_import_history,
)


def test_import_history_round_trip(tmp_path) -> None:  # noqa: ANN001
    history_path = tmp_path / "import_history.jsonl"
    entry = create_import_history_entry("runs.json", "json", 2)

    append_import_history(history_path, entry)
    loaded = load_import_history(history_path)

    assert len(loaded) == 1
    assert loaded[0].source_name == "runs.json"
    assert loaded[0].format == "json"
    assert loaded[0].records == 2
    assert loaded[0].status == "success"
