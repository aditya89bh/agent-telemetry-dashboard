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

The existing sidebar file path loader remains available for backward-compatible local telemetry loading.
