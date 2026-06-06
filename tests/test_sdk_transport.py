"""Tests for SDK transport behavior."""

from __future__ import annotations

import asyncio

from agent_telemetry_dashboard.sdk import TelemetryClient, TelemetrySDKConfig
from agent_telemetry_dashboard.trace_store import SQLiteTraceStore, StoredTrace, TraceRepository


class RecordingTransport:
    """Test transport that records sends."""

    def __init__(self) -> None:
        self.sent: list[StoredTrace] = []
        self.batches: list[list[StoredTrace]] = []

    def send(self, trace: StoredTrace) -> None:
        self.sent.append(trace)

    def send_batch(self, traces: list[StoredTrace]) -> None:
        self.batches.append(traces)


def test_sdk_uses_custom_transport(tmp_path):
    repository = TraceRepository(SQLiteTraceStore(tmp_path / "traces.sqlite"))
    transport = RecordingTransport()
    client = TelemetryClient(repository=repository, transport=transport)

    trace = client.emit_event(run_id="run-1", event_name="started")

    assert transport.sent == [trace]
    assert repository.list_traces("default") == []


def test_sdk_batches_until_flush(tmp_path):
    repository = TraceRepository(SQLiteTraceStore(tmp_path / "traces.sqlite"))
    transport = RecordingTransport()
    client = TelemetryClient(
        repository=repository,
        config=TelemetrySDKConfig(batch_size=2),
        transport=transport,
    )

    first = client.emit_event(run_id="run-1", event_name="one")
    second = client.emit_event(run_id="run-1", event_name="two")

    assert transport.sent == []
    assert transport.batches == [[first, second]]


def test_sdk_async_emit_uses_transport(tmp_path):
    repository = TraceRepository(SQLiteTraceStore(tmp_path / "traces.sqlite"))
    transport = RecordingTransport()
    client = TelemetryClient(repository=repository, transport=transport)

    trace = asyncio.run(client.async_emit("event", "run-1", {"event_name": "async"}))

    assert transport.sent == [trace]
