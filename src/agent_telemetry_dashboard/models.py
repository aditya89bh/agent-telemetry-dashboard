"""Typed telemetry models for AI agent runs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

RunStatus = Literal["success", "warning", "failed"]


class TelemetryRecord(BaseModel):
    """One telemetry event summarizing a single agent run or task step."""

    run_id: str
    agent_name: str
    task_name: str
    timestamp: datetime
    status: RunStatus
    memory_reads: int = Field(ge=0)
    memory_writes: int = Field(ge=0)
    tool_calls: int = Field(ge=0)
    failures: int = Field(ge=0)
    retries: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    drift_score: float = Field(ge=0.0, le=1.0)
    latency_ms: int = Field(ge=0)
    notes: str = ""

    @field_validator("run_id", "agent_name", "task_name")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value
