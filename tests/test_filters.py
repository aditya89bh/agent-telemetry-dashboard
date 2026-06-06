from pathlib import Path

from agent_telemetry_dashboard.filters import filter_telemetry
from agent_telemetry_dashboard.loader import load_telemetry

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_telemetry.json"


def test_filter_telemetry_by_agent_status_and_task() -> None:
    df = load_telemetry(DATA)
    agent = df.loc[0, "agent_name"]
    task = df.loc[0, "task_name"]

    result = filter_telemetry(
        df,
        agents=[agent],
        statuses=["success"],
        tasks=[task],
    )

    assert not result.empty
    assert set(result["agent_name"]) == {agent}
    assert set(result["status"]) == {"success"}
    assert set(result["task_name"]) == {task}


def test_filter_telemetry_by_date_range_and_confidence() -> None:
    df = load_telemetry(DATA)
    start = df["timestamp"].dt.date.min()
    end = start

    result = filter_telemetry(df, date_range=(start, end), min_confidence=0.85)

    assert (result["timestamp"].dt.date == start).all()
    assert (result["confidence"] >= 0.85).all()
