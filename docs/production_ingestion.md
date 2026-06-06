# Production Ingestion Layer

Phase 8 adds a deployable ingestion layer for persistent telemetry traces while preserving the local dashboard and direct repository SDK path.

## Collector API

The collector is available as a lightweight stdlib HTTP server:

```bash
python -m agent_telemetry_dashboard.collector_server
```

Environment variables:

- `AGENT_TELEMETRY_HOST` — bind host, default `0.0.0.0`
- `AGENT_TELEMETRY_PORT` — bind port, default `8080`
- `AGENT_TELEMETRY_STORE_PATH` — SQLite trace store path, default `data/trace_store.sqlite`
- `AGENT_TELEMETRY_DEFAULT_DATASET` — dataset used when requests omit `dataset_id`

## Endpoints

### Health

`GET /health`

Returns collector status and the default dataset id.

### Generic trace ingestion

`POST /v1/traces`

```json
{
  "trace_id": "trace-1",
  "dataset_id": "production",
  "trace_type": "event",
  "run_id": "run-1",
  "timestamp": "2026-01-01T00:00:00+00:00",
  "payload": {"event_name": "started"}
}
```

### Batched ingestion

`POST /v1/traces/batch`

```json
{
  "traces": [
    {
      "trace_id": "trace-1",
      "run_id": "run-1",
      "timestamp": "2026-01-01T00:00:00+00:00",
      "payload": {"event_name": "started"}
    }
  ]
}
```

### Memory traces

`POST /v1/memory-traces`

Accepts the same trace envelope as `/v1/traces` and defaults `trace_type` to `memory_trace`.

### Tool calls

`POST /v1/tool-calls`

Required fields: `trace_id`, `run_id`, `timestamp`, `tool_name`.

### Run lifecycle

`POST /v1/run-lifecycle`

Required fields: `trace_id`, `run_id`, `timestamp`, `lifecycle_event`.

### Trace search

`POST /v1/traces/search`

Supported criteria:

- `dataset_id`
- `trace_type`
- `run_id`
- `text` payload substring search
- `start_timestamp`
- `end_timestamp`
- `limit`

## SDK HTTP Transport

```python
from agent_telemetry_dashboard.sdk import HTTPTransport, TelemetryClient, TelemetrySDKConfig
from agent_telemetry_dashboard.trace_store import SQLiteTraceStore, TraceRepository

repository = TraceRepository(SQLiteTraceStore("local-fallback.sqlite"))
transport = HTTPTransport(
    "http://collector.example.com:8080",
    retry_attempts=3,
    retry_backoff_seconds=0.25,
)
client = TelemetryClient(
    repository=repository,
    config=TelemetrySDKConfig(dataset_id="production", batch_size=10),
    transport=transport,
)

client.emit_event("run-1", "started")
client.flush()
```

The SDK still supports the previous direct repository transport by default, so local-first usage remains backward compatible.

## Async Support

`TelemetryClient.async_emit(...)` and `TelemetryClient.async_flush(...)` adapt sync transports with `asyncio.to_thread`, allowing async applications to avoid blocking the event loop during collector sends.

## Schema Migrations

`TraceMigrationRunner` provides an initial SQLite migration framework with ordered migrations and `PRAGMA user_version` tracking. Future schema changes should add explicit migrations instead of changing tables silently.

## Deployment

Deployment assets:

- `deploy/collector.env.example` — environment template
- `deploy/collector.service` — example systemd unit
- `Dockerfile` — container image for the collector server

Docker example:

```bash
docker build -t agent-telemetry-collector .
docker run --rm -p 8080:8080 \
  -e AGENT_TELEMETRY_DEFAULT_DATASET=production \
  -v agent-telemetry-data:/var/lib/agent-telemetry \
  agent-telemetry-collector
```

## Current Limitations

- SQLite is still the only storage backend.
- Authentication, authorization, and tenant isolation are not implemented yet.
- The stdlib server is intentionally minimal; high-throughput deployments should front it with production process management and monitoring.
- Retry handling is client-side only; collector-side dead-letter queues are not implemented yet.
