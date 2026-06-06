"""Persistent trace store abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class StoredTrace:
    """A normalized trace record stored by a persistent backend."""

    trace_id: str
    dataset_id: str
    trace_type: str
    run_id: str
    timestamp: str
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TraceQuery:
    """Portable query object for trace backends."""

    dataset_id: str | None = None
    trace_type: str | None = None
    run_id: str | None = None
    limit: int = 100


class TraceStore(Protocol):
    """Protocol implemented by persistent trace storage backends."""

    def initialize(self) -> None:
        """Prepare backend storage resources."""

    def append_trace(self, trace: StoredTrace) -> None:
        """Persist one normalized trace."""

    def query_traces(self, query: TraceQuery) -> list[StoredTrace]:
        """Return traces matching a portable query."""
