"""Export helpers for telemetry analytics outputs."""

from __future__ import annotations

import json

import pandas as pd

from agent_telemetry_dashboard.analytics import (
    agent_performance_scores,
    aggregate_metrics,
    detect_anomalies,
    run_quality_scores,
)


def analytics_export_payload(df: pd.DataFrame) -> dict[str, object]:
    """Build a JSON-serializable analytics export payload."""
    return {
        "aggregate_metrics": aggregate_metrics(df),
        "agent_performance_scores": agent_performance_scores(df).to_dict(orient="records"),
        "run_quality_scores": run_quality_scores(df).to_dict(orient="records"),
        "anomalies": detect_anomalies(df).to_dict(orient="records"),
    }


def analytics_export_json(df: pd.DataFrame) -> str:
    """Export analytics as pretty JSON."""
    return json.dumps(analytics_export_payload(df), indent=2, default=str)


def analytics_quality_csv(df: pd.DataFrame) -> str:
    """Export run quality scores as CSV text."""
    return run_quality_scores(df).to_csv(index=False)
