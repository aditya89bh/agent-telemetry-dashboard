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

The existing sidebar file path loader remains available for backward-compatible local telemetry loading.
