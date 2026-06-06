"""Import history tracking for telemetry ingestion runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ImportHistoryEntry:
    """Persistent metadata about a telemetry import attempt."""

    source_name: str
    format: str
    records: int
    status: str
    imported_at: str
    message: str = ""


def create_import_history_entry(
    source_name: str,
    format: str,
    records: int,
    status: str = "success",
    message: str = "",
) -> ImportHistoryEntry:
    """Create a timestamped import history entry."""
    return ImportHistoryEntry(
        source_name=source_name,
        format=format,
        records=records,
        status=status,
        imported_at=datetime.now(timezone.utc).isoformat(),
        message=message,
    )


def append_import_history(path: str | Path, entry: ImportHistoryEntry) -> None:
    """Append an import history entry to a JSON Lines file."""
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def load_import_history(path: str | Path) -> list[ImportHistoryEntry]:
    """Load import history entries from a JSON Lines file."""
    history_path = Path(path)
    if not history_path.exists():
        return []
    entries: list[ImportHistoryEntry] = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(ImportHistoryEntry(**json.loads(line)))
    return entries
