"""Integration test for trade_cycle.py — the first live loop.

Seeds real bars, runs the cycle with the real registry (null_baseline
enabled), and asserts rows land in signals, decisions, and trades — the
three tables that stayed at zero for the project's first ten weeks.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import fetch
import trade_cycle
from config import WATCHED_SYMBOLS
from tests.fixtures.bars import FakeBarSource, make_bar_series


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


def _seed_all_symbols(db_path: Path, n: int = 60) -> None:
    start = datetime(2026, 7, 16, 0, 0, tzinfo=timezone.utc)
    bars = []
    for symbol in WATCHED_SYMBOLS:
        bars.extend(make_bar_series(symbol, start, n=n, base_price=100.0))
    source = FakeBarSource(bars=bars)
    fetch.fetch_window(
        source, WATCHED_SYMBOLS, start, start + timedelta(minutes=5 * n), db_path=db_path
    )


def _count(db_path: Path, table: str) -> int:
    with db.connect(db_path) as conn:
        return int(conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"])


def test_cycle_produces_signals_decisions_trades(tmp_db: Path) -> None:
    _seed_all_symbols(tmp_db)

    counts = trade_cycle.run_cycle(db_path=tmp_db)

    # null_baseline at p=0.10 over 5 symbols fires probabilistically per
    # cycle; the deterministic hash makes this specific fixture stable.
    # Whatever fired must have flowed through to decisions.
    assert counts["signals"] == _count(tmp_db, "signals")
    assert _count(tmp_db, "decisions") == _count(tmp_db, "signals")
    assert counts["placed"] <= counts["signals"]
    assert _count(tmp_db, "trades") == counts["placed"]


def test_cycle_is_idempotent_on_same_bars(tmp_db: Path) -> None:
    """Re-running on unchanged bars must not double-signal (deterministic
    null strategy + signals UNIQUE constraint)."""
    _seed_all_symbols(tmp_db)

    first = trade_cycle.run_cycle(db_path=tmp_db)
    second = trade_cycle.run_cycle(db_path=tmp_db)

    assert second["signals"] == 0 or _count(tmp_db, "signals") == first["signals"]
    assert _count(tmp_db, "decisions") == _count(tmp_db, "signals")


def test_cycle_eventually_fires_over_many_windows(tmp_db: Path) -> None:
    """Across 60 bars/symbol appended one at a time, p=0.10 across 5
    symbols makes at least one signal a statistical certainty (the
    deterministic hash gives a fixed, reproducible outcome)."""
    start = datetime(2026, 7, 16, 0, 0, tzinfo=timezone.utc)
    total_signals = 0
    for i in range(60):
        bars = []
        for symbol in WATCHED_SYMBOLS:
            bars.extend(
                make_bar_series(symbol, start + timedelta(minutes=5 * i), n=1, base_price=100.0)
            )
        fetch.fetch_window(
            FakeBarSource(bars=bars), WATCHED_SYMBOLS,
            start + timedelta(minutes=5 * i) - timedelta(minutes=1),
            start + timedelta(minutes=5 * i) + timedelta(minutes=1),
            db_path=tmp_db,
        )
        counts = trade_cycle.run_cycle(
            db_path=tmp_db, now=start + timedelta(minutes=5 * i + 1)
        )
        total_signals += counts["signals"]

    assert total_signals > 0, "null baseline never fired across 300 symbol-bars"
    assert _count(tmp_db, "decisions") == _count(tmp_db, "signals")
    assert _count(tmp_db, "trades") > 0, "no trade was ever placed"
