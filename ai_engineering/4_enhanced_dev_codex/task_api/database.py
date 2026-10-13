"""Small SQLite repository; each operation owns and closes its connection."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

MAX_TASK_ID = 2**63 - 1  # SQLite INTEGER's upper bound.


class TaskDatabase:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                    description TEXT,
                    status TEXT NOT NULL CHECK (status IN ('todo', 'in_progress', 'done')),
                    created_at TEXT NOT NULL
                )"""
            )

    def create(self, values: dict) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        with self.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, description, status, created_at) VALUES (?, ?, ?, ?)",
                (values["title"], values["description"], values["status"], created_at),
            )
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(row)

    def list(self) -> list[dict]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM tasks ORDER BY id")]

    def get(self, task_id: int) -> dict | None:
        if task_id > MAX_TASK_ID:
            return None
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def update(self, task_id: int, changes: dict) -> dict | None:
        if task_id > MAX_TASK_ID:
            return None
        with self.connection() as connection:
            # Serialize read/merge/write so concurrent patches cannot lose omitted fields.
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                return None
            values = dict(row)
            values.update(changes)
            connection.execute(
                "UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ?",
                (values["title"], values["description"], values["status"], task_id),
            )
            return values

    def delete(self, task_id: int) -> bool:
        if task_id > MAX_TASK_ID:
            return False
        with self.connection() as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount == 1
