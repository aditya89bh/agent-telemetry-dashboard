"""Trace store schema migration helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

MigrationFn = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class TraceMigration:
    """One ordered trace schema migration."""

    version: int
    name: str
    apply: MigrationFn


def _baseline_metadata(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS trace_schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


TRACE_MIGRATIONS: tuple[TraceMigration, ...] = (
    TraceMigration(version=1, name="baseline_metadata", apply=_baseline_metadata),
)


class TraceMigrationRunner:
    """Apply trace schema migrations to a SQLite database."""

    def __init__(
        self,
        path: str | Path,
        migrations: tuple[TraceMigration, ...] | None = None,
    ) -> None:
        self.path = Path(path)
        self.migrations = migrations or TRACE_MIGRATIONS

    def apply(self) -> list[int]:
        """Apply pending migrations and return their versions."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        applied: list[int] = []
        with sqlite3.connect(self.path) as connection:
            _baseline_metadata(connection)
            existing = {
                row[0]
                for row in connection.execute("SELECT version FROM trace_schema_migrations")
            }
            for migration in sorted(self.migrations, key=lambda item: item.version):
                if migration.version in existing:
                    continue
                migration.apply(connection)
                connection.execute(
                    "INSERT INTO trace_schema_migrations (version, name) VALUES (?, ?)",
                    (migration.version, migration.name),
                )
                applied.append(migration.version)
            connection.execute(f"PRAGMA user_version = {self.current_version}")
        return applied

    @property
    def current_version(self) -> int:
        """Return the latest configured migration version."""
        if not self.migrations:
            return 0
        return max(migration.version for migration in self.migrations)
