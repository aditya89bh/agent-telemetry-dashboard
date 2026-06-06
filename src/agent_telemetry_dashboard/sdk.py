"""Lightweight telemetry SDK for emitting persistent traces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from urllib import request
from uuid import uuid4

from agent_telemetry_dashboard.models import (
    MemoryDecisionTrace,
    MemoryInfluenceTrace,
    MemoryRetrievalTrace,
    MemoryWriteTrace,
)
from agent_telemetry_dashboard.trace_store import StoredTrace, TraceRepository


class TelemetryTransport(Protocol):
    """Transport protocol used by SDK clients."""

    def send(self, trace: StoredTrace) -> None:
        """Send one stored trace."""


class RepositoryTransport:
    """Telemetry transport that writes directly to a repository."""

    def __init__(self, repository: TraceRepository) -> None:
        self.repository = repository

    def send(self, trace: StoredTrace) -> None:
        """Persist one trace through the repository."""
        self.repository.save(trace)


@dataclass(frozen=True)
class HTTPTransport:
    """HTTP transport for sending traces to a collector endpoint."""

    base_url: str
    timeout_seconds: float = 5.0

    def send(self, trace: StoredTrace) -> None:
        """POST one trace to the collector API."""
        url = f"{self.base_url.rstrip('/')}/v1/traces"
        payload = json.dumps(trace_payload(trace)).encode("utf-8")
        http_request = request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
            if response.status >= 400:
                raise RuntimeError(f"collector returned HTTP {response.status}")


def trace_payload(trace: StoredTrace) -> dict[str, object]:
    """Convert a stored trace to collector JSON."""
    return {
        "trace_id": trace.trace_id,
        "dataset_id": trace.dataset_id,
        "trace_type": trace.trace_type,
        "run_id": trace.run_id,
        "timestamp": trace.timestamp,
        "payload": trace.payload,
    }


@dataclass(frozen=True)
class TelemetrySDKConfig:
    """Configuration for telemetry SDK clients."""

    dataset_id: str = "default"
    service_name: str = "agent-app"


class TelemetryClient:
    """Small SDK client for writing telemetry traces through a repository."""

    def __init__(
        self,
        repository: TraceRepository,
        config: TelemetrySDKConfig | None = None,
        transport: TelemetryTransport | None = None,
    ) -> None:
        self.repository = repository
        self.config = config or TelemetrySDKConfig()
        self.transport = transport or RepositoryTransport(repository)

    def _trace(
        self,
        trace_type: str,
        run_id: str,
        payload: dict[str, object],
        trace_id: str | None = None,
        timestamp: str | None = None,
    ) -> StoredTrace:
        return StoredTrace(
            trace_id=trace_id or str(uuid4()),
            dataset_id=self.config.dataset_id,
            trace_type=trace_type,
            run_id=run_id,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            payload={"service_name": self.config.service_name, **payload},
        )

    def emit(self, trace_type: str, run_id: str, payload: dict[str, object]) -> StoredTrace:
        """Emit a generic telemetry trace."""
        trace = self._trace(trace_type=trace_type, run_id=run_id, payload=payload)
        self.transport.send(trace)
        return trace

    def emit_event(
        self,
        run_id: str,
        event_name: str,
        attributes: dict[str, object] | None = None,
    ) -> StoredTrace:
        """Emit a generic named telemetry event."""
        return self.emit(
            trace_type="event",
            run_id=run_id,
            payload={"event_name": event_name, "attributes": attributes or {}},
        )

    def emit_memory_trace(
        self,
        trace: MemoryRetrievalTrace | MemoryWriteTrace | MemoryInfluenceTrace | MemoryDecisionTrace,
    ) -> StoredTrace:
        """Emit a memory-aware trace model through the SDK."""
        trace_type = (
            trace.__class__.__name__.replace("Memory", "memory_").replace("Trace", "").lower()
        )
        stored = self._trace(
            trace_type=trace_type,
            run_id=trace.run_id,
            payload=trace.model_dump(mode="json"),
            trace_id=trace.trace_id,
            timestamp=trace.timestamp.isoformat(),
        )
        self.transport.send(stored)
        return stored

    def emit_tool_call(
        self,
        run_id: str,
        tool_name: str,
        status: str = "success",
        latency_ms: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> StoredTrace:
        """Emit a tool-call telemetry trace."""
        return self.emit(
            trace_type="tool_call",
            run_id=run_id,
            payload={
                "tool_name": tool_name,
                "status": status,
                "latency_ms": latency_ms,
                "metadata": metadata or {},
            },
        )

    def emit_run_start(
        self,
        run_id: str,
        agent_name: str,
        task_name: str,
        metadata: dict[str, object] | None = None,
    ) -> StoredTrace:
        """Emit a run start lifecycle trace."""
        return self.emit(
            trace_type="run_lifecycle",
            run_id=run_id,
            payload={
                "lifecycle_event": "start",
                "agent_name": agent_name,
                "task_name": task_name,
                "metadata": metadata or {},
            },
        )

    def emit_run_end(
        self,
        run_id: str,
        status: str,
        latency_ms: int = 0,
        metadata: dict[str, object] | None = None,
    ) -> StoredTrace:
        """Emit a run end lifecycle trace."""
        return self.emit(
            trace_type="run_lifecycle",
            run_id=run_id,
            payload={
                "lifecycle_event": "end",
                "status": status,
                "latency_ms": latency_ms,
                "metadata": metadata or {},
            },
        )
