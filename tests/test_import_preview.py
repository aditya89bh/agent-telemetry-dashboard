"""Tests for import preview helpers."""

from __future__ import annotations

import pandas as pd

from agent_telemetry_dashboard.import_preview import import_preview, import_preview_summary


def test_import_preview_limits_and_orders_columns() -> None:
    df = pd.DataFrame(
        [
            {
                "run_id": "second",
                "agent_name": "agent",
                "task_name": "task",
                "timestamp": pd.Timestamp("2026-01-02"),
                "status": "success",
                "confidence": 0.9,
                "latency_ms": 20,
                "notes": "hidden",
            },
            {
                "run_id": "first",
                "agent_name": "agent",
                "task_name": "task",
                "timestamp": pd.Timestamp("2026-01-01"),
                "status": "warning",
                "confidence": 0.7,
                "latency_ms": 10,
                "notes": "hidden",
            },
        ]
    )

    preview = import_preview(df, limit=1)
    summary = import_preview_summary(df)

    assert preview["run_id"].tolist() == ["first"]
    assert "notes" not in preview.columns
    assert summary["records"] == 2
    assert summary["statuses"] == ["success", "warning"]
