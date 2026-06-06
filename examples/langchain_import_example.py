"""Example: convert LangChain events into dashboard telemetry JSON."""

from __future__ import annotations

import json

from agent_telemetry_dashboard.adapters import langchain_events_to_records

EVENTS = [
    {
        "id": "lc-example-1",
        "name": "ResearchChain",
        "run_type": "chain",
        "start_time": "2026-01-01T00:00:00",
        "status": "success",
        "child_runs": [{"id": "search-tool"}],
        "duration_ms": 250,
        "confidence": 0.88,
    }
]

if __name__ == "__main__":
    print(
        json.dumps(
            {"schema_version": "1.0", "records": langchain_events_to_records(EVENTS)},
            indent=2,
        )
    )
