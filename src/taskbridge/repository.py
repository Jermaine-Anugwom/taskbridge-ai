from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pydantic import BaseModel


class Repository:
    def __init__(self, path: str | Path = "taskbridge.db") -> None:
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pilots (
                    id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, scenario_id TEXT NOT NULL,
                    payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pilot_runs (
                    id TEXT PRIMARY KEY, pilot_id TEXT NOT NULL, fingerprint TEXT UNIQUE NOT NULL,
                    payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                """
            )

    def save(self, table: str, record_id: str, record: BaseModel, **columns: str) -> None:
        allowed = {"workflows", "assessments", "pilots", "pilot_runs"}
        if table not in allowed:
            raise ValueError("unsupported table")
        data = record.model_dump(mode="json")
        common = {"id": record_id, "payload": json.dumps(data, sort_keys=True), "created_at": str(data["created_at"])}
        values = {**common, **columns}
        names = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        with self._connect() as connection:
            connection.execute(
                f"INSERT OR REPLACE INTO {table} ({names}) VALUES ({placeholders})",
                tuple(values.values()),
            )

    def get(self, table: str, record_id: str) -> dict | None:
        if table not in {"workflows", "assessments", "pilots", "pilot_runs"}:
            raise ValueError("unsupported table")
        with self._connect() as connection:
            row = connection.execute(f"SELECT payload FROM {table} WHERE id = ?", (record_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def get_run_by_fingerprint(self, fingerprint: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM pilot_runs WHERE fingerprint = ?", (fingerprint,)
            ).fetchone()
        return json.loads(row["payload"]) if row else None
