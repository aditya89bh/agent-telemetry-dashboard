# Telemetry Analytics

Phase 3 adds deterministic analytics for local agent telemetry. The analytics layer is implemented in `src/agent_telemetry_dashboard/analytics.py` and is designed to remain backward-compatible with the existing run-summary schema.

## Analytics included

- **Aggregate metrics** — total runs, agents, tasks, statuses, failures, retries, tool calls, memory operations, confidence, drift, and latency.
- **Agent performance scoring** — a 0-100 score combining success rate, confidence, inverse drift, and failure avoidance.
- **Success and failure rates** — grouped calculations by agent or another telemetry column.
- **Trend analysis** — latency, confidence, drift, and memory usage over time.
- **Anomaly detection** — deterministic threshold rules for low confidence, high drift, retry spikes, and failed runs.
- **Tool reliability** — run-level estimate of tool success rate from tool calls and failures.
- **Retry effectiveness** — estimates how often retried runs recover to success or warning states.
- **Run quality scoring** — per-run 0-100 score using confidence, drift, latency, status, retries, and failures.

## Dashboard page

The **Analytics** tab visualizes:

- agent performance scores
- success/failure rates
- latency trend
- memory usage trend
- confidence and drift trends
- tool reliability metrics
- retry effectiveness metrics
- top run quality scores
- anomaly table

## Export functionality

The analytics page includes two downloads:

- `agent_telemetry_analytics.json` — aggregate metrics, agent scores, run quality scores, and anomalies
- `run_quality_scores.csv` — CSV export of per-run quality scoring

## Design notes

The analytics are intentionally deterministic and local-only. There are no LLM API calls, hosted databases, or external telemetry services. This keeps the project suitable for demos, CI, and portfolio review.

## Backward compatibility

The analytics functions operate on the existing telemetry dataframe columns. Existing JSON/CSV sample data and dashboard pages continue to work without schema changes.
