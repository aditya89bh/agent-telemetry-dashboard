"""Deterministic sample telemetry generation utilities."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from agent_telemetry_dashboard.models import TelemetryRecord

AGENTS = ("MemoryScout", "ToolPilot", "EvalRunner")
TASKS = (
    "summarize_customer_thread",
    "research_competitor",
    "route_support_ticket",
    "generate_run_report",
    "inspect_code_change",
    "triage_agent_failure",
)
STATUSES = ("success", "success", "success", "warning", "failed")


def generate_sample_records(
    count: int = 42,
    start: datetime | None = None,
) -> list[TelemetryRecord]:
    """Generate deterministic, validated telemetry records for demos and tests."""
    if count < 1:
        raise ValueError("count must be at least 1")

    start_time = start or datetime(2026, 5, 20, 9, 0)
    records: list[TelemetryRecord] = []
    for index in range(count):
        status = STATUSES[(index * 2 + index // 5) % len(STATUSES)]
        failures = 0 if status == "success" else (1 if status == "warning" else 2 + index % 2)
        retries = 0 if failures == 0 else min(3, failures + (index % 2))
        records.append(
            TelemetryRecord(
                run_id=f"run-{index + 1:03d}",
                agent_name=AGENTS[index % len(AGENTS)],
                task_name=TASKS[index % len(TASKS)],
                timestamp=start_time + timedelta(hours=9 * index),
                status=status,
                memory_reads=1 + (index * 2) % 8,
                memory_writes=(index % 5) // 2 + (1 if status != "failed" else 0),
                tool_calls=2 + (index * 3) % 11,
                failures=failures,
                retries=retries,
                confidence=round(_confidence_for(index=index, failures=failures), 3),
                drift_score=round(_drift_for(index=index, failures=failures), 3),
                latency_ms=650 + (index * 173) % 4200 + failures * 900,
                notes="sample local telemetry record for dashboard exploration",
            )
        )
    return records


def _confidence_for(index: int, failures: int) -> float:
    raw_confidence = 0.93 - failures * 0.13 - (index % 7) * 0.018 + (index % 3) * 0.025
    return max(0.42, min(0.98, raw_confidence))


def _drift_for(index: int, failures: int) -> float:
    raw_drift = 0.08 + index * 0.012 + failures * 0.08 + (index % 6) * 0.01
    return min(0.85, raw_drift)


def write_sample_json(path: str | Path, records: list[TelemetryRecord]) -> None:
    """Write generated telemetry as a JSON list."""
    Path(path).write_text(
        json.dumps([record.model_dump(mode="json") for record in records], indent=2),
        encoding="utf-8",
    )


def write_sample_csv(path: str | Path, records: list[TelemetryRecord]) -> None:
    """Write generated telemetry as CSV."""
    rows = [record.model_dump(mode="json") for record in records]
    if not rows:
        raise ValueError("records cannot be empty")
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic sample agent telemetry.")
    parser.add_argument("--count", type=int, default=42, help="Number of records to generate.")
    parser.add_argument("--json", type=Path, default=Path("data/sample_telemetry.json"))
    parser.add_argument("--csv", type=Path, default=Path("data/sample_telemetry.csv"))
    args = parser.parse_args()

    records = generate_sample_records(count=args.count)
    write_sample_json(args.json, records)
    write_sample_csv(args.csv, records)


if __name__ == "__main__":
    main()
