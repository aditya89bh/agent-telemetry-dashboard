"""Adapters for common external agent framework telemetry."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from agent_telemetry_dashboard.ingestion import normalize_telemetry_record


def _iso_now() -> str:
    return datetime.utcnow().isoformat()


def langchain_event_to_record(event: dict[str, Any]) -> dict[str, Any]:
    """Convert a LangChain run/event payload into dashboard telemetry."""
    status = "success"
    if event.get("error") or event.get("status") in {"error", "failed"}:
        status = "failed"
    elif event.get("status") in {"warning", "warn"}:
        status = "warning"

    agent_name = event.get("name") or event.get("serialized", {}).get("name") or "langchain"
    record = {
        "run_id": str(event.get("run_id") or event.get("id") or "langchain-run"),
        "agent_name": str(agent_name),
        "task_name": str(event.get("run_type") or event.get("event") or "langchain_run"),
        "timestamp": str(event.get("start_time") or event.get("timestamp") or _iso_now()),
        "status": status,
        "tool_calls": len(event.get("child_runs") or []),
        "failures": 1 if status == "failed" else 0,
        "retries": int(event.get("retry_count", 0) or 0),
        "confidence": float(event.get("confidence", 0.0) or 0.0),
        "drift_score": float(event.get("drift_score", 0.0) or 0.0),
        "latency_ms": int(event.get("latency_ms") or event.get("duration_ms") or 0),
        "notes": str(event.get("error") or event.get("tags") or "")[:500],
    }
    return normalize_telemetry_record(record)


def langchain_events_to_records(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert multiple LangChain events into dashboard telemetry records."""
    return [langchain_event_to_record(event) for event in events]
