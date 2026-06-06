# Multi-Agent Observability

Phase 4 adds backward-compatible observability helpers for multi-agent systems. Existing telemetry remains valid; multi-agent fields are optional extensions and derived views work with the current sample dataset.

## Models

### Agent registry

`AgentRegistryEntry` describes agents participating in observed workflows:

- `agent_name`
- `display_name`
- `role`
- `description`
- `owner`
- `enabled`

### Multi-agent telemetry

`MultiAgentTelemetryRecord` extends the base telemetry record with optional fields:

- `session_id`
- `workflow_id`
- `parent_run_id`
- `agent_role`
- `handoff_from`
- `handoff_to`
- `shared_memory_keys`

### Communication events

`AgentCommunicationEvent` captures agent-to-agent communication:

- message
- handoff
- memory share
- tool result
- status update

## Helpers

The `multi_agent.py` module includes:

- `agent_hierarchy` — parent-child run relationships
- `agent_relationship_graph` — node/edge tables for agent relationships
- `communication_events_to_dataframe` — typed event conversion
- `handoff_tracking` — handoff transition extraction
- `shared_memory_tracking` — shared memory key usage
- `agent_utilization_metrics` — run, latency, tool, and memory utilization
- `multi_agent_comparison` — per-agent comparison table
- `workflow_visualization_edges` — ordered workflow transitions
- `orchestration_metrics` — workflow, handoff, edge, and agent counts

## Dashboard integration

The **Agents** tab provides:

- orchestration metric cards
- per-agent summary cards
- utilization table
- run quality table
- latency trend
- confidence/drift trend
- multi-agent comparison
- workflow transition visualization

## Analytics integration

Phase 4 adds `multi_agent_analytics_summary`, which bundles orchestration metrics, utilization, and comparison data for analytics exports.

## Backward compatibility

The loader still validates the existing `TelemetryRecord` schema. Multi-agent models and helper functions can operate on richer dataframes when optional columns are present, while existing JSON/CSV sample telemetry continues to pass all tests and render in the dashboard.
