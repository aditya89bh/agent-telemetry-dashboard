"""Typed telemetry models for AI agent runs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RunStatus = Literal["success", "warning", "failed"]
SchemaVersion = Literal["1.0"]
AgentRole = Literal["planner", "executor", "critic", "memory", "tool", "observer", "other"]


class AgentRegistryEntry(BaseModel):
    """Registry metadata for an agent participating in observed runs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    agent_name: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    role: AgentRole = "other"
    description: str = Field(default="", max_length=500)
    owner: str = Field(default="", max_length=120)
    enabled: bool = True

    @field_validator("agent_name", "display_name")
    @classmethod
    def registry_names_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value


class TelemetryRecord(BaseModel):
    """One telemetry event summarizing a single agent run or task step."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: SchemaVersion = "1.0"
    run_id: str = Field(min_length=1, max_length=80)
    agent_name: str = Field(min_length=1, max_length=80)
    task_name: str = Field(min_length=1, max_length=120)
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
    notes: str = Field(default="", max_length=500)

    @field_validator("run_id", "agent_name", "task_name")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_operational_consistency(self) -> TelemetryRecord:
        """Catch contradictory run summaries before they reach the dashboard."""
        if self.status == "success" and self.failures > 0:
            raise ValueError("successful runs cannot report failures")
        if self.status == "failed" and self.failures == 0:
            raise ValueError("failed runs must report at least one failure")
        if self.failures == 0 and self.retries > 0:
            raise ValueError("retries require at least one failure")
        return self
