"""Tests for replay.py — including the non-negotiable look-ahead-bias guard.

The guard: for a signal generated on bar N's close, the entry price MUST
be the OPEN of bar N+1, never bar N's close. This test constructs a
fixture where bar N's close and bar N+1's open differ materially and
asserts the recorded entry price matches bar N+1's open.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import fetch
import replay
import signals
from signals import BarRow, Signal
from tests.fixtures.bars import FakeBarSource, make_bars_with_gap


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


def _seed_bars(db_path: Path, bars) -> None:
    start = datetime.fromisoformat(bars[0].timestamp)
    end = datetime.fromisoformat(bars[-1].timestamp)
    source = FakeBarSource(bars=bars)
    fetch.fetch_window(source, [bars[0].symbol], start, end, db_path=db_path)


def test_lookahead_bias_guard_uses_next_bar_open(tmp_db: Path) -> None:
    """The headline test of the project's first build-quality concern.

    Construct bars where bar N's close = 100.0 and bar N+1's open = 110.0.
    Register a strategy that signals 'buy' on bar N's close. The recorded
    entry price must equal 110.0 (the open of bar N+1), never 100.0.
    """
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars = make_bars_with_gap(
        symbol="BTC/USD",
        start=base,
        closes=[100.0, 105.0, 102.0, 108.0],
        next_opens=[110.0, 95.0, 115.0, 99.0],
    )
    _seed_bars(tmp_db, bars)

    fired_on_bar_idx = 0

    def fire_once_strategy(bars_so_far: list[BarRow], params: dict, ctx: dict) -> Signal | None:
        if len(bars_so_far) - 1 == fired_on_bar_idx:
            last = bars_so_far[-1]
            return Signal(
                symbol=last.symbol,
                variant_name="",
                strategy="fire_once",
                side="buy",
                bar_timestamp=last.timestamp,
                price_at_signal=last.close,
                reasoning={"fire": "on bar 0"},
            )
        return None

    signals.STRATEGY_REGISTRY["fire_once"] = fire_once_strategy
    try:
        variant = {
            "strategy": "fire_once",
            "params": {},
            "context_keys": [],
            "enabled": True,
            "phase_qualified": False,
        }
        with db.connect(tmp_db) as conn:
            trades = replay.replay_variant(
                conn,
                variant_name="fire_once_default",
                variant=variant,
                symbols=["BTC/USD"],
                start=base - timedelta(minutes=1),
                end=base + timedelta(hours=1),
            )

        assert len(trades) == 1
        trade = trades[0]
        assert trade.signal_bar_timestamp == bars[0].timestamp
        assert trade.entry_bar_timestamp == bars[1].timestamp
        assert trade.entry_price == 110.0, (
            f"look-ahead bias: entry price {trade.entry_price} should equal bar N+1 open (110.0), "
            f"NOT bar N close (100.0). The guard from week-0-synthesis.md D2 is broken."
        )
        assert trade.entry_price != 100.0
    finally:
        del signals.STRATEGY_REGISTRY["fire_once"]


def test_signal_on_last_bar_drops_no_entry_available(tmp_db: Path) -> None:
    """If a signal fires on the last bar in the window, no future bar exists
    to provide an entry open price. The signal must be dropped, not back-filled."""
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars = make_bars_with_gap(
        symbol="ETH/USD",
        start=base,
        closes=[100.0, 105.0],
        next_opens=[110.0, 120.0],
    )
    _seed_bars(tmp_db, bars)

    last_bar_idx = len(bars) - 1

    def fire_on_last(bars_so_far: list[BarRow], params: dict, ctx: dict) -> Signal | None:
        if len(bars_so_far) - 1 == last_bar_idx:
            last = bars_so_far[-1]
            return Signal(
                symbol=last.symbol, variant_name="", strategy="fire_on_last",
                side="buy", bar_timestamp=last.timestamp, price_at_signal=last.close,
                reasoning={},
            )
        return None

    signals.STRATEGY_REGISTRY["fire_on_last"] = fire_on_last
    try:
        variant = {
            "strategy": "fire_on_last", "params": {}, "context_keys": [],
            "enabled": True, "phase_qualified": False,
        }
        with db.connect(tmp_db) as conn:
            trades = replay.replay_variant(
                conn, "fire_on_last_default", variant, ["ETH/USD"],
                start=base - timedelta(minutes=1), end=base + timedelta(hours=1),
            )
        assert trades == [], "signal on the last bar must produce no trade — no future open available"
    finally:
        del signals.STRATEGY_REGISTRY["fire_on_last"]


def test_replay_null_variant_against_empty_registry(tmp_db: Path, monkeypatch) -> None:
    """replay --variant=null with empty STRATEGY_VARIANTS produces zero trades."""
    monkeypatch.setattr(replay, "STRATEGY_VARIANTS", {})
    markdown, trades = replay.run_replay(variant_arg="null", period="30d", db_path=tmp_db)
    assert trades == []
    assert "0 trades" in markdown
    assert "no variants registered" in markdown
    assert "no data yet" not in markdown


def test_replay_null_report_is_fully_formed_v1_pattern(tmp_db: Path, monkeypatch) -> None:
    monkeypatch.setattr(replay, "STRATEGY_VARIANTS", {})
    markdown, _ = replay.run_replay(variant_arg="null", period="30d", db_path=tmp_db)
    assert "# algotrading-paper / replay" in markdown
    assert "Variant — null" in markdown
    assert "Period — " in markdown

    assert "**—**" in markdown, "em-dash for not-yet-present (variants registered)"
    assert "**0**" in markdown, "explicit 0 for trades-in-period"
    assert "**$0.00**" in markdown, "explicit $0.00 for P&L"

    assert "§ 01 — Per-variant performance" in markdown
    assert "§ 02 — Bars in period" in markdown
    assert "§ 03 — Run summary" in markdown
    assert "§ 04 — Notes" in markdown
    assert "§ Flags · none" in markdown

    assert "no variants registered" in markdown
    assert markdown.rstrip().endswith(
        "[github.com/pwysocan-droid/algotrading-paper](https://github.com/pwysocan-droid/algotrading-paper)"
    )


def test_simulate_exit_take_profit(tmp_db: Path) -> None:
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars = [
        BarRow("BTC/USD", (base + timedelta(minutes=5)).isoformat(), 100.0, 106.0, 99.0, 104.0, 1.0),
        BarRow("BTC/USD", (base + timedelta(minutes=10)).isoformat(), 104.0, 105.0, 103.0, 104.5, 1.0),
    ]
    exit_ts, exit_price, exit_reason = replay.simulate_exit(
        bars, entry_price=100.0, side="buy",
    )
    assert exit_reason == "take_profit"
    assert exit_price == pytest.approx(105.0)


def test_simulate_exit_stop_loss(tmp_db: Path) -> None:
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars = [
        BarRow("BTC/USD", (base + timedelta(minutes=5)).isoformat(), 100.0, 101.0, 96.0, 97.0, 1.0),
    ]
    exit_ts, exit_price, exit_reason = replay.simulate_exit(
        bars, entry_price=100.0, side="buy",
    )
    assert exit_reason == "stop_loss"
    assert exit_price == pytest.approx(97.0)


def test_simulate_exit_time_exit(tmp_db: Path) -> None:
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars = [
        BarRow("BTC/USD", (base + timedelta(hours=h)).isoformat(),
               100.0, 100.5, 99.5, 100.0, 1.0)
        for h in range(1, 30)
    ]
    exit_ts, exit_price, exit_reason = replay.simulate_exit(
        bars, entry_price=100.0, side="buy",
    )
    assert exit_reason == "time_exit"


def test_replay_invalid_period_raises(tmp_db: Path) -> None:
    with pytest.raises(ValueError, match="period must end in 'd'"):
        replay.run_replay(variant_arg="null", period="30", db_path=tmp_db)
