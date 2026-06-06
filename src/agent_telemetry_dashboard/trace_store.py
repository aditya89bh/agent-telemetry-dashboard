"""Persistent trace store abstractions."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import pandas as pd

from agent_telemetry_dashboard.models import (
    MemoryDecisionTrace,
    MemoryInfluenceTrace,
    MemoryRetrievalTrace,
    MemoryWriteTrace,
)


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


class SQLiteTraceStore:
    """SQLite-backed trace store implementation."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    trace_type TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_dataset ON traces(dataset_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_run ON traces(run_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_type ON traces(trace_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp)"
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_traces_dataset_type_run
                ON traces(dataset_id, trace_type, run_id)
                """
            )

    def append_trace(self, trace: StoredTrace) -> None:
        self.initialize()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO traces
                (trace_id, dataset_id, trace_type, run_id, timestamp, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.trace_id,
                    trace.dataset_id,
                    trace.trace_type,
                    trace.run_id,
                    trace.timestamp,
                    json.dumps(trace.payload, sort_keys=True, default=str),
                ),
            )

    def query_traces(self, query: TraceQuery) -> list[StoredTrace]:
        self.initialize()
        clauses: list[str] = []
        values: list[object] = []
        if query.dataset_id is not None:
            clauses.append("dataset_id = ?")
            values.append(query.dataset_id)
        if query.trace_type is not None:
            clauses.append("trace_type = ?")
            values.append(query.trace_type)
        if query.run_id is not None:
            clauses.append("run_id = ?")
            values.append(query.run_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        values.append(query.limit)
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                f"""
                SELECT trace_id, dataset_id, trace_type, run_id, timestamp, payload_json
                FROM traces
                {where}
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                values,
            ).fetchall()
        return [
            StoredTrace(
                trace_id=row[0],
                dataset_id=row[1],
                trace_type=row[2],
                run_id=row[3],
                timestamp=row[4],
                payload=json.loads(row[5]),
            )
            for row in rows
        ]


class TraceRepository:
    """High-level repository API over a trace store backend."""

    def __init__(self, store: TraceStore) -> None:
        self.store = store
        self.store.initialize()

    def save(self, trace: StoredTrace) -> StoredTrace:
        """Persist and return a trace."""
        self.store.append_trace(trace)
        return trace

    def list_traces(self, dataset_id: str, limit: int = 100) -> list[StoredTrace]:
        """List traces for a dataset."""
        return self.store.query_traces(TraceQuery(dataset_id=dataset_id, limit=limit))

    def list_run_traces(
        self, dataset_id: str,
        run_id: str,
        limit: int = 100,
    ) -> list[StoredTrace]:
        """List traces for one run in a dataset."""
        return self.store.query_traces(
            TraceQuery(dataset_id=dataset_id, run_id=run_id, limit=limit)
        )


def traces_to_dataframe(traces: list[StoredTrace]) -> pd.DataFrame:
    """Convert stored traces into a dataframe for query views."""
    columns = ["trace_id", "dataset_id", "trace_type", "run_id", "timestamp", "payload"]
    df = pd.DataFrame(
        [
            {
                "trace_id": trace.trace_id,
                "dataset_id": trace.dataset_id,
                "trace_type": trace.trace_type,
                "run_id": trace.run_id,
                "timestamp": trace.timestamp,
                "payload": trace.payload,
            }
            for trace in traces
        ],
        columns=columns,
    )
    if df.empty:
        return pd.DataFrame(columns=columns)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
    return df.sort_values("timestamp").reset_index(drop=True)


def query_traces_dataframe(repository: TraceRepository, query: TraceQuery) -> pd.DataFrame:
    """Run a trace query and return dataframe output for dashboard use."""
    return traces_to_dataframe(repository.store.query_traces(query))


def filter_stored_traces(
    traces: list[StoredTrace],
    trace_type: str | None = None,
    run_id: str | None = None,
    dataset_id: str | None = None,
) -> list[StoredTrace]:
    """Filter stored traces in memory using common trace dimensions."""
    filtered = traces
    if trace_type is not None:
        filtered = [trace for trace in filtered if trace.trace_type == trace_type]
    if run_id is not None:
        filtered = [trace for trace in filtered if trace.run_id == run_id]
    if dataset_id is not None:
        filtered = [trace for trace in filtered if trace.dataset_id == dataset_id]
    return filtered


def memory_trace_to_stored_trace(
    trace: MemoryRetrievalTrace | MemoryWriteTrace | MemoryInfluenceTrace | MemoryDecisionTrace,
    dataset_id: str,
) -> StoredTrace:
    """Convert a memory-aware trace model into a persisted trace record."""
    trace_type = trace.__class__.__name__.replace("Memory", "memory_").replace("Trace", "").lower()
    return StoredTrace(
        trace_id=trace.trace_id,
        dataset_id=dataset_id,
        trace_type=trace_type,
        run_id=trace.run_id,
        timestamp=trace.timestamp.isoformat(),
        payload=trace.model_dump(mode="json"),
    )
