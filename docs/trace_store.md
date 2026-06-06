# Persistent Trace Store

Phase 7 adds a persistent telemetry platform foundation.

## Trace Store Abstraction

`TraceStore` defines the backend contract for durable trace storage:

- `initialize()` prepares backend resources.
- `append_trace(trace)` persists one normalized trace.
- `query_traces(query)` returns traces matching a portable query.

`StoredTrace` is the normalized stored record shape, and `TraceQuery` provides backend-agnostic query parameters. This abstraction keeps persistence optional and backward-compatible with existing dashboard loading flows.
