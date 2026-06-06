# Telemetry Schema

The dashboard expects one row per agent run or task-level run summary.

| Field | Type | Description |
| --- | --- | --- |
| `run_id` | string | Stable identifier for the run. |
| `agent_name` | string | Name of the agent that performed the task. |
| `task_name` | string | Human-readable task or workflow name. |
| `timestamp` | datetime | ISO-8601 timestamp for the run start. |
| `status` | enum | `success`, `warning`, or `failed`. |
| `memory_reads` | integer | Count of memory lookup/read events. |
| `memory_writes` | integer | Count of memory write/update events. |
| `tool_calls` | integer | Count of tool invocations. |
| `failures` | integer | Count of failures observed during the run. |
| `retries` | integer | Count of retry attempts. |
| `confidence` | float | Confidence score from 0.0 to 1.0. |
| `drift_score` | float | Drift score from 0.0 to 1.0. Higher means more drift. |
| `latency_ms` | integer | Run duration or observed latency in milliseconds. |
| `notes` | string | Optional human-readable context. |

Validation is implemented in `src/agent_telemetry_dashboard/models.py` with Pydantic.

## Validation rules

- Unknown fields are rejected so telemetry producers cannot silently drift from the schema.
- Identifiers and names must be non-empty after trimming whitespace.
- Count fields must be non-negative.
- `confidence` and `drift_score` must be between `0.0` and `1.0`.
- Successful runs cannot report failures.
- Failed runs must report at least one failure.
- Retries require at least one failure.

## Supported formats

- JSON: a list of telemetry objects
- CSV: one telemetry record per row

Both formats are included under `data/`.
