"""Stdlib HTTP server entrypoint for the telemetry collector."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from agent_telemetry_dashboard.collector import CollectorConfig, create_collector


class CollectorRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that dispatches JSON requests to CollectorAPI."""

    collector = create_collector()

    def do_GET(self) -> None:
        """Handle GET collector requests."""
        self._handle({})

    def do_POST(self) -> None:
        """Handle POST collector requests."""
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        payload: dict[str, Any] = json.loads(body.decode("utf-8"))
        self._handle(payload)

    def _handle(self, payload: dict[str, Any]) -> None:
        response = self.collector.dispatch(self.command, self.path, payload)
        body = json.dumps(response.body).encode("utf-8")
        self.send_response(int(response.status_code))
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_server() -> ThreadingHTTPServer:
    """Build a configured collector HTTP server."""
    host = os.getenv("AGENT_TELEMETRY_HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_TELEMETRY_PORT", "8080"))
    store_path = Path(os.getenv("AGENT_TELEMETRY_STORE_PATH", "data/trace_store.sqlite"))
    dataset_id = os.getenv("AGENT_TELEMETRY_DEFAULT_DATASET", "default")
    CollectorRequestHandler.collector = create_collector(
        CollectorConfig(store_path=store_path, default_dataset_id=dataset_id)
    )
    return ThreadingHTTPServer((host, port), CollectorRequestHandler)


def main() -> None:
    """Run the collector server until interrupted."""
    server = build_server()
    server.serve_forever()


if __name__ == "__main__":
    main()
