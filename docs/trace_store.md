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
