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

# Total migrations including any that modify existing schema (not just table-creates).
EXPECTED_MIGRATION_COUNT = 9

# Migrations that add a table (vs. modify an existing one). Used by the
# rollback-drops-table test which only applies to table-creating migrations.
TABLE_CREATING_VERSIONS = (
    ("001", "bars"),
    ("002", "context_data"),
    ("003", "signals"),
    ("004", "trades"),
    ("005", "decisions"),
    ("006", "runs"),
    ("007", "recommendations"),
    ("008", "llm_calls"),
)


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


def _columns(db_path: Path, table: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    conn.close()
    return [c[1] for c in cols]


def test_migrate_creates_all_tables(tmp_db: Path) -> None:
    applied = db.migrate(tmp_db)
    assert len(applied) == EXPECTED_MIGRATION_COUNT, (
        f"expected {EXPECTED_MIGRATION_COUNT} migrations, got {len(applied)}: {applied}"
    )

    tables = _tables(tmp_db)
    for table in EXPECTED_TABLES:
        assert table in tables, f"missing table: {table}"
    assert "schema_migrations" in tables


def test_migrate_is_idempotent(tmp_db: Path) -> None:
    first = db.migrate(tmp_db)
    second = db.migrate(tmp_db)
    assert len(first) == EXPECTED_MIGRATION_COUNT
    assert second == [], "second migrate should apply zero migrations"


def test_rollback_reverses_each_migration(tmp_db: Path) -> None:
    """Non-negotiable: every up migration has a working down migration.

    Migration 009 modifies an existing table (adds kind column to runs)
    rather than creating one, so the assertion is split: roll back the
    column-modifying migrations first, then verify table-creating
    migrations drop their tables on rollback.
    """
    db.migrate(tmp_db)
    initial_tables = _tables(tmp_db)
    initial_runs_cols = _columns(tmp_db, "runs")

    # Roll back migration 009 — removes a column, no table change.
    rolled = db.rollback(tmp_db, steps=1)
    assert rolled == ["009"]
    after_009 = _tables(tmp_db)
    assert after_009 == initial_tables, "migration 009 down should not drop a table"
    after_009_cols = _columns(tmp_db, "runs")
    assert "kind" in initial_runs_cols
    assert "kind" not in after_009_cols, "migration 009 down should remove the kind column"

    # Roll back 001-008 — each drops one table, in reverse creation order.
    for expected_version, expected_table_dropped in reversed(TABLE_CREATING_VERSIONS):
        before = _tables(tmp_db)
        rolled = db.rollback(tmp_db, steps=1)
        assert rolled == [expected_version]
        after = _tables(tmp_db)
        dropped = before - after
        assert dropped == {expected_table_dropped}, (
            f"expected {expected_table_dropped!r} to be dropped on rollback of "
            f"{expected_version}, actually dropped {dropped}"
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
    snapshot_runs_cols = _columns(tmp_db, "runs")

    rolled = db.rollback(tmp_db, steps=EXPECTED_MIGRATION_COUNT)
    assert len(rolled) == EXPECTED_MIGRATION_COUNT

    db.migrate(tmp_db)
    assert _tables(tmp_db) == snapshot
    assert _columns(tmp_db, "runs") == snapshot_runs_cols


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
    rolled = db.rollback(tmp_db, steps=4)
    assert rolled == ["009", "008", "007", "006"]
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
    assert versions == {
        "001", "002", "003", "004", "005", "006", "007", "008", "009",
    }


def test_migration_009_adds_kind_column_with_default_cron(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    cols = _columns(tmp_db, "runs")
    assert "kind" in cols, f"runs.kind column missing after migration 009; got {cols}"

    with db.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'ok')",
            ("2026-05-17T12:00:00+00:00",),
        )
    with db.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT kind FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row["kind"] == "cron", (
        f"new rows without an explicit kind must default to 'cron'; got {row['kind']!r}"
    )


def test_migration_009_kind_column_accepts_all_three_values(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    with db.connect(tmp_db) as conn:
        for kind in ("cron", "backfill", "manual"):
            conn.execute(
                "INSERT INTO runs (started_at, status, kind) VALUES (?, 'ok', ?)",
                ("2026-05-17T12:00:00+00:00", kind),
            )
    with db.connect(tmp_db) as conn:
        kinds = sorted(
            r["kind"] for r in conn.execute("SELECT kind FROM runs").fetchall()
        )
    assert kinds == ["backfill", "cron", "manual"]


def test_migration_009_down_removes_kind_column(tmp_db: Path) -> None:
    db.migrate(tmp_db)
    assert "kind" in _columns(tmp_db, "runs")
    rolled = db.rollback(tmp_db, steps=1)
    assert rolled == ["009"]
    assert "kind" not in _columns(tmp_db, "runs"), (
        "migration 009 down must drop the kind column cleanly"
    )
