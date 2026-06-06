# Agent Telemetry Dashboard

A polished, lightweight Streamlit dashboard for inspecting telemetry from memory-enabled and tool-using AI agents.

It helps answer the questions agent builders ask after a run: **What tools were called? Did memory help or drift? Where did failures and retries happen? How confident was the agent over time?**

## Screenshots

![Dashboard screenshot placeholder](docs/screenshot-placeholder.svg)

The repository currently includes a screenshot placeholder so the README layout is ready for a real capture. After launching the app, replace `docs/screenshot-placeholder.svg` with a dashboard screenshot or add additional images such as:

- `docs/screenshots/overview.png`
- `docs/screenshots/reliability.png`
- `docs/screenshots/timeline.png`

## Problem statement

Modern AI agents do not just generate text. They read and write memory, call tools, retry failed actions, branch across tasks, and accumulate drift over time. Without telemetry, debugging those systems becomes guesswork.

This repository provides a simple local dashboard and deterministic metrics layer for exploring agent run data without external services or LLM API calls.

## Why agent telemetry matters

Agent telemetry makes behavior observable:

- **Memory operations** reveal whether an agent is relying on context or over-writing state.
- **Tool call traces** show operational complexity and possible cost drivers.
- **Failure and retry metrics** expose brittle workflows.
- **Confidence distributions** help spot low-certainty tasks before they reach users.
- **Drift scores** make long-running agent behavior easier to monitor.
- **Timelines** turn scattered events into a run-level story.

## Dashboard overview

The dashboard is organized into four tabs:

1. **Overview** — run status, tool calls, memory activity, and drift trends.
2. **Reliability** — failure rate, retry totals, failed-run counts, confidence, and latency.
3. **Runs** — compact run listing for session exploration.
4. **Analytics** — aggregate metrics, scoring, trend analysis, anomalies, tool reliability, and retry effectiveness.
5. **Run timeline** — task-level run timeline using start timestamp and latency.
6. **Raw data** — filtered telemetry table for inspection and export workflows.

The sidebar lets you load a local telemetry file and filter by agent, status, task, date range, and minimum confidence.

See [`docs/session_exploration.md`](docs/session_exploration.md) for the run-level exploration workflow added in Phase 2.

See [`docs/telemetry_analytics.md`](docs/telemetry_analytics.md) for the analytics engine, scoring formulas, exports, and dashboard page added in Phase 3.

## Features

- Streamlit dashboard using local sample data
- Pydantic models for strict typed telemetry validation
- JSON and CSV telemetry loading utilities
- Schema versioning support for raw JSON, versioned JSON envelopes, and CSV files
- Deterministic sample telemetry generator utility
- Deterministic Pandas metrics, aggregate analytics engine, agent performance scoring, success-rate calculations, and failure-rate calculations, and latency, confidence, drift, memory usage trend analysis, and anomaly detection rules, and tool reliability metrics, and retry effectiveness metrics, and run quality scoring
- Plotly charts for:
  - Summary metric cards for run count, failures, confidence, drift, latency, and memory operations
  - Run status breakdown
  - Tool calls per run
  - Memory reads/writes over time and by agent
  - Failure rate
  - Latency distribution
  - Status-aware confidence distribution and per-agent confidence evolution
  - Drift score over time and per-agent drift evolution
  - Retry count, failures, failed runs per task, and selected-run failure/retry inspection
- Searchable run listing with dedicated status filtering, run metadata, run detail, run comparison, event, memory, tool-call, and run timeline views
- Sidebar filters for agent name, run status, task name, date range, and minimum confidence
- Tabbed dashboard layout for overview, reliability, runs, analytics, timeline, and raw data views
- Pytest coverage for loading, validation, filtering, generation, and metrics
- Parent-child hierarchy and relationship graph helpers for multi-agent run relationships
- Analytics export downloads for JSON summaries and run quality CSV
- GitHub Actions CI

## Feature descriptions

### Strict telemetry validation

Telemetry records are validated with Pydantic before being converted into dataframes. The loader rejects unknown fields, invalid score ranges, negative counts, unsupported schema versions, and contradictory summaries such as successful runs with failures.

### Local loading

The app loads local JSON and CSV files. It also supports versioned JSON envelopes:

```json
{
  "schema_version": "1.0",
  "records": []
}
```

### Deterministic metrics

Metrics are computed with Pandas and do not depend on external services. This keeps tests stable and makes the project easy to run in CI.

### Sample telemetry generation

The `generate-agent-telemetry` command creates deterministic sample telemetry for demos, screenshots, and local experimentation.

### Session exploration

The Runs tab supports search, status filtering, selected-run details, metadata, failure/retry inspection, memory and tool timelines, confidence/drift evolution, and run-to-run comparison.

## Quickstart

```bash
git clone https://github.com/aditya89bh/agent-telemetry-dashboard.git
cd agent-telemetry-dashboard
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
streamlit run app/streamlit_app.py
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Regenerate local sample telemetry:

```bash
generate-agent-telemetry --count 42
```

For Streamlit Community Cloud or simple deployments:

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Usage examples

Load the bundled JSON dataset:

```bash
streamlit run app/streamlit_app.py
```

Load the bundled CSV dataset by changing the sidebar telemetry file path to:

```text
data/sample_telemetry.csv
```

Generate a larger deterministic demo dataset:

```bash
generate-agent-telemetry --count 100 --json data/sample_telemetry.json --csv data/sample_telemetry.csv
```

Install the package locally for development:

```bash
pip install -e .[dev]
```

## Telemetry schema

Sample records live in [`data/sample_telemetry.json`](data/sample_telemetry.json) and [`data/sample_telemetry.csv`](data/sample_telemetry.csv).

Each record includes:

- `schema_version`
- `run_id`
- `agent_name`
- `task_name`
- `timestamp`
- `status`
- `memory_reads`
- `memory_writes`
- `tool_calls`
- `failures`
- `retries`
- `confidence`
- `drift_score`
- `latency_ms`
- `notes`

See [`docs/telemetry_schema.md`](docs/telemetry_schema.md) for details.

The loader defaults records to schema version `1.0` and also supports JSON envelopes like `{ "schema_version": "1.0", "records": [...] }`. It rejects unknown fields, invalid score ranges, negative counts, and contradictory run summaries before data reaches the dashboard.

## Example use cases

- Portfolio project demonstrating practical AI observability skills
- Local dashboard for inspecting prototype agent runs
- Evaluation aid for memory-agent experiments
- Starter schema for tool-use telemetry
- Teaching example for Streamlit + Pandas + Plotly dashboards
- Lightweight QA surface for comparing agent run behavior across experiments

## Roadmap

- Add exportable run reports
- Add session-level grouping across multiple runs
- Add anomaly markers for sudden drift or retry spikes
- Add optional SQLite ingestion
- Add screenshot assets and demo video
- Add richer timeline traces for individual tool calls

## No external services

This project intentionally uses local data only. It does not call LLM APIs, telemetry vendors, or hosted databases.

## License

MIT
