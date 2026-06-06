"""Tests for the production collector API."""

from __future__ import annotations

from agent_telemetry_dashboard.collector import CollectorConfig, create_collector


def test_collector_ingests_and_searches_trace(tmp_path):
    collector = create_collector(CollectorConfig(store_path=tmp_path / "traces.sqlite"))

    response = collector.dispatch(
        "POST",
        "/v1/traces",
        {
            "trace_id": "trace-1",
            "run_id": "run-1",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "trace_type": "event",
            "payload": {"event_name": "started"},
        },
    )

    assert response.status_code == 200
    assert response.body == {"accepted": 1, "trace_ids": ["trace-1"]}

    search = collector.dispatch("POST", "/v1/traces/search", {"text": "started"})

    assert search.status_code == 200
    assert search.body["count"] == 1
    assert search.body["traces"][0]["trace_id"] == "trace-1"


def test_collector_returns_validation_error(tmp_path):
    collector = create_collector(CollectorConfig(store_path=tmp_path / "traces.sqlite"))

    response = collector.dispatch("POST", "/v1/traces", {"trace_id": "missing-fields"})

    assert response.status_code == 400
    assert response.body["error"] == "validation_error"


def test_collector_ingests_batch(tmp_path):
    collector = create_collector(CollectorConfig(store_path=tmp_path / "traces.sqlite"))

    response = collector.dispatch(
        "POST",
        "/v1/traces/batch",
        {
            "traces": [
                {
                    "trace_id": "trace-1",
                    "run_id": "run-1",
                    "timestamp": "2026-01-01T00:00:00+00:00",
                    "payload": {"event_name": "one"},
                },
                {
                    "trace_id": "trace-2",
                    "run_id": "run-1",
                    "timestamp": "2026-01-01T00:00:01+00:00",
                    "payload": {"event_name": "two"},
                },
            ]
        },
    )

    assert response.status_code == 200
    assert response.body == {"accepted": 2, "trace_ids": ["trace-1", "trace-2"]}
