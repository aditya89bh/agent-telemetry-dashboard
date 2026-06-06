"""Typed telemetry models for AI agent runs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RunStatus = Literal["success", "warning", "failed"]
SchemaVersion = Literal["1.0"]
AgentRole = Literal["planner", "executor", "critic", "memory", "tool", "observer", "other"]
CommunicationType = Literal["message", "handoff", "memory_share", "tool_result", "status_update"]
MemorySource = Literal["episodic", "semantic", "procedural", "working", "external", "other"]
MemoryWriteOperation = Literal["create", "update", "delete", "merge", "expire"]
MemoryInfluenceKind = Literal["decision", "tool_selection", "response", "plan", "safety", "other"]


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


class MultiAgentTelemetryRecord(TelemetryRecord):
    """Optional extension for multi-agent and workflow-aware telemetry."""

    session_id: str = Field(default="default", min_length=1, max_length=120)
    workflow_id: str = Field(default="default", min_length=1, max_length=120)
    parent_run_id: str | None = Field(default=None, max_length=80)
    agent_role: AgentRole = "other"
    handoff_from: str | None = Field(default=None, max_length=80)
    handoff_to: str | None = Field(default=None, max_length=80)
    shared_memory_keys: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("session_id", "workflow_id")
    @classmethod
    def multi_agent_ids_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value


class AgentCommunicationEvent(BaseModel):
    """Communication event between agents in an observed workflow."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    source_agent: str = Field(min_length=1, max_length=80)
    target_agent: str = Field(min_length=1, max_length=80)
    communication_type: CommunicationType = "message"
    run_id: str | None = Field(default=None, max_length=80)
    payload_summary: str = Field(default="", max_length=500)


class MemoryRetrievalTrace(BaseModel):
    """Trace for a memory item retrieved during an agent run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    trace_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=80)
    memory_id: str = Field(min_length=1, max_length=120)
    timestamp: datetime
    query: str = Field(default="", max_length=500)
    source: MemorySource = "other"
    relevance_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(default=1, ge=1)
    content_summary: str = Field(default="", max_length=500)


class MemoryWriteTrace(BaseModel):
    """Trace for a memory write or lifecycle mutation during an agent run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    trace_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=80)
    memory_id: str = Field(min_length=1, max_length=120)
    timestamp: datetime
    operation: MemoryWriteOperation = "create"
    source: MemorySource = "other"
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    previous_summary: str = Field(default="", max_length=500)
    new_summary: str = Field(default="", max_length=500)


class MemoryInfluenceTrace(BaseModel):
    """Trace describing how a memory influenced downstream agent behavior."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    trace_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=80)
    memory_id: str = Field(min_length=1, max_length=120)
    timestamp: datetime
    influence_kind: MemoryInfluenceKind = "other"
    target: str = Field(default="", max_length=200)
    evidence: str = Field(default="", max_length=500)
    influence_strength: float = Field(default=0.0, ge=0.0, le=1.0)


class MemoryDecisionTrace(BaseModel):
    """Trace linking one or more memory items to an agent decision."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    trace_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=80)
    decision_id: str = Field(min_length=1, max_length=120)
    timestamp: datetime
    memory_ids: list[str] = Field(default_factory=list, max_length=50)
    decision_summary: str = Field(default="", max_length=500)
    rationale: str = Field(default="", max_length=500)
    confidence_delta: float = Field(default=0.0, ge=-1.0, le=1.0)
