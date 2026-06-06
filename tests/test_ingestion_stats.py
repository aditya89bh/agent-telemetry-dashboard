"""Tests for ingestion statistics."""

from __future__ import annotations

import pandas as pd

from agent_telemetry_dashboard.ingestion_stats import ingestion_statistics


def test_ingestion_statistics_summarizes_imported_dataframe() -> None:
    df = pd.DataFrame(
        [
            {
                "agent_name": "planner",
                "task_name": "Plan",
                "status": "success",
                "latency_ms": 100,
                "confidence": 0.8,
            },
            {
                "agent_name": "executor",
                "task_name": "Run",
                "status": "failed",
                "latency_ms": 300,
                "confidence": 0.4,
            },
        ]
    )

    stats = ingestion_statistics(df)

    assert stats["records"] == 2
    assert stats["agents"] == 2
    assert stats["tasks"] == 2
    assert stats["success_rate"] == 0.5
    assert stats["failure_rate"] == 0.5
    assert stats["avg_latency_ms"] == 200.0
    assert stats["avg_confidence"] == 0.6000000000000001
