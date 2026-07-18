"""Tests for fetch.py against fixture data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import fetch
from tests.fixtures.bars import FakeBarSource, make_bar_series


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


def _row_count(db_path: Path, table: str) -> int:
    with db.connect(db_path) as conn:
        return int(conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"])


def test_fetch_writes_bars_and_logs_run(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    bars = make_bar_series("BTC/USD", start, n=12, interval_minutes=5)
    source = FakeBarSource(bars=bars)

    run_id, n = fetch.fetch_window(source, ["BTC/USD"], start, end, db_path=tmp_db)
    assert n == 12
    assert _row_count(tmp_db, "bars") == 12

    with db.connect(tmp_db) as conn:
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert run["status"] == "ok"
    assert run["bars_added"] == 12
    assert run["error_text"] is None
    assert run["finished_at"] is not None


def test_fetch_is_idempotent(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    bars = make_bar_series("BTC/USD", start, n=12)
    source = FakeBarSource(bars=bars)

    fetch.fetch_window(source, ["BTC/USD"], start, end, db_path=tmp_db)
    fetch.fetch_window(source, ["BTC/USD"], start, end, db_path=tmp_db)

    assert _row_count(tmp_db, "bars") == 12
    assert _row_count(tmp_db, "runs") == 2


def test_fetch_failure_logs_run_as_failed(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    source = FakeBarSource(raise_on_call=RuntimeError("alpaca 503"))

    with pytest.raises(RuntimeError, match="fetch failed"):
        fetch.fetch_window(source, ["BTC/USD"], start, end, db_path=tmp_db)

    assert _row_count(tmp_db, "bars") == 0
    with db.connect(tmp_db) as conn:
        run = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    assert run["status"] == "failed"
    assert "alpaca 503" in run["error_text"]
    assert run["finished_at"] is not None


def test_fetch_filters_to_requested_symbols(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    btc = make_bar_series("BTC/USD", start, n=6)
    eth = make_bar_series("ETH/USD", start, n=6, base_price=2000.0)
    source = FakeBarSource(bars=btc + eth)

    fetch.fetch_window(source, ["BTC/USD"], start, end, db_path=tmp_db)
    assert _row_count(tmp_db, "bars") == 6
    with db.connect(tmp_db) as conn:
        symbols = {
            r["symbol"]
            for r in conn.execute("SELECT DISTINCT symbol FROM bars").fetchall()
        }
    assert symbols == {"BTC/USD"}


def test_fetch_zero_bars_succeeds(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    source = FakeBarSource(bars=[])

    run_id, n = fetch.fetch_window(source, ["BTC/USD"], start, end, db_path=tmp_db)
    assert n == 0
    with db.connect(tmp_db) as conn:
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert run["status"] == "ok"
    assert run["bars_added"] == 0


def test_fetch_default_kind_is_cron(tmp_db: Path) -> None:
    """Default kind='cron' matches the GitHub Actions workflow default; no
    code change needed in the workflow YAML."""
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    bars = make_bar_series("BTC/USD", start, n=3)
    source = FakeBarSource(bars=bars)

    run_id, _ = fetch.fetch_window(source, ["BTC/USD"], start, end, db_path=tmp_db)
    with db.connect(tmp_db) as conn:
        row = conn.execute("SELECT kind FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["kind"] == "cron"


def test_fetch_kind_backfill_is_recorded(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    bars = make_bar_series("BTC/USD", start, n=3)
    source = FakeBarSource(bars=bars)

    run_id, _ = fetch.fetch_window(
        source, ["BTC/USD"], start, end, db_path=tmp_db, kind="backfill"
    )
    with db.connect(tmp_db) as conn:
        row = conn.execute("SELECT kind FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["kind"] == "backfill"


def test_fetch_kind_manual_is_recorded(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    bars = make_bar_series("BTC/USD", start, n=3)
    source = FakeBarSource(bars=bars)

    run_id, _ = fetch.fetch_window(
        source, ["BTC/USD"], start, end, db_path=tmp_db, kind="manual"
    )
    with db.connect(tmp_db) as conn:
        row = conn.execute("SELECT kind FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["kind"] == "manual"


def test_fetch_kind_failure_still_records_kind(tmp_db: Path) -> None:
    """Failed fetches record kind too — important for filtering uptime
    diagnostics by where the failure happened."""
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    source = FakeBarSource(raise_on_call=RuntimeError("alpaca 503"))

    with pytest.raises(RuntimeError):
        fetch.fetch_window(
            source, ["BTC/USD"], start, end, db_path=tmp_db, kind="cron"
        )
    with db.connect(tmp_db) as conn:
        row = conn.execute("SELECT kind, status FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    assert row["kind"] == "cron"
    assert row["status"] == "failed"


def test_fetch_kind_rejects_invalid_value(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    source = FakeBarSource(bars=[])

    with pytest.raises(ValueError, match="kind must be one of"):
        fetch.fetch_window(
            source, ["BTC/USD"], start, end, db_path=tmp_db, kind="bogus"
        )


def test_upsert_overwrites_on_collision(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars_v1 = make_bar_series("BTC/USD", start, n=3, base_price=100.0)
    bars_v2 = make_bar_series("BTC/USD", start, n=3, base_price=200.0)

    fetch.fetch_window(
        FakeBarSource(bars=bars_v1), ["BTC/USD"], start, start + timedelta(minutes=30), db_path=tmp_db
    )
    fetch.fetch_window(
        FakeBarSource(bars=bars_v2), ["BTC/USD"], start, start + timedelta(minutes=30), db_path=tmp_db
    )

    assert _row_count(tmp_db, "bars") == 3
    with db.connect(tmp_db) as conn:
        rows = conn.execute("SELECT close FROM bars ORDER BY timestamp").fetchall()
    assert [r["close"] for r in rows] == [200.0, 201.0, 202.0]


def test_context_depth_imbalance_and_schema(tmp_path):
    """Layer-2 collector: pure imbalance math + schema creation (the
    network path runs only on the VPS; this pins the testable core)."""
    from scripts.collect_context import depth_imbalance, migrate
    import sqlite3

    assert depth_imbalance([("1", "10")], [("2", "0")]) == 1.0
    assert depth_imbalance([("1", "0")], [("2", "10")]) == -1.0
    assert depth_imbalance([("1", "5")], [("2", "5")]) == 0.0
    assert depth_imbalance([], []) is None

    dbp = tmp_path / "context.db"
    migrate(dbp)
    with sqlite3.connect(dbp) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(context_snapshots)")]
    assert {"symbol", "ts", "funding_rate", "open_interest",
            "spread_pct", "depth_imbalance"} <= set(cols)
