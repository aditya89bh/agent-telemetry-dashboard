from datetime import datetime
from pathlib import Path

from agent_telemetry_dashboard.generator import (
    generate_sample_records,
    write_sample_csv,
    write_sample_json,
)
from agent_telemetry_dashboard.loader import load_telemetry


def test_generate_sample_records_is_deterministic() -> None:
    start = datetime(2026, 1, 1, 9, 0)
    first = generate_sample_records(count=3, start=start)
    second = generate_sample_records(count=3, start=start)

    assert [record.model_dump() for record in first] == [record.model_dump() for record in second]
    assert first[0].run_id == "run-001"
    assert first[0].schema_version == "1.0"


def test_generated_files_load_successfully(tmp_path: Path) -> None:
    records = generate_sample_records(count=5)
    json_path = tmp_path / "telemetry.json"
    csv_path = tmp_path / "telemetry.csv"

    write_sample_json(json_path, records)
    write_sample_csv(csv_path, records)

    json_df = load_telemetry(json_path)
    csv_df = load_telemetry(csv_path)

    assert len(json_df) == 5
    assert len(csv_df) == 5
    assert json_df["run_id"].tolist() == csv_df["run_id"].tolist()
