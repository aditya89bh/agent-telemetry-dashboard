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
