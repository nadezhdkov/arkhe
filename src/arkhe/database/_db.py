from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Type, TypeVar

from ._connection import _connection
from ._select import SelectQuery
from ._insert import InsertQuery
from ._update import UpdateQuery
from ._delete import DeleteQuery
from ._schema import create_table as _create_table

T = TypeVar("T")


class _DB:
    """
    Facade that exposes the entire arkhe.database API through a single
    module-level ``DB`` object.

    All methods are class methods so you never need to instantiate _DB.

    Example::

        from arkhe.database import DB

        DB.connect("app.db", wal=True)

        users = (
            DB.select("id", "name")
              .from_table("users")
              .where("active = ?", True)
              .order_by("name", "ASC")
              .execute()
        )
    """

    # ── connection ────────────────────────────────────────────────────────────

    @classmethod
    def connect(cls, path: str, wal: bool = False) -> None:
        """Open (or re-open) the SQLite database at *path*."""
        _connection().connect(path, wal=wal)

    @classmethod
    def close(cls) -> None:
        """Close the current connection."""
        _connection().close()

    # ── transactions ──────────────────────────────────────────────────────────

    @classmethod
    @contextmanager
    def transaction(cls) -> Generator[None, None, None]:
        """
        Context manager that wraps a block in a transaction.

        Commits on success, rolls back on any exception::

            with DB.transaction():
                DB.update("accounts").set(balance=500).where("id = ?", 1).execute()
                DB.update("accounts").set(balance=1000).where("id = ?", 2).execute()
        """
        with _connection().transaction():
            yield

    # ── query builders ────────────────────────────────────────────────────────

    @classmethod
    def select(cls, *columns: str) -> SelectQuery:
        """
        Start a SELECT query.

            DB.select("*")
            DB.select("id", "name", "email")
        """
        return SelectQuery(*columns)

    @classmethod
    def insert_into(cls, table: str) -> InsertQuery:
        """
        Start an INSERT query.

            DB.insert_into("users").values(name="John").execute()
        """
        return InsertQuery(table)

    @classmethod
    def update(cls, table: str) -> UpdateQuery:
        """
        Start an UPDATE query.

            DB.update("users").set(name="Peter").where("id = ?", 1).execute()
        """
        return UpdateQuery(table)

    @classmethod
    def delete_from(cls, table: str) -> DeleteQuery:
        """
        Start a DELETE query.

            DB.delete_from("users").where("id = ?", 1).execute()
        """
        return DeleteQuery(table)

    # ── schema ────────────────────────────────────────────────────────────────

    @classmethod
    def create_table(cls, entity_cls: Type) -> None:
        """
        Generate and execute a CREATE TABLE from *entity_cls* metadata.

            DB.create_table(User)
        """
        _create_table(entity_cls)

    # ── raw escape hatch ──────────────────────────────────────────────────────

    @classmethod
    def execute_raw(cls, sql: str, *params) -> list[dict]:
        """
        Execute arbitrary SQL and return rows as dicts.

        Use only when the query builder cannot express what you need.
        """
        cur = _connection().cursor()
        cur.execute(sql, list(params))
        return [dict(row) for row in cur.fetchall()]


DB = _DB()
