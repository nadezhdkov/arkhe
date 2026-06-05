from __future__ import annotations

from typing import Any

from ._connection import _connection
from ._result import DBResult


class DeleteQuery:
    def __init__(self, table: str) -> None:
        self._table = table
        self._wheres: list[str] = []
        self._params: list[Any] = []

    def where(self, condition: str, *params: Any) -> "DeleteQuery":
        self._wheres.append(condition)
        self._params.extend(params)
        return self

    def _build_sql(self) -> tuple[str, list[Any]]:
        sql = f"DELETE FROM {self._table}"
        if self._wheres:
            sql += " WHERE " + " AND ".join(f"({w})" for w in self._wheres)
        return sql, self._params

    def execute(self) -> int:
        sql, params = self._build_sql()
        conn = _connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.rowcount

    def execute_safe(self) -> DBResult:
        try:
            return DBResult.success(self.execute())
        except Exception as exc:
            return DBResult.failure(exc)
