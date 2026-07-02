"""Tests for scripts/backfill.py."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import db
from scripts.backfill import parse_date, run_backfill
from tests.fixtures.bars import FakeBarSource, make_bar_series


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


def test_parse_date() -> None:
    assert parse_date("2026-01-03") == datetime(2026, 1, 3, tzinfo=timezone.utc)


def test_run_backfill_writes_bars_and_logs_backfill_kind(tmp_db: Path) -> None:
    start = datetime(2026, 1, 3, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, 1, 0, tzinfo=timezone.utc)
    bars = make_bar_series("BTC/USD", start, n=13, interval_minutes=5)
    source = FakeBarSource(bars=bars)

    run_id, bars_added = run_backfill(
        start, end, symbols=["BTC/USD"], source=source, db_path=tmp_db
    )

    assert bars_added == 13
    with db.connect(tmp_db) as conn:
        run = conn.execute("SELECT kind, status FROM runs WHERE id = ?", (run_id,)).fetchone()
        n = conn.execute("SELECT COUNT(*) AS c FROM bars").fetchone()["c"]
    assert run["kind"] == "backfill"
    assert run["status"] == "ok"
    assert n == 13


def test_run_backfill_end_before_start_raises(tmp_db: Path) -> None:
    start = datetime(2026, 1, 3, tzinfo=timezone.utc)
    end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="must be after"):
        run_backfill(start, end, symbols=["BTC/USD"], source=FakeBarSource(), db_path=tmp_db)


def test_run_backfill_defaults_to_watched_symbols(tmp_db: Path) -> None:
    from config import WATCHED_SYMBOLS

    start = datetime(2026, 1, 3, tzinfo=timezone.utc)
    end = datetime(2026, 1, 3, 1, 0, tzinfo=timezone.utc)
    all_bars = []
    for symbol in WATCHED_SYMBOLS:
        all_bars.extend(make_bar_series(symbol, start, n=3, interval_minutes=5))
    source = FakeBarSource(bars=all_bars)

    run_id, bars_added = run_backfill(start, end, source=source, db_path=tmp_db)

    assert bars_added == 3 * len(WATCHED_SYMBOLS)
    with db.connect(tmp_db) as conn:
        symbols_seen = {
            r["symbol"] for r in conn.execute("SELECT DISTINCT symbol FROM bars").fetchall()
        }
    assert symbols_seen == set(WATCHED_SYMBOLS)
