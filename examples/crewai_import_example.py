"""Example: convert CrewAI task payloads into dashboard telemetry JSON."""

from __future__ import annotations

import json

from agent_telemetry_dashboard.adapters import crewai_tasks_to_records

TASKS = [
    {
        "task_id": "crew-example-1",
        "agent": {"role": "Researcher"},
        "description": "Collect market evidence",
        "started_at": "2026-01-01T00:00:00",
        "status": "completed",
        "tools": ["search", "scrape"],
        "duration_ms": 410,
    }
]

if __name__ == "__main__":
    print(
        json.dumps(
            {"schema_version": "1.0", "records": crewai_tasks_to_records(TASKS)},
            indent=2,
        )
    )
