from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator


class _Connection:
    """
    Internal singleton that wraps a sqlite3 connection.

    Never instantiate directly — use DB.connect() and the module-level
    _connection() helper.
    """

    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def connect(self, path: str, wal: bool = False) -> None:
        if self._conn is not None:
            self._conn.close()

        # isolation_level=None → Python won't auto-BEGIN; we control every
        # transaction explicitly via BEGIN / COMMIT / ROLLBACK.
        self._conn = sqlite3.connect(path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row

        if wal:
            self._conn.execute("PRAGMA journal_mode=WAL")

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── raw access ────────────────────────────────────────────────────────────

    def get(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError(
                "No database connection. Call DB.connect() first."
            )
        return self._conn

    def cursor(self) -> sqlite3.Cursor:
        return self.get().cursor()

    def commit(self) -> None:
        self.get().execute("COMMIT")

    def rollback(self) -> None:
        self.get().execute("ROLLBACK")

    def _begin(self) -> None:
        """Start a new transaction (no-op if one is already open)."""
        try:
            self.get().execute("BEGIN")
        except sqlite3.OperationalError:
            pass  # already inside a transaction

    # ── transaction ───────────────────────────────────────────────────────────

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """
        Explicit transaction block: BEGIN → yield → COMMIT or ROLLBACK.

        Re-entrant safe: if a transaction is already open this is a no-op
        wrapper (inner commit is skipped; outer block stays in charge).
        """
        conn = self.get()
        # Detect whether we're already inside a transaction.
        in_transaction = conn.in_transaction
        if in_transaction:
            yield
            return

        conn.execute("BEGIN")
        try:
            yield
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise


# Module-level singleton — the only instance ever used.
_singleton = _Connection()


def _connection() -> _Connection:
    return _singleton
