"""
Tests for arkhe.database

Run with:  python -m pytest tests/ -v
"""

import pytest
from dataclasses import dataclass

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arkhe.database import DB, db_entity, db_column, DBResult


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Each test gets an isolated in-memory database."""
    DB.connect(":memory:")
    DB.execute_raw("""
        CREATE TABLE users (
            id    INTEGER PRIMARY KEY,
            name  TEXT,
            email TEXT UNIQUE,
            age   INTEGER
        )
    """)
    yield
    DB.close()


# ─── Models ───────────────────────────────────────────────────────────────────

@db_entity("players")
@dataclass
class Player:
    id:       int
    nickname: str
    score:    int


@db_entity("products")
class Product:
    id:    int = db_column(primary_key=True)
    name:  str = db_column()
    price: float = db_column(nullable=False)


# ─── Metadata ─────────────────────────────────────────────────────────────────

class TestMetadata:
    def test_db_entity_sets_attributes(self):
        assert Player.__nestify_db_entity__ is True
        assert Player.__nestify_db_table__ == "players"

    def test_db_column_registers_metadata(self):
        from arkhe.database._meta import get_columns
        cols = get_columns(Product)
        assert "id" in cols
        assert cols["id"].primary_key is True
        assert cols["price"].nullable is False

    def test_decorator_does_not_execute_sql(self):
        # Decorating a class must never touch the DB.
        @db_entity("ghost")
        class Ghost:
            x: int = db_column(primary_key=True)

        cursor = DB.execute_raw("SELECT name FROM sqlite_master WHERE type='table' AND name='ghost'")
        assert cursor == []


# ─── DBResult ─────────────────────────────────────────────────────────────────

class TestDBResult:
    def test_success(self):
        r = DBResult.success(42)
        assert r.is_success is True
        assert r.data == 42
        assert r.error is None

    def test_failure(self):
        exc = ValueError("boom")
        r = DBResult.failure(exc)
        assert r.is_success is False
        assert r.error is exc
        assert r.error_message == "boom"

    def test_repr_success(self):
        assert "success" in repr(DBResult.success(1))

    def test_repr_failure(self):
        assert "failure" in repr(DBResult.failure(RuntimeError("x")))


# ─── SELECT ───────────────────────────────────────────────────────────────────

class TestSelect:
    def _seed(self):
        DB.insert_into("users").values(name="Alice", email="alice@x.com", age=30).execute()
        DB.insert_into("users").values(name="Bob",   email="bob@x.com",   age=17).execute()
        DB.insert_into("users").values(name="Carol", email="carol@x.com", age=25).execute()

    def test_select_all(self):
        self._seed()
        rows = DB.select("*").from_table("users").execute()
        assert len(rows) == 3

    def test_select_specific_columns(self):
        self._seed()
        rows = DB.select("name", "age").from_table("users").execute()
        assert set(rows[0].keys()) == {"name", "age"}

    def test_where_single(self):
        self._seed()
        rows = DB.select("*").from_table("users").where("age > ?", 18).execute()
        assert len(rows) == 2

    def test_where_multiple_params(self):
        self._seed()
        rows = (DB.select("*")
                  .from_table("users")
                  .where("age > ? AND name != ?", 18, "Alice")
                  .execute())
        assert len(rows) == 1
        assert rows[0]["name"] == "Carol"

    def test_order_asc(self):
        self._seed()
        rows = DB.select("name").from_table("users").order_by("age", "ASC").execute()
        assert rows[0]["name"] == "Bob"

    def test_order_desc(self):
        self._seed()
        rows = DB.select("name").from_table("users").order_by("age", "DESC").execute()
        assert rows[0]["name"] == "Alice"

    def test_limit(self):
        self._seed()
        rows = DB.select("*").from_table("users").limit(2).execute()
        assert len(rows) == 2

    def test_offset(self):
        self._seed()
        rows = DB.select("*").from_table("users").order_by("id", "ASC").offset(1).execute()
        assert len(rows) == 2

    def test_first_returns_dict(self):
        self._seed()
        row = DB.select("*").from_table("users").where("name = ?", "Alice").first()
        assert row is not None
        assert row["name"] == "Alice"

    def test_first_returns_none_when_empty(self):
        row = DB.select("*").from_table("users").where("name = ?", "Nobody").first()
        assert row is None

    def test_into_maps_to_class(self):
        DB.execute_raw("CREATE TABLE players (id INTEGER, nickname TEXT, score INTEGER)")
        DB.insert_into("players").values(id=1, nickname="hero", score=999).execute()
        players = DB.select("*").from_table("players").into(Player)
        assert len(players) == 1
        assert isinstance(players[0], Player)
        assert players[0].nickname == "hero"

    def test_execute_safe_returns_dbresult_on_error(self):
        result = DB.select("*").from_table("nonexistent_table").execute_safe()
        assert result.is_success is False
        assert result.error is not None

    def test_order_by_invalid_direction(self):
        with pytest.raises(ValueError):
            DB.select("*").from_table("users").order_by("name", "SIDEWAYS")


# ─── INSERT ───────────────────────────────────────────────────────────────────

class TestInsert:
    def test_insert_returns_rowid(self):
        rowid = DB.insert_into("users").values(name="Dave", email="dave@x.com", age=40).execute()
        assert isinstance(rowid, int)
        assert rowid == 1

    def test_insert_increments_rowid(self):
        id1 = DB.insert_into("users").values(name="A", email="a@x.com").execute()
        id2 = DB.insert_into("users").values(name="B", email="b@x.com").execute()
        assert id2 > id1

    def test_insert_safe_duplicate_email(self):
        DB.insert_into("users").values(name="X", email="dup@x.com").execute()
        result = DB.insert_into("users").values(name="Y", email="dup@x.com").execute_safe()
        assert result.is_success is False

    def test_insert_safe_success(self):
        result = DB.insert_into("users").values(name="Z", email="z@x.com").execute_safe()
        assert result.is_success is True
        assert result.data == 1

    def test_insert_no_values_raises(self):
        with pytest.raises(RuntimeError):
            DB.insert_into("users").execute()


# ─── UPDATE ───────────────────────────────────────────────────────────────────

class TestUpdate:
    def _seed(self):
        DB.insert_into("users").values(name="Alice", email="alice@x.com", age=30).execute()
        DB.insert_into("users").values(name="Bob",   email="bob@x.com",   age=25).execute()

    def test_update_returns_affected_rows(self):
        self._seed()
        count = DB.update("users").set(age=99).where("name = ?", "Alice").execute()
        assert count == 1

    def test_update_persists(self):
        self._seed()
        DB.update("users").set(name="Alicia").where("email = ?", "alice@x.com").execute()
        row = DB.select("*").from_table("users").where("email = ?", "alice@x.com").first()
        assert row["name"] == "Alicia"

    def test_update_no_where_affects_all(self):
        self._seed()
        count = DB.update("users").set(age=0).execute()
        assert count == 2

    def test_update_no_set_raises(self):
        self._seed()
        with pytest.raises(RuntimeError):
            DB.update("users").where("id = ?", 1).execute()

    def test_update_safe_error(self):
        result = DB.update("no_table").set(x=1).execute_safe()
        assert result.is_success is False


# ─── DELETE ───────────────────────────────────────────────────────────────────

class TestDelete:
    def _seed(self):
        DB.insert_into("users").values(name="Alice", email="a@x.com").execute()
        DB.insert_into("users").values(name="Bob",   email="b@x.com").execute()

    def test_delete_with_where(self):
        self._seed()
        count = DB.delete_from("users").where("name = ?", "Alice").execute()
        assert count == 1
        rows = DB.select("*").from_table("users").execute()
        assert len(rows) == 1

    def test_delete_all(self):
        self._seed()
        DB.delete_from("users").execute()
        assert DB.select("*").from_table("users").execute() == []

    def test_delete_safe_error(self):
        result = DB.delete_from("no_table").where("id = ?", 1).execute_safe()
        assert result.is_success is False


# ─── SCHEMA ───────────────────────────────────────────────────────────────────

class TestSchema:
    def test_create_table_from_entity(self):
        DB.create_table(Product)
        tables = DB.execute_raw(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
        )
        assert len(tables) == 1

    def test_create_table_idempotent(self):
        DB.create_table(Product)
        DB.create_table(Product)  # should not raise (IF NOT EXISTS)

    def test_created_table_is_usable(self):
        DB.create_table(Product)
        DB.insert_into("products").values(name="Widget", price=9.99).execute()
        rows = DB.select("*").from_table("products").execute()
        assert rows[0]["name"] == "Widget"

    def test_create_table_from_dataclass(self):
        DB.execute_raw("DROP TABLE IF EXISTS players")
        DB.create_table(Player)
        tables = DB.execute_raw(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='players'"
        )
        assert len(tables) == 1


# ─── TRANSACTIONS ─────────────────────────────────────────────────────────────

class TestTransactions:
    def test_commit_on_success(self):
        with DB.transaction():
            DB.insert_into("users").values(name="T1", email="t1@x.com").execute()
            DB.insert_into("users").values(name="T2", email="t2@x.com").execute()

        rows = DB.select("*").from_table("users").execute()
        assert len(rows) == 2

    def test_rollback_on_exception(self):
        with pytest.raises(Exception):
            with DB.transaction():
                DB.insert_into("users").values(name="T1", email="ok@x.com").execute()
                # Force a constraint violation to trigger rollback
                DB.insert_into("users").values(name="T2", email="ok@x.com").execute()

        rows = DB.select("*").from_table("users").execute()
        assert rows == []

    def test_nested_operations_atomic(self):
        DB.execute_raw("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER)")
        DB.insert_into("accounts").values(id=1, balance=1000).execute()
        DB.insert_into("accounts").values(id=2, balance=500).execute()

        with DB.transaction():
            DB.update("accounts").set(balance=800).where("id = ?", 1).execute()
            DB.update("accounts").set(balance=700).where("id = ?", 2).execute()

        rows = DB.select("*").from_table("accounts").order_by("id").execute()
        assert rows[0]["balance"] == 800
        assert rows[1]["balance"] == 700


# ─── WAL mode ─────────────────────────────────────────────────────────────────

class TestWAL:
    def test_wal_connect(self, tmp_path):
        path = str(tmp_path / "wal_test.db")
        DB.connect(path, wal=True)
        rows = DB.execute_raw("PRAGMA journal_mode")
        assert rows[0]["journal_mode"] == "wal"
        DB.close()
        DB.connect(":memory:")  # restore for cleanup fixture
