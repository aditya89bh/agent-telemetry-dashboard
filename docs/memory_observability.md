# Memory-Aware Observability

Phase 6 adds memory-aware observability primitives for tracking how retrieved, written, and evolving memories affect agent behavior.

## Memory Retrieval Trace Schema

`MemoryRetrievalTrace` captures a retrieved memory item during an agent run:

- `trace_id`
- `run_id`
- `memory_id`
- `timestamp`
- `query`
- `source` (`episodic`, `semantic`, `procedural`, `working`, `external`, or `other`)
- `relevance_score`
- `rank`
- `content_summary`

The schema uses strict Pydantic validation and is backward-compatible with existing telemetry models.

## Memory Write Trace Schema

`MemoryWriteTrace` captures memory mutations during a run:

- `trace_id`
- `run_id`
- `memory_id`
- `timestamp`
- `operation` (`create`, `update`, `delete`, `merge`, or `expire`)
- `source`
- `importance_score`
- `previous_summary`
- `new_summary`

This lets the dashboard distinguish passive retrieval from active memory lifecycle changes.

## Memory Influence Tracking

`MemoryInfluenceTrace` records how a retrieved or written memory affected downstream behavior. It captures the influenced target, evidence, influence kind (`decision`, `tool_selection`, `response`, `plan`, `safety`, or `other`), and an `influence_strength` score. `memory_influence_dataframe` converts these traces into sorted dataframes for dashboard views.

## Memory Influence Scoring

`memory_influence_scores` aggregates influence traces by memory item and reports event count, average influence strength, and maximum influence strength. This helps identify which memories most strongly shape agent behavior across runs.

## Memory Effectiveness Metrics

`memory_effectiveness_metrics` combines retrieval, write, and influence traces into high-level effectiveness indicators: retrieval count, write count, influence count, average relevance, average influence strength, and useful retrieval rate. The useful retrieval rate measures how many retrieved memory IDs later appear in influence traces.

## Memory Conflict Detection

`detect_memory_conflicts` scans memory write traces for memory IDs that receive multiple distinct summaries. It reports write count, distinct summary count, and a conflict score so teams can identify unstable or contradictory memory state.

## Memory Drift Metrics

`memory_drift_metrics` estimates how much each memory changes over its write history. It reports version count, distinct summary count, average importance, and a normalized drift score so long-lived memories with unstable content are easy to spot.

## Memory Lifecycle Visualization

`memory_lifecycle_events` turns write traces into a timeline-ready dataframe with memory ID, timestamp, operation, source, importance score, and summary. Dashboard views can use this to visualize create, update, merge, delete, and expiration events across memory lifecycles.

## Memory Replay View

`memory_replay_events` combines retrieval, write, and influence traces into one chronological replay. It can be filtered by `run_id`, making it possible to reconstruct when a memory was retrieved, changed, and used during a specific agent run.

## Memory-to-Decision Tracing

`MemoryDecisionTrace` links memory IDs to explicit agent decisions with a decision ID, summary, rationale, and confidence delta. `memory_decision_trace_dataframe` flattens these traces into one row per memory-decision link for filtering and audit views.

## Memory Audit Timeline

`memory_audit_timeline` combines retrieval, write, influence, and decision traces into a single chronological audit table. This gives developers a unified sequence for reviewing how memory state affected an agent run or dataset.

## Memory Health Score

`memory_health_score` combines useful retrieval rate, average relevance, average influence strength, conflict count, and drift into a normalized health score. It provides a quick signal for whether an agent's memory subsystem appears useful, stable, and low-risk.

## Memory Observability Dashboard

The Streamlit app includes a **Memory** tab that surfaces memory health, useful retrieval rate, average relevance, conflict count, memory operations by agent, and memory operations over time. Existing telemetry remains compatible; when explicit memory traces are not provided, the dashboard derives lightweight memory observability signals from existing `memory_reads`, `memory_writes`, confidence, status, agent, and task fields.
