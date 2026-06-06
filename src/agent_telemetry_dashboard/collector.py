"""HTTP collector API primitives for production telemetry ingestion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any

from agent_telemetry_dashboard.trace_store import SQLiteTraceStore, TraceRepository

JsonObject = dict[str, Any]
CollectorHandler = Callable[[JsonObject], JsonObject]


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


def create_collector(config: CollectorConfig | None = None) -> CollectorAPI:
    """Create a configured collector API instance."""
    return CollectorAPI(config=config)
