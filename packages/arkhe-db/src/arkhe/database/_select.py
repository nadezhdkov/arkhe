from __future__ import annotations

from typing import Any, Type, TypeVar

from ._connection import _connection
from ._result import DBResult

T = TypeVar("T")


class SelectQuery:
    """
    Fluent SELECT query builder.

    Usage::

        users = (
            DB.select("id", "name")
              .from_table("users")
              .where("age > ?", 18)
              .order_by("name", "ASC")
              .limit(10)
              .offset(0)
              .execute()
        )
    """

    def __init__(self, *columns: str) -> None:
        self._columns: tuple[str, ...] = columns if columns else ("*",)
        self._table: str | None = None
        self._wheres: list[str] = []
        self._params: list[Any] = []
        self._order_col: str | None = None
        self._order_dir: str = "ASC"
        self._limit_val: int | None = None
        self._offset_val: int | None = None

    # ── builder methods ───────────────────────────────────────────────────────

    def from_table(self, table: str) -> "SelectQuery":
        self._table = table
        return self

    def where(self, condition: str, *params: Any) -> "SelectQuery":
        self._wheres.append(condition)
        self._params.extend(params)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "SelectQuery":
        direction = direction.upper()
        if direction not in ("ASC", "DESC"):
            raise ValueError(f"order_by direction must be ASC or DESC, got {direction!r}")
        self._order_col = column
        self._order_dir = direction
        return self

    def limit(self, n: int) -> "SelectQuery":
        self._limit_val = n
        return self

    def offset(self, n: int) -> "SelectQuery":
        self._offset_val = n
        return self

    # ── terminal methods ──────────────────────────────────────────────────────

    def _build_sql(self) -> str:
        if self._table is None:
            raise RuntimeError("from_table() must be called before executing a query.")

        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"

        if self._wheres:
            sql += " WHERE " + " AND ".join(f"({w})" for w in self._wheres)

        if self._order_col:
            sql += f" ORDER BY {self._order_col} {self._order_dir}"

        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        elif self._offset_val is not None:
            # SQLite requires LIMIT before OFFSET; -1 means "all rows"
            sql += " LIMIT -1"

        if self._offset_val is not None:
            sql += f" OFFSET {self._offset_val}"

        return sql

    def execute(self) -> list[dict[str, Any]]:
        """Execute and return a list of plain dicts."""
        sql = self._build_sql()
        cur = _connection().cursor()
        cur.execute(sql, self._params)
        return [dict(row) for row in cur.fetchall()]

    def first(self) -> dict[str, Any] | None:
        """Execute and return the first result dict, or None."""
        self._limit_val = 1
        rows = self.execute()
        return rows[0] if rows else None

    def into(self, cls: Type[T]) -> list[T]:
        """Execute and map each row into an instance of *cls* via cls(**row)."""
        rows = self.execute()
        return [cls(**row) for row in rows]

    def execute_safe(self) -> DBResult:
        """Execute without raising — returns a DBResult."""
        try:
            return DBResult.success(self.execute())
        except Exception as exc:
            return DBResult.failure(exc)

    def first_safe(self) -> DBResult:
        try:
            return DBResult.success(self.first())
        except Exception as exc:
            return DBResult.failure(exc)

    def into_safe(self, cls: Type[T]) -> DBResult:
        try:
            return DBResult.success(self.into(cls))
        except Exception as exc:
            return DBResult.failure(exc)
