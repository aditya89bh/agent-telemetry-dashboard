"""Example: convert OpenAI Agents traces into dashboard telemetry JSON."""

from __future__ import annotations

import json

from agent_telemetry_dashboard.adapters import openai_agents_traces_to_records

TRACES = [
    {
        "trace_id": "oa-example-1",
        "agent_name": "SupportAgent",
        "task": "Answer customer ticket",
        "created_at": "2026-01-01T00:00:00",
        "status": "success",
        "tool_calls": [{"name": "knowledge_base"}],
        "duration_ms": 180,
        "usage": {"input_tokens": 120, "output_tokens": 60},
    }
]

if __name__ == "__main__":
    print(
        json.dumps(
            {"schema_version": "1.0", "records": openai_agents_traces_to_records(TRACES)},
            indent=2,
        )
    )
