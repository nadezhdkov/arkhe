from __future__ import annotations
from typing import Any


# ─── db_entity ────────────────────────────────────────────────────────────────

def db_entity(table: str):
    """
    Mark a class as a database entity mapped to *table*.

    Stores metadata only — no SQL executed, no global registry updated.

        @db_entity("users")
        class User:
            pass

    Sets:
        User.__nestify_db_entity__ = True
        User.__nestify_db_table__  = "users"
    """

    def decorator(cls):
        cls.__nestify_db_entity__ = True
        cls.__nestify_db_table__ = table
        return cls

    return decorator


# ─── db_column ────────────────────────────────────────────────────────────────

class _ColumnMeta:
    """Descriptor that stores column metadata on the class's __nestify_columns__ registry."""

    def __init__(self, primary_key: bool = False, unique: bool = False, nullable: bool = True):
        self.primary_key = primary_key
        self.unique = unique
        self.nullable = nullable
        self._name: str | None = None

    def __set_name__(self, owner, name: str) -> None:
        self._name = name
        _register_column(owner, name, self)

    # Transparent get/set so the descriptor doesn't shadow instance attributes.
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self._name)

    def __set__(self, obj, value) -> None:
        obj.__dict__[self._name] = value


def _register_column(cls, name: str, meta: _ColumnMeta) -> None:
    if not hasattr(cls, "__nestify_columns__"):
        cls.__nestify_columns__ = {}
    cls.__nestify_columns__[name] = meta


def db_column(primary_key: bool = False, unique: bool = False, nullable: bool = True) -> _ColumnMeta:
    """
    Annotate a class attribute with column metadata.

    Stores metadata only — nothing is executed at decoration time.

        @db_entity("users")
        class User:
            id:    int   = db_column(primary_key=True)
            email: str   = db_column(unique=True)
            name:  str   = db_column()
    """
    return _ColumnMeta(primary_key=primary_key, unique=unique, nullable=nullable)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_table_name(cls) -> str:
    """Return the table name registered by @db_entity, or the lowercased class name."""
    return getattr(cls, "__nestify_db_table__", cls.__name__.lower())


def get_columns(cls) -> dict[str, _ColumnMeta]:
    """Return the column metadata dict registered via db_column()."""
    return getattr(cls, "__nestify_columns__", {})
