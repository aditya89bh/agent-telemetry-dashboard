"""Lightweight telemetry SDK for emitting persistent traces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from agent_telemetry_dashboard.models import (
    MemoryDecisionTrace,
    MemoryInfluenceTrace,
    MemoryRetrievalTrace,
    MemoryWriteTrace,
)
from agent_telemetry_dashboard.trace_store import StoredTrace, TraceRepository


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
    ) -> None:
        self.repository = repository
        self.config = config or TelemetrySDKConfig()

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
        return self.repository.save(trace)

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
        return self.repository.save(stored)

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
