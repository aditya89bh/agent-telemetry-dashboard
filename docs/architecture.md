# Architecture

Agent Telemetry Dashboard is intentionally small and easy to inspect.

```text
app/streamlit_app.py          Streamlit UI and Plotly charts
src/.../models.py             Pydantic telemetry model
src/.../loader.py             JSON/CSV loading and validation
src/.../metrics.py            Deterministic Pandas metric helpers
data/                         Local sample telemetry
tests/                        Loader and metrics tests
```

## Data flow

1. A local JSON or CSV file is selected in the Streamlit sidebar.
2. `load_telemetry` reads the file and validates every record with `TelemetryRecord`.
3. Validated records are converted to a consistently typed Pandas dataframe.
4. Sidebar filters narrow the dataset by agent, status, and date range.
5. Metric helpers produce chart-ready dataframes.
6. Streamlit renders KPIs, charts, a timeline, and raw data.

## Design principles

- Keep the schema readable.
- Prefer deterministic local metrics.
- Avoid external services and API calls.
- Make the code understandable as a portfolio project.
- Keep extensions obvious: ingestion, storage, richer traces, and reports.
