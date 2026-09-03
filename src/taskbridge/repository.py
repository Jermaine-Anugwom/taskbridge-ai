from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class Repository:
    def __init__(self, path: str | Path = "taskbridge.db") -> None:
        self.path = str(path)
        self.backend = "postgresql" if self.path.startswith(("postgresql://", "postgres://")) else "sqlite"
        self._initialize()

    def _connect(self) -> Any:
        if self.backend == "postgresql":
            try:
                import psycopg
                from psycopg.rows import dict_row
            except ImportError as exc:  # pragma: no cover - exercised by production image
                raise RuntimeError("PostgreSQL requires the psycopg package") from exc
            return psycopg.connect(self.path, row_factory=dict_row)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @property
    def placeholder(self) -> str:
        return "%s" if self.backend == "postgresql" else "?"

    def _initialize(self) -> None:
        schema = """
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
            CREATE TABLE IF NOT EXISTS model_traces (
                id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                payload TEXT NOT NULL, created_at TEXT NOT NULL
            );
        """
        with self._connect() as connection:
            if self.backend == "postgresql":
                for statement in schema.split(";"):
                    if statement.strip():
                        connection.execute(statement)
            else:
                connection.executescript(schema)

    def save(self, table: str, record_id: str, record: BaseModel, **columns: str) -> None:
        allowed = {"workflows", "assessments", "pilots", "pilot_runs", "model_traces"}
        if table not in allowed:
            raise ValueError("unsupported table")
        data = record.model_dump(mode="json")
        common = {"id": record_id, "payload": json.dumps(data, sort_keys=True), "created_at": str(data["created_at"])}
        values = {**common, **columns}
        names = ", ".join(values)
        placeholders = ", ".join(self.placeholder for _ in values)
        with self._connect() as connection:
            if self.backend == "postgresql":
                updates = ", ".join(
                    f"{name} = EXCLUDED.{name}" for name in values if name != "id"
                )
                query = (
                    f"INSERT INTO {table} ({names}) VALUES ({placeholders}) "
                    f"ON CONFLICT (id) DO UPDATE SET {updates}"
                )
            else:
                query = f"INSERT OR REPLACE INTO {table} ({names}) VALUES ({placeholders})"
            connection.execute(query, tuple(values.values()))

    def get(self, table: str, record_id: str) -> dict | None:
        if table not in {"workflows", "assessments", "pilots", "pilot_runs", "model_traces"}:
            raise ValueError("unsupported table")
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT payload FROM {table} WHERE id = {self.placeholder}", (record_id,)
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def get_run_by_fingerprint(self, fingerprint: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT payload FROM pilot_runs WHERE fingerprint = {self.placeholder}",
                (fingerprint,),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_model_traces(self, limit: int = 20) -> list[dict]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT payload FROM model_traces ORDER BY created_at DESC LIMIT {safe_limit}"
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]
