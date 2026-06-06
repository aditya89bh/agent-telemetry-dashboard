"""Lightweight telemetry SDK for emitting persistent traces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

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
