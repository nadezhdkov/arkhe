from __future__ import annotations

from typing import Any

from ._connection import _connection
from ._result import DBResult


class InsertQuery:
    """
    Fluent INSERT query builder.

    Usage::

        row_id = (
            DB.insert_into("users")
              .values(name="John", email="john@example.com")
              .execute()
        )
    """

    def __init__(self, table: str) -> None:
        self._table = table
        self._data: dict[str, Any] = {}

    def values(self, **kwargs: Any) -> "InsertQuery":
        self._data.update(kwargs)
        return self

    def _build_sql(self) -> tuple[str, list[Any]]:
        if not self._data:
            raise RuntimeError("values() must be called with at least one column.")

        cols = ", ".join(self._data.keys())
        placeholders = ", ".join("?" for _ in self._data)
        sql = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"
        return sql, list(self._data.values())

    def execute(self) -> int:
        """Execute and return the inserted row's rowid."""
        sql, params = self._build_sql()
        conn = _connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        # Only auto-commit when NOT inside an explicit transaction block.
        if not conn.get().in_transaction:
            pass  # isolation_level=None: statement already committed
        return cur.lastrowid

    def execute_safe(self) -> DBResult:
        try:
            return DBResult.success(self.execute())
        except Exception as exc:
            return DBResult.failure(exc)
