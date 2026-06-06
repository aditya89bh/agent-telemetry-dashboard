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

    def send_batch(self, traces: list[StoredTrace]) -> None:
        """Send multiple stored traces."""


class RepositoryTransport:
    """Telemetry transport that writes directly to a repository."""

    def __init__(self, repository: TraceRepository) -> None:
        self.repository = repository

    def send(self, trace: StoredTrace) -> None:
        """Persist one trace through the repository."""
        self.repository.save(trace)

    def send_batch(self, traces: list[StoredTrace]) -> None:
        """Persist multiple traces through the repository."""
        for trace in traces:
            self.send(trace)


@dataclass(frozen=True)
class HTTPTransport:
    """HTTP transport for sending traces to a collector endpoint."""

    base_url: str
    timeout_seconds: float = 5.0

    def send(self, trace: StoredTrace) -> None:
        """POST one trace to the collector API."""
        self._post("/v1/traces", trace_payload(trace))

    def send_batch(self, traces: list[StoredTrace]) -> None:
        """POST multiple traces to the collector API."""
        self._post("/v1/traces/batch", {"traces": [trace_payload(trace) for trace in traces]})

    def _post(self, path: str, body: dict[str, object]) -> None:
        """POST a JSON body to the collector API."""
        url = f"{self.base_url.rstrip('/')}{path}"
        payload = json.dumps(body).encode("utf-8")
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
    batch_size: int = 1


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
        self._buffer: list[StoredTrace] = []

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
        self._send_or_buffer(trace)
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
        self._send_or_buffer(stored)
        return stored

    def _send_or_buffer(self, trace: StoredTrace) -> None:
        """Send immediately or buffer until the configured batch size is reached."""
        if self.config.batch_size <= 1:
            self.transport.send(trace)
            return
        self._buffer.append(trace)
        if len(self._buffer) >= self.config.batch_size:
            self.flush()

    def flush(self) -> None:
        """Flush buffered traces through the configured transport."""
        if not self._buffer:
            return
        traces = list(self._buffer)
        self._buffer.clear()
        self.transport.send_batch(traces)

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
