from __future__ import annotations

from typing import Any, get_type_hints

from ._connection import _connection
from ._meta import get_table_name, get_columns, _ColumnMeta

_TYPE_MAP: dict[type, str] = {
    int:   "INTEGER",
    float: "REAL",
    str:   "TEXT",
    bytes: "BLOB",
    bool:  "INTEGER",
}

_DEFAULT_AFFINITY = "TEXT"


def _sql_type(python_type: Any) -> str:
    return _TYPE_MAP.get(python_type, _DEFAULT_AFFINITY)


def _build_create_table_sql(cls) -> str:
    table = get_table_name(cls)
    columns_meta: dict[str, _ColumnMeta] = get_columns(cls)

    try:
        hints = get_type_hints(cls)
    except Exception:
        hints = {}

    seen: set[str] = set()
    definitions: list[str] = []

    for col_name, meta in columns_meta.items():
        seen.add(col_name)
        python_type = hints.get(col_name)
        affinity = _sql_type(python_type) if python_type else _DEFAULT_AFFINITY

        parts = [col_name, affinity]
        if meta.primary_key:
            parts.append("PRIMARY KEY")
        if meta.unique:
            parts.append("UNIQUE")
        if not meta.nullable and not meta.primary_key:
            parts.append("NOT NULL")

        definitions.append(" ".join(parts))

    for field_name, python_type in hints.items():
        if field_name.startswith("_") or field_name in seen:
            continue
        affinity = _sql_type(python_type)
        definitions.append(f"{field_name} {affinity}")

    if not definitions:
        raise RuntimeError(
            f"Cannot generate CREATE TABLE for {cls.__name__!r}: "
            "no columns found. Use db_column() or type annotations."
        )

    col_defs = ",\n    ".join(definitions)
    return f"CREATE TABLE IF NOT EXISTS {table} (\n    {col_defs}\n)"


def create_table(cls) -> None:
    sql = _build_create_table_sql(cls)
    conn = _connection()
    conn.get().execute(sql)
