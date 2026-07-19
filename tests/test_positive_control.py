"""Positive control — the harness must recover a KNOWN planted edge.

Referee attack #1 (2026-07-19): '28/28 negative is equally consistent
with an edgeless market and with a harness bug that destroys all
edges... a telescope never pointed at a known star.' This test plants
a star: synthetic bars where a volume-marker bar is followed by a
known +3% drift, a strategy that fires on the marker, and the FULL
pipeline (replay entry at next bar open, per-variant exits, fees,
slippage, portfolio constraints, gauntlet scoring). The measured
expectancy must recover the planted edge within tolerance — and a
second, pattern-blind variant must recover ~nothing. Runs in CI
forever: any future harness change that destroys edges fails here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import fetch
import replay
import signals
from tests.fixtures.bars import FakeBarSource


MARKER_VOL = 99999.0
DRIFT_PCT = 0.03          # +3% over the 36 bars after a marker
BARS_PER_EVENT = 350      # ~29h apart, so the 24h exit lands on the plateau
N_DAYS = 60


def _synthetic_bars(symbol: str = "BTC/USD") -> list:
    """Flat 100.0 series; every 288th bar carries the volume marker and
    the NEXT 36 bars drift linearly +3%, then price steps back."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    n = N_DAYS * 288
    bars = []
    price = 100.0
    drift_left = 0
    for i in range(n):
        ts = (start + timedelta(minutes=5 * i)).isoformat()
        vol = 100.0
        if drift_left > 0:
            price *= (1.0 + DRIFT_PCT / 36)
            drift_left -= 1
        elif i % BARS_PER_EVENT == BARS_PER_EVENT - 1:
            price = 100.0  # reset at each marker; drift then HOLDS to next event
            vol = MARKER_VOL
            drift_left = 36
        # otherwise price holds its plateau — the edge must persist past
        # the 24h exit or the "star" is a transient the exits legitimately miss
        bars.append(fetch.Bar(
            symbol=symbol, timestamp=ts,
            open=price, high=price * 1.0004, low=price * 0.9996,
            close=price, volume=vol,
        ))
    return bars


def _oracle(bars, params, ctx):
    last = bars[-1]
    if last.volume != MARKER_VOL:
        return None
    return signals.Signal(
        symbol=last.symbol, variant_name="", strategy="pc_oracle",
        side="buy", bar_timestamp=last.timestamp,
        price_at_signal=last.close, reasoning={})


def _blind(bars, params, ctx):
    """Fires on a schedule uncorrelated with the marker — must earn ~0."""
    last = bars[-1]
    t = datetime.fromisoformat(last.timestamp)
    if not (t.hour == 11 and t.minute == 0):
        return None
    return signals.Signal(
        symbol=last.symbol, variant_name="", strategy="pc_blind",
        side="buy", bar_timestamp=last.timestamp,
        price_at_signal=last.close, reasoning={})


@pytest.fixture
def planted_db(tmp_path: Path) -> Path:
    path = tmp_path / "planted.db"
    db.migrate(path)
    bars = _synthetic_bars()
    start = datetime.fromisoformat(bars[0].timestamp)
    end = datetime.fromisoformat(bars[-1].timestamp)
    fetch.fetch_window(FakeBarSource(bars=bars), ["BTC/USD"], start, end,
                       db_path=path)
    return path


def _run(planted: Path, strategy_key: str, fn) -> list:
    signals.STRATEGY_REGISTRY[strategy_key] = fn
    try:
        variant = {"strategy": strategy_key,
                   "params": {"tp": 0.05, "sl": 0.03, "time_exit_hours": 24},
                   "context_keys": [], "enabled": True}
        with db.connect(planted) as conn:
            trades = replay.replay_variant(
                conn, f"{strategy_key}_v", variant, ["BTC/USD"],
                datetime(2025, 12, 31, tzinfo=timezone.utc),
                datetime(2026, 12, 31, tzinfo=timezone.utc),
                fee_pct=0.0025, slippage_pct=0.0005,
            )
        return [t for t in replay.apply_portfolio_constraints(trades) if t.accepted]
    finally:
        del signals.STRATEGY_REGISTRY[strategy_key]


def test_harness_recovers_planted_edge(planted_db: Path) -> None:
    placed = _run(planted_db, "pc_oracle", _oracle)
    assert len(placed) >= 35, f"expected ~{N_DAYS} marker fires, got {len(placed)}"
    closed = [t for t in placed if t.pnl_usd is not None]
    mean_pct = sum(t.pnl_usd / (t.qty * t.entry_price) for t in closed) / len(closed) * 100
    # planted: +3% drift, 24h time exit captures it, minus ~0.6% costs
    assert 1.5 < mean_pct < 3.5, (
        f"harness recovered {mean_pct:.2f}%/trade from a +3%-planted edge — "
        "outside tolerance; the pipeline is distorting known signal "
        "(referee attack #1: the telescope can't see the planted star)"
    )


def test_pattern_blind_arm_recovers_nothing(planted_db: Path) -> None:
    placed = _run(planted_db, "pc_blind", _blind)
    closed = [t for t in placed if t.pnl_usd is not None]
    assert len(closed) >= 30
    mean_pct = sum(t.pnl_usd / (t.qty * t.entry_price) for t in closed) / len(closed) * 100
    # blind arm fires at 11:00; markers at 23:55 with 3h drift — should
    # earn roughly the cost drag, certainly nothing like the planted edge
    assert mean_pct < 0.5, (
        f"pattern-blind arm earned {mean_pct:.2f}%/trade on synthetic data — "
        "the harness is inventing edge from nothing"
    )


def test_transient_edge_is_invisible_to_the_exit_scheme(tmp_path: Path) -> None:
    """Referee attack #2 made visible: a REAL +3% edge that reverts
    within 3 hours recovers ~nothing under the +5%/-3%/24h exits —
    transient structure dies by exit shape, not by market absence.
    Every registry verdict on a fast-reverting mechanism carries this
    caveat; this test keeps the confound impossible to forget."""
    global BARS_PER_EVENT
    path = tmp_path / "transient.db"
    db.migrate(path)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars, price, drift_left = [], 100.0, 0
    for i in range(N_DAYS * 288):
        ts = (start + timedelta(minutes=5 * i)).isoformat()
        vol = 100.0
        if drift_left > 0:
            price *= (1.0 + DRIFT_PCT / 36)
            drift_left -= 1
        elif i % 350 == 349:
            price, vol, drift_left = 100.0, MARKER_VOL, 36
        else:
            price = 100.0  # transient: reverts right after the drift
        bars.append(fetch.Bar(symbol="BTC/USD", timestamp=ts, open=price,
                              high=price * 1.0004, low=price * 0.9996,
                              close=price, volume=vol))
    fetch.fetch_window(FakeBarSource(bars=bars), ["BTC/USD"],
                       datetime.fromisoformat(bars[0].timestamp),
                       datetime.fromisoformat(bars[-1].timestamp), db_path=path)
    placed = _run(path, "pc_transient", _oracle)
    closed = [t for t in placed if t.pnl_usd is not None]
    mean_pct = sum(t.pnl_usd / (t.qty * t.entry_price) for t in closed) / len(closed) * 100
    assert mean_pct < 0.5, "transient edge unexpectedly captured — exits changed?"


def test_golden_values_detect_numeric_drift(planted_db: Path) -> None:
    """SRE Run-7 item #1: tests stay green through sign flips in cost
    accounting unless something pins exact numbers. The planted-edge
    replay is fully deterministic — these rounded goldens change ONLY
    if entry pricing, fee math, exit logic, or constraint order change,
    and any such diff demands human sign-off."""
    placed = _run(planted_db, "pc_oracle", _oracle)
    closed = [t for t in placed if t.pnl_usd is not None]
    assert len(closed) == 49
    total_pnl = round(sum(t.pnl_usd for t in closed), 2)
    total_fees = round(sum(t.fees_usd for t in closed), 2)
    first = closed[0]
    golden = (total_pnl, total_fees, round(first.entry_price, 4),
              round(first.pnl_usd, 4), first.exit_reason)
    expected = (230.14, 49.7, 100.1334, 4.6966, "time_exit")
    assert golden == expected, (
        f"GOLDEN DRIFT: {golden} != {expected} — the replay engine's "
        "arithmetic changed; verify intentionality and update the golden."
    )
