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


def crewai_task_to_record(task: dict[str, Any]) -> dict[str, Any]:
    """Convert a CrewAI task/agent execution payload into dashboard telemetry."""
    status = str(task.get("status") or "success").lower()
    if status in {"complete", "completed", "done"}:
        status = "success"
    if status in {"error", "failed"}:
        status = "failed"

    agent = task.get("agent") or {}
    agent_name = agent.get("role") or agent.get("name") or task.get("agent_name") or "crewai"
    record = {
        "run_id": str(task.get("id") or task.get("task_id") or "crewai-task"),
        "agent_name": str(agent_name),
        "task_name": str(task.get("description") or task.get("name") or "crewai_task")[:120],
        "timestamp": str(task.get("started_at") or task.get("timestamp") or _iso_now()),
        "status": status,
        "tool_calls": len(task.get("tools") or task.get("tool_calls") or []),
        "failures": 1 if status == "failed" else int(task.get("failures", 0) or 0),
        "retries": int(task.get("retries", 0) or 0),
        "confidence": float(task.get("confidence", 0.0) or 0.0),
        "drift_score": float(task.get("drift_score", 0.0) or 0.0),
        "latency_ms": int(task.get("latency_ms") or task.get("duration_ms") or 0),
        "notes": str(task.get("output") or task.get("error") or "")[:500],
    }
    return normalize_telemetry_record(record)


def crewai_tasks_to_records(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert multiple CrewAI task payloads into dashboard telemetry records."""
    return [crewai_task_to_record(task) for task in tasks]


def openai_agents_trace_to_record(trace: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAI Agents SDK trace/span payload into dashboard telemetry."""
    status = str(trace.get("status") or "success").lower()
    if status in {"errored", "error", "failed"}:
        status = "failed"
    elif status in {"in_progress", "cancelled"}:
        status = "warning"

    usage = trace.get("usage") or {}
    tools = trace.get("tool_calls") or trace.get("tools") or []
    run_id = trace.get("trace_id") or trace.get("run_id") or trace.get("id") or "openai-run"
    task_name = trace.get("input") or trace.get("task") or trace.get("type") or "agent_run"
    record = {
        "run_id": str(run_id),
        "agent_name": str(trace.get("agent_name") or trace.get("name") or "openai_agent"),
        "task_name": str(task_name)[:120],
        "timestamp": str(trace.get("created_at") or trace.get("started_at") or _iso_now()),
        "status": status,
        "memory_reads": int(trace.get("memory_reads", 0) or 0),
        "memory_writes": int(trace.get("memory_writes", 0) or 0),
        "tool_calls": len(tools),
        "failures": 1 if status == "failed" else 0,
        "retries": int(trace.get("retries", 0) or 0),
        "confidence": float(trace.get("confidence", 0.0) or 0.0),
        "drift_score": float(trace.get("drift_score", 0.0) or 0.0),
        "latency_ms": int(trace.get("latency_ms") or trace.get("duration_ms") or 0),
        "notes": str(trace.get("error") or usage or "")[:500],
    }
    return normalize_telemetry_record(record)


def openai_agents_traces_to_records(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert multiple OpenAI Agents trace payloads into dashboard telemetry records."""
    return [openai_agents_trace_to_record(trace) for trace in traces]
