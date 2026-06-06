"""Additional memory-aware tests for empty and low-signal states."""

from __future__ import annotations

import pandas as pd

from agent_telemetry_dashboard.memory_observability import (
    detect_memory_conflicts,
    memory_analytics_summary,
    memory_audit_timeline,
    memory_drift_metrics,
    memory_effectiveness_metrics,
    memory_health_score,
    memory_lifecycle_events,
    memory_replay_events,
)


def test_memory_observability_empty_trace_helpers_return_stable_shapes() -> None:
    assert detect_memory_conflicts([]).empty
    assert memory_drift_metrics([]).empty
    assert memory_lifecycle_events([]).empty
    assert memory_replay_events([], [], []).empty
    assert memory_audit_timeline([], [], [], []).empty


def test_memory_effectiveness_and_health_empty_states_are_zeroed() -> None:
    effectiveness = memory_effectiveness_metrics([], [], [])
    health = memory_health_score([], [], [])

    assert effectiveness["retrievals"] == 0
    assert effectiveness["useful_retrieval_rate"] == 0.0
    assert health["conflict_count"] == 0
    assert health["avg_drift_score"] == 0.0


def test_memory_analytics_summary_empty_dataframe_is_zeroed() -> None:
    summary = memory_analytics_summary(pd.DataFrame())

    assert summary == {
        "memory_active_runs": 0,
        "memory_active_rate": 0.0,
        "avg_memory_ops_per_run": 0.0,
        "memory_failure_rate": 0.0,
    }
