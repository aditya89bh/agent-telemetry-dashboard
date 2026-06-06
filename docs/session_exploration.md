# Session Exploration

Phase 2 adds run-level exploration for inspecting individual agent sessions from local telemetry.

## What the Runs tab provides

The **Runs** tab turns aggregate telemetry into an investigation workflow:

1. Search runs by run id, agent, task, status, or notes.
2. Filter the run listing by status.
3. Select a run for detail inspection.
4. Compare the selected run against another run.
5. Inspect metadata, memory activity, tool calls, confidence, drift, failures, and retries.

## Run listing

The run listing is a compact newest-first table with:

- `run_id`
- `agent_name`
- `task_name`
- `timestamp`
- `status`
- `confidence`
- `drift_score`
- `latency_ms`

## Detail panels

Selected runs expose:

- **Run metadata** — identity, agent, task, status, timestamp, latency, schema version.
- **Run detail** — telemetry summary values and notes.
- **Failure inspection** — failure count, severity, and notes.
- **Retry inspection** — retry count, retry/failure ratio, and recommended next action.

## Timelines

Because the current schema is run-summary telemetry, timelines are deterministic projections from validated run fields:

- **Event timeline** — run start, memory activity, tool activity, reliability events, completion.
- **Memory event timeline** — read and write activity within the run window.
- **Tool call timeline** — one event per tool call, evenly placed across the run duration.

These timelines are useful for portfolio-grade exploration while keeping the project local and dependency-light.

## Evolution charts

The selected run anchors trend charts for the same agent:

- Confidence evolution over time
- Drift evolution over time

These make it easier to spot whether a run is isolated or part of a broader agent behavior trend.

## Run comparison

The comparison view calculates metric deltas between two runs across:

- memory reads
- memory writes
- tool calls
- failures
- retries
- confidence
- drift score
- latency

Positive deltas mean the comparison run has a higher value than the selected baseline run.
