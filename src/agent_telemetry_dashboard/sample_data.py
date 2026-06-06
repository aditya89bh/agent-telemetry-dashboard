"""Helpers for locating bundled sample telemetry data."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sample_json_path() -> Path:
    return project_root() / "data" / "sample_telemetry.json"


def sample_csv_path() -> Path:
    return project_root() / "data" / "sample_telemetry.csv"
