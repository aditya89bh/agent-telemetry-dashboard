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

The existing sidebar file path loader remains available for backward-compatible local telemetry loading.
