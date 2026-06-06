# Telemetry SDK

Phase 7 introduces a lightweight SDK for writing traces into the persistent trace store.

## Core Package

`TelemetrySDKConfig` configures dataset ID and service name. `TelemetryClient` writes traces through `TraceRepository` and starts with a generic `emit(trace_type, run_id, payload)` method.

The SDK is intentionally small and local-first. It does not require a server, API key, or network service.

## Telemetry Event Emitter

`TelemetryClient.emit_event(run_id, event_name, attributes)` emits named generic telemetry events with optional structured attributes. Events are stored with trace type `event`.
