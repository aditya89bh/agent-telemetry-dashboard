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
