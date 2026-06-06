from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from agent_telemetry_dashboard.loader import load_telemetry

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_load_json_telemetry() -> None:
    df = load_telemetry(DATA_DIR / "sample_telemetry.json")

    assert len(df) == 42
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert df["run_id"].iloc[0] == "run-001"
    assert set(df["status"].unique()) == {"success", "warning", "failed"}


def test_load_csv_telemetry() -> None:
    df = load_telemetry(DATA_DIR / "sample_telemetry.csv")

    assert len(df) == 42
    assert df["tool_calls"].sum() > 0
    assert df["confidence"].between(0, 1).all()


def test_rejects_invalid_suffix(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.txt"
    path.write_text("[]")

    with pytest.raises(ValueError, match="Unsupported telemetry format"):
        load_telemetry(path)


def test_validation_rejects_bad_record(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        """
        [{
          "run_id": "run-bad",
          "agent_name": "Agent",
          "task_name": "Task",
          "timestamp": "2026-05-20T09:00:00",
          "status": "success",
          "memory_reads": -1,
          "memory_writes": 0,
          "tool_calls": 1,
          "failures": 0,
          "retries": 0,
          "confidence": 0.8,
          "drift_score": 0.1,
          "latency_ms": 100,
          "notes": "bad"
        }]
        """
    )

    with pytest.raises(ValidationError):
        load_telemetry(path)


def test_validation_rejects_contradictory_success_record(tmp_path: Path) -> None:
    path = tmp_path / "contradictory.json"
    path.write_text(
        """
        [{
          "run_id": "run-contradictory",
          "agent_name": "Agent",
          "task_name": "Task",
          "timestamp": "2026-05-20T09:00:00",
          "status": "success",
          "memory_reads": 1,
          "memory_writes": 0,
          "tool_calls": 1,
          "failures": 1,
          "retries": 0,
          "confidence": 0.8,
          "drift_score": 0.1,
          "latency_ms": 100,
          "notes": "contradictory"
        }]
        """
    )

    with pytest.raises(ValidationError, match="successful runs cannot report failures"):
        load_telemetry(path)


def test_validation_rejects_unexpected_fields(tmp_path: Path) -> None:
    path = tmp_path / "extra.json"
    path.write_text(
        """
        [{
          "run_id": "run-extra",
          "agent_name": "Agent",
          "task_name": "Task",
          "timestamp": "2026-05-20T09:00:00",
          "status": "success",
          "memory_reads": 1,
          "memory_writes": 0,
          "tool_calls": 1,
          "failures": 0,
          "retries": 0,
          "confidence": 0.8,
          "drift_score": 0.1,
          "latency_ms": 100,
          "notes": "extra",
          "unexpected": "field"
        }]
        """
    )

    with pytest.raises(ValidationError):
        load_telemetry(path)
