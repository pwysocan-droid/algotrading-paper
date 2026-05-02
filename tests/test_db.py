"""Tests for db.py migration runner.

Each migration must be applicable up and rollback-able down. Schema verification
happens by snapshotting table list at each step.
"""

import sqlite3
from pathlib import Path

import pytest

import db

EXPECTED_TABLES = [
    "bars",
    "context_data",
    "signals",
    "trades",
    "decisions",
    "runs",
    "recommendations",
    "llm_calls",
]


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


def _tables(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    return {r["name"] for r in rows}


def test_migrate_creates_all_tables(tmp_db: Path) -> None:
    applied = db.migrate(tmp_db)
    assert len(applied) == 8, f"expected 8 migrations, got {len(applied)}: {applied}"

    tables = _tables(tmp_db)
    for table in EXPECTED_TABLES:
        assert table in tables, f"missing table: {table}"
    assert "schema_migrations" in tables


def test_migrate_is_idempotent(tmp_db: Path) -> None:
    first = db.migrate(tmp_db)
    second = db.migrate(tmp_db)
    assert len(first) == 8
    assert second == [], "second migrate should apply zero migrations"


def test_rollback_reverses_each_migration(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    initial_tables = _tables(tmp_db)

    expected_drop_order = list(reversed(EXPECTED_TABLES))

    for expected_table_dropped in expected_drop_order:
        before = _tables(tmp_db)
        rolled = db.rollback(tmp_db, steps=1)
        assert len(rolled) == 1
        after = _tables(tmp_db)
        dropped = before - after
        assert dropped == {expected_table_dropped}, (
            f"expected {expected_table_dropped!r} to be dropped, "
            f"actually dropped {dropped}"
        )

    final_tables = _tables(tmp_db)
    assert final_tables == {"schema_migrations"}, (
        f"after full rollback, only schema_migrations should remain; "
        f"found {final_tables}"
    )

    db.migrate(tmp_db)
    re_applied = _tables(tmp_db)
    assert re_applied == initial_tables


def test_rollback_then_migrate_returns_to_same_schema(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    snapshot = _tables(tmp_db)

    rolled = db.rollback(tmp_db, steps=8)
    assert len(rolled) == 8

    db.migrate(tmp_db)
    assert _tables(tmp_db) == snapshot


def test_bars_schema_exact(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    conn = sqlite3.connect(tmp_db)
    cols = conn.execute("PRAGMA table_info(bars)").fetchall()
    conn.close()
    col_names = [c[1] for c in cols]
    assert col_names == [
        "symbol",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "fetched_at",
    ]


def test_llm_calls_schema(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    conn = sqlite3.connect(tmp_db)
    cols = conn.execute("PRAGMA table_info(llm_calls)").fetchall()
    conn.close()
    col_names = [c[1] for c in cols]
    expected = [
        "id",
        "timestamp",
        "prompt_hash",
        "prompt_full",
        "response_full",
        "model",
        "latency_ms",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "called_from",
    ]
    assert col_names == expected


def test_partial_rollback_steps(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    rolled = db.rollback(tmp_db, steps=3)
    assert rolled == ["008", "007", "006"]
    remaining = _tables(tmp_db)
    assert "bars" in remaining
    assert "context_data" in remaining
    assert "signals" in remaining
    assert "trades" in remaining
    assert "decisions" in remaining
    assert "runs" not in remaining
    assert "recommendations" not in remaining
    assert "llm_calls" not in remaining


def test_applied_versions_tracked(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    with db.connect(tmp_db) as conn:
        versions = db.applied_versions(conn)
    assert versions == {"001", "002", "003", "004", "005", "006", "007", "008"}
