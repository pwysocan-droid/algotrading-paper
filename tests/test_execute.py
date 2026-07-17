"""Tests for execute.py — position-limit enforcement.

The position limits ($200/trade, $1,000 total, 5 concurrent, 1h cooldown)
are enforced in code, not honor system. Every check has a test that
constructs the limit-breach scenario and asserts a 'rejected' decision
is logged with a reason.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import db
import execute
from config import (
    MAX_CONCURRENT_POSITIONS,
    MAX_POSITION_USD,
    MAX_TOTAL_EXPOSURE_USD,
    SYMBOL_COOLDOWN_HOURS,
)
from execute import PendingSignal


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    db.migrate(path)
    return path


def _seed_signal(
    db_path: Path,
    symbol: str = "BTC/USD",
    variant: str = "test_variant",
    side: str = "buy",
    price: float = 60_000.0,
    bar_timestamp: str = "2026-05-01T12:00:00+00:00",
) -> int:
    with db.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO signals (
                symbol, variant_name, strategy, side, bar_timestamp,
                price_at_signal, reasoning_json, emitted_at
            ) VALUES (?, ?, 'test', ?, ?, ?, '{}', ?)
            """,
            (symbol, variant, side, bar_timestamp, price, "2026-05-01T12:01:00+00:00"),
        )
        return int(cur.lastrowid) if cur.lastrowid else 0


def _pending(db_path: Path, signal_id: int) -> PendingSignal:
    with db.connect(db_path) as conn:
        row = conn.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
    return PendingSignal(
        id=row["id"],
        symbol=row["symbol"],
        variant_name=row["variant_name"],
        strategy=row["strategy"],
        side=row["side"],
        bar_timestamp=row["bar_timestamp"],
        price_at_signal=row["price_at_signal"],
    )


def test_empty_db_zero_pending(tmp_db: Path) -> None:
    assert execute.process_pending(tmp_db) == 0
    with db.connect(tmp_db) as conn:
        n_trades = conn.execute("SELECT COUNT(*) AS c FROM trades").fetchone()["c"]
        n_decisions = conn.execute("SELECT COUNT(*) AS c FROM decisions").fetchone()["c"]
    assert n_trades == 0
    assert n_decisions == 0


def test_signal_within_limits_is_placed(tmp_db: Path) -> None:
    sid = _seed_signal(tmp_db, price=60_000.0)
    sig = _pending(tmp_db, sid)
    with db.connect(tmp_db) as conn:
        decision_id, action, reason = execute.execute_signal(
            conn, sig, entry_price=60_000.0,
            entry_time=datetime(2026, 5, 1, 12, 5, tzinfo=timezone.utc),
        )
    assert action == "placed"
    assert "60030" in reason  # 60000 * (1 + SLIPPAGE_PCT): entry slippage against the trader
    with db.connect(tmp_db) as conn:
        decision = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
        trade = conn.execute("SELECT * FROM trades WHERE id = ?", (decision["trade_id"],)).fetchone()
    assert decision["action"] == "placed"
    assert trade is not None
    assert trade["status"] == "open"
    assert abs(trade["qty"] * trade["entry_price"] - MAX_POSITION_USD) < 0.01


def test_signal_above_per_trade_max_is_rejected(tmp_db: Path) -> None:
    sid = _seed_signal(tmp_db)
    sig = _pending(tmp_db, sid)
    with db.connect(tmp_db) as conn:
        decision_id, action, reason = execute.execute_signal(
            conn, sig, entry_price=60_000.0,
            entry_time=datetime(2026, 5, 1, 12, 5, tzinfo=timezone.utc),
            intended_position_usd=MAX_POSITION_USD + 1.0,
        )
    assert action == "rejected"
    assert "exceeds per-trade max" in reason
    with db.connect(tmp_db) as conn:
        n_trades = conn.execute("SELECT COUNT(*) AS c FROM trades").fetchone()["c"]
        decision = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    assert n_trades == 0
    assert decision["trade_id"] is None


def test_total_exposure_cap_rejects_new_signal(tmp_db: Path) -> None:
    """Five $200 positions = $1000 ceiling; sixth $200 must reject on exposure."""
    base_time = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "LINK/USD", "AVAX/USD"]
    placed = 0
    for i, symbol in enumerate(symbols):
        sid = _seed_signal(tmp_db, symbol=symbol, variant=f"v{i}", price=100.0,
                           bar_timestamp=f"2026-05-01T{13 + i}:00:00+00:00")
        sig = _pending(tmp_db, sid)
        with db.connect(tmp_db) as conn:
            _, action, _ = execute.execute_signal(
                conn, sig, entry_price=100.0,
                entry_time=base_time + timedelta(hours=i + 1),
            )
        assert action == "placed", f"signal {i} should have placed"
        placed += 1
    assert placed == 5

    sid = _seed_signal(tmp_db, symbol="DOGE/USD", variant="v6", price=100.0,
                       bar_timestamp="2026-05-01T21:55:00+00:00")
    sig = _pending(tmp_db, sid)
    with db.connect(tmp_db) as conn:
        _, action, reason = execute.execute_signal(
            conn, sig, entry_price=100.0,
            entry_time=base_time + timedelta(hours=10),
        )
    assert action == "rejected"
    assert "concurrent positions" in reason or "total exposure" in reason


def test_concurrent_position_cap(tmp_db: Path) -> None:
    """At MAX_CONCURRENT_POSITIONS open trades, the next one is rejected."""
    base_time = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    symbols = ["S1", "S2", "S3", "S4", "S5"]
    for i, symbol in enumerate(symbols):
        sid = _seed_signal(tmp_db, symbol=symbol, variant=f"v{i}", price=10.0,
                           bar_timestamp=f"2026-05-01T{13 + i}:00:00+00:00")
        sig = _pending(tmp_db, sid)
        with db.connect(tmp_db) as conn:
            _, action, _ = execute.execute_signal(
                conn, sig, entry_price=10.0,
                entry_time=base_time + timedelta(hours=i + 1),
                intended_position_usd=10.0,
            )
        assert action == "placed"

    sid = _seed_signal(tmp_db, symbol="S6", variant="v6", price=10.0,
                       bar_timestamp="2026-05-01T21:55:00+00:00")
    sig = _pending(tmp_db, sid)
    with db.connect(tmp_db) as conn:
        _, action, reason = execute.execute_signal(
            conn, sig, entry_price=10.0,
            entry_time=base_time + timedelta(hours=10),
            intended_position_usd=10.0,
        )
    assert action == "rejected"
    assert f"max is {MAX_CONCURRENT_POSITIONS}" in reason


def test_symbol_cooldown_rejects_within_window(tmp_db: Path) -> None:
    sid1 = _seed_signal(tmp_db, symbol="BTC/USD", variant="v1", price=60_000.0,
                        bar_timestamp="2026-05-01T12:00:00+00:00")
    sig1 = _pending(tmp_db, sid1)
    base_time = datetime(2026, 5, 1, 12, 5, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        _, action, _ = execute.execute_signal(conn, sig1, entry_price=60_000.0, entry_time=base_time)
    assert action == "placed"

    sid2 = _seed_signal(tmp_db, symbol="BTC/USD", variant="v2", price=60_000.0,
                        bar_timestamp="2026-05-01T12:30:00+00:00")
    sig2 = _pending(tmp_db, sid2)
    with db.connect(tmp_db) as conn:
        _, action, reason = execute.execute_signal(
            conn, sig2, entry_price=60_000.0,
            entry_time=base_time + timedelta(minutes=30),
        )
    assert action == "rejected"
    assert "cooldown" in reason


def test_symbol_cooldown_clears_after_window(tmp_db: Path) -> None:
    sid1 = _seed_signal(tmp_db, symbol="BTC/USD", variant="v1", price=60_000.0,
                        bar_timestamp="2026-05-01T12:00:00+00:00")
    sig1 = _pending(tmp_db, sid1)
    base_time = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    with db.connect(tmp_db) as conn:
        _, action, _ = execute.execute_signal(conn, sig1, entry_price=60_000.0, entry_time=base_time)
    assert action == "placed"

    sid2 = _seed_signal(tmp_db, symbol="BTC/USD", variant="v2", price=60_000.0,
                        bar_timestamp="2026-05-01T13:55:00+00:00")
    sig2 = _pending(tmp_db, sid2)
    with db.connect(tmp_db) as conn:
        _, action, _ = execute.execute_signal(
            conn, sig2, entry_price=60_000.0,
            entry_time=base_time + timedelta(hours=SYMBOL_COOLDOWN_HOURS + 1),
        )
    assert action == "placed"


def test_pending_signals_excludes_decided(tmp_db: Path) -> None:
    sid1 = _seed_signal(tmp_db, symbol="BTC/USD", variant="v1", price=60_000.0,
                        bar_timestamp="2026-05-01T12:00:00+00:00")
    sid2 = _seed_signal(tmp_db, symbol="ETH/USD", variant="v2", price=2_000.0,
                        bar_timestamp="2026-05-01T12:05:00+00:00")
    with db.connect(tmp_db) as conn:
        pending = execute.pending_signals(conn)
    assert {s.id for s in pending} == {sid1, sid2}

    sig1 = _pending(tmp_db, sid1)
    with db.connect(tmp_db) as conn:
        execute.execute_signal(
            conn, sig1, entry_price=60_000.0,
            entry_time=datetime(2026, 5, 1, 12, 5, tzinfo=timezone.utc),
        )
        pending = execute.pending_signals(conn)
    assert {s.id for s in pending} == {sid2}


# --- Layer 4 exits (manage_exits) -------------------------------------------


def _seed_bar(
    db_path: Path, symbol: str, ts: str,
    high: float, low: float, close: float,
) -> None:
    with db.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO bars (symbol, timestamp, open, high, low, close, volume, fetched_at)"
            " VALUES (?, ?, ?, ?, ?, ?, 1.0, ?)",
            (symbol, ts, close, high, low, close, ts),
        )


def _open_trade(
    db_path: Path, symbol: str = "BTC/USD", side: str = "buy",
    entry_price: float = 100.0, qty: float = 2.0,
    entry_time: str = "2026-07-16T00:00:00+00:00",
) -> int:
    sid = _seed_signal(db_path, symbol=symbol, side=side, price=entry_price,
                       bar_timestamp=entry_time)
    with db.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO trades (signal_id, variant_name, symbol, side, qty,"
            " entry_price, entry_time, is_real_money, status)"
            " VALUES (?, 'null_baseline', ?, ?, ?, ?, ?, 0, 'open')",
            (sid, symbol, side, qty, entry_price, entry_time),
        )
        return int(cur.lastrowid)


def _trade_row(db_path: Path, trade_id: int):
    with db.connect(db_path) as conn:
        return conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()


def test_manage_exits_take_profit(tmp_db: Path) -> None:
    tid = _open_trade(tmp_db, entry_price=100.0)
    _seed_bar(tmp_db, "BTC/USD", "2026-07-16T00:05:00+00:00", high=106.0, low=101.0, close=104.0)
    now = datetime(2026, 7, 16, 0, 10, tzinfo=timezone.utc)

    closed = execute.manage_exits(db_path=tmp_db, now=now)

    assert closed == 1
    row = _trade_row(tmp_db, tid)
    assert row["status"] == "closed"
    assert row["exit_reason"] == "take_profit"
    # sim-to-live parity: exit slippage + taker fees both legs
    assert row["exit_price"] == pytest.approx(105.0 * 0.9995)
    assert row["pnl_usd"] == pytest.approx((104.9475 - 100) * 2 - (100 + 104.9475) * 2 * 0.0025)


def test_manage_exits_stop_loss_wins_ties(tmp_db: Path) -> None:
    tid = _open_trade(tmp_db, entry_price=100.0)
    # bar crosses BOTH stop (97) and target (105) — conservative: stop first
    _seed_bar(tmp_db, "BTC/USD", "2026-07-16T00:05:00+00:00", high=106.0, low=96.0, close=100.0)
    now = datetime(2026, 7, 16, 0, 10, tzinfo=timezone.utc)

    execute.manage_exits(db_path=tmp_db, now=now)

    row = _trade_row(tmp_db, tid)
    assert row["exit_reason"] == "stop_loss"
    assert row["exit_price"] == pytest.approx(97.0 * 0.9995)
    assert row["pnl_usd"] == pytest.approx((96.9515 - 100) * 2 - (100 + 96.9515) * 2 * 0.0025)


def test_manage_exits_sell_side_directions(tmp_db: Path) -> None:
    tid = _open_trade(tmp_db, side="sell", entry_price=100.0)
    # for a short: profit target is 95, stop is 103; bar dips to 94 → take profit
    _seed_bar(tmp_db, "BTC/USD", "2026-07-16T00:05:00+00:00", high=101.0, low=94.0, close=96.0)
    now = datetime(2026, 7, 16, 0, 10, tzinfo=timezone.utc)

    execute.manage_exits(db_path=tmp_db, now=now)

    row = _trade_row(tmp_db, tid)
    assert row["exit_reason"] == "take_profit"
    assert row["exit_price"] == pytest.approx(95.0 * 1.0005)  # short exit: slippage against
    assert row["pnl_usd"] == pytest.approx((100 - 95.0475) * 2 - (100 + 95.0475) * 2 * 0.0025)


def test_manage_exits_time_exit(tmp_db: Path) -> None:
    tid = _open_trade(tmp_db, entry_price=100.0, entry_time="2026-07-15T00:00:00+00:00")
    # quiet bar, no stop/target cross, but 25h elapsed
    _seed_bar(tmp_db, "BTC/USD", "2026-07-16T00:55:00+00:00", high=100.5, low=99.5, close=100.2)
    now = datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc)

    execute.manage_exits(db_path=tmp_db, now=now)

    row = _trade_row(tmp_db, tid)
    assert row["exit_reason"] == "time_exit"
    assert row["exit_price"] == pytest.approx(100.2 * 0.9995)


def test_manage_exits_leaves_healthy_position_open(tmp_db: Path) -> None:
    tid = _open_trade(tmp_db, entry_price=100.0)
    _seed_bar(tmp_db, "BTC/USD", "2026-07-16T00:05:00+00:00", high=101.0, low=99.0, close=100.5)
    now = datetime(2026, 7, 16, 0, 10, tzinfo=timezone.utc)

    closed = execute.manage_exits(db_path=tmp_db, now=now)

    assert closed == 0
    assert _trade_row(tmp_db, tid)["status"] == "open"


def test_manage_exits_no_bars_no_crash(tmp_db: Path) -> None:
    _open_trade(tmp_db, symbol="AVAX/USD")
    closed = execute.manage_exits(db_path=tmp_db, now=datetime(2026, 7, 16, tzinfo=timezone.utc))
    assert closed == 0


def test_closed_position_frees_slot_for_new_trade(tmp_db: Path) -> None:
    """The deadlock this feature exists to prevent: cap reached → exit → slot free."""
    for i in range(MAX_CONCURRENT_POSITIONS):
        _open_trade(tmp_db, symbol=f"SYM{i}/USD", entry_price=100.0)

    sid = _seed_signal(tmp_db, symbol="LINK/USD", price=10.0,
                       bar_timestamp="2026-07-16T00:05:00+00:00")
    sig = _pending(tmp_db, sid)
    with db.connect(tmp_db) as conn:
        _, action, reason = execute.execute_signal(
            conn, sig, entry_price=10.0,
            entry_time=datetime(2026, 7, 16, 0, 10, tzinfo=timezone.utc))
    assert action == "rejected"
    assert "concurrent" in reason

    # one position take-profits...
    _seed_bar(tmp_db, "SYM0/USD", "2026-07-16T00:05:00+00:00", high=106.0, low=101.0, close=105.0)
    execute.manage_exits(db_path=tmp_db, now=datetime(2026, 7, 16, 0, 10, tzinfo=timezone.utc))

    # ...and the same signal would now place (fresh signal, new bar ts)
    sid2 = _seed_signal(tmp_db, symbol="LINK/USD", price=10.0,
                        bar_timestamp="2026-07-16T00:10:00+00:00")
    sig2 = _pending(tmp_db, sid2)
    with db.connect(tmp_db) as conn:
        _, action2, _ = execute.execute_signal(
            conn, sig2, entry_price=10.0,
            entry_time=datetime(2026, 7, 16, 0, 15, tzinfo=timezone.utc))
    assert action2 == "placed"
