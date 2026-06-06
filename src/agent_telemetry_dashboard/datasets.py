"""Dataset registry for persisted trace collections."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class DatasetEntry:
    """Metadata for a saved telemetry dataset."""

    dataset_id: str
    name: str
    created_at: str
    description: str = ""


class DatasetRegistry:
    """JSON-backed registry of trace datasets."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def list_datasets(self) -> list[DatasetEntry]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [DatasetEntry(**item) for item in payload.get("datasets", [])]

    def register(self, dataset_id: str, name: str, description: str = "") -> DatasetEntry:
        datasets = [item for item in self.list_datasets() if item.dataset_id != dataset_id]
        entry = DatasetEntry(
            dataset_id=dataset_id,
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        datasets.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"datasets": [asdict(item) for item in datasets]}, indent=2),
            encoding="utf-8",
        )
        return entry

    def get(self, dataset_id: str) -> DatasetEntry | None:
        """Return one dataset entry by ID."""
        return next((item for item in self.list_datasets() if item.dataset_id == dataset_id), None)

    def remove(self, dataset_id: str) -> bool:
        """Remove a dataset entry by ID and return whether it existed."""
        datasets = self.list_datasets()
        remaining = [item for item in datasets if item.dataset_id != dataset_id]
        if len(remaining) == len(datasets):
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"datasets": [asdict(item) for item in remaining]}, indent=2),
            encoding="utf-8",
        )
        return True
