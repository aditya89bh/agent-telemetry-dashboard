"""HTTP collector API primitives for production telemetry ingestion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any

from agent_telemetry_dashboard.trace_store import SQLiteTraceStore, StoredTrace, TraceRepository

JsonObject = dict[str, Any]
CollectorHandler = Callable[[JsonObject], JsonObject]


def require_fields(payload: JsonObject, fields: tuple[str, ...]) -> None:
    """Validate that required request fields are present and non-empty."""
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing required field(s): {names}")


@dataclass(frozen=True)
class CollectorConfig:
    """Runtime configuration for the telemetry collector."""

    store_path: Path = Path("data/trace_store.sqlite")
    default_dataset_id: str = "default"


@dataclass(frozen=True)
class CollectorResponse:
    """Serializable response returned by collector handlers."""

    status_code: int
    body: JsonObject


class CollectorAPI:
    """Small route registry for telemetry ingestion handlers."""

    def __init__(self, config: CollectorConfig | None = None) -> None:
        self.config = config or CollectorConfig()
        self.repository = TraceRepository(SQLiteTraceStore(self.config.store_path))
        self._routes: dict[tuple[str, str], CollectorHandler] = {}
        self.add_route("GET", "/health", self.health)
        self.add_route("POST", "/v1/traces", self.ingest_trace)
        self.add_route("POST", "/v1/memory-traces", self.ingest_memory_trace)
        self.add_route("POST", "/v1/tool-calls", self.ingest_tool_call)
        self.add_route("POST", "/v1/run-lifecycle", self.ingest_run_lifecycle)

    def add_route(self, method: str, path: str, handler: CollectorHandler) -> None:
        """Register a JSON handler for one HTTP method and path."""
        self._routes[(method.upper(), path)] = handler

    def dispatch(
        self,
        method: str,
        path: str,
        payload: JsonObject | None = None,
    ) -> CollectorResponse:
        """Dispatch a request to a registered handler."""
        handler = self._routes.get((method.upper(), path))
        if handler is None:
            return CollectorResponse(
                status_code=HTTPStatus.NOT_FOUND,
                body={"error": "not_found", "message": f"No route for {method.upper()} {path}"},
            )
        return CollectorResponse(status_code=HTTPStatus.OK, body=handler(payload or {}))

    def health(self, payload: JsonObject | None = None) -> JsonObject:
        """Return collector health metadata."""
        return {
            "status": "ok",
            "service": "agent-telemetry-collector",
            "dataset_id": self.config.default_dataset_id,
        }

    def ingest_trace(self, payload: JsonObject) -> JsonObject:
        """Persist one generic telemetry trace."""
        require_fields(payload, ("trace_id", "run_id", "timestamp"))
        trace = StoredTrace(
            trace_id=str(payload["trace_id"]),
            dataset_id=str(payload.get("dataset_id", self.config.default_dataset_id)),
            trace_type=str(payload.get("trace_type", "event")),
            run_id=str(payload["run_id"]),
            timestamp=str(payload["timestamp"]),
            payload=dict(payload.get("payload", {})),
        )
        self.repository.save(trace)
        return {"accepted": 1, "trace_ids": [trace.trace_id]}

    def ingest_memory_trace(self, payload: JsonObject) -> JsonObject:
        """Persist one memory trace from the collector API."""
        require_fields(payload, ("trace_id", "run_id", "timestamp"))
        memory_payload = dict(payload.get("payload", {}))
        trace_payload = {**payload, "trace_type": payload.get("trace_type", "memory_trace")}
        trace_payload["payload"] = memory_payload
        return self.ingest_trace(trace_payload)

    def ingest_tool_call(self, payload: JsonObject) -> JsonObject:
        """Persist one tool-call trace from the collector API."""
        require_fields(payload, ("trace_id", "run_id", "timestamp", "tool_name"))
        trace_payload = {**payload, "trace_type": "tool_call"}
        trace_payload["payload"] = {
            "tool_name": payload["tool_name"],
            "status": payload.get("status", "success"),
            "latency_ms": payload.get("latency_ms", 0),
            "metadata": payload.get("metadata", {}),
        }
        return self.ingest_trace(trace_payload)

    def ingest_run_lifecycle(self, payload: JsonObject) -> JsonObject:
        """Persist one run lifecycle trace from the collector API."""
        require_fields(payload, ("trace_id", "run_id", "timestamp", "lifecycle_event"))
        trace_payload = {**payload, "trace_type": "run_lifecycle"}
        trace_payload["payload"] = {
            "lifecycle_event": payload["lifecycle_event"],
            "agent_name": payload.get("agent_name", ""),
            "task_name": payload.get("task_name", ""),
            "status": payload.get("status", ""),
            "latency_ms": payload.get("latency_ms", 0),
            "metadata": payload.get("metadata", {}),
        }
        return self.ingest_trace(trace_payload)


def create_collector(config: CollectorConfig | None = None) -> CollectorAPI:
    """Create a configured collector API instance."""
    return CollectorAPI(config=config)
