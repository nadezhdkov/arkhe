from __future__ import annotations

from typing import Any

from ._connection import _connection
from ._result import DBResult


class UpdateQuery:
    def __init__(self, table: str) -> None:
        self._table = table
        self._sets: dict[str, Any] = {}
        self._wheres: list[str] = []
        self._where_params: list[Any] = []

    def set(self, **kwargs: Any) -> "UpdateQuery":
        self._sets.update(kwargs)
        return self

    def where(self, condition: str, *params: Any) -> "UpdateQuery":
        self._wheres.append(condition)
        self._where_params.extend(params)
        return self

    def _build_sql(self) -> tuple[str, list[Any]]:
        if not self._sets:
            raise RuntimeError("set() must be called with at least one column.")

        assignments = ", ".join(f"{col} = ?" for col in self._sets)
        params: list[Any] = list(self._sets.values())

        sql = f"UPDATE {self._table} SET {assignments}"

        if self._wheres:
            sql += " WHERE " + " AND ".join(f"({w})" for w in self._wheres)
            params.extend(self._where_params)

        return sql, params

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
