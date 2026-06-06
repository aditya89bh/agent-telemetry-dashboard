# Data Ingestion & Framework Integrations

Phase 5 adds ingestion and adapter capabilities so external developers can bring telemetry from their own agent systems into the dashboard.

## Supported Import Formats

- **JSON**: raw record arrays or versioned envelopes with `schema_version` and `records`.
- **CSV**: rows using the dashboard telemetry columns.
- **ZIP**: bundles containing any mix of supported JSON and CSV files.
- **Bulk upload**: multiple files selected in the Upload tab and combined into one timestamp-sorted import.

## Upload Workflow

1. Run the dashboard with `streamlit run app/streamlit_app.py`.
2. Open the **Upload** tab.
3. Select one or more `.json`, `.csv`, or `.zip` files.
4. Review file metadata, import statistics, preview summary, and preview rows.
5. Use the full dataframe expander to inspect all imported records.

Successful imports are tracked in `data/import_history.jsonl`.

## Validation, Normalization, and Migration

The ingestion pipeline applies these steps before imported data reaches dashboard analysis:

1. Parse the uploaded file format.
2. Migrate supported legacy schema versions to `1.0`.
3. Normalize common external field names and status aliases.
4. Validate records with the existing `TelemetryRecord` model.
5. Convert records into the dashboard dataframe format.

Unsupported schema versions and invalid rows raise user-facing `IngestionError` messages.

## Framework Adapters

Adapters live in `agent_telemetry_dashboard.adapters`:

- `langchain_event_to_record` / `langchain_events_to_records`
- `crewai_task_to_record` / `crewai_tasks_to_records`
- `openai_agents_trace_to_record` / `openai_agents_traces_to_records`

Each adapter returns dictionaries compatible with the dashboard schema. Wrap adapter output in a versioned JSON envelope before upload:

```json
{
  "schema_version": "1.0",
  "records": []
}
```

## Runnable Examples

See:

- `examples/langchain_import_example.py`
- `examples/crewai_import_example.py`
- `examples/openai_agents_import_example.py`

Each script prints a dashboard-compatible JSON envelope that can be redirected to a file and uploaded.

```bash
python examples/langchain_import_example.py > langchain_telemetry.json
```

## Backward Compatibility

The existing sidebar-based local JSON/CSV loader remains available. Existing overview, reliability, runs, analytics, agents, timeline, and raw-data views continue to operate on the loaded telemetry dataframe.
