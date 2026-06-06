# Data Ingestion & Integrations

Phase 5 turns the dashboard into an ingestion-capable developer tool for external agent telemetry.

## Telemetry Upload Page

The Streamlit app includes an **Upload** tab for staging external telemetry files. The page accepts JSON, CSV, and ZIP file selections and displays basic file metadata before later ingestion steps validate, normalize, preview, and import the uploaded records.

## JSON Uploads

JSON uploads can be either a raw list of telemetry records or a versioned envelope:

```json
{
  "schema_version": "1.0",
  "records": []
}
```

Uploaded JSON records are validated with the existing `TelemetryRecord` model and converted into the same dataframe shape used by local file loading.

## CSV Uploads

CSV uploads use the same columns as `data/sample_telemetry.csv`. Rows are validated with the existing schema before they are displayed in the upload page, so imported CSV data remains compatible with the overview, session exploration, analytics, and multi-agent tabs.

## ZIP Uploads

ZIP uploads can bundle multiple `.json` and `.csv` telemetry files. The ingestion layer reads supported files from the archive, ignores unrelated files, validates every record, and combines the imported runs into one timestamp-sorted dataframe.

## Validation Pipeline

`validate_ingestion_records` checks raw records before dataframe conversion and returns a report with total records, valid records, and row-level errors. This gives import flows a stable validation contract without changing the existing local telemetry loader.

## Error Handling

Upload parsing and validation failures raise `IngestionError`, a user-facing exception that preserves the source filename and row-level validation errors. The upload page catches this exception and displays actionable error details instead of crashing the dashboard.

## Normalization

The ingestion layer normalizes common external field names before validation. For example, `agent` maps to `agent_name`, `task` maps to `task_name`, `duration_ms` maps to `latency_ms`, and status aliases such as `ok` or `error` map to dashboard statuses. Missing optional metrics default to zero-valued telemetry fields so lightweight exports can still be imported safely.

## Import History

Successful uploads are recorded in `data/import_history.jsonl` with source name, format, record count, status, timestamp, and an optional message. The upload page displays the latest import history entries so developers can audit recent ingestion activity.

## Ingestion Statistics

Imported datasets are summarized with record count, distinct agents, distinct tasks, success rate, failure rate, average latency, and average confidence. These metrics help developers quickly check whether an import looks reasonable before analyzing it in the existing dashboard views.

## Bulk Imports

The upload page supports selecting multiple telemetry files at once. `ingest_bulk_uploads` dispatches each JSON, CSV, or ZIP upload through the existing ingestion pipeline, combines the validated dataframes, sorts the imported records by timestamp, and reports one combined import result.

## Import Preview

Before developers inspect the full imported dataframe, the upload flow now shows an import preview summary with record count, date range, statuses, and a compact table of representative run fields. This keeps large imports reviewable without hiding access to the full dataset.

## Schema Migration

The ingestion pipeline supports explicit schema migration before normalization and validation. Current telemetry uses schema version `1.0`; legacy `0.9` records are migrated by mapping historical fields such as `agent_id` and `task` into the current schema. Unknown schema versions are rejected with `IngestionError` so developers do not accidentally analyze incompatible telemetry.

## LangChain Adapter

`langchain_event_to_record` converts LangChain-style run/event dictionaries into dashboard telemetry records. It maps run IDs, chain names, run types, timestamps, child runs as tool calls, latency, confidence, status, and errors into the normalized telemetry schema.

## CrewAI Adapter

`crewai_task_to_record` converts CrewAI-style task execution payloads into dashboard telemetry records. It maps task IDs, agent role/name, task descriptions, timestamps, tools, latency, retries, failures, and outputs into the same schema used by uploaded telemetry.

## OpenAI Agents Adapter

`openai_agents_trace_to_record` converts OpenAI Agents SDK-style traces or spans into dashboard telemetry records. It maps trace IDs, agent names, task inputs, timestamps, status, tool calls, memory activity, latency, confidence, drift, usage metadata, and errors into the dashboard schema.

## Integration Examples

The `examples/` directory includes runnable scripts for LangChain, CrewAI, and OpenAI Agents payloads. Each script converts framework-specific telemetry into a versioned JSON envelope that can be uploaded through the dashboard.

## Test Coverage

Ingestion and integration behavior is covered by unit tests for JSON, CSV, ZIP, validation, error handling, normalization, history, statistics, preview, schema migration, and adapter conversion. Integration tests also verify that adapter output can be ingested as dashboard-compatible JSON.

The existing sidebar file path loader remains available for backward-compatible local telemetry loading.
