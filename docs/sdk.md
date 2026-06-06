# Telemetry SDK

Phase 7 introduces a lightweight SDK for writing traces into the persistent trace store.

## Core Package

`TelemetrySDKConfig` configures dataset ID and service name. `TelemetryClient` writes traces through `TraceRepository` and starts with a generic `emit(trace_type, run_id, payload)` method.

The SDK is intentionally small and local-first. It does not require a server, API key, or network service.

## Telemetry Event Emitter

`TelemetryClient.emit_event(run_id, event_name, attributes)` emits named generic telemetry events with optional structured attributes. Events are stored with trace type `event`.

## Memory Trace Emitter

`TelemetryClient.emit_memory_trace(trace)` accepts memory retrieval, write, influence, and decision trace models and persists them as normalized trace records. The emitter preserves the original trace ID and timestamp.

## Tool Call Emitter

`TelemetryClient.emit_tool_call(run_id, tool_name, status, latency_ms, metadata)` records tool usage with status, latency, and optional metadata. Tool traces use trace type `tool_call`.

## Run Lifecycle Emitter

`TelemetryClient.emit_run_start(...)` and `TelemetryClient.emit_run_end(...)` record run lifecycle events with trace type `run_lifecycle`. Start events include agent/task names; end events include status and latency.

## SDK Example

`examples/sdk_trace_store_example.py` demonstrates creating a SQLite trace store, wrapping it in `TraceRepository`, creating a `TelemetryClient`, and emitting run lifecycle, generic event, and tool call traces.
