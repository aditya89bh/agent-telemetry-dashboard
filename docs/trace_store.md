# Persistent Trace Store

Phase 7 adds a persistent telemetry platform foundation.

## Trace Store Abstraction

`TraceStore` defines the backend contract for durable trace storage:

- `initialize()` prepares backend resources.
- `append_trace(trace)` persists one normalized trace.
- `query_traces(query)` returns traces matching a portable query.

`StoredTrace` is the normalized stored record shape, and `TraceQuery` provides backend-agnostic query parameters. This abstraction keeps persistence optional and backward-compatible with existing dashboard loading flows.

## SQLite Backend

`SQLiteTraceStore` implements the trace store contract with a local SQLite database. It creates a `traces` table, stores trace payloads as JSON, indexes dataset IDs, and supports portable queries by dataset, trace type, run ID, and limit.

## Trace Repository Layer

`TraceRepository` provides a higher-level API over any `TraceStore` backend. It initializes the backend, saves traces, lists traces by dataset, and lists traces for a specific run. Dashboard and SDK code should prefer this repository layer over directly calling backend methods.

## Dataset Registry

`DatasetRegistry` stores dataset metadata in a small JSON file. `DatasetEntry` tracks dataset ID, display name, description, and creation timestamp. This registry lets the dashboard distinguish multiple persisted trace collections without changing existing local-file workflows.

## Dataset Selection

When `data/datasets.json` contains registered datasets, the dashboard sidebar shows a **Saved dataset** selector with dataset names and IDs. This introduces dataset awareness for trace-store workflows while preserving the existing local telemetry file input.

## Trace Querying Interface

`TraceQuery` can filter by dataset ID, trace type, run ID, and limit. `query_traces_dataframe` and `traces_to_dataframe` expose query results as Pandas dataframes so future dashboard views can inspect stored traces without backend-specific SQL.

## Trace Filtering Utilities

`filter_stored_traces` filters in-memory stored trace lists by dataset ID, trace type, and run ID. This is useful for UI workflows, tests, SDK-side previews, and post-query filtering without requiring a backend round trip.

## Memory Trace Persistence

`memory_trace_to_stored_trace` converts memory retrieval, write, influence, and decision trace models into normalized `StoredTrace` records. The conversion preserves trace ID, run ID, timestamp, dataset ID, trace type, and the JSON-safe model payload.

## Import-to-Store Pipeline

`telemetry_dataframe_to_traces` converts validated dashboard telemetry rows into `run_summary` traces, and `import_dataframe_to_store` persists those traces through `TraceRepository`. This bridges the Phase 5 ingestion pipeline with persistent Phase 7 storage.

## Saved Dataset Management

`DatasetRegistry` supports registering, listing, retrieving, and removing saved dataset metadata. Dataset removal only updates registry metadata; trace backend deletion can be added later without changing the registry API.

## Minimal Usage

```python
from agent_telemetry_dashboard.trace_store import (
    SQLiteTraceStore,
    StoredTrace,
    TraceRepository,
)

repository = TraceRepository(SQLiteTraceStore("data/traces.sqlite"))
repository.save(
    StoredTrace(
        trace_id="trace-1",
        dataset_id="demo",
        trace_type="event",
        run_id="run-1",
        timestamp="2026-01-01T00:00:00",
        payload={"event_name": "started"},
    )
)
traces = repository.list_traces("demo")
```

## Persistence Architecture

The store is intentionally local-first:

1. Ingestion validates telemetry and converts rows to dataframes.
2. `import_dataframe_to_store` converts rows into `run_summary` traces.
3. `TraceRepository` writes traces into a backend.
4. `SQLiteTraceStore` persists normalized traces locally.
5. Query helpers return `StoredTrace` lists or dataframes for UI workflows.

This keeps existing JSON/CSV dashboard loading operational while enabling durable trace workflows.
