"""
arkhe.database
==================

A fluent, lightweight and domain-isolated SQLite toolkit for Python.

Public API::

    from arkhe.database import DB, db_entity, db_column, DBResult

Quickstart::

    DB.connect("app.db")

    @db_entity("users")
    @dataclass
    class User:
        id:    int = db_column(primary_key=True)
        email: str = db_column(unique=True)
        name:  str = db_column()

    DB.create_table(User)

    DB.insert_into("users").values(name="Alice", email="alice@example.com").execute()

    users = DB.select("*").from_table("users").into(User)
"""

from ._db import DB
from ._meta import db_entity, db_column
from ._result import DBResult

__all__ = [
    "DB",
    "db_entity",
    "db_column",
    "DBResult",
]
