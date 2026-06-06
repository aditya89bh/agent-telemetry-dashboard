import json
from pathlib import Path

from agent_telemetry_dashboard.export import analytics_export_json, analytics_quality_csv
from agent_telemetry_dashboard.loader import load_telemetry

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_telemetry.json"


def test_analytics_export_json_contains_expected_sections() -> None:
    df = load_telemetry(DATA)
    payload = json.loads(analytics_export_json(df))

    assert "aggregate_metrics" in payload
    assert "agent_performance_scores" in payload
    assert "run_quality_scores" in payload
    assert "anomalies" in payload
    assert "multi_agent" in payload


def test_analytics_quality_csv_contains_quality_score() -> None:
    df = load_telemetry(DATA)
    csv_text = analytics_quality_csv(df)

    assert "quality_score" in csv_text
    assert "run_id" in csv_text
