import os
import sqlite3
from contextlib import contextmanager
from typing import Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "products.db")


@contextmanager
def _conn(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class BaseRepository:
    """
    Template Method pattern.

    Subclasses declare two class attributes:
        table      — the SQLite table name
        create_sql — the CREATE TABLE IF NOT EXISTS DDL string

    All generic CRUD methods (get_all, get_by_id, get_by_field,
    upsert, delete, delete_all) are inherited for free.
    Subclasses only need to add methods for domain-specific queries.
    """

    table: str = ""
    create_sql: str = ""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self._db = db_path
        with _conn(self._db) as conn:
            conn.execute(self.create_sql)

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        with _conn(self._db) as conn:
            return [dict(r) for r in conn.execute(f"SELECT * FROM {self.table}")]

    def get_by_id(self, id: str) -> dict | None:
        with _conn(self._db) as conn:
            row = conn.execute(
                f"SELECT * FROM {self.table} WHERE id = ?", (id,)
            ).fetchone()
            return dict(row) if row else None

    def get_by_field(self, field: str, value: Any) -> list[dict]:
        with _conn(self._db) as conn:
            rows = conn.execute(
                f"SELECT * FROM {self.table} WHERE {field} = ?", (value,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Write ─────────────────────────────────────────────────────────────────

    def upsert(self, data: dict) -> dict:
        cols    = list(data.keys())
        ph      = ", ".join("?" * len(cols))
        col_str = ", ".join(cols)
        updates = ", ".join(f"{c} = excluded.{c}" for c in cols if c != "id")
        sql = (
            f"INSERT INTO {self.table} ({col_str}) VALUES ({ph}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}"
        )
        with _conn(self._db) as conn:
            conn.execute(sql, list(data.values()))
        return data

    def delete(self, id: str) -> bool:
        with _conn(self._db) as conn:
            cur = conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (id,))
            return cur.rowcount > 0

    def delete_all(self) -> None:
        with _conn(self._db) as conn:
            conn.execute(f"DELETE FROM {self.table}")
