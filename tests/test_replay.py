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
from tests.fixtures.bars import FakeBarSource, make_bar_series, make_bars_with_gap


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


# --- Slippage --------------------------------------------------------------


class TestApplySlippage:
    def test_zero_pct_is_noop(self) -> None:
        assert replay._apply_slippage(100.0, "buy", "entry", 0.0) == 100.0

    def test_buy_entry_worse_is_higher(self) -> None:
        assert replay._apply_slippage(100.0, "buy", "entry", 0.01) == pytest.approx(101.0)

    def test_buy_exit_worse_is_lower(self) -> None:
        assert replay._apply_slippage(100.0, "buy", "exit", 0.01) == pytest.approx(99.0)

    def test_sell_entry_worse_is_lower(self) -> None:
        assert replay._apply_slippage(100.0, "sell", "entry", 0.01) == pytest.approx(99.0)

    def test_sell_exit_worse_is_higher(self) -> None:
        assert replay._apply_slippage(100.0, "sell", "exit", 0.01) == pytest.approx(101.0)


# --- Fees + slippage wired into replay_variant ------------------------------


def test_replay_variant_defaults_to_zero_cost(tmp_db: Path) -> None:
    """replay_variant's own defaults stay 0 — the look-ahead-bias tests above
    depend on exact bar-open prices and must not be perturbed by this change."""
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars = make_bars_with_gap(
        symbol="BTC/USD", start=base, closes=[100.0, 100.0], next_opens=[110.0, 110.0]
    )
    _seed_bars(tmp_db, bars)

    def fire_once(bars_so_far: list[BarRow], params: dict, ctx: dict) -> Signal | None:
        if len(bars_so_far) - 1 == 0:
            last = bars_so_far[-1]
            return Signal(
                symbol=last.symbol, variant_name="", strategy="fire_once", side="buy",
                bar_timestamp=last.timestamp, price_at_signal=last.close, reasoning={},
            )
        return None

    signals.STRATEGY_REGISTRY["fire_once"] = fire_once
    try:
        variant = {
            "strategy": "fire_once", "params": {}, "context_keys": [],
            "enabled": True, "phase_qualified": False,
        }
        with db.connect(tmp_db) as conn:
            plain = replay.replay_variant(
                conn, "v", variant, ["BTC/USD"],
                base - timedelta(minutes=1), base + timedelta(hours=1),
            )
            costed = replay.replay_variant(
                conn, "v", variant, ["BTC/USD"],
                base - timedelta(minutes=1), base + timedelta(hours=1),
                fee_pct=0.0025, slippage_pct=0.01,
            )
        assert len(plain) == 1 and len(costed) == 1
        p, c = plain[0], costed[0]

        assert p.entry_price == 110.0, "zero-cost default must match the raw bar open exactly"
        assert p.fees_usd == 0.0

        # buy entry worse = higher; buy exit worse = lower
        assert c.entry_price == pytest.approx(p.entry_price * 1.01)
        assert c.exit_price == pytest.approx(p.exit_price * 0.99)

        expected_fees = (c.entry_price + c.exit_price) * c.qty * 0.0025
        assert c.fees_usd == pytest.approx(expected_fees)

        gross = (c.exit_price - c.entry_price) * c.qty
        assert c.pnl_usd == pytest.approx(gross - expected_fees)
    finally:
        del signals.STRATEGY_REGISTRY["fire_once"]


def test_run_replay_defaults_apply_config_fee_and_slippage(
    tmp_db: Path, monkeypatch
) -> None:
    """The CLI/report path (run_replay), unlike replay_variant, must use the
    real config assumptions by default, not zero."""
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    bars = make_bars_with_gap(
        symbol="BTC/USD", start=base, closes=[100.0, 100.0], next_opens=[110.0, 110.0]
    )
    _seed_bars(tmp_db, bars)

    def fire_once(bars_so_far: list[BarRow], params: dict, ctx: dict) -> Signal | None:
        if len(bars_so_far) - 1 == 0:
            last = bars_so_far[-1]
            return Signal(
                symbol=last.symbol, variant_name="", strategy="fire_once", side="buy",
                bar_timestamp=last.timestamp, price_at_signal=last.close, reasoning={},
            )
        return None

    signals.STRATEGY_REGISTRY["fire_once"] = fire_once
    variant = {
        "strategy": "fire_once", "params": {}, "context_keys": [],
        "enabled": True, "phase_qualified": False,
    }
    monkeypatch.setattr(replay, "STRATEGY_VARIANTS", {"fire_once_default": variant})
    try:
        # period must cover `base` (2026-05-01) relative to the real wall-clock
        # `now` run_replay uses internally — a fixed generous window, not "30d".
        days_since_base = (datetime.now(timezone.utc) - base).days + 2
        markdown, trades = replay.run_replay(
            variant_arg="null", period=f"{days_since_base}d", db_path=tmp_db
        )
        assert len(trades) == 1
        assert trades[0].fees_usd > 0.0, "run_replay must apply the real config fee, not 0"
        assert trades[0].entry_price != 110.0, "run_replay must apply real slippage"
    finally:
        del signals.STRATEGY_REGISTRY["fire_once"]


# --- Portfolio constraints (mirrors execute.py.check_limits) ---------------


def _sim_trade(
    symbol: str,
    entry_ts: str,
    exit_ts: str,
    entry_price: float = 100.0,
    qty: float = 2.0,
    variant: str = "v",
) -> "replay.SimulatedTrade":
    return replay.SimulatedTrade(
        variant_name=variant,
        strategy="s",
        symbol=symbol,
        side="buy",
        signal_bar_timestamp=entry_ts,
        entry_bar_timestamp=entry_ts,
        entry_price=entry_price,
        qty=qty,
        exit_bar_timestamp=exit_ts,
        exit_price=entry_price,
        exit_reason="time_exit",
        pnl_usd=0.0,
        pnl_pct=0.0,
    )


def test_portfolio_constraints_empty_input() -> None:
    assert replay.apply_portfolio_constraints([]) == []


def test_portfolio_constraints_rejects_within_cooldown() -> None:
    t1 = _sim_trade("BTC/USD", "2026-05-01T00:00:00+00:00", "2026-05-01T00:30:00+00:00")
    t2 = _sim_trade("BTC/USD", "2026-05-01T00:30:00+00:00", "2026-05-01T01:00:00+00:00")
    out = replay.apply_portfolio_constraints([t1, t2])
    by_ts = {t.entry_bar_timestamp: t for t in out}
    assert by_ts[t1.entry_bar_timestamp].accepted is True
    assert by_ts[t2.entry_bar_timestamp].accepted is False
    assert "cooldown" in by_ts[t2.entry_bar_timestamp].reject_reason


def test_portfolio_constraints_allows_after_cooldown_elapses() -> None:
    t1 = _sim_trade("BTC/USD", "2026-05-01T00:00:00+00:00", "2026-05-01T00:05:00+00:00")
    t2 = _sim_trade("BTC/USD", "2026-05-01T02:00:00+00:00", "2026-05-01T02:30:00+00:00")
    out = replay.apply_portfolio_constraints([t1, t2])
    assert all(t.accepted for t in out)


def test_portfolio_constraints_rejects_over_concurrent_cap() -> None:
    five = [
        _sim_trade(f"SYM{i}/USD", "2026-05-01T00:00:00+00:00", "2026-05-01T10:00:00+00:00")
        for i in range(5)
    ]
    sixth = _sim_trade("SYM5/USD", "2026-05-01T00:00:00+00:00", "2026-05-01T10:00:00+00:00")
    out = replay.apply_portfolio_constraints(five + [sixth])
    assert sum(1 for t in out if t.accepted) == 5
    rejected = [t for t in out if not t.accepted]
    assert len(rejected) == 1
    assert "concurrent" in rejected[0].reject_reason


def test_portfolio_constraints_rejects_over_exposure_cap() -> None:
    # $250 notional each (entry_price=100, qty=2.5); 4 of them hit the $1,000 cap exactly
    four = [
        _sim_trade(
            f"SYM{i}/USD", "2026-05-01T00:00:00+00:00", "2026-05-01T10:00:00+00:00",
            entry_price=100.0, qty=2.5,
        )
        for i in range(4)
    ]
    fifth = _sim_trade(
        "SYM4/USD", "2026-05-01T00:00:00+00:00", "2026-05-01T10:00:00+00:00",
        entry_price=100.0, qty=2.5,
    )
    out = replay.apply_portfolio_constraints(four + [fifth])
    accepted = [t for t in out if t.accepted]
    rejected = [t for t in out if not t.accepted]
    assert len(accepted) == 4
    assert len(rejected) == 1
    assert "exposure" in rejected[0].reject_reason


def test_portfolio_constraints_frees_slot_after_position_exits() -> None:
    five = [
        _sim_trade(f"SYM{i}/USD", "2026-05-01T00:00:00+00:00", "2026-05-01T00:30:00+00:00")
        for i in range(5)
    ]
    later = _sim_trade("SYM9/USD", "2026-05-01T01:00:00+00:00", "2026-05-01T01:30:00+00:00")
    out = replay.apply_portfolio_constraints(five + [later])
    assert all(t.accepted for t in out), "the 5 early positions exit before the 6th opens"


# --- Bar coverage / continuity ----------------------------------------------


def test_bars_summary_reports_zero_gaps_for_complete_coverage(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    bars = make_bar_series("BTC/USD", start, n=13)  # exactly covers a 1h window
    _seed_bars(tmp_db, bars)
    with db.connect(tmp_db) as conn:
        rows = replay._bars_summary(conn, ["BTC/USD"], start, start + timedelta(hours=1))
    row = rows[0]
    assert row[0] == "BTC/USD"
    assert row[1] == "13"
    assert row[4] == "0", "13 bars at 5-min cadence over exactly 1h should show zero gaps"


def test_bars_summary_reports_missing_bars_as_gaps(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    all_bars = make_bar_series("BTC/USD", start, n=13)
    # drop 3 bars from the middle to simulate a data hole
    seeded = all_bars[:5] + all_bars[8:]
    _seed_bars(tmp_db, seeded)
    with db.connect(tmp_db) as conn:
        rows = replay._bars_summary(conn, ["BTC/USD"], start, start + timedelta(hours=1))
    assert rows[0][1] == "10"
    assert rows[0][4] == "3"


def test_bars_summary_empty_symbol_shows_emdash_gaps(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        rows = replay._bars_summary(conn, ["BTC/USD"], start, start + timedelta(hours=1))
    assert rows[0][1] == "0"
    assert rows[0][4] == replay.EMDASH


def test_check_coverage_full_coverage_has_no_gap(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    bars = make_bar_series("BTC/USD", start, n=13)
    _seed_bars(tmp_db, bars)
    with db.connect(tmp_db) as conn:
        reports = replay.check_coverage(conn, ["BTC/USD"], start, start + timedelta(hours=1))
    r = reports[0]
    assert r.n_bars == 13
    assert r.expected_bars == 13
    assert r.coverage_pct == pytest.approx(100.0)
    assert r.largest_gap_minutes == 0.0
    assert r.largest_gap_start is None


def test_check_coverage_finds_largest_gap(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    all_bars = make_bar_series("BTC/USD", start, n=13)
    # one 3-bar hole (15 min) in the middle; coverage math still uses the full window
    seeded = all_bars[:5] + all_bars[8:]
    _seed_bars(tmp_db, seeded)
    with db.connect(tmp_db) as conn:
        reports = replay.check_coverage(conn, ["BTC/USD"], start, start + timedelta(hours=1))
    r = reports[0]
    assert r.n_bars == 10
    assert r.expected_bars == 13
    assert r.coverage_pct == pytest.approx(10 / 13 * 100.0)
    assert r.largest_gap_minutes == pytest.approx(20.0)  # bars[4] to bars[8]: 4 steps * 5min
    assert r.largest_gap_start == all_bars[4].timestamp
    assert r.largest_gap_end == all_bars[8].timestamp


def test_check_coverage_no_bars_at_all(tmp_db: Path) -> None:
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        reports = replay.check_coverage(conn, ["BTC/USD"], start, start + timedelta(hours=1))
    r = reports[0]
    assert r.n_bars == 0
    assert r.coverage_pct == 0.0
    assert r.largest_gap_minutes == 0.0


# --- Sharpe / max drawdown ---------------------------------------------------


class TestSharpeRatio:
    def test_none_below_two_trades(self) -> None:
        assert replay.sharpe_ratio([], 30.0) is None
        assert replay.sharpe_ratio([1.0], 30.0) is None

    def test_none_on_zero_variance(self) -> None:
        assert replay.sharpe_ratio([0.5, 0.5, 0.5], 30.0) is None

    def test_none_on_zero_window(self) -> None:
        assert replay.sharpe_ratio([1.0, 2.0], 0.0) is None

    def test_positive_returns_positive_sharpe(self) -> None:
        s = replay.sharpe_ratio([0.5, 1.0, 0.8, 1.2, 0.6], 30.0)
        assert s is not None and s > 1.0

    def test_negative_returns_negative_sharpe(self) -> None:
        s = replay.sharpe_ratio([-0.5, -1.0, -0.8, -1.2, -0.6], 30.0)
        assert s is not None and s < 0.0

    def test_annualization_scales_with_trade_rate(self) -> None:
        pcts = [0.5, 1.0, 0.8, 1.2]
        dense = replay.sharpe_ratio(pcts, 10.0)   # same trades, shorter window
        sparse = replay.sharpe_ratio(pcts, 100.0)
        assert dense is not None and sparse is not None
        assert dense > sparse


class TestMaxDrawdown:
    def test_none_when_no_trades(self) -> None:
        assert replay.max_drawdown_pct([]) is None

    def test_zero_when_monotonic_gains(self) -> None:
        assert replay.max_drawdown_pct([10.0, 20.0, 5.0]) == pytest.approx(0.0)

    def test_simple_drawdown(self) -> None:
        # base 1000 → 1100 (peak) → 990: dd = 110/1100 = 10%
        dd = replay.max_drawdown_pct([100.0, -110.0])
        assert dd == pytest.approx(10.0)

    def test_recovery_does_not_erase_drawdown(self) -> None:
        dd = replay.max_drawdown_pct([100.0, -110.0, 500.0])
        assert dd == pytest.approx(10.0)

    def test_deepest_of_multiple_drawdowns_wins(self) -> None:
        # dd1: 1100→990 = 10%; dd2: 1490→1043 = 30%
        dd = replay.max_drawdown_pct([100.0, -110.0, 500.0, -447.0])
        assert dd == pytest.approx(30.0, abs=0.1)


class TestMakerFillModel:
    """fill_model='maker' — the cost lever (decision-log 2026-07-17).

    Entries are resting limits at the signal bar's close: they fill only on
    strict trade-through within the timeout, pay MAKER_FEE_PCT, no slippage.
    TP exits are also maker limits; SL/time exits stay taker + slippage.
    """

    BASE = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)

    def _bar(self, i: int, o: float, h: float, lo: float, c: float):
        from fetch import Bar
        ts = (self.BASE + timedelta(minutes=5 * i)).isoformat()
        return Bar(symbol="BTC/USD", timestamp=ts, open=o, high=h, low=lo,
                   close=c, volume=1000.0)

    def _run(self, tmp_db: Path, bars, **kwargs):
        _seed_bars(tmp_db, bars)

        def fire_on_first_bar(bars_so_far, params, ctx):
            if len(bars_so_far) != 1:
                return None
            last = bars_so_far[-1]
            return Signal(symbol=last.symbol, variant_name="", strategy="maker_fire",
                          side="buy", bar_timestamp=last.timestamp,
                          price_at_signal=last.close, reasoning={})

        signals.STRATEGY_REGISTRY["maker_fire"] = fire_on_first_bar
        try:
            variant = {"strategy": "maker_fire", "params": kwargs.pop("params", {}),
                       "context_keys": [], "enabled": True}
            with db.connect(tmp_db) as conn:
                return replay.replay_variant(
                    conn, "maker_fire_v", variant, ["BTC/USD"],
                    self.BASE - timedelta(minutes=1),
                    self.BASE + timedelta(hours=6),
                    fee_pct=0.0025, slippage_pct=0.0005,
                    fill_model="maker", **kwargs,
                )
        finally:
            del signals.STRATEGY_REGISTRY["maker_fire"]

    def test_entry_fills_on_trade_through_at_limit_price(self, tmp_db: Path) -> None:
        bars = [
            self._bar(0, 100, 100.5, 99.8, 100.0),   # signal bar: limit rests at 100
            self._bar(1, 100.2, 100.4, 99.5, 100.1),  # low 99.5 < 100 → fills
            self._bar(2, 100.1, 106.0, 100.0, 105.5),  # high 106 > tp 105 → maker tp
        ]
        trades = self._run(tmp_db, bars, params={"tp": 0.05, "sl": 0.03})
        assert len(trades) == 1
        t = trades[0]
        assert t.entry_price == 100.0  # limit price, no slippage
        assert t.entry_bar_timestamp == bars[1].timestamp  # fill bar, not signal+1 open
        assert t.exit_reason == "take_profit"
        assert t.exit_price == pytest.approx(105.0)  # no exit slippage on maker tp
        qty = 200.0 / 100.0
        assert t.fees_usd == pytest.approx((100.0 * 0.0015 + 105.0 * 0.0015) * qty)

    def test_unfilled_limit_drops_the_signal(self, tmp_db: Path) -> None:
        bars = [self._bar(0, 100, 100.5, 99.8, 100.0)] + [
            self._bar(i, 101, 102, 100.2, 101) for i in range(1, 8)  # never below 100
        ]
        trades = self._run(tmp_db, bars, limit_fill_timeout_bars=5)
        assert trades == []

    def test_touch_without_trade_through_does_not_fill(self, tmp_db: Path) -> None:
        bars = [self._bar(0, 100, 100.5, 99.8, 100.0)] + [
            self._bar(i, 101, 102, 100.0, 101) for i in range(1, 8)  # low == 100 exactly
        ]
        trades = self._run(tmp_db, bars, limit_fill_timeout_bars=5)
        assert trades == []

    def test_stop_loss_exit_stays_taker_with_slippage(self, tmp_db: Path) -> None:
        bars = [
            self._bar(0, 100, 100.5, 99.8, 100.0),
            self._bar(1, 100.2, 100.4, 99.5, 100.1),   # fills at 100
            self._bar(2, 99.0, 99.2, 96.5, 96.8),      # low 96.5 <= sl 97 → stop
        ]
        trades = self._run(tmp_db, bars, params={"tp": 0.05, "sl": 0.03})
        assert len(trades) == 1
        t = trades[0]
        assert t.exit_reason == "stop_loss"
        expected_exit = 97.0 * (1.0 - 0.0005)  # slippage against a sell exit
        assert t.exit_price == pytest.approx(expected_exit)
        qty = 200.0 / 100.0
        assert t.fees_usd == pytest.approx(
            (100.0 * 0.0015 + expected_exit * 0.0025) * qty
        )


def test_replay_system_state_keys_match_live_feed(tmp_db: Path) -> None:
    """The live and replay system_state feeds must expose the SAME keys.
    Round-004's fallback implementer added fields to the live feed only —
    the gated engine would have fired ZERO times in every gauntlet while
    working live (the vol_thrust never-fires bug, mirrored). This pins
    the contract end-to-end so the two sides can never drift again."""
    base = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    from tests.fixtures.bars import make_bar_series
    _seed_bars(tmp_db, make_bar_series("BTC/USD", base, n=6))

    captured: dict = {}

    def capture_state(bars_so_far, params, ctx):
        captured.update(state_keys=set((ctx.get("system_state") or {}).keys()))
        return None

    signals.STRATEGY_REGISTRY["state_capture"] = capture_state
    try:
        variant = {"strategy": "state_capture", "params": {},
                   "context_keys": ["system_state"], "enabled": True}
        with db.connect(tmp_db) as conn:
            replay.replay_variant(
                conn, "state_capture_v", variant, ["BTC/USD"],
                base - timedelta(minutes=1), base + timedelta(hours=1),
            )
            live_keys = set(signals.load_system_state(conn).keys())
    finally:
        del signals.STRATEGY_REGISTRY["state_capture"]

    assert captured.get("state_keys"), "capture strategy never received context"
    assert captured["state_keys"] == live_keys, (
        f"replay serves {captured['state_keys']}, live serves {live_keys} — "
        "extend replay._state_at whenever load_system_state grows"
    )


def test_window_bars_param_extends_replay_window(tmp_db: Path) -> None:
    """The vol_thrust never-fires class, third appearance (round-005,
    2026-07-20): strategies with multi-day lookbacks were silently
    truncated to 400 bars and fired ZERO times in the gauntlet while
    being valid live. params.window_bars now extends the replay window;
    this pins the convention across replay (here), run_variant, and
    parity_check (same param, same meaning)."""
    from tests.fixtures.bars import make_bar_series
    base = datetime(2026, 3, 1, tzinfo=timezone.utc)
    _seed_bars(tmp_db, make_bar_series("BTC/USD", base, n=700))

    seen = {"max_window": 0}

    def deep_lookback(bars_so_far, params, ctx):
        seen["max_window"] = max(seen["max_window"], len(bars_so_far))
        return None

    signals.STRATEGY_REGISTRY["deep_lookback"] = deep_lookback
    try:
        variant = {"strategy": "deep_lookback",
                   "params": {"window_bars": 600},
                   "context_keys": [], "enabled": True}
        with db.connect(tmp_db) as conn:
            replay.replay_variant(
                conn, "deep_v", variant, ["BTC/USD"],
                base - timedelta(minutes=1), base + timedelta(days=5),
            )
    finally:
        del signals.STRATEGY_REGISTRY["deep_lookback"]

    assert seen["max_window"] > 400, (
        f"window_bars=600 ignored: strategy max window {seen['max_window']} "
        "— multi-day lookbacks are being starved again"
    )
