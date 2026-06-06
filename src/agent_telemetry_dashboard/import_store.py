"""Import validated telemetry dataframes into a persistent trace store."""

from __future__ import annotations

import pandas as pd

from agent_telemetry_dashboard.trace_store import StoredTrace, TraceRepository


def telemetry_dataframe_to_traces(df: pd.DataFrame, dataset_id: str) -> list[StoredTrace]:
    """Convert dashboard telemetry rows into stored run summary traces."""
    traces: list[StoredTrace] = []
    for row in df.itertuples(index=False):
        payload = {column: getattr(row, column) for column in df.columns}
        traces.append(
            StoredTrace(
                trace_id=f"{dataset_id}:{row.run_id}",
                dataset_id=dataset_id,
                trace_type="run_summary",
                run_id=str(row.run_id),
                timestamp=row.timestamp.isoformat(),
                payload=payload,
            )
        )
    return traces


def import_dataframe_to_store(
    df: pd.DataFrame,
    repository: TraceRepository,
    dataset_id: str,
) -> int:
    """Persist a validated telemetry dataframe into the trace store."""
    traces = telemetry_dataframe_to_traces(df, dataset_id)
    for trace in traces:
        repository.save(trace)
    return len(traces)
