import pytest
from pydantic import ValidationError

from agent_telemetry_dashboard.models import AgentRegistryEntry


def test_agent_registry_entry_validates_agent_metadata() -> None:
    entry = AgentRegistryEntry(
        agent_name="MemoryScout",
        display_name="Memory Scout",
        role="memory",
        description="Indexes and retrieves memory context.",
    )

    assert entry.agent_name == "MemoryScout"
    assert entry.role == "memory"
    assert entry.enabled is True


def test_agent_registry_entry_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AgentRegistryEntry(agent_name="Agent", display_name="Agent", unexpected="field")
